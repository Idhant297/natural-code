#!/usr/bin/env python3
"""
Terminal Command Generator using Groq API
Generates the terminal command to run the transpiled code
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv


def generate_run_command(file_path, changes_summary):
    """
    Generate terminal command to run the transpiled code using Groq inference.

    Args:
        file_path: Original .n<lang> file path (e.g., "hello.npy")
        changes_summary: Git diff summary showing what files were created/modified

    Returns:
        dict: {
            "success": bool,
            "command": str,
            "error": str
        }
    """
    # Load environment and get API key
    load_dotenv()
    api_key = os.getenv("GROQ_API")

    if not api_key:
        return {
            "success": False,
            "command": None,
            "error": "GROQ_API key not found in .env",
        }

    # Build prompt for Groq
    prompt = f"""Generate the terminal command to run the transpiled code.

Original file: {file_path}
(e.g., if original is "hello.npy", the transpiled file will be "hello.py")

Changes made by the transpiler:
{changes_summary[:600]}

Your task: Generate the exact terminal command to run the main transpiled file.

Examples:
- If original: hello.npy → command: python hello.py
- If original: server.njs → command: node server.js
- If original: app.ngo → command: go run app.go
- If original: main.nts → command: tsx main.ts

Return ONLY the terminal command in this format:
```bash
<command>
```
"""

    try:
        # Call Groq API
        client = Groq(api_key=api_key)

        system_prompt = """You are a terminal command expert for a natural code transpiler system.

The system works like this:
- Users write code in .n<language> files (e.g., .npy for Python, .njs for JavaScript)
- The transpiler converts these to actual runnable code files
- Your job: Generate the EXACT terminal command to run the transpiled file

Rules:
1. The transpiled file name = original filename with 'n' removed from extension
   - hello.npy → hello.py → command: python hello.py
   - server.njs → server.js → command: node server.js
   - app.njava → app.java → command: java app (for Java, no extension)

2. Use the appropriate runtime/interpreter:
   - .py → python or python3
   - .js → node
   - .java → javac <file_name>.java && java <file_name>
   - .go → go run
   - .ts/.tsx → tsx or ts-node
   - .rb → ruby
   - .php → php
   
   NOTE: the command should be self contained and should NOT any further steps to run the code.

3. Return ONLY the command in this format:
   ```bash
   <command>
   ```

Do NOT add explanations, do NOT add extra text. ONLY the command in a bash code block."""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=100,
        )

        # Parse command from response
        raw_output = response.choices[0].message.content.strip()
        command = parse_bash_block(raw_output)

        if not command:
            return {
                "success": False,
                "command": None,
                "error": "Empty command generated",
            }

        return {"success": True, "command": command, "error": None}

    except Exception as e:
        return {"success": False, "command": None, "error": f"Groq API error: {str(e)}"}


def parse_bash_block(raw_output):
    """
    Parse command from Groq output in format:
    ```bash
    <command>
    ```
    """
    # Extract content between ```bash and ```
    match = re.search(r"```bash\s*\n(.+?)\n```", raw_output, re.DOTALL)
    if match:
        return match.group(1).strip().split("\n")[0].strip()

    # Fallback: try generic code block
    match = re.search(r"```\s*\n(.+?)\n```", raw_output, re.DOTALL)
    if match:
        return match.group(1).strip().split("\n")[0].strip()

    # Fallback: use raw output first line
    return raw_output.strip().split("\n")[0].strip()
