from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from agent import run_agent_loop, SUBAGENTS
from memory import session_history
print("версия 1.3")

console = Console()


if __name__ == "__main__":
    console.print(Panel.fit("Мультиагентный оркестратор", border_style="white"))
    console.print("Команды: 'выход' — закрыть, '/reset' — очистить контекст")

    while True:
        try:
            task = console.input("\nЗадача: ").strip()
            if not task:
                continue
            if task.lower() in ['выход', 'exit', 'quit']:
                console.print("Пока!")
                break
            if task.lower() == '/reset':
                session_history.clear()
                console.print("Контекст очищен")
                continue

            final = run_agent_loop(agent_id=None, task=task, is_supervisor=True, depth=0)
            console.print("\n")
            console.print(Panel(Markdown(final), title="ОТЧЁТ", border_style="green"))

        except KeyboardInterrupt:
            console.print("\nПрервано")
            break
        except Exception as e:
            console.print(f"Ошибка: {e}", markup=False)