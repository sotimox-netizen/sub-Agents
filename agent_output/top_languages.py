import json
import os

OUTPUT_DIR = "agent_output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "top_languages.json")

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

# 1. Save to JSON
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# 2. Print table
def print_table(title, rows):
    headers = ["Язык", "Рейтинг", "Изменение"]
    widths = [
        max(len(h) for h in headers),
        max(len(str(r["rating"])) for r in rows),
        max(len(str(r["change"])) for r in rows),
    ]
    # ensure headers fit
    widths = [max(w, len(h)) for w, h in zip(widths, headers)]

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(values):
        return "| " + " | ".join(str(v).ljust(w) for v, w in zip(values, widths)) + " |"

    # Section title centered
    total_width = sum(widths) + 3 * 3 + 1  # sum of widths + 3 separators + 1
    print(border)
    print("| " + title.center(total_width - 4) + " |")
    print(border)
    print(line(headers))
    print(border)
    for r in rows:
        print(line([r["name"], r["rating"], r["change"]]))
    print(border)
    print()

print_table("TIOBE", data["tiobe"])
print_table("PYPL", data["pypl"])
