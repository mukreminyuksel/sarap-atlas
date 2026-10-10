#!/usr/bin/env python3
"""Kapsam denetimi: her lisanslı/kayıtlı üretici için katalogdaki şarap sayısı.
Kullanım: python3 scripts/kapsam.py [esik]   (varsayılan eşik 2: bu sayı ve altındakiler listelenir)
Yeni veri turundan önce ve sonra çalıştır; az kayıtlı üreticilerin resmî portföyüne bak."""
import json, glob, sys, collections, os
kok = os.path.join(os.path.dirname(__file__), '..', 'arastirma')
esik = int(sys.argv[1]) if len(sys.argv) > 1 else 2
W = []
for f in glob.glob(os.path.join(kok, 'saraplar-*.json')):
    W += json.load(open(f, encoding='utf-8'))
say = collections.Counter(w.get('uretici') for w in W)
U = []
for f in glob.glob(os.path.join(kok, 'ureticiler-*.json')):
    U += json.load(open(f, encoding='utf-8'))
satir = []
for u in U:
    m = u.get('marka') or u['firma']
    n = say.get(m, 0) or sum(v for k, v in say.items() if k and (k.lower() in m.lower() or m.lower().split(' ')[0] in k.lower()))
    satir.append((n, m, u.get('il', ''), u.get('web', '')))
satir.sort()
az = [s for s in satir if s[0] <= esik]
print(f'Toplam şarap: {len(W)} · üretici: {len(U)} · {esik} ve altı kayıtlı: {len(az)}')
for n, m, il, web in az:
    print(f'{n:3}  {m}  ({il}) {web}')
