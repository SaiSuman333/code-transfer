"""
run.py — Start both the FastAPI backend and Streamlit frontend.
Usage: python run.py
"""
import subprocess
import sys
import os
import signal
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


BACKEND_PORT = 8080
FRONTEND_PORT = 8501


def wait_for_backend(port: int, timeout: int = 15) -> bool:
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def free_port(port: int) -> None:
    """Kill any process currently using the given port."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
             f"Select-Object -ExpandProperty OwningProcess | "
             f"Sort-Object -Unique | "
             f"ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass


def main():
    print("Starting Explain My Data...")
    print(f"Backend:  http://localhost:{BACKEND_PORT}")
    print(f"Frontend: http://localhost:{FRONTEND_PORT}")
    print("Press Ctrl+C to stop.\n")

    # Free ports if already in use
    free_port(BACKEND_PORT)
    free_port(FRONTEND_PORT)
    time.sleep(1)

    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "127.0.0.1",
            "--port", str(BACKEND_PORT),
            "--reload",
        ],
        cwd=BASE_DIR,
    )

    print("Waiting for backend to start...", end="", flush=True)
    if not wait_for_backend(BACKEND_PORT):
        print("\nERROR: Backend failed to start. Check if the port is available.")
        backend.terminate()
        return
    print(" ready!")

    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run",
                os.path.join(BASE_DIR, "frontend", "app.py"),
                "--server.port", str(FRONTEND_PORT),
                "--server.address", "localhost",
            ],
            cwd=BASE_DIR,
        )
    except KeyboardInterrupt:
        pass
    finally:
        backend.terminate()
        backend.wait()
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()
