import json
import os
import re
import shutil
import sys
import time

import openai
import subprocess
from javalang import parse
from javalang.tree import MethodDeclaration
from constants import *

# 上一个失败的测试用例
previous_failure_test = ''


def save_initial(project):
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = construct_initial_prompt(project, file)
        if not initial_prompt == '':
            f = open_file(os.path.join(INITIAL_PROMPT_FOLDER, project, file.rstrip(".json") + ".txt"))
            f.write(initial_prompt)
    print("Success!\nInitial Prompt is saved in " + INITIAL_PROMPT_FOLDER + "/" + project + "!")


def chat_initial(project):
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = construct_initial_prompt(project, file)
        if not initial_prompt == '':
            context = [{'role': 'user', 'content': initial_prompt}]
            response = openai.chat.completions.create(model=MODEL, messages=context)
            # 程序停止1s
            time.sleep(1)
            response_text = response.choices[0].message.content
            context.append({'role': 'assistant', 'content': response_text})
            context_path = os.path.join(INITIALCHAT_FOLDER, project, 'bug' + file.rstrip('.json') + '.txt')
            file = open_file(context_path)
            for element in context:
                file.write(element['content'])
                file.write('\n')
            file.close()
    print("Success!\nContext is saved in " + INITIALCHAT_FOLDER + "/" + project + "!")


def go_chat_repair(project):
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = construct_initial_prompt(project, file)
        if not initial_prompt == '':
            chat_repair(project, initial_prompt, file)


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
            response = openai.chat.completions.create(model=MODEL, messages=context)
            # 程序停止1s
            time.sleep(1)
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
        context_path = os.path.join(CHATREPAIR_FOLDER, project, 'bug' + json_file.rstrip('.json'),
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
            patches_prompt = ''
            for i in range(len(plausible_patches)):
                patches_prompt += 'plausible patch '+str(i+1)+' :\n'+plausible_patches[i]+'\n'
            prompt = delete_substring_to_end(initial_prompt.split('<Example end>')[1].strip(), "Please provide") + Alt_Instruct_1 + patches_prompt+ Alt_Instruct_2
            context.append({'role': 'user', 'content': prompt})
            response = openai.chat.completions.create(model=MODEL, messages=context)
            # 程序停止1s
            time.sleep(1)
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
            context_path = os.path.join(CHATREPAIR_FOLDER, project, 'bug' + json_file.rstrip('.json'),
                                        str(current_tries) + '.txt')
            file = open_file(context_path)
            for element in context:
                file.write(element['content'])
                file.write('\n')
            file.close()
    print("Success!\nContext is saved in " + CHATREPAIR_FOLDER + "/" + project + "!")
    return plausible_patches


# 验证对应patch 并构造feedback
def validate_patch(patch, project, json_file, plausible_patches):
    global previous_failure_test
    temp_javafile = ''
    javafile_path = ''
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
        javafile_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
        
        # 备份需要修改的文件 在一次验证结束后恢复
        with open(javafile_path, mode='r', encoding='latin-1') as javafile:
            temp_javafile = javafile.read()
            javafile.close
            
        # single line 和 single function标志  
        single_line = False
        single_function = False
        # replace类型的patch 找到对应的源代码文件 使用patch替换掉指定行
        if patch_type == PATCH_TYPE_REPLACE:
            from_line_no = data['0']['from_line_no']
            to_line_no = data['0']['to_line_no']
            if from_line_no == to_line_no:
                single_line = True
            # 读java file
            with open(javafile_path, mode='r', encoding='latin-1') as f1:
                lines = f1.readlines()
            del lines[from_line_no - 1:to_line_no]
            lines.insert(from_line_no - 1, patch)
            f1.close()
            # 修改之后重新写入java file
            with open(javafile_path, mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
            #print(''.join(lines))
        # insert类型的patch
        if patch_type == PATCH_TYPE_INSERT:
            next_line_no = data['0']['next_line_no']
            with open(javafile_path, mode='r', encoding='latin-1') as f1:
                lines = f1.readlines()
            lines.insert(next_line_no - 1, patch)
            f1.close()
            with open(javafile_path, mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
            #print(''.join(lines))
        # delete类型的patch 找到的对应的函数 替换整个函数
        if patch_type == PATCH_TYPE_DELETE:
            single_function = True
            next_line_no = data['0']['next_line_no']
            # 获得函数声明所在的行
            source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
            start_line = get_method_declaration_line_no(source_file_path, next_line_no)
            # 替换掉整个函数
            with open(javafile_path, "r", encoding='latin-1') as file:
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
            with open(javafile_path, mode='w', encoding='latin-1') as f2:
                f2.writelines(lines)
                f2.close()
    # 重新编译
    stdout, stderr = run_command(
        'cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE)
    pattern = r"BUILD FAILED"
    result = re.search(pattern, stderr, re.DOTALL)
    feedback = ''
    if result:
        errs = stderr.split("\n")
        for i in range(len(errs)):
            if re.search(r":\serror:\s", errs[i]):
                errmsg = 'error' + errs[i].split('error')[1]
                feedback = FeedBack_0 + FeedBack_2 + errmsg
                break
        if feedback == '':
            feedback = FeedBack_0 + FeedBack_3
    # 没有编译错误 运行defects4j test
    else:
        os.system('cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_TEST)
        # pass全部test 添加plausible_patch
        if is_file_empty_or_not_exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)):
            plausible_patches.append(patch)
            return ''
        # 未通过全部test 构造feedback
        failure_test_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)
        failure_test, test_error, test_file, test_line_no = get_failure_test_info(failure_test_path)
        file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX[project], test_file)
        if not os.path.exists(file):
            file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX_1, test_file)
        if failure_test == previous_failure_test:
            feedback = FeedBack_0 + FeedBack_1
        else:
            previous_failure_test = failure_test
            # get the test line
            test_lines = []
            with open(file, mode='r', encoding='latin-1') as test_file:
                lines = test_file.readlines()[test_line_no - 1:]
                for line in lines:
                    test_lines.append(line)
                    if line.count(';') == 1:
                        break
            feedback = FeedBack_0 + Failure_Test + failure_test + Failure_Test_line + ''.join(
                test_lines) + Failure_Test_error + test_error
    # 编译测试结束后恢复java文件的内容
    # shutil.rmtree(os.path.join(BUGGY_PROJECT_FOLDER, project + no))
    with open(javafile_path, mode='w', encoding='latin-1') as javafile:
        javafile.write(temp_javafile)
        javafile.close()
    if single_line:
        feedback += INITIAL_Single_line_final
    if single_function:
        feedback += INITIAL_Single_function_final
    if not single_line and not single_function:
        feedback += INITIAL_Single_hunk_final
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


def delete_substring_to_end(s, subs):
    index = s.find(subs)  # 查找子串在字符串中的位置
    if index != -1:
        new_string = s[:index]  # 使用切片操作获取子串之前的部分
        return new_string
    else:
        return s


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
    global previous_failure_test
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
            initial_prompt = INITIAL_APR_TOOL + INTIIAL_APR_EXAMPLE + get_example('Lang_example.txt')
            single_line = False
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
                    single_line = True
                    initial_prompt += INITIAL_Single_line + buggy_function + INITIAL_Single_line_2 + original_buggy_hunk
                # single hunk的patch
                else:
                    initial_prompt += INITIAL_Single_hunk + buggy_function + INITIAL_Single_hunk_2 + original_buggy_hunk
            # delete类型的patch
            if patch_type == PATCH_TYPE_DELETE:
                from_line_no = data['0']['from_line_no']
                to_line_no = data['0']['to_line_no']
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
                os.system('cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE_TEST)

            # 添加关于failure test的信息
            try:
                failure_test, test_error, test_file, test_line_no = get_failure_test_info(failure_test_path)
                #print(failure_test, test_error, test_file, test_line_no)
            except TypeError as e:
                print("Wrong! File:" + failure_test_path + " Not able to handle. With", e)
                with open(LOG_FILE, 'a') as file:
                    file.write("Wrong! File:" + failure_test_path + " Not able to handle." + "\n")
                    file.close()
                return ''
            # 设置全局变量 上一个失败的测试
            previous_failure_test = failure_test
            # 为test_file的路径添加前缀
            file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX[project], test_file)
            if is_file_empty_or_not_exists(file):
                file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX_1, test_file)
            # 根据test line所在的行到对应文件找到目标line
            test_lines = []
            with open(file, mode='r', encoding='latin-1') as test_file:
                lines = test_file.readlines()[test_line_no - 1:]
                for line in lines:
                    test_lines.append(line)
                    if re.sub(r'\".*?\"', '', line).count(';') == 1:
                        break
            initial_prompt += Failure_Test + failure_test + Failure_Test_line + ''.join(
                test_lines) + Failure_Test_error + test_error

            # 完整initial prompt的最后一句
            if patch_type == PATCH_TYPE_REPLACE or patch_type == PATCH_TYPE_INSERT:
                if single_line:
                    initial_prompt += INITIAL_Single_line_final
                else:
                    initial_prompt += INITIAL_Single_hunk_final
            else:
                initial_prompt += INITIAL_Single_function_final
            return initial_prompt
        else:
            return ''


# 构造带有或不带有INFILL标志的buggy function字符串
def get_buggy_function(file_path, from_line_no, to_line_no, patch_type):
    start_line_no = get_method_declaration_line_no(file_path, from_line_no)
    function_lines = get_method_lines(file_path, start_line_no)
    if patch_type == PATCH_TYPE_REPLACE:
        # del删除数组的元素 包含左边界 不包含右边界
        del function_lines[from_line_no - start_line_no:to_line_no - start_line_no + 1]
        function_lines.insert(from_line_no - start_line_no, INFILL)
    if patch_type == PATCH_TYPE_INSERT:
        function_lines.insert(to_line_no - start_line_no, INFILL)
    return ''.join(function_lines)


# 构造failing test相关的信息 根据chat repair的实现 只考虑一个failing test
def get_failure_test_info(test_file_path):
    with open(test_file_path, 'r', encoding='latin-1') as file:
        lines = file.readlines()
        failing_test = lines[0].strip('--- ').rstrip()
        test_error = lines[1].rstrip()
        test_function = failing_test.split("::")[1].rstrip()
        # test_file = failing_test.split("::")[0].replace('.', '/') + '.java'
        for i in range(2, len(lines)):
            if test_function in lines[i] :
                test_line_no = int(re.search(r'(\d+)\)', lines[i]).group(1))
                test_file = delete_substring_to_end(lines[i],'.'+test_function).split('at ')[1].replace('.', '/') + '.java'
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

def get_example(example_file):
    with open(example_file, 'r') as f:
        example = f.read()
        f.close()
        return example

if __name__ == '__main__':
    ins, p = sys.argv[1:3]
    if ins not in ["chatrepair", "initial-save", "initial-chat"]:
        print("Instruction only support \"chatrepair\"and\"initial-save\" and \"initial-chat\"")
    else:
        if p not in PROJECTS:
            print("Project only support these:\n")
            print(PROJECTS)
        else:
            if ins == "initial-save":
                save_initial(p)
            elif ins == "initial-chat":
                chat_initial(p)
            else:
                go_chat_repair(p)
