import os
from pathlib import Path
from ddgs import DDGS
from subagents.core.config import (
    console, BASE_DIR, FORBIDDEN_PATTERNS,
    MAX_FILE_SIZE, MAX_FILE_READ_CHARS, MAX_DIR_LIST_CHARS
)
from subagents.security.pathguard import safe_join, safe_filename
from subagents.security.sandbox import run_python_sandboxed

# Директория, в которую агенту разрешено писать файлы.
AGENT_OUTPUT_DIR = (BASE_DIR / "agent_output").resolve()


def is_safe_path(path: Path) -> tuple[bool, str]:
    try:
        resolved = path.resolve()
        if BASE_DIR not in resolved.parents and resolved != BASE_DIR:
            return False, f"Путь выходит за пределы {BASE_DIR}"
        rel_parts = resolved.relative_to(BASE_DIR).parts if resolved != BASE_DIR else ()
        for forbidden in FORBIDDEN_PATTERNS:
            if forbidden in rel_parts or resolved.name == forbidden:
                return False, f"Доступ к '{forbidden}' запрещён"
        if resolved.name in ("config.json", ".env") or resolved.name.endswith(".key"):
            return False, "Доступ к конфигурационным/секретным файлам запрещён"
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
        code = args.get("code", "")
        if not isinstance(code, str):
            return {"error": "code должен быть строкой"}
        try:
            return run_python_sandboxed(code)
        except Exception as e:
            return {"error": f"Ошибка песочницы: {e}"}

    elif tool_name == "save_to_file":
        filename = args.get("filename", "")
        code = args.get("code", "")
        if not isinstance(filename, str) or not isinstance(code, str):
            return {"error": "filename и code должны быть строками"}
        if not filename or not code:
            return {"error": "Укажи filename и code"}
        if len(code) > MAX_FILE_SIZE:
            return {"error": "Слишком большой объём данных для записи"}

        clean_name, err = safe_filename(filename)
        if err:
            return {"error": err}
        if "/" in filename or "\\" in filename:
            return {"error": f"Путь в имени файла запрещён: {filename!r}"}

        AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        file_path, err = safe_join(AGENT_OUTPUT_DIR, clean_name)
        if err:
            return {"error": err}
        try:
            real = file_path.resolve()
            if AGENT_OUTPUT_DIR not in real.parents:
                return {"error": "Путь выходит за пределы agent_output"}
        except Exception as e:
            return {"error": f"Ошибка проверки пути: {e}"}

        try:
            file_path.write_text(code, encoding="utf-8")
            console.print(f"    [green]Сохранён: {file_path}[/]")
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "list_directory":
        path_str = args.get("path", ".")
        target, err = safe_join(BASE_DIR, str(path_str))
        if err:
            return {"error": err}
        safe, reason = is_safe_path(target)
        if not safe:
            return {"error": reason}
        if not target.exists() or not target.is_dir():
            return {"error": f"Директория не найдена: {path_str}"}

        try:
            entries = []
            for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                safe_entry, _ = is_safe_path(entry)
                if not safe_entry:
                    continue
                if entry.is_dir():
                    entries.append(f"{entry.name}/")
                else:
                    size = entry.stat().st_size
                    s = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB"
                    entries.append(f"{entry.name} ({s})")
            output = "\n".join(entries) if entries else "(пустая директория)"
            from subagents.core.memory import clip
            return {"result": clip(output, MAX_DIR_LIST_CHARS)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "read_file":
        path_str = args.get("path", "")
        if not path_str:
            return {"error": "Не указан путь"}
        target, err = safe_join(BASE_DIR, str(path_str))
        if err:
            return {"error": err}
        safe, reason = is_safe_path(target)
        if not safe:
            return {"error": reason}
        if not target.exists() or not target.is_file():
            return {"error": f"Файл не найден: {path_str}"}

        try:
            fd_flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                fd_flags |= os.O_NOFOLLOW
            fd = os.open(target, fd_flags)
            try:
                size = os.fstat(fd).st_size
                if size > MAX_FILE_SIZE:
                    return {"error": "Файл слишком большой"}
                with os.fdopen(fd, "rb") as fh:
                    raw = fh.read(MAX_FILE_READ_CHARS + 1)
            except Exception:
                os.close(fd)
                raise
            content = raw.decode("utf-8", errors="replace")
            from subagents.core.memory import clip
            return {"result": clip(content, MAX_FILE_READ_CHARS)}
        except OSError as e:
            return {"error": f"Не удалось прочитать файл: {e.strerror or e}"}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Неизвестный инструмент: {tool_name}"}