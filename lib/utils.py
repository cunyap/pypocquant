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

import os
import getpass
import rawpy
import imageio
from pathlib import Path
import platform
import pytesseract
import exifread
from datetime import datetime
import pandas as pd
import sys
import time
import cv2
import logging
# Set logging level to Error for exifread to prevent the warning
# 'Possibly corrupted field FocusMode in MakerNote IFD'
logging.getLogger('exifread').setLevel(logging.ERROR)


def create_quality_control_images(
        results_folder_path: str,
        basename: str,
        map_of_images: dict,
        extension: str = ".png",
        quality: int = 100):
    """Save the list of requested quality control images.

    :param results_folder_path:
        Full path to the folder where to save the quality control images.
    :type results_folder_path: str
    :param basename:
        Common base name for all quality control images.
    :type basename: str
    :param map_of_images:
        Dictionary of keys to be appended to the base name with the corresponding image as value.
    :type map_of_images: dict
    :param extension:
        File extension (format). Optional, default is .png.
    :type extension: str
    :param quality:
        Image compression quality. Optional, default is 100. This is only considered if format is ".jpg".
    :type quality: int
    """

    # Check the format
    extension = extension.lower()

    if extension[0] != '.':
        extension = '.' + extension

    if extension == '.jpg':
        if quality < 0 or quality > 100:
            quality = 100

    for key in map_of_images:
        if map_of_images[key] is None:
            continue
        out_filename = str(results_folder_path / Path(basename + "_" + key + extension))

        if extension == '.jpg':
            cv2.imwrite(out_filename, map_of_images[key], [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            cv2.imwrite(out_filename, map_of_images[key])


def get_project_root() -> Path:
    """Returns project root folder.

    :returns: project_root
    :rtype: Path
    """
    try:
        # Running from a pyinstaller executable
        project_root = Path(sys._MEIPASS)
    except:
        project_root = Path(__file__).parent.parent
    return project_root


def get_data_folder() -> Path:
    """Returns the value of the environment variable DATA_FOLDER or,
    if not found, the value if `get_project_root()`.

    :returns: data_folder
    :rtype: Path
    """

    data_folder = ""
    if "DATA_FOLDER" in os.environ:
        data_folder = os.environ['DATA_FOLDER']

    if data_folder == "":
        data_folder = get_project_root()
    else:
        data_folder = Path(data_folder)
    return data_folder


def image_format_converter(directory, filename, output_dir=None, image_format='tif'):
    """Converts a image in raw format (.'nef') to the specified open format. Default is '.tif'.
       rawpy API: https://letmaik.github.io/rawpy/api/rawpy.RawPy.html,
                  https://letmaik.github.io/rawpy/api/rawpy.Params.html

    :param directory:
        Image directory
    :param filename:
        Filename of the image to be converted
    :type filename: str
    :param output_dir:
        Output directory to write the converted image to.
    :param image_format:
        Format of the image such as i.e. tif
    :type image_format: str

    """

    with rawpy.imread(str(directory.joinpath(filename))) as raw:
        rgb = raw.postprocess(gamma=(1, 1), no_auto_bright=False, output_bps=16)

        basename = Path(filename).stem
        if output_dir:
            imageio.imsave(str(output_dir.joinpath('{}.{}'.format(basename, image_format))), rgb)
        else:
            imageio.imsave(str(directory.joinpath('{}.{}'.format(basename, image_format))), rgb)


def get_iso_date_from_image(image_path):
    """ Returns the date in iso-date format for the image at the given path.

    :param image_path:
       Path to an image.
    :type image_path: str

    :returns: iso_date
    :returns: iso_time
    """
    # get all Exif image metadata
    f = open(image_path, 'rb')
    tags = exifread.process_file(f)
    f.close()
    try:
        # Convert datetime string to iso date
        date = datetime.strptime(tags['EXIF DateTimeOriginal'].values,
                                 '%Y:%m:%d %H:%M:%S')
        iso_date = date.strftime('%Y-%m-%d')
        iso_time = date.strftime('%H-%M-%S')
    except Exception as e:
        try:
            date = datetime.strptime(time.ctime(os.path.getctime(image_path)), "%a %b %d %H:%M:%S %Y")
            iso_date = date.strftime('%Y-%m-%d')
            iso_time = date.strftime('%H-%M-%S')
        except Exception as e:
            iso_date = -1
            iso_time = -1

    return iso_date, iso_time


def get_exif_details(image_path):
    """ Returns the Exif metadata for the image at the given path. In particular EXIF ExposureTime, EXIF FNumber,
    EXIF FocalLengthIn35mmFilm, EXIF ISOSpeedRatings.

    :param image_path:
       Path to an image.
    :type image_path: str

    :returns: exp_time
    :returns: f_number
    :returns: focal_length_35_mm
    :returns: iso_speed
    """
    # get all Exif image metadata
    f = open(image_path, 'rb')
    tags = exifread.process_file(f)
    f.close()

    try:
        exp_time = tags['EXIF ExposureTime'].values
    except Exception as e:
        exp_time = -1

    try:
        f_number = tags['EXIF FNumber'].values
    except Exception as e:
        f_number = -1

    try:
        focal_length_35_mm = tags['EXIF FocalLengthIn35mmFilm'].values
    except Exception as e:
        focal_length_35_mm = -1

    try:
        iso_speed = tags['EXIF ISOSpeedRatings'].values
    except Exception as e:
        try:
            iso_speed = tags['MakerNote ISOSpeedRequested'].values[1]
        except Exception as e:
            iso_speed = -1

    return exp_time, f_number, focal_length_35_mm, iso_speed


def get_orientation_from_image(image_path):
    """ Returns the image orientation for the image at the given path from the EXIF metadata.

    :param image_path:
       Path to an image.
    :type image_path: str

    :returns: orientation
    """
    # get all Exif image metadata
    f = open(image_path, 'rb')
    tags = exifread.process_file(f)
    # Get the orientation
    orientation = str(tags['Image Orientation'].printable)
    f.close()
    return orientation


def is_on_path(prog):
    """ Returns true if a certain program is on the environment variable PATH.

     :param prog:
        Name of a program
     :type prog: str

    :rtype: boolean
    """
    for root_dir in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(root_dir, prog)):
            return True
    return False


def set_tesseract_exe():
    """ Sets the path to the executable of tesseract.
    """
    if is_on_path('tesseract'):
        return
    else:
        # Check default installations
        if platform.system() == "Linux":
            pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        elif platform.system() == "Darwin":
            pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        elif platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def remove_filename_duplicates(data_frame):
    """ Removes duplicates entry from a pandas data frame based on the column NAME.
     :param data_frame:
        Pandas data frame
     :type data_frame: pd.DataFrame

     :returns: data_frame
     :rtype: pd.DataFrame

     """
    df = data_frame.copy()
    dff = pd.Series([False] * df.shape[0])
    filename_no_ext = [os.path.splitext(x)[0] for x in df.FILENAME]
    filename_ext = [os.path.splitext(x)[1] for x in df.FILENAME]
    df['NAME'] = filename_no_ext
    df['NAMEEXT'] = filename_ext
    unique_names = df.NAME.unique()

    for uname in unique_names:
        sel = df[df['NAME'] == uname]

        if sel.shape[0] > 1:
            idx = sel.NAMEEXT.str.lower() == '.nef'
            if sel[idx].FID.values == sel[~idx].FID.values:
                # save index of nef image
                dff[df['NAME'] == uname] = idx
            elif sel[idx].FID.values == '':
                # save index of jpg / jpeg or any other filename ending since nef file has no fid
                dff[df['NAME'] == uname] = ~idx
            else:
                # @todo review case
                # non empty nef file but non matching with jpg. what to do? lets trust raw more and keep raw fid
                dff[df['NAME'] == uname] = idx
        else:
            # If filename is NO duplicate keep it if none empty otherwise drop
            if sel.FID.values != '':
                dff[df['NAME'] == uname] = True
            else:
                dff[df['NAME'] == uname] = False

    return data_frame[dff]
