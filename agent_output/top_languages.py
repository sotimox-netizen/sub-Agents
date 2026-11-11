import json
import os

# Данные о топ-3 языках программирования
data = {
    "tiobe": [
        {"name": "Python", "rating": 23.5, "change": "+2.4"},
        {"name": "C++", "rating": 10.3, "change": "+0.8"},
        {"name": "C", "rating": 9.8, "change": "-1.2"},
    ],
    "pypl": [
        {"name": "Python", "rating": 29.6, "change": "-"},
        {"name": "JavaScript", "rating": 16.7, "change": "-"},
        {"name": "Java", "rating": 15.3, "change": "-"},
    ],
}

# 1. Сохранение в JSON
os.makedirs("agent_output", exist_ok=True)
with open(os.path.join("agent_output", "top_languages.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# 2. Вывод красивых таблиц
def print_table(title, rows):
    headers = ["Язык", "Рейтинг", "Изменение"]
    # Ширины столбцов: название языка, рейтинг, изменение
    name_w = max(len(h) for h in ["Язык"] + [str(r["name"]) for r in rows])
    rating_w = max(len("Рейтинг"), max(len(f"{r['rating']:.1f}") for r in rows))
    change_w = max(len("Изменение"), max(len(str(r["change"])) for r in rows))

    border = "+" + "-" * (name_w + 2) + "+" + "-" * (rating_w + 2) + "+" + "-" * (change_w + 2) + "+"

    print(border)
    print(f"| {title.center(name_w + rating_w + change_w + 4)} |")
    print(border)

    # Шапка
    print(f"| {'Язык'.ljust(name_w)} | {'Рейтинг'.ljust(rating_w)} | {'Изменение'.ljust(change_w)} |")
    print(border)

    # Строки данных
    for r in rows:
        print(
            f"| {r['name'].ljust(name_w)} | "
            f"{f'{r['rating']:.1f}'.ljust(rating_w)} | "
            f"{str(r['change']).ljust(change_w)} |"
        )
    print(border)
    print()

print_table("TIOBE Index — Top 3", data["tiobe"])
print_table("PYPL Index — Top 3", data["pypl"])
