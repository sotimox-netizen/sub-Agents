from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from agent import run_agent_loop, SUBAGENTS
from memory import session_history

console = Console()


if __name__ == "__main__":
    console.print(Panel.fit("[bold cyan]🤖 Мультиагентный оркестратор[/]", border_style="blue"))
    console.print("[dim]Команды: 'выход' — закрыть, '/reset' — очистить контекст[/]")

    while True:
        try:
            task = console.input("\n[bold green]📋 Задача:[/] ").strip()
            if not task:
                continue
            if task.lower() in ['выход', 'exit', 'quit']:
                console.print("[yellow]Пока![/]")
                break
            if task.lower() == '/reset':
                session_history.clear()
                console.print("[yellow]🧹 Контекст очищен[/]")
                continue

            final = run_agent_loop(agent_id=None, task=task, is_supervisor=True, depth=0)
            console.print("\n")
            console.print(Panel(Markdown(final), title="🏁 ОТЧЁТ", border_style="green"))

        except KeyboardInterrupt:
            console.print("\n[yellow]Прервано[/]")
            break
        except Exception as e:
            console.print(f"[bold red]❌ Ошибка: {e}[/]")