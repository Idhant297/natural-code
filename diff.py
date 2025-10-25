import sys
import json
import hashlib
from pathlib import Path


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


def scan(folder):
    folder = Path(folder)
    files = {}
    for f in folder.rglob("*"):
        if (
            f.is_file()
            and not f.name.startswith(".DS_Store")
            and ".git" not in str(f)
            and f.name != ".folder_state.json"
        ):
            files[str(f.relative_to(folder))] = {
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


def show_diff(added, removed, modified):
    if added:
        print("\nNEW FILES:")
        for f in sorted(added):
            print(f"\n+ {f}")
    if removed:
        print("\nDELETED FILES:")
        for f in sorted(removed):
            print(f"\n- {f}")
    if modified:
        print("\nMODIFIED FILES:")
        for f in modified:
            print(f"\n~ {f['file']}")
            old_content = f["old_content"]
            new_content = f["new_content"]

            old_lines = old_content.split("\n")
            new_lines = new_content.split("\n")

            print("Diff:")
            # Simple line-by-line comparison
            max_lines = max(len(old_lines), len(new_lines))
            for i in range(max_lines):
                old_line = old_lines[i] if i < len(old_lines) else ""
                new_line = new_lines[i] if i < len(new_lines) else ""

                if old_line != new_line:
                    if old_line and new_line:
                        print(f"  {i + 1:3d}|- {old_line}")
                        print(f"  {i + 1:3d}|+ {new_line}")
                    elif old_line:
                        print(f"  {i + 1:3d}|- {old_line}")
                    elif new_line:
                        print(f"  {i + 1:3d}|+ {new_line}")


def main():
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    flags = [arg for arg in sys.argv[1:] if arg.startswith("-")]
    folder = args[0] if args else "."
    statefile = ".folder_state.json"
    show_content = "--content" in flags or "-c" in flags

    curr = scan(folder)
    prev = load(statefile)
    if not prev:
        print("First run - saving baseline")
        save(curr, statefile)
        return

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

    if added or removed or modified:
        print("Changes:")
        for f in sorted(added):
            print(f"+ {f}")
        for f in sorted(removed):
            print(f"- {f}")
        for f in modified:
            print(f"~ {f['file']}")
        if show_content:
            show_diff(added, removed, modified)
    else:
        print("No changes")
    save(curr, statefile)


if __name__ == "__main__":
    main()
