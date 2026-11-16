"""Изолированный песочный execution-хост для выполнения Python-кода.

Код, полученный от LLM, НЕ выполняется через exec() в основном процессе.
Вместо этого он запускается в отдельном дочернем процессе с:
  - жёстким таймаутом;
  - лимитом памяти (через resource.setrlimit внутри дочернего процесса);
  - ограничением размера вывода;
  - рабочим каталогом = изолированная temp-папка (не проект).

Это не полная защита от determined attacker (для этого нужны контейнеры/железные
песочницы), но полностью устраняет RCE в основном процессе приложения:
краш, бесконечный цикл или утечка памяти в коде LLM больше не затрагивают
интерпретатор агента.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Скрипт-обёртка, запускаемая в дочернем процессе.
_CHILD_SRC = r"""
import sys, json, io, contextlib

MAX_OUTPUT = int(sys.argv[1])
MEM_LIMIT = int(sys.argv[2])
TIME_LIMIT = int(sys.argv[3])
PAYLOAD_FD = int(sys.argv[4])

try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))
    resource.setrlimit(resource.RLIMIT_CPU, (TIME_LIMIT, TIME_LIMIT))
except Exception:
    pass  # Windows / недоступно

code = sys.stdin.buffer.read().decode("utf-8", errors="replace")

ns = {"__name__": "__sandbox__"}
buf = io.StringIO()
status = "ok"
try:
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<llm_code>", "exec"), ns)
except BaseException as e:
    status = f"{type(e).__name__}: {e}"

result = ""
if "result" in ns:
    try:
        result = repr(ns["result"])
    except Exception:
        result = "<not representable>"

out = buf.getvalue()[:MAX_OUTPUT]
sys.stdout.flush()
payload = json.dumps({"status": status, "stdout": out, "result": result}, ensure_ascii=False)
# Пишем payload в служебный fd (pipe), чтобы не смешивать с stdout кода
import os
os.write(PAYLOAD_FD, payload.encode("utf-8"))
"""


def run_python_sandboxed(code: str, timeout: int = 10, max_output: int = 4000,
                         mem_limit_mb: int = 256) -> dict:
    """Выполняет код LLM в изолированном дочернем процессе. Возвращает dict-результат."""
    if not isinstance(code, str) or not code.strip():
        return {"error": "Пустой код"}

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.pop("OPENAI_API_KEY", None)  # не передаём секреты в песочницу

    with tempfile.TemporaryDirectory(prefix="agent_sandbox_") as tmpdir:
        child_script = Path(tmpdir) / "_runner.py"
        child_script.write_text(_CHILD_SRC, encoding="utf-8")

        r_fd, w_fd = os.pipe()
        # pass_fds сохраняет номер fd в дочернем процессе — передаём его чайлду.
        try:
            proc = subprocess.Popen(
                [sys.executable, "-I", "-s", str(child_script),
                 str(max_output), str(mem_limit_mb * 1024 * 1024),
                 str(timeout), str(w_fd)],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,   # print()-вывод кода перехватывается в буфер внутри чайлда
                stderr=subprocess.PIPE,
                pass_fds=(w_fd,),
                cwd=tmpdir,
                env=env,
            )
        finally:
            os.close(w_fd)  # родительский copy — закрываем сразу

        try:
            try:
                stdout_data, stderr_data = proc.communicate(
                    input=code.encode("utf-8"), timeout=timeout + 5
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return {"error": f"Таймаут выполнения ({timeout}с)"}

            # Читаем payload из pipe до EOF (закрыто вместе со смертью чайлда).
            chunks = []
            while True:
                chunk = os.read(r_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(r_fd)

        try:
            import json as _json
            payload = _json.loads(raw.decode("utf-8"))
        except Exception:
            err = (stderr_data or b"").decode("utf-8", errors="replace")[:max_output]
            if proc.returncode and proc.returncode < 0:
                return {"error": f"Процесс убит (возможно превышен лимит ресурсов). {err}".strip()}
            return {"error": f"Песочница завершилась с кодом {proc.returncode}. {err}".strip()}

    status = payload.get("status", "ok")
    out = payload.get("stdout", "")
    res = payload.get("result", "")
    parts = []
    if out:
        parts.append(out)
    if res:
        parts.append(f"result = {res}")
    if status != "ok":
        return {"error": status, "output": "\n".join(parts)}
    return {"output": "\n".join(parts) if parts else "OK (нет вывода)"}
