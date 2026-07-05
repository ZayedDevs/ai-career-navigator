import sys
sys.path.insert(0, ".")
from app.services.resume_parser import parse_resume

files = [
    r"C:\Users\iremi\Desktop\ZAYED_KHALED_RESUME2026.pdf",
    r"C:\Users\iremi\Desktop\Yaseen-Mohamed-FlowCV-Resume-20251203.pdf",
]

for f in files:
    print("\n" + "=" * 78)
    print(f"FILE: {f}")
    print("=" * 78)
    result = parse_resume(f)
    if result["success"]:
        print(result["text"])
    else:
        print(f"ERROR: {result['error']}")
