import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import json
#from itertools import combinations

class DataCorrelations:
    def __init__(self, df, figures_dir="EDA_output/figures", json_dir="EDA_output"):
        self.df = df
        self.figures_dir = figures_dir
        self.json_dir = json_dir
        os.makedirs(figures_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)

    def _clean_numeric(self):
        df_num = self.df.select_dtypes(include=[np.number])
        #df_num = df_num.loc[:, ~df_num.columns.str.lower().str.contains('id|unnamed')]
        df_num = df_num.loc[:, df_num.nunique() > 1] 
        return df_num

    def correlation_heatmap(self):
        df_num = self._clean_numeric()
        corr = df_num.corr(method='pearson')

        # Professional styling
        sns.set_theme(style="white")

        plt.figure(figsize=(16, 8))
        sns.heatmap(
            corr,
            annot=corr.shape[0] <= 20,      
            fmt=".2f",
            cmap="viridis",
            center=0,
            square=True,
            cbar_kws={'shrink': 0.8},
            linewidths=0.7,                 
            linecolor="white"              
        )

        plt.title("Correlation Heatmap", fontsize=16, weight='bold')

        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)

        sns.despine(left=True, bottom=True)

        plt.tight_layout()

        heatmap_path = os.path.join(self.figures_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        plt.close()


        return corr, heatmap_path  #, corr_json_path


    def plot_top_correlations(self, threshold=0.8, top_n=5):
        df_num = self._clean_numeric()

        sns.set_palette("deep")

        corr = df_num.corr().abs().unstack().sort_values(ascending=False)
        corr = corr[corr < 1]  

        strong_pairs = corr[corr > threshold].drop_duplicates().head(top_n)

        results = []
        for (col1, col2), value in strong_pairs.items():

            fig, ax = plt.subplots(figsize=(7, 4))

            sns.regplot(
                x=col1,
                y=col2,
                data=df_num,
                ax=ax,
                scatter_kws={
                    "s": 35,
                    "alpha": 0.6,
                    "edgecolor": "None"
                },
                line_kws={
                    "linewidth": 2.2,
                    "alpha": 0.9
                }
            )

            ax.set_title(
                f"{col1} vs {col2}  |  r = {value:.2f}",
                fontsize=14,
                weight="bold",
                pad=12
            )
            ax.set_xlabel(col1, fontsize=12)
            ax.set_ylabel(col2, fontsize=12)

            sns.despine(left=False, bottom=False)

            fig.tight_layout()

            path = os.path.join(self.figures_dir, f"corr_{col1}_{col2}.png")
            plt.savefig(path, dpi=300, bbox_inches="tight")
            plt.close(fig)

            results.append({
                "col1": col1,
                "col2": col2,
                "correlation": round(float(value),2)
                #"path": path
            })

        summary_path = os.path.join(self.json_dir, "data_summary.json")

        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Add correlation list
            data["correlations"] = results   

        # Save back to file
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=0)


        return results, summary_path



    def run(self):
        print("Generating correlation heatmap...")
        corr, heatmap_path  = self.correlation_heatmap()

        print("Generating top correlated pairs...")
        results, summary_path = self.plot_top_correlations()

        print("Correlation analysis completed.")
        return {
            "heatmap": heatmap_path,
            #"heatmap_json": corr_json_path,
            "top_correlations": summary_path
        }
    
''' Spearman and Kendall correlation versions for non-linear relationships.

Categorical–numeric correlation via ANOVA or Cramér’s V (for mixed data)
'''