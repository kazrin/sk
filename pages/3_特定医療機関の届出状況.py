import streamlit as st
import pandas as pd

st.title("📋 特定医療機関の届出状況")

@st.cache_data
def load_raw_data():
    return pd.read_excel("data/r7/tokyo.xlsx", skiprows=3)

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
        
        with col1:
            st.write(f"**医療機関番号:** {institution_data.iloc[0]['医療機関番号']}")
            st.write(f"**医療機関記号番号:** {institution_data.iloc[0]['医療機関記号番号']}")
            st.write(f"**種別:** {institution_data.iloc[0]['種別']}")
        
        with col2:
            st.write(f"**郵便番号:** {institution_data.iloc[0]['医療機関所在地（郵便番号）']}")
            st.write(f"**住所:** {institution_data.iloc[0]['医療機関所在地（住所）']}")
            st.write(f"**電話番号:** {institution_data.iloc[0]['電話番号']}")
        
        st.divider()
        
        # Display filing statuses
        st.write(f"### 届出状況一覧 ({len(institution_data)}件)")
        
        # Group by filing status and count
        filing_status = institution_data.groupby('受理届出名称').size().reset_index(name='件数')
        filing_status = filing_status.sort_values('件数', ascending=False)
        
        for _, row in filing_status.iterrows():
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{row['受理届出名称']}**")
                with col2:
                    st.metric("件数", f"{row['件数']:,}")
                st.divider()
    else:
        st.error("指定された医療機関のデータが見つかりませんでした。")
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")

