from pathlib import Path
import csv, html
out=Path('results/stage2')
rows=list(csv.DictReader((out/'summary_metrics.csv').open()))

def svg_bar(metric, fname, title, scale_to_one=False):
    variants=[r['variant'] for r in rows]
    vals=[float(r[metric]) for r in rows]
    maxv=1.0 if scale_to_one else max(vals) if max(vals)>0 else 1.0
    W,H=900,420; left=70; bottom=330; top=40; barw=90; gap=35
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{W/2}" y="24" text-anchor="middle" font-family="sans-serif" font-size="18">{html.escape(title)}</text>',
           f'<line x1="{left}" y1="{bottom}" x2="{W-30}" y2="{bottom}" stroke="black"/>',
           f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="black"/>']
    for i,(v,val) in enumerate(zip(variants,vals)):
        x=left+25+i*(barw+gap)
        h=(bottom-top)*val/maxv
        y=bottom-h
        parts.append(f'<rect x="{x}" y="{y:.2f}" width="{barw}" height="{h:.2f}" fill="#777"/>')
        parts.append(f'<text x="{x+barw/2}" y="{y-6:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12">{val:.3g}</text>')
        parts.append(f'<text x="{x+barw/2}" y="{bottom+18}" text-anchor="end" font-family="sans-serif" font-size="11" transform="rotate(-35 {x+barw/2} {bottom+18})">{html.escape(v)}</text>')
    parts.append('</svg>')
    (out/fname).write_text('\n'.join(parts), encoding='utf-8')

svg_bar('exact_recovery_rate','exact_recovery_rate.svg','Exact recovery rate',True)
svg_bar('final_preservation_rate','preservation_rate.svg','Final preservation rate',True)
svg_bar('mean_candidate_evals','candidate_evals.svg','Mean candidate evaluations',False)
