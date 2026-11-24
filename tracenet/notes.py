"""Status and note per complaint, saved next to the app so they survive a restart."""
import json
from pathlib import Path

STATUSES = ["new", "investigating", "frozen", "closed"]


def _path(base):
    return Path(base) / "case_notes.json"


def load_notes(base, prefix=""):
    try:
        raw = json.loads(_path(base).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {k[len(prefix):]: v for k, v in raw.items() if k.startswith(prefix)}


def save_note(base, prefix, cid, status, note):
    try:
        p = _path(base)
        raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        raw[prefix + cid] = dict(status=status, note=note)
        p.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
        return True
    except Exception:
        return False
