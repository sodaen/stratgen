import os, re, shutil, sys
BASE = "CHANGELOG.md"
LIMIT = 10 * 1024 * 1024  # 10 MB

def next_suffix():
    files = [f for f in os.listdir(".") if re.fullmatch(r"CHANGELOG\.(\d{3})\.md", f)]
    nums = sorted(int(re.search(r"(\d{3})", f).group(1)) for f in files) if files else []
    n = (nums[-1] + 1) if nums else 1
    return f"CHANGELOG.{n:03d}.md"

def rotate_if_needed():
    if not os.path.exists(BASE):
        print({"ok": True, "rotated": False, "reason": "missing"})
        return
    size = os.path.getsize(BASE)
    if size <= LIMIT:
        print({"ok": True, "rotated": False, "size": size})
        return
    dst = next_suffix()
    shutil.move(BASE, dst)
    with open(BASE, "w", encoding="utf-8") as f:
        f.write("# CHANGELOG (fortgesetzt)\n\n")
        f.write(f"_Vorherige Datei rotiert nach **{dst}** am Größenlimit von 10 MB._\n\n")
    print({"ok": True, "rotated": True, "archived": dst, "new_base": BASE})

if __name__ == "__main__":
    rotate_if_needed()
