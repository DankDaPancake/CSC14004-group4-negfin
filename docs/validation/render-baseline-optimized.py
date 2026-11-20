"""Render paired benchmark tables and lightweight SVGs without third-party packages."""
from collections import defaultdict
import csv
from html import escape
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
COLORS = {
    'light': {'surface': '#fcfcfb', 'ink': '#0b0b0b', 'muted': '#52514e',
              'grid': '#deddd8', 'baseline': '#2a78d6', 'optimized': '#eb6834'},
    'dark': {'surface': '#1a1a19', 'ink': '#f0efec', 'muted': '#c3c2b7',
             'grid': '#43423f', 'baseline': '#3987e5', 'optimized': '#d95926'},
}


def load_runs(source):
    """Load one run directory or recursively merge directories with runs.csv."""
    source = Path(source)
    paths = [source / 'runs.csv'] if (source / 'runs.csv').is_file() else sorted(source.glob('*/runs.csv'))
    if not paths:
        raise FileNotFoundError(f'No runs.csv found under {source}')
    rows = []
    seen = set()
    for path in paths:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                key = tuple(row.get(k, '') for k in
                            ('run_id', 'variant', 'scope', 'dataset', 'fraction', 'minsup', 'emit_mode', 'repetition'))
                if key in seen:
                    raise ValueError(f'duplicate run key: {key}')
                seen.add(key)
                rows.append(row)
    return rows


def aggregate(rows, *, scope, metric):
    groups = defaultdict(list)
    for row in rows:
        if row.get('scope') != scope or row.get('status') != 'ok' or not row.get(metric):
            continue
        value = float(row[metric])
        if value < 0:
            raise ValueError(f'negative {metric}')
        groups[(row['dataset'], row['minsup'], row['fraction'], row['variant'])].append(value)
    return {key: {'median': statistics.median(values), 'min': min(values), 'max': max(values), 'n': len(values)}
            for key, values in groups.items()}


def validate_paired_scale_hashes(rows):
    hashes = {}
    for row in rows:
        if not row.get('scope', '').startswith('scalability-') or row.get('status') != 'ok':
            continue
        key = (row['dataset'], row['minsup'], row['fraction'], row['scope'])
        variant = row['variant']
        digest = row.get('input_sha256', '')
        if key not in hashes:
            hashes[key] = {}
        old = hashes[key].setdefault(variant, digest)
        if old != digest:
            raise ValueError(f'inconsistent subset SHA256 within {key}')
    for key, values in hashes.items():
        if 'baseline' in values and 'optimized' in values and values['baseline'] != values['optimized']:
            raise ValueError(f'subset SHA256 mismatch for {key}: {values}')
    return True


def _svg_scatter(rows, dataset, *, metric, title, unit, theme='light', width=760, height=350, chart_id='chart'):
    if theme not in COLORS:
        raise ValueError('theme must be light or dark')
    palette = COLORS[theme]
    data = defaultdict(list)
    for row in rows:
        if row.get('scope') != 'scalability-cold' or row.get('dataset') != dataset or row.get('status') != 'ok':
            continue
        if not row.get(metric):
            continue
        value = float(row[metric])
        if metric == 'maxrss_bytes':
            value /= 2**20
        data[(row['variant'], float(row['fraction']))].append(value)
    fractions = sorted({fraction for _, fraction in data})
    if not fractions or not {'baseline', 'optimized'} <= {variant for variant, _ in data}:
        raise ValueError(f'missing paired data for {dataset}')
    left, right, top, bottom = 76, width - 22, 54, height - 60
    x = lambda f: left + (right-left) * ((f-min(fractions))/(max(fractions)-min(fractions)) if max(fractions) != min(fractions) else .5)
    maxval = max(max(v) for v in data.values()) * 1.14
    y = lambda value: bottom - (bottom-top) * value/maxval
    x_ticks = ''.join(f'<line x1="{x(f):.1f}" x2="{x(f):.1f}" y1="{top}" y2="{bottom}" stroke="var(--grid)"/><text x="{x(f):.1f}" y="{bottom+22}" text-anchor="middle">{f:.0%}</text>' for f in fractions)
    y_ticks = []
    for i in range(5):
        value = maxval * i / 4
        y_ticks.append(f'<line x1="{left}" x2="{right}" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="var(--grid)"/><text x="{left-10}" y="{y(value)+4:.1f}" text-anchor="end">{value:.0f}</text>')
    marks, legend = [], []
    for index, variant in enumerate(('baseline', 'optimized')):
        color = palette[variant]
        points = []
        for fraction in fractions:
            key = (variant, fraction)
            if key not in data:
                continue
            med = statistics.median(data[key])
            points.append((x(fraction), y(med)))
            label = f'{variant.title()}, {fraction:.0%}, median {med:.3g} {unit}, n={len(data[key])}'
            mark_color = 'var(--base)' if variant == 'baseline' else 'var(--opt)'
            marks.append(f'<circle cx="{x(fraction):.1f}" cy="{y(med):.1f}" r="4.5" fill="{mark_color}" stroke="var(--surface)" stroke-width="2" tabindex="0"><title>{escape(label)}</title></circle>')
        mark_color = 'var(--base)' if variant == 'baseline' else 'var(--opt)'
        marks.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' %
                     (mark_color, ' '.join(f'{px:.1f},{py:.1f}' for px, py in points)))
        legend.append(f'<line x1="{left + index*150}" y1="28" x2="{left+index*150+24}" y2="28" stroke="{mark_color}" stroke-width="3"/><text x="{left+index*150+32}" y="32">{variant.title()}</text>')
    circles = ''.join(marks)
    table_rows = []
    for fraction in fractions:
        for variant in ('baseline', 'optimized'):
            vals = data.get((variant, fraction), [])
            if vals:
                table_rows.append(f'<tr><th scope="row">{variant.title()}</th><td>{fraction:.0%}</td><td>{statistics.median(vals):.4g}</td><td>{len(vals)}</td></tr>')
    return f'''<svg class="plot" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title-{chart_id} desc-{chart_id}"><title id="title-{chart_id}">{escape(title)} — {escape(dataset)}</title><desc id="desc-{chart_id}">Median cold measurements over prefix fractions; hover or keyboard focus a point to see exact median and repetition count. Table follows.</desc><rect width="{width}" height="{height}" rx="12" fill="var(--surface)"/>{''.join(y_ticks)}{x_ticks}{''.join(legend)}<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="var(--muted)"/><line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="var(--muted)"/>{circles}<text x="{(left+right)/2}" y="{height-10}" text-anchor="middle">Prefix fraction</text><text transform="translate(18 {(top+bottom)/2}) rotate(-90)" text-anchor="middle">{escape(unit)}</text></svg><table><caption>{escape(dataset)} — {escape(title)}, median by fraction</caption><thead><tr><th>Variant</th><th>Fraction</th><th>Median</th><th>n</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table>'''


def scalability_svg(rows, theme='light'):
    validate_paired_scale_hashes(rows)
    return (_svg_scatter(rows, 'Accidents', metric='process_wall_seconds', title='Cold wall time', unit='seconds', theme=theme, chart_id='accidents-wall') +
            _svg_scatter(rows, 'Accidents', metric='maxrss_bytes', title='Peak RSS', unit='MiB', theme=theme, chart_id='accidents-rss') +
            _svg_scatter(rows, 'T10I4D100K', metric='process_wall_seconds', title='Cold wall time', unit='seconds', theme=theme, chart_id='t10-wall') +
            _svg_scatter(rows, 'T10I4D100K', metric='maxrss_bytes', title='Peak RSS', unit='MiB', theme=theme, chart_id='t10-rss'))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_root', type=Path, help='parent directory containing per-run folders')
    parser.add_argument('--output', type=Path, default=ROOT / 'figures' / 'baseline-optimized-scalability.html')
    args = parser.parse_args()
    rows = load_runs(args.run_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    body = scalability_svg(rows)
    doc = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Scale comparison</title><meta name="description" content="Cold runtime and peak RSS scalability for Baseline and Optimized on Accidents and T10I4D100K, with medians, interactive point details and table values."><style>
:root{color-scheme:light;--surface:#fcfcfb;--ink:#0b0b0b;--muted:#52514e;--border:#deddd8;--grid:#deddd8;--base:#2a78d6;--opt:#eb6834;font:16px/1.55 system-ui,sans-serif} @media(prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--border:#43423f;--grid:#43423f;--base:#3987e5;--opt:#d95926}}:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--border:#43423f;--grid:#43423f;--base:#3987e5;--opt:#d95926}:root[data-theme="light"]{color-scheme:light;--surface:#fcfcfb;--ink:#0b0b0b;--muted:#52514e;--border:#deddd8;--grid:#deddd8;--base:#2a78d6;--opt:#eb6834}*{box-sizing:border-box}body{margin:0;background:var(--surface);color:var(--ink);font:inherit}main{max-width:1100px;margin:auto;padding:24px 16px 56px}h1{font-size:clamp(1.7rem,4vw,2.6rem);line-height:1.15;margin:.3rem 0}.lede,.note{color:var(--muted);max-width:75ch}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{border:1px solid var(--border);border-radius:12px;padding:16px;background:color-mix(in srgb,var(--surface),var(--ink) 2%)}svg{display:block;width:100%;height:auto;overflow:visible}svg text{font:12px system-ui,sans-serif;fill:var(--ink)}circle{cursor:crosshair}circle:focus{outline:none;stroke:var(--ink);stroke-width:3}table{border-collapse:collapse;width:100%;margin-top:12px;font-size:.92rem}caption{text-align:left;color:var(--muted);padding:6px 0}th,td{text-align:left;padding:6px;border-bottom:1px solid var(--border);font-variant-numeric:tabular-nums}button{font:inherit;background:transparent;color:var(--ink);border:1px solid var(--border);border-radius:8px;padding:6px 10px}@media(max-width:760px){main{padding:20px 16px 40px}.grid{grid-template-columns:1fr}.card{padding:12px}}@media(forced-colors:active){.card{border:1px solid CanvasText}circle{forced-color-adjust:auto}}
</style></head><body><main><header><p class="note">Paired benchmark · 19 November 2026</p><h1>Scalability under load</h1><p class="lede">Cold child-process wall time and peak RSS across prefix fractions. Each point is the median of three runs; keyboard-focus or hover a mark for exact value. Tables provide a non-hover reading path. Subset SHA256 equality is checked before rendering.</p><button type="button" id="theme" aria-label="Toggle color theme">Toggle light/dark theme</button></header><section class="grid">__CHARTS__</section><p class="note">Peak RSS includes the Julia child runtime. Warm mining and output counts are summarized separately in the report. Cold wall includes startup, JIT and I/O.</p></main><script>document.getElementById('theme').addEventListener('click',()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark'});</script></body></html>'''.replace('__CHARTS__', ''.join(f'<article class="card">{chart}</table></article>' for chart in body.split('</table>')[:-1]))
    args.output.write_text(doc, encoding='utf-8')
    print(args.output)

if __name__ == '__main__':
    main()
