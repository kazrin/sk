import streamlit as st
import ast
from pathlib import Path
from dataframes import ShisetsuKijunDataFrame

feather_file_path = "data/2025/10/all.feather"


@st.cache_data(hash_funcs={dict: lambda x: str(x)})
def load_raw_data():
    """Load raw data from feather file"""
    return ShisetsuKijunDataFrame.from_feather(feather_file_path)


def format_bed_count(bed_count):
    """Format bed count dict to display string
    
    Args:
        bed_count: Bed count dict, string representation, or None
        
    Returns:
        Formatted string representation of bed count (e.g., "一般 20 / 療養 10")
    """
    # Convert string to dict if needed
    if isinstance(bed_count, str):
        try:
            bed_count = ast.literal_eval(bed_count)
        except:
            return ""
    
    # Handle non-dict cases
    if bed_count is None:
        return ""
    if not isinstance(bed_count, dict):
        return ""
    if not bed_count:  # Empty dict
        return ""
    
    bed_parts = []
    for bed_type, bed_number in bed_count.items():
        # Skip if both are None
        if bed_type is None and bed_number is None:
            continue
        # Handle different combinations
        if bed_type is None and bed_number is not None:
            bed_parts.append(str(bed_number))
        elif bed_type is not None and bed_number is None:
            bed_parts.append(str(bed_type))
        elif bed_type is not None and bed_number is not None:
            bed_parts.append(f"{bed_type} {bed_number}")
    return " / ".join(bed_parts)


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