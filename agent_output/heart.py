

import sys


def heart_shape(x: float, y: float) -> bool:
    """Возвращает True, если точка (x, y) лежит внутри сердца."""
    return (x**2 + y**2 - 1) ** 3 - x**2 * y**3 <= 0


def draw_heart(width: int = 60, height: int = 30, symbol: str = "\u2665") -> None:
    """
    Печатает сердце в консоль.

    Параметры:
        width  — количество столбцов (символов в строке).
        height — количество строк.
        symbol — символ, которым рисуется сердце.
    """
    # Границы области отображения.
    # Сердце «живёт» примерно в диапазоне x ∈ [-1.3, 1.3], y ∈ [-1.3, 1.6].
    x_min, x_max = -1.3, 1.3
    y_min, y_max = -1.3, 1.6

    for row in range(height):
        # y идёт сверху вниз: верх строки — это больший y.
        y = y_max - (y_max - y_min) * row / (height - 1)
        line = []
        for col in range(width):
            x = x_min + (x_max - x_min) * col / (width - 1)
            line.append(symbol if heart_shape(x, y) else " ")
        print("".join(line))


def _safe_print(text: str) -> None:
    """Печатает текст, перекодируя его под возможности текущей консоли."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Если консоль не поддерживает символ сердца, заменяем его на «#».
        print(text.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    # Перенаправляем stdout в кодировку с поддержкой замены символов,
    # чтобы избежать UnicodeEncodeError в консолях с cp1251 и т.п.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    # Если консоль явно не поддерживает символ сердца, используем «#».
    try:
        "\u2665".encode(sys.stdout.encoding or "ascii")
        symbol = "\u2665"
    except (UnicodeEncodeError, LookupError):
        symbol = "#"

    draw_heart(symbol=symbol)
