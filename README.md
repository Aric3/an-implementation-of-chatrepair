# Project Overview
This repository provides an implementation of the `chatrepair` approach and our experiment results. The folder structure outlined below helps to organize the project components for ease of use.

## Folder Structure

```plaintext
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

## Setup Instructions

### 1. Clone the Repository

Begin by cloning this project to your local machine.

### 2. Install the Defects4j Dataset

Install **Defects4j** and configure the environment path. Make sure that all **Defects4j** commands are accessible, as this script requires running `checkout`, `compile`, and `test` commands.

### 3. Install Python Dependencies

This project requires two external Python dependencies: `javalang` and `openai`. Install them using `pip`:

```bash
pip install javalang
pip install openai
```

Note: A Python version of **3.10** or higher is recommended for compatibility with the OpenAI API.

### 4. Set OpenAI API Key and Base URL

Edit the `constants.py` file to configure your OpenAI API key and base URL.

### 5. Run the Script

You can execute the script using the following command:

```bash
python main.py [first_argument] [second_argument] [third_argument]
```

- **First Argument**:
    - `initial-save`: Generate and save the initial prompt for all bugs in a project.
    - `initial-chat`: Interact with ChatGPT using the initial prompt.
    - `chatrepair`: Execute the chatrepair method implemented in this project.

- **Second Argument**: Choose from one of the following projects:
    - `Lang`, `Chart`, `Closure`, `Mockito`, `Math`, `Time`

- **Third Argument**: Select `y` or `n` to specify whether to use single function prompts or not:
    - `y`: Use single-function prompt.
    - `n`: Use single-hunk and single-line prompt.

## Important Notes

1. **Few Shot Example Clarification**:  
   The original **CHATREPAIR** paper did not provide a specific "Few Shot Example" format, and the example number is one. The prompts used in this repository are derived from the flowchart illustrating the **chatrepair** method in the paper. The response format follows a predefined template, as shown below:

   **Example Response**:

   ```plaintext
   1. Analysis of the problem:
   The issue arises due to the comparison of hours using `Calendar.HOUR`, which represents the 12-hour clock. The code should instead use `Calendar.HOUR_OF_DAY` to reflect the 24-hour clock.

   2. Expected Behavior of the Correct Fix:
   The fix should ensure that comparisons are made using `Calendar.HOUR_OF_DAY` to maintain consistency with other fields.

   3. Correct Code at the Infill Location:
   ```java
   cal1.get(Calendar.HOUR_OF_DAY) == cal2.get(Calendar.HOUR_OF_DAY) &&
   ```
   ```

2. **Prompt Design for Deletion and Insertion Patches**:  
   The **CHATREPAIR** paper does not provide explicit instructions on how to design prompts for patches involving line deletions or insertions in single-hunk or single-line scenarios. So we looked for the same way that fill-in-the-blank fixes handle the deletion and addition of lines of code that the author used in his published article *Automated Program Repair in the Era of Large Pre trained Language Models*. Link: https://zenodo.org/records/7592886
   
   For deletion-type fixes, the paper uses padding markers to replace code that should be removed. For insertion-type fixes, the paper uses markup to indicate where code should be inserted. This method, however, may provide extraneous information and lead to potential misdirections.

   We do not think this is a wise way for a repair task especially for delete type patch because it may provide extral information and cause misdirection.  
   
   Our random selection did not select a single hunk bug whose developer patch is deletion type.
   For an insertion type patch, INFILL marker will be embedded at the expecting repair place. 

   **Example Prompt of Insertion-Type Patch**:

   ```plaintext
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

       // Additional code...
   }
   ```

3. **Maximum Repair Attempts**:  
The maximum number of repair attempts allowed (including both initial repair and plausible patch generation steps) is 200 for single-line and single-hunk APR, and 100 for the single-function scenario of the experiment setting of the paper. 
This is too many for our study purpose, because we will analyse each response generated by ChatGPT manualy. So we limit the maximum number of attempts to **3** for manual analysis and **24** when comparing **One-Iteration** with **CHATREPAIR**.

---
