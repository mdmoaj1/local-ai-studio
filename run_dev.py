import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

BACKEND_DIR = ROOT / "apps" / "backend"
FRONTEND_DIR = ROOT / "apps" / "frontend"

VENV_DIR = BACKEND_DIR / "venv"


# -------------------------
# helpers
# -------------------------

def run(cmd, cwd=None):
    print(f"\n>>> {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd)


# -------------------------
# create folders
# -------------------------

def create_dirs():
    dirs = [
        ROOT / "models",
        ROOT / "datasets",
        ROOT / "voices",
        ROOT / "outputs",
        ROOT / "outputs" / "audio",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# -------------------------
# venv
# -------------------------

def create_venv():
    if not VENV_DIR.exists():
        print("Creating venv...")
        run(f"{sys.executable} -m venv venv", cwd=BACKEND_DIR)


def pip():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "pip")
    else:
        return str(VENV_DIR / "bin" / "pip")


def python():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python")
    else:
        return str(VENV_DIR / "bin" / "python")


# -------------------------
# install backend
# -------------------------

def install_backend():
    print("Installing backend requirements...")
    run(f"{pip()} install -r requirements.txt", cwd=BACKEND_DIR)


# -------------------------
# install frontend
# -------------------------

def install_frontend():
    print("Installing frontend npm...")
    run("npm install", cwd=FRONTEND_DIR)


# -------------------------
# run backend
# -------------------------

def start_backend():
    print("Starting backend...")

    return subprocess.Popen(
        [
            python(),
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--port",
            "8000",
        ],
        cwd=BACKEND_DIR,
    )


# -------------------------
# run frontend
# -------------------------

def start_frontend():
    print("Starting frontend...")

    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
    )


# -------------------------
# main
# -------------------------

def main():
    create_dirs()
    create_venv()
    install_backend()
    install_frontend()

    backend = start_backend()
    frontend = start_frontend()

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("Stopping...")
        backend.terminate()
        frontend.terminate()


if __name__ == "__main__":
    main()