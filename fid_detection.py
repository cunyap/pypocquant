import cv2
import os
import pytesseract
import numpy as np
from re import findall
import pathlib
from lib.barcode import detect
from lib.utils import get_project_root
from lib.utils import set_tesseract_exe
import pyzbar.pyzbar as pyzbar

# set tesseract executable
set_tesseract_exe()


def fid_detection():
    results = {}
    results2 = {}

    # Output dir
    project_root = get_project_root()
    print('PROJECT ROOT', project_root)
    output_dir = project_root.joinpath("test_data/output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(project_root.joinpath("test_data")):
        if filename.endswith(".JPG"):
            # Load the image
            image = cv2.imread(str(project_root.joinpath("test_data", filename)))

            # Run the detector
            barcode_img, (x, y, w, h), rotated_image, mask_image = \
                detect(image, expected_area=22000, expected_aspect_ratio=7.5,
                       blur_size=(3, 3), morph_rect=(9, 3), mm_iter=1, qc=False)

            # Common base name for the quality control images
            basename = pathlib.Path(filename).stem
            results[basename] = ""

            if barcode_img is not None:

                # Save the extracted bar code
                barcode_filename = str(pathlib.Path.joinpath(output_dir, basename + '_barcode' + '.tif'))
                cv2.imwrite(barcode_filename, barcode_img)

                text = pytesseract.image_to_string(barcode_img, lang='eng')
                print(text)

                # @todo test that for a few images offline
                # barcode = pyzbar.decode(unsharp_mask(image))
                # if barcode:
                #     print(barcode[0].data)
                #     fid2 = barcode[0].data.decode('UTF-8')
                # else:
                #     fid2 = []

                fid = findall(r'\d{7}', text)
                if fid and len(fid) == 1:
                    fid = 'F' + fid[0]
                else:
                    fid = ""

                results[basename] = fid
                # results2.update({basename: fid2})
    return results


def fid_detection_using_pyzbar():
    results = {}

    # Output dir
    project_root = get_project_root()
    output_dir = project_root.joinpath("test_data/output_pyzbar")
    output_dir.mkdir(exist_ok=True)

    for filename in os.listdir(str(project_root.joinpath("test_data"))):
        if filename.endswith(".JPG"):
            # Load the image
            image = cv2.imread(str(project_root.joinpath("test_data", filename)))

            # Run the pyzbar detector
            decoded_objects = pyzbar.decode(image)

            if len(decoded_objects) != 1:
                print(f"File {filename}: {len(decoded_objects)} objects found!")

            basename = pathlib.Path(filename).stem
            results[basename] = ""

            # Print results
            for obj in decoded_objects:
                results[basename] = obj.data.decode("utf-8")
                # print('Type : ', obj.type)
                # print('Data : ', obj.data, '\n')

                # if obj.type == "CODE39":
                #     results.update({basename: obj.data.decode("utf-8")})

                # points = obj.polygon
                #
                # # If the points do not form a quad, find convex hull
                # if len(points) > 4:
                #     hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                #     hull = list(map(tuple, np.squeeze(hull)))
                # else:
                #     hull = points
                #
                # # Number of points in the convex hull
                # n = len(hull)
                #
                # # Draw the convext hull
                # for j in range(0, n):
                #     cv2.line(image, hull[j], hull[(j + 1) % n], (255, 0, 0), 3)

            # # Save the difference image
            # cv2.imwrite("/home/aaron/Desktop/detection.png", image)

    return results


def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened
