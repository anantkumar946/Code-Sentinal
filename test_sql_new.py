"""Quick test for new SQL anti-pattern checks."""
import json
from sql_checks import run_sql

tests = [
    ("SELECT DISTINCT", "SELECT DISTINCT name FROM users"),
    ("Implicit join", "SELECT * FROM a, b WHERE a.id = b.id"),
    ("= NULL", "SELECT * FROM users WHERE name = NULL"),
    ("!= NULL", "SELECT * FROM users WHERE name != NULL"),
    ("ORDER BY no LIMIT", "SELECT * FROM users ORDER BY name"),
    ("Nested subquery", "SELECT * FROM (SELECT * FROM (SELECT id FROM t) AS inner_q) AS outer_q"),
    ("LIKE leading %", "SELECT * FROM users WHERE name LIKE '%john%'"),
    ("INSERT no columns", "INSERT INTO users VALUES (1, 'alice', 'alice@test.com')"),
]

for label, sql in tests:
    result = run_sql(sql)
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"SQL:  {sql}")
    print(f"Score: {result['score']}")
    for issue in result["issues"]:
        print(f"  [{issue['severity']}] {issue['message']}")
        print(f"    FIX: {issue['suggestion'][:80]}...")
