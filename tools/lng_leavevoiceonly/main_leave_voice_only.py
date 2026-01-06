"""
prompt chatGPT
-------------------------------------------------
write python code that takes in input an .mp3 files and produces another .mp3 leaving in only human voices

answer:
-------------------------------------------------
To create a Python script that processes an .mp3 file and outputs another .mp3 file containing only human voices, 
you can use the pydub library for audio processing and the vosk library for speech recognition to filter out non-human sounds. 
Here's a step-by-step guide:

Install the required libraries:
pip install pydub vosk

You will also need to install the FFmpeg tool, which pydub relies on for audio processing. 
Instructions for installing FFmpeg can be found on their official website.

Download a Vosk model:
Download a suitable Vosk model for speech recognition from the Vosk model repository and extract it to a directory. 
For example, you can use the small-en model for English.

Create the script:
Here's the Python script that takes an .mp3 file as input, processes it to keep only human voices, and outputs another .mp3 file:


"""

import os
import wave
import json
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from tqdm import tqdm


def extract_human_voice(input_mp3_path, output_mp3_path, model_path):

    # Load the Vosk model
    model = Model(model_path)

    # Convert mp3 to wav
    audio = AudioSegment.from_mp3(input_mp3_path)
    wav_path = "./delete.wav"
    
    audio.export(wav_path, format="wav")
    print("esportato in .wav")

    # Open the wav file
    nr_canali = 1
    with wave.open(wav_path, "rb") as wf:
        nr_canali = wf.getnchannels()
    if nr_canali > 1:        
        print(f"ha più di un canale, ne ha: {nr_canali}")
        audio = audio.set_channels(1)
        print("esporto di nuovo dopo aver selezionato il canale 1")
        audio.export(wav_path, format="wav")
    
    with wave.open(wav_path, "rb") as wf:

        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        human_voice_segments = []

        i = 0
        while True:
            if i % 100 == 0:
                print(f"\r{i} ", end = "")
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if 'result' in result:
                    for word in result['result']:
                        start = word['start']
                        end = word['end']
                        segment = audio[start * 1000:end * 1000]  # convert to milliseconds
                        human_voice_segments.append(segment)

        # Combine human voice segments
        combined = AudioSegment.silent(duration=100*15)
        for segment in human_voice_segments:
            combined += segment

        # Export the result
        combined.export(output_mp3_path, format="mp3")

    print("\nfinito")
    # Clean up temporary files
    os.remove(wav_path)


def lower_non_voice(input_mp3_path, output_mp3_path, model_path):

    # Load the Vosk model
    model = Model(model_path)

    # Convert mp3 to wav
    audio = AudioSegment.from_mp3(input_mp3_path)
    wav_path = "./delete.wav"
    
    audio.export(wav_path, format="wav")
    print("esportato in .wav")

    # Open the wav file
    nr_canali = 1
    with wave.open(wav_path, "rb") as wf:
        nr_canali = wf.getnchannels()
    if nr_canali > 1:        
        print(f"ha più di un canale, ne ha: {nr_canali}")
        audio = audio.set_channels(1)
        print("esporto di nuovo dopo aver selezionato il canale 1")
        audio.export(wav_path, format="wav")

    # -----------------------------------------

    with wave.open(wav_path, "rb") as wf:

        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        total_frames = wf.getnframes()
        chunk_size = 4000
        duration_ms = len(audio)  # Total duration of the audio in milliseconds

        # Create a silent audio segment of the same duration
        processed_audio = AudioSegment.silent(duration=duration_ms)

        # Initialize tqdm progress bar
        with tqdm(total=total_frames, unit='frames', desc='Processing Audio') as pbar:
            current_position = 0  # Current position in milliseconds
            while True:
                data = wf.readframes(chunk_size)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if 'result' in result:
                        for word in result['result']:
                            start_ms = int(word['start'] * 1000)
                            end_ms = int(word['end'] * 1000)
                            segment = audio[start_ms:end_ms]
                            processed_audio = processed_audio.overlay(segment, position=start_ms)
                # Update progress bar and current position
                pbar.update(chunk_size)
                current_position += int(chunk_size / wf.getframerate() * 1000)

    # Export the result
    processed_audio.export(output_mp3_path, format="mp3")

    # Clean up temporary files
    os.remove(wav_path)




input_mp3 = "D:\\large\\lng-video\\\out-audio\\Bleach-001720pDualAnime_Gallery.mp3"
output_mp3_extract_voice = "./extract_voice.mp3"
output_mp3_lower_non_voice = "./lower_non_voice.mp3"
model_directory = "D:\\data_ENRICO\\08_dev\\08-dev-pers\\vosk_models\\vosk-model-small-ja-0.22"
wav_path = "d:\\large\\lng-video\\out-audio\\Bleach-001720pDualAnime_Gallery.wav"


if __name__ == "__main__":

    # extract_human_voice(input_mp3, output_mp3_extract_voice, model_directory)
    lower_non_voice(input_mp3, output_mp3_lower_non_voice, model_directory)