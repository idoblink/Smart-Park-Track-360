"""
ParkTrack 360 — tests/test_vision.py
Unit tests for computer vision digit recognition (marker digits 1 to 8).
"""

import pytest
import numpy as np
import cv2
from server.vision import DigitRecognizer


@pytest.fixture
def recognizer():
    return DigitRecognizer()


def test_template_bank_loaded(recognizer):
    assert len(recognizer.bank) == 8
    for d in range(1, 9):
        assert len(recognizer.bank[d]) > 0
        for tpl in recognizer.bank[d]:
            assert tpl.shape == (32, 32)


def test_digit_recognition_all_numbers(recognizer):
    """Verifies that synthetic black marker digits 1 through 8 on white paper
    are detected and correctly classified with high confidence."""
    for expected_digit in range(1, 9):
        # Create white paper patch
        paper = np.ones((120, 120), dtype=np.uint8) * 240
        # Draw black marker digit
        cv2.putText(paper, str(expected_digit), (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (20, 20, 20), 4)

        # Convert to BGR frame as would come from camera
        frame = cv2.cvtColor(paper, cv2.COLOR_GRAY2BGR)

        detections = recognizer.detect_digits(frame)
        assert len(detections) > 0, f"Digit {expected_digit} was not detected!"
        top = detections[0]
        assert top["digit"] == expected_digit, (
            f"Expected digit {expected_digit}, but classified as {top['digit']} "
            f"(conf: {top['conf']:.2f})"
        )
        assert top["conf"] >= 0.65, (
            f"Confidence for digit {expected_digit} too low: {top['conf']:.2f}"
        )


def test_non_digit_rejection(recognizer):
    """Verifies that plain white paper with no text produces 0 detections."""
    blank_paper = np.ones((120, 120, 3), dtype=np.uint8) * 240
    detections = recognizer.detect_digits(blank_paper)
    assert len(detections) == 0
