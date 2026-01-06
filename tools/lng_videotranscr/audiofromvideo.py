
import os

from moviepy.editor import VideoFileClip

def extract_audio_from_videos(input_dir, output_dir, force = False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith((".mp4", ".mkv", ".avi")):
            video_path = os.path.join(input_dir, filename)
            audio_output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.mp3")
            if not force and os.path.isfile(audio_output_path):
                continue
            video_clip = VideoFileClip(video_path)
            video_clip.audio.write_audiofile(audio_output_path)

