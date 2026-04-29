import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x600")

        self.expenses = []
        self.load_data()

        # --- Поля ввода ---
        input_frame = ttk.LabelFrame(root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5)
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", "Другое"]
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, values=categories, width=15)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)
        self.category_combo.current(0)

        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=12)
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        add_btn = ttk.Button(input_frame, text="Добавить расход", command=self.add_expense)
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        # --- Фильтры ---
        filter_frame = ttk.LabelFrame(root, text="Фильтры", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_category_var = tk.StringVar()
        self.filter_category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                  values=["Все"] + categories, width=15)
        self.filter_category_combo.grid(row=0, column=1, padx=5, pady=5)
        self.filter_category_combo.current(0)

        ttk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5, pady=5)
        self.from_date_entry = ttk.Entry(filter_frame, width=12)
        self.from_date_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="Дата до (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5)
        self.to_date_entry = ttk.Entry(filter_frame, width=12)
        self.to_date_entry.grid(row=0, column=5, padx=5, pady=5)

        filter_btn = ttk.Button(filter_frame, text="Применить фильтр", command=self.filter_expenses)
        filter_btn.grid(row=0, column=6, padx=10, pady=5)

        reset_btn = ttk.Button(filter_frame, text="Сбросить фильтр", command=self.reset_filter)
        reset_btn.grid(row=0, column=7, padx=5, pady=5)

        period_btn = ttk.Button(filter_frame, text="Подсчёт суммы за период", command=self.calc_period_sum)
        period_btn.grid(row=1, column=0, columnspan=8, pady=5)

        # --- Таблица расходов ---
        columns = ("ID", "Сумма", "Категория", "Дата")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопка удаления записи
        del_btn = ttk.Button(root, text="Удалить выбранную запись", command=self.delete_selected)
        del_btn.pack(pady=5)

        # Статус / сумма
        self.status_label = ttk.Label(root, text="", relief="sunken")
        self.status_label.pack(fill="x", padx=10, pady=5)

        self.refresh_table()

    def add_expense(self):
        """Добавляет новый расход с проверкой"""
        try:
            amount = float(self.amount_entry.get())
            if amount <=0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму (число)")
            return

        category = self.category_var.get().strip()
        if not category:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return

        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return

        # Генерируем ID (простой автоинкремент)
        new_id = max([e["id"] for e in self.expenses], default=0) + 1

        self.expenses.append({
            "id": new_id,
            "amount": amount,
            "category": category,
            "date": date_str
        })
        self.save_data()
        self.refresh_table()
        self.amount_entry.delete(0, tk.END)

    def refresh_table(self, expenses_to_show=None):
        """Обновляет таблицу. Если не передан список, показывает все."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        data = expenses_to_show if expenses_to_show is not None else self.expenses
        for exp in data:
            self.tree.insert("", tk.END, values=(exp["id"], f"{exp['amount']:.2f}", exp["category"], exp["date"]))

        total = sum(e["amount"] for e in data)
        self.status_label.config(text=f"Показано записей: {len(data)} | Общая сумма: {total:.2f}")

    def filter_expenses(self):
        """Фильтрует по категории и диапазону дат"""
        filtered = self.expenses[:]

        category = self.filter_category_var.get()
        if category != "Все":
            filtered = [e for e in filtered if e["category"] == category]

        from_date = self.from_date_entry.get().strip()
        to_date = self.to_date_entry.get().strip()

        try:
            if from_date:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") >= from_dt]
            if to_date:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") <= to_dt]
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты в фильтре. Используйте ГГГГ-ММ-ДД")
            return

        self.refresh_table(filtered)

    def reset_filter(self):
        """Сбрасывает все фильтры"""
        self.filter_category_var.set("Все")
        self.from_date_entry.delete(0, tk.END)
        self.to_date_entry.delete(0, tk.END)
        self.refresh_table()

    def calc_period_sum(self):
        """Подсчёт суммы за период (отдельное окно)"""
        def compute():
            from_date = from_entry.get().strip()
            to_date = to_entry.get().strip()
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else None
                to_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else None
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты")
                return

            total = 0
            for e in self.expenses:
                e_date = datetime.strptime(e["date"], "%Y-%m-%d")
                if from_dt and e_date < from_dt:
                    continue
                if to_dt and e_date > to_dt:
                    continue
                total += e["amount"]

            messagebox.showinfo("Сумма за период", f"Общая сумма расходов: {total:.2f}")

        win = tk.Toplevel(self.root)
        win.title("Подсчёт суммы за период")
        win.geometry("300x150")

        ttk.Label(win, text="Дата от (ГГГГ-ММ-ДД):").pack(pady=5)
        from_entry = ttk.Entry(win, width=15)
        from_entry.pack()

        ttk.Label(win, text="Дата до (ГГГГ-ММ-ДД):").pack(pady=5)
        to_entry = ttk.Entry(win, width=15)
        to_entry.pack()

        ttk.Button(win, text="Посчитать", command=compute).pack(pady=10)

    def delete_selected(self):
        """Удаляет выбранную запись по ID"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        item = selected[0]
        values = self.tree.item(item, "values")
        exp_id = int(values[0])

        self.expenses = [e for e in self.expenses if e["id"] != exp_id]
        self.save_data()
        self.refresh_table()

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, indent=4, ensure_ascii=False)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.expenses = json.load(f)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
