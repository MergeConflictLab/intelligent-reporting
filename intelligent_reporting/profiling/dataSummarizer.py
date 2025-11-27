import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")  # clean background
sns.set_palette("Set2")

class AutoExploratory:
    def __init__(self, df):
        self.df = df
        self.output_dir = "EDA_output"
        self.figures_dir = "EDA_output/figures"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

    
    def summary(self):
        print(f"the data has {self.df.shape[0]} row and {self.df.shape[1]} columns")
        n_rows, n_cols = self.df.shape

        print("the first row of the data \n", self.df.head(1))
        print("the last row of the data \n", self.df.tail(1))

        summary_info = {"num_rows": n_rows, "num_columns": n_cols}
        outliers = self.detect_outliers()
        outlier_plot_path = self.plot_outliers(outliers)

        summary_info["outliers_per_column"] = outliers

        numeric_df = self.df.select_dtypes(include='number')
        if numeric_df.empty:
            print("No numeric columns found — skipping skew/kurtosis analysis.")
            return summary_info

        skew = numeric_df.skew().abs()
        kurtosis = numeric_df.kurtosis().abs()
        score = skew * kurtosis
        target_col = score.idxmax()

        log = (kurtosis[target_col] > 5) or (skew[target_col] > 1)
        data_to_plot = np.log1p(self.df[target_col]) if log else self.df[target_col]
        plot_title = f"{'Most Extreme Column (Log Scale):' if log else 'Most Extreme Column:'} {target_col}\nSkew={skew[target_col]:.2f}, Kurtosis={kurtosis[target_col]:.2f}"

        top_tail_skew = skew.sort_values(ascending=False)
        print(f"Most largest skewed column: {top_tail_skew.index[0]} (skew = {top_tail_skew.iloc[0]:.2f})")
        print(f"Most lowest skewed column: {top_tail_skew.index[-1]} (skew = {top_tail_skew.iloc[-1]:.2f})")

        summary_info["large_skew"] = {"column": top_tail_skew.index[0], "skew_value": round(top_tail_skew.iloc[0], 2)}
        summary_info["low_skew"] = {"column": top_tail_skew.index[-1], "skew_value": round(top_tail_skew.iloc[-1], 2)}

        print('-------------------')
        print(f'a statistical summary of the data: \n {numeric_df.describe()}')
        print(f'number of duplicated rows: {self.df.duplicated().sum()}')

        summary_info['missing_values'] = self.df.isnull().sum().to_dict()
        summary_info["statistical_summary"] = numeric_df.describe().to_dict()

        constant_cols = {}
        for col in self.df.columns:
            top_freq = self.df[col].value_counts(normalize=True, dropna=False).iloc[0]
            if top_freq >= 0.8:
                constant_cols[col] = round(float(top_freq), 2)
        summary_info["constant_columns"] = constant_cols if constant_cols else "there's no constant column"

        json_path = os.path.join(self.output_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, indent=4, ensure_ascii=False)

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        sns.boxplot(x=data_to_plot, width=0.5, fliersize=5, linewidth=2)  # narrower box, thicker lines
        plt.title(f"{plot_title} (Boxplot)", fontsize=14, fontweight='bold')
        plt.xlabel("")  # optional, remove default xlabel for cleaner look
        plt.ylabel("Values", fontsize=12)

        plt.subplot(1, 2, 2)
        sns.histplot(data_to_plot, kde=True, color='#FF6F61', edgecolor='black', bins=20)
        plt.title(f"{plot_title} (Histogram)", fontsize=14, fontweight='bold')
        plt.xlabel("Values", fontsize=12)
        plt.ylabel("Count", fontsize=12)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, "skewed_columns_plot.png"))

    def detect_outliers(self):
        numeric_cols = self.df.select_dtypes(include='number').columns
        outlier_counts = {}
        for col in numeric_cols:
            q1, q3 = self.df[col].quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_counts[col] = int(((self.df[col] < lower) | (self.df[col] > upper)).sum())
        return outlier_counts

    def plot_outliers(self, outlier_counts):

    # Set theme and palette
        sns.set_theme(style="whitegrid")
        sns.set_palette("Set2")

        # Figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Data
        cols = list(outlier_counts.keys())
        counts = list(outlier_counts.values())

        # Barplot with professional styling
        sns.barplot(x=cols, y=counts, ax=ax, edgecolor='black', linewidth=1.5)

        # Titles and labels
        ax.set_title("Outlier Count per Column", fontsize=16, fontweight='bold')
        ax.set_xlabel("Columns", fontsize=12)
        ax.set_ylabel("Outlier Count", fontsize=12)

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha="right")

        # Add value labels on top of bars
        for i, count in enumerate(counts):
            ax.text(i, count + max(counts)*0.01, str(count), ha='center', va='bottom', fontsize=10)

        # Layout and save
        plt.tight_layout()
        path = os.path.join(self.figures_dir, "outliers_per_column.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')  # high-quality save
        plt.close(fig)

        return path

        
