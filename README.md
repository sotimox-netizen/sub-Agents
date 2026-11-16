# SubAgents

Мультиагентный оркестратор (LLM + инструменты).

## Структура проекта

```
main.py                  # точка входа
config.json              # конфиг агентов (содержит секреты, не коммитить ключи!)
.env                     # переменные окружения (в .gitignore)
subagents/
  core/                  # ядро приложения
    config.py            # загрузка настроек, клиента OpenAI, BASE_DIR
    agent.py             # цикл оркестратора и сабагенты
    tools.py             # инструменты (поиск, файлы, python-песочница)
    memory.py            # история сессии и обрезка контекста
  security/              # компоненты безопасности
    pathguard.py         # безопасная работа с путями (защита от traversal)
    sandbox.py           # изолированное выполнение Python-кода
  tests/                 # вспомогательные скрипты/тесты
```

## Запуск

```bash
pip install openai rich ddgs
export OPENAI_API_KEY=...   # или заполните .env по примеру .env.example
python main.py
```

## Сборка exe (PyInstaller)

```bash
pyinstaller SubAgents.spec
```
