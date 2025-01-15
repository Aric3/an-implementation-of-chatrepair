# Introduction of the folder structure:
``` plaintext
|-- Lang_example.txt 
|-- Lang_single_function_example.txt
|-- README.md
|-- Results
|   |-- chatrepair-additional
|   |-- chatrepair-infill
|   |-- chatrepair-sf
|   |-- initialchat-additional
|   |-- initialchat-infill
|   |-- initialchat-sf
|   `-- initialchat-sf-24
|-- chatrepair.sh
|-- constants.py
|-- full_run.sh
|-- initialchat.sh
|-- main.py
|-- patches
|   |-- Chart
|   |-- Closure
|   |-- Lang
|   |-- Math
|   |-- Mockito
|   `-- Time
|-- single-function-patches
|   |-- Chart
|   |-- Closure
|   |-- Lang
|   |-- Math
|   |-- Mockito
|   `-- Time
`-- tables
    |-- Alternative_Patches.xlsx
    |-- initial-infill.xlsx
    `-- initial-sf.xlsx
```

# How to use this script
## 1. Clone this project.

## 2. Install Defects4j dataset.
Install Defects4j and configure the environment path. Ensure all defects4j command is available. Because this script needs to run `checkout`, `compile` and `test` commands.
## 3. Download dependences in your python environment.
This script needs 2 extral dependences: `javalang` and `openai`
If you use pip as the package manager, you could run `pip install javalang` and `pip install openai`.(To ensure the openai api is workable, a python version 3.10 is recommended.)
## 4. Set your openapi key and base url.
Modify the openai api key and base url in constant.py.
## 5. Run the script with arguments or shell scripts.
Run the script by command `python main.py` with 3 arguments: 

- First argument
    - `initial-save` : Generate and save the initial prompt of all bugs of a project.
    - `initial-chat` : Chat with chatgpt with the initial prompt.
    - `chatrepair` Run the chatreapir method we implemented.

- Second argument: `Lang`, `Chart`,`Closure`,`Mockito`,`Math`,`Time`.

- Third argument: `y` or `n`
    - `y`: use single function prompt.
    - `n`: use signle hunk and single line prompt.

# Notice
1. The form of "Few Shot Example" was not given in orginal `CHATREPAIR` paper and the paper use one example. So the prompts we use in the example are derived from the prompts used in the flowchart explaining the chatrepair method in the paper, and in the response format, we have provided a template for a reply as below:
``` plaintext
Example response:

1. Analysis of the problem:
The problem seems to arise from the comparison of hours using `Calendar.HOUR`. However, `Calendar.HOUR` represents the 12-hour clock hour whereas `Calendar.HOUR_OF_DAY` represents the 24-hour clock hour. Since the code is aiming to compare the hour component in a manner consistent with the other fields (such as minute, second, millisecond), it should use `Calendar.HOUR_OF_DAY` instead.

2. Expected Behavior of Correct Fix:
The correct fix should ensure that the comparison is done using the 24-hour clock hour (Calendar.HOUR_OF_DAY) to maintain consistency with the other fields.

3. Correct code at the Infill Location:

```java
cal1.get(Calendar.HOUR_OF_DAY) == cal2.get(Calendar.HOUR_OF_DAY) &&
```
```
```
2. The author doesn't give a clue about how to knock out and design prompts for patches of the deletion and insertion types in single hunk or single line scenario, so we looked for the same way that fill-in-the-blank fixes handle the deletion and addition of lines of code that the author used in his published article _ Automated Program Repair in the Era of Large Pre trained Language Models_: In the case of deletion-type fixes, the author replaces the code that needs to be removed correctly with a padding marker; For insertion type fixes, the author adds markup where a line of code needs to be inserted. The code used in the article link: https://zenodo.org/records/7592886.
We do not think this is a wise way for a repair task especially for delete type patch, because it may provide extral information and cause misdirection. 
Our random selection did not select a single hunk bug whose developer patch is deletion type. For an insertion type patch, INFILL marker will be embedded at the expecting repair places. Prompt will look like this:
``` plaintext

The following code contains a bug:
    public static String random(int count, int start, int end, boolean letters, boolean numbers,
                                char[] chars, Random random) {
        if (count == 0) {
            return "";
        } else if (count < 0) {
            throw new IllegalArgumentException("Requested random string length " + count + " is less than 0.");
        }
        if (chars != null && chars.length == 0) {
            throw new IllegalArgumentException("The chars array must not be empty");
        }

        if (start == 0 && end == 0) {
            if (chars != null) {
                end = chars.length;
            } else {
                if (!letters && !numbers) {
                    end = Integer.MAX_VALUE;
                } else {
                    end = 'z' + 1;
                    start = ' ';                
                }
            }
>>>[INFILL]<<<
        }

        char[] buffer = new char[count];
        int gap = end - start;

        while (count-- != 0) {
            char ch;
            if (chars == null) {
                ch = (char) (random.nextInt(gap) + start);
            } else {
                ch = chars[random.nextInt(gap) + start];
            }
            if (letters && Character.isLetter(ch)
                    || numbers && Character.isDigit(ch)
                    || !letters && !numbers) {
                if(ch >= 56320 && ch <= 57343) {
                    if(count == 0) {
                        count++;
                    } else {
                        // low surrogate, insert high surrogate after putting it in
                        buffer[count] = ch;
                        count--;
                        buffer[count] = (char) (55296 + random.nextInt(128));
                    }
                } else if(ch >= 55296 && ch <= 56191) {
                    if(count == 0) {
                        count++;
                    } else {
                        // high surrogate, insert low surrogate before putting it in
                        buffer[count] = (char) (56320 + random.nextInt(128));
                        count--;
                        buffer[count] = ch;
                    }
                } else if(ch >= 56192 && ch <= 56319) {
                    // private high surrogate, no effing clue, so skip it
                    count++;
                } else {
                    buffer[count] = ch;
                }
            } else {
                count++;
            }
        }
        return new String(buffer);
    }
The code fails on this test:
org.apache.commons.lang3.RandomStringUtilsTest::testLANG807
on this test line:
            assertTrue("Message (" + msg + ") must contain 'start'", msg.contains("start"));
with the following test error:
junit.framework.AssertionFailedError: Message (bound must be positive) must contain 'start'
Please provide an analysis of the problem and the expected behaviour of the correct fix, and the correct hunk at the infill location in the form of Java Markdown code block.

```
3. The maximum number of repair attempts allowed (including both initial repair and plausible patch generation steps) is 200 for single-line and single-hunk APR, and 100 for the single-function scenario of the experiment setting of the paper. This is too many under our study purpose, because we will analyse each response generated by CHATGPT manualy. So we set the maximum number of attempts for each bug to be 3 (when analysing responses manualy) and 24 (when comparing One-Iteration with CHATREPAIR). 