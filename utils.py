import streamlit as st
import pandas as pd
import re

@st.cache_data
def load_raw_data():
    """Load raw data from Excel file and parse bed count column"""
    df = pd.read_excel("data/r7/tokyo.xlsx", skiprows=3)
    
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
            
            bed_dicts.append(bed_dict)
        
        # Overwrite 病床数 column with dict format
        df['病床数'] = bed_dicts
    
    return df

def display_institution_basic_info(row_data):
    """Display basic institution information in two columns"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**医療機関番号:** {row_data['医療機関番号']}")
        st.write(f"**医療機関記号番号:** {row_data['医療機関記号番号']}")
        st.write(f"**種別:** {row_data['種別']}")
        # Display bed information
        bed_count = row_data.get('病床数', {})
        
        if bed_count and isinstance(bed_count, dict):
            bed_display_parts = []
            for bed_type, bed_number in bed_count.items():
                if bed_type is None and bed_number is not None:
                    bed_display_parts.append(str(bed_number))
                elif bed_type is not None and bed_number is None:
                    bed_display_parts.append(str(bed_type))
                elif bed_type is not None and bed_number is not None:
                    bed_display_parts.append(f"{bed_type} {bed_number}")
            
            if bed_display_parts:
                st.write(f"**病床種類・病床数:** {' / '.join(bed_display_parts)}")
    
    with col2:
        st.write(f"**郵便番号:** {row_data['医療機関所在地（郵便番号）']}")
        st.write(f"**住所:** {row_data['医療機関所在地（住所）']}")
        st.write(f"**電話番号:** {row_data['電話番号']}")

