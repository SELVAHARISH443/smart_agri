import os
import glob
import hashlib

def analyze_dataset_dir(dataset_name, out_file):
    base_dir = os.path.join("dataset", dataset_name)
    all_files = glob.glob(os.path.join(base_dir, "**", "*.*"), recursive=True)
    all_files = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    out_file.write(f"=== {dataset_name} detailed check ===\n")
    hashes = {}
    duplicates = 0
    by_class = {}

    for path in all_files:
        rel = os.path.relpath(path, base_dir)
        parts = rel.split(os.sep)
        cls = parts[1] if len(parts) >= 3 else "unknown"
        
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        if file_hash in hashes:
            duplicates += 1
        else:
            hashes[file_hash] = path
            
        if cls not in by_class:
            by_class[cls] = []
        by_class[cls].append((path, file_hash))

    out_file.write(f"Total files: {len(all_files)}, Unique hashes: {len(hashes)}, Duplicates: {duplicates}\n")
    for cls, files in sorted(by_class.items()):
        cls_hashes = set(h for _, h in files)
        out_file.write(f"  Class '{cls}': {len(files)} files, {len(cls_hashes)} unique\n")

with open('tmp/dup_output.txt', 'w', encoding='utf-8') as f_out:
    analyze_dataset_dir("soil", f_out)
    analyze_dataset_dir("crop_disease", f_out)
