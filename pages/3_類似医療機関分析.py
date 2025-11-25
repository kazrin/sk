import ast

import streamlit as st
from dataframes import JaccardSimilarityDataFrame, ShisetsuKijunDataFrame, ShisetsuKijunFilingCrossTabDataFrame
from utils import display_institution_basic_info, format_bed_count, load_raw_data

st.title("🔍 類似医療機関分析")


@st.cache_resource
def find_similar_institutions(target_institution, _df):
    """Find similar institutions based on filing contents"""
    # Convert to ShisetsuKijunDataFrame if not already
    if not isinstance(_df, ShisetsuKijunDataFrame):
        _df = ShisetsuKijunDataFrame(_df)

    return JaccardSimilarityDataFrame.from_shisetsu_kijun(_df, target_institution)


# Get selected institution from session state
selected_institution = st.session_state.get("selected_institution", None)

if selected_institution:
    st.write(f"### 対象医療機関: {selected_institution}")

    # Load data
    df = load_raw_data()

    # Filter data for selected institution
    institution_data = df.filter_by_exact_institution_name(selected_institution)

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
        target_bed_count = row_data.get("病床数", {})
        target_bed_types = []
        if isinstance(target_bed_count, str):
            try:
                target_bed_count = ast.literal_eval(target_bed_count)
            except (ValueError, SyntaxError):
                target_bed_count = {}
        if isinstance(target_bed_count, dict):
            target_bed_types = [str(k).strip() for k in target_bed_count.keys() if k is not None and str(k).strip()]

        # Get all available bed types from similar institutions
        from dataframes import JaccardSimilarityDataFrame

        # similar_df is already JaccardSimilarityDataFrame from calculate_jaccard_similarity
        all_bed_types = similar_df.get_all_bed_types()

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
                    key="bed_type_filter",
                    help="選択した病床種類を持つ医療機関のみを表示します",
                )

                # Filter by selected bed types
                if selected_bed_types:
                    filtered_df = similar_df.filter_by_bed_types(selected_bed_types)
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
            if selected_bed_types and len(filtered_df) > 0:
                # Get max bed counts (JaccardSimilarityDataFrame has this method)
                bed_count_max = filtered_df.get_bed_count_max(selected_bed_types)

                # Create bed count filters for each selected bed type (vertical layout)
                if bed_count_max:
                    for bed_type, max_val in bed_count_max.items():
                        # Use slider for bed count range (min is always 1)
                        bed_count_range = st.slider(
                            f"{bed_type}の病床数",
                            min_value=1,
                            max_value=max_val,
                            value=(1, max_val),
                            key=f"bed_count_filter_{bed_type}",
                            help=f"範囲: 1〜{max_val}床",
                        )
                        bed_count_filters[bed_type] = bed_count_range

        # Apply bed count filters
        if bed_count_filters and len(filtered_df) > 0:
            # JaccardSimilarityDataFrame has this method
            filtered_df = filtered_df.filter_by_bed_counts_generic(bed_count_filters)

        st.write(f"**表示件数: {len(filtered_df)}件 (全{len(similar_df)}件中)**")

        # Display detailed table
        display_columns = ["医療機関名称", "病床数", "類似度", "重複届出数", "対象機関のみの届出数", "類似機関のみの届出数"]

        # Format similarity as percentage and format bed count for display
        # Use deep copy to ensure dicts are preserved
        display_df = filtered_df[display_columns].copy(deep=True)
        display_df["類似度"] = display_df["類似度"].apply(lambda x: f"{x:.1%}")
        display_df["病床数"] = display_df["病床数"].apply(format_bed_count)

        st.dataframe(display_df, width="stretch", hide_index=True)

        # Create cross-tabulation table for top 20 similar institutions
        st.write("### 📊 申請施設基準の届出状況（類似度上位20件）")

        # Get target institution number for optimization (already computed earlier)
        target_institution_number = row_data["医療機関番号"]

        # Get top 20 institutions for cross-tabulation
        top_20_filtered_df = filtered_df.head(20)

        # Create cross-tabulation DataFrame (no caching - always recalculate to reflect filter changes)
        with st.spinner("申請施設基準の届出状況を計算中..."):
            cross_tab_df = ShisetsuKijunFilingCrossTabDataFrame.from_jaccard_similarity(
                top_20_filtered_df, df, selected_institution, top_n=20, target_institution_number=target_institution_number
            )

        if len(cross_tab_df) > 0:
            # Filter: Show only filing types that target institution has NOT filed
            show_only_unfiled = st.checkbox(
                "対象医療機関が未届の施設基準のみ表示", value=False, key="show_only_unfiled_filter"
            )

            if show_only_unfiled:
                filtered_cross_tab_df = cross_tab_df.filter_unfiled_by_target(selected_institution)
            else:
                filtered_cross_tab_df = cross_tab_df

            # Get display DataFrame with proper column order
            display_df = filtered_cross_tab_df.get_display_dataframe(selected_institution)

            # Display the table
            st.dataframe(display_df, width="stretch", hide_index=True)

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
