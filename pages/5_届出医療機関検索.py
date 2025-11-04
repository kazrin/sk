import streamlit as st
import pandas as pd
from utils import load_raw_data, format_bed_count

st.title("🔍 届出医療機関検索")

# Navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("← ホームページに戻る"):
        st.switch_page("main.py")
with col2:
    if st.button("📋 施設基準別届出数を見る"):
        st.switch_page("pages/4_施設基準別届出数.py")

# Load data
df = load_raw_data()

# Get all available filing names and symbols for autocomplete
if '受理届出名称' in df.columns and '受理記号' in df.columns:
    # Get unique combinations of 受理届出名称 and 受理記号 (1-to-1 relationship)
    filing_options = (
        df.groupby('受理届出名称')['受理記号']
        .first()
        .reset_index()
    )
    filing_options = filing_options.sort_values('受理届出名称')
    
    # Create options list with display format
    filing_display_options = []
    for _, row in filing_options.iterrows():
        name = row['受理届出名称']
        symbol = row['受理記号']
        if pd.notna(symbol) and str(symbol).strip():
            display_text = f"{name} ({symbol})"
        else:
            display_text = name
        filing_display_options.append({
            'display': display_text,
            'name': name,
            'symbol': symbol if pd.notna(symbol) else ''
        })
else:
    filing_display_options = []

# Search interface
st.write("### 検索条件")

# Single select for filing criteria
if filing_display_options:
    selected_display_option = st.selectbox(
        "受理届出名称または受理記号を選択:",
        options=[""] + [opt['display'] for opt in filing_display_options],
        key='filing_search_select',
        help="受理届出名称または受理記号を選択してください"
    )
    
    # Extract selected filing name and symbol
    selected_filing_name = None
    selected_filing_symbol = None
    
    if selected_display_option:
        for opt in filing_display_options:
            if opt['display'] == selected_display_option:
                selected_filing_name = opt['name']
                selected_filing_symbol = opt['symbol'] if opt['symbol'] else None
                break
    
    # Search
    if selected_filing_name:
        st.write("### 検索結果")
        
        # Cached function to get search results
        @st.cache_data(hash_funcs={dict: lambda x: str(x)})
        def search_institutions_by_filing(_df, filing_name, filing_symbol=None):
            """Search institutions by filing name or symbol"""
            # Filter institutions that have the selected filing
            # Match against either 受理届出名称 or 受理記号
            name_mask = _df['受理届出名称'] == filing_name
            if filing_symbol:
                symbol_mask = _df['受理記号'] == filing_symbol
                mask = name_mask | symbol_mask
            else:
                mask = name_mask
            
            matching_records = _df[mask]
            
            if len(matching_records) == 0:
                return pd.DataFrame()
            
            # Get unique institutions (by institution number)
            institution_numbers = matching_records['医療機関番号'].unique()
            
            # Aggregate institution data
            institution_data = []
            for inst_num in institution_numbers:
                inst_records = _df[_df['医療機関番号'] == inst_num]
                first_record = inst_records.iloc[0]
                
                institution_data.append({
                    '医療機関名称': first_record['医療機関名称'],
                    '医療機関番号': inst_num,
                    '医療機関記号番号': first_record.get('医療機関記号番号', ''),
                    '種別': first_record.get('種別', ''),
                    '医療機関所在地（郵便番号）': first_record.get('医療機関所在地（郵便番号）', ''),
                    '医療機関所在地（住所）': first_record.get('医療機関所在地（住所）', ''),
                    '電話番号': first_record.get('電話番号', ''),
                    '病床数': first_record.get('病床数', {}),
                    '届出数': len(inst_records)
                })
            return pd.DataFrame(institution_data)
        
        with st.spinner("検索中..."):
            institution_summary = search_institutions_by_filing(df, selected_filing_name, selected_filing_symbol)
        
        if len(institution_summary) > 0:
            
            st.write(f"**該当医療機関数: {len(institution_summary):,} 件**")
            
            # Format bed count for display
            display_df = institution_summary.copy()
            display_df['病床数'] = display_df['病床数'].apply(format_bed_count)
            
            # Select display columns
            display_columns = ['医療機関名称', '医療機関番号', '医療機関記号番号', '種別', 
                             '医療機関所在地（郵便番号）', '医療機関所在地（住所）', 
                             '電話番号', '病床数', '届出数']
            available_columns = [col for col in display_columns if col in display_df.columns]
            display_df = display_df[available_columns]
            
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )
            
            # Add navigation section
            st.divider()
            st.write("### 📋 届出状況を確認する医療機関を選択:")
            
            # Create buttons in rows of 5
            institution_names = display_df['医療機関名称'].tolist()
            for i in range(0, len(institution_names), 5):
                cols = st.columns(5)
                for j, col in enumerate(cols):
                    if i + j < len(institution_names):
                        institution_name = institution_names[i + j]
                        # Truncate long names
                        display_name = institution_name if len(institution_name) <= 20 else institution_name[:20] + "..."
                        if col.button(f"📋 {display_name}", key=f"search_btn_{i+j}_{institution_name}"):
                            st.session_state['selected_institution'] = institution_name
                            st.switch_page("pages/2_特定医療機関の届出状況.py")
        else:
            st.warning("該当する医療機関が見つかりませんでした。")
    else:
        st.info("検索条件を選択してください。")
else:
    st.error("データを読み込めませんでした。")

