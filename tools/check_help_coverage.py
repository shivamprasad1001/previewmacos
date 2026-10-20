import os
import json
import re

def verify_coverage():
    # 1. Load help dictionary
    with open("preview/data/help_data.json", "r", encoding="utf-8") as f:
        help_data = json.load(f)

    dict_items = help_data.get("dictionary", [])
    dict_names = {item["name"].lower(): item for item in dict_items}
    dict_actions = {item.get("action_id"): item for item in dict_items if item.get("action_id")}

    print(f"Total Help Dictionary entries: {len(dict_items)}")

    # 2. Extract menus and actions from main_window.py
    with open("preview/ui/main_window.py", "r", encoding="utf-8") as f:
        main_code = f.read()

    action_names = re.findall(r'QAction\("([^"]+)"', main_code)
    # Strip accelerators like "...", shortcuts, etc.
    cleaned_actions = set()
    for act in action_names:
        clean = act.replace("...", "").strip()
        if clean and not clean.startswith("&"):
            cleaned_actions.add(clean)

    print(f"Found {len(cleaned_actions)} distinct UI actions in main_window.py")

    # 3. Check writing rules for all dictionary entries
    # Rule 1: Sentences under 20 words
    violations = []
    for item in dict_items:
        # Check meaning
        for sent in re.split(r'[.!?]', item["meaning"]):
            words = sent.strip().split()
            if len(words) > 20:
                violations.append((item["name"], "meaning", sent.strip(), len(words)))
        # Check steps
        for step in item["steps"]:
            for sent in re.split(r'[.!?]', step):
                words = sent.strip().split()
                if len(words) > 20:
                    violations.append((item["name"], "step", sent.strip(), len(words)))

    if violations:
        print(f"WARNING: {len(violations)} writing rule violations found (sentences > 20 words):")
        for v in violations[:5]:
            print(f"  {v[0]} [{v[1]}]: '{v[2]}' ({v[3]} words)")
    else:
        print("ALL Help Dictionary sentences comply with the <= 20 words writing rule!")

    # 4. Check that image guide and PDF assets exist
    for guide in help_data.get("image_guide", []):
        img_l = os.path.join("preview/assets/help", guide["image_light"])
        img_d = os.path.join("preview/assets/help", guide["image_dark"])
        assert os.path.exists(img_l), f"Missing {img_l}"
        assert os.path.exists(img_d), f"Missing {img_d}"

    assert os.path.exists("preview/data/preview_macos_user_guide.pdf"), "Missing user guide PDF"
    assert os.path.exists("preview/data/preview_macos_cheatsheet.pdf"), "Missing cheatsheet PDF"

    print("ALL Image Guide screenshots (light + dark) and PDF downloads verified present!")
    return True

if __name__ == "__main__":
    verify_coverage()
