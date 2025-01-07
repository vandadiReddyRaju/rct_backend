import csv
import os

# List of question directories to process
questions_to_process = [
    "congratsCard",
    "cowinDashboard",
    "cryptoCurrencyTracker",
    "debuggingCashWithdrawal",
    "debuggingFetchAndRouting",
    "instaShare",
    "notifications",
    "nxtmart",
    "simpleTodos"
]

def extract_test_cases(input_directory, output_csv):
    # Dictionary to hold aggregated test cases for each question
    test_cases_dict = {}

    for root, dirs, files in os.walk(input_directory):
        # Filter directories to only process specified questions
        if any(question in root for question in questions_to_process) and '__tests__' in dirs:
            question_name = os.path.basename(root)
            test_dir = os.path.join(root, '__tests__')
            aggregated_tests = ""  # Initialize an empty string to hold all test cases

            for file in os.listdir(test_dir):
                if file.endswith('.js'):  # Assuming JavaScript test files end with .js
                    file_path = os.path.join(test_dir, file)
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip().startswith("it('"):
                                # Append the test case to the string, enclosed in single quotes
                                aggregated_tests += "'" + line.strip() + "' "

            # Remove the trailing space and add the aggregated tests to the dictionary
            if aggregated_tests:
                test_cases_dict[question_name] = aggregated_tests.strip()

    # Write data to CSV using 'wb' mode for Python 2.7 compatibility
    with open(output_csv, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Question Name', 'Test Cases'])
        for question, tests in test_cases_dict.items():
            writer.writerow([question, tests])

if __name__ == '__main__':
    input_directory = '/home/workspace/.tmp/reactjs/coding-practices'  # Update this path
    output_csv = '/home/workspace/all_test_cases.csv'  # Update this path
    extract_test_cases(input_directory, output_csv)
