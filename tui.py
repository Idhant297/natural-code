#!/usr/bin/env python3
"""
nrun - Natural Code Runner
A clean, classic terminal interface for running natural code files
"""

import sys
import os
import time
import threading
import random
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.text import Text
import cli
import diff

# Collection of fun ASCII animation styles - one is picked randomly per session
ANIMATION_STYLES = {
    "circle": ["◐", "◓", "◑", "◒"],
    "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "growing": ["·", "··", "···", "····", "·····", "····", "···", "··"],
    "arrows": ["→", "⇢", "⇉", "➜", "⇉", "⇢"],
    "bounce": ["◡", "◠", "◡", "◠"],
    "pulse": ["○", "◎", "●", "◎"],
    "dance": ["⊂", "⊃", "⊂", "⊃"],
    "wave": ["~", "≈", "≋", "≈"],
    "blocks": ["▁", "▃", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▃"],
    "sparkle": ["✦", "✧", "★", "✧"],
    "pipe": ["|", "/", "—", "\\"],
    "progress": [
        "[    ]",
        "[=   ]",
        "[==  ]",
        "[=== ]",
        "[====]",
        "[ ===]",
        "[  ==]",
        "[   =]",
    ],
    "clock": ["◷", "◶", "◵", "◴"],
    "squares": ["◰", "◳", "◲", "◱"],
    "triangles": ["◢", "◣", "◤", "◥"],
    "asterix": [
        "✢",
        "✣",
        "✤",
        "✥",
        "✦",
        "✧",
        "",
        "✩",
        "✪",
        "✫",
        "✬",
        "✭",
        "✮",
        "✯",
        "✰",
        "✱",
        "✲",
        "✳",
        "✴",
        "✵",
        "✶",
        "✷",
        "✸",
        "✹",
        "✺",
        "✻",
        "✼",
        "✽",
        "✾",
        "✿",
        "❀",
        "❁",
        "❂",
        "❃",
        "❄",
        "❅",
        "❆",
        "❇",
        "❈",
        "❉",
        "❊",
        "❋",
        "❍",
    ],
}

# Fun ASCII-style status messages that rotate during code generation
FUN_VERBS = [
    "* thinking about this...",
    "> sketching the logic...",
    "~ focusing on the details...",
    "+ building your function...",
    "* adding the finishing touches...",
    ">> making it snappy...",
    "~ connecting the pieces...",
    "* brewing up some code...",
    "> growing your idea...",
    "+ writing it down...",
    "* performing some magic...",
    ">> launching the logic...",
    "~ having a lightbulb moment...",
    "> consulting the archives...",
    "+ composing your symphony...",
    "* deep thinking mode activated...",
    "~ setting the stage...",
    "> going with the flow...",
    "+ rolling the dice...",
    "* experimenting with ideas...",
    ">> aiming for perfection...",
    "~ sprinkling some stardust...",
    "> heating things up...",
    "+ painting the picture...",
    "* turning the gears...",
    "~ laying the foundation...",
    "> orchestrating the solution...",
    "+ making it happen...",
    "* adding some flavor...",
    "~ mixing the ingredients...",
    "> parsing the possibilities...",
    "+ compiling creativity...",
    "* weaving the logic...",
    "~ crafting the solution...",
    "> assembling the pieces...",
    "+ cooking up something good...",
    "* conjuring the code...",
]


class NaturalCodeRunner:
    """Main class for the nrun TUI"""

    def __init__(self, filename):
        self.filename = filename
        self.console = Console()
        self.animation_running = True
        self.current_frame = 0
        self.status = "Initializing..."
        self.error = None

        # Pick a random animation style for this session
        self.animation_style = random.choice(list(ANIMATION_STYLES.keys()))
        self.animation_frames = ANIMATION_STYLES[self.animation_style]

        # Track verb rotation - used when codex is actively generating
        self.verb_index = 0
        self.last_verb_time = time.time()
        self.use_fun_verbs = False  # Flag to show we're in code generation mode

    def get_animation_frame(self):
        """Get the current animation frame"""
        frame = self.animation_frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
        return frame

    def get_fun_verb(self):
        """Get a fun verb, rotating through them"""
        # Rotate verbs every 2 seconds
        if time.time() - self.last_verb_time > 2.0:
            self.verb_index = (self.verb_index + 1) % len(FUN_VERBS)
            self.last_verb_time = time.time()
        return FUN_VERBS[self.verb_index]

    def create_display(self):
        """Create clean, minimal display"""
        lines = []

        # Simple header with filename and animation - teal/cyan theme
        lines.append("")
        header_text = Text()
        header_text.append("  nrun ", style="bold cyan")
        header_text.append(self.get_animation_frame(), style="cyan")

        display = Text()
        display.append(header_text)
        display.append("\n\n")
        display.append(f"  {self.filename}\n\n", style="dim")

        # Status - show fun verbs during code generation, normal status otherwise
        if self.error:
            display.append(f"  ✗ {self.error}", style="red")
        elif self.use_fun_verbs:
            display.append(f"  {self.get_fun_verb()}", style="cyan")
        else:
            display.append(f"  {self.status}", style="dim")
        display.append("\n")

        return display

    def update_status(self, new_status):
        """Update the current status message"""
        self.status = new_status

    def set_error(self, error_message):
        """Set an error message"""
        self.error = error_message
        self.animation_running = False

    def spacer_terminal_command(self, command):
        """
        SPACER FUNCTION: Execute terminal command and return result

        This is a placeholder for custom terminal command logic.
        You can implement your own logic here later.

        Args:
            command: The command string to execute

        Returns:
            The result of the command execution
        """
        # TODO: Implement custom terminal command logic here
        # For now, this is a placeholder that you can fill in later

        # Let fun verbs continue showing while running
        time.sleep(0.5)  # Simulated delay

        # Placeholder implementation
        # Replace this with your actual command execution logic
        return {
            "success": True,
            "message": "Spacer function called - implement your logic here",
            "command": command,
        }

    def run_natural_code(self):
        """Run the natural code file through cli.py"""
        try:
            self.update_status("Validating file...")
            time.sleep(0.3)

            # Validate file exists and has correct extension
            path = Path(self.filename)
            if not path.exists():
                self.set_error(f"File not found: {self.filename}")
                return False

            # Check for .n<language> extension
            import re

            match = re.search(r"\.n(\w+)$", self.filename)
            if not match:
                self.set_error(
                    "File must have .n<language> extension (e.g., .npy, .njs)"
                )
                return False

            lang = match.group(1)
            self.update_status(f"Detected language: {lang}")
            time.sleep(0.3)

            # Load environment
            self.update_status("Loading environment...")
            cli.load_env_file()
            time.sleep(0.2)

            # Get API key
            groq_api_key = os.getenv("GROQ_API")
            if not groq_api_key:
                self.set_error("GROQ_API key not found in .env file")
                return False

            self.update_status("Analyzing changes...")
            time.sleep(0.3)

            # Get absolute path
            tagged_file = str(path.resolve())

            # Create log directory
            cli.ensure_log_dir()
            log_file = cli.get_log_filepath(self.filename)

            self.update_status("Constructing prompt...")
            time.sleep(0.3)

            # Build prompt
            full_prompt = cli.cli_prompt(tagged_file)

            self.update_status("Executing via Codex...")
            time.sleep(0.5)

            # Run codex
            pid = cli.run_codex(
                full_prompt,
                tagged_file,
                groq_api_key,
                log_file,
                show_output=False,  # We'll handle output ourselves
            )

            # Enable fun verbs mode - codex is now actively generating code!
            self.use_fun_verbs = True
            time.sleep(4.0)  # Let fun verbs rotate for a bit

            # Call spacer function for terminal command
            _result = self.spacer_terminal_command(f"codex process {pid}")

            # Continue showing fun verbs a bit longer
            time.sleep(2.0)

            # Disable fun verbs and show completion
            self.use_fun_verbs = False
            self.update_status("Checking for changes...")
            time.sleep(0.5)

            # Get file changes using diff.py
            changes_summary = diff.main(folder=".", print_output=False)

            self.update_status(f"Complete! Check log: {log_file.name}")
            time.sleep(1.0)

            return True, changes_summary

        except Exception as e:
            self.set_error(f"Error: {str(e)}")
            return False, None

    def run(self):
        """Main run method with live display"""
        execution_thread = None
        success = False
        changes_summary = None

        try:
            with Live(
                self.create_display(),
                console=self.console,
                refresh_per_second=12,
                transient=False,
            ) as live:
                # Start execution in background thread
                def execute():
                    nonlocal success, changes_summary
                    success, changes_summary = self.run_natural_code()
                    self.animation_running = False

                execution_thread = threading.Thread(target=execute, daemon=True)
                execution_thread.start()

                # Keep updating the display while animation is running
                while self.animation_running:
                    live.update(self.create_display())
                    time.sleep(0.08)

                # Wait for execution to complete
                if execution_thread:
                    execution_thread.join(timeout=1.0)

                # Final update
                live.update(self.create_display())
                time.sleep(0.5)

            # Print final message
            if success:
                self.console.print(
                    "\n  ✓ Natural code execution initiated successfully!",
                    style="bold green",
                )
                self.console.print(
                    "  → Check the log file in: cli-logs/\n", style="dim"
                )

                # Display file changes summary - single line with color coding
                if changes_summary:
                    self._display_changes_summary(changes_summary)
            else:
                self.console.print("\n  ✗ Execution failed!", style="bold red")
                if self.error:
                    self.console.print(f"  → Error: {self.error}", style="red")
                return 1

            return 0

        except KeyboardInterrupt:
            self.console.print("\n\n  ⚠ Cancelled by user")
            return 130
        except Exception as e:
            self.console.print(f"\n  ✗ Unexpected error: {e}")
            return 1

    def _display_changes_summary(self, changes_summary):
        """Parse and display file changes in a single line with color coding"""
        lines = changes_summary.split("\n")

        added = set()
        modified = set()
        deleted = set()

        # Parse only the summary section (before detailed diffs)
        in_summary = False
        for line in lines:
            line_stripped = line.strip()

            # Start of summary section
            if line_stripped == "Changes:":
                in_summary = True
                continue

            # Stop parsing when we hit detailed diff sections
            if line_stripped in [
                "NEW FILES:",
                "DELETED FILES:",
                "Modified files:",
                "```diff",
            ]:
                break

            # Parse file names only in summary section
            if in_summary:
                if line_stripped.startswith("+ "):
                    added.add(line_stripped[2:])
                elif line_stripped.startswith("~ "):
                    modified.add(line_stripped[2:])
                elif line_stripped.startswith("- "):
                    deleted.add(line_stripped[2:])

        # Build the display text with color coding
        if added or modified or deleted:
            display = Text("  ")

            if added:
                display.append("+ ", style="green")
                display.append(", ".join(sorted(added)), style="green")

            if modified:
                if added:
                    display.append("  ", style="dim")
                display.append("~ ", style="yellow")
                display.append(", ".join(sorted(modified)), style="yellow")

            if deleted:
                if added or modified:
                    display.append("  ", style="dim")
                display.append("- ", style="red")
                display.append(", ".join(sorted(deleted)), style="red")

            display.append("\n")
            self.console.print(display)
        else:
            self.console.print("  No changes\n", style="dim")


def show_animated_logo():
    """Show animated expansion from 'nrun' to 'natural run' then big NRUN logo"""
    console = Console()

    # Text expansion frames
    text_frames = [
        "nrun",
        "n run",
        "na run",
        "nat run",
        "natu run",
        "natur run",
        "natura run",
        "natural run",
    ]

    console.clear()

    # Animate the text expansion - slower with normal font
    for frame in text_frames:
        console.clear()
        console.print("\n\n\n")
        console.print(f"        {frame}", style="bold cyan")
        time.sleep(0.15)  # Slower animation

    # Pause before showing big logo
    time.sleep(0.3)

    # Show the big pixelated NRUN logo
    console.clear()
    console.print("")
    console.print("  ███╗   ██╗██████╗ ██╗   ██╗███╗   ██╗", style="bold cyan")
    console.print("  ████╗  ██║██╔══██╗██║   ██║████╗  ██║", style="bold cyan")
    console.print("  ██╔██╗ ██║██████╔╝██║   ██║██╔██╗ ██║", style="bold cyan")
    console.print("  ██║╚██╗██║██╔══██╗██║   ██║██║╚██╗██║", style="bold cyan")
    console.print("  ██║ ╚████║██║  ██║╚██████╔╝██║ ╚████║", style="bold cyan")
    console.print("  ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝", style="bold cyan")
    console.print("")


def main():
    """Entry point for nrun command"""
    # Check if help is requested or no file provided
    if len(sys.argv) == 1 or sys.argv[1] in ["-h", "--help", "help"]:
        show_animated_logo()

        # Show usage information
        console = Console()
        console.print("  [bold]Usage:[/bold]")
        console.print("    nrun <file.n<language>>\n")
        console.print("  [bold]Examples:[/bold]")
        console.print("    nrun hello.npy          Run a Python natural code file")
        console.print("    nrun server.njs         Run a JavaScript natural code file")
        console.print("    nrun app.njava          Run a Java natural code file\n")
        console.print(
            "  The file must have a .n<language> extension where <language> is the"
        )
        console.print("  target programming language (e.g., py, js, java, etc.)\n")
        console.print(" ")
        console.print(
            "  github: [link=https://github.com/idhant297/natural-code]https://github.com/idhant297/natural-code[/link]"
        )
        sys.exit(0)

    # Normal execution with file argument
    filename = sys.argv[1]

    # Create and run the TUI
    runner = NaturalCodeRunner(filename)
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
