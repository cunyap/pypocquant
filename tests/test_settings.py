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
from pypocquant.lib.settings import default_settings, load_settings, save_settings
from pathlib import Path
import ast


class TestSettings(TestCase):

    def testDefaultSettings(self):
        expected_settings = {'raw_auto_stretch': False, 'raw_auto_wb': False, 'strip_try_correct_orientation': False,
                             'strip_try_correct_orientation_rects': (0.52, 0.15, 0.09), 'strip_text_to_search': 'COVID',
                             'strip_text_on_right': True, 'qr_code_border': 40, 'sensor_size': (61, 249),
                             'sensor_center': (178, 667), 'subtract_background': True, 'sensor_border': (7, 7),
                             'perform_sensor_search': True, 'sensor_thresh_factor': 2, 'sensor_search_area': (71, 259),
                             'peak_expected_relative_location': (0.25, 0.53, 0.79), 'control_band_index': -1,
                             'force_fid_search': False, 'sensor_band_names': ('igm', 'igg', 'ctl'), 'verbose': True,
                             'qc': True}

        test_settings = default_settings()

        print(f"\nExpected result: dict; Test result: {type(test_settings)}")
        self.assertEqual(type(test_settings), dict)
        print(f"\nExpected result: {expected_settings}; Test result: {test_settings}")
        self.assertEqual(expected_settings, test_settings)

    def testSaveSettings(self):
        path = Path(__file__).parent.parent
        path_out = Path(path / 'tests')

        # Get default settings
        settings = default_settings()
        # Change a settings field
        settings['raw_auto_stretch'] = True
        # Save the project
        save_settings(settings, str(Path(path_out, 'test_saved_config.conf')))

        test_settings = load_settings(str(Path(path_out, 'test_saved_config.conf')))

        expected_settings = {'raw_auto_stretch': True, 'raw_auto_wb': False, 'strip_try_correct_orientation': False,
                             'strip_try_correct_orientation_rects': (0.52, 0.15, 0.09), 'strip_text_to_search': 'COVID',
                             'strip_text_on_right': True, 'qr_code_border': 40, 'sensor_size': (61, 249),
                             'sensor_center': (178, 667), 'subtract_background': True, 'sensor_border': (7, 7),
                             'perform_sensor_search': True, 'sensor_thresh_factor': 2, 'sensor_search_area': (71, 259),
                             'peak_expected_relative_location': (0.25, 0.53, 0.79), 'control_band_index': -1,
                             'force_fid_search': False, 'sensor_band_names': ('igm', 'igg', 'ctl'), 'verbose': True,
                             'qc': True}

        self.assertEqual(test_settings, expected_settings)

    def testLoadSettings(self):

        path = Path(__file__).parent.parent
        path_out = Path(path / 'tests')

        # Get default settings
        settings = default_settings()

        # Change a settings field
        settings['qc'] = False
        # Save changes
        save_settings(settings, str(Path(path_out, 'test_loading_with_saved_config.conf')))

        # Observe change back to what was saved to file
        test_settings = load_settings(str(Path(path_out, 'test_loading_with_saved_config.conf')))

        expected_settings = {'raw_auto_stretch': False, 'raw_auto_wb': False, 'strip_try_correct_orientation': False,
                             'strip_try_correct_orientation_rects': (0.52, 0.15, 0.09), 'strip_text_to_search': 'COVID',
                             'strip_text_on_right': True, 'qr_code_border': 40, 'sensor_size': (61, 249),
                             'sensor_center': (178, 667), 'subtract_background': True, 'sensor_border': (7, 7),
                             'perform_sensor_search': True, 'sensor_thresh_factor': 2, 'sensor_search_area': (71, 259),
                             'peak_expected_relative_location': (0.25, 0.53, 0.79), 'control_band_index': -1,
                             'force_fid_search': False, 'sensor_band_names': ('igm', 'igg', 'ctl'), 'verbose': True,
                             'qc': False}

        self.assertEqual(test_settings, expected_settings)


if __name__ == "__main__":
    main()