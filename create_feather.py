from argparse import ArgumentParser
import pandas as pd
import re
from pathlib import Path


def create_feather_file(input_dir_path, output_file_path):
    """Load raw data from Excel files in data/2025/10 directory and parse bed count column"""
    data_dir = Path(input_dir_path)
    
    # Collect all Excel files recursively
    excel_files = list(data_dir.glob("**/*.xlsx"))
        
    all_dataframes = []
    
    # Load each Excel file and all its sheets
    for excel_file in excel_files:
        xl_file = pd.ExcelFile(excel_file)
        
        # Read all sheets from the Excel file
        for sheet_name in xl_file.sheet_names:
            # Read with skiprows=3
            df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=3)
            assert '区分' in df.columns, f"区分 column is not found in {excel_file.name} {sheet_name}"
            all_dataframes.append(df)
    
    df = pd.concat(all_dataframes, ignore_index=True)
    
    # Parse 病床数 column first (before grouping)
    # This needs to be done before grouping to ensure all rows have processed 病床数
    
    # Parse 病床数 column and convert to dict format
    # Formats supported:
    # - "一般　　22" -> {"一般": 22}
    # - "一般　　1178／精神　　40" -> {"一般": 1178, "精神": 40}
    # - "22" -> {None: 22}
    # - "一般" -> {"一般": None}
    if '病床数' in df.columns:
        bed_dicts = []
        
        for value in df['病床数']:
            if pd.isna(value):
                bed_dicts.append({})
                continue
            
            value_str = str(value).strip()
            bed_dict = {}
            
            # Split by "／" (全角スラッシュ) or "/" (半角スラッシュ) if multiple entries
            parts = re.split(r'[／/]', value_str)
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Extract type and number from each part
                # Pattern: 文字列部分と数値部分を分離
                # 全角・半角スペースに対応
                match = re.match(r'^(.+?)[\s\u3000]+(\d+)$', part)
                if match:
                    # Both type and number
                    bed_type = match.group(1).strip().replace('\u3000', ' ').strip()  # 全角スペースを半角に変換してトリム
                    # 重複した単語を除去（例: "一般 一般" -> "一般"）
                    words = bed_type.split()
                    bed_type = ' '.join(sorted(set(words), key=words.index))  # 順序を保ちつつ重複除去
                    bed_number = int(match.group(2))
                    bed_dict[bed_type] = bed_number
                else:
                    # Check if it's number only
                    if part.isdigit():
                        bed_dict[None] = int(part)
                    else:
                        # Type only - 全角スペースを処理して重複除去
                        bed_type = part.strip().replace('\u3000', ' ').strip()
                        words = bed_type.split()
                        bed_type = ' '.join(sorted(set(words), key=words.index))  # 順序を保ちつつ重複除去
                        if bed_type:  # 空文字列でない場合のみ
                            bed_dict[bed_type] = None
            
            # Remove keys with None values to keep dict clean
            # Keep only keys that have actual values (not None)
            # Exception: keep {None: number} format for number-only entries
            clean_bed_dict = {}
            for k, v in bed_dict.items():
                if v is not None:  # Keep all entries with non-None values
                    clean_bed_dict[k] = v
            bed_dicts.append(clean_bed_dict)
        
        # Overwrite 病床数 column with dict format
        df['病床数'] = bed_dicts
    
    # Aggregate data by 医療機関番号 and 受理番号 to make them primary keys
    # Create a function to aggregate remarks into a dict
    def aggregate_remarks(group):
        remarks_dict = {}
        if '備考（見出し）' in group.columns and '備考（データ）' in group.columns:
            for _, row in group.iterrows():
                header = row['備考（見出し）']
                data = row['備考（データ）']
                # Skip if header is blank/NaN
                if pd.notna(header) and str(header).strip():
                    # Use data value, or empty string if data is blank
                    data_value = str(data).strip() if pd.notna(data) and str(data).strip() else ''
                    remarks_dict[str(header).strip()] = data_value
        return remarks_dict
    
    # Define aggregation functions for each column type
    def take_first_dict(x):
        """Take the first non-empty dict, or return empty dict if all are empty"""
        for val in x:
            if isinstance(val, dict) and val:
                return val
        return x.iloc[0] if len(x) > 0 else {}
    
    agg_dict = {}
    for col in df.columns:
        if col in ['医療機関番号', '受理番号']:
            continue  # Skip grouping keys
        elif col == '備考（見出し）' or col == '備考（データ）':
            continue  # Will be aggregated separately
        elif col == '病床数':
            # For dict columns, take the first non-empty dict, or merge if needed
            agg_dict[col] = take_first_dict
        else:
            # For other columns, take the first non-null value
            agg_dict[col] = 'first'
    
    # Group by 医療機関番号 and 受理番号
    grouped = df.groupby(['医療機関番号', '受理番号'], dropna=False)
    
    # Aggregate remarks
    aggregated_remarks = grouped.apply(aggregate_remarks).reset_index(name='備考集約')
    
    # Aggregate other columns
    df_agg = grouped.agg(agg_dict).reset_index()
    
    # Merge aggregated remarks
    df = df_agg.merge(aggregated_remarks[['医療機関番号', '受理番号', '備考集約']], 
                        on=['医療機関番号', '受理番号'], how='left')
    
    # Fill NaN with empty dict for 備考集約
    df['備考集約'] = df['備考集約'].apply(lambda x: x if isinstance(x, dict) else {})
    
    # assert len(df["都道府県名"].unique()) == 47, f"Some prefectures are missing.. {df["都道府県名"].unique()}"

    df.drop('備考集約', axis=1).to_feather(output_file_path)

    return df


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input-dir-path", type=str, help="input directory path that xlsx files are located. e.g. data/2025/10")
    parser.add_argument("--output-file-path", type=str, help="output feather file path. e.g. data/2025/10/all.feather")
    args = parser.parse_args()
    df = create_feather_file(args.input_dir_path, args.output_file_path)