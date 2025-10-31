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
                match = re.match(r'^(.+?)\s+(\d+)$', part)
                if match:
                    # Both type and number
                    bed_type = match.group(1).strip()
                    bed_number = int(match.group(2))
                    bed_dict[bed_type] = bed_number
                else:
                    # Check if it's number only
                    if part.isdigit():
                        bed_dict[None] = int(part)
                    else:
                        # Type only
                        bed_dict[part] = None
            
            bed_dicts.append(bed_dict)
        
        # Overwrite 病床数 column with dict format
        df['病床数'] = bed_dicts
    
    return df

