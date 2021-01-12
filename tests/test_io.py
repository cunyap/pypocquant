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
from pypocquant.lib.io import load_and_process_image, is_raw
import numpy as np
from pathlib import Path


class TestIO(TestCase):

    def testLoadAndProcessImage(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)

        print(f"\nExpected result: numpy.ndarray; Test result: {type(image)}")
        self.assertEquals(type(image), np.ndarray)

    def testLoadAndProcessImageShape(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)

        print(f"\nExpected result: (3456, 5184, 3); Test result: {image.shape}")
        self.assertEqual(image.shape, image.shape)

    def testLoadAndProcessImageToRGB(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        px_val = [image[800, 800, 0], image[800, 800, 1], image[800, 800, 2]]
        print(f"\nExpected result RGB: (48 50 49); Test result: {px_val}")
        self.assertEqual([48, 50, 49], px_val)

    def testLoadAndProcessImageToBGR(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)
        px_val = [image[800, 800, 0], image[800, 800, 1], image[800, 800, 2]]
        print(f"\nExpected result BGR: (49 50 48); Test result: {px_val}")
        self.assertEqual([49, 50, 48], px_val)

    def testIsRAW(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        ret = is_raw(full_filename)
        print(f"\nExpected result False: Test result: {ret}")
        self.assertEqual(False, ret)


if __name__ == "__main__":
    main()
