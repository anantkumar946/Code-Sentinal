# 🛡 CodeSentinel — Python Static Code Analyzer

CodeSentinel is a lightweight **static code analysis tool** for Python that helps detect issues related to **syntax, semantics, complexity, style, and security**.

It analyzes Python source code and provides:

* Detailed issue reports
* Severity-based warnings
* A health score (0–100)
* Optional HTML reports for visualization

---

## 🚀 Features

### ✅ 1. Syntax Analysis

* Detects syntax errors using Python AST parsing

### ✅ 2. Semantic Analysis

* Unused variables
* Unused imports
* Missing docstrings

### ✅ 3. Complexity Analysis

* Cyclomatic complexity detection
* Function length warnings
* Deep nesting detection

### ✅ 4. Style Checks

* Line length > 79 characters
* Trailing whitespace
* Tabs instead of spaces
* Naming conventions (snake_case, CamelCase)
* Bad practices like `== None`

### ✅ 5. Security Checks

* Use of `eval()` / `exec()`
* Hardcoded passwords & API keys
* SQL injection risks
* Unsafe `pickle` usage
* `subprocess` with `shell=True`

---

## 🧠 How It Works

CodeSentinel parses your Python file using the built-in `ast` module and runs multiple analysis passes.

Each issue is categorized and assigned a severity:

* ERROR
* HIGH
* MEDIUM
* WARNING
* INFO

### 📊 Scoring System

* Starts from **100**
* Deducts points based on severity:

  * ERROR → -20
  * HIGH → -10
  * WARNING → -5
  * MEDIUM → -3
  * INFO → -1

Final score is calculated in: 

---

## 📂 Project Structure

```
CodeSentinel/
│
├── main.py        # Entry point (CLI interface)
├── checks.py      # All analysis logic
├── report.py      # Terminal & HTML reporting
├── test.py        # Sample file with issues
└── README.md
```

---

## ⚙️ Installation

No external dependencies required (basic version).

Optional (for better terminal output):

```
pip install rich
```

---

## ▶️ Usage

### 🔹 Run basic analysis

```
python main.py test.py
```

### 🔹 Generate HTML report

```
python main.py test.py --html
```

### 🔹 Custom output file

```
python main.py test.py --html --output my_report.html
```

CLI handling is implemented in: 

---

## 📄 Output Example

### Terminal Output

* Categorized issues
* Severity labels
* Health score with grade

### HTML Report

* Interactive dashboard
* Category-wise issue breakdown
* Visual score indicator

HTML generation handled in: 

---

## 🧪 Test File

A sample file with intentional issues is included:

* Security vulnerabilities
* Style violations
* Complexity issues

See: 

---

## 📌 Example Issues Detected

* Hardcoded password → 🔴 HIGH
* `eval()` usage → 🔴 HIGH
* Unused variables → ⚠️ WARNING
* Deep nesting → ⚠️ WARNING
* Missing docstring → ℹ️ INFO

---

## 🎯 Use Cases

* Code quality analysis
* Learning clean coding practices
* Security awareness in Python
* Compiler Design / Academic projects

---

## 🔮 Future Improvements

* Support for multiple files / folders
* Integration with VS Code
* Auto-fix suggestions
* Support for other languages (C++, Java)

---

## 👨‍💻 Author

**Anant Kumar**
BTech — Graphic Era Hill University

---

## 📜 License

This project is for educational purposes. Feel free to modify and extend.

---

## ⭐ Contribution

Contributions are welcome!
Fork the repo and submit a pull request 🚀
