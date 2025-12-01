import os
import json
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="whitegrid")
sns.set_palette("Set2")

class DataSummarizer:
    def __init__(self, *, df: pl.DataFrame, output_dir="EDA_output", figures_dir=None, verbose=False):
        self.df = df
        self.output_dir = output_dir
        self.figures_dir = figures_dir or os.path.join(output_dir, "figures")
        self.verbose = verbose

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

    # ------------------- SUMMARY -------------------
    def summary(self, analyze_outliers=True, analyze_skew=True, detect_constants=True):
        """Orchestrates the full EDA summary workflow and returns a summary dict."""
        n_rows, n_cols = self.df.shape
        if self.verbose:
            print(f"Data has {n_rows} rows and {n_cols} columns.")

        summary_info = {
            "num_rows": n_rows,
            "num_columns": n_cols,
            "duplicated_rows": int(self.df.height - self.df.unique().height)
        }

        # Missing values
        summary_info["missing_values"] = {col: int(self.df[col].null_count()) for col in self.df.columns}

        # Outlier analysis
        if analyze_outliers:
            outliers = self.detect_outliers()
            summary_info["outliers_per_column"] = outliers
            summary_info["outlier_plot_path"] = self.plot_outliers(outliers)

        # Numeric column statistics
        numeric_cols = [col for col, dt in zip(self.df.columns, self.df.dtypes) if dt in [pl.Int64, pl.Float64]]
        if numeric_cols and analyze_skew:
            numeric_df = self.df.select(numeric_cols)
            summary_info["statistical_summary"] = self.describe_numeric(numeric_df)
            summary_info["most_extreme_column_plot_path"] = self.plot_most_extreme_column(numeric_df)

        # Constant columns
        if detect_constants:
            summary_info["constant_columns"] = self.detect_constants()

        # Save summary JSON
        json_path = os.path.join(self.output_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, indent=4, ensure_ascii=False)
        if self.verbose:
            print(f"Summary saved to: {json_path}")

        return summary_info

    # ------------------- OUTLIERS -------------------
    def detect_outliers(self):
        numeric_cols = [col for col, dt in zip(self.df.columns, self.df.dtypes) if dt in [pl.Int64, pl.Float64]]
        outlier_counts = {}
        
        for col in numeric_cols:
            # Skip column if all values are null
            if self.df[col].null_count() == self.df.height:
                outlier_counts[col] = 0
                continue

            # Compute Q1 and Q3 with interpolation
            q1 = self.df[col].quantile(0.25, interpolation="nearest")
            q3 = self.df[col].quantile(0.75, interpolation="nearest")
            if q1 is None or q3 is None:  # fallback
                outlier_counts[col] = 0
                continue

            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_counts[col] = int(((self.df[col] < lower) | (self.df[col] > upper)).sum())
        
        return outlier_counts



    def plot_outliers(self, outlier_counts):
        fig, ax = plt.subplots(figsize=(10, 6))
        cols = list(outlier_counts.keys())
        counts = list(outlier_counts.values())
        sns.barplot(x=cols, y=counts, ax=ax, edgecolor='black', linewidth=1.5)
        ax.set_title("Outlier Count per Column", fontsize=16, fontweight='bold')
        ax.set_xlabel("Columns", fontsize=12)
        ax.set_ylabel("Outlier Count", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        for i, count in enumerate(counts):
            ax.text(i, count + max(counts) * 0.01, str(count), ha='center', va='bottom', fontsize=10)
        plt.tight_layout()
        path = os.path.join(self.figures_dir, "outliers_per_column.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        if self.verbose:
            print(f"Outlier plot saved to: {path}")
        return path

    # ------------------- STATISTICS -------------------
    def describe_numeric(self, numeric_df: pl.DataFrame):
        """Return descriptive statistics for numeric columns in a dict format."""
        desc = numeric_df.describe()
        summary_dict = {}

        # Polars describe gives rows: ['mean', 'std', 'min', 'max', 'median']
        # Convert each column to dict
        for col in numeric_df.columns:
            col_stats = {}
            for row in desc.rows():
                stat_name = row[0]  # first column of desc is the statistic name
                stat_value = row[desc.columns.index(col)]
                col_stats[stat_name] = float(stat_value) if stat_value is not None else None
            summary_dict[col] = col_stats

        return summary_dict


    def plot_most_extreme_column(self, numeric_df: pl.DataFrame):
        """Plot histogram and boxplot for column with highest skew*kurtosis."""
        skew_kurt = {}
        for col in numeric_df.columns:
            skew = numeric_df[col].skew()
            kurt = numeric_df[col].kurtosis()
            # Handle None values safely
            skew_val = abs(skew) if skew is not None else 0
            kurt_val = abs(kurt) if kurt is not None else 0
            skew_kurt[col] = skew_val * kurt_val

        if not skew_kurt:
            print("No numeric columns to plot.")
            return None

        extreme_col = max(skew_kurt, key=skew_kurt.get)
        data = numeric_df[extreme_col].to_numpy()
        
        log_scale = False
        skew = numeric_df[extreme_col].skew() or 0
        kurt = numeric_df[extreme_col].kurtosis() or 0
        if abs(skew) > 1 or abs(kurt) > 5:
            data = np.log1p(data)
            log_scale = True

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        sns.boxplot(x=data, ax=axs[0], width=0.5, fliersize=5, linewidth=2)
        axs[0].set_title(f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Boxplot)", fontsize=14, fontweight='bold')
        sns.histplot(data, kde=True, color='#FF6F61', edgecolor='black', bins=20, ax=axs[1])
        axs[1].set_title(f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Histogram)", fontsize=14, fontweight='bold')
        plt.tight_layout()

        path = os.path.join(self.figures_dir, "most_extreme_column.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"Most extreme numeric column plot saved to: {path}")
        return path


    # ------------------- CONSTANT COLUMNS -------------------
    def detect_constants(self):
        constant_cols = {}
        for col in self.df.columns:
            vc = self.df[col].value_counts()
            counts_col = vc.columns[1]  # always the second column is the counts
            counts = vc[counts_col]
            top_freq = counts.max() / self.df.height
            if top_freq >= 0.8:
                constant_cols[col] = round(float(top_freq), 2)
        return constant_cols if constant_cols else "No constant column"




