# Şarap Atlası — geliştirici notları

Türkçe şarap atlası: Türkiye ve dünya şarapları, üzümler, bölgeler, prestij ve ödüller, tadım okulu. Yayın: https://sarap-atlas.pages.dev · Depo: `mukreminyuksel/sarap-atlas` (`main`).

## Çalıştırma
- Yerel: `python3 -m http.server 8000`; 18 yaş onayı için `localStorage.setItem('sarap_yas','1')`.
- Veri `arastirma/` dosyalarından üretilir: `python3 arastirma/derle.py` → yalnızca `index.html` içindeki `DATA` bloğunu ve `data/*.json` dosyalarını yeniden yazar. **Arayüz değişikliği doğrudan `index.html`'de yapılır** (derleme sırasında ezilmez).
- Sekmeler: Keşfet (Katalog, Üzüm Rehberi, Bölgeler), Öğren & Prestij (Tadım Okulu, Prestij & Ödüller), Sofra & Kültür, Öneriler, Mahzenim, Sosyal Buluşmalar, Kaynaklar. Dünya şaraplarında fiyat USD gösterilir; TL için `data/fiyatlar.json` içinde `kur.usd` gerekir (aylık fiyat görevi doldurur).

## Yapı
- Türkiye: `ureticiler-trakya|ege|anadolu.json` (163 lisanslı firma, resmî listeye göre), `saraplar-trakya|ege|anadolu.json` (~490 şarap), `lisans-sarap.json`.
- Dünya: `dunya-bolgeler.json` (16 ülke, sınıflandırmalar, prestij piramidi, rekolte tablosu), `dunya-saraplar.json` (317), `dunya-uzumler.json` (55), `oduller.json` (yarışmalar, Wine Spectator yılın şarapları 2010-2025, Türk şaraplarının başarıları, eleştirmenler), `tadim-okulu.json` (renk skalası, aroma çarkı, damak yapısı, kusurlar, servis).
- Türkiye rehberi: `uzumler.json` (51), `bolgeler.json` (12), `yemek.json` (33), `kultur.json`.
- **Puanlar:** Türk yazarların 10'luk notları 100'e çevrilmiştir (50 + 5 × not); yalnızca madalyası olanlar için altın 93, gümüş 89, bronz 86 gibi tahmini bir değer kullanılmıştır. Sitede her puanın dayanağı gösterilir. Dünya şaraplarında "editoryal konsensüs" aralıkları genel bilgiye dayanır, tek tek eleştirmen sayfasından doğrulanmamıştır; bunu sitede belirt.
- IWSC'nin iki Türk ödülü (2025 Akberg Şirince, 2026 V'Asbos) arama özetine dayanıyor, iwsc.net'ten doğrulanmadı; "doğrulanacak" notuyla gösterilir.

## Veri dosyaları ve betikler
- `data/fiyatlar.json` — fiyat kayıtları (kaynak, güven, tarih). Elle düzenleme; aylık görev `scripts/fiyat-guncelle.mjs` ile yazar (`sec` → araştırılacaklar, `uygula dosya.json` → güvenlik kontrolleriyle yazar; şüpheli değişimleri reddeder).
- `data/baglantilar.json` — üreticilerin resmî site ve sosyal medya bağlantıları. `scripts/baglanti.mjs` (`sec` / `ekle` / `yok` / `kontrol` / `sil`). Yalnızca **resmî** hesaplar.
- `data/satis.json` — "Nereden Alınır" (yasal not, zincir, duty-free, butik); `data/topluluk.json` — kulüp, grup, festival, kanallar.

## Genel kurallar (bütün atlas siteleri için)
- **Dil:** Site metinleri, commit mesajları ve kullanıcıyla yazışma **Türkçe**. Kod ve değişken adları mevcut dosyadaki dile uysun.
- **Tek dosyalık uygulama:** Arayüz ve mantık `index.html` içinde (satır içi `<script>`); ortak yardımcılar `raf.js`. Derleme adımı yok. Sözdizimi kontrolü: `node -e "const s=require('fs').readFileSync('index.html','utf8');[...s.matchAll(/<script>([\\s\\S]*?)<\\/script>/g)].forEach(x=>new Function(x[1]));console.log('ok')"` (**non-greedy** regex; sayfada birden fazla `<script>` var).
- **Önbellek:** Sayfa ya da veri değiştirince `sw.js` içindeki `CACHE` adındaki sürüm numarasını artır (ör. `…-v38` → `…-v39`). Artırmazsan kullanıcılar eski sürümü görür.
- **Yayın:** `main`'e push = Cloudflare Pages otomatik yayın (build komutu yok, çıktı dizini `/`). PR gerekmez. Veri deposu KV bağlaması `wrangler.toml` içinde, adı `VERI`.
- **Sunucu tarafı:** `api/*.ts` platformdan bağımsız çekirdek, `functions/api/*.ts` Cloudflare katmanı (KV: `api/kv.ts`). Uç noktalar: `/api/sync` (bulut kodu + telefon/PIN), `/api/gece` (tadım geceleri), `/api/kulup` (kulüpler), `/api/barkod` (Raf Asistanı barkod sözlüğü). Yerelde denemek için `npx wrangler pages dev .`; saf mantık testi için `node --experimental-strip-types` ile `api/*.ts` içindeki `isle(req, depo)` bellek içi sahte depoyla çağrılabilir.
- **Gizlilik ilkeleri (bozma):** Telefon ve PIN düz metin saklanmaz (SHA-256 özeti); bulut kodu ve PIN ekranda varsayılan **gizli** (👁 düğmesi); tadım gecesinde başkalarının puanı oylama bitmeden gizli; GoatCounter çerezsiz sayaçtır, kişisel veri yok.
- **Veri dürüstlüğü (en önemli kural):**
  - Uydurma bilgi, fiyat, puan ya da ödül **yok**. Emin olunmayan alan boş bırakılır; fiyatı kaynaksız olan "tahmin" diye işaretlenir.
  - Gerçek kişiler hakkında yalnızca kamuya açık ve kaynağı gösterilebilen bilgi. Özel hayat, sağlık, bağımlılık, paparazzi/özel fotoğraftan çıkarım **yok**. Türkiye'den yaşayan gerçek kişi (iş insanı, ünlü) magazin listelerine eklenmez.
  - Untappd, BeerAdvocate, RateBeer, Whiskybase, Vivino, CellarTracker gibi sitelerden veri **kazınmaz**.
  - Giriş, captcha, bot koruması ya da yaş doğrulama kapısı olan sayfalar **aşılmaz**; açılmıyorsa atlanır.
  - Türk sitelerini okurken `WebFetch` çalışmaz: `curl -sL -m 25 -A 'Mozilla/5.0' URL` kullan.
  - Türkiye'de alkolün internetten tüketiciye satışı yasaktır: "internetten satın al" bağlantısı verilmez; yalnızca fiziksel mağaza, duty-free ve markanın kendi sitesi.
- **Kapsam denetimi (ders: Şarap'ta Kayra'nın 15 markasından yalnız 4'ü kataloğa girmişti):** Yeni veri turlarında yalnız tadım sitelerine değil, **resmî lisans listesine ve her üreticinin / Türkiye dağıtıcısının resmî ürün portföyüne** bakılır. Tur öncesi ve sonrası üretici başına katalogdaki ürün sayısı kontrol edilir; az kayıtlı büyük üretici ya da hiç kaydı olmayan lisanslı üretici eksik sayılır. `python3 scripts/kapsam.py` bu sayımı yapar.
- **Commit mesajı:** Türkçe, ne ve neden. Sonuna şu iki satır eklenir (yapay zekâ ile yapılan işlerde):
  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  Claude-Session: <oturum bağlantısı>
  ```
- **Otomatik görevler (Claude Routines) bu depolara kendiliğinden push eder:** fiyat (ayın 1-6'sı, siteye göre), görseller (3-4'ü, viski ve bira), üretici bağlantıları (ayın 5'i, hepsi). **Çalışmaya başlamadan önce `git pull`.** Bu görevler yalnızca kendi veri dosyasına dokunur (`data/fiyatlar.json`, `data/gorseller.json` + `img/`, `data/baglantilar.json`).
- **Kardeş siteler:** viski-atlas, bira-atlas, raki-atlas, sarap-atlas (hepsi `*.pages.dev`). Ortak parçalar (api, raf.js, kardeş bağlantı kutusu, göz düğmesi, filtre yapıları) siteler arasında kopyadır; birinde yapılan ortak bir düzeltme genelde diğerlerine de gerekir. Yol haritası: `docs/ONERILER.md`.
- **localStorage anahtarları site önekli** (`viski_`, `bira_`, `raki_`, `sarap_`); ayrı alan adlarında çakışmaz ama önekleri değiştirme, kayıtlı kullanıcı verisi kaybolur.

## Ekim 2026 eklemeleri (şarap kartı, sıralama, üzüm haritası)
- **Yeni ham dosyalar:** `arastirma/saraplar-ek.json` (degustasyon.net WP API ile çekilen roze + Kayra ürünleri; derle.py `ek` bölümü olarak okur), `arastirma/uzum-il.json` (il il bağcılık → `data/uzum-il.json`), `arastirma/bul-dogrulanmadi.json` (bulunabilirliği doğrulanmamış şarap id'leri; sitede "(tahmini)" görünür, doğrulanınca id silinir).
- **DATA'ya taşınan yeni alanlar:** `gorunum`, `koku`, `agiz` (derle.py `kisalt()` ile ~220 karaktere kısaltılır), `servis`, `yemek`, `yillanma`, `sek` (alkol_seker), `pk` (profil kaynağı), `pr` (profil rekoltesi), `pn` (profil notu), `pnot` (puan dayanağı), `pTah` (tahmini puan: madalya/alt sınırdan türetilmiş, sitede "~"), `bulT` (bulunabilirlik tahmini), `bolgeEski`/`bolgeK` (bölge düzeltmesi ve kaynağı). Bölge düzeltmeleri (Ege/Anadolu ajanlarının ~20 şarabı) korunur.
- **iyisarap.com / iyisarap.plus bağlantıları sitede gösterilmez** (alkolün internetten satışı yasak): derle.py `kaynak_temiz()` bunları `kaynak` ve `profil_kaynak`'tan ayıklar; fiyat yalnızca "liste fiyatı (kaynak, tarih)" metni olarak görünür.
- **Kadehte bölümü** (`kadehteHTML` in index.html): kaynakta gerçek alan varsa o gösterilir ("kaynakta var"); yoksa üzüm yapısı (`uzumler.json` → `yapi`, `aromalar`), renk ve alkolden türetilir ve "türetilmiş" etiketlenir. Damak çubukları metindeki anahtar sözcüklerden ("metinden") ya da üzümden türetilir.
- **Türkiye Şarap Sıralaması** (`trsira` sekmesi) yöntemi: *Bileşik skor* = puan + ödül bonusu (Platin/Best in Show 10, Altın 6, Gümüş 3, Bronz 1,5, diğer 1 birim; toplamın yarısı, en çok +5; tahmini puanlı şaraba bonus yok). *Fiyat/performans* = (puan − 70) × 1000 ÷ TL, puan ≥ 85 ve kaynaklı fiyat şart. *Şaraphane* = en yüksek 3 puanın ortalaması, en az 2 puanlı şarap. En iyi 50/100/200 seçicisi `localStorage['sarap_topn']` (Puan Sıralaması ile ortak).
- **Üzüm Haritası** (`uzumil` sekmesi): `data/uzum-il.json`; uygunluk değerleri `yuksek/orta/dusuk/uygun_degil/dogrulanmadi` (null → "kaynak doğrulanmadı"); aynı markanın çift lisans kaydı (Shiluh) tek kartta birleşir; Cimin (Erzincan) için "şaraba uygun değil — neden" açıkça görünür.
- **Kayra:** Diageo Türkiye marka listesi: Imperial, Versus, Vintage, Buzbağ Rezerv, Cameo, Madre, Heritage, Allure, Experimental Series, Terra, Leona, Buzbağ, Tılsım, Cumartesi, Güzel Marmara. Tılsım ve Güzel Marmara için kaynak bulunamadı, eklenmedi. "Allure Beyaz Kalecik Karası" bir roze (2020 tadımı), "Allure Kalecik Karası" kırmızıdır.
