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
import shutil
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import os
from pathlib import Path
from tqdm import tqdm
import multiprocessing

from pypocquant.lib.analysis import read_patient_data_by_ocr
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, rotate_if_needed_fh, \
    find_strip_box_from_barcode_data_fh

from pypocquant.lib.io import load_and_process_image


def run_pool(files, input_folder_path, output_folder_path, undefined_path, max_workers=4, manufacturer_names=[]):
    """ Tread pool to run split images in parallel on different workers.py

    :param files:
        List of image file names to be split
    :type files: list

    :param input_folder_path:
        Path to the input folder
    :type input_folder_path: str

    :param output_folder_path:
        Path to the output folder
    :type output_folder_path: str

    :param undefined_path:
        Path to the undefined folder where unidentified images will be kept.
    :type undefined_path: str

    :param max_workers:
        Max number of workers to use.
    :type max_workers: int

    :param manufacturer_names:
        List of manufacturer names.
    :type manufacturer_names: list

    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        run_n = partial(run, input_folder_path=input_folder_path, output_folder_path=output_folder_path,
                        undefined_path=undefined_path, manufacturer_names=manufacturer_names)
        results = list(tqdm(executor.map(run_n, files), total=len(files)))


def run(filename, input_folder_path, output_folder_path, undefined_path, manufacturer_names):
    """ Runnable for splitting images by type in parallel to

    :param filename:
        Name of an image file.
    :type filename: str

    :param input_folder_path:
        Path to the input folder
    :type input_folder_path: str

    :param output_folder_path:
        Path to the output folder
    :type output_folder_path: str

    :param undefined_path:
        Path to the undefined folder where unidentified images will be kept
    :type undefined_path: str

    :param manufacturer_names:
        List of manufacturer names.
    :type manufacturer_names: list

    :returns: void

    """

    # Load  the image
    image = load_and_process_image(str(input_folder_path / filename), raw_auto_stretch=False, raw_auto_wb=False)
    if image is None:
        return

    # Find the location of the barcodes
    barcode_data, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor, fid_128 = \
        try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
            image,
            lower_bound_range=(0, 5, 15, 25, 35),
            upper_bound_range=(100, 98, 95, 92, 89),
            scaling=(0.25, 0.5)
        )

    # Rotate the image if needed
    image_was_rotated, image, image_log = rotate_if_needed_fh(image, barcode_data, [])

    # If the image was rotated, we need to find the location of the barcodes again.
    # Curiously, re-using the best percentiles we found earlier is *not* guaranteed
    # to succeed. Therefore, we search again.
    if image_was_rotated:
        barcode_data, new_fid, new_manufacturer, new_plate, new_well, new_user, _, _, _, _, _ = \
            try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )
        manufacturer = new_manufacturer if manufacturer == "" and new_manufacturer != "" else manufacturer

    # If we could not find a valid FID, we try to run OCR in a region
    # a bit larger than the box (in y direction).
    if manufacturer == "":

        # Find location of the strip box from the barcode data
        box, qr_code_extents, qc_image, box_rect = find_strip_box_from_barcode_data_fh(
            image,
            barcode_data,
            qr_code_border=30,
            qc=True)

        manufacturer = ""
        if box_rect is not None:
            box_start_y = box_rect[0] - 600
            if box_start_y < 0:
                box_start_y = 0
            area_for_ocr = image[
                           box_start_y:box_rect[1],
                           box_rect[2]:box_rect[3]
                           ]
            _, manufacturer = read_patient_data_by_ocr(area_for_ocr, known_manufacturers=manufacturer_names)

    if manufacturer != "":
        target_path = Path(output_folder_path / manufacturer.upper())
        target_path.mkdir(exist_ok=True)
        try:
            shutil.move(str(input_folder_path / filename), str(target_path))
        except Exception as e:
            e
    else:
        try:
            shutil.move(str(input_folder_path / filename), str(undefined_path))
        except Exception as e:
            e


if __name__ == '__main__':
    #
    # Parsing input arguments
    #
    parser = argparse.ArgumentParser(description='Split images by strip type.')
    """ Input argument parser for split images by strip type. This is the command line interface for splitting images 
    of a same kind (i.e same manufacturer)."""

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
        help="output folder where all results are written (if omitted, it defaults to a 'pipeline' subfolder in the input folder)."
    )

    # Max number of cores to use
    parser.add_argument(
        '-w',
        '--max_workers',
        default=2,
        help='Max number of cores to use'
    )

    # List of manufacturer names
    parser.add_argument(
        '-m',
        '--manufacturer_names',
        nargs='+',
        help='<names of manufacturers present on the image on i.e qr code labels to be detected with OCR.',
        equired=False)

    # Parse the arguments
    args = vars(parser.parse_args())

    # Max number of cores
    if args["max_workers"] == "":
        max_workers = 1
    else:
        max_workers = int(args["max_workers"])
        # limit max_workers by the max available one
        if max_workers > multiprocessing.cpu_count():
            max_workers = multiprocessing.cpu_count()

    manufacturer_names = args["manufacturer_names"]

    # Input and output dirs
    input_folder_path = Path(args['folder'])
    output_folder_path = Path(args['output_folder'])

    output_folder_path.mkdir(parents=True, exist_ok=True)

    undefined_path = Path(output_folder_path / "UNDEFINED")
    undefined_path.mkdir(parents=True, exist_ok=True)

    # Get the list of all files
    file_names = sorted(os.listdir(str(input_folder_path)))

    # Get quantification results
    run_pool(file_names, input_folder_path, output_folder_path, undefined_path, max_workers, manufacturer_names)
