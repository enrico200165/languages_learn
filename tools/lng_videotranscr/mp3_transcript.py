import os
import whisper
from datetime import timedelta
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # garantisce risultati deterministici


def format_timestamp(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))

def format_txt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def format_srt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def process_audio_file(model, audio_path: str, output_base: str):
    result = model.transcribe(audio_path, task="transcribe", word_timestamps=False)

    srt_path = output_base + ".srt"
    txt_path = output_base + ".txt"

    with open(srt_path, "w", encoding="utf-8") as srt_file, open(txt_path, "w", encoding="utf-8") as txt_file:
        current_lang = None
        counter = 1

        for segment in result['segments']:
            # --- SRT ---
            start_srt = format_srt_timestamp(segment['start'])
            end_srt = format_srt_timestamp(segment['end'])

            srt_file.write(f"{counter}\n")
            srt_file.write(f"{start_srt} --> {end_srt}\n")
            srt_file.write(segment['text'].strip() + "\n\n")

            # --- Detect lingua per TXT ---
            try:
                detected_lang = detect(segment['text'])
            except:
                detected_lang = "unknown"

            if detected_lang != current_lang:
                current_lang = detected_lang
                txt_file.write(f"\n==================  {current_lang} ===============\n\n")

            # --- TXT ---
            start_txt = format_txt_timestamp(segment['start'])
            txt_file.write(f"{start_txt}\n")
            txt_file.write(segment['text'].strip() + "\n\n")

            counter += 1

def transcribe_directory(input_dir: str, output_dir: str, model_size="medium", overwrite = False):
    
    print(f"caricoo modello: <{model_size}> può essere molto grande, lento e fallire")
    model = whisper.load_model(model_size)
    print(f"OK! caricato modello: <{model_size}>")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".mp3"):
            audio_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_transcript.txt")
            if os.path.exists(output_path) and not overwrite:
                print(f"salto, esiste già {output_path} ")
                continue
            print(f"Elaborazione: {filename}")
            process_audio_file(model, audio_path, output_path)

# USO:
# transcribe_directory("input_mp3", "output_trascrizioni")

msize = "base"
msize = "small"

#transcribe_directory("d:\\04_large\\audio\\", "d:\\04_large\\audio\\out\\", model_size = msize)
transcribe_directory("v:\\", "d:\\04_large\\audio\\out\\", model_size = msize)
