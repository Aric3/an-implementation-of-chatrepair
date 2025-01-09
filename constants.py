# Project Name
CHART = "Chart"
CLOSURE = "Closure"
LANG = "Lang"
MATH = "Math"
MOCKITO = "Mockito"
TIME = "Time"

PROJECTS = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]

# patch types
PATCH_TYPE_REPLACE = 'replace'
PATCH_TYPE_INSERT = 'insert'
PATCH_TYPE_DELETE = 'delete'

LOG_FILE = "logs.txt"

PATCH_JSON_FOLDER = "patches"
CHATREPAIR_FOLDER = "chatrepair"
INITIALCHAT_FOLDER = "initialchat"
INITIAL_PROMPT_FOLDER = "initial"

BUGGY_PROJECT_FOLDER = "bugs"
FAILING_TEST_FILE = "failing_tests"

TEST_FILEPATH_PREFIX = {"Closure": "test", "Mockito": "test", "Chart": "tests", "Lang": "src/test/java",
                        "Math": "src/test/java", "Time": "src/test/java"}
TEST_FILEPATH_PREFIX_1 = "src/test"

# defects4j commands
DEFECTS4J_CHECKOUT = "defects4j checkout -p %s -v %s -w %s"
DEFECTS4J_COMPILE = "defects4j compile"
DEFECTS4J_TEST = "defects4j test"
DEFECTS4J_COMPILE_TEST = "defects4j compile ; defects4j test"
TEST_TIMEOUT_MAX_S = 60

INFILL = ">>>[INFILL]<<<\n"
INITIAL_APR_TOOL = "You are an Automated Program Repair Tool.\n"
INTIIAL_APR_EXAMPLE = "Here is an example of a repair job:\n"

INITIAL_Single_line = "The following code contains a buggy line that has been removed:\n"
INITIAL_Single_hunk = "The following code contains a buggy hunk that has been removed:\n"
INITIAL_Single_function = "The following code contains a bug:\n"

INITIAL_Single_line_2 = "This was the original buggy line which was removed by the infill location\n"
INITIAL_Single_hunk_2 = "This was the original buggy hunk which was removed by the infill location\n"

Failure_Test = "The code fails on this test:\n"
Failure_Test_line = "\non this test line:\n"
Failure_Test_error = "with the following test error:\n"

# INITIAL_Single_line_final = "\nPlease provide the correct line at the infill location.\n"
# INITIAL_Single_hunk_final = "\nPlease provide the correct hunk at the infill location.\n"
# INITIAL_Single_function_final = "\nPlease provide the correct function.\n"

INITIAL_Single_line_final = "\nPlease provide an analysis of the problem and the expected behaviour of the correct fix, and the correct line at the infill location in the form of Java Markdown code block.\n"
INITIAL_Single_hunk_final = "\nPlease provide an analysis of the problem and the expected behaviour of the correct fix, and the correct hunk at the infill location in the form of Java Markdown code block.\n"
INITIAL_Single_function_final = "\nPlease provide an analysis of the problem and the expected behaviour of the correct fix, and the correct version of the function in the form of Java Markdown code block.\n"

FeedBack_0 = "The fixed version is still not correct."
FeedBack_1 = "It still does not fix the original test failure."
FeedBack_2 = "Code has the following compilation error: "
FeedBack_3 = "Code has compilation error."
FeedBack_4 = "The program timed out while executing the test cases in 60s."


Alt_Instruct_1 = "It can be fixed by these possible patches:\n"
Alt_Instruct_2 = "Please generate an alternative patch in the form of Java Markdown code block."

Alt_Instruct_3 = "It can be fixed by these possible correct version:\n"
Alt_Instruct_4 = "Please generate an alternative correct version of the function in the form of Java Markdown code block."

FEEDBACK_STATISTICS_FILE = 'feedback_statistics.csv'
ALTERNATIVES_STATISTICS_FILE = 'alternatives_statistics.csv'
INITIALCHAT_STATISTIFCS_FILE = 'initialchat_statistics.csv'

# initialchat settings
NUMOFREPEAT_PER_BUG = 24
PATCH_FAILURE_CATEGORY = ['FNT','FOT','CE','CE','TOUT','P']


# chatrepair settings

Max_Tries = 24

Max_Conv_len = 3

# OpenAI API
MODEL = "gpt-3.5-turbo"

API_KEY = ''
BASE_URL = ''