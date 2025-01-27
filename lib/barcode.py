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

import cv2
import imutils
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
from pytesseract import Output
from pyzbar.locations import Rect
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from re import findall
from skimage import exposure
import math
import re
from typing import Union

from pypocquant.lib.processing import BGR2Gray
from pypocquant.lib.consts import SymbolTypes


class Barcode(object):
    """Pythonic barcode object."""

    def __init__(self, top: int, left: int, width: int, height: int, data: Union[bytes, str], symbol: str):
        """Constructor."""
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        if type(data) is bytes:
            self.data = data.decode("utf-8")
        else:
            self.data = data
        self.symbol = symbol

    @classmethod
    def from_barcode(cls, barcode):
        """Initialize from pyzbar barcode object.

        :param barcode:
            A barcode (QR, CODE39, CODE128).

        """
        top = barcode.rect.top
        left = barcode.rect.left
        width = barcode.rect.width
        height = barcode.rect.height
        data = barcode.data
        symbol = barcode.type
        return cls(top, left, width, height, data, symbol)

    def scale(self, factor: float):
        """Scale the barcode object by given factor.

        The (top, left) is scaled accordingly.

        :param factor:
            Scaling factor for the barcode.

        """
        self.top = int(factor * self.top)
        self.left = int(factor * self.left)
        self.width = int(factor * self.width)
        self.height = int(factor * self.height)

    def __str__(self):
        return f"Barcode of type '{self.symbol}' " \
               f"and data '{self.data}' at " \
               f"location ({self.left}, {self.top}) " \
               f"and size ({self.width}, {self.height})"

    def __repr__(self):
        return f"{self.__class__.__name__}(" \
               f"top={self.top}, left={self.left}, " \
               f"width={self.width}, height={self.height}, " \
               f"data='{self.data}', symbol='{self.symbol}')"


def detect(image: np.ndarray, expected_area=22000, expected_aspect_ratio=7.5, barcode_border=75, blur_size=(3, 3),
           morph_rect=(9, 3), mm_iter=1, qc=True, verbose=False):
    """Detect the barcode in the image.

    Adapted from: https://www.pyimagesearch.com/2014/11/24/detecting-barcodes-images-python-opencv/

    Returns the extracted barcode image, the coordinates of the extracted rectangle,
    the (possibly rotated) image, and (if qc is True) a copy of the (possibly rotated)
    image with the extracted rectangle coordinates overlaid on it.

    :param image:
        Image from which barcode should be read
    :type image: np.ndarray

    :param expected_area:
        Expected area for barcode.
    :type expected_area: int

    :param expected_aspect_ratio:
        Aspect ratio for barcode.
    :type expected_aspect_ratio: float

    :param barcode_border:
        Border of the barcode.
    :type barcode_border: int

    :param blur_size:
        Kernel (3,3) by default for bluring the image.
    :type blur_size: tuple

    :param morph_rect:
        Kernel (9,3) by default for morph rect.
    :type morph_rect: tuple

    :param mm_iter:
        Dilation & Eroding iterations.
    :type mm_iter: int

    :param qc:
        Bool, if true quality control images will be saved.
    :type qc: bool

    :param verbose:
        Bool, if true additional loggin info will be displayed.
    :type verbose: bool

    :returns: barcode_img:
        The image of the barcode.
    :returns: coordinates:
        The position and size coordinates of the barcode (x,y, w, h)/
    :rtype: coordinates: tuple
    :returns: image:
        The image.
    :returns: mask_image
        The mask of the image.
    :rtype: tuple

    """

    # Make sure the image is an array with three "channels"
    if type(image) is not np.ndarray:
        image = np.ndarray(image)

    if image.shape[2] != 3:
        raise Exception("RGB or BGR image expected.")

    # Run the extraction and check the orientation of the barcode and
    # the image. If necessary, rotate the image and rerun the extraction.
    y = 0
    x = 0
    h = image.shape[0]
    w = image.shape[1]
    box = [[x, y], [x, h], [y, w], [w, h]]
    correct_orientation = False
    num_rotations = 0
    give_up = False
    while correct_orientation is False:

        if num_rotations > 5:
            print(f"Giving up trying rotations.")
            give_up = True
            break

        if verbose:
            print(f"Rotations so far: {num_rotations}")

        # We start with a copy of the B/W image
        gray = BGR2Gray(image).copy()

        # Sharpen the image
        blurred = cv2.GaussianBlur(gray, (9, 9), 10.0)
        gray = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0, image)

        # Image main axes
        x_mid = gray.shape[1] / 2
        y_mid = gray.shape[0] / 2

        # Compute the Scharr gradient magnitude representation of the images
        # in both the x and y direction using OpenCV
        gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)

        # Subtract the y-gradient from the x-gradient
        gradient = cv2.subtract(gradX, gradY)
        gradient = cv2.convertScaleAbs(gradient)

        # Blur and threshold the image
        blurred = cv2.blur(gradient, blur_size)
        (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

        # Construct a closing kernel and apply it to the thresholded image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, morph_rect)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Perform a series of erosions and dilations
        closed = cv2.erode(closed, None, iterations=mm_iter)
        closed = cv2.dilate(closed, None, iterations=mm_iter)

        # Find the contours in the thresholded image, then sort the contours
        # by their area, keeping only the largest one
        cnts = cv2.findContours(
            closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = imutils.grab_contours(cnts)

        # Now do the same with a 90-degree rotated morphological rectangle
        kernel_rot = cv2.getStructuringElement(
            cv2.MORPH_RECT, (morph_rect[1], morph_rect[0]))
        closed_rot = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_rot)

        # Perform a series of erosions and dilations
        closed_rot = cv2.erode(closed_rot, None, iterations=mm_iter)
        closed_rot = cv2.dilate(closed_rot, None, iterations=mm_iter)

        # Find the contours in the thresholded image, then sort the contours
        # by their area, keeping only the largest one
        cnts_rot = cv2.findContours(
            closed_rot.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c_rot = imutils.grab_contours(cnts_rot)

        # Process all contours in the two orientations, and pick the best

        c_areas = []
        c_aspect_ratios = []
        for current in c:
            area_c, aspect_ratio_c = calc_area_and_approx_aspect_ratio(current)
            c_areas.append(area_c - expected_area)
            c_aspect_ratios.append(aspect_ratio_c - expected_aspect_ratio)

        c_scores = []
        if len(c_areas) > 0:
            c_score_area = np.array(c_areas) / np.std(c_areas)
            c_score_aspect_ratio = np.array(
                c_aspect_ratios) / np.std(c_aspect_ratios)
            c_scores = np.sqrt(c_score_area ** 2 + c_score_aspect_ratio ** 2)
            if verbose:
                print(f"Min c score = {np.min(c_scores)}")

        c_rot_areas = []
        c_rot_aspect_ratios = []
        for current_rot in c_rot:
            area_c_rot, aspect_ratio_c_rot = calc_area_and_approx_aspect_ratio(
                current_rot)
            c_rot_areas.append(area_c_rot - expected_area)
            c_rot_aspect_ratios.append(
                aspect_ratio_c_rot - expected_aspect_ratio)

        c_rot_scores = []
        if len(c_rot_areas) > 0:
            c_rot_score_area = np.array(c_rot_areas) / np.std(c_rot_areas)
            c_rot_score_aspect_ratio = np.array(
                c_rot_aspect_ratios) / np.std(c_rot_aspect_ratios)
            c_rot_scores = np.sqrt(c_rot_score_area ** 2 +
                                   c_rot_score_aspect_ratio ** 2)
            if verbose:
                print(f"Min c_rot score = {np.min(c_rot_scores)}")

        # If both orientations failed to provide any contour,
        # there is no point to try with a 90-degree rotation.
        if len(c_scores) == 0 and len(c_rot_scores) == 0:
            return None, (0, 0, 0, 0), None, None

        # Find the orientation with the best score
        best_c_score_index = -1
        best_c_score = np.inf
        if len(c_scores) > 0:
            best_c_score_index = np.array(c_scores).argmin(axis=0)
            best_c_score = c_scores[best_c_score_index]

        best_c_rot_score_index = -1
        best_c_rot_score = np.inf
        if len(c_rot_scores) > 0:
            best_c_rot_score_index = np.array(c_rot_scores).argmin(axis=0)
            best_c_rot_score = c_rot_scores[best_c_rot_score_index]

        # Which direction of the filters gave the best response?
        if best_c_rot_score < best_c_score:
            # Rotate the original image by 90 degrees cw
            image = rotate(image, -90)
            correct_orientation = False
            num_rotations += 1
            if verbose:
                print(f"Rotated image by 90 degrees clockwise.")
            continue

        # If we are here, the c contours contain the best score.

        # Extract the winning contour
        c = c[best_c_score_index]

        # Inform
        if verbose:
            print(f"Best score = {best_c_score}")

        # Compute the rotated bounding box of the largest contour
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # Extract the bar code
        x, y, w, h = cv2.boundingRect(box)

        # One more control to make sure the orientation is correct
        if w > h:

            # The image is either oriented correctly, or flipped 180 degrees
            # towards the bottom.
            if y < y_mid:

                # The image seems to be oriented correctly
                correct_orientation = True

            else:

                # The (original) image must be rotated 180 degrees
                image = rotate(image, 180)

                # Inform
                if verbose:
                    print(f"Rotated image by 180 degrees.")

                # Try again
                correct_orientation = False
                num_rotations += 1

                # Skip the rest
                continue

        else:

            # Try another rotation by 90 degrees cw
            image = rotate(image, -90)
            correct_orientation = False
            num_rotations += 1
            if verbose:
                print(f"Rotated image by 90 degrees clockwise.")
            continue

    if give_up is True:
        return None, (0, 0, 0, 0), None, None

    # Now extract the barcode image with a user-defined border around (and make B/W)
    b_y0 = y - barcode_border
    if b_y0 < 0:
        b_y0 = 0
    b_y = y + h + barcode_border
    if b_y > image.shape[0]:
        b_y = image.shape[0]
    b_x0 = x - barcode_border
    if b_x0 < 0:
        b_x0 = 0
    b_x = x + w + barcode_border
    if b_x > image.shape[1]:
        b_x = image.shape[1]
    barcode_img = image[b_y0: b_y, b_x0: b_x].copy()
    barcode_img = BGR2Gray(barcode_img)

    # Draw a bounding box around the detected barcode
    mask_image = None
    if qc:
        mask_image = image.copy()
        cv2.drawContours(mask_image, [box], -1, (0, 255, 0), 3)
        # plt.imshow(mask_image)
        # plt.show()

    # Return
    return barcode_img, (b_x0, b_y0, barcode_img.shape[1], barcode_img.shape[0]), image, mask_image


def rotate(image, angle):
    """Rotate the image by given angle in degrees.

    :param image:
        The image to be rotated.
    :param angle:
        Rotation angle in degrees for the image.

    :returns: image:
        Rotated image.
    """

    if angle == 0:
        return image

    # Image size
    height, width = image.shape[:2]

    # Image center, for getRotationMatrix2D() in (x, y) order
    center = (width / 2, height / 2)

    # Get transformation matrix for the rotation with the given angle
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculate the size of the rotated bounding box
    abs_cos = abs(M[0, 0])
    abs_sin = abs(M[0, 1])
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # Subtract old image center and add new image center coordinates
    M[0, 2] += bound_w / 2 - center[0]
    M[1, 2] += bound_h / 2 - center[1]

    # Now rotate with the calculated target image size
    return cv2.warpAffine(image, M, (bound_w, bound_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def calc_area_and_approx_aspect_ratio(contour):
    """Calculate area and approximate aspect ratio of a contour.

    :param contour:
        cv2.Contour.

    :returns: area:
        Area of the contour.
    :returns: aspect_ratio:
        Aspect ratio of the contour.

    """

    # Calculate area
    area = cv2.contourArea(contour)

    # Calculate aspect ratio
    x = []
    y = []
    for c in contour:
        x.append(c[0][0])
        y.append(c[0][1])

    dx = max(x) - min(x)
    dy = max(y) - min(y)
    aspect_ratio = dx / dy if dy > 0 else np.Inf

    return area, aspect_ratio


def rotate_90_if_needed(image):
    """Try to estimate the orientation of the image, and rotate if needed.

    @TODO: This is not very robust so far.

    :param image:
        Image to be rotated by 90 degrees.

    :returns: image:
        By 90 degrees rotated image.
    """

    # We start with a copy of the B/W image
    gray = BGR2Gray(image).copy()

    # Blur
    blur_gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Extract edges
    low_threshold = 50
    high_threshold = 150
    edges = cv2.Canny(blur_gray, low_threshold, high_threshold)

    rho = 1  # distance resolution in pixels of the Hough grid
    theta = np.pi / 90  # angular resolution in radians of the Hough grid
    # minimum number of votes (intersections in Hough grid cell)
    threshold = 250
    min_line_length = 500  # minimum number of pixels making up a line
    max_line_gap = 100  # maximum gap in pixels between connectable line segments
    line_image = np.copy(gray) * 0  # creating a blank to draw lines on

    # Run Hough on edge detected image
    # Output "lines" is an array containing endpoints of detected line segments
    lines = cv2.HoughLinesP(edges, rho, theta, threshold,
                            np.array([]), min_line_length, max_line_gap)

    v_votes = 0
    h_votes = 0
    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 5)
            if abs(x2 - x1) > abs(y2 - y1):
                h_votes += 1
            else:
                v_votes += 1

    plt.imshow(line_image)
    plt.show()

    if h_votes > v_votes:
        image = rotate(image, -90)

    return image


def read_FID_from_barcode_image(image):
    """
    Read the FID string from the barcode image using pytesseract and
    decode the barcode itself using pyzbar.

    :param image:
        Image to read FID from barcode.

    :returns: fid_tesseract:
        FID detected by tesseract (OCR).
    :returns: fid_pyzbar:
        FID detected by pyzbar (barcode).

    :returns: score:
        Score how well FID detection worked. For more details about the score read the manual.
    """

    fid_tesseract = ""
    fid_pyzbar = ""

    if image is None:
        return fid_tesseract, fid_pyzbar

    # Use pytesseract to extract the FID
    text = pytesseract.image_to_string(image, lang='eng')
    fid = findall(r'\d{7}', text)
    if fid and len(fid) == 1:
        fid_tesseract = 'F' + fid[0]
    else:
        fid_tesseract = ""

    # Use pyzbar to decode the barcode
    decoded_objects = decode(image, SymbolTypes.TYPES.value)
    for obj in decoded_objects:
        if obj.type == "CODE128":
            fid_pyzbar = obj.data.decode("utf-8")

    # Give a score to the extraction (max is 3)
    if fid_tesseract == "" and fid_pyzbar == "":
        score = 0
    else:
        score = sum([
            fid_tesseract != "",
            fid_pyzbar != "",
            fid_tesseract == fid_pyzbar and fid_tesseract != ""])

    return fid_tesseract, fid_pyzbar, score


def get_fid_from_barcode_data(barcode_data, barcode_type="CODE128"):
    """Parse the output of pyzbar and retrieve the FID.

    :param barcode_data:
        Barcode data (zbar).
    :param barcode_type:
        Type of barcode (CODE39, CODE128, QRCODE).

    :returns: barcode:
        Decoded barcode as utf8.
    """
    for barcode in barcode_data:
        if barcode.type == barcode_type:
            return barcode.data.decode("utf-8")
    return ""


def get_fid_from_box_image_using_ocr(box_img):
    """Use pytesseract to retrieve FID from the strip box image.

    :param box_img:
        Image of the QR code box.

    :returns: fid_tesseract:
        FID detected by tesseract from image using OCR.
    """

    # Use pytesseract to extract the FID
    text = pytesseract.image_to_string(box_img, lang='eng')
    fid = findall(r'\d{7}', text)
    if fid and len(fid) == 1:
        fid_tesseract = fid[0]
    else:
        # Try rotating the image 90 degrees counter-clockwise
        box_img_90 = rotate(box_img, -90)
        text = pytesseract.image_to_string(box_img, lang='eng')
        fid = findall(r'\d{7}', text)
        if fid and len(fid) == 1:
            fid_tesseract = fid[0]
        else:
            fid_tesseract = ""

    return fid_tesseract


def try_extracting_barcode_from_box_with_rotations(box, scaling=(1.0, 0.5, 0.25), verbose=False, log_list=None):
    """  Try extracting barcode from QR code box while scaling it for different orientations [0, 90, 180, -90].

    :param box:
        QR code box
    :param scaling:
        Scaling factors.
    :param verbose:
        Display additional logging information to the console.
    :param log_list:
        Log list.

    :returns: fid:
        FID number

    :returns: log_list
        Appended Log list with current log information.
    """

    # Switch to RGB
    rgb = cv2.cvtColor(box, cv2.COLOR_BGR2RGB)

    fid = ""
    rotations = [0, 90, 180, -90]
    for rotation in rotations:

        # Apply rotation to a copy of the original box image
        current = rotate(rgb.copy(), rotation)

        for s in scaling:

            if s != 1.0:
                w = int(s * current.shape[1])
                h = int(s * current.shape[0])
                current_scaled = cv2.resize(current, (w, h), cv2.INTER_LANCZOS4)
            else:
                current_scaled = current.copy()

            fid, _, log_list = try_extracting_barcode_with_rotation(
                current_scaled,
                angle_range=15,
                verbose=verbose,
                log_list=log_list
            )

            if fid != "":
                return fid, log_list

    return fid, log_list


def try_extracting_barcode_with_rotation(image, angle_range=15, verbose=True, log_list: list=None):
    """ Try extracting barcode from QR code box for a list of angles in the range of `angle_range`.

    :param image:
        Input image

    :param angle_range:
        Range of angles to rotate input images in degrees.
    :type angle_range: int

    :param verbose:
        Display additional logging information to the console.
    :param log_list:
        Log list.

    :returns: fid:
        Extracted FID
    :returns: angle:
        Rotation angle that led to FID detection
    :returns: log_list:
        Appended log list.
    """

    # Prepare the list of angles to try (build a generator)
    angles = (x // 2 if x % 2 == 1 else -x // 2 for x in range(1, 2 * (angle_range + 1)))

    for angle in angles:

        # Rotate by the given angle
        if angle != 0:
            current = rotate(image.copy(), angle)
        else:
            current = image.copy()

        # Use pyzbar
        barcode_data = decode(current, SymbolTypes.TYPES.value)
        fid_pyzbar = get_fid_from_barcode_data(barcode_data)
        if fid_pyzbar != "":
            if verbose:
                msg = f"Barcode found with a rotation of {angle} degrees."
                if log_list is None:
                    print(msg)
                else:
                    log_list.append(msg)
            return fid_pyzbar, angle, log_list

        # Use pytesseract to extract the FID
        results = pytesseract.image_to_data(current, output_type=Output.DICT)
        n_boxes = len(results['text'])
        for i in range(n_boxes):
            fid_tesseract = findall(r'\d{7}', results['text'][i])
            if fid_tesseract and len(fid_tesseract) == 1:
                fid_tesseract = fid_tesseract[0]
                if verbose:
                    msg = f"Barcode found by OCR with a rotation of {angle} degrees."
                    if log_list is None:
                        print(msg)
                    else:
                        log_list.append(msg)
                return fid_tesseract, 0, log_list

    return "", None, log_list


def find_strip_box_from_barcode_data_fh(image, barcode_data, qr_code_border=30, qc=False):
    """Extract the box around the strip using the QR barcode data.

    :param image:
        Strip image.
    :param barcode_data:
        Barcode data.
    :param qr_code_border:
        Border around QR codes.
    :param qc:
        Bool, if true quality control image will be saved.

    :returns: box:
        Strip box.
    :returns: qr_code_size:
        The size of the QR codes (qr_code_width, qr_code_height).
    :returns: qc_image:
        Quality control image.
    :returns: box_rect:
        Rectangle of the QR box.

    """

    if qc:
        qc_image = image.copy()
    else:
        qc_image = None

    # Initialize box coordinates
    all_y0 = []
    all_y = []
    all_x0 = []
    all_x = []

    # Keep track of the QR code width and height
    qr_code_widths = []
    qr_code_heights = []

    # Process the barcode data
    for barcode in barcode_data:
        if barcode.symbol == "QRCODE":
            if barcode.data.upper() == "BR":
                # Append candidate coordinates for bottom-rigth corner (x and y)
                current_x = barcode.left + barcode.width + qr_code_border
                current_y = barcode.top + barcode.height + qr_code_border
                all_x.append(current_x)
                all_y.append(current_y)
                qr_code_widths.append(barcode.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x, current_y), 11, (0, 0, 255), -1)

            elif barcode.data.upper() == "BL":
                # Append candidate coordinates for bottom-left corner (x0 and y)
                current_x0 = barcode.left - qr_code_border
                current_y = barcode.top + barcode.height + qr_code_border
                all_x0.append(current_x0)
                all_y.append(current_y)
                qr_code_widths.append(barcode.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x0, current_y), 11, (0, 0, 255), -1)

            elif barcode.data.upper() == "TR":
                # Append candidate coordinates for top-right corner (x and y0)
                current_x = barcode.left + barcode.width + qr_code_border
                current_y0 = barcode.top - qr_code_border
                all_x.append(current_x)
                all_y0.append(current_y0)
                qr_code_widths.append(barcode.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x, current_y0), 11, (0, 0, 255), -1)

            elif barcode.data.upper() == "TL":
                # Append candidate coordinates for top-left corner (x0 and y0)
                current_x0 = barcode.left - qr_code_border
                current_y0 = barcode.top - qr_code_border
                all_x0.append(current_x0)
                all_y0.append(current_y0)
                qr_code_widths.append(barcode.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x0, current_y0), 11, (0, 0, 255), -1)

            elif barcode.data.upper() == "TL_P":
                # @TODO: Use this to make sure that the page is oriented correctly.
                if qc:
                    qc_image = cv2.circle(qc_image, (barcode.left - qr_code_border, barcode.top - qr_code_border), 11,
                                          (0, 0, 255), -1)

            elif barcode.data.upper() == "R_G":
                # Currently ignored
                pass

            elif barcode.data.upper() == "L_G":
                # Currently ignored
                pass

            else:
                # This is assumed to be the barcode with patient data; we can ignore it.
                pass

        else:
            print(f"Unexpected barcode with type {barcode.symbol}.")

    # Now extract the box
    x0 = -1
    if len(all_x0) > 0:
        x0 = int(np.median(all_x0))
    x = -1
    if len(all_x) > 0:
        x = int(np.median(all_x))
    y0 = -1
    if len(all_y0) > 0:
        y0 = int(np.median(all_y0))
    y = -1
    if len(all_y) > 0:
        y = int(np.median(all_y))

    if x0 != -1 and x != -1 and x > x0 and y0 != -1 and y != -1 and y > y0:
        box = image[y0:y, x0:x]
        box_rect = [y0, y, x0, x]
        if qc:
            qc_image = qc_image[y0:y, x0:x, :]
    else:
        box = None
        box_rect = None

    # Calculate the size of the QR codes
    qr_code_width = 0 if len(qr_code_widths) == 0 else int(np.median(qr_code_widths))
    qr_code_height = 0 if len(qr_code_heights) == 0 else int(np.median(qr_code_heights))

    return box, (qr_code_width, qr_code_height), qc_image, box_rect


def find_strip_box_from_barcode_data(image, barcode_data, qr_code_border=30, qr_code_spacer=40, barcode_border=80,
                                     qc=False):
    """Extract the box around the strip using the QR barcode data.

    :param image:
        Input image.
    :param barcode_data:
        Barcode data
    :param qr_code_border:
        Border around QR code on image.
    :param qr_code_spacer:
        Spacer around QR code.
    :param barcode_border:
        Border around barcode such as CODE128.
    :param qc:
        Bool, if true quality control image will be saved.

    :returns: box
        QR code box around strip
    :returns: x_barcode
        Return the (x) coordinate of the left edge of the barcode rectangle.
    :returns: qr_code_size:
        The size of the QR codes (qr_code_width, qr_code_height).
    :returns: qc_image
        Quality control image.
    """

    if qc:
        qc_image = image.copy()
    else:
        qc_image = None

    # Initialize box coordinates
    all_y0 = []
    all_y = []
    all_x0 = []
    all_x = []

    # x coordinate of the left edge of the barcode
    x_barcode = -1

    # Keep track of the QR code width and height
    qr_code_widths = []
    qr_code_heights = []

    # Process the barcode data
    for barcode in barcode_data:
        if barcode.type == "QRCODE":
            if barcode.data.decode("utf-8").upper() == "BR":
                # Append candidate coordinates for bottom-rigth corner (x and y)
                current_x = barcode.rect.left + barcode.rect.width + qr_code_border
                current_y = barcode.rect.top + barcode.rect.height + qr_code_border
                all_x.append(current_x)
                all_y.append(current_y)
                qr_code_widths.append(barcode.rect.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.rect.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x, current_y), 11, (0, 0, 255), -1)

            elif barcode.data.decode("utf-8").upper() == "BL":
                # Append candidate coordinates for bottom-left corner (x0 and y)
                current_x0 = barcode.rect.left - qr_code_border
                current_y = barcode.rect.top + barcode.rect.height + qr_code_border
                all_x0.append(current_x0)
                all_y.append(current_y)
                qr_code_widths.append(barcode.rect.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.rect.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x0, current_y), 11, (0, 0, 255), -1)

            elif barcode.data.decode("utf-8").upper() == "TR":
                # Append candidate coordinates for top-right corner (x and y0)
                current_x = barcode.rect.left + barcode.rect.width + qr_code_border
                current_y0 = barcode.rect.top - qr_code_border
                all_x.append(current_x)
                all_y0.append(current_y0)
                qr_code_widths.append(barcode.rect.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.rect.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x, current_y0), 11, (0, 0, 255), -1)

            elif barcode.data.decode("utf-8").upper() == "TL":
                # Append candidate coordinates for top-left corner (x0 and y0)
                current_x0 = barcode.rect.left - qr_code_border
                current_y0 = barcode.rect.top - qr_code_border
                all_x0.append(current_x0)
                all_y0.append(current_y0)
                qr_code_widths.append(barcode.rect.width + 2 * qr_code_border)
                qr_code_heights.append(barcode.rect.height + 2 * qr_code_border)
                if qc:
                    qc_image = cv2.circle(qc_image, (current_x0, current_y0), 11, (0, 0, 255), -1)

            elif barcode.data.decode("utf-8").upper() == "TL_P":
                # @TODO: Use this to make sure that the page is oriented correctly.
                if qc:
                    qc_image = cv2.circle(qc_image,
                                          (barcode.rect.left - qr_code_border, barcode.rect.top - qr_code_border), 11,
                                          (0, 0, 255), -1)

            else:
                print(f"Unexpected QR code with data {barcode.data.decode('utf-8')}.")

        elif barcode.type == "CODE128" or barcode.type == "CODE39":

            # Return the (x) coordinate of the left edge of the barcode rectangle.
            # We can use this to crop it away or mask it for alignment later.
            x_barcode = barcode.rect.left

            if qc:
                cv2.line(qc_image, (x_barcode, barcode.rect.top), (x_barcode, barcode.rect.top + barcode.rect.height),
                         (0, 255, 0), 2)

        else:
            print(f"Unexpected barcode with type {barcode.type}.")

    # Now extract the box
    x0 = -1
    if len(all_x0) > 0:
        x0 = int(np.median(all_x0))
    x = -1
    if len(all_x) > 0:
        x = int(np.median(all_x))
    y0 = -1
    if len(all_y0) > 0:
        y0 = int(np.median(all_y0))
    y = -1
    if len(all_y) > 0:
        y = int(np.median(all_y))

    if x0 != -1 and x != -1 and y0 != -1 and y != -1:
        box = image[y0:y, x0:x]
        if qc:
            qc_image = qc_image[y0:y, x0:x, :]
    else:
        box = None

    # Calculate the size of the QR codes
    qr_code_width = int(np.median(qr_code_widths))
    qr_code_height = int(np.median(qr_code_heights))

    # Express x_barcode (without border) as a function of x_0
    if x_barcode != -1:
        x_barcode -= (barcode_border + qr_code_spacer + x0)

    return box, x_barcode, (qr_code_width, qr_code_height), qc_image


def try_extracting_barcode_with_linear_stretch(image, lower_bound_range=(25,), upper_bound_range=(98,)):
    # NOTE:  CONTRAST is KEY. Rescaling intensity a bit helps not only in detecting the barcode but also QR
    # codes. We might try other options such as Adaptive Hist, CLAHE, etc
    # NOTE2: Orientation might play a role - however minor. Prefered orientation for the barcode detector seams
    # horizontal but vertical works too
    """ Try to extract the barcodes from the image by rescaling the intensity of the image with a linear stretch.

    :param image:
        Input image

    :param lower_bound_range:
        Lower bound range.
    :param lower_bound_range: tuple

    :param upper_bound_range:
        Upper bound range.
    :param upper_bound_range: tuple

    :returns: ""
    :returns: gray

    """

    gray = BGR2Gray(image.copy())

    for lb in lower_bound_range:
        for ub in upper_bound_range:

            # Linearly stretch the contrast
            pLb, pUb = np.percentile(gray, (lb, ub))
            stretched_gray = exposure.rescale_intensity(gray, in_range=(pLb, pUb))

            # Run the barcode detection
            barcode_data = decode(stretched_gray, SymbolTypes.TYPES.value)

            # Retrieve the FID from the barcode data
            fid_pyzbar = get_fid_from_barcode_data(barcode_data)

            if fid_pyzbar != "":
                return fid_pyzbar, stretched_gray

    return "", gray


def try_getting_fid_from_code128_barcode(barcode_data):
    """Try finding a CODE 128 barcode in barcode data that should contain the patient FID.

    :param barcode_data:
        Barcode data

    :returns: barcode:
        Decoded CODE128 barcode.
    """

    for barcode in barcode_data:
        if barcode.symbol == "CODE128":
            return barcode.data.decode("utf-8")
    return ""


def try_get_fid_from_rgb(image):
    """ Extract FID from rgb image.

    :param image:
        RGB image with FID.

    :returns: fid:
        Detected FID as string.

    """
    barcode_data = decode(image, SymbolTypes.TYPES.value)

    # return "" if no barcode or of wrong type was detected
    fid = ""
    for barcode in barcode_data:
        if barcode.type == "CODE128" or barcode.type == "CODE39":
            tmp = barcode.data.decode("utf-8")
            if tmp != "":
                fid = tmp
    return fid


def try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
        image,
        lower_bound_range=(0, 5, 15, 25, 35),
        upper_bound_range=(100, 98, 95, 92, 89),
        scaling=(1.0, )
    ):
    """ Try extracting the fid and all barcodes from the image by rescaling the intensity of the image with a
    linear stretch.

    :param image:
        Input image

    :param lower_bound_range:
        Lower bound range.
    :param lower_bound_range: tuple

    :param upper_bound_range:
        Upper bound range.
    :param upper_bound_range: tuple

    :param scaling:
        Scaling factor
    :param scaling: tuple

    :returns: barcodes:
        Barcode object
    :returns: fid:
        FID number
    :returns: manufacturer:
        Manufacturer name.
    :returns: plate:
        Plate info.
    :returns: well:
        Well info.
    :returns: user:
        Additional user data.
    :returns: best_lb:
        Best lower bound.
    :returns: best_ub:
        Best upper bound
    :returns: best_score:
        Best score.
    :returns: best_scaling_factor:
        Best scaling factor
    :returns: fid_128:
        FID 128 code.

    """

    if image.ndim == 3:
        gray = BGR2Gray(image.copy())
    else:
        gray = image.copy()

    best_score = -1
    best_scaling_factor = 1.0
    best_barcode_data = None
    best_lb = 0
    best_ub = 100
    fid = ""
    manufacturer = ""
    plate = ""
    well = ""
    user = ""
    fid_128 = ""   # Backward-compatibility with old barcode-based FID

    for scaling_factor in scaling:

        if scaling_factor != 1.0:
            w = int(scaling_factor * gray.shape[1])
            h = int(scaling_factor * gray.shape[0])
            gray_resized = cv2.resize(gray, (w, h), cv2.INTER_LANCZOS4)
        inv_scaling_factor = 1.0 / scaling_factor

        for lb in lower_bound_range:
            for ub in upper_bound_range:

                # Restart from the original contrast in the scaled image
                gray_process = gray_resized.copy()

                # Keep score
                score = 0

                # Linearly stretch the contrast
                pLb, pUb = np.percentile(gray_process, (lb, ub))
                stretched_gray = exposure.rescale_intensity(gray_process, in_range=(pLb, pUb))

                # Run the barcode detection
                barcode_data = decode(stretched_gray, SymbolTypes.TYPES.value)

                # Are all QR codes and barcodes found successfully?
                for barcode in barcode_data:
                    if barcode.type == "QRCODE":
                        if barcode.data.decode("utf-8").upper() == "BR":
                            score += 1
                        elif barcode.data.decode("utf-8").upper() == "BL":
                            score += 1
                        elif barcode.data.decode("utf-8").upper() == "TR":
                            score += 1
                        elif barcode.data.decode("utf-8").upper() == "TL":
                            score += 1
                        elif barcode.data.decode("utf-8").upper() == "TL_P":
                            score += 1
                        elif barcode.data.decode("utf-8").upper() == "L_G":
                            # L_G QR code currently ignored and does not contribute to the score.
                            pass
                        elif barcode.data.decode("utf-8").upper() == "R_G":
                            # R_G QR code currently ignored and does not contribute to the score
                            pass
                        else:
                            # Try extracting the FID

                            match = re.search(
                                # r'^(?P<fid>[A-Z]+[0-9]{6,18})-(?P<manufacturer>.+)-Plate (?P<plate>\d{1,3})-Well (?P<well>.+)-(?P<user>.+)$',
                                r'^(?P<fid>[A-Z]{0,18}[0-9]{0,18})-(?P<manufacturer>.+)-Plate (?P<plate>\d{1,3})-Well (?P<well>.+)-(?P<user>.+)$',
                                barcode.data.decode('utf-8'))
                            if match is None:

                                # Let's try a simple F1234567
                                match = re.search(
                                    r'^(?P<fid>F[0-9]{7})$',
                                    barcode.data.decode('utf-8'))

                                if match is None:

                                    # Last attempt
                                    match = re.search(
                                        r'^(?P<fid>[0-9]{5})$',
                                        barcode.data.decode('utf-8'))

                                    if match is None:
                                        print(f"Unexpected QR code with data {barcode.data.decode('utf-8')}.")

                                    else:

                                        fid = match.group('fid')
                                        manufacturer = ""
                                        plate = ""
                                        well = ""
                                        user = ""
                                        score += 1

                                else:
                                    fid = match.group('fid')
                                    manufacturer = ""
                                    plate = ""
                                    well = ""
                                    user = ""
                                    score += 1

                            else:
                                fid = match.group('fid')
                                manufacturer = match.group('manufacturer')
                                plate = match.group('plate')
                                well = match.group('well')
                                user = match.group('user')
                                score += 1

                    elif barcode.type == "CODE128" or barcode.type == 'CODE39':
                        tmp = barcode.data.decode("utf-8")
                        if fid_128 == "" and tmp != "":
                            fid_128 = tmp

                    else:
                        print(f"Unexpected barcode type {barcode.type}.")

                if score == 6:

                    # Return a list of (scaled) Barcode objects
                    barcodes = []
                    for barcode in barcode_data:
                        try:
                            obj = Barcode.from_barcode(barcode)
                            obj.scale(inv_scaling_factor)
                            barcodes.append(obj)
                        except:
                            pass

                    return barcodes, fid, manufacturer, plate, well, user, lb, ub, score, scaling_factor, fid_128

                else:
                    if score > best_score:
                        best_score = score
                        best_barcode_data = barcode_data
                        best_lb = lb
                        best_ub = ub
                        best_stretched_gray = stretched_gray
                        best_scaling_factor = scaling_factor

    # Return a list of (scaled) Barcode objects
    barcodes = []
    for barcode in best_barcode_data:
        try:
            obj = Barcode.from_barcode(barcode)
            obj.scale(1.0 / best_scaling_factor)
            barcodes.append(obj)
        except:
            pass

    return barcodes, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor, fid_128


def try_extracting_all_barcodes_with_linear_stretch(
        image,
        lower_bound_range=(0, 5, 15, 25, 35),
        upper_bound_range=(100, 98, 95, 92, 89)
):
    """ Try extracting the fid and all barcodes from the image by rescaling the intensity of the image with a
    linear stretch.

    :param image:
        Input image.

    :param lower_bound_range:
        Lower bound range.
    :param lower_bound_range: tuple

    :param upper_bound_range:
        Upper bound range.
    :param upper_bound_range: tuple

    :returns: best_barcode_data
    :returns: best_lb
    :returns: best_ub
    :returns: best_score
    """
    # NOTE:  CONTRAST is KEY. Rescaling intensity a bit helps not only in detecting the barcode but also QR
    # codes. We might try other options such as Adaptive Hist, CLAHE, etc
    # NOTE2: Orientation might play a role - however minor. Preferred orientation for the barcode detector sems
    # horizontal but vertical works too

    if image.ndim == 3:
        gray = BGR2Gray(image.copy())
    else:
        gray = image.copy()

    best_score = -1
    best_barcode_data = None
    best_lb = 0
    best_ub = 100

    for lb in lower_bound_range:
        for ub in upper_bound_range:

            # result = [TL_P_found, TL_found, TR_found, BL_found, BR_found, FID_found]
            TL_P, TL, TR, BL, BR, FID = 0, 1, 2, 3, 4, 5
            result = [False, False, False, False, False, False]

            # Linearly stretch the contrast
            pLb, pUb = np.percentile(gray, (lb, ub))
            stretched_gray = exposure.rescale_intensity(gray, in_range=(pLb, pUb))

            # Run the barcode detection
            barcode_data = decode(stretched_gray, SymbolTypes.TYPES.value)

            # Are all QR codes and barcodes found successfully?
            for barcode in barcode_data:
                if barcode.type == "QRCODE":
                    if barcode.data.decode("utf-8").upper() == "BR":
                        result[BR] = True
                    elif barcode.data.decode("utf-8").upper() == "BL":
                        result[BL] = True
                    elif barcode.data.decode("utf-8").upper() == "TR":
                        result[TR] = True
                    elif barcode.data.decode("utf-8").upper() == "TL":
                        result[TL] = True
                    elif barcode.data.decode("utf-8").upper() == "TL_P":
                        result[TL_P] = True
                    else:
                        print(f"Unexpected QR code with data {barcode.data.decode('utf-8')}.")
                elif barcode.type == "CODE128" or barcode.type == "CODE39":
                    # Let's check if the FID was read
                    if barcode.data.decode("utf-8") != "":
                        result[FID] = True
                else:
                    print(f"Unexpected barcode type {barcode.type}.")

            score = np.sum(result)
            if score == 6:
                return barcode_data, lb, ub, score
            else:
                if score > best_score:
                    best_score = score
                    best_barcode_data = barcode_data
                    best_lb = lb
                    best_ub = ub
                    best_stretched_gray = stretched_gray

    return best_barcode_data, best_lb, best_ub, best_score


def rotate_if_needed_fh(image, barcode_data, image_log, verbose=True):
    """Rotate the image if the orientation is not the expected one.

    :param image:
        Input image.
    :param barcode_data:
        Barcode data.
    :param image_log:
        Image log list.
    :param verbose:
        Bool, if true displays additional information to the console.
    :type verbose: bool

    :returns: image_was_rotated:
        Bool, true if image was rotated.
    :rtype: image_was_rotated: bool
    :returns: image:
        Rotated image.
    :rtype: tuple
    """

    positions = {
        "TL_P": None,
        "TL": None,
        "TR": None,
        "BL": None,
        "BR": None,
        "L_G": None,
        "R_G": None
    }

    # Extract the information
    for barcode in barcode_data:
        if barcode.symbol == "QRCODE":
            key = barcode.data.upper()
            if key in positions:
                try:
                    positions[key] = {"x": barcode.left, "y": barcode.top}
                except:
                    positions[key] = None

    # Use the information to understand the orientation of the image.
    # Find the four corners of the box (additional QR codes can be used
    # to make the detection more robust).
    G_TL = None
    if positions["TL"] is not None or positions["TL_P"] is not None:
        G_TL = positions["TL"] if positions["TL"] is not None else positions["TL_P"]

    G_BL = None
    if positions["BL"] is not None or positions["L_G"] is not None:
        G_BL = positions["BL"] if positions["BL"] is not None else positions["L_G"]

    G_BR = None
    if positions["BR"] is not None or positions["R_G"] is not None:
        G_BR = positions["BR"] if positions["BR"] is not None else positions["R_G"]

    G_TR = None
    if positions["TR"] is not None:
        G_TR = positions["TR"]
    else:
        if G_TL is not None and G_BL is not None and G_BR is not None:
            G_TR["x"] = G_TL["x"] + (G_BR["x"] - G_BL["x"])
            G_TR["y"] = G_TL["y"] + (G_BR["y"] - G_BL["y"])

    # Now use the relative position of the four corners to
    # determine the orientation of the image.

    if G_TL["x"] < G_TR["x"] and G_TL["y"] < G_BL["y"] and \
            G_TL["x"] < G_BR["x"] and G_TL["y"] < G_BR["y"]:
        # Case 1: the image is already oriented correctly
        image_was_rotated = False
        return image_was_rotated, image, image_log

    elif G_TR["x"] < G_BR["x"] and G_TR["y"] < G_TL["y"] and \
            G_TR["x"] < G_BL["x"] and G_TR["y"] < G_BL["y"]:
        # Case 2: the image needs to be rotated 90 degrees clockwise
        image = rotate(image, -90)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    elif G_BR["x"] < G_BL["x"] and G_BR["y"] < G_TR["y"] and \
            G_BR["x"] < G_TL["x"] and G_BR["y"] < G_TL["y"]:
        # Case 3: the image needs to be rotated 180 degrees
        image = rotate(image, 180)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    elif G_BL["x"] < G_TL["x"] and G_BL["y"] < G_BR["y"] and \
            G_BL["x"] < G_TR["x"] and G_BL["y"] < G_TR["y"]:
        # Case 4: the image needs to be rotated 90 degrees counter-clockwise
        image = rotate(image, 90)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    else:
        # We could not understand how to rotate the image.
        # Let's fall back to the old code.
        image_log.append("Fell back to old algorithm for coarse image orientation correction.")
        pass

    #
    # This is the original implementation of this function, that could
    # give wrong results if the image was rotated at intermediate angles.
    # It is only run if the new algorithm above failed for some reason.
    #

    # Try to find the LEFT X AXIS
    n = 0
    left_x_axis = 0
    if positions["TL_P"] is not None:
        left_x_axis += positions["TL_P"]["x"]
        n += 1
    if positions["TL"] is not None:
        left_x_axis += positions["TL"]["x"]
        n += 1
    if positions["BL"] is not None:
        left_x_axis += positions["BL"]["x"]
        n += 1
    if positions["L_G"] is not None:
        left_x_axis += positions["L_G"]["x"]
        n += 1
    if n > 0:
        left_x_axis = left_x_axis / n

    # Try to find the RIGHT X AXIS
    n = 0
    right_x_axis = 0
    if positions["TR"] is not None:
        right_x_axis += positions["TR"]["x"]
        n += 1
    if positions["BR"] is not None:
        right_x_axis += positions["BR"]["x"]
        n += 1
    if positions["R_G"] is not None:
        right_x_axis += positions["R_G"]["x"]
        n += 1
    if n > 0:
        right_x_axis = right_x_axis / n

    # Try to find the TOP Y AXIS
    n = 0
    top_y_axis = 0
    if positions["TL_P"] is not None:
        top_y_axis += positions["TL_P"]["y"]
        n += 1
    if positions["TL"] is not None:
        top_y_axis += positions["TL"]["y"]
        n += 1
    if positions["TR"] is not None:
        top_y_axis += positions["TR"]["y"]
        n += 1
    if n > 0:
        top_y_axis = top_y_axis / n

    # Try to find the BOTTOM Y AXIS
    n = 0
    bottom_y_axis = 0
    if positions["BL"] is not None:
        bottom_y_axis += positions["BL"]["y"]
        n += 1
    if positions["BR"] is not None:
        bottom_y_axis += positions["BR"]["y"]
        n += 1
    if positions["L_G"] is not None:
        bottom_y_axis += positions["L_G"]["y"]
        n += 1
    if positions["R_G"] is not None:
        bottom_y_axis += positions["R_G"]["y"]
        n += 1
    if n > 0:
        bottom_y_axis = bottom_y_axis / n

    # Now use the relative position of the main axes to
    # determine the orientation of the image.

    # Case 1: the image is already oriented correctly
    if left_x_axis < right_x_axis and top_y_axis < bottom_y_axis:
        # The image does not need to be rotated
        image_was_rotated = False
        return image_was_rotated, image, image_log

    # Case 2: the image is rotated 180 degrees
    if left_x_axis > right_x_axis and top_y_axis > bottom_y_axis:
        # The image needs to be rotated 180 degrees
        image = rotate(image, 180)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    # Case 3: the image is rotated 90 degrees clockwise
    if left_x_axis > right_x_axis and top_y_axis < bottom_y_axis:
        # The image needs to be rotated 90 degrees counter-clockwise
        image = rotate(image, 90)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    # Case 4: the image is rotated 90 degrees counter-clockwise (270 degrees clockwise)
    if left_x_axis < right_x_axis and top_y_axis > bottom_y_axis:
        # The image needs to be rotated 90 degrees clockwise
        image = rotate(image, -90)
        image_was_rotated = True
        return image_was_rotated, image, image_log

    # Unhandled case!
    image_log.append(
        f"Unhandled rotation case: " +
        f"top y axis = {top_y_axis}; " +
        f"bottom Y axis = {bottom_y_axis}; " +
        f"left x axis = {left_x_axis}; " +
        f"right x axis = {right_x_axis}."
    )

    return False, image, image_log


def rotate_if_needed(image, barcode_data, image_log, verbose=True):
    """Rotate the image if the orientation is not the expected one.

    :param image:
        Input image.
    :param barcode_data:
        Barcode data.
    :param image_log:
        Image log list.
    :param verbose:
        Bool, if true displays additional information to the console.
    :type verbose: bool

    :returns: image_was_rotated:
        Bool, true if image was rotated.
    :rtype: image_was_rotated: bool
    :returns: image:
        Rotated image.
    :returns: image_log:
        Log for this image
    :rtype: tuple
    """

    # Center axes of the image
    mid_y = image.shape[0] // 2
    mid_x = image.shape[1] // 2

    # The barcode TL_P should be at the top left of the page
    x0 = -1
    y0 = -1
    for barcode in barcode_data:
        if barcode.type == "QRCODE":
            if barcode.data.decode("utf-8").upper() == "TL_P":
                x0 = barcode.rect.left
                y0 = barcode.rect.top
                break

    if x0 != -1 and y0 != -1:

        if verbose:
            # print(f"Barcode 'TL_P' found at location (x={x0}, y={y0})")
            # print(f"Image size is (h={image.shape[0]}, w={image.shape[1]})")
            image_log.append(f"Barcode 'TL_P' found at location (x={x0}, y={y0})")
            image_log.append(f"Barcode 'TL_P' found at location (x={x0}, y={y0})")

        image_was_rotated = False

        # We expect image height to be > image width
        if image.shape[0] > image.shape[1]:

            # The image is vertical, let's check if the TL_P QR code is at
            # the top-left or at the bottom-right corner of the image
            if x0 < mid_x and y0 < mid_y:

                # The TL_P is in the top-left quadrant, nothing to do
                image_was_rotated = False

            elif x0 > mid_x and y0 > mid_y:

                # The TL_P is in the bottom-right quadrant, rotate 180 degrees
                image = rotate(image, 180)

                image_was_rotated = True

            else:

                raise Exception("This case must still be handled!")

        else:

            # The image is horizontal, let's check if the TL_P QR code is at
            # the top-right or at the bottom-left corner of the image
            if x0 > mid_x // 2 and y0 < mid_y:

                # The TL_P is in the top-right quadrant, rotate 90 degrees counter-clockwise
                image = rotate(image, 90)

                image_was_rotated = True

            elif x0 < mid_x and y0 > mid_y:

                # The TL_P is in the bottom-left quadrant, rotate 90 degrees clockwise
                image = rotate(image, -90)

                image_was_rotated = True

            else:

                raise Exception("This case must still be handled!")

    else:

        # The TL_P QR code could not be found, try using the others.
        # From all the detected ones, try to estimate the center of the strip box.
        all_x = []
        all_y = []
        # Process the barcode data
        for barcode in barcode_data:
            if barcode.type == "QRCODE":
                if barcode.data.decode("utf-8").upper() == "BR" or \
                        barcode.data.decode("utf-8").upper() == "BL" or \
                        barcode.data.decode("utf-8").upper() == "TR" or \
                        barcode.data.decode("utf-8").upper() == "TL":
                    all_x.append(barcode.rect.left + barcode.rect.width // 2)
                    all_y.append(barcode.rect.top + barcode.rect.height // 2)

        x_strip = np.mean([np.min(all_x), np.max(all_x)])
        y_strip = np.mean([np.min(all_y), np.max(all_y)])

        d_x = x_strip - mid_x
        d_y = y_strip - mid_y

        if image.shape[0] < image.shape[1]:
            # The image is horizontal

            # Consistency check
            if abs(d_x) <= abs(d_y):
                print("Unexpected strip position!")
                image_was_rotated = False

                return image_was_rotated, image, image_log

            if d_x < 0:
                # Rotate 90 degrees counter-clockwise
                image = rotate(image, 90)
                image_was_rotated = True
            else:
                # Rotate 90 degrees clockwise
                image = rotate(image, -90)
                image_was_rotated = True
        else:
            # The image is vertical

            # Consistency check
            if abs(d_y) <= abs(d_x):
                print("Unexpected strip position!")
                image_was_rotated = False

                return image_was_rotated, image, image_log

            if d_y < 0:
                # Rotate 180 degrees
                image = rotate(image, 180)
                image_was_rotated = True
            else:
                # The image is in the right orientation
                image_was_rotated = False

    return image_was_rotated, image, image_log


def pick_FID_from_candidates(fid_pyzbar, fid_tesseract):
    """ Selection of FID from candidates depending on if candidates contain a FID.

    :param fid_pyzbar:
        FID string determined with pyzbar.
    :param fid_tesseract:
        FID string determined with tesseract.

    :returns: fid
        FID number
    :returns: score
        Score for the candidate determination.

    """
    if fid_pyzbar == "" and fid_tesseract == "":
        return "", 0

    # Give a score to the extraction (max is 3)
    score = sum([
        fid_tesseract != "",
        fid_pyzbar != "",
        fid_tesseract == fid_pyzbar and fid_tesseract != ""])

    # Now pick the FID
    if fid_pyzbar != "":

        # If fid_pyzbar is not "", we pick it
        fid = fid_pyzbar

    else:

        # If fid_pyzbar is "", we pick fid_tesseract, which
        # could be "" -- but then the score would be 0.
        fid = fid_tesseract

    return fid, score


def mask_strip(strip_gray, x_barcode, qr_code_extents):
    """Hide the barcode on the strip image.

    :param strip_gray:
        Image of the strip (POCT).
    :param x_barcode:
        X coordinate of the barcode on the strip.
    :param qr_code_extents:
        QR code extents on the strip.

    :returns: strip_gray_masked
        Strip with QR code masked away.
    :returns: background_value
        Background value used for strip masking.

    """
    strip_gray_masked = strip_gray.copy()
    rel_x_barcode = x_barcode - qr_code_extents[1]
    background_value = np.median(strip_gray_masked[:, rel_x_barcode - 5:rel_x_barcode])
    strip_gray_masked[:, rel_x_barcode:] = background_value
    return strip_gray_masked, background_value


def extract_strip_from_box(box, qr_code_width, qr_code_height, qr_code_spacer=40, slack=0):
    """Extract the strip from the strip box.

    :param box:
        Image of the QR code box.
    :param qr_code_width:
        Width ot the QR code
    :param qr_code_height:
        Height ot the QR code
    :param qr_code_spacer:
        Horizontal and vertical distance between the internal edge of the QR codes and the beginning of the strip.
    :param slack:
        Some buffer (subtracted from qr_code_spacer) to avoid cropping into the strip

    :returns: strip
        Returns the extracted POCT strip as image matrix.
    """
    vertical_offset = qr_code_height + qr_code_spacer - slack
    horizontal_offset = qr_code_width + qr_code_spacer - slack
    if box.ndim == 3:
        strip = box[vertical_offset:-vertical_offset, horizontal_offset:-horizontal_offset, :]
    else:
        strip = box[vertical_offset:-vertical_offset, horizontal_offset:-horizontal_offset]
    return strip


def get_fid_numeric_value_fh(fid):
    """Return the numeric value of the FID (as string).

    A FID could be in the form 'F0123456'. We want to preserve
    the leading 0 after we removed the 'F'.

    :param fid:
        FID number
    :type fid: str

    :returns: fid:

    """
    if fid is None:
        return ""
    return ''.join(filter(lambda i: i.isdigit(), fid))


def get_fid_numeric_value(fid):
    """Return the numeric value of the FID.

    :param fid:
        FID number
    :type fid: str

    :returns: filtered_fid:
        FID number as numeric

    """
    if fid is None:
        return -1
    filtered_fid = ''.join(filter(lambda i: i.isdigit(), fid))
    if filtered_fid == '':
        return -1
    return int(filtered_fid)


def get_box_rotation_angle(pt1, pt2, pt3):
    """ Determine the the QR code box rotation angle

    :param pt1:
        Coordinate corner 1
    :param pt2:
        Coordinate corner 2
    :param pt3:
        Coordinate corner 3

    :returns: rot_angle
        Rotation angle in degree.
    """
    v1_angle = np.arctan2((pt2[1] - pt1[1]), (pt2[0] - pt1[0]))
    v2_angle = np.arctan2((pt3[1] - pt1[1]), (pt3[0] - pt1[0]))
    rot_angle = math.degrees(v2_angle - v1_angle)
    return rot_angle


def align_box_with_image_border_fh(barcode_data, image):
    """ Method to align QR code box with image border of the full image (old pipeline).

    :param barcode_data:
        QR code data
    :param image:
        Image

    :returns: image_rotated:
        Rotated image
    :returns: angle
        Rotation angle in degrees.

    """
    qr_centroids = {}
    for code in barcode_data:
        qr_name = code.data
        qr_centroids[qr_name.replace('b', '')] = (int(code.left + (code.width / 2)),
                                                  int(code.top + (code.height / 2)))

    # Case we have BL and BR
    if {"BL", "BR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['BL'], (qr_centroids['BR'][0], qr_centroids['BL'][1]),
                                       qr_centroids['BR'])
        image_rotated = imutils.rotate_bound(image, -angle)
    # Case we have TL and TR
    elif {"TL", "TR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TL'], (qr_centroids['TR'][0], qr_centroids['TL'][1]),
                                       qr_centroids['TR'])
        image_rotated = imutils.rotate_bound(image, -angle)
    # Case we have TL and BL
    elif {"TL", "BL"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TL'], (qr_centroids['BL'][0], qr_centroids['TL'][1]),
                                       qr_centroids['BL'])
        image_rotated = imutils.rotate_bound(image, -(90 - abs(angle)))
    # Case we have TR and BR
    elif {"TR", "BR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TR'], (qr_centroids['BR'][0], qr_centroids['TR'][1]),
                                       qr_centroids['BR'])
        image_rotated = imutils.rotate_bound(image, -(90 - abs(angle)))
    # Case no valid pair was detected
    else:
        # Return same image
        image_rotated = image
        angle = -1

    return image_rotated, angle


def align_box_with_image_border(barcode_data, image):
    """ Method to align QR code box with image border of the full image.

    :param barcode_data:
        QR code data
    :param image:
        Image

    :returns: image_rotated:
        Rotated image
    :returns: angle
        Rotation angle in degrees.
    """
    qr_centroids = {}
    for code in barcode_data:
        qr_name = code.data.decode()
        qr_centroids[qr_name.replace('b', '')] = (int(code.rect.left + (code.rect.width / 2)),
                                                  int(code.rect.top + (code.rect.height / 2)))

    # Case we have BL and BR
    if {"BL", "BR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['BL'], (qr_centroids['BR'][0], qr_centroids['BL'][1]),
                                       qr_centroids['BR'])
        image_rotated = imutils.rotate_bound(image, -angle)
    # Case we have TL and TR
    elif {"TL", "TR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TL'], (qr_centroids['TR'][0], qr_centroids['TL'][1]),
                                       qr_centroids['TR'])
        image_rotated = imutils.rotate_bound(image, -angle)
    # Case we have TL and BL
    elif {"TL", "BL"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TL'], (qr_centroids['BL'][0], qr_centroids['TL'][1]),
                                       qr_centroids['BL'])
        image_rotated = imutils.rotate_bound(image, -(90 - abs(angle)))
    # Case we have TR and BR
    elif {"TR", "BR"}.issubset(qr_centroids):
        angle = get_box_rotation_angle(qr_centroids['TR'], (qr_centroids['BR'][0], qr_centroids['TR'][1]),
                                       qr_centroids['BR'])
        image_rotated = imutils.rotate_bound(image, -(90 - abs(angle)))
    # Case no valid pair was detected
    else:
        # Return same image
        image_rotated = image
        angle = -1

    return image_rotated, angle
