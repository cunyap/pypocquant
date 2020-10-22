import ast


def default_settings():
    """Return a dictionary containing the default settings."""
    return {
        "raw_auto_stretch": False,
        "raw_auto_wb": False,
        "strip_try_correct_orientation": True,
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
        "force_fid_search": False,
        "sensor_band_names": ('igm', 'igg', 'ctl'),
        "verbose": True,
        "qc": True
    }


def load_settings(filename):
    """Loads settings from file and returns them in a dictionary."""
    settings_dictionary = {}
    with open(filename, "r") as f:
        lines = f.readlines()
    for line in lines:
        key, value = line.split("=")
        settings_dictionary[key.strip()] = ast.literal_eval(value.strip())
    return settings_dictionary


def save_settings(settings_dictionary, filename):
    """Save settings from a dictionary to file."""
    with open(filename, "w+") as f:
        for key in settings_dictionary:
            if type(settings_dictionary[key]) == str:
                f.write(f"{key}='{settings_dictionary[key]}'\n")
            else:
                f.write(f"{key}={settings_dictionary[key]}\n")
