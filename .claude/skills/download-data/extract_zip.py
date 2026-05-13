"""Extract ZIP files with Japanese filenames (cp932/utf-8 auto-detect) to a flat directory."""

import argparse
import os
import shutil
import sys
import zipfile


def extract_jp_zip(zip_path: str, dest_dir: str) -> list[str]:
    os.makedirs(dest_dir, exist_ok=True)
    extracted = []

    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            try:
                name = info.filename.encode("cp437").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                try:
                    name = info.filename.encode("cp437").decode("cp932")
                except Exception:
                    name = info.filename

            basename = os.path.basename(name)
            if not basename or info.is_dir():
                continue
            if not basename.lower().endswith(".xlsx"):
                continue

            out_path = os.path.join(dest_dir, basename)
            with zf.open(info) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(basename)

    return extracted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="ZIPファイルのパス")
    parser.add_argument("dest_dir", help="展開先ディレクトリ")
    args = parser.parse_args()

    files = extract_jp_zip(args.zip_path, args.dest_dir)
    for f in files:
        print(f"  -> {f}")
    print(f"{len(files)} ファイルを展開しました")
    sys.exit(0 if files else 1)
