#import pandas as pd
from sklearn.model_selection import train_test_split

class Sampling:
    def __init__(self, df, max_rows = 100):
        self.df = df
        self.max_rows = max_rows
        self.frac = min(1.0, max_rows / len(df)) 

    # small data no need to sample
    def no_sample(self):
        if self.df.shape[0] <= self.max_rows:
            print("no need to sample. we are using the entire dataset")
            return self.df
        return None

    # systematic sampling, when we have a datetime column
    def datetime_sample(self):
        datetime_cols = self.df.select_dtypes(include=['datetime64[ns]']).columns
        if len(datetime_cols) > 0:
            print("applying systematic sampling.")
            step = max(1, len(self.df) // self.max_rows)
            return self.df.iloc[::step, :].reset_index(drop=True)
        return None

    # stratified sampling
    def stratified_sample(self):
        categorical_cols = [
            col for col in self.df.columns
            if self.df[col].dtype == 'object' or self.df[col].nunique() < 20
        ]
        categorical_cols = sorted(categorical_cols, key=lambda c: self.df[c].nunique())

        for col in categorical_cols:
            counts = self.df[col].value_counts()
            if counts.min() < 2:  
                continue
            
            try:
                print(f"stratified sampling based on: {col}")
                sample_df, _ = train_test_split(
                    self.df,
                    stratify=self.df[col],
                    test_size=1 - self.frac,
                    random_state=42
                )
                return sample_df.reset_index(drop=True)
            except Exception:
                continue

        return None  

    # random sampling
    def random_sample(self):
        print("Applying random sampling.")
        n = min(self.max_rows, len(self.df))
        return self.df.sample(n=n, random_state=42).reset_index(drop=True)


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
            sample.to_json(output_path, orient=orient, indent=2)
            print(f"Sample successfully saved to: {output_path}")
        except Exception as e:
            print(f"Failed to save Json: {e}")
            return None

        return output_path
