from enum import Enum
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
