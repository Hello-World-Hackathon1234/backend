import os

def process_files_in_directory(directory_path, output_file_path):
    """
    Iterates through all files in a given directory, reads their content,
    and writes the filename and content to an output file.

    Args:
        directory_path (str): The path to the directory to process.
        output_file_path (str): The path to the output text file.
    """
    try:
        # Get a list of all files and directories in the specified path
        print("lol")
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for entry in os.scandir(directory_path):
                print("lol2")
                if entry.is_file():
                    try:
                        with open(entry.path, 'r', encoding='utf-8', errors='ignore') as infile:
                            print("lol3")
                            content = infile.read()
                            outfile.write(f"--- {entry.name} ---\n")
                            outfile.write(content)
                            outfile.write("\n\n")
                    except Exception as e:
                        print(f"Error reading file {entry.name}: {e}")
        print(f"Successfully processed files and wrote to {output_file_path}")

    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # Replace '.' with the path to the directory you want to process.
    # '.' refers to the current directory where the script is located.
    directory_to_process = './'

    # The name of the output file.
    output_filename = './output.txt'
    # --- End of Configuration ---

    process_files_in_directory(directory_to_process, output_filename)