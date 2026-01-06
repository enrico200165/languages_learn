import os
import re
import datetime
from typing import List, Set, Tuple, Optional

from aqt import mw
from aqt.qt import QAction, QFileDialog
from aqt.utils import showInfo, showCritical, getText, getItem


ADDON_NAME = "didactic_import_vals"
LOG_FILENAME = "didactic_import_vals.log"


def _addon_dir() -> str:
    return os.path.dirname(__file__)


def _log_path() -> str:
    return os.path.join(_addon_dir(), LOG_FILENAME)


def _log_line(message: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Se il log fallisce, evitare di bloccare il flusso del plugin.
        pass


def _read_vals_from_file(path: str) -> List[str]:
    vals: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            v = raw.strip()
            if not v:
                continue
            vals.append(v)
    return vals


_HASH_WRAPPED_RE = re.compile(r"^\s*##(.*?)##\s*$", re.DOTALL)


def _normalize_field_value(field_value: str) -> str:
    """
    Normalizzare il contenuto del campo per confrontarlo con val.

    Regola:
    - se è nel formato ##...##, estrarre il contenuto interno
    - altrimenti usare il valore così com’è, con trim spazi
    """
    if field_value is None:
        return ""
    s = str(field_value).strip()
    m = _HASH_WRAPPED_RE.match(s)
    if m:
        return (m.group(1) or "").strip()
    return s


def _get_deck_id_by_name(deck_name: str) -> Optional[int]:
    try:
        return mw.col.decks.id(deck_name)
    except Exception:
        return None


def _get_model_by_name(model_name: str):
    try:
        return mw.col.models.by_name(model_name)
    except Exception:
        return None


def _collect_existing_vals(deck_name: str, field_name: str, model_name: str) -> Set[str]:
    """
    Caricare tutte le note nel deck (opzionalmente filtrate per note type)
    e costruire l’insieme dei valori normalizzati del campo.
    """
    existing: Set[str] = set()

    # Query Anki: limitare al deck; se model_name è fornito, limitare anche al note type.
    # Nota: note:"..." è una sintassi di ricerca di Anki.
    q_parts = [f'deck:"{deck_name}"']
    if model_name:
        q_parts.append(f'note:"{model_name}"')
    query = " ".join(q_parts)

    try:
        note_ids = mw.col.find_notes(query)
    except Exception as e:
        _log_line(f'ERRORE find_notes query="{query}" err="{e}"')
        return existing

    for nid in note_ids:
        try:
            note = mw.col.get_note(nid)
            if field_name not in note:
                continue
            norm = _normalize_field_value(note[field_name])
            if norm:
                existing.add(norm)
        except Exception:
            # Se una nota non è leggibile, ignorare e continuare.
            continue

    return existing


def _create_note(deck_id: int, model_name: str, field_name: str, val: str) -> Tuple[bool, str]:
    """
    Creare una nuova nota nel deck_id, usando il modello model_name,
    impostando field_name = ##val##.

    Ritorna: (ok, message)
    """
    model = _get_model_by_name(model_name)
    if not model:
        return (False, f'Modello non trovato: "{model_name}"')

    try:
        note = mw.col.new_note(model)
    except Exception as e:
        return (False, f'Impossibile creare new_note() per modello "{model_name}": {e}')

    if field_name not in note:
        return (False, f'Campo "{field_name}" non presente nel modello "{model_name}"')

    note[field_name] = f"##{val}##"

    try:
        mw.col.add_note(note, deck_id)
        return (True, "OK")
    except Exception as e:
        return (False, f'add_note fallito: {e}')


def _choose_deck_name() -> Optional[str]:
    try:
        deck_names = sorted([d["name"] for d in mw.col.decks.all_names_and_ids()])
    except Exception:
        # Fallback per API meno recente: usare deckNames()
        deck_names = sorted(mw.col.decks.all_names())

    if not deck_names:
        return None

    chosen, ok = getItem(
        parent=mw,
        title="Selezione deck",
        prompt="Selezionare il deck in cui verificare e creare le note:",
        items=deck_names,
        current=0,
        editable=False,
    )
    if not ok:
        return None
    return chosen


def _choose_model_name() -> Optional[str]:
    model_names = sorted([m["name"] for m in mw.col.models.all()])
    if not model_names:
        return None

    chosen, ok = getItem(
        parent=mw,
        title="Selezione modello (Note Type)",
        prompt="Selezionare il modello (Note Type) da usare per le nuove note:",
        items=model_names,
        current=0,
        editable=False,
    )
    if not ok:
        return None
    return chosen


def _ask_field_name() -> Optional[str]:
    field_name, ok = getText(
        parent=mw,
        title="Campo da controllare/valorizzare",
        prompt='Inserire il nome del campo (es. "Front", "Back", "campo"):',
    )
    if not ok:
        return None
    field_name = (field_name or "").strip()
    if not field_name:
        return None
    return field_name


def _choose_input_file() -> Optional[str]:
    path, _ = QFileDialog.getOpenFileName(
        mw,
        "Selezionare file .txt (una riga = un val)",
        "",
        "Text Files (*.txt);;All Files (*)",
    )
    path = (path or "").strip()
    if not path:
        return None
    return path


def run_import_vals() -> None:
    if mw.col is None:
        showCritical("Collezione non disponibile.")
        return

    deck_name = _choose_deck_name()
    if not deck_name:
        return

    model_name = _choose_model_name()
    if not model_name:
        return

    field_name = _ask_field_name()
    if not field_name:
        return

    input_path = _choose_input_file()
    if not input_path:
        return

    deck_id = _get_deck_id_by_name(deck_name)
    if deck_id is None:
        showCritical(f'Deck non trovato: "{deck_name}"')
        return

    if not os.path.exists(input_path):
        showCritical(f"File non trovato:\n{input_path}")
        return

    _log_line("------------------------------------------------------------")
    _log_line(f'AVVIO import: deck="{deck_name}" deck_id="{deck_id}" model="{model_name}" field="{field_name}" file="{input_path}"')

    try:
        vals = _read_vals_from_file(input_path)
    except Exception as e:
        showCritical(f"Errore lettura file:\n{e}")
        _log_line(f'ERRORE lettura file="{input_path}" err="{e}"')
        return

    if not vals:
        showInfo("Nessun valore valido nel file (righe vuote o spazi).")
        _log_line("Nessun val nel file.")
        return

    existing_vals = _collect_existing_vals(deck_name=deck_name, field_name=field_name, model_name=model_name)

    created = 0
    present = 0
    skipped = 0
    errors = 0

    for v in vals:
        norm_v = v.strip()
        if not norm_v:
            skipped += 1
            _log_line('SCARTATA val="" (riga vuota dopo trim)')
            continue

        if norm_v in existing_vals:
            present += 1
            _log_line(f'PRESENTE val="{norm_v}"')
            continue

        ok, msg = _create_note(deck_id=deck_id, model_name=model_name, field_name=field_name, val=norm_v)
        if ok:
            created += 1
            existing_vals.add(norm_v)
            _log_line(f'CREATA val="{norm_v}" note_field="##{norm_v}##"')
        else:
            errors += 1
            _log_line(f'ERRORE_CREAZIONE val="{norm_v}" msg="{msg}"')

    try:
        mw.col.save()
    except Exception:
        # Salvataggio best-effort
        pass

    summary = (
        "Operazione completata.\n\n"
        f"Deck: {deck_name}\n"
        f"Modello: {model_name}\n"
        f"Campo: {field_name}\n"
        f"File: {input_path}\n\n"
        f"Valori presenti: {present}\n"
        f"Note create: {created}\n"
        f"Valori scartati: {skipped}\n"
        f"Errori: {errors}\n\n"
        f"Log: {_log_path()}"
    )
    showInfo(summary)
    _log_line(f'FINE import: presenti={present} create={created} scartate={skipped} errori={errors}')


def _setup_menu() -> None:
    action = QAction("Didactic: Import VAL file e crea note mancanti", mw)
    action.triggered.connect(run_import_vals)
    mw.form.menuTools.addAction(action)


_setup_menu()
