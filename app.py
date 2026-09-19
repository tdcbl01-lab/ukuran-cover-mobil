import base64
from datetime import datetime
from io import BytesIO
import os
import re
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

# --- LINK GOOGLE SHEETS ANDA ---
SHEET_ID = "1embajr0ZrRRCs-pj5gnI32FqTOh3Je44"
SHEET_NAME = "Sheet1"


# --- FUNGSI PENYIMPANAN CERDAS DENGAN TOKEN CLASSIC & GITHUB API ---
def save_data_smart(df_target, file_path, commit_message):
    if {"Merek", "Model", "Tahun"}.issubset(df_target.columns):
        df_target["_m"] = df_target["Merek"].astype(str).str.strip().str.lower()
        df_target["_mo"] = (
            df_target["Model"].astype(str).str.strip().str.lower()
        )
        df_target["_t"] = df_target["Tahun"].astype(str).str.strip().str.lower()

        df_target = df_target[df_target["_m"] != ""]
        df_target = df_target.drop_duplicates(
            subset=["_m", "_mo", "_t"], keep="last"
        )
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
            "Authorization": f"token {token}",
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
        return (
            False,
            f"GitHub API status code {r_put.status_code}: {r_put.text}",
        )
    except Exception as e:
        return False, str(e)


# --- FUNGSI MEMUAT DATA ---
@st.cache_data(show_spinner=False)
def load_data(file_mtime):
    try:
        url_csv = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
        df_g = pd.read_csv(url_csv, dtype=str, keep_default_na=False)
        if not df_g.empty:
            df_g.columns = df_g.columns.str.strip()
            if {"Merek", "Model", "Tahun"}.issubset(df_g.columns):
                df_g["_m"] = df_g["Merek"].astype(str).str.strip().str.lower()
                df_g["_mo"] = df_g["Model"].astype(str).str.strip().str.lower()
                df_g["_t"] = df_g["Tahun"].astype(str).str.strip().str.lower()
                df_g = df_g[df_g["_m"] != ""]
                df_g = df_g.drop_duplicates(subset=["_m", "_mo", "_t"], keep="last")
                df_g = df_g.drop(columns=["_m", "_mo", "_t"], errors="ignore")
                df_g = df_g.reset_index(drop=True)
                if "ID" in df_g.columns:
                    df_g["ID"] = (df_g.index + 1).astype(str)
            for i in range(1, 5):
                col_name = f"Foto{i}"
                if col_name not in df_g.columns:
                    df_g[col_name] = ""
            return df_g
    except Exception:
        pass

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
        df_dummy = pd.DataFrame(
            columns=[
                "ID",
                "Merek",
                "Model",
                "Tahun",
                "Ukuran",
                "Panjang",
                "Lebar",
                "Tinggi",
                "Status",
                "Catatan",
                "Foto1",
                "Foto2",
                "Foto3",
                "Foto4",
            ]
        )
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
            valid_ids = pd.to_numeric(
                df_check["ID"], errors="coerce"
            ).dropna()
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

st.markdown(
    "<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True
)

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
                    list_foto_tersedia.append(
                        (
                            path_foto,
                            f"Foto {i} - {hasil_row['Merek'].values[0]} {hasil_row['Model'].values[0]}",
                        )
                    )

    if list_foto_tersedia:
        st.markdown("### 📸 Foto Dokumentasi:")
        for i in range(0, len(list_foto_tersedia), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(list_foto_tersedia):
                    p_file, cap_text = list_foto_tersedia[i + j]
                    with cols[j]:
                        st.image(
                            p_file, caption=cap_text, use_container_width=True
                        )


kolom_sembunyi = [
    "Catatan",
    "Pilihan_Edit",
    "Foto1",
    "Foto2",
    "Foto3",
    "Foto4",
]

if menu == "🔍 Cari Ukuran Cover":
    st.title("Daftar Ukuran Cover Mobil")
    if df.empty:
        st.warning("Data belum ada.")
    else:
        daftar_merek = sorted(
            [m for m in df["Merek"].dropna().unique() if str(m).strip() != ""]
        )
        if not daftar_merek:
            st.warning("Data belum tersedia.")
        else:
            merek_pilihan = st.selectbox("Pilih Merek:", daftar_merek)
            df_merk = df[df["Merek"] == merek_pilihan]
            daftar_model = sorted(
                [
                    m
                    for m in df_merk["Model"].dropna().unique()
                    if str(m).strip() != ""
                ]
            )
            model_pilihan = st.selectbox("Pilih Model:", daftar_model)
            df_model = df_merk[df_merk["Model"] == model_pilihan]
            daftar_tahun = sorted(
                [
                    t
                    for t in df_model["Tahun"].dropna().unique()
                    if str(t).strip() != ""
                ]
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
                    hasil.drop(
                        columns=kolom_sembunyi, errors="ignore"
                    ).style.apply(highlight_cols, axis=None),
                    use_container_width=True,
                    hide_index=True,
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
            [u for u in df["Ukuran"].dropna().unique() if str(u).strip() != ""]
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
                st.write(
                    f"### Daftar Mobil dengan Ukuran **{ukuran_pilihan}**:"
                )
                st.dataframe(
                    df_filter_ukuran.drop(
                        columns=kolom_sembunyi, errors="ignore"
                    ).style.apply(highlight_cols, axis=None),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Tidak ada data mobil untuk ukuran ini.")

elif menu == "📂 Filter Merek & Model":
    st.title("Filter Berdasarkan Merek & Model")
    if df.empty:
        st.warning("Data belum ada.")
    else:
        daftar_merek_fm = sorted(
            [m for m in df["Merek"].dropna().unique() if str(m).strip() != ""]
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
            df_hasil_fm = (
                df_fm_merek[
                    df_fm_merek["Model"].str.contains(
                        keyword_model, case=False, na=False
                    )
                ]
                if keyword_model.strip() != ""
                else df_fm_merek
            )
            df_hasil_fm = df_hasil_fm[
                df_hasil_fm["ID"].astype(str).str.strip() != ""
            ]
            if not df_hasil_fm.empty:
                st.dataframe(
                    df_hasil_fm.drop(
                        columns=kolom_sembunyi, errors="ignore"
                    ).style.apply(highlight_cols, axis=None),
                    use_container_width=True,
                    hide_index=True,
                )
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
                use_container_width=True,
            )
        st.markdown("---")

        if st.session_state["show_popup"] is not None:
            p_type = st.session_state["popup_type"]
            p_title = st.session_state["popup_title"]
            p_msg = st.session_state["popup_msg"]

            icon_header = (
                "⚠️"
                if p_type == "warning"
                else ("🎉" if p_type == "success" else "❌")
            )
            title_color = (
                "#f63366" if p_type in ["warning", "error"] else "#28a745"
            )
            box_bg_color = (
                "#fff3cd"
                if p_type == "warning"
                else ("#d4edda" if p_type == "success" else "#f8d7da")
            )
            text_box_color = (
                "#856404"
                if p_type == "warning"
                else ("#155724" if p_type == "success" else "#721c24")
            )

            @st.dialog(" ")
            def modal_notifikasi():
                st.markdown(
                    f"""
                    <h3 style="color: {title_color}; margin-top: -10px; display: flex; align-items: center; gap: 10px; font-size: 22px;">
                        <span>{icon_header}</span> {p_title}
                    </h3>
                    <div style="background-color: {box_bg_color}; color: {text_box_color}; padding: 14px; border-radius: 8px; font-size: 14px; margin: 12px 0 20px 0; line-height: 1.5;">
                        {p_msg}
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "✖️ Tutup", type="primary", use_container_width=True
                ):
                    st.session_state["show_popup"] = None
                    st.session_state["popup_msg"] = ""
                    st.session_state["popup_title"] = ""
                    st.rerun()

            modal_notifikasi()

        mode_kelola = st.pills(
            "Pilih Aksi:",
            ["➕ Tambah Data Baru", "✏️ Edit Data yang Ada"],
            label_visibility="collapsed",
            key="mode_kelola_aksi",
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
                "ID Display",
                value=str(next_id),
                disabled=True,
                label_visibility="collapsed",
            )

            base_merek_list = sorted(
                [
                    m
                    for m in df["Merek"].dropna().unique()
                    if str(m).strip() != ""
                ]
            )
            extended_merek_set = set(base_merek_list)
            for m in base_merek_list:
                extended_merek_set.add(m.lower())
                extended_merek_set.add(m.upper())
            existing_merek_list = sorted(list(extended_merek_set))

            st.markdown(
                "Merek <span style='color:red;'>*</span>",
                unsafe_allow_html=True,
            )
            selected_merek_raw = st.selectbox(
                "Merek Input",
                options=[""] + existing_merek_list,
                accept_new_options=True,
                label_visibility="collapsed",
                key="add_merek_selectbox",
            )

            input_merek = str(selected_merek_raw).strip()
            if input_merek.lower().startswith("add:"):
                input_merek = input_merek[4:].strip()

            matching_existing = [
                m for m in base_merek_list if m.lower() == input_merek.lower()
            ]
            if matching_existing:
                input_merek = matching_existing[0]

            df_merek_terpilih = df[
                df["Merek"].astype(str).str.strip().str.lower()
                == input_merek.lower()
            ]
            base_model_list = sorted(
                [
                    mo
                    for mo in df_merek_terpilih["Model"].dropna().unique()
                    if str(mo).strip() != ""
                ]
            )

            extended_model_set = set(base_model_list)
            for mo in base_model_list:
                extended_model_set.add(mo.lower())
                extended_model_set.add(mo.upper())
            existing_model_list = sorted(list(extended_model_set))

            st.markdown(
                "Model <span style='color:red;'>*</span>",
                unsafe_allow_html=True,
            )
            selected_model_raw = st.selectbox(
                "Model Input",
                options=[""] + existing_model_list,
                accept_new_options=True,
                label_visibility="collapsed",
                key="add_model_selectbox",
            )

            input_model = str(selected_model_raw).strip()
            if input_model.lower().startswith("add:"):
                input_model = input_model[4:].strip()

            matching_existing_model = [
                mo
                for mo in base_model_list
                if mo.lower() == input_model.lower()
            ]
            if matching_existing_model:
                input_model = matching_existing_model[0]

            st.markdown(
                "Tahun <span style='color:red;'>*</span>",
                unsafe_allow_html=True,
            )
            input_tahun = st.text_input(
                "Tahun Input",
                placeholder="Contoh: 2018-2023",
                label_visibility="collapsed",
            )

            input_sisa_data = {}
            for col in df.columns:
                if (
                    col
                    not in [
                        "ID",
                        "Pilihan_Edit",
                        "Merek",
                        "Model",
                        "Tahun",
                        "Status",
                    ]
                    + kolom_foto_list
                ):
                    if col in kolom_wajib:
                        st.markdown(
                            f"{col} <span style='color:red;'>*</span>",
                            unsafe_allow_html=True,
                        )
                        input_sisa_data[col] = st.text_input(
                            f"in_{col}", label_visibility="collapsed"
                        )
                    else:
                        st.markdown(f"{col}", unsafe_allow_html=True)
                        input_sisa_data[col] = st.text_input(
                            f"in_{col}", label_visibility="collapsed"
                        )

            st.markdown(
                "Status <span style='color:red;'>*</span>",
                unsafe_allow_html=True,
            )
            input_status = st.selectbox(
                "Status Input", list_status_fix, label_visibility="collapsed"
            )

            st.markdown("---")
            st.markdown("### 📸 Upload Foto Dokumentasi:")
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

            if st.button("💾 Simpan Data ke Excel", type="primary"):
                if (
                    not str(input_merek).strip()
                    or not str(input_model).strip()
                    or not str(input_tahun).strip()
                ):
                    st.error(
                        "❌ Gagal! Merek, Model, dan Tahun wajib diisi dengan benar!"
                    )
                else:
                    if os.path.exists(EXCEL_FILE):
                        df_cek_duplikat = pd.read_excel(
                            EXCEL_FILE, dtype=str, keep_default_na=False
                        )
                        df_cek_duplikat.columns = (
                            df_cek_duplikat.columns.str.strip()
                        )
                    else:
                        df_cek_duplikat = df.copy()

                    merek_baru_clean = str(input_merek).strip().lower()
                    model_baru_clean = str(input_model).strip().lower()
                    tahun_baru_clean = str(input_tahun).strip().lower()

                    is_duplicate = False
                    if not df_cek_duplikat.empty and {
                        "Merek",
                        "Model",
                        "Tahun",
                    }.issubset(df_cek_duplikat.columns):
                        duplikat_match = df_cek_duplikat[
                            (
                                df_cek_duplikat["Merek"]
                                .str.strip()
                                .str.lower()
                                == merek_baru_clean
                            )
                            & (
                                df_cek_duplikat["Model"]
                                .str.strip()
                                .str.lower()
                                == model_baru_clean
                            )
                            & (
                                df_cek_duplikat["Tahun"]
                                .str.strip()
                                .str.lower()
                                == tahun_baru_clean
                            )
                        ]
                        if not duplikat_match.empty:
                            is_duplicate = True

                    if is_duplicate:
                        st.session_state["popup_title"] = (
                            "Peringatan: Data Sudah Ada"
                        )
                        st.session_state[
                            "popup_msg"
                        ] = f"Data untuk Merek <b>{input_merek}</b>, Model <b>{input_model}</b>, Tahun <b>{input_tahun}</b> sudah pernah ada di database!<br><br>Silakan periksa kembali agar tidak terjadi data ganda."
                        st.session_state["popup_type"] = "warning"
                        st.session_state["show_popup"] = "aktif"
                        st.rerun()
                    else:
                        baru_data = {
                            "ID": str(next_id),
                            "Merek": str(input_merek).strip(),
                            "Model": str(input_model).strip(),
                            "Tahun": str(input_tahun).strip(),
                            "Status": str(input_status).strip(),
                        }
                        for k, v in input_sisa_data.items():
                            baru_data[k] = str(v).strip()

                        timestamp_awalan = int(datetime.now().timestamp())
                        for key_f, up_f in uploaded_files.items():
                            if up_f is not None:
                                nama_file_foto = (
                                    f"{timestamp_awalan}_{key_f}_{up_f.name}"
                                )
                                path_simpan = os.path.join(
                                    FOTO_FOLDER, nama_file_foto
                                )
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
                        df_final = pd.concat(
                            [df_fisik, df_baru_item], ignore_index=True
                        )

                        sukses_simpan, err_msg = save_data_smart(
                            df_final,
                            EXCEL_FILE,
                            f"Tambah data ID {next_id} via Streamlit",
                        )

                        if sukses_simpan:
                            st.cache_data.clear()
                            st.session_state["popup_title"] = "Berhasil!"
                            st.session_state[
                                "popup_msg"
                            ] = "Data baru berhasil ditambahkan dan tersimpan permanen ke database Excel!"
                            st.session_state["popup_type"] = "success"
                            st.session_state["show_popup"] = "aktif"
                            st.rerun()
                        else:
                            st.error(f"❌ Gagal menyimpan data: {err_msg}")

        elif mode_kelola == "✏️ Edit Data yang Ada":
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
                    + " ("
                    + df_aktif["Tahun"]
                    + ")"
                )

                idx_str = st.selectbox(
                    "Pilih Data:",
                    df_aktif["Pilihan_Edit"].unique(),
                    key="select_data_edit_unique",
                )
                idx_pilih = int(idx_str.split(" - ")[0])

                val_merek_asli = (
                    str(df.loc[idx_pilih, "Merek"])
                    if "Merek" in df.columns
                    else ""
                )
                val_model_asli = (
                    str(df.loc[idx_pilih, "Model"])
                    if "Model" in df.columns
                    else ""
                )
                val_tahun_asli = (
                    str(df.loc[idx_pilih, "Tahun"])
                    if "Tahun" in df.columns
                    else ""
                )
                val_status_asli = (
                    str(df.loc[idx_pilih, "Status"])
                    if "Status" in df.columns
                    else "STANDAR"
                )

                st.markdown(
                    "Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.",
                    unsafe_allow_html=True,
                )

                # --- MEREK SELECTBOX ---
                base_merek_list = sorted(
                    [
                        m
                        for m in df["Merek"].dropna().unique()
                        if str(m).strip() != ""
                    ]
                )
                if val_merek_asli not in base_merek_list and val_merek_asli != "":
                    base_merek_list = [val_merek_asli] + base_merek_list

                default_merek_idx = (
                    base_merek_list.index(val_merek_asli)
                    if val_merek_asli in base_merek_list
                    else 0
                )

                st.markdown(
                    "Merek <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                edit_merek = st.selectbox(
                    "Merek Edit Selectbox",
                    options=base_merek_list,
                    index=default_merek_idx,
                    label_visibility="collapsed",
                    key=f"edit_merek_choice_{idx_pilih}",
                )

                # --- MODEL SELECTBOX (MENYESUAIKAN MEREK YANG DIPILIH) ---
                df_merek_edit_terpilih = df[
                    df["Merek"].astype(str).str.strip().str.lower()
                    == str(edit_merek).strip().lower()
                ]
                base_model_edit_list = sorted(
                    [
                        mo
                        for mo in df_merek_edit_terpilih[
                            "Model"
                        ].dropna().unique()
                        if str(mo).strip() != ""
                    ]
                )

                if val_model_asli not in base_model_edit_list:
                    if len(base_model_edit_list) > 0:
                        val_model_asli = base_model_edit_list[0]
                    else:
                        val_model_asli = ""

                if val_model_asli not in base_model_edit_list and val_model_asli != "":
                    base_model_edit_list = [val_model_asli] + base_model_edit_list

                default_model_idx = (
                    base_model_edit_list.index(val_model_asli)
                    if val_model_asli in base_model_edit_list
                    else 0
                )

                st.markdown(
                    "Model <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                edit_model = st.selectbox(
                    "Model Edit Selectbox",
                    options=base_model_edit_list,
                    index=default_model_idx,
                    label_visibility="collapsed",
                    key=f"edit_model_choice_{idx_pilih}",
                )

                st.markdown(
                    "Tahun <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                edit_tahun = st.text_input(
                    "Tahun Edit",
                    value=val_tahun_asli,
                    label_visibility="collapsed",
                    key=f"edit_tahun_{idx_pilih}",
                )

                edit_sisa_data = {}
                for col in df.columns:
                    if (
                        col
                        not in [
                            "ID",
                            "Pilihan_Edit",
                            "Merek",
                            "Model",
                            "Tahun",
                            "Status",
                        ]
                        + kolom_foto_list
                    ):
                        val_col_asli = (
                            str(df.loc[idx_pilih, col])
                            if col in df.columns
                            else ""
                        )
                        if col in kolom_wajib:
                            st.markdown(
                                f"{col} <span style='color:red;'>*</span>",
                                unsafe_allow_html=True,
                            )
                            edit_sisa_data[col] = st.text_input(
                                f"edit_{col}",
                                value=val_col_asli,
                                label_visibility="collapsed",
                                key=f"edit_{col}_{idx_pilih}",
                            )
                        else:
                            st.markdown(f"{col}", unsafe_allow_html=True)
                            edit_sisa_data[col] = st.text_input(
                                f"edit_{col}",
                                value=val_col_asli,
                                label_visibility="collapsed",
                                key=f"edit_{col}_{idx_pilih}",
                            )

                st.markdown(
                    "Status <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                try:
                    status_idx = list_status_fix.index(val_status_asli)
                except ValueError:
                    status_idx = 0
                edit_status = st.selectbox(
                    "Status Edit",
                    list_status_fix,
                    index=status_idx,
                    label_visibility="collapsed",
                    key=f"edit_status_{idx_pilih}",
                )

                st.markdown("---")
                st.markdown("### 📸 Ganti Foto Dokumentasi (Opsional):")
                edit_uploaded_files = {}
                c1, c2 = st.columns(2)
                with c1:
                    edit_uploaded_files["Foto1"] = st.file_uploader(
                        "Ganti Foto 1",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_up_1_{idx_pilih}",
                    )
                    edit_uploaded_files["Foto2"] = st.file_uploader(
                        "Ganti Foto 2",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_up_2_{idx_pilih}",
                    )
                with c2:
                    edit_uploaded_files["Foto3"] = st.file_uploader(
                        "Ganti Foto 3",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_up_3_{idx_pilih}",
                    )
                    edit_uploaded_files["Foto4"] = st.file_uploader(
                        "Ganti Foto 4",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_up_4_{idx_pilih}",
                    )

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💾 Simpan Perubahan", type="primary", key=f"btn_save_{idx_pilih}"):
                        if (
                            not str(edit_merek).strip()
                            or not str(edit_model).strip()
                            or not str(edit_tahun).strip()
                        ):
                            st.error(
                                "❌ Gagal! Merek, Model, dan Tahun wajib diisi!"
                            )
                        else:
                            df.loc[idx_pilih, "Merek"] = str(edit_merek).strip()
                            df.loc[idx_pilih, "Model"] = str(edit_model).strip()
                            df.loc[idx_pilih, "Tahun"] = str(edit_tahun).strip()
                            df.loc[idx_pilih, "Status"] = str(edit_status).strip()

                            for k, v in edit_sisa_data.items():
                                df.loc[idx_pilih, k] = str(v).strip()

                            timestamp_awalan = int(datetime.now().timestamp())
                            for key_f, up_f in edit_uploaded_files.items():
                                if up_f is not None:
                                    nama_file_foto = (
                                        f"{timestamp_awalan}_{key_f}_{up_f.name}"
                                    )
                                    path_simpan = os.path.join(
                                        FOTO_FOLDER, nama_file_foto
                                    )
                                    with open(path_simpan, "wb") as f:
                                        f.write(up_f.getbuffer())
                                    df.loc[idx_pilih, key_f] = nama_file_foto

                            sukses_simpan, err_msg = save_data_smart(
                                df,
                                EXCEL_FILE,
                                f"Update data ID {df.loc[idx_pilih, 'ID']} via Streamlit",
                            )

                            if sukses_simpan:
                                st.cache_data.clear()
                                st.session_state["popup_title"] = "Berhasil!"
                                st.session_state[
                                    "popup_msg"
                                ] = "Perubahan data berhasil disimpan secara permanen!"
                                st.session_state["popup_type"] = "success"
                                st.session_state["show_popup"] = "aktif"
                                st.rerun()
                            else:
                                st.error(f"❌ Gagal memperbarui data: {err_msg}")

                with col_b2:
                    if st.button("🗑️ Hapus Data Ini", type="secondary", key=f"btn_del_{idx_pilih}"):
                        df = df.drop(idx_pilih).reset_index(drop=True)
                        if "ID" in df.columns and not df.empty:
                            df["ID"] = (df.index + 1).astype(str)

                        sukses_simpan, err_msg = save_data_smart(
                            df,
                            EXCEL_FILE,
                            f"Hapus data ID {df.loc[idx_pilih, 'ID']} via Streamlit",
                        )

                        if sukses_simpan:
                            st.cache_data.clear()
                            st.session_state["popup_title"] = (
                                "Berhasil Dihapus!"
                            )
                            st.session_state[
                                "popup_msg"
                            ] = "Data berhasil dihapus dari database."
                            st.session_state["popup_type"] = "success"
                            st.session_state["show_popup"] = "aktif"
                            st.rerun()
                        else:
                            st.error(f"❌ Gagal menghapus data: {err_msg}")