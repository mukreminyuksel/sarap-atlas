# 🍷 Şarap Atlası

Türkiye'nin ve dünyanın şarapları bölge, şaraphane ve şarap şarap; yerli üzüm rehberi, tadım okulu, sofra eşleşmeleri, prestij ve ödüller ve kişisel mahzen.
Viski Atlası, Bira Atlası ve Rakı Atlası'nın kardeşi: https://viski-atlas.pages.dev · https://bira-atlas.pages.dev · https://raki-atlas.pages.dev

## Özellikler

- **Katalog:** Türkiye ve dünya şarapları tek ağaçta, *Ülke → Bölge → Şaraphane → Şarap*; Türkiye en üstte. Alternatif düzenler: *Üzüme göre* ve *Renge göre*.
  Filtreler: ülke, renk, yerli / uluslararası üzüm, katman (Efsane, İkon, Klasik, Değer), puan ve fiyat aralığı, bulunabilirlik, "Türkiye'de bulunur", sadece ödüllüler.
- **Şarap künyesi:** renk, üzümler (her biri üzüm rehberine bağlı), rekolte, alkol, tat, puan, fiyat (Türkiye perakende, 75 cl; kaynaklı fiyatlarda “doğrulanmış” rozeti; dünya şaraplarında yaklaşık USD),
  ödül, sınıflandırma, kaynaklar, şaraphane kartı (hikâye, web, Instagram) ve “Yanında ne iyi gider” (3 yemek önerisi). Paylaşılabilir bağlantı: `#s=<id>`.
- **🍇 Üzüm Rehberi:** yerli ve uluslararası üzümler; karakter, yapı çubukları (asit, tanen, gövde, alkol), bölge, eşleşme, örnek üreticiler, o üzümden katalog şarapları; denenen üzümlere damga (Üzüm Pasaportu).
- **🗺️ Bölgeler:** Türkiye'nin 12 bağ bölgesi (iklim, toprak, üzümler, şaraphaneler, bağ rotası, hasat) + resmî kayıt kutusu (lisans listesine göre il il firma sayısı); dünya ülkeleri ve bölgeleri (kalite sistemi, sınıflandırma, ikonlar, iyi yıllar); dünya ölçeğinde Leaflet haritası.
- **🎓 Tadım Okulu:** kadehte renk skalası, aroma çarkı, damak yapısı, BLIC kalite ölçütleri, kusurlar, 6 adımlık sistematik tadım, servis sıcaklığı, yıllanma. Tadım notu formu aynı sistemi kullanır.
- **🏆 Prestij & Ödüller:** prestij piramidi, rekolte tablosu (ısı haritası), yarışmalar, yılın şarapları, dünya sahnesinde Türk şarapları, eleştirmen ölçekleri.
- **🍽️ Sofra:** Türk mutfağı ve şarap eşleşmeleri (et, balık, zeytinyağlı, sokak, peynir, tatlı); ne uymaz bilgisi; katalogdan öneriler.
- **📜 Kültür:** tarihçe zaman çizelgesi, servis rehberi (sıcaklık, dekantasyon, kadeh, saklama), aramalı terimler sözlüğü, bağ bozumu festivalleri.
- **Topluluk** ve **Nereden Alınır** (yasal not, zincir marketler, duty-free).
- **Mahzenim:** Denedim / Deneyeceğim listeleri, tadım notu (renk, burun, damak) ve kişisel puan, Gurme puanı
  (Meraklı → Kadeh Arkadaşı → Bağ Gezgini → Yerli Üzüm Kâşifi → Mahzen Sahibi → Sommelier Ruhlu), Üzüm Pasaportu, istatistik ve paylaşım kartı, akıllı öneriler, yedek al/yükle.
- **Sosyal:** bulut kaydı (kod ya da telefon + PIN), tadım geceleri (kör tadım dahil), davetle kapalı kulüpler.
- **📷 Raf Asistanı:** etiket ya da barkod tanıma (`raf.js`, `/api/barkod`).
- PWA: çevrimdışı çalışır (`sw.js`), ana ekrana eklenebilir. 18 yaş onayı vardır.

## Veri politikası

- **Uydurma yok.** Her şarap kaydında kaynak bağlantıları (`kaynak`) bulunur; doğrulanamayan alan boş bırakılır (ör. puan yoksa “—”).
- **Fiyatlar kaynaklıdır ya da yoktur.** Türk şaraplarının fiyatları Ekim 2026 Türkiye perakende fiyatlarıdır (75 cl) ve kaynak adresiyle tutulur; kaynaksız fiyat sitede gösterilmez.
  Dünya şaraplarında kaynaklardaki yaklaşık piyasa fiyatı USD olarak verilir.
- Puanlar tadım yazıları, yarışma sonuçları ve eleştirmen notlarından derlenen editoryal puanlardır (0-100), tek bir yayının canlı puanı değildir.
- Şaraphane listesi yalnızca piyasada bilinen markası olan kayıtları gösterir; Tarım ve Orman Bakanlığı'nın alkollü içki üretim izni listesindeki diğer firmalar yalnızca “resmî kayıt” sayısına katılır. Harita konumları il/ilçe/bölge düzeyinde yaklaşıktır.
- Sitede magazin, ünlüler ve kurgu karakterleri bölümü yoktur.

## Dosyalar

| Yol | İçerik |
|---|---|
| `index.html` | Tek sayfalık uygulama; `DATA` dizisi `arastirma/derle.py` ile üretilir |
| `arastirma/` | Ham araştırma verisi (`saraplar-*.json`, `ureticiler-*.json`, `lisans-sarap.json`, `uzumler.json`, `bolgeler.json`, `yemek.json`, `kultur.json`, `satis.json`; varsa `dunya-*.json`, `oduller.json`, `tadim-okulu.json`) ve `derle.py` |
| `data/` | Sitenin okuduğu JSON'lar: `fiyatlar`, `ureticiler`, `lisans`, `uzumler`, `bolgeler`, `yemek`, `kultur`, `topluluk`, `satis`, `oduller`, `tadim-okulu`, `baglantilar`, `gorseller` |
| `api/` | Platformdan bağımsız sunucu çekirdeği: `sync.ts` (bulut kaydı), `gece.ts` (tadım geceleri), `kulup.ts`, `barkod.ts`, `ortak.ts`, `kv.ts` |
| `functions/api/` | Cloudflare Pages katmanı (KV bağlaması: `VERI`, `wrangler.toml`) |
| `scripts/fiyat-guncelle.mjs` | Aylık fiyat doğrulama yardımcısı (`sec` / `uygula`; 75 cl) |
| `scripts/baglanti.mjs` | Şaraphanelerin resmî site/sosyal medya bağlantıları |

Veriyi yeniden üretmek için: `python3 arastirma/derle.py` (ham veriyi önce scratchpad klasöründen, yoksa `arastirma/` içinden okur; Ege ve Anadolu dosyaları büyüdükçe yeniden çalıştırmak yeterlidir, tekrar eden id'ler ayıklanır).

Alkolü ölçülü tüketin; içtiyseniz araç kullanmayın. Bu site 18 yaşından büyükler içindir.
