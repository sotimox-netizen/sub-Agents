import json
from config import console, MAX_CONTEXT_CHARS, MAX_TOOL_RESULT_CHARS


# История сессии (только в RAM)
session_history = []


def clip(text: str, limit: int) -> str:
    """Обрезает текст до лимита."""
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[ОБРЕЗАНО: было {len(text)} символов]"


def _msg_chars(m: dict) -> int:
    """Размер одного сообщения в символах."""
    c = m.get("content") or ""
    if not isinstance(c, str):
        c = json.dumps(c, ensure_ascii=False)
    s = len(c)
    if m.get("tool_calls"):
        s += len(json.dumps(m["tool_calls"], ensure_ascii=False))
    return s


def trim_working_messages(messages: list) -> list:
    """
    Обрезает messages так, чтобы их суммарный размер не превышал MAX_CONTEXT_CHARS.
    Сохраняет системное сообщение и текущую задачу, удаляет старую историю.
    """
    if sum(_msg_chars(m) for m in messages) <= MAX_CONTEXT_CHARS:
        return messages

    system = messages[0] if messages and messages[0].get("role") == "system" else None
    body = messages[1:] if system else list(messages)

    # Индекс последнего user-сообщения (текущая задача)
    last_user = 0
    for i, m in enumerate(body):
        if m.get("role") == "user":
            last_user = i
    head = body[:last_user]  # старая история
    tail = body[last_user:]  # текущая задача + шаги

    def size():
        return sum(_msg_chars(m) for m in ([system] if system else []) + head + tail)

    # Удаляем старую историю парами
    while head and size() > MAX_CONTEXT_CHARS:
        del head[0:2]

    # Удаляем старые блоки шагов агента
    while size() > MAX_CONTEXT_CHARS and len(tail) > 1:
        cut = None
        for i in range(1, len(tail)):
            if tail[i].get("role") == "assistant":
                cut = i
                break
        if cut is None:
            break
        end = cut + 1
        while end < len(tail) and tail[end].get("role") == "tool":
            end += 1
        del tail[cut:end]

    return ([system] if system else []) + head + tail