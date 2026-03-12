# Kriptoloji Soru Bankası

Kriptoloji sınavına hazırlık için soru havuzu uygulaması. Sorular `[[formül]]` sözdizimi ile LaTeX olarak render edilir.

## Gereksinimler

- Python 3.8+
- pip

## Kurulum

```bash
git clone https://github.com/beraterms/exam_app.git
cd exam_app
pip install -r requirements.txt
```

## Çalıştırma

```bash
py -m src.app
```

## Özellikler

- **Soru Çözme** — Her oturumda 20 rastgele soru, anında doğru/yanlış geri bildirimi
- **LaTeX Formüller** — `[[formül]]` sözdizimi ile yazılan ifadeler görsel olarak render edilir
- **Konu & Kaynak Gösterimi** — Her soruda konu adı ve kaynak bilgisi görünür
- **Çözüm Açıklamaları** — Cevap seçildikten sonra adım adım açıklama gösterilir
- **RSA Hesaplayıcı** — p, q, e ve mesaj M girilerek şifreleme/çözme adımları hesaplanır
- **Diffie-Hellman Hesaplayıcı** — p, g, a, b değerleriyle ortak gizli anahtar hesaplanır

## Soru Formatı

Sorular `data/kriptoloji.ndjson` dosyasına NDJSON formatında eklenir. Her satır bir JSON nesnesidir:

```json
{"type": "item", "id": "Q0001", "source": "Odev1", "lesson": 1, "topic": "Kriptolojiye Giriş", "difficulty": "Orta", "question": "Soru metni...\nA) ...\nB) ...\nC) ...\nD) ...", "solution": "Doğru Cevap: C\nAçıklama: ..."}
```

LaTeX formüller çift köşeli parantez ile yazılır: `[[a^{p-1} \equiv 1 \pmod{p}]]`
