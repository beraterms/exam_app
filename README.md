# Soru Bankasi

Soru bankasi, sinavlara hazirlik icin soru cozmeyi kolaylastirmak amaciyla gelistirilmis basit bir masaustu uygulamasidir.

## Gereksinimler

- Python 3.11+ (onerilen)
- Windows + PowerShell

## Kurulum

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
```
Ya da direkt VS Code gibi bir IDE ile çalıştırma
```powershell
python app.py
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
