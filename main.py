import streamlit as st
import pandas as pd

st.title("🏥 医療機関検索システム")

# Configuration
MAX_DISPLAY_COUNT = 50

def display_institution_info(row):
    """Display institution information in expander"""
    with st.expander(f"{row['医療機関名称']} ({row['届出数']}件)"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**医療機関番号:** {row['医療機関番号']}")
            st.write(f"**併設医療機関番号:** {row['併設医療機関番号']}")
            st.write(f"**医療機関記号番号:** {row['医療機関記号番号']}")
            st.write(f"**種別:** {row['種別']}")
            st.write(f"**届出数:** {row['届出数']}件")
        
        with col2:
            st.write(f"**郵便番号:** {row['医療機関所在地（郵便番号）']}")
            st.write(f"**住所:** {row['医療機関所在地（住所）']}")
            st.write(f"**電話番号:** {row['電話番号']}")
            st.write(f"**FAX番号:** {row['FAX番号']}")
            st.write(f"**病床数:** {row['病床数']}")

@st.cache_data
def load_data():
    df = pd.read_excel("data/r7/tokyo.xlsx", skiprows=3)
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
institutions = load_data()
st.write(f"総医療機関数: {len(institutions):,} 件")

# Search
search_term = st.text_input("医療機関名で検索", placeholder="医療機関名の一部を入力")

# Filter results
if search_term:
    filtered_institutions = institutions[institutions['医療機関名称'].str.contains(search_term, case=False, na=False)]
    
    if len(filtered_institutions) > 0:
        st.write(f"検索結果: {len(filtered_institutions)} 件")
        
        # Display results (limit to MAX_DISPLAY_COUNT for performance)
        display_count = min(MAX_DISPLAY_COUNT, len(filtered_institutions))
        if len(filtered_institutions) > MAX_DISPLAY_COUNT:
            st.info(f"表示件数を{MAX_DISPLAY_COUNT}件に制限しています（全{len(filtered_institutions)}件中）")
        
        for _, row in filtered_institutions.head(display_count).iterrows():
            display_institution_info(row)
    else:
        st.warning("該当する医療機関が見つかりませんでした。")
else:
    # Display top institutions when no search term
    st.write(f"上位{MAX_DISPLAY_COUNT}件の医療機関一覧:")
    
    for _, row in institutions.head(MAX_DISPLAY_COUNT).iterrows():
        display_institution_info(row)

