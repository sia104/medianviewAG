"""Deterministic 3x3 median filter implementation."""

from __future__ import annotations

import numpy as np
from PIL import Image


def apply_median_filter_2d(channel: np.ndarray) -> np.ndarray:
    """Apply a deterministic 3x3 median filter to a 2D single-channel image array.

    Uses replicate ('edge') padding for boundary handling and computes the exact
    median value (index 4 of the 9 sorted neighborhood pixels).

    Args:
        channel: 2D numpy array of image pixel values.

    Returns:
        2D numpy array containing the filtered pixel values with identical dtype and shape.
    """
    if channel.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape {channel.shape}")

    # Deterministic edge (replicate) boundary padding of width 1
    padded = np.pad(channel, pad_width=1, mode="edge")

    # Extract 3x3 sliding windows: shape will be (H, W, 3, 3)
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    height, width = channel.shape
    flat_windows = windows.reshape(height, width, 9)

    # In a sorted 9-element neighborhood (indices 0..8), index 4 is the exact median
    partitioned = np.partition(flat_windows, 4, axis=-1)
    median_vals = partitioned[..., 4]

    return median_vals.astype(channel.dtype)


def apply_median_filter(image_array: np.ndarray) -> np.ndarray:
    """Apply deterministic 3x3 median filtering to a 2D or 3D multi-channel image array.

    For multi-channel images (e.g. RGB), the filter is applied channel-independently.

    Args:
        image_array: 2D (grayscale) or 3D (multi-channel) numpy array.

    Returns:
        Filtered numpy array with identical shape and dtype.
    """
    if image_array.ndim == 2:
        return apply_median_filter_2d(image_array)
    elif image_array.ndim == 3:
        num_channels = image_array.shape[2]
        channels = [
            apply_median_filter_2d(image_array[..., c])
            for c in range(num_channels)
        ]
        return np.stack(channels, axis=-1)
    else:
        raise ValueError(
            f"Unsupported image array dimensions: {image_array.ndim}. Expected 2D or 3D array."
        )


def filter_pil_image(image: Image.Image) -> Image.Image:
    """Apply deterministic 3x3 median filtering to a PIL Image.

    Converts palette or exotic modes to RGB. Preserves 'L' (grayscale) and 'RGB'.

    Args:
        image: Source PIL Image.

    Returns:
        Filtered PIL Image.
    """
    target_mode = "L" if image.mode == "L" else "RGB"
    working_image = image if image.mode == target_mode else image.convert(target_mode)

    arr = np.asarray(working_image)
    filtered_arr = apply_median_filter(arr)
    return Image.fromarray(filtered_arr, mode=target_mode)
