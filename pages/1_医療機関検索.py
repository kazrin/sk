import streamlit as st
from utils import load_raw_data

st.title("🏥 医科医療機関検索")

# Maximum number of results to display
MAX_DISPLAY_RESULTS = 500

# Create display columns
DISPLAY_COLUMNS = ['医療機関名称', '医療機関番号', '都道府県名', '病床数', '届出数', 
                   '医療機関所在地（郵便番号）', '医療機関所在地（住所）', 
                   '電話番号', 'FAX番号', '医療機関記号番号', '種別']

@st.cache_data(hash_funcs={dict: lambda x: str(x)})
def load_stats_data():
    df = load_raw_data()
    institutions = df.aggregate_by_institution_name()
    return institutions.sort_values('医療機関名称')

def display_institutions_table(df, available_columns):
    """Display institutions dataframe and create selection buttons"""
    # Create display dataframe with available columns
    display_df = df[available_columns].copy()
    
    # Display results in table format
    st.dataframe(
        display_df,
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
                button_key = f"institution_btn_{i+j}_{institution_name}"
                if col.button(f"📋 {display_name}", key=button_key):
                    st.session_state['selected_institution'] = institution_name
                    st.switch_page("pages/2_特定医療機関の届出状況.py")

# Load data
institutions = load_stats_data()
st.write(f"総医療機関数: {len(institutions):,} 件")

# Search
search_term = st.text_input("医療機関名で検索", placeholder="医療機関名の一部を入力")

# Filter results
if search_term:
    filtered_institutions = institutions.filter_by_institution_name(search_term)
    
    if len(filtered_institutions) > 0:
        total_count = len(filtered_institutions)
        # Limit to top MAX_DISPLAY_RESULTS results
        filtered_institutions = filtered_institutions.head(MAX_DISPLAY_RESULTS)
        if total_count > MAX_DISPLAY_RESULTS:
            st.write(f"検索結果: {total_count:,} 件 (表示件数: 上位{MAX_DISPLAY_RESULTS}件に絞りました)")
        else:
            st.write(f"検索結果: {total_count:,} 件")
        
        # Select columns that exist in the dataframe
        available_columns = [col for col in DISPLAY_COLUMNS if col in filtered_institutions.columns]
        
        # Display institutions table with selection buttons
        display_institutions_table(filtered_institutions, available_columns)
    else:
        st.warning("該当する医療機関が見つかりませんでした。")
else:
    # Display all institutions when no search term (limited to top MAX_DISPLAY_RESULTS)
    total_count = len(institutions)
    institutions_display = institutions.sort_values('届出数', ascending=False).head(MAX_DISPLAY_RESULTS)
    if total_count > MAX_DISPLAY_RESULTS:
        st.write(f"医療機関一覧 (総数: {total_count:,}件、表示件数: 上位{MAX_DISPLAY_RESULTS}件に絞りました):")
    else:
        st.write(f"医療機関一覧 ({total_count:,}件):")
    
    # Select columns that exist in the dataframe
    available_columns = [col for col in DISPLAY_COLUMNS if col in institutions_display.columns]
    
    # Display institutions table with selection buttons
    display_institutions_table(institutions_display, available_columns)
