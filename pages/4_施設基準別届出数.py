import streamlit as st
import pandas as pd
from utils import load_raw_data

st.title("📋 施設基準別届出数")

# Navigation button
col1, col2 = st.columns(2)
with col1:
    if st.button("← ホームページに戻る"):
        st.switch_page("main.py")

# Load raw data
df = load_raw_data()

# Aggregation conditions
st.write("### 集計条件")
st.caption("集計対象とする医療機関の条件を設定します")

# Bed type filter (always enabled, default to all)
# Get all available bed types
all_bed_types = set()
for bed_count in df['病床数']:
    if isinstance(bed_count, dict):
        bed_types = [str(k).strip() for k in bed_count.keys() if k is not None and str(k).strip()]
        all_bed_types.update(bed_types)
all_bed_types = sorted([bt for bt in all_bed_types if bt])

selected_bed_types = []
if all_bed_types:
    selected_bed_types = st.multiselect(
        "病床種類を選択:",
        options=all_bed_types,
        default=all_bed_types,  # Default to all bed types selected
        key='bed_type_multiselect',
        help="選択した病床種類を持つ医療機関の届出のみを集計対象とします"
    )

# Display filter
st.write("### 表示フィルター")
st.caption("集計結果の表示内容を絞り込みます")

# Facility criteria filter (改行区切り入力, always enabled)
criteria_input = st.text_area(
    "施設基準を改行区切りで入力:",
    placeholder="施設基準1\n施設基準2\n施設基準3",
    key='facility_criteria_input',
    height=100,
    help="空白の場合はすべて表示、入力時は完全一致する施設基準のみを表示します。受理届出名称または受理記号のいずれかに一致するものが表示されます。入力後、テキストボックスからフォーカスを外すと絞り込みが反映されます。"
)

selected_facility_criteria = []
if criteria_input:
    selected_facility_criteria = [line.strip() for line in criteria_input.split('\n') if line.strip()]

# Apply filters and calculate filing status
st.write("### 集計結果")

# Filter data by bed type
filtered_df = df.copy()
if selected_bed_types:
    # Get institutions (by institution number) that have selected bed types
    def aggregate_bed_types(group):
        """Aggregate all bed types from all records of an institution"""
        all_bed_types = set()
        for bed_count in group:
            if isinstance(bed_count, dict):
                bed_types = [str(k).strip() for k in bed_count.keys() if k is not None and str(k).strip()]
                all_bed_types.update(bed_types)
        return all_bed_types
    
    institution_bed_types = (
        df.groupby('医療機関番号')['病床数']
        .apply(aggregate_bed_types)
        .to_dict()
    )
    
    # Filter institutions that have at least one of the selected bed types
    filtered_institution_numbers = {
        inst_num for inst_num, bed_types in institution_bed_types.items()
        if set(selected_bed_types).intersection(bed_types)
    }
    
    # Filter data to only include filtered institutions
    mask = filtered_df['医療機関番号'].isin(filtered_institution_numbers)
    filtered_df = filtered_df[mask]

# Get total number of institutions in filtered data (by institution number)
total_institutions = filtered_df['医療機関番号'].nunique()

# Calculate filing status counts and institution counts
# Group by both 受理届出名称 and 受理記号 (1-to-1 relationship)
groupby_columns = ['受理届出名称']
if '受理記号' in filtered_df.columns:
    groupby_columns.append('受理記号')

filing_status = (
    filtered_df.groupby(groupby_columns)
    .agg({
        '医療機関番号': 'nunique',  # Number of unique institutions
        '受理届出名称': 'count'     # Total count of filings
    })
    .rename(columns={
        '医療機関番号': '届出医療機関数',
        '受理届出名称': '件数'
    })
    .reset_index()
)

# Calculate percentage
filing_status['届出医療機関割合'] = (
    filing_status['届出医療機関数'] / total_institutions * 100
).round(2)

# Filter by facility criteria (exact match if criteria are provided)
# Match against either 受理届出名称 or 受理記号
if selected_facility_criteria:
    # Filter filing statuses that exactly match the input criteria
    name_mask = filing_status['受理届出名称'].isin(selected_facility_criteria)
    symbol_mask = filing_status['受理記号'].isin(selected_facility_criteria)
    mask = name_mask | symbol_mask
    filing_status = filing_status[mask]


# Sort by count in descending order (default)
filing_status = filing_status.sort_values('件数', ascending=False)

# Display summary
st.write(f"**対象医療機関数: {total_institutions:,} 件**")

# Display in table format
if len(filing_status) > 0:
    # Format percentage column
    display_df = filing_status.copy()
    display_df['届出医療機関割合'] = display_df['届出医療機関割合'].apply(lambda x: f"{x:.2f}%")
    
    # Reorder columns (include 受理記号 if available)
    display_columns = ['受理届出名称']
    if '受理記号' in display_df.columns:
        display_columns.append('受理記号')
    display_columns.extend(['件数', '届出医療機関割合'])
    display_df = display_df[[col for col in display_columns if col in display_df.columns]]
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True
    )
else:
    st.warning("該当する届出が見つかりませんでした。")

