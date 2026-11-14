#!/usr/bin/env python3
"""Copy an export of the artifact's database into docs/data so the website shows the same content.

usage: python3 tools/sync.py <export_dir>
<export_dir> holds one folder per collection (editions, images, depeches, histoire, catalogue, textes,
and optionally musee, salles), each with <doc_id>.json files as written by the ArtifactData tool.
Collections that are absent from the export are left untouched in docs/data.
"""
import json, pathlib, shutil, sys
root = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1]); data = root / "docs" / "data"
(data / "textes").mkdir(parents=True, exist_ok=True); (data / "salles").mkdir(parents=True, exist_ok=True)
def docs(name):
    d = src / name
    return sorted(d.glob("*.json")) if d.is_dir() else []
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def dump(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
report = []
eds = [p for p in docs("editions")]
if eds:
    latest = load(eds[-1]); dump(data / "edition.json", latest); dump(root / "edition.json", latest)
    report.append(f"edition {latest.get('date')} no {latest.get('numero')}")
    img = src / "images" / f"{latest.get('date')}.json"
    if img.exists():
        dump(data / "image.json", load(img)); dump(root / "image.json", load(img)); report.append("image of the day")
dep = docs("depeches")
if dep: d = load(dep[-1]); dump(data / "depeches.json", d); report.append(f"depeches {d.get('date')} ({len(d.get('items', []))} items)")
his = docs("histoire")
if his:
    d = load(his[-1]); dump(data / "histoire.json", d); report.append(f"histoire {d.get('date')}")
    img = src / "images" / f"{d.get('date')}-h.json"
    if img.exists(): dump(data / "image-h.json", load(img))
    elif (data / "image-h.json").exists(): (data / "image-h.json").unlink()
cats = docs("catalogue")
if cats:
    items = []
    for p in cats: items += load(p).get("items", [])
    dump(data / "catalogue.json", {"items": items}); report.append(f"catalogue {len(items)} texts")
n = 0
for p in docs("textes"):
    t = data / "textes" / p.name
    if not t.exists() or t.stat().st_size != p.stat().st_size: shutil.copy(p, t); n += 1
if n: report.append(f"{n} texts copied")
mus = docs("musee")
if mus: dump(data / "musee.json", sorted((load(p) for p in mus), key=lambda x: x.get("ordre", 0))); report.append(f"musee {len(mus)} rooms")
for p in docs("salles"): shutil.copy(p, data / "salles" / p.name)
missing = []
cat = data / "catalogue.json"
if cat.exists():
    for i in load(cat)["items"]:
        if not (data / "textes" / f"{i['id']}.json").exists(): missing.append(i["id"])
print("synced:", "; ".join(report) or "nothing")
print("texts in the catalogue but not yet exported:", ", ".join(missing) if missing else "none")
