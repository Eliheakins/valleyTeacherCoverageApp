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
        
        with dpg.value_registry():
            dpg.add_string_value(default_value=datetime.date.today(), tag="date_input")
            for i in range(len(self.teachers)):
                dpg.add_bool_value(default_value=False, tag=f"teacher_{i}")

        dpg.create_viewport(title='Custom Title', width=600, height=450)
        
        # We create a window to hold all our widgets. We configure it to look like the main viewport.
        with dpg.window(tag="main_window", label="main_window", no_move=True, no_resize=True, no_title_bar=True, pos=(0, 0), width=600, height=450):
            # All widgets go inside this window
            with dpg.group(tag="main_group", horizontal=False):
                dpg.add_text("Valley Teacher Coverage", tag="title_text")
                dpg.add_separator()
                dpg.add_input_text(label="Date (YYYY-MM-DD)", source="date_input", width=-1)
                
                dpg.add_text("Teachers Out:", tag="teachers_label")
                for i, teacher in enumerate(self.teachers):
                    dpg.add_checkbox(label=teacher, source=f"teacher_{i}")

                dpg.add_button(label="Submit", callback=self.receiveValues_and_stop)

        dpg.set_primary_window("main_window", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

def main():
    teachers = ["Mr. Smith", "Ms. Johnson", "Mrs. Lee", "Mr. Brown"]
    app = TeacherCoverageApp(teachers)
    app.create_gui()
    
    print("Teachers out:", app.is_teacher_out)
    print("Date selected:", app.date)

if __name__ == "__main__":
    main()