# 项目名
CHART = "Chart"
CLOSURE = "Closure"
LANG = "Lang"
MATH = "Math"
MOCKITO = "Mockito"
TIME = "Time"

PROJECTS = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]

# patch类型
PATCH_TYPE_REPLACE = 'replace'
PATCH_TYPE_INSERT = 'insert'
PATCH_TYPE_DELETE = 'delete'

# 文件夹常量
LOG_FILE = "logs.txt"

PATCH_JSON_FOLDER = "patches"
CHATREPAIR_FOLDER = "chat-repair"
INITIALCHAT_FOLDER = "initial-chat"
INITIAL_PROMPT_FOLDER = "initial"

BUGGY_PROJECT_FOLDER = "bugs"
FAILING_TEST_FILE = "failing_tests"

TEST_FILEPATH_PREFIX = {"Closure": "test", "Mockito": "test", "Chart": "tests", "Lang": "src/test/java",
                        "Math": "src/test/java", "Time": "src/test/java"}
TEST_FILEPATH_PREFIX_1 = "src/test"

# defects4j命令常量
DEFECTS4J_CHECKOUT = "defects4j checkout -p %s -v %s -w %s"
DEFECTS4J_COMPILE = "defects4j compile"
DEFECTS4J_TEST = "defects4j test"
DEFECTS4J_COMPILE_TEST = "defects4j compile ; defects4j test"

# Prompt常量
INFILL = ">>>[INFILL]<<<\n"
INITIAL_APR_tool = "You are an Automated Program Repair Tool.\n"

# 每个项目的few shot example
Example_Chart = ""
Example_Lang = ""
Example_Closure = ""
Example_Math = ""
Example_Time = ""
Example_Mockito = ""

INITIAL_Single_line = "The following code contains a buggy line that has been removed:\n"
INITIAL_Single_hunk = "The following code contains a buggy hunk that has been removed:\n"
INITIAL_Single_function = "The following code contains a bug\n"

INITIAL_Single_line_2 = "This was the original buggy line which was removed by the infill location\n"
INITIAL_Single_hunk_2 = "This was the original buggy hunk which was removed by the infill location\n"

Failure_Test = "The code fails on this test:\n"
Failure_Test_line = "\non this test line:\n"
Failure_Test_error = "with the following test error:\n"

# INITIAL_Single_line_final = "\nPlease provide the correct line at the infill location.\n"
# INITIAL_Single_hunk_final = "\nPlease provide the correct hunk at the infill location.\n"
# INITIAL_Single_function_final = "\nPlease provide the correct function.\n"

INITIAL_Single_line_final = "\nPlease provide an analysis of the failure and correct line at the infill location in the form of Java Markdown code block.\n"
INITIAL_Single_hunk_final = "\nPlease provide an analysis of the failure and correct hunk at the infill location in the form of Java Markdown code block.\n"
INITIAL_Single_function_final = "\nPlease provide an analysis of the failure and correct function in the form of Java Markdown code block.\n"

FeedBack_0 = "The fixed version is still not correct.\n"
FeedBack_1 = "It still does not fix the original test failure.\n"
FeedBack_2 = "Code has the following compilation error.\n"

Alt_Instruct_1 = "It can be fixed by these possible patches:\n"
Alt_Instruct_2 = "Please generate an alternative patch."

# chatrepair常量配置
# 最大调用api次数
Max_Tries = 20
# 一个对话中的最大问答次数
Max_Conv_len = 3

# OpenAI API接口
MODEL = "gpt-3.5-turbo"

#第三方网站aikey的接口
API_KEY = 'sk-BTijAxza2faVBDpy452344F136154561Ab9f4fF2037d47E0'
BASE_URL = 'https://api.aikey.one/v1/'

# 师兄的接口（openai官方接口）
#API_KEY = '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'
#BASE_URL = 'https://uu.tanpan.eu.org/v1/'

