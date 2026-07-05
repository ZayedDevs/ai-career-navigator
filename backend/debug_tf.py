import joblib
import re

# Load skill database
db = joblib.load("ml/saved_models/skill_database.pkl")
alias_map = db["alias_map"]
canonical_skills = db["canonical_skills"]

# Show what maps to tensorflow
print("Aliases that map TO tensorflow:")
for alias, canonical in alias_map.items():
    if canonical == "tensorflow":
        print(f"  '{alias}' -> 'tensorflow'")

# Now load Zayed's resume text
from app.services.resume_parser import parse_resume
result = parse_resume(r"C:\Users\iremi\Desktop\ZAYED_KHALED_RESUME2026.pdf")
text = result["text"].lower()

# Check which alias triggered
print("\nChecking what was found in resume:")
for alias, canonical in alias_map.items():
    if canonical == "tensorflow":
        escaped = re.escape(alias)
        pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
        if re.search(pattern, " " + text + " "):
            print(f"  Found alias '{alias}' in text!")
            # Show context
            for match in re.finditer(pattern, text):
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                print(f"    Context: ...{text[start:end]}...")

# Also check if "tensorflow" itself appears
if "tensorflow" in text:
    print("'tensorflow' IS in the text")
    idx = text.find("tensorflow")
    print(f"  Context: ...{text[max(0,idx-50):idx+60]}...")
else:
    print("'tensorflow' is NOT in the text directly")

# Check 'tf' alias
if " tf " in " " + text + " ":
    print("\n'tf' standalone IS in the text")
