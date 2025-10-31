import streamlit as st
import pandas as pd
from utils import load_raw_data

st.title("📋 特定医療機関の届出状況")

# Get selected institution from session state
selected_institution = st.session_state.get('selected_institution', None)

if selected_institution:
    st.write(f"### 医療機関: {selected_institution}")
    
    # Load data
    df = load_raw_data()
    
    # Filter data for selected institution
    institution_data = df[df['医療機関名称'] == selected_institution]
    
    if len(institution_data) > 0:
        # Display basic information
        col1, col2 = st.columns(2)
        
        row_data = institution_data.iloc[0]
        
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
        st.error("指定された医療機関のデータが見つかりませんでした。")
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")

