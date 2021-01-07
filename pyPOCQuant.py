#  ********************************************************************************
#   Copyright © 2020-2021, ETH Zurich, D-BSSE, Andreas P. Cuny & Aaron Ponti
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU Public License v3.0
#   which accompanies this distribution, and is available at
#   http://www.gnu.org/licenses/gpl
#
#   Contributors:
#     * Andreas P. Cuny - initial API and implementation
#     * Aaron Ponti - initial API and implementation
#  *******************************************************************************

import os, sys
sys.path += [os.path.abspath('..')]

import argparse
from pathlib import Path
import sys

from pypocquant.lib.pipeline import run_pipeline
from pypocquant.lib.settings import default_settings, load_settings, save_settings

__exe__ = "pyPOCQuant"
__version__ = "0.1.0"

if __name__ == '__main__':

    #
    # Parsing input arguments
    #
    parser = argparse.ArgumentParser(description='Automated analysis tool to batch detect and quantify test line '
                                                 'signals of point of care test strips.')
    """ Input argument parser for pyPOCQuant automated analysis tool to batch detect and quantify test line signals of 
    point of care test strips.This is the command line interface. Type --help or read the manual for 
    help with the usage."""

    # Version
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=f"{__exe__} {__version__}"
    )

    # Input folder
    parser.add_argument(
        '-f',
        '--folder',
        default='',
        help='folder to be processed'
    )

    # Input folder
    parser.add_argument(
        '-o',
        '--output_folder',
        default='',
        help="output folder where all results are written (if omitted, it defaults to a 'pipeline' subfolder in the"
             " input folder)."
    )

    # Create settings file
    parser.add_argument(
        '-c',
        '--create_settings_file',
        default='',
        help='create a settings file with default values'
    )

    # Create settings file
    parser.add_argument(
        '-s',
        '--settings_file',
        default='',
        help='path to the settings file to be used for the analysis'
    )

    # Max number of cores to use
    parser.add_argument(
        '-w',
        '--max_workers',
        default=2,
        help='Max number of cores to use for running the pipeline'
    )

    # Parse the arguments
    args = vars(parser.parse_args())

    # Default parameter values
    DEFAULT_PARAMETERS = default_settings()

    # Create default settings file?
    if args["create_settings_file"] != "":
        save_settings(
            DEFAULT_PARAMETERS,
            args["create_settings_file"]
        )
        print(f"Default settings written to {args['create_settings_file']}")

        # We can exit now
        sys.exit(0)

    # Get the rest of the arguments

    # Input folder path: contains the images to be processed
    if args["folder"] == "":
        print(f"Please specify an input folder to process.")
        sys.exit(1)

    # Check that the input folder exists
    input_folder_path = Path(args["folder"])
    if not input_folder_path.is_dir():
        print(f"The input folder {input_folder_path} does not exist.")
        sys.exit(1)

    # Result folder
    if args["output_folder"] == "":
        # Defaults to a pipeline subfolder in the input folder
        results_folder_path = Path(input_folder_path / "pipeline")
    else:
        results_folder_path = Path(args["output_folder"])

    # Make sure the output folder exists
    results_folder_path.mkdir(parents=True, exist_ok=True)

    # Settings file
    if args["settings_file"] == "":
        print(f"Please specify a settings file.")
        sys.exit(1)
    settings_file = Path(args["settings_file"])
    if not settings_file.is_file():
        print(f"The settings file {settings_file} does not exist.")
        sys.exit(1)

    # Load the settings
    settings = load_settings(settings_file)

    # If the 'max_workers' parameter is in the settings file, drop it
    if 'max_workers' in settings:
        del settings['max_workers']

    # BACKWARD COMPATIBILITY
    # If the 'control_band_index' parameter is *not* in the settings file, add it
    if 'control_band_index' not in settings:
        settings['control_band_index'] = -1

    # Make sure that the settings file is usable
    if DEFAULT_PARAMETERS.keys() != settings.keys():
        setKeysDiffA = set(DEFAULT_PARAMETERS.keys()) - set(settings.keys())
        setKeysDiffB = set(settings.keys()) - set(DEFAULT_PARAMETERS.keys())
        setKeysDiff = setKeysDiffA.union(setKeysDiffB)
        print(f"The settings file {settings_file} is not valid.")
        print(f"Please check the following keys: {str(setKeysDiff)}.")
        sys.exit(1)

    # Max number of cores
    if args["max_workers"] == "":
        max_workers = 1
    else:
        max_workers = int(args["max_workers"])

    # Inform
    print(f"")
    print(f"Starting analysis with parameters:")
    print(f"                                  Input: {input_folder_path}")
    print(f"                                 Output: {results_folder_path}")
    print(f"                          Settings file: {Path(settings_file).resolve()}")
    print(f"                      Number of workers: {max_workers}")
    print(f"           RAW auto stretch intensities: {settings['raw_auto_stretch']}")
    print(f"           RAW apply auto white balance: {settings['raw_auto_wb']}")
    print(f"   Try to correct for strip orientation: {settings['strip_try_correct_orientation']}")
    print(f" Strip orientation rectangle properties: {settings['strip_try_correct_orientation_rects']}")
    print(f"     Strip text to search (orientation): {settings['strip_text_to_search']}")
    print(f"             Strip text is on the right: {settings['strip_text_on_right']}")
    print(f"                         QR code border: {settings['qr_code_border']}")
    print(f"                  Perform sensor search: {settings['perform_sensor_search']}")
    print(f"                            Sensor size: {settings['sensor_size']}")
    print(f"                          Sensor center: {settings['sensor_center']}")
    print(f"                     Sensor search area: {settings['sensor_search_area']}")
    print(f"                Sensor threshold factor: {settings['sensor_thresh_factor']}")
    print(f"                          Sensor border: {settings['sensor_border']}")
    print(f"                      Sensor band names: {settings['sensor_band_names']}")
    print(f"       Expected peak relative positions: {settings['peak_expected_relative_location']}")
    print(f"                     Control band index: {settings['control_band_index']}")
    print(f"             Subtract signal background: {settings['subtract_background']}")
    print(f"                       Force FID search: {settings['force_fid_search']}")
    print(f"                         Verbose output: {settings['verbose']}")
    print(f"         Create quality-control figures: {settings['qc']}")
    print(f"")

    # Run the pipeline
    run_pipeline(
        input_folder_path,
        results_folder_path,
        **settings,
        max_workers=max_workers
    )

    # Properly shut everything down
    sys.exit(0)
