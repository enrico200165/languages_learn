"""

NON FUNZIONA PERCHè FALLISCE LA CHIAMATA A GOOGLE TRANSLATE, CIO' è RAGIONEVOLE PER 2 MOTIVI
- IL CODICE DI CHATGPT RIUTILIZZATO NON UTILIZZA CREDENZIALI
- ANCHE SE LE CREDENZIALI VENISSERO GESTITE è IMPROBABILE CHE UN ENOME FILE WAV DI 25+ MIN VENGA UPLOADATO
  (ANDREBBE SPEZZETTATO)
- CI SONO ENORMI RUMORI DI SOTTOFONDO CHE ANDREBBERO RIMOSSI

chatGPT prompt:
-------------------------------------------------
Scrivi codice python che elabora filmati in lingua giapponese e produce output per studiare la lingua.
Il programma deve:

elaborare tutti i files video presenti in una directory e, per ogni file:
estrarre l'audio in un file mp3
prendere in input l'audio e generare sottotitoli in Italiano in format .srt e, in un altro file, spiegare tutti i sostantivi e verbi
il programma deve funzionare anche con audio in linguaggio misto, ad esempio Inglese e Giapponese
il programma per la trascrizione e traduzione può usare librerie Google o altre librerie gratuite

risposta:
-------------------------------------------------
Per elaborare filmati in lingua giapponese e produrre output utili per lo studio della lingua, puoi seguire questi passi:

Estrarre l'audio dai video.
Trascrivere l'audio e generare sottotitoli.
Tradurre i sottotitoli in italiano.
Analizzare i sottotitoli per estrarre e spiegare sostantivi e verbi.
Per questo, useremo diverse librerie Python:

moviepy per estrarre l'audio dai video.
speech_recognition per la trascrizione dell'audio.
googletrans per la traduzione.
subtitles (creata ad hoc) per creare file SRT e analizzare i testi.

"""

import os


os.chdir("./lngvideotranscr")
import moduledefs as mdefs
import audiofromvideo as afv
import trascraudio as ta
import translate as trsl


def main():
    afv.extract_audio_from_videos(mdefs.input_directory, mdefs.output_directory)
    transcriptions = ta.dir_transcribe_audio(mdefs.output_directory)
    trsl.generate_subtitles(transcriptions, mdefs.SRT_OUT_DIR)


if __name__ == "__main__":
    try:
        main()
    finally:
        print(f"working dir: {os.getcwd()}")


