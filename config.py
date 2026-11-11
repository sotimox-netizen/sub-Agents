from pathlib import Path
from openai import OpenAI
from rich.console import Console

console = Console()

# Загрузка API ключа
key_path = Path.home() / "Documents" / "blablabla.txt"
try:
    api_key = key_path.read_text(encoding="utf-8").strip()
    if not api_key:
        console.print(f"[red]❌ Файл {key_path} пустой[/]")
        exit(1)
except FileNotFoundError:
    console.print(f"[red]❌ Файл не найден: {key_path}[/]")
    exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.aikeysforyou.com/v1"  # <-- URL от продавца
)

# Базовая директория
BASE_DIR = Path.cwd().resolve()

# Жёсткие лимиты (защита от 413)
MAX_TOOL_RESULT_CHARS = 2500
MAX_FILE_READ_CHARS = 3500
MAX_DIR_LIST_CHARS = 2000
MAX_SUB_RESULT_CHARS = 2000
MAX_CONTEXT_CHARS = 15000
MAX_HISTORY_TURNS = 2
MAX_FILE_SIZE = 100 * 1024

# Запрещённые файлы/папки
FORBIDDEN_PATTERNS = [
    ".env",
    "blablabla.txt",
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".idea",
]

console.print(f"[green]✅ API ключ загружен[/]")