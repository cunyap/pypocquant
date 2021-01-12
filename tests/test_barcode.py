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
from pypocquant.lib.barcode import try_extracting_fid_and_all_barcodes_with_linear_stretch_fh
from pypocquant.lib.io import load_and_process_image
from pathlib import Path


class TestBarcode(TestCase):

    def testTryExtractingFidAndAllBarcodesWithLinearStretch(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
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

    def testTryExtractingFidAndAllBarcodesWithLinearStretchBarcodeSampleMetadata(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        barcode_data, _, _, plate, _, _, _, _, _, _, _ = try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )
        code1 = barcode_data[0]
        data = code1.data
        symbol = code1.symbol
        print(f"\nExpected result: Sample metadata: H01601828610122-SUREBIOTECH-Plate 04-Well A 01-CUNYA; Test result:"
              f"{data}")
        self.assertEquals('H01601828610122-SUREBIOTECH-Plate 04-Well A 01-CUNYA', data)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol}")
        self.assertEquals('QRCODE', symbol)

    def testTryExtractingFidAndAllBarcodesWithLinearStretchBarcodePositionIdentification(self):
        file_path = Path(__file__).parent.absolute().parent
        full_filename = str(Path(file_path / 'examples' / 'images' / 'IMG_9067.JPG'))
        image = load_and_process_image(full_filename, raw_auto_stretch=False, raw_auto_wb=False, to_rgb=True)
        barcode_data, _, _, plate, _, _, _, _, _, _, _ = try_extracting_fid_and_all_barcodes_with_linear_stretch_fh(
                image,
                lower_bound_range=(0, 5, 15, 25, 35),
                upper_bound_range=(100, 98, 95, 92, 89),
                scaling=(0.25, 0.5)
            )
        code1 = barcode_data[1]
        data1 = code1.data
        symbol1 = code1.symbol
        print(f"\nExpected result: Sample metadata: TR; Test result:" f"{data1}")
        self.assertEquals('TR', data1)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol1}")
        self.assertEquals('QRCODE', symbol1)

        code2 = barcode_data[2]
        data2 = code2.data
        symbol2 = code2.symbol
        print(f"\nExpected result: Sample metadata: TL; Test result:" f"{data2}")
        self.assertEquals('TL', data2)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol2}")
        self.assertEquals('QRCODE', symbol2)

        code3 = barcode_data[3]
        data3 = code3.data
        symbol3 = code3.symbol
        print(f"\nExpected result: Sample metadata: BR; Test result:" f"{data3}")
        self.assertEquals('BR', data3)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol3}")
        self.assertEquals('QRCODE', symbol3)

        code4 = barcode_data[4]
        data4 = code4.data
        symbol4 = code4.symbol
        print(f"\nExpected result: Sample metadata: BL; Test result:" f"{data4}")
        self.assertEquals('BL', data4)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol4}")
        self.assertEquals('QRCODE', symbol4)

        code5 = barcode_data[5]
        data5 = code5.data
        symbol5 = code5.symbol
        print(f"\nExpected result: Sample metadata: L_G; Test result:" f"{data5}")
        self.assertEquals('L_G', data5)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol5}")
        self.assertEquals('QRCODE', symbol5)

        code6 = barcode_data[6]
        data6 = code6.data
        symbol6 = code6.symbol
        print(f"\nExpected result: Sample metadata: TL_P; Test result:" f"{data6}")
        self.assertEquals('TL_P', data6)
        print(f"\nExpected result: Code type: QRCODE; Test result: {symbol6}")
        self.assertEquals('QRCODE', symbol6)


if __name__ == "__main__":
    main()
