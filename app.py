# ----------------- LOGIKA DIALOG POP-UP SIMPAN (ANTI NYANGKUT) -----------------
@st.dialog("⚠️ Konfirmasi Simpan Data")
def dialog_konfirmasi_tambah(data_baru):
  st.write("Apakah data sudah benar?")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("✅ Ya, Simpan", use_container_width=True):
      try:
        # Baca DataFrame fisik terbaru langsung secara aman
        if os.path.exists(EXCEL_FILE):
          current_df = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
        else:
          current_df = df

        # Gabungkan data baru
        updated_df = pd.concat(
            [current_df, pd.DataFrame([data_baru])], ignore_index=True
        )
        
        # Coba simpan langsung ke file Excel
        updated_df.to_excel(EXCEL_FILE, index=False)
        
        # Sync ke GitHub di background
        sync_to_github_background(EXCEL_FILE)

        st.cache_data.clear()
        st.session_state["notif_sukses"] = (
            "✅ Data berhasil ditambahkan ke Excel & GitHub!"
        )
        st.rerun()

      except PermissionError:
        st.error(
            "❌ **GAGAL SIMPAN!** File `data_cover.xlsx` terkunci oleh Windows"
            " atau Microsoft Excel. **Tutup total aplikasi Excel Anda**, pastikan"
            " tidak ada proses Excel yang nyangkut di Task Manager, lalu klik simpan lagi!"
        )
      except Exception as e:
        st.error(f"❌ Terjadi kesalahan sistem saat menyimpan: {e}")

  with col2:
    if st.button("❌ Batal", use_container_width=True):
      st.rerun()