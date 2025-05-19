import streamlit as st
import re
import string
from transformers import AutoProcessor, Gemma3ForConditionalGeneration, BitsAndBytesConfig
from google.cloud import storage
import torch
import os

# Cek device
device = "cuda" if torch.cuda.is_available() else "cpu"

# =================== Load Model dari GCS ===================
def download_model_once(bucket="chatbot-models-sunda", model_path="models", local_path="/models"):
    if not os.path.exists(os.path.join(local_path, "model_downloaded.flag")):
        os.makedirs(local_path, exist_ok=True)
        client = storage.Client()
        bucket = client.bucket(bucket)
        blobs = bucket.list_blobs(prefix=model_path)

        for blob in blobs:
            filename = blob.name.replace(model_path + "/", "")
            if filename:
                destination = os.path.join(local_path, filename)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                blob.download_to_filename(destination)

        # Buat flag untuk menandai sudah diunduh
        open(os.path.join(local_path, "model_downloaded.flag"), "w").close()

def load_model_from_disk(local_path="/models"):
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",  # nf4 biasanya lebih akurat daripada fp4
    )

    model = Gemma3ForConditionalGeneration.from_pretrained(
        local_path,
        device_map="auto",
        quantization_config=quant_config
    ).eval()

    processor = AutoProcessor.from_pretrained(local_path)
    return model, processor

# Download jika perlu, lalu load dari disk
download_model_once()
model, processor = load_model_from_disk()


def generate_locally_with_model(history, prompt, max_new_tokens=200):
    messages = [
        {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]}
    ]
    if history:
        for user_msg, bot_msg, _ in history:
            messages.append({"role": "user", "content": [{"type": "text", "text": user_msg}]})
            messages.append({"role": "assistant", "content": [{"type": "text", "text": bot_msg}]})

    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True,
        return_dict=True, return_tensors="pt"
    ).to(device)

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        generation = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False
        )
        generation = generation[0][input_len:]

    decoded = processor.decode(generation, skip_special_tokens=True)
    return decoded

def generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa="Sunda", history=None):
    # Instruksi berdasarkan fitur dan mode bahasa
    if fitur == "chatbot":
        if mode_bahasa == "Sunda":
            instruksi_bahasa = "Jawablah hanya dalam Bahasa Sunda LOMA. Jawab pertanyaannya mau itu Bahasa Sunda, Bahasa Indonesia atau English tapi tetap jawab pakai Bahasa Sunda Loma. Gunakan tata bahasa sunda yang baik dan benar."
        elif mode_bahasa == "Indonesia":
            instruksi_bahasa = "Jawablah hanya dalam Bahasa Indonesia. Jawab pertanyaannya mau itu Bahasa Indonesia, Bahasa Sunda atau English tapi tetap jawab pakai Bahasa Indonesia."
        elif mode_bahasa == "English":
            instruksi_bahasa = "Please respond only in English. Answer the questions whether it is in Indonesian, Sundanese or English but always answer in English"
        else:
            instruksi_bahasa = ""
        
        final_prompt = f"""
        {instruksi_bahasa}
        Kamu adalah Lestari, chatbot yang interaktif dan talkactive membantu pengguna menjawab pertanyaan secara ramah dan jelas informasinya.
        Jawab pertanyaan secara sederhana saja jangan terlalu panjang dan jangan cerewet. Ingat kamu dibangun menggunakan Llama4-scout.
        Jangan gunakan huruf-huruf aneh seperti kanji korea, kanji jepang, atau kanji china.
        Pertanyaan dari pengguna: "{user_input}"
        """

    elif fitur == "terjemahindosunda":
        final_prompt = f"""Kamu adalah penerjemah yang ahli bahasa sunda dan bahasa indonesia.
        Terjemahkan kalimat berikut ke dalam Bahasa Sunda LOMA secara alami seperti digunakan dalam kehidupan sehari-hari.     
        Jangan mengajak mengobrol seperti fitur chatbot. anda hanya menterjemahkan input dari user seperti google translater.
        Jangan menambahkan kata bahasa sunda yang memang bukan arti dari kalimat bahasa indonesia tersebut.
        Sesuaikan gaya bahasanya agar cocok dengan konteks relasi antarpenutur dalam hal ini teman sebaya anak-anak umur 7 - 10 tahun.
        Perintah anda hanya terjemahkan dari input user, bukan menjawab hal lain. Jangan menggunakan kata awalan atau sapaan sebagai tambahan jawaban.
        Jangan beri penjelasan atau keterangan tambahan, langsung berikan hasil terjemahannya saja. 
        Jangan jadikan semua huruf pada awal kata huruf kapital kecuali nama tempat dan nama orang.
        Huruf pada awal kalimat dan setelah titik harus huruf kapital.
        Nama orang dan nama tempat juga harus berawalan huruf kapital.
        Kalimat: {user_input}"""
        
    elif fitur == "terjemahsundaindo":
        final_prompt = f"""Kamu adalah penerjemah yang ahli bahasa indonesia dan bahasa sunda.
        Terjemahkan kalimat berikut ke dalam Bahasa Indonesia yang baku dan mudah dimengerti.
        Jangan mengajak mengobrol seperti fitur chatbot, anda hanya menterjemahkan input dari user seperti google translate.
        Jangan tambahkan penjelasan atau keterangan apa pun. Langsung tampilkan hasil terjemahannya.
        Jangan jadikan semua huruf pada awal kata huruf kapital, kecuali nama orang dan nama tempat.
        Huruf pada awal kalimat dan setelah titik harus huruf kapital.
        Nama orang dan nama tempat juga harus berawalan huruf kapital.
        Kalimat: {user_input}"""

    else:
        # fallback
        final_prompt = f"Jawablah dengan sopan dan informatif: {user_input}"

    # === Panggil LLM Groq API di sini ===
    response = generate_locally_with_model(history=history, prompt=final_prompt)  # Fungsi ini kamu sesuaikan dengan API Groq kamu
    return response
    
def kapitalisasi_awal_kalimat(teks):
    # Pecah teks berdasarkan titik
    kalimat_list = re.split(r'([.!?])', teks)
    hasil = ""
    for i in range(0, len(kalimat_list), 2):
        kalimat = kalimat_list[i].strip()
        if kalimat:
            kapital = kalimat[0].upper() + kalimat[1:] if len(kalimat) > 1 else kalimat.upper()
            hasil += kapital
        if i+1 < len(kalimat_list):
            hasil += kalimat_list[i+1] + " "
    return hasil.strip()
