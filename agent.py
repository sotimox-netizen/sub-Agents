import json
import time
from pathlib import Path
from config import console, client, BASE_DIR, MAX_TOOL_RESULT_CHARS, MAX_SUB_RESULT_CHARS, MAX_HISTORY_TURNS
from memory import session_history, clip, trim_working_messages
from tools import execute_subagent_tool

# Загрузка конфига
CONFIG_PATH = BASE_DIR / "config.json"
if not CONFIG_PATH.exists():
    console.print(f"[red]❌ Не найден {CONFIG_PATH}[/]")
    exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

console.print(f"[green]✅ Конфиг загружен: {CONFIG_PATH}[/]")

# Определение инструментов для субагентов (остаются в коде, так как связаны с логикой)
AGENT_TOOLS = {
    "researcher": [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Поиск информации в интернете",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос"}
                    },
                    "required": ["query"]
                }
            }
        }
    ],
    "coder": [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "Показывает содержимое директории проекта. Для корня передай path='.'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Относительный путь, например '.' или 'agent_output'"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Читает содержимое текстового файла из проекта.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Относительный путь к файлу"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_to_file",
                "description": "Сохраняет код в файл внутри папки agent_output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Имя файла с расширением .py"},
                        "code": {"type": "string", "description": "Полный код для сохранения"}
                    },
                    "required": ["filename", "code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_code",
                "description": "Выполняет Python код и возвращает результат.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python код для выполнения"}
                    },
                    "required": ["code"]
                }
            }
        }
    ],
    "writer": []
}

# Формируем SUBAGENTS из конфига + инструментов
SUBAGENTS = {}
for agent_id, agent_config in CONFIG.get("agents", {}).items():
    SUBAGENTS[agent_id] = {
        "name": agent_config.get("name", agent_id),
        "color": agent_config.get("color", "blue"),
        "system_prompt": agent_config.get("system_prompt", ""),
        "tools": AGENT_TOOLS.get(agent_id, [])
    }

console.print(f"[green]Загружено агентов: {len(SUBAGENTS)}[/]")


def create_completion_with_retry(max_retries=5, **kwargs):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            if hasattr(response, 'usage'):
                console.print(f"    [dim]Токенов: {response.usage.total_tokens}[/]")
            return response
        except Exception as e:
            err = str(e)
            if "429" in err or "rate limit" in err.lower():
                if attempt < max_retries - 1:
                    wait = 60
                    console.print(f"    [yellow]Rate limit, ждём {wait}с...[/]")
                    time.sleep(wait)
                    continue
            raise
    raise Exception("Не удалось выполнить запрос")


def _build_supervisor_tools():
    tools = []
    for agent_id, cfg in SUBAGENTS.items():
        tools.append({
            "type": "function",
            "function": {
                "name": f"delegate_to_{agent_id}",
                "description": f"Делегировать задачу агенту '{cfg['name']}'. {cfg['system_prompt'][:120]}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Чёткое ТЗ для субагента"}
                    },
                    "required": ["task"]
                }
            }
        })
    return tools


def run_agent_loop(agent_id: str, task: str, is_supervisor: bool = False, depth: int = 0) -> str:
    agent = SUBAGENTS.get(agent_id)
    indent = "  " * depth
    color = agent["color"] if agent else "blue"
    name = agent["name"] if agent else "Супервизор"

    console.print(f"{indent}[bold {color}]▶ {name} получил задачу:[/] [dim]{task[:100]}...[/]")

    if is_supervisor:
        working_messages = [
            {"role": "system", "content": CONFIG["supervisor"]["system_prompt"]},
        ]
        working_messages.extend(session_history)
        working_messages.append({"role": "user", "content": task})
        if session_history:
            console.print(f"{indent}[dim]Диалогов в сессии: {len(session_history) // 2}[/]")
    else:
        working_messages = [
            {"role": "system", "content": agent["system_prompt"] if agent else ""},
            {"role": "user", "content": task}
        ]

    tools = _build_supervisor_tools() if is_supervisor else (agent["tools"] if agent else [])
    max_iter = 8 if is_supervisor else 5

    for i in range(max_iter):
        working_messages = trim_working_messages(working_messages)

        request_kwargs = {
            "model": "deepseek-v4-pro",
            "messages": working_messages,
            "max_tokens": 5000,
        }
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = "auto"

        response = create_completion_with_retry(**request_kwargs)
        msg = response.choices[0].message
        msg_dict = msg.model_dump()
        msg_dict.pop("annotations", None)
        msg_dict = {k: v for k, v in msg_dict.items() if v is not None}
        working_messages.append(msg_dict)

        if not msg.tool_calls:
            console.print(f"{indent}[bold {color}]✓ {name} завершил работу[/]")
            final_content = msg.content or ""
            if is_supervisor:
                session_history.append({"role": "user", "content": task[:400]})
                session_history.append({"role": "assistant", "content": final_content[:1500]})
                while len(session_history) > MAX_HISTORY_TURNS * 2:
                    del session_history[0:2]
            return final_content

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                working_messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"error": "Невалидный JSON, повтори корректно"}, ensure_ascii=False)
                })
                continue

            available_tools = [t["function"]["name"] for t in tools]
            if fn_name not in available_tools:
                error_msg = (
                    f"Инструмент '{fn_name}' не существует. "
                    f"Доступные инструменты: {', '.join(available_tools)}. "
                    f"Используй только их."
                )
                console.print(f"{indent}    [red]⚠️  {error_msg}[/]")
                working_messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"error": error_msg}, ensure_ascii=False)
                })
                continue

            if is_supervisor and fn_name.startswith("delegate_to_"):
                sub_id = fn_name.replace("delegate_to_", "")
                if sub_id not in SUBAGENTS:
                    working_messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps({"error": f"Агент '{sub_id}' не существует"}, ensure_ascii=False)
                    })
                    continue
                sub_task = fn_args.get("task", "")
                console.print(f"{indent}  [dim cyan]Делегирование → {SUBAGENTS[sub_id]['name']}[/]")
                sub_result = run_agent_loop(sub_id, sub_task, is_supervisor=False, depth=depth + 1)
                working_messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": clip(sub_result, MAX_SUB_RESULT_CHARS)
                })
            else:
                result = execute_subagent_tool(agent_id, fn_name, fn_args, SUBAGENTS)
                payload = json.dumps(result, ensure_ascii=False)
                working_messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": clip(payload, MAX_TOOL_RESULT_CHARS)
                })

    return "[ОШИБКА: Превышен лимит итераций]"