import dearpygui.dearpygui as dpg
import datetime

class TeacherCoverageApp:
    def __init__(self, teachers):
        self.teachers = teachers
        self.date = ""
        self.is_teacher_out = [False] * len(teachers)

    def receiveValues_and_stop(self):
        self.date = dpg.get_value("date_input")
        self.is_teacher_out = [dpg.get_value(f"teacher_{i}") for i in range(len(self.teachers))]
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
            for i in range(len(self.teachers)):
                dpg.add_bool_value(default_value=False, tag=f"teacher_{i}")

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
                    
                    # Iterate in steps of 2 to group teachers in pairs
                    for i in range(0, len(self.teachers), 2):
                        with dpg.table_row():
                            # First teacher in the pair goes in the first cell
                            with dpg.table_cell():
                                dpg.add_checkbox(label=self.teachers[i], source=f"teacher_{i}")

                            # Check if a second teacher exists for the pair
                            if i + 1 < len(self.teachers):
                                # Second teacher goes in the second cell
                                with dpg.table_cell():
                                    dpg.add_checkbox(label=self.teachers[i+1], source=f"teacher_{i+1}")
                            
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

        
def main():
    teachers = ["Mr. Smith", "Ms. Johnson", "Mrs. Lee", "Mr. Brown", "Ms. Davis", "Mr. Wilson", "Mrs. Taylor", "Ms. Anderson", "Mr. Thomas", "Ms. Jackson", "Mr. White", "Ms. Harris", "Mrs. Martin", "Mr. Thompson", "Ms. Garcia", "Mr. Martinez", "Mrs. Robinson", "Ms. Clark", "Mr. Rodriguez", "Ms. Lewis"]
    app = TeacherCoverageApp(teachers)
    app.create_gui()
    
    print("Teachers out:", app.is_teacher_out)
    print("Date selected:", app.date)

if __name__ == "__main__":
    main()