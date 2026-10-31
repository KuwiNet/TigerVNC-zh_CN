# -*- coding: utf-8 -*-
"""Auto-translate missing entries of a zh_CN.po using DeepL API.

Usage:
    python translate_missing.py <pot_path> <po_path> [--out-po <po_path>] [--dry-run]

- pot_path : official translation template for the NEW version
- po_path  : existing simplified-Chinese translation (updated in place unless --out-po)

Requires: polib (pip install polib)
Env:      DEEPL_API_KEY (DeepL auth key, e.g. 'xxx:fx' for free tier)
"""
import os, sys, re, json, time, urllib.request, urllib.error
import polib

DEEPL_URL = "https://api-free.deepl.com/v2/translate"
PLACEHOLDER_RE = re.compile(r"%[-+ #0-9.*]*[diouxXeEfFgGcs%]|%\([^)]+\)[diouxXeEfFgGcs%]")
AMP_RE = re.compile(r"&")

def deepl_translate(texts, target="ZH", source="EN", key=None):
    """Translate a list of texts via DeepL. Returns list of translated texts."""
    if not texts:
        return []
    key = key or os.environ.get("DEEPL_API_KEY", "")
    if not key:
        print("NO_DEEPL_API_KEY")
        sys.exit(2)
    body = json.dumps({"text": texts, "target_lang": target, "source_lang": source}).encode("utf-8")
    req = urllib.request.Request(DEEPL_URL, method="POST", data=body)
    req.add_header("Authorization", "DeepL-Auth-Key " + key)
    req.add_header("User-Agent", "doubao-agent")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [t["text"] for t in data.get("translations", [])]
    except urllib.error.HTTPError as e:
        print("DEEPL_HTTP_ERR", e.code, e.read().decode("utf-8", "replace")[:300])
        raise

def protect_amp(msgid):
    """Remove '&' accelerator markers, remembering their positions to restore."""
    positions = []
    stripped = []
    for i, ch in enumerate(msgid):
        if ch == "&":
            positions.append(i)
        else:
            stripped.append(ch)
    return "".join(stripped), positions

def restore_amp(text, positions):
    """Re-insert '&' at original positions. If text shrank, append at end; if grew, insert near same relative spot."""
    if not positions:
        return text
    chars = list(text)
    # If translated text is shorter than needed, pad to allow insertion
    if len(chars) < len(positions):
        chars.extend([" "] * (len(positions) - len(chars)))
    out = []
    pi = 0
    # insert '&' before character at original index (clamped)
    for i, ch in enumerate(chars):
        while pi < len(positions) and positions[pi] <= i:
            out.append("&")
            pi += 1
        out.append(ch)
    while pi < len(positions):
        out.append("&")
        pi += 1
    return "".join(out).rstrip()

def placeholders_preserved(orig, trans):
    """Check all %-placeholders in orig appear (in order) in trans."""
    po_ = PLACEHOLDER_RE.findall(orig)
    pt_ = PLACEHOLDER_RE.findall(trans)
    return po_ == pt_

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    out_po = None
    pos_args = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out-po":
            out_po = args[i+1]
            i += 2
        elif a.startswith("--"):
            i += 1
        else:
            pos_args.append(a)
            i += 1
    if len(pos_args) != 2:
        print("usage: python translate_missing.py <pot_path> <po_path> [--out-po <out>] [--dry-run]")
        sys.exit(2)
    pot_path, po_path = pos_args
    if out_po is None:
        out_po = po_path

    pot = polib.pofile(pot_path, encoding="utf-8")
    po = polib.pofile(po_path, encoding="utf-8")
    po_lookup = {(e.msgctxt, e.msgid): e for e in po}

    # collect missing: msgid present in pot, missing or empty in po
    missing = []
    for e in pot:
        old = po_lookup.get((e.msgctxt, e.msgid))
        if old is None or not old.msgstr:
            missing.append(e)
    print("MISSING_ENTRIES", len(missing))
    if not missing:
        print("NOTHING_TO_TRANSLATE")
        return

    # translate in batches of 40
    results = {}  # key (ctxt, msgid) -> translated msgstr
    batch_size = 40
    for start in range(0, len(missing), batch_size):
        batch = missing[start:start+batch_size]
        inputs = []
        metas = []
        for e in batch:
            txt = e.msgid
            stripped, positions = protect_amp(txt)
            inputs.append(stripped)
            metas.append((e.msgctxt, e.msgid, positions))
        outs = deepl_translate(inputs)
        for (ctxt, msgid, positions), trans in zip(metas, outs):
            trans2 = restore_amp(trans, positions)
            if not placeholders_preserved(msgid, trans2):
                print("SKIP_PLACEHOLDER:", repr(msgid), "->", repr(trans2))
                continue
            results[(ctxt, msgid)] = trans2
        time.sleep(0.5)

    # apply to po
    applied = 0
    for e in pot:
        key = (e.msgctxt, e.msgid)
        if key in results:
            old = po_lookup.get(key)
            if old is None:
                new_e = polib.POEntry(msgid=e.msgid, msgctxt=e.msgctxt, msgstr=results[key])
                po.append(new_e)
            else:
                old.msgstr = results[key]
                old.flags = []
            applied += 1

    po.save(out_po, newline="\n")
    print("APPLIED", applied)
    print("OUT_PO", out_po)
    # print applied samples
    for (ctxt, msgid), trans in list(results.items())[:10]:
        print("  ", repr(msgid), "->", repr(trans))

if __name__ == "__main__":
    main()
