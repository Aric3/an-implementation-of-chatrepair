# chatrepair
## 1. Download or Clone this project.

## 2. Ensure Defects4j 2.0 has installed in your machine.
Install Defects4j 2.0 and configure the environment path. Ensure all defects4j command is available.
## 3. Download dependences.
run `pip install javalang` and `pip install openai`.(To ensure the openai api is workable,a python version 3.10 is needed.)
## 4. Set your openapi key and base url.
Modify the openai api key and base url in constant.py.
## 5. Run the script with arguments.
run the script by command `python main.py` with 2 arguments, the first argument is your instruction, the second is the project.

instruction:
- `initial-save` save the initial prompt of all bugs of your project.
- `initial-chat` chat with chatgpt only using the initial prompt and just one shot.
- `chatrepair` run the method chatrepair.

project:
- Lang
- Chart
- Closure
- Mockito
- Math
- Time

eg:
run this command:
`python main.py initial-save Lang`
will save initial prompt of all bugs of the project Lang.

**Note that a valid openai apikey and secret is necessary!**.

