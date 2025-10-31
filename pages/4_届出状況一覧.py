import streamlit as st
import pandas as pd
from utils import load_raw_data

st.title("📋 届出状況一覧")

# Navigation button
col1, col2 = st.columns(2)
with col1:
    if st.button("← ホームページに戻る"):
        st.switch_page("main.py")

# Load raw data
df = load_raw_data()

# Filters
st.write("### フィルター")

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
        key='bed_type_multiselect'
    )

# Facility criteria filter (改行区切り入力, always enabled)
criteria_input = st.text_area(
    "施設基準を改行区切りで入力:",
    placeholder="施設基準1\n施設基準2\n施設基準3",
    key='facility_criteria_input',
    height=100
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
filing_status = filtered_df['受理届出名称'].value_counts().reset_index()
filing_status.columns = ['受理届出名称', '件数']

# Calculate number of institutions filing each status (by institution number)
institution_counts = (
    filtered_df.groupby('受理届出名称')['医療機関番号']
    .nunique()
    .reset_index()
)
institution_counts.columns = ['受理届出名称', '届出医療機関数']

# Merge with filing status
filing_status = filing_status.merge(institution_counts, on='受理届出名称', how='left')

# Calculate percentage
filing_status['届出医療機関割合'] = (
    filing_status['届出医療機関数'] / total_institutions * 100
).round(2)

# Filter by facility criteria (exact match if criteria are provided)
if selected_facility_criteria:
    # Filter filing statuses that exactly match the input criteria
    mask = filing_status['受理届出名称'].isin(selected_facility_criteria)
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
    
    # Reorder columns
    display_columns = ['受理届出名称', '件数', '届出医療機関割合']
    display_df = display_df[display_columns]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("該当する届出が見つかりませんでした。")

