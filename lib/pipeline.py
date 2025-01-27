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

import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

from pypocquant.lib.analysis import extract_inverted_sensor, analyze_measurement_window, \
    extract_rotated_strip_from_box, get_sensor_contour_fh, use_ocr_to_rotate_strip_if_needed, \
    read_patient_data_by_ocr, use_hough_transform_to_rotate_strip_if_needed
from pypocquant.lib.barcode import rotate_if_needed_fh, find_strip_box_from_barcode_data_fh, \
    try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, get_fid_numeric_value_fh, \
    align_box_with_image_border_fh, try_get_fid_from_rgb, try_extracting_barcode_from_box_with_rotations
from pypocquant.lib.consts import Issue
from pypocquant.lib.io import load_and_process_image, is_raw
from pypocquant.lib.processing import BGR2Gray
from pypocquant.lib.settings import save_settings
from pypocquant.lib.utils import get_iso_date_from_image, get_exif_details, create_quality_control_images
from pypocquant.lib.utils import set_tesseract_exe

plt.switch_backend('qt5agg')


def run_pool(files, raw_auto_stretch, raw_auto_wb, input_folder_path,
             results_folder_path, strip_try_correct_orientation,
             strip_try_correct_orientation_rects, strip_text_to_search,
             strip_text_on_right, min_sensor_score, qr_code_border,
             perform_sensor_search, sensor_size, sensor_center,
             sensor_search_area, sensor_thresh_factor,
             sensor_border, peak_expected_relative_location,
             control_band_index, subtract_background,
             force_fid_search, sensor_band_names,
             verbose, qc, max_workers=4):
    """Run a thread pool for the analysis.

    :param files:
        List with image file names to be processed
    :type files: list

    :param raw_auto_stretch:
        Whether to automatically correct the white balance of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_stretch: bool

    :param raw_auto_wb:
        Whether to automatically stretch image intensities of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_wb: bool

    :param input_folder_path:
        Folder with the raw images to process.
    :type input_folder_path: str

    :param results_folder_path:
        Target folder, where all results and quality control figures are written.
    :type results_folder_path: str

    :param strip_try_correct_orientation:
        Try to assess and possibly correct for wrong orientation of the strip by searching for the
        position of the injection inlet.
    :type strip_try_correct_orientation: bool

    :param strip_try_correct_orientation_rects:
        Tuple containing information about the relative position of the two rectangles
        to be searched for the inlet on both sides of the center of the image:
             rectangle_props[0]: relative (0..1) vertical height of the rectangle with
                                 respect to the image height.
             rectangle_props[1]: relative (0..1) distance of the left edge of the right rectangle
                                 with respect to the center of the image.
             rectangle_props[2]: relative (0..1) distance of the left edge of the left rectangle
                                 with respect to the center of the image.
    :type strip_try_correct_orientation_rects: tuple

    :param strip_text_to_search:
        Text to search on the strip to assess orientation. Set to "" to skip.
    :type strip_text_to_search: str

    :param strip_text_on_right:
        Assuming the strip is oriented horizontally, whether the 'strip_text_to_search' text
        is assumed to be on the right. If 'strip_text_on_right' is True and the text is found on the
        left hand-side of the strip, the strip will be rotated 180 degrees. Ignored if
        strip_text_to_search is "".
    :type strip_text_on_right: bool

    :param min_sensor_score:
        Minimum segmentation score for the sensor to be considered peak analysis (0.0 <= min_sensor_score <= 1.0).
        **This is currently ignored.**
    :type min_sensor_score: float

    :param qr_code_border:
        Lateral and vertical extension of the (white) border around each QR code.
    :type qr_code_border: int

    :param perform_sensor_search:
        If True, the (inverted) sensor is searched within 'sensor_search_area' around the expected 'sensor_center';
        if False, the sensor of size 'sensor_size' is simply extracted from the strip image centered at the
        relative strip position 'sensor_center'.
    :type perform_sensor_search: bool

    :param sensor_size:
        Area of the sensor to be extracted (height, width).
    :type sensor_size: tuple

    :param sensor_center:
        Coordinates of the center of the sensor with respect to the strip image (y, x).
    :type sensor_center: tuple

    :param sensor_search_area:
        Search area around the sensor (height, width). Used only if 'skip_sensor_search' is False.
    :type sensor_search_area: tuple

    :param sensor_thresh_factor:
        Set the number of (robust) standard deviations away from the median band background for a peak
        to be considered valid.
    :type sensor_thresh_factor: int

    :param sensor_border:
        Lateral and vertical sensor border to be ignored in the analysis to avoid border effects.
    :type sensor_border: tuple

    :param peak_expected_relative_location:
        Expected relative peak positions as a function of the width of the sensor (= 1.0)
    :type peak_expected_relative_location: tuple

    :param control_band_index:
        Index of the control band in the peak_expected_relative_location.
        (Optional, default -1 := right-most)
    :type control_band_index: int

    :param subtract_background:
        If True, estimate and subtract the background of the sensor intensity profile.
    :type subtract_background: bool

    :param force_fid_search:
        If True, apply a series of search fall-back approaches to extract patient data from
        the image. Only use this if the expected QR code with patient data was not added to
        the image or could not be extracted.
    :type force_fid_search: bool

    :param sensor_band_names:
        Names of the bands for the data frame header. Please notice: the third ([2]) band is
        always the control band.
    :type sensor_band_names: tuple

    :param verbose:
        Toggle verbose output.
    :type verbose: bool

    :param qc:
        Toggle creation of quality control figures.
    :type qc: bool

    :param max_workers:
        Number of max cores to use for running the pipeline
    :type max_workers: int

    :returns: res
    :rtype: list
    :returns: log_list
    :rtype: list
    """

    res = []
    log_list = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        run_n = partial(run, raw_auto_stretch=raw_auto_stretch, raw_auto_wb=raw_auto_wb,
                        input_folder_path=input_folder_path, results_folder_path=results_folder_path,
                        strip_try_correct_orientation=strip_try_correct_orientation,
                        strip_try_correct_orientation_rects=strip_try_correct_orientation_rects,
                        strip_text_to_search=strip_text_to_search, strip_text_on_right=strip_text_on_right,
                        min_sensor_score=min_sensor_score, qr_code_border=qr_code_border,
                        perform_sensor_search=perform_sensor_search, sensor_size=sensor_size,
                        sensor_center=sensor_center, sensor_search_area=sensor_search_area,
                        sensor_thresh_factor=sensor_thresh_factor,
                        sensor_border=sensor_border,
                        peak_expected_relative_location=peak_expected_relative_location,
                        control_band_index=control_band_index,
                        subtract_background=subtract_background,
                        force_fid_search=force_fid_search,
                        sensor_band_names=sensor_band_names,
                        verbose=verbose, qc=qc)
        results = list(tqdm(executor.map(run_n, files), total=len(files)))
    for result in results:
        if result is not None:
            if result[0]:
                res.append(result[0])
            log_list.append(result[1])
    return res, log_list


def run_pipeline(
        input_folder_path: Path,
        results_folder_path: Path,
        raw_auto_stretch: bool = False,
        raw_auto_wb: bool = False,
        strip_try_correct_orientation: bool = False,
        strip_try_correct_orientation_rects: tuple = (0.52, 0.15, 0.09),
        strip_text_to_search: str = "COVID",
        strip_text_on_right: bool = True,
        min_sensor_score: float = 0.85,
        qr_code_border: int = 30,  # LSR: 30, mobile: 45
        perform_sensor_search: bool = True,
        sensor_size: tuple = (61, 249),
        sensor_center: tuple = (178, 667),
        sensor_search_area: tuple = (71, 259),
        sensor_thresh_factor: float = 2,
        sensor_border: tuple = (7, 7),
        peak_expected_relative_location: tuple = (0.25, 0.53, 0.79),
        control_band_index: int = -1,
        subtract_background: bool = True,
        force_fid_search: bool = False,
        sensor_band_names: tuple = ('igm', 'igg', 'ctl'),
        verbose: bool = False,
        qc: bool = False,
        max_workers: int = 2
):
    """Run the whole processing and analysis pipeline.

    :param input_folder_path:
        Folder with the raw images to process.
    :type input_folder_path: str

    :param results_folder_path:
        Target folder, where all results and quality control figures are written.
    :type results_folder_path: str

    :param raw_auto_stretch:
        Whether to automatically correct the white balance of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_stretch: bool

    :param raw_auto_wb:
        Whether to automatically stretch image intensities of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_wb: bool

    :param strip_try_correct_orientation:
        Try to assess and possibly correct for wrong orientation of the strip by searching for the
        position of the injection inlet.
    :type strip_try_correct_orientation: bool

    :param strip_try_correct_orientation_rects:
        Tuple containing information about the relative position of the two rectangles
        to be searched for the inlet on both sides of the center of the image:
             rectangle_props[0]: relative (0..1) vertical height of the rectangle with
                                 respect to the image height.
             rectangle_props[1]: relative (0..1) distance of the left edge of the right rectangle
                                 with respect to the center of the image.
             rectangle_props[2]: relative (0..1) distance of the left edge of the left rectangle
                                 with respect to the center of the image.
    :type strip_try_correct_orientation_rects: tuple

    :param strip_text_to_search:
        Text to search on the strip to assess orientation. Set to "" to skip.
    :type strip_text_to_search: str

    :param strip_text_on_right:
        Assuming the strip is oriented horizontally, whether the 'strip_text_to_search' text
        is assumed to be on the right. If 'strip_text_on_right' is True and the text is found on the
        left hand-side of the strip, the strip will be rotated 180 degrees. Ignored if
        strip_text_to_search is "".
    :type strip_text_on_right: bool

    :param min_sensor_score:
        Minimum segmentation score for the sensor to be considered peak analysis (0.0 <= min_sensor_score <= 1.0).
        **This is currently ignored.**
    :type min_sensor_score: float

    :param qr_code_border:
        Lateral and vertical extension of the (white) border around each QR code.
    :type qr_code_border: int

    :param perform_sensor_search:
        If True, the (inverted) sensor is searched within 'sensor_search_area' around the expected 'sensor_center';
        if False, the sensor of size 'sensor_size' is simply extracted from the strip image centered at the
        relative strip position 'sensor_center'.
    :type perform_sensor_search: bool

    :param sensor_size:
        Area of the sensor to be extracted (height, width).
    :type sensor_size: tuple

    :param sensor_center:
        Coordinates of the center of the sensor with respect to the strip image (y, x).
    :type sensor_center: tuple

    :param sensor_search_area:
        Search area around the sensor (height, width). Used only if 'skip_sensor_search' is False.
    :type sensor_search_area: tuple

    :param sensor_thresh_factor:
        Set the number of (robust) standard deviations away from the median band background for a peak
        to be considered valid.
    :type sensor_thresh_factor: int

    :param sensor_border:
        Lateral and vertical sensor border to be ignored in the analysis to avoid border effects.
    :type sensor_border: tuple

    :param peak_expected_relative_location:
        Expected relative peak positions as a function of the width of the sensor (= 1.0)
    :type peak_expected_relative_location: tuple

    :param control_band_index:
        Index of the control band in the peak_expected_relative_location.
        (Optional, default -1 := right-most)
    :type control_band_index: int

    :param subtract_background:
        If True, estimate and subtract the background of the sensor intensity profile.
    :type subtract_background: bool

    :param force_fid_search:
        If True, apply a series of search fall-back approaches to extract patient data from
        the image. Only use this if the expected QR code with patient data was not added to
        the image or could not be extracted.
    :type force_fid_search: bool

    :param sensor_band_names:
        Names of the bands for the data frame header. Please notice: the third ([2]) band is
        always the control band.
    :type sensor_band_names: tuple

    :param verbose:
        Toggle verbose output.
    :type verbose: bool

    :param qc:
        Toggle creation of quality control figures.
    :type qc: bool

    :param max_workers:
        Number of max cores to use for running the pipeline
    :type max_workers: int
    """

    # Set the path to the tesseract executable
    set_tesseract_exe()

    # Make sure the results folder exists
    results_folder_path.mkdir(exist_ok=True)

    # Get the list of file names
    filenames = sorted(os.listdir(str(input_folder_path)))

    # Get quantification results
    rows_list, log_list = run_pool(filenames, raw_auto_stretch, raw_auto_wb, input_folder_path,
                                   results_folder_path, strip_try_correct_orientation,
                                   strip_try_correct_orientation_rects, strip_text_to_search,
                                   strip_text_on_right, min_sensor_score, qr_code_border,
                                   perform_sensor_search, sensor_size, sensor_center,
                                   sensor_search_area, sensor_thresh_factor, sensor_border,
                                   peak_expected_relative_location, control_band_index,
                                   subtract_background, force_fid_search, sensor_band_names,
                                   verbose, qc, max_workers=max_workers)

    # Save data frame
    data = pd.DataFrame(rows_list)
    data.to_csv(str(results_folder_path / "quantification_data.csv"), index=False)
    print(f"Results written to {str(results_folder_path / 'quantification_data.csv')}")

    # Save log
    with open(str(results_folder_path / "log.txt"), 'w+', encoding="utf-8") as f:
        for image_log in log_list:
            f.writelines("%s\n" % item for item in image_log)
        f.close()
    print(f"Logfile written to {str(results_folder_path / 'log.txt')}")

    # Save the settings
    save_settings(
        {
            "raw_auto_stretch": raw_auto_stretch,
            "raw_auto_wb": raw_auto_wb,
            "strip_try_correct_orientation": strip_try_correct_orientation,
            "strip_try_correct_orientation_rects": strip_try_correct_orientation_rects,
            "strip_text_to_search": strip_text_to_search,
            "strip_text_on_right": strip_text_on_right,
            "qr_code_border": qr_code_border,
            "perform_sensor_search": perform_sensor_search,
            "sensor_size": sensor_size,
            "sensor_center": sensor_center,
            "sensor_search_area": sensor_search_area,
            "sensor_thresh_factor": sensor_thresh_factor,
            "sensor_border": sensor_border,
            "peak_expected_relative_location": peak_expected_relative_location,
            "control_band_index": control_band_index,
            "subtract_background": subtract_background,
            "force_fid_search": force_fid_search,
            "sensor_band_names": sensor_band_names,
            "verbose": verbose,
            "qc": qc
        },
        str(results_folder_path / "settings.conf")
    )
    print(f"Settings written to {str(results_folder_path / 'settings.conf')}")

    # Inform
    print("Pipeline completed.")


def run(
        filename,
        raw_auto_stretch,
        raw_auto_wb,
        input_folder_path: Path,
        results_folder_path: Path,
        strip_try_correct_orientation: bool,
        strip_try_correct_orientation_rects: tuple,
        strip_text_to_search: str,
        strip_text_on_right: bool,
        min_sensor_score: float = 0.85,
        qr_code_border: int = 30,  # LSR: 30, mobile: 45
        perform_sensor_search: bool = False,
        sensor_size: tuple = (37, 185),
        sensor_center: tuple = (119, 471),
        sensor_search_area: tuple = (50, 195),
        sensor_thresh_factor: float = 2,
        sensor_border: tuple = (7, 7),
        peak_expected_relative_location: tuple = (0.27, 0.55, 0.79),
        control_band_index: int = -1,
        subtract_background: bool = True,
        force_fid_search: bool = False,
        sensor_band_names: tuple = ('igm', 'igg', 'ctl'),
        verbose: bool = False,
        qc: bool = False):
    """Runnable which runs the analysis on a worker

    :param filename:
        Image file name to be processed
    :type filename: list

    :param raw_auto_stretch:
        Whether to automatically correct the white balance of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_stretch: bool

    :param raw_auto_wb:
        Whether to automatically stretch image intensities of RAW images on load.
        This does not affect JPEG images!
    :type raw_auto_wb: bool

    :param input_folder_path:
        Folder with the raw images to process.
    :type input_folder_path: str

    :param results_folder_path:
        Target folder, where all results and quality control figures are written.
    :type results_folder_path: str

    :param strip_try_correct_orientation:
        Try to assess and possibly correct for wrong orientation of the strip by searching for the
        position of the injection inlet.
    :type strip_try_correct_orientation: bool

    :param strip_try_correct_orientation_rects:
        Tuple containing information about the relative position of the two rectangles
        to be searched for the inlet on both sides of the center of the image:
             rectangle_props[0]: relative (0..1) vertical height of the rectangle with
                                 respect to the image height.
             rectangle_props[1]: relative (0..1) distance of the left edge of the right rectangle
                                 with respect to the center of the image.
             rectangle_props[2]: relative (0..1) distance of the left edge of the left rectangle
                                 with respect to the center of the image.
    :type strip_try_correct_orientation_rects: tuple

    :param strip_text_to_search:
        Text to search on the strip to assess orientation. Set to "" to skip.
    :type strip_text_to_search: str

    :param strip_text_on_right:
        Assuming the strip is oriented horizontally, whether the 'strip_text_to_search' text
        is assumed to be on the right. If 'strip_text_on_right' is True and the text is found on the
        left hand-side of the strip, the strip will be rotated 180 degrees. Ignored if
        strip_text_to_search is "".
    :type strip_text_on_right: bool

    :param min_sensor_score:
        Minimum segmentation score for the sensor to be considered peak analysis (0.0 <= min_sensor_score <= 1.0).
        **This is currently ignored.**
    :type min_sensor_score: float

    :param qr_code_border:
        Lateral and vertical extension of the (white) border around each QR code.
    :type qr_code_border: int

    :param perform_sensor_search:
        If True, the (inverted) sensor is searched within 'sensor_search_area' around the expected 'sensor_center';
        if False, the sensor of size 'sensor_size' is simply extracted from the strip image centered at the
        relative strip position 'sensor_center'.
    :type perform_sensor_search: bool

    :param sensor_size:
        Area of the sensor to be extracted (height, width).
    :type sensor_size: tuple

    :param sensor_center:
        Coordinates of the center of the sensor with respect to the strip image (y, x).
    :type sensor_center: tuple

    :param sensor_search_area:
        Search area around the sensor (height, width). Used only if 'skip_sensor_search' is False.
    :type sensor_search_area: tuple

    :param sensor_thresh_factor:
        Set the number of (robust) standard deviations away from the median band background for a peak
        to be considered valid.
    :type sensor_thresh_factor: int

    :param sensor_border:
        Lateral and vertical sensor border to be ignored in the analysis to avoid border effects.
    :type sensor_border: tuple

    :param peak_expected_relative_location:
        Expected relative peak positions as a function of the width of the sensor (= 1.0)
    :type peak_expected_relative_location: tuple

    :param control_band_index:
        Index of the control band in the peak_expected_relative_location.
        (Optional, default -1 := right-most)
    :type control_band_index: int

    :param subtract_background:
        If True, estimate and subtract the background of the sensor intensity profile.
    :type subtract_background: bool

    :param force_fid_search:
        If True, apply a series of search fall-back approaches to extract patient data from
        the image. Only use this if the expected QR code with patient data was not added to
        the image or could not be extracted.
    :type force_fid_search: bool

    :param sensor_band_names:
        Names of the bands for the data frame header. Please notice: the third ([2]) band is
        always the control band.
    :type sensor_band_names: tuple

    :param verbose:
        Toggle verbose output.
    :type verbose: bool

    :param qc:
        Toggle creation of quality control figures.
    :type qc: bool

    :returns: row_data
    :returns: image_log
    """

    # Initialize the log list
    image_log = [f" ", f"File = {filename}"]

    # Load  the image
    image = load_and_process_image(str(input_folder_path / filename), raw_auto_stretch, raw_auto_wb)
    if image is None:
        return {}, image_log

    # Initialize results to to add to the dataframe
    results_row = {
        "fid": "",
        "fid_num": "",
        "filename": filename,
        "extension": os.path.splitext(filename)[1],
        "basename": Path(filename).stem,
        "iso_date": "",
        "iso_time": "",
        "exp_time": "",
        "f_number": "",
        "focal_length_35_mm": "",
        "iso_speed": "",
        "manufacturer": "",
        "plate": "",
        "well": "",
        "issue": Issue.NONE.value
    }

    # Also the band names
    for sensor_band_name in sensor_band_names:
        results_row[sensor_band_name] = 0
        results_row[f"{sensor_band_name}_abs"] = 0.0
        results_row[f"{sensor_band_name}_ratio"] = 0.0

    # Inform
    image_log.append(f"Processing {filename}")

    # Extract ISO date from file metadata
    iso_date, iso_time = get_iso_date_from_image(str(input_folder_path / filename))
    results_row["iso_date"] = iso_date
    results_row["iso_time"] = iso_time

    # Extract additional ISO information
    exp_time, f_number, focal_length_35_mm, iso_speed = get_exif_details(str(input_folder_path / filename))
    results_row["exp_time"] = exp_time
    results_row["f_number"] = f_number
    results_row["focal_length_35_mm"] = focal_length_35_mm
    results_row["iso_speed"] = iso_speed

    # Extract the base name
    basename = Path(filename).stem

    # Store the basename in the results
    results_row["basename"] = basename

    # Find the location of the barcodes
    barcode_data, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor, fid_128 = \
        try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
            image,
            lower_bound_range=(0, 5, 15, 25, 35),
            upper_bound_range=(100, 98, 95, 92, 89),
            scaling=(0.25, 0.5)
        )

    # Inform
    if verbose:
        image_log.append(
            f"Best percentiles for barcode extraction: ({best_lb}, {best_ub}); "
            f"best scaling factor = {best_scaling_factor}; score = {best_score}/6"
        )

    # Simple check -- if less than three QR codes were found, we have the guarantee that
    # we do not have enough information to extract the strip box.
    # @TODO: Actually check.
    if best_score < 3:
        # Add issue to the results
        results_row["issue"] = Issue.STRIP_BOX_EXTRACTION_FAILED.value
        image_log.append(f"File {filename}: QR/barcode extraction failed. Skipping.")
        row_data = {}
        row_data.update(results_row)
        return row_data, image_log

    # Rotate the image if needed
    image_was_rotated, image, image_log = rotate_if_needed_fh(image, barcode_data, image_log, verbose=verbose)

    # Create quality control images
    if qc:
        create_quality_control_images(
            str(results_folder_path),
            filename.replace('.', '_'),
            {
                "rotated": image
            },
            extension=".jpg",
            quality=85
        )

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

        image_log.append(f"Detected FIDs for rotated image: {fid} {new_fid} {fid_128} {new_fid_128}")

        # Inform
        if verbose:
            image_log.append(
                f"File {filename}: best percentiles for barcode extraction after "
                f"rotation: ({new_best_lb}, {new_best_ub}); "
                f"best scaling factor = {new_best_scaling_factor}; "
                f"score = {new_best_score}/6"
            )

    # Align the strip box with the image borders (remove potential rotation)
    image, box_rotation_angle = align_box_with_image_border_fh(barcode_data, image)

    # Inform
    if verbose:
        image_log.append(
            f"File {filename}: Strip box image rotated by angle {box_rotation_angle} "
            f"degrees using QR code locations.")

    # Create quality control images
    if qc:
        create_quality_control_images(
            str(results_folder_path),
            filename.replace('.', '_'),
            {
                "aligned_box": image
            },
            extension=".jpg",
            quality=85
        )

    # In case there was still a significant rotation, find the location of the barcodes yet again
    if abs(box_rotation_angle) > 0.5:
        barcode_data, _, _, _, _, _, _, _, best_score, _, fid_128 = \
            try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )

    # Find location of the strip box from the barcode data
    box, qr_code_extents, qc_image, box_rect = find_strip_box_from_barcode_data_fh(
        image,
        barcode_data,
        qr_code_border=qr_code_border,
        qc=True)

    if box is None or box.shape[0] == 0 or box.shape[1] == 0:
        image_log.append(f"File {filename}: could not extract strip box. Skipping!")

        # Add issue to the results and return
        results_row["issue"] = Issue.STRIP_BOX_EXTRACTION_FAILED.value
        row_data = {}
        row_data.update(results_row)
        return row_data, image_log

    # Create quality control images
    if qc:
        create_quality_control_images(
            str(results_folder_path),
            filename.replace('.', '_'),
            {
                "box": qc_image
            },
            extension=".jpg",
            quality=85
        )
    # If we could not find a valid FID, we try to look for code128 barcodes
    # (previous version of pyPOCQuant)
    if fid == "":
        if fid_128 != "":
            fid = fid_128
        else:
            if force_fid_search:
                fid = try_get_fid_from_rgb(image)

    # If at this stage we haven't found the FID, and 'force_fid_search' is
    # set to True, we try with a series of fallback attempts to extract it
    # from the image.
    #
    # Next attempt, look for the barcode attached to the strip (we use the
    # whole box anyway). If this works, however, we will only find the FID
    # and no information about the manufacturer. (This is a fallback for old
    # images coming from a previous study.)
    if fid == "" and force_fid_search:
        # Extract the barcode
        fid, image_log = try_extracting_barcode_from_box_with_rotations(
            box,
            scaling=(1.0, 0.5, 0.25),
            verbose=verbose,
            log_list=image_log
        )

    # If we still could not find a valid FID, we try to run OCR in a region
    # a bit larger than the box (in y direction). Some images had a label with
    # the FID attached above the strip box.
    if fid == "" and force_fid_search:
        box_start_y = box_rect[0] - 600
        if box_start_y < 0:
            box_start_y = 0
        area_for_ocr = image[
                       box_start_y:box_rect[1],
                       box_rect[2]:box_rect[3]
                       ]
        fid, new_manufacturer = read_patient_data_by_ocr(area_for_ocr)
        if manufacturer == "" and new_manufacturer != "":
            # Update manufacturer
            manufacturer = new_manufacturer

    # Do we have a valid FID? If we do not have a valid FID,
    # we can still try and continue with the analysis. Some
    # strips are annotated by hand, and the band result could
    # still be associated to a patient by manually curating the
    # results in the end.
    if fid == "":
        # Add issue to the results
        results_row["issue"] = Issue.FID_EXTRACTION_FAILED.value
        image_log.append(f"File {filename}: could not extract FID. "
                         f"Will proceed with the analysis.")

    # Store patient data into the results
    results_row["fid"] = fid
    results_row["manufacturer"] = manufacturer
    results_row["plate"] = plate
    results_row["well"] = well
    results_row["user"] = user
    results_row["fid_num"] = get_fid_numeric_value_fh(fid)
    if verbose:
        image_log.append(f"File {filename}: FID = '{fid}'")

    # Convert box to gray value
    box_gray = BGR2Gray(box)

    # Crop the strip from the box while correcting for possible rotation
    strip_gray, strip = extract_rotated_strip_from_box(box_gray, box)
    if strip_gray is None:

        # Log failure
        image_log.append(f"File {filename}: could not extract strip. Skipping!")

        # Add issue to the results and return
        results_row["issue"] = Issue.STRIP_EXTRACTION_FAILED.value
        row_data = {}
        row_data.update(results_row)
        return row_data, image_log

    # Make a copy of the strip images for analysis
    strip_for_analysis = strip.copy()
    strip_gray_for_analysis = strip_gray.copy()

    # Always save the (aligned) strip image
    create_quality_control_images(
        str(results_folder_path),
        filename.replace('.', '_'),
        {
            "strip_gray_aligned": strip_gray_for_analysis
        }
    )

    # Since the strip is sometimes placed facing the wrong direction
    # in the box, we will try (if the user requested it, that is) a
    # couple of approaches to determine whether we should rotate it
    # 180 degrees.

    if strip_try_correct_orientation:
        # Use the Hough transform to look for expected details in the
        # strip. If needed, ask the function to perform an intensity stretch.
        stretch = is_raw(filename) and raw_auto_stretch is False
        strip_gray_for_analysis, strip_for_analysis, qc_image, was_rotated, _, _ = \
            use_hough_transform_to_rotate_strip_if_needed(
                strip_gray_for_analysis,
                strip_try_correct_orientation_rects,
                stretch=stretch,
                img=strip_for_analysis,
                qc=qc
            )

        # Inform
        image_log.append(f"File {filename}: the image {'was' if was_rotated else 'was not'} rotated "
                         f"based on Hough transform analysis.")

        # If requested, save the quality control image
        create_quality_control_images(
            str(results_folder_path),
            filename.replace('.', '_'),
            {
                "strip_gray_hough_analysis_candidates": qc_image,
                "strip_gray_hough_analysis": strip_gray_for_analysis
            }
        )

    # Use tesseract to find expected text from the strip.
    if strip_text_to_search != "":
        strip_gray_for_analysis, strip_for_analysis, was_rotated = \
            use_ocr_to_rotate_strip_if_needed(
                strip_gray_for_analysis,
                strip_for_analysis,
                strip_text_to_search,
                strip_text_on_right
            )

        # Inform
        image_log.append(f"File {filename}: the image {'was' if was_rotated else 'was not'} rotated "
                         f"based on OCR analysis.")

        # Save the (aligned) strip image
        create_quality_control_images(
            str(results_folder_path),
            filename.replace('.', '_'),
            {
                "strip_gray_OCR_analysis": strip_gray_for_analysis
            }
        )

    if perform_sensor_search:

        # Extract the sensor
        sensor, sensor_coords, sensor_score = get_sensor_contour_fh(
            strip_gray_for_analysis,
            sensor_center=sensor_center,
            sensor_size=sensor_size,
            sensor_search_area=sensor_search_area,
            peak_expected_relative_location=peak_expected_relative_location,
            control_band_index=control_band_index,
            min_control_bar_width=5
        )

        if verbose:
            image_log.append(f"File {filename}: sensor coordinates = {sensor_coords}, score = {sensor_score}")

    else:
        # Extract the sensor
        sensor = extract_inverted_sensor(
            strip_gray_for_analysis,
            sensor_center=sensor_center,
            sensor_size=sensor_size
        )
        sensor_score = 1.0

    # Make sure that the sensor could be extracted
    if sensor.shape[0] == 0 or sensor.shape[1] == 0:
        image_log.append(f"File {filename}: could not extract the sensor. Skipping!")

        # Add issue to the results and return
        results_row["issue"] = Issue.SENSOR_EXTRACTION_FAILED.value
        row_data = {}
        row_data.update(results_row)
        return row_data, image_log

    # Add the sensor score to the results
    # results_row["sensor_score"] = sensor_score

    # Always save the sensor image
    create_quality_control_images(
        str(results_folder_path),
        filename.replace('.', '_'),
        {
            "sensor": sensor,
        }
    )

    # Analyse the sensor (it sensor score is >= min_sensor_score)
    if sensor_score >= min_sensor_score:

        # Some (rare) strips have extremely narrow bands. If the normal analysis
        # fails, we try with a narrower peak_width
        peak_widths = [7, 3]
        successful_peak_width = -1
        window_results = dict()
        for curr_peak_width in peak_widths:

            # We have a sensor image and we can proceed with the analysis
            window_results, image_log = analyze_measurement_window(
                sensor,
                border_x=sensor_border[0],
                border_y=sensor_border[1],
                sensor_band_names=sensor_band_names,
                peak_expected_relative_location=peak_expected_relative_location,
                control_band_index=control_band_index,
                subtract_background=subtract_background,
                thresh_factor=sensor_thresh_factor,
                peak_width=curr_peak_width,
                out_qc_folder=results_folder_path,
                basename=filename.replace('.', '_'),
                qc=True,
                verbose=verbose,
                image_log=image_log
            )

            # Do we have a control band in the results?
            if sensor_band_names[control_band_index] in window_results:
                successful_peak_width = curr_peak_width
                break

        # If we have band results, we append them to the dataframe row.

        # The values default to zero, so we do not need to explicitly set them in the
        # corresponding band is missing. If the control band is missing, however, we
        # add flag the issue in the result row.

        # First, we check the control band
        control_band_name = sensor_band_names[control_band_index]
        if control_band_name in window_results:
            results_row[control_band_name] = 1
            results_row[f"{control_band_name}_abs"] = window_results[control_band_name]["signal"]
            results_row[f"{control_band_name}_ratio"] = window_results[control_band_name]["normalized_signal"]

            # Inform
            band_type = "normal" if successful_peak_width == peak_widths[0] else "narrow"
            image_log.append(f"File {filename}: the bands were '{band_type}'.")
        else:
            # Inform
            image_log.append(f"File {filename}: the strip does not seem to have a valid control band!")

            # Add issue to the results
            results_row["issue"] = Issue.CONTROL_BAND_MISSING.value

        # Now process all other bands
        for current_sensor_band in sensor_band_names:
            if current_sensor_band == control_band_name:
                continue

            if current_sensor_band in window_results:
                results_row[current_sensor_band] = 1
                results_row[f"{current_sensor_band}_abs"] = window_results[current_sensor_band]["signal"]
                results_row[f"{current_sensor_band}_ratio"] = window_results[current_sensor_band]["normalized_signal"]

    else:
        # Inform
        image_log.append(f"File {filename}: the sensor did not reach the minimum acceptable "
                         f"score and will be dropped.")

        # The sensor extraction failed. Report the issue
        results_row["issue"] = Issue.SENSOR_EXTRACTION_FAILED.value

    # Save data as dictionary and append to a list of dicts for fast df creation with many rows
    row_data = {}
    row_data.update(results_row)

    # Inform
    if verbose:
        image_log.append(f"✓ File {filename}: successfully processed and added to results table.")

    return row_data, image_log
