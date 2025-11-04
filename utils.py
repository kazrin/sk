import streamlit as st
from pathlib import Path
from dataframes import ShisetsuKijunDataFrame

feather_file_path = "data/2025/10/all.feather"


@st.cache_data(hash_funcs={dict: lambda x: str(x)})
def load_raw_data():
    """Load raw data from feather file"""
    return ShisetsuKijunDataFrame.from_feather(feather_file_path)


def display_institution_basic_info(row_data):
    """Display basic institution information in two columns"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**医療機関番号:** {int(row_data['医療機関番号'])}")
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