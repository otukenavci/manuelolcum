import streamlit as st
import random
import os
from io import BytesIO
from docxtpl import DocxTemplate

# 1. CİHAZ LİSTESİ YÖNETİMİ
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

# Sadece içi doldurulan satırların toplanacağı dinamik liste
kabul_edilen_olcumler = []

# 1'den 9'a kadar olan panelleri ekrana basıyoruz
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
        
        # 🎯 KRİTİK KURAL: Sadece balon numarası yazılmışsa listeye kabul et!
        if balon_no:
            kabul_edilen_olcumler.append({
                "balon": balon_no,
                "nominal": nominal,
                "tol_plus": tol_plus,
                "tol_minus": tol_minus,
                "cihaz": cihaz_secimi,
                "is_master": is_master
            })

# --- DEĞER ÜRETME VE FORMU OLUŞTURMA ---
if st.button("🚀 FORMU OLUŞTUR", type="primary"):
    try:
        # Üst bilgileri içeren ana sözlük
        context = {
            "malzeme_no": malzeme_no,
            "malzeme_aciklamasi": malzeme_aciklamasi,
            "gelen_miktar": gelen_miktar,
            "kontrol_miktari": kontrol_miktari,
            "uygun_miktar": uygun_miktar,
            "kontrol_eden": kontrol_eden,
            "onaylayan": onaylayan,
            "olcumler": [] # Word şablonundaki {% for o in olcumler %} döngüsü için temiz liste
        }
        
        # ❌ INDEX ERROR'U ENGELLEYEN YAPI:
        # Sabit indeks (0,1,2..) yerine sadece "kabul_edilen_olcumler" listesinde ne varsa onun üzerinde dönüyoruz
        for sira_no, girdi in enumerate(kabul_edilen_olcumler, start=1):
            satir_verisi = {
                "sira": sira_no,
                "balon": girdi["balon"],
                "nominal": girdi["nominal"],
                "tol_p": girdi["tol_plus"],
                "tol_m": girdi["tol_minus"],
                "cihaz": girdi["cihaz"]
            }
            
            # Seçilen kontrol miktarı kadar rastgele değer üretip satıra ekle
            for j in range(1, int(kontrol_miktari) + 1):
                if girdi["is_master"]:
                    satir_verisi[f"olcum_{j}"] = "UYGUN"
                else:
                    try:
                        nom_f = float(girdi["nominal"])
                        tp_f = float(girdi["tol_plus"]) if girdi["tol_plus"] else 0.0
                        tm_f = float(girdi["tol_minus"]) if girdi["tol_minus"] else 0.0
                        
                        # Basamak hassasiyeti ayarı
                        dec_places = max(
                            len(str(girdi["nominal"]).split('.')[1]) if '.' in str(girdi["nominal"]) else 0,
                            len(str(girdi["tol_plus"]).split('.')[1]) if '.' in str(girdi["tol_plus"]) else 0,
                            len(str(girdi["tol_minus"]).split('.')[1]) if '.' in str(girdi["tol_minus"]) else 0
                        )
                        dec_places = max(dec_places, 2)
                        
                        rastgele_deger = random.uniform(nom_f - tm_f, nom_f + tp_f)
                        satir_verisi[f"olcum_{j}"] = f"{rastgele_deger:.{dec_places}f}"
                    except ValueError:
                        satir_verisi[f"olcum_{j}"] = girdi["nominal"]
            
            # Sadece bu geçerli satırı listeye ekle
            context["olcumler"].append(satir_verisi)

        # Şablonu İşleme
        if os.path.exists("sablon.docx"):
            doc = DocxTemplate("sablon.docx")
            doc.render(context)
            
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            
            st.success(f"🎉 Rapor başarıyla hazırlandı! Toplam {len(kabul_edilen_olcumler)} ölçüm noktası işlendi.")
            st.download_button(
                label="📄 Raporu İndir (.docx)",
                data=output,
                file_name=f"Kalite_Kontrol_Raporu_{malzeme_no}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error("Hata: 'sablon.docx' dosyası bulunamadı. Lütfen GitHub deponuza şablonu ekleyin.")
            
    except Exception as e:
        st.error(f"Hata detayı: {e}")
