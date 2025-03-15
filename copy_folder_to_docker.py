# copy_folder_to_docker.py

import os
import pandas as pd
from zipfile import ZipFile, BadZipFile
import subprocess
import shutil

def get_question_details(question_id, column_name):
    csv_file_path = './commands.csv' 
    print(type(question_id))
    try:
        df = pd.read_csv(csv_file_path)
        if column_name not in df.columns:
            print(f"Column '{column_name}' not found in the CSV.")
            return None
        result = df[df['question_command_id'] == question_id]
        
        if result.empty:
            print(f"Question ID '{question_id}' not found in the CSV.")
            return None
        return str(result[column_name].iloc[0])
    
    except FileNotFoundError:
        print(f"CSV file '{csv_file_path}' not found.")
        return None
    except pd.errors.EmptyDataError:
        print("The CSV file is empty.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def check_and_delete_folder(folder_path):
    if os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path)
            print(f"Folder '{folder_path}' has been deleted.")
            return True
        except Exception as e:
            print(f"Error occurred while deleting the folder: {e}")
            return False
    else:
        print(f"Folder '{folder_path}' does not exist.")
        return False

def extract_zip(zip_path, output_folder="./workspace"):
    try:
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        print(f"Extracted '{zip_path}' to '{output_folder}'.")
        return output_folder
    except BadZipFile:
        print("The provided file is not a valid ZIP.")
        return None
    except Exception as e:
        print(f"An error occurred while extracting ZIP: {e}")
        return None

def copy_folder_to_docker(container_id, input_folder, output_folder):
    if not os.path.exists(input_folder):
        raise ValueError(f"Input folder '{input_folder}' does not exist")
    print(f"output_folder : {output_folder}")
    create_output_cmd = f"docker exec {container_id} mkdir -p {output_folder}"
    subprocess.run(create_output_cmd, shell=True, check=True)

    copy_cmd = f"docker cp {input_folder}/. {container_id}:{output_folder}"
    subprocess.run(copy_cmd, shell=True, check=True)

    print(f"Contents of '{input_folder}' have been copied to '{output_folder}' in container '{container_id}'")

def prepare_docker_environment(question_id, zip_path, container_id):
    # Get folder location from CSV
    folder = get_question_details(question_id, "question_folder_location")
    if not folder:
        print(f"Could not find folder location for question ID: {question_id}")
        return
    
    # Clean workspace
    if check_and_delete_folder("./workspace"):
        print("Workspace cleaned.")
    else:
        print("Workspace could not be cleaned or does not exist.")
    
    # Extract code from ZIP
    output_folder = extract_zip(zip_path)
    if not output_folder:
        print("Failed to extract ZIP. Aborting Docker preparation.")
        return
    
    # Copy to Docker
    try:
        copy_folder_to_docker(container_id, output_folder, folder)
    except Exception as e:
        print(f"Failed to copy folder to Docker: {e}")
