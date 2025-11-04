import pandas as pd
import ast


class ShisetsuKijunDataFrame(pd.DataFrame):
    """Custom DataFrame class for medical institution data with filtering methods"""
    
    @property
    def _constructor(self):
        return ShisetsuKijunDataFrame
    
    @classmethod
    def from_feather(cls, file_path):
        """Load data from feather file and return ShisetsuKijunDataFrame instance"""
        df = pd.read_feather(file_path)
        # Clean up bed count dicts: remove keys with None values
        # pandas feather format merges all dict keys across rows, adding None for missing keys
        if '病床数' in df.columns:
            def clean_bed_dict(bed_count):
                # Convert string representation to dict if needed
                if isinstance(bed_count, str):
                    try:
                        bed_count = ast.literal_eval(bed_count)
                    except:
                        return {}
                
                if isinstance(bed_count, dict):
                    # Keep only keys with non-None values and ensure values are int
                    cleaned = {}
                    for k, v in bed_count.items():
                        if v is not None:
                            # Convert value to int if it's a number
                            try:
                                cleaned[k] = int(v)
                            except (ValueError, TypeError):
                                # If conversion fails, skip this entry
                                continue
                    return cleaned
                return bed_count
            df['病床数'] = df['病床数'].apply(clean_bed_dict)
        
        return cls(df)
    
    def get_all_bed_types(self):
        """Get all available bed types from the dataframe"""
        all_bed_types = set()
        for bed_count in self['病床数']:
            if isinstance(bed_count, dict):
                bed_types = [str(k).strip() for k in bed_count.keys() if k is not None and str(k).strip()]
                all_bed_types.update(bed_types)
        return sorted([bt for bt in all_bed_types if bt])
    
    def filter_by_bed_types(self, selected_bed_types):
        """Filter dataframe by selected bed types
        
        Args:
            selected_bed_types: List of bed type names to filter by
            
        Returns:
            ShisetsuKijunDataFrame filtered by bed types
        """
        if not selected_bed_types:
            return self.copy()
        
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
            self.groupby('医療機関番号')['病床数']
            .apply(aggregate_bed_types)
            .to_dict()
        )
        
        # Filter institutions that have at least one of the selected bed types
        filtered_institution_numbers = {
            inst_num for inst_num, bed_types in institution_bed_types.items()
            if set(selected_bed_types).intersection(bed_types)
        }
        
        # Filter data to only include filtered institutions
        mask = self['医療機関番号'].isin(filtered_institution_numbers)
        return self[mask].copy()
    
    def filter_by_bed_counts(self, bed_count_filters):
        """Filter dataframe by bed count ranges
        
        Args:
            bed_count_filters: Dict mapping bed type to (min_val, max_val) tuple
            
        Returns:
            ShisetsuKijunDataFrame filtered by bed counts
        """
        if not bed_count_filters:
            return self.copy()
        
        # Get unique institutions with their bed counts
        unique_institutions = self[['医療機関番号', '病床数']].drop_duplicates(subset='医療機関番号', keep='first')
        
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
        
        # Filter institutions by bed count
        mask = unique_institutions.apply(passes_bed_count_filter, axis=1)
        filtered_institution_numbers_by_bed_count = unique_institutions[mask]['医療機関番号'].unique()
        
        # Apply the filter to self
        mask = self['医療機関番号'].isin(filtered_institution_numbers_by_bed_count)
        return self[mask].copy()
    
    def get_bed_count_max(self, selected_bed_types, unique_by='医療機関番号'):
        """Get maximum bed count for each selected bed type
        
        Args:
            selected_bed_types: List of bed type names
            unique_by: Column name to use for unique identification (default: '医療機関番号')
            
        Returns:
            Dict mapping bed type to max bed count
        """
        if not selected_bed_types:
            return {}
        
        bed_count_max = {}
        # Get unique institutions with their bed counts (more efficient)
        if unique_by in self.columns:
            unique_institutions = self[[unique_by, '病床数']].drop_duplicates(subset=unique_by, keep='first')
        else:
            # Fallback: use index if unique_by column doesn't exist
            unique_institutions = self[['病床数']].drop_duplicates()
        
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
        
        return bed_count_max
    
    def filter_by_bed_counts_generic(self, bed_count_filters, unique_by='医療機関番号'):
        """Filter dataframe by bed count ranges (generic version that works with any unique column)
        
        Args:
            bed_count_filters: Dict mapping bed type to (min_val, max_val) tuple
            unique_by: Column name to use for unique identification (default: '医療機関番号')
            
        Returns:
            ShisetsuKijunDataFrame filtered by bed counts
        """
        if not bed_count_filters:
            return self.copy()
        
        # Get unique institutions with their bed counts
        if unique_by in self.columns:
            unique_institutions = self[[unique_by, '病床数']].drop_duplicates(subset=unique_by, keep='first')
        else:
            # Fallback: use index if unique_by column doesn't exist
            unique_institutions = self[['病床数']].copy()
            unique_institutions['_index'] = unique_institutions.index
            unique_by = '_index'
        
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
        
        # Filter institutions by bed count
        mask = unique_institutions.apply(passes_bed_count_filter, axis=1)
        filtered_unique_values = unique_institutions[mask][unique_by].unique()
        
        # Apply the filter to self
        if unique_by == '_index':
            mask = self.index.isin(filtered_unique_values)
        else:
            mask = self[unique_by].isin(filtered_unique_values)
        return self[mask].copy()
    
    def filter_by_facility_criteria(self, selected_facility_criteria):
        """Filter by facility criteria (受理届出名称 or 受理記号)
        
        Args:
            selected_facility_criteria: List of facility criteria names or symbols
            
        Returns:
            ShisetsuKijunDataFrame filtered by facility criteria
        """
        if not selected_facility_criteria:
            return self.copy()
        
        # Filter by facility criteria (exact match)
        name_mask = self['受理届出名称'].isin(selected_facility_criteria)
        symbol_mask = self['受理記号'].isin(selected_facility_criteria)
        mask = name_mask | symbol_mask
        
        return self[mask].copy()
    
    def aggregate_by_institution_name(self):
        """Aggregate data by institution name, grouping multiple filings per institution
        
        Returns:
            ShisetsuKijunDataFrame with one row per institution, including filing count
        """
        institutions = self.groupby('医療機関名称').agg({
            '医療機関番号': 'first',
            '併設医療機関番号': 'first',
            '医療機関記号番号': 'first',
            '都道府県名': 'first',
            '医療機関所在地（郵便番号）': 'first',
            '医療機関所在地（住所）': 'first',
            '電話番号': 'first',
            'FAX番号': 'first',
            '病床数': 'first',
            '種別': 'first',
            '受理届出名称': 'count'
        }).rename(columns={
            '受理届出名称': '届出数'  # Rename filing count column
        }).reset_index()
        
        return self.__class__(institutions)
    
    def filter_by_institution_name(self, search_term, case_sensitive=False):
        """Filter dataframe by institution name (partial match)
        
        Args:
            search_term: String to search for in institution names
            case_sensitive: Whether the search should be case sensitive (default: False)
            
        Returns:
            ShisetsuKijunDataFrame filtered by institution name
        """
        if not search_term:
            return self.copy()
        
        if '医療機関名称' not in self.columns:
            return self.copy()
        
        mask = self['医療機関名称'].str.contains(search_term, case=case_sensitive, na=False)
        return self[mask].copy()
    
    def filter_by_exact_institution_name(self, institution_name):
        """Filter dataframe by exact institution name match
        
        Args:
            institution_name: Exact institution name to match
            
        Returns:
            ShisetsuKijunDataFrame filtered by exact institution name
        """
        if not institution_name:
            return self.copy()
        
        if '医療機関名称' not in self.columns:
            return self.copy()
        
        mask = self['医療機関名称'] == institution_name
        return self[mask].copy()

