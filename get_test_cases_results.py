import sys
import json
import subprocess
import re 
import pandas as pd


def extract_test_results(test_output):
    failed_tests = []
    passed_tests = []

    lines = test_output.split("\n")

    for line in lines:
        match = re.search(r'([✓✕])\s*:::(.*?):::(.*?):::', line)
        if match:
            status = match.group(1)
            test_id = match.group(2).strip()
            test_text = match.group(3).strip()
            test_case = {"id": test_id, "text": test_text}
            if status == '✕':
                failed_tests.append(test_case)
            elif status == '✓':
                passed_tests.append(test_case)

    return {
        "failed": failed_tests,
        "passed": passed_tests,
    }


def get_question_details(question_id, column_name):
    csv_file_path = 'commands.csv' 
    
    try:
        df = pd.read_csv(csv_file_path)
        if column_name not in df.columns:
            return f"Column '{column_name}' not found in the CSV."
        result = df[df['question_id'] == question_id]
        
        if result.empty:
            return f"Question ID '{question_id}' not found in the CSV."
        return str(result[column_name].iloc[0])
    
    except FileNotFoundError:
        return f"CSV file '{csv_file_path}' not found."
    except pd.errors.EmptyDataError:
        return "The CSV file is empty."
    except Exception as e:
        return f"An error occurred: {str(e)}"



def remove_ansi_escape_codes(text):
        ansi_escape = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)




def get_test_case_results(question_id):

    command = (
        f'cd {get_question_details(question_id,"question_folder_location")} && '
        'rm -rf node_modules && '
        'pnpm i -D --save-exact jest-watch-typeahead@0.6.5 && '
        f'cd {get_question_details(question_id,"question_tmp_folder_location")}  && cp -rf __tests__ {get_question_details(question_id,"question_folder_location")}/src  && cd {get_question_details(question_id,"question_folder_location")} && npm test '
    )
    docker_command = f'docker exec -it ccbp-ide /bin/bash -c "{command}"'
    process = subprocess.Popen(docker_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    print(process.returncode)
    print(stdout)
    print(stderr)

    if process.returncode == 0:
        return extract_test_results(remove_ansi_escape_codes(stdout))
    else:
        print(f"Command failed with return code {process.returncode}")
        print("Command output:", stdout)
        print("Command error:", stderr)

get_test_case_results("4f15b6eb32c443ec921fe9b408ff7c4d")
# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python script.py <question_id>")
#         sys.exit(1)
    
#     question_id = sys.argv[1]
#     results = get_test_case_results(question_id)
    
#     # Save results to a JSON file
#     with open(f'test_results_{question_id}.json', 'w') as f:
#         json.dump(results, f)