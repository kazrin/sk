"""
前回の all.feather と件数を比較し、大幅な減少がないかチェックする。

Usage:
    python3 compare_feather.py data/2026/05/all.feather [--threshold 5.0]

Exit codes:
    0: 正常（減少率が閾値未満、または前回データなし）
    1: 警告（減少率が閾値以上）
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def find_previous_feather(current_path: Path) -> Path | None:
    """data/YYYY/MM/all.feather の形式を前提に、時系列で直前のファイルを探す。"""
    data_root = current_path.parents[2]  # data/
    candidates = sorted(data_root.glob("*/*/all.feather"))
    current_resolved = current_path.resolve()
    before = [p for p in candidates if p.resolve() != current_resolved]
    return before[-1] if before else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current", help="今回生成した all.feather のパス")
    parser.add_argument("--threshold", type=float, default=5.0,
                        help="警告とする減少率の閾値（%%、デフォルト: 5.0）")
    args = parser.parse_args()

    current_path = Path(args.current)
    prev_path = find_previous_feather(current_path)

    current_count = len(pd.read_feather(current_path))

    if prev_path is None:
        print(f"今回: {current_count:,} 行（比較対象の前回データなし）")
        sys.exit(0)

    prev_count = len(pd.read_feather(prev_path))
    diff = current_count - prev_count
    rate = (current_count / prev_count - 1) * 100

    print(f"前回 ({prev_path.parts[-3]}/{prev_path.parts[-2]}): {prev_count:,} 行")
    print(f"今回 ({current_path.parts[-3]}/{current_path.parts[-2]}): {current_count:,} 行")
    print(f"差分: {diff:+,} 行 ({rate:+.1f}%)")

    if rate < -args.threshold:
        print(f"\n[WARNING] 件数が {abs(rate):.1f}% 減少しています（閾値: {args.threshold}%）。")
        print("ダウンロードしたファイルや各地域の件数を確認してください。")
        sys.exit(1)
    else:
        print("\n[OK] 件数は正常範囲内です。")
        sys.exit(0)


if __name__ == "__main__":
    main()
