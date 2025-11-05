# 医療機関検索システム

医療機関データを検索・分析するStreamlitアプリケーションです。

## データソース

| 都道府県/機関名 | URL | 備考 |
| --- | --- | --- |
| 北海道厚生局 | https://kouseikyoku.mhlw.go.jp/hokkaido/gyomu/gyomu/hoken_kikan/todokede_juri_ichiran.html | |
| 東北 | https://kouseikyoku.mhlw.go.jp/tohoku/gyomu/gyomu/hoken_kikan/documents/201805koushin.html | |
| 関東 | https://kouseikyoku.mhlw.go.jp/kantoshinetsu/chousa/kijyun.html | | 
| 中部 | https://kouseikyoku.mhlw.go.jp/tokaihokuriku/newpage_00287.html | |
| 近畿 | https://kouseikyoku.mhlw.go.jp/kinki/gyomu/gyomu/hoken_kikan/shitei_jokyo_00004.html | |
| 中国 | https://kouseikyoku.mhlw.go.jp/chugokushikoku/chousaka/shisetsukijunjuri.html | 
| 四国 | https://kouseikyoku.mhlw.go.jp/shikoku/gyomu/gyomu/hoken_kikan/shitei/index.html | 4.施設基準の届出受理状況（全体） |
| 九州 | https://kouseikyoku.mhlw.go.jp/kyushu/gyomu/gyomu/hoken_kikan/index_00007.html | |



## データの準備

### Featherファイルの作成

ExcelファイルからFeatherファイルを生成するには、以下のコマンドを実行します：

```bash
uv run python create_feather.py --input-dir-path data/2025/10 --output-file-path data/2025/10/all.feather
```

- `--input-dir-path`: Excelファイルが格納されているディレクトリパス（再帰的に検索されます）
- `--output-file-path`: 出力するFeatherファイルのパス

このスクリプトは以下の処理を行います：
- 指定ディレクトリ内のすべてのExcelファイルを読み込み
- 病床数カラムを辞書形式に変換
- 算定開始年月日を日付型に変換（`算定開始年月日_date`カラムとして追加）
- 医療機関番号と受理番号でグループ化して集約

## 機能

- **医療機関検索**: 医療機関名で検索し、詳細情報を確認
- **施設基準別届出数**: すべての届出種別と件数を確認
- **特定医療機関の届出状況**: 選択した医療機関の届出詳細を確認
- **類似医療機関分析**: Jaccard係数による類似度分析
- **届出医療機関検索**: 受理届出名称または受理記号で医療機関を検索

## ローカルでの実行

### uvを使用する場合（推奨）

```bash
# 依存関係のインストール（uv使用）
uv sync

# アプリケーションの起動
uv run streamlit run main.py
```
