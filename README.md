
# TreeMark

**TreeMark** — Fast, scalable folder → Markdown / JSON structure generator (CLI + interactive mode).

TreeMark scans a folder (or zip archive) and generates:
- a **nested JSON tree** (compact export with `name`, `type`, `children`), and
- a **flat list** of file paths (array of strings) in the same JSON file,

and/or a Markdown representation. It also supports:
- recreating a folder structure from JSON/Markdown,
- converting JSON ↔ Markdown,
- an interactive CLI with default/custom flows and friendly prompts.

---

## Features

- `generate` CLI: scan a folder and output Markdown and/or JSON.
- Combined JSON format: `{ "tree": {...}, "flat": ["a/b.py", ...] }`.
- `create-from-json`: recreate directories/files from TreeMark JSON (supports both `tree` and `flat`).
- `interactive` mode: guided menu, default vs custom options, `back` to previous steps, `exit` anytime.
- Async-safe scanning with controlled concurrency (configurable).
- Modular Clean Architecture: `core`, `adapters`, `cli`, `factory`, `scripts`.
- Pydantic models + dataclasses for robust schemas and easy validation.
- Tests (pytest + pytest-asyncio) and CI workflow (GitHub Actions) included.

---

## Project structure (high level)

```
treemark/
├─ pyproject.toml
├─ README.md
├─ .github/
│  └─ workflows/ci.yml
├─ tree\_mark/
│  ├─ **init**.py
│  ├─ main.py
│  ├─ cli/
│  │  └─ app.py
│  ├─ core/
│  │  ├─ models/   # pydantic schemas and usecase result
│  │  ├─ entities/ # TreeNode dataclass
│  │  └─ usecases/ # GenerateStructureUseCase
│  ├─ adapters/
│  │  ├─ filesystem/
│  │  │  ├─ scanner.py
│  │  │  └─ archive\_scanner.py
│  │  ├─ serializers/
│  │  │  ├─ json\_serializer.py
│  │  │  └─ markdown\_serializer.py
│  │  └─ repository/
│  │     └─ file\_repository.py
│  ├─ factory/
│  ├─ scripts/
│  ├─ utils/
│  └─ logging\_config.py
├─ tests/
└─ docs/

````

---

## Quickstart (development)

**Requirements**
- Python 3.11+ recommended
- Poetry (recommended) or virtualenv + pip

**Install & run (Poetry)**
```bash
# from repo root
poetry install
# run CLI
poetry run treemark generate "D:\Projects\Helpers\treemark\tree_mark" --output both --concurrency 8
# or interactive
poetry run treemark interactive
````

**Install & run (venv / pip)**

```bash
python -m venv .venv
# Windows PowerShell:
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt   # or install packages manually
python -m tree_mark.main generate "D:\Projects\Helpers\treemark\tree_mark" --output both
```

---

## Interactive mode (friendly guide)

Run:

```bash
poetry run treemark interactive
```

Behavior highlights:

* At each prompt you may type `exit` to terminate immediately.
* Type `back` to return to the previous prompt.
* Default flow: press **Enter** at prompts to accept suggested defaults (Outputs: both, Keep extensions: Yes, Outputs dir: `outputs`, Concurrency: 10).
* Custom flow: when prompted select “No” to specify output format, whether to keep extensions, output folder, concurrency, etc.
* Output files are stored in a single `outputs/` directory by default. Filenames are sanitized versions of the scanned path.

---

## Output formats

### JSON (combined)

The generated JSON contains two keys:

* `tree` — nested object with this schema for nodes:

  ```json
  { "name": "app", "type": "directory", "children": [ ... ] }
  ```

  Note: **no `path` or `size` fields** — only `name`, `type`, and optional `children`.

* `flat` — an array of relative file paths, e.g.:

  ```json
  ["app/agentic_sql_assistant.py", "app/application/services/charting_service.py"]
  ```

Combined JSON example:

```json
{
  "tree": {
    "name": "app",
    "type": "directory",
    "children": [
      { "name": "agentic_sql_assistant.py", "type": "file" },
      {
        "name": "application",
        "type": "directory",
        "children": [
          {
            "name": "services",
            "type": "directory",
            "children": [
              { "name": "charting_service.py", "type": "file" },
              { "name": "content_service.py", "type": "file" }
            ]
          }
        ]
      }
    ]
  },
  "flat": [
    "app/agentic_sql_assistant.py",
    "app/application/services/charting_service.py",
    "app/application/services/content_service.py"
  ]
}
```

### Markdown

A nested bullet list using two-space indentation and `- name/` for directories.

---

## Recreate / Convert tools

* `treemark create-from-json <json> <dest> [--dry-run]` — recreate structure.
* `treemark interactive` offers conversion tools: JSON → Markdown, Markdown → JSON, Recreate.

The create-from-json prefers the `flat` list if present (most accurate); otherwise it builds structure from `tree`.

---

## Development notes

* Clean Architecture: adapters & core separated; easy to replace scanners (S3, etc.).
* Pydantic + dataclasses used for validation and internal models.
* I/O is async-friendly (uses `asyncio.to_thread` for blocking filesystem calls and `aiofiles` for async writing).
* Logging uses `loguru`. See `tree_mark/logging_config.py`.

---

## Running tests & CI

Run tests locally:

```bash
poetry run pytest -q
# or
pytest -q
```

CI: GitHub Actions workflow `./.github/workflows/ci.yml` is configured to run tests on push/pull requests.

---

## Contributing

See `CONTRIBUTING.md` (recommended). Keep PRs small and focused. Add unit tests for new features.

---

## License

This project is provided under the [MIT License](./LICENSE).

---

## Contact / support

Open an issue on GitHub for bugs or feature requests.

````

---

## 2) Optional repo files (recommended)

### .gitignore (repo root: `.gitignore`)
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.pdb

# Virtual env
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.iml

# Outputs / artifacts
outputs/
treemark_out*.json
treemark_out*.md

# OS
.DS_Store
Thumbs.db

# Logs
*.log
````


---
## 3) How to run (Windows PowerShell)
pip install -r requirements.txt (if you created one)
or
pip install typer rich loguru pydantic aiofiles fastapi uvicorn.


---
### If you are using Poetry — run via poetry run
From project root D:\Projects\Helpers\treemark
```powershell
cd D:\Projects\Helpers\treemark
# Activate virtualenv if required
. .venv\Scripts\Activate.ps1
# Run using Poetry:
poetry run treemark generate "D:\Projects\Helpers\treemark\tree_mark"
    --output both --concurrency 6 --out-prefix ".\treemark_out_package"
```

---

### If you are not using Poetry — run via python -m

Make sure your venv is activated, then:
```powershell

cd D:\Projects\Helpers\treemark
# Activate virtualenv if required
. .venv\Scripts\Activate.ps1

# Run using module invocation:
python -m tree_mark.main generate "D:\Projects\Helpers\treemark\tree_mark" --output both --concurrency 6 --out-prefix ".\treemark_out_package"
```
(On Windows python -m tree_mark.main will load the package and pass CLI args to Typer; generate is the command.)

---

### How to run the new interactive mode & examples (Windows PowerShell)

Start interactive session:
```powershell
cd D:\Projects\Helpers\treemark
# From project root D:\Projects\Helpers\treemark
# (venv activated)
python -m tree_mark.main interactive
# or
poetry run treemark interactive

```

- You will be prompted for inputs step-by-step. Type `exit` to quit anytime, or `back` to return to the previous prompt.

- You can choose default or custom options, and generate JSON/Markdown outputs, convert between formats, or recreate a structure from JSON/Markdown.
