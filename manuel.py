import streamlit as st
import random
import os
from datetime import datetime
from io import BytesIO
from docxtpl import DocxTemplate

# Cihaz Listesi Yönetimi
def cihazlari_yukle():
    if os.path.exists("cihazlar.txt"):
        with open("cihazlar.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["DFA - 0469 KUMPAS", "DFA - 0001 MİKROMETRE", "DFA - 0002 RADYUS MASTAR"]

mevcut_cihazlar = cihazlari_yukle()

# --- ARABİRİM TASARIMI ---
st.set_page_config(page_title="Teknolus Manuel Ölçü Paneli", layout="wide")
st.title("🔧 Teknolus Manuel Ölçü Paneli")

# Sol Panel: Üst Veriler
with st.sidebar:
    st.header("📋 Malzeme & Kontrol Bilgileri")
    malzeme_no = st.text_input("Malzeme No:", value="0004017.0000")
    malzeme_aciklamasi = st.text_input("Malzeme Açıklaması:", value="BLM1800-Bearing Washer")
    gelen_miktar = st.number_input("Gelen Miktar:", value=125, step=1)
    kontrol_miktari = st.number_input("Kontrol Miktarı:", value=15, step=1)
    uygun_miktar = st.number_input("Uygun Miktar:", value=15, step=1)
    kontrol_eden = st.text_input("Kontrol Eden:", value="Ötuken Avcı")
    onaylayan = st.text_input("Onaylayan:", value="Ötuken Avcı")

# Ana Panel: Ölçüm Noktaları
st.header("📏 Ölçüm Noktası Girişleri")

# Form verilerini toplamak için sözlük yapısı
panel_verileri = {}

# 1'den 9'a kadar olan panelleri oluşturuyoruz
for i in range(1, 10):
    with st.expander(f"🔹 Ölçüm Noktası {i}", expanded=(i in [2, 3])):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            balon_no = st.text_input(f"Balon No", key=f"balon_{i}", value=str(i) if i in [2,3] else "").strip()
        with col2:
            nominal = st.text_input(f"Nominal", key=f"nominal_{i}", value="10" if i==2 else ("0.5" if i==3 else ""))
        with col3:
            tol_plus = st.text_input(f"Tol(+)", key=f"tol_p_{i}", value="0.03" if i==2 else ("0.1" if i==3 else ""))
        with col4:
            tol_minus = st.text_input(f"Tol(-)", key=f"tol_m_{i}", value="0.03" if i==2 else ("0.1" if i==3 else ""))
        with col5:
            is_master = any(x in str(nominal).upper() for x in ["GÖ", "GEÇER", "MASTAR", "HELICOIL", "GO"])
            if is_master:
                cihaz_secimi = st.selectbox(f"Cihaz Seç", ["VİDA DİŞ MASTARI", "GEÇER/GEÇMEZ MASTAR"], key=f"cihaz_{i}")
            else:
                cihaz_secimi = st.selectbox(f"Cihaz Seç", mevcut_cihazlar, key=f"cihaz_{i}")
        
        # Sadece Balon No girildiyse veriyi kaydet
        if balon_no:
            panel_verileri[i] = {
                "balon": balon_no,
                "nominal": nominal,
                "tol_plus": tol_plus,
                "tol_minus": tol_minus,
                "cihaz": cihaz_secimi,
                "is_master": is_master
            }

# --- DEĞER ÜRETME VE FORMU OLUŞTURMA ---
if st.button("🚀 FORMU OLUŞTUR", type="primary"):
    try:
        # Word şablonundaki üst bilgilerle birebir eşleme
        context = {
            "envanter_no": "",
            "tarih": datetime.now().strftime("%d.%m.%Y"),
            "malzeme_no": malzeme_no,
            "malzeme_adi": malzeme_aciklamasi,  # Şablonundaki {{malzeme_adi}}
            "genel_miktar": gelen_miktar,       # Şablonundaki {{genel_miktar}}
            "kontrol_miktari": kontrol_miktari,
            "uygun_miktar": uygun_miktar,
            "kontrol_eden": kontrol_eden,
            "onaylayan": onaylayan
        }
        
        # Şablondaki tüm olası hücreleri (9 sütun x 10 satır) başlangıçta boşaltıyoruz
        for i in range(1, 10):
            context[f"balonno{i}"] = ""
            context[f"nom{i}"] = ""
            context[f"tolarti{i}"] = ""
            context[f"toleksi{i}"] = ""
            context[f"cihaz{i}"] = ""
            for j in range(1, 11):
                context[f"o_{i}_{j}"] = ""
                context[f"s_{i}_{j}"] = ""
        
        # Numune sıra numaralarını (1-10) yazdırıyoruz
        for j in range(1, 11):
            context[f"serino{j}"] = str(j) if j <= int(kontrol_miktari) else ""

        # Sadece kullanıcının doldurduğu ölçüm noktalarını matrise yerleştiriyoruz
        for i, girdi in panel_verileri.items():
            context[f"balonno{i}"] = girdi["balon"]
            context[f"nom{i}"] = girdi["nominal"]
            context[f"tolarti{i}"] = girdi["tol_plus"]
            context[f"toleksi{i}"] = girdi["tol_minus"]
            context[f"cihaz{i}"] = girdi["cihaz"]
            
            # Kontrol miktarı kadar (en fazla 10 satır) rastgele değer üretimi
            sinir_miktari = min(int(kontrol_miktari), 10)
            for j in range(1, sinir_miktari + 1):
                if girdi["is_master"]:
                    context[f"o_{i}_{j}"] = "UYGUN"
                    context[f"s_{i}_{j}"] = "UYGUN"
                else:
                    try:
                        nom_f = float(girdi["nominal"])
                        tp_f = float(girdi["tol_plus"]) if girdi["tol_plus"] else 0.0
                        tm_f = float(girdi["tol_minus"]) if girdi["tol_minus"] else 0.0
                        
                        # Hassasiyet basamağını hesapla
                        dec_places = max(
                            len(str(girdi["nominal"]).split('.')[1]) if '.' in str(girdi["nominal"]) else 0,
                            len(str(girdi["tol_plus"]).split('.')[1]) if '.' in str(girdi["tol_plus"]) else 0,
                            len(str(girdi["tol_minus"]).split('.')[1]) if '.' in str(girdi["tol_minus"]) else 0
                        )
                        dec_places = max(dec_places, 2)
                        
                        rastgele_deger = random.uniform(nom_f - tm_f, nom_f + tp_f)
                        context[f"o_{i}_{j}"] = f"{rastgele_deger:.{dec_places}f}"
                        context[f"s_{i}_{j}"] = "UYGUN"
                    except ValueError:
                        context[f"o_{i}_{j}"] = girdi["nominal"]
                        context[f"s_{i}_{j}"] = "UYGUN"

        # Şablon adını kontrol edip yüklüyoruz
        dosya_adi = "manuel.docx"
        if os.path.exists(dosya_adi):
            doc = DocxTemplate(dosya_adi)
            doc.render(context)
            
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            
            st.success("🎉 Rapor başarıyla dolduruldu!")
            st.download_button(
                label="📄 Raporu İndir (.docx)",
                data=output,
                file_name=f"Kalite_Kontrol_Raporu_{malzeme_no}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error(f"Hata: GitHub deponuzda '{dosya_adi}' dosyası bulunamadı.")
            
    except Exception as e:
        st.error(f"Sistem Hatası: {e}")
