import dearpygui.dearpygui as dpg
import datetime

class Teacher:
    def __init__(self, name, periods_need_covered, periods_available):
        self.name = name
        self.is_out = False
        self.periods_need_covered = periods_need_covered
        self.periods_available = periods_available

class TeacherCoverageApp:
    def __init__(self, teachers):
        self.date = ""
        # dictionary mapping teacher name to teacher object
        self.teacherObjects = teachers

    def receiveValues_and_stop(self):
        self.date = dpg.get_value("date_input")
        # Iterate through the dictionary keys to ensure correct mapping
        for name in self.teacherObjects.keys():
            self.teacherObjects[name].is_out = dpg.get_value(f"teacher_{name}")
        dpg.stop_dearpygui()

    def create_gui(self):
        dpg.create_context()

        # Add Font Registries
        with dpg.font_registry():
            default_font = dpg.add_font("assets/Roboto-Regular.ttf", 30)

        dpg.bind_font(default_font)

        # Create a custom theme for a modern look
        with dpg.theme(tag="my_custom_theme"):
            with dpg.theme_component(dpg.mvAll):
                # Set background colors (e.g., a deep gray)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 25, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100, 255))
                # Set text color (e.g., a light gray)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 10)

        with dpg.value_registry():
            dpg.add_string_value(default_value=str(datetime.date.today()), tag="date_input")
            # Use teacher names for tags to ensure correct mapping
            for name in self.teacherObjects.keys():
                dpg.add_bool_value(default_value=False, tag=f"teacher_{name}")

        dpg.create_viewport(title='Custom Title', width=800, height=800)
        
        with dpg.window(tag="main_window", label="main_window", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=800, height=800):
            with dpg.group(tag="main_group", horizontal=False):
                dpg.add_text("Valley Teacher Coverage", tag="title_text")
                dpg.add_spacer(height=5)
                
                dpg.add_text("Teachers Out:", tag="teachers_label")
                dpg.add_spacer(height=5)
                
                # Use a table to display checkboxes in a 2-column layout
                with dpg.table(header_row=False, resizable=True, policy=dpg.mvTable_SizingStretchSame, borders_outerV=False, borders_innerV=False, borders_outerH=False, borders_innerH=True):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    # Iterate through teacher names directly
                    teacher_names = list(self.teacherObjects.keys())
                    for i in range(0, len(teacher_names), 2):
                        with dpg.table_row():
                            # First teacher in the pair goes in the first cell
                            with dpg.table_cell():
                                dpg.add_checkbox(label=teacher_names[i], source=f"teacher_{teacher_names[i]}")

                            # Check if a second teacher exists for the pair
                            if i + 1 < len(teacher_names):
                                # Second teacher goes in the second cell
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

def parse_schedule(file_path):
    # Placeholder function to parse the schedule file
    # returns a dictionary mapping names to Teacher objects
    return None
        
def main():
    # Example teachers for demonstration
    teacher_names = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank"]
    teachers = {name: Teacher(name, [1], [1]) for name in teacher_names}
    app = TeacherCoverageApp(teachers)
    app.create_gui()
    
    # After GUI closes, access the results
    print("Date:", app.date)
    for name, teacher in app.teacherObjects.items():
        print(f"Teacher: {name}, Is Out: {teacher.is_out}")
        # periods need covered and periods available can be accessed as well
        print(f"   Periods Need Covered: {teacher.periods_need_covered}")
        print(f"   Periods Available: {teacher.periods_available}")

if __name__ == "__main__":
    main()