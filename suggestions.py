"""
suggestions.py — Actionable fix suggestions for every CodeSentinel issue.
Maps (category, message_pattern) → developer-friendly fix string.
"""

import re

# ── Suggestion rules ────────────────────────────────────────────────────────
# Each rule: (category, compiled_regex_on_message, suggestion_template)
# The template may use {name} which is extracted from the first regex group.

_RULES = [
    # ── Syntax ──────────────────────────────────────────────────────────────
    ("Syntax", re.compile(r"SyntaxError"),
     "Fix the syntax error reported above. Check for missing colons, "
     "brackets, or quotation marks near the indicated line."),

    # ── Semantic ────────────────────────────────────────────────────────────
    ("Semantic", re.compile(r"Unused variable '(.+?)'"),
     "Remove the variable or prefix with `_` to indicate intentional disuse:\n"
     "    _{name} = ..."),

    ("Semantic", re.compile(r"Unused import '(.+?)'"),
     "Remove the unused import:\n"
     "    # delete: import {name}"),

    ("Semantic", re.compile(r"Missing docstring in function '(.+?)'"),
     "Add a docstring immediately after the function signature:\n"
     '    def {name}(...):\n'
     '        """Describe what this function does."""'),

    ("Semantic", re.compile(r"Missing docstring in class '(.+?)'"),
     "Add a docstring immediately after the class definition:\n"
     '    class {name}:\n'
     '        """Describe what this class represents."""'),

    # ── Complexity ──────────────────────────────────────────────────────────
    ("Complexity", re.compile(r"high cyclomatic complexity"),
     "Extract conditional branches into smaller helper functions.\n"
     "Consider using lookup tables (dicts) instead of long if/elif chains."),

    ("Complexity", re.compile(r"is too long"),
     "Break the function into smaller, focused functions — each doing one thing.\n"
     "Aim for functions under 30 lines."),

    ("Complexity", re.compile(r"deep nesting"),
     "Use early returns or guard clauses to flatten nesting:\n"
     "    if not condition:\n"
     "        return\n"
     "    # main logic here (one level less)"),

    # ── Style ───────────────────────────────────────────────────────────────
    ("Style", re.compile(r"Line too long"),
     "Break the line using parentheses or backslash continuation:\n"
     "    result = (first_part\n"
     "              + second_part)"),

    ("Style", re.compile(r"Tab used"),
     "Replace tabs with 4 spaces. Configure your editor to insert spaces on Tab."),

    ("Style", re.compile(r"Trailing whitespace"),
     "Remove whitespace at the end of the line. "
     "Enable 'trim trailing whitespace' in your editor settings."),

    ("Style", re.compile(r"is None"),
     "Replace `== None` with `is None` (identity check):\n"
     "    if value is None:"),

    ("Style", re.compile(r"if x:.*True"),
     "Simplify the boolean check:\n"
     "    if value:          # instead of: if value == True\n"
     "    if not value:      # instead of: if value == False"),

    ("Style", re.compile(r"Bare 'except:'"),
     "Specify the exception type you expect:\n"
     "    except ValueError:\n"
     "    except (TypeError, KeyError):"),

    ("Style", re.compile(r"should be CamelCase"),
     "Rename the class to CamelCase:\n"
     "    class MyHandler:   # instead of: class myHandler"),

    ("Style", re.compile(r"should be snake_case"),
     "Rename the function to snake_case:\n"
     "    def calculate_area():  # instead of: def calculateArea()"),

    # ── Security ────────────────────────────────────────────────────────────
    ("Security", re.compile(r"Hardcoded password"),
     "Use environment variables instead:\n"
     "    import os\n"
     '    password = os.environ.get("PASSWORD")'),

    ("Security", re.compile(r"Hardcoded API key"),
     "Use environment variables instead:\n"
     "    import os\n"
     '    api_key = os.environ.get("API_KEY")'),

    ("Security", re.compile(r"'eval\(\)'"),
     "Use `ast.literal_eval()` for safe evaluation of data literals, "
     "or use a dedicated parser:\n"
     "    import ast\n"
     "    result = ast.literal_eval(expr)"),

    ("Security", re.compile(r"'exec\(\)'"),
     "Avoid `exec()` entirely. Use structured logic, dispatch tables, "
     "or plugin patterns instead."),

    ("Security", re.compile(r"pickle\.load"),
     "Use a safer serialization format:\n"
     "    import json\n"
     '    data = json.load(open(filename))'),

    ("Security", re.compile(r"Importing 'pickle'"),
     "Consider using `json` or `msgpack` instead of `pickle`.\n"
     "`pickle` can execute arbitrary code during deserialization."),

    ("Security", re.compile(r"shell=True"),
     "Pass the command as a list to avoid shell injection:\n"
     "    subprocess.run(['ls', '-la'])  # instead of shell=True"),

    ("Security", re.compile(r"SQL.*string concat"),
     "Use parameterized queries to prevent SQL injection:\n"
     '    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))'),

    ("Security", re.compile(r"SQL.*f-string"),
     "Use parameterized queries instead of f-strings:\n"
     '    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'),

    # ── SQL-specific ────────────────────────────────────────────────────────
    ("SQL", re.compile(r"SELECT \*"),
     "Specify columns explicitly for clarity and performance:\n"
     "    SELECT col1, col2 FROM table_name"),

    ("SQL", re.compile(r"missing WHERE"),
     "Add a WHERE clause to avoid unintended modification of all rows:\n"
     "    UPDATE table SET col = val WHERE id = ?"),

    ("SQL", re.compile(r"implicit join|cartesian|comma-separated"),
     "Use explicit JOIN syntax for readability:\n"
     "    SELECT ... FROM a JOIN b ON a.id = b.a_id\n"
     "    -- instead of: SELECT ... FROM a, b WHERE a.id = b.a_id"),

    ("SQL", re.compile(r"SELECT DISTINCT"),
     "Verify that DISTINCT is truly needed. Often it masks a bad JOIN or\n"
     "missing constraint. Fix the root cause instead:\n"
     "    -- Check for duplicate joins or missing WHERE conditions\n"
     "    -- Add UNIQUE constraints if the data should be unique"),

    ("SQL", re.compile(r"IS NULL instead|= NULL"),
     "Use IS NULL for NULL comparisons (= NULL always returns NULL):\n"
     "    WHERE column IS NULL       -- instead of: column = NULL\n"
     "    WHERE column IS NOT NULL   -- instead of: column != NULL"),

    ("SQL", re.compile(r"IS NOT NULL instead"),
     "Use IS NOT NULL for NULL comparisons:\n"
     "    WHERE column IS NOT NULL   -- instead of: column != NULL\n"
     "    WHERE column IS NULL       -- instead of: column = NULL"),

    ("SQL", re.compile(r"ORDER BY without LIMIT"),
     "Add a LIMIT clause when using ORDER BY to bound the sort cost:\n"
     "    SELECT col FROM table ORDER BY col LIMIT 100"),

    ("SQL", re.compile(r"LIMIT"),
     "Add a LIMIT clause to prevent unbounded result sets:\n"
     "    SELECT col FROM table LIMIT 100"),

    ("SQL", re.compile(r"Nested subquery|CTE"),
     "Refactor nested subqueries into CTEs for readability:\n"
     "    WITH sub AS (SELECT ... FROM ...)\n"
     "    SELECT ... FROM sub"),

    ("SQL", re.compile(r"leading wildcard|LIKE.*%"),
     "Avoid leading wildcards in LIKE — they prevent index usage:\n"
     "    -- Consider full-text search (e.g., MATCH ... AGAINST in MySQL)\n"
     "    -- Or use a reverse-index pattern if prefix search suffices"),

    ("SQL", re.compile(r"INSERT without.*column"),
     "Always specify columns in INSERT statements:\n"
     "    INSERT INTO users (name, email) VALUES ('Alice', 'a@example.com')\n"
     "    -- instead of: INSERT INTO users VALUES ('Alice', 'a@example.com')"),

    ("SQL", re.compile(r"OR.*IN"),
     "Replace multiple OR conditions with IN:\n"
     "    WHERE status IN ('active', 'pending')  -- instead of OR chains"),

    ("SQL", re.compile(r"unaliased subquery"),
     "Alias the subquery for clarity:\n"
     "    SELECT * FROM (SELECT ...) AS subq"),

    ("SQL", re.compile(r"deprecated"),
     "Replace deprecated syntax with modern SQL equivalents."),

    ("SQL", re.compile(r"SyntaxError|parse error|Parse error"),
     "Check the SQL statement for syntax errors near the indicated position.\n"
     "Verify keywords, commas, and parentheses are correct."),
]


def get_suggestion(category: str, message: str) -> str:
    """Return a fix suggestion for the given issue, or a generic fallback."""
    for rule_cat, pattern, template in _RULES:
        if rule_cat == category and pattern.search(message):
            match = pattern.search(message)
            name = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
            return template.format(name=name)

    # Generic fallback by category
    fallbacks = {
        "Syntax":     "Review the syntax near the indicated line and fix the error.",
        "Semantic":   "Review the code for unused or misused identifiers.",
        "Complexity": "Refactor the code to reduce complexity.",
        "Style":      "Follow PEP 8 style guidelines.",
        "Security":   "Review and fix the security concern as indicated.",
        "SQL":        "Review and correct the SQL statement.",
    }
    return fallbacks.get(category, "Review and address this issue.")
