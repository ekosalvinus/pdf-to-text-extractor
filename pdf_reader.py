#!/usr/bin/env python3
"""
PDF Reader - Ekstrak teks bersih dari file PDF
Mendukung PDF teks biasa dan PDF terenkripsi
"""

import sys
import os
import re
import argparse
from pathlib import Path


def check_dependencies():
    """Periksa library yang dibutuhkan."""
    missing = []
    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")
    try:
        import fitz  # PyMuPDF
    except ImportError:
        missing.append("pymupdf")

    if missing:
        print(f"❌ Library kurang: {', '.join(missing)}")
        print(f"   Jalankan: pip install {' '.join(missing)}")
        sys.exit(1)


def clean_text(text: str) -> str:
    """Bersihkan dan normalisasi teks hasil ekstraksi."""
    if not text:
        return ""

    # Hapus karakter kontrol kecuali newline & tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Normalkan multiple spaces jadi satu
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalkan multiple newlines (maks 2 baris kosong)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Bersihkan spasi di awal/akhir tiap baris
    lines = [line.strip() for line in text.split('\n')]

    # Hapus baris yang hanya berisi satu karakter berulang (header/footer garis)
    lines = [l for l in lines if not re.fullmatch(r'[-=_*]{3,}', l)]

    return '\n'.join(lines).strip()


def extract_with_pdfplumber(pdf_path: str, password: str = None) -> dict:
    """Ekstrak teks menggunakan pdfplumber (akurat untuk layout)."""
    import pdfplumber

    result = {
        "method": "pdfplumber",
        "pages": [],
        "full_text": "",
        "metadata": {},
        "page_count": 0,
        "tables_found": 0,
        "success": False,
        "error": None
    }

    try:
        open_kwargs = {"password": password} if password else {}
        with pdfplumber.open(pdf_path, **open_kwargs) as pdf:
            result["page_count"] = len(pdf.pages)
            result["metadata"] = pdf.metadata or {}

            all_text_parts = []

            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                tables = page.extract_tables()
                result["tables_found"] += len(tables)

                # Gabungkan teks tabel ke halaman
                table_texts = []
                for table in tables:
                    rows = []
                    for row in table:
                        if row:
                            rows.append("  |  ".join(str(c or "").strip() for c in row))
                    if rows:
                        table_texts.append("\n".join(rows))

                clean = clean_text(page_text)
                page_info = {
                    "page": i,
                    "text": clean,
                    "tables": table_texts,
                    "char_count": len(clean)
                }
                result["pages"].append(page_info)

                if clean:
                    all_text_parts.append(f"--- Halaman {i} ---\n{clean}")
                if table_texts:
                    for t in table_texts:
                        all_text_parts.append(f"[Tabel Hal. {i}]\n{t}")

            result["full_text"] = "\n\n".join(all_text_parts)
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def extract_with_pymupdf(pdf_path: str, password: str = None) -> dict:
    """Ekstrak teks menggunakan PyMuPDF (fallback, cepat)."""
    import fitz

    result = {
        "method": "PyMuPDF",
        "pages": [],
        "full_text": "",
        "metadata": {},
        "page_count": 0,
        "tables_found": 0,
        "success": False,
        "error": None
    }

    try:
        doc = fitz.open(pdf_path)

        if doc.needs_pass:
            if not password or not doc.authenticate(password):
                result["error"] = "PDF terenkripsi. Gunakan opsi --password."
                return result

        result["page_count"] = doc.page_count
        result["metadata"] = dict(doc.metadata) if doc.metadata else {}

        all_text_parts = []
        for i, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            clean = clean_text(page_text)
            page_info = {
                "page": i,
                "text": clean,
                "tables": [],
                "char_count": len(clean)
            }
            result["pages"].append(page_info)

            if clean:
                all_text_parts.append(f"--- Halaman {i} ---\n{clean}")

        doc.close()
        result["full_text"] = "\n\n".join(all_text_parts)
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def detect_pdf_type(pdf_path: str) -> str:
    """Deteksi apakah PDF memiliki teks atau hanya gambar (scan)."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        sample_pages = min(3, doc.page_count)
        total_chars = 0
        for i in range(sample_pages):
            total_chars += len(doc[i].get_text("text").strip())
        doc.close()
        if total_chars < 50:
            return "scanned"
        return "text"
    except Exception:
        return "unknown"


def print_report(result: dict, verbose: bool = False):
    """Tampilkan laporan hasil ekstraksi."""
    SEP = "=" * 60
    sep = "-" * 60

    print(f"\n{SEP}")
    print(f"  📄 HASIL EKSTRAKSI PDF")
    print(SEP)

    status = "✅ Berhasil" if result["success"] else "❌ Gagal"
    print(f"  Status      : {status}")
    print(f"  Metode      : {result['method']}")
    print(f"  Total Hal.  : {result['page_count']}")
    print(f"  Total Tabel : {result['tables_found']}")

    if result["metadata"]:
        meta = result["metadata"]
        if meta.get("title"):
            print(f"  Judul       : {meta['title']}")
        if meta.get("author"):
            print(f"  Penulis     : {meta['author']}")
        if meta.get("creator"):
            print(f"  Dibuat dgn  : {meta['creator']}")

    total_chars = sum(p["char_count"] for p in result["pages"])
    print(f"  Total Karakt: {total_chars:,}")
    print(sep)

    if result["error"]:
        print(f"  ⚠️  Error: {result['error']}")
        return

    if verbose:
        for page_info in result["pages"]:
            print(f"\n{'─'*50}")
            print(f"  📃 Halaman {page_info['page']} ({page_info['char_count']} karakter)")
            print('─' * 50)
            if page_info["text"]:
                print(page_info["text"])
            else:
                print("  [Tidak ada teks terdeteksi]")
            for t in page_info["tables"]:
                print(f"\n  📊 Tabel:\n{t}")
    else:
        # Preview 500 karakter pertama
        preview = result["full_text"][:500].strip()
        if preview:
            print(f"\n📝 Preview teks (500 karakter pertama):\n")
            print(preview)
            if len(result["full_text"]) > 500:
                print(f"\n  ... (+{len(result['full_text']) - 500:,} karakter lagi)")
        else:
            print("\n  ⚠️  Tidak ada teks yang dapat diekstrak.")
            print("     Kemungkinan PDF hasil scan. Gunakan OCR (Tesseract) untuk ini.")

    print(f"\n{SEP}\n")


def save_output(result: dict, output_path: str):
    """Simpan teks ke file."""
    with open(output_path, "w", encoding="utf-8") as f:
        # Header info
        f.write(f"# Hasil Ekstraksi PDF\n")
        f.write(f"# Metode: {result['method']}\n")
        f.write(f"# Total Halaman: {result['page_count']}\n")
        if result["metadata"].get("title"):
            f.write(f"# Judul: {result['metadata']['title']}\n")
        f.write(f"# {'=' * 56}\n\n")
        f.write(result["full_text"])
    print(f"💾 Teks disimpan ke: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="📄 PDF Reader — Ekstrak teks bersih dari file PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python pdf_reader.py dokumen.pdf
  python pdf_reader.py dokumen.pdf -v
  python pdf_reader.py dokumen.pdf -o hasil.txt
  python pdf_reader.py dokumen.pdf --pages 1-5
  python pdf_reader.py dokumen.pdf --password rahasia123
  python pdf_reader.py dokumen.pdf --method pymupdf
        """
    )

    parser.add_argument("pdf_file", help="Path ke file PDF yang ingin dibaca")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Tampilkan teks per halaman secara detail")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Simpan teks ke file (misal: hasil.txt)")
    parser.add_argument("--pages", metavar="RANGE",
                        help="Halaman yang diekstrak, misal: 1-5 atau 2,4,6")
    parser.add_argument("--password", metavar="PASS",
                        help="Password jika PDF terenkripsi")
    parser.add_argument("--method", choices=["auto", "pdfplumber", "pymupdf"],
                        default="auto",
                        help="Metode ekstraksi (default: auto)")
    parser.add_argument("--info", action="store_true",
                        help="Hanya tampilkan info PDF tanpa isi teks")

    args = parser.parse_args()

    # Validasi file
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ File tidak ditemukan: {pdf_path}")
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print(f"⚠️  Peringatan: File bukan PDF ({pdf_path.suffix})")

    check_dependencies()

    print(f"\n🔍 Membaca: {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")

    # Deteksi tipe PDF
    pdf_type = detect_pdf_type(str(pdf_path))
    if pdf_type == "scanned":
        print("⚠️  PDF ini tampaknya hasil scan (tidak ada teks layer).")
        print("   Untuk OCR, install tesseract + pytesseract.")

    # Hanya info?
    if args.info:
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            meta = doc.metadata
            print(f"\n📋 Info PDF:")
            print(f"   Halaman     : {doc.page_count}")
            print(f"   Judul       : {meta.get('title', '-')}")
            print(f"   Penulis     : {meta.get('author', '-')}")
            print(f"   Subjek      : {meta.get('subject', '-')}")
            print(f"   Creator     : {meta.get('creator', '-')}")
            print(f"   Producer    : {meta.get('producer', '-')}")
            print(f"   Tipe        : {pdf_type}")
            print(f"   Terenkripsi : {'Ya' if doc.needs_pass else 'Tidak'}")
            doc.close()
        except Exception as e:
            print(f"❌ Gagal membaca info: {e}")
        sys.exit(0)

    # Pilih metode ekstraksi
    if args.method == "auto" or args.method == "pdfplumber":
        print("⚙️  Menggunakan metode: pdfplumber")
        result = extract_with_pdfplumber(str(pdf_path), args.password)
        # Fallback ke PyMuPDF jika gagal
        if not result["success"] and args.method == "auto":
            print("⚙️  Fallback ke PyMuPDF...")
            result = extract_with_pymupdf(str(pdf_path), args.password)
    else:
        print("⚙️  Menggunakan metode: PyMuPDF")
        result = extract_with_pymupdf(str(pdf_path), args.password)

    # Filter halaman jika diminta
    if args.pages and result["success"]:
        try:
            selected = set()
            for part in args.pages.split(","):
                if "-" in part:
                    start, end = part.split("-")
                    selected.update(range(int(start), int(end) + 1))
                else:
                    selected.add(int(part))

            result["pages"] = [p for p in result["pages"] if p["page"] in selected]
            result["full_text"] = "\n\n".join(
                f"--- Halaman {p['page']} ---\n{p['text']}"
                for p in result["pages"] if p["text"]
            )
            print(f"📌 Menampilkan halaman: {sorted(selected)}")
        except ValueError:
            print("⚠️  Format --pages tidak valid. Gunakan: 1-5 atau 2,4,6")

    # Tampilkan laporan
    print_report(result, verbose=args.verbose)

    # Simpan output
    if args.output and result["success"]:
        save_output(result, args.output)
    elif result["success"] and not args.verbose:
        # Auto-save dengan nama sama
        default_out = pdf_path.with_suffix(".txt")
        save_output(result, str(default_out))


if __name__ == "__main__":
    main()
