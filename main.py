import dearpygui.dearpygui as dpg
import datetime
import json
import os
import pandas as pd

class Teacher:
    def __init__(self, name, periods_need_covered):
        self.name= name
        self.last_name = name.split(',')[0]  # Assuming the last name is the first part of the full name
        self.is_out = False
        self.periods_need_covered = periods_need_covered
        self.periods_available = []
        self.periods_need_covered_CT = []

class TeacherCoverageApp:
    def __init__(self, schedule_filepath):
        self.date = ""
        self.teacherObjects = parseSchedule(schedule_filepath)

    def validate_and_proceed(self):
        date_string = dpg.get_value("date_input")
        try:
            # Attempt to parse the date from the input string
            datetime.date.fromisoformat(date_string)
            self.date = date_string
            # If the date is valid, call the method to proceed
            self.receiveValues_and_stop()
        except ValueError:
            # Show a popup and don't stop the application
            # Capture the ID of the new window
            with dpg.window(label="Error", modal=True, no_resize=True, no_close=True) as popup_window:
                dpg.add_text("Invalid date format. Please use YYYY-MM-DD.")
                dpg.add_button(label="Ok", callback=lambda: dpg.delete_item(popup_window))

    def receiveValues_and_stop(self):
        # Now this method is only called after successful validation
        for name in self.teacherObjects.keys():
            self.teacherObjects[name].is_out = dpg.get_value(f"teacher_{name}")
        dpg.stop_dearpygui()

    def create_gui(self):
        dpg.create_context()

        with dpg.font_registry():
            default_font = dpg.add_font("assets/Roboto-Regular.ttf", 30)
        dpg.bind_font(default_font)

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
            for name in self.teacherObjects.keys():
                dpg.add_bool_value(default_value=False, tag=f"teacher_{name}")

        dpg.create_viewport(title='Custom Title', width=800, height=800)
        
        with dpg.window(tag="main_window", label="main_window", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=800, height=800):
            with dpg.group(tag="main_group", horizontal=False):
                dpg.add_text("Valley Teacher Coverage", tag="title_text")
                dpg.add_spacer(height=5)
                
                dpg.add_text("Teachers Out:", tag="teachers_label")
                dpg.add_spacer(height=5)
                
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
                dpg.add_text("Date (YYYY-MM-DD)")
                dpg.add_input_text(source="date_input", width=250)
                dpg.add_spacer(height=5)

                dpg.add_button(label="Submit", callback=self.validate_and_proceed)

        dpg.bind_item_theme("main_window", "my_custom_theme")
        dpg.set_primary_window("main_window", True)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

def add_ordinal_suffix(number):
    """
    Adds the correct ordinal suffix (st, nd, rd, th) to a given number.
    Handles special cases for numbers ending in 11, 12, and 13.
    """
    digit= int(number)
    if digit == 1:
        suffix = "st"
    elif digit == 2:
        suffix = "nd"
    elif digit == 3:
        suffix = "rd"
    else:
        suffix = "th"
    return str(number) + suffix


def check_coteachers(teachers, filepath):
    schedule_df = pd.read_excel(filepath, sheet_name=0)
    for teacher in teachers:
        teacher = teachers[teacher]
        if not teacher.is_out:
            continue
        for period in teacher.periods_need_covered_CT:
            if '/' in period:
                period1, period2 = period.split('/')
                check_periods = [period1.strip(), period2.strip()]
            else:
                check_periods = [period.strip()]
            for period in check_periods:
                period=add_ordinal_suffix(period)
                if period in schedule_df.columns:
                    period_data = schedule_df[period].dropna().astype(str).str.strip().str.lower().tolist()
                    substrings = [s.split('CT') for s in period_data]
                    coteacher = None
                    # Flatten the list and get the coteacher name if present
                    for split in substrings:
                        if len(split) > 1 and split[1].strip():
                            coteacher = split[1].strip()
                            break
                    if coteacher:
                        if teachers[coteacher].is_out:
                            teacher[coteacher].periods_need_covered_CT.remove(period)
                            teacher.periods_need_covered_CT.remove(period)
                            teacher.periods_need_covered.append(period)
                        else:
                            teacher.periods_need_covered_CT.remove(period)
                        
def parseSchedule(filepath):
    schedule_df = pd.read_excel(filepath, sheet_name=0)

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
            needs_coverage = substrings[0].strip().split(",") if pd.notna(substrings[0]) else []
            needs_coverage_CT = [s.strip() for s in substrings[0].split(",")] if len(substrings) > 1 and pd.notna(substrings[1]) else []
        else:
            needs_coverage = [s.strip() for s in need_coverage_str.split(',')] if pd.notna(need_coverage_str) else []

        teacher = Teacher(name, needs_coverage)
        teacher.periods_need_covered_CT = needs_coverage_CT
        teachers[name] = teacher
        
    for period in range(1, 12):
        period_suffex=add_ordinal_suffix(period)
        duty_col = f'Duty {period_suffex}'
        if duty_col in schedule_df.columns:
            # Create a list of all duty assignments for this period
            duty_assignments = [str(entry).strip().lower() for entry in schedule_df[duty_col].dropna()]
            print(f"Duty assignments for period {period}: {duty_assignments}")
            # Check each teacher against the list of duty assignments
            for duty in duty_assignments:
                iss=False
                if "ISS" in duty:
                    duty = duty.replace("ISS", "").strip()
                    iss=True
                for teacher in teachers.values():
                    if teacher.last_name.lower() in duty:
                        if iss:
                            teacher.periods_available.append(f"{period} (ISS)")
                        else:
                            teacher.periods_available.append(str(period))

    return teachers
        
def determineCoverage_and_save(teachers, date, coverage_tracker_json):
    outputString = f"Date: {date}\n"
    if os.path.exists(coverage_tracker_json) and os.path.getsize(coverage_tracker_json) > 0:
        with open(coverage_tracker_json, 'r') as f:
            coverage_data = json.load(f)
    else:
        coverage_data = {}

    for name in teachers.keys():
        if name not in coverage_data:
            coverage_data[name] = {'times_covered': 0, 'coverage_log': []}

    teachers_out = [name for name, teacher in teachers.items() if teacher.is_out]
    sorted_available_teachers = sorted([
        (name, data['times_covered']) for name, data in coverage_data.items()
        if name not in teachers_out
    ], key=lambda x: x[1])

    for teacher_out_name in teachers_out:
        outputString += f"{teacher_out_name}:\n"
        teacher_out_obj = teachers[teacher_out_name]
        iss=False
        for period in teacher_out_obj.periods_need_covered:
            assigned_teacher_name = None
            if '/' in period:
                period1, period2 = period.split('/')
                for teacher_name, _ in sorted_available_teachers:
                    if period1 in teachers[teacher_name].periods_available and period2 in teachers[teacher_name].periods_available:
                        teachers[teacher_name].periods_available.remove(period1)
                        teachers[teacher_name].periods_available.remove(period2)
                        assigned_teacher_name = teacher_name
                        break
            else:
                for name, _ in sorted_available_teachers:
                    if period in teachers[name].periods_available:
                        teachers[name].periods_available.remove(period)
                        assigned_teacher_name = name
                        break
            if not assigned_teacher_name:
                for name, _ in sorted_available_teachers:
                    if f"{period} (ISS)" in teachers[name].periods_available:
                        teachers[name].periods_available.remove(f"{period} (ISS)")
                        assigned_teacher_name = name
                        iss=True 
                        break
            if assigned_teacher_name:
                if iss:
                    outputString += f"  (Close ISS) {period} {assigned_teacher_name}\n"
                else:
                    outputString += f"  {period} {assigned_teacher_name}\n"
                coverage_data[assigned_teacher_name]['times_covered'] += 1
                new_log_entry = {
                    'date': date,
                    'covered_for': teacher_out_name,
                    'period': period
                }
                coverage_data[assigned_teacher_name]['coverage_log'].append(new_log_entry)
                
            else:
                outputString += f"  {period} No available teacher\n"
        for period in teacher_out_obj.periods_need_covered_CT:
            assigned_teacher_name = None
            if '/' in period:
                period1, period2 = period.split('/')
                for teacher_name, _ in sorted_available_teachers:
                    if period1 in teachers[teacher_name].periods_available and period2 in teachers[teacher_name].periods_available:
                        teachers[teacher_name].periods_available.remove(period1)
                        teachers[teacher_name].periods_available.remove(period2)
                        assigned_teacher_name = teacher_name
                        break
            else:
                for name, _ in sorted_available_teachers:
                    if period in teachers[name].periods_available:
                        teachers[name].periods_available.remove(period)
                        assigned_teacher_name = name
                        break

            if assigned_teacher_name:
                outputString += f"  {period} {assigned_teacher_name}\n"
                coverage_data[assigned_teacher_name]['times_covered'] += 1
                new_log_entry = {
                    'date': date,
                    'covered_for': teacher_out_name,
                    'period': period
                }
                coverage_data[assigned_teacher_name]['coverage_log'].append(new_log_entry)
                
            else:
                outputString += f"  {period} No available teacher\n"

    with open(coverage_tracker_json, 'w') as f:
        json.dump(coverage_data, f, indent=4)

    with open(f"coverage_{date}.txt", 'w') as f:
        f.write(outputString)

def main():

    schedule_filepath = "Coverage_Schedule.xlsx"

    app = TeacherCoverageApp(schedule_filepath)
    app.create_gui()
    check_coteachers(app.teacherObjects, schedule_filepath)
    coverage_file = "coverage_tracker.json"
    determineCoverage_and_save(app.teacherObjects, app.date, coverage_file)

    print("\n--- Final Results ---")
    with open(coverage_file, 'r') as f:
        final_data = json.load(f)
    print(json.dumps(final_data, indent=4))

    #print all teacher objects for debugging
    for name, teacher in app.teacherObjects.items():
        print(f"Teacher: {name}, Is Out: {teacher.is_out}, Needs Coverage: {teacher.periods_need_covered}, Available: {teacher.periods_available}, Last Name: {teacher.last_name}")

if __name__ == "__main__":
    main()