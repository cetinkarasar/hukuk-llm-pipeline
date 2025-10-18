import os
import fitz  # PyMuPDF
import json
import re
from tqdm import tqdm

# -------- AYARLAR --------
PDF_KLASORU = "data/pdfs"
CIKTI_DOSYASI = "data/islenmis_veri_nihai.jsonl"
# -------------------------

def extract_pdf_text(pdf_path):
    """Verilen PDF dosyasının metnini çıkarır."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Hata: {pdf_path} dosyası okunurken sorun oluştu: {e}")
        return None

def main():
    if not os.path.exists(PDF_KLASORU):
        print(f"'{PDF_KLASORU}' klasörü bulunamadı.")
        return

    pdf_files = [f for f in os.listdir(PDF_KLASORU) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"'{PDF_KLASORU}' klasöründe hiç PDF dosyası bulunamadı.")
        return

    print(f"Toplam {len(pdf_files)} PDF dosyası bulundu. Nihai tarama ile işleniyor...")

    tum_chunklar = []
    
    for dosya_adi in tqdm(pdf_files, desc="PDF'ler işleniyor"):
        dosya_yolu = os.path.join(PDF_KLASORU, dosya_adi)
        tam_metin = extract_pdf_text(dosya_yolu)
        if not tam_metin:
            continue

        # Anahtar Değişiklik: Metni "Madde X-" kalıplarından bölerek ana blokları oluşturuyoruz.
        madde_etiketleri = re.findall(r'Madde \d+-\s*', tam_metin)
        madde_icerikleri = re.split(r'Madde \d+-\s*', tam_metin)

        # İlk blok genellikle giriş metnidir, onu atlıyoruz.
        for i, blok_icerigi in enumerate(madde_icerikleri[1:]):
            
            # İlgili madde numarasını ve etiketini al
            madde_etiketi = madde_etiketleri[i]
            madde_no = re.search(r'(\d+)', madde_etiketi).group(1)
            
            # Başlık, bir önceki bloğun son anlamlı satırıdır.
            onceki_blok = madde_icerikleri[i]
            baslik_satirlari = [satir.strip() for satir in onceki_blok.strip().split('\n') if satir.strip()]
            madde_basligi = baslik_satirlari[-1] if baslik_satirlari else None

            # *** İŞTE DÜZELTME VE BASİTLEŞTİRME BURADA ***
            # Bloğu satırlara ayır ve son satırın bir sonraki başlık olup olmadığını kontrol et
            mevcut_blok_satirlari = blok_icerigi.strip().split('\n')
            
            # Eğer bu son madde değilse, son satır muhtemelen bir sonraki maddenin başlığıdır.
            if (i + 1) < len(madde_etiketleri):
                # Son satırı (başlığı) metinden çıkar
                temiz_metin = "\n".join(mevcut_blok_satirlari[:-1]).strip()
            else:
                # Bu son madde ise, metni olduğu gibi al
                temiz_metin = "\n".join(mevcut_blok_satirlari).strip()

            # Temizlenmiş metni fıkralara ayır
            fikra_bolme_kalibi = r'(\(\d+\))'
            fikralar = re.split(fikra_bolme_kalibi, temiz_metin)
            
            # Fıkraları işle...
            # ... (Bu kısım öncekiyle aynı)
            j = 1
            while j < len(fikralar):
                fikra_no_etiketi = fikralar[j]
                fikra_icerigi = fikralar[j+1].strip() if (j+1) < len(fikralar) else ""
                fikra_no = re.search(r'(\d+)', fikra_no_etiketi).group(1)

                if fikra_icerigi:
                    tum_chunklar.append({
                        "kaynak": dosya_adi, "madde_no": madde_no, "madde_basligi": madde_basligi,
                        "fikra_no": fikra_no, "text": f"({fikra_no}) {fikra_icerigi}"
                    })
                j += 2

    print(f"\nToplam {len(tum_chunklar)} adet anlamlı chunk (fıkra) bulundu.")
    
    os.makedirs(os.path.dirname(CIKTI_DOSYASI), exist_ok=True)
    with open(CIKTI_DOSYASI, 'w', encoding='utf-8') as f:
        for chunk_data in tqdm(tum_chunklar, desc="Dosyaya yazılıyor"):
            f.write(json.dumps(chunk_data, ensure_ascii=False) + '\n')
    
    print(f"Veri hazırlama işlemi başarıyla tamamlandı! Çıktı: '{CIKTI_DOSYASI}'")

if __name__ == "__main__":
    main()