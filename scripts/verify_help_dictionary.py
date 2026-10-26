#!/usr/bin/env python3
"""
Compares menu actions, toolbar tools, and dialog features in the codebase against
help/content/dictionary.json and verifies completeness (100% coverage).
"""

import json
import re
import sys
import os

def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def extract_actions_from_main_window():
    actions = set()
    mw_path = "preview/ui/main_window.py"
    if not os.path.exists(mw_path):
        return actions

    with open(mw_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match QAction("Name", ...)
    matches = re.findall(r'QAction\s*\(\s*["\']([^"\']+)["\']', content)
    for m in matches:
        clean = m.replace("...", "").replace("&", "").strip()
        if clean and not clean.startswith("No Recent"):
            actions.add(clean)
            
    # Match toolbar buttons
    tb_matches = re.findall(r'setToolTip\s*\(\s*["\']([^"\']+)["\']', content)
    for m in tb_matches:
        # e.g. "Toggle Sidebar (Ctrl+B) - Learn more (F1)" -> "Toggle Sidebar"
        cleaned = re.sub(r'\s*-\s*Learn more.*', '', m, flags=re.IGNORECASE)
        base = re.sub(r'\s*\([^)]*\)', '', cleaned).strip()
        if base:
            actions.add(base)
            
    return actions

def extract_actions_from_markup_toolbar():
    actions = set()
    mt_path = "preview/ui/markup_toolbar.py"
    if not os.path.exists(mt_path):
        return actions

    with open(mt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tool buttons created with _create_tool_button
    matches = re.findall(r'_create_tool_button\s*\(\s*["\'][^"\']+["\']\s*,\s*["\']([^"\']+)["\']', content)
    for m in matches:
        cleaned = re.sub(r'\s*-\s*Learn more.*', '', m, flags=re.IGNORECASE)
        base = re.sub(r'\s*\([^)]*\)', '', cleaned).strip()
        actions.add(base)

    # QAction names
    qa_matches = re.findall(r'QAction\s*\(\s*["\']([^"\']+)["\']', content)
    for m in qa_matches:
        actions.add(m.strip())

    # Tooltips
    tt_matches = re.findall(r'setToolTip\s*\(\s*["\']([^"\']+)["\']', content)
    for m in tt_matches:
        cleaned = re.sub(r'\s*-\s*Learn more.*', '', m, flags=re.IGNORECASE)
        base = re.sub(r'\s*\([^)]*\)', '', cleaned).strip()
        if base and "Active" not in base:
            actions.add(base)

    return actions

def extract_actions_from_sidebar():
    actions = set()
    sb_path = "preview/ui/mac_sidebar.py"
    if not os.path.exists(sb_path):
        return actions

    with open(sb_path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.findall(r'QAction\s*\(\s*["\']([^"\']+)["\']', content)
    for m in matches:
        clean = m.replace("...", "").strip()
        actions.add(clean)
    return actions

def main():
    dict_path = "help/content/dictionary.json"
    if not os.path.exists(dict_path):
        print(f"Error: Dictionary not found at {dict_path}")
        sys.exit(1)

    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dict_entries = data.get("entries", [])
    dict_names = {normalize(e["name"]) for e in dict_entries}
    dict_ids = {normalize(e["id"]) for e in dict_entries}

    code_actions = set()
    code_actions.update(extract_actions_from_main_window())
    code_actions.update(extract_actions_from_markup_toolbar())
    code_actions.update(extract_actions_from_sidebar())

    # Filter out dynamic items or common small words
    ignored = {"", "dones", "show colors", "no recent documents"}
    
    missing = []
    matched = 0

    # Common synonym mapping for menu/tool names
    aliases = {
        "previouspageimage": "previouspageimage",
        "nextpageimage": "nextpageimage",
        "firstpageimage": "firstpageimage",
        "lastpageimage": "lastpageimage",
        "rotateright": "rotateright",
        "rotateleft": "rotateleft",
        "rotateselection": "rotateselection",
        "markup": "markuptoolbar",
        "showhidemarkuptoolbar": "markuptoolbar",
        "showmarkuptoolbar": "markuptoolbar",
        "togglesidebar": "sidebar",
        "showmagnifierloupe": "loupemagnifier",
        "magnifier": "loupemagnifier",
        "hidemagnifier": "loupemagnifier",
        "zoomtofit": "zoomtofit",
        "actualsize": "actualsize",
        "zoommaximize": "zoommaximize",
        "minimize": "minimizewindow",
        "previewhelp": "helpwindow",
        "keyboardshortcutsguide": "keyboardshortcutsguide",
        "checkforupdates": "checkforupdates",
        "aboutdocumentviewer": "aboutdocumentviewer",
        "quitdocumentviewer": "quitdocumentviewer",
        "hidewindow": "closewindow",
        "closewindow": "closewindow",
        "save": "save",
        "savechanges": "savechangesprompt",
        "revertooriginal": "reverttooriginal",
        "exportaspdf": "exportaspdf",
        "export": "exportdialog",
        "mergepdfs": "mergepdfs",
        "splitpdfextractpages": "splitpdfextractpages",
        "setpdfpasswordencryption": "passwordandencryption",
        "print": "print",
        "printpreview": "printpreview",
        "undo": "undo",
        "redo": "redo",
        "copytext": "copytext",
        "copyselection": "copytext",
        "copypagetext": "copytext",
        "extractalltexttofile": "extractalltext",
        "insertblankpage": "insertblankpage",
        "insertblankpageafter": "insertblankpage",
        "insertpagefromfile": "insertpagefromfile",
        "applyallredactions": "applyallredactions",
        "applyredactions": "applyallredactions",
        "singlepage": "singlepageview",
        "twopagescontinuous": "twopagescontinuousview",
        "twopagescontinuoustwoup": "twopagescontinuousview",
        "slideshowmode": "slideshowmode",
        "framelesswindowmode": "framelesswindowmode",
        "gotopage": "gotopage",
        "crop": "cropselection",
        "cropselection": "cropselection",
        "adjustcolor": "adjustcolor",
        "adjustsize": "adjustsize",
        "showinspector": "inspector",
        "inspector": "inspector",
        "toggledarklighttheme": "darklightthemetoggle",
        "autosystemdefault": "darklightthemetoggle",
        "preferences": "preferences",
        "open": "openfile",
        "openfile": "openfile",
        "openfiles": "openfile",
        "openfolderofimages": "openfolderimages",
        "openfolder": "openfolderimages",
        "clearmenu": "clearrecentmenu",
        "pointerselect": "pointerselecttool",
        "sketchpen": "pentool",
        "highlighter": "highlightertool",
        "textbox": "textboxtool",
        "stickynote": "stickynotetool",
        "redactblackoutinfo": "redactiontool",
        "signdocument": "signaturetool",
        "signatures": "signaturetool",
        "rectanglularselection": "rectangularselection",
        "rectangularselection": "rectangularselection",
        "ovalellipticalselection": "ovalselection",
        "ovalselection": "ovalselection",
        "lassoselection": "lassoselection",
        "rectangle": "rectangleshape",
        "roundedrectangle": "roundedrectangleshape",
        "ovalcircle": "ellipseovalshape",
        "line": "linetool",
        "arrow": "arrowtool",
        "thumbnails": "thumbnailsview",
        "contactsheet": "contactsheetview",
        "tableofcontents": "tableofcontentsview",
        "deletepage": "deletepage",
        "duplicatepage": "duplicatepage"
    }

    for action in sorted(code_actions):
        norm = normalize(action)
        if norm in ignored or len(norm) <= 2:
            continue
        
        target = aliases.get(norm, norm)
        if target in dict_names or target in dict_ids or any(target in dn for dn in dict_names):
            matched += 1
        else:
            missing.append(action)

    print(f"Total Code Features Audited: {len(code_actions)}")
    print(f"Matched Dictionary Entries: {matched}")
    print(f"Dictionary Total Coverage: {len(dict_entries)} entries in dictionary.json")
    
    if missing:
        print("\nMissing Entries Found in Codebase:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print("\nAll menu actions and toolbar tools are 100% documented in the Help Dictionary!")
        sys.exit(0)

if __name__ == "__main__":
    main()
