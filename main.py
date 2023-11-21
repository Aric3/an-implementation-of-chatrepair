# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import os

from enum import Enum
from javalang import parse
from javalang.tree import MethodDeclaration

class ChatRepairConstant(Enum):
    Chart = "Chart"
    Closure = "Closure"
    Lang = "Lang"
    Math = "Math"
    Mockito = "Mockito"
    Time = "Time"
    Patches_base_folder = "patches"
    INFILL = "[INFILL]"
def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

# ChatRepair 算法
# 1.checkout 对应buggy项目 结合 patches文件构造initial input
def initial_input(project):
    base_dir = os.path.dirname(__file__)
    project_path = os.path.join(os.path.join(base_dir, ChatRepairConstant.Patches_base_folder.value), project)
    files = os.listdir(project_path)
    n = files.__len__()
    while n > 0:
        with open(os.path.join(project_path,files[n-1]),'r') as f:
            data = json.load(f)
            num_of_hunks = data[num_of_hunks]
            if num_of_hunks == 1:
                file_name = data[0][file_name]
                patch_type = data[0][patch_type]
                if patch_type == 'replace':
                    from_line_no = data[0][from_line_no]
                    to_line_no = data[0][to_line_no]
                    replaced = data[0][replaced]
                if patch_type == 'insert':
                    next_line_no = data[0][next_line_no]

        n=n-1


def find_java_function(file_path, line_number):
    with open(file_path, "r") as file:
        source_code = file.read()
    tree = parse.parse(source_code)
    for path, node in tree.filter(MethodDeclaration):
        print(node.name)
        return



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    find_java_function("./AnnotationUtils.java",300)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
