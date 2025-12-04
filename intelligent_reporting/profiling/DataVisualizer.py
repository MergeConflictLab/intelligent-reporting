import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
#import numpy as np

warnings.filterwarnings("ignore")


class DataVisualizer:
    def __init__(self, *, df: pl.DataFrame, summary_dir="EDA_output",figures_dir, top_k_categories=5):
        self.df = df
        self.summary_dir = summary_dir
        self.figures_dir = figures_dir if figures_dir and os.path.isabs(figures_dir) else os.path.join(self.summary_dir, "figures")
        self.top_k_categories = top_k_categories
        self.top_k_categories = top_k_categories

        
        self.primary_color = "#2E4057"     
        self.secondary_color = "#F5B041"   
        self.neutral_color = "#BFC9CA"     

        os.makedirs(self.summary_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

        # know columns type
        self.numeric_cols = [col for col, dt in zip(df.columns, df.dtypes)
                             if dt in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                                       pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                                       pl.Float32, pl.Float64)]
        
        self.cat_cols = [col for col, dt in zip(df.columns, df.dtypes)
                         if dt == pl.Utf8 or dt == pl.Boolean]
        
        self.datetime_cols = [col for col, dt in zip(df.columns, df.dtypes)
                              if dt == pl.Datetime]

    def _save_plot(self, fig, name):
        """Save figure in figures folder."""
        path = os.path.join(self.figures_dir, f"{name}.png")
        fig.savefig(path, bbox_inches="tight", dpi=300)
        plt.close(fig)
        return path

    def plot_numeric_distributions(self, top_n=2):
        '''plot numeric columns depends on variance value'''
        if not self.numeric_cols:
            return

        # top variance columns
        variances = {col: float(self.df[col].var()) for col in self.numeric_cols}
        top_vars = dict(sorted(variances.items(), key=lambda x: x[1], reverse=True)[:top_n])

        for col, var in top_vars.items():
            fig, ax = plt.subplots(figsize=(8, 6))

            sns.histplot(self.df[col].to_numpy(), bins=25, kde=True,
                         color=self.primary_color, edgecolor='white', linewidth=1.2, ax=ax)

            ax.set_title(f"{col} Distribution (Variance={var:.2f})", fontsize=16, fontweight="bold", color=self.primary_color)
            ax.set_xlabel(col, fontsize=13)
            ax.set_ylabel("Frequency", fontsize=13)
            ax.grid(alpha=0.25, linestyle='--', color=self.neutral_color)
            sns.despine(left=True, bottom=True)
            fig.tight_layout()

            self._save_plot(fig, f"hist_{col}")

    def plot_categorical_columns(self):
        '''plot categorical columns'''

        if not self.cat_cols:
            return

        for col in self.cat_cols[:2]:
            vc = self.df[col].value_counts().sort("count", descending=True)
            top_categories = vc.head(self.top_k_categories).to_pandas()

            fig, ax = plt.subplots(figsize=(10, 6))

            colors = [self.primary_color if i < self.top_k_categories-1 else self.secondary_color
                      for i in range(len(top_categories))]
            
            bars = ax.bar(top_categories[col], top_categories["count"],
                          color=colors, edgecolor=self.neutral_color, linewidth=1.2, alpha=0.9)

            ax.set_title(f"Top {self.top_k_categories} Categories for {col}",
                         fontsize=16, fontweight="bold", color=self.primary_color)
            ax.set_xlabel(col, fontsize=13)
            ax.set_ylabel("Count", fontsize=13)
            plt.xticks(rotation=45, ha="right")
            ax.grid(axis='y', alpha=0.2, linestyle='--', color=self.neutral_color)

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + max(top_categories["count"])*0.02,
                        f'{int(height)}', ha='center', fontsize=11, fontweight='bold', color=self.primary_color)

            sns.despine(left=True, bottom=True)
            fig.tight_layout()
            self._save_plot(fig, f"bar_{col}")


    def plot_time_series_columns(self):
        '''plot time column'''
        if not self.datetime_cols or not self.numeric_cols:
            return

        # umeric column with highest variance
        variances = {col: float(self.df[col].var()) for col in self.numeric_cols}
        best_num = max(variances, key=variances.get)

        for dt_col in self.datetime_cols[:2]:
            time_df = self.df.groupby(dt_col).agg(pl.col(best_num).mean()).sort(dt_col).to_pandas()

            fig, ax = plt.subplots(figsize=(10, 5))

            ax.plot(time_df[dt_col], time_df[best_num], marker='o',
                    linewidth=2, color=self.primary_color)
            ax.fill_between(time_df[dt_col], time_df[best_num]*0.97, time_df[best_num]*1.03,
                            color=self.primary_color, alpha=0.1)

            ax.set_title(f"{best_num} over time ({dt_col})", fontsize=16, fontweight="bold", color=self.primary_color)
            ax.set_xlabel(dt_col, fontsize=13)
            ax.set_ylabel(best_num, fontsize=13)
            ax.grid(alpha=0.25, linestyle='--', color=self.neutral_color)

            sns.despine(left=True, bottom=True)
            fig.tight_layout()
            self._save_plot(fig, f"time_series_{dt_col}")

    def run_viz(self):
        self.plot_numeric_distributions()
        self.plot_categorical_columns()
        self.plot_time_series_columns()