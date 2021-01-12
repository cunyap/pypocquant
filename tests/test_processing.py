from unittest import TestCase, main
from pypocquant.lib.processing import \
    phase_only_correlation, \
    find_position_in_image_using_phase_corr, \
    crop_image_around_position_to_size, \
    find_position_in_image_using_norm_xcorr, \
    correlation_coefficient, \
    create_rgb_image
from pypocquant.lib.utils import get_project_root
import numpy as np
import cv2
from PIL import Image


class TestProcessing(TestCase):

    def testSimplePhaseCorr(self):

        a = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)
        b = a + 1

        result = phase_only_correlation(a, b)

        expected_result = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64)

        approx_equal = np.all(np.abs(result - expected_result) < 1e-7)
        self.assertTrue(approx_equal)

    def testFindSinglePositionInImage(self):

        a = np.zeros((3, 3))
        b = np.zeros((9, 9))

        a[1, 1] = 1
        b[7, 6] = 1

        y, x = find_position_in_image_using_phase_corr(a, b)

        expected_y, expected_x = 7, 6

        self.assertTrue(y == expected_y)
        self.assertTrue(x == expected_x)

    def testFindExtendedPositionInImage(self):

        a = np.zeros((7, 7))
        b = np.zeros((15, 15))

        a[2:5, 2:5] = 1
        b[11:14, 10:13] = 1

        y, x = find_position_in_image_using_phase_corr(a, b)

        expected_y, expected_x = 12, 11

        self.assertTrue(y == expected_y)
        self.assertTrue(x == expected_x)

    def testFindExtendedPositionInImageEvenDims(self):

        a = np.zeros((6, 6))
        b = np.zeros((14, 14))

        a[2:5, 2:5] = 1
        b[11:14, 10:13] = 1

        y, x = find_position_in_image_using_phase_corr(a, b)

        expected_y, expected_x = 12, 11

        self.assertTrue(y == expected_y)
        self.assertTrue(x == expected_x)

    def testFindExtendedPositionInImageUsingNormCrossCorr(self):

        a = np.zeros((6, 6))
        b = np.zeros((14, 14))

        a[2:5, 2:5] = 1
        b[11:14, 11:14] = 1

        # Since the normalized cross-correlation is completely flat
        # over the overlapping areas, the position returned is actually
        # at the top-left corner of the a object in b, instead of the center.
        # @TODO: Check how it will behave with real image data.
        y, x = find_position_in_image_using_norm_xcorr(a, b)

        expected_y, expected_x = 11, 11

        self.assertTrue(y == expected_y)
        self.assertTrue(x == expected_x)

    def testFindTemplatesInTargetImage(self):

        # Get project root path
        root_path = get_project_root()

        # Load and prepare the templates
        template_dir_path = root_path.joinpath("pyPOCQuant", "templates")
        templates = {
            "test_strip_template_left_0_degrees.png": None,
            "test_strip_template_left_pos_2_degrees.png": None,
            "test_strip_template_right_neg_3_degrees.png": None,
            "test_strip_template_left_neg_1_degrees.png": None,
            "test_strip_template_left_pos_3_degrees.png": None,
            "test_strip_template_right_pos_1_degrees.png": None,
            "test_strip_template_left_neg_2_degrees.png": None,
            "test_strip_template_right_0_degrees.png": None,
            "test_strip_template_right_pos_2_degrees.png": None,
            "test_strip_template_left_neg_3_degrees.png": None,
            "test_strip_template_right_neg_1_degrees.png": None,
            "test_strip_template_right_pos_3_degrees.png": None,
            "test_strip_template_left_pos_1_degrees.png": None,
            "test_strip_template_right_neg_2_degrees.png": None
        }

        for template_name in templates:
            template_path = template_dir_path.joinpath(template_name)
            template = cv2.imread(str(template_path))
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            templates[template_name] = template
            print(f"Loaded template {template_name} with size {template.shape}")

        # Load the target image
        target_folder_path = root_path.joinpath("pyPOCQuant", "tests", "test_correlation")
        target_path = root_path.joinpath(target_folder_path, "DSC_9790.JPG")
        target = cv2.imread(str(target_path))

        # Make the image B/W
        gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).copy()

        # Extract a subregion in the center where the test strip
        # can be safely search for
        x0, x = 1200, 3000
        y0, y = 1230, 2200
        gray = gray[y0:y, x0:x]

        # Keep track of the best result (i.e. highest correlation coefficient)
        max_cc = -2
        max_cc_template = None
        max_cropped_gray = None

        # Find template in image with phase-only correlation
        for key in templates:

            # Use phase-only correlation to find the template
            y, x = find_position_in_image_using_phase_corr(templates[key], gray)
            print(f"{key}: found at position (y={y}, x={x})")

            # Extract the area from the target image
            cropped_gray = crop_image_around_position_to_size(gray, y, x, templates[key].shape)

            # Calculate the correlation coefficient
            cc = correlation_coefficient(templates[key], cropped_gray)
            if cc > max_cc:
                max_cc = cc
                max_cc_template = key
                max_cropped_gray = cropped_gray

        # Inform
        print(f"Best result found for template {max_cc_template} with correlation coefficient {max_cc}.")

        # Build an RGB quality control
        rgb = create_rgb_image(templates[max_cc_template], max_cropped_gray)

        # Save the image
        rgb_image_path = target_folder_path.joinpath("control_RGB.jpg")
        rgb = Image.fromarray(rgb)
        rgb.save(rgb_image_path)

        self.assertTrue(True)


if __name__ == "__main__":
    main()
