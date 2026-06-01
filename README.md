<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" />
</p>

<h1 align="center">🛡️ CodeSentinel</h1>
<p align="center"><strong>A Python & SQL Static Code Analyzer</strong></p>
<p align="center">
  Detect security vulnerabilities, style violations, complexity issues, and SQL anti-patterns — from the terminal or a premium web UI.
</p>

---

## ✨ Features

| Category        | What it checks                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------ |
| **Syntax**      | Parse errors via Python `ast`                                                                    |
| **Semantic**    | Unused variables, unused imports, missing docstrings                                             |
| **Complexity**  | Cyclomatic complexity, function length, deep nesting                                             |
| **Style**       | PEP 8 line length, tabs vs spaces, trailing whitespace, naming conventions (CamelCase/snake_case)|
| **Security**    | `eval`/`exec`, hardcoded secrets, `pickle` deserialization, `subprocess shell=True`, SQL injection (concat, f-string, %-format, `.format()`) |
| **SQL**         | `SELECT *`, missing `WHERE`, implicit joins, `= NULL`, `ORDER BY` without `LIMIT`, nested subqueries, `LIKE '%...'`, `INSERT` without columns, `SELECT DISTINCT` overuse |

Every issue comes with an **actionable fix suggestion** so developers know exactly how to resolve it.

---

## 🏗️ Architecture

```
┌──────────────┐       ┌────────────────┐
│   main.py    │──────▶│   checks.py    │   Python analysis (AST + regex)
│  (CLI entry) │       └────────────────┘
└──────────────┘               │
                               ▼
                       ┌────────────────┐
                       │ suggestions.py │   Pattern-matched fix suggestions
                       └────────────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │   report.py    │   Terminal (Rich) + HTML output
                       └────────────────┘

┌──────────────┐       ┌────────────────┐
│    app.py    │──────▶│  sql_checks.py │   SQL analysis (sqlglot AST)
│ (Flask web)  │       └────────────────┘
└──────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  templates/index.html                 │
│  static/style.css  ·  static/app.js  │   Premium dark-themed web UI
└───────────────────────────────────────┘
```

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/anantkumar946/Code-Sentinal.git
cd Code-Sentinal

# (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install flask rich sqlglot
```

### Dependencies

| Package    | Purpose                            | Required |
| ---------- | ---------------------------------- | -------- |
| `flask`    | Web UI server                      | Yes      |
| `rich`     | Colored terminal output            | Optional |
| `sqlglot`  | SQL parsing & anti-pattern checks  | Optional (regex fallback for SQL-in-Python) |

---

## 🚀 Usage

### CLI Mode

Analyze a Python file and print results to the terminal:

```bash
python main.py test.py
```

Generate an HTML report:

```bash
python main.py test.py --html
python main.py test.py --html --output my_report.html
```

### Web UI Mode

Launch the Flask development server:

```bash
python app.py
```

Open **http://localhost:5000** in your browser. Toggle between **Python** and **SQL** modes, paste your code, and hit **⚡ Analyze Code**.

---

## 📁 Project Structure

```
Code-Sentinal/
├── main.py              # CLI entry point
├── app.py               # Flask web server
├── checks.py            # Python analysis passes (syntax, semantic, complexity, style, security)
├── sql_checks.py        # SQL analysis passes (syntax, style, best practices, anti-patterns)
├── suggestions.py       # Pattern-matched fix suggestions for all issue types
├── report.py            # Terminal (Rich) and HTML report generation
├── templates/
│   └── index.html       # Web UI template
├── static/
│   ├── style.css        # Premium dark-themed stylesheet
│   └── app.js           # Client-side logic (editor, results rendering)
├── test.py              # Sample Python file with intentional issues (for testing)
├── test_sql_new.py      # SQL anti-pattern test script
└── README.md
```

---

## 📊 Scoring System

CodeSentinel assigns a **Health Score (0–100)** based on the issues found:

| Severity   | Penalty |
| ---------- | ------- |
| `ERROR`    | −20     |
| `HIGH`     | −10     |
| `WARNING`  | −5      |
| `MEDIUM`   | −3      |
| `INFO`     | −1      |

Grades: **A** (≥ 80) · **B** (≥ 60) · **C** (≥ 40) · **F** (< 40)

---

## 🧪 Running Tests

Use the included test files to verify the analyzer:

```bash
# Python analysis test
python main.py test.py --html

# SQL anti-pattern tests
python test_sql_new.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ as a <strong>Compiler Design Project</strong>
</p>
