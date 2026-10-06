import base64
from datetime import datetime
from io import BytesIO
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Aplikasi Cover Mobil TDC")

FOTO_FOLDER = "foto_cover"
if not os.path.exists(FOTO_FOLDER):
    os.makedirs(FOTO_FOLDER)

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
SHEET_ID = "17jSyS0mOaTpGUBmr6y-xv8m3_iz-RySf"
SHEET_NAME = "Sheet1"
GSHEET_NAME = "data_cover"  # Ganti dengan judul/nama file Google Sheets Anda jika berbeda

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def save_to_google_sheets(baru_data):
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
            client = gspread.authorize(creds)
            sheet = client.open(GSHEET_NAME).sheet1

            row_values = [
                str(baru_data.get("ID", "")),
                str(baru_data.get("Merek", "")),
                str(baru_data.get("Model", "")),
                str(baru_data.get("Tahun", "")),
                str(baru_data.get("Ukuran", "")),
                str(baru_data.get("Panjang", "")),
                str(baru_data.get("Lebar", "")),
                str(baru_data.get("Tinggi", "")),
                str(baru_data.get("Status", "")),
                str(baru_data.get("Catatan", "")),
                str(baru_data.get("Foto1", "")),
                str(baru_data.get("Foto2", "")),
                str(baru_data.get("Foto3", "")),
                str(baru_data.get("Foto4", "")),
            ]
            sheet.append_row(row_values)
            return True, ""
        else:
            return False, "Kredensial gcp_service_account belum diatur di st.secrets."
    except Exception as e:
        return False, str(e)


def save_data_smart(df_target, file_path, commit_message):
    absolute_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path) if "__file__" in locals() else file_path

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

    try:
        df_target.to_excel(absolute_file_path, index=False)
    except Exception as e:
        return False, str(e)

    if not has_github_secrets:
        return True, ""

    try:
        gh = st.secrets["github"]
        token = gh.get("token")
        repo = gh.get("repo")
        branch = gh.get("branch", "main")

        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

        sha = None
        r_get = requests.get(url, headers=headers)
        if r_get.status_code == 200:
            sha = r_get.json().get("sha")

        with open(absolute_file_path, "rb") as f:
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
        return False, f"GitHub API status code {r_put.status_