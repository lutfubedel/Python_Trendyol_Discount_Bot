import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

import webbrowser
import mysql.connector
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import functions
import os
from dotenv import load_dotenv

user = os.getenv("USER")
password = os.getenv("PASSWORD")

class ProductGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ürün Fiyat Takip Sistemi")
        self.root.geometry("900x500")

        self.style = tb.Style(theme="superhero")

        title_label = tb.Label(self.root, text="Ürün Listesi", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        self.tree = tb.Treeview(
            self.root,
            columns=("ID", "Website", "Name", "Mark", "Normal Price", "Current Price", "Date", "URL"),
            show="headings",
            bootstyle="info"
        )

        columns = [
            ("ID", 40), ("Website", 120), ("Name", 150),
            ("Mark", 100), ("Normal Price", 100),
            ("Current Price", 100), ("Date", 150), ("URL", 100)
        ]

        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(expand=True, fill="both", padx=10, pady=5)

        self.tree.bind("<ButtonRelease-1>", self.open_link)

        btn_frame = tb.Frame(self.root)
        btn_frame.pack(pady=10)

        add_button = tb.Button(btn_frame, text="Ürün Ekle", command=self.add_product, width=18, bootstyle=SUCCESS)
        add_button.grid(row=0, column=0, padx=5)

        delete_button = tb.Button(btn_frame, text="Seçili Ürünü Sil", command=self.delete_product, width=18, bootstyle=DANGER)
        delete_button.grid(row=0, column=1, padx=5)

        self.load_data()

    def load_data(self):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user= user,
                password= password,
                database="product_price_tracking_db"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT id, website, name, mark, normal_price, current_price, control_date, URL FROM fiyat_takip")
            rows = cursor.fetchall()

            for row in self.tree.get_children():
                self.tree.delete(row)

            for row in rows:
                row_data = list(row)
                row_data[-1] = "Link"  
                self.tree.insert("", "end", values=row_data, tags=(row[-1],))

            conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("MySQL Hata", f"Veritabanına bağlanırken hata oluştu:\n{err}")

    def open_link(self, event):
        """URL sütununa tıklanınca linki aç"""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        col = self.tree.identify_column(event.x)  # Tıklanan sütunu bul
        col_index = int(col[1:]) - 1  # Tkinter sütunları 1'den başlıyor, dizin 0'dan

        if col_index == 7:  # URL sütunu (8. sütun, index 7)
            product_id = self.tree.item(selected_item, "values")[0]

            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user= user,
                    password= password,
                    database="product_price_tracking_db"
                )
                cursor = conn.cursor()
                cursor.execute("SELECT URL FROM fiyat_takip WHERE id = %s", (product_id,))
                url = cursor.fetchone()[0]
                conn.close()

                if url:
                    webbrowser.open(url)  # Tarayıcıda aç
            except mysql.connector.Error as err:
                messagebox.showerror("Hata", f"MySQL Hatası:\n{err}")

    def add_product(self):
        add_window = tb.Toplevel(self.root)
        add_window.title("Yeni Ürün Ekle")
        add_window.geometry("550x250")

        tb.Label(add_window, text="Ürün Linki:", font=("Arial", 11)).pack(pady=5)
        website_entry = tb.Entry(add_window, width=50)
        website_entry.pack(pady=5)

        def save_product():
            product = functions.find_product_trendyol(website_entry.get())

            if not product:
                messagebox.showwarning("Hata", "Ürün bilgisi bulunamadı!")
                return
            
            website, name, mark, price, url = product.website, product.name, product.mark, product.price, product.url

            missing_fields = []

            if not website:
                missing_fields.append("Website")
            if not name:
                missing_fields.append("Name")
            if not mark:
                missing_fields.append("Mark")
            if not price:
                missing_fields.append("Price")

            if missing_fields:
                messagebox.showwarning("Eksik Bilgi", f"Lütfen şu alanları doldurun: {', '.join(missing_fields)}")
                return


            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user= user,
                    password= password,
                    database="product_price_tracking_db"
                )
                cursor = conn.cursor()

                cursor.execute("SELECT name, mark FROM fiyat_takip")
                rows = cursor.fetchall()

                for i in range(0,len(rows)):
                    if(rows[i][0] == name or rows[i][1] == mark):
                        messagebox.showerror("Hata","Bu ürün tabloda bulunmaktadır")
                        return 


                sql = "INSERT INTO fiyat_takip (website, name, mark, normal_price, current_price, control_date, URL) VALUES (%s, %s, %s, %s, %s, NOW(), %s)"
                cursor.execute(sql, (website, name, mark, price, price, url))
                conn.commit()
                conn.close()
                messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!")
                add_window.destroy()
                self.load_data()
            except mysql.connector.Error as err:
                messagebox.showerror("Hata", f"MySQL Hatası:\n{err}")

        save_button = tb.Button(add_window, text="Kaydet", command=save_product, bootstyle=PRIMARY)
        save_button.pack(pady=10)

    def delete_product(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Seçim Hatası", "Lütfen silmek için bir ürün seçin!")
            return

        product_id = self.tree.item(selected_item, "values")[0]

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user= user,
                password= password,
                database="product_price_tracking_db"
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fiyat_takip WHERE id = %s", (product_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", "Ürün başarıyla silindi!")
            self.load_data()
        except mysql.connector.Error as err:
            messagebox.showerror("Hata", f"MySQL Hatası:\n{err}")


root = tb.Window(themename="superhero")
app = ProductGUI(root)
root.mainloop()
