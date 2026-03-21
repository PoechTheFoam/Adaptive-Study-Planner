from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(base_dir: Path) -> None:
    env_path = base_dir / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    static_dir: Path
    database_path: Path
    host: str
    port: int
    ai_provider: str
    gemini_api_key: str
    gemini_model: str


def load_config() -> AppConfig:
    base_dir = Path(__file__).resolve().parent.parent
    load_dotenv(base_dir)

    database_raw = os.getenv("DATABASE_PATH", str(base_dir / "adaptive_partner.db"))
    database_path = Path(database_raw)
    if not database_path.is_absolute():
        database_path = base_dir / database_path

    return AppConfig(
        base_dir=base_dir,
        static_dir=base_dir / "app" / "static",
        database_path=database_path,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8765")),
        ai_provider=os.getenv("AI_PROVIDER", "gemini").strip().lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash",
    )
