elif mode_kelola == "✏️ Edit Data yang Ada":
            df_aktif = df[df["ID"].astype(str).str.strip() != ""].copy()
            if df_aktif.empty:
                st.info("Data kosong.")
            else:
                df_aktif["Pilihan_Edit"] = (
                    "ID " + df_aktif["ID"].astype(str)
                    + " - "
                    + df_aktif["Merek"]
                    + " "
                    + df_aktif["Model"]
                    + " ("
                    + df_aktif["Tahun"]
                    + ")"
                )

                # --- FUNGSI CALLBACK KETIKA PILIHAN DATA DIGANTI ---
                def update_edit_form_state():
                    selected_val = st.session_state["select_data_edit_unique"]
                    sel_id = selected_val.split(" - ")[0].replace("ID", "").strip()
                    row_match = df_aktif[df_aktif["ID"].astype(str).str.strip() == sel_id]
                    
                    if not row_match.empty:
                        idx = row_match.index[0]
                        st.session_state["edit_merek_val"] = str(df.loc[idx, "Merek"])
                        st.session_state["edit_model_val"] = str(df.loc[idx, "Model"])
                        st.session_state["edit_tahun_val"] = str(df.loc[idx, "Tahun"])
                        st.session_state["edit_status_val"] = str(df.loc[idx, "Status"]) if "Status" in df.columns else "STANDAR"
                        for c in df.columns:
                            if c not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
                                st.session_state[f"edit_{c}_val"] = str(df.loc[idx, c]) if c in df.columns else ""

                # Selectbox dengan on_change callback
                select_edit_pilihan = st.selectbox(
                    "Pilih Data:",
                    df_aktif["Pilihan_Edit"].unique(),
                    key="select_data_edit_unique",
                    on_change=update_edit_form_state
                )
                
                id_terpilih = select_edit_pilihan.split(" - ")[0].replace("ID", "").strip()
                match_row = df_aktif[df_aktif["ID"].astype(str).str.strip() == id_terpilih]
                
                if match_row.empty:
                    st.error("Data tidak ditemukan.")
                else:
                    idx_pilih = match_row.index[0]

                    # Inisialisasi session state pertama kali jika kosong
                    if "edit_merek_val" not in st.session_state:
                        st.session_state["edit_merek_val"] = str(df.loc[idx_pilih, "Merek"])
                        st.session_state["edit_model_val"] = str(df.loc[idx_pilih, "Model"])
                        st.session_state["edit_tahun_val"] = str(df.loc[idx_pilih, "Tahun"])
                        st.session_state["edit_status_val"] = str(df.loc[idx_pilih, "Status"]) if "Status" in df.columns else "STANDAR"
                        for c in df.columns:
                            if c not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
                                st.session_state[f"edit_{c}_val"] = str(df.loc[idx_pilih, c]) if c in df.columns else ""

                    st.markdown(f"**Edit Data untuk ID {id_terpilih}**")
                    st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)

                    st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
                    edit_merek = st.text_input("Edit Merek", value=st.session_state["edit_merek_val"], key="input_edit_merek", label_visibility="collapsed")
                    
                    st.markdown("Model <span style='color:red;'>*</span>", unsafe_allow_html=True)
                    edit_model = st.text_input("Edit Model", value=st.session_state["edit_model_val"], key="input_edit_model", label_visibility="collapsed")
                    
                    st.markdown("Tahun <span style='color:red;'>*</span>", unsafe_allow_html=True)
                    edit_tahun = st.text_input("Edit Tahun", value=st.session_state["edit_tahun_val"], key="input_edit_tahun", label_visibility="collapsed")

                    edit_sisa_data = {}
                    for col in df.columns:
                        if col not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
                            val_state_key = f"edit_{col}_val"
                            default_col_val = st.session_state.get(val_state_key, str(df.loc[idx_pilih, col]) if col in df.columns else "")
                            
                            if col in kolom_wajib:
                                st.markdown(f"{col} <span style='color:red;'>*</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"{col}", unsafe_allow_html=True)
                                
                            edit_sisa_data[col] = st.text_input(f"Edit {col}", value=default_col_val, key=f"input_edit_{col}", label_visibility="collapsed")

                    try:
                        idx_status_default = list_status_fix.index(st.session_state["edit_status_val"])
                    except ValueError:
                        idx_status_default = 0

                    st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
                    edit_status = st.selectbox("Edit Status", list_status_fix, index=idx_status_default, key="input_edit_status", label_visibility="collapsed")

                    st.markdown("---")
                    st.markdown("### 📸 Update Foto Dokumentasi (Opsional):")
                    edit_uploaded_files = {}
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        edit_uploaded_files["Foto1"] = st.file_uploader("Ganti Foto 1", type=["jpg", "jpeg", "png"], key="edit_up_1")
                        edit_uploaded_files["Foto2"] = st.file_uploader("Ganti Foto 2", type=["jpg", "jpeg", "png"], key="edit_up_2")
                    with ec2:
                        edit_uploaded_files["Foto3"] = st.file_uploader("Ganti Foto 3", type=["jpg", "jpeg", "png"], key="edit_up_3")
                        edit_uploaded_files["Foto4"] = st.file_uploader("Ganti Foto 4", type=["jpg", "jpeg", "png"], key="edit_up_4")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("💾 Simpan Perubahan", type="primary", key="btn_save_changes_edit"):
                            if not str(edit_merek).strip() or not str(edit_model).strip() or not str(edit_tahun).strip():
                                st.error("❌ Gagal! Merek, Model, dan Tahun wajib diisi dengan benar!")
                            else:
                                abs_p_edit = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_FILE) if "__file__" in locals() else EXCEL_FILE
                                if os.path.exists(abs_p_edit):
                                    df_edit_db = pd.read_excel(abs_p_edit, dtype=str, keep_default_na=False)
                                    df_edit_db.columns = df_edit_db.columns.str.strip()
                                else:
                                    df_edit_db = df.copy()

                                if idx_pilih < len(df_edit_db):
                                    df_edit_db.loc[idx_pilih, "Merek"] = str(edit_merek).strip()
                                    df_edit_db.loc[idx_pilih, "Model"] = str(edit_model).strip()
                                    df_edit_db.loc[idx_pilih, "Tahun"] = str(edit_tahun).strip()
                                    df_edit_db.loc[idx_pilih, "Status"] = str(edit_status).strip()

                                    for k, v in edit_sisa_data.items():
                                        if k in df_edit_db.columns:
                                            df_edit_db.loc[idx_pilih, k] = str(v).strip()

                                    timestamp_awalan = int(datetime.now().timestamp())
                                    for key_f, up_f in edit_uploaded_files.items():
                                        if up_f is not None:
                                            nama_file_foto = f"{timestamp_awalan}_{key_f}_{up_f.name}"
                                            path_simpan = os.path.join(FOTO_FOLDER, nama_file_foto)
                                            with open(path_simpan, "wb") as f:
                                                f.write(up_f.getbuffer())
                                            if key_f in df_edit_db.columns:
                                                df_edit_db.loc[idx_pilih, key_f] = nama_file_foto

                                    sukses_edit, err_msg_edit = save_data_smart(
                                        df_edit_db,
                                        EXCEL_FILE,
                                        f"Update data ID {id_terpilih} via Streamlit",
                                    )

                                    if sukses_edit:
                                        st.cache_data.clear()
                                        for key_to_del in list(st.session_state.keys()):
                                            if "edit_" in key_to_del:
                                                del st.session_state[key_to_del]

                                        st.session_state["popup_title"] = "Berhasil Diperbarui!"
                                        st.session_state["popup_msg"] = f"Data untuk ID <b>{id_terpilih}</b> berhasil diperbarui dan tersimpan permanen!"
                                        st.session_state["popup_type"] = "success"
                                        st.session_state["show_popup"] = "aktif"
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Gagal memperbarui data: {err_msg_edit}")
                                else:
                                    st.error("❌ Terjadi kesalahan indeks baris data.")

                    with col_b2:
                        if st.button("🗑️ Hapus Data Ini", type="secondary", key="btn_del_data_edit"):
                            df_edit_db = df.drop(idx_pilih).reset_index(drop=True)
                            if "ID" in df_edit_db.columns and not df_edit_db.empty:
                                df_edit_db["ID"] = (df_edit_db.index + 1).astype(str)

                            sukses_simpan, err_msg = save_data_smart(
                                df_edit_db,
                                EXCEL_FILE,
                                f"Hapus data ID {id_terpilih} via Streamlit",
                            )

                            if sukses_simpan:
                                st.cache_data.clear()
                                for key_to_del in list(st.session_state.keys()):
                                    if "edit_" in key_to_del:
                                        del st.session_state[key_to_del]

                                st.session_state["popup_title"] = "Berhasil Dihapus!"
                                st.session_state["popup_msg"] = "Data berhasil dihapus dari database."
                                st.session_state["popup_type"] = "success"
                                st.session_state["show_popup"] = "aktif"
                                st.rerun()
                            else:
                                st.error(f"❌ Gagal menghapus data: {err_msg}")