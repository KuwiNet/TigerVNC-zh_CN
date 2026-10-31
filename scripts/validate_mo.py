# -*- coding: utf-8 -*-
"""Validate a GNU gettext MO file and spot-check Chinese translations.

Usage:
    python validate_mo.py <path_to_tigervnc.mo>
"""
import struct, sys

def main():
    if len(sys.argv) != 2:
        print("usage: python validate_mo.py <path_to.mo>")
        sys.exit(2)
    mo_path = sys.argv[1]
    data = open(mo_path, "rb").read()
    print("mo size:", len(data))

    magic = data[0:4]
    if magic == b'\xde\x12\x04\x95':
        le = True
    elif magic == b'\x95\x04\x12\xde':
        le = False
    else:
        le = None
    print("magic hex:", magic.hex(), "little_endian:", le)
    if le is None:
        sys.exit("NOT A MO FILE")

    def rd(off, fmt):
        return struct.unpack_from(fmt, data, off)[0] if le else struct.unpack_from(">" + fmt[1:], data, off)[0]

    rev = rd(4, "<I"); n = rd(8, "<I"); o = rd(12, "<I"); t = rd(16, "<I")
    print("rev:", rev, "nstrings:", n, "orig_table_off:", o, "trans_table_off:", t)

    def read_str_table(table_off, idx):
        eoff = table_off + idx*8
        slen = rd(eoff, "<I"); sofs = rd(eoff+4, "<I")
        return data[sofs:sofs+slen]

    hdr = read_str_table(o, 0)
    print("header keys:", hdr.decode("utf-8", "replace")[:120])

    lookup = {}
    for i in range(n):
        s = read_str_table(o, i)
        ts = read_str_table(t, i)
        if s.startswith(b"\x04"):
            ctx, _, msgid = s[1:].partition(b"\x04")
            key = (ctx.decode("utf-8","replace"), msgid.decode("utf-8","replace"))
        else:
            key = (None, s.decode("utf-8","replace"))
        lookup[key] = ts.decode("utf-8","replace")

    print("total lookup entries:", len(lookup))

    checks = [
        ("VNC server:", None),
        ("TigerVNC options", None),
        ("Preferred encoding", None),
        ("Connect", None),
        ("About TigerVNC", None),
        ("Password:", None),
        ("Disconn&ect", "ContextMenu|"),
    ]
    for msgid, ctx in checks:
        val = lookup.get((ctx, msgid))
        print("%r -> %r" % (msgid, val))

    zh = [v for v in lookup.values() if any('\u4e00' <= c <= '\u9fff' for c in v)]
    print("entries containing Chinese:", len(zh))
    print("sample:", zh[:5])

if __name__ == "__main__":
    main()
