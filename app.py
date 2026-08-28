from datetime import datetime
import os
import re
import base64
import pandas as pd
import requests
import streamlit as st

# Konfigurasi halaman
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


# --- FUNGSI SIMPAN UTAMA LANGSUNG KE GITHUB (ANTI HILANG) ---
def save_to_github_directly(df_target, file_path, commit_message):
  try:
    if "github" in st.secrets:
      gh = st.secrets["github"]
      token = gh.get("token")
      repo = gh.get("repo")
      branch = gh.get("branch", "main")

      if token and repo:
        # Simpan lokal terlebih dahulu untuk dibaca bytes-nya
        df_target.to_excel(file_path, index=False)
        
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        
        # Ambil SHA terbaru agar tidak terjadi konflik commit di GitHub
        sha = None
        r_get = requests.get(url, headers=headers)
        if r_get.status_code == 200:
          sha = r_get.json().get("sha")

        with open(file_path, "rb") as f:
          content_bytes = f.read()
        content_encoded = base64.b64encode(content_bytes).decode("utf-8")

        payload = {
            "message": commit_message,
            "content": content_encoded,
            "branch": branch,
        }
        if sha:
          payload["sha"] = sha
          
        r_put = requests.put(url, json=payload, headers=headers)
        if r_put.status_code in [200, 201]:
          return True
    return False
  except Exception as e:
    st.error(f"Gagal koneksi ke GitHub: {e}")
    return False


# Fungsi memuat data stabil dengan cache
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
  if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
    for i in range(1, 5):
      col_name = f"Foto{i}"
      if col_name not in df.columns:
        df[col_name] = ""
    return df
  else:
    df_dummy = pd.DataFrame(columns=[
        "ID", "Merek", "Model", "Tahun", "Ukuran", "Panjang", "Lebar", "Tinggi", "Status", "Catatan", "Foto1", "Foto2", "Foto3", "Foto4"
    ])
    df_dummy.to_excel(EXCEL_FILE, index=False)
    return df_dummy


df = load_data()
df.columns = df.columns.str.strip()
for i in range(1, 5):
  if f"Foto{i}" not in df.columns:
    df[f"Foto{i}"] = ""


def get_next_id():
  if os.path.exists(EXCEL_FILE):
    df_check = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
  else:
    df_check = df

  if not df_check.empty and "ID" in df_check.columns:
    try:
      valid_ids = pd.to_numeric(df_check["ID"], errors="coerce").dropna()
      if not valid_ids.empty:
        return int(valid_ids.max()) + 1
    except Exception:
      pass
  return 1


def highlight_cols(x):
  df_styler = pd.DataFrame("", index=x.index, columns=x.columns)
  df_styler.iloc[:, 0] = "background-color: #f0f2f6"
  df_styler.iloc[:, 4] = (
      "background-color: #fff3cd; font-weight: bold; color: #856404;"
  )
  df_styler.iloc[:, 8] = "color: #ff4b4b; font-weight: bold"
  return df_styler


if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

col_logo, col_tagline = st.columns([1, 2])
with col_logo:
  st.image("Logo TDC.png", width=160)
with col_tagline:
  st.markdown(
      """
    <div style="display: flex; align-items: center; height: 100%; padding-top: 18px;">
        <h4 style="color: #555; font-style: italic; font-weight: 600; margin: 0; letter-spacing: 0.5px;">Automotive Accessories</h4>
    </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)

if "menu_pilihan" not in st.session_state:
  st.session_state["menu_pilihan"] = "🔍 Cari Ukuran Cover"

def update_menu():
  st.session_state["menu_pilihan"] = st.session_state["widget_pills_menu"]

st.markdown("<style>div.stPills { margin-bottom: -15px; }</style>", unsafe_allow_html=True)
st.pills(
    "Pilih Menu:",
    ["🔍 Cari Ukuran Cover", "📊 Filter Berdasarkan Ukuran", "📂 Filter Merek & Model", "➕ Tambah / Edit Data"],
    key="widget_pills_menu",
    default=st.session_state["menu_pilihan"],
    on_change=update_menu,
    label_visibility="collapsed",
)

menu = st.session_state["menu_pilihan"]
st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)

def tampilkan_detail_tambahan(hasil_row):
  catatan_val = hasil_row["Catatan"].values[0]
  if catatan_val and catatan_val != "nan" and catatan_val != "None":
    st.info(f"**Catatan & Riwayat Edit:** {catatan_val}")

  list_foto_tersedia = []
  for i in range(1, 5):
    kol_foto = f"Foto{i}"
    if kol_foto in hasil_row.columns:
      val_foto = str(hasil_row[kol_foto].values[0]).strip()
      if val_foto and val_foto != "nan" and val_foto != "None":
        path_foto = os.path.join(FOTO_FOLDER, val_foto)
        if os.path.exists(path_foto):
          list_foto_tersedia.append((path_foto, f"Foto {i} - {hasil_row['Merek'].values[0]} {hasil_row['Model'].values[0]}"))

  if list_foto_tersedia:
    st.markdown("### 📸 Foto Dokumentasi:")
    for i in range(0, len(list_foto_tersedia), 2):
      cols = st.columns(2)
      for j in range(2):
        if i + j < len(list_foto_tersedia):
          p_file, cap_text = list_foto_tersedia[i + j]
          with cols[j]:
            st.image(p_file, caption=cap_text, use_container_width=True)

kolom_sembunyi = ["Catatan", "Pilihan_Edit", "Foto1", "Foto2", "Foto3", "Foto4"]

if menu == "🔍 Cari Ukuran Cover":
  st.title("Daftar Ukuran Cover Mobil")
  if df.empty:
    st.warning("Data belum ada.")
  else:
    daftar_merek = sorted([m for m in df["Merek"].dropna().unique() if m != ""])
    if not daftar_merek:
      st.warning("Data belum tersedia.")
    else:
      merek_pilihan = st.selectbox("Pilih Merek:", daftar_merek)
      df_merk = df[df["Merek"] == merek_pilihan]
      daftar_model = sorted([m for m in df_merk["Model"].dropna().unique() if m != ""])
      model_pilihan = st.selectbox("Pilih Model:", daftar_model)
      df_model = df_merk[df_merk["Model"] == model_pilihan]
      daftar_tahun = sorted([t for t in df_model["Tahun"].dropna().unique() if t != ""])
      tahun_pilihan = st.selectbox("Pilih Tahun:", daftar_tahun)

      hasil = df_model[(df_model["Tahun"] == tahun_pilihan) & (df_model["Merek"] != "") & (df_model["Merek"].notna())]
      hasil = hasil[hasil["ID"].astype(str).str.strip() != ""]

      if not hasil.empty:
        st.write("### Hasil Pencarian:")
        st.dataframe(hasil.drop(columns=kolom_sembunyi, errors="ignore").style.apply(highlight_cols, axis=None), use_container_width=True, hide_index=True)
        tampilkan_detail_tambahan(hasil)
      else:
        st.info("Data belum tersedia untuk pilihan ini.")

elif menu == "📊 Filter Berdasarkan Ukuran":
  st.title("Daftar Mobil Berdasarkan Ukuran Cover")
  if df.empty:
    st.warning("Data belum ada.")
  else:
    daftar_ukuran = sorted([u for u in df["Ukuran"].dropna().unique() if u != ""])
    if not daftar_ukuran:
      st.warning("Data ukuran belum tersedia.")
    else:
      ukuran_pilihan = st.selectbox("Pilih Ukuran Cover:", daftar_ukuran)
      df_filter_ukuran = df[(df["Ukuran"] == ukuran_pilihan) & (df["ID"].astype(str).str.strip() != "")]
      if not df_filter_ukuran.empty:
        st.write(f"### Daftar Mobil dengan Ukuran **{ukuran_pilihan}**:")
        st.dataframe(df_filter_ukuran.drop(columns=kolom_sembunyi, errors="ignore").style.apply(highlight_cols, axis=None), use_container_width=True, hide_index=True)
      else:
        st.info("Tidak ada data mobil untuk ukuran ini.")

elif menu == "📂 Filter Merek & Model":
  st.title("Filter Berdasarkan Merek & Model")
  if df.empty:
    st.warning("Data belum ada.")
  else:
    daftar_merek_fm = sorted([m for m in df["Merek"].dropna().unique() if m != ""])
    if not daftar_merek_fm:
      st.warning("Data merek belum tersedia.")
    else:
      merek_fm_pilihan = st.selectbox("Pilih Merek:", daftar_merek_fm, key="fm_merek")
      df_fm_merek = df[df["Merek"] == merek_fm_pilihan]
      keyword_model = st.text_input("Cari / Filter Kata Kunci Model (contoh: Yaris):", "")
      df_hasil_fm = df_fm_merek[df_fm_merek["Model"].str.contains(keyword_model, case=False, na=False)] if keyword_model.strip() != "" else df_fm_merek
      df_hasil_fm = df_hasil_fm[df_hasil_fm["ID"].astype(str).str.strip() != ""]
      if not df_hasil_fm.empty:
        st.dataframe(df_hasil_fm.drop(columns=kolom_sembunyi, errors="ignore").style.apply(highlight_cols, axis=None), use_container_width=True, hide_index=True)
      else:
        st.info("Tidak ada data mobil yang cocok.")

elif menu == "➕ Tambah / Edit Data":
  st.title("Kelola Data Cover Mobil")

  if not st.session_state["logged_in"]:
    password_input = st.text_input("Masukkan Password Admin:", type="password")
    if st.button("🔑 Login"):
      if password_input == "admin123":
        st.session_state["logged_in"] = True
        st.rerun()
      else:
        st.error("Password Salah!")
  else:
    if st.button("🔓 Logout"):
      st.session_state["logged_in"] = False
      st.rerun()

    st.success("Akses Diterima!")

    if "notif_sukses" in st.session_state:
      st.success(st.session_state["notif_sukses"])
      del st.session_state["notif_sukses"]

    mode_kelola = st.pills("Pilih Aksi:", ["➕ Tambah Data Baru", "✏️ Edit Data yang Ada"], label_visibility="collapsed")
    st.markdown("<hr style='margin-top: 2px; margin-bottom: 10px;'>", unsafe_allow_html=True)

    kolom_wajib = ["Merek", "Model", "Tahun", "Ukuran", "Panjang", "Lebar", "Tinggi", "Status"]
    kolom_foto_list = ["Foto1", "Foto2", "Foto3", "Foto4"]

    list_merek_excel = sorted(list(set([str(m).strip() for m in df["Merek"].dropna().unique() if str(m).strip() != "" and str(m).lower() != "nan"])))
    if not list_merek_excel:
      list_merek_excel = ["Toyota", "Honda", "Daihatsu", "Suzuki"]

    list_status_fix = ["STANDAR", "HARUS CUSTOM"]

    if mode_kelola == "➕ Tambah Data Baru":
      next_id = get_next_id()

      st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)
      st.markdown("ID <span style='color:gray;'>(Otomatis)</span>", unsafe_allow_html=True)
      st.text_input("ID Display", value=str(next_id), disabled=True, label_visibility="collapsed")

      st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
      input_merek = st.selectbox("Merek Input", list_merek_excel, index=0, label_visibility="collapsed", accept_new_options=True)

      st.markdown("Model <span style='color:red;'>*</span>", unsafe_allow_html=True)
      input_model = st.text_input("Model Input", placeholder="Contoh: Avanza", label_visibility="collapsed")

      st.markdown("Tahun <span style='color:red;'>*</span>", unsafe_allow_html=True)
      input_tahun = st.text_input("Tahun Input", placeholder="Contoh: 2018-2023", label_visibility="collapsed")

      input_sisa_data = {}
      for col in df.columns:
        if col not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
          if col in kolom_wajib:
            st.markdown(f"{col} <span style='color:red;'>*</span>", unsafe_allow_html=True)
            input_sisa_data[col] = st.text_input(f"in_{col}", label_visibility="collapsed")
          else:
            input_sisa_data[col] = st.text_input(f"in_{col}")

      st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
      input_status = st.selectbox("Status Input", list_status_fix, label_visibility="collapsed")

      st.markdown("---")
      st.markdown("### 📸 Upload Foto Dokumentasi:")
      uploaded_files = {}
      c1, c2 = st.columns(2)
      with c1:
        uploaded_files["Foto1"] = st.file_uploader("Foto 1", type=["jpg", "jpeg", "png"], key="up_t1")
        uploaded_files["Foto2"] = st.file_uploader("Foto 2", type=["jpg", "jpeg", "png"], key="up_t2")
      with c2:
        uploaded_files["Foto3"] = st.file_uploader("Foto 3", type=["jpg", "jpeg", "png"], key="up_t3")
        uploaded_files["Foto4"] = st.file_uploader("Foto 4", type=["jpg", "jpeg", "png"], key="up_t4")

      if st.button("💾 Simpan Data ke Excel", type="primary"):
        if not str(input_merek).strip() or not str(input_model).strip() or not str(input_tahun).strip():
          st.error("❌ Gagal! Merek, Model, dan Tahun wajib diisi!")
        else:
          baru_data = {
              "ID": str(next_id),
              "Merek": str(input_merek).strip(),
              "Model": str(input_model).strip(),
              "Tahun": str(input_tahun).strip(),
              "Status": str(input_status).strip()
          }
          for k, v in input_sisa_data.items():
            baru_data[k] = str(v).strip()

          timestamp_awalan = int(datetime.now().timestamp())
          for key_f, up_f in uploaded_files.items():
            if up_f is not None:
              nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
              path_simpan = os.path.join(FOTO_FOLDER, nama_file_foto)
              with open(path_simpan, "wb") as f:
                f.write(up_f.getbuffer())
              baru_data[key_f] = nama_file_foto
            else:
              baru_data[key_f] = ""

          if os.path.exists(EXCEL_FILE):
            df_fisik = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
            df_fisik.columns = df_fisik.columns.str.strip()
          else:
            df_fisik = pd.DataFrame(columns=list(baru_data.keys()))

          for c in df_fisik.columns:
            if c not in baru_data:
              baru_data[c] = ""

          df_baru_item = pd.DataFrame([baru_data])
          df_final = pd.concat([df_fisik, df_baru_item], ignore_index=True)
          
          # SIMPAN LANGSUNG KE GITHUB
          sukses_github = save_to_github_directly(df_final, EXCEL_FILE, f"Tambah data ID {next_id} via Streamlit")
          
          if sukses_github:
            st.cache_data.clear()
            st.session_state["notif_sukses"] = "🎉 BERHASIL! Data tersimpan permanen ke GitHub & file Excel."
            st.rerun()
          else:
            st.error("❌ Gagal menyimpan ke GitHub! Pastikan pengaturan secrets GitHub di Streamlit sudah benar.")

    else:
      df_aktif = df[df["ID"].astype(str).str.strip() != ""]
      if df_aktif.empty:
        st.info("Data kosong.")
      else:
        df_aktif = df_aktif.copy()
        df_aktif["Pilihan_Edit"] = df_aktif.index.astype(str) + " - " + df_aktif["Merek"] + " " + df_aktif["Model"]
        idx_str = st.selectbox("Pilih Data:", df_aktif["Pilihan_Edit"].unique())
        idx_pilih = int(idx_str.split(" - ")[0])

        foto_lama = {}
        for i in range(1, 5):
          k_f = f"Foto{i}"
          val_F = str(df.loc[idx_pilih, k_f]) if k_f in df.columns else ""
          foto_lama[k_f] = "" if val_F in ["nan", "None"] else val_F

        st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)
        update = {}

        merek_lama = str(df.loc[idx_pilih, "Merek"]) if "Merek" in df.columns else ""
        if merek_lama not in list_merek_excel and merek_lama.strip() != "":
          list_merek_excel.append(merek_lama)
          list_merek_excel.sort()

        default_idx_merek = list_merek_excel.index(merek_lama) if merek_lama in list_merek_excel else 0
        st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
        update["Merek"] = st.selectbox("Merek Edit", list_merek_excel, index=default_idx_merek, label_visibility="collapsed", accept_new_options=True)

        for col in df.columns:
          if col not in ["ID", "Pilihan_Edit", "Merek", "Status"] + kolom_foto_list:
            val_lama = str(df.loc[idx_pilih, col]) if col in df.columns else ""
            if val_lama in ["nan", "None"]:
              val_lama = ""
            if col == "Catatan" and val_lama:
              val_lama = re.sub(r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$", "", val_lama).strip()

            if col in kolom_wajib:
              st.markdown(f"{col} <span style='color:red;'>*</span>", unsafe_allow_html=True)
              update[col] = st.text_input(f"edit_{col}", value=val_lama, label_visibility="collapsed")
            else:
              update[col] = st.text_input(f"edit_{col}", value=val_lama)

        status_lama = str(df.loc[idx_pilih, "Status"]) if "Status" in df.columns else "STANDAR"
        if status_lama not in list_status_fix:
          status_lama = "STANDAR"
        default_idx_status = list_status_fix.index(status_lama)

        st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
        update["Status"] = st.selectbox("Status Edit", list_status_fix, index=default_idx_status, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### 📸 Ganti Foto Dokumentasi:")
        uploaded_files_edit = {}
        c1, c2 = st.columns(2)
        with c1:
          uploaded_files_edit["Foto1"] = st.file_uploader("Ganti Foto 1", type=["jpg", "jpeg", "png"], key="up_e1")
          uploaded_files_edit["Foto2"] = st.file_uploader("Ganti Foto 2", type=["jpg", "jpeg", "png"], key="up_e2")
        with c2:
          uploaded_files_edit["Foto3"] = st.file_uploader("Ganti Foto 3", type=["jpg", "jpeg", "png"], key="up_e3")
          uploaded_files_edit["Foto4"] = st.file_uploader("Ganti Foto 4", type=["jpg", "jpeg", "png"], key="up_e4")

        if st.button("✏️ Update / Simpan Perubahan", type="primary"):
          if any(not str(update.get(k)).strip() for k in kolom_wajib):
            st.error("❌ Gagal! Kolom wajib termasuk Merek harus diisi!")
          else:
            if os.path.exists(EXCEL_FILE):
              df_fisik = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
              df_fisik.columns = df_fisik.columns.str.strip()
            else:
              df_fisik = df.copy()

            waktu_sekarang = datetime.now().strftime("%d-%m-%Y %H:%M")
            catatan_input_user = update.get("Catatan", "")
            catatan_bersih = re.sub(r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$", "", catatan_input_user).strip()
            update["Catatan"] = f"{catatan_bersih} | Terakhir diedit: {waktu_sekarang}" if catatan_bersih else f"Terakhir diedit: {waktu_sekarang}"

            timestamp_awalan = int(datetime.now().timestamp())
            for key_f, up_f in uploaded_files_edit.items():
              if up_f is not None:
                nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
                path_simpan = os.path.join(FOTO_FOLDER, nama_file_foto)
                with open(path_simpan, "wb") as f:
                  f.write(up_f.getbuffer())
                update[key_f] = nama_file_foto
              else:
                update[key_f] = foto_lama[key_f]

            for k, v in update.items():
              if k in df_fisik.columns and idx_pilih < len(df_fisik):
                df_fisik.loc[idx_pilih, k] = v

            # SIMPAN PERUBAHAN LANGSUNG KE GITHUB
            sukses_github = save_to_github_directly(df_fisik, EXCEL_FILE, f"Edit data index {idx_pilih} via Streamlit")

            if sukses_github:
              st.cache_data.clear()
              st.session_state["notif_sukses"] = "✏️ Data berhasil diperbarui dan tersimpan permanen ke GitHub & Excel!"
              st.rerun()
            else:
              st.error("❌ Gagal memperbarui ke GitHub! Pastikan token secrets aktif.")