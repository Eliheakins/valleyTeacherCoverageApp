"""
Unit tests for schedule parsing functionality
"""

import pytest
import pandas as pd
import tempfile
import os
from main import parseSchedule, _parse_name, _parse_coverage, _make_teacher, _merge_teacher_periods

class TestScheduleParsing:
    """Test schedule file parsing"""
    
    def test_parse_excel_file(self, sample_schedule_df, temp_schedule_file):
        """Test parsing Excel schedule file"""
        teachers, error = parseSchedule(temp_schedule_file)
        
        assert error is None
        assert len(teachers) == 4
        assert 'Smith, John' in teachers
        assert 'Doe, Jane' in teachers
    
    def test_parse_csv_file(self, sample_schedule_df, temp_csv_schedule_file):
        """Test parsing CSV schedule file"""
        teachers, error = parseSchedule(temp_csv_schedule_file)
        
        assert error is None
        assert len(teachers) == 4
        assert 'Smith, John' in teachers
    
    def test_parse_invalid_file(self):
        """Test parsing invalid file"""
        teachers, error = parseSchedule('nonexistent.xlsx')
        
        assert teachers == {}
        assert 'File not found' in error
    
    def test_parse_corrupted_file(self):
        """Test parsing corrupted file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.write(b'corrupted excel data')
        temp_file.close()
        
        try:
            teachers, error = parseSchedule(temp_file.name)
            assert teachers == {}
            assert 'Failed to read' in error
        finally:
            os.unlink(temp_file.name)

class TestNameParsing:
    """Test teacher name parsing"""
    
    @pytest.mark.parametrize("raw_name,expected", [
        ("Smith, John", "Smith, John"),
        ("Smith, John (Long Term)", "Smith, John"),
        ("  Smith, John  ", "Smith, John"),
        ("Smith, John - AM", "Smith, John - AM"),
        ("Smith, John - PM", "Smith, John - PM"),
        ("", None),
        ("nan", None),
        ("Name", None),
        ("Duty 1st", None),
        ("Plan", None),
        ("A", None),  # Too short
    ])
    def test_parse_name(self, raw_name, expected):
        """Test various name formats"""
        result = _parse_name(raw_name)
        assert result == expected, f"Failed for {repr(raw_name)}"

class TestCoverageParsing:
    """Test coverage string parsing"""
    
    @pytest.mark.parametrize("coverage_str,expected_regular,expected_ct", [
        ("1,3,5", ["1", "3", "5"], []),
        ("1,4,11 CT-2,5/6,8/9,10", ["1", "4", "11"], ["2", "5/6", "8/9", "10"]),
        ("1,2,4,5/6,10,11,", ["1", "2", "4", "5/6", "10", "11"], []),  # Trailing comma
        ("", [], []),
        ("nan", [], []),
        ("None", [], []),
        ("CT-2,3", ["CT-2", "3"], []),  # CT only (treated as regular periods)
    ])
    def test_parse_coverage(self, coverage_str, expected_regular, expected_ct):
        """Test various coverage string formats"""
        regular, ct = _parse_coverage(coverage_str)
        assert regular == expected_regular
        assert ct == expected_ct

class TestTeacherCreation:
    """Test teacher object creation and management"""
    
    def test_make_teacher(self):
        """Test creating new teacher"""
        teacher = _make_teacher("Smith, John", ["1", "3", "5"], ["2", "4"])
        
        assert teacher.name == "Smith, John"
        assert teacher.periods_need_covered == ["1", "3", "5"]
        assert teacher.periods_need_covered_CT == ["2", "4"]
    
    def test_merge_teacher_periods(self):
        """Test merging periods for existing teacher"""
        existing = _make_teacher("Smith, John", ["1", "3"], ["2"])
        _merge_teacher_periods(existing, ["3", "5"], ["4", "6"])
        
        assert sorted(existing.periods_need_covered) == ["1", "3", "5"]
        assert sorted(existing.periods_need_covered_CT) == ["2", "4", "6"]
    
    def test_duplicate_teacher_handling(self, sample_schedule_df, temp_schedule_file):
        """Test handling duplicate teacher entries"""
        # Create schedule with duplicate teacher names
        df = sample_schedule_df.copy()
        new_row = {'Name': 'Smith, John', 'Need Coverage': '2,4', '1st': 'Class', '2nd': 'Class', 
                  '3rd': 'Class', '4th': 'Class', '5th': 'Lunch', '6th': 'Class', 
                  '7th': 'Class', '8th': 'Class', '9th': 'Plan', '10th': 'Class', '11th': 'Class'}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        
        try:
            teachers, error = parseSchedule(temp_file.name)
            
            # Should merge periods, not create duplicate
            assert 'Smith, John' in teachers
            assert len(teachers) == 4  # No duplicate created
            smith = teachers['Smith, John']
            assert '1' in smith.periods_need_covered
            assert '2' in smith.periods_need_covered  # From duplicate entry
            
        finally:
            os.unlink(temp_file.name)

class TestEdgeCases:
    """Test edge cases in schedule parsing"""
    
    def test_missing_columns(self):
        """Test schedule with missing required columns"""
        df = pd.DataFrame(columns=['Name'])  # Missing Need Coverage and period columns
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        
        try:
            teachers, error = parseSchedule(temp_file.name)
            assert error is None
            assert teachers == {}
            
        finally:
            os.unlink(temp_file.name)
    
    def test_malformed_csv(self):
        """Test handling malformed CSV"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        temp_file.write(b'Name,Need Coverage\n"Smith, John",1,2,3\n"Doe, Jane",4,5,6,7,8')  # Uneven columns
        temp_file.close()
        
        try:
            teachers, error = parseSchedule(temp_file.name)
            # Should handle gracefully
            assert isinstance(teachers, dict)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_empty_coverage_needs(self):
        """Test teachers with no coverage needs"""
        df = pd.DataFrame({
            'Name': ['Smith, John', 'Doe, Jane'],
            'Need Coverage': ['', 'nan'],
            '1st': ['Class', 'Class'],
            '2nd': ['Class', 'Class'],
            '3rd': ['Class', 'Class'],
            '4th': ['Class', 'Class'],
            '5th': ['Lunch', 'Lunch'],
            '6th': ['Class', 'Class'],
            '7th': ['Class', 'Class'],
            '8th': ['Class', 'Class'],
            '9th': ['Plan', 'Plan'],
            '10th': ['Class', 'Class'],
            '11th': ['Class', 'Class'],
        })
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        
        try:
            teachers, error = parseSchedule(temp_file.name)
            
            # Should create teachers but they won't need coverage
            assert len(teachers) == 2
            smith = teachers['Smith, John']
            assert len(smith.periods_need_covered) == 0
            assert len(smith.periods_need_covered_CT) == 0
            
        finally:
            os.unlink(temp_file.name)
