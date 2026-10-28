import os
import glob
import json

summary = {}
for d in ['soil', 'crop_disease']:
    base = os.path.join('dataset', d)
    summary[d] = {}
    all_files = [f for f in glob.glob(os.path.join(base, '**', '*.*'), recursive=True) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    for f in all_files:
        rel = os.path.relpath(f, base)
        parts = rel.split(os.sep)
        if len(parts) >= 3:
            split, cls = parts[0], parts[1]
            if cls not in summary[d]:
                summary[d][cls] = {'total': 0, 'splits': {}}
            summary[d][cls]['total'] += 1
            summary[d][cls]['splits'][split] = summary[d][cls]['splits'].get(split, 0) + 1

with open('tmp/summary.txt', 'w', encoding='utf-8') as f_out:
    for d, classes in summary.items():
        f_out.write(f"=== {d.upper()} DATASET ===\n")
        for cls, info in sorted(classes.items()):
            f_out.write(f"{cls:25s} | Total: {info['total']:3d} | Splits: {info['splits']}\n")
