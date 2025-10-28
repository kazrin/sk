import streamlit as st
import pandas as pd

st.title("🏥 医療機関検索システム")

@st.cache_data
def load_data():
    df = pd.read_excel("data/r7/tokyo.xlsx", skiprows=3)
    institutions = df.groupby('医療機関名称').agg({
        '種別': 'first',
        '医療機関所在地（住所）': 'first',
        '受理届出名称': 'count'
    }).rename(columns={
        '種別': '種別',
        '医療機関所在地（住所）': '住所',
        '受理届出名称': '届出数'
    }).reset_index()
    return institutions.sort_values('医療機関名称')

# Load data
institutions = load_data()
st.write(f"総医療機関数: {len(institutions):,} 件")

# Search
search_term = st.text_input("医療機関名で検索", placeholder="医療機関名の一部を入力")

# Filter results
if search_term:
    institutions = institutions[institutions['医療機関名称'].str.contains(search_term, case=False, na=False)]

# Display results
for _, row in institutions.iterrows():
    with st.expander(f"{row['医療機関名称']} ({row['届出数']}件)"):
        st.write(f"種別: {row['種別']}")
        st.write(f"住所: {row['住所']}")
        st.write(f"届出数: {row['届出数']}件")

