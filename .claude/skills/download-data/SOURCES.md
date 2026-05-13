# データソース一覧

## 地方厚生局URL

| 地域 | URL |
|------|-----|
| 北海道 | https://kouseikyoku.mhlw.go.jp/hokkaido/gyomu/gyomu/hoken_kikan/todokede_juri_ichiran.html |
| 東北   | https://kouseikyoku.mhlw.go.jp/tohoku/gyomu/gyomu/hoken_kikan/documents/201805koushin.html |
| 関東   | https://kouseikyoku.mhlw.go.jp/kantoshinetsu/chousa/kijyun.html |
| 中部   | https://kouseikyoku.mhlw.go.jp/tokaihokuriku/newpage_00349.html |
| 近畿   | https://kouseikyoku.mhlw.go.jp/kinki/gyomu/gyomu/hoken_kikan/shitei_jokyo_00004.html |
| 中国   | https://kouseikyoku.mhlw.go.jp/chugokushikoku/chousaka/shisetsukijunjuri.html |
| 四国   | https://kouseikyoku.mhlw.go.jp/shikoku/gyomu/gyomu/hoken_kikan/shitei/index.html |
| 九州   | https://kouseikyoku.mhlw.go.jp/kyushu/gyomu/gyomu/hoken_kikan/index_00007.html |

## 地域別メモ

### 北海道
- ページに医科・歯科・薬局の3つのExcelリンクがある
- 医科は最初のリンク（ファイルサイズが最大のもの）

### 東北
- 6県分まとめファイル（`shisetsu-touhoku-ika-*.xlsx`）と届出項目別ファイルがある
- 全体（6県分）の医科ファイルのみダウンロードする
- URLに二重ドット（`..xlsx`）が含まれることがある（サイト側のtypo）

### 関東
- ZIPに10都県分のxlsxが入っている
- `届出項目別`のZIPは不要、全体分（`shisetsu_ika_*.zip`）のみ

### 中部
- ZIPに都道府県名が括弧に入ったxlsxが入っている（例: `2605（愛知医科）届出受理医療機関名簿.xlsx`）

### 近畿
- ZIPに7府県分のxlsxが入っている（例: `2026.5_sisetukijun_osaka_ika.xlsx`）
- 「施設基準の届出受理状況（全体）」セクションの「各府県Excelデータ（医科）」を選択

### 中国
- ZIPに5県分のxlsxが入っている（例: `34_広島_届出受理医療機関名簿.xlsx`）
- 歯科・訪問看護向けのZIPとURLが異なるので注意

### 四国
- ページが複数セクションに分かれている
- **セクション4「施設基準の届出受理状況（全体）」**の医科ZIPを選択（歯科・薬局ではない）
- ZIPに4県分のxlsxが入っている（例: `02_01 香川 医科 届出受理医療機関名簿.xlsx`）

### 九州
- 月別・事務所別の一覧ページ（毎月8事務所×複数月）
- 対象年月（YYYY年M月1日現在）の8事務所分を選択
  - 指導監査課（福岡）/ 佐賀事務所 / 長崎事務所 / 熊本事務所 / 大分事務所 / 宮崎事務所 / 鹿児島事務所 / 沖縄事務所
- 対象月のデータがない場合は最新（最上部）の月を使用
- 各ZIPに医科（`_ika_`）・歯科（`_shika_`）・薬局（`_yakkyoku_`）ファイルが混在するので医科のみ残す
