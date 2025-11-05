from argparse import ArgumentParser
import pandas as pd
import re
from pathlib import Path
from datetime import datetime


def parse_japanese_era_date(date_str):
    """Parse Japanese era date string to datetime object
    
    Supports formats like:
    - "令和元年12月 1日" -> 2019-12-01
    - "平成29年 9月 1日" -> 2017-09-01
    - "昭和63年 1月 1日" -> 1988-01-01
    
    Args:
        date_str: String containing Japanese era date
        
    Returns:
        datetime object or None if parsing fails
    """
    if pd.isna(date_str) or not date_str:
        return None
    
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Era to Western year base mapping
    era_base = {
        '令和': 2018,  # 令和元年 = 2019 = 2018 + 1
        '平成': 1988,  # 平成元年 = 1989 = 1988 + 1
        '昭和': 1925,  # 昭和元年 = 1926 = 1925 + 1
        '大正': 1911,  # 大正元年 = 1912 = 1911 + 1
        '明治': 1867,  # 明治元年 = 1868 = 1867 + 1
    }
    
    # Pattern to match: 元号(元年|N年)M月 D日
    # Examples: "令和元年12月 1日", "平成29年 9月 1日", "令和 6年 7月 1日"
    # Match one of the era names explicitly
    # Handle spaces after era name and between year/month/day
    # Handle both half-width and full-width spaces (\s includes \u3000)
    era_pattern = '|'.join(era_base.keys())
    # Allow spaces after era name: 令和 6年 or 令和6年
    pattern = rf'({era_pattern})[\s\u3000]*(?:元|(\d+))年[\s\u3000]*(\d+)[\s\u3000]*月[\s\u3000]*(\d+)[\s\u3000]*日'
    match = re.match(pattern, date_str)
    
    if not match:
        # Try alternative pattern without spaces (for cases like "令和6年7月1日")
        pattern = rf'({era_pattern})(?:元|(\d+))年(\d+)月(\d+)日'
        match = re.match(pattern, date_str)
    
    if not match:
        return None
    
    era_name = match.group(1)
    year_str = match.group(2)  # None if 元年
    month_str = match.group(3)
    day_str = match.group(4)
    
    # Get era base year (already validated by regex, but double-check)
    if era_name not in era_base:
        return None
    
    # Calculate Western year
    if year_str is None:  # 元年
        western_year = era_base[era_name] + 1
    else:
        western_year = era_base[era_name] + int(year_str)
    
    # Parse month and day
    try:
        month = int(month_str)
        day = int(day_str)
        
        # Validate date
        if month < 1 or month > 12 or day < 1 or day > 31:
            return None
        
        # Create datetime object
        return datetime(western_year, month, day)
    except (ValueError, TypeError):
        return None


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
    
    # Parse 算定開始年月日 column and create date column
    if '算定開始年月日' in df.columns:
        df['算定開始年月日_date'] = df['算定開始年月日'].apply(parse_japanese_era_date)
        
        # Assert that all non-null 算定開始年月日 values are successfully parsed
        problematic = df[df['算定開始年月日'].notna() & df['算定開始年月日_date'].isna()]
        if len(problematic) > 0:
            # Show some examples of problematic values
            examples = problematic['算定開始年月日'].unique()[:10]
            error_msg = f"Found {len(problematic)} rows where 算定開始年月日 has value but 算定開始年月日_date is null. Examples: {list(examples)}"
            raise AssertionError(error_msg)
    
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