import json
import os

# 1-2. Проверяем/создаём папку agent_output
out_dir = "agent_output"
os.makedirs(out_dir, exist_ok=True)

# 3. Формируем JSON-структуру с обоими рейтингами
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

# 4. Сохраняем в файл
file_path = os.path.join(out_dir, "top_languages.json")
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# 5. Читаем обратно и выводим
with open(file_path, "r", encoding="utf-8") as f:
    content = json.load(f)

print(json.dumps(content, indent=4, ensure_ascii=False))
