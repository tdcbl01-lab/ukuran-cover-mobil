import streamlit as st
import pandas as pd
import os

# Konfigurasi halaman web
st.set_page_config(
    page_title="Cek Ukuran Cover Mobil - TDC Variasi",
    page_icon="🚗",
    layout="centered"
)

# Judul Aplikasi
st.title("🚗 Cek Ukuran & Tipe Cover Mobil")
st.write("TDC Variasi - Custom Car & Motorcycle Cover")

# Fungsi untuk memuat data Excel dengan aman
@st.cache_data
def load_data():
    file_path = 'data_cover.xlsx'
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        return df
    else:
        return None

data = load_data()

# Cek apakah file Excel tersedia
if data is not None:
    # Bersihkan nama kolom dari spasi berlebih jika ada
    data.columns = data.columns.str.strip()
    
    # Pastikan kolom yang dibutuhkan ada di Excel
    # Sesuaikan 'Merek' dan 'Model' dengan nama kolom asli di Excel kamu kalau berbeda
    kolom_merek = 'Merek' if 'Merek' in data.columns else data.columns[0]
    kolom_model = 'Model' if 'Model' in data.columns else data.columns[1]

    st.markdown("---")
    st.subheader("🔍 Pilih Kendaraan")

    # 1. Pilih Merek Mobil (Otomatis ada fitur ketik/search di HP)
    daftar_merek = sorted(data[kolom_merek].dropna().unique())
    merek_pilihan = st.selectbox("Pilih Merek Mobil:", daftar_merek)

    # Filter data berdasarkan merek yang dipilih
    data_filtered_merek = data[data[kolom_merek] == merek_pilihan]

    # 2. Pilih Model Mobil dari merek tersebut
    daftar_model = sorted(data_filtered_merek[kolom_model].dropna().unique())
    model_pilihan = st.selectbox("Pilih Model / Tahun Mobil:", daftar_model)

    # Ambil data spesifik untuk mobil yang dipilih
    row_data = data_filtered_merek[data_filtered_merek[kolom_model] == model_pilihan].iloc[0]

    st.markdown("---")
    st.subheader("📋 Detail Ukuran & Informasi")

    # Tampilkan informasi detail (sesuaikan kolom lain sesuai isi Excel kamu)
    st.success(f"**Pilihan Kamu:** {merek_pilihan} - {model_pilihan}")

    # Menampilkan sisa kolom yang ada di excel secara otomatis
    for col in data.columns:
        if col not in [kolom_merek, kolom_model]:
            val = row_data[col]
            if pd.notna(val):
                st.write(f"**{col}:** {val}")

    # Contoh menampilkan gambar jika ada kolom foto atau folder foto_cover
    # (Opsional, bagian ini bisa disesuaikan dengan struktur foto kamu)
    
else:
    st.error("⚠️ File `data_cover.xlsx` tidak ditemukan di dalam folder! Pastikan file Excel-nya sudah ada di sebelah file `app.py`.")