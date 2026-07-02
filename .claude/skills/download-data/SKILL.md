---
description: 各地方厚生局から施設基準届出受理の医科Excelをダウンロードし data/YYYY/MM/地域名/ に保存後、all.feather を生成する
---

引数 `$ARGUMENTS` から年月（`YYYY/MM`、例: `2026/05`）を受け取り、各地方厚生局サイトから施設基準届出受理医療機関名簿（**医科**）ExcelをダウンロードしてRAWデータとして保存する。

各地方厚生局のサイトは毎月更新されるとは限らない。**対象年月と完全一致する表記が無くても構わないので、各地域ページに現在掲載されている最新のデータをそのままダウンロードすること。** 「まだ対象月のデータが公開されていない」と判断して処理を中断してはいけない（九州のように月別ページがある場合は最新月を選べばよい。それ以外の地域は常に最新のExcel/ZIPを取得する）。

データソースURLと地域別の詳細は `SOURCES.md` を参照。

## Step 1: ディレクトリ作成

```bash
mkdir -p data/YYYY/MM/{北海道,東北,関東,中部,近畿,中国,四国,九州}
```

## Step 2: 各地域のダウンロード

WebFetchで各URLを取得し、医科の施設基準届出受理に関するExcel/ZIPリンクを特定してダウンロードする。相対パスhrefには `https://kouseikyoku.mhlw.go.jp` を補完すること。

| 地域 | 形式 | ダウンロード対象 |
|------|------|----------------|
| 北海道 | xlsx直接 | 医科の最初のExcelリンク（1ファイル） |
| 東北 | xlsx直接 | `shisetsu-touhoku-ika-*.xlsx`（6県分） |
| 関東 | ZIP | 「医科（ZIP）」`shisetsu_ika_*.zip` |
| 中部 | ZIP | 「届出受理医療機関名簿（医科）」ZIP |
| 近畿 | ZIP | 「各府県Excelデータ」`*sisetukijun_ika.zip` |
| 中国 | ZIP | 「各県分エクセルデータ（医科）」ZIP |
| 四国 | ZIP | セクション4「施設基準届出受理状況（全体）」医科ZIP |
| 九州 | ZIP×8 | 対象月（なければ最新月）の8事務所分 |

## Step 3: ZIP展開

macOSの`unzip`は日本語ファイル名を扱えないため、`extract_zip.py` を使う:

```bash
python3 .claude/skills/download-data/extract_zip.py /tmp/xxx.zip data/YYYY/MM/地域名/
rm /tmp/xxx.zip
```

九州のZIPには歯科(`_shika_`)・薬局(`_yakkyoku_`)ファイルも含まれるので、展開後に削除する:

```bash
find data/YYYY/MM/九州/ -name "*.xlsx" | grep -v '_ika' | xargs rm -f
```

## Step 4: feather生成

ダウンロードしたxlsxファイルから `all.feather` を生成する。42ファイル分の読み込みには10分前後かかることがあるため、**フォアグラウンドで実行しない**（Bashツールのタイムアウトで処理が強制終了され、最初からやり直しになる）。必ず最初からバックグラウンドで実行すること:

```bash
nohup uv run python create_feather.py \
  --input-dir-path data/YYYY/MM \
  --output-file-path data/YYYY/MM/all.feather \
  > /tmp/create_feather.log 2>&1 &
```

その後は`BashOutput`ツールや`sleep 60`程度の間隔でのポーリングで完了を待つ。**待っている間に同じコマンドを再実行しない**（プロセスが二重に走るだけで無駄になる）。`/tmp/create_feather.log` にエラーが出ていればユーザーに報告して停止する。

エラーが出た場合はエラーメッセージをユーザーに報告して停止する。

## Step 5: 完了確認

```bash
find data/YYYY/MM -name "*.xlsx" | sort
find data/YYYY/MM -name "*.xlsx" | wc -l
ls -lh data/YYYY/MM/all.feather
```

ファイルが0件の地域があればURLを再確認してユーザーに報告する。

## Step 6: 前回データとの件数比較

`compare_feather.py` を使って `data/` 配下の直前の `all.feather` と件数を比較する:

```bash
uv run python .claude/skills/download-data/compare_feather.py data/YYYY/MM/all.feather
```

- 減少率が **5% 未満**なら `[OK]` を表示して終了
- 減少率が **5% 以上**なら `[WARNING]` を表示し、ユーザーに報告して対処を仰ぐ
- 前回データが存在しない場合は比較をスキップして終了

## Step 7: utils.py のデータパスを更新

`utils.py` の `feather_file_path` を今回のパスに書き換える:

```bash
sed -i '' 's|feather_file_path = "data/.*/all.feather"|feather_file_path = "data/YYYY/MM/all.feather"|' utils.py
```

変更後に確認する:

```bash
grep "feather_file_path" utils.py
```
