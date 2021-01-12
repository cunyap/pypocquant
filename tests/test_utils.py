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
from pypocquant.lib.utils import get_iso_date_from_image, get_exif_details
import numpy as np
from pathlib import Path

# from pypocquant.lib.io import load_and_process_image
# image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=False)


class TestUtils(TestCase):

    def testGetIsoDateFromImage(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        iso_date, iso_time = get_iso_date_from_image(full_filename)

        print(f"\nExpected result: Iso date: 2020-06-21; Test result: {iso_date}")
        self.assertEquals('2020-06-21', iso_date)
        print(f"\nExpected result: Iso time: 12-14-03; Test result: {iso_time}")
        self.assertEquals('12-14-03', iso_time)

    def testGetExifDetails(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))

        exp_time, f_number, focal_length_35_mm, iso_speed = get_exif_details(full_filename)
        print(exp_time, f_number, focal_length_35_mm, iso_speed)

        # print(f"\nExpected result: Iso time: [1/10] ; Test result: {exp_time}")
        print([1/10], np.array(exp_time[0]))
        # self.assertAlmostEquals([1/10], np.array(exp_time[0]), places=4)


if __name__ == "__main__":
    main()
