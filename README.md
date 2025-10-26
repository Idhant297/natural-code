# 🌟 Natural Code

> Write code the way you think. Transform natural language pseudocode into production-ready code files.

Natural Code is a CLI tool that bridges the gap between your ideas and implementation. Write what you want in plain English (or any language), and let AI generate the actual code files for you.

## ✨ The Magic

Instead of writing this:
```python
# Traditional approach
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

You write this:
```
// fibonacci.npy
Create a function that calculates fibonacci numbers recursively.
It should handle edge cases and return the nth number in the sequence.
```

Natural Code handles the rest. 🚀

## 🎯 How It Works

1. **Write Natural Code**: Create a `.n<language>` file (`.npy` for Python, `.njs` for JavaScript, etc.)
2. **Run the CLI**: Execute `python cli.py your-file.npy`
3. **Get Real Code**: Watch as your natural language transforms into actual, runnable code
4. **Iterate**: Make changes, run again - Natural Code tracks your diffs and updates intelligently

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/natural-code.git
cd natural-code

# Install dependencies
pip install -e .

# Set up your environment
cp .env.example .env
# Add your GROQ_API key to .env
```

## 🚀 Quick Start

### 1. Create a Natural Code File

```bash
echo "Create a web scraper that fetches article titles from a news website" > scraper.npy
```

### 2. Run Natural Code

```bash
python cli.py scraper.npy
```

### 3. Watch the Magic

Natural Code will:
- ✅ Generate the actual Python file (`scraper.py`)
- ✅ Track changes between runs
- ✅ Update existing code based on your modifications
- ✅ Log everything for debugging

## 📝 Supported Extensions

- `.npy` - Python
- `.njs` - JavaScript
- `.njava` - Java
- `.ngo` - Go
- `.nrs` - Rust
- *...and any language you can imagine!*

## 🎛️ CLI Options

```bash
# Run in background (default)
python cli.py your-file.npy

# Wait for completion
python cli.py your-file.npy --wait

# Check logs
cat cli-logs/your-file_*.log
```

## 🔥 Features

### Intelligent Diff Tracking
Natural Code uses `diff.py` to track changes between runs, so it knows exactly what you've modified and can update code accordingly.

### Smart Gitignore Support
Automatically respects your `.gitignore` patterns - no need to worry about tracking unnecessary files.

### Background Execution
Run your code generation in the background and keep working. All output is logged for later review.

### Contextual Understanding
Natural Code sees your entire project context, making intelligent decisions about how to structure and update your code.

## 📂 Project Structure

```
natural-code/
├── cli.py              # Main CLI interface
├── diff.py             # Intelligent diff tracking
├── prompt.md           # System prompt (customizable!)
├── .env                # API keys and config
├── cli-logs/           # Execution logs
└── .state.json         # Tracks file states
```

## 🎨 Customization

Want to customize how Natural Code generates code? Edit `prompt.md` to add your own guidelines, coding standards, or preferences.

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🎨 UI/UX enhancements

Just open a PR!

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [Codex](https://github.com/Abaso007/codex) - The AI coding CLI that powers Natural Code
- [GROQ](https://groq.com/) - Fast LLM inference
- Python & a dream ✨

---

<div align="center">

**[⭐ Star this repo](https://github.com/yourusername/natural-code)** if Natural Code helps you code faster!

Made with ❤️ by [idhant](https://github.com/idhant)

</div>
