"""
Unit tests for CT (Co-Teaching) logic
"""

import pytest
from main import _is_ct_entry, check_coteachers
from tests.fixtures import (
    CT_TEST_DATA, create_teacher_with_periods, create_test_schedule_with_real_teachers,
    create_schedule_with_ct
)

class TestCTEntryDetection:
    """Test CT entry detection patterns"""
    
    @pytest.mark.parametrize("entry,expected,description", CT_TEST_DATA)
    def test_is_ct_entry(self, entry, expected, description):
        """Test various CT entry formats"""
        result = _is_ct_entry(entry)
        assert result == expected, f"Failed for {description}: {repr(entry)}"

class TestCTScenarios:
    """Test CT logic scenarios"""
    
    def test_ct_teacher_present(self):
        """Test Scenario 1: CT teacher present - no coverage needed"""
        # Create realistic schedule
        schedule_df = create_test_schedule_with_real_teachers()
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1', '4', '11'], ['2', '10'], is_out=True),
                'Costello, Elizabeth': create_teacher_with_periods('Costello, Elizabeth', ['1', '3', '5'], is_out=False),
                'Smith, John': create_teacher_with_periods('Smith, John', ['2', '4', '6'], is_out=False),
            }

            check_coteachers(teachers, temp_file.name)

            # Verify CT periods removed (Costello is present in schedule for periods 2 and 10)
            assert len(teachers['Barr, Ryann'].periods_need_covered_CT) == 0
            assert '2' not in teachers['Barr, Ryann'].periods_need_covered_CT
            assert '10' not in teachers['Barr, Ryann'].periods_need_covered_CT
            
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_both_teachers_out(self):
        """Test Scenario 2: Both teachers out - CT becomes regular coverage"""
        # Create realistic schedule
        schedule_df = create_test_schedule_with_real_teachers()
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1', '4', '11'], ['2', '10'], is_out=True),
                'Costello, Elizabeth': create_teacher_with_periods('Costello, Elizabeth', ['1', '3', '5'], is_out=True),
                'Smith, John': create_teacher_with_periods('Smith, John', ['2', '4', '6'], is_out=False),
            }

            check_coteachers(teachers, temp_file.name)

            # Verify CT converted to regular coverage for both
            assert len(teachers['Barr, Ryann'].periods_need_covered_CT) == 0
            assert '2' in teachers['Barr, Ryann'].periods_need_covered
            assert '10' in teachers['Barr, Ryann'].periods_need_covered
            assert hasattr(teachers['Barr, Ryann'], 'converted_ct_periods')
            assert '2' in teachers['Barr, Ryann'].converted_ct_periods
            
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_no_ct_found(self):
        """Test Scenario 3: No CT teacher found - keep CT need"""
        # Create schedule without CT assignments (just regular classes)
        import pandas as pd
        from main import add_ordinal_suffix
        
        columns = ['Name', 'Need Coverage'] + [add_ordinal_suffix(i) for i in range(1, 12)]
        data = [
            ['Barr, Ryann', '1,4,11 CT-2,10'] + ['Class'] * 11,  # No CT markers in schedule
            ['Costello, Elizabeth', '1,3,5'] + ['Class'] * 11,
        ]
        schedule_df = pd.DataFrame(data, columns=columns)
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1', '4', '11'], ['2', '10'], is_out=True),
                'Costello, Elizabeth': create_teacher_with_periods('Costello, Elizabeth', ['1', '3', '5'], is_out=False),
            }
            
            check_coteachers(teachers, temp_file.name)
            
            # Verify CT periods preserved since no CT teacher found in schedule
            assert '2' in teachers['Barr, Ryann'].periods_need_covered_CT
            assert '10' in teachers['Barr, Ryann'].periods_need_covered_CT
            
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_multiple_ct_teachers(self):
        """Test Scenario 4: Multiple CT teachers - one present, one out"""
        # Use realistic schedule where Costello is CT teacher
        schedule_df = create_test_schedule_with_real_teachers()
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1', '4', '11'], ['2', '10'], is_out=True),
                'Costello, Elizabeth': create_teacher_with_periods('Costello, Elizabeth', ['1', '3', '5'], is_out=False),  # Present
                'Smith, John': create_teacher_with_periods('Smith, John', ['2', '4', '6'], is_out=True),  # Out but not CT
            }

            check_coteachers(teachers, temp_file.name)

            # Should find Costello (present) and remove CT periods
            assert len(teachers['Barr, Ryann'].periods_need_covered_CT) == 0
            
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_split_periods_with_ct(self):
        """Test Scenario 5: Split periods with CT"""
        # Use realistic schedule with split period 5/6 CT
        import pandas as pd
        from main import add_ordinal_suffix
        
        columns = ['Name', 'Need Coverage'] + [add_ordinal_suffix(i) for i in range(1, 12)]
        data = [
            ['Barr, Ryann', '1,4,11 CT-5/6', 'Class', 'Class', 'Class', 'Class', 'Class CT Costello', 'Class CT Costello', 'Class', 'Class', 'Class', 'Class', 'Class'],
            ['Costello, Elizabeth', '1,3,5', 'Class', 'Class', 'Class', 'Class', 'Class CT Ryann', 'Class CT Ryann', 'Class', 'Class', 'Class', 'Class', 'Class'],
        ]
        schedule_df = pd.DataFrame(data, columns=columns)
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1', '4', '11'], ['5/6'], is_out=True),
                'Costello, Elizabeth': create_teacher_with_periods('Costello, Elizabeth', ['1', '3', '5'], is_out=False),
            }

            check_coteachers(teachers, temp_file.name)

            # Verify split CT period handled correctly
            assert len(teachers['Barr, Ryann'].periods_need_covered_CT) == 0
            
        finally:
            import os
            os.unlink(temp_file.name)

class TestCTErrorHandling:
    """Test CT logic error handling"""
    
    def test_empty_schedule(self):
        """Test handling of empty schedule"""
        import tempfile
        import pandas as pd
        
        empty_df = pd.DataFrame(columns=['Name'] + [f'{i}st' if i == 1 else f'{i}nd' if i == 2 else f'{i}rd' if i == 3 else f'{i}th' for i in range(1, 12)])
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        empty_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Test, Teacher': create_teacher_with_periods('Test, Teacher', ['1'], ['1'], is_out=True)
            }
            
            # Should not crash
            check_coteachers(teachers, temp_file.name)
            
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_invalid_file(self):
        """Test handling of invalid file path"""
        teachers = {
            'Test, Teacher': create_teacher_with_periods('Test, Teacher', ['1'], ['1'], is_out=True)
        }
        
        # Should not crash
        check_coteachers(teachers, 'nonexistent_file.xlsx')
    
    def test_teacher_not_in_schedule(self):
        """Test when teacher not found in schedule"""
        import tempfile
        
        ct_assignments = {'2nd': ['Costello, Elizabeth']}
        schedule_df = create_schedule_with_ct(ct_assignments)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        schedule_df.to_excel(temp_file.name, index=False)
        
        try:
            teachers = {
                'Barr, Ryann': create_teacher_with_periods('Barr, Ryann', ['1'], ['2'], is_out=True),
                'Unknown, Teacher': create_teacher_with_periods('Unknown, Teacher', ['1'], [], is_out=False),
            }
            
            check_coteachers(teachers, temp_file.name)
            
            # Should preserve CT period when teacher not found
            assert '2' in teachers['Barr, Ryann'].periods_need_covered_CT
            
        finally:
            import os
            os.unlink(temp_file.name)
