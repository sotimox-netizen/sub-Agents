"""Безопасные операции с путями: whitelist-подход вместо чёрных списков подстрок.

Главное правило: никогда не доверяем «сырой» строке пути от LLM. Путь
канонизируется (resolve) и проверяется на принадлежность разрешённой
директории; имена файлов дополнительно очищаются от разделителей и «..».
"""

from pathlib import Path


def safe_join(base: Path, *parts: str) -> tuple[Path | None, str]:
    """Безопасно соединяет base и parts. Возвращает (path, error).

    - Отказывается от абсолютных путей и путей с escape через '..'.
    - Проверяет уже разрешённый (resolve) путь внутри base.
    """
    base = base.resolve()
    try:
        target = (base.joinpath(*[str(p) for p in parts])).resolve()
    except Exception as e:
        return None, f"Некорректный путь: {e}"

    if target != base and base not in target.parents:
        return None, f"Путь выходит за пределы {base}"
    return target, ""


def safe_filename(filename: str) -> tuple[str, str]:
    """Превращает имя файла от LLM в безопасное простое имя.

    Убираются пути, управляющие символы; запрещены '..', скрытые файлы
    и недопустимые символы. Возвращает (clean_name, error).
    """
    if not isinstance(filename, str) or not filename.strip():
        return "", "Пустое имя файла"

    name = filename.strip().replace("\\", "/").split("/")[-1]  # только базовое имя

    if name in ("", ".", ".."):
        return "", f"Недопустимое имя: {filename!r}"
    if name.startswith("."):
        return "", f"Скрытые файлы запрещены: {filename!r}"
    bad_chars = set('<>:"|?*\x00') | set(chr(c) for c in range(32))
    if any(ch in name for ch in bad_chars):
        return "", f"Недопустимые символы в имени: {filename!r}"
    if len(name) > 128:
        return "", "Имя файла слишком длинное"
    return name, ""
