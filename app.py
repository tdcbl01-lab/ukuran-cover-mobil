elif mode_kelola == "➕ Tambah Data Baru":
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

      # Tombol Simpan Biasa (Tanpa st.form agar pembacaan nilai 100% akurat)
      if st.button("💾 Simpan Data ke Excel", type="primary"):
        # Validasi kolom wajib
        if not input_merek.strip() or not input_model.strip() or not input_tahun.strip():
          st.error("❌ Gagal! Merek, Model, dan Tahun wajib diisi!")
        else:
          # Siapkan data baris baru
            baru_data = {
                "ID": str(next_id),
                "Merek": str(input_merek).strip(),
                "Model": str(input_model).strip(),
                "Tahun": str(input_tahun).strip(),
                "Status": str(input_status).strip()
            }
            for k, v in input_sisa_data.items():
              baru_data[k] = str(v).strip()

            # Proses foto
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

            # Baca file fisik terbaru detik ini
            if os.path.exists(EXCEL_FILE):
              df_fisik = pd.read_excel(EXCEL_FILE, dtype=str, keep_default_na=False)
              df_fisik.columns = df_fisik.columns.str.strip()
            else:
              df_fisik = pd.DataFrame(columns=list(baru_data.keys()))

            # Pastikan kolom sinkron
            for c in df_fisik.columns:
              if c not in baru_data:
                baru_data[c] = ""

            df_baru_item = pd.DataFrame([baru_data])
            df_final = pd.concat([df_fisik, df_baru_item], ignore_index=True)
            
            # Eksekusi tulis mutlak
            df_final.to_excel(EXCEL_FILE, index=False)
            
            # Sync & Bersihkan Cache
            sync_to_github_background(EXCEL_FILE)
            st.cache_data.clear()

            st.success("🎉 BERHASIL! Data sudah tertulis permanen ke file Excel.")
            st.balloons()