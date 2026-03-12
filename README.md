# Soru Bankasi

Bu proje, sinava calismak icin hazirlanmis basit bir Python masaustu uygulamasidir.

## Ozellikler

- Sorular ile uygulama kodlarini ayri klasorlerde tutar.
- `Soru Ekle` ekrani ile yeni soru kaydedebilir.
- `Calis` ekraninda ders filtresi ile soru cozer.
- Sorular `data/questions.json` icinde saklanir.

## Klasor Yapisi

- `app.py`: Uygulama giris noktasi
- `src/question_bank/`: Uygulama kodlari
- `data/questions.json`: Sorularin saklandigi veri dosyasi

## Calistirma

PowerShell:

```powershell
.\.venv\Scripts\python.exe .\app.py
```
