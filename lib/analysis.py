import re
import warnings
from pathlib import Path

from copy import deepcopy
from typing import Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndimage
from pytesseract import Output
from pytesseract import pytesseract
from scipy.ndimage import label
from scipy.ndimage.filters import gaussian_filter1d
from scipy.ndimage.morphology import binary_fill_holes, binary_opening
from scipy.optimize import linear_sum_assignment
from scipy.signal import find_peaks
from scipy.spatial.distance import cdist
from skimage import filters, exposure
from sklearn.linear_model import HuberRegressor

from pypocquant.lib import consts
from pypocquant.lib.barcode import rotate
from pypocquant.lib.processing import BGR2Gray
from pypocquant.lib.consts import BAND_COLORS


def get_min_dist(xy1, xy2):
    dists = cdist(xy2, xy1, metric='euclidean')
    return np.min(dists), np.argmin(dists)


def identify_bars_alt(
        peak_positions: list,
        profile_length: int,
        sensor_band_names: Tuple[str, ...],
        expected_relative_peak_positions: Tuple[float, ...],
        control_band_index: int,
        tolerance: float = 0.1
):
    """Assign the peaks to the corresponding bar based on the known relative position in the sensor.

    :param peak_positions: list
        List of absolute peak positions in pixels.

    :param profile_length:
        Length of the profile in pixels.

    :param sensor_band_names: Tuple[str, ...]
        Tuple of sensor band names.

    :param expected_relative_peak_positions: Tuple[float, ...}
        Tuple of expected relative (0.0 -> 1.0) peak positions.

    :param control_band_index:
        Index of the control band in tuple of sensor band names and expected relative positions.

    :param tolerance:
        Distance tolerance between pean position and expected position for assignment.

    :return dictionary of band assignments: {bar_name: index}
    """

    # Instantiate results dictionary
    bars = {}

    # Calculate relative (expected) peak positions
    relative_peak_positions = (
            np.array(peak_positions) / profile_length
    ).reshape(-1, 1)
    expected_relative_peak_positions = np.array(
        expected_relative_peak_positions
    ).reshape(-1, 1)

    # Calculate all distances between expected and
    # candidate peak positions
    dists = cdist(
        expected_relative_peak_positions,
        relative_peak_positions,
        metric='euclidean'
    )

    # Calculate linear assignment
    row, col = linear_sum_assignment(dists)

    # For every row (expected relative peak position), pick
    # the corresponding column (the candidate band closest in
    # a *global* assignment way)
    for r, c in zip(row, col):
        # If the distance is larger than the tolerance, ignore it;
        # otherwise, store it
        if dists[r, c] <= tolerance:
            bars[sensor_band_names[r]] = c

    return bars


def invert_image(image, bit_depth=8):
    image_inv = (2 ** bit_depth - image)
    return image_inv.astype('uint8')


def local_minima(array, min_distance=1):
    """Find all local minima of the array, separated by at least min_distance."""
    max_points = array == ndimage.maximum_filter(
        array, 1 + 2 * min_distance, mode='constant', cval=array.max() + 1)
    return np.array([indices[max_points] for indices in np.indices(array.shape)])


def _find_lower_background(profile: np.ndarray, peak_index: int, lowest_bound: int, max_skip: int = 1):
    """This method is used by find_peak_bounds() and is not meant to be used as
    a standalone method."""

    # Peak intensity
    peak_intensity = profile[peak_index]

    current_lower_background = peak_intensity
    n = 0
    current_lower_bound = peak_index - 1
    for index in range(peak_index - 1, lowest_bound, -1):
        if profile[index] <= current_lower_background:
            current_lower_background = profile[index]
            current_lower_bound = index
        else:
            # If any of the next indices (up to a max of max_skip) is lower than
            # 'current_background', we still allow them to be picked; to avoid
            # picking a noisy bump instead.
            if n > max_skip:
                break
            n += 1
    d_lower = peak_index - current_lower_bound
    return current_lower_bound, current_lower_background, d_lower


def _find_upper_background(profile: np.ndarray, peak_index: int, highest_bound: int, max_skip: int = 1):
    """This method is used by find_peak_bounds() and is not meant to be used as
    a standalone method."""

    # Peak intensity
    peak_intensity = profile[peak_index]

    # On the other side
    current_upper_background = peak_intensity
    n = 0
    current_upper_bound = peak_index + 1
    for index in range(peak_index + 1, highest_bound):
        if profile[index] <= current_upper_background:
            current_upper_background = profile[index]
            current_upper_bound = index
        else:
            # If any of the next indices (up to a max of max_skip) is lower than
            # 'current_background', we still allow them to be picked; to avoid
            # picking a noisy bump instead.
            if n > max_skip:
                break
            n += 1
    d_upper = current_upper_bound - peak_index
    return current_upper_bound, current_upper_background, d_upper


def find_peak_bounds(profile, border, peak_index, image_log, verbose=False):
    """Find the lower and upper bounds of current band."""

    profile = np.asarray(profile)

    # Do not go into the border!
    lowest_bound = border
    highest_bound = len(profile) - border

    # Peak intensity
    peak_intensity = profile[peak_index]

    # Not move away from the peak in both directions until the intensity in under 'relative_intensity'

    # First find the lower bound
    current_lower_bound, current_lower_background, d_lower = _find_lower_background(
        profile,
        peak_index,
        lowest_bound,
        max_skip=1
    )

    # Then find the upper bound
    current_upper_bound, current_upper_background, d_upper = _find_upper_background(
        profile,
        peak_index,
        highest_bound,
        max_skip=1
    )

    # Now do some quality check on the extracted bounds
    background = current_lower_background if current_lower_background < current_upper_background else current_upper_background
    i_lower = (current_lower_background - background) / (peak_intensity - background)
    i_upper = (current_upper_background - background) / (peak_intensity - background)

    # Make sure that both i_lower and i_upper are reasonably close to 0; but put
    # a reasonable cap to the number of attempts to bring it down.
    # Start with the lower bound.
    max_skip_lower = 2
    while i_lower > 0.25 and max_skip_lower <= 5:
        # Rerun the search for the lower bound
        current_lower_bound, current_lower_background, d_lower = _find_lower_background(
            profile,
            peak_index,
            lowest_bound,
            max_skip=max_skip_lower
        )

        # Update the current bounds
        background = current_lower_background if current_lower_background < current_upper_background else current_upper_background
        i_lower = (current_lower_background - background) / (peak_intensity - background)

        # Update max_skip_lower
        max_skip_lower += 1

    # Make sure that both i_lower and i_upper are reasonably close to 0; but put
    # a reasonable cap to the number of attempts to bring it down.
    # Continue with the upper bound.
    max_skip_upper = 2
    while i_upper > 0.25 and max_skip_upper <= 5:
        # Rerun the search for the upper bound
        current_upper_bound, current_upper_background, d_upper = _find_upper_background(
            profile,
            peak_index,
            highest_bound,
            max_skip=max_skip_upper
        )

        # Update the current bounds
        background = current_lower_background if current_lower_background < current_upper_background else current_upper_background
        i_upper = (current_upper_background - background) / (peak_intensity - background)

        # Update max_skip_upper
        max_skip_upper += 1

    if verbose:
        band_skewness = d_upper / d_lower
        image_log.append(f"Peak {peak_index} has lower bound {current_lower_bound} (d = {d_lower}) "
                         f"with relative intensity {i_lower:.2f} and "
                         f"upper bound {current_upper_bound} (d = {d_upper}) with relative intensity {i_upper:.2f}. "
                         f"Band width is {current_upper_bound - current_lower_bound + 1}. Band skewness is {band_skewness:.2f}")

    return current_lower_bound, current_upper_bound, image_log


def fit_and_subtract_background(profile, border, subtract_offset=10):
    """Use a robust linear estimator to estimate the background of the profile and subtract it."""

    # Prepare data
    y = profile[border:-border].squeeze()
    x = np.arange(y.size).reshape(-1, 1)

    # Instantiate the model
    model = HuberRegressor(fit_intercept=True)

    # Fit
    model.fit(x, y)

    # Predict
    y_hat = model.predict(x)

    # Subtract the background
    subtr = y - (y_hat - subtract_offset)

    # Insert in the original profile
    profile[border:-border] = subtr

    # Also return the predicted background and the predicted background with offset
    background = 0 * profile.copy()
    background[border:-border] = y_hat

    background_offset = 0 * profile.copy()
    background_offset[border:-border] = y_hat - subtract_offset

    return profile, background, background_offset


def estimate_threshold_for_significant_peaks(
        profile: np.ndarray,
        border_x: int,
        thresh_factor: float):
    # First find all local minima (add back the border offset)
    loc_min_indices = border_x + local_minima(profile[border_x: len(profile) - border_x])

    # Calculate a statistical threshold for peaks using the local min intensities.
    min_values = profile[loc_min_indices]
    md = np.median(min_values)
    ma = np.median(np.abs(min_values - md))
    peak_threshold = md + thresh_factor * ma

    # Now remove the outliers from the local minima
    new_min_values = min_values[min_values < peak_threshold]

    # Calculate the new threshold
    md = np.median(new_min_values)
    ma = np.median(np.abs(new_min_values - md))
    peak_threshold = md + thresh_factor * ma
    lowest_background_threshold = md - thresh_factor * ma

    # Keep only the local minima that passed both tests
    loc_min_indices = loc_min_indices[profile[loc_min_indices] < peak_threshold]
    if np.any(profile[loc_min_indices] >= peak_threshold):
        raise Exception("Logical flaw in estimate_threshold_for_significant_peaks().")

    return peak_threshold, loc_min_indices, md, lowest_background_threshold


def analyze_measurement_window(
        window: np.ndarray,
        border_x: int = 10,
        border_y: int = 5,
        thresh_factor: float = 3.0,
        peak_width: int = 7,
        sensor_band_names: Tuple[str, ...] = ('igm', 'igg', 'ctl'),
        peak_expected_relative_location: Tuple[float, ...] = (0.27, 0.55, 0.79),
        control_band_index: int = -1,
        subtract_background: bool = False,
        qc: bool = False,
        verbose: bool = False,
        out_qc_folder: Union[str, Path] = '',
        basename: str = '',
        image_log: list = []):
    """Quantify the band signal across the sensor.

    Notice: the expected relative peak positions for the original strips were: [0.30, 0.52, 0.74]
    """

    # Initialize profile
    profile = np.zeros(window.shape[1])

    # Process all columns
    for c in range(border_x, window.shape[1] - border_x):
        # Extract the column (without border)
        column = window[border_y: window.shape[0] - border_y, c]

        # Calculate and store the median value
        profile[c] = np.median(column)

    # Subtract the background
    if subtract_background:

        if qc:
            original_profile = profile.copy()

        # Estimate and subtract the background
        profile, background, background_offset = fit_and_subtract_background(
            profile,
            border_x,
            subtract_offset=20
        )

        # Quality control plots
        if qc:
            # Suppress warnings
            warnings.filterwarnings("ignore")

            fig, ax = plt.subplots()

            # Plot profile and estimated background
            ax.plot(
                np.arange(border_x, len(original_profile) - border_x),
                original_profile[border_x: len(original_profile) - border_x],
                'k-',
                markersize=6)
            ax.plot(
                np.arange(border_x, len(background) - border_x),
                background[border_x: len(background) - border_x],
                'k--',
                markersize=6)
            ax.plot(
                np.arange(border_x, len(background_offset) - border_x),
                background_offset[border_x: len(background_offset) - border_x],
                'r-',
                markersize=6)

            # Save to output folder
            filename = str(Path(out_qc_folder) / (basename + "_peak_background_estimation.png"))
            fig.savefig(filename)
            plt.close(fig)

            # Restore warnings
            warnings.resetwarnings()

    # Estimate a threshold (on the noisy data) to distinguish noisy candidate peaks from likely correct ones
    peak_threshold, loc_min_indices, md, lowest_background_threshold = \
        estimate_threshold_for_significant_peaks(profile, border_x, thresh_factor)

    # Low-pass filter the profile
    profile[border_x:-border_x] = gaussian_filter1d(profile[border_x:-border_x], 1)

    # Make sure that no intensities in the profile may be lower than lowest_background_threshold
    tmp = profile[border_x:-border_x]
    tmp = np.where(tmp < lowest_background_threshold, lowest_background_threshold, tmp)
    profile[border_x:-border_x] = tmp

    # Find the peaks (add back the border offset)
    peaks = find_peaks(profile[border_x: len(profile) - border_x], width=peak_width)[0] + border_x

    # Integrate the band signals
    valid_peaks = []
    valid_lower_bounds = []
    valid_upper_bounds = []
    for index, c_peak in enumerate(peaks):
        # If the absolute peak value is under the peak_threshold,
        # drop it and move on to the next candidate.
        if profile[c_peak] < peak_threshold:
            continue

        # Find the peak bounds
        lower_bound, upper_bound, image_log = find_peak_bounds(
            profile, border_x, c_peak, image_log, verbose
        )

        # Store the information
        valid_peaks.append(c_peak)
        valid_lower_bounds.append(lower_bound)
        valid_upper_bounds.append(upper_bound)

    # Check that the peaks do not overlap
    for i in range(len(valid_lower_bounds) - 1):
        next_lower_bound = valid_lower_bounds[i + 1]
        current_upper_bound = valid_upper_bounds[i]
        if current_upper_bound >= next_lower_bound:
            split = (current_upper_bound + next_lower_bound) // 2
            valid_lower_bounds[i + 1] = split
            valid_upper_bounds[i] = split - 1

    # Finally integrate the signal
    band_signals = []
    for c_peak, lower_bound, upper_bound in zip(valid_peaks, valid_lower_bounds, valid_upper_bounds):
        # Integrate the signal
        dy = (profile[upper_bound] - profile[lower_bound]) / (upper_bound - lower_bound + 1)
        tot_intensity = 0.0
        i = 0
        for c in range(lower_bound, upper_bound + 1):
            tot_intensity += profile[c] - (profile[lower_bound] + float(i) * dy)
            i += 1

        band_signals.append(tot_intensity)

    # Now assign the peaks to the physical band location
    bars = identify_bars_alt(
        valid_peaks,
        len(profile),
        sensor_band_names,
        peak_expected_relative_location,
        control_band_index
    )

    # Merge quantification and bars dictionary
    merged_results = {}
    for bar in bars:
        indx = int(bars[bar])
        if indx is not None:
            current = {
                "band": bar,
                "peak_pos": valid_peaks[indx],
                "signal": band_signals[indx],
                "normalized_signal": 0.0,
                "peak_index": indx
            }
            merged_results[bar] = current

    # Update the valid_peaks, valid_lower_bounds, and upper_lower_bounds lists
    valid_peaks_original = valid_peaks.copy()
    valid_lower_bounds_original = valid_lower_bounds.copy()
    valid_upper_bounds_original = valid_upper_bounds.copy()
    valid_peaks = []
    valid_lower_bounds = []
    valid_upper_bounds = []
    for bar in bars:
        indx = bars[bar]
        if indx is not None:
            valid_peaks.append(valid_peaks_original[indx])
            valid_lower_bounds.append(valid_lower_bounds_original[indx])
            valid_upper_bounds.append(valid_upper_bounds_original[indx])
            merged_results[bar]['lower_bound'] = valid_lower_bounds_original[indx]
            merged_results[bar]['upper_bound'] = valid_upper_bounds_original[indx]
            merged_results[bar]['color'] = \
                BAND_COLORS[sensor_band_names.index(bar) % len(BAND_COLORS)]

    # Get the control band name
    control_band_name = sensor_band_names[control_band_index]

    # Now normalize the signals against the control
    if control_band_name in merged_results:
        ctl_signal = merged_results[control_band_name]["signal"]
        merged_results[control_band_name]["normalized_signal"] = 1.0

        # Now process all other bands
        for current_band_name in sensor_band_names:
            if current_band_name == control_band_name:
                continue
            if current_band_name in merged_results:
                merged_results[current_band_name]["normalized_signal"] = \
                    merged_results[current_band_name]["signal"] / ctl_signal

    # Quality control plots
    if qc:
        # Suppress warnings
        warnings.filterwarnings("ignore")

        fig, ax = plt.subplots()

        # Plot profile
        ax.plot(
            np.arange(border_x, len(profile) - border_x), profile[border_x: len(profile) - border_x],
            'k-', markersize=6)

        ax.set_xlim([0, len(profile)])
        ax.set_ylim([
            np.min(profile[loc_min_indices]) * 0.9,
            np.max(profile) * 1.1])

        # Plot minima
        for min in loc_min_indices:
            ax.plot(min, profile[min], 'g.')

        # Plot peaks and local bounds
        for _, result in merged_results.items():
            ax.plot(result['peak_pos'], profile[result['peak_pos']], 'rs', markersize=4)
            ax.plot(
                [result['lower_bound'], result['upper_bound']],
                [profile[result['lower_bound']], profile[result['upper_bound']]],
                'o-', linewidth=2, color=result['color']
            )

        # Plot the peak threshold
        ax.plot([0, len(profile)], [peak_threshold, peak_threshold], 'r--')

        # Plot the estimated background
        ax.plot([0, len(profile)], [md, md], 'g--')

        # Save to output folder
        filename = str(Path(out_qc_folder) / (basename + "_peak_analysis.png"))
        fig.savefig(filename)
        plt.close(fig)

        # Restore warnings
        warnings.resetwarnings()

        # Suppress warnings (this seems to be necessary)
        warnings.filterwarnings("ignore")

        # Draw the band on the original image
        fig, ax = plt.subplots()
        ax.imshow(window, cmap='gray')
        for _, result in merged_results.items():
            lb, ub = result['lower_bound'], result['upper_bound']
            ax.plot([lb, ub, ub, lb, lb],
                    [border_y, border_y, window.shape[0] - border_y, window.shape[0] - border_y, border_y],
                    '-', linewidth=2, color=result['color'])

        # Save to output folder
        filename = str(Path(out_qc_folder) / (basename + "_peak_overlays.png"))
        fig.savefig(filename)
        plt.close(fig)

        # Restore warnings
        warnings.resetwarnings()

    return merged_results, image_log


def extract_inverted_sensor(gray, sensor_center=(119, 471), sensor_size=(40, 190)):
    """Returns the sensor area at the requested position without searching."""
    x0 = sensor_center[1] - sensor_size[1] // 2
    x = x0 + sensor_size[1]
    y0 = sensor_center[0] - sensor_size[0] // 2
    y = y0 + sensor_size[0]
    return invert_image(gray[y0:y, x0:x])


def get_sensor_contour_fh(
        strip_gray,
        sensor_center,
        sensor_size,
        sensor_search_area,
        peak_expected_relative_location,
        control_band_index=-1,
        min_control_bar_width=7
):
    """Extract the sensor area from the gray strip image.

    :param strip_gray: np.ndarray
        Gray-value image of the extracted strip.

    :param sensor_center: Tuple[int, int]
        Coordinates of the center of the sensor (x, y).

    :param sensor_size: Tuple[int, int]
        Size of the sensor (width, height).

    :param sensor_search_area: Tuple[int, int]
        Size of the sensor search area (width, height).

    :param peak_expected_relative_location: list[float, ...]
        List of expected relative peak (band) positions in the sensor (0.0 -> 1.0).

    :param control_band_index: int
        Index of the control band in the peak_expected_relative_location.
        (Optional, default -1 := right-most)

    :param min_control_bar_width: int
        Minimum width of the control bar (in pixels).
        (Optional, default 7)

    :return Tuple:
        Realigned sensor: np.ndarray
        Sensor coordinates: [y0, y, x0, x]
        sensor_score: score for the sensor extracted (obsolete: fixed at 1.0)
    """

    # Input argument sanitation
    if sensor_search_area[0] < sensor_size[0] or sensor_search_area[1] < sensor_size[1]:
        sensor_search_area = deepcopy(sensor_size)

    # Invert the image so that the bands are white
    bit_depth = 8 if strip_gray.dtype == np.uint8 else 16
    strip_gray_inverted = invert_image(strip_gray.copy(), bit_depth)

    # Extract the search area
    dy = sensor_search_area[0] // 2
    dx = sensor_search_area[1] // 2
    search_area = strip_gray_inverted[
                  sensor_center[0] - dy: sensor_center[0] + dy + 1,
                  sensor_center[1] - dx: sensor_center[1] + dx + 1,
                  ]

    # Segment using Li
    optimal_threshold = filters.threshold_li(search_area)
    search_area_bw = search_area > optimal_threshold

    # Now find the control band starting from the right
    profile = np.zeros(search_area_bw.shape[1])
    for x in range(search_area_bw.shape[1] - 1, -1, -1):
        profile[x] = np.sum(search_area_bw[:, x])

    # Find the bars
    peaks, properties = find_peaks(profile, prominence=5, width=min_control_bar_width)

    # Keep bars that are wide enough as candidates
    candidate_locations = []
    candidate_relative_locations = []
    candidate_widths = []
    for i in range(len(peaks)):
        width = properties["widths"][i]
        if width > min_control_bar_width:
            candidate_locations.append(peaks[i])
            candidate_relative_locations.append(float(peaks[i]) / sensor_search_area[1])
            candidate_widths.append(width)

    # Keep bar that is closest to the expected position
    # (even considering the mistake given by the largest
    # search area)
    accepted_loc = -1
    accepted_width = -1
    if len(candidate_locations) > 0:
        indx = np.argmin(
            cdist(
                np.array(peak_expected_relative_location[control_band_index]).reshape(-1, 1),
                np.array(candidate_relative_locations).reshape(-1, 1),
            )
        )
        accepted_loc = candidate_locations[indx]
        accepted_width = candidate_widths[indx]

    # If nothing was found, just return the center of the
    # search area (with the expected size)
    if accepted_loc == -1:
        # Return the center of the search_area
        y0 = sensor_center[0] - sensor_size[0] // 2
        y = y0 + sensor_size[0]
        x0 = sensor_center[1] - sensor_size[1] // 2
        x = x0 + sensor_size[1]

        # @ToDo Come up with a proper score
        sensor_score = 0.0

        return strip_gray_inverted[y0: y, x0: x], [y0, y, x0, x], sensor_score

    # Now use the expected peak location to re-center the sensor in x
    corrected_pos = accepted_loc - (sensor_search_area[1] - sensor_size[1]) // 2
    curr_rel_pos_on_sensor_width = float(corrected_pos) / sensor_size[1]
    expected_rel_pos = peak_expected_relative_location[control_band_index]

    # Calculate the correction factor in x
    sensor_center_dx = int((expected_rel_pos - curr_rel_pos_on_sensor_width) * sensor_size[1])

    # Use the vertical extent of the bar to re-center the sensor in y
    b_x0 = int(accepted_loc - accepted_width // 2)
    b_x = int(np.round(b_x0 + accepted_width))
    bar_bw = search_area_bw[:, b_x0:b_x]

    # Find the center of mass of the bar
    y, x = np.where(bar_bw)

    # Did we find the control bar?
    if len(y) == 0:
        # If the control bar was not found, just return the center of the
        # search area (with the expected size)
        y0 = sensor_center[0] - sensor_size[0] // 2
        y = y0 + sensor_size[0]
        x0 = sensor_center[1] - sensor_size[1] // 2
        x = x0 + sensor_size[1]

        # @ToDo Come up with a proper score
        sensor_score = 0.0

        return strip_gray_inverted[y0: y, x0: x], [y0, y, x0, x], sensor_score

    # Calculate the correction factor in y
    sensor_center_dy = int(np.round(np.mean(y)) - sensor_search_area[0] // 2)

    # New coordinates around the shifted center of the sensor
    y0 = sensor_center[0] + sensor_center_dy - sensor_size[0] // 2
    y = y0 + sensor_size[0]
    x0 = sensor_center[1] + sensor_center_dx - sensor_size[1] // 2
    x = x0 + sensor_size[1]

    # @ToDo Come up with a proper score
    sensor_score = 1.00

    # Return the extracted (inverted) sensor
    return strip_gray_inverted[y0: y, x0: x], [y0, y, x0, x], sensor_score


def extract_rotated_strip_from_box(box_gray, box):
    """Segments the strip from the box image and rotates it so that it is horizontal."""

    # Segment using Li
    optimal_threshold = filters.threshold_li(box_gray)
    BW = box_gray > optimal_threshold

    # Make sure that there is no global border around the image, or
    # the morphological operations below will fill in the whole image

    # Carve a hole in the left edge (if needed)
    x = int(0)
    y = int(box.shape[0] / 2)
    while BW[y - 1, x] or BW[y, x] or BW[y + 1, x]:
        BW[y - 1, x] = False
        BW[y, x] = False
        BW[y + 1, x] = False
        x += 1

    # Carve a hole in the right edge (if needed)
    x = int(box.shape[1]) - 1
    y = int(box.shape[0] / 2)
    while BW[y - 1, x] or BW[y, x] or BW[y + 1, x]:
        BW[y - 1, x] = False
        BW[y, x] = False
        BW[y + 1, x] = False
        x -= 1

    # Carve a hole in the top edge (if needed)
    x = int(box.shape[1] / 2)
    y = int(0)
    while BW[y, x - 1] or BW[y, x] or BW[y, x + 1]:
        BW[y, x - 1] = False
        BW[y, x] = False
        BW[y, x + 1] = False
        y += 1

    # Carve a hole in the bottom edge (if needed)
    x = int(box.shape[1] / 2)
    y = int(box.shape[0]) - 1
    while BW[y, x - 1] or BW[y, x] or BW[y, x + 1]:
        BW[y, x - 1] = False
        BW[y, x] = False
        BW[y, x + 1] = False
        y -= 1

    # Clean up the mask
    BW = binary_fill_holes(BW)
    BW = binary_opening(BW, iterations=3)

    # Find the connected components
    labels, nb = label(BW)

    # Now we want to find a large object (not necessarily the largest)
    # that contains the center of the image.
    center_y = box_gray.shape[0] // 2
    center_x = box_gray.shape[1] // 2

    # Collect all objects areas
    areas = [np.sum(labels == x) for x in range(1, nb + 1)]

    is_found = False
    while not is_found:

        # Gets currently largest object (might be changed
        # at the end of current iteration)
        indx = 1 + np.argmax(areas)

        # Make sure that we haven't already processed all objects
        if areas[indx - 1] < 0:
            return None, None

        # Copy the object to a new mask
        nBW = (0 * BW.copy()).astype(np.uint8)
        nBW[labels == indx] = 255

        # Is the pixel at the center of the image contained in
        # this object
        if nBW[center_y, center_x] == 255:
            # The center pixel is contained in this object;
            # with use this.
            is_found = True
        else:
            # This object does not cover the center of the image;
            # we test the second largest. We eliminate current
            # object from the race and continue.
            areas[indx - 1] = -1

    # Find the (possibly rotated) contour
    # contours, hierarchy = cv2.findContours(nBW, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if cv2.getVersionMajor() == 4:
        contours, hierarchy = cv2.findContours(
            nBW, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    else:
        _, contours, hierarchy = cv2.findContours(
            nBW, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Make sure to work with the largest contour
    if len(contours) == 1:
        contour = contours[0]

    else:
        contour = None
        max_length = -1
        for c in contours:
            if c.shape[0] > max_length:
                max_length = c.shape[0]
                contour = c

    if contour is None:
        return None, None

    # Get the coarse orientation from the bounding box
    _, _, width, height = cv2.boundingRect(contour)

    # Get the rotated rectangle; the angle is not obvious to
    # interpret; we will need the bounding rectangle for that
    rect = cv2.minAreaRect(contour)

    # Apply the rotation (this assumes that the extracted rectangle has
    # its width somewhat parallel to the X axis)
    if width > height:
        angle = rect[2]
        if 0 <= angle < 45:
            corr_angle = -angle
        elif 0 > angle >= -45:
            corr_angle = angle
        elif 45 <= angle < 90:
            corr_angle = 90 - angle
        else:
            corr_angle = angle + 90

        # Rotate
        nBW_rotated = rotate(nBW, corr_angle)
        box_gray_rotated = rotate(box_gray, corr_angle)
        box_rotated = rotate(box, corr_angle)

    else:

        # The strip appears to be oriented vertically.
        # This is most likely wrong; we won't try to
        # rotate it.
        nBW_rotated = nBW
        box_gray_rotated = box_gray
        box_rotated = box

    # Find the contour of the rotated BW mask
    # contours, _ = cv2.findContours(nBW_rotated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if cv2.getVersionMajor() == 4:
        contours, _ = cv2.findContours(
            nBW_rotated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    else:
        _, contours, _ = cv2.findContours(
            nBW_rotated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Make sure to work with the largest contour
    if len(contours) == 1:
        contour = contours[0]

    else:
        contour = None
        max_length = -1
        for c in contours:
            if c.shape[0] > max_length:
                max_length = c.shape[0]
                contour = c

    if contour is None:
        return None, None

    # Get the coarse orientation from the bounding box
    x, y, width, height = cv2.boundingRect(contour)

    # Get the bounding box closer to the rectangle
    y0, y, x0, x = adapt_bounding_box(nBW_rotated, x, y, width, height, fraction=0.75)

    # Extract the rotated strip
    strip_gray = box_gray_rotated[y0: y, x0: x]
    strip = box_rotated[y0: y, x0: x]

    # Return
    return strip_gray, strip


def adapt_bounding_box(bw, x0, y0, width, height, fraction=0.75):
    """Make the bounding box come closer to the strip by remove bumps along the outline."""

    # Make sure we have a binary mask
    bw = bw > 0

    # height, width = bw.shape
    fraction_h = fraction * height
    fraction_w = fraction * width

    new_x0 = x0
    new_x = x0 + width - 1
    new_y0 = y0
    new_y = y0 + height - 1

    # End points
    mid_x = x0 + width // 2 + 1
    mid_y = y0 + height // 2 + 1

    # From left
    for w in range(x0, mid_x):
        if np.sum(bw[:, w]) > fraction_h:
            new_x0 = w
            break

    # From right
    for w in range(x0 + width - 1, mid_x, -1):
        if np.sum(bw[:, w]) > fraction_h:
            new_x = w
            break

    # From top
    for h in range(y0, mid_y):
        if np.sum(bw[h, :]) > fraction_w:
            new_y0 = h
            break

    # From bottom
    for h in range(y0 + height - 1, mid_y, -1):
        if np.sum(bw[h, :]) > fraction_w:
            new_y = h
            break

    return new_y0, new_y, new_x0, new_x


def point_in_rect(point, rect):
    """Check if the given point (x, y) is contained in the rect (x0, y0, width, height)."""
    x1, y1, w, h = rect
    x2, y2 = x1 + w, y1 + h
    x, y = point
    if x1 <= x <= x2:
        if y1 <= y <= y2:
            return True
    return False


def get_rectangles_from_image_and_rectangle_props(
        img_shape,
        rectangle_props=(0.52, 0.15, 0.09)
):
    """Calculate the left and right rectangles to be used for the orientation
    analysis using the Hough transform.

    :param img_shape: tuple
    Image shape (width, height)

    :param rectangle_props: tuple
        Tuple containing information about the relative position of the two rectangles
        to be searched for the inlet on both sides of the center of the image:
             rectangle_props[0]: relative (0..1) vertical height of the rectangle with
                                 respect to the image height.
             rectangle_props[1]: relative distance of the left edge of the right rectangle
                                 with respect to the center of the image.
             rectangle_props[2]: relative distance of the left edge of the left rectangle
                                 with respect to the center of the image.

    :return Tuple containing left and right rectangles
    """

    # Define shape of search rectangles
    height_factor = rectangle_props[0]
    center_cut_off = round(rectangle_props[1] * img_shape[1])
    border_cut_off = round(rectangle_props[2] * img_shape[1])
    left_rect = [
        border_cut_off,
        round(img_shape[0] / 2 - ((img_shape[0] * height_factor) / 2)),
        round(img_shape[1] / 2) - center_cut_off - border_cut_off,
        round(img_shape[0] * height_factor)
    ]
    right_rect = [
        round(img_shape[1] / 2) + center_cut_off,
        round(img_shape[0] / 2 - ((img_shape[0] * height_factor) / 2)),
        round(img_shape[1] / 2) - center_cut_off - border_cut_off,
        round(img_shape[0] * height_factor)
    ]

    return left_rect, right_rect


def use_hough_transform_to_rotate_strip_if_needed(
        img_gray,
        rectangle_props=(0.52, 0.15, 0.09),
        stretch=False,
        img=None,
        qc=False
):
    """Estimate the orientation of the strip looking at features in the area around the
    expected sensor position. If the orientation is estimated to be wrong, rotate the strip.

    :param img_gray: np.ndarray
        Gray-scale image to be analyzed.

    :param rectangle_props: tuple
        Tuple containing information about the relative position of the two rectangles
        to be searched for the inlet on both sides of the center of the image:
             rectangle_props[0]: relative (0..1) vertical height of the rectangle with
                                 respect to the image height.
             rectangle_props[1]: relative distance of the left edge of the right rectangle
                                 with respect to the center of the image.
             rectangle_props[2]: relative distance of the left edge of the left rectangle
                                 with respect to the center of the image.


    :param stretch: bool
        Set to True to apply auto-stretch to the image for Hough detection (1, 99 percentile).
        The *original* image will be rotated, if needed.

    :param img: np.ndarray or None (default)
        Apply correction also to this image, if passed.

    :param qc: bool
        If True, create quality control images.
    """

    # Initialize quality control image if needed
    qc_image = None
    if qc:
        if img is not None:
            qc_image = img.copy()
        else:
            qc_image = cv2.cvtColor(img_gray.copy(), cv2.COLOR_GRAY2RGB)

    # Get search rectangles
    left_rect, right_rect = get_rectangles_from_image_and_rectangle_props(
        img_gray.shape,
        rectangle_props
    )

    # Pre-process the image to make the detection of circles more robust
    try:
        img_work = img_gray.copy()
        if stretch:
            pLb, pUb = np.percentile(img_work, (1, 99))
            img_work = exposure.rescale_intensity(img_work, in_range=(pLb, pUb))
        img_work = cv2.medianBlur(img_work, 13)
        img_work = cv2.Laplacian(img_work, cv2.CV_8UC1, ksize=5)
        img_work = cv2.dilate(img_work, (3, 3))
        img_work = cv2.bilateralFilter(img_work, 5, 9, 9)

    except Exception:
        # If something went wrong, return the original images
        return img_gray, img, qc_image, False, left_rect, right_rect

    min_radius = int(0.15 * img_gray.shape[0] * rectangle_props[0])
    max_radius = int(0.30 * img_gray.shape[0] * rectangle_props[0])

    # Find circles
    circles = cv2.HoughCircles(
        img_work,
        cv2.HOUGH_GRADIENT,
        1,
        1,
        param1=75,
        param2=20,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    # Build a weighed vote for both sides
    weighed_vote_left = 0.0
    weighed_vote_right = 0.0

    # Were there any circles found?
    if circles is not None:

        # Calculate and store the coordinates of the centers of
        # the left and right rectangles
        left_rect_center = (
            left_rect[0] + 0.5 * left_rect[2],
            left_rect[1] + 0.5 * left_rect[3]
        )
        right_rect_center = (
            right_rect[0] + 0.5 * right_rect[2],
            right_rect[1] + 0.5 * right_rect[3]
        )

        # Distances will be normalized to half diagonal distance inside the rectangle
        norm_left_rect_dist = np.sqrt(
            0.5 * left_rect[2] * 0.5 * left_rect[2] +
            0.5 * left_rect[3] * 0.5 * left_rect[3]
        )
        norm_right_rect_dist = np.sqrt(
            0.5 * right_rect[2] * 0.5 * right_rect[2] +
            0.5 * right_rect[3] * 0.5 * right_rect[3]
        )

        # Process the circles
        circles = np.uint16(np.around(circles))
        num_best_circles = 30
        c = 0
        for centers in circles[0, :]:

            # Get the center coordinates and the radius
            center_x, center_y, radius = centers

            # Count in left region
            ret_left = point_in_rect([center_x, center_y], left_rect)
            if ret_left:
                # Calculate weighted distance (1.0 - normalized distance)
                # and add it as a weight
                dx_l = center_x - left_rect_center[0]
                dy_l = center_y - left_rect_center[1]
                w_l = 1.0 - (np.sqrt(dx_l * dx_l + dy_l * dy_l) / norm_left_rect_dist)
                weighed_vote_left += w_l

            # Count in right region
            ret_right = point_in_rect([center_x, center_y], right_rect)
            if ret_right:
                # Calculate weighted distance (1.0 - normalized distance)
                # and add it as a weight
                dx_r = center_x - right_rect_center[0]
                dy_r = center_y - right_rect_center[1]
                w_r = 1.0 - (np.sqrt(dx_r * dx_r + dy_r * dy_r) / norm_right_rect_dist)
                weighed_vote_right += w_r

            if qc:
                if ret_left or ret_right:
                    cv2.circle(qc_image, (center_x, center_y), radius, (255, 0, 255), 1)
                else:
                    cv2.circle(qc_image, (center_x, center_y), radius, (255, 0, 0), 1)

            c += 1
            if c >= (num_best_circles - 1):
                if weighed_vote_left >= 0 or weighed_vote_right >= 0:
                    break
                else:
                    # If we still haven't found anything, let's try one more. We will stop
                    # as soon as we find one circle in one of the rectangles, or we run out
                    # of circles.
                    c -= 1

    if qc:
        # Add search rectangles to image (the winning one is in red)
        cv2.rectangle(
            qc_image,
            (left_rect[0], left_rect[1]),
            (left_rect[2] + left_rect[0], left_rect[3] + left_rect[1]),
            (0, 0, 255) if weighed_vote_left >= weighed_vote_right else (255, 255, 255),
            2
        )
        cv2.rectangle(
            qc_image,
            (right_rect[0], right_rect[1]),
            (right_rect[2] + right_rect[0], right_rect[3] + right_rect[1]),
            (0, 0, 255) if weighed_vote_left < weighed_vote_right else (255, 255, 255),
            2
        )

    # The condition for rotation is that there are more circles
    # in the search rectangle on the right than on the left
    rotated = False
    if weighed_vote_right > weighed_vote_left:
        rotated = True
        img_gray = rotate(img_gray, 180)
        if img is not None:
            img = rotate(img, 180)

    return img_gray, img, qc_image, rotated, left_rect, right_rect


def use_ocr_to_rotate_strip_if_needed(img_gray, img=None, text="COVID", on_right=True):
    """Try reading the given text on the strip. The text is expected to be on one
    side of the strip; if it is found on the other side, rotate the strip.

    We apply the same rotation also to the second image, if passed.
    """

    rotated = False

    # If text is "", do nothing. For robustness, also check against '""'.
    if text == "" or text == '""':
        return img_gray, img, rotated

    # Try with the following orientations
    angles = [0, -90, 90, 180]

    # Use tesseract to read text from the strip. If successful,
    # this can be used to figure out the direction in which the
    # strip was placed under the camera. In a first attempt, we
    # search for the given text.

    for angle in angles:

        # Rotate the image
        rotated_img_gray = rotate(img_gray.copy(), angle)

        # Search for the text
        results = pytesseract.image_to_data(rotated_img_gray, output_type=Output.DICT)
        n_boxes = len(results['text'])
        for i in range(n_boxes):
            if text.upper() in results['text'][i].upper():

                center_of_mass_x = results['left'][i] + results['width'][i] // 2
                center_of_mass_y = results['top'][i] + results['height'][i] // 2

                # Found: now consider the possible cases
                if angle == 0:

                    # The image was not rotated; so it's still lying horizontally
                    if on_right:
                        if center_of_mass_x < rotated_img_gray.shape[1] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)
                    else:
                        if center_of_mass_x > rotated_img_gray.shape[1] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)

                    return img_gray, img, rotated

                elif angle == -90:

                    # The image was rotated 90 degrees clockwise; "right" is now "down"
                    if on_right:
                        if center_of_mass_y < rotated_img_gray.shape[0] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)
                    else:
                        if center_of_mass_y > rotated_img_gray.shape[0] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)

                    return img_gray, img, rotated

                else:

                    # The image was rotated 90 degrees counter-clockwise; "right" is now "up"
                    if on_right:
                        if center_of_mass_y > rotated_img_gray.shape[0] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)
                    else:
                        if center_of_mass_y < rotated_img_gray.shape[0] // 2:
                            # The label is on the wrong side of the strip
                            rotated = True
                            img_gray = rotate(img_gray, 180)
                            if img is not None:
                                img = rotate(img, 180)

                    return img_gray, img, rotated

    # The image was not rotated
    rotated = False

    return img_gray, img, rotated


def read_patient_data_by_ocr(
        image,
        known_manufacturers=consts.KnownManufacturers):
    """Try to extract the patient data by OCR."""

    # Use a gray-value image (works better than RGB)
    image_gray = BGR2Gray(image)

    # Initialize outputs
    fid = ""
    manufacturer = ""

    # Try with different angles
    angles = [0, -90, 90, 180]

    for angle in angles:

        # Stop if we have everything
        if fid != "" and manufacturer != "":
            return fid, manufacturer

        # Use tesseract to read text from the strip. If successful,
        # this can be used to figure out the direction in which the
        # strip was placed under the camera. In a first attempt, we
        # search for the given text.
        try:
            results = pytesseract.image_to_data(
                rotate(image_gray.copy(), angle),
                output_type=Output.DICT
            )
        except:
            continue

        # Examine the results
        n_boxes = len(results['text'])
        for i in range(n_boxes):
            current_text = results['text'][i].upper()
            if current_text != "":

                # Test for manufacturer name
                for m in known_manufacturers:
                    if m.upper() in current_text.upper():
                        manufacturer = m.upper()
                        continue

                # Test for fid
                match = re.search(r'^(?P<fid>[A-Z]{0,18}[0-9]{0,18}).*', current_text)
                if match is None:
                    continue
                else:
                    fid = match.group('fid')

    return fid, manufacturer
