#!/usr/bin/env python3
"""CLI tool to run natural code files .n<language> files through codex"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from diff import main as diff_main

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
    # Try current working directory first (where the user runs the command)
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        # Fall back to script directory (for development mode)
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


def cli_prompt(tagged_file):
    """
    Collect and construct the full prompt for codex.

    Args:
        prompt_file: Path to the natural code file
        additional_context: Optional additional context to include

    Returns:
        Fully formatted prompt string ready for codex
    """
    tagged_file = f"@{tagged_file}"

    # Get diff output without printing to stdout
    diff = diff_main(print_output=False)

    # Handle case where diff_main returns None
    if diff is None:
        diff = "No diff information available"

    # prompt = f"""{system_prompt}

    prompt = f"""Main file that the user is intended to run:
{tagged_file}

Changes that user has made since the last run of the code:
{diff}

Now please create the desired code file (if not already created) for the user to run and other necessary ones OR update the existing code file to the desired state."""

    return prompt


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

    # Use the prompt that was passed in (already constructed by cli_prompt)
    full_prompt = prompt

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

        print(f"process started (PID: {process.pid})")
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
    read_natural_code_file(args.file)

    # Get absolute path to the prompt file
    tagged_file = str(Path(args.file).resolve())

    # Generate log file path
    log_file = get_log_filepath(args.file)

    print(f"Running codex with prompt from {args.file}...")

    # Construct full prompt using cli_prompt function
    full_prompt = cli_prompt(tagged_file)

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
            log_handle.write(f"Prompt file: {args.file}\n")
            if PROMPT_FILE.exists():
                log_handle.write(f"System prompt file: {PROMPT_FILE}\n")
            log_handle.write(
                f"Prompt: {full_prompt[:100]}{'...' if len(full_prompt) > 100 else ''}\n"
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
            full_prompt,
            tagged_file,
            groq_api_key,
            log_file,
            show_output=SHOW_CODEX_OUTPUT,
        )
        if SHOW_CODEX_OUTPUT:
            print(f"Codex is running in the background (PID: {pid}) - output visible")
        else:
            print(f"Codex is running in the background (PID: {pid})")


if __name__ == "__main__":
    main()
