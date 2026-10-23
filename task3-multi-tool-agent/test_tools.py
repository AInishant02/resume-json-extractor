"""Step 2: test each tool on its own."""
from tools import calculator, read_file, list_files, web_search


def show(label, output):
    print(f"\n>>> {label}")
    print(str(output)[:500])


show("calculator: 12500 / 5", calculator.invoke({"expression": "12500 / 5"}))
show("calculator: sqrt(144) + 2**3", calculator.invoke({"expression": "sqrt(144) + 2**3"}))
show("calculator: 1 / 0", calculator.invoke({"expression": "1 / 0"}))
show("calculator: huge exponent", calculator.invoke({"expression": "2 ** 100000"}))
show("calculator: code injection attempt",
     calculator.invoke({"expression": "__import__('os').system('dir')"}))

show("list_files", list_files.invoke({}))
show("read_file: project_notes.txt", read_file.invoke({"filename": "project_notes.txt"}))
show("read_file: expenses.csv", read_file.invoke({"filename": "expenses.csv"}))
show("read_file: missing.txt", read_file.invoke({"filename": "missing.txt"}))
show("read_file: ../.env (escape attempt)", read_file.invoke({"filename": "../.env"}))

show("web_search: capital of Japan", web_search.invoke({"query": "capital of Japan"}))