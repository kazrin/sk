import streamlit as st
from utils import load_raw_data

st.title("🏥 医療機関検索システム")

# Navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("📋 届出状況一覧を見る"):
        st.switch_page("pages/2_届出状況一覧.py")

# Create display columns
DISPLAY_COLUMNS = ['医療機関名称', '医療機関番号', '医療機関記号番号', '種別', '届出数', 
                   '医療機関所在地（郵便番号）', '医療機関所在地（住所）', '電話番号', '病床数']

@st.cache_data
def load_stats_data():
    df = load_raw_data()
    institutions = df.groupby('医療機関名称').agg({
        '医療機関番号': 'first',
        '併設医療機関番号': 'first',
        '医療機関記号番号': 'first',
        '医療機関所在地（郵便番号）': 'first',
        '医療機関所在地（住所）': 'first',
        '電話番号': 'first',
        'FAX番号': 'first',
        '病床数': 'first',
        '種別': 'first',
        '受理届出名称': 'count'
    }).rename(columns={
        '受理届出名称': '届出数' # 届出数を受理届出名称の件数に変更
    }).reset_index()
    return institutions.sort_values('医療機関名称')

# Load data
institutions = load_stats_data()
st.write(f"総医療機関数: {len(institutions):,} 件")

# Search
search_term = st.text_input("医療機関名で検索", placeholder="医療機関名の一部を入力")

# Filter results
if search_term:
    filtered_institutions = institutions[institutions['医療機関名称'].str.contains(search_term, case=False, na=False)]
    
    if len(filtered_institutions) > 0:
        st.write(f"検索結果: {len(filtered_institutions)} 件")
        
        # Select columns that exist in the dataframe
        available_columns = [col for col in DISPLAY_COLUMNS if col in filtered_institutions.columns]
        
        # Create display dataframe
        display_df = filtered_institutions[available_columns].copy()
        
        # Display results in table format
        st.dataframe(
            display_df,
            use_container_width=True,
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
                    if col.button(f"📋 {institution_name[:20]}...", key=f"result_btn_{i+j}_{institution_name}"):
                        st.session_state['selected_institution'] = institution_name
                        st.switch_page("pages/3_特定医療機関の届出状況.py")
    else:
        st.warning("該当する医療機関が見つかりませんでした。")
else:
    # Display all institutions when no search term
    st.write(f"医療機関一覧 ({len(institutions)}件):")
    
    # Select columns that exist in the dataframe
    available_columns = [col for col in DISPLAY_COLUMNS if col in institutions.columns]
    
    # Create display dataframe
    display_df = institutions[available_columns].copy()
    
    # Display results in table format
    st.dataframe(
        display_df,
        use_container_width=True,
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
                if col.button(f"📋 {display_name}", key=f"list_btn_{i+j}_{institution_name}"):
                    st.session_state['selected_institution'] = institution_name
                    st.switch_page("pages/3_特定医療機関の届出状況.py")
