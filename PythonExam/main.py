from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon
import sqlite3
import traceback
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Function to handle exceptions and print error information to console
def handle_exception(exc_type, exc_value, exc_traceback):
    # Output error information to console
    traceback.print_exception(exc_type, exc_value, exc_traceback)

# Set the function handle_exception as the exception hook
sys.excepthook = handle_exception

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('PlannerApp.ui', self) # Load the UI from the specified file

        self.connection = sqlite3.connect('tasks.db')  # Connect to the SQLite database (or create it if it doesn't exist)
        self.cursor = self.connection.cursor()

        # Create the tasks table if it does not exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                date TEXT,
                name TEXT,
                time TEXT,
                duration TEXT,
                status TEXT
            )
        ''')
        self.connection.commit() # Commit the changes to the database

        # Make background of QTextBrowser transparent
        self.text_browser = self.findChild(QtWidgets.QTextBrowser, 'DailyPlanner')
        self.text_browser.setStyleSheet("background-color: transparent")

        # Find the calendar widget and connect its clicked signal to the date_clicked method
        self.calendar = self.findChild(QtWidgets.QCalendarWidget, 'calendarWidget')
        self.calendar.clicked.connect(self.date_clicked)

       # Find the add task button and connect its clicked signal to the add_task method
        self.add_button = self.findChild(QtWidgets.QPushButton, 'pushButton')
        self.add_button.clicked.connect(self.add_task)

        # Find the table widget and connect its cellClicked signal to the cell_clicked method
        self.table = self.findChild(QtWidgets.QTableWidget, 'tableWidget')
        self.table.cellClicked.connect(self.cell_clicked)

        # Start the scheduler that will check every minute if a task is due
        self.start_scheduler()

        self.show() # Show the main window

    # Function to notify when a task is due
    def notify_task(self):
        connection = sqlite3.connect('tasks.db')  # Connect to the database
        cursor = connection.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        date_str = str(self.calendar.selectedDate().toPyDate())
        cursor.execute('SELECT name, time, duration, status FROM tasks WHERE date = ?', (date_str,))
        tasks = [{'name': row[0], 'time': row[1], 'duration': row[2], 'status': row[3]} for row in cursor.fetchall()]

        for task in tasks:
            if task['time'] == current_time and task['status'] != 'Completed':
                self.send_notification('Task Due', f'Task {task["name"]} is due now!')

        connection.close()  # Close the connection to the database

    # Function to send a notification using a message box
    def send_notification(self, title, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()

     # Function to start the background scheduler
    def start_scheduler(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.notify_task, 'interval', minutes=1)
        self.scheduler.start()

    # Inner class to handle time dialog box
    class TimeDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super(Ui.TimeDialog, self).__init__(parent)

            self.setWindowTitle('Enter Time')

            # Spin box for hours input
            self.hour_input = QtWidgets.QSpinBox(self)
            self.hour_input.setRange(0, 23)
            self.hour_input.setSuffix(' H')

            # Spin box for minutes input
            self.minute_input = QtWidgets.QSpinBox(self)
            self.minute_input.setRange(0, 59)
            self.minute_input.setSuffix(' M')

            # OK and Cancel buttons
            self.button_box = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)

            # Set the layout of the dialog
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.hour_input)
            layout.addWidget(self.minute_input)
            layout.addWidget(self.button_box)

        # Function to get the time from the dialog box
        def get_time(self):
            return self.hour_input.value(), self.minute_input.value()

    # Function to handle date clicked event
    def date_clicked(self, date):
        date = self.calendar.selectedDate()
        self.show_tasks(date)

    # Function to show tasks for a selected date
    def show_tasks(self, date):
        # Clear the table
        self.table.setRowCount(0)

        tasks = self.get_tasks(date)
        for task in tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Add task details to table
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(task['name']))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(task['time']))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(task['duration']))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(task['status']))

            # Add a delete button to the last column
            delete_button = QtWidgets.QPushButton()
            delete_button.setIcon(QIcon('C:/Users/rutih/PycharmProjects/PythonExam/DeleteButtonIcon.png'))
            delete_button.clicked.connect(lambda: self.delete_task(row))
            self.table.setCellWidget(row, 4, delete_button)

        # Set the column widths
        self.table.setColumnWidth(0, 100)  # Set the width of the first column to 100
        self.table.setColumnWidth(1, 75)  # Set the width of the second column to 75
        self.table.setColumnWidth(2, 75)  # Set the width of the third column to 75
        self.table.setColumnWidth(3, 100)  # Set the width of the fourth column to 100
        self.table.setColumnWidth(4, 50)  # Set the width of the fifth column to 50

    # Function to handle cell clicked event
    def cell_clicked(self, row, column):
        if column == 3:
            # Change status
            status, ok = QtWidgets.QInputDialog.getItem(self, 'Change Status', 'Status:', ['Not started', 'Started', 'Completed'])
            if ok:
                self.table.item(row, column).setText(status)
                # Update task in database

    # Function to add a task
    def add_task(self):
            # Show an input dialog to get the task name
            name, ok = QtWidgets.QInputDialog.getText(self, 'Add Task', 'Task name:')
            if not ok:
                return

            # Show the time dialog to get the task time
            time_dialog = Ui.TimeDialog(self)
            if time_dialog.exec_() == QtWidgets.QDialog.Accepted:
                hour, minute = time_dialog.get_time()
            else:
                return

            # Show an input dialog to get the task duration
            duration, ok = QtWidgets.QInputDialog.getText(self, 'Add Task', 'Duration:')
            if not ok:
                return

            # Convert hour and minute to a time string
            time = f'{hour:02d}:{minute:02d}'

            # Add task to database and refresh list
            task = {'date': str(self.calendar.selectedDate().toPyDate()), 'name': name, 'time': time,
                    'duration': duration, 'status': 'Not started'}
            self.add_task_to_db(task) # Add the task to the database
            self.show_tasks(self.calendar.selectedDate()) # Refresh the task list

    # Function to add a task to the database
    def add_task_to_db(self, task):
        # Add task to database
        self.cursor.execute('INSERT INTO tasks (date, name, time, duration, status) VALUES (?, ?, ?, ?, ?)',
                            (task['date'], task['name'], task['time'], task['duration'], task['status']))
        self.connection.commit()

    # Function to get tasks from the database
    def get_tasks(self, date):
        # Get tasks from database

        # Get tasks from database
        date_str = str(date.toPyDate())
        self.cursor.execute('SELECT name, time, duration, status FROM tasks WHERE date = ?', (date_str,))
        tasks = [{'name': row[0], 'time': row[1], 'duration': row[2], 'status': row[3]} for row in self.cursor.fetchall()]
        return tasks

    # Function to delete a task
    def delete_task(self, row):
        # Get task details
        date = str(self.calendar.selectedDate().toPyDate())
        name_item = self.table.item(row, 0)
        time_item = self.table.item(row, 1)

        # Check that the items are not None
        if name_item is not None and time_item is not None:
            name = name_item.text()
            time = time_item.text()

            # Delete task from database
            self.cursor.execute('DELETE FROM tasks WHERE date = ? AND name = ? AND time = ?', (date, name, time))
            self.connection.commit()

        # Remove row from table
        self.table.removeRow(row)

# Run the application
app = QtWidgets.QApplication([])
window = Ui()
app.exec_()