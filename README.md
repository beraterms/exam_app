# Soru Bankasi

Soru bankasi, sinavlara hazirlik icin soru cozmeyi kolaylastirmak amaciyla gelistirilmis basit bir masaustu uygulamasidir.

## Gereksinimler

- Python 3.11+ (onerilen)
- Windows + PowerShell

## Kurulum
Anaconda powershell prompt'u başlat.

```powershell
cd /uygulamanın_bulunduğu_dizin
```
## Calistirma

```powershell
python app.py
```
NOT: Dilerseniz bu işlemi virtual enviroment oluşturarak yapın.

## Bat ile Calistirma (Tek Tik)

Windows'ta uygulamayi tek tikla acmak icin `SoruBankasi.bat` dosyasina cift tiklayin.
Bu yontem proje klasorunden calisir ve varsa `.venv` icindeki Python'u kullanir.
Python kurulu degilse calismaz.

## IDE ile çalıştırma

Ya da direkt VS Code gibi bir IDE ile çalıştırma:
```powershell
python app.py
```



## Klasor Yapisi

- `app.py`: Uygulama giris noktasi
- `src/question_bank/`: Uygulama kodlari
- `data/questions.json`: Sorularin saklandigi veri dosyasi

## Lisans

Bu proje MIT lisansi ile lisanslanmistir. Ayrinti icin `LICENSE` dosyasina bakin.

