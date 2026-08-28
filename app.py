def sync_to_github_background(file_path):
  """Fungsi otomatis yang membaca token dari st.secrets untuk sync ke GitHub"""
  try:
    # Abaikan file temporary Excel seperti ~$data_cover.xlsx
    if "~\$" in file_path or os.path.basename(file_path).startswith("~$"):
      return

    if "github" in st.secrets and os.path.exists(file_path):
      gh = st.secrets["github"]
      token = gh.get("token")
      repo = gh.get("repo")  # Format: "username/nama-repo"
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