import os
import json
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="whitegrid")
sns.set_palette("Set2")


class DataSummarizer:
    def __init__(self, *, df: pl.DataFrame, output_dir: str, figures_dir=None, verbose=False):

        # extract num and cat cols
        numeric_cols = [
            col for col, dt in zip(df.columns, df.dtypes)
            if dt in (
                pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                pl.Float32, pl.Float64
            )
        ]

        categorical_cols = [
            col for col, dt in zip(df.columns, df.dtypes)
            if dt == pl.Utf8 or dt == pl.Boolean
        ]

        self.df = df
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols

        self.output_dir = output_dir
        self.figures_dir = figures_dir if figures_dir and os.path.isabs(figures_dir) else os.path.join(self.output_dir, figures_dir or "figures")
        self.verbose = verbose

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)


    def summary(self, analyze_outliers=True, analyze_skew=True, detect_constants=True):
        '''extracting high level statistics'''

        n_rows, n_cols = self.df.shape

        summary_info = {
            "num_rows": n_rows,
            "num_columns": n_cols,
            "duplicated_rows": int(self.df.height - self.df.unique().height),
        }

        # counting Missing values
        summary_info["missing_values"] = {
            col: int(self.df[col].null_count())
            for col in self.df.columns
        }

        # detect outliers
        if analyze_outliers and self.numeric_cols:
            outliers = self.detect_outliers()
            summary_info["outliers_per_column"] = outliers
            summary_info["outlier_plot_path"] = self.plot_outliers(outliers)

        # extract stats and extreme column
        if analyze_skew and self.numeric_cols:
            numeric_df = self.df.select(self.numeric_cols)
            summary_info["statistical_summary"] = self.describe_numeric(numeric_df)
            summary_info["most_extreme_column_plot_path"] = self.plot_most_extreme_column(numeric_df)

        # const col
        if detect_constants:
            summary_info["constant_columns"] = self.detect_constants()

        # Save summary JSON
        json_path = os.path.join(self.output_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, indent=4, ensure_ascii=False)

        if self.verbose:
            print(f"Summary saved to: {json_path}")

        return summary_info


    def detect_outliers(self):
        '''detecting outliers'''
        outlier_counts = {}
        for col in self.numeric_cols:
            series = self.df[col].drop_nulls()
            if series.is_empty():
                outlier_counts[col] = 0
                continue

            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_counts[col] = int(((series < lower) | (series > upper)).sum())

        return outlier_counts

    def plot_outliers(self, outlier_counts):
        '''plot outliers'''
        fig, ax = plt.subplots(figsize=(10, 6))
        cols = list(outlier_counts.keys())
        counts = list(outlier_counts.values())

        sns.barplot(x=cols, y=counts, ax=ax, edgecolor='black', linewidth=1.5)
        ax.set_title("Outlier Count per Column", fontsize=16, fontweight='bold')
        ax.set_xlabel("Columns")
        ax.set_ylabel("Outlier Count")
        plt.xticks(rotation=45, ha="right")

        for i, count in enumerate(counts):
            ax.text(i, count + max(counts) * 0.01, str(count), ha='center')

        plt.tight_layout()
        path = os.path.join(self.figures_dir, "outliers_per_column.png")
        plt.savefig(path, dpi=300)
        plt.close(fig)
        return path


    def describe_numeric(self, numeric_df: pl.DataFrame):
        desc = numeric_df.describe()
        summary_dict = {}

        for col in numeric_df.columns:
            col_stats = {}
            for row in desc.rows():
                stat_name = row[0]
                stat_value = row[desc.columns.index(col)]
                col_stats[stat_name] = float(stat_value) if stat_value is not None else None
            summary_dict[col] = col_stats

        return summary_dict

    def plot_most_extreme_column(self, numeric_df: pl.DataFrame):
        '''plot the extrem col based on kurtosis and skeweness'''
        skew_kurt = {}

        for col in numeric_df.columns:
            series = numeric_df[col].drop_nulls()
            if series.is_empty():
                continue

            skew = series.skew()
            kurt = series.kurtosis()
            skew_val = abs(skew) if skew else 0
            kurt_val = abs(kurt) if kurt else 0

            skew_kurt[col] = skew_val * kurt_val

        if not skew_kurt:
            return None

        extreme_col = max(skew_kurt, key=skew_kurt.get)
        data = numeric_df[extreme_col].drop_nulls().to_numpy()

        log_scale = False
        skew_val = numeric_df[extreme_col].drop_nulls().skew() or 0
        kurt_val = numeric_df[extreme_col].drop_nulls().kurtosis() or 0

        if abs(skew_val) > 1 or abs(kurt_val) > 5:
            data = np.log1p(data)
            log_scale = True

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))

        sns.boxplot(x=data, ax=axs[0], width=0.5, fliersize=5, linewidth=2)
        axs[0].set_title(
            f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Boxplot)",
            fontsize=14
        )

        sns.histplot(data, kde=True, edgecolor='black', bins=20, ax=axs[1])
        axs[1].set_title(
            f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Histogram)",
            fontsize=14
        )

        plt.tight_layout()

        path = os.path.join(self.figures_dir, "most_extreme_column.png")
        plt.savefig(path, dpi=300)
        plt.close(fig)
        return path


    def detect_constants(self):
        '''highlighting constant columns'''
        constant_cols = {}
        n = self.df.height

        for col in self.df.columns:
            vc = self.df[col].value_counts()

            if vc.is_empty():
                continue

            top_count = vc["count"].max()
            top_freq = top_count / n

            if top_freq >= 0.8:
                constant_cols[col] = round(float(top_freq), 3)

        return constant_cols
