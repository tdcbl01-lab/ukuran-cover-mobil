from datetime import datetime
import os
import re
import base64
import pandas as pd
import requests
import streamlit as st

# Konfigurasi halaman (Harus paling atas)
st.set_page_config(page_title="Aplikasi Cover Mobil TDC")

# Folder penyimpanan foto
FOTO_FOLDER = "foto_cover"
if not os.path.exists(FOTO_FOLDER):
  os.makedirs(FOTO_FOLDER)

# CSS dasar untuk tabel
st.markdown(
    """
    <style>
        [data-testid="stDataFrame"] { width: 100% !important; }
        .stDataFrame table { width: 100% !important; }
    </style>
""",
    unsafe_allow_html=True,
)

EXCEL_FILE = "data_cover.xlsx"


# --- FUNGSI INTEGRASI GITHUB ---
def sync_to_github_background(file_path):
  try:
    if "data_cover" not in file_path or os.path.basename(file_path).startswith("~$"):
      return

    if "github" in st.secrets and os.path.exists(file_path):
      gh = st.secrets["github"]
      token = gh.get("token")
      repo = gh.get("repo")
      branch = gh.get("branch", "main")

      if token and repo:
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        sha = None
        r_get = requests.get(url, headers=headers)
        if r_get.status_code == 200:
          sha = r_get.json().get("sha")

        with open(file_path, "rb") as f:
          content_bytes = f.read()
        content_encoded = base64.b64encode(content_bytes).decode("utf-8")

        payload = {
            "message": f"Auto-sync data_cover.xlsx via Streamlit {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content_encoded,
            "branch": branch,
        }
        if sha:
          payload["sha"] = sha

        requests.put(url, json=payload, headers=headers)
  except Exception:
    pass


# Fungsi memuat data (Aman & Mengabaikan file temp Windows)
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
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
      
  df_dummy = pd.DataFrame(columns=[
      "ID", "Merek", "Model", "Tahun", "Ukuran", 
      "Panjang", "Lebar", "Tinggi", "Status", "Catatan", 
      "Foto1", "Foto2", "Foto3", "Foto4",
  ])
  return df_dummy