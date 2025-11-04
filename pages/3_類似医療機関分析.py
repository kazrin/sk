import streamlit as st
import pandas as pd
import ast
from utils import load_raw_data, display_institution_basic_info

st.title("🔍 類似医療機関分析")

def calculate_jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity coefficient between two sets"""
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

@st.cache_data(hash_funcs={dict: lambda x: str(x), list: lambda x: str(x)})
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
    
    # Get bed counts for each institution using drop_duplicates
    # This is more efficient than looping
    unique_institutions = df[['医療機関番号', '病床数']].drop_duplicates(subset='医療機関番号', keep='first')
    
    # Convert to dict, handling string to dict conversion
    institution_bed_counts = {}
    for _, row in unique_institutions.iterrows():
        inst_num = row['医療機関番号']
        bed_count = row['病床数']
        
        # If it's a string (JSON-like), convert to dict
        if isinstance(bed_count, str):
            try:
                institution_bed_counts[inst_num] = ast.literal_eval(bed_count)
            except:
                institution_bed_counts[inst_num] = {}
        # If already a dict, use as is
        elif isinstance(bed_count, dict):
            institution_bed_counts[inst_num] = bed_count
        else:
            institution_bed_counts[inst_num] = {}
    
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
        
        # Get bed count from our mapping (should already be a dict)
        bed_count = institution_bed_counts.get(institution_number, {})
        
        # Ensure it's a dict and make a copy
        if not isinstance(bed_count, dict):
            bed_count = {}
        else:
            bed_count = dict(bed_count)
        
        # Extract bed types from bed count dict (keys are bed types)
        bed_types = []
        if bed_count:
            bed_types = [str(k).strip() for k in bed_count.keys() if k is not None and str(k).strip()]
            bed_types = sorted([bt for bt in bed_types if bt])  # Remove empty strings and sort
        
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
    if not similarities:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(similarities)
    
    # Ensure病床数 column is treated as object type to preserve dicts
    if '病床数' in result_df.columns:
        result_df['病床数'] = result_df['病床数'].astype(object)
    
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
        if isinstance(target_bed_count, str):
            try:
                target_bed_count = ast.literal_eval(target_bed_count)
            except:
                target_bed_count = {}
        if isinstance(target_bed_count, dict):
            target_bed_types = [str(k).strip() for k in target_bed_count.keys() if k is not None and str(k).strip()]
        
        # Get all available bed types from similar institutions
        all_bed_types = set()
        for bed_types_list in similar_df['病床種類']:
            if isinstance(bed_types_list, list):
                # Filter out None values and empty strings, and strip whitespace
                cleaned_types = [str(bt).strip() for bt in bed_types_list if bt is not None and str(bt).strip()]
                all_bed_types.update(cleaned_types)
        all_bed_types = sorted([bt for bt in all_bed_types if bt])  # Remove empty strings
        
        # Initialize selected_bed_types
        selected_bed_types = []
        bed_count_filters = {}
        
        # Filter section header with expander
        with st.expander("### フィルター条件", expanded=False):
            st.caption("類似医療機関の検索結果を絞り込みます")
            
            # Bed type filter (multiselect) - default to target institution's bed types only
            if all_bed_types:
                # Default to only the target institution's bed types
                default_selection = [bt for bt in target_bed_types if bt in all_bed_types]
                selected_bed_types = st.multiselect(
                    "病床種類でフィルター:",
                    options=all_bed_types,
                    default=default_selection,
                    key='bed_type_filter',
                    help="選択した病床種類を持つ医療機関のみを表示します"
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
            
            # Bed count filter by bed type
            if selected_bed_types:
                st.write("")
                st.caption("選択した病床種類の病床数範囲でフィルターします")
        
            # Get max bed counts for each selected bed type from filtered_df
            bed_count_max = {}
            if selected_bed_types and len(filtered_df) > 0:
                # Get unique institutions with their bed counts (using 医療機関名称 since 医療機関番号 is not in similar_df)
                unique_institutions = filtered_df[['医療機関名称', '病床数']].drop_duplicates(subset='医療機関名称', keep='first')
                
                # Collect all bed counts for all selected bed types in a single pass
                bed_counts_by_type = {bed_type: [] for bed_type in selected_bed_types}
                
                # Single loop through unique institutions (direct Series iteration is faster than iterrows)
                bed_count_series = unique_institutions['病床数']
                for bed_count_dict in bed_count_series:
                    if isinstance(bed_count_dict, dict):
                        for bed_type in selected_bed_types:
                            if bed_type in bed_count_dict:
                                bed_num = bed_count_dict[bed_type]
                                if isinstance(bed_num, (int, float)) and bed_num is not None:
                                    bed_counts_by_type[bed_type].append(bed_num)
                
                # Calculate max for each bed type
                for bed_type, bed_counts in bed_counts_by_type.items():
                    if bed_counts:
                        bed_count_max[bed_type] = int(max(bed_counts))
            
            # Create bed count filters for each selected bed type (vertical layout)
            if bed_count_max:
                for bed_type, max_val in bed_count_max.items():
                    # Use slider for bed count range (min is always 1)
                    bed_count_range = st.slider(
                        f"{bed_type}の病床数",
                        min_value=1,
                        max_value=max_val,
                        value=(1, max_val),
                        key=f'bed_count_filter_{bed_type}',
                        help=f"範囲: 1〜{max_val}床"
                    )
                    bed_count_filters[bed_type] = bed_count_range
        
        # Apply bed count filters
        if bed_count_filters:
            def passes_bed_count_filter(row):
                """Check if institution passes bed count filters"""
                bed_count_dict = row['病床数']
                if not isinstance(bed_count_dict, dict):
                    return True  # Include records without bed count data
                
                # Check if ALL selected bed type filters are satisfied (AND condition)
                for bed_type, (min_val, max_val) in bed_count_filters.items():
                    # If this bed type exists in the institution's bed count
                    if bed_type in bed_count_dict:
                        bed_num = bed_count_dict[bed_type]
                        if isinstance(bed_num, (int, float)) and bed_num is not None:
                            # Check if it's within the range
                            if not (min_val <= bed_num <= max_val):
                                return False  # Failed this filter condition
                        else:
                            return False  # Invalid bed number
                    else:
                        # If bed type is not in the institution, include it (True)
                        continue  # Skip this filter condition and check others
                
                # All conditions passed
                return True
            
            if len(filtered_df) > 0:
                mask = filtered_df.apply(passes_bed_count_filter, axis=1)
                filtered_df = filtered_df[mask].copy()
        
        st.write(f"**表示件数: {len(filtered_df)}件 (全{len(similar_df)}件中)**")
        
        # Display detailed table
        display_columns = ['医療機関名称', '病床数', '類似度', '重複届出数', '対象機関のみの届出数', '類似機関のみの届出数']
        
        # Format similarity as percentage and format bed count for display
        # Use deep copy to ensure dicts are preserved
        display_df = filtered_df[display_columns].copy(deep=True)
        display_df['類似度'] = display_df['類似度'].apply(lambda x: f"{x:.1%}")
        
        # Format bed count (dict) to display string
        def format_bed_count(bed_count):
            """Format bed count dict to display string"""
            # Convert string to dict if needed
            if isinstance(bed_count, str):
                try:
                    bed_count = ast.literal_eval(bed_count)
                except:
                    return ""
            
            # Handle non-dict cases
            if bed_count is None:
                return ""
            if not isinstance(bed_count, dict):
                return ""
            if not bed_count:  # Empty dict
                return ""
            
            bed_parts = []
            for bed_type, bed_number in bed_count.items():
                # Skip if both are None
                if bed_type is None and bed_number is None:
                    continue
                # Handle different combinations
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
            width='stretch',
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
        
        # Create mapping from 受理届出名称 to 受理記号 (1-to-1 relationship)
        if '受理記号' in df.columns:
            filing_name_to_symbol = (
                df.groupby('受理届出名称')['受理記号']
                .first()
                .to_dict()
            )
        else:
            filing_name_to_symbol = {}
        
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
            # Build data for cross-tabulation
            rows_data = []
            
            for filing_type in all_filing_types:
                row_data = {
                    '受理届出名称': filing_type,
                    '受理記号': filing_name_to_symbol.get(filing_type, '')
                }
                
                # First, add target institution's filing status
                target_filing_types_set = institution_filings_by_number.get(target_institution_number, set())
                row_data[selected_institution] = filing_type in target_filing_types_set
                
                # Then, add top 20 institutions' filing status
                for institution_name in top_20_institutions:
                    institution_number = institution_number_mapping.get(institution_name)
                    if institution_number:
                        filing_types_set = institution_filings_by_number.get(institution_number, set())
                        row_data[institution_name] = filing_type in filing_types_set
                    else:
                        row_data[institution_name] = False
                
                rows_data.append(row_data)
            
            # Create DataFrame with 受理届出名称 and 受理記号 as columns
            cross_tab_df = pd.DataFrame(rows_data)
            # Set 受理届出名称 as index for filtering, but we'll display it as a column
            cross_tab_df = cross_tab_df.set_index('受理届出名称')
            
            # Filter: Show only filing types that target institution has NOT filed
            show_only_unfiled = st.checkbox(
                "対象医療機関が未届の施設基準のみ表示",
                value=False,
                key='show_only_unfiled_filter'
            )
            
            if show_only_unfiled:
                # Filter rows where target institution column is False
                filtered_cross_tab_df = cross_tab_df[cross_tab_df[selected_institution] == False].copy()
            else:
                filtered_cross_tab_df = cross_tab_df.copy()
            
            # Reset index to display 受理届出名称 as a regular column
            display_df = filtered_cross_tab_df.reset_index()
            
            # Reorder columns: 受理届出名称, 受理記号, then institution columns
            institution_columns = [selected_institution] + top_20_institutions
            display_columns = ['受理届出名称', '受理記号'] + institution_columns
            display_df = display_df[display_columns]
            
            # Display the table
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )
        
        # Add explanation about Jaccard similarity at the end
        st.divider()
        st.write("### 📖 類似度の計算方法について")
        st.markdown("""
        **Jaccard係数（Jaccard similarity coefficient）**を使用して類似度を計算しています。
        
        Jaccard係数は、2つの集合がどれだけ似ているかを測る指標で、以下の式で計算されます：
        
        $$
        J(A, B) = \\frac{|A \\cap B|}{|A \\cup B|} = \\frac{\\text{共通要素数}}{\\text{全要素数}}
        $$
        
        **具体例：**
        
        医療機関Aの届出施設基準：`{基本診療料, 特掲診療料1, 特掲診療料2}`
        
        医療機関Bの届出施設基準：`{基本診療料, 特掲診療料2, 特掲診療料3}`
        
        - **共通する届出（積集合）**: `{基本診療料, 特掲診療料2}` → 2個
        - **すべての届出（和集合）**: `{基本診療料, 特掲診療料1, 特掲診療料2, 特掲診療料3}` → 4個
        - **Jaccard係数**: 2 ÷ 4 = 0.5 (50%)
        
        Jaccard係数は0から1の値を取り、1に近いほど類似度が高く、0に近いほど類似度が低いことを示します。
        """)
else:
    st.info("医療機関検索ページから医療機関を検索して選択してください。")
