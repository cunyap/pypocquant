from pypocquant.lib.analysis import extract_rotated_strip_from_box, use_hough_transform_to_rotate_strip_if_needed, \
    use_ocr_to_rotate_strip_if_needed
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh, rotate_if_needed_fh, \
    align_box_with_image_border_fh, find_strip_box_from_barcode_data_fh
from pypocquant.lib.processing import BGR2Gray


def extract_strip(image, qr_code_border, strip_text_to_search="", strip_text_on_right=True):
    """Attempts to extract the strip from the original image.
    :param image: numpy array
        RGB image to be processed.

    :param qr_code_border: int
        Lateral and vertical extension of the (white) border around each QR code.

    :param strip_text_to_search: str
        Text to search on the strip to assess orientation. Set to "" to skip.

    :param strip_text_on_right: bool
        Assuming the strip is oriented horizontally, whether the 'strip_text_to_search' text
        is assumed to be on the right. If 'strip_text_on_right' is True and the text is found on the
        left hand-side of the strip, the strip will be rotated 180 degrees. Ignored if
        strip_text_to_search is "".

    :return (strip, error_msg): Tuple
        strip: Strip image (RGB) or None if extraction fails.
        error_msg: If strip is None, the cause of failure will be stored in error_message.
    """

    # Find the location of the barcodes
    barcode_data, _, _, _, _, _, _, _, best_score, _ = \
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
        return None, "Failed decoding QR codes to extract POCT position."

    # Rotate the image if needed
    image_was_rotated, image, image_log = rotate_if_needed_fh(
        image,
        barcode_data,
        [],
        verbose=False
    )

    # If the image was rotated, we need to find the location of the barcodes again.
    # Curiously, re-using the best percentiles we found earlier is *not* guaranteed
    # to succeed. Therefore, we search again.
    # Also, if we managed to extract patient data last time and we fail this time
    # we fall back to the previous values.
    if image_was_rotated:
        barcode_data, _, _, _, _, _, _, _, _, _ = \
            try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )

    # Align the strip box with the image borders (remove potential rotation)
    image, box_rotation_angle = align_box_with_image_border_fh(barcode_data, image)

    # Find location of the strip box from the barcode data
    box, qr_code_extents, qc_image, box_rect = find_strip_box_from_barcode_data_fh(
        image,
        barcode_data,
        qr_code_border=qr_code_border,
        qc=False)

    if box is None or box.shape[0] == 0 or box.shape[1] == 0:
        return None, "Could not extract POCT from barcode data."

    # Convert box to gray value
    box_gray = BGR2Gray(box)

    # Crop the strip from the box while correcting for possible rotation
    strip_gray, strip = extract_rotated_strip_from_box(box_gray, box)

    # Make a copy of the strip images for analysis
    strip_for_analysis = strip.copy()
    strip_gray_for_analysis = strip_gray.copy()

    # Since the strip is sometimes placed facing the wrong direction
    # in the box, we will try a couple of approaches to determine
    # whether we should rotate it 180 degrees.

    # Use the Hough transform to look for expected details in the
    # strip.
    strip_gray_for_analysis, strip_for_analysis, _, _ = \
        use_hough_transform_to_rotate_strip_if_needed(
            strip_gray_for_analysis,
            strip_for_analysis,
            qc=False
        )

    # Use tesseract to find expected text from the strip.
    strip_gray_for_analysis, strip_for_analysis, _ = \
        use_ocr_to_rotate_strip_if_needed(
            strip_gray_for_analysis,
            strip_for_analysis,
            strip_text_to_search,
            strip_text_on_right
        )

    return strip_for_analysis, ""
