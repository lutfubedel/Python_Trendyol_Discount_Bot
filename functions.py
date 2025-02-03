# Gerekli kütüphaneleri içe aktarıyoruz
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv

user = os.getenv("USER")
password = os.getenv("PASSWORD")

class Product:
    def __init__(self, website, name, mark, price, control_date,url):
        self.website = website
        self.name = name
        self.mark = mark
        self.price = price
        self.control_date = control_date
        self.url = url


def find_product_trendyol(product_url):
    # Kullanıcı bilgisi eklemek için bir başlık tanımlıyoruz (bot olmadığımızı belirtmek için)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # URL'ye istek gönderiyoruz
    response = requests.get(product_url, headers=headers)
    
    # HTML yanıtını ayrıştırıyoruz
    soup = BeautifulSoup(response.text, 'html.parser')

    product_website = "Trendyol"

    # Ürün adını çekiyoruz
    h1_tag = soup.find("h1", class_="pr-new-br")
    if h1_tag:
        spans = h1_tag.find_all("span")  # Tüm <span> etiketlerini liste olarak al
        product_name = spans[1].text.strip() if len(spans) > 1 else (spans[0].text.strip() if len(spans) == 1 else None)
    else:
        product_name = None

    # Marka ve fiyat bilgisini çekiyoruz
    try:
        product_price = soup.find("span", {"class": "prc-dsc"}).text.strip()
        product_mark = soup.find("span", {"class": "product-brand-name-without-link"}) or \
                    soup.find("a", {"class": "product-brand-name-with-link"})
        print(product_mark.text.strip())
        if product_mark:
            product_mark = product_mark.text.strip()
        else:
            raise AttributeError  # Eğer hiçbiri bulunmazsa, hata fırlat

    except AttributeError:
        print("Ürün fiyatı ya da marka bilgisi bulunamadı.")
        return None


    # İşlemin yapıldığı tarih ve saati alıyoruz
    control_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Product nesnesini oluşturuyoruz
    return Product(product_website, product_name, product_mark, product_price, control_date,product_url)

def check_discount():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user= user,
            password= password,
            database="product_price_tracking_db"
        )
        
        if conn.is_connected():
            print("MySQL bağlantısı başarılı!")
                
        cursor = conn.cursor()
        cursor.execute("SELECT current_price, URL FROM fiyat_takip")

        products_price_diff = []
        for row in cursor.fetchall():
            current_product = find_product_trendyol(row[1])
            current_date = datetime.now()
            new_price = current_product.price
            url = current_product.url

            if row[0] != new_price:
                update_query = "UPDATE fiyat_takip SET normal_price = %s ,control_date = %s WHERE URL = %s"
                cursor.execute(update_query, (new_price,current_date, url))
                text = (
                    f"Ürün İsmi : {current_product.name}\n"
                    f"Eski Fiyat: {row[0]}\n"
                    f"Güncel Fiyat: {current_product.price}\n"
                    f"Ürün Linki: {current_product.url}"
                )
                products_price_diff.append(text)
        
        conn.commit()
        conn.close()

        if not products_price_diff:
            return ["Fiyatlar sabit"]
        else:
            return products_price_diff

    except mysql.connector.Error as err:
        print(f"Hata: {err}")
        return ["Bir hata oluştu!"]

def update_product_list():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user= user,
            password= password,
            database="product_price_tracking_db"
        )
        
        if conn.is_connected():
            print("MySQL bağlantısı başarılı!")
                
        cursor = conn.cursor()
        cursor.execute("SELECT control_date, URL FROM fiyat_takip")

        for row in cursor.fetchall():
            control_date = row[0]  # Veritabanından gelen tarih
            url = row[1]  # Ürün linki

            updated_price = find_product_trendyol(url).price

            current_date = datetime.now()
            days_difference = (current_date - control_date).days

            if days_difference > 30:
                update_query = "UPDATE fiyat_takip SET normal_price = %s ,control_date = %s WHERE URL = %s"
                cursor.execute(update_query, (updated_price,current_date, url))

        conn.commit()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Hata: {err}")










