CHART = "Chart"
Closure = "Closure"
LANG = "Lang"
MATH = "Math"
MOCKITO = "Mockito"
TIME = "Time"
PATCH_JSON_FOLDER = "patches"
BUGGY_PROJECT_FOLDER = "bugs"
FAILING_TEST_FILE = "failing_tests"
TEST_PATH_PREFIX = "/src/test/"
TEST_PATH_PREFIX_JAVA = "/src/test/java/"
INFILL = ">>>[INFILL]<<<\n"

DEFECTS4J_CHECKOUT = "defects4j checkout -p %s -v %s -w %s"
DEFECTS4J_COMPILE_TEST = "defects4j compile ; defects4j test"

INITIAL_1 = ("You are an automated program repair tool.\n"
                 "The following function contains a buggy hunk that has been replaced by the mark >>>[INFILL]<<<:\n")
INITIAL_2 = "This was the original buggy hunk which was replaced by the >>>[INFILL]<<< mark:\n"

INITIAL_3 = "The code fails on this test:\n"
INITIAL_4 = "on this test line:\n"
INITIAL_5 = "with the following test error:\n"

INITIAL_6 = ("Please provide the correct lines at the >>>[INFILL]<<< location. Your code should be a replacement "
                 "for >>>["
                 "INFILL]<<<, so don't include lines of code before and after >>>[INFILL]<<<.")
INITIAL_7 = "You are an automated program repair tool.\nThe following function is a buggy function.\n"
INITIAL_8 = "Please provide the correct repair of this function.Make sure all failing test cases pass."