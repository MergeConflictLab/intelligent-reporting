import polars as pl
import os
from math import floor
import warnings
import json

warnings.filterwarnings("ignore")


class DataSampler:
    def __init__(self, *, df: pl.DataFrame, max_rows: int = 3, output_path: str = None):
        if output_path is None:
            raise ValueError("You must provide an output_path (including filename).")
        self.df = df
        self.max_rows = max_rows
        self.output_path = output_path
        self.frac = min(1.0, max_rows / df.height)

        # Ensure parent folder exists
        folder = os.path.dirname(self.output_path)
        if folder:
            os.makedirs(folder, exist_ok=True)


    def no_sample(self):
        '''avoid sampling if the data is already small'''

        if self.df.height <= self.max_rows:
            print("No sampling needed.")
            return self.df
        return None


    def systematic_sample(self):
        '''apply systematic sampling if there's any time related column'''

        datetime_cols = [
            col for col, dtype in zip(self.df.columns, self.df.dtypes)
            if dtype == pl.Datetime
        ]
        if datetime_cols:
            print("Applying datetime systematic sampling.")
            step = max(1, self.df.height // self.max_rows)
            return self.df.take_every(step)
        return None


    def stratified_sample(self):
        '''apply stratified sampling if there's categorical column'''
        print('apply statified logic')

        categorical_cols = [
            col for col in self.df.columns
            if self.df[col].dtype == pl.Utf8 or self.df[col].n_unique() < 20
        ]
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

        print("Applying random sampling.")
        n = min(self.max_rows, self.df.height)
        return self.df.sample(n=n, seed=42)

    def run_sample(self):
        print("Selecting sampling strategy...")

        for strategy in [
            self.no_sample,
            self.systematic_sample,
            self.stratified_sample,
            self.random_sample
        ]:
            sample = strategy()
            if sample is not None and not sample.is_empty():
                print(f"Final sample shape: {sample.height} rows")
                
                # make json serializable
                sample_json = sample.to_dicts()

                # dump JSON to file
                with open(self.output_path, "w") as f:
                    json.dump(sample_json, f, indent=4)

                # return sample
                return sample_json

        raise RuntimeError("No sampling strategy produced a valid sample.")