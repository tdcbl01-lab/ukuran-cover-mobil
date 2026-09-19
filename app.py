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
                idx_pilih_awal = int(idx_str.split(" - ")[0])

                val_merek_asli = (
                    str(df.loc[idx_pilih_awal, "Merek"])
                    if "Merek" in df.columns
                    else ""
                )
                val_model_asli = (
                    str(df.loc[idx_pilih_awal, "Model"])
                    if "Model" in df.columns
                    else ""
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
                    key=f"edit_merek_choice_{idx_pilih_awal}",
                )

                # --- MODEL SELECTBOX ---
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
                    key=f"edit_model_choice_{idx_pilih_awal}",
                )

                # --- TEMUKAN INDEKS BARIS AKTIF BERDASARKAN MEREK & MODEL YANG DIPILIH ---
                matched_row = df[
                    (df["Merek"].astype(str).str.strip().str.lower() == str(edit_merek).strip().lower()) & 
                    (df["Model"].astype(str).str.strip().str.lower() == str(edit_model).strip().lower())
                ]
                if not matched_row.empty:
                    idx_pilih = matched_row.index[0]
                else:
                    idx_pilih = idx_pilih_awal

                # AMBIL NILAI AKTIF DARI BARIS YANG BARU
                val_tahun_aktif = str(df.loc[idx_pilih, "Tahun"]) if "Tahun" in df.columns else ""
                val_status_aktif = str(df.loc[idx_pilih, "Status"]) if "Status" in df.columns else "STANDAR"

                st.markdown(
                    "Tahun <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                # PERHATIKAN: Key menggunakan idx_pilih agar ikut ter-refresh saat baris berubah
                edit_tahun = st.text_input(
                    "Tahun Edit",
                    value=val_tahun_aktif,
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
                        val_col_aktif = (
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
                                value=val_col_aktif,
                                label_visibility="collapsed",
                                key=f"edit_{col}_{idx_pilih}",
                            )
                        else:
                            st.markdown(f"{col}", unsafe_allow_html=True)
                            edit_sisa_data[col] = st.text_input(
                                f"edit_{col}",
                                value=val_col_aktif,
                                label_visibility="collapsed",
                                key=f"edit_{col}_{idx_pilih}",
                            )

                st.markdown(
                    "Status <span style='color:red;'>*</span>",
                    unsafe_allow_html=True,
                )
                try:
                    status_idx = list_status_fix.index(val_status_aktif)
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