"""Extract the ISO9660 file system from a Dreamcast GD-ROM high-density track.

Usage: python gdrom_extract.py <track3.bin> <out_dir> [--list]

The track is a raw MODE1/2352 dump (Redump layout). The high-density area starts
at LBA 45000, so every extent address in the file system is offset by that much.
The source image is only read, never written.
"""
import os
import struct
import sys

SECTOR = 2352
HEADER = 16
DATA = 2048
BASE_LBA = 45000


class Track:
    def __init__(self, path):
        self.f = open(path, "rb")

    def read(self, lba, length):
        out = bytearray()
        sec = lba - BASE_LBA
        while len(out) < length:
            self.f.seek(sec * SECTOR + HEADER)
            out += self.f.read(DATA)
            sec += 1
        return bytes(out[:length])


def walk(track, lba, size, prefix, out):
    data = track.read(lba, size)
    pos = 0
    while pos < len(data):
        rec_len = data[pos]
        if rec_len == 0:
            # records never span sectors; skip to the next one
            pos = (pos // DATA + 1) * DATA
            continue
        rec = data[pos:pos + rec_len]
        pos += rec_len
        ext_lba, ext_size = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
        flags = rec[25]
        name = rec[33:33 + rec[32]]
        if name in (b"\x00", b"\x01"):
            continue
        name = name.decode("ascii", "replace").split(";")[0]
        path = prefix + name
        if flags & 2:
            walk(track, ext_lba, ext_size, path + "/", out)
        else:
            out.append((path, ext_lba, ext_size))


def main():
    track_path, out_dir = sys.argv[1], sys.argv[2]
    list_only = "--list" in sys.argv
    track = Track(track_path)
    pvd = track.read(BASE_LBA + 16, DATA)
    if pvd[1:6] != b"CD001":
        raise SystemExit("No ISO9660 volume descriptor found at LBA 45016")
    root = pvd[156:190]
    root_lba, root_size = struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0]
    files = []
    walk(track, root_lba, root_size, "", files)
    total = 0
    for path, lba, size in files:
        total += size
        if list_only:
            print(f"{size:>10}  {path}")
            continue
        dest = os.path.join(out_dir, path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest) or out_dir, exist_ok=True)
        with open(dest, "wb") as o:
            o.write(track.read(lba, size))
    print(f"{len(files)} files, {total / 1e6:.1f} MB", "listed" if list_only else f"extracted to {out_dir}")


if __name__ == "__main__":
    main()
