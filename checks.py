"""
checks.py — All analysis passes for Python source code.
Each function takes source code (str) and returns a list of Issue dicts.
Issue = { "line": int, "category": str, "severity": str, "message": str, "suggestion": str }
"""

import ast, re
from suggestions import get_suggestion

# Try to import sqlglot for SQL-in-Python detection
try:
    import sqlglot
    from sqlglot import errors as sqlglot_errors
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False


def _issue(line, category, severity, message, suggestion=None):
    """Create an issue dict with an attached fix suggestion."""
    if suggestion is None:
        suggestion = get_suggestion(category, message)
    return {
        "line": line,
        "category": category,
        "severity": severity,
        "message": message,
        "suggestion": suggestion,
    }


# ── 1. SYNTAX ────────────────────────────────────────────────────────────────

def check_syntax(code):
    try:
        return ast.parse(code), []
    except SyntaxError as e:
        return None, [_issue(e.lineno, "Syntax", "ERROR", f"SyntaxError: {e.msg}")]


# ── 2. SEMANTIC ──────────────────────────────────────────────────────────────

def check_semantic(tree):
    issues = []

    # Unused variables
    assigned, used = {}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    assigned[t.id] = node.lineno
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    for name, lineno in assigned.items():
        if name not in used:
            issues.append(_issue(lineno, "Semantic", "WARNING", f"Unused variable '{name}'"))

    # Unused imports
    imported, used_names = {}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[a.asname or a.name.split(".")[0]] = node.lineno
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                imported[a.asname or a.name] = node.lineno
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        if isinstance(node, ast.Attribute):
            n = node
            while isinstance(n, ast.Attribute): n = n.value
            if isinstance(n, ast.Name): used_names.add(n.id)
    for name, lineno in imported.items():
        if name not in used_names:
            issues.append(_issue(lineno, "Semantic", "WARNING", f"Unused import '{name}'"))

    # Missing docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            has_doc = (node.body and isinstance(node.body[0], ast.Expr)
                       and isinstance(node.body[0].value, ast.Constant))
            if not has_doc:
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                issues.append(_issue(node.lineno, "Semantic", "INFO",
                                     f"Missing docstring in {kind} '{node.name}'"))

    return issues


# ── 3. COMPLEXITY ────────────────────────────────────────────────────────────

def check_complexity(tree):
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Cyclomatic complexity (count branches)
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            if isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        if complexity > 7:
            issues.append(_issue(node.lineno, "Complexity", "WARNING",
                                 f"'{node.name}' has high cyclomatic complexity ({complexity})"))

        # Function length
        length = node.end_lineno - node.lineno + 1
        if length > 30:
            issues.append(_issue(node.lineno, "Complexity", "WARNING",
                                 f"'{node.name}' is too long ({length} lines)"))

        # Deep nesting
        def max_depth(n, depth=0):
            d = depth
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    d = max(d, max_depth(child, depth + 1))
            return d
        depth = max_depth(node)
        if depth >= 4:
            issues.append(_issue(node.lineno, "Complexity", "WARNING",
                                 f"'{node.name}' has deep nesting (depth {depth})"))

    return issues


# ── 4. STYLE ─────────────────────────────────────────────────────────────────

def check_style(code, tree):
    issues = []

    for i, line in enumerate(code.splitlines(), 1):
        if len(line) > 79:
            issues.append(_issue(i, "Style", "INFO", f"Line too long ({len(line)} chars)"))
        if "\t" in line:
            issues.append(_issue(i, "Style", "INFO", "Tab used instead of spaces"))
        if line != line.rstrip():
            issues.append(_issue(i, "Style", "INFO", "Trailing whitespace"))
        if re.search(r"==\s*None|!=\s*None", line):
            issues.append(_issue(i, "Style", "INFO", "Use 'is None' instead of '== None'"))
        if re.search(r"==\s*(True|False)", line):
            issues.append(_issue(i, "Style", "INFO", "Use 'if x:' instead of '== True/False'"))
        if re.match(r"\s*except\s*:", line):
            issues.append(_issue(i, "Style", "WARNING", "Bare 'except:' — specify exception type"))

    # Naming via AST
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                issues.append(_issue(node.lineno, "Style", "INFO",
                                     f"Class '{node.name}' should be CamelCase"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if re.search(r"[A-Z]", node.name):
                issues.append(_issue(node.lineno, "Style", "INFO",
                                     f"Function '{node.name}' should be snake_case"))

    return issues


# ── 5. SECURITY ──────────────────────────────────────────────────────────────

def _extract_sql_strings(tree):
    """Extract potential SQL string literals from the AST for sqlglot analysis."""
    sql_strings = []
    sql_keywords = re.compile(
        r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b", re.IGNORECASE
    )

    for node in ast.walk(tree):
        # String constants that look like SQL
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if sql_keywords.search(node.value):
                sql_strings.append((node.lineno, node.value))

        # f-strings with SQL keywords (JoinedStr)
        if isinstance(node, ast.JoinedStr):
            # Reconstruct the static parts of the f-string
            static_parts = []
            has_expr = False
            for val in node.values:
                if isinstance(val, ast.Constant):
                    static_parts.append(str(val.value))
                else:
                    has_expr = True
                    static_parts.append("?")  # placeholder
            combined = "".join(static_parts)
            if sql_keywords.search(combined) and has_expr:
                sql_strings.append((node.lineno, combined))

    return sql_strings


def check_security(code, tree):
    issues = []

    # AST: eval/exec, pickle, subprocess shell=True
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (node.func.id if isinstance(node.func, ast.Name)
                    else node.func.attr if isinstance(node.func, ast.Attribute) else None)
            if name in ("eval", "exec"):
                issues.append(_issue(node.lineno, "Security", "HIGH",
                                     f"'{name}()' executes arbitrary code — dangerous"))
            if name in ("load", "loads"):
                obj = getattr(node.func, "value", None)
                if isinstance(obj, ast.Name) and obj.id == "pickle":
                    issues.append(_issue(node.lineno, "Security", "MEDIUM",
                                         "pickle.load() — unsafe deserialization"))
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value:
                    issues.append(_issue(node.lineno, "Security", "HIGH",
                                         "subprocess with shell=True — shell injection risk"))

        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "pickle":
                    issues.append(_issue(node.lineno, "Security", "MEDIUM",
                                         "Importing 'pickle' — unsafe deserialization module"))

    # Regex: hardcoded secrets
    for i, line in enumerate(code.splitlines(), 1):
        if re.search(r'(?i)(password|passwd|pwd)\s*=\s*["\'].{3,}["\']', line):
            issues.append(_issue(i, "Security", "HIGH", "Hardcoded password detected"))
        if re.search(r'(?i)(api_key|secret_key|token)\s*=\s*["\'].{6,}["\']', line):
            issues.append(_issue(i, "Security", "HIGH", "Hardcoded API key/secret detected"))

    # SQL injection detection — AST-driven with sqlglot when available
    if HAS_SQLGLOT:
        _check_sql_injection_sqlglot(tree, code, issues)
    else:
        _check_sql_injection_regex(code, issues)

    return issues


def _check_sql_injection_sqlglot(tree, code, issues):
    """Detect SQL injection risks by finding SQL strings built via concat/f-string."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ("execute", "executemany", "raw", "executescript"):
                if node.args:
                    arg = node.args[0]

                    # String concatenation: "SELECT ..." + var
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        sql_fragment = _try_extract_str(arg)
                        msg = "SQL query built with string concatenation — injection risk"
                        if sql_fragment and _is_valid_sql_fragment(sql_fragment):
                            msg += f" (detected SQL pattern in query)"
                        issues.append(_issue(node.lineno, "Security", "HIGH", msg))

                    # f-string: f"SELECT ... {var}"
                    elif isinstance(arg, ast.JoinedStr):
                        has_expr = any(
                            isinstance(v, ast.FormattedValue) for v in arg.values
                        )
                        if has_expr:
                            issues.append(_issue(node.lineno, "Security", "HIGH",
                                                 "SQL query built with f-string — injection risk"))

                    # %-formatting: "SELECT ... %s" % var
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                        issues.append(_issue(node.lineno, "Security", "HIGH",
                                             "SQL query built with %-formatting — injection risk"))

                    # .format(): "SELECT ... {}".format(var)
                    elif (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute)
                          and arg.func.attr == "format"):
                        issues.append(_issue(node.lineno, "Security", "HIGH",
                                             "SQL query built with .format() — injection risk"))


def _try_extract_str(node):
    """Try to extract a string constant from a BinOp (concat) node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _try_extract_str(node.left)
        if left:
            return left
        return _try_extract_str(node.right)
    return None


def _is_valid_sql_fragment(fragment):
    """Check if a string fragment looks like valid SQL using sqlglot."""
    try:
        result = sqlglot.parse(fragment)
        return any(r is not None for r in result)
    except Exception:
        return False


def _check_sql_injection_regex(code, issues):
    """Fallback regex-based SQL injection detection."""
    for i, line in enumerate(code.splitlines(), 1):
        if re.search(r'(?i)execute\s*\(\s*["\'].*["\'\s]*\+', line):
            issues.append(_issue(i, "Security", "HIGH",
                                 "SQL query built with string concat — injection risk"))
        if re.search(r'(?i)execute\s*\(\s*f["\']', line):
            issues.append(_issue(i, "Security", "HIGH",
                                 "SQL query built with f-string — injection risk"))


# ── RUNNER ───────────────────────────────────────────────────────────────────

def run(code, filepath="<unknown>"):
    """Run all checks. Returns findings dict."""
    tree, syntax_issues = check_syntax(code)

    if tree is None:
        return {"file": filepath, "issues": syntax_issues, "score": 0}

    issues = (syntax_issues
              + check_semantic(tree)
              + check_complexity(tree)
              + check_style(code, tree)
              + check_security(code, tree))

    # Score: start 100, deduct by severity
    penalty = sum({"ERROR": 20, "HIGH": 10, "WARNING": 5, "MEDIUM": 3, "INFO": 1}
                  .get(i["severity"], 0) for i in issues)
    score = max(0, 100 - penalty)

    return {"file": filepath, "issues": issues, "score": score}
