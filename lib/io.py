import cv2
import rawpy


def load_and_process_image(full_filename: str, raw_auto_stretch: bool = False, raw_auto_wb: bool = False):
    """Load a supported (standard) image file format such as '.jpg', '.tif', '.png' and
     some RAW file formats ('.nef', '.cr2', .'arw').

     :param full_filename: str
        Full path to the file to open.
     :param raw_auto_stretch: bool
        (Only applies to RAW image file formats). Set to True to automatically stretch image instensities.
     :param raw_auto_wb: bool
        (Only applies to RAW image file formats). Set to True to automatically apply white-balancing.

     :return image Loaded (and possibly processed) image, or None it the image could not be opened.
     """

    # Make sure full_filename is a string
    full_filename = str(full_filename)

    # Make a lower case copy to check for the extension
    lower_full_filename = full_filename.lower()

    # Load  the image
    if lower_full_filename.endswith(".jpg") or lower_full_filename.endswith(".jpeg"):
        image = cv2.imread(full_filename)
    elif lower_full_filename.endswith(".nef") or \
            lower_full_filename.endswith(".cr2") or \
            lower_full_filename.endswith(".arw"):
        with rawpy.imread(full_filename) as raw:
            image = raw.postprocess(
                no_auto_bright=not raw_auto_stretch,
                use_auto_wb=raw_auto_wb,
                use_camera_wb=False,
                gamma=(1, 1),
                output_bps=8)

            # Swap channels to BGR to be opencv compatible
            image = image[:, :, [0, 1, 2]] = image[:, :, [2, 1, 0]]
    else:
        return None

    # Return the image
    return image
