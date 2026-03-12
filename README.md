# Soru Bankasi

Python ile gelistirilmis basit bir masaustu soru bankasi uygulamasi.

## Ozellikler

- Duz ve sade bir arayuz.
- Sorular odakta calisma ekrani.
- `Soru Ekle` ile yeni soru kaydi.
- `Soru Listesi` ile goruntuleme ve silme.
- Sorular `data/questions.json` icinde saklanir.
- Kategori adlari otomatik duzeltilir ve sade bir ana kategoriye indirgenir.

## Gereksinimler

- Python 3.11+ (onerilen)
- Windows + PowerShell

## Kurulum

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
```

## Calistirma

```powershell
.\.venv\Scripts\python.exe .\app.py
```

## Klasor Yapisi

- `app.py`: Uygulama giris noktasi
- `src/question_bank/`: Uygulama kodlari
- `data/questions.json`: Sorularin saklandigi veri dosyasi

## Lisans

Bu proje MIT lisansi ile lisanslanmistir. Ayrinti icin `LICENSE` dosyasina bakin.
