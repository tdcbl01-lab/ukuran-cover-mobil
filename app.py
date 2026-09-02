import base64
from datetime import datetime
from io import BytesIO
import os
import re
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Aplikasi Cover Mobil TDC",
    layout="centered",
    initial_sidebar_state="collapsed",
)

FOTO_FOLDER = "foto_cover"
if not os.path.exists(FOTO_FOLDER):
    os.makedirs(FOTO_FOLDER)

EXCEL_FILE = "data_cover.xlsx"
EXCEL_EKSPEDISI_FILE = "data_ekspedisi.xlsx"

st.markdown(
    """
    <style>
        [data-testid="stDataFrame"] { width: 100% !important; }
        .stDataFrame table { width: 100% !important; }
    </style>
""",
    unsafe_allow_html=True,
)


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


@st.cache_data(show_spinner=False)
def load_ekspedisi_data(file_mtime_eks):
    if os.path.exists(EXCEL_EKSPEDISI_FILE):
        df_eks = pd.read_excel(
            EXCEL_EKSPEDISI_FILE, dtype=str, keep_default_na=False
        )
        if "No" in df_eks.columns:
            df_eks = df_eks.reset_index(drop=True)
            df_eks["No"] = (df_eks.index + 1).astype(str)
        return df_eks
    else:
        df_dummy_eks = pd.DataFrame(
            columns=[
                "No",
                "Nama Expedisi",
                "Alamat",
                "No Telpon",
                "Nama PIC/Kurir",
                "Keterangan",
                "Google Map",
            ]
        )
        df_dummy_eks.to_excel(EXCEL_EKSPEDISI_FILE, index=False)
        return df_dummy_eks


file_mtime = os.path.getmtime(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else 0
df = load_data(file_mtime)
df.columns = df.columns.str.strip()
for i in range(1, 5):
    if f"Foto{i}" not in df.columns:
        df[f"Foto{i}"] = ""

file_mtime_eks = (
    os.path.getmtime(EXCEL_EKSPEDISI_FILE)
    if os.path.exists(EXCEL_EKSPEDISI_FILE)
    else 0
)
df_ekspedisi = load_ekspedisi_data(file_mtime_eks)
df_ekspedisi.columns = df_ekspedisi.columns.str.strip()


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
    for col in x.columns:
        c_lower = str(col).strip().lower()
        if c_lower == "id":
            df_styler[col] = "background-color: #f0f2f6"
        elif c_lower == "ukuran":
            df_styler[col] = (
                "background-color: #fff3cd; font-weight: bold; color: #856404;"
            )
        elif c_lower == "status":
            df_styler[col] = "color: #ff4b4b; font-weight: bold"
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

col_logo, col_tagline = st.columns([1, 4])
with col_logo:
    try:
        st.image("Logo TDC.png", width=140)
    except:
        st.write("Logo TDC")
with col_tagline:
    st.markdown(
        """
    <div style="display: flex; align-items: center; height: 100%; padding-top: 12px;">
        <h4 style="color: #555; font-style: italic; font-weight: 600; margin: 0; letter-spacing: 0.5px;">Automotive Accessories</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True
)

if "menu_pilihan" not in st.session_state:
    st.session_state["menu_pilihan"] = "🔍 Cari Ukuran Cover"


def update_menu():
    st.session_state["menu_pilihan"] = st.session_state["widget_pills_menu"]


st.pills(
    "Pilih Menu:",
    [
        "🔍 Cari Ukuran Cover",
        "📊 Filter Berdasarkan Ukuran",
        "📂 Filter Merek & Model",
        "🚚 Data Ekspedisi",
        "➕ Tambah / Edit Data",
    ],
    key="widget_pills_menu",
    default=st.session_state["menu_pilihan"],
    on_change=update_menu,
    label_visibility="collapsed",
)

menu = st.session_state["menu_pilihan"]
st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True
)


def tampilkan_detail_tambahan(hasil_row):
    st.markdown("### 🛡️ Pilihan Tipe Cover Durable TDC:")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(
            """
        - **Durable Premium** (Kualitas Tertinggi)
        - **Durable Xtrem** (4 Layer Proteksi Ekstra)
        """
        )
    with col_t2:
        st.markdown(
            """
        - **Durable Guardian** (3 Layer Perlindungan)
        - **Durable Rubuk** (3 Layer Ekonomis)
        """
        )
    st.markdown("---")

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
            c1, c2, c3 = st.columns(3)
            with c1:
                merek_pilihan = st.selectbox("Pilih Merek:", daftar_merek)
            df_merk = df[df["Merek"] == merek_pilihan]
            daftar_model = sorted(
                [
                    m
                    for m in df_merk["Model"].dropna().unique()
                    if str(m).strip() != ""
                ]
            )
            with c2:
                model_pilihan = st.selectbox("Pilih Model:", daftar_model)
            df_model = df_merk[df_merk["Model"] == model_pilihan]
            daftar_tahun = sorted(
                [
                    t
                    for t in df_model["Tahun"].dropna().unique()
                    if str(t).strip() != ""
                ]
            )
            with c3:
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
            c1, c2 = st.columns(2)
            with c1:
                merek_fm_pilihan = st.selectbox(
                    "Pilih Merek:", daftar_merek_fm, key="fm_merek"
                )
            df_fm_merek = df[df["Merek"] == merek_fm_pilihan]
            with c2:
                keyword_model = st.text_input(
                    "Cari Kata Kunci Model (contoh: Yaris):", ""
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

elif menu == "🚚 Data Ekspedisi":
    st.title("Manajemen Data Ekspedisi")
    st.markdown(
        "Daftar lengkap ekspedisi, alamat, kontak PIC, dan tautan Google Maps."
    )

    if not df_ekspedisi.empty:
        st.dataframe(
            df_ekspedisi, use_container_width=True, hide_index=True
        )
    else:
        st.info("Belum ada data ekspedisi tersimpan.")

    with st.expander("➕ Tambah atau Edit Data Ekspedisi"):
        if not st.session_state["logged_in"]:
            st.warning(
                "Silakan login di menu **Tambah / Edit Data** terlebih dahulu"
                " untuk mengubah data ekspedisi."
            )
        else:
            with st.form("form_tambah_ekspedisi"):
                st.markdown("### Input Data Ekspedisi Baru")
                f_nama_eks = st.text_input("Nama Expedisi")
                f_alamat = st.text_area("Alamat")
                f_telp = st.text_input("No Telpon")
                f_pic = st.text_input("Nama PIC/Kurir")
                f_ket = st.text_input("Keterangan")
                f_gmap = st.text_input("Google Map (Link / Catatan)")

                submit_eks = st.form_submit_button(
                    "Simpan Ekspedisi Baru", type="primary"
                )
                if submit_eks:
                    if not f_nama_eks.strip():
                        st.error("Nama Expedisi wajib diisi!")
                    else:
                        new_row_eks = {
                            "No": str(len(df_ekspedisi) + 1),
                            "Nama Expedisi": f_nama_eks.strip(),
                            "Alamat": f_alamat.strip(),
                            "No Telpon": f_telp.strip(),
                            "Nama PIC/Kurir": f_pic.strip(),
                            "Keterangan": f_ket.strip(),
                            "Google Map": f_gmap.strip(),
                        }
                        df_ekspedisi = pd.concat(
                            [
                                df_ekspedisi,
                                pd.DataFrame([new_row_eks]),
                            ],
                            ignore_index=True,
                        )
                        df_ekspedisi["No"] = (
                            df_ekspedisi.index + 1
                        ).astype(str)

                        ok_eks, err_eks = save_data_smart(
                            df_ekspedisi,
                            EXCEL_EKSPEDISI_FILE,
                            "Tambah data ekspedisi via Streamlit",
                        )
                        if ok_eks:
                            st.cache_data.clear()
                            st.success(
                                "Data ekspedisi berhasil disimpan ke Excel!"
                            )
                            st.rerun()
                        else:
                            st.error(f"Gagal menyimpan: {err_eks}")

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
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            if os.path.exists(EXCEL_FILE):
                with open(EXCEL_FILE, "rb") as f:
                    excel_bytes = f.read()
                st.download_button(
                    label="📥 Download Excel Cover Mobil",
                    data=excel_bytes,
                    file_name="data_cover_tdc.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True,
                )
        with col_dl2:
            if os.path.exists(EXCEL_EKSPEDISI_FILE):
                with open(EXCEL_EKSPEDISI_FILE, "rb") as f:
                    excel_eks_bytes = f.read()
                st.download_button(
                    label="📥 Download Excel Ekspedisi",
                    data=excel_eks_bytes,
                    file_name="data_ekspedisi_tdc.xlsx",
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
            "<hr style='margin-top: 2px; margin-bottom: 15px;'>",
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
                "Kolom dengan tanda <span style='color:red;'>*</span> wajib"
                " diisi.",
                unsafe_allow_html=True,
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
                mo for mo in base_model_list if mo.lower() == input_model.lower()
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
            for f_idx in range(1, 5):
                k_foto = f"Foto{f_idx}"
                st.markdown(f"**Foto {f_idx}:**")
                uploaded_files[k_foto] = st.file_uploader(
                    f"Foto {f_idx}",
                    type=["jpg", "jpeg", "png"],
                    key=f"up_t{f_idx}",
                    label_visibility="collapsed",
                )

            if st.button("💾 Simpan Data ke Excel", type="primary"):
                if (
                    not str(input_merek).strip()
                    or not str(input_model).strip()
                    or not str(input_tahun).strip()
                ):
                    st.error(
                        "❌ Gagal! Merek, Model, dan Tahun wajib diisi dengan"
                        " benar!"
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
                        ] = f"Data untuk Merek <b>{input_merek}</b>, Model <b>{input_model}</b>, Tahun <b>{input_tahun}</b> sudah pernah ada di database!<br><br>Silakan periksa kembali."
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
                            st.session_state["popup_title"] = "Berhasil Disimpan"
                            st.session_state[
                                "popup_msg"
                            ] = f"Data baru untuk <b>{input_merek} {input_model}</b> berhasil ditambahkan!"
                            st.session_state["popup_type"] = "success"
                            st.session_state["show_popup"] = "aktif"
                            st.rerun()
                        else:
                            st.error(f"Gagal menyimpan ke penyimpanan: {err_msg}")

        elif mode_kelola == "✏️ Edit Data yang Ada":
            st.markdown("### Edit atau Hapus Data Mobil")
            if df.empty:
                st.warning("Belum ada data untuk diedit.")
            else:
                df_tampil_edit = df[
                    df["ID"].astype(str).str.strip() != ""
                ].copy()
                df_tampil_edit.insert(0, "Pilih", False)

                edited_df = st.data_editor(
                    df_tampil_edit.drop(
                        columns=[
                            "Catatan",
                            "Foto1",
                            "Foto2",
                            "Foto3",
                            "Foto4",
                        ],
                        errors="ignore",
                    ),
                    use_container_width=True,
                    hide_index=True,
                    key="grid_edit_data",
                )

                baris_terpilih = edited_df[edited_df["Pilih"] == True]

                if len(baris_terpilih) > 1:
                    st.warning(
                        "⚠️ Pilih hanya **satu** baris data yang ingin"
                        " diedit/dihapus pada satu waktu."
                    )
                elif len(baris_terpilih) == 1:
                    selected_row_orig = baris_terpilih.iloc[0]
                    target_id = str(selected_row_orig["ID"])

                    match_row = df[df["ID"].astype(str) == target_id]
                    if not match_row.empty:
                        row_data = match_row.iloc[0]
                        st.markdown("---")
                        st.markdown(
                            f"### 📝 Edit Data (ID: {target_id}) - "
                            f"{row_data['Merek']} {row_data['Model']} "
                            f"({row_data['Tahun']})"
                        )

                        with st.form(f"form_edit_{target_id}"):
                            edit_merek = st.text_input(
                                "Merek", value=str(row_data["Merek"])
                            )
                            edit_model = st.text_input(
                                "Model", value=str(row_data["Model"])
                            )
                            edit_tahun = st.text_input(
                                "Tahun", value=str(row_data["Tahun"])
                            )

                            edit_sisa = {}
                            for c in df.columns:
                                if c not in [
                                    "ID",
                                    "Merek",
                                    "Model",
                                    "Tahun",
                                    "Status",
                                    "Catatan",
                                    "Pilih",
                                ] + kolom_foto_list:
                                    edit_sisa[c] = st.text_input(
                                        c, value=str(row_data[c])
                                    )

                            current_status_val = str(row_data["Status"])
                            idx_status = (
                                list_status_fix.index(current_status_val)
                                if current_status_val in list_status_fix
                                else 0
                            )
                            edit_status = st.selectbox(
                                "Status",
                                list_status_fix,
                                index=idx_status,
                            )
                            edit_catatan = st.text_area(
                                "Catatan & Riwayat Edit",
                                value=str(row_data.get("Catatan", "")),
                            )

                            st.markdown("---")
                            st.markdown("### 📸 Foto Dokumentasi Saat Ini:")
                            edit_uploaded_files = {}
                            for f_idx in range(1, 5):
                                k_foto = f"Foto{f_idx}"
                                existing_foto_val = str(
                                    row_data.get(k_foto, "")
                                ).strip()
                                if (
                                    existing_foto_val
                                    and existing_foto_val.lower()
                                    not in ["nan", "none", ""]
                                ):
                                    p_existing = os.path.join(
                                        FOTO_FOLDER, existing_foto_val
                                    )
                                    if os.path.exists(p_existing):
                                        st.image(
                                            p_existing,
                                            width=150,
                                            caption=f"Foto {f_idx} (Tersimpan)",
                                        )

                                edit_uploaded_files[k_foto] = st.file_uploader(
                                    f"Ganti/Tambah Foto {f_idx}",
                                    type=["jpg", "jpeg", "png"],
                                    key=f"up_edit_{target_id}_{f_idx}",
                                )

                            col_tombol_1, col_tombol_2 = st.columns(2)
                            with col_tombol_1:
                                submit_update = st.form_submit_button(
                                    "💾 Simpan Perubahan", type="primary"
                                )
                            with col_tombol_2:
                                submit_delete = st.form_submit_button(
                                    "🗑️ Hapus Data Ini", type="secondary"
                                )

                            if submit_update:
                                df_update = df.copy()
                                idx_target_row = df_update[
                                    df_update["ID"].astype(str) == target_id
                                ].index
                                if not idx_target_row.empty:
                                    i_row = idx_target_row[0]
                                    df_update.loc[i_row, "Merek"] = str(
                                        edit_merek
                                    ).strip()
                                    df_update.loc[i_row, "Model"] = str(
                                        edit_model
                                    ).strip()
                                    df_update.loc[i_row, "Tahun"] = str(
                                        edit_tahun
                                    ).strip()
                                    for k_s, v_s in edit_sisa.items():
                                        df_update.loc[i_row, k_s] = str(
                                            v_s
                                        ).strip()
                                    df_update.loc[i_row, "Status"] = str(
                                        edit_status
                                    ).strip()
                                    df_update.loc[i_row, "Catatan"] = str(
                                        edit_catatan
                                    ).strip()

                                    timestamp_awalan = int(
                                        datetime.now().timestamp()
                                    )
                                    for (
                                        key_f,
                                        up_f,
                                    ) in edit_uploaded_files.items():
                                        if up_f is not None:
                                            nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
                                            path_simpan = os.path.join(
                                                FOTO_FOLDER, nama_file_foto
                                            )
                                            with open(path_simpan, "wb") as f:
                                                f.write(up_f.getbuffer())
                                            df_update.loc[
                                                i_row, key_f
                                            ] = nama_file_foto

                                    ok_up, err_up = save_data_smart(
                                        df_update,
                                        EXCEL_FILE,
                                        f"Update data ID {target_id} via Streamlit",
                                    )
                                    if ok_up:
                                        st.cache_data.clear()
                                        st.session_state["popup_title"] = (
                                            "Perubahan Disimpan"
                                        )
                                        st.session_state[
                                            "popup_msg"
                                        ] = f"Data ID <b>{target_id}</b> berhasil diperbarui!"
                                        st.session_state["popup_type"] = (
                                            "success"
                                        )
                                        st.session_state["show_popup"] = "aktif"
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"Gagal menyimpan pembaruan: {err_up}"
                                        )

                            if submit_delete:
                                df_del = df.copy()
                                df_del = df_del[
                                    df_del["ID"].astype(str) != target_id
                                ]
                                ok_del, err_del = save_data_smart(
                                    df_del,
                                    EXCEL_FILE,
                                    f"Hapus data ID {target_id} via Streamlit",
                                )
                                if ok_del:
                                    st.cache_data.clear()
                                    st.session_state["popup_title"] = (
                                        "Data Dihapus"
                                    )
                                    st.session_state[
                                        "popup_msg"
                                    ] = f"Data ID <b>{target_id}</b> berhasil dihapus dari database!"
                                    st.session_state["popup_type"] = "success"
                                    st.session_state["show_popup"] = "aktif"
                                    st.rerun()
                                else:
                                    st.error(f"Gagal menghapus data: {err_del}")