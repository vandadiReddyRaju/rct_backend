# run_test_cases.py

import subprocess

def run_test_case_script(container_name, question_id):
    """
    Runs test cases inside the specified Docker container.

    Args:
        container_name (str): The name of the Docker container.
        question_id (str): The unique identifier for the question.

    Returns:
        dict: A dictionary containing test results.
    """
    try:
        # Example command to run tests, adjust according to your testing framework
        test_command = f"docker exec {container_name} python /path/to/test_script.py {question_id}"
        result = subprocess.run(test_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Parse the test results from stdout
        # This is highly dependent on how your test script outputs results
        # For demonstration, assume it returns JSON
        import json
        test_results = json.loads(result.stdout)
        return test_results
    except subprocess.CalledProcessError as e:
        print(f"Test execution failed: {e.stderr}")
        return {"failed": ["Test execution failed"]}
    except Exception as e:
        print(f"An unexpected error occurred during test execution: {e}")
        return {"failed": [str(e)]}
