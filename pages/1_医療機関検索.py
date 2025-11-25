import streamlit as st
from utils import load_raw_data

st.title("🏥 医科医療機関検索")

# Maximum number of results to display
MAX_DISPLAY_RESULTS = 500

# Create display columns
DISPLAY_COLUMNS = [
    "医療機関名称",
    "医療機関番号",
    "都道府県名",
    "病床数",
    "届出数",
    "医療機関所在地（郵便番号）",
    "医療機関所在地（住所）",
    "電話番号",
    "FAX番号",
    "医療機関記号番号",
    "種別",
]


@st.cache_resource
def load_stats_data():
    df = load_raw_data()
    institutions = df.aggregate_by_institution_name()
    return institutions.sort_values("医療機関名称")


def limit_and_display_results(df, max_results, label_prefix="結果", sort_column=None, ascending=False):
    """Limit results to max_results and display with count message

    Args:
        df: DataFrame to limit and display
        max_results: Maximum number of results to display
        label_prefix: Prefix for the count message (default: "結果")
        sort_column: Column name to sort by before limiting (optional)
        ascending: Sort order (default: False, descending)

    Returns:
        Limited DataFrame ready for display
    """
    total_count = len(df)

    # Sort if sort_column is provided
    if sort_column and sort_column in df.columns:
        df = df.sort_values(sort_column, ascending=ascending)

    # Limit results
    limited_df = df.head(max_results)

    # Display count message
    if total_count > max_results:
        st.write(f"{label_prefix}: {total_count:,} 件 (表示件数: 上位{max_results}件に絞りました)")
    else:
        st.write(f"{label_prefix}: {total_count:,} 件")

    return limited_df


def display_institutions_table(df, display_columns):
    """Display institutions dataframe and create selection buttons

    Args:
        df: DataFrame to display
        display_columns: List of column names to display (only existing columns will be used)
    """
    # Select columns that exist in the dataframe
    available_columns = [col for col in display_columns if col in df.columns]
    # Create display dataframe with available columns
    display_df = df[available_columns].copy()

    # Display results in table format
    st.dataframe(display_df, hide_index=True)

    # Add navigation section
    st.divider()
    st.write("### 📋 届出状況を確認する医療機関を選択:")

    # Create buttons in rows of 5
    institution_names = display_df["医療機関名称"].tolist()
    for i in range(0, len(institution_names), 5):
        cols = st.columns(5)
        for j, col in enumerate(cols):
            if i + j < len(institution_names):
                institution_name = institution_names[i + j]
                # Truncate long names
                display_name = institution_name if len(institution_name) <= 20 else institution_name[:20] + "..."
                button_key = f"institution_btn_{i + j}_{institution_name}"
                if col.button(f"📋 {display_name}", key=button_key):
                    st.session_state["selected_institution"] = institution_name
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
        # Limit and display results
        filtered_institutions = limit_and_display_results(filtered_institutions, MAX_DISPLAY_RESULTS, label_prefix="検索結果")

        # Display table
        display_institutions_table(filtered_institutions, DISPLAY_COLUMNS)
    else:
        st.warning("該当する医療機関が見つかりませんでした。")
else:
    # Display all institutions when no search term (limited to top MAX_DISPLAY_RESULTS)
    institutions_display = limit_and_display_results(
        institutions, MAX_DISPLAY_RESULTS, label_prefix="医療機関一覧", sort_column="届出数", ascending=False
    )

    # Display table
    display_institutions_table(institutions_display, DISPLAY_COLUMNS)
