import base64
import os
import pandas as pd
import requests
import streamlit as st


# --- FUNGSI AUTO-SYNC KE GITHUB ---
def push_to_github(file_path, commit_message):
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["REPO_NAME"]
  except Exception:
    # Jika secrets belum diset, lewati proses push otomatis
    return

  url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
  headers = {
      "Authorization": f"token {token}",
      "Accept": "vnd.github.v3+json",
  }

  # Cek SHA file di GitHub
  response = requests.get(url, headers=headers)
  sha = None
  if response.status_code == 200:
    sha = response.json().get("sha")

  # Baca file lokal dan encode ke base64
  if os.path.exists(file_path):
    with open(file_path, "rb") as f:
      content_bytes = f.read()
    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

    data = {"message": commit_message, "content": content_base64, "branch": "main"}
    if sha:
      data["sha"] = sha

    # Kirim update ke GitHub API
    requests.put(url, headers=headers, json=data)


# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(page_title="TDC Variasi - Data App", layout="wide")

st.title("🚗 TDC Variasi - Manajemen Data & Katalog")
st.write("Aplikasi terhubung dengan penyimpanan otomatis ke GitHub.")

# Nama file Excel utama
EXCEL_FILE = "data.xlsx"

# Contoh inisialisasi data jika file belum ada
if not os.path.exists(EXCEL_FILE):
  df_default = pd.DataFrame(
      columns=["No", "Kategori", "Judul Produk", "Karakter"]
  )
  df_default.to_excel(EXCEL_FILE, index=False)

# Memuat data
df = pd.read_excel(EXCEL_FILE)

st.subheader("Data Produk Saat Ini")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

if st.button("Simpan Perubahan & Sinkronkan ke GitHub"):
  # Simpan ke file excel lokal
  edited_df.to_excel(EXCEL_FILE, index=False)

  # Kirim otomatis ke GitHub
  push_to_github(EXCEL_FILE, "Update data Excel via aplikasi Streamlit")

  st.success("Data berhasil disimpan dan disinkronkan ke GitHub secara otomatis!")