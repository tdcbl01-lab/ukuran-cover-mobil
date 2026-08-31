import os
import re
import base64
from datetime import datetime
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


# --- FUNGSI PENYIMPANAN CERDAS DENGAN PEMBERSIH DUPLIKAT OTOMATIS ---
def save_data_smart(df_target, file_path, commit_message):
    if {"Merek", "Model", "Tahun"}.issubset(df_target.columns):
        df_target["_m"] = df_target["Merek"].astype(str).str.strip().str.lower()
        df_target["_mo"] = df_target["Model"].astype(str).str.strip().str.lower()
        df_target["_t"] = df_target["Tahun"].astype(str).str.strip().str.lower()
        
        df_target = df_target[df_target["_m"] != ""]
        df_target = df_target.drop_duplicates(subset=["_m", "_mo", "_t"], keep="last")
        df_target = df_target.drop(columns=["_m", "_mo", "_t"], errors="ignore")
        
        df_target = df_target.reset_index(drop=True)
        if "ID" in df_target.columns:
            df_target["ID"] = (df_target.index + 1).astype(str)

    has_github_secrets = False
    try:
        if "github" in st.secrets:
            gh = st.secrets["github"]
            if gh.get("token") and gh.get("repo"):
                has_github_secrets = True
    except Exception:
        has_github_secrets = False

    if not has_github_secrets:
        try:
            df_target.to_excel(file_path, index=False)
            return True, ""
        except Exception as e:
            return False, str(e)

    try:
        gh = st.secrets["github"]
        token = gh.get("token")
        repo = gh.get("repo")
        branch = gh.get("branch", "main")

        df_target.to_excel(file_path, index=False)
        
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
            "message": commit_message,
            "content": content_encoded,
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
            
        r_put = requests.put(url, json=payload, headers=headers)
        if r_put.status_code in [200, 201]:
            return True, ""
        return False, f"GitHub API status code {r_put.status_code}"
    except Exception as e:
        return False, str(e)


# --- FUNGSI MEMUAT DATA DENGAN DETEKSI PERUBAHAN FILE OTOMATIS ---
@st.cache_data(show_spinner=False)
def load_data(file_mtime):
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
        if {"Merek", "Model", "Tahun"}.issubset(df.columns):
            df["_m"] = df["Merek"].astype(str).str.strip().str.lower()
            df["_mo"] = df["Model"].astype(str).str.strip().str.lower()
            df["_t"] = df["Tahun"].astype(str).str.strip().str.lower()
            df = df[df["_m"] != ""]
            df = df.drop_duplicates(subset=["_m", "_mo", "_t"], keep="last")
            df = df.drop(columns=["_m", "_mo", "_t"], errors="ignore")
            df = df.reset_index(drop=True)
            if "ID" in df.columns:
                df["ID"] = (df.index + 1).astype(str)
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


file_mtime = os.path.getmtime(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else 0

df = load_data(file_mtime)
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

if "show_popup" not in st.session_state:
    st.session_state["show_popup"] = None
if "popup_msg" not in st.session_state:
    st.session_state["popup_msg"] = ""
if "popup_title" not in st.session_state:
    st.session_state["popup_title"] = ""
if "popup_type" not in st.session_state:
    st.session_state["popup_type"] = "warning"


col_logo, col_tagline = st.columns([1, 2])
with col_logo:
    try:
        st.image("Logo TDC.png", width=160)
    except:
        st.write("Logo TDC")
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
    if catatan_val and str(catatan_val).lower() not in ["nan", "none", ""]:
        st.info(f"**Catatan & Riwayat Edit:** {catatan_val}")

    list_foto_tersedia = []
    for i in range(1, 5):
        kol_foto = f"Foto{i}"
        if kol_foto in hasil_row.columns:
            val_foto = str(hasil_row[kol_foto].values[0]).strip()
            if val_foto and val_foto.lower() not in ["nan", "none", ""]:
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
        daftar_merek = sorted([m for m in df["Merek"].dropna().unique() if str(m).strip() != ""])
        if not daftar_merek:
            st.warning("Data belum tersedia.")
        else:
            merek_pilihan = st.selectbox("Pilih Merek:", daftar_merek)
            df_merk = df[df["Merek"] == merek_pilihan]
            daftar_model = sorted([m for m in df_merk["Model"].dropna().unique() if str(m).strip() != ""])
            model_pilihan = st.selectbox("Pilih Model:", daftar_model)
            df_model = df_merk[df_merk["Model"] == model_pilihan]
            daftar_tahun = sorted([t for t in df_model["Tahun"].dropna().unique() if str(t).strip() != ""])
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
        daftar_ukuran = sorted([u for u in df["Ukuran"].dropna().unique() if str(u).strip() != ""])
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
        daftar_merek_fm = sorted([m for m in df["Merek"].dropna().unique() if str(m).strip() != ""])
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

        st.markdown("### 📥 Ekspor Laporan Database")
        if os.path.exists(EXCEL_FILE):
            with open(EXCEL_FILE, "rb") as f:
                excel_bytes = f.read()
            st.download_button(
                label="📥 Download File Excel (Database Terbaru)",
                data=excel_bytes,
                file_name="data_cover_tdc.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                use_container_width=True
            )
        st.markdown("---")

        if st.session_state["show_popup"] is not None:
            p_type = st.session_state["popup_type"]
            p_title = st.session_state["popup_title"]
            p_msg = st.session_state["popup_msg"]
            
            icon_header = "⚠️" if p_type == "warning" else ("🎉" if p_type == "success" else "❌")
            title_color = "#f63366" if p_type in ["warning", "error"] else "#28a745"
            box_bg_color = "#fff3cd" if p_type == "warning" else ("#d4edda" if p_type == "success" else "#f8d7da")
            text_box_color = "#856404" if p_type == "warning" else ("#155724" if p_type == "success" else "#721c24")

            @st.dialog(" ")
            def modal_notifikasi():
                st.markdown(f"""
                    <h3 style="color: {title_color}; margin-top: -10px; display: flex; align-items: center; gap: 10px; font-size: 22px;">
                        <span>{icon_header}</span> {p_title}
                    </h3>
                    <div style="background-color: {box_bg_color}; color: {text_box_color}; padding: 14px; border-radius: 8px; font-size: 14px; margin: 12px 0 20px 0; line-height: 1.5;">
                        {p_msg}
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("✖️ Tutup", type="primary", use_container_width=True):
                    st.session_state["show_popup"] = None
                    st.session_state["popup_msg"] = ""
                    st.session_state["popup_title"] = ""
                    st.rerun()

            modal_notifikasi()

        mode_kelola = st.pills("Pilih Aksi:", ["➕ Tambah Data Baru", "✏️ Edit Data yang Ada"], label_visibility="collapsed")
        st.markdown("<hr style='margin-top: 2px; margin-bottom: 10px;'>", unsafe_allow_html=True)

        kolom_wajib = ["Merek", "Model", "Tahun", "Ukuran", "Panjang", "Lebar", "Tinggi", "Status"]
        kolom_foto_list = ["Foto1", "Foto2", "Foto3", "Foto4"]

        list_status_fix = ["STANDAR", "HARUS CUSTOM"]

        if mode_kelola == "➕ Tambah Data Baru":
            next_id = get_next_id()

            st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)
            st.markdown("ID <span style='color:gray;'>(Otomatis)</span>", unsafe_allow_html=True)
            st.text_input("ID Display", value=str(next_id), disabled=True, label_visibility="collapsed")

            # --- MEREK PILIHAN DENGAN MENGABUNGKAN VERSI HURUF KECIL KE OPSI SUPAYA "Add:" HILANG ---
            base_merek_list = sorted([m for m in df["Merek"].dropna().unique() if str(m).strip() != ""])
            extended_merek_set = set(base_merek_list)
            for m in base_merek_list:
                extended_merek_set.add(m.lower())
                extended_merek_set.add(m.upper())
            existing_merek_list = sorted(list(extended_merek_set))
            
            st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
            selected_merek_raw = st.selectbox(
                "Merek Input", 
                options=[""] + existing_merek_list, 
                accept_new_options=True, 
                label_visibility="collapsed", 
                key="add_merek_selectbox"
            )

            input_merek = str(selected_merek_raw).strip()
            if input_merek.lower().startswith("add:"):
                input_merek = input_merek[4:].strip()
            
            # Normalisasi otomatis ke format standar yang sudah ada di database jika cocok secara case-insensitive
            matching_existing = [m for m in base_merek_list if m.lower() == input_merek.lower()]
            if matching_existing:
                input_merek = matching_existing[0]
            # -------------------------------------------------------------------------------------------------------------------

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
                        st.markdown(f"{col}", unsafe_allow_html=True)
                        input_sisa_data[col] = st.text_input(f"in_{col}", label_visibility="collapsed")

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
                    st.error("❌ Gagal! Merek, Model, dan Tahun wajib diisi dengan benar!")
                else:
                    if os.path.exists(EXCEL_FILE):
                        df_cek_duplikat = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
                        df_cek_duplikat.columns = df_cek_duplikat.columns.str.strip()
                    else:
                        df_cek_duplikat = df.copy()

                    merek_baru_clean = str(input_merek).strip().lower()
                    model_baru_clean = str(input_model).strip().lower()
                    tahun_baru_clean = str(input_tahun).strip().lower()

                    is_duplicate = False
                    if not df_cek_duplikat.empty and {"Merek", "Model", "Tahun"}.issubset(df_cek_duplikat.columns):
                        duplikat_match = df_cek_duplikat[
                            (df_cek_duplikat["Merek"].str.strip().str.lower() == merek_baru_clean) &
                            (df_cek_duplikat["Model"].str.strip().str.lower() == model_baru_clean) &
                            (df_cek_duplikat["Tahun"].str.strip().str.lower() == tahun_baru_clean)
                        ]
                        if not duplikat_match.empty:
                            is_duplicate = True

                    if is_duplicate:
                        st.session_state["popup_title"] = "Peringatan: Data Sudah Ada"
                        st.session_state["popup_msg"] = f"Data untuk Merek <b>{input_merek}</b>, Model <b>{input_model}</b>, Tahun <b>{input_tahun}</b> sudah pernah ada di database!<br><br>Silakan periksa kembali agar tidak terjadi data ganda."
                        st.session_state["popup_type"] = "warning"
                        st.session_state["show_popup"] = "aktif"
                        st.rerun()
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

                        df_fisik = df_cek_duplikat
                        for c in df_fisik.columns:
                            if c not in baru_data:
                                baru_data[c] = ""

                        df_baru_item = pd.DataFrame([baru_data])
                        df_final = pd.concat([df_fisik, df_baru_item], ignore_index=True)
                        
                        sukses_simpan, err_msg = save_data_smart(df_final, EXCEL_FILE, f"Tambah data ID {next_id} via Streamlit")
                        
                        if sukses_simpan:
                            st.cache_data.clear()
                            st.session_state["popup_title"] = "Berhasil!"
                            st.session_state["popup_msg"] = "Data baru berhasil ditambahkan dan tersimpan permanen ke database Excel!"
                            st.session_state["popup_type"] = "success"
                            st.session_state["show_popup"] = "aktif"
                            st.rerun()
                        else:
                            st.error(f"❌ Gagal menyimpan data: {err_msg}")

        # === BLOK EDIT DATA ===
        elif mode_kelola == "✏️ Edit Data yang Ada":
            df_aktif = df[df["ID"].astype(str).str.strip() != ""]
            if df_aktif.empty:
                st.info("Data kosong.")
            else:
                df_aktif = df_aktif.copy()
                df_aktif["Pilihan_Edit"] = df_aktif.index.astype(str) + " - " + df_aktif["Merek"] + " " + df_aktif["Model"] + " (" + df_aktif["Tahun"] + ")"
                
                idx_str = st.selectbox("Pilih Data:", df_aktif["Pilihan_Edit"].unique(), key="select_data_edit_unique")
                idx_pilih = int(idx_str.split(" - ")[0])

                val_merek_asli = str(df.loc[idx_pilih, "Merek"]) if "Merek" in df.columns else ""
                val_model_asli = str(df.loc[idx_pilih, "Model"]) if "Model" in df.columns else ""
                val_tahun_asli = str(df.loc[idx_pilih, "Tahun"]) if "Tahun" in df.columns else ""
                val_status_asli = str(df.loc[idx_pilih, "Status"]) if "Status" in df.columns else "STANDAR"

                st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)

                widget_values = {}

                # --- MEREK EDIT AMAN DENGAN EKSTENSI OPSI HURUF KECIL/BESAR ---
                base_merek_list = sorted([m for m in df["Merek"].dropna().unique() if str(m).strip() != ""])
                extended_merek_set = set(base_merek_list)
                for m in base_merek_list:
                    extended_merek_set.add(m.lower())
                    extended_merek_set.add(m.upper())
                existing_merek_list = sorted(list(extended_merek_set))
                
                default_merek_idx = existing_merek_list.index(val_merek_asli) if val_merek_asli in existing_merek_list else 0

                st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
                selected_merek_edit_raw = st.selectbox(
                    "Merek Edit Selectbox", 
                    options=existing_merek_list, 
                    index=default_merek_idx, 
                    accept_new_options=True, 
                    label_visibility="collapsed", 
                    key=f"edit_merek_choice_{idx_pilih}"
                )

                selected_merek = str(selected_merek_edit_raw).strip()
                if selected_merek.lower().startswith("add:"):
                    selected_merek = selected_merek[4:].strip()

                matching_existing_edit = [m for m in base_merek_list if m.lower() == selected_merek.lower()]
                if matching_existing_edit:
                    selected_merek = matching_existing_edit[0]

                widget_values["Merek"] = selected_merek

                daftar_model_berdasarkan_merek = sorted(list(set([str(m).strip() for m in df[df["Merek"].str.strip().str.lower() == selected_merek.strip().lower()]["Model"].dropna().unique() if str(m).strip() != ""])))
                
                st.markdown("Model <span style='color:red;'>*</span>", unsafe_allow_html=True)
                if daftar_model_berdasarkan_merek:
                    if val_model_asli not in daftar_model_berdasarkan_merek and selected_merek.strip().lower() == val_merek_asli.strip().lower():
                        daftar_model_berdasarkan_merek.insert(0, val_model_asli)
                    
                    default_model_idx = daftar_model_berdasarkan_merek.index(val_model_asli) if (selected_merek.strip().lower() == val_merek_asli.strip().lower() and val_model_asli in daftar_model_berdasarkan_merek) else 0
                    
                    selected_model = st.selectbox("Model Edit Select", daftar_model_berdasarkan_merek, index=default_model_idx, label_visibility="collapsed", key=f"edit_model_sel_{idx_pilih}")
                else:
                    initial_model_val = val_model_asli if selected_merek.strip().lower() == val_merek_asli.strip().lower() else ""
                    selected_model = st.text_input("Model Edit Text", value=initial_model_val, placeholder="Contoh: J7, E5", label_visibility="collapsed", key=f"edit_model_txt_{idx_pilih}")
                
                widget_values["Model"] = selected_model

                df_ref_matched = df[(df["Merek"].str.strip().str.lower() == selected_merek.strip().lower()) & (df["Model"].str.strip().str.lower() == selected_model.strip().lower())]
                if not df_ref_matched.empty:
                    row_ref = df_ref_matched.iloc[-1]
                else:
                    row_ref = df.loc[idx_pilih]

                dynamic_key_suffix = f"{selected_merek}_{selected_model}".replace(" ", "_")

                for col in df.columns:
                    if col not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
                        val_lama = str(row_ref[col]) if col in row_ref else ""
                        if val_lama.lower() in ["nan", "none"]:
                            val_lama = ""
                        if col == "Catatan" and val_lama:
                            val_lama = re.sub(r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$", "", val_lama).strip()

                        widget_key = f"edit_{col}_{idx_pilih}_{dynamic_key_suffix}"
                        
                        if col in kolom_wajib:
                            st.markdown(f"{col} <span style='color:red;'>*</span>", unsafe_allow_html=True)
                            widget_values[col] = st.text_input(f"{col} Edit", value=val_lama, label_visibility="collapsed", key=widget_key)
                        else:
                            st.markdown(f"{col}", unsafe_allow_html=True)
                            widget_values[col] = st.text_input(f"{col} Edit", value=val_lama, label_visibility="collapsed", key=widget_key)

                val_tahun_ref = str(row_ref["Tahun"]) if "Tahun" in row_ref else val_tahun_asli
                if val_tahun_ref.lower() in ["nan", "none"]:
                    val_tahun_ref = val_tahun_asli

                st.markdown("Tahun <span style='color:red;'>*</span>", unsafe_allow_html=True)
                tahun_key = f"edit_tahun_{idx_pilih}_{dynamic_key_suffix}"
                widget_values["Tahun"] = st.text_input("Tahun Edit", value=val_tahun_ref, label_visibility="collapsed", key=tahun_key)

                val_status_ref = str(row_ref["Status"]) if "Status" in row_ref else val_status_asli
                if val_status_ref not in list_status_fix: 
                    val_status_ref = "STANDAR"
                default_idx_status = list_status_fix.index(val_status_ref) if val_status_ref in list_status_fix else 0

                st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
                status_key = f"edit_status_{idx_pilih}_{dynamic_key_suffix}"
                widget_values["Status"] = st.selectbox("Status Edit", list_status_fix, index=default_idx_status, label_visibility="collapsed", key=status_key)

                st.markdown("---")
                st.markdown("### 📸 Ganti Foto Dokumentasi:")
                uploaded_files_edit = {}
                c1, c2 = st.columns(2)
                with c1:
                    uploaded_files_edit["Foto1"] = st.file_uploader("Ganti Foto 1", type=["jpg", "jpeg", "png"], key=f"up_e1_{idx_pilih}")
                    uploaded_files_edit["Foto2"] = st.file_uploader("Ganti Foto 2", type=["jpg", "jpeg", "png"], key=f"up_e2_{idx_pilih}")
                with c2:
                    uploaded_files_edit["Foto3"] = st.file_uploader("Ganti Foto 3", type=["jpg", "jpeg", "png"], key=f"up_e3_{idx_pilih}")
                    uploaded_files_edit["Foto4"] = st.file_uploader("Ganti Foto 4", type=["jpg", "jpeg", "png"], key=f"up_e4_{idx_pilih}")

                st.markdown("")
                
                col_btn_center1, col_btn_center2, col_btn_center3 = st.columns([1, 2, 1])
                with col_btn_center2:
                    tombol_simpan_edit = st.button("💾 Update / Simpan Perubahan", type="primary", key=f"btn_save_{idx_pilih}")

                if tombol_simpan_edit:
                    ada_perubahan_data = False
                    for k, v in widget_values.items():
                        val_lama_db = str(df.loc[idx_pilih, k]) if k in df.columns else ""
                        if val_lama_db.lower() in ["nan", "none"]:
                            val_lama_db = ""
                        if k == "Catatan":
                            val_lama_db = re.sub(r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$", "", val_lama_db).strip()
                        
                        val_input_clean = " ".join(str(v).split()).strip()
                        val_db_clean = " ".join(str(val_lama_db).split()).strip()

                        if val_input_clean != val_db_clean:
                            ada_perubahan_data = True
                            break

                    ada_foto_baru = any(up_f is not None for up_f in uploaded_files_edit.values())

                    if not ada_perubahan_data and not ada_foto_baru:
                        st.session_state["popup_title"] = "Perhatian"
                        st.session_state["popup_msg"] = "Tidak ada perubahan data atau foto yang dilakukan!<br><br>Silakan ubah data terlebih dahulu jika ingin menyimpan."
                        st.session_state["popup_type"] = "warning"
                        st.session_state["show_popup"] = "aktif"
                        st.rerun()
                    elif any(not str(widget_values.get(k)).strip() for k in ["Merek", "Model", "Tahun", "Status"]):
                        st.error("❌ Gagal! Kolom wajib (Merek, Model, Tahun, Status) harus diisi dengan benar!")
                    else:
                        if os.path.exists(EXCEL_FILE):
                            df_fisik = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
                            df_fisik.columns = df_fisik.columns.str.strip()
                        else:
                            df_fisik = df.copy()

                        update = dict(widget_values)
                        waktu_sekarang = datetime.now().strftime("%d-%m-%Y %H:%M")
                        catatan_input_user = update.get("Catatan", "")
                        catatan_bersih = re.sub(r"\s*([\|–-]|Terakhir diedit|Diedit tgl|Pernah diedit).*$", "", catatan_input_user).strip()
                        update["Catatan"] = f"{catatan_bersih} | Terakhir diedit: {waktu_sekarang}" if catatan_bersih else f"Terakhir diedit: {waktu_sekarang}"

                        for key_f, up_f in uploaded_files_edit.items():
                            if up_f is not None:
                                timestamp_awalan = int(datetime.now().timestamp())
                                nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
                                path_simpan = os.path.join(FOTO_FOLDER, nama_file_foto)
                                with open(path_simpan, "wb") as f:
                                    f.write(up_f.getbuffer())
                                update[key_f] = nama_file_foto
                            else:
                                update[key_f] = str(df_fisik.loc[idx_pilih, key_f]) if key_f in df_fisik.columns else ""

                        for k, v in update.items():
                            if k in df_fisik.columns:
                                df_fisik.loc[idx_pilih, k] = str(v).strip()

                        sukses_simpan, err_msg = save_data_smart(df_fisik, EXCEL_FILE, f"Update data ID {df_fisik.loc[idx_pilih, 'ID']} via Streamlit")

                        if sukses_simpan:
                            st.cache_data.clear()
                            st.session_state["popup_title"] = "Berhasil Disimpan!"
                            st.session_state["popup_msg"] = "Perubahan data berhasil diperbarui dan disimpan secara permanen ke database Excel!"
                            st.session_state["popup_type"] = "success"
                            st.session_state["show_popup"] = "aktif"
                            st.rerun()
                        else:
                            st.error(f"❌ Gagal memperbarui data: {err_msg}")