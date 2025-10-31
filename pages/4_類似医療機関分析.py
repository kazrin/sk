import streamlit as st
import pandas as pd
from utils import load_raw_data, display_institution_basic_info

st.title("🔍 類似医療機関分析")

def calculate_jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity coefficient between two sets"""
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def find_similar_institutions(target_institution, df):
    """Find similar institutions based on filing contents"""
    # Get target institution's filings
    target_data = df[df['医療機関名称'] == target_institution]
    target_filings = set(target_data['受理届出名称'].dropna().unique())
    
    if len(target_filings) == 0:
        return pd.DataFrame()
    
    # Get all institutions and their filings
    institution_filings = {}
    for institution in df['医療機関名称'].unique():
        if institution != target_institution:
            institution_data = df[df['医療機関名称'] == institution]
            filings = set(institution_data['受理届出名称'].dropna().unique())
            institution_filings[institution] = filings
    
    # Calculate similarities
    similarities = []
    for institution, filings in institution_filings.items():
        if len(filings) > 0:
            similarity = calculate_jaccard_similarity(target_filings, filings)
            overlap = target_filings.intersection(filings)
            unique_to_target = target_filings - filings
            unique_to_institution = filings - target_filings
            
            similarities.append({
                '医療機関名称': institution,
                '類似度': similarity,
                '重複届出数': len(overlap),
                '対象機関のみの届出数': len(unique_to_target),
                '類似機関のみの届出数': len(unique_to_institution),
            })
    
    # Convert to DataFrame and sort by similarity
    result_df = pd.DataFrame(similarities)
    if len(result_df) > 0:
        result_df = result_df.sort_values('類似度', ascending=False)
    
    return result_df

# Get selected institution from session state
selected_institution = st.session_state.get('selected_institution', None)

if selected_institution:
    st.write(f"### 対象医療機関: {selected_institution}")
    
    # Load data
    df = load_raw_data()
    
    # Filter data for selected institution
    institution_data = df[df['医療機関名称'] == selected_institution]
    
    # Display basic information
    row_data = institution_data.iloc[0]
    display_institution_basic_info(row_data)
    
    st.divider()
    
    # Calculate and display similar institutions
    st.write("### 🔍 類似医療機関分析")
    
    with st.spinner("類似医療機関を計算中..."):
        similar_df = find_similar_institutions(selected_institution, df)
    
    st.write(f"**類似度上位{len(similar_df)}件の医療機関**")
    
    # Display detailed table
    display_columns = ['医療機関名称', '類似度', '重複届出数', '対象機関のみの届出数', '類似機関のみの届出数']
    
    # Format similarity as percentage
    display_df = similar_df[display_columns].copy()
    display_df['類似度'] = display_df['類似度'].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Add expandable details for each institution
    st.write("### 📋 詳細情報")
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")
