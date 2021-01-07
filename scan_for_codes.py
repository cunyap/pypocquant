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
import pandas as pd
import shutil
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import os
from pathlib import Path
from tqdm import tqdm
import multiprocessing

from pypocquant.lib.analysis import read_patient_data_by_ocr
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, rotate_if_needed_fh, \
    find_strip_box_from_barcode_data_fh, try_get_fid_from_rgb

from pypocquant.lib.io import load_and_process_image


def run_pool(files, input_folder_path, max_workers=4):
    """ Thread pool for batch processing the QR code metadata extraction.py

    :param files:
        Name of the image file
    :type files: list

    :param input_folder_path:
        Path to results input folder.
    :type input_folder_path: str

    :param max_workers:
        Max number of workers to use in parallel.
    :type max_workers: int

    :returns: void: Results writted to a .csv file directly in `input_folder_path`.

     """
    res = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        run_n = partial(run, input_folder_path=input_folder_path)
        results = list(tqdm(executor.map(run_n, files), total=len(files)))
    for result in results:
        if result is not None:
            res.append(result)

    # Save data frame
    data = pd.DataFrame(res)
    data.to_csv(str(input_folder_path / "fids.csv"), index=False)
    print(f"Results written to {str(input_folder_path / 'fids.csv')}")


def run(filename, input_folder_path):
    """ Runnable for QR code metadata extraction.

    :param filename:
        Name of the image file
    :type filename: str

    :param input_folder_path:
        Path to results input folder.
    :type input_folder_path: str

    :returns: results_row
    :rtype: dict
    """

    # Initialize results to to add to the dataframe
    results_row = {
        'filename': '',
        'fid': ''
    }

    # Load  the image
    image = load_and_process_image(str(input_folder_path / filename), raw_auto_stretch=False, raw_auto_wb=False)
    if image is None:
        return {}

    # Find the location of the barcodes
    barcode_data, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor, fid_128 = \
        try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
            image,
            lower_bound_range=(0, 5, 15, 25, 35),
            upper_bound_range=(100, 98, 95, 92, 89),
            scaling=(0.25, 0.5)
        )

    # Simple check -- if less than three QR codes were found, we have the guarantee that
    # we do not have enough information to extract the strip box.
    # @TODO: Actually check.
    if best_score < 3:
        # Add to results nd return
        results_row["filename"] = filename
        results_row["fid"] = ''
        return results_row

    # Rotate the image if needed
    image_was_rotated, image, image_log = rotate_if_needed_fh(image, barcode_data, [], verbose=False)

    # If the image was rotated, we need to find the location of the barcodes again.
    # Curiously, re-using the best percentiles we found earlier is *not* guaranteed
    # to succeed. Therefore, we search again.
    # Also, if we managed to extract patient data last time and we fail this time
    # we fall back to the previous values.
    if image_was_rotated:
        barcode_data, new_fid, new_manufacturer, new_plate, new_well, new_user, new_best_lb, \
        new_best_ub, new_best_score, new_best_scaling_factor, new_fid_128 = \
            try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )
        fid = new_fid if fid == "" and new_fid != "" else fid
        manufacturer = new_manufacturer if manufacturer == "" and new_manufacturer != "" else manufacturer
        plate = new_plate if plate == "" and new_plate != "" else plate
        well = new_well if well == "" and new_well != "" else well
        user = new_user if user == "" and new_user != "" else user

        # If we did not find the FID from the QRCODE data, did we find it with the
        # fallback CODE128 barcode?
        if fid == "" and fid_128 != "":
            fid = fid_128
        if fid == "" and new_fid_128 != "":
            fid = new_fid_128

    # If we could not find a valid FID, we try to look for code128 barcodes
    # (previous version of pyPOCQuant)
    if fid == "":
        fid = try_get_fid_from_rgb(image)

    # Store the information
    results_row['filename'] = filename
    results_row['fid'] = fid

    return results_row


if __name__ == '__main__':
    #
    # Parsing input arguments
    #
    parser = argparse.ArgumentParser(description='Extract patient data from images.')
    """ Input argument parser for extracting patient data from images. This is the command line interface for metadata
    extraction such as FID."""

    # Input folder
    parser.add_argument(
        '-f',
        '--folder',
        default='',
        help='folder to be processed'
    )

    # Max number of cores to use
    parser.add_argument(
        '-w',
        '--max_workers',
        default=2,
        help='Max number of cores to use'
    )

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

    # Input dir
    input_folder_path = Path(args['folder'])

    # Get the list of all files
    file_names = sorted(os.listdir(str(input_folder_path)))

    # Get quantification results
    run_pool(file_names, input_folder_path, max_workers)
