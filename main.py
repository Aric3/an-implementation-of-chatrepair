import json
import os
import re
import difflib
import sys
import time

import openai
import subprocess
from javalang import parse
from javalang.tree import MethodDeclaration
from constants import *

# 上一个失败的测试用例
previous_failure_test = ''


def save_initial(project, all_single_function_flag):
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for file in files:
        initial_prompt = ''
        if all_single_function_flag == True:
            initial_prompt = construct_single_function_initial_prompt(project,file)
        else:
            initial_prompt = construct_initial_prompt(project, file)
        if not initial_prompt == '':
            f = open_file(os.path.join(INITIAL_PROMPT_FOLDER, project, file.rstrip(".json") + ".txt"),'w')
            f.write(initial_prompt)
    print("Success!\nInitial Prompt is saved in " + INITIAL_PROMPT_FOLDER + "/" + project + "!")


def chat_initial(project, all_single_function_flag):
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    json_files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    for json_file in json_files:
        i = 0
        no = json_file.rstrip('.json')
        while i < NUMOFREPEAT_PER_BUG:
            initial_prompt = ''
            if all_single_function_flag == True:
                initial_prompt = construct_single_function_initial_prompt(project, json_file)
            else:
                initial_prompt = construct_initial_prompt(project, json_file)
            if not initial_prompt == '':
                context = [{'role': 'user', 'content': initial_prompt}]
                response = openai.chat.completions.create(model=MODEL, messages=context)
                # 程序停止1s
                time.sleep(1)
                response_text = response.choices[0].message.content
                context.append({'role': 'assistant', 'content': response_text})
                patch = match_patch_code(response_text)
                # 如果没有符合规范的patch 重新开始本次循环
                if patch == '':
                    continue
                # 获得结果信息
                result = []
                feedback = validate_patch(patch, project, json_file, all_single_function_flag, result)
                if feedback == 'Exception':
                    continue
                
                # 保存对话到各自的文件
                context_path = os.path.join(INITIALCHAT_FOLDER, project, 'bug' + no,str(i+1)+'.txt')
                file = open_file(context_path,'w')
                for element in context:
                    file.write(element['content'])
                    file.write('\n\n')
                if all_single_function_flag:
                    # 获得patch与buggy function的diff结果
                    diff_result = diff_buggy_and_new(project, json_file, patch)
                    file.write(diff_result)
                file.close()
                i += 1
            else:
                break
            # 保存数据到整合文件
            file = open_file(os.path.join(INITIALCHAT_FOLDER,INITIALCHAT_STATISTIFCS_FILE),'a')
            file.write(project+', '+ no +', '+PATCH_FAILURE_CATEGORY[result[0]]+'\n')
            file.close()
            
            
def diff_buggy_and_new(project, json_file, new_function):
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
    if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
        os.system(DEFECTS4J_CHECKOUT % (project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
    next_line_no = data['0']['next_line_no']
    file_name = data['0']['file_name']
    source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
    buggy_function = get_buggy_function(source_file_path, next_line_no, next_line_no, PATCH_TYPE_DELETE)
    diff = difflib.Differ()
    buggy_squences = [line.strip() for line in buggy_function.splitlines() if line.strip()]
    new_squences = [line.strip() for line in new_function.splitlines() if line.strip()]
    return '\n'.join(diff.compare(buggy_squences,new_squences))
     

def diff_buggy_and_newlist(project, json_file, new_function_list):
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
    if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
        os.system(DEFECTS4J_CHECKOUT % (project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
    next_line_no = data['0']['next_line_no']
    file_name = data['0']['file_name']
    source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
    buggy_function = get_buggy_function(source_file_path, next_line_no, next_line_no, PATCH_TYPE_DELETE)
    diff = difflib.Differ()
    buggy_squences = [line.strip() for line in buggy_function.splitlines() if line.strip()]
    diff_result = []
    for new_function in new_function_list:
        new_squences = [line.strip() for line in new_function.splitlines() if line.strip()]
        diff_result.append('\n'.join(diff.compare(buggy_squences,new_squences)))
    return diff_result
     
def go_chat_repair(project, all_single_function_flag):
    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    files = os.listdir(os.path.join(PATCH_JSON_FOLDER, project))
    i = 0
    while i < len(files):
        initial_prompt = ''
        if all_single_function_flag == True:
            initial_prompt = construct_single_function_initial_prompt(project,files[i])
        else:
            initial_prompt = construct_initial_prompt(project, files[i])
        # 测试文件不符合要求 或 不是 single hunk 跳过当前文件
        if initial_prompt == '':
            i += 1
        if not initial_prompt == '':
            # chatrepair抛出异常 重试当前bug
            if chat_repair(project, initial_prompt, files[i], all_single_function_flag) != 'Exception':
                i +=1


def chat_repair(project, initial_prompt, json_file, all_single_function_flag):
    current_tries = 0
    plausible_patches = []

    openai.base_url = BASE_URL
    openai.api_key = API_KEY
    
    # 统计feedback状态的值
    fa = 0
    fb = 0
    first_plausible_try = 0
    
    # 找到一个plausible patch
    while current_tries < Max_Tries and len(plausible_patches) == 0:
        context = []
        current_length = 0
        prompt = initial_prompt
        # 添加统计feedback 效果的数组
        feedback_list = []
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
            feedback = validate_patch(patch, project, json_file, all_single_function_flag, feedback_list)
            if feedback == '':
                plausible_patches.append(patch)
                current_length += 1
                current_tries += 1
                break
            if feedback == 'Exception':
                return 'Exception'
            else:
                prompt = feedback
            current_length += 1
            current_tries += 1
            
        # 处理feedback_list 没有修对的情况下 validate函数被调用3次 修对的情况下validate函数被调用1次 或 2次 或 3次
        a, b =process_fb_list(feedback_list)
        fa += a
        fb += b
        # 保存结果到各自文件中
        file = open_file(os.path.join(CHATREPAIR_FOLDER, project, json_file.rstrip('.json')+'.txt'),'a')
        file.write('current trys: '+str(current_tries)+', feedback list: '+str(feedback_list)+' Feedback statistics: '+ str(fa) + '/' + str(fb)+'\n')
        if feedback_list[len(feedback_list)-1] == 5:
            first_plausible_try = current_tries
            file.write('current trys: '+str(current_tries)+', feedback list: '+str(feedback_list)+' First plausible patch at '+str(current_tries)+' tries!\n')
        file.close
        
        # 保存对话到各自文件中
        context_path = os.path.join(CHATREPAIR_FOLDER, project, 'bug' + json_file.rstrip('.json'),
                                    str(current_tries) + '.txt')
        file = open_file(context_path,'w')
        for element in context:
            file.write(element['content'])
            file.write('\n\n')
        file.close()
        
    # 保存结果到整合表中
    file = open_file(os.path.join(CHATREPAIR_FOLDER, FEEDBACK_STATISTICS_FILE),'a')
    file.write(project+', '+ json_file.rstrip('.json')+', '+str(fa)+', '+str(fb)+', '+str(first_plausible_try)+'\n')
    file.close()
        
    # 当有一个plausible patch时 generate更多的plausible patch
    if len(plausible_patches) != 0:
        alternatives_list = []
        duplicates_num = 0
        while current_tries < Max_Tries:
            context = []
            patches_prompt = ''
            patch_or_function = 'plausible patch '
            if all_single_function_flag:
                patch_or_function = 'Correct version '
            for i in range(len(plausible_patches)):
                patches_prompt += patch_or_function +str(i+1)+' :\n'+plausible_patches[i]+'\n'
            if all_single_function_flag:
                prompt = delete_substring_to_end(initial_prompt.split('<Example end>')[1].strip(), "Please provide") + Alt_Instruct_3 + patches_prompt+ Alt_Instruct_4
            else: 
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
            feedback = validate_patch(patch, project, json_file, all_single_function_flag,alternatives_list)
            if feedback == 'Exception':
                return 'Exception'
            # 判断是否已经包含指定字符串
            if feedback == '':
                if not_exist(plausible_patches, patch):
                    plausible_patches.append(patch)
                else:
                    duplicates_num += 1
            current_tries += 1
            # 保存对话到文件中
            context_path = os.path.join(CHATREPAIR_FOLDER, project, 'bug' + json_file.rstrip('.json'),
                                        str(current_tries) + '.txt')
            file = open_file(context_path,'w')
            for element in context:
                file.write(element['content'])
                file.write('\n')
            file.close()
        
        # 获得各类patch数量        
        num_ce_patches, num_f_patches, num_to_patches, num_plausible_patches = proces_alter_list(alternatives_list)
        # 加上the first plausible patch
        num_plausible_patches+=1
        # 保存结果到各自文件
        file = open_file(os.path.join(CHATREPAIR_FOLDER, project, json_file.rstrip('.json'))+'.txt','a')
        file.write('current trys: '+str(current_tries)+'. Below is statistics of all generation patches:\n')
        file.write('\nCompilation Error patches number: '+str(num_ce_patches)+'\nFailure patches number: '
                +str(num_f_patches)+'\nTime out patches number: '+str(num_to_patches)+'\nPlausible patches number: '
                +str(num_plausible_patches)+'\nDuplicate plausible patches number: '+str(duplicates_num))
        file.close()
        # 保存结果到整合文件
        file = open_file(os.path.join(CHATREPAIR_FOLDER, ALTERNATIVES_STATISTICS_FILE),'a')
        file.write(project+', '+ json_file.rstrip('.json')+', '+str(num_ce_patches)+', '+str(num_f_patches)+', '
                +str(num_to_patches)+', '+str(num_plausible_patches)+', '+str(duplicates_num)+', '+str(len(plausible_patches))+'\n')
        file.close()
        # 保存diff结果到各自文件
        file = open_file(os.path.join(CHATREPAIR_FOLDER, project, 'bug' +json_file.rstrip('.json'),'diffpatches.txt'),'w')
        diff_result = diff_buggy_and_newlist(project, json_file, plausible_patches)
        for result in diff_result:
            file.write(result+'\n\n')
        file.close()
    return plausible_patches


# 验证对应patch 并构造feedback
def validate_patch(patch, project, json_file, all_single_function_flag,fb_list):
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
    # single line 和 single function标志  
    single_line = False
    single_function = False 
    file_name = data['0']['file_name']
    patch_type = data['0']['patch_type']
    javafile_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
    
    # 备份需要修改的文件 在一次验证结束后恢复
    with open(javafile_path, mode='r', encoding='latin-1') as javafile:
        temp_javafile = javafile.read()
        javafile.close
    if all_single_function_flag == False:  
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
            rewrite_function_to_javafile(next_line_no, javafile_path, patch)
    if all_single_function_flag == True:
        next_line_no = data['0']['next_line_no']
        rewrite_function_to_javafile(next_line_no, javafile_path, patch)
    # 执行 defect4j compile ; defects4j test 并返回feedback
    feedback = construct_feedback_after_validate(project, no, fb_list)
    # 返回空字符 则patch正确 
    if feedback == '':
        # 编译测试结束后恢复java文件的内容
        with open(javafile_path, mode='w', encoding='latin-1') as javafile:
            javafile.write(temp_javafile)
            javafile.close()
        return ''
    if feedback == 'Exception':
        # 编译测试结束后恢复java文件的内容
        with open(javafile_path, mode='w', encoding='latin-1') as javafile:
            javafile.write(temp_javafile)
            javafile.close()
        return feedback
    # 编译测试结束后恢复java文件的内容
    with open(javafile_path, mode='w', encoding='latin-1') as javafile:
        javafile.write(temp_javafile)
        javafile.close()
    if single_line:
        feedback += INITIAL_Single_line_final
    if single_function or all_single_function_flag:
        feedback += INITIAL_Single_function_final
    if all_single_function_flag == False and not single_line and not single_function:
        feedback += INITIAL_Single_hunk_final
    return feedback

def rewrite_function_to_javafile(next_line_no, javafile_path, patch):
    # 获得函数声明所在的行
    start_line = get_method_declaration_line_no(javafile_path, next_line_no)
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


def construct_feedback_after_validate(project, no,fb_list):
    global previous_failure_test
    # 重新编译
    flag, stdout, stderr = run_command(DEFECTS4J_COMPILE.split(' '),'latin-1', os.path.join(BUGGY_PROJECT_FOLDER, project + no),TEST_TIMEOUT_MAX_S)
    if not flag:
        print(stderr)    
    pattern = r"BUILD FAILED"
    result = re.search(pattern, stderr, re.DOTALL)
    feedback = ''
    if result:
        errs = stderr.split("\n")
        for i in range(len(errs)):
            if re.search(r":\serror:\s", errs[i]):
                errmsg = 'error' + errs[i].split('error')[1]
                feedback = FeedBack_0 + FeedBack_2 + errmsg
                # 匹配的编译错误 添加状态2
                fb_list.append(2)
                break
        if feedback == '':
            feedback = FeedBack_0 + FeedBack_3
            # 无法匹配的编译错误 添加状态3
            fb_list.append(3)
    # 没有编译错误 运行defects4j test
    else:
        temp_failingtests = ''
        failingtests_path = os.path.join(BUGGY_PROJECT_FOLDER,project + no,FAILING_TEST_FILE)
        with open(failingtests_path, mode='r', encoding='latin-1') as failingtests:
            temp_failingtests = failingtests.read()
            failingtests.close()
        flag, stdout, stderr = run_command(DEFECTS4J_TEST.split(' '),'latin-1', os.path.join(BUGGY_PROJECT_FOLDER, project + no),TEST_TIMEOUT_MAX_S)
        if not flag and stderr.count('[ERROR]') != 0:
            feedback = FeedBack_0 + FeedBack_4
            # 执行命令超时 添加状态4
            fb_list.append(4)
        elif flag:    
            # pass全部test 添加plausible_patch
            if is_file_empty_or_not_exists(failingtests_path):   
                # feedback为空 结束此次conversation 添加状态5
                fb_list.append(5)
                # 恢复failing_tests文件
                with open(failingtests_path, mode='w', encoding='latin-1') as failingtests:
                    failingtests.write(temp_failingtests)
                    failingtests.close()
                return ''
            # 未通过全部test 构造feedback
            failure_test, test_error, test_file, test_line_no = get_failure_test_info(failingtests_path)
            if test_file == '' or test_line_no == '':
                print("Warning!!! Unable to handle file [" + failingtests_path + "]while validate the patch.")
                with open(LOG_FILE, 'a') as file:
                    file.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"\nWarning!!! Unable to handle file [" + failingtests_path + "] while validate the patch.")
                    file.close()
                # 恢复failing_tests文件
                with open(failingtests_path, mode='w', encoding='latin-1') as failingtests:
                    failingtests.write(temp_failingtests)
                    failingtests.close()
                return 'Exception'
            
            file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX[project], test_file)
            if not os.path.exists(file):
                file = os.path.join(BUGGY_PROJECT_FOLDER, project + no, TEST_FILEPATH_PREFIX_1, test_file)
            if failure_test == previous_failure_test:
                feedback = FeedBack_0 + FeedBack_1
                # fail original failure，添加状态1
                fb_list.append(1)
            else:
                previous_failure_test = failure_test
                # fail一个新的test，添加状态0
                fb_list.append(0)
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
        # 恢复failing_tests文件
        with open(failingtests_path, mode='w', encoding='latin-1') as failingtests:
            failingtests.write(temp_failingtests)
            failingtests.close()
    return feedback



def process_fb_list(fb_list):
    a = 0
    # fb_list里有1到3个元素
    for i in range(1, len(fb_list)):
        # 这次feedback和上次feedback是一样的
        if fb_list[i] == fb_list[i-1]:
            a += 1
    return a, len(fb_list)


def proces_alter_list(alter_list):
    num_ce_patches = 0
    num_f_patches = 0
    num_to_patches = 0
    num_plausible_patches = 0
    
    for alter in alter_list:
        if alter == 0 or alter == 1:
            num_f_patches+=1
        elif alter == 2 or alter == 3:
            num_ce_patches+=1
        elif alter == 4:
            num_to_patches+=1
        elif alter == 5:
            num_plausible_patches+=1
    return num_ce_patches, num_f_patches, num_to_patches, num_plausible_patches


def not_exist(list, s):
    for l in list:
        if l.replace(' ','').replace('\n','') == s.replace(' ','').replace('\n',''):
            return False
    return True
    


# 从chat gpt文本中提取代码部分
def match_patch_code(response_text):
    if(response_text.count('```java') > 1):
        response_text = '\n'.join(response_text.split('\n')[1:])
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

def run_command(cmd, encoding='utf-8', cwd=None, timeout=None):
    try:
        finished = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=timeout)
        finished.check_returncode()
        return True, finished.stdout.decode(encoding), finished.stderr.decode(encoding)
    except subprocess.CalledProcessError:
        return False, finished.stdout.decode(encoding), finished.stderr.decode(encoding)
    except subprocess.TimeoutExpired:
        return False, '[ERROR]:{} time out after {} seconds'.format(cmd, timeout), '[ERROR]:{} time out after {} seconds'.format(cmd, timeout)




# 打开文件 如果不存在则创建
def open_file(path, pattern):
    # 检查路径是否存在
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if pattern not in ['r', 'w', 'a']:
        return ''
    file = open(path, pattern)
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

            failure_info = prompt_add_failure_test_info(project, json_file)
            if failure_info != '':
                initial_prompt += failure_info
            else:
                return ''
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

def construct_single_function_initial_prompt(project, json_file):
    global previous_failure_test
    # 读对应json文件
    no = json_file.rstrip('.json')
    with open(os.path.join(PATCH_JSON_FOLDER, project, json_file), 'r', encoding="latin-1") as f:
        data = json.load(f)
        f.close()
    if not os.path.exists(os.path.join(BUGGY_PROJECT_FOLDER, project + no)):
        os.system(DEFECTS4J_CHECKOUT % (project, no + 'b', os.path.join(BUGGY_PROJECT_FOLDER, project + no)))
    initial_prompt = INITIAL_APR_TOOL + INTIIAL_APR_EXAMPLE + get_example('Lang_single_function_example.txt')
    next_line_no = data['0']['next_line_no']
    file_name = data['0']['file_name']
    source_file_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, file_name)
    buggy_function = get_buggy_function(source_file_path, next_line_no, next_line_no, PATCH_TYPE_DELETE)
    failure_info = prompt_add_failure_test_info(project, json_file)
    if failure_info != '':
        initial_prompt += INITIAL_Single_function + buggy_function + failure_info + INITIAL_Single_function_final
    else:
        initial_prompt = ''
    return initial_prompt
    

def prompt_add_failure_test_info(project,json_file):
    global previous_failure_test
    no = json_file.rstrip('.json')
    failure_test_path = os.path.join(BUGGY_PROJECT_FOLDER, project + no, FAILING_TEST_FILE)
    if is_file_empty_or_not_exists(failure_test_path):
        os.system('cd ' + os.path.join(BUGGY_PROJECT_FOLDER, project + no) + ' && ' + DEFECTS4J_COMPILE_TEST)
    # 添加关于failure test的信息
    failure_test, test_error, test_file, test_line_no = get_failure_test_info(failure_test_path)
    #print(failure_test, test_error, test_file, test_line_no)
    if test_file == '' or test_line_no == '':
        print("Wrong!!! Unable to handle file:[" + failure_test_path + '] while construct the initial prompt.')
        with open(LOG_FILE, 'a') as file:
            file.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"\nWrong!!! Unable to handle file [" + failure_test_path + "] while construct the initial prompt.")
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
        return Failure_Test + failure_test + Failure_Test_line + ''.join(test_lines) + Failure_Test_error + test_error
    
    
    

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
            if test_function in lines[i]:
                try:
                    test_line_no = int(re.search(r'(\d+)\)', lines[i]).group(1))
                    test_file = delete_substring_to_end(lines[i],'.'+test_function).split('at ')[1].replace('.', '/') + '.java'
                    return failing_test, test_error, test_file, test_line_no
                except AttributeError as e:
                    print("Warning!!! Unable to handle file [" + test_file_path + "]while get the the test info:",e)
                    with open(LOG_FILE, 'a') as file:
                        file.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"\nWarning!!! Unable to handle file [" + test_file_path + "] while get the the test info.")
                        file.close()
                    return failing_test, test_error, '', ''
        # 不符合要求的failing_test文件
        return failing_test, test_error, '', ''

# 从源代码文件中找出行所在的函数定义起始在哪一行
def get_method_declaration_line_no(source_file_path, line_no):
    with open(source_file_path, "r",encoding="latin-1") as file:
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
    ins, p, all = sys.argv[1:4]
    if ins not in ["chatrepair", "initial-save", "initial-chat"]:
        print("Instruction only support \"chatrepair\"and\"initial-save\" and \"initial-chat\"")
    else:
        if p not in PROJECTS:
            print("Project only support these:\n")
            print(PROJECTS)
        else:
            if ins == "initial-save" and all == 'y':
                save_initial(p,True)
            elif ins == "initial-save" and all == 'n':
                save_initial(p,False)
            elif ins == "initial-chat" and all == 'y':
                chat_initial(p, True)
            elif ins == "initial-chat" and all == 'n':
                chat_initial(p, False)
            elif ins == "chatrepair" and all == 'y':
                go_chat_repair(p,True)
            elif ins == "chatrepair" and all == 'n':
                go_chat_repair(p, False)