"""Unit tests for deterministic 3x3 median filter."""

import numpy as np
import pytest
from PIL import Image

from medianview.filter import (
    apply_median_filter,
    apply_median_filter_2d,
    filter_pil_image,
)


def test_median_filter_2d_synthetic_matrix() -> None:
    """Test 3x3 median filter against an exact known synthetic matrix."""
    # 5x5 image with an isolated spike in the center
    # [[10, 10, 10, 10, 10],
    #  [10, 10, 10, 10, 10],
    #  [10, 10, 255, 10, 10],
    #  [10, 10, 10, 10, 10],
    #  [10, 10, 10, 10, 10]]
    input_matrix = np.full((5, 5), 10, dtype=np.uint8)
    input_matrix[2, 2] = 255  # impulse noise

    filtered = apply_median_filter_2d(input_matrix)

    # The 3x3 window around (2, 2) has eight 10s and one 255.
    # Sorted: [10, 10, 10, 10, 10, 10, 10, 10, 255].
    # Median is index 4 -> 10.
    assert filtered[2, 2] == 10
    # Entire output should be smoothed to 10
    expected = np.full((5, 5), 10, dtype=np.uint8)
    np.testing.assert_array_equal(filtered, expected)


def test_median_filter_boundary_handling() -> None:
    """Test deterministic edge (replicate) boundary padding."""
    # 3x3 matrix:
    # [[100,  10,  10],
    #  [ 10,  10,  10],
    #  [ 10,  10,  10]]
    # Top-left pixel (0,0) with edge replicate padding:
    # Padded 3x3 window around (0,0):
    # [[100, 100, 10],
    #  [100, 100, 10],
    #  [ 10,  10, 10]]
    # Sorted: [10, 10, 10, 10, 10, 100, 100, 100, 100]
    # Median is index 4 -> 10.
    arr = np.full((3, 3), 10, dtype=np.uint8)
    arr[0, 0] = 100
    filtered = apply_median_filter_2d(arr)
    assert filtered[0, 0] == 10


def test_median_filter_strict_determinism() -> None:
    """Verify that multiple iterations produce byte-for-byte identical output."""
    rng = np.random.default_rng(seed=42)
    random_image = rng.integers(0, 256, size=(50, 50, 3), dtype=np.uint8)

    run1 = apply_median_filter(random_image)
    run2 = apply_median_filter(random_image)
    run3 = apply_median_filter(random_image)

    np.testing.assert_array_equal(run1, run2)
    np.testing.assert_array_equal(run2, run3)


def test_median_filter_rgb_channel_independent() -> None:
    """Verify that multi-channel RGB images are processed per-channel."""
    # Channel 0 has an impulse spike; Channel 1 has constant 20; Channel 2 has constant 30
    img = np.zeros((5, 5, 3), dtype=np.uint8)
    img[:, :, 0] = 50
    img[2, 2, 0] = 255
    img[:, :, 1] = 20
    img[:, :, 2] = 30

    filtered = apply_median_filter(img)

    assert filtered[2, 2, 0] == 50
    np.testing.assert_array_equal(filtered[:, :, 1], np.full((5, 5), 20, dtype=np.uint8))
    np.testing.assert_array_equal(filtered[:, :, 2], np.full((5, 5), 30, dtype=np.uint8))


def test_median_filter_invalid_dimensions() -> None:
    """Check that invalid array dimensions raise a ValueError."""
    with pytest.raises(ValueError, match="Expected 2D array"):
        apply_median_filter_2d(np.zeros((5, 5, 5), dtype=np.uint8))

    with pytest.raises(ValueError, match="Unsupported image array dimensions"):
        apply_median_filter(np.zeros((5,), dtype=np.uint8))


def test_filter_pil_image() -> None:
    """Verify PIL Image wrapper works seamlessly for RGB and Grayscale."""
    pil_rgb = Image.new("RGB", (10, 10), color=(128, 64, 32))
    filtered_rgb = filter_pil_image(pil_rgb)
    assert filtered_rgb.mode == "RGB"
    assert filtered_rgb.size == (10, 10)

    pil_l = Image.new("L", (10, 10), color=128)
    filtered_l = filter_pil_image(pil_l)
    assert filtered_l.mode == "L"
    assert filtered_l.size == (10, 10)
