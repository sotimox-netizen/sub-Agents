from pathlib import Path
from openai import OpenAI

key = Path.home().joinpath("Documents", "blablabla.txt").read_text().strip()

client = OpenAI(
    api_key=key,
    base_url="https://api.aikeysforyou.com/v1"
)

print("Отправляем запрос к прокси продавца...")

try:
    r = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": "Скажи 'Работает!'"}],
        max_tokens=10
    )
    print(f"✅ УСПЕХ! Ответ: {r.choices[0].message.content}")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    print("Проверь, точно ли модель называется 'deepseek-v4-pro' в твоем лоте.")