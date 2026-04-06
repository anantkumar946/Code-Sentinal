import os
import sys
import pickle  # unused import + dangerous module

# Hardcoded secrets (Security)
password = "admin123"
API_KEY = "sk-abc123secretkey"

# Magic numbers + camelCase naming (Style + Semantic)
def calculateCircleArea(radius):
    unused_var = 99
    area = 3.14159 * radius * radius
    return area

# Deep nesting (Complexity)
def process_numbers(data):
    result = []
    for item in data:
        if item > 0:
            if item > 100:
                if item > 1000:
                    if item > 9999:
                        result.append(item * 2)
    return result

# Security issues: eval + SQL injection
class myDataHandler:
    def run_query(self, user_input):
        query = "SELECT * FROM users WHERE name = " + user_input
        code = input("Enter expression: ")
        eval(code)
        return query

    def load_data(self, filename):
        with open(filename, "rb") as f:
            return pickle.load(f)   # unsafe deserialization

# Unused variables
x = 10
y = 20
unused_result = x + y

# Bare except + comparison to None (Style)
def fetch_data(value):
    try:
        if value == None:
            return []
        if value == True:
            return [1, 2, 3]
    except:
        pass

# Missing docstring, long line (Style)
def compute_statistics(numbers):
    total = sum(numbers); average = total / len(numbers); minimum = min(numbers); maximum = max(numbers)
    return total, average, minimum, maximum

# subprocess shell=True (Security)
import subprocess
def run_command(cmd):
    subprocess.run(cmd, shell=True)
