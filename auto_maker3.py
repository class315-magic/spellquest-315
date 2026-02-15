import easyocr
from gtts import gTTS
import cv2
import os
import glob

print("🚀 启动【网页点读-多图防压缩终极版】...")

audio_folder = 'audios'
os.makedirs(audio_folder, exist_ok=True)

target_words = []
if os.path.exists('words.txt'):
    with open('words.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): target_words.append(line.strip())
else:
    print("❌ 找不到 words.txt")
    exit()

# 【魔法核心】：自动寻找所有以 pic 开头的图片 (比如 pic1.jpg, pic2.jpg)
image_files = sorted(glob.glob('pic*.jpg'))
if not image_files:
    print("❌ 找不到任何以 pic 开头的图片！请把图片命名为 pic1.jpg, pic2.jpg")
    exit()

pronunciation_guide = {"PE": "P E", "IT": "I T"}
reader = easyocr.Reader(['en'])

html_images = ""

print("\n" + "="*50)
html_name = input("✍️ 请输入这个单元网页的名字 (比如第一单元填 map1，第二单元填 map2): ")
if not html_name: html_name = "map"

remaining_words = target_words.copy()

for img_file in image_files:
    print(f"\n🔍 正在扫描图片: {img_file} ...")
    base_img_bgr = cv2.imread(img_file)
    img_height, img_width = base_img_bgr.shape[:2]
    
    # 自动重命名并保存图片
    new_img_name = f"{html_name}_{image_files.index(img_file)+1}.jpg"
    cv2.imwrite(new_img_name, base_img_bgr)
    
    html_images += f'\n<div class="image-container">'
    html_images += f'\n    <img src="{new_img_name}" alt="单词地图" class="bg-image">'

    result = reader.readtext(base_img_bgr)
    found_words_in_this_img = {}
    
    for item in result:
        text = item[1].strip()
        for target in remaining_words:
            if target.lower() in text.lower():
                found_words_in_this_img[target] = ((int(item[0][0][0]), int(item[0][0][1])), (int(item[0][2][0]), int(item[0][2][1])))

    words_to_remove = []
    for word_to_read in remaining_words:
        pos = None
        if word_to_read in found_words_in_this_img:
            pos = found_words_in_this_img[word_to_read]
            print(f"  🎯 自动锁定: {word_to_read}")
        else:
            print(f"  ⚠️ 没认出 '{word_to_read}'。")
            print(f"  👉 如果它在【{img_file}】这张图里，请用鼠标画框；如果不在，请直接按回车跳过！")
            
            h, w = base_img_bgr.shape[:2]
            max_display = 800
            scale = max_display / max(h, w) if max(h, w) > max_display else 1.0
            display_img = cv2.resize(base_img_bgr, (int(w * scale), int(h * scale)))
            
            roi = cv2.selectROI(f"Draw '{word_to_read}' (Enter to skip)", display_img, showCrosshair=True, fromCenter=False)
            cv2.destroyAllWindows()
            x, y, w_box, h_box = roi
            if w_box > 0:
                pos = ((int(x / scale), int(y / scale)), (int((x + w_box) / scale), int((y + h_box) / scale)))
                print(f"  ✅ 画框成功！")
            else:
                print(f"  ⏩ 已跳过。")
        
        if pos:
            words_to_remove.append(word_to_read)
            text_for_tts = pronunciation_guide.get(word_to_read, word_to_read)
            safe_name = word_to_read.replace(' ', '_').replace(':', '').replace("'", "")
            audio_filename = os.path.join(audio_folder, f"{safe_name}.mp3")
            if not os.path.exists(audio_filename):
                tts = gTTS(text=text_for_tts, lang='en')
                tts.save(audio_filename)
            
            (x1, y1), (x2, y2) = pos
            left_pct = (x1 / img_width) * 100
            top_pct = (y1 / img_height) * 100
            width_pct = ((x2 - x1) / img_width) * 100
            height_pct = ((y2 - y1) / img_height) * 100
            
            html_images += f"""
    <div class="click-box" style="left: {left_pct-1}%; top: {top_pct-1}%; width: {width_pct+2}%; height: {height_pct+2}%;" onclick="playSound('{safe_name}')"></div>"""

    for w in words_to_remove:
        remaining_words.remove(w)
        
    html_images += f'\n</div>' 

final_html_file = f"{html_name}.html"

full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>315班 - {html_name} 点读</title>
    <style>
        body {{ background-color: #e8f5e9; text-align: center; font-family: 'Segoe UI', sans-serif; color: #2e7d32; margin: 0; padding: 10px; }}
        h2 {{ margin-bottom: 5px; }}
        .game-board {{ display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 10px; width: 100%; }}
        .image-container {{ position: relative; display: inline-block; box-shadow: 0 6px 20px rgba(0,0,0,0.15); border-radius: 12px; max-width: 98%; }}
        .bg-image {{ display: block; max-width: 100%; height: auto; border-radius: 12px; }}
        .click-box {{ position: absolute; cursor: pointer; border: 3px solid transparent; border-radius: 8px; transition: all 0.2s; box-sizing: border-box; }}
        .click-box:hover {{ border: 3px solid #ff5722; background-color: rgba(255, 87, 34, 0.2); transform: scale(1.05); box-shadow: 0 0 10px rgba(255, 87, 34, 0.5); }}
        .click-box:active {{ transform: scale(0.95); }}
        .back-btn {{ margin-bottom: 15px; padding: 10px 20px; background: #00f2fe; color: white; border: none; border-radius: 20px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 10px rgba(0,242,254,0.4); text-decoration: none; display: inline-block; }}
    </style>
</head>
<body>

    <a href="index.html" class="back-btn">⬅️ 返回游戏主页</a>
    <h2>🗺️ 魔法点读地图</h2>
    <p>👇 上下滑动查看全部，点击发音 👇</p>
    
    <div class="game-board">
        {html_images}
    </div>

    <script>
        function playSound(fileName) {{
            let audio = new Audio('audios/' + fileName + '.mp3');
            audio.currentTime = 0; 
            audio.play().catch(e => console.log("等待用户交互"));
        }}
    </script>
</body>
</html>
"""

with open(final_html_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"\n--- 🌟 成功！已生成 {final_html_file}，包含了 {len(image_files)} 张高清原图排版！ ---")