import shutil
from datetime import datetime, timedelta
from pathlib import Path

from motocontrol.config import BACKUP_DIR, DB_PATH
from motocontrol.database.db import get_connection
from motocontrol.database.repositories import SettingsRepository


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_backup(backup_type: str = "manual", dest_dir: Path | None = None) -> Path:
    target_dir = dest_dir or BACKUP_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"motocontrol_{backup_type}_{_timestamp()}.db"
    dest = target_dir / filename
    shutil.copy2(DB_PATH, dest)

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO backup_log (backup_type, file_path) VALUES (?, ?)",
            (backup_type, str(dest)),
        )

    SettingsRepository.set(f"last_backup_{backup_type}", datetime.now().isoformat())
    return dest


def restore_backup(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Backup não encontrado: {source}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    pre_restore = BACKUP_DIR / f"pre_restore_{_timestamp()}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, pre_restore)
    shutil.copy2(source, DB_PATH)


def _should_run(backup_type: str, delta: timedelta) -> bool:
    enabled = SettingsRepository.get(f"backup_{backup_type}", "0") == "1"
    if not enabled:
        return False
    last = SettingsRepository.get(f"last_backup_{backup_type}", "")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return True
    return datetime.now() - last_dt >= delta


def run_scheduled_backups() -> list[Path]:
    created: list[Path] = []
    if _should_run("daily", timedelta(days=1)):
        created.append(create_backup("daily"))
    if _should_run("weekly", timedelta(weeks=1)):
        created.append(create_backup("weekly"))
    if _should_run("monthly", timedelta(days=30)):
        created.append(create_backup("monthly"))
    return created


def list_backups() -> list[dict]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for path in sorted(BACKUP_DIR.glob("motocontrol_*.db"), reverse=True):
        stat = path.stat()
        backups.append(
            {
                "path": str(path),
                "name": path.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "created": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%d/%m/%Y %H:%M"
                ),
            }
        )
    return backups
