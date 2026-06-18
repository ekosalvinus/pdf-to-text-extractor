# PDF to Text Extractor
This application is used to extract PDF files into text.
The extracted files can be saved as ```*.txt``` files.

Before using it, use the instructions to set up a Python ```venv``` and install the required dependencies. 

## Set Up Environtment (venv)
```bash
## Set up Virtual Environment
sudo apt update
sudo apt install python3-venv python3-full

## Create folder for you work with
mkdir myproject
cd myproject

## Create venv for python
python3 -m venv venv
source venv/bin/activate

## install required dependency
## in this case we use pdfplumber pymupdf
## Read how to isntall pdfplumber pymupdf below
pip install nama_paket

```

### Install Dependency

```bash
pip install pdfplumber pymupdf

```


## How to Use this Application
**I use python3 in this case**

```bash
# Baca PDF biasa (auto-save ke .txt)
python3 pdf_reader.py dokumen.pdf

# Tampilkan isi per halaman
python3 pdf_reader.py dokumen.pdf -v

# Simpan ke file tertentu
python3 pdf_reader.py dokumen.pdf -o hasil.txt

# Cek info PDF tanpa baca isi
python3 pdf_reader.py dokumen.pdf --info

# Ekstrak halaman tertentu saja
python3 pdf_reader.py dokumen.pdf --pages 1-5
python3 pdf_reader.py dokumen.pdf --pages 1,3,7

# Baca PDF yang pakai password
python3 pdf_reader.py dokumen.pdf --password rahasia123

# Gunakan metode tertentu
python3 pdf_reader.py dokumen.pdf --method pymupdf

```

### How to use sample
Get into your PDF file folder path and excute this application

```bash
# Convert PDF ke file *.txt
python3 pdf_reader.py cys3.pdf -o hasil.txt

# Cek info PDF tanpa baca isi
python3 pdf_reader.py cys3.pdf --info

```

## Fitur yang ada:

- Auto-detect apakah PDF punya teks layer atau hasil scan
- Dual engine => pakai ```pdfplumber``` utama, fallback ke ```PyMuPDF``` otomatis kalau gagal
- Ekstrak tabel juga ikut diambil
- Bersihkan teks => hapus karakter aneh, normalize spasi & baris
- Export langsung ke ```*.txt``` dengan nama sama
- Preview 500 karakter pertama tanpa ``` -v ```
- Support PDF terenkripsi via ``` --password ```


⚠️ Kalau PDF hasil scan (foto/gambar), tidak ada teks layer yang bisa dibaca maka butuh OCR (Tesseract). Aplikasi ini akan kasih peringatan otomatis kalau ketemu kasus tersebut.


## Sample log
```bash
## script
python3 pdf_reader.py sample-doc.pdf -o hasil.txt
```

```bash
🔍 Membaca: sample-doc.pdf (527.8 KB)
⚙️  Menggunakan metode: pdfplumber

============================================================
  📄 HASIL EKSTRAKSI PDF
============================================================
  Status      : ✅ Berhasil
  Metode      : pdfplumber
  Total Hal.  : 12
  Total Tabel : 4
  Total Karakt: 44,746
------------------------------------------------------------

📝 Preview teks (500 karakter pertama):

--- Halaman 1 ---
DS Journal of Cyber Security
Volume 3 Issue 3, 39-50, Jul - Sep 2025
ISSN: 2584-0665 / https://doi.org/10.59232/CYS-V3I3P103
Original Article
Effect of Cyber Security on Organization
Network: A Case Study of Selected
Commercial Banks in Nigeria
Abba, Monday Okoroma1, Osodeke, Efe Charles2,
Ibekwe, Christopher Chimaobi3*
1Department of Information Systems and Technology, Faculty of Computing, Umuahia Study Centre, National Open University of Nigeria.
2Department of Computer Scie

  ... (+48,110 karakter lagi)

============================================================

💾 Teks disimpan ke: hasil.txt
```