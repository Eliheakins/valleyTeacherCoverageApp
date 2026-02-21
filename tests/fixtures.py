"""
Test fixtures and utilities for Valley Teacher Coverage App tests
"""

import pytest
import pandas as pd
import tempfile
import os
from main import Teacher, add_ordinal_suffix

@pytest.fixture
def sample_schedule_df():
    """Create a sample schedule DataFrame for testing"""
    columns = ['Name', 'Need Coverage'] + [add_ordinal_suffix(i) for i in range(1, 12)]
    data = [
        ['Smith, John', '1,3,5', 'Class', 'Class CT Doe', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Plan', 'Class', 'Class'],
        ['Doe, Jane', '2,4,6', 'Class CT Smith', 'Class', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Plan', 'Class', 'Class'],
        ['Brown, Bob', '1,4,11 CT-2,5/6,8/9,10', 'Class', 'Class', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Plan', 'Class', 'Class'],
        ['Wilson, Alice', '1,2,4,5/6,8/9,11', 'Class', 'Class', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Plan', 'Class', 'Class'],
    ]
    return pd.DataFrame(data, columns=columns)

@pytest.fixture
def sample_teachers():
    """Create sample teacher objects"""
    teachers = {
        'Smith, John': Teacher('Smith, John', ['1', '3', '5']),
        'Doe, Jane': Teacher('Doe, Jane', ['2', '4', '6']),
        'Brown, Bob': Teacher('Brown, Bob', ['1', '4', '11']),
        'Wilson, Alice': Teacher('Wilson, Alice', ['1', '2', '4', '5/6', '8/9', '11']),
    }
    
    # Add CT periods
    teachers['Brown, Bob'].periods_need_covered_CT = ['2', '5/6', '8/9', '10']
    
    return teachers

@pytest.fixture
def temp_schedule_file(sample_schedule_df):
    """Create a temporary schedule file"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    sample_schedule_df.to_excel(temp_file.name, index=False)
    yield temp_file.name
    # Cleanup
    os.unlink(temp_file.name)

@pytest.fixture
def temp_csv_schedule_file(sample_schedule_df):
    """Create a temporary CSV schedule file"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
    sample_schedule_df.to_csv(temp_file.name, index=False)
    yield temp_file.name
    # Cleanup
    os.unlink(temp_file.name)

@pytest.fixture
def temp_coverage_tracker():
    """Create a temporary coverage tracker file"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.write('{}')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    os.unlink(temp_file.name)

@pytest.fixture
def mock_gui_app():
    """Create a mock GUI application for testing"""
    class MockApp:
        def __init__(self):
            self.schedule_filepath = None
            self.teacherObjects = {}
            self.date = "2026-02-20"
            self.evenDay = False
            
        def update_selected_count(self):
            pass
            
        def open_file_dialog(self):
            pass
    
    return MockApp()

# Test data sets
CT_TEST_DATA = [
    # (entry, expected_ct, description)
    ("Class CT Smith", True, "Standard CT format"),
    ("CT Johnson", True, "Simple CT format"),
    ("Class CT", True, "CT without name"),
    ("CT-Davis", True, "CT with dash"),
    ("(CT) Wilson", True, "CT in parentheses"),
    ("Lunch", False, "Non-CT entry"),
    ("Faculty", False, "False positive check"),
    ("Study Hall", False, "Another false positive"),
]

NAME_MATCHING_DATA = [
    # (entry, target_teacher, teacher_list, expected, description)
    # Note: These test the matching logic with realistic patterns
    ("class ct smith", "Smith, John", ["Smith, John", "Johnson, Mary"], True, "Last name match in lowercase"),
    ("class ct john", "Smith, John", ["Smith, John", "Johnson, Mary"], True, "First name match in lowercase"),
    ("class ct smith", "Johnson, Mary", ["Smith, John", "Johnson, Mary"], False, "Wrong teacher should not match"),
    ("class ct unknown", "Smith, John", ["Smith, John", "Johnson, Mary"], False, "Non-existent teacher should not match"),
]

COVERAGE_TEST_DATA = [
    # (teacher_out, ct_periods, expected_behavior, description)
    ("Smith, John", ["2"], "ct_present", "CT teacher present"),
    ("Doe, Jane", ["1"], "both_out", "Both teachers out"),
    ("Brown, Bob", ["7"], "no_ct_found", "No CT teacher found"),
    ("Wilson, Alice", ["5/6"], "split_period", "Split period with CT"),
]

# Utility functions for tests
def create_teacher_with_periods(name, regular_periods=None, ct_periods=None, is_out=False):
    """Helper to create teacher with specific periods"""
    teacher = Teacher(name, regular_periods or [])
    if ct_periods:
        teacher.periods_need_covered_CT = ct_periods
    teacher.is_out = is_out
    return teacher

def create_test_schedule_with_real_teachers():
    """Create a realistic schedule with actual teacher names for CT testing"""
    columns = ['Name', 'Need Coverage'] + [add_ordinal_suffix(i) for i in range(1, 12)]
    
    # Create realistic teacher data with CT assignments
    # Columns: Name, Need Coverage, 1st, 2nd, 3rd, 4th, 5th, 6th, 7th, 8th, 9th, 10th, 11th
    data = [
        ['Barr, Ryann', '1,4,5/6,8/9,11 CT-2,10', 'Class', 'Class CT Costello', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Class', 'Class CT Costello', 'Class'],
        ['Costello, Elizabeth', '1,3,5', 'Class CT Ryann', 'Class', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Class', 'Class', 'Class'],
        ['Smith, John', '2,4,6', 'Class', 'Class', 'Class', 'Class', 'Lunch', 'Class', 'Class', 'Class', 'Class', 'Class', 'Class'],
    ]
    
    return pd.DataFrame(data, columns=columns)

def create_schedule_with_ct(ct_assignments):
    """Create schedule DataFrame with specific CT assignments"""
    columns = ['Name', 'Need Coverage'] + [add_ordinal_suffix(i) for i in range(1, 12)]
    data = []
    
    # Add base teachers
    teachers = ['Teacher A', 'Teacher B', 'Teacher C', 'Teacher D']
    for teacher in teachers:
        row = [teacher, ''] + [''] * 11
        data.append(row)
    
    # Add CT assignments
    for period, ct_teachers in ct_assignments.items():
        period_idx = int(period) if period.isdigit() else 0
        if 1 <= period_idx <= 11:
            for i, row in enumerate(data):
                if i < len(ct_teachers) and ct_teachers[i]:
                    row[period_idx + 1] = f"Class CT {ct_teachers[i]}"
    
    return pd.DataFrame(data, columns=columns)
