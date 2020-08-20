import argparse
import shutil
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import cv2
import os
import rawpy
from pathlib import Path
from tqdm import tqdm

from lib.analysis import read_patient_data_by_ocr
from lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, rotate_if_needed_fh, \
    find_strip_box_from_barcode_data_fh

from pypocquant.lib.io import load_and_process_image


def run_pool(files, output_folder_path, undefined_path, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        run_n = partial(run, output_folder_path=output_folder_path, undefined_path=undefined_path)
        results = list(tqdm(executor.map(run_n, files), total=len(files)))


def run(filename, output_folder_path, undefined_path):

    # Load  the image
    image = load_and_process_image(str(input_folder_path / filename), raw_auto_stretch=False, raw_auto_wb=False)
    if image is None:
        return

    # Find the location of the barcodes
    barcode_data, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor = \
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
        barcode_data, new_fid, new_manufacturer, new_plate, new_well, new_user, _, _, _, _ = \
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
            _, manufacturer = read_patient_data_by_ocr(area_for_ocr)

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

    # Parse the arguments
    args = vars(parser.parse_args())

    # Max number of cores
    if args["max_workers"] == "":
        max_workers = 1
    else:
        max_workers = int(args["max_workers"])

    # Input and output dirs
    input_folder_path = Path(args['folder'])
    output_folder_path = Path(args['output_folder'])

    output_folder_path.mkdir(parents=True, exist_ok=True)

    undefined_path = Path(output_folder_path / "UNDEFINED")
    undefined_path.mkdir(parents=True, exist_ok=True)

    # Get the list of all files
    filenames = sorted(os.listdir(str(input_folder_path)))

    # Get quantification results
    run_pool(filenames, output_folder_path, undefined_path, max_workers)
