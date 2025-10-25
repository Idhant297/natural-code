#!/usr/bin/env python3
"""CLI tool to run natural code files .n<language> files through codex"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Configuration: Set to False to hide codex output
SHOW_CODEX_OUTPUT = True

# Log directory
LOG_DIR = Path(__file__).parent / "cli-logs"

PROMPT_FILE = Path(__file__).parent / "prompt.md"


def read_prompt_file():
    """Read the contents of the prompt file"""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def ensure_log_dir():
    """Create log directory if it doesn't exist"""
    LOG_DIR.mkdir(exist_ok=True)


def get_log_filepath(input_file):
    """Generate log file path based on input file and timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_filename = Path(input_file).stem
    log_filename = f"{input_filename}_{timestamp}.log"
    return LOG_DIR / log_filename


def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(f"Warning: .env file not found at {env_path}", file=sys.stderr)


def read_natural_code_file(filepath):
    """Read the contents of a .n<language> file"""
    import re

    path = Path(filepath)

    if not path.exists():
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)

    # Extract language from .n<lang> extension
    match = re.search(r"\.n(\w+)$", filepath)
    if not match:
        print(
            "Error: File must have .n<language> extension (e.g., .npy, .njava, .njs)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Language extracted but not currently used

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def run_codex(
    prompt, prompt_file, groq_api_key, log_file, show_output=SHOW_CODEX_OUTPUT
):
    """Run codex with the given prompt in the background"""
    if not groq_api_key:
        print("Error: GROQ_API key not found in .env file", file=sys.stderr)
        sys.exit(1)

    # Set up environment with GROQ_API_KEY
    env = os.environ.copy()
    env["GROQ_API_KEY"] = groq_api_key

    # Read the system prompt if it exists
    system_prompt = ""
    if PROMPT_FILE.exists():
        system_prompt = read_prompt_file()

    # Construct the codex command using 'exec' for non-interactive mode
    # Combine system prompt with the natural code file
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n@{prompt_file}"
    else:
        full_prompt = f"@{prompt_file}"

    cmd = [
        "codex",
        "exec",
        "--profile",
        "groq",
        "--model",
        "openai/gpt-oss-120b",
        full_prompt,
    ]

    try:
        # Open log file for writing
        log_handle = open(log_file, "w", encoding="utf-8")

        # Write header to log file
        log_handle.write("=== Codex Execution Log ===\n")
        log_handle.write(f"Timestamp: {datetime.now().isoformat()}\n")
        log_handle.write(
            f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
        )
        log_handle.write(f"{'=' * 50}\n\n")
        log_handle.flush()

        # Determine output streams based on configuration
        if show_output:
            # Use Tee-like behavior: show on terminal AND write to log
            stdout_stream = subprocess.PIPE
            stderr_stream = subprocess.STDOUT
        else:
            # Only write to log file, don't show on terminal
            stdout_stream = log_handle
            stderr_stream = subprocess.STDOUT

        # Run codex in the background
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=stdout_stream,
            stderr=stderr_stream,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        # If showing output, we need to tee the output to both terminal and log file
        if show_output and stdout_stream == subprocess.PIPE:

            def tee_output():
                try:
                    for line in process.stdout:
                        print(line, end="")  # Print to terminal
                        log_handle.write(line)  # Write to log
                        log_handle.flush()
                    log_handle.close()
                except Exception as e:
                    print(f"Error in tee_output: {e}", file=sys.stderr)

            import threading

            tee_thread = threading.Thread(target=tee_output, daemon=True)
            tee_thread.start()

        print(f"Codex process started (PID: {process.pid})")
        print(f"Log file: {log_file}")
        return process.pid

    except FileNotFoundError:
        print(
            "Error: 'codex' command not found. Make sure codex CLI is installed.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running codex: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run natural code files (.npy/.njava) through codex CLI"
    )
    parser.add_argument("file", help="Path to .npy or .njava file")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for codex to complete instead of running in background",
    )

    args = parser.parse_args()

    # Ensure log directory exists
    ensure_log_dir()

    # Load environment variables
    load_env_file()

    # Get GROQ_API key
    groq_api_key = os.getenv("GROQ_API")

    # Validate the natural code file (but don't read it, pass it directly to codex)
    prompt = read_natural_code_file(args.file)

    # Get absolute path to the prompt file
    prompt_file = str(Path(args.file).resolve())

    # Generate log file path
    log_file = get_log_filepath(args.file)

    print(f"Running codex with prompt from {args.file}...")

    # Read system prompt if it exists
    system_prompt = ""
    if PROMPT_FILE.exists():
        system_prompt = read_prompt_file()

    # Construct full prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n@{prompt_file}"
    else:
        full_prompt = f"@{prompt_file}"

    # Run codex
    if args.wait:
        # If --wait flag is used, run synchronously
        env = os.environ.copy()
        env["GROQ_API_KEY"] = groq_api_key

        # Open log file for writing
        with open(log_file, "w", encoding="utf-8") as log_handle:
            # Write header to log file
            log_handle.write("=== Codex Execution Log ===\n")
            log_handle.write(f"Timestamp: {datetime.now().isoformat()}\n")
            log_handle.write(f"Prompt file: {prompt_file}\n")
            if system_prompt:
                log_handle.write(f"System prompt file: {PROMPT_FILE}\n")
            log_handle.write(
                f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
            )
            log_handle.write(f"{'=' * 50}\n\n")
            log_handle.flush()

            # Determine output streams based on configuration
            if SHOW_CODEX_OUTPUT:
                # Show on terminal AND write to log using tee-like behavior
                result = subprocess.run(
                    [
                        "codex",
                        "exec",
                        "--profile",
                        "groq",
                        "--model",
                        "openai/gpt-oss-120b",
                        full_prompt,
                    ],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                # Write to both terminal and log
                print(result.stdout, end="")
                log_handle.write(result.stdout)
            else:
                # Only write to log file, don't show on terminal
                result = subprocess.run(
                    [
                        "codex",
                        "exec",
                        "--profile",
                        "groq",
                        "--model",
                        "openai/gpt-oss-120b",
                        full_prompt,
                    ],
                    env=env,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

        print(f"Log file: {log_file}")

        if result.returncode == 0:
            print("Codex completed successfully")
        else:
            print(f"Codex exited with code {result.returncode}", file=sys.stderr)
            sys.exit(result.returncode)
    else:
        # Run in background
        pid = run_codex(
            prompt, prompt_file, groq_api_key, log_file, show_output=SHOW_CODEX_OUTPUT
        )
        if SHOW_CODEX_OUTPUT:
            print(f"Codex is running in the background (PID: {pid}) - output visible")
        else:
            print(f"Codex is running in the background (PID: {pid})")


if __name__ == "__main__":
    main()
