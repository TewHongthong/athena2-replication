"""Hand-authored seed snippets that follow the GSCS document (the 'standard code' ground truth).

These are NOT real-world code: real open-source code does not follow a 2015 in-house standard, so there is no
compliant version to compare against.  Each seed is small, contains one documented function, and lists the
identifiers Athena Sim may corrupt (name, kind).
Edit / add seeds here and rerun build_gscs_pack.py.
"""


def hdr(lang: str, indent: str, objective: str, params: str, desc: str, ret: str) -> str:
    lines = [f"Function Objective: {objective}", f"Input parameters : {params}",
             f"Function description: {desc}", f"Return Value : {ret}", "Created By : Programmer A",
             "Create Date: 2026-09-28", "Revised By:", "Revised Date:"]
    if lang == "python":
        return "\n".join(f"{indent}# {l}" for l in lines)
    first = f"{indent}/* {lines[0]}"
    rest = [f"{indent}   {l}" for l in lines[1:]]
    return "\n".join([first] + rest + [f"{indent}*/"])


_GPAX = dict(objective="Compute the GPAX of one student",
             params="f_point_total (float) weighted grade points, f_credit_total (float) registered credits",
             desc="Divide the weighted grade points by the registered credits, capped at the maximum GPAX",
             ret="float GPAX value")
_REPORT = dict(objective="Print one line of the grade report",
               params="str_student_name (string) student name, f_gpax (float) GPAX value",
               desc="Shorten a long name to the maximum length, then print the name and the GPAX",
               ret="void")
_COUNT = dict(objective="Count the scores that reach the pass mark",
              params="i_score_list (integer list) all scores, i_pass_score (integer) pass mark",
              desc="Walk through the scores and count every score that is at least the pass mark",
              ret="int number of passed scores")
_AVERAGE = dict(objective="Compute the average score of a class",
                params="i_total_score (integer) sum of all scores, i_student_total_num (integer) number of students",
                desc="Divide the total score by the number of students; a class without students gives zero",
                ret="float average score")

_DEPOSIT = dict(objective="Add money to an account",
                params="d_amount (double) money to add",
                desc="Add the amount to the balance only when it reaches the minimum deposit",
                ret="void")
_CELSIUS = dict(objective="Convert a Fahrenheit text to Celsius",
                params="str_text (string) temperature in Fahrenheit written as text",
                desc="Read the text as a number and convert it to Celsius; text that is not a number gives zero",
                ret="float temperature in Celsius")
_VOWEL = dict(objective="Count the vowels of a word",
              params="str_word (string) the word to check",
              desc="Walk through the characters of the word and count every vowel",
              ret="int number of vowels")
_ADDCOUNT = dict(objective="Increase the counter by a step",
                 params="i_step_size (integer) amount to add",
                 desc="Add the step to the counter, but never let the counter pass the maximum count",
                 ret="void")
_PRICE = dict(objective="Read a price from text",
              params="str_price_text (string) price written as text",
              desc="Convert the text to a number rounded to two decimals; text that is not a number gives zero",
              ret="float price")
_SORTED = dict(objective="Check whether numbers are in ascending order",
               params="i_number_list (integer list) the numbers to check",
               desc="Compare every number with the next one and report whether all pairs are in order",
               ret="boolean true when the list is sorted")
_SETNAME = dict(objective="Store the name of a student",
                params="str_new_name (string) the new student name",
                desc="Keep the new name, shortened to the maximum name size when it is too long",
                ret="void")
_MAXIMUM = dict(objective="Find the largest value in a list",
                params="f_value_list (float array) the values, f_value_total (integer) number of values",
                desc="Start from the first value and keep the largest value seen while walking through the list",
                ret="float largest value")
_SHOWGRADE = dict(objective="Print pass or fail for a score",
                  params="f_score_point (float) the score of a student",
                  desc="Print pass when the score reaches the pass point, otherwise print fail",
                  ret="void")

SEEDS = [
    # ------------------------------------------------------------------ Java
    {"id": "gscs_java_001", "language": "java", "function": ("f_Calculate_Gpax", "function"),
     "header": hdr("java", "    ", **_GPAX),
     "template": """class student_Type {
{HEADER}
    static float f_Calculate_Gpax(float f_point_total, float f_credit_total) {
        final float MAX_GPAX = 4.0f;
        float f_gpax = 0.0f;
        // check that credits were registered
        if (f_credit_total > 0) {
            f_gpax = f_point_total / f_credit_total;
        }
        // else no credit registered, keep GPAX at zero
        else {
            f_gpax = 0.0f;
        }
        return Math.min(f_gpax, MAX_GPAX);
    }
}""",
     "identifiers": [("student_Type", "class"), ("f_Calculate_Gpax", "function"), ("f_point_total", "parameter"),
                     ("f_credit_total", "parameter"), ("f_gpax", "variable"), ("MAX_GPAX", "constant")]},
    {"id": "gscs_java_002", "language": "java", "function": ("Print_Report", "procedure"),
     "header": hdr("java", "    ", **_REPORT),
     "template": """class report_Type {
{HEADER}
    static void Print_Report(String str_student_name, float f_gpax) {
        final int MAX_NAME_LENGTH = 30;
        boolean bln_Is_Name_Long = str_student_name.length() > MAX_NAME_LENGTH;
        // check whether the name must be shortened
        if (bln_Is_Name_Long) {
            System.out.println(str_student_name.substring(0, MAX_NAME_LENGTH) + " " + f_gpax);
        }
        // else the name fits on one line
        else {
            System.out.println(str_student_name + " " + f_gpax);
        }
    }
}""",
     "identifiers": [("report_Type", "class"), ("Print_Report", "procedure"), ("str_student_name", "parameter"),
                     ("f_gpax", "parameter"), ("MAX_NAME_LENGTH", "constant"), ("bln_Is_Name_Long", "boolean_variable")]},
    {"id": "gscs_java_003", "language": "java", "function": ("i_Count_Passed", "function"),
     "header": hdr("java", "    ", **_COUNT),
     "template": """class score_Type {
{HEADER}
    static int i_Count_Passed(int[] i_score_list, int i_pass_score) {
        int i_passed_total = 0;
        // count every score that reaches the pass mark
        for (int i_index = 0; i_index < i_score_list.length; i_index++) {
            // check the score against the pass mark
            if (i_score_list[i_index] >= i_pass_score) {
                i_passed_total = i_passed_total + 1;
            }
            // else the score is below the pass mark, skip it
            else {
                i_passed_total = i_passed_total + 0;
            }
        }
        return i_passed_total;
    }
}""",
     "identifiers": [("score_Type", "class"), ("i_Count_Passed", "function"), ("i_score_list", "parameter"),
                     ("i_pass_score", "parameter"), ("i_passed_total", "variable"), ("i_index", "variable")]},
    # ------------------------------------------------------------------ Python
    {"id": "gscs_python_001", "language": "python", "function": ("f_Calculate_Gpax", "function"),
     "header": hdr("python", "    ", **_GPAX),
     "template": """class student_Type:
{HEADER}
    def f_Calculate_Gpax(self, f_point_total, f_credit_total):
        MAX_GPAX = 4.0
        f_gpax = 0.0
        # check that credits were registered
        if f_credit_total > 0:
            f_gpax = f_point_total / f_credit_total
        # else no credit registered, keep GPAX at zero
        else:
            f_gpax = 0.0
        return min(f_gpax, MAX_GPAX)""",
     "identifiers": [("student_Type", "class"), ("f_Calculate_Gpax", "function"), ("f_point_total", "parameter"),
                     ("f_credit_total", "parameter"), ("f_gpax", "variable"), ("MAX_GPAX", "constant")]},
    {"id": "gscs_python_002", "language": "python", "function": ("Print_Report", "procedure"),
     "header": hdr("python", "", **_REPORT),
     "template": """{HEADER}
def Print_Report(str_student_name, f_gpax):
    MAX_NAME_LENGTH = 30
    bln_Is_Name_Long = len(str_student_name) > MAX_NAME_LENGTH
    # check whether the name must be shortened
    if bln_Is_Name_Long:
        print(str_student_name[:MAX_NAME_LENGTH], f_gpax)
    # else the name fits on one line
    else:
        print(str_student_name, f_gpax)""",
     "identifiers": [("Print_Report", "procedure"), ("str_student_name", "parameter"), ("f_gpax", "parameter"),
                     ("MAX_NAME_LENGTH", "constant"), ("bln_Is_Name_Long", "boolean_variable")]},
    {"id": "gscs_python_003", "language": "python", "function": ("f_Get_Average", "function"),
     "header": hdr("python", "", **_AVERAGE),
     "template": """{HEADER}
def f_Get_Average(i_total_score, i_student_total_num):
    f_average = 0.0
    bln_Is_Done = False
    try:
        # divide the total score by the number of students
        f_average = i_total_score / i_student_total_num
    except ZeroDivisionError:
        # no student registered, the average stays zero
        f_average = 0.0
    finally:
        # mark the calculation as finished
        bln_Is_Done = True
    return f_average""",
     "identifiers": [("f_Get_Average", "function"), ("i_total_score", "parameter"),
                     ("i_student_total_num", "parameter"), ("f_average", "variable"),
                     ("bln_Is_Done", "boolean_variable")]},
    # ------------------------------------------------------------------ C++
    {"id": "gscs_cpp_001", "language": "cpp", "function": ("f_Calculate_Gpax", "function"),
     "header": hdr("cpp", "    ", **_GPAX),
     "template": """class student_Type {
public:
{HEADER}
    float f_Calculate_Gpax(float f_point_total, float f_credit_total) {
        const float MAX_GPAX = 4.0f;
        float f_gpax = 0.0f;
        // check that credits were registered
        if (f_credit_total > 0) {
            f_gpax = f_point_total / f_credit_total;
        }
        // else no credit registered, keep GPAX at zero
        else {
            f_gpax = 0.0f;
        }
        return f_gpax < MAX_GPAX ? f_gpax : MAX_GPAX;
    }
};""",
     "identifiers": [("student_Type", "class"), ("f_Calculate_Gpax", "function"), ("f_point_total", "parameter"),
                     ("f_credit_total", "parameter"), ("f_gpax", "variable"), ("MAX_GPAX", "constant")]},
    {"id": "gscs_cpp_002", "language": "cpp", "function": ("Print_Report", "procedure"),
     "header": hdr("cpp", "", **_REPORT),
     "template": """#include <iostream>
#include <string>
{HEADER}
void Print_Report(std::string str_student_name, float f_gpax) {
    const int MAX_NAME_LENGTH = 30;
    bool bln_Is_Name_Long = str_student_name.length() > MAX_NAME_LENGTH;
    // check whether the name must be shortened
    if (bln_Is_Name_Long) {
        std::cout << str_student_name.substr(0, MAX_NAME_LENGTH) << " " << f_gpax << std::endl;
    }
    // else the name fits on one line
    else {
        std::cout << str_student_name << " " << f_gpax << std::endl;
    }
}""",
     "identifiers": [("Print_Report", "procedure"), ("str_student_name", "parameter"), ("f_gpax", "parameter"),
                     ("MAX_NAME_LENGTH", "constant"), ("bln_Is_Name_Long", "boolean_variable")]},
    {"id": "gscs_cpp_003", "language": "cpp", "function": ("i_Count_Passed", "function"),
     "header": hdr("cpp", "", **{**_COUNT, "params": "i_score_list (integer array) all scores, i_score_total (integer) number of scores, i_pass_score (integer) pass mark"}),
     "template": """{HEADER}
int i_Count_Passed(const int i_score_list[], int i_score_total, int i_pass_score) {
    int i_passed_total = 0;
    // count every score that reaches the pass mark
    for (int i_index = 0; i_index < i_score_total; i_index++) {
        // check the score against the pass mark
        if (i_score_list[i_index] >= i_pass_score) {
            i_passed_total = i_passed_total + 1;
        }
        // else the score is below the pass mark, skip it
        else {
            i_passed_total = i_passed_total + 0;
        }
    }
    return i_passed_total;
}""",
     "identifiers": [("i_Count_Passed", "function"), ("i_score_list", "parameter"), ("i_score_total", "parameter"),
                     ("i_pass_score", "parameter"), ("i_passed_total", "variable"), ("i_index", "variable")]},
    # ------------------------------------------------------------------ second batch (added before any LLM run)
    {"id": "gscs_java_004", "language": "java", "function": ("Deposit_Money", "procedure"),
     "header": hdr("java", "    ", **_DEPOSIT),
     "template": """class account_Type {
    private double d_balance = 0.0;
{HEADER}
    void Deposit_Money(double d_amount) {
        final double MIN_DEPOSIT = 1.0;
        boolean bln_Is_Valid = d_amount >= MIN_DEPOSIT;
        // check that the amount is large enough to deposit
        if (bln_Is_Valid) {
            d_balance = d_balance + d_amount;
        }
        // else the amount is too small, keep the balance
        else {
            d_balance = d_balance + 0.0;
        }
    }
}""",
     "identifiers": [("account_Type", "class"), ("d_balance", "field"), ("Deposit_Money", "procedure"),
                     ("d_amount", "parameter"), ("MIN_DEPOSIT", "constant"), ("bln_Is_Valid", "boolean_variable")]},
    {"id": "gscs_java_005", "language": "java", "function": ("f_Convert_Celsius", "function"),
     "header": hdr("java", "    ", **_CELSIUS),
     "template": """class temperature_Type {
{HEADER}
    static float f_Convert_Celsius(String str_text) {
        final float FREEZING_POINT = 32.0f;
        float f_celsius = 0.0f;
        try {
            // read the Fahrenheit value from the text
            float f_fahrenheit = Float.parseFloat(str_text);
            f_celsius = (f_fahrenheit - FREEZING_POINT) * 5.0f / 9.0f;
        } catch (NumberFormatException e) {
            // the text is not a number, keep zero
            f_celsius = 0.0f;
        } finally {
            // nothing to release, the result is ready
            f_celsius = f_celsius + 0.0f;
        }
        return f_celsius;
    }
}""",
     "identifiers": [("temperature_Type", "class"), ("f_Convert_Celsius", "function"), ("str_text", "parameter"),
                     ("FREEZING_POINT", "constant"), ("f_celsius", "variable"), ("f_fahrenheit", "variable")]},
    {"id": "gscs_java_006", "language": "java", "function": ("i_Count_Vowels", "function"),
     "header": hdr("java", "    ", **_VOWEL),
     "template": """class word_Type {
{HEADER}
    static int i_Count_Vowels(String str_word) {
        final String VOWEL_LIST = "aeiou";
        int i_vowel_total = 0;
        // check every character of the word
        for (int i_pos = 0; i_pos < str_word.length(); i_pos++) {
            // check whether the character is a vowel
            if (VOWEL_LIST.indexOf(str_word.charAt(i_pos)) >= 0) {
                i_vowel_total = i_vowel_total + 1;
            }
            // else the character is not a vowel, skip it
            else {
                i_vowel_total = i_vowel_total + 0;
            }
        }
        return i_vowel_total;
    }
}""",
     "identifiers": [("word_Type", "class"), ("i_Count_Vowels", "function"), ("str_word", "parameter"),
                     ("VOWEL_LIST", "constant"), ("i_vowel_total", "variable"), ("i_pos", "variable")]},
    {"id": "gscs_python_004", "language": "python", "function": ("Add_Count", "procedure"),
     "header": hdr("python", "    ", **_ADDCOUNT),
     "template": """class counter_Type:
    def __init__(self):
        self.i_count_total = 0
{HEADER}
    def Add_Count(self, i_step_size):
        MAX_COUNT = 100
        bln_Is_Full = self.i_count_total + i_step_size > MAX_COUNT
        # check whether the counter would pass the limit
        if bln_Is_Full:
            self.i_count_total = MAX_COUNT
        # else the counter still fits under the limit
        else:
            self.i_count_total = self.i_count_total + i_step_size""",
     "identifiers": [("counter_Type", "class"), ("i_count_total", "field"), ("Add_Count", "procedure"),
                     ("i_step_size", "parameter"), ("MAX_COUNT", "constant"), ("bln_Is_Full", "boolean_variable")]},
    {"id": "gscs_python_005", "language": "python", "function": ("f_Parse_Price", "function"),
     "header": hdr("python", "", **_PRICE),
     "template": """{HEADER}
def f_Parse_Price(str_price_text):
    MISSING_PRICE = 0.0
    f_price = MISSING_PRICE
    try:
        # convert the text to a number
        f_price = float(str_price_text)
    except ValueError:
        # the text is not a number, keep the default price
        f_price = MISSING_PRICE
    finally:
        # the value is ready, round it to two decimals
        f_price = round(f_price, 2)
    return f_price""",
     "identifiers": [("f_Parse_Price", "function"), ("str_price_text", "parameter"), ("MISSING_PRICE", "constant"),
                     ("f_price", "variable")]},
    {"id": "gscs_python_006", "language": "python", "function": ("bln_Is_Sorted", "function"),
     "header": hdr("python", "", **_SORTED),
     "template": """{HEADER}
def bln_Is_Sorted(i_number_list):
    bln_Sorted_So_Far = True
    # compare every number with the next one
    for i_index in range(len(i_number_list) - 1):
        # check that the pair is in ascending order
        if i_number_list[i_index] > i_number_list[i_index + 1]:
            bln_Sorted_So_Far = False
        # else the pair is in order, keep the answer
        else:
            bln_Sorted_So_Far = bln_Sorted_So_Far
    return bln_Sorted_So_Far""",
     "identifiers": [("bln_Is_Sorted", "function"), ("i_number_list", "parameter"), ("bln_Sorted_So_Far", "boolean_variable"),
                     ("i_index", "variable")]},
    {"id": "gscs_cpp_004", "language": "cpp", "function": ("Set_Name", "procedure"),
     "header": hdr("cpp", "    ", **_SETNAME),
     "template": """#include <string>
class pupil_Type {
private:
    std::string str_student_name;
public:
{HEADER}
    void Set_Name(std::string str_new_name) {
        const int MAX_NAME_SIZE = 30;
        bool bln_Is_Long = str_new_name.size() > MAX_NAME_SIZE;
        // check whether the name must be shortened
        if (bln_Is_Long) {
            str_student_name = str_new_name.substr(0, MAX_NAME_SIZE);
        }
        // else the name fits, keep it
        else {
            str_student_name = str_new_name;
        }
    }
};""",
     "identifiers": [("pupil_Type", "class"), ("str_student_name", "field"), ("Set_Name", "procedure"),
                     ("str_new_name", "parameter"), ("MAX_NAME_SIZE", "constant"), ("bln_Is_Long", "boolean_variable")]},
    {"id": "gscs_cpp_005", "language": "cpp", "function": ("f_Find_Maximum", "function"),
     "header": hdr("cpp", "", **_MAXIMUM),
     "template": """{HEADER}
float f_Find_Maximum(const float f_value_list[], int i_value_total) {
    float f_maximum = f_value_list[0];
    // check every value after the first one
    for (int i_index = 1; i_index < i_value_total; i_index++) {
        // check whether the value is larger than the current maximum
        if (f_value_list[i_index] > f_maximum) {
            f_maximum = f_value_list[i_index];
        }
        // else the value is not larger, keep the maximum
        else {
            f_maximum = f_maximum + 0.0f;
        }
    }
    return f_maximum;
}""",
     "identifiers": [("f_Find_Maximum", "function"), ("f_value_list", "parameter"), ("i_value_total", "parameter"),
                     ("f_maximum", "variable"), ("i_index", "variable")]},
    {"id": "gscs_cpp_006", "language": "cpp", "function": ("Show_Grade", "procedure"),
     "header": hdr("cpp", "", **_SHOWGRADE),
     "template": """#include <iostream>
{HEADER}
void Show_Grade(float f_score_point) {
    const float PASS_POINT = 50.0f;
    bool bln_Has_Passed = f_score_point >= PASS_POINT;
    // check whether the score reaches the pass point
    if (bln_Has_Passed) {
        std::cout << "pass" << std::endl;
    }
    // else the score is below the pass point
    else {
        std::cout << "fail" << std::endl;
    }
}""",
     "identifiers": [("Show_Grade", "procedure"), ("f_score_point", "parameter"), ("PASS_POINT", "constant"),
                     ("bln_Has_Passed", "boolean_variable")]},
]

# Development / test split, fixed BEFORE any LLM was run.  Dev (tuning) = the 003 and 006 seed of every language;
# everything else is test and must not be used to tune prompts or retrieval settings.
DEV_IDS = {f"gscs_{lang}_{n}" for lang in ("java", "python", "cpp") for n in ("003", "006")}
for _seed in SEEDS:
    _seed["split"] = "dev" if _seed["id"] in DEV_IDS else "test"
