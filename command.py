#!/usr/bin/env python3
"""
Terminal Command Generator using Groq API
Generates the appropriate terminal command to run transpiled code
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv


def generate_run_command(changes_summary):
    """
    Generate terminal command to run the transpiled code using Groq inference.

    Args:
        changes_summary: String containing diff/changes summary from diff.py

    Returns:
        dict: {
            "success": bool,
            "command": str,         # The terminal command to run
            "explanation": str,     # Brief explanation
            "error": str           # Error message if failed
        }
    """
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GROQ_API")

    if not api_key:
        return {
            "success": False,
            "command": None,
            "explanation": None,
            "error": "GROQ_API key not found in .env",
        }

    # Extract files from changes summary
    files = _extract_files_from_changes(changes_summary)

    if not files:
        return {
            "success": False,
            "command": None,
            "explanation": None,
            "error": "No executable files found in changes",
        }

    # Build the prompt for Groq
    prompt = _build_prompt(changes_summary, files)

    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)

        # Call Groq API for inference
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a terminal command expert. Generate ONLY the exact command needed to run code files. Return just the command, nothing else - no explanations, no markdown, no extra text.
in the format of:
```bash
<command>
```""",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=100,
        )

        # Extract command from response
        command = response.choices[0].message.content.strip()

        # Clean the command
        command = _clean_command(command)

        if not command:
            return {
                "success": False,
                "command": None,
                "explanation": None,
                "error": "Empty command generated",
            }

        # Generate explanation
        explanation = _explain_command(command, files)

        return {
            "success": True,
            "command": command,
            "explanation": explanation,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "command": None,
            "explanation": None,
            "error": f"Groq API error: {str(e)}",
        }


def _extract_files_from_changes(changes_summary):
    """
    Extract executable file names from the changes summary.
    Returns list of files sorted by priority (Python > JS > Java > Go > etc.)
    """
    files = []

    # Parse changes summary
    lines = changes_summary.split("\n")

    for line in lines:
        line = line.strip()
        # Look for added or modified files (+ or ~)
        if line.startswith("+ ") or line.startswith("~ "):
            filename = line[2:].strip()
            if _is_runnable_file(filename):
                files.append(filename)

    # Also check for "File: " patterns in diff output
    if not files:
        file_pattern = re.compile(r"^File: (.+)$", re.MULTILINE)
        matches = file_pattern.findall(changes_summary)
        for match in matches:
            if _is_runnable_file(match.strip()):
                files.append(match.strip())

    # Sort by priority
    return _prioritize_files(files)


def _is_runnable_file(filename):
    """Check if file is a runnable code file"""
    runnable_extensions = [
        ".py",
        ".js",
        ".java",
        ".go",
        ".ts",
        ".tsx",
        ".jsx",
        ".rb",
        ".php",
        ".rs",
        ".c",
        ".cpp",
        ".sh",
        ".bash",
    ]
    return any(filename.endswith(ext) for ext in runnable_extensions)


def _prioritize_files(files):
    """Sort files by language priority"""
    priority = {
        ".py": 1,
        ".js": 2,
        ".java": 3,
        ".go": 4,
        ".ts": 5,
        ".tsx": 6,
    }

    def get_priority(f):
        for ext, p in priority.items():
            if f.endswith(ext):
                return p
        return 99

    return sorted(files, key=get_priority)


def _build_prompt(changes_summary, files):
    """Build the Groq prompt for command generation"""

    main_file = files[0] if files else "file"
    files_str = ", ".join(files[:3])  # Show max 3 files

    prompt = f"""Generate the terminal command to run this code.

Files: {files_str}
Primary file: {main_file}

Changes summary:
{changes_summary[:400]}

Return ONLY the command. Examples:
- For .py: python {main_file}
- For .js: node {main_file}
- For .java: java {os.path.splitext(main_file)[0]}
- For .go: go run {main_file}
- For .ts/.tsx: tsx {main_file}

Command:"""

    return prompt


def _clean_command(command):
    """Clean up the generated command"""
    # Remove markdown code blocks
    command = re.sub(r"^```(?:bash|sh|shell|python|javascript)?\s*", "", command)
    command = re.sub(r"\s*```$", "", command)

    # Remove quotes if present
    command = command.strip("\"'")

    # Take first line only
    command = command.split("\n")[0].strip()

    # Remove any extra whitespace
    command = " ".join(command.split())

    return command


def _explain_command(command, files):
    """Generate brief explanation of the command"""
    main_file = files[0] if files else ""

    if command.startswith("python"):
        return f"Run Python: {main_file}"
    elif command.startswith("node"):
        return f"Run JavaScript: {main_file}"
    elif command.startswith("java "):
        return f"Run Java: {main_file}"
    elif command.startswith("go run"):
        return f"Run Go: {main_file}"
    elif command.startswith("tsx") or command.startswith("ts-node"):
        return f"Run TypeScript: {main_file}"
    else:
        return f"Execute: {main_file}"


# Test function
if __name__ == "__main__":
    # Test with sample changes
    test_changes = """Changes:
+ test_hello.py
~ main.py

NEW FILES:
  + test_hello.py

Modified files:

File: test_hello.py
----------------------------------------------------------------------
```diff
+    1  def hello():
+    2      print("Hello, World!")
+    3
+    4  if __name__ == "__main__":
+    5      hello()
```
"""

    print("Testing command generation...")
    result = generate_run_command(test_changes)

    if result["success"]:
        print(" Success!")
        print(f"  Command: {result['command']}")
        print(f"  Explanation: {result['explanation']}")
    else:
        print(f" Failed: {result['error']}")
