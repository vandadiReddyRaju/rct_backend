# test.py

from copy_folder_to_docker import copy_folder_to_docker
from helpers import get_question_details
from run_test_cases import run_test_case_script
import os 
import subprocess

def test_code(question_id, zip_path, container_name):
    """
    Tests the code by preparing the Docker environment and running test cases.

    Args:
        question_id (str): The unique identifier for the question.
        zip_path (str): Path to the ZIP file.
        container_name (str): The name of the Docker container.

    Returns:
        None
    """
    # Step 1: Prepare Docker environment (extract and copy code)
    copy_folder_to_docker(container_name, zip_path, question_id)
    
    # Step 2: Run test cases
    run_test_case_script(container_name, question_id)
