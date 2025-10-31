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
    # Get target institution's number first
    target_institution_data = df[df['医療機関名称'] == target_institution]
    if len(target_institution_data) == 0:
        return pd.DataFrame()
    
    target_institution_number = target_institution_data.iloc[0]['医療機関番号']
    
    # Pre-group all institutions' filings by institution number (more accurate than name)
    institution_filings_dict = (
        df.groupby('医療機関番号')['受理届出名称']
        .apply(lambda x: set(x.dropna().unique()))
        .to_dict()
    )
    
    # Get institution name mapping (number -> name)
    institution_name_mapping = (
        df.groupby('医療機関番号')['医療機関名称']
        .first()
        .to_dict()
    )
    
    # Pre-group all institutions' bed counts by institution number
    def aggregate_bed_types(group):
        """Aggregate all bed types from all records of an institution"""
        all_bed_types = set()
        for bed_count in group:
            if isinstance(bed_count, dict):
                # Get bed types and clean them (remove None, strip whitespace)
                bed_types = [str(k).strip() for k in bed_count.keys() if k is not None and str(k).strip()]
                all_bed_types.update(bed_types)
        # Return sorted list of unique bed types
        return sorted([bt for bt in all_bed_types if bt])
    
    institution_bed_types = (
        df.groupby('医療機関番号')['病床数']
        .apply(aggregate_bed_types)
        .to_dict()
    )
    
    # Get bed counts (dict) for each institution
    institution_bed_counts = (
        df.groupby('医療機関番号')['病床数']
        .first()
        .to_dict()
    )
    
    # Get target institution's filings
    target_filings = institution_filings_dict.get(target_institution_number, set())
    
    if len(target_filings) == 0:
        return pd.DataFrame()
    
    # Calculate similarities for all other institutions
    similarities = []
    for institution_number, filings in institution_filings_dict.items():
        if institution_number == target_institution_number or len(filings) == 0:
            continue
        
        similarity = calculate_jaccard_similarity(target_filings, filings)
        overlap = target_filings.intersection(filings)
        unique_to_target = target_filings - filings
        unique_to_institution = filings - target_filings
        
        # Get bed types and bed count for this institution
        bed_types = institution_bed_types.get(institution_number, [])
        bed_count = institution_bed_counts.get(institution_number, {})
        
        # Get institution name
        institution_name = institution_name_mapping.get(institution_number, f"医療機関番号: {institution_number}")
        
        similarities.append({
            '医療機関名称': institution_name,
            '病床種類': bed_types,
            '病床数': bed_count,
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
    
    if len(similar_df) > 0:
        # Get target institution's bed types for default filter
        target_bed_count = row_data.get('病床数', {})
        target_bed_types = []
        if isinstance(target_bed_count, dict):
            target_bed_types = [k for k in target_bed_count.keys() if k is not None]
        
        # Get all available bed types from similar institutions
        all_bed_types = set()
        for bed_types_list in similar_df['病床種類']:
            if isinstance(bed_types_list, list):
                # Filter out None values and empty strings, and strip whitespace
                cleaned_types = [str(bt).strip() for bt in bed_types_list if bt is not None and str(bt).strip()]
                all_bed_types.update(cleaned_types)
        all_bed_types = sorted([bt for bt in all_bed_types if bt])  # Remove empty strings
        
        # Bed type filter (multiselect)
        if all_bed_types:
            default_selection = target_bed_types if target_bed_types else all_bed_types
            selected_bed_types = st.multiselect(
                "病床種類でフィルター:",
                options=all_bed_types,
                default=default_selection,
                key='bed_type_filter'
            )
            
            # Filter by selected bed types
            if selected_bed_types:
                # Filter institutions that have at least one of the selected bed types
                mask = similar_df['病床種類'].apply(
                    lambda x: bool(set(x).intersection(set(selected_bed_types)))
                )
                filtered_df = similar_df[mask].copy()
            else:
                # If no selection, show all
                filtered_df = similar_df.copy()
        else:
            # No bed types available, show all
            filtered_df = similar_df.copy()
        
        st.write(f"**表示件数: {len(filtered_df)}件 (全{len(similar_df)}件中)**")
        
        # Display detailed table
        display_columns = ['医療機関名称', '病床数', '類似度', '重複届出数', '対象機関のみの届出数', '類似機関のみの届出数']
        
        # Format similarity as percentage and format bed count for display
        display_df = filtered_df[display_columns].copy()
        display_df['類似度'] = display_df['類似度'].apply(lambda x: f"{x:.1%}")
        
        # Format bed count (dict) to display string
        def format_bed_count(bed_count):
            """Format bed count dict to display string"""
            if not isinstance(bed_count, dict) or not bed_count:
                return ""
            bed_parts = []
            for bed_type, bed_number in bed_count.items():
                if bed_type is None and bed_number is not None:
                    bed_parts.append(str(bed_number))
                elif bed_type is not None and bed_number is None:
                    bed_parts.append(str(bed_type))
                elif bed_type is not None and bed_number is not None:
                    bed_parts.append(f"{bed_type} {bed_number}")
            return " / ".join(bed_parts)
        
        display_df['病床数'] = display_df['病床数'].apply(format_bed_count)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Create cross-tabulation table for top 20 similar institutions
        st.write("### 📊 申請施設基準の届出状況（類似度上位20件）")
        
        # Get top 20 institutions
        top_20_df = filtered_df.head(20).copy()
        top_20_institutions = top_20_df['医療機関名称'].tolist()
        
        # Pre-compute institution filings by institution number (for performance)
        institution_filings_by_number = (
            df.groupby('医療機関番号')['受理届出名称']
            .apply(lambda x: set(x.dropna().unique()))
            .to_dict()
        )
        
        # Get institution numbers for these institutions
        institution_number_mapping = (
            df.groupby('医療機関名称')['医療機関番号']
            .first()
            .to_dict()
        )
        
        # Get all filing types (施設基準) from target and top 20 institutions
        all_filing_types = set()
        
        # Get target institution's filing types
        target_institution_number = institution_data.iloc[0]['医療機関番号']
        target_filing_types = institution_filings_by_number.get(target_institution_number, set())
        all_filing_types.update(target_filing_types)
        
        # Get top 20 institutions' filing types
        for institution_name in top_20_institutions:
            institution_number = institution_number_mapping.get(institution_name)
            if institution_number:
                filing_types = institution_filings_by_number.get(institution_number, set())
                all_filing_types.update(filing_types)
        
        all_filing_types = sorted(list(all_filing_types))
        
        if all_filing_types and top_20_institutions:
            # Create cross-tabulation matrix
            cross_tab_data = {}
            
            for filing_type in all_filing_types:
                row = []
                for institution_name in top_20_institutions:
                    institution_number = institution_number_mapping.get(institution_name)
                    if institution_number:
                        filing_types_set = institution_filings_by_number.get(institution_number, set())
                        has_filing = filing_type in filing_types_set
                        row.append(has_filing)
                    else:
                        row.append(False)
                cross_tab_data[filing_type] = row
            
            # Create DataFrame
            cross_tab_df = pd.DataFrame(cross_tab_data, index=top_20_institutions)
            # Transpose to have filing types as rows and institutions as columns
            cross_tab_df = cross_tab_df.T
            
            # Display the table
            st.dataframe(
                cross_tab_df,
                use_container_width=True
            )
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")

# Back button
if st.button("← ホームページに戻る"):
    st.switch_page("main.py")
