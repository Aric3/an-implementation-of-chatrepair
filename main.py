import json
import os
import re
import linecache

from javalang import parse
from javalang.tree import MethodDeclaration
from constants import *


# ChatRepair Algorithm
def initial_input(project):
    base_dir = os.path.dirname(__file__)
    project_path = os.path.join(os.path.join(base_dir, PATCH_JSON_FOLDER), project)
    files = os.listdir(project_path)
    # read the 'patches' folder
    for file in files:
        no = file.strip('.json')
        with open(os.path.join(project_path, file), 'r', encoding="latin-1") as f:
            data = json.load(f)
            num_of_hunks = data['num_of_hunks']
            if num_of_hunks == 1:
                # if project folder doesn't exist then run defects4j checkout
                if not os.path.exists(BUGGY_PROJECT_FOLDER + '/' + project + no):
                    os.system(DEFECTS4J_CHECKOUT.value % (
                        project, no + 'b', BUGGY_PROJECT_FOLDER + '/' + project + no))

                file_name = data['0']['file_name']
                patch_type = data['0']['patch_type']
                INITIAL_prompt = ''
                if patch_type == 'replace':
                    from_line_no = data['0']['from_line_no']
                    to_line_no = data['0']['to_line_no']
                    original_buggy_hunk = data['0']['replaced']
                    buggy_function = ''.join(
                        find_buggy_function(
                            BUGGY_PROJECT_FOLDER + '/' + project + no + '/' + file_name,
                            from_line_no, to_line_no, 'replace'))
                    INITIAL_prompt = INITIAL_1.value + buggy_function + INITIAL_2 + original_buggy_hunk
                if patch_type == 'insert':
                    next_line_no = data['0']['next_line_no']
                    buggy_function = ''.join(
                        find_buggy_function(
                            BUGGY_PROJECT_FOLDER + '/' + project + no + '/' + file_name,
                            next_line_no, next_line_no, 'insert'))
                    INITIAL_prompt = INITIAL_7 + buggy_function
                # If failing_test doesn't exists then run defects4j compile ; defects4j test
                failing_test = BUGGY_PROJECT_FOLDER + '/' + project + no + '/' + FAILING_TEST_FILE
                if not os.path.exists('./' + failing_test):
                    os.system(
                        'cd ' + BUGGY_PROJECT_FOLDER + '/' + project + no + ' && ' + DEFECTS4J_COMPILE_TEST)
                tests = []
                errors = []
                files = []
                test_lines = []
                find_failing_test(failing_test, tests, errors, files, test_lines)
                for i in range(0, len(tests)):
                    file = BUGGY_PROJECT_FOLDER + '/' + project + no + TEST_PATH_PREFIX + files[i]
                    if not os.path.exists(file):
                        file = BUGGY_PROJECT_FOLDER + '/' + project + no + TEST_PATH_PREFIX_JAVA + \
                               files[i]
                    test_line = linecache.getline(file, test_lines[i])
                    INITIAL_prompt = INITIAL_prompt + INITIAL_3 + tests[
                        i] + INITIAL_4 + test_line + INITIAL_5 + errors[i]
                if patch_type == 'replace':
                    INITIAL_prompt += INITIAL_6
                if patch_type == 'insert':
                    INITIAL_prompt += INITIAL_8;
                return INITIAL_prompt


# 1.construct the initial input
def find_buggy_function(file_path, from_line_no, to_line_no, patch_type):
    with open(file_path, "r") as file:
        source_code = file.read()
    tree = parse.parse(source_code)
    line_nos = []
    target_line = 0
    for path, node in tree.filter(MethodDeclaration):
        line_nos.append(node.position.line)
    for i in range(0, len(line_nos) - 1):
        if line_nos[i] <= from_line_no <= line_nos[i + 1]:
            target_line = line_nos[i]
    if target_line == 0:
        target_line = line_nos[len(line_nos) - 1]
    with open(file_path, "r") as file:
        lines = file.readlines()[target_line - 1:]
    left_open_brackets = 0
    right_open_brackets = 0
    function_lines = []
    for line in lines:
        function_lines.append(line)
        left_open_brackets += line.count('{')
        right_open_brackets += line.count('}')
        if left_open_brackets == right_open_brackets and not left_open_brackets == 0:
            break
    if patch_type == 'replace':
        del function_lines[from_line_no - target_line:to_line_no - target_line + 1]
        function_lines.insert(from_line_no - target_line, INFILL)
    return function_lines


def find_failing_test(file_path, tests, errors, files, test_lines):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines)):
            if re.match(r'^---', lines[i]):
                tests.append(lines[i].strip('---'))
                errors.append(lines[i + 1])
            match = re.search(r'\(.*Test\.java:(\d+)\)$', lines[i])
            if match:
                files.append(
                    ''.join(re.findall(r'[A-Za-z0-9]+\.', lines[i])[0:-1]).replace('.', '/')[:-1] + '.java')
                test_lines.append(int(match.group(1)))


if __name__ == '__main__':
    initial_input(LANG)
