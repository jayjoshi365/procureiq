"""Tests for utils.py"""
import pytest
from utils import sx, hex_to_rgba, safe_divide


class TestUtils:
    """Test utility functions."""

    def test_sx_number_formatting(self):
        """Test sx function formats numbers correctly."""
        # Test integers
        assert sx(1000) == "1,000"
        assert sx(1000000) == "1,000,000"

        # Test floats
        assert sx(1234.56) == "1,234.56"
        assert sx(1234567.89) == "1,234,567.89"

        # Test zero and negative
        assert sx(0) == "0"
        assert sx(-1000) == "-1,000"

        # Test None
        assert sx(None) == "0"

    def test_sx_large_numbers(self):
        """Test sx with very large numbers."""
        assert sx(1000000000) == "1,000,000,000"
        assert sx(1234567890) == "1,234,567,890"

    def test_hex_to_rgba_valid_hex(self):
        """Test hex_to_rgba with valid hex colors."""
        # Test 6-digit hex
        result = hex_to_rgba("#FF0000", 0.5)
        assert result == "rgba(255, 0, 0, 0.5)"

        # Test another color
        result = hex_to_rgba("#00FF00", 0.8)
        assert result == "rgba(0, 255, 0, 0.8)"

        # Test black
        result = hex_to_rgba("#000000", 1.0)
        assert result == "rgba(0, 0, 0, 1.0)"

    def test_hex_to_rgba_edge_cases(self):
        """Test hex_to_rgba with edge cases."""
        # Test with alpha = 0
        result = hex_to_rgba("#FFFFFF", 0)
        assert result == "rgba(255, 255, 255, 0)"

        # Test with alpha = 1
        result = hex_to_rgba("#123456", 1)
        assert result == "rgba(18, 52, 86, 1)"

    def test_hex_to_rgba_invalid_input(self):
        """Test hex_to_rgba handles invalid input gracefully."""
        # Invalid hex should not crash (implementation dependent)
        # For now, just test that it returns a string
        result = hex_to_rgba("invalid", 0.5)
        assert isinstance(result, str)

        result = hex_to_rgba("#GGG", 0.5)  # Invalid hex digits
        assert isinstance(result, str)

    def test_safe_divide_normal_cases(self):
        """Test safe_divide with normal division."""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(15, 3) == 5.0
        assert safe_divide(1, 4) == 0.25

    def test_safe_divide_by_zero(self):
        """Test safe_divide handles division by zero."""
        result = safe_divide(10, 0)
        assert result == 0.0  # Should return 0 for division by zero

    def test_safe_divide_zero_numerator(self):
        """Test safe_divide with zero numerator."""
        assert safe_divide(0, 5) == 0.0
        assert safe_divide(0, 1) == 0.0

    def test_safe_divide_negative_numbers(self):
        """Test safe_divide with negative numbers."""
        assert safe_divide(-10, 2) == -5.0
        assert safe_divide(10, -2) == -5.0
        assert safe_divide(-10, -2) == 5.0

    def test_safe_divide_float_inputs(self):
        """Test safe_divide with float inputs."""
        assert safe_divide(10.5, 2.0) == 5.25
        assert safe_divide(1.0, 3.0) == pytest.approx(0.3333, rel=1e-3)

    def test_safe_divide_return_type(self):
        """Test safe_divide always returns float."""
        assert isinstance(safe_divide(10, 2), float)
        assert isinstance(safe_divide(10, 0), float)
        assert isinstance(safe_divide(0, 5), float)