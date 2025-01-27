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

import argparse
import cv2
import rawpy
from pathlib import Path
import sys

__exe__ = "extractPOCT"
__version__ = "0.1.0"

from pypocquant.lib.analysis import extract_rotated_strip_from_box, use_hough_transform_to_rotate_strip_if_needed
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, rotate_if_needed_fh, \
    align_box_with_image_border_fh, find_strip_box_from_barcode_data_fh
from pypocquant.lib.io import load_and_process_image
from pypocquant.lib.processing import BGR2Gray
from pypocquant.lib.tools import extract_strip

if __name__ == '__main__':

    #
    # Parsing input arguments
    #
    parser = argparse.ArgumentParser(description='Extract POCT from selected image to help defining analysis paremeters.')
    """ Input argument parser for extracting POCT from a selected image.
    """

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
        '--filename',
        default='',
        help='image to be processed'
    )

    # Input folder
    parser.add_argument(
        '-o',
        '--output_filename',
        default='',
        help="output file name"
    )

    parser.add_argument(
        '-b-',
        '--border',
        default=40,
        type=int,
        help="extension of the white border of the QR codes."
    )

    parser.add_argument(
        '-r',
        '--raw_auto_stretch',
        action='store_true',
        help="apply auto-stretch of intensities for RAW images (only)."
    )

    parser.add_argument(
        '-w',
        '--raw_auto_wb',
        action='store_true',
        help="apply auto white-balancing for RAW images (only)."
    )

    parser.add_argument(
        '-t',
        '--text_to_search',
        default='',
        help="text to search on the strip."
    )

    parser.add_argument(
        '-g',
        '--text_on_right',
        action='store_true',
        help="whether the text to search on the strip should be on the right."
    )

    # Parse the arguments
    args = vars(parser.parse_args())

    # Extract the arguments
    filename = args["filename"]
    output_filename = args["output_filename"]
    qr_code_border = args["border"]
    raw_auto_stretch = args["raw_auto_stretch"]
    raw_auto_wb = args["raw_auto_wb"]
    strip_text_to_search = args["text_to_search"]
    strip_text_on_right = args["text_on_right"]

    # Check that the input file exists
    if not Path(filename).is_file():
        print(f"Error: The file {filename} does not exist!")
        sys.exit(-1)

    # Load  the image
    image = load_and_process_image(filename, raw_auto_stretch, raw_auto_wb)

    # Run the extraction
    strip_image, error_msg = extract_strip(image, qr_code_border, strip_text_to_search, strip_text_on_right)

    if strip_image is None:
        print(f"Sorry, extraction failed. {error_msg}.")
    else:
        # Save the final image
        cv2.imwrite(output_filename, strip_image)
        print(f"Successfully saved extracted POCT to {output_filename}.")
