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
    
    # Deteksi nama kolom Merek dan Model
    kolom_merek = 'Merek' if 'Merek' in data.columns else data.columns[0]
    kolom_model = 'Model' if 'Model' in data.columns else data.columns[1]

    st.markdown("---")
    st.subheader("🔍 Pilih Kendaraan")

    # 1. Pilih Merek Mobil (Bertahap supaya mudah di HP)
    daftar_merek = sorted(data[kolom_merek].dropna().unique())
    merek_pilihan = st.selectbox("Pilih Merek Mobil:", daftar_merek)

    # Filter data berdasarkan merek yang dipilih
    data_filtered_merek = data[data[kolom_merek] == merek_pilihan]

    # 2. Pilih Model Mobil dari merek tersebut
    daftar_model = sorted(data_filtered_merek[kolom_model].dropna().unique())
    model_pilihan = st.selectbox("Pilih Model / Tahun Mobil:", daftar_model)

    # Ambil data spesifik untuk baris mobil yang dipilih
    row_data = data_filtered_merek[data_filtered_merek[kolom_model] == model_pilihan].iloc[0]

    st.markdown("---")
    st.subheader("📋 Detail Spesifikasi Cover Mobil")

    # Kotak hijau info pilihan kendaraan
    st.success(f"**Kendaraan Dipilih:** {merek_pilihan} - {model_pilihan}")

    # Tampilan kotak-kotak rapi per informasi penting
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Tahun' in row_data and pd.notna(row_data['Tahun']):
            st.info(f"📅 **Tahun:** {row_data['Tahun']}")
        if 'Ukuran' in row_data and pd.notna(row_data['Ukuran']):
            st.warning(f"📏 **Ukuran Cover:** {row_data['Ukuran']}")

    with col2:
        if 'Status' in row_data and pd.notna(row_data['Status']):
            st.error(f"📌 **Status:** {row_data['Status']}")

    # Dimensi lengkap
    panjang = row_data.get('Panjang', '-')
    lebar = row_data.get('Lebar', '-')
    tinggi = row_data.get('Tinggi', '-')
    st.markdown(f"**🚗 Dimensi (P x L x T):** {panjang} x {lebar} x {tinggi}")

    # Catatan khusus jika ada di Excel
    if 'Catatan' in row_data and pd.notna(row_data['Catatan']):
        st.markdown(f"**📝 Catatan Tambahan:**\n> {row_data['Catatan']}")

else:
    st.error("⚠️ File `data_cover.xlsx` tidak ditemukan di dalam folder! Pastikan file Excel-nya ada di sebelah file `app.py`.")