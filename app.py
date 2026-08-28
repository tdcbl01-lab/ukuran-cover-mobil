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


# Fungsi memuat data langsung dari file fisik (Tanpa Cache yang bikin nyangkut)
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


df = load_data()
df.columns = df.columns.str.strip()
for i in range(1, 5):
  if f"Foto{i}" not in df.columns:
    df[f"Foto{i}"] = ""


# Fungsi untuk menentukan ID berikutnya secara akurat (Anti-Loncat)
def get_next_id():
  df_check = None
  if os.path.exists(EXCEL_FILE) and not EXCEL_FILE.startswith("~$"):
    try:
      df_check = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
    except Exception:
      pass
  
  if df_check is None or df_check.empty:
    df_check = df

  if not df_check.empty and "ID" in df_check.columns:
    try:
      valid_ids = pd.to_numeric(df_check["ID"].astype(str).str.strip(), errors="coerce").dropna()
      if not valid_ids.empty:
        return int(valid_ids.max()) + 1
    except Exception:
      pass
      
  return 1


# --- FUNGSI STYLING TABEL ---
def highlight_cols(x):
  df_styler = pd.DataFrame("", index=x.index, columns=x.columns)
  df_styler.iloc[:, 0] = "background-color: #f0f2f6"
  df_styler.iloc[:, 4] = (
      "background-color: #fff3cd; font-weight: bold; color: #856404;"
  )
  df_styler.iloc[:, 8] = "color: #ff4b4b; font-weight: bold"
  return df_styler


# --- LOGIKA DIALOG POP-UP SIMPAN & EDIT ---
@st.dialog("⚠️ Konfirmasi Simpan Data")
def dialog_konfirmasi_tambah(data_baru):
  st.write("Apakah data sudah benar?")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("✅ Ya, Simpan", use_container_width=True):
      try:
        if os.path.exists(EXCEL_FILE):
          current_df = pd.read_excel(
              EXCEL_FILE, dtype=str, keep_default_na=False
          )
        else:
          current_df = df

        data_baru["ID"] = str(get_next_id())

        updated_df = pd.concat(
            [current_df, pd.DataFrame([data_baru])], ignore_index=True
        )
        updated_df.to_excel(EXCEL_FILE, index=False)
        sync_to_github_background(EXCEL_FILE)

        st.session_state["notif_sukses"] = (
            f"✅ Data Calya (ID {data_baru['ID']}) berhasil disimpan permanen ke Excel & GitHub!"
        )
        st.rerun()

      except PermissionError:
        st.error(
            "❌ **GAGAL SIMPAN!** File `data_cover.xlsx` sedang terbuka di"
            " Microsoft Excel. Tutup file Excel-nya terlebih dahulu!"
        )
      except Exception as e:
        st.error(f"❌ Terjadi kesalahan sistem saat menyimpan: {e}")

  with col2:
    if st.button("❌ Batal", use_container_width=True):
      st.rerun()


@st.dialog("⚠️ Konfirmasi Perubahan Data")
def dialog_konfirmasi_edit(idx_pilih, data_update):
  st.write("Apakah data yang diubah sudah benar?")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("✅ Ya, Update", use_container_width=True):
      try:
        if os.path.exists(EXCEL_FILE):
          current_df = pd.read_excel(
              EXCEL_FILE, dtype=str, keep_default_na=False
          )
        else:
          current_df = df

        for k, v in data_update.items():
          if idx_pilih in current_df.index:
            current_df.loc[idx_pilih, k] = v

        current_df.to_excel(EXCEL_FILE, index=False)
        sync_to_github_background(EXCEL_FILE)

        st.session_state["notif_sukses"] = "✏️ Data berhasil diperbarui!"
        st.rerun()

      except PermissionError:
        st.error(
            "❌ **GAGAL UPDATE!** File `data_cover.xlsx` sedang terbuka di"
            " Microsoft Excel. Harap tutup file Excel-nya!"
        )
      except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")

  with col2:
    if st.button("❌ Batal", use_container_width=True):
      st.rerun()


# --- SISTEM LOGIN/LOGOUT ---
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

# --- HEADER (LOGO & TAGLINE) ---
col_logo, col_tagline = st.columns([1, 2])

with col_logo:
  if os.path.exists("Logo TDC.png"):
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

st.markdown(
    "<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True
)

# --- MENU PILLS ---
if "menu_pilihan" not in st.session_state:
  st.session_state["menu_pilihan"] = "🔍 Cari Ukuran Cover"


def update_menu():
  st.session_state["menu_pilihan"] = st.session_state["widget_pills_menu"]


st.markdown(
    "<style>div.stPills { margin-bottom: -15px; }</style>",
    unsafe_allow_html=True,
)

st.pills(
    "Pilih Menu:",
    [
        "🔍 Cari Ukuran Cover",
        "📊 Filter Berdasarkan Ukuran",
        "📂 Filter Merek & Model",
        "➕ Tambah / Edit Data",
    ],
    key="widget_pills_menu",
    default=st.session_state["menu_pilihan"],
    on_change=update_menu,
    label_visibility="collapsed",
)

menu = st.session_state["menu_pilihan"]
st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True
)


# ----------------- FUNGSI BANTUAN TAMPIL FOTO (GRID 2x2) -----------------
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
          list_foto_tersedia.append((
              path_foto,
              (
                  f"Foto {i} - {hasil_row['Merek'].values[0]}"
                  f" {hasil_row['Model'].values[0]}"
              ),
          ))

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

# ----------------- HALAMAN UTAMA -----------------
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

      daftar_model = sorted(
          [m for m in df_merk["Model"].dropna().unique() if m != ""]
      )
      model_pilihan = st.selectbox("Pilih Model:", daftar_model)
      df_model = df_merk[df_merk["Model"] == model_pilihan]

      daftar_tahun = sorted(
          [t for t in df_model["Tahun"].dropna().unique() if t != ""]
      )
      tahun_pilihan = st.selectbox("Pilih Tahun:", daftar_tahun)

      hasil = df_model[
          (df_model["Tahun"] == tahun_pilihan)
          & (df_model["Merek"] != "")
          & (df_model["Merek"].notna())
      ]
      hasil = hasil[hasil["ID"].astype(str).str.strip() != ""]

      if not hasil.empty:
        st.write("### Hasil Pencarian:")
        st.dataframe(
            hasil.drop(columns=kolom_sembunyi, errors="ignore").style.apply(
                highlight_cols, axis=None
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Ukuran": st.column_config.TextColumn("Ukuran", width="small"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
            },
        )
        tampilkan_detail_tambahan(hasil)
      else:
        st.info("Data belum tersedia untuk pilihan ini.")

elif menu == "📊 Filter Berdasarkan Ukuran":
  st.title("Daftar Mobil Berdasarkan Ukuran Cover")
  if df.empty:
    st.warning("Data belum ada.")
  else:
    daftar_ukuran = sorted(
        [u for u in df["Ukuran"].dropna().unique() if u != ""]
    )
    if not daftar_ukuran:
      st.warning("Data ukuran belum tersedia.")
    else:
      ukuran_pilihan = st.selectbox("Pilih Ukuran Cover:", daftar_ukuran)
      df_filter_ukuran = df[
          (df["Ukuran"] == ukuran_pilihan)
          & (df["ID"].astype(str).str.strip() != "")
      ]

      if not df_filter_ukuran.empty:
        st.write(f"### Daftar Mobil dengan Ukuran **{ukuran_pilihan}**:")
        st.dataframe(
            df_filter_ukuran.drop(
                columns=kolom_sembunyi, errors="ignore"
            ).style.apply(highlight_cols, axis=None),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Ukuran": st.column_config.TextColumn("Ukuran", width="small"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
            },
        )
        st.success(
            f"Total ada {len(df_filter_ukuran)} data mobil yang menggunakan"
            f" ukuran **{ukuran_pilihan}**."
        )
      else:
        st.info("Tidak ada data mobil untuk ukuran ini.")

elif menu == "📂 Filter Merek & Model":
  st.title("Filter Berdasarkan Merek & Model")
  if df.empty:
    st.warning("Data belum ada.")
  else:
    daftar_merek_fm = sorted(
        [m for m in df["Merek"].dropna().unique() if m != ""]
    )
    if not daftar_merek_fm:
      st.warning("Data merek belum tersedia.")
    else:
      merek_fm_pilihan = st.selectbox(
          "Pilih Merek:", daftar_merek_fm, key="fm_merek"
      )
      df_fm_merek = df[df["Merek"] == merek_fm_pilihan]
      keyword_model = st.text_input(
          "Cari / Filter Kata Kunci Model (contoh: Yaris):", ""
      )

      if keyword_model.strip() != "":
        df_hasil_fm = df_fm_merek[
            df_fm_merek["Model"].str.contains(
                keyword_model, case=False, na=False
            )
        ]
      else:
        df_hasil_fm = df_fm_merek

      df_hasil_fm = df_hasil_fm[df_hasil_fm["ID"].astype(str).str.strip() != ""]

      if not df_hasil_fm.empty:
        st.write(
            "### Hasil Filter Merek"
            f" **{merek_fm_pilihan}** dengan Model mengandung"
            f" **'{keyword_model}'**:"
        )
        st.dataframe(
            df_hasil_fm.drop(
                columns=kolom_sembunyi, errors="ignore"
            ).style.apply(highlight_cols, axis=None),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Ukuran": st.column_config.TextColumn("Ukuran", width="small"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
            },
        )
        st.success(f"Ditemukan {len(df_hasil_fm)} data terkait.")
      else:
        st.info("Tidak ada data mobil yang cocok dengan filter tersebut.")

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

    mode_kelola = st.pills(
        "Pilih Aksi:",
        ["➕ Tambah Data Baru", "✏️ Edit Data yang Ada"],
        label_visibility="collapsed",
    )
    st.markdown(
        "<hr style='margin-top: 2px; margin-bottom: 10px;'>",
        unsafe_allow_html=True,
    )

    kolom_wajib = [
        "Merek",
        "Model",
        "Tahun",
        "Ukuran",
        "Panjang",
        "Lebar",
        "Tinggi",
        "Status",
    ]
    kolom_foto_list = ["Foto1", "Foto2", "Foto3", "Foto4"]

    list_merek_excel = sorted([
        str(m)
        for m in df["Merek"].dropna().unique()
        if str(m).strip() != "" and str(m).lower() != "nan"
    ])
    if not list_merek_excel:
      list_merek_excel = ["Toyota", "Honda", "Daihatsu", "Suzuki"]

    list_status_fix = ["STANDAR", "HARUS CUSTOM"]

    if mode_kelola == "➕ Tambah Data Baru":
      next_id = get_next_id()

      st.markdown(
          "Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.",
          unsafe_allow_html=True,
      )

      st.markdown(
          "ID <span style='color:gray;'>(Otomatis)</span>",
          unsafe_allow_html=True,
      )
      st.text_input(
          "ID", value=str(next_id), disabled=True, label_visibility="collapsed"
      )

      st.markdown(
          "Merek <span style='color:red;'>*</span> <span style='font-size:"
          " 11px; color: gray;'>(Pilih dari daftar atau ketik langsung merek"
          " baru)</span>",
          unsafe_allow_html=True,
      )
      input_merek = st.selectbox(
          "Merek",
          list_merek_excel,
          index=0,
          label_visibility="collapsed",
          accept_new_options=True,
      )

      st.markdown(
          "Model <span style='color:red;'>*</span>", unsafe_allow_html=True
      )
      input_model = st.text_input(
          "Model", placeholder="Contoh: Calya", label_visibility="collapsed"
      )

      st.markdown(
          "Tahun <span style='color:red;'>*</span>", unsafe_allow_html=True
      )
      input_tahun = st.text_input(
          "Tahun", placeholder="Contoh: 2016-On", label_visibility="collapsed"
      )

      with st.form("form_tambah_sisa"):
        baru = {
            "ID": str(next_id),
            "Merek": input_merek,
            "Model": input_model,
            "Tahun": input_tahun,
        }

        for col in df.columns:
          if (
              col
              not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"]
              + kolom_foto_list
          ):
            if col in kolom_wajib:
              label_html = f"{col} <span style='color:red;'>*</span>"
              st.markdown(label_html, unsafe_allow_html=True)
              baru[col] = st.text_input(col, label_visibility="collapsed")
            else:
              baru[col] = st.text_input(col)

        st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
        baru["Status"] = st.selectbox(
            "Status", list_status_fix, label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 📸 Upload Foto Dokumentasi (Maksimal 4 Foto):")
        uploaded_files = {}
        c1, c2 = st.columns(2)
        with c1:
          uploaded_files["Foto1"] = st.file_uploader(
              "Foto 1", type=["jpg", "jpeg", "png"], key="up_t1"
          )
          uploaded_files["Foto2"] = st.file_uploader(
              "Foto 2", type=["jpg", "jpeg", "png"], key="up_t2"
          )
        with c2:
          uploaded_files["Foto3"] = st.file_uploader(
              "Foto 3", type=["jpg", "jpeg", "png"], key="up_t3"
          )
          uploaded_files["Foto4"] = st.file_uploader(
              "Foto 4", type=["jpg", "jpeg", "png"], key="up_t4"
          )

        if st.form_submit_button("Simpan Data Baru"):
          df_submit_check = (
              pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
              if os.path.exists(EXCEL_FILE) and not EXCEL_FILE.startswith("~$")
              else df
          )
          duplikat_cek = df_submit_check[
              (
                  df_submit_check["Merek"].str.strip().str.lower()
                  == str(input_merek).strip().lower()
              )
              & (
                  df_submit_check["Model"].str.strip().str.lower()
                  == str(input_model).strip().lower()
              )
              & (
                  (
                      df_submit_check["Tahun"].str.strip().str.lower()
                      == str(input_tahun).strip().lower()
                  )
                  if input_tahun.strip() != ""
                  else True
              )
              & (df_submit_check["ID"].astype(str).str.strip() != "")
          ]

          if any(not str(baru.get(k)).strip() for k in kolom_wajib):
            st.error(
                "❌ Gagal! Kolom wajib bertanda bintang merah harus diisi dengan"
                " benar!"
            )
          elif not duplikat_cek.empty:
            st.error(
                f'⚠️ Gagal Disimpan! Model "{input_model}" untuk Merek'
                f' "{input_merek}" dengan tahun tersebut sudah ada di database.'
            )
          else:
            timestamp_awalan = int(datetime.now().timestamp())
            for key_f, up_f in uploaded_files.items():
              if up_f is not None:
                nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
                path_simpan = os.path.join(FOTO_FOLDER, nama_file_foto)
                with open(path_simpan, "wb") as f:
                  f.write(up_f.getbuffer())
                baru[key_f] = nama_file_foto
              else:
                baru[key_f] = ""

            dialog_konfirmasi_tambah(baru)
    else:
      df_aktif = df[df["ID"].astype(str).str.strip() != ""]
      if df_aktif.empty:
        st.info("Data kosong.")
      else:
        df_aktif = df_aktif.copy()
        df_aktif["Pilihan_Edit"] = (
            df_aktif.index.astype(str)
            + " - "
            + df_aktif["Merek"]
            + " "
            + df_aktif["Model"]
        )
        idx_str = st.selectbox(
            "Pilih Data:", df_aktif["Pilihan_Edit"].unique()
        )
        idx_pilih = int(idx_str.split(" - ")[0])

        foto_lama = {}
        for i in range(1, 5):
          k_f = f"Foto{i}"
          val_F = str(df.loc[idx_pilih, k_f]) if k_f in df.columns else ""
          if val_F == "nan" or val_F == "None":
            val_F = ""
          foto_lama[k_f] = val_F

        with st.form("form_edit"):
          st.markdown(
              "Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.",
              unsafe_allow_html=True,
          )
          update = {}

          merek_lama = (
              str(df.loc[idx_pilih, "Merek"]) if "Merek" in df.columns else ""
          )
          if merek_lama not in list_merek_excel and merek_lama.strip() != "":
            list_merek_excel.append(merek_lama)
            list_merek_excel.sort()

          default_idx_merek = (
              list_merek_excel.index(merek_lama)
              if merek_lama in list_merek_excel
              else 0
          )

          st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
          update["Merek"] = st.selectbox(
              "Merek Edit",
              list_merek_excel,
              index=default_idx_merek,
              label_visibility="collapsed",
              accept_new_options=True,
          )

          for col in df.columns:
            if (
                col not in ["ID", "Pilihan_Edit", "Merek", "Status"]
                + kolom_foto_list
            ):
              val_lama = (
                  str(df.loc[idx_pilih, col]) if col in df.columns else ""
              )
              if val_lama == "nan" or val_lama == "None":
                val_lama = ""

              if col == "Catatan" and val_lama:
                val_lama = re.sub(
                    r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$",
                    "",
                    val_lama,
                ).strip()

              if col in kolom_wajib:
                label_html = f"{col} <span style='color:red;'>*</span>"
                st.markdown(label_html, unsafe_allow_html=True)
                update[col] = st.text_input(
                    col, value=val_lama, label_visibility="collapsed"
                )
              else:
                update[col] = st.text_input(col, value=val_lama)

          status_lama = (
              str(df.loc[idx_pilih, "Status"])
              if "Status" in df.columns
              else "STANDAR"
          )
          if status_lama not in list_status_fix:
            status_lama = "STANDAR"

          default_idx_status = list_status_fix.index(status_lama)

          st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
          update["Status"] = st.selectbox(
              "Status",
              list_status_fix,
              index=default_idx_status,
              label_visibility="collapsed",
          )

          st.markdown("---")
          st.markdown("### 📸 Kelola / Ganti Foto Dokumentasi:")
          uploaded_files_edit = {}
          c1, c2 = st.columns(2)

          for i in range(1, 5):
            k_f = f"Foto{i}"
            if foto_lama[k_f]:
              st.caption(f"✔️ {k_f} saat ini: `{foto_lama[k_f]}`")
            else:
              st.caption(f"❌ {k_f} saat ini: (Kosong)")

          with c1:
            uploaded_files_edit["Foto1"] = st.file_uploader(
                "Ganti Foto 1 (Opsional)",
                type=["jpg", "jpeg", "png"],
                key="up_e1",
            )
            uploaded_files_edit["Foto2"] = st.file_uploader(
                "Ganti Foto 2 (Opsional)",
                type=["jpg", "jpeg", "png"],
                key="up_e2",
            )
          with c2:
            uploaded_files_edit["Foto3"] = st.file_uploader(
                "Ganti Foto 3 (Opsional)",
                type=["jpg", "jpeg", "png"],
                key="up_e3",
            )
            uploaded_files_edit["Foto4"] = st.file_uploader(
                "Ganti Foto 4 (Opsional)",
                type=["jpg", "jpeg", "png"],
                key="up_e4",
            )

          if st.form_submit_button("Update / Simpan Perubahan"):
            if any(not str(update.get(k)).strip() for k in kolom_wajib):
              st.error(
                  "❌ Gagal! Kolom wajib bertanda bintang merah termasuk Merek"
                  " harus diisi!"
              )
            else:
              waktu_sekarang = datetime.now().strftime("%d-%m-%Y %H:%M")
              catatan_input_user = update.get("Catatan", "")
              catatan_bersih = re.sub(
                  r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$",
                  "",
                  catatan_input_user,
              ).strip()
              jejak_edit = f" | Terakhir diedit: {waktu_sekarang}"
              if catatan_bersih:
                update["Catatan"] = f"{catatan_bersih}{jejak_edit}"
              else:
                update["Catatan"] = f"Terakhir diedit: {waktu_sekarang}"

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

              dialog_konfirmasi_edit(idx_pilih, update)