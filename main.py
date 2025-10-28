import streamlit as st

st.title("🏥 医療機関検索システム")

st.markdown("""
## システム概要
このシステムでは、医療機関の検索と届出状況の確認ができます。

### 機能
- **医療機関検索**: 医療機関名で検索し、詳細情報を確認
- **届出状況一覧**: すべての届出種別と件数を確認
- **特定医療機関の届出状況**: 選択した医療機関の届出詳細を確認

### 使用方法
1. 左側のメニューから目的のページを選択
2. または下のボタンから直接アクセス
""")

# Navigation buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 医療機関検索", use_container_width=True):
        st.switch_page("pages/1_医療機関検索.py")

with col2:
    if st.button("📋 届出状況一覧", use_container_width=True):
        st.switch_page("pages/2_届出状況一覧.py")

with col3:
    st.info("特定医療機関の届出状況は、医療機関検索からアクセスできます")

st.markdown("---")
st.markdown("*データソース: 東京都医療機関データ*")

