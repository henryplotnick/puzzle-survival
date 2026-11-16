import sys, io, csv, os, gzip, json, shutil
from array import array
import zstandard, numpy as np
src, out = sys.argv[1], sys.argv[2]
CH, BS = 512, 25
def rows():
    with open(src,'rb') as f:
        rd = csv.reader(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(f), encoding='utf-8'))
        next(rd)
        for row in rd: yield row
# pass 1: ratings -> rank of every row (stable sort by rating)
rat = array('H')
for row in rows(): rat.append(int(row[3]))
r = np.frombuffer(rat, dtype=np.uint16); n = len(r)
order = np.argsort(r, kind='stable'); rank = np.empty(n, dtype=np.uint32); rank[order] = np.arange(n, dtype=np.uint32)
bmin, bmax = int(r.min())//BS, int(r.max())//BS; nb = bmax - bmin + 1
sr = r[order]; bandStart = [int(np.searchsorted(sr, (bmin+b)*BS, side='left')) for b in range(nb)] + [n]
del order, sr
print('rows', n, 'rating', int(r.min()), int(r.max()), 'bands', nb, flush=True)
# pass 2: fill chunks, build theme index
nch = (n + CH - 1)//CH
bufs = [bytearray() for _ in range(nch)]; cnt = [0]*nch
idx = {}
SKIP = set()
for i, row in enumerate(rows()):
    c = int(rank[i]) // CH; k = cnt[c]; cnt[c] = k + 1
    fen = ' '.join(row[1].split(' ')[:4])
    bufs[c] += (row[0] + '|' + fen + '|' + row[2] + '|' + row[3] + '\n').encode()
    g = c*CH + k; b = int(row[3])//BS - bmin
    for t in row[7].split():
        a = idx.get((t,b))
        if a is None: a = idx[(t,b)] = array('I')
        a.append(g)
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out + '/c'); os.makedirs(out + '/i')
tot = 0
for c in range(nch):
    d = out + '/c/%02d' % (c % 100); os.makedirs(d, exist_ok=True)
    data = gzip.compress(bytes(bufs[c][:-1]), 9, mtime=0); tot += len(data)
    open('%s/%d.gz' % (d, c), 'wb').write(data)
print('chunks', nch, 'bytes', tot, flush=True)
themes = sorted({t for t,_ in idx}); counts = {t:[0]*nb for t in themes}; itot = 0
def varint(a):
    a = np.sort(np.frombuffer(a, dtype=np.uint32)); d = np.diff(a, prepend=np.uint32(0)).tolist(); o = bytearray()
    for v in d:
        while v >= 128: o.append((v & 127) | 128); v >>= 7
        o.append(v)
    return bytes(o)
for (t,b), a in idx.items():
    counts[t][b] = len(a); d = out + '/i/' + t; os.makedirs(d, exist_ok=True)
    data = varint(a); itot += len(data); open('%s/%d.bin' % (d, b), 'wb').write(data)
print('index files', len(idx), 'bytes', itot, flush=True)
json.dump({'n':n,'chunk':CH,'bandSize':BS,'bandMin':bmin,'bandStart':bandStart,'themes':themes,'counts':counts,'date':sys.argv[3]}, open(out+'/manifest.json','w'), separators=(',',':'))
print({t:sum(counts[t]) for t in themes})
