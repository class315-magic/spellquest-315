import easyocr
from gtts import gTTS
import cv2
import numpy as np
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import os

print("🚀 启动【一键生成单词视频-视频专属版】...")

audio_folder = 'audios'
os.makedirs(audio_folder, exist_ok=True)

target_words = []
if not os.path.exists('words.txt'):
    print("❌ 找不到 words.txt")
    exit()

with open('words.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip(): target_words.append(line.strip())

image_file = 'pic.jpg'
base_img_bgr = cv2.imread(image_file)
if base_img_bgr is None: exit()

pronunciation_guide = {"PE": "P E", "IT": "I T"}

print("正在请出 OCR 助手看图找词...")
reader = easyocr.Reader(['en'])
result = reader.readtext(image_file)

found_words_memo = {}
for item in result:
    text = item[1].strip()
    for target in target_words:
        if target.lower() in text.lower():
            found_words_memo[target] = ((int(item[0][0][0]), int(item[0][0][1])), (int(item[0][2][0]), int(item[0][2][1])))
            
recipe = []

for word_to_read in target_words:
    if word_to_read in found_words_memo:
        pos = found_words_memo[word_to_read]
    else:
        print(f"\n⚠️ AI 没认出 '{word_to_read}'，请用鼠标在弹出的图片上画框！(按回车确认)")
        h, w = base_img_bgr.shape[:2]
        max_display = 800
        scale = max_display / max(h, w) if max(h, w) > max_display else 1.0
        display_img = cv2.resize(base_img_bgr, (int(w * scale), int(h * scale)))
        
        roi = cv2.selectROI(f"Draw: {word_to_read} (Enter)", display_img, showCrosshair=True, fromCenter=False)
        cv2.destroyAllWindows()
        x, y, w_box, h_box = roi
        if w_box > 0:
            pos = ((int(x / scale), int(y / scale)), (int((x + w_box) / scale), int((y + h_box) / scale)))
        else:
            continue

    text_for_tts = pronunciation_guide.get(word_to_read, word_to_read)
    safe_name = word_to_read.replace(' ', '_').replace(':', '').replace("'", "")
    audio_filename = os.path.join(audio_folder, f"{safe_name}.mp3")
    
    tts = gTTS(text=text_for_tts, lang='en')
    tts.save(audio_filename)
    recipe.append({"word": word_to_read, "audio": audio_filename, "pos": pos})

if len(recipe) > 0:
    print("🎬 开始合成双层描边视频...")
    base_img_rgb = cv2.cvtColor(base_img_bgr, cv2.COLOR_BGR2RGB)
    pause_clip = ImageClip(base_img_rgb).with_duration(2)
    video_clips = []
    
    for item in recipe:
        audio_file = item["audio"]
        (x1, y1), (x2, y2) = item["pos"]
        img_with_box = base_img_rgb.copy()
        
        center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
        radius_x, radius_y = max(5, int((abs(x2 - x1) / 2) * 1.1) + 25), max(5, int(abs(y2 - y1) / 2) + 20)

        cv2.ellipse(img_with_box, (center_x, center_y), (radius_x, radius_y), 0, 0, 360, (255, 255, 255), 20)
        cv2.ellipse(img_with_box, (center_x, center_y), (radius_x, radius_y), 0, 0, 360, (255, 0, 0), 12)
        
        audio_clip = AudioFileClip(audio_file)
        img_clip = ImageClip(img_with_box).with_duration(audio_clip.duration).with_audio(audio_clip)
        
        video_clips.append(img_clip)
        video_clips.append(pause_clip) 
        
    print("正在导出最终 MP4，耐心等待...")
    concatenate_videoclips(video_clips).write_videofile("final_video.mp4", fps=24)
    print("--- 🌟 视频生成大功告成！ ---")