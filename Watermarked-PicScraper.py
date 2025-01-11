import os
import time
import base64
import requests
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote_plus
import threading
from PIL import ImageEnhance
import webbrowser


# encoding utf-8
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup google driver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=fa")
    chrome_options.add_argument("--headless")  
    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    return driver

def close_google_popup(driver):
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "W0wltc"))
        )
        close_button.click()
        print("پنجره Google بسته شد.")
    except TimeoutException:
        print("پنجره Google برای بستن وجود نداشت.")
    except Exception as e:
        print(f"خطای غیرمنتظره در بستن پنجره: {e}")


def remove_divs(driver):
    try:
        driver.execute_script("""
            var elements = document.querySelectorAll('div.PHj8of.J1AhHd');
            elements.forEach(function(element) {
                element.remove();
            });
        """)
        print("divهای مزاحم حذف شدند.")
    except Exception as e:
        print(f"خطا در حذف divها: {e}")

# image proccess
def scrape_images(search_terms, watermark_path, progress, status_label, root):
    driver = setup_driver()
    output_dir = "downloaded_images"
    os.makedirs(output_dir, exist_ok=True)

    try:
        for i, term in enumerate(search_terms):
            progress["value"] = (i + 1) * 100 / len(search_terms)
            status_label.config(text=f"در حال پردازش: {term}")
            root.update_idletasks()

            print(f"در حال جستجو: {term}")
            search_url = f"https://www.google.com/search?q={quote_plus(term)}&tbm=isch"
            driver.get(search_url)

            close_google_popup(driver)
            remove_divs(driver)

            try:
                click_image(driver, term, output_dir, watermark_path)
            except Exception as e:
                print(f"خطا در پردازش {term}: {e}")

            time.sleep(2)

    finally:
        driver.quit()
        progress["value"] = 0
        status_label.config(text="تمامی تصاویر ذخیره شدند.")
        messagebox.showinfo("تمام شد", "تمامی تصاویر ذخیره شدند.")
        status_label.pack_forget()
        progress.pack_forget()


def click_image(driver, term, output_dir, watermark_path):
    try:
        first_image = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "img.YQ4gaf"))
        )
        driver.execute_script("arguments[0].click();", first_image)

        img_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.sFlh5c, img.FyHeAf, img.iPVvYb"))
        )
        image_url = img_tag.get_attribute("src")

        save_path = os.path.join(output_dir, f"{term}.webp")
        add_watermark_to_image(image_url, watermark_path, save_path)

        return save_path
    except Exception as e:
        print(f"خطا در پردازش تصویر برای '{term}': {e}")
    return None

def enhance_image_quality(image_path):
   
    img = Image.open(image_path)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0) 
    
    
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)  

    
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)  

    return img


def add_watermark_to_image(url, watermark_path, output_path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open("temp_image.jpg", "wb") as temp_file:
                for chunk in response.iter_content(1024):
                    temp_file.write(chunk)

            base_image = Image.open("temp_image.jpg")
            watermark = Image.open(watermark_path).convert("RGBA")
            base_image = base_image.resize((watermark.width, watermark.height), Image.Resampling.LANCZOS)

            combined = Image.new("RGBA", watermark.size, (0, 0, 0, 0))
            combined.paste(base_image, (0, 0))
            combined.paste(watermark, (0, 0), mask=watermark)
            combined.convert("RGB").save(output_path, "webp")

            os.remove("temp_image.jpg")
            print(f"تصویر با موفقیت ذخیره شد: {output_path}")
        else:
            print(f"خطا در دانلود تصویر: {url}")
    except Exception as e:
        print(f"خطا در افزودن واترمارک: {e}")


def start_processing(progress, status_label, root):
    search_terms = text_box.get("1.0", "end-1c").split("\n")
    search_terms = [term.strip() for term in search_terms if term.strip()]

    if search_terms:
        watermark_path = filedialog.askopenfilename(
            title="انتخاب فایل واترمارک",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")]
        )
        if not watermark_path:
            messagebox.showwarning("خطا", "هیچ فایل واترمارکی انتخاب نشد.")
            return

        progress.pack(pady=10)
        status_label.pack(pady=10)
        status_label.config(text="در حال پردازش لطفا صبر کنید...")

        thread = threading.Thread(target=scrape_images, args=(search_terms, watermark_path, progress, status_label, root))
        thread.start()
    else:
        messagebox.showwarning("خطا", "هیچ کلمه‌ای وارد نشده است.")




def get_search_terms_and_watermark():
    root = tk.Tk()
    root.title("جستجوی تصاویر")
    root.geometry("500x550")
    root.resizable(False, False)

    
    def paste_clipboard():
        text_box.insert("end", root.clipboard_get())
        update_line_numbers()
    
    def clear_text():
        text_box.delete("1.0", "end") 
        update_line_numbers()  

    def show_help():
        help_window = tk.Toplevel(root)
        help_window.title("راهنمای استفاده")
        help_window.geometry("1000x400")
        help_window.resizable(False, False)

        help_text = """
         : راهنمای استفاده  
        \n
        برای کارایی بهتر ابزار بهتر است در هر بار درخواست 40 تا عنوان وارد شود، سپس درخواست بعدی را وارد کنید * 
       بعد از زدن دکمه شروع پردازش فایل واتر مارک را وارد کنید (پس زمینه شفاف داشته) *
        در صورت مشاهده پیغام ورژن مروگر کروم، به آخرین نسخه آپدیت کنید *
        برنامه تا پایان فرآیند بسته نشود *
        """
        
        
        label = tk.Label(help_window, text=help_text, justify="right", font=("Vazir", 12))
        label.pack(padx=20, pady=20)
        


   
    def update_line_numbers(event=None):
        line_numbers = ''
        current_line = text_box.index('1.0').split('.')[0]
        lines = text_box.get('1.0', 'end-1c').split('\n')
        for i in range(len(lines)):
            line_numbers += str(i + 1) + '\n'
        canvas.delete("all") 
        canvas.create_text(5, 5, anchor="nw", text=line_numbers, font=("Courier", 10), fill="gray")

    main_frame = tk.Frame(root)
    main_frame.pack(pady=10)

    scrollbar = ttk.Scrollbar(main_frame)
    scrollbar.pack(side="right", fill="y")

    canvas = tk.Canvas(main_frame, width=50, bg="white")
    canvas.pack(side="left", fill="y", padx=(5, 0))
    
    global text_box
    text_box = tk.Text(
        main_frame,
        height=10,
        width=40,
        yscrollcommand=scrollbar.set,
        padx=10,
        font=("Vazir", 12),  
        exportselection=0,
        wrap="word", 
        undo=True, 
        selectbackground="lightblue",  
    )
    text_box.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_box.yview)

    text_box.bind("<KeyRelease>", update_line_numbers)  
    text_box.tag_configure("right", justify="right")
    text_box.bind("<FocusIn>", lambda event: text_box.tag_add("right", "1.0", "end"))
    text_box.config(state="normal")

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    paste_button = tk.Button(button_frame, text="چسباندن", command=paste_clipboard)
    paste_button.grid(row=0, column=0, padx=10)

    clear_button = tk.Button(button_frame, text="پاک کردن", command=clear_text)
    clear_button.grid(row=0, column=1, padx=10)

   
    help_button = tk.Button(button_frame, text="راهنما", command=show_help)
    help_button.grid(row=0, column=2, padx=10)

    progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    status_label = tk.Label(root, text="در حال پردازش لطفا صبر کنید...", fg="blue")

    start_button = tk.Button(root, text="شروع پردازش", command=lambda: start_processing(progress, status_label, root))
    start_button.pack(pady=20)

    footer_frame = tk.Frame(root)
    footer_frame.pack(side="bottom", fill="x", pady=10)
    version_label = tk.Label(footer_frame, text="Version 1.0.0", anchor="w")
    version_label.pack(side="left")
    footer_label = tk.Label(footer_frame, text="Watermarked PicScraper", anchor="e")
    footer_label.pack(side="right")
 
    website_label = tk.Label(footer_frame, text="https://farshadabolfathi.ir/", fg="blue", cursor="hand2", anchor="center")
    website_label.pack(side="top")  
    website_label.bind("<Button-1>", lambda e: webbrowser.open("https://farshadabolfathi.ir/"))

    root.bind_all("<Control-a>", lambda event: text_box.tag_add("sel", "1.0", "end"))
    root.bind_all("<Control-A>", lambda event: text_box.tag_add("sel", "1.0", "end"))
    root.bind_all("<Control-v>", lambda event: text_box.insert("end", root.clipboard_get()))
    root.bind_all("<Control-V>", lambda event: text_box.insert("end", root.clipboard_get()))

    root.mainloop()

if __name__ == "__main__":
    get_search_terms_and_watermark()


