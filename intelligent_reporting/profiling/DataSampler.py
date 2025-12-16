import polars as pl
import os
from math import floor
import warnings
import json
from datetime import datetime, date

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

warnings.filterwarnings("ignore")

class DataSampler:
    def __init__(self, *, df: pl.DataFrame, max_rows: int = 3, sample_dir: str = None):
        if sample_dir is None:
            raise ValueError("You must provide an sample_dir")
        self.df = df
        self.max_rows = max_rows
        self.sample_dir = sample_dir
        self.frac = min(1.0, max_rows / df.height)

        # Ensure parent folder exists
        folder = os.path.dirname(self.sample_dir)
        if folder:
            os.makedirs(folder, exist_ok=True)

    def no_sample(self):
        '''avoid sampling if the data is already small'''

        if self.df.height <= self.max_rows:
            logger.info("No sampling applied due to small dataset: rows=%d <= max_rows=%d",
            self.df.height,self.max_rows,)
            return self.df
        return None

    def systematic_sample(self):
        '''apply systematic sampling if there's any time related column'''

        datetime_cols = [col for col, dtype in zip(self.df.columns, self.df.dtypes) if isinstance(dtype, (pl.Datetime, pl.Date))
        ]
        if datetime_cols:
            step = max(1, self.df.height // self.max_rows)
            return self.df.gather_every(step)
        return None

    def stratified_sample(self):
        '''apply stratified sampling if there's categorical column'''

        categorical_cols = [col for col in self.df.columns if self.df[col].dtype == pl.Utf8 or self.df[col].n_unique() < 20]
        categorical_cols = sorted(categorical_cols, key=lambda c: self.df[c].n_unique())

        for col in categorical_cols:
            unique_vals = self.df[col].unique().to_list()
            per_group = max(1, floor(self.max_rows / len(unique_vals)))
            sampled_groups = []

            for value in unique_vals:
                group = self.df.filter((pl.col(col).is_not_null()) & (pl.col(col) == value))
                n = min(per_group, group.height)
                if n > 0:
                    sampled_groups.append(group.sample(n=n, seed=42))

            if sampled_groups:
                return pl.concat(sampled_groups).head(self.max_rows)

        return None


    def random_sample(self):
        '''apply sample random sampling when each row have the same proba to be present the the sample'''

        n = min(self.max_rows, self.df.height)
        return self.df.sample(n=n, seed=42)
    
    def _json_safe(self, rows):
        safe_rows = []
        for row in rows:
            safe_row = {}
            for k, v in row.items():
                if isinstance(v, (datetime, date)):
                    safe_row[k] = v.isoformat()
                else:
                    safe_row[k] = v
            safe_rows.append(safe_row)
        return safe_rows


    def run_sample(self):
        for strategy in [
            self.no_sample, self.systematic_sample, self.stratified_sample, self.random_sample]:
            sample = strategy()
            if sample is not None and not sample.is_empty():
                logger.info("Sampling strategy used: %s | rows=%d",strategy.__name__,sample.height,)
            
                # make json serializable
                sample_json = self._json_safe(sample.to_dicts())

                with open(f"{self.sample_dir}/sample.json", "w") as f:
                    json.dump(sample_json, f, separators=(",", ":"))
                return sample_json
            
        logger.error("No sampling strategy produced a valid sample")

        raise RuntimeError("No sampling strategy produced a valid sample")