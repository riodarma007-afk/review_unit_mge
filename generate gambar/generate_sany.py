from PIL import Image, ImageDraw, ImageFont
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- KONFIGURASI ---
INPUT_IMAGE = os.path.join(BASE_DIR, 'Sany.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_sany')
# Path ke font
FONT_PATH = r'C:\Users\Domain Expansion\AppData\Local\Microsoft\Windows\Fonts\Swiss 721 Condensed Bold.otf'

# Konfigurasi Teks 1 (Di tengah vesel / body putih)
POS_BODY = (1800, 700) # Estimasi koordinat X, Y untuk tulisan body Sany
FONT_SIZE_BODY = 80
COLOR_BODY = (43, 58, 66) # Warna abu-abu gelap

# Konfigurasi Teks 2 (Di pintu/depan) - Sesuaikan jika perlu
POS_FRONT = (345, 870) # Estimasi koordinat X, Y untuk tulisan pintu depan
FONT_SIZE_FRONT = 45
COLOR_FRONT = (255, 255, 255) # Warna putih
BG_COLOR_FRONT = (0, 0, 255) # Biru GHT

# Path Logo
LOGO_PATH = os.path.join(BASE_DIR, 'logo_mge.png')

# Konfigurasi Logo MGE
LOGO_SCALE = 1.2      # Skala tinggi logo relatif terhadap tinggi teks (1.0 = sama tinggi dengan teks)
LOGO_PADDING_RIGHT = 10 # Jarak (spasi) antara logo dengan teks GHT
LOGO_OFFSET_Y = 0     # Geser logo ke atas (minus) atau ke bawah (plus) jika kurang sejajar

def generate_truck_images(start=41, end=50):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    try:
        base_img = Image.open(INPUT_IMAGE).convert("RGBA")
    except Exception as e:
        print(f"Gagal membuka {INPUT_IMAGE}: {e}")
        return

    try:
        logo_img = Image.open(LOGO_PATH).convert("RGBA")
    except Exception as e:
        logo_img = None
        print(f"Gagal membuka logo {LOGO_PATH}: {e}")

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
        text = f"GHT-{unit_number}"
        
        img_copy = base_img.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Gambar teks di body
        draw.text(POS_BODY, text, font=font_body, fill=COLOR_BODY, anchor="mm")
        
        if logo_img:
            # Hitung bounding box teks body untuk menempelkan logo
            bbox_body = draw.textbbox(POS_BODY, text, font=font_body, anchor="mm")
            text_height = bbox_body[3] - bbox_body[1]
            
            # Ubah ukuran logo agar tingginya proporsional dengan teks
            aspect_ratio = logo_img.width / logo_img.height
            logo_h = int(text_height * LOGO_SCALE)
            logo_w = int(logo_h * aspect_ratio)
            logo_resized = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            
            # Posisi logo di sebelah kiri teks
            logo_x = int(bbox_body[0] - logo_w - LOGO_PADDING_RIGHT)
            logo_y = int(bbox_body[1] - (logo_h - text_height) / 2) + LOGO_OFFSET_Y
            
            img_copy.paste(logo_resized, (logo_x, logo_y), logo_resized)
        
        # Hitung ukuran teks depan untuk kotak background
        bbox = draw.textbbox((POS_FRONT[0], POS_FRONT[1]), text, font=font_front, anchor="mm")
        # Tambahkan padding (jarak antara teks dan batas kotak)
        pad_x, pad_y = 15, 8
        rect_bbox = [bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y]
        
        # Gambar kotak merah
        draw.rectangle(rect_bbox, fill=BG_COLOR_FRONT)
        
        # Gambar teks di depan
        draw.text((POS_FRONT[0], POS_FRONT[1]), text, font=font_front, fill=COLOR_FRONT, anchor="mm")
        
        final_img = img_copy.convert("RGB")
        out_path = os.path.join(OUTPUT_DIR, f"{text}.jpg")
        final_img.save(out_path, "JPEG", quality=95)
        print(f"Berhasil membuat: {out_path}")

if __name__ == "__main__":
    print("Memulai proses generate gambar SANY (GMT 741 - 750)...")
    generate_truck_images(41, 50)
    print("Selesai! Gambar tersimpan di folder 'output_sany'.")
