# HEIC & Media Tools Pro 📸🗜️

> **Ultra High Quality HEIC Converter & Smart Image Compressor**  
> *Apple Display P3 ICC Profili, EXIF koruma ve 4:4:4 Chroma Subsampling destekli kayıpsız dönüştürücü + Akıllı görsel boyut optimize edici.*

---

## 🌟 2 Güçlü Araç Bir Arada / Two Powerful Tools in One

### 1. 🔄 Format Dönüştürücü (Converter)
- **Sıfır Renk Kaybı:** iPhone fotoğraflarının geniş gamutlu **Apple Display P3** renk profilini korur; renklerin solmasını önler.
- **4:4:4 Chroma Subsampling:** Kırmızı ve mavi renk kenarlarındaki sıkıştırma bulanıklığını tamamen sıfırlar.
- **Dinamik Çıktı:** **JPG**, **JPEG** (kalite ayarlı) veya tamamen kayıpsız (lossless) **PNG** desteği.
- **EXIF Metadata:** Çekim açısı (orientation) ve kamera bilgileri eksiksiz aktarılır.

### 2. 🗜️ Boyut Optimize Edici (Image Compressor)
- **Geniş Format Desteği:** HEIC, JPG, JPEG, PNG, WEBP dosyalarını optimize eder.
- **Canlı Tradeoff Göstergesi:**
  - 🟢 **Hafif Sıkıştırma (%85-%95):** Görsel fark yok, %100 keskinlik (~%20-%35 tasarruf).
  - 🟡 **Dengeli Sıkıştırma (%70-%84):** Web ve paylaşım için ideal, fark algılanmaz (~%40-%60 tasarruf).
  - 🔴 **Agresif Sıkıştırma (%50-%69):** Maksimum tasarruf (~%70-%80 tasarruf).
- **Detaylı Tasarruf Raporu:** İşlem bitiminde kazanılan toplam megabayt ve tasarruf yüzdesini gösterir.

---

## 📦 Kurulumsuz Kullanım (Tek Tıkla İndir & Aç)

Python kurmanıza veya terminal kullanmanıza **gerek yoktur**.  
👉 [GitHub Releases](https://github.com/KULLANICI_ADINIZ/heic-to-jpeg/releases) sayfasına gidin:
- **Windows:** `HEIC-Tools-Windows.zip` indirin, içindeki `HEIC-Tools.exe`ye çift tıklayın.
- **Linux:** `HEIC-Tools-Linux` indirin, çift tıklayıp çalıştırın.
- **macOS:** `HEIC-Tools-macOS.zip` indirin ve `.app` uygulamasını açın.

---

## 🛠️ Kaynak Koddan Çalıştırma / Run from Source

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/heic-to-jpeg.git
cd heic-to-jpeg
```

### 2. Sanal Ortam & Paketler

#### Linux (Bash / Zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Linux (Fish Shell):
```bash
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

> **Linux Notu:** Tkinter eksikse: `sudo apt install python3-tk` (Ubuntu) veya `sudo pacman -S tk` (Arch/CachyOS).

#### Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Başlatma
```bash
# Arayüzü (GUI) açmak için:
python main.py

# Komut satırından (CLI) doğrudan dönüştürmek için:
python main.py foto.heic -f png -o ./cikti/
```

---

## 📄 Lisans / License
MIT License. Açık kaynaklı ve ücretsizdir.
