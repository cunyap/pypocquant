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

from enum import Enum
import matplotlib.colors as mcolors
from pyzbar.pyzbar import ZBarSymbol


class Issue(Enum):
    NONE = 0
    BARCODE_EXTRACTION_FAILED = 1
    FID_EXTRACTION_FAILED = 2
    STRIP_BOX_EXTRACTION_FAILED = 3
    STRIP_EXTRACTION_FAILED = 4
    POOR_STRIP_ALIGNMENT = 5
    SENSOR_EXTRACTION_FAILED = 6
    BAND_QUANTIFICATION_FAILED = 7
    CONTROL_BAND_MISSING = 8


class SymbolTypes(Enum):
    TYPES = [ZBarSymbol.CODE39, ZBarSymbol.CODE128, ZBarSymbol.QRCODE]


# List of known strip manufacturers
KnownManufacturers = (
    'AUGURIX',
    'BIOZAK',
    'CTKBIOTECH',
    'DRALBERMEXACARE',
    'LUMIRATEK',
    'NTBIO',
    'SUREBIOTECH',
    'TAMIRNA'
)

# Standard plot colors for sensor bands
BAND_COLORS = [
    mcolors.TABLEAU_COLORS['tab:blue'],
    mcolors.TABLEAU_COLORS['tab:orange'],
    mcolors.TABLEAU_COLORS['tab:green'],
    mcolors.TABLEAU_COLORS['tab:purple'],
    mcolors.TABLEAU_COLORS['tab:brown'],
    mcolors.TABLEAU_COLORS['tab:olive'],
    mcolors.TABLEAU_COLORS['tab:cyan'],
    mcolors.TABLEAU_COLORS['tab:red'],
    mcolors.TABLEAU_COLORS['tab:pink'],
    mcolors.TABLEAU_COLORS['tab:gray']
]


