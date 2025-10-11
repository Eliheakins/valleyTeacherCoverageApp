import dearpygui.dearpygui as dpg
import datetime
import json
import os
import pandas as pd
import sys
from pathlib import Path

# --- CONFIGURATION CONSTANTS ---
SCHEDULE_FILENAME = "Coverage_Schedule.xlsx"

# Get proper paths for bundled vs development mode
def get_app_data_dir():
    """Returns a writable directory for app data (config, outputs)."""
    if sys.platform == "darwin":  # macOS
        app_data = Path.home() / "Library" / "Application Support" / "ValleyCoverageApp"
    elif sys.platform == "win32":  # Windows
        app_data = Path(os.getenv("APPDATA", Path.home())) / "ValleyCoverageApp"
    else:  # Linux/other
        app_data = Path.home() / ".valleycoverageapp"

    # Create the directory if it doesn't exist
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data

# Set config file path to writable location
APP_DATA_DIR = get_app_data_dir()
CONFIG_FILENAME = str(APP_DATA_DIR / "config.json")
# -------------------------------

# --- CONFIGURATION MANAGEMENT FUNCTIONS ---

def load_config():
    """Loads settings from config.json or returns defaults if not found."""
    default_config = {
        "SCHEDULE_FILE_PATH": None,
        # Future settings can be added here
    }
    try:
        if os.path.exists(CONFIG_FILENAME):
            with open(CONFIG_FILENAME, 'r') as f:
                config = json.load(f)
                # Ensure all default keys exist, in case the config file is old
                return {**default_config, **config} 
        return default_config
    except json.JSONDecodeError:
        print(f"Warning: {CONFIG_FILENAME} is corrupt. Using default settings.")
        return default_config
    except Exception as e:
        print(f"Error loading config: {e}. Using default settings.")
        return default_config

def save_config(config):
    """Saves the current configuration to config.json."""
    try:
        with open(CONFIG_FILENAME, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

# ------------------------------------------

class Teacher:
    def __init__(self, name, periods_need_covered):
        self.name= name.strip()
        self.is_out = False
        self.periods_need_covered = periods_need_covered
        self.periods_available = []
        self.periods_need_covered_CT = []
        self.iss_periods_available = []
        self.otherDutyPeriods_available = [] 
        self.evenDayPeriods_available = []
        self.oddDayPeriods_available = []

class TeacherCoverageApp:
    def __init__(self, schedule_filepath):
        self.date = ""
        # The schedule_filepath is an absolute path passed from main()
        self.schedule_filepath = schedule_filepath 
        self.teacherObjects, self.critical_error_message = parseSchedule(schedule_filepath) 
        self.evenDay = False

    def validate_and_proceed(self):
        date_string = dpg.get_value("date_input")
        
        # 1. Check Date Format
        try:
            datetime.date.fromisoformat(date_string)
            self.date = date_string
        except ValueError:
            with dpg.window(label="Error", modal=True, no_resize=True, no_close=True) as popup_window:
                dpg.add_text("Invalid date format. Please use YYYY-MM-DD.")
                dpg.add_button(label="Ok", callback=lambda: dpg.delete_item(popup_window))
            return # Stop execution if date is invalid

        # 2. Check if at least one teacher is selected
        selected_teachers_count = 0
        for name in self.teacherObjects.keys():
            if dpg.get_value(f"teacher_{name}"):
                selected_teachers_count += 1
        
        if selected_teachers_count == 0:
            with dpg.window(label="Warning", modal=True, no_resize=True, no_close=True) as popup_window:
                dpg.add_text("Please select at least one teacher who is out.")
                dpg.add_button(label="Ok", callback=lambda: dpg.delete_item(popup_window))
            return # Stop execution if no teacher is selected

        # If validation passes, proceed to calculation
        self.receiveValues_and_stop()

    def receiveValues_and_stop(self):
        for name in self.teacherObjects.keys():
            self.teacherObjects[name].is_out = dpg.get_value(f"teacher_{name}")
        self.evenDay = dpg.get_value("even_day_checkbox")
        dpg.stop_dearpygui() # Stops DPG loop and returns control to main to run logic

    def clear_all_teachers(self):
        """Resets all teacher checkboxes to False."""
        for name in self.teacherObjects.keys():
            dpg.set_value(f"teacher_{name}", False)
            
    # --- MODIFIED: ADDED BUTTON CALLBACK TO RE-OPEN FILE DIALOG ---
    def open_file_dialog(self):
        dpg.show_item("file_dialog_tag")

    def create_gui(self):
        dpg.create_context()
        
        # Set Global Font Scale to 2.0 (Twice the size)
        dpg.set_global_font_scale(2.0)

        # Define custom theme for darker colors
        with dpg.theme(tag="my_custom_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 25, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 10)

        with dpg.value_registry():
            dpg.add_string_value(default_value=str(datetime.date.today()), tag="date_input")
            dpg.add_bool_value(default_value=False, tag="even_day_checkbox")
            # Initialize bool sources for each teacher's checkbox state
            for name in self.teacherObjects.keys():
                dpg.add_bool_value(default_value=False, tag=f"teacher_{name}")

        dpg.create_viewport(title='Teacher Coverage', width=800, height=800)
        
        with dpg.window(tag="main_window", label="main_window", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=800, height=800):
            with dpg.group(tag="main_group", horizontal=False):
                dpg.add_text("Valley Teacher Coverage", tag="title_text")
                dpg.add_spacer(height=5)
                
                # --- ADDED: Display current schedule file path ---
                dpg.add_text(f"Schedule File: {os.path.basename(self.schedule_filepath)}", tag="file_status")
                dpg.add_button(label="Change Schedule File", callback=self.open_file_dialog)
                dpg.add_spacer(height=10)
                # ------------------------------------------------
                
                dpg.add_text("Teachers Out:", tag="teachers_label")
                dpg.add_spacer(height=5)
                
                # Table for clean, two-column layout of checkboxes
                with dpg.table(header_row=False, resizable=True, policy=dpg.mvTable_SizingStretchSame, borders_outerV=False, borders_innerV=False, borders_outerH=False, borders_innerH=True):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    teacher_names = list(self.teacherObjects.keys())
                    for i in range(0, len(teacher_names), 2):
                        with dpg.table_row():
                            with dpg.table_cell():
                                dpg.add_checkbox(label=teacher_names[i], source=f"teacher_{teacher_names[i]}")

                            if i + 1 < len(teacher_names):
                                with dpg.table_cell():
                                    dpg.add_checkbox(label=teacher_names[i+1], source=f"teacher_{teacher_names[i+1]}")
                            
                dpg.add_spacer(height=5)
                
                # Add Clear All button
                dpg.add_button(label="Clear All Selections", callback=self.clear_all_teachers, width=-1)
                dpg.add_spacer(height=5)

                dpg.add_text("Date (YYYY-MM-DD)")
                dpg.add_input_text(source="date_input", width=250)
                dpg.add_spacer(height=5)

                dpg.add_checkbox(label="Even Day", source="even_day_checkbox")
                dpg.add_spacer(height=5)

                dpg.add_button(label="Submit", callback=self.validate_and_proceed)

        dpg.bind_item_theme("main_window", "my_custom_theme")
        dpg.set_primary_window("main_window", True)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

# --- FILE DIALOG CALLBACK ---

def file_dialog_callback(sender, app_data, user_data):
    """
    Handles the result of the file dialog. Runs application logic to save
    the path and reload the schedule data if successful.
    """
    selected_file_path = app_data.get('file_path_name')
    
    if selected_file_path and os.path.exists(selected_file_path):
        # 1. Update Configuration
        config = load_config()
        config['SCHEDULE_FILE_PATH'] = selected_file_path
        save_config(config)
        
        # 2. Stop DPG so main() can restart the application logic with the new path
        dpg.stop_dearpygui()
    else:
        # User cancelled or selected an invalid file, just close the dialog
        dpg.configure_item("file_dialog_tag", show=False)


# --- INITIAL FILE SELECTION GUI ---

def get_initial_file_path():
    """
    Checks config for file path. If not found, runs a temporary DPG context 
    with a file dialog to get the path from the user.
    """
    config = load_config()
    file_path = config.get("SCHEDULE_FILE_PATH")

    if file_path and os.path.exists(file_path):
        return file_path, None

    # --- Run File Selection GUI ---
    dpg.create_context()
    dpg.set_global_font_scale(2.0)
    dpg.create_viewport(title='Select Schedule File', width=600, height=200)

    # Use a temporary window for instructions
    with dpg.window(label="Schedule File Required", no_resize=True, no_close=True, no_title_bar=True, pos=(0, 0), width=600, height=200):
        dpg.add_text("Please locate and select your 'Coverage_Schedule.xlsx' file.", wrap=550)
        dpg.add_spacer(height=10)
        dpg.add_button(label="Browse for File", callback=lambda: dpg.show_item("file_dialog_tag"))

    # File dialog configuration
    with dpg.file_dialog(
        directory_selector=False, 
        show=False, 
        callback=file_dialog_callback, 
        tag="file_dialog_tag", 
        width=700, 
        height=400
    ):
        dpg.add_file_extension(".xlsx", color=(150, 255, 150, 255))
        dpg.add_file_extension("", color=(255, 255, 255, 255)) 

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui() 
    dpg.destroy_context()

    # Re-read config after the GUI stops (i.e., after a file was successfully selected/saved)
    new_config = load_config()
    final_path = new_config.get("SCHEDULE_FILE_PATH")
    
    if final_path and os.path.exists(final_path):
        return final_path, None
    else:
        # If the user closes the dialog without selecting a file
        return None, "Application closed. Please select the schedule file to proceed."


# --- CORE LOGIC FUNCTIONS (Unchanged from previous version) ---

def add_ordinal_suffix(number):
    """Adds the correct ordinal suffix (st, nd, rd, th) to a given number."""
    try:
        digit = int(number)
    except ValueError:
        return str(number)

    if 10 <= digit % 100 <= 20:
        suffix = "th"
    else:
        last_digit = digit % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"
    return str(number) + suffix

def unique_and_ordered(sequence):
    """Removes duplicates while preserving the order of first appearance."""
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

def sort_periods(period_sequence):
    """Sorts periods numerically, handling split periods like '5/6'."""
    
    def sort_key(item):
        period_str = item[0] if isinstance(item, tuple) else item
        try:
            return int(period_str.split('/')[0])
        except (ValueError, IndexError):
            return 99 

    return sorted(period_sequence, key=sort_key)

def check_coteachers(teachers, filepath):
    """
    Checks the schedule for co-teachers (CT). If a co-teacher for a period is 
    NOT out, the period is removed from the principal teacher's CT coverage list.
    """
    schedule_df = pd.read_excel(filepath, sheet_name=0) 
    for teacher_key in teachers:
        teacher = teachers[teacher_key]
        if not teacher.is_out:
            continue
        for period in teacher.periods_need_covered_CT:
            if '/' in period:
                period1, period2 = period.split('/')
                check_periods = [period1.strip(), period2.strip()]
            else:
                check_periods = [period.strip()]
            
            for check_period in check_periods:
                period_suffex=add_ordinal_suffix(check_period)
                if period_suffex in schedule_df.columns:
                    period_data = schedule_df[period_suffex].dropna().astype(str).str.strip().str.lower().tolist()
                    coteacher_name = None
                    for entry in period_data:
                        if 'ct' in entry:
                            for name in teachers.keys():
                                if name.strip().lower() in entry.lower():
                                    if name != teacher.name:
                                        coteacher_name = name
                                        break
                            if coteacher_name:
                                break

                    if coteacher_name:
                        if teachers[coteacher_name].is_out:
                            if period in teachers[coteacher_name].periods_need_covered_CT:
                                teachers[coteacher_name].periods_need_covered_CT.remove(period)
                            
                            if period in teacher.periods_need_covered_CT:
                                teacher.periods_need_covered_CT.remove(period)
                                teacher.periods_need_covered.append(period)
                        else:
                            if period in teacher.periods_need_covered_CT:
                                teacher.periods_need_covered_CT.remove(period)


def parseSchedule(filepath):
    """
    Parses the schedule file and returns a tuple: (teachers_dict, error_message or None).
    """
    try:
        schedule_df = pd.read_excel(filepath, sheet_name=0)
    except FileNotFoundError:
        # This error should now be rare if the file selection logic works, 
        # but kept for robustness.
        return {}, f"File not found at saved path: '{filepath}'. Please re-select the file."
    except Exception as e:
        return {}, f"Failed to read the schedule file. Details: {type(e).__name__}: {e}"

    teachers = {}
    
    for index, row in schedule_df.iterrows():
        name = row.get('Name')
        if pd.isna(name) or not name:
            continue
        if '(' in name:
            name = name.split('(')[0].strip()

        need_coverage_str = str(row.get('Need Coverage'))
        needs_coverage_CT = []
        needs_coverage = []
        
        if "CT" in need_coverage_str:
            substrings= need_coverage_str.split(" CT-")
            periods_list = [s.strip() for s in substrings[0].split(",") if s.strip()]
            needs_coverage = unique_and_ordered(periods_list)
            
            if len(substrings) > 1 and substrings[1].strip():
                periods_ct_list = [s.strip() for s in substrings[1].split(",") if s.strip()]
                needs_coverage_CT = unique_and_ordered(periods_ct_list)
        else:
            periods_list = [s.strip() for s in need_coverage_str.split(',') if s.strip()]
            needs_coverage = unique_and_ordered(periods_list)
        
        teacher = Teacher(name, sort_periods(needs_coverage)) 
        teacher.periods_need_covered_CT = sort_periods(needs_coverage_CT)
        teachers[name] = teacher
        
    for period in range(1, 12):
        period_suffex=add_ordinal_suffix(period)
        duty_col = f'Duty {period_suffex}'
        if duty_col in schedule_df.columns:
            duty_assignments_raw = [str(entry).strip().lower() for entry in schedule_df[duty_col].dropna()]
            
            for duty_raw in duty_assignments_raw:
                duty_raw = duty_raw.strip().lower()
                
                iss = "iss" in duty_raw
                evenDay = "even days" in duty_raw
                oddDay = "odd days" in duty_raw
                otherDuty = "-" in duty_raw and not iss and not evenDay and not oddDay

                for teacher_name, teacher in teachers.items():
                    teacher_full_name_lower = teacher_name.strip().lower()
                    
                    if teacher_full_name_lower in duty_raw:
                        period_to_add = str(period)
                        
                        if iss:
                            teacher.iss_periods_available.append(period_to_add)
                        elif evenDay:
                            teacher.evenDayPeriods_available.append(period_to_add)
                        elif oddDay:
                            teacher.oddDayPeriods_available.append(period_to_add)
                        elif otherDuty:
                            teacher.otherDutyPeriods_available.append(period_to_add)
                        else:
                            teacher.periods_available.append(period_to_add)
                            
    return teachers, None

def determineCoverage_and_save(teachers, date, coverage_tracker_json, evenDay):
    """
    Calculates coverage, updates the JSON tracker, saves to a text file, and 
    returns the coverage text output.
    """
    outputString = f"Date: {date}\n"
    
    if os.path.exists(coverage_tracker_json) and os.path.getsize(coverage_tracker_json) > 0:
        try:
            with open(coverage_tracker_json, 'r') as f:
                coverage_data = json.load(f)
        except json.JSONDecodeError:
            coverage_data = {}
    else:
        coverage_data = {}

    for name in teachers.keys():
        if name not in coverage_data:
            coverage_data[name] = {'times_covered': 0, 'coverage_log': []}

    teachers_out = [name for name, teacher in teachers.items() if teacher.is_out]
    
    sorted_available_teachers = sorted([
        (name, data['times_covered']) for name, data in coverage_data.items()
        if name not in teachers_out and name in teachers
    ], key=lambda x: x[1])

    for teacher_out_name in teachers_out:
        outputString += f"{teacher_out_name}:\n"
        teacher_out_obj = teachers[teacher_out_name]

        all_periods_to_cover_raw = []
        for period in teacher_out_obj.periods_need_covered:
            all_periods_to_cover_raw.append((period, False)) 
        for period in teacher_out_obj.periods_need_covered_CT:
            all_periods_to_cover_raw.append((period, True)) 
        
        all_periods_to_cover = sort_periods(all_periods_to_cover_raw) 
        
        def find_and_assign(p1, p2=None):
            """Core logic to find the least-used available teacher for a period (or split period)."""
            temp_assigned_teacher_name = None
            temp_iss_covered = False
            temp_otherDuty_covered = False
            
            # 1. Check Standard/Day-Dependent Availability
            for name, _ in sorted_available_teachers:
                teacher = teachers[name]
                
                temp_available = set(teacher.periods_available)
                if evenDay:
                    temp_available.update(teacher.evenDayPeriods_available)
                else:
                    temp_available.update(teacher.oddDayPeriods_available)
                
                periods_to_check = [p1]
                if p2: 
                    periods_to_check.append(p2)
                
                if all(p in temp_available for p in periods_to_check):
                    for p in periods_to_check:
                        if p in teacher.periods_available:
                            teacher.periods_available.remove(p)
                        elif evenDay and p in teacher.evenDayPeriods_available:
                            teacher.evenDayPeriods_available.remove(p)
                        elif not evenDay and p in teacher.oddDayPeriods_available:
                            teacher.oddDayPeriods_available.remove(p)
                            
                    temp_assigned_teacher_name = name
                    return temp_assigned_teacher_name, temp_iss_covered, temp_otherDuty_covered
            
            # 2. Check ISS Availability (Fallback)
            for name, _ in sorted_available_teachers:
                teacher = teachers[name]
                if (p2 and p1 in teacher.iss_periods_available and p2 in teacher.iss_periods_available) or \
                   (not p2 and p1 in teacher.iss_periods_available):
                    
                    if p1 in teacher.iss_periods_available: 
                        teacher.iss_periods_available.remove(p1)
                    if p2 and p2 in teacher.iss_periods_available: 
                        teacher.iss_periods_available.remove(p2)
                        
                    temp_assigned_teacher_name = name
                    temp_iss_covered = True
                    return temp_assigned_teacher_name, temp_iss_covered, temp_otherDuty_covered
                    
            # 3. Check Other Duty Availability (Fallback)
            for name, _ in sorted_available_teachers:
                teacher = teachers[name]
                if (p2 and p1 in teacher.otherDutyPeriods_available and p2 in teacher.otherDutyPeriods_available) or \
                   (not p2 and p1 in teacher.otherDutyPeriods_available):
                    
                    if p1 in teacher.otherDutyPeriods_available: 
                        teacher.otherDutyPeriods_available.remove(p1)
                    if p2 and p2 in teacher.otherDutyPeriods_available: 
                        teacher.otherDutyPeriods_available.remove(p2)

                    temp_assigned_teacher_name = name
                    temp_otherDuty_covered = True
                    return temp_assigned_teacher_name, temp_iss_covered, temp_otherDuty_covered

            return None, False, False

        for period, is_ct in all_periods_to_cover:
            
            if '/' in period:
                period1, period2 = period.split('/')
                assigned_teacher_name, iss_covered, otherDuty_covered = find_and_assign(period1, period2)
            else:
                assigned_teacher_name, iss_covered, otherDuty_covered = find_and_assign(period)
            
            if assigned_teacher_name:
                duty_tag = ""
                if iss_covered:
                    duty_tag = " (Close ISS)"
                elif otherDuty_covered: 
                    duty_tag = " (OTHER DUTY)"
                
                ct_prefix = "   (CT)" if is_ct else "   "

                outputString += f"{ct_prefix}{duty_tag} {period} {assigned_teacher_name}\n"

                coverage_data[assigned_teacher_name]['times_covered'] += 1
                new_log_entry = {
                    'date': date,
                    'covered_for': teacher_out_name,
                    'period': period
                }
                coverage_data[assigned_teacher_name]['coverage_log'].append(new_log_entry)
            else:
                if is_ct:
                    outputString += f"   (CT) {period} No available teacher\n"
                else:
                    outputString += f"   {period} No available teacher\n"

    with open(coverage_tracker_json, 'w') as f:
        json.dump(coverage_data, f, indent=4)

    # Save coverage output to app data directory
    output_file = APP_DATA_DIR / f"coverage_{date}.txt"
    with open(output_file, 'w') as f:
        f.write(outputString)

    return outputString

def display_fatal_error_gui(error_message):
    dpg.create_context()
    
    dpg.set_global_font_scale(2.0)
            
    dpg.create_viewport(title='Critical Error', width=600, height=250)
    
    with dpg.window(label="Error", modal=True, no_resize=True, no_close=True, width=600, height=250):
        dpg.add_text("A critical error occurred during schedule file loading.", color=(255, 100, 100, 255))
        dpg.add_spacer(height=10)
        dpg.add_text(error_message, wrap=550)
        dpg.add_spacer(height=10)
        dpg.add_button(label="Exit Application", callback=lambda: dpg.stop_dearpygui(), width=-1)
        
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def display_results_gui(results_text, date):
    """
    Displays the coverage results in a new DearPyGui window.
    """
    dpg.create_context()
    dpg.set_global_font_scale(1.5) 

    def copy_results_to_clipboard():
        dpg.set_clipboard_text(dpg.get_value("results_text_output"))
        with dpg.window(label="Copied", modal=True, no_resize=True, no_close=True, width=250) as popup:
            dpg.add_text("Results copied to clipboard!")
            dpg.add_button(label="OK", callback=lambda: dpg.delete_item(popup))
            
    dpg.create_viewport(title=f'Coverage Results - {date}', width=650, height=800)
    
    with dpg.window(tag="results_window", label="Coverage Results", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=650, height=800):
        dpg.add_text("Coverage Calculated Successfully!", color=(100, 255, 100, 255))
        dpg.add_spacer(height=5)
        
        dpg.add_input_text(
            tag="results_text_output", 
            default_value=results_text, 
            multiline=True, 
            readonly=True, 
            width=-1, 
            height=650
        )
        dpg.add_spacer(height=10)

        dpg.add_button(label="Copy to Clipboard", callback=copy_results_to_clipboard, width=-1)
        dpg.add_spacer(height=5)

        dpg.add_button(label="Close and Exit", callback=lambda: dpg.stop_dearpygui(), width=-1)

    dpg.set_primary_window("results_window", True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def main():
    
    # --- Reworked main loop to handle file path setting ---
    
    # This loop ensures the app re-runs if the user selects a new file path 
    # from the main GUI's "Change Schedule File" button.
    while True:
        # 1. Get the schedule file path (from config or user selection)
        schedule_file_path, initial_error = get_initial_file_path()

        if initial_error:
            # Only happens if the user closes the initial file selection GUI
            print(f"Exiting application: {initial_error}")
            return

        if not schedule_file_path:
            # Should not happen if get_initial_file_path works correctly, but safe guard.
            return

        # 2. Initialize the application object with the (potentially new) path
        app = TeacherCoverageApp(schedule_file_path)
        
        if app.critical_error_message:
            # Error reading the file at the chosen path
            display_fatal_error_gui(app.critical_error_message)
            # After showing the error, the user must re-select the file, 
            # so the loop continues to get_initial_file_path()
            continue 

        # 3. Run the main input GUI
        app.create_gui()
        
        # Check if the user closed the main GUI (app.date will be empty)
        if not app.date:
            return

        # Check if the user requested a file change (app.date will be set, but we handle it in file_dialog_callback)
        # If file_dialog_callback runs and saves a new path, it calls dpg.stop_dearpygui() which returns control here.
        # We rely on the `while True` loop to pick up the new path on the next iteration.

        # 4. Run coverage logic
        check_coteachers(app.teacherObjects, schedule_file_path)

        # Use app data directory for coverage tracker
        coverage_file = str(APP_DATA_DIR / "coverage_tracker.json")
        coverage_results_text = determineCoverage_and_save(app.teacherObjects, app.date, coverage_file, app.evenDay)

        # 5. Display the results in a new GUI window
        display_results_gui(coverage_results_text, app.date)
        
        # If the app reaches here, it means the user submitted data and viewed results. 
        # Since display_results_gui() ends with dpg.stop_dearpygui() (Exit), the program returns here.
        # We break the main loop to exit the program completely.
        break 


if __name__ == "__main__":
    main()
 