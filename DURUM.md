# Şarap Atlası — çalışma durumu

Temel: raki-atlas yapısı. Ham veriler: scratchpad/sarap → arastirma/ (derle.py ikisinden de okur, scratchpad öncelikli; yenilemek için `python3 arastirma/derle.py`).
index.html parçalardan birleştirilip üretildi (scratchpad/build/assemble.py); sonrasında yalnızca DATA bloğu derle.py ile yenilenir.

## Adımlar
- [x] api/, functions/api/, raf.js, satis.json kopyalandı; api/sync.ts kelime listeleri şarap temalı (3x32)
- [x] arastirma/derle.py (TR + dünya + rehber bölge eşleştirme; eksik dosyaları atlar)
- [x] index.html üretildi (tema, sekmeler, ağaç Ülke→Bölge→Şaraphane→Şarap, üzüm/renk modu, üzüm rehberi, bölgeler+harita, prestij, tadım okulu, sofra, kültür, sosyal)
- [x] sw.js, manifest, ikonlar, scripts (75 cl), README, docs/ONERILER.md
- [x] Kalite kontrol: script sözdizimi, playwright 390/1280 (20 sekme, hata ve yatay taşma yok), api/*.ts sahte KV testi, kelime grep'i
- [x] oduller.json geldi, derle.py ile işlendi; Prestij sekmesi kontrol edildi
- [ ] (isteğe bağlı) ham veriler büyürse `python3 arastirma/derle.py` yeniden çalıştırılır

## Notlar
- Harita (Leaflet/Esri) sandbox'ta internet olmadığından yalnızca sahte L ile denendi (205 nokta çizildi); canlıda kontrol edilmeli.
- Dünya şarap fiyatı USD; TL karşılığı için data/fiyatlar.json'da kur.usd gerekir (aylık görev doldurur).
