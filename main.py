import dearpygui.dearpygui as dpg
import datetime
import json
import os

class Teacher:
    def __init__(self, name, periods_need_covered, periods_available):
        self.name = name
        self.is_out = False
        self.periods_need_covered = periods_need_covered
        self.periods_available = periods_available

class TeacherCoverageApp:
    def __init__(self, teachers):
        self.date = ""
        self.teacherObjects = teachers

    def receiveValues_and_stop(self):
        self.date = dpg.get_value("date_input")
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

                dpg.add_button(label="Submit", callback=self.receiveValues_and_stop)

        dpg.bind_item_theme("main_window", "my_custom_theme")
        dpg.set_primary_window("main_window", True)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

def determineCoverage_and_save(teachers, date, coverage_tracker_json):
    # Check if the file exists and is not empty before attempting to load
    if os.path.exists(coverage_tracker_json) and os.path.getsize(coverage_tracker_json) > 0:
        with open(coverage_tracker_json, 'r') as f:
            coverage_data = json.load(f)
    else:
        coverage_data = {}

    # Ensure all teachers from the current list are in the coverage data
    for name in teachers.keys():
        if name not in coverage_data:
            coverage_data[name] = {'times_covered': 0, 'coverage_log': []}

    # Identify teachers who are out and sort available teachers by times covered
    teachers_out = [name for name, teacher in teachers.items() if teacher.is_out]
    sorted_available_teachers = sorted([
        (name, data['times_covered']) for name, data in coverage_data.items()
        if name not in teachers_out
    ], key=lambda x: x[1])

    for teacher_out_name in teachers_out:
        teacher_out_obj = teachers[teacher_out_name]
        for period in teacher_out_obj.periods_need_covered:
            # Find the first available teacher who can cover the period
            assigned_teacher_name = None
            for name, _ in sorted_available_teachers:
                if period in teachers[name].periods_available:
                    assigned_teacher_name = name
                    break

            if assigned_teacher_name:
                # Update times_covered and log the coverage event in the JSON data
                coverage_data[assigned_teacher_name]['times_covered'] += 1
                new_log_entry = {
                    'date': date,
                    'covered_for': teacher_out_name,
                    'period': period
                }
                coverage_data[assigned_teacher_name]['coverage_log'].append(new_log_entry)
                
                print(f"Assigned {assigned_teacher_name} to cover {teacher_out_name} for period {period}")
            else:
                print(f"No available teachers to cover {teacher_out_name} for period {period}")

    with open(coverage_tracker_json, 'w') as f:
        json.dump(coverage_data, f, indent=4)

def main():
    teacher_names = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank"]
    teachers = {
        "Alice": Teacher("Alice", [1], [2, 3]),
        "Bob": Teacher("Bob", [2], [1, 3]),
        "Charlie": Teacher("Charlie", [3], [1, 2]),
        "David": Teacher("David", [1], [2, 3]),
        "Eva": Teacher("Eva", [2], [1, 3]),
        "Frank": Teacher("Frank", [3], [1, 2]),
    }

    app = TeacherCoverageApp(teachers)
    app.create_gui()
    
    coverage_file = "coverage_tracker.json"
    determineCoverage_and_save(app.teacherObjects, app.date, coverage_file)

    print("\n--- Final Results ---")
    with open(coverage_file, 'r') as f:
        final_data = json.load(f)
    print(json.dumps(final_data, indent=4))

if __name__ == "__main__":
    main()