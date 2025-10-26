![nrun](nrun.png)
# natural run


`natural-code` bridges the gap between human thought and executable software. our mission is to make programming accessible to everyone, regardless of their technical background or experience with traditional programming languages.

we've built a language-agnostic framework that transforms your ideas into working code. simply describe what you want to build using natural language—your preferred way of thinking and expressing logic—and we handle the translation to executable code in any target programming language.

with recent breakthroughs in large language models, code generation has reached unprecedented levels of sophistication. natural code harnesses these capabilities to democratize software development. whether you're a seasoned developer looking to prototype faster or someone with no programming experience wanting to bring ideas to life, our tool adapts to your level and helps you create functional software.

**write naturally. build anything.** — let the code follow your thoughts, not the other way around.

## usage
```bash
nrun <filename>.n<lang>
```
> we have came up with this custom file extension i.e `.n<lang>` and then this is converted into the target language code and then executed.

## setup

```bash
pip install uv (if not already installed)

git clone https://github.com/idhant297/natural-code.git
uv pip install natural-code/
```

## internal workings

### core flow

1. **input**: write your logic in `.n<lang>` files (e.g., `.npy` for python, `.njs` for javascript, `.ntsx` for typescript/react)
2. **transpilation**: run `nrun <filename>.n<lang>` to convert natural language to executable code via llm inference
3. **execution**: the generated code runs automatically with the appropriate interpreter

### change tracking

the system maintains a state of your codebase using file hashing:

- all files are hashed and stored in `.state.json`
- on each run, it generates a diff between current and previous states
- the transpiler receives these diffs to understand what changed
- this enables incremental updates rather than regenerating entire files

### key features

- **smart updates**: only modified portions of code are updated, preserving manual edits
- **gitignore support**: respects `.gitignore` patterns when tracking changes
- **session logging**: all transpilation runs are logged to `cli-logs/` for debugging
- **auto-execution**: automatically determines and runs the correct command for your generated code