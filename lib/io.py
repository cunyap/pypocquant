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

from pathlib import Path

import cv2
import rawpy
import numpy as np


def load_and_process_image(
        full_filename: str,
        raw_auto_stretch: bool = False,
        raw_auto_wb: bool = False,
        to_rgb: bool = False):
    """Load a supported (standard) image file format such as '.jpg', '.tif', '.png' and
     some RAW file formats ('.nef', '.cr2', .'arw').

     :param full_filename:
        Full path to the file to open.
     :type full_filename: str

     :param raw_auto_stretch:
        (Only applies to RAW image file formats). Set to True to automatically stretch image intensities (default = False).
     :type raw_auto_stretch: bool

     :param raw_auto_wb:
        (Only applies to RAW image file formats). Set to True to automatically apply white-balancing (default = False).
     :type raw_auto_wb: bool

     :param to_rgb:
        Set to True to convert from BGR (openCV standard, used in processing) to RGB (for display, default = False).
     :type to_rgb: bool

     :returns: image: Loaded (and possibly processed) image, or None it the image could not be opened.
     :rtype: cv2.Image
     """

    # Make sure full_filename is a string
    full_filename = str(full_filename)

    # Make a lower case copy to check for the extension
    lower_full_filename = full_filename.lower()

    # Load  the image
    if lower_full_filename.endswith(".jpg") or lower_full_filename.endswith(".jpeg"):

        # openCV opens the image in BGR mode
        image = cv2.imread(full_filename)

        if image is None:

            # openCV's imread() cannot open files with non-ASCII characters in the path.
            # Let's try a workaround.
            image = cv2.imdecode(np.fromfile(full_filename, np.uint8), cv2.IMREAD_UNCHANGED)

            # Did it work this time?
            if image is None:
                return None

        # Convert to RGB?
        if to_rgb:
            # Swap to RGB as requested
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    elif lower_full_filename.endswith(".nef") or \
            lower_full_filename.endswith(".cr2") or \
            lower_full_filename.endswith(".arw"):
        with rawpy.imread(full_filename) as raw:

            # rawpy opens the image in RGB mode
            image = raw.postprocess(
                no_auto_bright=not raw_auto_stretch,
                use_auto_wb=raw_auto_wb,
                use_camera_wb=False,
                gamma=(1, 1),
                output_bps=8)

            if image is None:
                return None

            if to_rgb:
                # The image is already in RGB, nothing to do
                pass
            else:
                # Swap channels to BGR to be opencv compatible
                image = image[:, :, [0, 1, 2]] = image[:, :, [2, 1, 0]]

    else:
        return None

    # Return the image
    return image


def is_raw(filename: str) -> bool:
    """Check whether the image is one of the supported RAW images
     (by checking the file extension.

     :param filename: Full file name.
     :type filename: str

     :returns bool: True if the image is RAW, false otherwise.
     :rtype: bool
     """

    # Check the extension
    lower_filename = filename.lower()
    if lower_filename.endswith(".nef") or \
            lower_filename.endswith(".cr2") or \
            lower_filename.endswith(".arw"):
        return True

    return False
