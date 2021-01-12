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
#  *********************************************************************************
from unittest import TestCase, main
from pypocquant.lib.tools import extract_strip
from pypocquant.lib.io import load_and_process_image
import numpy as np
from pathlib import Path


class TestTools(TestCase):

    def testExtractStrip(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        strip_for_analysis, error_msg, left_rect, right_rect = extract_strip(image, qr_code_border=40,
                                                                             strip_try_correct_orientation=False,
                              strip_try_correct_orientation_rects=(0.52, 0.15, 0.09), stretch_for_hough=False,
                              strip_text_to_search="", strip_text_on_right=True)

        print(f"\nExpected result: numpy.ndarray; Test result: {type(strip_for_analysis)}")
        self.assertEquals(type(strip_for_analysis), np.ndarray)
        print(f"\nExpected result: Strip shape: (300, 1056, 3); Test result: {strip_for_analysis.shape}")
        self.assertEquals((300, 1056, 3),  strip_for_analysis.shape)

    def testExtractStripTryCorrectOrientation(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        strip_for_analysis, error_msg, left_rect, right_rect = extract_strip(image, qr_code_border=40,
                                                                             strip_try_correct_orientation=True,
                              strip_try_correct_orientation_rects=(0.52, 0.15, 0.09), stretch_for_hough=False,
                              strip_text_to_search="", strip_text_on_right=True)

        print(f"\nExpected result: numpy.ndarray; Test result: {type(strip_for_analysis)}")
        self.assertEquals(type(strip_for_analysis), np.ndarray)
        print(f"\nExpected result: Strip shape: (300, 1056, 3); Test result: {strip_for_analysis.shape}")
        self.assertEquals((300, 1056, 3),  strip_for_analysis.shape)
        print(f"\nExpected result: Left rect: [95, 72, 275, 156]; Test result: {left_rect}")
        self.assertEquals([95, 72, 275, 156], left_rect)
        print(f"\nExpected result: Right rect: [686, 72, 275, 156]; Test result: {right_rect}")
        self.assertEquals([686, 72, 275, 156], right_rect)


if __name__ == "__main__":
    main()
