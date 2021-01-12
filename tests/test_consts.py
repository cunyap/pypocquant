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

import pandas as pd
from pathlib import Path
import shutil
from unittest import TestCase, main

from pyzbar.wrapper import ZBarSymbol

from pypocquant.lib.analysis import identify_bars_alt
from pypocquant.lib.consts import Issue, SymbolTypes, KnownManufacturers, BAND_COLORS
from pypocquant.lib.pipeline import run_pipeline
from pypocquant.lib.settings import load_settings


class TestConsts(TestCase):

    def test_issues(self):
        self.assertEqual(0, Issue.NONE.value)
        self.assertEqual(1, Issue.BARCODE_EXTRACTION_FAILED.value)
        self.assertEqual(2, Issue.FID_EXTRACTION_FAILED.value)
        self.assertEqual(3, Issue.STRIP_BOX_EXTRACTION_FAILED.value)
        self.assertEqual(4, Issue.STRIP_EXTRACTION_FAILED.value)
        self.assertEqual(5, Issue.POOR_STRIP_ALIGNMENT.value)
        self.assertEqual(6, Issue.SENSOR_EXTRACTION_FAILED.value)
        self.assertEqual(7, Issue.BAND_QUANTIFICATION_FAILED.value)
        self.assertEqual(8, Issue.CONTROL_BAND_MISSING.value)

    def test_symbol_types(self):
        self.assertEqual(
            SymbolTypes.TYPES.value[0], ZBarSymbol.CODE39
        )
        self.assertEqual(
            SymbolTypes.TYPES.value[1], ZBarSymbol.CODE128
        )
        self.assertEqual(
            SymbolTypes.TYPES.value[2], ZBarSymbol.QRCODE
        )

    def test_known_manufactures(self):
        expected_KnownManufacturers = (
            'AUGURIX',
            'BIOZAK',
            'CTKBIOTECH',
            'DRALBERMEXACARE',
            'LUMIRATEK',
            'NTBIO',
            'SUREBIOTECH',
            'TAMIRNA'
        )
        self.assertEqual(
            expected_KnownManufacturers,
            KnownManufacturers)

    def test_band_colors(self):
        self.assertEqual(10, len(BAND_COLORS))


if __name__ == "__main__":
    main()
