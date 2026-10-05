# Şarap Atlası — çalışma durumu

Temel: raki-atlas yapısı. Ham veriler: scratchpad/sarap → arastirma/ (derle.py ikisinden de okur, scratchpad öncelikli; yenilemek için `python3 arastirma/derle.py`).
index.html parçalardan birleştirilip üretildi (scratchpad/build/assemble.py); sonrasında yalnızca DATA bloğu derle.py ile yenilenir.

## Adımlar
- [x] api/, functions/api/, raf.js, satis.json kopyalandı; api/sync.ts kelime listeleri şarap temalı (3x32)
- [x] arastirma/derle.py (TR + dünya + rehber bölge eşleştirme; eksik dosyaları atlar)
- [x] index.html üretildi (tema, sekmeler, ağaç Ülke→Bölge→Şaraphane→Şarap, üzüm/renk modu, üzüm rehberi, bölgeler+harita, prestij, tadım okulu, sofra, kültür, sosyal)
- [x] sw.js, manifest, ikonlar, scripts (75 cl), README, docs/ONERILER.md
- [ ] Kalite kontrol (sözdizimi, playwright 390/1280, api testi, grep)
- [ ] oduller.json geldiğinde derle.py'yi yeniden çalıştır; Prestij sekmesini kontrol et

## Notlar
- oduller.json henüz yok (Prestij sekmesi yedek metin gösterir); dunya-uzumler.json büyüyebilir.
