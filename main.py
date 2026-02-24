import dearpygui.dearpygui as dpg
import datetime
import json
import os
import pandas as pd
import re
import sys
from pathlib import Path

# --- CONFIGURATION CONSTANTS ---

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
        self.coverage_time_preference = None  # None = Full day, 'AM' = periods 1-4, 'PM' = periods 5-11

class TeacherCoverageApp:
    def __init__(self, schedule_filepath):
        self.date = ""
        # The schedule_filepath is an absolute path passed from main()
        self.schedule_filepath = schedule_filepath 
        self.teacherObjects, self.critical_error_message = parseSchedule(schedule_filepath) 
        self.evenDay = False
        self.file_changed = False

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
            # Get time preference and convert string "None" to Python None
            time_pref = dpg.get_value(f"teacher_time_pref_{name}")
            self.teacherObjects[name].coverage_time_preference = None if time_pref == "None" else time_pref
        self.evenDay = dpg.get_value("day_type_radio") == "Even Day"
        dpg.stop_dearpygui() # Stops DPG loop and returns control to main to run logic

    def clear_all_teachers(self):
        """Resets all teacher checkboxes to False and time preferences to None."""
        for name in self.teacherObjects.keys():
            dpg.set_value(f"teacher_{name}", False)
            dpg.set_value(f"teacher_time_pref_{name}", "None")
        self.update_selected_count()

    def toggle_time_preference(self, sender, app_data, user_data):
        """Cycles through time preference states: None -> AM -> PM -> None"""
        teacher_name = user_data
        current_pref = dpg.get_value(f"teacher_time_pref_{teacher_name}")
        
        # Cycle: None -> AM -> PM -> None
        if current_pref == "None":
            new_pref = "AM"
        elif current_pref == "AM":
            new_pref = "PM"
        else:
            new_pref = "None"
        
        dpg.set_value(f"teacher_time_pref_{teacher_name}", new_pref)
        self.update_time_pref_button_appearance(teacher_name)

    def update_time_pref_button_appearance(self, teacher_name):
        """Updates the button appearance based on current time preference"""
        current_pref = dpg.get_value(f"teacher_time_pref_{teacher_name}")
        
        if current_pref == "None":
            dpg.configure_item(f"time_pref_btn_{teacher_name}", label="Full")
            dpg.bind_item_theme(f"time_pref_btn_{teacher_name}", "am_pm_theme")
        elif current_pref == "AM":
            dpg.configure_item(f"time_pref_btn_{teacher_name}", label="AM")
            dpg.bind_item_theme(f"time_pref_btn_{teacher_name}", "am_pm_selected_theme")
        else:  # PM
            dpg.configure_item(f"time_pref_btn_{teacher_name}", label="PM")
            dpg.bind_item_theme(f"time_pref_btn_{teacher_name}", "am_pm_selected_theme")

    def update_selected_count(self, sender=None, app_data=None, user_data=None):
        """Updates the live selected teacher count label and button visibility."""
        # Update count
        count = sum(1 for name in self.teacherObjects.keys() if dpg.get_value(f"teacher_{name}"))
        label = f"{count} teacher{'s' if count != 1 else ''} selected"
        dpg.set_value("selected_count_text", label)
        
        # Update button visibility based on checkbox state
        for name in self.teacherObjects.keys():
            is_checked = dpg.get_value(f"teacher_{name}")
            if is_checked:
                dpg.show_item(f"time_pref_btn_{name}")
            else:
                dpg.hide_item(f"time_pref_btn_{name}")
            
    # --- MODIFIED: ADDED BUTTON CALLBACK TO RE-OPEN FILE DIALOG ---
    def open_file_dialog(self):
        dpg.configure_item("file_dialog_tag", user_data=self)
        dpg.show_item("file_dialog_tag")

    def create_gui(self):
        dpg.create_context()
        
        # Set Global Font Scale to 2.0 (Twice the size)
        dpg.set_global_font_scale(2.0)

        # Modern Slate/Navy Theme
        with dpg.theme(tag="modern_theme"):
            with dpg.theme_component(dpg.mvAll):
                # Main background - slate 900
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 23, 42, 255))
                # Text - slate 100
                dpg.add_theme_color(dpg.mvThemeCol_Text, (241, 245, 249, 255))
                # Borders - slate 700
                dpg.add_theme_color(dpg.mvThemeCol_Border, (51, 65, 85, 255))
                # Separator - slate 600
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (71, 85, 105, 255))
                # Frame background - slate 800
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 41, 59, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (51, 65, 85, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (71, 85, 105, 255))
                # Rounded corners everywhere
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 10)
                # Better padding
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 8, 6)

        # Primary accent button (sky blue)
        with dpg.theme(tag="primary_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (14, 165, 233, 255))  # Sky 500
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (56, 189, 248, 255))  # Sky 400
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (2, 132, 199, 255))  # Sky 600
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 10)

        # Secondary button (slate)
        with dpg.theme(tag="secondary_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (51, 65, 85, 255))  # Slate 700
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (71, 85, 105, 255))  # Slate 600
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 41, 59, 255))  # Slate 800
                dpg.add_theme_color(dpg.mvThemeCol_Text, (148, 163, 184, 255))  # Slate 400
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)

        # Time preference button (default state)
        with dpg.theme(tag="am_pm_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 41, 59, 255))  # Slate 800
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (51, 65, 85, 255))  # Slate 700
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (71, 85, 105, 255))  # Slate 600
                dpg.add_theme_color(dpg.mvThemeCol_Text, (148, 163, 184, 255))  # Slate 400
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)

        # Time preference button (selected state - emerald)
        with dpg.theme(tag="am_pm_selected_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (16, 185, 129, 255))  # Emerald 500
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (52, 211, 153, 255))  # Emerald 400
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (5, 150, 105, 255))  # Emerald 600
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)

        # Card/Child window theme
        with dpg.theme(tag="card_theme"):
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 41, 59, 255))  # Slate 800
                dpg.add_theme_color(dpg.mvThemeCol_Border, (51, 65, 85, 255))  # Slate 700
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

        # Checkbox theme
        with dpg.theme(tag="checkbox_theme"):
            with dpg.theme_component(dpg.mvCheckbox):
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (14, 165, 233, 255))  # Sky 500
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (51, 65, 85, 255))  # Slate 700
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (71, 85, 105, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (14, 165, 233, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)

        # Radio button theme
        with dpg.theme(tag="radio_theme"):
            with dpg.theme_component(dpg.mvRadioButton):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (51, 65, 85, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (71, 85, 105, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (14, 165, 233, 255))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (14, 165, 233, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)

        # Input text theme
        with dpg.theme(tag="input_theme"):
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 41, 59, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (51, 65, 85, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (51, 65, 85, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (241, 245, 249, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)

        with dpg.value_registry():
            dpg.add_string_value(default_value=str(datetime.date.today()), tag="date_input")
            dpg.add_string_value(default_value="Even Day", tag="day_type_radio")
            # Initialize bool sources for each teacher's checkbox state
            for name in self.teacherObjects.keys():
                dpg.add_bool_value(default_value=False, tag=f"teacher_{name}")
            # Initialize string values for each teacher's time preference (None, 'AM', 'PM')
            for name in self.teacherObjects.keys():
                dpg.add_string_value(default_value="None", tag=f"teacher_time_pref_{name}")

        dpg.create_viewport(title='Teacher Coverage', width=800, height=800)
        
        with dpg.window(tag="main_window", label="main_window", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=800, height=800):
            with dpg.group(tag="main_group", horizontal=False):
                # Modern header with accent color
                with dpg.group(horizontal=True):
                    dpg.add_text("Valley Teacher Coverage", tag="title_text", color=(56, 189, 248, 255))
                dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                # Schedule file info card (non-scrolling)
                with dpg.group() as file_card:
                    with dpg.group(horizontal=True):
                        dpg.add_text("Schedule:", color=(148, 163, 184, 255))
                        dpg.add_spacer(width=5)
                        dpg.add_text(f"{os.path.basename(self.schedule_filepath)}", tag="file_status")
                    dpg.add_spacer(height=5)
                    change_btn = dpg.add_button(label="Change Schedule File", callback=self.open_file_dialog)
                    dpg.bind_item_theme(change_btn, "secondary_btn_theme")
                dpg.bind_item_theme(file_card, "card_theme")
                dpg.add_spacer(height=15)

                # Teachers Out section header
                with dpg.group(horizontal=True):
                    dpg.add_text("Teachers Out", color=(241, 245, 249, 255))
                    dpg.add_spacer(width=10)
                    dpg.add_text("0 teachers selected", tag="selected_count_text", color=(148, 163, 184, 255))
                dpg.add_spacer(height=8)

                # Scrollable teacher list in card container
                with dpg.child_window(height=360, border=True) as teacher_card:
                    with dpg.table(header_row=False, resizable=True, policy=dpg.mvTable_SizingStretchProp, borders_outerV=False, borders_innerV=False, borders_outerH=False, borders_innerH=True):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        
                        teacher_names = list(self.teacherObjects.keys())
                        for i in range(0, len(teacher_names), 2):
                            with dpg.table_row():
                                # First teacher in row
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True, horizontal_spacing=8):
                                        cb = dpg.add_checkbox(
                                            label=teacher_names[i],
                                            source=f"teacher_{teacher_names[i]}",
                                            callback=self.update_selected_count
                                        )
                                        dpg.bind_item_theme(cb, "checkbox_theme")
                                        dpg.add_spacer(width=4)
                                        time_btn = dpg.add_button(
                                            label="Full",
                                            tag=f"time_pref_btn_{teacher_names[i]}",
                                            callback=self.toggle_time_preference,
                                            user_data=teacher_names[i],
                                            width=65,
                                            height=26,
                                            show=False
                                        )
                                        dpg.bind_item_theme(time_btn, "am_pm_theme")
                                
                                # Second teacher in row (if exists)
                                if i + 1 < len(teacher_names):
                                    with dpg.table_cell():
                                        with dpg.group(horizontal=True, horizontal_spacing=8):
                                            cb = dpg.add_checkbox(
                                                label=teacher_names[i+1],
                                                source=f"teacher_{teacher_names[i+1]}",
                                                callback=self.update_selected_count
                                            )
                                            dpg.bind_item_theme(cb, "checkbox_theme")
                                            dpg.add_spacer(width=4)
                                            time_btn = dpg.add_button(
                                                label="Full",
                                                tag=f"time_pref_btn_{teacher_names[i+1]}",
                                                callback=self.toggle_time_preference,
                                                user_data=teacher_names[i+1],
                                                width=65,
                                                height=26,
                                                show=False
                                            )
                                            dpg.bind_item_theme(time_btn, "am_pm_theme")
                dpg.bind_item_theme(teacher_card, "card_theme")

                dpg.add_spacer(height=12)
                clear_btn = dpg.add_button(label="Clear All Selections", callback=self.clear_all_teachers, width=-1)
                dpg.bind_item_theme(clear_btn, "secondary_btn_theme")
                dpg.add_spacer(height=15)

                # Date input section
                with dpg.group(horizontal=True):
                    dpg.add_text("Date", color=(148, 163, 184, 255))
                    dpg.add_spacer(width=5)
                    dpg.add_text(f"(today: {datetime.date.today()})", color=(100, 116, 139, 255))
                date_input = dpg.add_input_text(source="date_input", width=280, hint="YYYY-MM-DD")
                dpg.bind_item_theme(date_input, "input_theme")
                dpg.add_spacer(height=15)

                # Day Type section with modern radio buttons
                dpg.add_text("Day Type", color=(148, 163, 184, 255))
                dpg.add_spacer(height=5)
                day_radio = dpg.add_radio_button(
                    items=["Even Day", "Odd Day"],
                    source="day_type_radio",
                    horizontal=True
                )
                dpg.bind_item_theme(day_radio, "radio_theme")
                dpg.add_spacer(height=20)

                # Submit button with primary theme
                submit_btn = dpg.add_button(label="Submit", callback=self.validate_and_proceed, width=-1, height=45)
                dpg.bind_item_theme(submit_btn, "primary_btn_theme")

            # File dialog configuration (must be inside window context)
            with dpg.file_dialog(
                directory_selector=False, 
                show=False, 
                callback=file_dialog_callback, 
                tag="file_dialog_tag", 
                width=700, 
                height=400,
                user_data=self
            ):
                dpg.add_file_extension(".xlsx", color=(56, 211, 159, 255))
                dpg.add_file_extension(".csv", color=(56, 189, 248, 255))
                dpg.add_file_extension("", color=(148, 163, 184, 255)) 

        dpg.bind_item_theme("main_window", "modern_theme")
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
        
        # 2. Mark that a file change triggered the stop, then stop DPG
        if user_data and hasattr(user_data, 'file_changed'):
            user_data.file_changed = True
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
        dpg.add_text("Please locate and select your schedule file (.xlsx or .csv).", wrap=550)
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
        dpg.add_file_extension(".csv", color=(150, 150, 255, 255))
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
        if isinstance(item, tuple):
            period_str = str(item[0])
        else:
            period_str = str(item)
        try:
            return int(period_str.split('/')[0])
        except (ValueError, IndexError):
            return 99 

    return sorted(period_sequence, key=sort_key)

def _is_ct_entry(entry):
    """More robust CT detection with specific patterns"""
    # Sanitize the entry first to handle formatting issues
    sanitized = _sanitize_period_entry(entry).lower()
    
    # Look for specific CT patterns to avoid false positives
    ct_patterns = [
        ' ct ',     # "Class CT Smith"
        'ct ',      # "CT Smith"  
        ' ct',      # "Class CT"
        'ct-',      # "CT-Smith"
        '(ct)',     # "(CT) Smith"
    ]
    return any(pattern in sanitized for pattern in ct_patterns)

def _find_coteacher_in_entry(entry, teacher_name, all_teachers):
    """Find co-teacher using flexible name matching for CT entries"""
    # Sanitize the entry first to handle formatting issues
    sanitized = _sanitize_period_entry(entry).lower()
    
    for name in all_teachers:
        if name == teacher_name:
            continue  # Skip self
            
        name_lower = name.lower().strip()
        
        # Try multiple matching strategies
        
        # 1. Full name match (Last, First format)
        match_pos = sanitized.find(name_lower)
        if match_pos != -1:
            # Check word boundaries
            end_pos = match_pos + len(name_lower)
            after_char = sanitized[end_pos] if end_pos < len(sanitized) else ''
            before_char = sanitized[match_pos - 1] if match_pos > 0 else ''
            
            valid_before = match_pos == 0 or not before_char.isalpha()
            valid_after = end_pos >= len(sanitized) or not after_char.isalpha()
            
            if valid_before and valid_after:
                return name
        
        # 2. First name only match (handle "Class CT Costello" vs "Costello, Elizabeth")
        if ',' in name_lower:
            first_name = name_lower.split(',')[1].strip()
            first_name_pos = sanitized.find(first_name)
            if first_name_pos != -1:
                # Check word boundaries for first name
                end_pos = first_name_pos + len(first_name)
                after_char = sanitized[end_pos] if end_pos < len(sanitized) else ''
                before_char = sanitized[first_name_pos - 1] if first_name_pos > 0 else ''
                
                valid_before = first_name_pos == 0 or not before_char.isalpha()
                valid_after = end_pos >= len(sanitized) or not after_char.isalpha()
                
                if valid_before and valid_after:
                    return name
        
        # 3. Last name only match (handle "CT Smith" vs "Smith, John")
        last_name = name_lower.split(',')[0].strip()
        last_name_pos = sanitized.find(last_name)
        if last_name_pos != -1:
            # Check word boundaries for last name
            end_pos = last_name_pos + len(last_name)
            after_char = sanitized[end_pos] if end_pos < len(sanitized) else ''
            before_char = sanitized[last_name_pos - 1] if last_name_pos > 0 else ''
            
            valid_before = last_name_pos == 0 or not before_char.isalpha()
            valid_after = end_pos >= len(sanitized) or not after_char.isalpha()
            
            if valid_before and valid_after:
                return name
                
    return None

def check_coteachers(teachers, filepath):
    """
    Checks the schedule for co-teachers (CT). If a co-teacher for a period is 
    NOT out, the period is removed from the principal teacher's CT coverage list.
    """
    try:
        schedule_df = _load_schedule_df(filepath)  # Use same function as parseSchedule
    except Exception as e:
        # If we can't load the schedule, skip CT validation
        print(f"Warning: Could not load schedule for CT validation: {e}")
        return
        
    for teacher_key in teachers:
        teacher = teachers[teacher_key]
        if not teacher.is_out:
            continue
            
        # Iterate over a copy to avoid mutating the list mid-loop
        for period in list(teacher.periods_need_covered_CT):
            if '/' in period:
                period1, period2 = period.split('/')
                check_periods = [period1.strip(), period2.strip()]
            else:
                check_periods = [period.strip()]

            # Search all sub-periods to find the co-teacher before making any decision
            coteacher_name = None
            for check_period in check_periods:
                period_suffix = add_ordinal_suffix(check_period)
                
                if period_suffix not in schedule_df.columns:
                    continue
                    
                period_data = schedule_df[period_suffix].dropna().astype(str)
                for entry in period_data:
                    if _is_ct_entry(entry):
                        found_name = _find_coteacher_in_entry(entry, teacher.name, teachers.keys())
                        if found_name:
                            coteacher_name = found_name
                            break
                if coteacher_name:
                    break

            if coteacher_name:
                if teachers[coteacher_name].is_out:
                    # Both teachers out - convert CT to regular coverage for principal teacher only
                    if period in teachers[coteacher_name].periods_need_covered_CT:
                        teachers[coteacher_name].periods_need_covered_CT.remove(period)
                    if period in teacher.periods_need_covered_CT:
                        teacher.periods_need_covered_CT.remove(period)
                        # Add to regular coverage but preserve CT information
                        teacher.periods_need_covered.append(period)
                        # Mark this period as originally CT for output formatting
                        if not hasattr(teacher, 'converted_ct_periods'):
                            teacher.converted_ct_periods = []
                        teacher.converted_ct_periods.append(period)
                else:
                    # Co-teacher present - remove CT need from principal teacher
                    if period in teacher.periods_need_covered_CT:
                        teacher.periods_need_covered_CT.remove(period)
            # If no co-teacher found, keep CT need (data issue but don't break)


def _load_schedule_df(filepath):
    """Loads the schedule file into a DataFrame, handling both .xlsx and .csv formats."""
    if filepath.endswith('.csv'):
        schedule_df = pd.read_csv(filepath, header=0, skipinitialspace=True)
        schedule_df = schedule_df.loc[:, ~schedule_df.columns.str.match('^Unnamed|^$')]
        schedule_df.columns = schedule_df.columns.str.strip()
        if 'Name' not in schedule_df.columns:
            for col in schedule_df.columns:
                if schedule_df[col].notna().any() and any(schedule_df[col].dropna().astype(str).str.contains(',')):
                    schedule_df = schedule_df.rename(columns={col: 'Name'})
                    break
    else:
        schedule_df = pd.read_excel(filepath, sheet_name=0)
    return schedule_df


def _parse_name(raw):
    """
    Validates and normalises a raw Name cell value.
    Returns the cleaned name string, or None if the row should be skipped.
    """
    if pd.isna(raw) or not raw or str(raw).strip() == '':
        return None
    name = str(raw).strip()
    if (name.lower() in ('name', '', 'nan') or
            name.startswith('Duty') or
            name.startswith('Plan') or
            len(name) < 2):
        return None
    if '(' in name:
        name = name.split('(')[0].strip()
    return name


def _sanitize_need_coverage(need_coverage_str):
    """
    Sanitizes the Need Coverage string to fix common formatting issues:
    - Removes spaces after commas: "1, 4, 11" -> "1,4,11"
    - Removes spaces around forward slashes: "5 / 6" -> "5/6"
    - Normalizes whitespace around CT markers: "CT -" -> "CT-"
    """
    if not need_coverage_str or need_coverage_str in ('', 'nan', 'None'):
        return ''
    
    # Remove spaces after commas
    sanitized = need_coverage_str.replace(', ', ',')
    
    # Remove spaces around forward slashes (for split periods)
    sanitized = sanitized.replace(' / ', '/').replace(' /', '/').replace('/ ', '/')
    
    # Normalize CT marker whitespace: "CT -" -> "CT-"
    sanitized = sanitized.replace('CT -', 'CT-').replace('CT  ', 'CT ')
    
    return sanitized


def _sanitize_period_entry(period_value):
    """
    Sanitizes a period cell entry to normalize CT formatting:
    - Collapses multiple spaces to single space: "Class CT                        Enciso" -> "Class CT Enciso"
    - Normalizes various CT formats to standard "Class CT [Name]"
    """
    if not period_value or pd.isna(period_value):
        return ''
    
    sanitized = str(period_value).strip()
    
    # Collapse multiple whitespace to single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Normalize CT markers: remove asterisks, standardize spacing
    sanitized = sanitized.replace('*Class CT', 'Class CT')
    sanitized = sanitized.replace('*CT', 'CT')
    
    return sanitized


def _parse_coverage(need_coverage_str):
    """
    Parses a Need Coverage cell string into standard and CT period lists.
    Returns (needs_coverage, needs_coverage_CT).
    """
    # Sanitize the input first
    need_coverage_str = _sanitize_need_coverage(need_coverage_str)
    
    if need_coverage_str in ('', 'nan', 'None'):
        return [], []
    if 'CT' in need_coverage_str:
        substrings = need_coverage_str.split(' CT-')
        needs_coverage = unique_and_ordered([s.strip() for s in substrings[0].split(',') if s.strip()])
        needs_coverage_CT = []
        if len(substrings) > 1 and substrings[1].strip():
            needs_coverage_CT = unique_and_ordered([s.strip() for s in substrings[1].split(',') if s.strip()])
    else:
        needs_coverage = unique_and_ordered([s.strip() for s in need_coverage_str.split(',') if s.strip()])
        needs_coverage_CT = []
    return needs_coverage, needs_coverage_CT


def _make_teacher(name, needs_coverage, needs_coverage_CT):
    """Constructs a new Teacher object from parsed coverage data."""
    teacher = Teacher(name, sort_periods(needs_coverage))
    teacher.periods_need_covered_CT = sort_periods(needs_coverage_CT)
    return teacher


def _merge_teacher_periods(existing, needs_coverage, needs_coverage_CT):
    """Merges new coverage periods into an existing Teacher entry."""
    existing.periods_need_covered = sort_periods(
        unique_and_ordered(existing.periods_need_covered + needs_coverage)
    )
    existing.periods_need_covered_CT = sort_periods(
        unique_and_ordered(existing.periods_need_covered_CT + needs_coverage_CT)
    )


def _parse_duties(schedule_df, teachers):
    """Populates each teacher's availability lists from the Duty columns."""
    for period in range(1, 12):
        period_suffix = add_ordinal_suffix(period)
        duty_col = f'Duty {period_suffix}'
        if duty_col not in schedule_df.columns:
            continue
        for duty_raw in schedule_df[duty_col].dropna():
            duty_raw = str(duty_raw).strip().lower()
            duty_type = _classify_duty(duty_raw)
            for teacher_name, teacher in teachers.items():
                teacher_name_lower = teacher_name.strip().lower()
                match_pos = duty_raw.find(teacher_name_lower)
                if match_pos == -1:
                    continue
                end_pos = match_pos + len(teacher_name_lower)
                after_char = duty_raw[end_pos] if end_pos < len(duty_raw) else ''
                if after_char.isalpha():
                    continue
                _get_duty_list(teacher, duty_type).append(str(period))


def _detect_ct_periods_from_row(row, needs_coverage):
    """
    Analyzes period columns to identify which periods are co-taught (CT).
    Returns (regular_periods, ct_periods) tuple.
    
    For each period in needs_coverage, checks the corresponding period column
    for 'CT' marker. If found, period goes to ct_periods, otherwise regular_periods.
    """
    if not needs_coverage:
        return [], []
    
    regular_periods = []
    ct_periods = []
    
    for period in needs_coverage:
        # Get the column name for this period (e.g., '1st', '2nd', '5th')
        period_col = add_ordinal_suffix(period)
        
        # Get and sanitize the period value
        period_value = _sanitize_period_entry(row.get(period_col, ''))
        
        # Use same CT detection logic as _is_ct_entry
        ct_patterns = [' ct ', 'ct ', ' ct', 'ct-', '(ct)']
        is_ct = any(pattern in period_value.lower() for pattern in ct_patterns)
        
        if is_ct:
            ct_periods.append(period)
        else:
            regular_periods.append(period)
    
    return regular_periods, ct_periods


def parseSchedule(filepath):
    """
    Parses the schedule file and returns a tuple: (teachers_dict, error_message or None).
    """
    try:
        schedule_df = _load_schedule_df(filepath)
    except FileNotFoundError:
        return {}, f"File not found at saved path: '{filepath}'. Please re-select the file."
    except Exception as e:
        return {}, f"Failed to read the schedule file. Details: {type(e).__name__}: {e}"

    teachers = {}
    for _, row in schedule_df.iterrows():
        name = _parse_name(row.get('Name'))
        if not name:
            continue
        needs_coverage, needs_coverage_CT = _parse_coverage(str(row.get('Need Coverage', '')).strip())
        
        # Auto-detect CT periods from period columns if no CT- format in Need Coverage
        if not needs_coverage_CT and needs_coverage:
            needs_coverage, needs_coverage_CT = _detect_ct_periods_from_row(row, needs_coverage)
        
        # Include teachers even if they have no coverage needs
        if name in teachers:
            _merge_teacher_periods(teachers[name], needs_coverage, needs_coverage_CT)
        else:
            teachers[name] = _make_teacher(name, needs_coverage, needs_coverage_CT)

    _parse_duties(schedule_df, teachers)
    return teachers, None

def _classify_duty(duty_raw):
    """Returns a duty type string based on keywords found in the duty cell text."""
    if "iss" in duty_raw:       return 'iss'
    if "even days" in duty_raw: return 'even'
    if "odd days" in duty_raw:  return 'odd'
    if "-" in duty_raw:         return 'other'
    return 'standard'


def _get_duty_list(teacher, duty_type):
    """Returns the correct availability list on a Teacher for a given duty type."""
    return {
        'iss':      teacher.iss_periods_available,
        'even':     teacher.evenDayPeriods_available,
        'odd':      teacher.oddDayPeriods_available,
        'other':    teacher.otherDutyPeriods_available,
        'standard': teacher.periods_available,
    }[duty_type]


def _filter_periods_by_time_preference(periods, time_preference):
    """
    Filters a list of periods based on time preference.
    AM = periods 1-4, PM = periods 5-11, None = all periods.
    Handles split periods like '5/6' by checking the first part.
    """
    if time_preference is None:
        return periods
    
    def get_period_number(period):
        """Extract numeric period value, handling split periods like '5/6'"""
        period_str = str(period)
        if '/' in period_str:
            # For split periods like '5/6', use the first period
            return int(period_str.split('/')[0])
        try:
            return int(period_str)
        except ValueError:
            return 99  # Unknown periods go to end
    
    filtered = []
    for period in periods:
        period_num = get_period_number(period)
        if time_preference == 'AM' and 1 <= period_num <= 4:
            filtered.append(period)
        elif time_preference == 'PM' and 5 <= period_num <= 11:
            filtered.append(period)
    
    return filtered


def _try_assign_from_list(duty_type, teachers, sorted_available_teachers, periods, evenDay=None):
    """
    Attempts to find the least-used available teacher who has all requested
    periods free in the given duty list. Removes the periods on success.
    Returns the assigned teacher name, or None.
    """
    for name, _ in sorted_available_teachers:
        teacher = teachers[name]

        if duty_type == 'standard':
            # Standard availability merges base free periods with day-specific ones
            avail = set(teacher.periods_available)
            avail.update(teacher.evenDayPeriods_available if evenDay else teacher.oddDayPeriods_available)
        else:
            avail = _get_duty_list(teacher, duty_type)

        if all(p in avail for p in periods):
            if duty_type == 'standard':
                # Remove from whichever source list actually held each period
                for p in periods:
                    if p in teacher.periods_available:
                        teacher.periods_available.remove(p)
                    elif evenDay and p in teacher.evenDayPeriods_available:
                        teacher.evenDayPeriods_available.remove(p)
                    elif not evenDay and p in teacher.oddDayPeriods_available:
                        teacher.oddDayPeriods_available.remove(p)
            else:
                target = _get_duty_list(teacher, duty_type)
                for p in periods:
                    target.remove(p)
            return name
    return None


def find_and_assign(p1, teachers, sorted_available_teachers, coverage_data, evenDay, p2=None):
    """Core logic to find the least-used available teacher for a period (or split period)."""
    periods = [p1, p2] if p2 else [p1]

    # 1. Check Standard/Day-Dependent Availability
    name = _try_assign_from_list('standard', teachers, sorted_available_teachers, periods, evenDay)
    if name:
        return name, False, False

    # 2. Check ISS Availability (Fallback)
    name = _try_assign_from_list('iss', teachers, sorted_available_teachers, periods)
    if name:
        return name, True, False

    # 3. Check Other Duty Availability (Fallback)
    name = _try_assign_from_list('other', teachers, sorted_available_teachers, periods)
    if name:
        return name, False, True

    return None, False, False


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

    for teacher_out_name in teachers_out:
        outputString += f"{teacher_out_name}:\n"
        teacher_out_obj = teachers[teacher_out_name]

        all_periods_to_cover_raw = []
        # Filter periods based on time preference
        filtered_periods = _filter_periods_by_time_preference(
            teacher_out_obj.periods_need_covered,
            teacher_out_obj.coverage_time_preference
        )
        for period in filtered_periods:
            all_periods_to_cover_raw.append((period, False)) 
        
        # Filter CT periods based on time preference
        filtered_ct_periods = _filter_periods_by_time_preference(
            teacher_out_obj.periods_need_covered_CT,
            teacher_out_obj.coverage_time_preference
        )
        for period in filtered_ct_periods:
            all_periods_to_cover_raw.append((period, True)) 
        
        all_periods_to_cover = sort_periods(all_periods_to_cover_raw) 

        for period, is_ct in all_periods_to_cover:
            # Re-sort before each assignment to reflect updated coverage counts
            sorted_available_teachers = sorted([
                (name, data['times_covered']) for name, data in coverage_data.items()
                if name not in teachers_out and name in teachers
            ], key=lambda x: x[1])

            if '/' in period:
                period1, period2 = period.split('/')
                assigned_teacher_name, iss_covered, otherDuty_covered = find_and_assign(
                    period1, teachers, sorted_available_teachers, coverage_data, evenDay, period2
                )
            else:
                assigned_teacher_name, iss_covered, otherDuty_covered = find_and_assign(
                    period, teachers, sorted_available_teachers, coverage_data, evenDay
                )
            
            if assigned_teacher_name:
                duty_tag = ""
                if iss_covered:
                    duty_tag = " (Close ISS)"
                elif otherDuty_covered: 
                    duty_tag = " (OTHER DUTY)"
                
                # Check if this period was originally CT (either from CT list or converted CT)
                is_converted_ct = hasattr(teacher_out_obj, 'converted_ct_periods') and period in teacher_out_obj.converted_ct_periods
                period_display = f"{period} (CT)" if (is_ct or is_converted_ct) else period
                outputString += f"   {period_display} {assigned_teacher_name}{duty_tag}\n"

                coverage_data[assigned_teacher_name]['times_covered'] += 1
                new_log_entry = {
                    'date': date,
                    'covered_for': teacher_out_name,
                    'period': period
                }
                coverage_data[assigned_teacher_name]['coverage_log'].append(new_log_entry)
            else:
                period_display = f"{period} (CT)" if is_ct else period
                outputString += f"   {period_display} No available teacher\n"

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
    Displays the coverage results in a new DearPyGui window with modern theme.
    """
    dpg.create_context()
    dpg.set_global_font_scale(1.5) 

    # Modern theme for results window
    with dpg.theme(tag="results_modern_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 23, 42, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (241, 245, 249, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 41, 59, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (14, 165, 233, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (56, 189, 248, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (2, 132, 199, 255))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)

    def copy_results_to_clipboard():
        dpg.set_clipboard_text(dpg.get_value("results_text_output"))
        with dpg.window(label="Copied", modal=True, no_resize=True, no_close=True, width=250) as popup:
            dpg.add_text("Results copied to clipboard!")
            dpg.add_button(label="OK", callback=lambda: dpg.delete_item(popup))
            
    dpg.create_viewport(title=f'Coverage Results - {date}', width=650, height=800)
    
    with dpg.window(tag="results_window", label="Coverage Results", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=650, height=800):
        dpg.add_text("✓ Coverage Calculated Successfully!", color=(52, 211, 153, 255))
        dpg.add_spacer(height=15)
        
        # Results in a card-like container
        with dpg.child_window(height=650, border=True) as results_card:
            dpg.add_input_text(
                tag="results_text_output", 
                default_value=results_text, 
                multiline=True, 
                readonly=True, 
                width=-1, 
                height=-1
            )
        dpg.bind_item_theme(results_card, "card_theme")
        dpg.add_spacer(height=15)

        with dpg.group(horizontal=True):
            copy_btn = dpg.add_button(label="Copy to Clipboard", callback=copy_results_to_clipboard, width=300)
            dpg.bind_item_theme(copy_btn, "secondary_btn_theme")
            dpg.add_spacer(width=10)
            close_btn = dpg.add_button(label="Close and Exit", callback=lambda: dpg.stop_dearpygui(), width=300)
            dpg.bind_item_theme(close_btn, "primary_btn_theme")

    dpg.bind_item_theme("results_window", "results_modern_theme")
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

        # If the user changed the schedule file, loop to reload with the new path
        if app.file_changed:
            continue

        # Check if the user closed the main GUI (app.date will be empty)
        if not app.date:
            return

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
 