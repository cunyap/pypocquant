import argparse
import os
import shutil
import sys
from pathlib import Path


def process(input_folder, output_folder, results_file_name='quantification_data.csv'):
    """Process input folder recursively."""

    # Get list of dirs right under input_folder
    dirs = os.listdir(input_folder)

    n_copied = 0
    # Process subdirs
    for dir in dirs:
        full_path = Path(input_folder) / dir
        if full_path.is_dir():
            entries = os.listdir(full_path)
            for entry in entries:
                entry_full_path = full_path / entry
                if Path(entry_full_path).is_dir():
                    # Test if the results file exists
                    results_file_path = entry_full_path / results_file_name
                    if results_file_path.is_file():
                        # Build target name
                        target_file_path = Path(output_folder) / Path(dir.upper() + "_" + entry.upper() + "_" + results_file_name)

                        # Copy source to target
                        shutil.copy(results_file_path, target_file_path)
                        n_copied += 1

    print(f"Copied {n_copied} files to {output_folder}.")


if __name__ == '__main__':
    #
    # Parsing input arguments
    #
    parser = argparse.ArgumentParser(description='Split images by strip type.')

    # Input folder
    parser.add_argument(
        '-f',
        '--folder',
        default='',
        help='folder to be processed recursively'
    )

    # Input folder
    parser.add_argument(
        '-o',
        '--output_folder',
        default='',
        help="output folder where all results files will be collected."
    )

    # Parse the arguments
    args = vars(parser.parse_args())

    if args["folder"] == "":
        print("Input folder not specified.")
        sys.exit(-1)

    if args["output_folder"] == "":
        args["output_folder"] = args["folder"]

    print(f"Processing folder {args['folder']}.")

    # Process
    process(args["folder"], args["output_folder"])
