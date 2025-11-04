import pandas as pd
from .shisetsu_kijun import ShisetsuKijunDataFrame


class ShisetsuKijunFilingCrossTabDataFrame(pd.DataFrame):
    """Custom DataFrame class for cross-tabulation of facility criteria filing status across institutions"""
    
    @property
    def _constructor(self):
        return ShisetsuKijunFilingCrossTabDataFrame
    
    @classmethod
    def from_jaccard_similarity(cls, jaccard_df, source_df, target_institution_name, top_n=20):
        """Create ShisetsuKijunFilingCrossTabDataFrame from JaccardSimilarityDataFrame
        
        Args:
            jaccard_df: JaccardSimilarityDataFrame with similarity results
            source_df: ShisetsuKijunDataFrame with original data
            target_institution_name: Name of the target institution
            top_n: Number of top similar institutions to include (default: 20)
            
        Returns:
            ShisetsuKijunFilingCrossTabDataFrame with filing status comparison
        """
        # Ensure source_df is ShisetsuKijunDataFrame
        if not isinstance(source_df, ShisetsuKijunDataFrame):
            source_df = ShisetsuKijunDataFrame(source_df)
        
        # Get top N institutions
        top_n_df = jaccard_df.head(top_n).copy()
        top_n_institutions = top_n_df['医療機関名称'].tolist()
        
        if not top_n_institutions:
            return cls()
        
        # Pre-compute institution filings by institution number (for performance)
        institution_filings_by_number = (
            source_df.groupby('医療機関番号')['受理届出名称']
            .apply(lambda x: set(x.dropna().unique()))
            .to_dict()
        )
        
        # Get institution numbers for these institutions
        institution_number_mapping = (
            source_df.groupby('医療機関名称')['医療機関番号']
            .first()
            .to_dict()
        )
        
        # Create mapping from 受理届出名称 to 受理記号 (1-to-1 relationship)
        if '受理記号' in source_df.columns:
            filing_name_to_symbol = (
                source_df.groupby('受理届出名称')['受理記号']
                .first()
                .to_dict()
            )
        else:
            filing_name_to_symbol = {}
        
        # Get target institution's number
        target_institution_data = source_df.filter_by_exact_institution_name(target_institution_name)
        if len(target_institution_data) == 0:
            return cls()
        
        target_institution_number = target_institution_data.iloc[0]['医療機関番号']
        
        # Get all filing types (施設基準) from target and top N institutions
        all_filing_types = set()
        
        # Get target institution's filing types
        target_filing_types = institution_filings_by_number.get(target_institution_number, set())
        all_filing_types.update(target_filing_types)
        
        # Get top N institutions' filing types
        for institution_name in top_n_institutions:
            institution_number = institution_number_mapping.get(institution_name)
            if institution_number:
                filing_types = institution_filings_by_number.get(institution_number, set())
                all_filing_types.update(filing_types)
        
        all_filing_types = sorted(list(all_filing_types))
        
        if not all_filing_types:
            return cls()
        
        # Build data for cross-tabulation
        rows_data = []
        
        for filing_type in all_filing_types:
            row_data = {
                '受理届出名称': filing_type,
                '受理記号': filing_name_to_symbol.get(filing_type, '')
            }
            
            # First, add target institution's filing status
            target_filing_types_set = institution_filings_by_number.get(target_institution_number, set())
            row_data[target_institution_name] = filing_type in target_filing_types_set
            
            # Then, add top N institutions' filing status
            for institution_name in top_n_institutions:
                institution_number = institution_number_mapping.get(institution_name)
                if institution_number:
                    filing_types_set = institution_filings_by_number.get(institution_number, set())
                    row_data[institution_name] = filing_type in filing_types_set
                else:
                    row_data[institution_name] = False
            
            rows_data.append(row_data)
        
        # Create DataFrame with 受理届出名称 and 受理記号 as columns
        cross_tab_df = pd.DataFrame(rows_data)
        # Set 受理届出名称 as index for filtering
        cross_tab_df = cross_tab_df.set_index('受理届出名称')
        
        return cls(cross_tab_df)
    
    def filter_unfiled_by_target(self, target_institution_name):
        """Filter rows where target institution has NOT filed
        
        Args:
            target_institution_name: Name of the target institution
            
        Returns:
            ShisetsuKijunFilingCrossTabDataFrame filtered to show only unfiled items
        """
        if target_institution_name not in self.columns:
            return self.copy()
        
        filtered_df = self[self[target_institution_name] == False].copy()
        return self.__class__(filtered_df)
    
    def get_display_dataframe(self, target_institution_name):
        """Get DataFrame formatted for display with proper column order
        
        Args:
            target_institution_name: Name of the target institution
            
        Returns:
            DataFrame with columns reordered for display
        """
        # Reset index to display 受理届出名称 as a regular column
        display_df = self.reset_index()
        
        # Get institution columns (excluding 受理届出名称 and 受理記号)
        institution_columns = [col for col in display_df.columns 
                             if col not in ['受理届出名称', '受理記号']]
        
        # Reorder: target institution first, then others
        if target_institution_name in institution_columns:
            other_institutions = [col for col in institution_columns if col != target_institution_name]
            institution_columns = [target_institution_name] + other_institutions
        
        # Reorder columns: 受理届出名称, 受理記号, then institution columns
        display_columns = ['受理届出名称', '受理記号'] + institution_columns
        display_df = display_df[display_columns]
        
        return display_df

