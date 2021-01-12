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
from pypocquant.lib.utils import get_iso_date_from_image, get_exif_details, get_orientation_from_image, is_on_path, \
    get_project_root, create_quality_control_images, image_format_converter
import numpy as np
from pathlib import Path
import pytesseract
from pypocquant.lib.io import load_and_process_image


class TestUtils(TestCase):

    def testCreateQualityControlImages(self):

        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)
        images_dict = {'1': image}
        create_quality_control_images(results_folder_path=Path(file_path / 'tests'), basename='qc_test_image',
                                      map_of_images=images_dict, extension=".jpg", quality=100)

        full_filename = str(Path(file_path / 'tests' / 'qc_test_image_1.jpg'))
        image_new = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)
        self.assertEqual(image.all(), image_new.all())

    def testImageFormatConverter(self):

        file_path = Path(__file__).parent.absolute().parent
        image_format_converter(Path(file_path / 'tests' / 'test_raw'), filename='DSC_0115.NEF',
                               output_dir=Path(file_path / 'tests' / 'test_raw'), image_format='jpeg')

        full_filename = str(Path(file_path / 'tests' / 'test_raw' / 'DSC_0115.jpeg'))
        image_new = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)
        self.assertEqual((2868, 4310, 3), image_new.shape)

    def testGetProjectRoot(self):
        file_path = Path(__file__).parent.absolute().parent

        ret = get_project_root()
        self.assertEqual(file_path, ret)

    def testGetIsoDateFromImage(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        iso_date, iso_time = get_iso_date_from_image(full_filename)

        print(f"\nExpected result: Iso date: 2020-06-21; Test result: {iso_date}")
        self.assertEqual('2020-06-21', iso_date)
        print(f"\nExpected result: Iso time: 12-14-03; Test result: {iso_time}")
        self.assertEqual('12-14-03', iso_time)

    def testGetExifDetails(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))

        exp_time, f_number, focal_length_35_mm, iso_speed = get_exif_details(full_filename)

        self.assertAlmostEqual(1/10, np.array(exp_time[0].num/exp_time[0].den), places=4)
        self.assertAlmostEqual(63 / 10, np.array(f_number[0].num / f_number[0].den), places=4)
        self.assertEqual(-1, focal_length_35_mm)
        self.assertEqual(100, np.array(iso_speed[0]))

    def testGetOrientationFromImage(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))

        orientation = get_orientation_from_image(full_filename)
        self.assertEqual('Horizontal (normal)', orientation)


if __name__ == "__main__":
    main()
