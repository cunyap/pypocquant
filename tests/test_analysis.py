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
from unittest import TestCase, main

from pypocquant.lib.analysis import identify_bars_alt
from pypocquant.lib.io import load_and_process_image
import numpy as np


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
        peak_positions = [80, 100, 160]
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


if __name__ == "__main__":
    main()
