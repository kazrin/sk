import pandas as pd
from .shisetsu_kijun import ShisetsuKijunDataFrame


class ShisetsuKijunFilingStatusDataFrame(pd.DataFrame):
    """Custom DataFrame class for facility criteria filing status aggregation"""
    
    @property
    def _constructor(self):
        return ShisetsuKijunFilingStatusDataFrame
    
    @classmethod
    def from_shisetsu_kijun(cls, df):
        """Create ShisetsuKijunFilingStatusDataFrame from ShisetsuKijunDataFrame
        
        Args:
            df: ShisetsuKijunDataFrame with filtered data
            
        Returns:
            ShisetsuKijunFilingStatusDataFrame with aggregated filing status
        """
        # Ensure df is ShisetsuKijunDataFrame
        if not isinstance(df, ShisetsuKijunDataFrame):
            df = ShisetsuKijunDataFrame(df)
        
        # Get total number of institutions in filtered data (by institution number)
        total_institutions = df['医療機関番号'].nunique()
        
        if total_institutions == 0:
            return cls()
        
        # Calculate filing status counts and institution counts
        # Group by both 受理届出名称 and 受理記号 (1-to-1 relationship)
        filing_status = (
            df.groupby(['受理届出名称', '受理記号'])
            .agg({
                '医療機関番号': 'nunique',  # Number of unique institutions
            })
            .rename(columns={
                '医療機関番号': '届出医療機関数',
            })
            .reset_index()
        )
        
        # Calculate percentage
        filing_status['届出医療機関割合'] = (
            filing_status['届出医療機関数'] / total_institutions * 100
        ).round(2)
        
        return cls(filing_status)
    
    def filter_by_facility_criteria(self, facility_criteria):
        """Filter by facility criteria (受理届出名称 or 受理記号)
        
        Args:
            facility_criteria: List of facility criteria names or symbols
            
        Returns:
            ShisetsuKijunFilingStatusDataFrame filtered by facility criteria
        """
        if not facility_criteria:
            return self.copy()
        
        # Filter filing statuses that exactly match the input criteria
        # Match against either 受理届出名称 or 受理記号
        name_mask = self['受理届出名称'].isin(facility_criteria)
        symbol_mask = self['受理記号'].isin(facility_criteria)
        mask = name_mask | symbol_mask
        
        return self[mask].copy()
    
    def get_display_dataframe(self):
        """Get DataFrame formatted for display with percentage formatted as string
        
        Returns:
            DataFrame with percentage column formatted as string (e.g., "50.00%")
        """
        display_df = self.copy()
        display_df['届出医療機関割合'] = display_df['届出医療機関割合'].apply(lambda x: f"{x:.2f}%")
        
        # Reorder columns
        display_columns = ['受理届出名称', '受理記号', '届出医療機関数', '届出医療機関割合']
        display_df = display_df[display_columns]
        
        return display_df
    
    def get_total_institutions(self, source_df):
        """Get total number of institutions from source DataFrame
        
        Args:
            source_df: ShisetsuKijunDataFrame with original data
            
        Returns:
            Total number of unique institutions
        """
        if not isinstance(source_df, ShisetsuKijunDataFrame):
            source_df = ShisetsuKijunDataFrame(source_df)
        return source_df['医療機関番号'].nunique()

