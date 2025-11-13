import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
#from itertools import combinations

class DataCorrelations:
    def __init__(self, df, figures_dir="figures", json_dir="json_output"):
        self.df = df.copy()
        self.figures_dir = figures_dir
        self.json_dir = json_dir
        os.makedirs(figures_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)

    def _clean_numeric(self):
        # Drop non-numeric or ID-like columns
        df_num = self.df.select_dtypes(include=[np.number])
        df_num = df_num.loc[:, ~df_num.columns.str.lower().str.contains('id|unnamed')]
        df_num = df_num.loc[:, df_num.nunique() > 1]  # remove constant columns
        return df_num

    def correlation_heatmap(self):
        df_num = self._clean_numeric()
        corr = df_num.corr(method='pearson')

        plt.figure(figsize=(12, 8))
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            square=True,
            cbar_kws={'shrink': 0.8},
            linewidths=0.5
        )
        plt.title("Correlation Heatmap", fontsize=14, weight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        heatmap_path = os.path.join(self.figures_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Save correlation matrix as JSON
        corr_json_path = os.path.join(self.json_dir, "correlation_matrix.json")
        corr.round(3).to_json(corr_json_path, orient="index")

        return corr, heatmap_path, corr_json_path

    def plot_top_correlations(self, threshold=0.7, top_n=5):
        df_num = self._clean_numeric()
        corr = df_num.corr().abs().unstack().sort_values(ascending=False)
        corr = corr[corr < 1]  # remove self-correlations

        # Keep only strong correlations
        strong_pairs = corr[corr > threshold].drop_duplicates().head(top_n)

        results = []
        for (col1, col2), value in strong_pairs.items():
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.scatterplot(x=df_num[col1], y=df_num[col2], data = self.df)
            ax.set_title(f"{col1} vs {col2}\n(r = {value:.2f})", fontsize=12)
            ax.set_xlabel(col1)
            ax.set_ylabel(col2)
            plt.tight_layout()

            path = os.path.join(self.figures_dir, f"corr_{col1}_{col2}.png")
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)

            results.append({"col1": col1, "col2": col2, "correlation": float(value), "path": path})

        # Save summary JSON
        summary_path = os.path.join(self.json_dir, "top_correlations.json")
        pd.DataFrame(results).to_json(summary_path, orient="records", indent=2)

        return results, summary_path

    def run(self):
        print("Generating correlation heatmap...")
        corr, heatmap_path, corr_json_path = self.correlation_heatmap()

        print("Generating top correlated pairs...")
        results, summary_path = self.plot_top_correlations()

        print("Correlation analysis completed.")
        return {
            "heatmap": heatmap_path,
            "heatmap_json": corr_json_path,
            "top_correlations": summary_path
        }
    
''' Spearman and Kendall correlation versions for non-linear relationships.

Categorical–numeric correlation via ANOVA or Cramér’s V (for mixed data)
'''