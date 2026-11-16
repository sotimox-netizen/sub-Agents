import os
from pathlib import Path
from time import sleep

from openai import OpenAI
from rich.console import Console

console = Console()


def _load_dotenv(env_path: Path) -> None:
    """Минимальный загрузчик .env (без внешних зависимостей)."""
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass


# Корень проекта: если приложение запущено из исходников — поднимаемся
# на два уровня от subagents/core/config.py; иначе (exe в корне) берём cwd.
_project_root = Path(__file__).resolve().parents[2]
BASE_DIR = _project_root if (_project_root / "config.json").exists() else Path.cwd().resolve()

# Загрузка секрета: сначала переменная окружения, затем .env рядом с проектом.
_load_dotenv(BASE_DIR / ".env")

key_path = Path.home() / "Documents" / "blablabla.txt"
try:
    api_key = key_path.read_text(encoding="utf-8").strip()
    if not api_key:
        console.print(f"[red]файл {key_path} пустой[/red]")
        sleep(50)
        exit(1)
except FileNotFoundError:
    console.print(f"[red] файл не найден")

base_url = os.environ.get("OPENAI_BASE_URL", "https://api.aikeysforyou.com/v1")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

MAX_TOOL_RESULT_CHARS = 2500
MAX_FILE_READ_CHARS = 3500
MAX_DIR_LIST_CHARS = 2000
MAX_SUB_RESULT_CHARS = 2000
MAX_CONTEXT_CHARS = 15000
MAX_HISTORY_TURNS = 2
MAX_FILE_SIZE = 100 * 1024

FORBIDDEN_PATTERNS = [
    ".env",
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".idea",
    "build",
    "dist",
]

console.print(f"API ключ загружен", markup=False)