import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

# ---------------- Database Setup ---------------- #
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")
conn.commit()

# ---------------- Functions ---------------- #
def add_expense():
    dt = date_entry.get()
    cat = category_var.get()
    desc = desc_entry.get()
    amt = amount_entry.get()

    if not dt or not cat or not amt:
        messagebox.showerror("Error", "Date, Category, and Amount are required!")
        return

    try:
        amt = float(amt)
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number!")
        return

    cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                   (dt, cat, desc, amt))
    conn.commit()
    clear_inputs()
    load_expenses()

def clear_inputs():
    date_entry.delete(0, tk.END)
    date_entry.insert(0, str(date.today()))
    category_var.set(categories[0])
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)

def load_expenses():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM expenses")
    for expense in cursor.fetchall():
        tree.insert("", tk.END, values=expense)

def delete_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "No expense selected!")
        return
    expense_id = tree.item(selected[0])["values"][0]
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    load_expenses()

# ---------------- UI Setup ---------------- #
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("700x500")

# Input Frame
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
date_entry = tk.Entry(input_frame)
date_entry.insert(0, str(date.today()))
date_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(input_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
categories = ["Food", "Transport", "Bills", "Shopping", "Other"]
category_var = tk.StringVar(value=categories[0])
category_menu = ttk.Combobox(input_frame, textvariable=category_var, values=categories, state="readonly")
category_menu.grid(row=0, column=3, padx=5, pady=5)

tk.Label(input_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
desc_entry = tk.Entry(input_frame)
desc_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(input_frame, text="Amount:").grid(row=1, column=2, padx=5, pady=5)
amount_entry = tk.Entry(input_frame)
amount_entry.grid(row=1, column=3, padx=5, pady=5)

# Buttons
tk.Button(input_frame, text="Add Expense", command=add_expense).grid(row=2, column=0, columnspan=2, pady=10)
tk.Button(input_frame, text="Delete Selected", command=delete_expense).grid(row=2, column=2, columnspan=2, pady=10)

# Expense Table
columns = ("ID", "Date", "Category", "Description", "Amount")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True)

load_expenses()
root.mainloop()
