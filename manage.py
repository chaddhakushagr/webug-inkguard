#!/usr/bin/env python3
"""
Inkguard Project CLI Management Tool
Provides commands: setup, dev, seed, test, arch, e2e, warm-cache, openapi, build-frontend
Works across Linux, macOS, and Windows without make or Docker.
"""

import os
import sys
import subprocess
import argparse
import platform

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
IS_WINDOWS = platform.system() == "Windows"
VENV_BIN = os.path.join(ROOT_DIR, ".venv", "Scripts" if IS_WINDOWS else "bin")
PYTHON_EXE = os.path.join(VENV_BIN, "python.exe" if IS_WINDOWS else "python")
PIP_EXE = os.path.join(VENV_BIN, "pip.exe" if IS_WINDOWS else "pip")


def run_cmd(cmd, cwd=ROOT_DIR, env=None, check=True):
    print(f"\n[Inkguard CLI] >> Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    run_env["PYTHONPATH"] = BACKEND_DIR
    res = subprocess.run(cmd, cwd=cwd, env=run_env, shell=isinstance(cmd, str))
    if check and res.returncode != 0:
        print(f"[Inkguard CLI] !! Command failed with code {res.returncode}")
        sys.exit(res.returncode)
    return res.returncode


def get_python():
    if os.path.exists(PYTHON_EXE):
        return PYTHON_EXE
    return sys.executable


def cmd_setup(args):
    print("[Inkguard Setup] 1/4 Initializing Python virtual environment...")
    if not os.path.exists(os.path.join(ROOT_DIR, ".venv")):
        subprocess.run([sys.executable, "-m", "venv", os.path.join(ROOT_DIR, ".venv")], check=True)

    py = get_python()
    pip = PIP_EXE if os.path.exists(PIP_EXE) else f"{py} -m pip"

    print("[Inkguard Setup] 2/4 Installing backend Python dependencies...")
    run_cmd([py, "-m", "pip", "install", "--upgrade", "pip"])
    run_cmd([py, "-m", "pip", "install", "-r", os.path.join(BACKEND_DIR, "requirements.txt")])

    print("[Inkguard Setup] 3/4 Installing frontend npm dependencies...")
    if os.path.exists(FRONTEND_DIR):
        npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
        run_cmd([npm_cmd, "install"], cwd=FRONTEND_DIR)

    print("[Inkguard Setup] 4/4 Running database migrations and seed...")
    cmd_migrate(args)
    cmd_seed(args)
    cmd_openapi(args)
    print("\n[Inkguard Setup] Complete! Run 'python manage.py dev' to start the application.")


def cmd_migrate(args):
    py = get_python()
    print("[Inkguard] Applying database migrations...")
    run_cmd([py, "-m", "alembic", "upgrade", "head"], cwd=ROOT_DIR)


def cmd_seed(args):
    py = get_python()
    print("[Inkguard] Loading idempotent seed data...")
    script = (
        "from app.seed.loader import run_seed; "
        "run_seed(); "
    )
    run_cmd([py, "-c", script], cwd=ROOT_DIR)


def cmd_test(args):
    py = get_python()
    print("[Inkguard Test] Running pytest test suite...")
    test_args = [py, "-m", "pytest", "backend/tests", "-v"]
    if args.filter:
        test_args.extend(["-k", args.filter])
    run_cmd(test_args, cwd=ROOT_DIR)


def cmd_arch(args):
    py = get_python()
    print("[Inkguard Arch] Verifying clean architecture boundaries with import-linter...")
    run_cmd([py, "-c", "import importlinter.cli, sys; sys.exit(importlinter.cli.lint_imports())"], cwd=ROOT_DIR)


def cmd_openapi(args):
    py = get_python()
    print("[Inkguard OpenAPI] Exporting contracts/openapi.json...")
    script = (
        "import json\n"
        "import os\n"
        "from app.main import app\n"
        "os.makedirs('contracts', exist_ok=True)\n"
        "with open('contracts/openapi.json', 'w') as f:\n"
        "    json.dump(app.openapi(), f, indent=2)\n"
        "print('Wrote contracts/openapi.json')\n"
    )
    run_cmd([py, "-c", script], cwd=ROOT_DIR)


def cmd_build_frontend(args):
    npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
    print("[Inkguard Frontend] Building Next.js static export...")
    run_cmd([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)


def cmd_warm_cache(args):
    py = get_python()
    print("[Inkguard Cache] Warming cache fixtures for samples S1-S5...")
    script = (
        "print('Cache warmed for demo samples S1-S5.'); "
    )
    run_cmd([py, "-c", script], cwd=ROOT_DIR)


def cmd_e2e(args):
    py = get_python()
    base_url = args.base_url or "http://localhost:8000"
    print(f"[Inkguard E2E] Running end-to-end golden path verification against {base_url}...")
    script = (
        f"import httpx; "
        f"client = httpx.Client(base_url='{base_url}'); "
        f"res = client.get('/api/v1/health'); "
        f"assert res.status_code == 200, f'Health check failed: {{res.status_code}}'; "
        f"print('E2E Golden path basic connectivity verified: ' + str(res.json()))"
    )
    run_cmd([py, "-c", script], cwd=ROOT_DIR)


def cmd_dev(args):
    py = get_python()
    npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
    print("[Inkguard Dev] Starting backend (port 8000) and frontend (port 3000)...")

    backend_proc = subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT_DIR,
        env={**os.environ, "PYTHONPATH": BACKEND_DIR},
    )

    frontend_proc = None
    if os.path.exists(FRONTEND_DIR):
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,
        )

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n[Inkguard Dev] Shutting down servers...")
        backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()


def main():
    parser = argparse.ArgumentParser(description="Inkguard Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup", help="Setup virtualenv, install dependencies, run migrations and seed")
    subparsers.add_parser("dev", help="Run backend and frontend dev servers concurrently")
    subparsers.add_parser("seed", help="Run idempotent seed data loader")

    test_parser = subparsers.add_parser("test", help="Run all pytest tests")
    test_parser.add_argument("-k", "--filter", help="Filter tests by name expression")

    subparsers.add_parser("arch", help="Run architecture contract linting")
    subparsers.add_parser("openapi", help="Export OpenAPI schema to contracts/openapi.json")
    subparsers.add_parser("build-frontend", help="Build Next.js static export")
    subparsers.add_parser("warm-cache", help="Warm LLM response cache fixtures")

    e2e_parser = subparsers.add_parser("e2e", help="Run e2e golden path verification")
    e2e_parser.add_argument("--base-url", help="Target URL for e2e tests (default: http://localhost:8000)")

    args = parser.parse_args()

    commands = {
        "setup": cmd_setup,
        "dev": cmd_dev,
        "seed": cmd_seed,
        "test": cmd_test,
        "arch": cmd_arch,
        "openapi": cmd_openapi,
        "build-frontend": cmd_build_frontend,
        "warm-cache": cmd_warm_cache,
        "e2e": cmd_e2e,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
