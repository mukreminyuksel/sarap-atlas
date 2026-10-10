# Araştırma dosyalarından Şarap Atlası'nın verisini yeniden üretir.
#   index.html içindeki DATA dizisi   ← saraplar-trakya/ege/anadolu.json (+ varsa dunya-saraplar.json)
#   data/ureticiler.json              ← ureticiler-*.json (yalnızca markası olanlar şaraphane olarak; konum il/ilçe merkezi)
#   data/lisans.json                  ← lisans-sarap.json (+ markasız kayıtların sayısı)
#   data/uzumler.json                 ← uzumler.json (+ varsa dunya-uzumler.json) + katalogda geçen diğer üzümler
#   data/bolgeler.json                ← bolgeler.json (+ varsa dunya-bolgeler.json)
#   data/yemek.json, kultur.json, topluluk.json, satis.json (zincir + duty-free)
#   data/oduller.json, data/tadim-okulu.json (varsa)
#   data/fiyatlar.json: yalnızca henüz kaydı olmayan KAYNAKLI fiyatlar eklenir (aylık görevin kayıtları korunur)
# Ham veriler iki yerden okunur: önce araştırma scratchpad'i (SARAP_HAM ortam değişkeniyle değiştirilebilir),
# yoksa bu klasör (arastirma/). Ege ve Anadolu dosyaları büyüdükçe betiği yeniden çalıştırmak yeterli;
# tekrar eden id'ler ayıklanır. Henüz gelmemiş dosyalar atlanır.
# Kullanım: python3 arastirma/derle.py
import json, os, re, unicodedata, collections

KOK = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(KOK)
HTML = os.path.join(SITE, 'index.html')
DATA_DIR = os.path.join(SITE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
TARIH = '2026-10-05'
HAM = [os.environ.get('SARAP_HAM') or '/tmp/claude-0/-home-user/2a88b075-3c7c-5c77-9d4f-349a62689e42/scratchpad/sarap', KOK]
uyarilar = []


def oku(ad, var=None):
    for d in HAM:
        p = os.path.join(d, ad)
        if os.path.exists(p):
            try:
                return json.load(open(p, encoding='utf-8'))
            except Exception as e:  # yarım yazılmış dosya: diğer klasörü dene
                uyarilar.append(f'{p} okunamadı ({e})')
    return var


def yaz(ad, veri):
    with open(os.path.join(DATA_DIR, ad), 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
        f.write('\n')


TRC = str.maketrans('ıİşŞçÇğĞöÖüÜâÂîÎûÛ', 'iissccggoouuaaiiuu')


def norm(s):
    s = unicodedata.normalize('NFD', str(s or '').translate(TRC))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', '', s)


def slug(s):
    s = unicodedata.normalize('NFD', str(s or '').translate(TRC))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def metin(v):
    if isinstance(v, list):
        return ', '.join(str(x) for x in v if x not in (None, ''))
    return str(v or '').strip()


SATIS_URL = re.compile(r'iyisarap\.(com|plus)', re.I)  # çevrimiçi satıcı bağlantısı: alkolün internetten satışı yasak, sitede gösterilmez


def kaynak_temiz(liste):
    return [k for k in (liste or []) if k and not SATIS_URL.search(k)]


def kisalt(t, n=220):
    """Kaynak metnini en fazla ~n karaktere indirir: tam cümlelerde keser, tek cümle uzunsa virgülden böler."""
    t = re.sub(r'\s+', ' ', str(t or '')).strip()
    if not t:
        return ''
    if len(t) <= n:
        return t if t[-1] in '.!?' else t + '.'
    cum = re.split(r'(?<=[.!?])\s+', t)
    out = ''
    for c in cum:
        if len(out) + len(c) + (1 if out else 0) <= n:
            out = (out + ' ' + c).strip()
        else:
            break
    if out:
        return out
    k = t[:n]
    k = k[:k.rfind(',')] if ',' in k[60:] else k[:k.rfind(' ')]
    return k.rstrip(' ,;:') + '.'


def tahmini_puan(w):
    """Puan tadım notundan değil madalyadan/alt sınırdan türetilmişse True (sitede 'tahmini' işaretlenir)."""
    pn = str(w.get('puan_not') or '').lower()
    if pn:
        return bool(re.search(r've üzeri|alt sınır|tahmin|madalya', pn)) and 'degustasyon.net' not in pn.split('→')[0]
    return bool(w.get('odul')) and not any('degustasyon' in k for k in (w.get('kaynak') or []))


RENKLER = {'kirmizi', 'beyaz', 'roze', 'kopuren', 'tatli', 'turuncu', 'fortifiye'}
RENK_ES = {'kırmızı': 'kirmizi', 'red': 'kirmizi', 'white': 'beyaz', 'rose': 'roze', 'rosé': 'roze', 'köpüren': 'kopuren',
           'kopuklu': 'kopuren', 'köpüklü': 'kopuren', 'sparkling': 'kopuren', 'tatlı': 'tatli', 'sweet': 'tatli', 'orange': 'turuncu',
           'fortified': 'fortifiye', 'fortifiye': 'fortifiye', 'likör şarabı': 'fortifiye'}
BULLAR = {'kolay', 'tekel', 'sarapci', 'zor'}
KATMANLAR = {'efsane', 'ikon', 'klasik', 'deger'}

# ---------- Şaraphane seviyesi (Premium / 2. Düzey / 3. Düzey / Derecelendirilmedi) ----------
# Her derlemede yeniden hesaplanır; yalnızca mevcut puan, katman ve ödül alanlarından türetilir.
# sev: 'Premium' | '2' | '3' | '0' (derecelendirilmedi). Seviye ŞARAPHANE düzeyindedir; her şarap şaraphanesinin değerini taşır.
SEVIYE_ESIKLERI = {
    'tr_premium': 91,   # Türkiye: en yüksek 3 puanın ortalaması >= 91 -> Premium
    'tr_ikinci': 87,    # 87 <= ortalama < 91 -> 2. Düzey; altı 3. Düzey
    'tr_en_iyi_n': 3,   # ortalamaya giren en yüksek puan sayısı
}
# Dünya: şaraphanenin en üst editoryal katmanı. efsane -> Premium; ikon -> 2; klasik/değer -> 3
DUNYA_KATMAN_SEV = {'efsane': 'Premium', 'ikon': '2', 'klasik': '3', 'deger': '3'}
KATMAN_ONCELIK = ['efsane', 'ikon', 'klasik', 'deger']
UST_ODUL = re.compile(r'platin|best in show|grand gold', re.I)
YER_TUTUCU = ('Üreticisi doğrulanamadı', 'Üreticisi belirtilmemiş')


def seviye_hesapla(veri):
    gruplar = collections.defaultdict(list)
    for d in veri:
        gruplar[(d['ulke'], d['sh'] or d['ure'])].append(d)
    sonuc = {}
    for (ulke, ad), ws in gruplar.items():
        if ad in YER_TUTUCU:
            sonuc[(ulke, ad)] = '0'
        elif ulke != 'Türkiye':
            k = [w['katman'] for w in ws if w.get('katman')]
            en = next((x for x in KATMAN_ONCELIK if x in k), None)
            sonuc[(ulke, ad)] = DUNYA_KATMAN_SEV[en] if en else '0'
        else:
            p = sorted((w['puan'] for w in ws if (w['puan'] or 0) > 0), reverse=True)[:SEVIYE_ESIKLERI['tr_en_iyi_n']]
            if not p:
                sonuc[(ulke, ad)] = '0'
                continue
            ort = sum(p) / len(p)
            ust = any(UST_ODUL.search(w.get('odul') or '') for w in ws)
            sonuc[(ulke, ad)] = 'Premium' if (ort >= SEVIYE_ESIKLERI['tr_premium'] or ust) else '2' if ort >= SEVIYE_ESIKLERI['tr_ikinci'] else '3'
    for d in veri:
        d['sev'] = sonuc[(d['ulke'], d['sh'] or d['ure'])]
    return sonuc

# ---------- Türkiye bölgeleri: il / ilçe / bölge metninden bölge kimliği ----------
KURAL = [
    ('diger', 'assos ayvacik bayramic gomec madra balya mudanya iznik foca'),
    ('bozcaada-gokceada', 'bozcaada gokceada avsa'),
    ('guneydogu', 'guneydogu mardin midyat diyarbakir sirnak idil egil cermik ergani'),
    ('trakya', 'trakya gelibolu eceabat saroz sarkoy murefte tekirdag kirklareli edirne luleburgaz silivri marmaraereglisi corlu suleymanpasa havsa ipsala uzunkopru'),
    ('urla', 'urla cesme seferihisar menderes kemalpasa'),
    ('sirince-selcuk', 'sirince selcuk torbali tire germencik'),
    ('ic-ege', 'akhisar alasehir kula salihli esme sarigol'),
    ('denizli-cal', 'cal denizli guney'),
    ('akdeniz', 'akdeniz elmali mut datca bodrum silifke kepez belen hatay antakya'),
    ('kapadokya', 'kapadokya urgup avanos gulsehir hacibektas guzelyurt nevsehir kayseri kocasinan aksaray'),
    ('kalecik', 'ankara kalecik akyurt hasandede'),
    ('elazig', 'doguanadolu elazig sivrice malatya agin'),
    ('karadeniz', 'karadeniz tokat amasya niksar artvin borcka gumushacikoy'),
]
IL_BOLGE = {'Tekirdağ': 'trakya', 'Kırklareli': 'trakya', 'Edirne': 'trakya', 'İstanbul': 'trakya', 'Çanakkale': 'trakya',
            'Aydın': 'sirince-selcuk', 'Manisa': 'ic-ege', 'Uşak': 'ic-ege', 'Denizli': 'denizli-cal', 'Antalya': 'akdeniz',
            'Muğla': 'akdeniz', 'Mersin': 'akdeniz', 'Hatay': 'akdeniz', 'Nevşehir': 'kapadokya', 'Kırşehir': 'kapadokya',
            'Aksaray': 'kapadokya', 'Kayseri': 'kapadokya', 'Ankara': 'kalecik', 'Kırıkkale': 'kalecik', 'Elazığ': 'elazig',
            'Malatya': 'elazig', 'Diyarbakır': 'guneydogu', 'Mardin': 'guneydogu', 'Şırnak': 'guneydogu', 'Tokat': 'karadeniz',
            'Amasya': 'karadeniz', 'Artvin': 'karadeniz'}


def kelime_var(t, k):
    return ' ' + k + ' ' in t


def tr_bolge(il, bolge_metni, ilce=''):
    def ascii_(s):
        s = unicodedata.normalize('NFD', str(s or '').translate(TRC))
        return re.sub(r'[^a-z0-9 ]+', ' ', ''.join(c for c in s if not unicodedata.combining(c)).lower())
    t = ' ' + ascii_(bolge_metni).replace('dogu anadolu', 'doguanadolu') + ' ' + ascii_(ilce) + ' '
    for bid, kel in KURAL:
        if any(kelime_var(t, k) for k in kel.split()):
            return bid
    return IL_BOLGE.get(il, 'diger')


# ---------- Yaklaşık konumlar (ilçe ya da il merkezi) ----------
IL = {'Tekirdağ': [40.978, 27.511], 'Kırklareli': [41.735, 27.225], 'Edirne': [41.677, 26.556], 'İstanbul': [41.008, 28.978],
      'Çanakkale': [40.146, 26.408], 'Balıkesir': [39.649, 27.886], 'Bursa': [40.183, 29.067], 'İzmir': [38.423, 27.143],
      'Manisa': [38.614, 27.43], 'Aydın': [37.845, 27.84], 'Denizli': [37.776, 29.086], 'Uşak': [38.682, 29.408],
      'Muğla': [37.215, 28.364], 'Antalya': [36.897, 30.713], 'Mersin': [36.8, 34.633], 'Hatay': [36.202, 36.16],
      'Nevşehir': [38.625, 34.714], 'Kırşehir': [39.146, 34.16], 'Aksaray': [38.369, 34.037], 'Kayseri': [38.731, 35.479],
      'Ankara': [39.934, 32.86], 'Kırıkkale': [39.846, 33.515], 'Tokat': [40.314, 36.554], 'Amasya': [40.654, 35.833],
      'Elazığ': [38.675, 39.223], 'Malatya': [38.355, 38.309], 'Diyarbakır': [37.914, 40.231], 'Mardin': [37.313, 40.735],
      'Şırnak': [37.518, 42.454], 'Artvin': [41.183, 41.818], 'Isparta': [37.764, 30.556], 'Konya': [37.871, 32.485]}
ILCE = [('Mürefte', [40.668, 27.236]), ('Uçmakdere', [40.79, 27.36]), ('Hoşköy', [40.69, 27.29]), ('Şarköy', [40.613, 27.112]),
        ('Marmaraereğlisi', [40.97, 27.955]), ('Çorlu', [41.159, 27.8]), ('Lüleburgaz', [41.404, 27.356]), ('Havsa', [41.548, 26.82]),
        ('İpsala', [40.92, 26.383]), ('Gömeç', [39.39, 26.84]), ('Avşa', [40.51, 27.5]), ('Balya', [39.75, 27.58]),
        ('İznik', [40.43, 29.72]), ('Mudanya', [40.375, 28.883]), ('Silivri', [41.074, 28.247]), ('Ayvacık', [39.6, 26.4]),
        ('Eceabat', [40.184, 26.357]), ('Bozcaada', [39.835, 26.07]), ('Bayramiç', [39.81, 26.61]), ('Gelibolu', [40.41, 26.67]),
        ('Gökçeada', [40.19, 25.9]), ('Urla', [38.322, 26.765]), ('Tire', [38.089, 27.735]), ('Germencik', [37.87, 27.6]),
        ('Torbalı', [38.155, 27.36]), ('Şirince', [37.944, 27.43]), ('Selçuk', [37.95, 27.37]), ('Güney', [38.15, 29.07]),
        ('Çal', [38.08, 29.4]), ('Alaşehir', [38.35, 28.517]), ('Akhisar', [38.918, 27.84]), ('Salihli', [38.483, 28.139]),
        ('Kula', [38.547, 28.65]), ('Eşme', [38.4, 28.97]), ('Elmalı', [36.736, 29.92]), ('Kepez', [36.94, 30.71]),
        ('Belen', [36.49, 36.19]), ('Mut', [36.645, 33.437]), ('Silifke', [36.377, 33.93]), ('Kemalpaşa', [38.43, 27.42]),
        ('Seferihisar', [38.2, 26.84]), ('Çeşme', [38.323, 26.303]), ('Menderes', [38.253, 27.134]), ('Akyurt', [40.13, 33.08]),
        ('Gülşehir', [38.745, 34.62]), ('Ürgüp', [38.63, 34.91]), ('Avanos', [38.715, 34.847]), ('Hacıbektaş', [38.94, 34.56]),
        ('Güzelyurt', [38.28, 34.37]), ('Kocasinan', [38.75, 35.48]), ('Gümüşhacıköy', [40.87, 35.23]), ('Kalecik', [40.1, 33.41]),
        ('Midyat', [37.42, 41.37]), ('İdil', [37.34, 41.89]), ('Eğil', [38.26, 40.08]), ('Sivrice', [38.45, 39.31]),
        ('Ağın', [38.94, 38.71]), ('Borçka', [41.36, 41.67]), ('Çermik', [38.13, 39.45]), ('Ergani', [38.27, 39.76])]


def tr_konum(il, ilce):
    for ad, c in ILCE:
        if ad in (ilce or ''):
            return c
    return IL.get(il)


# Dünya bölgeleri için yaklaşık konum (bölge adında geçen anahtar → [enlem, boylam]); yoksa ülke merkezi
DUNYA_KONUM = [
    ('sampanya', [49.04, 3.95]), ('kuzey rhone', [45.45, 4.85]), ('guney rhone', [44.2, 4.85]), ('alsas', [48.2, 7.33]),
    ('guneybati', [44.5, 0.5]), ('jura', [46.8, 5.7]), ('kaliforniya', [38.5, -122.3]), ('bati avustralya', [-33.95, 115.07]),
    ('guney avustralya', [-34.5, 138.9]), ('yeni guney galler', [-32.8, 151.3]), ('western cape', [-33.9, 19.0]), ('constantia', [-34.03, 18.42]),
    ('aconcagua', [-32.8, -70.6]), ('central valley', [-35.0, -71.2]), ('niederosterreich', [48.4, 15.8]), ('burgenland', [47.8, 16.5]),
    ('baden', [48.1, 7.8]), ('nahe', [49.8, 7.6]), ('rheinhessen', [49.8, 8.2]), ('galicya', [42.5, -8.0]), ('katalonya', [41.4, 1.7]),
    ('kastilya', [41.65, -4.0]), ('endulus', [36.9, -5.8]), ('aragon', [41.6, -0.9]), ('friuli', [46.1, 13.2]), ('alto adige', [46.5, 11.3]),
    ('abruzzo', [42.2, 13.9]), ('campania', [40.9, 14.8]), ('puglia', [40.8, 17.0]), ('lombardiya', [45.6, 9.9]), ('dalmacya', [43.5, 16.4]),
    ('valais', [46.2, 7.6]), ('golan', [33.0, 35.8]), ('ningxia', [38.3, 106.0]), ('yunnan', [27.0, 100.0]), ('ontario', [43.1, -79.5]),
    ('minho', [41.7, -8.3]), ('ege adalari', [36.4, 25.43]), ('makedonya', [40.63, 22.07]), ('mora', [37.82, 22.66]), ('wairarapa', [-41.2, 175.5]),
    ('stefan voda', [46.5, 29.6]), ('guney ingiltere', [51.0, 0.3]), ('kartli', [41.9, 44.1]), ('imereti', [42.2, 42.7]), ('kremstal', [48.4, 15.6]),
    ('bordeaux', [44.84, -0.58]), ('medoc', [45.2, -0.9]), ('pauillac', [45.2, -0.75]), ('saint emilion', [44.89, -0.16]),
    ('sauternes', [44.53, -0.34]), ('pomerol', [44.93, -0.2]), ('burgonya', [47.05, 4.83]), ('bourgogne', [47.05, 4.83]),
    ('burgundy', [47.05, 4.83]), ('chablis', [47.81, 3.8]), ('cote d or', [47.1, 4.85]), ('champagne', [49.04, 3.95]),
    ('sampanya', [49.04, 3.95]), ('rhone', [44.9, 4.85]), ('ron', [44.9, 4.85]), ('chateauneuf', [44.06, 4.83]),
    ('loire', [47.38, 0.69]), ('alsace', [48.2, 7.33]), ('alsas', [48.2, 7.33]), ('provence', [43.5, 6.0]), ('beaujolais', [46.1, 4.6]),
    ('languedoc', [43.6, 3.3]), ('rioja', [42.47, -2.45]), ('ribera del duero', [41.65, -3.7]), ('priorat', [41.2, 0.8]),
    ('jerez', [36.68, -6.13]), ('rias baixas', [42.4, -8.7]), ('cava', [41.4, 1.7]), ('penedes', [41.35, 1.7]),
    ('douro', [41.16, -7.55]), ('porto', [41.15, -8.61]), ('madeira', [32.75, -16.95]), ('alentejo', [38.57, -7.9]),
    ('vinho verde', [41.7, -8.3]), ('mosel', [49.9, 6.95]), ('rheingau', [50.0, 8.0]), ('pfalz', [49.3, 8.15]),
    ('piemonte', [44.7, 8.0]), ('piedmont', [44.7, 8.0]), ('barolo', [44.61, 7.94]), ('barbaresco', [44.72, 8.08]),
    ('toskana', [43.4, 11.2]), ('toscana', [43.4, 11.2]), ('tuscany', [43.4, 11.2]), ('chianti', [43.5, 11.3]),
    ('montalcino', [43.06, 11.49]), ('bolgheri', [43.23, 10.6]), ('veneto', [45.5, 11.0]), ('valpolicella', [45.55, 10.9]),
    ('prosecco', [45.9, 12.1]), ('sicilya', [37.6, 14.0]), ('sicily', [37.6, 14.0]), ('etna', [37.75, 15.0]),
    ('napa', [38.5, -122.3]), ('sonoma', [38.45, -122.8]), ('willamette', [45.1, -123.1]), ('washington', [46.3, -119.5]),
    ('barossa', [-34.53, 138.95]), ('mclaren', [-35.2, 138.55]), ('coonawarra', [-37.3, 140.83]), ('margaret river', [-33.95, 115.07]),
    ('hunter', [-32.8, 151.3]), ('yarra', [-37.7, 145.5]), ('mendoza', [-32.89, -68.84]), ('salta', [-24.8, -65.4]),
    ('maipo', [-33.7, -70.7]), ('colchagua', [-34.6, -71.3]), ('casablanca', [-33.3, -71.4]), ('marlborough', [-41.5, 173.9]),
    ('central otago', [-45.0, 169.2]), ('hawke', [-39.6, 176.8]), ('stellenbosch', [-33.93, 18.86]), ('swartland', [-33.4, 18.7]),
    ('tokaj', [48.12, 21.41]), ('wachau', [48.36, 15.43]), ('santorini', [36.4, 25.43]), ('nemea', [37.82, 22.66]),
    ('naoussa', [40.63, 22.07]), ('bekaa', [33.85, 35.9]), ('kakheti', [41.65, 45.7]), ('kaheti', [41.65, 45.7]),
]
ULKE_KONUM = {'fransa': [46.6, 2.4], 'italya': [42.8, 12.6], 'ispanya': [40.2, -3.6], 'portekiz': [39.6, -8.0],
              'almanya': [50.5, 8.5], 'avusturya': [47.6, 14.6], 'abd': [38.5, -100.0], 'amerika': [38.5, -100.0],
              'avustralya': [-33.0, 141.0], 'yeni zelanda': [-41.3, 174.0], 'arjantin': [-33.0, -68.5], 'sili': [-34.0, -71.0],
              'guney afrika': [-33.9, 19.0], 'macaristan': [47.2, 19.4], 'yunanistan': [39.0, 22.0], 'lubnan': [33.85, 35.86],
              'gurcistan': [42.0, 44.0], 'israil': [31.5, 34.9], 'slovenya': [46.1, 14.8], 'hirvatistan': [45.1, 15.2],
              'romanya': [45.9, 24.9], 'moldova': [47.0, 28.8], 'bulgaristan': [42.7, 25.4], 'kanada': [43.1, -79.1],
              'ingiltere': [51.0, 0.5], 'birlesik krallik': [51.0, 0.5], 'isvicre': [46.5, 7.5], 'cin': [37.5, 106.0],
              'uruguay': [-34.6, -56.0], 'kibris': [35.0, 33.0], 'japonya': [35.7, 138.6], 'ermenistan': [40.1, 45.0]}


def dunya_konum(ulke, bolge):
    t = ' ' + re.sub(r'[^a-z0-9 ]+', ' ', unicodedata.normalize('NFD', str(bolge or '').translate(TRC)).encode('ascii', 'ignore').decode().lower()) + ' '
    for k, c in DUNYA_KONUM:
        if ' ' + k + ' ' in t or ' ' + k in t:
            return c
    u = re.sub(r'[^a-z ]+', '', unicodedata.normalize('NFD', str(ulke or '').translate(TRC)).encode('ascii', 'ignore').decode().lower()).strip()
    return ULKE_KONUM.get(u)


# ---------- 1. Üzümler (rehber + dünya üzümleri + katalogda geçen diğerleri) ----------
uzum_rehber = oku('uzumler.json', []) or []
dunya_uzum = oku('dunya-uzumler.json', None)
if isinstance(dunya_uzum, dict):
    dunya_uzum = dunya_uzum.get('uzumler') or next((v for v in dunya_uzum.values() if isinstance(v, list)), [])
dunya_uzum = dunya_uzum or []
ALIAS = {'shiraz': 'syrah', 'papaskarasi': 'papazkarasi', 'kuntra': 'karasakiz', 'alicante': 'alicante-bouschet',
         'calkarasi': 'calkarasi', 'grenachenoir': 'grenache', 'garnacha': 'grenache', 'monastrell': 'mourvedre',
         'tinto': 'tempranillo', 'tintaroriz': 'tempranillo', 'pinotnero': 'pinot-noir', 'spatburgunder': 'pinot-noir',
         'blackmuscat': 'muscat-noir', 'siyahmisket': 'muscat-noir', 'primitivo': 'zinfandel'}
ULUSLARARASI = {norm(x) for x in ['Malbec', 'Fiano', 'Pinot Gris', 'Pinot Grigio', 'Sauvignon Gris', 'Marsanne', 'Muscat of Alexandria',
                                  'Ekigaïna', 'Tannat', 'Rebo', 'Corinto', 'Marselan', 'Chenin Blanc', 'Nebbiolo', 'Muscat', 'Solaris',
                                  'Gewürztraminer', 'Semillon', 'Sémillon', 'Roussanne', 'Riesling', 'Cinsault', 'Petite Sirah',
                                  'Touriga Nacional', 'Albariño', 'Grüner Veltliner', 'Gamay', 'Barbera', 'Aglianico', 'Carménère',
                                  'Pinotage', 'Furmint', 'Assyrtiko', 'Saperavi', 'Pinot Meunier', 'Muscadelle']}

UZ = []          # birleşik üzüm listesi
UZ_ANAHTAR = {}  # norm(ad) → kayıt


def uzum_anahtarlari(u):
    ks = {norm(u.get('id')), norm(u.get('ad'))}
    for parca in re.split(r'[/(),]', str(u.get('ad') or '')):
        if norm(parca):
            ks.add(norm(parca))
    for e in u.get('diger_adlar') or u.get('esanlamlar') or []:
        ks.add(norm(e))
    return {k for k in ks if k}


for u in uzum_rehber:
    k = dict(u, rehber=True, kaynakDosya='tr')
    UZ.append(k)
    for a in uzum_anahtarlari(u):
        UZ_ANAHTAR.setdefault(a, k)
for u in dunya_uzum:
    if not isinstance(u, dict) or not (u.get('ad') or u.get('id')):
        continue
    var = next((UZ_ANAHTAR[a] for a in uzum_anahtarlari(u) if a in UZ_ANAHTAR), None)
    if var is None:
        var = {'id': u.get('id') or slug(u.get('ad')), 'ad': u.get('ad') or u.get('id'), 'yerli': bool(u.get('yerli')), 'rehber': True, 'kaynakDosya': 'dunya'}
        UZ.append(var)
    for alan, deger in u.items():
        if alan in ('id',):
            continue
        if alan not in var or var.get(alan) in (None, '', [], {}):
            var[alan] = deger
        elif alan in ('kaynak',) and isinstance(deger, list):
            var[alan] = list(dict.fromkeys((var.get(alan) or []) + deger))
    var['dunya'] = True
    for a in uzum_anahtarlari(u):
        UZ_ANAHTAR.setdefault(a, var)


def uzum_bul(ad):
    n = norm(ad)
    if n in ALIAS:
        n = norm(ALIAS[n])
    return UZ_ANAHTAR.get(n)


def uzum_kaydi(ad, renk):
    u = uzum_bul(ad)
    if u:
        return u
    u = {'id': slug(ad), 'ad': ad, 'yerli': norm(ad) not in ULUSLARARASI, 'rehber': False,
         'renk': 'beyaz' if renk == 'beyaz' else 'kirmizi' if renk == 'kirmizi' else ''}
    UZ.append(u)
    UZ_ANAHTAR[norm(ad)] = u
    return u


# ---------- 2. Türkiye şaraplarını birleştir (tekrar eden id'ler ayıklanır) ----------
ham = []
for bolum in ('trakya', 'ege', 'anadolu'):
    ham += [(bolum, x) for x in (oku(f'saraplar-{bolum}.json', []) or []) if isinstance(x, dict)]

ure_ham = []
for bolum in ('trakya', 'ege', 'anadolu'):
    ure_ham += [x for x in (oku(f'ureticiler-{bolum}.json', []) or []) if isinstance(x, dict)]

# Şaraphaneler: markası olan kayıtlar, marka adına göre birleşir (ör. Kavaklıdere'nin birden çok tesisi)
SARAPHANE = collections.OrderedDict()
for r in ure_ham:
    m = (r.get('marka') or '').strip()
    if not m:
        continue
    s = SARAPHANE.setdefault(m, {'ad': m, 'tesisler': [], 'kaynak': []})
    s['tesisler'].append(r)
    for alan in ('kurulus', 'baglar', 'web', 'instagram', 'hikaye'):
        if not s.get(alan) and r.get(alan):
            s[alan] = r[alan]
    s['uzumler'] = list(dict.fromkeys((s.get('uzumler') or []) + (r.get('uzumler') or [])))
    s['kaynak'] = list(dict.fromkeys(s['kaynak'] + (r.get('kaynak') or [])))


def saraphane_bul(ad):
    if ad in SARAPHANE:
        return ad
    n = norm(ad)
    for m in SARAPHANE:
        bas = norm(re.split(r' / | \(| – | - ', m)[0])
        if bas == n or norm(m).startswith(n) and len(n) >= 4:
            return m
    return None


def odul_sayisi(o):
    return len([x for x in re.split(r';', o or '') if x.strip()])


BUL_TAHMIN = set((oku('bul-dogrulanmadi.json', {}) or {}).get('idler') or [])
DATA, ids = [], set()
for bolum, w in ham:
    wid = str(w.get('id') or '').strip()
    if not wid or wid in ids:
        continue
    ids.add(wid)
    renk = RENK_ES.get(str(w.get('renk') or '').lower(), str(w.get('renk') or '').lower())
    if renk not in RENKLER:
        uyarilar.append(f'{wid}: bilinmeyen renk {w.get("renk")}')
    bul = w.get('bul') if w.get('bul') in BULLAR else 'zor'
    ure = (w.get('uretici') or '').strip() or 'Üreticisi doğrulanamadı'
    sh = saraphane_bul(ure)
    tesis_ilce = ''
    if sh:
        t0 = next((t for t in SARAPHANE[sh]['tesisler'] if t.get('il') == w.get('il')), SARAPHANE[sh]['tesisler'][0])
        tesis_ilce = t0.get('ilce') or ''
    bolge_metni = w.get('bolge') or ''
    # "Ege" gibi genel bölge adlarında üreticinin ilçesine bak
    bid = tr_bolge(w.get('il'), bolge_metni + (' ' + tesis_ilce if norm(bolge_metni) in ('ege', '') else ''))
    uz = [uzum_kaydi(a, renk) for a in (w.get('uzum') or []) if str(a).strip()]
    yerli = [u.get('yerli') for u in uz]
    tl = int(w.get('tl') or 0)
    d = {'id': wid, 'ad': w.get('ad') or wid, 'ure': ure, 'sh': sh or '', 'ulke': 'Türkiye', 'bolge': bid,
         'bolgeAd': bolge_metni, 'il': w.get('il') or '', 'renk': renk,
         'uzum': [str(a).strip() for a in (w.get('uzum') or []) if str(a).strip()], 'uz': [u['id'] for u in uz],
         'yrl': ('yerli' if all(yerli) else 'dunya' if not any(yerli) else 'karma') if yerli else '',
         'yil': str(w.get('yil') or ''), 'abv': w.get('abv') or 0, 'tat': w.get('tat') or '', 'puan': w.get('puan') or 0,
         'tl': tl, 'tlK': w.get('tl_kaynak') or '', 'odul': w.get('odul') or '', 'bul': bul, 'kaynak': w.get('kaynak') or []}
    if tl and not d['tlK']:
        uyarilar.append(f'{wid}: kaynaksız fiyat (tl={tl}) — fiyat gösterilmeyecek')
        d['tl'] = 0
    d['kaynak'] = kaynak_temiz(d['kaynak'])
    for a, k in (('gorunum', 'gorunum'), ('koku', 'koku'), ('agiz', 'agiz')):
        if w.get(a):
            d[k] = kisalt(w[a])
    for a in ('servis', 'yillanma'):
        if w.get(a):
            d[a] = str(w[a]).strip()
    if w.get('yemek'):
        d['yemek'] = [str(x).strip() for x in w['yemek'] if str(x).strip()][:6]
    if w.get('alkol_seker'):
        d['sek'] = str(w['alkol_seker']).strip()
    pk = w.get('profil_kaynak')
    if pk and not SATIS_URL.search(pk):
        d['pk'] = pk
    for a, k in (('profil_rekolte', 'pr'), ('profil_not', 'pn'), ('puan_not', 'pnot'), ('bolge_eski', 'bolgeEski'), ('bolge_kaynak', 'bolgeK')):
        if w.get(a):
            d[k] = str(w[a]).strip()
    if d['puan'] and tahmini_puan(w):
        d['pTah'] = 1
    if wid in BUL_TAHMIN:
        d['bulT'] = 1
    DATA.append(d)
tr_sayi = len(DATA)

# ---------- 3. Dünya şarapları (varsa) ----------
dunya = oku('dunya-saraplar.json', None)
if isinstance(dunya, dict):
    dunya = dunya.get('saraplar') or next((v for v in dunya.values() if isinstance(v, list)), [])
DUNYA_BOLGE = collections.OrderedDict()
for w in dunya or []:
    if not isinstance(w, dict):
        continue
    wid = str(w.get('id') or '').strip()
    if not wid or wid in ids:
        if wid:
            uyarilar.append('dünya: tekrar eden id ' + wid)
        continue
    ids.add(wid)
    renk = RENK_ES.get(str(w.get('renk') or '').lower(), str(w.get('renk') or '').lower())
    ulke = (w.get('ulke') or '').strip() or 'Bilinmiyor'
    bolge = (w.get('bolge') or '').strip()
    bid = slug(ulke) + '/' + slug(bolge or 'genel')
    DUNYA_BOLGE.setdefault(bid, {'ulke': ulke, 'bolge': bolge})
    uz = [uzum_kaydi(a, renk) for a in (w.get('uzum') or []) if str(a).strip()]
    yerli = [u.get('yerli') for u in uz]
    katman = slug(w.get('katman') or '').replace('-', '')
    usd = w.get('fiyat_usd') or 0
    try:
        usd = round(float(usd))
    except Exception:
        usd = 0
    d = {'id': wid, 'ad': w.get('ad') or wid, 'ure': (w.get('uretici') or '').strip() or 'Üreticisi belirtilmemiş', 'sh': '',
         'ulke': ulke, 'bolge': bid, 'bolgeAd': bolge, 'alt': w.get('alt') or '', 'il': '', 'renk': renk,
         'uzum': [str(a).strip() for a in (w.get('uzum') or []) if str(a).strip()], 'uz': [u['id'] for u in uz],
         'yrl': ('yerli' if all(yerli) else 'dunya' if not any(yerli) else 'karma') if yerli else '',
         'yil': str(w.get('yil') or ''), 'abv': w.get('abv') or 0, 'tat': w.get('tat') or '', 'puan': w.get('puan') or 0,
         'pnot': w.get('puan_not') or '', 'tl': 0, 'tlK': '', 'odul': metin(w.get('odul')), 'usd': usd,
         'bul': 'ithal' if w.get('tr_bulunur') else 'yurtdisi', 'katman': katman if katman in KATMANLAR else '',
         'sinif': metin(w.get('siniflandirma')), 'yillanma': metin(w.get('yillanma')), 'iyi': metin(w.get('iyi_yillar')),
         'kaynak': w.get('kaynak') or []}
    if renk not in RENKLER:
        uyarilar.append(f'{wid}: bilinmeyen renk {w.get("renk")}')
    DATA.append(d)

SEV = seviye_hesapla(DATA)
# Sıra: Türkiye önce, bölge, üretici, ad
TR_SIRA = [b['id'] for b in (oku('bolgeler.json', []) or [])] + ['diger']
DATA.sort(key=lambda d: (d['ulke'] != 'Türkiye', d['ulke'], TR_SIRA.index(d['bolge']) if d['bolge'] in TR_SIRA else 99,
                         d['bolge'], d['ure'], -(d['puan'] or 0), d['ad']))
satirlar, onceki = [], None
for d in DATA:
    d = {k: v for k, v in d.items() if v not in ('', [], None) or k in ('id', 'ad', 'ure', 'ulke', 'bolge', 'renk', 'puan', 'tl', 'bul', 'sev')}
    if (d['ulke'], d['ure']) != onceki:
        satirlar.append('// ===== ' + d['ulke'] + ' · ' + d['ure'] + ' =====')
        onceki = (d['ulke'], d['ure'])
    satirlar.append(json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ',')
blok = 'const DATA = [\n' + '\n'.join(satirlar) + '\n];'
s = open(HTML, encoding='utf-8').read()
i = s.index('const DATA = [')
j = s.index('\n];', i) + 3
s = s[:i] + blok + s[j:]
open(HTML, 'w', encoding='utf-8').write(s)

# ---------- 4. Üzüm listesi (katalog sayılarıyla) ----------
say = collections.Counter(u for d in DATA for u in set(d['uz']))
uz_cikti = []
for u in UZ:
    k = {a: v for a, v in u.items() if a != 'kaynakDosya'}
    k['katalog'] = say.get(u['id'], 0)
    if not k.get('rehber') and not k['katalog']:
        continue
    uz_cikti.append(k)
yaz('uzumler.json', {'_aciklama': 'Üzüm rehberi: rehber=true olanların ayrıntısı araştırma dosyalarından; rehber=false olanlar yalnızca katalogda geçen üzümler.',
                     'uzumler': uz_cikti})

# ---------- 5. Şaraphaneler + harita konumu ----------
kullanilan = collections.Counter()
sh_cikti = []
sarap_say = collections.Counter(d['sh'] for d in DATA if d['sh'])
for m, s_ in SARAPHANE.items():
    tes = []
    for t in s_['tesisler']:
        c = tr_konum(t.get('il'), t.get('ilce'))
        if not c:
            uyarilar.append('konum yok: ' + m + ' ' + str(t.get('il')))
            continue
        n = kullanilan[tuple(c)]
        kullanilan[tuple(c)] += 1
        tes.append({'firma': t.get('firma'), 'il': t.get('il'), 'ilce': t.get('ilce') or '', 'bolge': tr_bolge(t.get('il'), '', t.get('ilce')),
                    'konum': [round(c[0] + 0.035 * (n % 4) - 0.05 * (n // 4), 4), round(c[1] + 0.05 * (n % 4), 4)]})
    sh_cikti.append({'ad': m, 'kurulus': s_.get('kurulus') or '', 'baglar': s_.get('baglar') or '', 'uzumler': s_.get('uzumler') or [],
                     'web': s_.get('web') or '', 'instagram': s_.get('instagram') or '', 'hikaye': s_.get('hikaye') or '',
                     'kaynak': s_['kaynak'], 'tesisler': tes, 'sarap': sarap_say.get(m, 0), 'sev': SEV.get(('Türkiye', m), '0')})
yaz('ureticiler.json', {'_aciklama': 'Şaraphaneler (yalnızca markası bilinen kayıtlar). konum: ilçe ya da il merkezine göre yaklaşık.',
                        'ureticiler': sh_cikti})

# ---------- 5b. Üzüm Haritası / İl İl Bağcılık (uzum-il.json) ----------
ui = oku('uzum-il.json', None)
if isinstance(ui, dict):
    UYG = {'yuksek', 'orta', 'dusuk', 'uygun_degil'}
    iller_c = []
    for il in ui.get('iller') or []:
        yer, goruldu = [], {}
        for y in il.get('yerel_uretici') or []:
            ad = str(y.get('ad') or '').strip()
            if not ad or ad.lower().startswith('bilinen yerel') or 'kayıt bulunmadı' in str(y.get('not') or '').lower() and not y.get('web'):
                continue
            n = norm(ad)
            if n in goruldu:  # aynı markanın birden çok lisanslı firma kaydı tek karta birleşir
                k = goruldu[n]
                k['not'] = (k.get('not', '') + ' | ' + str(y.get('not') or '')).strip(' |')
                k['firma_sayisi'] = k.get('firma_sayisi', 1) + 1
                continue
            k = {'ad': ad, 'not': str(y.get('not') or ''), 'web': y.get('web') or '', 'firma_sayisi': 1}
            sh_ad = saraphane_bul(ad)
            if sh_ad:
                k['sh'] = sh_ad
                k['sarap'] = sarap_say.get(sh_ad, 0)
            goruldu[n] = k
            yer.append(k)
        uzs = []
        for u in il.get('uzumler') or []:
            uyg = u.get('sarap_uygunlugu')
            k = dict(u)
            k['sarap_uygunlugu'] = uyg if uyg in UYG else 'dogrulanmadi'
            rec = uzum_bul(u.get('ad', '')) or uzum_bul(re.split(r'[(/,]', str(u.get('ad', '')))[0].strip())
            if rec and rec.get('rehber'):
                k['uz'] = rec['id']
            uzs.append(k)
        iller_c.append({'id': slug(il.get('il')), 'il': il.get('il'), 'bolge': il.get('bolge') or '', 'bag_notu': il.get('bag_notu') or '',
                        'uzumler': uzs, 'yerel_uretici': yer, 'kaynak': kaynak_temiz(il.get('kaynak'))})
    yaz('uzum-il.json', {'_aciklama': 'İl il bağcılık: her ilin bağ notu, üzümleri (şaraba uygunluk: yuksek/orta/dusuk/uygun_degil/dogrulanmadi) ve yerel üreticiler.',
                         'iller': iller_c, 'diger_uzumler': ui.get('uzum_ek') or [], 'notlar': ui.get('notlar') or {}})
    print(f'uzum-il: {len(iller_c)} il · {sum(len(i["uzumler"]) for i in iller_c)} üzüm kaydı')

# ---------- 6. Resmî lisans listesi ----------
lis = oku('lisans-sarap.json', []) or []
il_say = collections.Counter(x.get('il') for x in lis)
yaz('lisans.json', {
    '_aciklama': 'T.C. Tarım ve Orman Bakanlığı Tütün ve Alkol Dairesi Başkanlığı — Alkollü İçki Üretim İzin Belgesi Sahibi Firmalar listesinden şarap üreticileri.',
    'kaynak': 'https://pdtadb.tarimorman.gov.tr/webUibList.aspx', 'tarih': '2026-10-04',
    'firma_sayisi': len(lis), 'iller': [{'il': k, 'sayi': v} for k, v in sorted(il_say.items(), key=lambda x: (-x[1], x[0]))],
    'kategoriler': dict(collections.Counter(k for x in lis for k in x.get('kategoriler') or [])),
    'arastirilan_kayit': len(ure_ham), 'markasiz_kayit': sum(1 for r in ure_ham if not (r.get('marka') or '').strip()),
    'firmalar': lis})

# ---------- 7. Bölgeler (Türkiye + varsa dünya) ----------
tr_b = oku('bolgeler.json', []) or []
for b in tr_b:
    b['sarap'] = sum(1 for d in DATA if d['bolge'] == b['id'])
diger_iller = sorted({t['il'] for s_ in sh_cikti for t in s_['tesisler'] if t['bolge'] == 'diger'} | {d['il'] for d in DATA if d['bolge'] == 'diger'})
tr_b.append({'id': 'diger', 'ad': 'Diğer bağ alanları', 'diger': True, 'iller': diger_iller,
             'aciklama': '12 ana bölgenin dışında kalan bağlar ve şaraphaneler (Kuzey Ege kıyısı, Güney Marmara, Foça ve benzeri).',
             'sarap': sum(1 for d in DATA if d['bolge'] == 'diger')})
db = oku('dunya-bolgeler.json', None) or {}
if isinstance(db, list):
    db = {'ulkeler': db}
ulkeler = db.get('ulkeler') or []
for u in ulkeler:
    if not isinstance(u, dict):
        continue
    u['id'] = u.get('id') or slug(u.get('ad') or u.get('ulke'))
    uad = u.get('ad') or u.get('ulke') or ''
    u['konum'] = u.get('konum') or ULKE_KONUM.get(re.sub(r'[^a-z ]+', '', unicodedata.normalize('NFD', uad.translate(TRC)).encode('ascii', 'ignore').decode().lower()).strip())
    for b in u.get('bolgeler') or []:
        if isinstance(b, dict):
            bad = b.get('ad') or b.get('bolge') or ''
            b['id'] = slug(uad) + '/' + slug(bad or 'genel')
            b['konum'] = b.get('konum') or dunya_konum(uad, bad)
            b['sarap'] = sum(1 for d in DATA if d['bolge'] == b['id'])
# Katalogdaki dünya bölgeleri (şarapların kendi bölge adı) ↔ rehber bölgeleri: ad/alt ad jetonlarıyla ve elle eşleştirme
GENEL = {'guney', 'kuzey', 'bati', 'dogu', 'vadisi', 'valley', 'western', 'central', 'adalari', 'vadi', 'bolgesi', 'tepeleri', 'eyaleti'}
ALIAS_B = {'sampanya': ['champagne'], 'alsas': ['alsace'], 'guneyrhone': ['rhone'], 'kuzeyrhone': ['rhone'], 'kaliforniya': ['napa', 'sonoma'],
           'guneyavustralya': ['barossa', 'coonawarra'], 'batiavustralya': ['margaret'], 'yenigueygaller': ['hunter'], 'yeniguneygaller': ['hunter'],
           'westerncape': ['stellenbosch'], 'constantia': ['stellenbosch'], 'swartland': ['stellenbosch'], 'minho': ['vinho verde'.replace(' ', '')],
           'egeadalari': ['santorini'], 'makedonya': ['naoussa'], 'morapeloponnisos': ['nemea'], 'katalonya': ['priorat', 'cava'],
           'kastilyaveleon': ['ribera'], 'endulus': ['jerez'], 'burgonya': ['burgonya'], 'beaujolais': ['burgonya']}


def jetonlar(txt):
    t = unicodedata.normalize('NFD', str(txt or '').translate(TRC)).encode('ascii', 'ignore').decode().lower()
    return [w for w in re.split(r'[^a-z0-9]+', t) if len(w) >= 4 and w not in GENEL]


katalog_b = []
for k, v in DUNYA_BOLGE.items():
    kn = norm(v['bolge'])
    anahtarlar = ALIAS_B.get(kn) or ALIAS_B.get(norm(v['bolge'].split('(')[0])) or jetonlar(v['bolge'])
    rehber = []
    for u in ulkeler:
        if not isinstance(u, dict) or norm(u.get('ad') or u.get('ulke')) != norm(v['ulke']):
            continue
        for b in u.get('bolgeler') or []:
            if not isinstance(b, dict):
                continue
            metin_ = norm((b.get('ad') or '') + ' ' + ' '.join(b.get('alt') or []))
            if any(norm(a) in metin_ for a in anahtarlar):
                rehber.append(b['id'])
    katalog_b.append({'id': k, 'ulke': v['ulke'], 'ad': v['bolge'] or v['ulke'], 'konum': dunya_konum(v['ulke'], v['bolge']),
                      'sarap': sum(1 for d in DATA if d['bolge'] == k), 'rehber': rehber})
for u in ulkeler:
    if not isinstance(u, dict):
        continue
    for b in u.get('bolgeler') or []:
        if isinstance(b, dict):
            b['katalog'] = [c['id'] for c in katalog_b if b['id'] in c['rehber']]
            b['sarap'] = sum(c['sarap'] for c in katalog_b if b['id'] in c['rehber'])
ek = katalog_b
yaz('bolgeler.json', {'turkiye': tr_b, 'ulkeler': ulkeler, 'katalog_bolgeleri': ek,
                      'prestij_piramidi': db.get('prestij_piramidi'), 'rekolte_tablosu': db.get('rekolte_tablosu')})

# ---------- 8. Sofra, kültür, topluluk, satış, ödüller, tadım okulu ----------
yaz('yemek.json', {'yemekler': oku('yemek.json', []) or []})
kul = oku('kultur.json', {}) or {}
# Kardeş sitelerin konusu olan içki adları sitede yalnızca kardeş site bağlantısında geçsin: tarihçedeki geçiş nötrleştirilir
kul_json = json.dumps({k: v for k, v in kul.items() if k not in ('topluluk', 'notlar')}, ensure_ascii=False)
kul_json = kul_json.replace('şarap, bira ve bal likörünün (mead)', 'şarap ve diğer mayalı içeceklerin (bal likörü mead dahil)')
yaz('kultur.json', json.loads(kul_json))
yaz('topluluk.json', {'topluluklar': kul.get('topluluk') or []})
sat = oku('satis.json', {'yasal_not': '', 'yerler': []})
sat['yerler'] = [y for y in sat.get('yerler', []) if y.get('tur') in ('zincir', 'duty-free')]
yaz('satis.json', sat)
for ad in ('oduller.json', 'tadim-okulu.json'):
    v = oku(ad, None)
    p = os.path.join(DATA_DIR, ad)
    if v is not None:
        yaz(ad, v)
    elif os.path.exists(p):
        os.remove(p)

# ---------- 9. Fiyatlar (kaynaklı olanlar) ----------
fp = os.path.join(DATA_DIR, 'fiyatlar.json')
fiy = json.load(open(fp, encoding='utf-8')) if os.path.exists(fp) else {'guncelleme': None, 'kur': None, 'fiyatlar': {}, 'denendi': {}, 'inceleme': []}
eklenen = 0
for d in DATA:
    if d['tl'] > 0 and d['tlK'] and d['id'] not in fiy['fiyatlar']:
        fiy['fiyatlar'][d['id']] = {'tl': d['tl'], 'tarih': TARIH, 'tur': 'tr_liste', 'guven': 'orta', 'kaynak': d['tlK'],
                                    'not': 'Ekim 2026 Türkiye perakende, 75 cl', 'gecmis': [[TARIH, d['tl']]]}
        eklenen += 1
fiy['fiyatlar'] = dict(sorted(fiy['fiyatlar'].items()))
fiy['guncelleme'] = fiy.get('guncelleme') or TARIH
yaz('fiyatlar.json', fiy)

for ad, anahtar in (('baglantilar.json', 'baglantilar'), ('gorseller.json', 'gorseller')):
    if not os.path.exists(os.path.join(DATA_DIR, ad)):
        yaz(ad, {anahtar: {}, 'yok': {}})

if uyarilar:
    print('\n'.join('⚠️ ' + h for h in uyarilar[:60]) + ('' if len(uyarilar) <= 60 else f'\n… {len(uyarilar) - 60} uyarı daha'))
for _u, _ad in (('Türkiye', 'Türkiye'), ('dünya', 'dünya')):
    _s = collections.Counter(v for (u, _a), v in SEV.items() if (u == 'Türkiye') == (_ad == 'Türkiye'))
    _w = collections.Counter(d['sev'] for d in DATA if (d['ulke'] == 'Türkiye') == (_ad == 'Türkiye'))
    print(f'seviye {_u}: şaraphane {dict(_s)} · şarap {dict(_w)}')
print(f'{tr_sayi} Türkiye + {len(DATA) - tr_sayi} dünya şarabı · {len(sh_cikti)} şaraphane · {len(uz_cikti)} üzüm '
      f'({sum(1 for u in uz_cikti if u.get("rehber"))} rehberde) · {sum(1 for d in DATA if d["tlK"])} kaynaklı fiyat ({eklenen} yeni) · '
      f'{len(lis)} lisanslı firma · {len(ulkeler)} dünya ülkesi')
