import json
import linecache
import os
import re
import openai

from javalang import parse
from javalang.tree import MethodDeclaration
from constants import *


def go_chat_repair(project):
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = initial_input(project, file)
        if not initial_prompt == '':
            chat_repair(project, initial_prompt)


def chat_repair(project, initial_prompt):
    current_tries = 0
    plausible_patches = []
    context = []
    openai.api_key = API_KEY
    # while current_tries < Max_Tries and plausible_patches is None:
    #    current_length = 0
    prompt = initial_prompt
    #    while current_length < Max_Conv_len:
    context.append({'role': 'user', 'content': prompt})
    response = openai.Completion.create(model='gpt-3.5-turbo-0301', message=context)
    result = response.choices[0].message['content']
    context.append({'role': 'assistant', 'content': result})
    print(result)


def validate(patch, project, json_file):
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
        file_name = data['0']['file_name']
        patch_type = data['0']['patch_type']
        # replace
        if patch_type == 'replace':
            from_line_no = data['0']['from_line_no']
            to_line_no = data['0']['to_line_no']
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='r', encoding='latin-1') as f:
                lines = f.readlines()
            del lines[from_line_no - 1:to_line_no - 1]
            lines.insert(from_line_no - 1, patch)
            f.close()
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
        if patch_type == 'insert':
            next_line_no = data['0']['next_line_no']
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='r', encoding='latin-1') as f:
                lines = f.readlines()
            lines.insert(next_line_no, patch)
            f.close()
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
        # re compile and test
        os.system(
            'cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE_TEST)

        return is_file_empty_or_not_exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE))


def is_file_empty_or_not_exists(file_path):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return True  # 文件不存在

    # 检查文件大小
    file_size = os.path.getsize(file_path)

    # 判断文件是否为空或不存在
    if file_size == 0:
        return True  # 文件为空
    else:
        return False  # 文件非空


def initial_input(project, json_file):
    # read the specified patch json file
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
        num_of_hunks = data['num_of_hunks']
        # only deal with single hunk bugs
        if num_of_hunks == 1:
            # if project folder doesn't exist then run defects4j checkout
            if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
                os.system(DEFECTS4J_CHECKOUT % (
                    project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
            file_name = data['0']['file_name']
            patch_type = data['0']['patch_type']
            initial_prompt = ''
            # replace
            if patch_type == 'replace':
                from_line_no = data['0']['from_line_no']
                to_line_no = data['0']['to_line_no']
                original_buggy_hunk = data['0']['replaced']
                # find the original buggy function, add infill mark
                buggy_function = ''.join(
                    find_buggy_function(os.path.join(
                        BUGGY_PROJECT_FOLDER, project + no, file_name),
                        from_line_no, to_line_no, 'replace'))
                # construct the initial prompt
                initial_prompt = INITIAL_1 + buggy_function + INITIAL_2 + original_buggy_hunk
            # insert
            if patch_type == 'insert':
                next_line_no = data['0']['next_line_no']
                buggy_function = ''.join(
                    find_buggy_function(os.path.join(
                        BUGGY_PROJECT_FOLDER, project + no, file_name),
                        next_line_no, next_line_no, 'insert'))
                initial_prompt = INITIAL_7 + buggy_function
            # If failing_test doesn't exists then run defects4j compile ; defects4j test
            failing_test = os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)
            if not os.path.exists(failing_test):
                os.system(
                    'cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE_TEST)
            # find the failing tests, test line and error message
            tests = []
            errors = []
            files = []
            test_lines = []
            find_failing_test(failing_test, tests, errors, files, test_lines)
            for i in range(0, len(tests)):
                file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX, files[i])
                if not os.path.exists(file):
                    file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX_JAVA, files[i])
                # get the test line in case multi line
                test_line = linecache.getline(file, test_lines[i])
                initial_prompt = initial_prompt + INITIAL_3 + tests[
                    i] + INITIAL_4 + test_line + INITIAL_5 + errors[i]
            # complete the initial prompt
            if patch_type == 'replace':
                initial_prompt += INITIAL_6
            if patch_type == 'insert':
                initial_prompt += INITIAL_8
            return initial_prompt
        else:
            return ''


# find the original buggy function
def find_buggy_function(file_path, from_line_no, to_line_no, patch_type):
    # get the line number of the target function declaration
    with open(file_path, "r") as file:
        source_code = file.read()
        file.close()
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
    # get the target function, replace the buggy hunk
    with open(file_path, "r", encoding='latin-1') as file:
        lines = file.readlines()[target_line - 1:]
        file.close()
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


# find the failing tests, test line and error message
def find_failing_test(file_path, tests, errors, files, test_lines):
    with open(file_path, 'r', encoding='latin-1') as file:
        lines = file.readlines()
        for i in range(0, len(lines)):
            # match '--- org.apache.commons.lang3.StringUtilsTest::testEscapeSurrogatePairs
            # java.lang.StringIndexOutOfBoundsException: String index out of range: 2'
            if re.match(r'^---', lines[i]):
                tests.append(lines[i].strip('---'))
                errors.append(lines[i + 1])
            # match 'at org.apache.commons.lang3.StringUtilsTest.testEscapeSurrogatePairs(StringUtilsTest.java:2187)'
            match = re.search(r'\(.*Test\.java:(\d+)\)$', lines[i])
            if match:
                # org/apache/commons/lang3/StringUtilsTest
                files.append(
                    ''.join(re.findall(r'[A-Za-z0-9]+\.', lines[i])[0:-1]).replace('.', '/')[:-1] + '.java')
                # 2187
                test_lines.append(int(match.group(1)))


if __name__ == '__main__':
    go_chat_repair(LANG)
