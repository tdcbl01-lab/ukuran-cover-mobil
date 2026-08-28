EXCEL_FILE = "data_cover.xlsx"

# --- FUNGSI INTEGRASI GITHUB ---
def sync_to_github_background(file_path):
  try:
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


# Fungsi memuat data (tanpa cache yang mengunci saat simpan)
def load_data_fresh():
  if os.path.exists(EXCEL_FILE):
    df_load = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
    df_load.columns = df_load.columns.str.strip()
    for i in range(1, 5):
      col_name = f"Foto{i}"
      if col_name not in df_load.columns:
        df_load[col_name] = ""
    return df_load
  else:
    df_dummy = pd.DataFrame(columns=[
        "ID", "Merek", "Model", "Tahun", "Ukuran", "Panjang", "Lebar", "Tinggi", "Status", "Catatan", "Foto1", "Foto2", "Foto3", "Foto4"
    ])
    df_dummy.to_excel(EXCEL_FILE, index=False)
    return df_dummy

# Muat dataframe aktif
df = load_data_fresh()

# Fungsi ID otomatis dari data paling fresh
def get_next_id():
  df_id = load_data_fresh()
  if not df_id.empty and "ID" in df_id.columns:
    try:
      valid_ids = pd.to_numeric(df_id["ID"], errors="coerce").dropna()
      if not valid_ids.empty:
        return int(valid_ids.max()) + 1
    except Exception:
      pass
  return 1