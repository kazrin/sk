import pandas as pd
import ast
from .shisetsu_kijun import ShisetsuKijunDataFrame


class JaccardSimilarityDataFrame(pd.DataFrame):
    """Custom DataFrame class for Jaccard similarity results"""
    
    @property
    def _constructor(self):
        return JaccardSimilarityDataFrame
    
    @classmethod
    def _calculate_jaccard_similarity(cls, set1, set2):
        """Calculate Jaccard similarity coefficient between two sets"""
        if len(set1) == 0 and len(set2) == 0:
            return 1.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    @classmethod
    def from_shisetsu_kijun(cls, df, target_institution_name):
        """Create JaccardSimilarityDataFrame from ShisetsuKijunDataFrame by calculating Jaccard similarity
        
        Args:
            df: ShisetsuKijunDataFrame instance
            target_institution_name: Name of the target institution
            
        Returns:
            JaccardSimilarityDataFrame with similarity results
        """
        # Ensure df is ShisetsuKijunDataFrame
        if not isinstance(df, ShisetsuKijunDataFrame):
            df = ShisetsuKijunDataFrame(df)
        
        # Get target institution's number first
        target_institution_data = df.filter_by_exact_institution_name(target_institution_name)
        if len(target_institution_data) == 0:
            return cls()
        
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
            return cls()
        
        # Calculate similarities for all other institutions
        similarities = []
        for institution_number, filings in institution_filings_dict.items():
            if institution_number == target_institution_number or len(filings) == 0:
                continue
            
            similarity = cls._calculate_jaccard_similarity(target_filings, filings)
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
        
        return cls.from_similarity_results(similarities)
    
    @classmethod
    def from_similarity_results(cls, similarity_data):
        """Create JaccardSimilarityDataFrame from similarity results
        
        Args:
            similarity_data: List of dictionaries with similarity data
            
        Returns:
            JaccardSimilarityDataFrame instance
        """
        if not similarity_data:
            return cls()
        
        result_df = pd.DataFrame(similarity_data)
        
        # Ensure 病床数 column is treated as object type to preserve dicts
        if '病床数' in result_df.columns:
            result_df['病床数'] = result_df['病床数'].astype(object)
        
        if len(result_df) > 0:
            result_df = result_df.sort_values('類似度', ascending=False)
        
        return cls(result_df)
    
    def get_all_bed_types(self):
        """Get all available bed types from the dataframe"""
        all_bed_types = set()
        if '病床種類' not in self.columns:
            return []
        
        for bed_types_list in self['病床種類']:
            if isinstance(bed_types_list, list):
                # Filter out None values and empty strings, and strip whitespace
                cleaned_types = [str(bt).strip() for bt in bed_types_list if bt is not None and str(bt).strip()]
                all_bed_types.update(cleaned_types)
        
        return sorted([bt for bt in all_bed_types if bt])  # Remove empty strings
    
    def filter_by_bed_types(self, selected_bed_types):
        """Filter dataframe by selected bed types
        
        Args:
            selected_bed_types: List of bed type names to filter by
            
        Returns:
            JaccardSimilarityDataFrame filtered by bed types
        """
        if not selected_bed_types:
            return self.copy()
        
        if '病床種類' not in self.columns:
            return self.copy()
        
        # Filter institutions that have at least one of the selected bed types
        mask = self['病床種類'].apply(
            lambda x: bool(set(x).intersection(set(selected_bed_types))) if isinstance(x, list) else False
        )
        return self[mask].copy()
    
    def get_bed_count_max(self, selected_bed_types):
        """Get maximum bed count for each selected bed type
        
        Args:
            selected_bed_types: List of bed type names
            
        Returns:
            Dict mapping bed type to max bed count
        """
        # Lazy import to avoid circular dependency
        from .shisetsu_kijun import ShisetsuKijunDataFrame
        # Convert to ShisetsuKijunDataFrame for bed count operations
        temp_df = ShisetsuKijunDataFrame(self[['医療機関名称', '病床数']])
        return temp_df.get_bed_count_max(selected_bed_types, unique_by='医療機関名称')
    
    def filter_by_bed_counts_generic(self, bed_count_filters):
        """Filter dataframe by bed count ranges
        
        Args:
            bed_count_filters: Dict mapping bed type to (min_val, max_val) tuple
            
        Returns:
            JaccardSimilarityDataFrame filtered by bed counts
        """
        if not bed_count_filters:
            return self.copy()
        
        # Lazy import to avoid circular dependency
        from .shisetsu_kijun import ShisetsuKijunDataFrame
        # Convert to ShisetsuKijunDataFrame for filtering
        temp_df = ShisetsuKijunDataFrame(self[['医療機関名称', '病床数']])
        filtered_temp_df = temp_df.filter_by_bed_counts_generic(bed_count_filters, unique_by='医療機関名称')
        
        # Get the filtered institution names and filter the original DataFrame
        filtered_institution_names = set(filtered_temp_df['医療機関名称'].unique())
        return self[self['医療機関名称'].isin(filtered_institution_names)].copy()

