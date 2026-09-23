import streamlit as st
import pandas as pd
# Tambahkan import lain yang Anda butuhkan (misal: koneksi database, dll)

# --- FUNGSI RESET CACHE STATE EDIT ---
def reset_edit_state():
    for key in list(st.session_state.keys()):
        if key.startswith("edit_"):
            del st.session_state[key]

def main():
    st.title("Aplikasi Manajemen Data Mobil")

    # Contoh DataFrame (Sesuaikan dengan data/koneksi Anda yang sebenarnya)
    if "data_mobil" not in st.session_state:
        st.session_state["data_mobil"] = pd.DataFrame({
            "ID_Mobil": ["M001", "M002", "M003"],
            "Merek": ["Toyota", "Honda", "Suzuki"],
            "Model": ["Avanza", "Civic", "Ertiga"],
            "Tahun": [2020, 2022, 2021],
            "Ukuran": ["Sedang", "Sedang", "Sedang"],
            "Panjang": [4190, 4670, 4395],
            "Lebar": [1660, 1800, 1735]
        })

    df_aktif = st.session_state["data_mobil"].copy()

    # Membuat kolom gabungan unik untuk pilihan edit (misal: ID + Merek + Model)
    df_aktif["Pilihan_Edit"] = df_aktif["ID_Mobil"].astype(str) + " - " + df_aktif["Merek"] + " " + df_aktif["Model"]

    st.subheader("Menu Edit Data Mobil")

    # Dropdown Pilih Data dengan on_change=reset_edit_state
    select_edit_pilihan = st.selectbox(
        "Pilih Data:",
        df_aktif["Pilihan_Edit"].unique(),
        key="select_data_edit_unique",
        on_change=reset_edit_state, # <--- Mengosongkan cache state saat pilihan diganti
    )

    # Ambil baris data yang sesuai dengan pilihan
    if select_edit_pilihan:
        id_terpilih = select_edit_pilihan.split(" - ")[0]
        data_terpilih = df_aktif[df_aktif["ID_Mobil"] == id_terpilih].iloc[0]

        st.markdown("---")
        st.write(f"Form Edit untuk ID: **{id_terpilih}**")

        # Input Form Edit (menggunakan key dengan awalan 'edit_')
        merek_baru = st.text_input("Merek", value=data_terpilih["Merek"], key="edit_merek")
        model_baru = st.text_input("Model", value=data_terpilih["Model"], key="edit_model")
        tahun_baru = st.number_input("Tahun", value=int(data_terpilih["Tahun"]), key="edit_tahun")
        ukuran_baru = st.text_input("Ukuran", value=data_terpilih["Ukuran"], key="edit_ukuran")
        panjang_baru = st.number_input("Panjang", value=float(data_terpilih["Panjang"]), key="edit_panjang")
        lebar_baru = st.number_input("Lebar", value=float(data_terpilih["Lebar"]), key="edit_lebar")

        if st.button("Simpan Perubahan"):
            # Update data ke dataframe / database Anda di sini
            idx = st.session_state["data_mobil"][st.session_state["data_mobil"]["ID_Mobil"] == id_terpilih].index[0]
            st.session_state["data_mobil"].at[idx, "Merek"] = merek_baru
            st.session_state["data_mobil"].at[idx, "Model"] = model_baru
            st.session_state["data_mobil"].at[idx, "Tahun"] = tahun_baru
            st.session_state["data_mobil"].at[idx, "Ukuran"] = ukuran_baru
            st.session_state["data_mobil"].at[idx, "Panjang"] = panjang_baru
            st.session_state["data_mobil"].at[idx, "Lebar"] = lebar_baru
            
            st.success("Data berhasil diperbarui!")
            st.rerun()

    # Tampilkan tabel data saat ini
    st.markdown("---")
    st.subheader("Tabel Data Mobil Saat Ini")
    st.dataframe(st.session_state["data_mobil"])

if __name__ == "__main__":
    main()