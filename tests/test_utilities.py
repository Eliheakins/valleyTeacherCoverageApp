"""
Unit tests for utility functions
"""

import pytest
from main import add_ordinal_suffix, unique_and_ordered, sort_periods

class TestOrdinalSuffix:
    """Test ordinal suffix generation"""
    
    @pytest.mark.parametrize("number,expected", [
        (1, "1st"),
        (2, "2nd"),
        (3, "3rd"),
        (4, "4th"),
        (11, "11th"),
        (12, "12th"),
        (13, "13th"),
        (21, "21st"),
        (22, "22nd"),
        (23, "23rd"),
        (101, "101st"),
        (111, "111th"),
        (112, "112th"),
        (113, "113th"),
        (0, "0th"),
        ("1", "1st"),
        ("2", "2nd"),
        ("3", "3rd"),
    ])
    def test_add_ordinal_suffix(self, number, expected):
        """Test ordinal suffix generation for various numbers"""
        result = add_ordinal_suffix(number)
        assert result == expected
    
    def test_add_ordinal_suffix_invalid(self):
        """Test ordinal suffix with invalid input"""
        result = add_ordinal_suffix("invalid")
        assert result == "invalid"

class TestUniqueOrdered:
    """Test unique and ordered list functionality"""
    
    def test_basic_unique_ordered(self):
        """Test basic duplicate removal while preserving order"""
        result = unique_and_ordered([1, 2, 3, 2, 1, 4, 3])
        assert result == [1, 2, 3, 4]
    
    def test_string_list(self):
        """Test with string list"""
        result = unique_and_ordered(["a", "b", "a", "c", "b"])
        assert result == ["a", "b", "c"]
    
    def test_empty_list(self):
        """Test empty list"""
        result = unique_and_ordered([])
        assert result == []
    
    def test_no_duplicates(self):
        """Test list with no duplicates"""
        result = unique_and_ordered([1, 2, 3, 4])
        assert result == [1, 2, 3, 4]
    
    def test_all_duplicates(self):
        """Test list with all duplicates"""
        result = unique_and_ordered([1, 1, 1, 1])
        assert result == [1]
    
    def test_mixed_types(self):
        """Test list with mixed types"""
        result = unique_and_ordered([1, "1", 2, "2", 1, "1"])
        assert result == [1, "1", 2, "2"]

class TestSortPeriods:
    """Test period sorting functionality"""
    
    def test_basic_sort(self):
        """Test basic period sorting"""
        result = sort_periods([3, 1, 2, 4])
        assert result == [1, 2, 3, 4]
    
    def test_split_periods(self):
        """Test sorting with split periods"""
        result = sort_periods([3, "5/6", 1, "8/9", 2])
        assert result == [1, 2, 3, "5/6", "8/9"]
    
    def test_string_periods(self):
        """Test sorting string periods"""
        result = sort_periods(["3", "1", "2"])
        assert result == ["1", "2", "3"]
    
    def test_empty_list(self):
        """Test empty list"""
        result = sort_periods([])
        assert result == []
    
    def test_single_period(self):
        """Test single period"""
        result = sort_periods([1])
        assert result == [1]
    
    def test_complex_split_periods(self):
        """Test complex split period sorting"""
        result = sort_periods(["11/12", "1/2", "3/4", "5/6", "7/8", "9/10"])
        assert result == ["1/2", "3/4", "5/6", "7/8", "9/10", "11/12"]
    
    def test_mixed_periods(self):
        """Test mixed regular and split periods"""
        result = sort_periods([3, "1/2", 1, "3/4", 2, "5/6"])
        # String sorting puts "1/2" before integers when converted to strings
        assert result == ['1/2', 1, 2, 3, '3/4', '5/6']
    
    def test_invalid_periods(self):
        """Test with invalid period formats"""
        result = sort_periods([3, "invalid", 1, "5/6", 2])
        # Invalid entries should be sorted to the end
        assert result[:4] == [1, 2, 3, "5/6"]
        assert result[4] == "invalid"
    
    def test_tuple_periods(self):
        """Test sorting with tuple periods (for CT tracking)"""
        result = sort_periods([(3, True), (1, False), (2, True), "5/6"])
        assert result == [(1, False), (2, True), (3, True), "5/6"]
