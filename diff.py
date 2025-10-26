import json
import hashlib
import fnmatch
from pathlib import Path
import difflib


def get_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def get_content(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_gitignore_patterns(folder):
    """Load patterns from .gitignore file"""
    gitignore_path = Path(folder) / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            pass

    return patterns


def is_ignored(file_path, patterns):
    """Check if a file path matches any gitignore pattern"""
    file_path_str = str(file_path)

    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            if file_path_str.startswith(pattern) or ("/" + pattern) in file_path_str:
                return True
        # Handle negation patterns (starting with !)
        elif pattern.startswith("!"):
            # This is a negation pattern - would need more complex logic
            # For now, we'll skip negation patterns
            continue
        # Handle glob patterns
        else:
            if fnmatch.fnmatch(file_path_str, pattern) or fnmatch.fnmatch(
                file_path_str, "*/" + pattern
            ):
                return True
            # Also check if any parent directory matches
            parts = file_path_str.split("/")
            for i in range(len(parts)):
                partial_path = "/".join(parts[: i + 1])
                if fnmatch.fnmatch(partial_path, pattern):
                    return True

    return False


def scan(folder):
    folder = Path(folder)
    files = {}
    gitignore_patterns = load_gitignore_patterns(folder)

    for f in folder.rglob("*"):
        if (
            f.is_file()
            and not f.name.startswith(".DS_Store")
            and ".git" not in str(f)
            and f.name != ".state.json"
        ):
            relative_path = f.relative_to(folder)

            # Check if file should be ignored based on gitignore patterns
            if not is_ignored(relative_path, gitignore_patterns):
                files[str(relative_path)] = {
                    "hash": get_hash(f),
                    "content": get_content(f),
                }
    return files


def save(data, fname):
    with open(fname, "w") as f:
        json.dump(data, f, indent=2)


def load(fname):
    if Path(fname).exists():
        try:
            with open(fname) as f:
                return json.load(f) or {}
        except Exception:
            return {}
    return {}


def is_json_file(filename):
    """Check if a file is likely a JSON file based on extension"""
    return filename.lower().endswith((".json", ".ipynb"))


def format_content_for_diff(content, filename):
    """Format content for better diff display"""
    if is_json_file(filename):
        try:
            # Try to parse and pretty-print JSON
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2, sort_keys=True)
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, return as-is
            pass
    return content


def show_diff(added, removed, modified, context_lines=2):
    """Display changes in a clean, simple format - returns string instead of printing"""
    output = []

    # New files
    if added:
        output.append("NEW FILES:")
        for f in sorted(added):
            output.append(f"  + {f}")
        output.append("")

    # Deleted files
    if removed:
        output.append("DELETED FILES:")
        for f in sorted(removed):
            output.append(f"  - {f}")
        output.append("")

    # Modified files
    if modified:
        output.append("Modified files:")
        output.append("")

        for f in modified:
            filename = f["file"]
            output.append(f"File: {filename}")
            output.append("-" * 70)

            old_content = f["old_content"]
            new_content = f["new_content"]

            # Format content for better diffing (pretty-print JSON, etc.)
            old_formatted = format_content_for_diff(old_content, filename)
            new_formatted = format_content_for_diff(new_content, filename)

            # Split content into lines
            old_lines = old_formatted.splitlines()
            new_lines = new_formatted.splitlines()

            # Use SequenceMatcher for comparison
            matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
            opcodes = list(matcher.get_opcodes())

            # Check if there are any changes
            has_changes = any(tag != "equal" for tag, _, _, _, _ in opcodes)
            if not has_changes:
                output.append("  (No textual differences found)")
                output.append("")
                continue

            # Build hunks: regions to display (changes + context)
            hunks = []
            for tag, i1, i2, j1, j2 in opcodes:
                if tag != "equal":
                    # Include context around changes
                    # For inserts where i1==i2, ensure we still create a valid hunk
                    hunk_start = max(0, i1 - context_lines)
                    hunk_end = min(len(old_lines), max(i1, i2) + context_lines)
                    hunks.append((hunk_start, hunk_end, tag, i1, i2, j1, j2))

            # Merge overlapping hunks and track which opcodes belong to each
            if hunks:
                merged_hunks = [(hunks[0][0], hunks[0][1], [hunks[0][2:]])]
                for hunk_start, hunk_end, tag, i1, i2, j1, j2 in hunks[1:]:
                    last_start, last_end, last_ops = merged_hunks[-1]
                    if hunk_start <= last_end + 1:
                        # Overlapping or adjacent, merge them
                        merged_hunks[-1] = (
                            last_start,
                            max(last_end, hunk_end),
                            last_ops + [(tag, i1, i2, j1, j2)],
                        )
                    else:
                        merged_hunks.append(
                            (hunk_start, hunk_end, [(tag, i1, i2, j1, j2)])
                        )

                # Start markdown diff block
                output.append("```diff")

                # Display each hunk
                for hunk_idx, (hunk_start, hunk_end, hunk_ops) in enumerate(
                    merged_hunks
                ):
                    # Show ellipsis if this isn't the first hunk
                    if hunk_idx > 0:
                        output.append("...")

                    # Track current line numbers for old and new files
                    old_line_num = hunk_start + 1
                    new_line_num = hunk_start + 1

                    # Calculate new_line_num offset by counting changes before this hunk
                    for tag, i1, i2, j1, j2 in opcodes:
                        if i1 >= hunk_start:
                            break
                        if tag == "insert":
                            new_line_num += j2 - j1
                        elif tag == "delete":
                            new_line_num -= i2 - i1
                        elif tag == "replace":
                            new_line_num += (j2 - j1) - (i2 - i1)

                    # Process all opcodes, showing context and changes
                    for tag, i1, i2, j1, j2 in opcodes:
                        # Check if this opcode overlaps with current hunk
                        if tag == "equal":
                            # For equal sections, only show if within hunk range
                            start_idx = max(i1, hunk_start)
                            end_idx = min(i2, hunk_end)
                            if start_idx < end_idx:
                                for idx in range(start_idx, end_idx):
                                    output.append(
                                        f"  {old_line_num:4d}  {old_lines[idx]}"
                                    )
                                    old_line_num += 1
                                    new_line_num += 1
                        else:
                            # For changes, check if this change is part of current hunk
                            change_in_hunk = False
                            for change_tag, ci1, ci2, cj1, cj2 in hunk_ops:
                                if (
                                    tag == change_tag
                                    and i1 == ci1
                                    and i2 == ci2
                                    and j1 == cj1
                                    and j2 == cj2
                                ):
                                    change_in_hunk = True
                                    break

                            if not change_in_hunk:
                                # Update line numbers for skipped changes
                                if tag == "insert":
                                    new_line_num += j2 - j1
                                elif tag == "delete":
                                    old_line_num += i2 - i1
                                elif tag == "replace":
                                    old_line_num += i2 - i1
                                    new_line_num += j2 - j1
                                continue

                            if tag == "replace":
                                # Show removed lines
                                for idx in range(i1, i2):
                                    output.append(
                                        f"- {old_line_num:4d}  {old_lines[idx]}"
                                    )
                                    old_line_num += 1
                                # Show added lines
                                for idx in range(j1, j2):
                                    output.append(
                                        f"+ {new_line_num:4d}  {new_lines[idx]}"
                                    )
                                    new_line_num += 1

                            elif tag == "delete":
                                for idx in range(i1, i2):
                                    output.append(
                                        f"- {old_line_num:4d}  {old_lines[idx]}"
                                    )
                                    old_line_num += 1

                            elif tag == "insert":
                                # For inserts, show the new line numbers
                                for idx in range(j1, j2):
                                    output.append(
                                        f"+ {new_line_num:4d}  {new_lines[idx]}"
                                    )
                                    new_line_num += 1

                # End markdown diff block
                output.append("```")

            output.append("")

    return "\n".join(output)


def main(folder=".", print_output=True):
    """
    Main diff function - returns diff as string.

    Args:
        folder: Folder to scan for changes
        print_output: If True, prints output to console. If False, only returns string.

    Returns:
        String containing the diff output
    """
    statefile = ".state.json"

    curr = scan(folder)
    prev = load(statefile)

    if not prev:
        result = "First run - establishing baseline"
        if print_output:
            print(result)
        save(curr, statefile)
        return result

    added = set(curr) - set(prev)
    removed = set(prev) - set(curr)
    modified = []

    for f in curr:
        if f in prev and curr[f]["hash"] != prev[f]["hash"]:
            modified.append(
                {
                    "file": f,
                    "old_content": prev[f]["content"],
                    "new_content": curr[f]["content"],
                }
            )

    output = []

    if added or removed or modified:
        output.append("Changes:")
        for f in sorted(added):
            output.append(f"+ {f}")
        for f in sorted(removed):
            output.append(f"- {f}")
        for f in modified:
            output.append(f"~ {f['file']}")

        diff_details = show_diff(added, removed, modified)
        if diff_details:
            output.append(diff_details)
    else:
        output.append("No changes")

    result = "\n".join(output)

    if print_output:
        print(result)

    save(curr, statefile)
    return result


if __name__ == "__main__":
    main()
