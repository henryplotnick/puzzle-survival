"""Adds the game-order index to an existing build: m/<move>/<page>.bin and m/index.json.
Positions must match build_data.py exactly, so this repeats its ranking and chunk numbering."""
import sys, io, csv, os, json, gzip, shutil, random
from array import array
import zstandard, numpy as np
src, out = sys.argv[1], sys.argv[2]
CH, PAGE = 512, 4096
def rows():
    with open(src,'rb') as f:
        rd = csv.reader(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(f), encoding='utf-8'))
        next(rd)
        for row in rd: yield row
rat = array('H')
for row in rows(): rat.append(int(row[3]))
r = np.frombuffer(rat, dtype=np.uint16); n = len(r)
order = np.argsort(r, kind='stable'); rank = np.empty(n, dtype=np.uint32); rank[order] = np.arange(n, dtype=np.uint32)
del order
cnt = [0]*((n + CH - 1)//CH)
G = np.empty(n, dtype=np.uint32); MV = np.empty(n, dtype=np.uint16); samples = []
for i, row in enumerate(rows()):
    c = int(rank[i]) // CH; k = cnt[c]; cnt[c] = k + 1
    G[i] = c*CH + k
    p = row[1].split(' ')
    MV[i] = int(p[5]) + (1 if p[1] == 'b' else 0)   # move number on which the solver plays
    if random.random() < 0.0004: samples.append((int(G[i]), row[0]))
# check a sample of positions against the chunk files already built
bad = 0
for g, pid in samples:
    c = g // CH
    lines = gzip.decompress(open('%s/c/%02d/%d.gz' % (out, c % 100, c),'rb').read()).decode().split('\n')
    if not lines[g % CH].startswith(pid + '|'): bad += 1
print('position check', len(samples), 'bad', bad, flush=True); assert bad == 0
if os.path.exists(out + '/m'): shutil.rmtree(out + '/m')
counts = {}; tot = 0; files = 0
for m in np.unique(MV).tolist():
    sel = np.nonzero(MV == m)[0]
    o = sel[np.lexsort((G[sel], r[sel]))]           # easier first, ties by position
    arr = G[o].astype('<u4'); counts[m] = int(len(arr))
    d = '%s/m/%d' % (out, m); os.makedirs(d)
    for pg in range(0, len(arr), PAGE):
        b = arr[pg:pg+PAGE].tobytes(); tot += len(b); files += 1
        open('%s/%d.bin' % (d, pg // PAGE), 'wb').write(b)
json.dump({'min':min(counts), 'max':max(counts), 'page':PAGE, 'counts':counts}, open(out + '/m/index.json','w'), separators=(',',':'))
print('moves', len(counts), 'files', files, 'bytes', tot)
