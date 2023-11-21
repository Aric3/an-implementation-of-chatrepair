# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import os
import re

from enum import Enum
from javalang import parse
from javalang.tree import MethodDeclaration


class Cons(Enum):
    Chart = "Chart"
    Closure = "Closure"
    Lang = "Lang"
    Math = "Math"
    Mockito = "Mockito"
    Time = "Time"
    Patches_base_folder = "patches"
    Buggy_Folder = "bugs"
    INFILL = "[INFILL]\n"

    Defects4j_Checkout = "defects4j checkout -p %s -v %s -w %s"
    Defects4j_Compile_Test = "defects4j compile ; defects4j test"

    Initial_1 = ("You are an automated program repair tool.\n"
                 "The following function contains a buggy hunk that has been replaced by the mark [INFILL]:")
    Initial_2 = "This was the original buggy hunk which was replaced by the [INFILL] mark:\n"
    Initial_3 = "The code fails on this test:\n"
    Initial_4 = "on this test line:\n"
    Initial_5 = "with the following test error:\n"
    Initial_6 = ("Please provide the correct lines at the [INFILL] location. Your code should be a replacement for ["
                 "INFILL], so don't include lines of code before and after [INFILL].")


# ChatRepair 算法

# 1.
def initial_input(project):
    base_dir = os.path.dirname(__file__)
    project_path = os.path.join(os.path.join(base_dir, Cons.Patches_base_folder.value), project)
    files = os.listdir(project_path)
    for file in files:
        no = file.strip('.json')
        with open(os.path.join(project_path, file), 'r') as f:
            data = json.load(f)
            num_of_hunks = data['num_of_hunks']
            if num_of_hunks == 1:
                os.system(Cons.Defects4j_Checkout.value % (
                    project, no + 'b', Cons.Buggy_Folder.value + '/' + project + no))
                os.system(
                    'cd ' + Cons.Buggy_Folder.value + '/' + project + no + ' && ' + Cons.Defects4j_Compile_Test.value)
                file_name = data['0']['file_name']
                patch_type = data['0']['patch_type']
                input = Cons.Initial_1.value
                buggy_function = ''
                if patch_type == 'replace':
                    from_line_no = data['0']['from_line_no']
                    to_line_no = data['0']['to_line_no']
                    replaced = data['0']['replaced']
                    buggy_function = ''.join(
                        find_buggy_function(
                            Cons.Buggy_Folder.value + '/' + project + no + '/' + file_name,
                            from_line_no, to_line_no, 'replace'))
                    input = input + buggy_function + Cons.Initial_2.value + replaced + Cons.Initial_3.value

                if patch_type == 'insert':
                    next_line_no = data['0']['next_line_no']
                    buggy_function = ''.join(
                        find_buggy_function(
                            Cons.Buggy_Folder.value + '/' + project + no + '/' + file_name,
                            next_line_no, next_line_no, 'insert'))
                print(buggy_function)


def find_buggy_function(file_path, from_line_no, to_line_no, patch_type):
    with open(file_path, "r") as file:
        source_code = file.read()
    tree = parse.parse(source_code)
    line_nos = []
    target_line = 0
    for path, node in tree.filter(MethodDeclaration):
        line_nos.append(node.position.line)
    for i in range(0, len(line_nos) - 2):
        if line_nos[i] <= from_line_no <= line_nos[i + 1]:
            target_line = line_nos[i]
    if target_line == 0:
        target_line = line_nos[len(line_nos) - 1]
    with open(file_path, "r") as file:
        lines = file.readlines()[target_line - 1:]
    open_brackets = 0
    function_lines = []
    for line in lines:
        function_lines.append(line)
        open_brackets += line.count('{')
        open_brackets -= line.count('}')
        if open_brackets == 0:
            break
    if patch_type == 'replace':
        del function_lines[from_line_no - target_line:to_line_no - target_line + 1]
        function_lines.insert(from_line_no - target_line, Cons.INFILL.value)
    return function_lines


def find_failing_test(file_path, tests, errors, files, lines):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines) - 1):
            if re.match(r'^---', lines[i]):
                tests.append(lines[i].strip('---'))
                errors.append(lines[i + 1])
            match = re.search(r'\(.*Test\.java:(\d+)\)$', lines[i])
            if match:
                files.append(''.join(re.findall(r'[A-Za-z0-9]+\.', lines[i])[0:-1])).replace('.', '/')
                lines.append(match.group(1))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    initial_input(Cons.Lang.value)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
