import json, statistics as st
from ic import by, dates, ics, summ, target
from combo import z, comp_ic
W = {'sur_sales': .22, 'ins_sellers_np': -.16, 'ey': .16, 'ev_sell': -.10, 'ev_neg30': .08, 'rev_eps4': -.08, 'ev_r': -.08, 'sur_eps': .06, 'vol12': -.06}
def spread(w, h, ds, q=5):
    out = []
    for d in ds:
        rows = by[d]; y = target(rows, h, 'universe'); Z = {s: z(rows, s) for s in w}
        sc = [(sum(w[s] * Z[s][i] for s in w), y[i]) for i in range(len(rows)) if y[i] is not None]
        sc.sort(); n = len(sc) // q
        out.append(st.mean(b for a, b in sc[-n:]) - st.mean(b for a, b in sc[:n]))
    return st.mean(out), sum(1 for x in out if x > 0) / len(out)
if __name__ == '__main__':
    for h, ov in (('f4b', 4), ('f12b', 12)):
        ds = [d for d in dates if any(r[h] is not None for r in by[d])]
        for nm, w in (('NEW', W), ('CURRENT', {'ev_comp': 1})):
            a = summ(comp_ic(w, h, 'universe', ds), ov); s = summ(comp_ic(w, h, 'sector', ds), ov)
            hh = [summ(comp_ic(w, h, 'universe', p), ov) for p in (ds[:len(ds)//2], ds[len(ds)//2:])]
            sp, hit = spread(w, h, ds)
            print(f"{h} {nm:8s} IC {a['ic']:+.3f} (t {a['t']:+.1f}, hit {a['hit']:.0%}) | sector-rel {s['ic']:+.3f} | halves {hh[0]['ic']:+.3f} / {hh[1]['ic']:+.3f} | top-minus-bottom quintile {sp*100:+.1f}% per period, positive {hit:.0%}")
