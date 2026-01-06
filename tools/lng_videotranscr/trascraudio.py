
import os
import subprocess
import speech_recognition as sr

def file_transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_path)

    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        # Riconoscimento del parlato
        text = recognizer.recognize_google(audio_data, language="ja-JP")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")


def dir_transcribe_audio(audio_directory):


    transcriptions = {}

    for audio_file in os.listdir(audio_directory):
        if audio_file.endswith(".mp3"):
            audio_path = os.path.join(audio_directory, audio_file)

            # connverti in .wav mp3 non sembra funzoinare
            pre, _ = os.path.splitext(audio_path)
            wav_audio_path = pre+".wav"
            if not os.path.exists(wav_audio_path):
                subprocess.call(['ffmpeg', '-i', audio_path, wav_audio_path ])

            transcription = file_transcribe_audio(wav_audio_path)
            transcriptions[audio_file] = transcription
    
    return transcriptions
