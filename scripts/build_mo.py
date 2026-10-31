# -*- coding: utf-8 -*-
"""Portable: merge official pot + existing zh_CN.po -> tigervnc.mo.

Usage:
    python build_mo.py <pot_path> <po_path> <out_mo_path>

- pot_path : official translation template (e.g. from TigerVNC/tigervnc repo)
- po_path  : existing simplified-Chinese translation (zh_CN.po)
- out_mo_path : where to write the compiled tigervnc.mo

Requires: polib  (pip install polib)
"""
import os, sys
import polib

def main():
    if len(sys.argv) != 4:
        print("usage: python build_mo.py <pot_path> <po_path> <out_mo_path>")
        sys.exit(2)
    pot_path, po_path, out_mo = sys.argv[1], sys.argv[2], sys.argv[3]

    pot = polib.pofile(pot_path, encoding="utf-8")
    po  = polib.pofile(po_path, encoding="utf-8")

    old_lookup = {}
    for e in po:
        old_lookup[(e.msgctxt, e.msgid)] = e

    new_po = polib.POFile()
    new_po.header = ""
    new_po.metadata.update({
        "Project-Id-Version": pot.metadata.get("Project-Id-Version", ""),
        "Report-Msgid-Bugs-To": "tigervnc-devel@googlegroups.com",
        "POT-Creation-Date": pot.metadata.get("POT-Creation-Date", ""),
        "PO-Revision-Date": "2026-10-31 22:20+0800",
        "Last-Translator": "Doubao (based on Translation Project zh_CN)",
        "Language-Team": "Chinese (simplified) <i18n-zh@googlegroups.com>",
        "Language": "zh_CN",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": "nplurals=1; plural=0;",
    })

    missing = []
    used_fuzzy = 0
    kept = 0
    for e in pot:
        key = (e.msgctxt, e.msgid)
        new_e = polib.POEntry(
            msgid=e.msgid,
            msgctxt=e.msgctxt,
            msgstr=e.msgstr or "",
            occurrences=list(e.occurrences),
            flags=list(e.flags),
        )
        old = old_lookup.get(key)
        if old is not None and old.msgstr:
            new_e.msgstr = old.msgstr
            new_e.flags = []
            kept += 1
            if "fuzzy" in (old.flags or []):
                used_fuzzy += 1
        else:
            missing.append(new_e)
        new_po.append(new_e)

    # Also write the aligned .po beside the .mo for traceability
    out_po = os.path.splitext(out_mo)[0] + ".po"
    new_po.save(out_po, newline="\n")

    mo = polib.MOFile()
    mo.metadata = new_po.metadata
    for e in new_po:
        mo.append(e)
    mo.save(out_mo)

    total = len(pot)
    print("TOTAL_ENTRIES", total)
    print("KEPT_TRANSLATED", kept)
    print("USED_FUZZY", used_fuzzy)
    print("MISSING", len(missing))
    print("PO_OUT", out_po)
    print("MO_OUT", out_mo, os.path.getsize(out_mo))

if __name__ == "__main__":
    main()
