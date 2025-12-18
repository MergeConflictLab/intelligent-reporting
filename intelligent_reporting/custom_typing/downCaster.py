import polars as pl
class DownCaster :
    """This class should be responsible of downcasting type columns of a pl.DataFrame object"""

    def downcast_integer(self, serie: pl.Series):
        """Downcast a pl.Series object based on its minimum and maximum values to a more convienient pl.Int"""
        INT_TYPES = [(pl.Int8, -128, 127), (pl.Int16, -32768, 32767), (pl.Int32, -2**31, 2**31 - 1)]
        max_value = serie.max()
        min_value = serie.min()

        for dtype, min_type, max_type in INT_TYPES:
            if max_value <= max_type and min_value >= min_type:
                return serie.cast(dtype)
            
        return serie
    
    def downcast_float(self, serie: pl.Series):
        """Downcast a pl.Series object based on its minimum and maximum values to a more convienient pl.Float"""
        FLOAT_TYPES = [(pl.Float32,-3.4e38, 3.4e38)]
        max_value = serie.max()
        min_value = serie.min()

        for dtype, min_type, max_type in FLOAT_TYPES:
            if max_value <= max_type and min_value >= min_type:
                return serie.cast(dtype)
            
        return serie
        

    def optimize(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Downcast a pl.DataFrame dataframe into a more narrow type
        """
        for col in df.columns:
            if df[col].dtype in [pl.Int64]:
                df = df.with_columns(self.downcast_integer(df[col]).alias(col))
            elif df[col].dtype in [pl.Float64]:
                df = df.with_columns(self.downcast_float(df[col]).alias(col))
        return df