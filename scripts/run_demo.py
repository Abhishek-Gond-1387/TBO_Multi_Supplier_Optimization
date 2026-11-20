"""Start and supervise the local Delhi discovery demo on Windows or other desktops."""

from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
API_PORT = 8000
WEB_PORT = 5500
API_HEALTH_URL = f"http://{HOST}:{API_PORT}/api/v1/health"
LANDING_URL = f"http://{HOST}:{WEB_PORT}/index.html"
MAP_URL = f"http://{HOST}:{WEB_PORT}/map_view.html"
LOG_DIR = ROOT / ".demo-logs"


class DemoStartupError(RuntimeError):
    """Raised when a required demo process cannot become ready."""


def fetch(url: str, timeout: float = 0.8) -> int | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status
    except (OSError, urllib.error.URLError):
        return None


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.3)
        return probe.connect_ex((HOST, port)) == 0


def log_tail(path: Path, lines: int = 18) -> str:
    if not path.exists():
        return "(No server log was created.)"
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError as exc:
        return f"(Could not read {path.name}: {exc})"


def start_service(
    name: str,
    url: str,
    port: int,
    command: list[str],
    env: dict[str, str],
    log_path: Path,
) -> subprocess.Popen[bytes] | None:
    if fetch(url) == 200:
        print(f"{name}: already responding at {url}")
        return None
    if port_is_open(port):
        raise DemoStartupError(
            f"Port {port} is already occupied, but it did not serve the expected demo URL:\n"
            f"  {url}\nClose the other app using port {port}, then run run_demo.bat again."
        )

    log_file = log_path.open("wb")
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    finally:
        log_file.close()

    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise DemoStartupError(
                f"{name} exited during startup. Recent log output from {log_path}:\n{log_tail(log_path)}"
            )
        if fetch(url) == 200:
            print(f"{name}: ready at {url}")
            return process
        time.sleep(0.4)

    stop_service(process)
    raise DemoStartupError(
        f"{name} did not become ready at {url} within 25 seconds.\n"
        f"Recent log output from {log_path}:\n{log_tail(log_path)}"
    )


def stop_service(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def ensure_env_file() -> None:
    env_path = ROOT / ".env"
    example_path = ROOT / ".env.example"
    if not env_path.exists():
        shutil.copyfile(example_path, env_path)
        print("Created .env from .env.example (local-only; it is ignored by Git).")


def main() -> int:
    missing = [
        module
        for module in (
            "fastapi",
            "uvicorn",
            "requests",
            "pydantic",
            "dotenv",
            "httpx",
            "rapidfuzz",
            "prometheus_client",
        )
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        print(f"Missing packages in this Python environment: {', '.join(missing)}")
        print("Run run_demo.bat from the repository folder so it can install requirements.txt.")
        return 1

    ensure_env_file()
    LOG_DIR.mkdir(exist_ok=True)
    demo_env = os.environ.copy()
    # The quickstart is intentionally self-contained and uses the bundled JSON data.
    demo_env.update(
        {
            "USE_DATABASE": "false",
            "USE_REDIS": "false",
            "ENABLE_CELERY": "false",
            "CORS_ORIGINS": f"http://{HOST}:{WEB_PORT},http://localhost:{WEB_PORT}",
        }
    )

    api_process: subprocess.Popen[bytes] | None = None
    web_process: subprocess.Popen[bytes] | None = None
    try:
        api_process = start_service(
            "API",
            API_HEALTH_URL,
            API_PORT,
            [sys.executable, "-m", "uvicorn", "services.main:app", "--host", HOST, "--port", str(API_PORT)],
            demo_env,
            LOG_DIR / "api.log",
        )
        web_process = start_service(
            "Frontend",
            MAP_URL,
            WEB_PORT,
            [
                sys.executable,
                "-m",
                "http.server",
                str(WEB_PORT),
                "--bind",
                HOST,
                "--directory",
                str(ROOT / "frontend"),
            ],
            demo_env,
            LOG_DIR / "frontend.log",
        )

        print("\nTBO Multi-Supplier Travel Intelligence Platform is ready:")
        print(f"  Landing Page: http://{HOST}:{WEB_PORT}/index.html")
        print(f"  Google Map:   http://{HOST}:{WEB_PORT}/map_view.html")
        print(f"  Admin Hub:    http://{HOST}:{WEB_PORT}/admin.html")
        print(f"  API docs:     http://{HOST}:{API_PORT}/docs")
        print("  Inventory:    560+ live hotels & sightseeing experiences with competitive multi-supplier rates.")
        print("  Features:     Google Maps styling, real-time autocomplete, voice search, room normalization & inclusion diffs.")
        print("\nOpening the landing page in your browser...")
        webbrowser.open_new_tab(LANDING_URL)
        demo_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "demo.py")],
            cwd=ROOT,
            env=demo_env,
            check=False,
        )
        if demo_result.returncode != 0:
            print("The browser map is running, but the terminal walkthrough failed.")
        print("\nKeep this window open while using the demo. Press Ctrl+C here to stop services started by this launcher.")
        while True:
            for name, process in (("API", api_process), ("Frontend", web_process)):
                if process is not None and process.poll() is not None:
                    log_path = LOG_DIR / ("api.log" if name == "API" else "frontend.log")
                    raise DemoStartupError(
                        f"{name} stopped unexpectedly. Recent log output:\n{log_tail(log_path)}"
                    )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping demo services started by this launcher...")
        return 0
    except DemoStartupError as exc:
        print(f"\nDemo startup error:\n{exc}")
        return 1
    finally:
        stop_service(web_process)
        stop_service(api_process)


if __name__ == "__main__":
    raise SystemExit(main())
