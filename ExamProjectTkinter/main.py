import tkinter as tk
from tkcalendar import Calendar
from tkinter import ttk

root = tk.Tk()
root.title("Calendar App")
root.geometry("585x1000")

# Function to handle date selection in the calendar
def calendar_date_selected(event):
    selected_date = calendar.selection_get().strftime("%Y-%m-%d")
    display_tasks(selected_date)

# Create the calendar widget
calendar = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
calendar.pack(pady=10)
calendar.bind("<<CalendarSelected>>", calendar_date_selected)

# Create a Treeview widget to display tasks
task_list = ttk.Treeview(root, columns=("Name", "Date", "Duration", "Completed"), show="headings")
task_list.heading("Name", text="Name")
task_list.heading("Date", text="Date")
task_list.heading("Duration", text="Duration")
task_list.heading("Completed", text="Completed")
task_list.pack()

# Configure the width of the columns
task_list.column("Name", width=100)
task_list.column("Date", width=100)
task_list.column("Duration", width=100)
task_list.column("Completed", width=100)

import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

# Create the tasks table in the database if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_name TEXT NOT NULL,
    task_date TEXT NOT NULL,
    task_duration INTEGER NOT NULL,
    task_completed BOOLEAN NOT NULL
)
""")

conn.commit()

# Function to setup a task
def setup_task():
    # Inner function to save a task
    def save_task():
        # Get the task details from the Entry widgets
        task_name = task_name_entry.get()
        task_duration = int(task_duration_entry.get())
        task_date = calendar.selection_get().strftime("%Y-%m-%d")
        # Insert the new task into the database
        cursor.execute("""
        INSERT INTO tasks (task_name, task_date, task_duration, task_completed)
        VALUES (?, ?, ?, ?)
        """, (task_name, task_date, task_duration, False))
        # Commit the changes
        conn.commit()
        # Update the displayed tasks for the selected date
        display_tasks(task_date)
        # Close the task setup window after saving the task
        top.destroy()
        # Refresh the task list
        selected_date = calendar.selection_get().strftime("%Y-%m-%d")
        display_tasks(selected_date)
    top = tk.Toplevel(root)
    top.title("Task Setup")

    task_name_label = tk.Label(top, text="Task Name:")
    task_name_label.pack()

    task_name_entry = tk.Entry(top)
    task_name_entry.pack()

    task_duration_label = tk.Label(top, text="Task Duration (minutes):")
    task_duration_label.pack()

    task_duration_entry = tk.Entry(top)
    task_duration_entry.pack()

    save_button = tk.Button(top, text="Save", command=save_task)
    save_button.pack()

# Create the button
task_setup_button = tk.Button(root, text="Setup Task", command=setup_task)

task_setup_button.pack()



def display_tasks(selected_date):
    # Execute SQL query to get tasks for the selected date
    cursor.execute("""
    SELECT task_name, task_date, task_duration, CASE WHEN task_completed = 1 THEN 'Completed' ELSE 'Not Completed' END
    FROM tasks
    WHERE task_date = ?
    """, (selected_date,))
    tasks = cursor.fetchall()

    # Clear all items from the task list
    task_list.delete(*task_list.get_children())

    # Insert tasks into the task list
    for task in tasks:
        task_list.insert("", "end", values=(task[0], task[1], task[2], task[3]))

# Function to delete a task
def delete_task():
    # Get the selected task in the task list
    selected_task = task_list.selection()
    if selected_task:
        task_name = task_list.item(selected_task)["values"][0]
        # Execute SQL query to delete the selected task
        cursor.execute("""
            DELETE FROM tasks WHERE task_name = ?
            """, (task_name,))
        # Commit the changes
        conn.commit()
        # Refresh the task list
        display_tasks(calendar.selection_get().strftime("%Y-%m-%d"))

# Bind the delete function to double-click event in the task list
task_list.bind("<Double-1>", lambda event: delete_task())

# Function to mark a task as completed
def mark_task_as_completed():
    # Get the selected task in the task list
    selected_task = task_list.selection()
    if selected_task:
        task_name = task_list.item(selected_task)["values"][0]
        # Execute SQL query to update the task status
        cursor.execute("""
        UPDATE tasks SET task_completed = 1 WHERE task_name = ?
        """, (task_name,))
        # Commit the changes
        conn.commit()
        # Refresh the task list
        display_tasks(calendar.selection_get().strftime("%Y-%m-%d"))

# Create and pack Button widget for marking tasks as completed
mark_completed_button = tk.Button(root, text="Mark as Completed", command=mark_task_as_completed)
mark_completed_button.pack(pady=10)

# Run the application
root.mainloop()


