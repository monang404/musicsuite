import os

with open("main.py", encoding="utf-8") as f:
    main_content = f.read()

with open("ui/screens/download_screen.py", encoding="utf-8") as f:
    ds_content = f.read()

print("=== main.py checks ===")
proc_route = 'register_screen("PROCESS"' in main_content
print("PROCESS route still registered:", proc_route)

queue_sidebar = '"Queue"' in main_content
print("Queue sidebar label still present:", queue_sidebar)

dl_route = 'register_screen("DOWNLOAD"' in main_content
print("DOWNLOAD route registered:", dl_route)

print()
print("=== download_screen.py hardcoded colors ===")
hardcoded = [l.strip() for l in ds_content.splitlines() if "#4CAF50" in l or "#EF4444" in l]
if hardcoded:
    for h in hardcoded:
        print("  FOUND:", h)
else:
    print("  None found (or only in _show_completed/_show_failed state methods)")

print()
print("=== ui/screens/ new files ===")
known = {
    "__init__.py", "base_screen.py", "compilation_inspector_screen.py",
    "download_screen.py", "playlist_inspector_screen.py", "process_screen.py",
    "queue_screen.py", "results_center_screen.py", "results_screen.py", "search_screen.py"
}
unexpected = []
for f in os.listdir("ui/screens"):
    if f not in known and not f.endswith(".pyc") and f != "__pycache__":
        unexpected.append(f)

if unexpected:
    for f in unexpected:
        print("  UNEXPECTED:", f)
else:
    print("  No unexpected files found.")

print()
print("=== Summary ===")
print("[OK] ProcessScreen not a route:" , not proc_route)
print("[OK] Queue not in sidebar:", not queue_sidebar)
print("[OK] DOWNLOAD route exists:", dl_route)
print("[OK] No unexpected new files:", not unexpected)
