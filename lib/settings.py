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

import ast


def default_settings():
    """Return a dictionary containing the default settings."""
    return {
        "raw_auto_stretch": False,
        "raw_auto_wb": False,
        "strip_try_correct_orientation": False,
        "strip_try_correct_orientation_rects": (0.52, 0.15, 0.09),
        "strip_text_to_search": "COVID",
        "strip_text_on_right": True,
        "qr_code_border": 40,
        "sensor_size": (61, 249),
        "sensor_center": (178, 667),
        "subtract_background": True,
        "sensor_border": (7, 7),
        "perform_sensor_search": True,
        "sensor_thresh_factor": 2,
        "sensor_search_area": (71, 259),
        "peak_expected_relative_location": (0.25, 0.53, 0.79),
        "control_band_index": -1,
        "force_fid_search": False,
        "sensor_band_names": ('igm', 'igg', 'ctl'),
        "verbose": True,
        "qc": True
    }


def load_settings(filename):
    """Loads settings from file and returns them in a dictionary.

    :param filename:
        Name of the settings file.
    :type filename: str

    :returns: settings_dictionary
    :rtype: dict
    """
    settings_dictionary = {}
    with open(filename, "r") as f:
        lines = f.readlines()
    for line in lines:
        key, value = line.split("=")
        settings_dictionary[key.strip()] = ast.literal_eval(value.strip())
    return settings_dictionary


def save_settings(settings_dictionary, filename):
    """Save settings from a dictionary to file.

    :param settings_dictionary:
        Settings dictionary
    :param filename:
        Filename of the settings file to be saved.
    :type filename: str
    """
    with open(filename, "w+") as f:
        for key in settings_dictionary:
            if type(settings_dictionary[key]) == str:
                f.write(f"{key}='{settings_dictionary[key]}'\n")
            else:
                f.write(f"{key}={settings_dictionary[key]}\n")


def load_list_file(filename):
    """Loads list from file and returns them as list.

    :param filename:
        Filename of the settings file to be loaded.
    :type filename: str

    :returns: file_content_list
    :rtype: list
    """
    file_content_list = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            line_text = line.rstrip().replace('\n', '').replace(';', ',').replace('\t', ',').replace(' ', '')
            for el in line_text.split(','):
                if el.strip():
                    file_content_list.append(el.strip())
    return file_content_list
