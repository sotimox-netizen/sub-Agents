from openai import OpenAI  # noqa: F401  (используется в config.py)

# Ключ берём из окружения / .env (см. config.py), а не из текстового файла.
from subagents.core.config import client  # использует OPENAI_API_KEY / OPENAI_BASE_URL

print("Отправляем запрос к провайдеру...")

try:
    r = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": "Скажи 'Работает!'"}],
        max_tokens=10
    )
    print(f"УСПЕХ! Ответ: {r.choices[0].message.content}")
except Exception as e:
    print(f"ОШИБКА: {e}")
    print("Проверь, точно ли модель называется 'deepseek-v4-pro' в твоем лоте.")