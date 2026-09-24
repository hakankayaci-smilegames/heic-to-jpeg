# Proje Mimarisi: HEIC & Medya Araçları Pro

Bu doküman, projenin mimari yapısını, iki temel modülünü (Format Dönüştürücü ve Boyut Optimize Edici), veri modellerini ve CI/CD akışını belgeler.

---

## 1. Dizin ve Dosya Yapısı

```text
heic-to-jpeg/
├── core/
│   ├── __init__.py
│   ├── converter.py       # HEIC format dönüştürme motoru (ICC P3, EXIF, 4:4:4 subsampling)
│   └── optimizer.py       # Boyut küçültme ve sıkıştırma motoru (Progressive JPEG, PNG comp-9, WEBP)
├── ui/
│   ├── __init__.py
│   └── app.py             # CustomTkinter 2 Sekmeli (Tabview) modern arayüz (TR/EN desteği)
├── .github/
│   └── workflows/
│       └── release.yml    # Windows, Linux ve macOS için bağımsız tek tık binary derleyen CI
├── main.py                # Giriş noktası (CLI ve GUI ayrımı)
├── requirements.txt       # Bağımlılıklar (pillow, pillow-heif, customtkinter)
├── .gitignore             # Git yoksayma kuralları
├── README.md              # Çok dilli kullanıcı rehberi
└── PROJECT_ARCHITECTURE.md # Mimari dokümantasyon
```

---

## 2. Modüller ve İşleyiş

### A. Format Dönüştürücü (`core/converter.py` & Sekme 1)
- **Hedef:** HEIC/HEIF görsellerini görsel olarak sıfır kayıpla (`visually lossless`) JPG, JPEG veya kayıpsız PNG formatına çevirmek.
- **Kritik Parametreler:**
  - `subsampling=0`: 4:4:4 kroma alt örnekleme ile renk kenar keskinliği korunur.
  - `icc_profile`: Apple Display P3 renk gamutunun korunmasını sağlar (soluk renkleri engeller).
  - `exif`: Çekim açısı (orientation) ve kamera metadata'sını eksiksiz aktarır.

### B. Boyut Optimize Edici (`core/optimizer.py` & Sekme 2)
- **Hedef:** HEIC, JPG, JPEG, PNG ve WEBP formatlarındaki görsellerin dosya boyutunu küçültmek.
- **Dinamik Tradeoff Kadroları:**
  - **%85 - %95:** Hafif Sıkıştırma (Görsel fark yok, %100 keskinlik, ~%20-%35 boyut tasarrufu).
  - **%70 - %84:** Dengeli Sıkıştırma (Web ve paylaşım için ideal, fark gözle algılanmaz, ~%40-%60 boyut tasarrufu).
  - **%50 - %69:** Agresif Sıkıştırma (Maksimum küçültme, ~%70-%80 boyut tasarrufu).
- **Sonuç Hesaplama:** Toplam orijinal bayt ve yeni bayt hesaplanarak anlık tasarruf yüzdesi ve açma butonu gösterilir.

### C. Çoklu Platform Derleme (`.github/workflows/release.yml`)
- GitHub Actions üzerinde `windows-latest`, `ubuntu-latest` ve `macos-latest` ortamlarında `pyinstaller` çalıştırılarak Python gerektirmeyen bağımsız binary'ler üretilir.
