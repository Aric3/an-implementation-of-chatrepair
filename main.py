import json
import os
import re
import shutil
import time
import openai
import subprocess
from javalang import parse
from javalang.tree import MethodDeclaration
from constants import *


def go_chat_repair(project):
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = construct_initial_prompt(project, file)
        if not initial_prompt == '':
            #     plausible_patches = chat_repair(project, initial_prompt, file)
            #     print(plausible_patches)
            f = open_file(os.path.join(INITIAL_PROMPT_FOLDER, project, file.rstrip(".json") + ".txt"))
            f.write(initial_prompt)


def chat_repair(project, initial_prompt, json_file):
    current_tries = 0
    plausible_patches = []
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    # 找到一个plausible patch
    while current_tries < Max_Tries and len(plausible_patches) == 0:
        context = []
        current_length = 0
        prompt = initial_prompt
        while current_length < Max_Conv_len:
            context.append({'role': 'user', 'content': prompt})
            response = openai.chat.completions.create(model=Model, messages=context)
            # 程序停止25s
            # time.sleep(25)
            response_text = response.choices[0].message.content
            context.append({'role': 'assistant', 'content': response_text})
            patch = match_patch_code(response_text)
            # 不符合规范的回答文本 跳过此次对话
            if patch == '':
                break
            feedback = validate_patch(patch, project, json_file, plausible_patches)
            if feedback == '':
                break
            else:
                prompt = feedback
            current_length += 1
            current_tries += 1
        # 保存对话到文件中
        context_path = os.path.join(CONVERSATION_FOLDER, project, 'bug' + json_file.rstrip('.json'),
                                    str(current_tries) + '.txt')
        file = open_file(context_path)
        for element in context:
            file.write(element['content'])
            file.write('\n')
        file.close()
    # 当有一个plausible patch时 generate更多的plausible patch
    if len(plausible_patches) != 0:
        while current_tries < Max_Tries:
            context = []
            prompt = initial_prompt.rstrip(INITIAL_6).rstrip(INITIAL_8) + Alt_Instruct_1 + '\n'.join(
                plausible_patches) + Alt_Instruct_2
            context.append({'role': 'user', 'content': prompt})
            response = openai.chat.completions.create(model=Model, messages=context)
            # 程序停止25s
            # time.sleep(25)
            response_text = response.choices[0].message.content
            context.append({'role': 'assistant', 'content': response_text})
            patch = match_patch_code(response_text)
            # 不符合规范的回答文本 跳过此次对话
            if patch == '':
                continue
            feedback = validate_patch(patch, project, json_file, plausible_patches)
            if feedback == '' and patch not in plausible_patches:
                plausible_patches.append(patch)
            current_tries += 1
            # 保存对话到文件中
            context_path = os.path.join(CONVERSATION_FOLDER, project, 'bug' + json_file.rstrip('.json'),
                                        str(current_tries) + '.txt')
            file = open_file(context_path)
            for element in context:
                file.write(element['content'])
                file.write('\n')
            file.close()
    return plausible_patches


# 验证对应patch 并构造feedback
def validate_patch(patch, project, json_file, plausible_patches):
    no = json_file.rstrip('.json')
    # 如果还没有对应bug的文件夹 运行defects4j checkout
    if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
        os.system(DEFECTS4J_CHECKOUT % (
            project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
        file_name = data['0']['file_name']
        patch_type = data['0']['patch_type']
        # replace类型的patch 找到对应的源代码文件 使用patch替换掉指定行
        if patch_type == 'replace':
            from_line_no = data['0']['from_line_no']
            to_line_no = data['0']['to_line_no']
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='r', encoding='latin-1') as f1:
                lines = f1.readlines()
            del lines[from_line_no - 1:to_line_no]
            lines.insert(from_line_no - 1, patch)
            f1.close()
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
        # insert类型的patch 找到的对应的函数 替换整个函数
        if patch_type == PATCH_TYPE_INSERT:
            next_line_no = data['0']['next_line_no']
            # 获得函数声明所在的行
            source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
            start_line = get_method_declaration_line_no(source_file_path, next_line_no)
            # 替换掉整个函数
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), "r", encoding='latin-1') as file:
                lines = file.readlines()
                file.close()
            left_open_brackets = 0
            right_open_brackets = 0
            end_line = start_line - 1
            for line in lines[start_line - 1:-1]:
                left_open_brackets += line.count('{')
                right_open_brackets += line.count('}')
                end_line += 1
                if left_open_brackets == right_open_brackets and not left_open_brackets == 0:
                    break
            del lines[start_line - 1:end_line]
            lines.insert(start_line - 1, patch)
            file.close()
            with open(os.path.join(
                    BUGGY_PROJECT_FOLDER, project + no, file_name), mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
        # 重新编译
        stdout, stderr = run_command(
            'cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE)
        pattern = r"compile:(.*?)BUILD FAILED"
        result = re.search(pattern, stderr, re.DOTALL)
        # 有编译错误 构造feedback
        if result:
            output = result.group(1).strip()
            feedback = FeedBack_2 + output
            return feedback
        # 没有编译错误 运行defects4j test
        else:
            os.system('cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_TEST)
            # pass全部test 添加plausible_patch
            if is_file_empty_or_not_exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)):
                plausible_patches.append(patch)
                return ''
            # 未通过全部test 构造feedback
            failing_test_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)
            failing_test, test_error, test_file, test_line_no = get_failing_test_info(failing_test_path)
            file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX, test_file)
            if not os.path.exists(file):
                file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX_JAVA, test_file)
            # get the test line
            test_lines = []
            with open(file, mode='r', encoding='latin-1') as test_file:
                lines = test_file.readlines()[test_line_no - 1:]
                for line in lines:
                    test_lines.append(line)
                    if line.count(';') == 1:
                        break
            feedback = FeedBack_1 + INITIAL_3 + failing_test + INITIAL_4 + ''.join(test_lines) + INITIAL_5 + test_error
            # 删除checkout的项目文件
            shutil.rmtree(os.path.join(BUGGY_PROJECT_FOLDER, project + no))
            return feedback


# 从chat gpt文本中提取代码部分
def match_patch_code(response_text):
    pattern = r"```java(.*)```"
    match = re.search(pattern, response_text, re.DOTALL)
    if match is None:
        pattern = r"```(.*)```"
        match = re.search(pattern, response_text, re.DOTALL)
    # 不符合规范的回答文本 停止此次对话
    if match is None:
        return ''
    return match.group(1)


# 判读文件是否存在或为空
def is_file_empty_or_not_exists(file_path):
    if not os.path.exists(file_path):
        return True
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return True
    else:
        return False


# 运行系统命令并返回标准输出与标准错误输出
def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()

    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')

    return stdout, stderr


# 打开文件 如果不存在则创建
def open_file(path):
    # 检查路径是否存在
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    file = open(path, 'w')
    return file


def construct_initial_prompt(project, json_file):
    # 读对应json文件
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
        num_of_hunks = data['num_of_hunks']
        if num_of_hunks == 1:
            # 如果还没有对应bug的文件夹 运行defects4j checkout
            if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
                os.system(DEFECTS4J_CHECKOUT % (
                    project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
            file_name = data['0']['file_name']
            patch_type = data['0']['patch_type']
            initial_prompt = INITIAL_APR_tool
            # replace类型的patch
            if patch_type == PATCH_TYPE_REPLACE:
                from_line_no = data['0']['from_line_no']
                to_line_no = data['0']['to_line_no']
                original_buggy_hunk = data['0']['replaced']
                source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
                buggy_function = get_buggy_function(source_file_path, from_line_no, to_line_no, PATCH_TYPE_REPLACE)
                # construct the initial prompt
                # single line的patch
                if from_line_no == to_line_no:
                    initial_prompt += INITIAL_Single_line + buggy_function + INITIAL_Single_line_2 + original_buggy_hunk
                # single hunk的patch
                else:
                    initial_prompt += INITIAL_Single_hunk + buggy_function + INITIAL_Single_hunk_2 + original_buggy_hunk
            # delete类型的patch
            if patch_type == PATCH_TYPE_DELETE:
                next_line_no = data['0']['next_line_no']
                source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
                buggy_function = get_buggy_function(source_file_path, from_line_no, next_line_no, PATCH_TYPE_DELETE)
                initial_prompt += INITIAL_Single_function + buggy_function
            # insert类型的patch
            if patch_type == PATCH_TYPE_INSERT:
                next_line_no = data['0']['next_line_no']
                source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
                buggy_function = get_buggy_function(source_file_path, next_line_no, next_line_no, PATCH_TYPE_INSERT)
                initial_prompt += INITIAL_Single_function + buggy_function

            # 如果不存在failing test文件或为空 说明没有执过defects4j test命令 执行
            failure_test_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)
            if is_file_empty_or_not_exists(failure_test_path):
                os.system(
                    'cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE_TEST)

            # 添加关于failing test的信息
            failing_test, test_error, test_file, test_line_no = get_failing_test_info(failure_test_path)
            file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX, test_file)
            if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX, test_file)):
                file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX_JAVA, test_file)
                if not os.path.exists(file):
                    file = os.path.join(BUGGY_PROJECT_FOLDER, project + no,TEST_PATH_PREFIX_1, test_file)
                    if not os.path.exists(file):
                        file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_PATH_PREFIX_2, test_file)
            # 根据test line所在的行到对应文件找到目标line
            test_lines = []
            with open(file, mode='r', encoding='latin-1') as test_file:
                lines = test_file.readlines()[test_line_no - 1:]
                for line in lines:
                    test_lines.append(line)
                    if line.count(';') == 1:
                        break
            initial_prompt = initial_prompt + INITIAL_3 + failing_test + INITIAL_4 + ''.join(
                test_lines) + INITIAL_5 + test_error

            # 完整initial prompt的最后一句
            if patch_type == 'replace':
                initial_prompt += INITIAL_6
            if patch_type == 'insert':
                initial_prompt += INITIAL_8
            return initial_prompt
        else:
            return ''


# 构造带有或不带有INFILL标志的buggy function字符串
def get_buggy_function(file_path, from_line_no, to_line_no, patch_type):
    start_line_no = get_method_declaration_line_no(file_path, from_line_no)
    function_lines = get_method_lines(file_path, start_line_no)
    if patch_type == PATCH_TYPE_REPLACE or PATCH_TYPE_DELETE:
        # del删除数组的元素 包含左边界 不包含右边界
        del function_lines[from_line_no - start_line_no:to_line_no - start_line_no + 1]
        function_lines.insert(from_line_no - start_line_no, INFILL)
    if patch_type == PATCH_TYPE_INSERT:
        function_lines.insert(to_line_no - start_line_no, INFILL)
    return ''.join(function_lines)


# 构造failing test相关的信息 根据chat repair的实现 只考虑一个failing test
def get_failing_test_info(test_file_path):
    with open(test_file_path, 'r', encoding='latin-1') as file:
        lines = file.readlines()
        for i in range(0, len(lines)):
            # match '--- org.apache.commons.lang3.StringUtilsTest::testEscapeSurrogatePairs
            # java.lang.StringIndexOutOfBoundsException: String index out of range: 2'
            if re.match(r'^---', lines[i]):
                failing_test = lines[i].strip('---')
                test_error = lines[i + 1]
            # match 'at org.apache.commons.lang3.StringUtilsTest.testEscapeSurrogatePairs(StringUtilsTest.java:2187)'
            match = re.search(r'\(.*Tests?\.java:(\d+)\)$', lines[i])
            if match:
                # org/apache/commons/lang3/StringUtilsTest
                test_file = ''.join(re.findall(r'[A-Za-z0-9]+\.', lines[i])[0:-1]).replace('.', '/')[:-1] + '.java'
                # 2187
                test_line_no = int(match.group(1))
                return failing_test, test_error, test_file, test_line_no


# 从源代码文件中找出行所在的函数定义起始在哪一行
def get_method_declaration_line_no(source_file_path, line_no):
    with open(source_file_path, "r") as file:
        source_code = file.read()
        file.close()
    tree = parse.parse(source_code)
    line_nos = []
    start_line_no = 0
    for path, node in tree.filter(MethodDeclaration):
        line_nos.append(node.position.line)
    for i in range(0, len(line_nos) - 1):
        if line_nos[i] <= line_no <= line_nos[i + 1]:
            start_line_no = line_nos[i]
    if start_line_no == 0:
        start_line_no = line_nos[len(line_nos) - 1]
    return start_line_no


# 从源代码文件中找出对应函数的lines
def get_method_lines(source_file_path, start_line_no):
    with open(source_file_path, "r", encoding='latin-1') as file:
        lines = file.readlines()[start_line_no - 1:]
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
    return function_lines


if __name__ == '__main__':
    go_chat_repair(Closure)
