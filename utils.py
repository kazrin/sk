import streamlit as st
import pandas as pd
import re
from pathlib import Path

feather_file_path = "data/2025/10/all.feather"

@st.cache_data
def load_raw_data():
    df = pd.read_feather(feather_file_path)
    # Clean up bed count dicts: remove keys with None values
    # pandas feather format merges all dict keys across rows, adding None for missing keys
    if '病床数' in df.columns:
        def clean_bed_dict(bed_count):
            if isinstance(bed_count, dict):
                # Keep only keys with non-None values
                return {k: v for k, v in bed_count.items() if v is not None}
            return bed_count
        df['病床数'] = df['病床数'].apply(clean_bed_dict)
    return df


def display_institution_basic_info(row_data):
    """Display basic institution information in two columns"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**医療機関番号:** {row_data['医療機関番号']}")
        st.write(f"**医療機関記号番号:** {row_data['医療機関記号番号']}")
        st.write(f"**都道府県:** {row_data['都道府県名']}")
        st.write(f"**病床数:** {row_data['病床数']}")
    with col2:
        st.write(f"**郵便番号:** {row_data['医療機関所在地（郵便番号）']}")
        st.write(f"**住所:** {row_data['医療機関所在地（住所）']}")
        st.write(f"**電話番号:** {row_data['電話番号']}")
        st.write(f"**種別:** {row_data['種別']}")

if __name__ == "__main__":
    create_feather_file()