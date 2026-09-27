"""Compare the Pyodide builds recorded in pyodide-result.txt with CPython builds of the same samples."""
import json, hashlib, sys, pathlib, time
txt = open('pyodide-result.txt').read()
res = json.loads(txt[txt.index('{'):txt.rindex('console:')])
sys.path.insert(0, 'builder')
import build_exam
same = diff = 0
for name, info in res['result']['builds'].items():
    t = time.perf_counter()
    written = build_exam.build(pathlib.Path('samples') / name, pathlib.Path('cpython-out') / name[:-8])
    ms = round((time.perf_counter() - t) * 1000)
    for p in written:
        if info['files'][p.name][1] == hashlib.sha256(p.read_bytes()).hexdigest(): same += 1
        else: diff += 1; print("DIFF", p.name)
    print(name, "pyodide ms", info['ms'], "cpython ms", ms)
print("identical files:", same, "different:", diff)
