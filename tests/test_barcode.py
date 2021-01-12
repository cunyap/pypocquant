#  /********************************************************************************
#  * Copyright © 2020-2021, ETH Zurich, D-BSSE, Andreas P. Cuny & Aaron Ponti
#  * All rights reserved. This program and the accompanying materials
#  * are made available under the terms of the GNU Public License v3.0
#  * which accompanies this distribution, and is available at
#  * http://www.gnu.org/licenses/gpl
#  *
#  * Contributors:
#  *     Andreas P. Cuny - initial API and implementation
#  *     Aaron Ponti - initial API and implementation
#  *******************************************************************************/
from unittest import TestCase, main
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh
from pypocquant.lib.io import load_and_process_image
import numpy as np


class TestIO(TestCase):

    def testTryExtractingFidAndAllBarcodesWithLinearStretch(self):
        full_filename = '../examples/images/IMG_9067.JPG'
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        barcode_data, fid, manufacturer, plate, well, user, best_lb, best_ub, best_score, best_scaling_factor, fid_128 = \
            try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )

        print(f"\nExpected result: FID: H01601828610122; Test result: {fid}")
        self.assertEquals('H01601828610122', fid)
        print(f"\nExpected result: Manufacturer: 'SUREBIOTECH'; Test result: {manufacturer}")
        self.assertEquals('SUREBIOTECH', manufacturer)
        print(f"\nExpected result: Plate: 04; Test result: {plate}")
        self.assertEquals('04', plate)
        print(f"\nExpected result: Well: A 01; Test result: {well}")
        self.assertEquals('A 01', well)
        print(f"\nExpected result: User: CUNYA; Test result: {user}")
        self.assertEquals('CUNYA', user)
        print(f"\nExpected result: Score: 6; Test result: {best_score}")
        self.assertEquals(6, best_score)
        print(f"\nExpected result: FID_128: ''; Test result: {fid_128}")
        self.assertEquals('', fid_128)


if __name__ == "__main__":
     main()
