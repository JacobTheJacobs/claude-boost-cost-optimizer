"""Pass/fail per task, run inside a finished work dir."""
import json, re, subprocess, sys
from pathlib import Path
task, d = sys.argv[1], Path(sys.argv[2])
def py(code):
    return subprocess.run([sys.executable, "-c", code], cwd=d, capture_output=True).returncode == 0
ok = False
if task == "bugfix":
    ok = py("from shop.money import parse_price as p; assert p('$1,234.50')==1234.5 and p('12.99')==12.99 and p('$7')==7.0")
elif task == "feature":
    ok = py("from shop.stats import top_n; it=[{'price':1,'qty':5},{'price':10,'qty':1},{'price':3,'qty':3}]; assert top_n(it,2)==[it[1],it[2]] and top_n(it,0)==[]")
elif task == "lookup":
    a = (d / "ANSWER.txt").read_text() if (d / "ANSWER.txt").exists() else ""
    ok = bool(re.search(r"shop/audit\.py:1[45]\b", a)) and "record" in a
elif task == "logcount":
    a = (d / "ANSWER.txt").read_text().strip() if (d / "ANSWER.txt").exists() else ""
    ok = a == str(json.load(open(Path(__file__).parent / "expected.json"))["timeouts"])
elif task == "helpers":
    a = (d / "ANSWER.txt").read_text().strip() if (d / "ANSWER.txt").exists() else ""
    ok = a == str(json.load(open(Path(__file__).parent / "expected.json"))["helpers"])
elif task == "logbreakdown":
    try:
        ok = json.loads((d / "ANSWER.json").read_text()) == json.load(open(Path(__file__).parent / "expected.json"))["breakdown"]
    except (OSError, ValueError):
        ok = False
elif task in ("warncount", "modcount", "whereis", "diskfull"):
    a = (d / "ANSWER.txt").read_text().strip() if (d / "ANSWER.txt").exists() else ""
    exp = json.load(open(Path(__file__).parent / "expected.json"))
    a = a.removeprefix("./")
    ok = a == {"warncount": str(exp["warn"]), "modcount": "25", "whereis": "shop/mod09.py", "diskfull": str(exp["diskfull"])}[task]
print(json.dumps({"pass": ok}))
