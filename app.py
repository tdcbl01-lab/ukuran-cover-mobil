elif menu == "✏️ Edit Data yang Ada":
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

                val_merek_asli = str(df.loc[idx_pilih, "Merek"]) if "Merek" in df.columns else ""
                val_model_asli = str(df.loc[idx_pilih, "Model"]) if "Model" in df.columns else ""
                val_tahun_aktif = str(df.loc[idx_pilih, "Tahun"]) if "Tahun" in df.columns else ""
                val_status_aktif = str(df.loc[idx_pilih, "Status"]) if "Status" in df.columns else "STANDAR"

                st.markdown("Kolom dengan tanda <span style='color:red;'>*</span> wajib diisi.", unsafe_allow_html=True)

                # --- MEREK SELECTBOX ---
                base_merek_list = sorted([m for m in df["Merek"].dropna().unique() if str(m).strip() != ""])
                if val_merek_asli not in base_merek_list and val_merek_asli != "":
                    base_merek_list = [val_merek_asli] + base_merek_list

                extended_merek_set_edit = set(base_merek_list)
                for m in base_merek_list:
                    extended_merek_set_edit.add(m.lower())
                    extended_merek_set_edit.add(m.upper())
                existing_merek_list_edit = sorted(list(extended_merek_set_edit))

                default_merek_idx = (
                    existing_merek_list_edit.index(val_merek_asli) + 1
                    if val_merek_asli in existing_merek_list_edit
                    else 0
                )

                st.markdown("Merek <span style='color:red;'>*</span>", unsafe_allow_html=True)
                selected_edit_merek_raw = st.selectbox(
                    "Merek Edit",
                    options=[""] + existing_merek_list_edit,
                    index=default_merek_idx,
                    accept_new_options=True,
                    label_visibility="collapsed",
                    key="edit_merek_selectbox",
                )

                input_edit_merek = str(selected_edit_merek_raw).strip()
                if input_edit_merek.lower().startswith("add:"):
                    input_edit_merek = input_edit_merek[4:].strip()

                # --- MODEL SELECTBOX ---
                df_merek_edit_pilih = df[df["Merek"].astype(str).str.strip().str.lower() == input_edit_merek.lower()]
                base_model_list_edit = sorted([mo for mo in df_merek_edit_pilih["Model"].dropna().unique() if str(mo).strip() != ""])
                if val_model_asli not in base_model_list_edit and val_model_asli != "":
                    base_model_list_edit = [val_model_asli] + base_model_list_edit

                extended_model_set_edit = set(base_model_list_edit)
                for mo in base_model_list_edit:
                    extended_model_set_edit.add(mo.lower())
                    extended_model_set_edit.add(mo.upper())
                existing_model_list_edit = sorted(list(extended_model_set_edit))

                default_model_idx = (
                    existing_model_list_edit.index(val_model_asli) + 1
                    if val_model_asli in existing_model_list_edit
                    else 0
                )

                st.markdown("Model <span style='color:red;'>*</span>", unsafe_allow_html=True)
                selected_edit_model_raw = st.selectbox(
                    "Model Edit",
                    options=[""] + existing_model_list_edit,
                    index=default_model_idx,
                    accept_new_options=True,
                    label_visibility="collapsed",
                    key="edit_model_selectbox",
                )

                input_edit_model = str(selected_edit_model_raw).strip()
                if input_edit_model.lower().startswith("add:"):
                    input_edit_model = input_edit_model[4:].strip()

                # --- INPUT TAHUN & KOLOM LAINNYA BERDASARKAN idx_pilih ---
                st.markdown("Tahun <span style='color:red;'>*</span>", unsafe_allow_html=True)
                edit_tahun = st.text_input(
                    "Tahun Edit",
                    value=val_tahun_aktif,
                    label_visibility="collapsed",
                    key=f"edit_tahun_{idx_pilih}",
                )

                edit_sisa_data = {}
                for col in df.columns:
                    if col not in ["ID", "Pilihan_Edit", "Merek", "Model", "Tahun", "Status"] + kolom_foto_list:
                        val_col_aktif = str(df.loc[idx_pilih, col]) if col in df.columns else ""
                        if val_col_aktif.lower() in ["nan", "none"]:
                            val_col_aktif = ""
                        
                        if col in kolom_wajib:
                            st.markdown(f"{col} <span style='color:red;'>*</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"{col}", unsafe_allow_html=True)
                            
                        edit_sisa_data[col] = st.text_input(
                            f"edit_{col}",
                            value=val_col_aktif,
                            label_visibility="collapsed",
                            key=f"edit_{col}_{idx_pilih}",
                        )

                try:
                    status_idx = list_status_fix.index(val_status_aktif)
                except ValueError:
                    status_idx = 0
                st.markdown("Status <span style='color:red;'>*</span>", unsafe_allow_html=True)
                edit_status = st.selectbox(
                    "Status Edit",
                    list_status_fix,
                    index=status_idx,
                    label_visibility="collapsed",
                    key=f"edit_status_{idx_pilih}",
                )