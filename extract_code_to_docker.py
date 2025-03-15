#!/usr/bin/env python3
import os
import pandas as pd
from zipfile import ZipFile
import shutil
import logging
import sys
import webbrowser
import time
import subprocess

# ---------------------- Configuration ----------------------

CSV_FILE_PATH = "commands.csv"  # Path to your CSV file
WORKSPACE_DIR = "./workspace"  # Temporary workspace for extraction
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Path to Chrome
BASE_WORKSPACE_URL = "http://localhost/#"  # Base workspace URL
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")  # Directory to look for ZIP files
DOCKER_CONTAINER_ID = "dd5790b111f4"  # Replace with your Docker container ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ---------------------- Helper Functions ----------------------

def get_latest_zip_file(download_dir):

    """
    Finds the latest ZIP file in the specified directory.
    """
    try:
        zip_files = [f for f in os.listdir(download_dir) if f.lower().endswith('.zip')]
        if not zip_files:
            logging.error(f"No ZIP files found in '{download_dir}'.")
            return None

        zip_files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
        latest_zip = os.path.join(download_dir, zip_files[0])
        logging.info(f"Latest ZIP file found: '{latest_zip}'.")
        return latest_zip
    except Exception as e:
        logging.error(f"Error finding latest ZIP file: {e}")
        return None

def get_question_folder_location(command_id, csv_file_path):
    """
    Fetches the folder_location from the CSV based on question_command_id.
    """
    try:
        df = pd.read_csv(csv_file_path)
        if "question_command_id" not in df.columns or "question_folder_location" not in df.columns:
            logging.error("Required columns not found in the CSV.")
            return None

        result = df[df['question_command_id'] == command_id]
        if result.empty:
            logging.error(f"No entry found in CSV for question_command_id '{command_id}'.")
            return None

        folder_location = str(result['question_folder_location'].iloc[0])
        logging.info(f"Retrieved folder_location: '{folder_location}' from CSV.")
        return folder_location
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
        return None

def open_workspace_in_chrome(folder_location):
    """
    Opens the specific workspace in Chrome using the folder_location.
    """
    # Construct the full URL
    workspace_url = f"{BASE_WORKSPACE_URL}/{folder_location.lstrip('/')}"
    logging.info(f"Opening workspace in Chrome at {workspace_url}...")
    webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(CHROME_PATH))
    webbrowser.get("chrome").open(workspace_url)
    logging.info("Workspace opened successfully in Chrome.")

def check_and_delete_folder(folder_path):
    """
    Deletes the specified folder if it exists.
    """
    if os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path)
            logging.info(f"Folder '{folder_path}' has been deleted.")
        except Exception as e:
            logging.error(f"Error occurred while deleting folder: {e}")

def extract_zip_to_workspace(zip_file_path, output_folder):
    """
    Extracts a ZIP file to the specified output folder.
    """
    try:
        with ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        logging.info(f"Extracted ZIP file to '{output_folder}'.")
    except Exception as e:
        logging.error(f"Failed to extract ZIP file: {e}")
        sys.exit(1)

def copy_folder_to_docker(container_id, input_folder, output_folder):
    """
    Copies the extracted folder contents to the workspace folder inside the Docker container.
    """
    if not os.path.exists(input_folder):
        logging.error(f"Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    try:
        logging.info(f"Copying folder contents to Docker container at '{output_folder}'...")
        create_folder_cmd = f"docker exec {container_id} mkdir -p {output_folder}"
        subprocess.run(create_folder_cmd, shell=True, check=True)

        copy_cmd = f"docker cp {input_folder}/. {container_id}:{output_folder}"
        subprocess.run(copy_cmd, shell=True, check=True)

        logging.info(f"Folder contents successfully copied to '{output_folder}' in container '{container_id}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error copying files to Docker: {e}")
        sys.exit(1)

# ---------------------- Main Script ----------------------

def main():
    # Step 1: Find the latest ZIP file
    latest_zip = get_latest_zip_file(DOWNLOADS_DIR)
    if not latest_zip:
        logging.error("Failed to find the latest ZIP file. Exiting.")
        sys.exit(1)

    # Step 2: Extract command_id from ZIP file name
    command_id = os.path.splitext(os.path.basename(latest_zip))[0]
    logging.info(f"Extracted command_id: '{command_id}'.")

    # Step 3: Get folder location from CSV
    folder_location = get_question_folder_location(command_id, CSV_FILE_PATH)
    if not folder_location:
        logging.error("Failed to retrieve folder location. Exiting.")
        sys.exit(1)

    # Step 4: Open workspace in Chrome
    open_workspace_in_chrome(folder_location)

    # Step 5: Wait for the workspace to load
    logging.info("Waiting for the workspace to initialize...")
    time.sleep(10)  # Adjust delay as needed

    # Step 6: Prepare and copy workspace contents to Docker
    check_and_delete_folder(WORKSPACE_DIR)
    extract_zip_to_workspace(latest_zip, WORKSPACE_DIR)
    copy_folder_to_docker(DOCKER_CONTAINER_ID, WORKSPACE_DIR, folder_location)

    logging.info("Workspace updated successfully.")

if __name__ == "__main__":
    main()
