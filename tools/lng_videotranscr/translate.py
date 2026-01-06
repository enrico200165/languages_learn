
from googletrans import Translator
import srt

def generate_subtitles(transcriptions, output_dir):
    translator = Translator()

    for audio_file, transcription in transcriptions.items():
        translated_text = translator.translate(transcription, src='ja', dest='it').text

        # Creazione del file SRT
        subtitles = []
        lines = translated_text.split('\n')
        for i, line in enumerate(lines):
            start_time = srt.timedelta(seconds=i * 2)
            end_time = srt.timedelta(seconds=(i + 1) * 2)
            subtitle = srt.Subtitle(index=i + 1, start=start_time, end=end_time, content=line)
            subtitles.append(subtitle)

        srt_content = srt.compose(subtitles)
        srt_filename = os.path.join(output_dir, f"{os.path.splitext(audio_file)[0]}.srt")
        with open(srt_filename, "w", encoding='utf-8') as f:
            f.write(srt_content)

