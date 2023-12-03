# 项目名
CHART = "Chart"
Closure = "Closure"
LANG = "Lang"
MATH = "Math"
MOCKITO = "Mockito"
TIME = "Time"

# patch类型
PATCH_TYPE_REPLACE = 'replace'
PATCH_TYPE_INSERT = 'insert'

# 文件夹常量
PATCH_JSON_FOLDER = "patches"
CONVERSATION_FOLDER = "conversations"
BUGGY_PROJECT_FOLDER = "bugs"
FAILING_TEST_FILE = "failing_tests"
TEST_PATH_PREFIX = "src/test"
TEST_PATH_PREFIX_JAVA = "src/test/java"

# defects4j命令常量
DEFECTS4J_CHECKOUT = "defects4j checkout -p %s -v %s -w %s"
DEFECTS4J_COMPILE = "defects4j compile"
DEFECTS4J_TEST = "defects4j test"
DEFECTS4J_COMPILE_TEST = "defects4j compile ; defects4j test"

# Prompt常量
Example = ""
INFILL = ">>>[INFILL]<<<\n"
INITIAL_1 = ("You are an automated program repair tool.\n"
             "The following function contains a buggy hunk that has been replaced by the mark >>>[INFILL]<<<:\n")
INITIAL_2 = "This was the original buggy hunk which was replaced by the >>>[INFILL]<<< mark:\n"

INITIAL_3 = "The code fails on this test:\n"
INITIAL_4 = "on this test line:\n"
INITIAL_5 = "with the following test error:\n"

INITIAL_6 = ("Please provide the correct lines at the >>>[INFILL]<<< location. Your code should be a replacement "
             "for >>>INFILL]<<<, so don't include lines before and after >>>[INFILL]<<<.\n")
INITIAL_7 = "You are an automated program repair tool.\nThe following function is a buggy function.\n"
INITIAL_8 = "Please provide the correct repair of this function.Make sure all failing test cases pass.\n"

FeedBack_1 = "Your code still not correct.\n"
FeedBack_2 = "Your code has compilation error:\n"

Alt_Instruct_1 = "The bug can be fixed by these patches:\n"
Alt_Instruct_2 = "Please generate another alternative patch.\n"

# chat repair常量配置
Max_Tries = 10
Max_Conv_len = 3
API_KEY = 'sk-BTijAxza2faVBDpy452344F136154561Ab9f4fF2037d47E0'
BASE_URL = 'https://api.aikey.one/v1/'
Model = "gpt-3.5-turbo"
