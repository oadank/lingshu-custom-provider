"""Repack exe replacing three patched modules."""
import marshal
import struct
import sys
import zlib
import py_compile
import tempfile
import os

WORK = r"C:\D\opt\lingshu-work"
EXE_IN = WORK + r"\backup-20260914\nova-api.exe.bak"
EXE_OUT = WORK + r"\nova-api.new3.exe"
CA_MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"
COOKIE_FMT = "!8sIIII64s"
COOKIE_SIZE = struct.calcsize(COOKIE_FMT)

TARGETS = {
    "app.llm.providers": WORK + r"\patch\providers.py",
    "app.services.settings": WORK + r"\patch\settings.py",
    "app.routers.settings": WORK + r"\patch\routers_settings.py",
}


def load_code(py_path):
    pyc = tempfile.mktemp(suffix=".pyc")
    py_compile.compile(py_path, pyc, doraise=True)
    with open(pyc, "rb") as f:
        f.read(16)
        code = marshal.load(f)
    os.remove(pyc)
    return code


def main():
    exe = open(EXE_IN, "rb").read()
    cp = exe.rfind(CA_MAGIC)
    _, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack(COOKIE_FMT, exe[cp : cp + COOKIE_SIZE])
    pkg_start = cp + COOKIE_SIZE - pkg_len
    toc_start = pkg_start + toc_off
    toc_data = exe[toc_start : toc_start + toc_len]

    p = 0
    pyz_entry = None
    while p < len(toc_data):
        (el,) = struct.unpack("!i", toc_data[p : p + 4])
        pos, cmpr, uncmpr, flag, typ = struct.unpack("!IIIBc", toc_data[p + 4 : p + 18])
        if typ == b"z":
            pyz_entry = (p, pos, cmpr)
        p += el
    assert pyz_entry, "no pyz entry"
    p_off, p_pos, p_cmpr = pyz_entry

    pyz = exe[pkg_start + p_pos : pkg_start + p_pos + p_cmpr]
    assert pyz[:4] == b"PYZ\0"
    magic = pyz[4:8]
    to = int.from_bytes(pyz[8:12], "big")
    toc = marshal.loads(pyz[to:])

    pending = dict(TARGETS)
    data_region = pyz[12:to]
    new_pos = 12 + len(data_region)
    new_toc = []
    for name, (typ, pos, ln) in toc:
        if name in pending:
            blob = zlib.compress(marshal.dumps(load_code(pending.pop(name))), 9)
            new_toc.append((name, (typ, new_pos, len(blob))))
            data_region += blob
            new_pos += len(blob)
            print("replaced", name)
        else:
            new_toc.append((name, (typ, pos, ln)))
    assert not pending, pending
    new_pyz = b"PYZ\0" + magic + (12 + len(data_region)).to_bytes(4, "big") + data_region + marshal.dumps(new_toc)
    print(f"PYZ {len(pyz)} -> {len(new_pyz)}")

    new_toc_off = toc_off + (len(new_pyz) - p_cmpr)
    body = bytearray(exe[pkg_start : pkg_start + toc_off])
    body[p_pos:] = new_pyz
    tocb = bytearray(toc_data)
    struct.pack_into("!II", tocb, p_off + 8, len(new_pyz), len(new_pyz))
    cookie = struct.pack(COOKIE_FMT, CA_MAGIC, new_toc_off + toc_len + COOKIE_SIZE, new_toc_off, toc_len, pyver, pylib)
    out = exe[:pkg_start] + bytes(body) + bytes(tocb) + cookie
    open(EXE_OUT, "wb").write(out)
    print("written", EXE_OUT, len(out))


if __name__ == "__main__":
    sys.exit(main())
