import csv
import os

def combine_csv_files(input_directory, output_file):
    combined_data = []
    headers = ['File Name', 'All Test Cases']

    # Loop through all files in the directory
    for filename in os.listdir(input_directory):
        if filename.endswith('.csv'):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip the header row
                for row in reader:
                    combined_data.append(row)

    # Write combined data to a new CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write header
        writer.writerows(combined_data)  # Write all data

if __name__ == '__main__':
    input_directory = 'C:/Users/ranji/Downloads/qr_bot_ide_questions/qr_bot_ide_questions/extracted_tests'  # Adjust this path
    output_file = 'C:/Users/ranji/Downloads/qr_bot_ide_questions/qr_bot_ide_questions/combined_tests.csv'  # Output file path
    combine_csv_files(input_directory, output_file)
