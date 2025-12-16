import polars as pl
import numpy as np
import math
import csv
import re
from .base_connector import BaseConnector
from .registry import register_file
from ..expection import *
import os

@register_file([".csv", ".tsv", ".txt"])
class CSVConnector(BaseConnector):

    def __init__(self, path: str):
        self.params = {}
        self.path = path

    def _detect_header(self):
        """
            Say whether a text file has a header row,
            I can consider that a row is header if:
            1. it has no nulls (or null_likes)
            2. if the values are all unique
            3. if the number of in second and third are > number of nmerics in first
            4. if the values are like identifiers
            5. if it contains numbers, then all should be numbers and in ascending order
        """
        try:
            sample = pl.read_csv(self.path, has_header=False, infer_schema_length=0,ignore_errors=True ,n_rows=2)
            first_row = sample.row(0)
            second_row = sample.row(1) if sample.height > 1 else []
            third_row = sample.row(2) if sample.height > 2 else []
            # helpers
            def is_number(v):
                if isinstance(v, (bool, np.bool_)):
                    return False
                if isinstance(v, (int, float, np.number)):
                    return not (isinstance(v, float) and math.isnan(v))
                try:
                    return str(v).replace(".", "", 1).isdigit()
                except Exception:
                    return False
                
            def is_identifier_like(v: object):
                if not isinstance(v, str):
                    return False
                s = v.strip()
                if not s:
                    return False
                
                if s == " ":
                    return False
                
                s_no_quotes = re.sub(r'^(["\'])(.*)\1$', r"\2", s)
                clean = re.sub(r"[_\-\s]+", "", s_no_quotes)

                # if numeric
                if re.match(r"^[\d.]+$", clean):
                    return False

                # most letters
                alpha_ratio = sum(c.isalpha() for c in clean) / len(clean)

                # accept if most are alphabetic and no weird symbols
                allowed_pattern = re.compile(r"^[A-Za-z0-9 _\-]+$")
                return bool(alpha_ratio > 0.6 and bool(allowed_pattern.match(s)))
            
            def _is_null_like(v: object):
                NULL_LIKES = {
                    " ", "null", "none", "nan", "n/a", "na", "#n/a", "#na", "--", "?", 
                    "unknown", "missing", "#value!", "#ref!", "nil", "undefined", ".", "blank", "empty"
                }
                if v is None or (isinstance(v, float) and math.isnan(v)) or v is pl.Null:
                    return True

                if isinstance(v, str):
                    v = v.strip().lower()
                    return v in NULL_LIKES
            
                return False
            
            # 1 (need to keep one chance for the index if exists)
            has_nulls = sum(_is_null_like(v) for v in first_row) > 1

            # 2
            uniqueness_ratio = (len(set(first_row)) / max(len(first_row), 1))
            mostly_unique = uniqueness_ratio > 0.9
                        
            # 3
            first_num = sum(is_number(v) for v in first_row)
            second_num = sum(is_number(v) for v in second_row)
            third_num = sum(is_number(v) for v in third_row)
            dtype_shift = (
                len(second_row) > 0 and 
                first_num < second_num and 
                (len(third_row) == 0 or second_num == third_num)
            )
            # 4
            
            identifier_ratio = sum(is_identifier_like(v) for v in first_row) / len(first_row)
            mostly_identifiers = identifier_ratio > 0.8            
            # 5 
            numeric_values = [float(v) for v in first_row if is_number(v)]
            ascending_numbers = (
                len(numeric_values) == len(first_row) and 
                all(x < y for x, y in zip(numeric_values, numeric_values[1:]))
            )
            
            is_header = (
                not has_nulls and
                mostly_unique and
                (dtype_shift or mostly_identifiers or ascending_numbers)
            )
            return bool(is_header)

        except Exception as e:
            print(e)
            return None
        
    def _detect_delimiter(self):
        """
        Detect what delimiter is used in the CSVConnector instance
        """
        with open(self.path, "r", newline="") as f:
            sample = f.read(2048)
            sniffer = csv.Sniffer()

            # Detect delimiter
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        return delimiter
    
    def _detect_null_likes(self, df: pl.DataFrame):
        """
        A method to detect null likes and convert them to polars.none values
        """
        NULL_LIKES = {
                    None, pl.Null," ", "", "null", "none", "nan", "n/a", "na", "#n/a", "#na", "--", "-", "?", 
                    "unknown", "missing", "undefined", ".", "blank", "empty"
                }

        string_nulls = {str(v).lower() for v in NULL_LIKES if v is not None}

        for column in df.columns:
            col_data = df[column]

            # convert everything to str for comparison
            col_as_str = (
                col_data.cast(pl.Utf8)
                .str.strip_chars()
                .str.to_lowercase()
            )

            # build mask: match normalized string nulls OR real NaNs
            mask = col_as_str.is_in(string_nulls) | col_data.is_null()
            
            df = df.with_columns(
                pl.when(mask).then(None).otherwise(col_data).alias(column)
            )

        return df
    
    def _detect_quotes(self):
        """
        Detect which quote is used in a CSVConnector instance
        """
        with open(self.path, "r", newline="") as f:
            sample = f.read(2048)
            sniffer = csv.Sniffer()

            dialect = sniffer.sniff(sample)

            quote = dialect.quotechar
            quoting_mode = dialect.quoting

        if quote and quoting_mode is not csv.QUOTE_NONE:
            return quote
        
        return False
    
    def load(self, **options):
        """
        Load the CSVConnector instance into a Polars DataFrame object
        """
        if not os.path.exists(self.path):
            raise DataLoadingError(
                f"File not found: {self.path}"
            )

        try:
            # Try to read only a small sample first
            df = pl.read_csv(
                self.path,
                n_rows=10,
                infer_schema_length=0,
            )
        except Exception as e:
            raise DataLoadingError(
                f"Failed to read CSV file: {self.path}"
            ) from e

        if df.width == 0:
            raise EmptyDatasetError(
                f"CSV file has no columns: {self.path}"
            )

        if df.height == 0:
            raise EmptyDatasetError(
                f"CSV file contains no rows: {self.path}"
            )

        try:
            has_header = self._detect_header()
            delimiter = self._detect_delimiter()

            if "has_header" not in options.keys() and has_header is not None:
                options["has_header"] = has_header

            if "seperator" not in options.keys():
                options["separator"] = delimiter
            
            options["infer_schema_length"]=0

            # detect quotes
            quote = self._detect_quotes()
            if "quote_char" not in options.keys():
                options["quote_char"] = quote

            # actually load the file with the parameters given
            df = pl.read_csv(self.path, **options)
            df = self._detect_null_likes(df=df)
            return df
        
        except Exception as e:
            raise DataLoadingError(
                f"Failed to fully load CSV file: {self.path}"
            ) from e
