import streamlit as st
import pandas as pd
from utils import load_raw_data, display_institution_basic_info

st.title("📋 特定医療機関の届出状況")

# Get selected institution from session state
selected_institution = st.session_state.get('selected_institution', None)

if selected_institution:
    st.write(f"### 医療機関: {selected_institution}")
    
    # Load data
    df = load_raw_data()
    
    # Filter data for selected institution
    institution_data = df[df['医療機関名称'] == selected_institution]
    
    # Display basic information
    row_data = institution_data.iloc[0]
    display_institution_basic_info(row_data)
    
    st.divider()
    
    # Display filing statuses in table format
    st.write(f"### 届出状況一覧 ({len(institution_data)}件)")
    
    # Prepare data for table
    display_columns = ['受理届出名称', '受理記号', '受理番号', '算定開始年月日', '個別有効開始年月日']
    
    # Check which columns exist in the data
    available_columns = [col for col in display_columns if col in institution_data.columns]
    
    if available_columns:
        # Create display dataframe
        display_data = institution_data[available_columns].copy()
        
        # Display as table
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )
    
    # Add navigation to similar institutions analysis
    st.divider()
    if st.button("🔍 類似医療機関を分析する", use_container_width=True):
        st.switch_page("pages/4_類似医療機関分析.py")
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")

