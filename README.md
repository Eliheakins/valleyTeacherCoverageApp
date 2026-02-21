Valley Teacher Coverage Application Guide
The valleyTeacherCoverageApp is a dedicated tool for calculating daily teacher coverage assignments based on a pre-formatted Excel schedule, optimizing assignments by prioritizing the least-covered staff.

Program Usage
The application uses a two-stage process: File Configuration and Daily Calculation.

Stage 1: Initial Setup (Schedule File Selection)
The first time you run the program, or if the schedule file location has been changed, the application will prompt you to locate the master schedule file.

Launch the Program: Run the compiled executable or the main script (main.py).

File Prompt: A small window will open asking you to locate the schedule file.

Browse and Select: Click "Browse for File" and select your schedule file. Both Excel (.xlsx) and CSV (.csv) formats are supported.

Configuration Saved: Once selected, the program saves the absolute path of this file to a config.json file, so you won't be prompted again unless the file is moved or deleted.

Stage 2: Daily Coverage Calculation
After the schedule file is loaded, the main input GUI appears.

Select Teachers Out: Check the box next to every teacher who is out for the day.

Quick Reset: Use the "Clear All Selections" button to quickly deselect all teachers before starting a new entry.

Enter Date: Confirm or edit the date in the YYYY-MM-DD format (e.g., 2025-09-26).

Select Day Type: Check the "Even Day" box if the current day follows the even-day schedule. Leave it unchecked for odd days.

Submit: Click "Submit" to run the calculation.

Stage 3: Results Display and Output
After submission, the main GUI closes, and a new results window appears.

GUI Results: The window displays the finalized list of assignments (Who is covering which period for Whom).

Copy to Clipboard: Use the "Copy to Clipboard" button to quickly transfer the entire schedule text for pasting into emails, communication apps, or announcements.

File Output: The results are automatically saved as a date-stamped text file in the same directory as the program: coverage_YYYY-MM-DD.txt.

Exit: Click "Close and Exit" to close the application.

Schedule File Formatting Requirements
The program relies on very specific formatting. The schedule must be contained within an Excel file (.xlsx) or a CSV file (.csv).

1. Column Headers (First Row)
The following column headers must be present in the first row:

Teacher Name: Must be exactly Name.

Coverage Needs: Must be exactly Need Coverage.

Standard Periods: Must be formatted as [Number][Ordinal Suffix] (e.g., 1st, 2nd, 3rd, ... 11th). Periods 1 through 11 should be listed.

Duty Periods: Must be formatted as Duty [Number][Ordinal Suffix] (e.g., Duty 1st, Duty 2nd, ... Duty 11th). Matches the corresponding period column.

2. Teacher Naming Conventions
Name Column: Teacher names should be formatted as [Last Name], [First Name] (e.g., Fry, Philip).

Optional Sub Name: You can include the name of the teacher they are covering long-term in parentheses (e.g., Fry, Philip (Leela)). The program ignores the text in parentheses.

Duty Assignments: Any name used inside a Duty [Period] column must exactly match the format found in the Name column (e.g., Fry, Philip ISS or Fry, Philip - Even Days).

3. "Need Coverage" Column Formatting
This column dictates which periods need external coverage if the teacher is out.

Standard Periods: Simple number strings, comma-separated (e.g., 1, 4, 11).

Split Periods: Numbers joined by a single slash (/), with no spaces (e.g., 5/6, 8/9). Represents adjacent periods that must be covered by a single available teacher.

Co-Taught Periods: Must STRICTLY use the pattern: [Standard Periods] CT-[Co-Taught Periods]. (e.g., 1,4,11 CT-2,5/6,8/9,10). Periods listed after CT- are only covered if the co-teacher is also out. If the co-teacher is present, coverage is not needed for that period.

4. Special Codes in Duty Columns
The program uses keywords within the Duty [Period] cells to flag different types of available periods.

ISS Duty: The text ISS must appear anywhere in the cell (e.g., Fry, Philip ISS). This is prioritized after all standard (non-duty) and day-specific free periods. It is considered a "fallback" coverage.

Even Day Specific: Must include  - Even Days (with leading space and dash) (e.g., Fry, Philip - Even Days). Only available for coverage when "Even Day" is checked in the GUI.

Odd Day Specific: Must include  - Odd Days (with leading space and dash) (e.g., Fry, Philip - Odd Days). Only available for coverage when "Even Day" is not checked in the GUI.

Other Duty: Any duty containing a dash (-) that does not also contain ISS, Even Days, or Odd Days is treated as Other Duty (e.g., Fry, Philip - Res or Fry, Philip - Hall). This is the final "fallback" coverage.