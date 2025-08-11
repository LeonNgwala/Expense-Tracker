import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import date
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

# ---------- Database Setup ----------
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

# ---------- Functions ----------
def fetch_expenses(filter_month=None, filter_year=None):
    query = "SELECT * FROM expenses"
    params = []
    if filter_month and filter_year:
        query += " WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params = [f"{int(filter_month):02d}", str(filter_year)]
    elif filter_year:
        query += " WHERE strftime('%Y', date) = ?"
        params = [str(filter_year)]
    cursor.execute(query, params)
    return cursor.fetchall()

def refresh_expenses():
    for row in tree.get_children():
        tree.delete(row)
    month = month_var.get()
    year = year_var.get()
    if month == "All": month = None
    if year == "All": year = None
    expenses = fetch_expenses(month, year)
    total = 0
    for expense in expenses:
        tree.insert("", "end", values=expense)
        total += expense[4]
    total_var.set(f"Total: R{total:.2f}")

def update_charts():
    month = month_var.get()
    year = year_var.get()
    if month == "All": month = None
    if year == "All": year = None
    
    expenses = fetch_expenses(month, year)
    
    # Bar Chart
    monthly_totals = collections.defaultdict(float)
    for exp in expenses:
        exp_date = exp[1]
        y, m, _ = exp_date.split("-")
        key = f"{y}-{m}"
        monthly_totals[key] += exp[4]
    
    sorted_keys = sorted(monthly_totals.keys())
    values = [monthly_totals[k] for k in sorted_keys]
    
    ax_bar.clear()
    ax_bar.bar(sorted_keys, values, color='#4e79a7')  # solid color for bars
    ax_bar.set_title("Monthly Spending Summary")
    ax_bar.set_ylabel("Amount (R)")
    ax_bar.set_xlabel("Month")
    ax_bar.tick_params(axis='x', rotation=45)
    ax_bar.grid(True, linestyle='--', alpha=0.5)

    # Pie Chart
    category_totals = collections.defaultdict(float)
    for exp in expenses:
        category_totals[exp[2]] += exp[4]

    ax_pie.clear()
    if category_totals:
        labels = list(category_totals.keys())
        sizes = list(category_totals.values())
        colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1']
        ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(labels)])
        ax_pie.set_title("Spending by Category")
    else:
        ax_pie.text(0.5, 0.5, 'No Data', ha='center', va='center')
        ax_pie.set_title("Spending by Category")

    fig.tight_layout()
    canvas.draw()

def refresh_all():
    refresh_expenses()
    update_charts()

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

    try:
        y,m,d = map(int, dt.split('-'))
    except Exception:
        messagebox.showerror("Error", "Date must be in YYYY-MM-DD format!")
        return

    cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                   (dt, cat, desc, amt))
    conn.commit()
    clear_inputs()
    refresh_all()

def clear_inputs():
    date_entry.delete(0, "end")
    date_entry.insert(0, str(date.today()))
    category_var.set(categories[0])
    desc_entry.delete(0, "end")
    amount_entry.delete(0, "end")

def delete_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "No expense selected!")
        return
    expense_id = tree.item(selected[0])["values"][0]
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    refresh_all()

def edit_expense_popup(event):
    selected = tree.selection()
    if not selected:
        return
    expense_id, dt, cat, desc, amt = tree.item(selected[0])["values"]

    def save_edit():
        new_date = edit_date_entry.get()
        new_cat = edit_category_var.get()
        new_desc = edit_desc_entry.get()
        new_amt = edit_amount_entry.get()

        if not new_date or not new_cat or not new_amt:
            messagebox.showerror("Error", "Date, Category, and Amount are required!")
            return
        try:
            new_amt = float(new_amt)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number!")
            return
        try:
            y,m,d = map(int, new_date.split('-'))
        except Exception:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format!")
            return

        cursor.execute("""
            UPDATE expenses SET date=?, category=?, description=?, amount=? WHERE id=?
        """, (new_date, new_cat, new_desc, new_amt, expense_id))
        conn.commit()
        refresh_all()
        edit_win.destroy()

    edit_win = tb.Toplevel(root)
    edit_win.title("Edit Expense")
    edit_win.geometry("350x220")

    tb.Label(edit_win, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=10, pady=8, sticky="w")
    edit_date_entry = tb.Entry(edit_win)
    edit_date_entry.grid(row=0, column=1, padx=10, pady=8)
    edit_date_entry.insert(0, dt)

    tb.Label(edit_win, text="Category:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
    edit_category_var = tb.StringVar(value=cat)
    edit_category_menu = tb.Combobox(edit_win, values=categories, textvariable=edit_category_var)
    edit_category_menu.grid(row=1, column=1, padx=10, pady=8)

    tb.Label(edit_win, text="Description:").grid(row=2, column=0, padx=10, pady=8, sticky="w")
    edit_desc_entry = tb.Entry(edit_win)
    edit_desc_entry.grid(row=2, column=1, padx=10, pady=8)
    edit_desc_entry.insert(0, desc)

    tb.Label(edit_win, text="Amount:").grid(row=3, column=0, padx=10, pady=8, sticky="w")
    edit_amount_entry = tb.Entry(edit_win)
    edit_amount_entry.grid(row=3, column=1, padx=10, pady=8)
    edit_amount_entry.insert(0, amt)

    tb.Button(edit_win, text="Save", command=save_edit).grid(row=4, column=0, columnspan=2, pady=15)

def export_csv():
    expenses = fetch_expenses(
        None if month_var.get() == "All" else month_var.get(),
        None if year_var.get() == "All" else year_var.get()
    )
    if not expenses:
        messagebox.showinfo("Export CSV", "No expenses to export!")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files","*.csv")],
        title="Save as"
    )
    if not file_path:
        return

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID","Date","Category","Description","Amount"])
        writer.writerows(expenses)
    messagebox.showinfo("Export CSV", f"Exported {len(expenses)} expenses to {file_path}")

# ---------- UI Setup with ttkbootstrap ----------
style = tb.Style("darkly")  # Change theme here if you want

root = style.master
root.title("Personal Expense Tracker - ttkbootstrap")
root.geometry("950x720")

# --- Input Frame ---
input_frame = tb.Frame(root, padding=10)
input_frame.pack(fill="x", padx=15, pady=15)

tb.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
date_entry = tb.Entry(input_frame)
date_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
date_entry.insert(0, str(date.today()))

tb.Label(input_frame, text="Category:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
categories = ["Food", "Transport", "Bills", "Shopping", "Other"]
category_var = tb.StringVar(value=categories[0])
category_menu = tb.Combobox(input_frame, values=categories, textvariable=category_var, state="readonly")
category_menu.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

tb.Label(input_frame, text="Description:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
desc_entry = tb.Entry(input_frame)
desc_entry.grid(row=1, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

tb.Label(input_frame, text="Amount:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
amount_entry = tb.Entry(input_frame)
amount_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

add_btn = tb.Button(input_frame, text="Add Expense", bootstyle="success", command=add_expense)
add_btn.grid(row=2, column=2, sticky="ew", padx=5, pady=5)

delete_btn = tb.Button(input_frame, text="Delete Selected", bootstyle="danger", command=delete_expense)
delete_btn.grid(row=2, column=3, sticky="ew", padx=5, pady=5)

# --- Filter Frame ---
filter_frame = tb.Frame(root, padding=10)
filter_frame.pack(fill="x", padx=15)

tb.Label(filter_frame, text="Filter by Month:").pack(side="left", padx=(0, 10))
month_var = tb.StringVar(value="All")
months = ["All"] + [f"{m:02d}" for m in range(1, 13)]
month_menu = tb.Combobox(filter_frame, values=months, textvariable=month_var, state="readonly", width=10)
month_menu.pack(side="left")

tb.Label(filter_frame, text="Year:").pack(side="left", padx=(20, 10))
year_var = tb.StringVar(value="All")
current_year = date.today().year
years = ["All"] + [str(y) for y in range(current_year - 5, current_year + 1)]
year_menu = tb.Combobox(filter_frame, values=years, textvariable=year_var, state="readonly", width=10)
year_menu.pack(side="left")

apply_filter_btn = tb.Button(filter_frame, text="Apply Filter", bootstyle="primary", command=refresh_all)
apply_filter_btn.pack(side="left", padx=20)

export_btn = tb.Button(filter_frame, text="Export CSV", bootstyle="info", command=export_csv)
export_btn.pack(side="right")

# --- Treeview for expenses ---
columns = ("ID", "Date", "Category", "Description", "Amount")
tree = ttk.Treeview(root, columns=columns, show="headings", height=18)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
tree.pack(padx=15, pady=15, fill="both", expand=True)

tree.bind("<Double-1>", edit_expense_popup)

# --- Total Label ---
total_var = tb.StringVar(value="Total: R0.00")
total_label = tb.Label(root, textvariable=total_var, font=("Helvetica", 16, "bold"))
total_label.pack(pady=(0, 10))

# --- Dashboard Frame for Charts ---
dashboard_frame = tb.Frame(root)
dashboard_frame.pack(fill="both", padx=15, pady=(0,15), expand=False)

fig = Figure(figsize=(10, 3), dpi=100)
ax_bar = fig.add_subplot(121)
ax_pie = fig.add_subplot(122)

canvas = FigureCanvasTkAgg(fig, master=dashboard_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill="both", expand=True)

# --- Initialize ---
refresh_all()

root.mainloop()
