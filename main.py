import streamlit as st

st.title("🏥 医療機関施設基準届出検索システム")

st.markdown("""
## システム概要
このシステムでは、全国の医科医療機関の施設基準届出状況を検索・分析できます。

### 主な機能
- **医療機関検索**: 医療機関名で検索し、届出状況を確認
- **届出医療機関検索**: 施設基準（受理届出名称・記号）から該当医療機関を検索
- **施設基準別届出数**: すべての施設基準の届出数・医療機関数を集計表示
- **特定医療機関の届出状況**: 選択した医療機関の届出詳細を確認
- **類似医療機関分析**: 届出内容から類似する医療機関を分析

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
    if st.button("🔍 届出医療機関検索", use_container_width=True):
        st.switch_page("pages/5_届出医療機関検索.py")

with col3:
    if st.button("📋 施設基準別届出数", use_container_width=True):
        st.switch_page("pages/4_施設基準別届出数.py")

st.markdown("---")
st.markdown("*データソース: 全国医科医療機関 施設基準届出受理医療機関名簿（2025年10月）*")

