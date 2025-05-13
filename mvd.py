import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "mvd_system"
}

def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            login VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(50) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(100),
            description TEXT,
            address VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(100),
            description TEXT,
            address VARCHAR(255),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

class Users:
    def get_user_by_login(self, login):
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELLECT * FROM users WHERE login = %s", (login,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Пользователь не найден: {e}")
            return None
    def delete_user(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Пользователь не найден: {e}")
            return None


class ReportForm:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Подача обращения")
        self.top.geometry("400x300")

        tk.Label(self.top, text="Тип обращения").pack()
        self.type_entry = tk.Entry(self.top)
        self.type_entry.pack()

        tk.Label(self.top, text="Описание проблемы").pack()
        self.desc_entry = tk.Entry(self.top)
        self.desc_entry.pack()

        tk.Label(self.top, text="Адрес").pack()
        self.addr_entry = tk.Entry(self.top)
        self.addr_entry.pack()

        tk.Button(self.top, text="Отправить", command=self.submit_report).pack(pady=10)

    def submit_report(self):
        report_type = self.type_entry.get()
        desc = self.desc_entry.get()
        addr = self.addr_entry.get()

        if not report_type or not desc or not addr:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reports (type, description, address) VALUES (%s, %s, %s)",
                       (report_type, desc, addr))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успех", "Обращение отправлено")
        self.top.destroy()

class ReportViewer:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Просмотр обращений")
        self.top.geometry("800x500")

        filter_frame = tk.Frame(self.top)
        filter_frame.pack(pady=5)

        tk.Label(filter_frame, text="Тип:").grid(row=0, column=0)
        self.type_var = tk.StringVar()
        self.type_entry = tk.Entry(filter_frame, textvariable=self.type_var)
        self.type_entry.grid(row=0, column=1)

        tk.Label(filter_frame, text="Дата (YYYY-MM-DD):").grid(row=0, column=2)
        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(filter_frame, textvariable=self.date_var)
        self.date_entry.grid(row=0, column=3)

        tk.Button(filter_frame, text="Фильтровать", command=self.load_reports).grid(row=0, column=4)

        self.tree = ttk.Treeview(self.top, columns=("ID", "Тип", "Описание", "Адрес", "Дата"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)

        self.load_reports()

    def load_reports(self):
        self.tree.delete(*self.tree.get_children())
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = "SELECT id, type, description, address, created_at FROM reports WHERE 1=1"
            params = []

            if self.type_var.get():
                query += " AND type = %s"
                params.append(self.type_var.get())

            if self.date_var.get():
                query += " AND DATE(created_at) = %s"
                params.append(self.date_var.get())

            cursor.execute(query, params)
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке отчетов: {err}")
        finally:
            conn.close()

class IncidentManager:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Управление статусом дел")
        self.top.geometry("800x500")

        self.tree = ttk.Treeview(self.top, columns=("ID", "Тип", "Описание", "Адрес"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        self.tree.pack(fill="both", expand=True)

        self.load_reports()

        status_frame = tk.Frame(self.top)
        status_frame.pack(pady=10)

        tk.Label(status_frame, text="Статус:").grid(row=0, column=0)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, values=["в обработке", "закрыто"])
        self.status_combo.grid(row=0, column=1, padx=10)

        tk.Button(status_frame, text="Зарегистрировать как инцидент", command=self.register_incident).grid(row=0, column=2)

    def load_reports(self):
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, description, address FROM reports ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert('', tk.END, values=row)

    def register_incident(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите обращение.")
            return
        status = self.status_var.get()
        if not status:
            messagebox.showwarning("Статус", "Выберите статус.")
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        report_type, description, address = values[1], values[2], values[3]

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incidents (type, description, address, status)
            VALUES (%s, %s, %s, %s)
        """, (report_type, description, address, status))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успех", "Инцидент зарегистрирован.")

class IncidentListEditor:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Инциденты")
        self.top.geometry("800x500")

        self.tree = ttk.Treeview(self.top, columns=("ID", "Тип", "Описание", "Адрес", "Статус", "Дата"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120 if col != "Описание" else 200)
        self.tree.pack(fill="both", expand=True)

        self.load_incidents()

        edit_frame = tk.Frame(self.top)
        edit_frame.pack(pady=10)

        tk.Label(edit_frame, text="Новый статус:").grid(row=0, column=0)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(edit_frame, textvariable=self.status_var, values=["в обработке", "закрыто"])
        self.status_combo.grid(row=0, column=1, padx=10)

        tk.Button(edit_frame, text="Изменить статус", command=self.update_status).grid(row=0, column=2)

    def load_incidents(self):
        self.tree.delete(*self.tree.get_children())
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, description, address, status, created_at FROM incidents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.tree.insert('', tk.END, values=row)

    def update_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите инцидент для изменения.")
            return

        new_status = self.status_var.get()
        if not new_status:
            messagebox.showwarning("Статус", "Выберите новый статус.")
            return

        item = self.tree.item(selected[0])
        incident_id = item["values"][0]

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("UPDATE incidents SET status = %s WHERE id = %s", (new_status, incident_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успех", "Статус обновлён.")
        self.load_incidents()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Информационная система МВД")
        self.root.geometry("400x300")
        self.init_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def init_login_screen(self):
        self.clear_window()
        tk.Label(self.root, text="Авторизация", font=('Arial', 16)).pack(pady=10)
        tk.Label(self.root, text="Логин").pack()
        self.login_entry = tk.Entry(self.root)
        self.login_entry.pack()
        tk.Label(self.root, text="Пароль").pack()
        self.pass_entry = tk.Entry(self.root, show="*")
        self.pass_entry.pack()

        tk.Button(self.root, text="Войти", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Регистрация", command=self.register_screen).pack()

    def register_screen(self):
        self.clear_window()
        tk.Label(self.root, text="Регистрация", font=('Arial', 16)).pack(pady=10)
        tk.Label(self.root, text="Логин").pack()
        self.reg_login = tk.Entry(self.root)
        self.reg_login.pack()
        tk.Label(self.root, text="Пароль").pack()
        self.reg_pass = tk.Entry(self.root, show="*")
        self.reg_pass.pack()
        tk.Button(self.root, text="Зарегистрироваться", command=self.register).pack(pady=10)
        tk.Button(self.root, text="Назад", command=self.init_login_screen).pack()

    def register(self):
        login = self.reg_login.get()
        password = self.reg_pass.get()
        if not login or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (login, password))
            conn.commit()
            conn.close()
            messagebox.showinfo("Успех", "Регистрация прошла успешно")
            self.init_login_screen()
        except mysql.connector.errors.IntegrityError:
            messagebox.showerror("Ошибка", "Такой пользователь уже существует")

    def login(self):
        login = self.login_entry.get()
        password = self.pass_entry.get()
        self.show_user_panel()

        if login == "mvd" and password == "zlatoust":
            self.show_admin_panel()
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (login,))
        user = cursor.fetchone()
        conn.close()

        if user and password == user[0]:
            self.show_user_panel()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def show_user_panel(self):
        self.clear_window()
        tk.Label(self.root, text="Добро пожаловать, гражданин!", font=('Arial', 14)).pack(pady=10)
        tk.Button(self.root, text="Подать обращение", command=self.open_report_form).pack(pady=5)
        tk.Button(self.root, text="Выход", command=self.init_login_screen).pack(pady=5)

    def show_admin_panel(self):
        self.clear_window()
        tk.Label(self.root, text="Админ-панель МВД", font=('Arial', 14)).pack(pady=10)
        tk.Button(self.root, text="Просмотр обращений", command=self.view_reports).pack(pady=5)
        tk.Button(self.root, text="Управление делами", command=self.manage_incidents).pack(pady=5)
        tk.Button(self.root, text="Редактировать инциденты", command=self.edit_incidents).pack(pady=5)
        tk.Button(self.root, text="Выход", command=self.init_login_screen).pack(pady=10)

    def open_report_form(self):
        ReportForm(self.root)

    def view_reports(self):
        ReportViewer(self.root)

    def manage_incidents(self):
        IncidentManager(self.root)

    def edit_incidents(self):
        IncidentListEditor(self.root)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = App(root)
    root.mainloop()