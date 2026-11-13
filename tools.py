import json
import time
from pathlib import Path
from ddgs import DDGS
from config import (
    console, BASE_DIR, FORBIDDEN_PATTERNS,
    MAX_FILE_SIZE, MAX_FILE_READ_CHARS, MAX_DIR_LIST_CHARS
)


def is_safe_path(path: Path) -> tuple[bool, str]:
    try:
        resolved = path.resolve()
        if BASE_DIR not in resolved.parents and resolved != BASE_DIR:
            return False, f"Путь выходит за пределы {BASE_DIR}"
        for forbidden in FORBIDDEN_PATTERNS:
            if forbidden in resolved.parts or resolved.name == forbidden:
                return False, f"Доступ к '{forbidden}' запрещён"
        return True, "OK"
    except Exception as e:
        return False, f"Ошибка проверки пути: {e}"


def execute_subagent_tool(agent_id: str, tool_name: str, args: dict, subagents: dict):
    agent = subagents[agent_id]
    console.print(f"    [dim][{agent['color']}]{tool_name}()[/]")


    if tool_name == "search_web":
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(args.get('query', ''), max_results=5))
                return {"result": "\n".join([f"{r['title']}: {r['body']}" for r in results])}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "execute_code":
        try:
            result = {}
            exec(args["code"], result)
            return {"output": str(result.get("result", "OK"))}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "save_to_file":
        filename = args.get("filename", "")
        code = args.get("code", "")
        if not filename or not code:
            return {"error": "Укажи filename и code"}
        forbidden = ["../", "/etc/", "C:\\Windows", "main.py"]
        if any(p in filename for p in forbidden):
            return {"error": f"Запрещено: {filename}"}
        agent_dir = BASE_DIR / "agent_output"
        agent_dir.mkdir(exist_ok=True)
        file_path = agent_dir / filename
        try:
            file_path.write_text(code, encoding="utf-8")
            console.print(f"    [green]📄 Сохранён: {file_path}[/]")
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "list_directory":
        path_str = args.get("path", ".")
        target = BASE_DIR / path_str
        safe, reason = is_safe_path(target)
        if not safe:
            return {"error": reason}
        if not target.exists() or not target.is_dir():
            return {"error": f"Директория не найдена: {path_str}"}
        try:
            entries = []
            for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if any(f in entry.parts or entry.name == f for f in FORBIDDEN_PATTERNS):
                    continue
                if entry.is_dir():
                    entries.append(f"📁 {entry.name}/")
                else:
                    size = entry.stat().st_size
                    s = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB"
                    entries.append(f"📄 {entry.name} ({s})")
            output = "\n".join(entries) if entries else "(пустая директория)"
            from memory import clip
            return {"result": clip(output, MAX_DIR_LIST_CHARS)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "read_file":
        path_str = args.get("path", "")
        if not path_str:
            return {"error": "Не указан путь"}
        target = BASE_DIR / path_str
        safe, reason = is_safe_path(target)
        if not safe:
            return {"error": reason}
        if not target.exists() or not target.is_file():
            return {"error": f"Файл не найден: {path_str}"}
        if target.stat().st_size > MAX_FILE_SIZE:
            return {"error": "Файл слишком большой"}
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            from memory import clip
            return {"result": clip(content, MAX_FILE_READ_CHARS)}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Неизвестный инструмент: {tool_name}"}