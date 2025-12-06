import os
import json
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
sns.set_theme(style="whitegrid")

class DataCorrelater:

    def __init__(self, df: pl.DataFrame):
        self.df = df
        self.figures_dir = os.path.join('results', 'figures')
        self.json_path = os.path.join('results', f"{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.json")


        # Professional colors
        self.primary_color = "#2E4057"
        self.secondary_color = "#F5B041"
        self.neutral_color = "#BFC9CA"

        # Create folders
        os.makedirs(self.figures_dir, exist_ok=True)
        os.makedirs('results', exist_ok=True)

    def _numeric_columns(self):
        return [col for col, dt in zip(self.df.columns, self.df.dtypes)
                if dt in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                          pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                          pl.Float32, pl.Float64)]

    def correlation_heatmap(self):
        numeric_cols = self._numeric_columns()
        if not numeric_cols:
            print("No numeric columns for correlation heatmap.")
            return None, None

        # Polars correlation matrix
        corr_df = self.df.select(numeric_cols).to_pandas().corr(method='pearson')

        plt.figure(figsize=(16, 8))
        sns.heatmap(
            corr_df,
            annot=corr_df.shape[0] <= 20,
            fmt=".2f",
            cmap="viridis",
            center=0,
            square=True,
            linewidths=0.7,
            linecolor="white"
        )
        plt.title("Correlation Heatmap", fontsize=16, weight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        sns.despine(left=True, bottom=True)
        plt.tight_layout()

        heatmap_path = os.path.join(self.figures_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=300)
        plt.close()
        return corr_df, heatmap_path

    def plot_top_correlations(self, threshold=0.8, top_n=5):
        numeric_cols = self._numeric_columns()
        if not numeric_cols:
            print("No numeric columns for top correlations.")
            return []

        df_numeric = self.df.select(numeric_cols).to_pandas()
        corr = df_numeric.corr().abs().unstack()
        corr = corr[corr < 1].sort_values(ascending=False)
        strong_pairs = corr[corr > threshold].drop_duplicates().head(top_n)

        results = []
        for (col1, col2), value in strong_pairs.items():
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.regplot(
                x=col1, y=col2, data=df_numeric, ax=ax,
                scatter_kws={"s":35, "alpha":0.6, "edgecolor":"None"},
                line_kws={"linewidth":2.2, "alpha":0.9, "color": self.primary_color}
            )
            ax.set_title(f"{col1} vs {col2}  |  r = {value:.2f}", fontsize=14, weight="bold")
            ax.set_xlabel(col1, fontsize=12)
            ax.set_ylabel(col2, fontsize=12)
            sns.despine(left=False, bottom=False)
            fig.tight_layout()
            path = os.path.join(self.figures_dir, f"corr_{col1}_{col2}.png")
            plt.savefig(path, dpi=300)
            plt.close(fig)
            results.append({"col1": col1, "col2": col2, "correlation": round(float(value),2)})

        # # Update JSON summary without storing paths

        # if os.path.exists(self.json_path):
        #     with open(self.json_path, "r", encoding="utf-8") as f:
        #         data = json.load(f)
        # else:
        #     data = {}
        # data["correlations"] = results
        # with open(self.json_path, "w", encoding="utf-8") as f:
        #     json.dump(data, f, indent=4)

        return results

    def run(self, threshold=0.8, top_n=5):
        _ , heatmap_path = self.correlation_heatmap()
        _ = self.plot_top_correlations(threshold=threshold, top_n=top_n)
        # return {
        #     "heatmap": heatmap_path,
        #     "top_correlations_summary": self.json_path
        # }
