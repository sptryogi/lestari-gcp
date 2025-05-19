import random
import re
import pandas as pd
import numpy as np


def constraint_text(text, df_kamus, df_idiom):

    # ================= Clean text_kecil =================
    text = text.replace("-", " ")
    text_kecil_clean = re.sub(r"[^\w\s-]", "", text.lower())

    kata_kalimat = set(text_kecil_clean.split())

    # ================= Filter Kata di Kamus IDIOM & PARIBASA =================
    df_idiom["IDIOM"] = df_idiom["IDIOM"].str.lower().str.replace(";", ",", regex=False)
    df_idiom["IDIOM"] = df_idiom["IDIOM"].str.replace("é", "e")

    # Mengubah seluruh kolom menjadi satu list besar
    all_idioms = []
    for row in df_idiom["IDIOM"]:
        items = [i.strip() for i in row.split(",")]
        all_idioms.extend(items)

    def extract_idiom_words(kalimat_asli, word_list):
        kalimat_normal = kalimat_asli.replace("é", "e")

        words_asli = kalimat_asli.split()
        words_normal = kalimat_normal.split()
        result = []

        used_indices = set()

        # Cari idiom dari yang panjang ke pendek
        for length in [5, 4, 3, 2]:
            for i in range(len(words_normal) - length + 1):
                if any((i + j) in used_indices for j in range(length)):
                    continue  # Lewati jika bagian dari idiom sebelumnya

                sublist = " ".join(words_normal[i : i + length])
                if sublist in word_list:
                    result.extend(words_asli[i : i + length])
                    used_indices.update(range(i, i + length))

        return result

    # Panggil fungsi
    filtered_words_idiom = extract_idiom_words(text_kecil_clean, all_idioms)
    print(f"==========> {filtered_words_idiom}")

    # kata_kalimat = kata_kalimat - set(filtered_words_idiom)
    # print(f"==========> {kata_kalimat}")

    # ================= Filter Kata di Kamus LEMA=================

    df_e_petik = df_kamus[df_kamus["LEMA"].str.contains("[éÉ]", na=False, regex=True)]
    df_e_petik.loc[:, "LEMA"] = df_e_petik["LEMA"].str.replace("[éÉ]", "e", regex=True)
    kata_e_petik = {kata.lower() for kata in df_e_petik["LEMA"].astype(str)}

    # Ambil baris yang mengandung é atau É pada SUBLEMA
    df_e_petik_sub = df_kamus[
        df_kamus["SUBLEMA"].str.contains("[éÉ]", na=False, regex=True)
    ]
    df_e_petik_sub.loc[:, "SUBLEMA"] = df_e_petik_sub["SUBLEMA"].str.replace(
        "[éÉ]", "e", regex=True
    )
    kata_e_petik_sub = {
        item.strip().lower()
        for sublema in df_e_petik_sub["SUBLEMA"].dropna()
        for item in sublema.split(",")
    }

    df_e_petik2 = df_kamus[df_kamus["LEMA"].str.contains("[èÈ]", na=False, regex=True)]
    df_e_petik2.loc[:, "LEMA"] = df_e_petik2["LEMA"].str.replace(
        "[èÈ]", "e", regex=True
    )
    kata_e_petik2 = {kata.lower() for kata in df_e_petik2["LEMA"].astype(str)}

    kata_dataframe1 = {
        kata.lower() for kata in df_kamus["LEMA"].astype(str)
    }  # Konversi ke string jika ada NaN

    kata_dataframe2 = {
        kata.strip().replace(".", "")  # Hapus spasi ekstra & titik
        for kata_list in df_kamus["SUBLEMA"].astype(str)  # Konversi ke string
        for kata in kata_list.split(",")  # Pecah berdasarkan koma
        if kata.strip()  # Hanya tambahkan jika tidak kosong
    }

    # Ambil baris yang mengandung é atau É pada SUBLEMA
    df_e_petik_sub2 = df_kamus[
        df_kamus["SUBLEMA"].str.contains("[èÈ]", na=False, regex=True)
    ]
    df_e_petik_sub2.loc[:, "SUBLEMA"] = df_e_petik_sub2["SUBLEMA"].str.replace(
        "[èÈ]", "e", regex=True
    )
    kata_e_petik_sub2 = {
        item.strip().lower()
        for sublema in df_e_petik_sub2["SUBLEMA"].dropna()
        for item in sublema.split(",")
    }

    # Membersihkan teks: Menghapus tanda baca dan membuat huruf kecil
    def clean_text(text):
        text = re.sub(r"[^\w\s]", "", text)  # Hapus tanda baca
        return text.lower()  # Konversi ke huruf kecil

    kata_dataframe3 = {
        kata.strip().replace(".", "")  # Hapus spasi ekstra & titik
        for kata_list in df_kamus["SINONIM"].astype(str)  # Konversi ke string
        for kata in kata_list.split(",")  # Pecah berdasarkan koma
        if kata.strip()  # Hanya tambahkan jika tidak kosong
    }

    # Memisahkan setiap kata dalam set
    # kata_dataframe4 = {
    #     kata
    #     for kalimat in df_kamus["CONTOH KALIMAT LOMA"].astype(str)
    #     for kata in clean_text(kalimat).split()
    # }

    # kata_dataframe = kata_dataframe1 | kata_dataframe2 | kata_dataframe4

    kata_dataframe = (
        kata_dataframe1
        | kata_dataframe2
        | kata_dataframe3
        # | kata_dataframe4
        | kata_e_petik
        | kata_e_petik2
        # | nama_orang_tempat
        | kata_e_petik_sub
        | kata_e_petik_sub2
    )

    kata_terdapat = sorted(kata_kalimat.intersection(kata_dataframe))
    kata_terdapat = [kata for kata in kata_terdapat if not re.search(r"\d", kata)]
    kata_terdapat = kata_terdapat + filtered_words_idiom

    kata_tidak_terdapat = sorted(kata_kalimat - kata_dataframe)
    kata_tidak_terdapat = [
        kata for kata in kata_tidak_terdapat if not re.search(r"\d", kata)
    ]
    kata_tidak_terdapat = [
        kata for kata in kata_tidak_terdapat if kata not in filtered_words_idiom
    ]

    print("\n")
    print("Kata yang ditemukan di Kamus:", kata_terdapat)
    print("Kata yang tidak ditemukan di Kamus:", kata_tidak_terdapat)

    # =====================================================================================
    # ======================== 9. Apakah ada sinonim Berjenis Loma? ========================
    # =====================================================================================

    # Dictionary untuk menyimpan pasangan kata asli dan kata pengganti
    pasangan_kata = {}
    kata_terdapat_tidak_loma = []

    # Loop setiap kata dalam kata_terdapat
    for kata in kata_terdapat[
        :
    ]:  # Gunakan slicing agar bisa mengubah list di dalam loop
        # Cari kata di kamus
        row = df_kamus[df_kamus["LEMA"].str.lower() == kata]

        if not row.empty:
            kategori = row["(HALUS/LOMA/KASAR)"].values[0]  # Ambil kategori kata utama

            if pd.notna(kategori) and "LOMA" not in kategori.upper():
                # Ambil daftar sinonim dari kolom SINONIM
                sinonim_raw = (
                    row["SINONIM"].values[0]
                    if pd.notna(row["SINONIM"].values[0])
                    else ""
                )
                sinonim_list = [s.strip() for s in sinonim_raw.split(",") if s.strip()]

                # Cari sinonim yang berkategori "LOMA"
                sinonim_loma = []
                for sinonim in sinonim_list:
                    sinonim_row = df_kamus[df_kamus["LEMA"].str.lower() == sinonim]
                    if not sinonim_row.empty:
                        kategori_sinonim = sinonim_row["(HALUS/LOMA/KASAR)"].values[0]
                        if kategori_sinonim == "LOMA":
                            sinonim_loma.append(sinonim)

                # Jika ada sinonim LOMA, pilih salah satu sebagai pengganti
                if sinonim_loma:
                    pasangan_kata[kata] = random.choice(sinonim_loma)
                else:
                    # Jika tidak ada sinonim LOMA, pindahkan ke kata_tidak_terdapat
                    kata_tidak_terdapat.append(kata)
                    kata_terdapat.remove(kata)  # Hapus dari kata_terdapat
                    kata_terdapat_tidak_loma.append(kata)

    # Tampilkan hasil pasangan kata
    for kata_asli, kata_pengganti in pasangan_kata.items():
        kata_terdapat.append(kata_pengganti)
        print(f"{kata_asli} -> {kata_pengganti}")

    print(pasangan_kata)

    # =====================================================================================
    # ================================ 10.Pengecekan Typo =================================
    # =====================================================================================

    return (
        kata_terdapat,
        kata_tidak_terdapat,
        kata_terdapat_tidak_loma,
        pasangan_kata,
        kata_e_petik,
        kata_e_petik2,
        kata_e_petik_sub,
        kata_e_petik_sub2,
        filtered_words_idiom,
    )


def highlight_text(translated_text, df_kamus, df_idiom, fitur):
    (
        kata_terdapat,
        kata_tidak_terdapat,
        kata_terdapat_tidak_loma,
        pasangan_kata,
        kata_e_petik,
        kata_e_petik2,
        kata_e_petik_sub,
        kata_e_petik_sub2,
        filtered_words_idiom,
    ) = constraint_text(translated_text, df_kamus, df_idiom)

    hasil_lines = []
    pasangan_ekuivalen = {}

    for baris in translated_text.splitlines():
        kata_list = baris.split()
        hasil_baris = []

        i = 0
        while i < len(kata_list):
            match = re.match(r"^(\W*)([\w'-]+)(\W*)$", kata_list[i])
            if not match:
                matches = re.findall(r"\*([^\s*]+)\*", translated_text)
                if matches:
                    kata_list_clean = re.sub(r"[^a-zA-Z0-9\s]", "", kata_list[i])
                    if kata_list_clean not in kata_terdapat:
                        hasil_baris.append(
                            f'<span style="color:blue; font-style:italic;">{kata_list[i]}</span>'
                        )
                    else:
                        hasil_baris.append(kata_list[i])
                else:
                    hasil_baris.append(kata_list[i])
                i += 1
                continue

            simbol_depan, kata, simbol_belakang = match.groups()
            kata = pasangan_kata.get(kata, kata)

            if kata.lower() not in kata_terdapat:
                if kata.lower() not in kata_terdapat_tidak_loma:
                    if re.search(r"\d", kata):
                        hasil_baris.append(simbol_depan + kata + simbol_belakang)
                    else:
                        hasil_baris.append(
                            f'{simbol_depan}<span style="color:red; font-style:italic;">{kata}</span>{simbol_belakang}'
                        )
                else:
                    if kata not in filtered_words_idiom and fitur == "chatbot":
                        # print(f"==? ASD : {kata}")
                        ekuivalen = df_kamus[df_kamus["LEMA"] == kata][
                            "ARTI EKUIVALEN 1"
                        ].values
                        if len(ekuivalen) > 0 and not pd.isna(
                            ekuivalen[0]
                        ):  # Check if ekuivalen is not empty 
                            print(f"EKUIVALEN ARRAY =========> {ekuivalen}")
                            # Pastikan ambil elemen pertama
                            ekuivalen = ekuivalen[0] if isinstance(ekuivalen, (list, np.ndarray)) else ekuivalen
                            ekuivalen = str(ekuivalen).split(',')[0]
                            pasangan_ekuivalen[kata] = ekuivalen
                            print(f"TYPE =========> {type(ekuivalen)}")                         
                            hasil_baris.append(
                                f'{simbol_depan}<span>{ekuivalen}</span>{simbol_belakang}'
                            )
                            print("ADA EKUIVALENNYA")
                        else:
                            ekuivalen = kata
                            hasil_baris.append(                               
                                f'{simbol_depan}<span style="color:purple; font-style:italic;">{ekuivalen}</span>{simbol_belakang}'
                            )                            
                            print("TIDAK ADA EKUIVALENNYA")

                        print(f"===========>>> {ekuivalen}")
                    else:
                        # print(f"==? XZY : {kata}")
                        hasil_baris.append(
                            f'{simbol_depan}<span>{kata}</span>{simbol_belakang}'
                        )
            else:
                kata_lower = kata.lower()
                if kata_lower in kata_e_petik:
                    kata = kata.replace("e", "é").replace("E", "É")
                if kata_lower in kata_e_petik2:
                    kata = kata.replace("e", "è").replace("E", "È")
                if kata_lower in kata_e_petik_sub:
                    kata = kata.replace("e", "è").replace("E", "È")
                if kata_lower in kata_e_petik_sub2:
                    kata = kata.replace("e", "è").replace("E", "È")
                hasil_baris.append(simbol_depan + kata + simbol_belakang)

            i += 1
        hasil_lines.append(" ".join(hasil_baris))

    return "<br>".join(hasil_lines), kata_terdapat, kata_tidak_terdapat, pasangan_kata, pasangan_ekuivalen


def ubah_ke_lema(chat_user_indo, df_kamus, df_idiom):
    (
        kata_terdapat,
        kata_tidak_terdapat,
        kata_terdapat_tidak_loma,
        pasangan_kata,
        kata_e_petik,
        kata_e_petik2,
        kata_e_petik_sub,
        kata_e_petik_sub2,
        filtered_words_idiom,
    ) = constraint_text(chat_user_indo, df_kamus, df_idiom)
    
    # Tokenisasi kalimat
    kata_kata = chat_user_indo.lower().split()

    # Buat mapping dari ARTI EKUIVALEN 1 ke LEMA
    map_arti_ke_lema = {}
    
    for idx, row in df_kamus.iterrows():
        # Ambil arti ekuivalen atau gunakan arti 1 jika kosong
        arti_ekuivalen = row["ARTI EKUIVALEN 1"]
        if pd.isna(arti_ekuivalen):
            arti_ekuivalen = row["ARTI 1"]
            
        lema = row["LEMA"]
        
        if pd.notna(arti_ekuivalen):
            for kata in str(arti_ekuivalen).split(","):
                map_arti_ke_lema[kata.strip().lower()] = lema

    # Proses kombinasi kata
    tokens = re.findall(r"\w+|[^\w\s]", chat_user_indo.lower())
    

    hasil = []
    pasangan_ganti = {}  # Dictionary untuk menyimpan pasangan kata yang diganti
    i = 0
    while i < len(tokens):
        token = tokens[i]
    
        # Hanya proses jika token termasuk dalam kata_tidak_terdapat
        if token in kata_tidak_terdapat:
            if re.match(r"[^\w\s]", token):
                hasil.append(token)
                i += 1
                continue
    
            trigram = " ".join(tokens[i : i + 3])
            bigram = " ".join(tokens[i : i + 2])
            unigram = token
    
            if i + 2 < len(tokens) and trigram in map_arti_ke_lema:
                hasil.append(map_arti_ke_lema[trigram])
                pasangan_ganti[trigram] = map_arti_ke_lema[trigram]
                i += 3
            elif i + 1 < len(tokens) and bigram in map_arti_ke_lema:
                hasil.append(map_arti_ke_lema[bigram])
                pasangan_ganti[bigram] = map_arti_ke_lema[bigram]
                i += 2
            elif unigram in map_arti_ke_lema:
                hasil.append(map_arti_ke_lema[unigram])
                pasangan_ganti[unigram] = map_arti_ke_lema[unigram]
                i += 1
            else:
                hasil.append(unigram)
                i += 1
        else:
            hasil.append(token)
            i += 1  # ⬅️ WAJIB untuk menghindari infinite loop
    
        hasil_akhir = (
            " ".join(hasil)
            .replace(" ,", ",")
            .replace(" .", ".")
            .replace(" ?", "?")
            .replace(" !", "!")
        )

    return hasil_akhir, pasangan_ganti

def find_the_lema_pair(data_kamus, kata_list, kata_tidak_terdapat):
    data_kamus[['ARTI EKUIVALEN 1', 'ARTI 1']] = data_kamus[['ARTI EKUIVALEN 1', 'ARTI 1']].apply(lambda col: col.str.lower())
    # Normalisasi kolom SUBLEMA jadi list, ganti "é" menjadi "e"
    def sublema_contains_kata(sublema_str, kata):
        if pd.isna(sublema_str):
            return False
        # Ganti semua "é" dengan "e" pada sublema_str
        sublema_str = sublema_str.replace('é', 'e')
        return kata in [item.strip() for item in sublema_str.split(',')]

    # Membuat dictionary hasil
    hasil_dict = {}

    # Ganti semua "é" dengan "e" pada kata_list
    kata_list = [kata.replace('é', 'e') for kata in kata_list]
    
    import re
    
    def bersihkan_kata(kata_list):
        bersih_list = []
        for kata in kata_list:
            # Hanya mempertahankan huruf (termasuk huruf dengan aksen seperti é)
            bersih = re.sub(r"[^\w\s]|_", "", kata, flags=re.UNICODE)
            # Optional: jika ingin menghapus angka juga, gunakan ini:
            # bersih = re.sub(r"[^\p{L}\s]", "", kata)
            bersih_list.append(bersih)
        return bersih_list
    
    # Contoh penggunaan
    hasil = bersihkan_kata(kata_list)
    print(hasil)

    # Cari di kolom LEMA
    for kata in kata_list:
        if kata in kata_tidak_terdapat:  # Hanya proses jika ada di list1
            arti_lema = data_kamus[data_kamus['LEMA'].str.replace('é', 'e') == kata]['ARTI 1'].tolist()
            if arti_lema:
                hasil_dict[kata] = arti_lema[0]
            else:    
                arti_lema_ekuivalen = data_kamus[data_kamus['LEMA'].str.replace('é', 'e') == kata]['ARTI EKUIVALEN 1'].tolist()
                if arti_lema_ekuivalen:           
                    hasil_dict[kata] = arti_lema_ekuivalen
    
    # Cari di kolom SUBLEMA
    for kata in kata_list:
        if kata in kata_tidak_terdapat and kata not in hasil_dict:  # Tambahkan cek list1
            match_rows = data_kamus[data_kamus['SUBLEMA'].apply(lambda x: sublema_contains_kata(x, kata))]
            for _, row in match_rows.iterrows():
                if row['ARTI 1'] is None or pd.isna(row['ARTI 1']):
                    hasil_dict[kata] = row['ARTI EKUIVALEN 1']
                else:
                    hasil_dict[kata] = row['ARTI 1']
                break  # Ambil arti pertama yang ditemukan


    # Tampilkan hasil dalam bentuk dict
    print(hasil_dict)
    return hasil_dict

def cari_arti_lema(teks, df):
    """
    Mencari arti berdasarkan LEMA dan SUBLEMA dari teks, dengan normalisasi huruf é menjadi e.

    Parameters:
    - teks (str): Teks yang ingin dianalisis.
    - df (pd.DataFrame): DataFrame dengan kolom 'LEMA', 'SUBLEMA', dan 'ARTI 1'.

    Returns:
    - dict: Pasangan {kata_dari_teks: arti} yang ditemukan dari teks.
    """
    # Ganti é dengan e di teks
    teks = teks.lower().replace('é', 'e')
    kata_dalam_teks = teks.split()

    # Ganti é dengan e di kolom LEMA dan SUBLEMA
    df = df.copy()
    df['LEMA'] = df['LEMA'].str.lower().str.replace('é', 'e')
    df['SUBLEMA'] = df['SUBLEMA'].fillna('').str.lower().str.replace('é', 'e')

    hasil = {}

    for kata in kata_dalam_teks:
        # Cek ke kolom LEMA
        cocok_lema = df[df['LEMA'] == kata]
        if not cocok_lema.empty:
            arti = cocok_lema.iloc[0]['ARTI 1']
            hasil[kata] = arti
            continue

        # Cek ke kolom SUBLEMA
        for _, baris in df.iterrows():
            sublema_list = [s.strip() for s in baris['SUBLEMA'].split(',')]
            if kata in sublema_list:
                hasil[kata] = baris['ARTI 1']
                break

    return hasil
