"""
Unit tests for coverage assignment logic
"""

import pytest
import tempfile
import os
from main import find_and_assign, determineCoverage_and_save, _classify_duty, _get_duty_list, Teacher

class TestCoverageAssignment:
    """Test coverage assignment logic"""
    
    def test_find_and_assign_iss_fallback(self):
        """Test ISS assignment as fallback"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
            'Teacher B': Teacher('Teacher B', ['1', '2', '3']),  # Will add ISS periods
            'Teacher C': Teacher('Teacher C', ['4', '5', '6']),
        }
        # Manually add ISS periods to Teacher B
        teachers['Teacher B'].iss_periods_available = ['1', '2']
        
        # Teacher A is out, needs coverage for period 1
        # Only Teacher B has ISS availability
        sorted_available = [('Teacher B', 0), ('Teacher C', 0)]
        coverage_data = {'Teacher B': {'times_covered': 0, 'coverage_log': []}}
        
        result = find_and_assign('1', teachers, sorted_available, coverage_data, False)
        
        assert result[0] == 'Teacher B'
        assert result[1] == True  # ISS covered
        assert '1' not in teachers['Teacher B'].iss_periods_available
    
    def test_find_and_assign_no_availability(self):
        """Test when no teacher is available"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
            'Teacher B': Teacher('Teacher B', ['4', '5', '6']),
        }
        
        # Need coverage for period 7, but no one has it
        sorted_available = [('Teacher A', 0), ('Teacher B', 0)]
        coverage_data = {}
        
        result = find_and_assign('7', teachers, sorted_available, coverage_data, False)
        
        assert result[0] is None
        assert result[1] == False
        assert result[2] == False
    
    def test_even_day_logic(self):
        """Test even/odd day availability logic"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),  # Odd day only
            'Teacher B': Teacher('Teacher B', ['1', '2', '3']),  # Even day only
            'Teacher C': Teacher('Teacher C', ['1', '4', '7']),  # Both
        }
        # Manually add day-specific periods
        teachers['Teacher A'].oddDayPeriods_available = ['4', '5', '6']
        teachers['Teacher B'].evenDayPeriods_available = ['1', '2', '3']
        teachers['Teacher B'].oddDayPeriods_available = ['4', '5', '6']
        teachers['Teacher C'].evenDayPeriods_available = ['2', '5', '8']
        teachers['Teacher C'].oddDayPeriods_available = ['1', '4', '7']
        
        # Even day, need coverage for period 2
        sorted_available = [('Teacher A', 0), ('Teacher B', 0), ('Teacher C', 0)]
        coverage_data = {'Teacher B': {'times_covered': 0, 'coverage_log': []}}
        
        result = find_and_assign('2', teachers, sorted_available, coverage_data, True)  # Even day
        
        assert result[0] == 'Teacher B'  # Should get even day teacher
        assert '2' not in teachers['Teacher B'].evenDayPeriods_available

class TestDutyClassification:
    """Test duty type classification"""
    
    @pytest.mark.parametrize("duty_raw,expected", [
        ("iss smith", 'iss'),
        ("smith iss", 'iss'),
        ("class - even days", 'even'),
        ("class - odd days", 'odd'),
        ("class - hall duty", 'other'),
        ("class - res", 'other'),
        ("regular class", 'standard'),
        ("", 'standard'),
    ])
    def test_classify_duty(self, duty_raw, expected):
        """Test duty type classification"""
        result = _classify_duty(duty_raw)
        assert result == expected

class TestDutyLists:
    """Test duty list retrieval"""
    
    def test_get_duty_list(self):
        """Test getting correct duty list for teacher"""
        teacher = Teacher('Test Teacher', ['1', '2'])
        # Manually add duty periods
        teacher.evenDayPeriods_available = ['3', '4']
        teacher.oddDayPeriods_available = ['5', '6']
        teacher.iss_periods_available = ['7', '8']
        teacher.otherDutyPeriods_available = ['9', '10']
        
        assert _get_duty_list(teacher, 'standard') == teacher.periods_available
        assert _get_duty_list(teacher, 'even') == teacher.evenDayPeriods_available
        assert _get_duty_list(teacher, 'odd') == teacher.oddDayPeriods_available
        assert _get_duty_list(teacher, 'iss') == teacher.iss_periods_available
        assert _get_duty_list(teacher, 'other') == teacher.otherDutyPeriods_available

class TestCoverageCalculation:
    """Test end-to-end coverage calculation"""
    
    def test_determine_coverage_basic(self, temp_coverage_tracker):
        """Test basic coverage calculation"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
            'Teacher B': Teacher('Teacher B', ['4', '5', '6']),
            'Teacher C': Teacher('Teacher C', ['1', '4', '7']),
        }
        
        teachers['Teacher A'].is_out = True
class TestCoverageEdgeCases:
    """Test edge cases in coverage calculation"""
    
    def test_no_teachers_out(self, temp_coverage_tracker):
        """Test when no teachers are out"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
            'Teacher B': Teacher('Teacher B', ['4', '5', '6']),
        }
        
        result = determineCoverage_and_save(teachers, '2026-02-20', temp_coverage_tracker, False)
        
        # Should have date but no assignments
        assert 'Date: 2026-02-20' in result
        assert len(result.split('\n')) == 2  # Just date line and empty line
    
    def test_all_teachers_out(self, temp_coverage_tracker):
        """Test when all teachers are out"""
        teachers = {
            'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
            'Teacher B': Teacher('Teacher B', ['4', '5', '6']),
        }
        
        teachers['Teacher A'].is_out = True
        teachers['Teacher B'].is_out = True
        
        result = determineCoverage_and_save(teachers, '2026-02-20', temp_coverage_tracker, False)
        
        # Should show no available teachers
        assert 'No available teacher' in result
    
    def test_corrupted_tracker_file(self):
        """Test handling of corrupted coverage tracker"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.write('invalid json data')
        temp_file.close()
        
        try:
            teachers = {
                'Teacher A': Teacher('Teacher A', ['1', '2', '3']),
                'Teacher B': Teacher('Teacher B', ['4', '5', '6']),
            }
            
            teachers['Teacher A'].is_out = True
            teachers['Teacher A'].periods_need_covered = ['1']
            
            # Should handle corrupted file gracefully
            result = determineCoverage_and_save(teachers, '2026-02-20', temp_file.name, False)
            assert 'Date: 2026-02-20' in result
            
        finally:
            os.unlink(temp_file.name)
