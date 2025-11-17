#import pandas as pd
from sklearn.model_selection import train_test_split

class Sampling:
    def __init__(self, df, max_rows=50):
        self.df = df
        self.max_rows = max_rows
        self.frac = min(1.0, max_rows / len(df)) 

    # if we already have a small dataset
    def no_sample(self):
        if self.df.shape[0] < self.max_rows:
            print("No sampling needed.")
            return self.df
        return None

    # if we have datetime column - systematic sampling
    def datetime_sample(self):
        datetime_cols = self.df.select_dtypes(include=['datetime64[ns]']).columns
        if len(datetime_cols) > 0:
            print("Datetime column found, applying systematic sampling.")
            step = max(1, len(self.df) // self.max_rows)
            return self.df.iloc[::step, :].reset_index(drop=True)
        return None

    # if we have categorical column - stratified sampling
    def stratified_sample(self):
        categorical_cols = [
            col for col in self.df.columns
            if self.df[col].dtype == 'object' or self.df[col].nunique() < 20
        ]

        if categorical_cols:
            stratify_col = max(categorical_cols, key=lambda c: self.df[c].nunique())
            try:
                print(f"Stratified sampling based on: {stratify_col}")
                sample_df, _ = train_test_split(
                    self.df,
                    stratify=self.df[stratify_col],
                    test_size=1 - self.frac,
                    random_state=42
                )
                return sample_df.reset_index(drop=True)
            except Exception as e:
                print(f"Stratified sampling failed: {e}")
        return None

    # if all numeric → random sampling
    def random_sample(self):
        print("Applying random sampling.")
        return self.df.sample(frac=self.frac, random_state=42).reset_index(drop=True)


    def run_simple(self, output_path="sample_output.json", orient='records'):
        print("Checking sampling strategy...")

        sample = self.no_sample()
        if sample is None:
            sample = self.datetime_sample()
        if sample is None:
            sample = self.stratified_sample()
        if sample is None:
            sample = self.random_sample()
        

        print(f"Final sample shape: {sample.shape}")

        try:
            sample.to_json(output_path, orient = orient, indent=2)
            print(f"Sample successfully saved to: {output_path}")
        except Exception as e:
            print(f"Failed to save Json: {e}")
            return None

        return output_path

              