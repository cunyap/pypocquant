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

from pypocquant.lib.analysis import identify_bars_alt
from pypocquant.lib.pipeline import run_pipeline
from pypocquant.lib.settings import load_settings


class TestIO(TestCase):

    def test_bands_assignments(self):

        # Test 1: igg only
        peak_positions = [62]
        expected_bars = {'igg': 0}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 2: igm only
        peak_positions = [125]
        expected_bars = {'igm': 0}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 3: ctl only
        peak_positions = [190]
        expected_bars = {'ctl': 0}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 3: all assigned
        peak_positions = [62, 125, 190]
        expected_bars = {'igg': 0, 'igm': 1, 'ctl': 2}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 4: only two bands, assigned
        peak_positions = [62, 190]
        expected_bars = {'igg': 0, 'ctl': 1}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 5: three bands, out of order, assigned
        # This does not happen in practice, but tests the
        # linear assignment
        peak_positions = [190, 125, 62]
        expected_bars = {'igg': 2, 'igm': 1, 'ctl': 0}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 6: bar 2 distance from the expected position is out of tolerance
        peak_positions = [62, 110, 195]
        expected_bars = {'igg': 0, 'ctl': 2}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.05
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 7: both bar 2 and 3 are close to ctl, but bar 2 is closer
        # and should be the one assigned to ctl
        peak_positions = [60, 190, 195]
        expected_bars = {'igg': 0, 'ctl': 1}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 8: both bar 2 and 3 are close to ctl, but bar 3 is closer
        # and should be the one assigned to ctl
        peak_positions = [60, 180, 190]
        expected_bars = {'igg': 0, 'ctl': 2}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 9: all bars are above distance tolerance
        peak_positions = [30, 90, 160]
        expected_bars = {}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

        # Test 10: all bars have large deviations (still within tolerance)
        peak_positions = [80, 100, 170]
        expected_bars = {"igg": 0, "igm": 1, "ctl": 2}

        bars = identify_bars_alt(
            peak_positions,
            profile_length=250,
            sensor_band_names=("igg", "igm", "ctl"),
            expected_relative_peak_positions=(0.25, 0.5, 0.75),
            tolerance=0.1
        )

        print(f"\nExpected result: {expected_bars}; Test result: {bars}")
        self.assertEqual(expected_bars, bars)

    def test_full_pipeline(self):
        """Test full pipeline on a test image."""

        # Test pipeline path
        input_folder_path = Path(__file__).parent / "test_pipeline"

        # Settings file
        settings_file = input_folder_path / "test_pipeline_settings.conf"

        # Load settings file
        settings = load_settings(settings_file)

        # If the "pipeline" subfolder in input_folder exists,
        # delete it recursively
        results_folder_path = input_folder_path / "pipeline"
        if results_folder_path.is_dir():
            shutil.rmtree(results_folder_path)
        results_folder_path.mkdir(parents=False, exist_ok=False)

        # Start pipeline
        run_pipeline(
            input_folder_path,
            results_folder_path,
            **settings,
            max_workers=1
        )

        # Now load the results
        results = pd.read_csv(
            str(results_folder_path / "quantification_data.csv")
        )

        # Expected results
        expected_fid = 'F5922985'
        expected_iso_date = '2020-06-21'
        expected_manufacturer = 'SUREBIOTECH'
        expected_plate = 6
        expected_well = 'F 07'
        expected_issue = 0
        expected_igm = 1
        expected_igm_abs = 761.070957692734
        expected_igm_ratio = 0.720671272145915
        expected_igg = 1
        expected_igg_abs = 1748.84250473075
        expected_igg_ratio = 1.6560092589632
        expected_ctl = 1
        expected_ctl_abs = 1056.05840985797
        expected_ctl_ratio = 1

        # Compare results
        self.assertEqual(expected_fid, results['fid'].item())
        self.assertEqual(expected_iso_date, results['iso_date'].item())
        self.assertEqual(expected_manufacturer, results['manufacturer'].item())
        self.assertEqual(expected_plate, results['plate'].item())
        self.assertEqual(expected_well, results['well'].item())
        self.assertEqual(expected_issue, results['issue'].item())
        self.assertEqual(expected_igm, results['igm'].item())
        self.assertAlmostEqual(expected_igm_abs, results['igm_abs'].item(), places=6)
        self.assertAlmostEqual(expected_igm_ratio, results['igm_ratio'].item(), places=6)
        self.assertEqual(expected_igg, results['igm'].item())
        self.assertAlmostEqual(expected_igg_abs, results['igg_abs'].item(), places=6)
        self.assertAlmostEqual(expected_igg_ratio, results['igg_ratio'].item(), places=6)
        self.assertEqual(expected_ctl, results['ctl'].item())
        self.assertAlmostEqual(expected_ctl_abs, results['ctl_abs'].item(), places=6)
        self.assertAlmostEqual(expected_ctl_ratio, results['ctl_ratio'].item(), places=6)

        # Delete the "pipeline" subfolder
        if results_folder_path.is_dir():
            shutil.rmtree(results_folder_path)


if __name__ == "__main__":
    main()
