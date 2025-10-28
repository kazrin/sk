import streamlit as st
import pandas as pd

st.title("📋 届出状況一覧")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")

# Configuration
MAX_DISPLAY_COUNT = 100

@st.cache_data
def load_raw_data():
    return pd.read_excel("data/r7/tokyo.xlsx", skiprows=3)

@st.cache_data
def load_filing_status_data():
    """Load and prepare filing status data"""
    df = load_raw_data()
    # Get unique filing statuses
    filing_status = df['受理届出名称'].value_counts().reset_index()
    filing_status.columns = ['受理届出名称', '件数']
    return filing_status.sort_values('受理届出名称')

# Load data
filing_status_df = load_filing_status_data()
st.write(f"総届出種類数: {len(filing_status_df):,} 種類")

# Search functionality
search_term = st.text_input("受理届出名称で検索", placeholder="届出名称の一部を入力")

# Filter results
if search_term:
    filtered_status = filing_status_df[filing_status_df['受理届出名称'].str.contains(search_term, case=False, na=False)]
    
    if len(filtered_status) > 0:
        st.write(f"検索結果: {len(filtered_status)} 種類")
        
        # Display results as a table
        display_count = min(MAX_DISPLAY_COUNT, len(filtered_status))
        if len(filtered_status) > MAX_DISPLAY_COUNT:
            st.info(f"表示件数を{MAX_DISPLAY_COUNT}件に制限しています（全{len(filtered_status)}件中）")
        
        # Display as a nice table with styling
        for _, row in filtered_status.head(display_count).iterrows():
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{row['受理届出名称']}**")
                with col2:
                    st.metric("件数", f"{row['件数']:,}")
                st.divider()
    else:
        st.warning("該当する届出が見つかりませんでした。")
else:
    # Display all filing statuses when no search term, sorted by count
    st.write(f"上位{MAX_DISPLAY_COUNT}件の届出種別一覧 (件数順):")
    
    sorted_status = filing_status_df.sort_values('件数', ascending=False).head(MAX_DISPLAY_COUNT)
    for _, row in sorted_status.iterrows():
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{row['受理届出名称']}**")
            with col2:
                st.metric("件数", f"{row['件数']:,}")
            st.divider()

