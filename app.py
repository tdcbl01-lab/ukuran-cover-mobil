# Fungsi memuat data (Aman & Mengabaikan file temp Windows)
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
  # Pastikan tidak membaca file lock/temp Excel
  target_file = EXCEL_FILE
  if target_file.startswith("~$"):
    target_file = "data_cover.xlsx"

  if os.path.exists(target_file) and not target_file.startswith("~$"):
    try:
      df = pd.read_excel(target_file, dtype=str, keep_default_na=False)
      for i in range(1, 5):
        col_name = f"Foto{i}"
        if col_name not in df.columns:
          df[col_name] = ""
      return df
    except Exception:
      pass
      
  # Fallback buat dummy jika file utama belum ada
  df_dummy = pd.DataFrame(columns=[
      "ID", "Merek", "Model", "Tahun", "Ukuran", 
      "Panjang", "Lebar", "Tinggi", "Status", "Catatan", 
      "Foto1", "Foto2", "Foto3", "Foto4",
  ])
  return df_dummy