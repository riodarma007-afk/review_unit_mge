from PIL import Image, ImageDraw, ImageFont
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- KONFIGURASI ---
INPUT_IMAGE = os.path.join(BASE_DIR, 'GMT.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_gmt')
# Path ke font
FONT_PATH = r'C:\Users\Domain Expansion\AppData\Local\Microsoft\Windows\Fonts\Swiss 721 Condensed Bold.otf'

# Konfigurasi Teks 1 (Di bawah/sejajar logo MGE pada body putih)
POS_BODY = (1870, 585) # Posisi Y agar turun sedikit
FONT_SIZE_BODY = 110
COLOR_BODY = (43, 58, 66) # Warna abu-abu gelap

# Konfigurasi Teks 2 (Di pintu/depan)
POS_FRONT = (380, 780) # Posisi ke kanan
FONT_SIZE_FRONT = 35 # Font dikecilin
COLOR_FRONT = (255, 255, 255) # Warna putih
BG_COLOR_FRONT = (0, 0, 255) # Biru murni (#0000FF)

def generate_truck_images(start=1, end=30):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    try:
        base_img = Image.open(INPUT_IMAGE).convert("RGBA")
    except Exception as e:
        print(f"Gagal membuka {INPUT_IMAGE}: {e}")
        return

    try:
        font_body = ImageFont.truetype(FONT_PATH, FONT_SIZE_BODY)
        font_front = ImageFont.truetype(FONT_PATH, FONT_SIZE_FRONT)
    except Exception as e:
        print(f"Gagal memuat font dari {FONT_PATH}. Menggunakan font default. Error: {e}")
        font_body = ImageFont.load_default()
        font_front = ImageFont.load_default()

    for i in range(start, end + 1):
        # Format misal GMT-701
        unit_number = 700 + i
        text = f"GMT-{unit_number}"
        
        img_copy = base_img.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Gambar teks di body
        draw.text(POS_BODY, text, font=font_body, fill=COLOR_BODY)
        
        # Hitung ukuran teks depan untuk kotak background
        bbox = draw.textbbox(POS_FRONT, text, font=font_front)
        # Tambahkan padding (jarak antara teks dan batas kotak)
        pad_x, pad_y = 10, 5
        rect_bbox = [bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y]
        
        # Gambar kotak biru muda
        draw.rectangle(rect_bbox, fill=BG_COLOR_FRONT)
        
        # Gambar teks di depan
        draw.text(POS_FRONT, text, font=font_front, fill=COLOR_FRONT)
        
        final_img = img_copy.convert("RGB")
        out_path = os.path.join(OUTPUT_DIR, f"{text}.jpg")
        final_img.save(out_path, "JPEG", quality=95)
        print(f"Berhasil membuat: {out_path}")

if __name__ == "__main__":
    print("Memulai proses generate gambar GMT (GMT-701 - GMT-730)...")
    generate_truck_images(1, 30)
    print("Selesai! Gambar tersimpan di folder 'output_gmt'.")
