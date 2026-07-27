"""
tiktok_profile_downloader.py
-----------------------------
Scarica tutti i video di un profilo TikTok non ancora scaricati in precedenza,
includendo i sottotitoli/didascalie quando disponibili. Pensato per lo studio
delle lingue offline (rivedere più volte lo stesso video).

Basato su yt-dlp. Funziona su Windows, macOS, Linux (Python 3.8+).

INSTALLAZIONE (una tantum):
    pip install -U yt-dlp
    (consigliato) installare anche ffmpeg per unire audio/video

USO BASE:
    python tiktok_profile_downloader.py https://www.tiktok.com/@nome_profilo

OPZIONI:
    --out CARTELLA       cartella di destinazione (default: ./downloads/<nome_profilo>)
    --limit N            scarica al massimo N video nuovi (utile per test)
    --no-subs            non tentare di scaricare i sottotitoli
    --cookies-from-browser BROWSER[:PROFILO]
                          usa i cookie di login già presenti nel browser
                          (chrome, firefox, edge, brave, opera, vivaldi, safari)
                          per accedere a contenuti visibili solo da account loggati.
                          Esempio: --cookies-from-browser chrome
                          Se hai più profili nello stesso browser (es. più profili
                          Chrome), specifica quale usare:
                          --cookies-from-browser "chrome:Profile 2"
                          Il nome del profilo corrisponde alla cartella dentro
                          %LocalAppData%\\Google\\Chrome\\User Data\\ su Windows
                          (es. "Default", "Profile 1", "Profile 2").
                          Nota: chiudere il browser prima di eseguire lo script,
                          alcuni browser bloccano il file dei cookie mentre sono aperti.

Come funziona il "non riscaricare due volte":
    Viene creato un file <cartella_output>/archivio_scaricati.txt che elenca
    gli ID dei video già scaricati. Ad ogni esecuzione successiva, yt-dlp
    consulta questo file e salta i video già presenti, scaricando solo
    quelli nuovi pubblicati dal profilo da allora.

Note importanti:
- TikTok non sempre fornisce sottotitoli veri; quando mancano, lo script
  scarica comunque il video (i sottotitoli restano un "se disponibili").
- Solo contenuti pubblici: profili privati o video ad accesso ristretto
  non sono supportati da questo script.
- Se dopo un aggiornamento di TikTok lo script smette di funzionare,
  spesso risolve un aggiornamento di yt-dlp: pip install -U yt-dlp
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import Optional


BROWSER_PROCESS_NAMES = {
    "chrome": ["chrome.exe"],
    "chromium": ["chromium.exe"],
    "firefox": ["firefox.exe"],
    "edge": ["msedge.exe"],
    "brave": ["brave.exe"],
    "opera": ["opera.exe", "opera_gx.exe"],
    "vivaldi": ["vivaldi.exe"],
}


def is_browser_running_windows(browser_name: str) -> bool:
    """
    Su Windows, controlla tramite 'tasklist' se il processo del browser indicato
    è ancora attivo (anche in background). Ritorna False su altri sistemi
    operativi o se il browser non è nella mappa sopra (es. safari).
    """
    if sys.platform != "win32":
        return False

    process_names = BROWSER_PROCESS_NAMES.get(browser_name.lower())
    if not process_names:
        return False

    try:
        result = subprocess.run(
            ["tasklist"], capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower()
        return any(name.lower() in output for name in process_names)
    except Exception:
        # Se il controllo stesso fallisce per qualche motivo, non blocchiamo
        # l'esecuzione: si procederà normalmente e l'eventuale errore di
        # permessi verrà comunque intercettato più avanti.
        return False

try:
    import yt_dlp
except ImportError:
    print("Il modulo 'yt-dlp' non è installato.")
    print("Installalo con:  pip install -U yt-dlp")
    sys.exit(1)


def parse_browser_and_profile(value: str):
    """
    Converte una stringa tipo "chrome" o "chrome:Profile 2" nella tupla
    che yt-dlp si aspetta per l'opzione cookiesfrombrowser:
    (nome_browser, profilo, keyring, container)
    """
    if ":" in value:
        browser, profile = value.split(":", 1)
        return (browser.strip(), profile.strip(), None, None)
    return (value.strip(), None, None, None)


def slug_from_profile_url(url: str) -> str:
    match = re.search(r"tiktok\.com/@([^/?]+)", url)
    return match.group(1) if match else "profilo_tiktok"


def download_profile(
    profile_url: str,
    output_dir: str,
    limit: Optional[int],
    want_subs: bool,
    cookies_browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    archive_file = os.path.join(output_dir, "archivio_scaricati.txt")
    outtmpl = os.path.join(output_dir, "%(upload_date)s - %(title).80s [%(id)s].%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "download_archive": archive_file,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "ignoreerrors": True,   # se un video fallisce, continua con gli altri
        "quiet": False,
        "no_warnings": False,
    }

    if limit:
        ydl_opts["playlistend"] = limit

    if cookies_file:
        if not os.path.isfile(cookies_file):
            print(f"\nIl file di cookie indicato non esiste: {cookies_file}")
            sys.exit(1)
        ydl_opts["cookiefile"] = cookies_file

    elif cookies_browser:
        # es: "chrome", "firefox", "chrome:Profile 2", "chrome:Lavoro"
        browser_name = cookies_browser.split(":", 1)[0].strip()

        if browser_name.lower() in ("chrome", "chromium", "edge", "brave", "opera", "vivaldi"):
            print(
                f"\nNota: dal 2024 Chrome e i browser basati su Chromium (incluso {browser_name}) "
                "cifrano i cookie in un modo che yt-dlp spesso non riesce a decifrare su Windows "
                "(errore 'Failed to decrypt with DPAPI'), indipendentemente da quanto il browser "
                "sia chiuso. Se ottieni questo errore, le alternative sono:\n"
                "  1) usa Firefox per i cookie: --cookies-from-browser firefox\n"
                "  2) esporta i cookie manualmente in un file cookies.txt (es. con l'estensione "
                "browser 'Get cookies.txt LOCALLY') e usa --cookies-file percorso\\al\\cookies.txt\n"
            )

        if is_browser_running_windows(browser_name):
            print(f"Attenzione: '{browser_name}' risulta ancora in esecuzione (anche in background).")
            print("Il file dei cookie potrebbe essere bloccato e la lettura potrebbe fallire.")
            print(f"Se lo script si interrompe con un errore di permessi, chiudi completamente")
            print(f"'{browser_name}' da Task Manager (Ctrl+Shift+Esc) e riprova.\n")

        ydl_opts["cookiesfrombrowser"] = parse_browser_and_profile(cookies_browser)

    if want_subs:
        ydl_opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["all"],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([profile_url])
    except Exception as e:
        error_text = str(e)

        if "DPAPI" in error_text:
            print(f"\nErrore di decifratura dei cookie di '{cookies_browser}' (DPAPI).")
            print("Questo NON dipende dal browser aperto o chiuso: Chrome e i browser Chromium")
            print("moderni cifrano i cookie in un modo che yt-dlp non riesce a decifrare su Windows.")
            print("Alternative:")
            print("  1) usa Firefox: --cookies-from-browser firefox")
            print("  2) esporta i cookie manualmente in cookies.txt e usa --cookies-file percorso\\cookies.txt")
            sys.exit(1)

        if isinstance(e, yt_dlp.utils.DownloadError):
            # Altri errori di download (URL non valido, video privato, rimosso, ecc.):
            # yt-dlp stampa già un messaggio leggibile, non serve aggiungerne un altro.
            sys.exit(1)

        # Errori nella lettura dei cookie dal browser (permessi, browser aperto,
        # nome browser errato, profilo browser non trovato, ecc.)
        if cookies_browser:
            print(f"\nImpossibile leggere i cookie da '{cookies_browser}': {e}")
            print("Verifica che:")
            print(f"  - il browser sia scritto correttamente (es. chrome, firefox, edge)")
            print(f"  - se hai indicato un profilo (es. chrome:Profile 2), che il nome sia esatto")
            print(f"  - il browser sia completamente chiuso (anche i processi in background:")
            print(f"    controlla in Task Manager, Ctrl+Shift+Esc, e termina tutti i processi del browser)")
            print(f"  - tu abbia effettivamente un profilo/cookie salvati in quel browser")
            sys.exit(1)
        raise

    if cookies_browser:
        print(f"\nNota: sono stati usati i cookie di '{cookies_browser}'.")
        print("Questo NON garantisce che tu risulti loggato su TikTok in quella sessione:")
        print("se non avevi eseguito l'accesso nel browser, lo script ha comunque scaricato")
        print("solo i contenuti pubblici, senza segnalare errori.")

    print(f"\nCompletato. File salvati in: {output_dir}")
    print(f"Archivio dei video già scaricati: {archive_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Scarica tutti i video nuovi di un profilo TikTok, con sottotitoli se disponibili."
    )
    parser.add_argument("profile_url", help="URL del profilo TikTok, es: https://www.tiktok.com/@nome_profilo")
    parser.add_argument("--out", default=None, help="Cartella di destinazione (default: ./downloads/<profilo>)")
    parser.add_argument("--limit", type=int, default=None, help="Numero massimo di video nuovi da scaricare")
    parser.add_argument("--no-subs", action="store_true", help="Non tentare di scaricare i sottotitoli")
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        metavar="BROWSER[:PROFILO]",
        help="Usa i cookie di login già presenti nel browser (chrome, firefox, edge, brave, opera, vivaldi, chromium, safari). "
             "Se hai più profili nello stesso browser (es. più profili Chrome), specifica quale usare con "
             "'chrome:NomeProfilo', es: --cookies-from-browser \"chrome:Profile 2\". "
             "Il nome del profilo è quello mostrato nel browser, oppure il nome della cartella in "
             "%%LocalAppData%%\\Google\\Chrome\\User Data\\ su Windows (es. 'Default', 'Profile 1', 'Profile 2'). "
             "Senza indicarlo, viene usato il profilo predefinito.",
    )

    parser.add_argument(
        "--cookies-file",
        default=None,
        metavar="PERCORSO",
        help="Percorso a un file cookies.txt esportato manualmente dal browser (formato Netscape), "
             "es. con l'estensione 'Get cookies.txt LOCALLY'. Alternativa a --cookies-from-browser, "
             "utile quando Chrome dà errore di decifratura DPAPI. Se entrambi indicati, questo ha priorità.",
    )

    args = parser.parse_args()

    output_dir = args.out or os.path.join("downloads", slug_from_profile_url(args.profile_url))

    try:
        download_profile(
            args.profile_url,
            output_dir,
            limit=args.limit,
            want_subs=not args.no_subs,
            cookies_browser=args.cookies_from_browser,
            cookies_file=args.cookies_file,
        )
    except yt_dlp.utils.DownloadError as e:
        print(f"\nErrore durante il download: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
