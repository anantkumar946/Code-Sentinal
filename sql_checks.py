"""
sql_checks.py — SQL analysis using sqlglot AST for CodeSentinel.
Provides syntax validation, style checks, and best-practice enforcement.
"""

import sqlglot
from sqlglot import errors as sqlglot_errors
from sqlglot import exp as sqlglot_exp
from suggestions import get_suggestion


def _issue(line, category, severity, message):
    """Create an issue dict with an auto-attached fix suggestion."""
    return {
        "line": line,
        "category": category,
        "severity": severity,
        "message": message,
        "suggestion": get_suggestion(category, message),
    }


# ── 1. SQL SYNTAX ───────────────────────────────────────────────────────────

def check_sql_syntax(sql):
    """Parse SQL and return (parsed_expressions, issues)."""
    try:
        expressions = sqlglot.parse(sql)
        # Filter out None entries (empty statements)
        expressions = [e for e in expressions if e is not None]
        if not expressions:
            return None, [_issue(1, "SQL", "ERROR",
                                 "No valid SQL statements found in the input.")]
        return expressions, []
    except sqlglot_errors.ParseError as e:
        return None, [_issue(1, "SQL", "ERROR",
                             f"SQL Parse error: {str(e)}")]


# ── 2. SQL STYLE ────────────────────────────────────────────────────────────

def check_sql_style(expressions):
    """Check SQL style issues via AST inspection."""
    issues = []

    for expr in expressions:
        # SELECT * detection
        for select in expr.find_all(sqlglot_exp.Select):
            for sel_expr in select.expressions:
                if isinstance(sel_expr, sqlglot_exp.Star):
                    issues.append(_issue(1, "SQL", "WARNING",
                                         "SELECT * — specify columns explicitly for clarity and performance"))
                elif isinstance(sel_expr, sqlglot_exp.Column) and sel_expr.name == "*":
                    issues.append(_issue(1, "SQL", "WARNING",
                                         "SELECT * — specify columns explicitly for clarity and performance"))

        # UPDATE/DELETE without WHERE
        for node in expr.find_all(sqlglot_exp.Update):
            if not node.find(sqlglot_exp.Where):
                issues.append(_issue(1, "SQL", "HIGH",
                                     "UPDATE without WHERE — missing WHERE clause risks modifying all rows"))

        for node in expr.find_all(sqlglot_exp.Delete):
            if not node.find(sqlglot_exp.Where):
                issues.append(_issue(1, "SQL", "HIGH",
                                     "DELETE without WHERE — missing WHERE clause risks deleting all rows"))

        # Unaliased subqueries in FROM
        for subquery in expr.find_all(sqlglot_exp.Subquery):
            if not subquery.alias:
                issues.append(_issue(1, "SQL", "INFO",
                                     "Subquery without alias — add an unaliased subquery alias for readability"))

    return issues


# ── 3. SQL BEST PRACTICES ──────────────────────────────────────────────────

def check_sql_best_practices(expressions):
    """Check SQL best practices via AST inspection."""
    issues = []

    for expr in expressions:
        # Unbounded SELECT (no LIMIT)
        if isinstance(expr, sqlglot_exp.Select):
            has_limit = expr.find(sqlglot_exp.Limit)
            has_agg = any(
                isinstance(s, (sqlglot_exp.Count, sqlglot_exp.Sum, sqlglot_exp.Avg,
                                sqlglot_exp.Min, sqlglot_exp.Max))
                for s in expr.find_all(sqlglot_exp.AggFunc)
            )
            # Only flag if not an aggregate and no limit
            if not has_limit and not has_agg:
                issues.append(_issue(1, "SQL", "INFO",
                                     "SELECT without LIMIT — consider adding LIMIT to prevent unbounded result sets"))

        # Multiple OR that could be IN
        for where in expr.find_all(sqlglot_exp.Where):
            or_count = 0
            same_col = set()
            for or_node in where.find_all(sqlglot_exp.Or):
                or_count += 1
                # Check if both sides compare the same column
                for eq in or_node.find_all(sqlglot_exp.EQ):
                    col = eq.find(sqlglot_exp.Column)
                    if col:
                        same_col.add(col.name)
            if or_count >= 2 and len(same_col) == 1:
                issues.append(_issue(1, "SQL", "INFO",
                                     f"Multiple OR conditions on '{same_col.pop()}' — consider using IN instead of OR chains"))

    return issues


# ── 4. SQL ANTI-PATTERNS ───────────────────────────────────────────────────

def check_sql_antipatterns(expressions):
    """Check for common SQL anti-patterns via AST inspection."""
    issues = []

    for expr in expressions:
        # SELECT DISTINCT overuse (often masks a bad join)
        for select in expr.find_all(sqlglot_exp.Select):
            if select.args.get("distinct"):
                issues.append(_issue(1, "SQL", "INFO",
                    "SELECT DISTINCT may indicate a bad join or missing "
                    "constraint — verify the query logic before relying "
                    "on DISTINCT to deduplicate results"))

        # Implicit joins (comma-separated FROM)
        for join in expr.find_all(sqlglot_exp.Join):
            join_kind = join.args.get("kind", "")
            join_side = join.args.get("side", "")
            join_on = join.args.get("on")
            join_using = join.args.get("using")
            if not join_kind and not join_side and not join_on and not join_using:
                issues.append(_issue(1, "SQL", "WARNING",
                    "implicit join (comma-separated FROM) detected — use "
                    "explicit JOIN ... ON syntax for readability and "
                    "correctness"))
                break

        # = NULL instead of IS NULL
        for eq in expr.find_all(sqlglot_exp.EQ):
            if isinstance(eq.right, sqlglot_exp.Null) or isinstance(eq.left, sqlglot_exp.Null):
                issues.append(_issue(1, "SQL", "WARNING",
                    "Comparison with NULL using '=' — use IS NULL instead "
                    "(= NULL always evaluates to NULL, not TRUE/FALSE)"))

        # != NULL instead of IS NOT NULL
        for neq in expr.find_all(sqlglot_exp.NEQ):
            if isinstance(neq.right, sqlglot_exp.Null) or isinstance(neq.left, sqlglot_exp.Null):
                issues.append(_issue(1, "SQL", "WARNING",
                    "Comparison with NULL using '!='/'<>' — use IS NOT NULL "
                    "instead (comparisons with NULL always evaluate to NULL)"))

        # ORDER BY without LIMIT
        if isinstance(expr, sqlglot_exp.Select):
            has_order = expr.find(sqlglot_exp.Order)
            has_limit = expr.find(sqlglot_exp.Limit)
            if has_order and not has_limit:
                issues.append(_issue(1, "SQL", "INFO",
                    "ORDER BY without LIMIT — sorting without a bound can "
                    "be expensive on large result sets"))

        # Nested subqueries that could be CTEs
        for subquery in expr.find_all(sqlglot_exp.Subquery):
            nested = list(subquery.find_all(sqlglot_exp.Subquery))
            # nested includes the subquery itself, so > 1 means truly nested
            if len(nested) > 1:
                issues.append(_issue(1, "SQL", "INFO",
                    "Nested subquery detected — consider refactoring to a "
                    "Common Table Expression (CTE) for readability"))
                break

        # LIKE with leading wildcard (prevents index usage)
        for like in expr.find_all(sqlglot_exp.Like):
            pattern = like.expression
            if isinstance(pattern, sqlglot_exp.Literal) and pattern.is_string:
                val = pattern.this
                if val.startswith("%"):
                    issues.append(_issue(1, "SQL", "WARNING",
                        "LIKE with leading wildcard '%...' — prevents index "
                        "usage and causes full table scans. Consider "
                        "full-text search instead"))

        # INSERT without explicit column list
        for insert in expr.find_all(sqlglot_exp.Insert):
            if not insert.args.get("columns"):
                # Only flag INSERT ... VALUES, not INSERT ... SELECT
                if insert.find(sqlglot_exp.Values):
                    issues.append(_issue(1, "SQL", "WARNING",
                        "INSERT without explicit column list — fragile to "
                        "schema changes. Specify columns: "
                        "INSERT INTO table (col1, col2) VALUES (...)"))

    return issues


# ── RUNNER ──────────────────────────────────────────────────────────────────

def run_sql(sql, filepath="<stdin>"):
    """Run all SQL checks. Returns findings dict."""
    expressions, syntax_issues = check_sql_syntax(sql)

    if expressions is None:
        return {"file": filepath, "issues": syntax_issues, "score": 0}

    issues = (syntax_issues
              + check_sql_style(expressions)
              + check_sql_best_practices(expressions)
              + check_sql_antipatterns(expressions))

    # Score: start 100, deduct by severity
    penalty = sum({"ERROR": 20, "HIGH": 10, "WARNING": 5, "MEDIUM": 3, "INFO": 1}
                  .get(i["severity"], 0) for i in issues)
    score = max(0, 100 - penalty)

    return {"file": filepath, "issues": issues, "score": score}
