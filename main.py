"""
CodeSentinel — Python Static Code Analyzer
Usage:
    python main.py test.py
    python main.py test.py --html
    python main.py test.py --html --output my_report.html
"""

import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks import run
from report import print_terminal, generate_html


def main():
    parser = argparse.ArgumentParser(description="CodeSentinel — Python Static Analyzer")
    parser.add_argument("file",             help="Python file to analyze")
    parser.add_argument("--html",           action="store_true", help="Generate HTML report")
    parser.add_argument("--output",         default="report.html", help="HTML output path")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    if not args.file.endswith(".py"):
        print("[ERROR] Only .py files are supported.")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        code = f.read()

    findings = run(code, args.file)
    print_terminal(findings)

    if args.html:
        path = generate_html(findings, args.output)
        print(f"\n  HTML report → {path}\n")


if __name__ == "__main__":
    main()
