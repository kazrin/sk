import streamlit as st
import pandas as pd
from utils import load_raw_data, format_bed_count
from dataframes import ShisetsuKijunDataFrame

st.title("🔍 届出医療機関検索")

# Create display columns (matching 医科医療機関検索)
DISPLAY_COLUMNS = ['医療機関名称', '医療機関番号', '都道府県名', '病床数', '届出数', 
                   '算定開始年月日', '医療機関所在地（郵便番号）', '医療機関所在地（住所）', 
                   '電話番号', 'FAX番号', '医療機関記号番号', '種別']

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
filing_display_options = df.get_filing_options()

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
        
        with st.spinner("検索中..."):
            institution_summary = df.search_institutions_by_filing(selected_filing_name, selected_filing_symbol)
        
        if len(institution_summary) > 0:
            st.write(f"**該当医療機関数: {len(institution_summary):,} 件**")
            
            # Filter section
            st.divider()
            st.write("### フィルター条件")
            
            # Ensure institution_summary is ShisetsuKijunDataFrame
            if not isinstance(institution_summary, ShisetsuKijunDataFrame):
                institution_summary = ShisetsuKijunDataFrame(institution_summary)
            
            # Get all available bed types from filtered results
            all_bed_types = institution_summary.get_all_bed_types()
            
            selected_bed_types = []
            bed_count_filters = {}
            
            with st.expander("### フィルター条件", expanded=False):
                st.caption("検索結果を病床種別・病床数で絞り込みます")
                
                if all_bed_types:
                    selected_bed_types = st.multiselect(
                        "病床種類でフィルター:",
                        options=all_bed_types,
                        default=all_bed_types,  # Default to all bed types selected
                        key='filing_search_bed_type_filter',
                        help="選択した病床種類を持つ医療機関のみを表示します"
                    )
                else:
                    st.warning("⚠️ 病床種別データが見つかりませんでした。")
                    selected_bed_types = []
                
                # Bed count filter by bed type
                if selected_bed_types:
                    st.write("")
                    st.caption("選択した病床種類の病床数範囲でフィルターします")
                    
                    # Get max bed counts for each selected bed type from filtered results
                    bed_count_max = institution_summary.get_bed_count_max(selected_bed_types)
                    
                    # Create bed count filters for each selected bed type (vertical layout)
                    if bed_count_max:
                        for bed_type, max_val in bed_count_max.items():
                            # Use slider for bed count range (min is always 1)
                            bed_count_range = st.slider(
                                f"{bed_type}の病床数",
                                min_value=1,
                                max_value=max_val,
                                value=(1, max_val),
                                key=f'filing_search_bed_count_filter_{bed_type}',
                                help=f"範囲: 1〜{max_val}床"
                            )
                            bed_count_filters[bed_type] = bed_count_range
            
            # Apply filters (outside expander)
            filtered_institution_summary = institution_summary.copy()
            if selected_bed_types:
                filtered_institution_summary = filtered_institution_summary.filter_by_bed_types(selected_bed_types)
            if bed_count_filters:
                filtered_institution_summary = filtered_institution_summary.filter_by_bed_counts(bed_count_filters)
            
            st.write(f"**表示件数: {len(filtered_institution_summary):,} 件 (全{len(institution_summary):,} 件中)**")
            
            # Create trend chart for 算定開始年月日 (using filtered data)
            if '算定開始年月日_date' in filtered_institution_summary.columns:
                # Filter out null dates and create month column
                date_df = filtered_institution_summary[filtered_institution_summary['算定開始年月日_date'].notna()].copy()
                if len(date_df) > 0:
                    # Extract year-month from date
                    date_df['month'] = date_df['算定開始年月日_date'].dt.to_period('M').astype(str)
                    # Count by month
                    monthly_counts = date_df.groupby('month').size().reset_index(name='count')
                    monthly_counts = monthly_counts.sort_values('month')
                    
                    # Display trend chart
                    st.write("### 📈 算定開始年月日のトレンド")
                    st.line_chart(
                        monthly_counts.set_index('month'),
                        y='count'
                    )
                    st.divider()
            
            # Format bed count for display (using filtered data)
            display_df = filtered_institution_summary.copy()
            display_df['病床数'] = display_df['病床数'].apply(format_bed_count)
            
            # Format date column for display and rename
            if '算定開始年月日_date' in display_df.columns:
                display_df['算定開始年月日'] = display_df['算定開始年月日_date'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None
                )
                display_df = display_df.drop(columns=['算定開始年月日_date'])
            
            # Select display columns (matching 医科医療機関検索 column order)
            available_columns = [col for col in DISPLAY_COLUMNS if col in display_df.columns]
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

