import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
from scipy.stats import kruskal

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

warnings.filterwarnings("ignore")

class DataVisualizer:
    def __init__(self, *, df: pl.DataFrame, summary_dir="EDA_output",figures_dir = None, top_k_categories=5):
        self.df = df
        self.top_k_categories = top_k_categories

        self.summary_dir = summary_dir 
        self.figures_dir = figures_dir if figures_dir and os.path.isabs(figures_dir) else os.path.join(self.summary_dir, "figures")
        self.summary_dir = os.path.abspath(self.summary_dir)
        self.figures_dir = os.path.abspath(self.figures_dir)
        
        self.primary_color = "#2E4057"     
        self.secondary_color = "#F5B041"   
        self.neutral_color = "#BFC9CA"     

        os.makedirs(self.summary_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

        self.index_cols = self._detect_index_columns(df)

        self.numeric_cols = [col for col, dt in zip(df.columns, df.dtypes) if col not in self.index_cols and dt in ( pl.Int8, pl.Int16, pl.Int32, pl.Int64,
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64)]

        self.cat_cols = [col for col, dt in zip(df.columns, df.dtypes) if col not in self.index_cols and (dt == pl.Utf8 or dt == pl.Boolean)]

        self.datetime_cols = [col for col, dt in zip(df.columns, df.dtypes) if col not in self.index_cols and dt == pl.Datetime]

        if self.index_cols:
            logger.info(
                "Visualizer excluded index columns: %s",
                sorted(self.index_cols),
            )

        logger.info(
            "Visualizer initialized | numeric=%d | categorical=%d | datetime=%d",
            len(self.numeric_cols),
            len(self.cat_cols),
            len(self.datetime_cols),
        )
        
    def _detect_index_columns(self, df):
        index_cols = []

        for col in df.columns:
            s = df[col]

            if s.n_unique() != df.height:
                continue

            if s.dtype in pl.INTEGER_DTYPES:
                if (s.diff().drop_nulls() == 1).all():
                    index_cols.append(col)
                    continue
            
            if col.lower() in {"id", "index", "idx", "row_id", "rowid"}:
                index_cols.append(col)
                continue

        return index_cols

    def _save_plot(self, fig, name):
        """Save figure in figures folder."""
        path = os.path.join(self.figures_dir, f"{name}.png")
        try:
            fig.savefig(path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            return path
        except Exception as e:
            logger.exception("Failed to save plot %s: %s", path, e)
            plt.close(fig)
            return None


    def plot_numeric_distributions(self, top_n=2):
        '''plot numeric columns depends on variance value'''
        if not self.numeric_cols:
            logger.info("Skipping numeric distributions bcs there's no numeric columns")
            return

        # top variance columns
        variances = {col: float(self.df[col].var() or 0.0) for col in self.numeric_cols}
        top_vars = dict(sorted(variances.items(), key=lambda x: x[1], reverse=True)[:top_n])

        for col, var in top_vars.items():
            with sns.axes_style("whitegrid"):

                fig, ax = plt.subplots(figsize=(8, 6))

                sns.histplot(self.df[col].drop_nulls().to_numpy(), bins=25, kde=True, color=self.primary_color, edgecolor='white', linewidth=1.2, ax=ax)
                ax.set_title(f"{col} Distribution (Variance={var:.2f})", fontsize=16, fontweight="bold", color=self.primary_color)
                ax.set_xlabel(col, fontsize=13)
                ax.set_ylabel("Frequency", fontsize=13)
                ax.grid(alpha=0.25, linestyle='--', color=self.neutral_color)
                sns.despine(left=True, bottom=True)
                fig.tight_layout()

                self._save_plot(fig, f"hist_{col}")

    def plot_categorical_columns(self, max_unique=50, max_label_len=40):
        """Safely plot categorical columns while skipping unusable ones silently."""
        if not self.cat_cols:
            logger.info("Skipping categorical plots: no categorical columns")
            return

        for col in self.cat_cols[:2]: 
            # Cardinality filter
            n_unique = self.df[col].n_unique()
            if n_unique == 0 or n_unique > max_unique:
                continue

            vc = self.df[col].value_counts()
            if vc.height == 0:
                continue

            value_col = [c for c in vc.columns if c != "count"][0]

            # Sort by count
            vc = vc.with_columns(pl.col(value_col).cast(pl.Utf8).alias("__val_str"))
            vc = vc.sort([pl.col("count").reverse(), pl.col("__val_str")])

            top_categories = vc.head(self.top_k_categories).to_pandas()
            if top_categories.empty:
                continue

            labels = top_categories[value_col].astype(str)
            if labels.map(len).max() > max_label_len:
                labels = labels.str.slice(0, max_label_len - 1) + "…"

            counts = top_categories["count"].astype(int)
            if counts.empty:
                continue

            with sns.axes_style("whitegrid"):
                fig, ax = plt.subplots(figsize=(10, 6))

                colors = [self.primary_color if i < self.top_k_categories - 1 else self.secondary_color for i in range(len(labels))]
                bars = ax.bar(labels, counts,color=colors,edgecolor= self.neutral_color, linewidth=1.2, alpha=0.9)

                ax.set_title(
                    f"Top {self.top_k_categories} Categories for {col}",fontsize=16,fontweight="bold",color=self.primary_color)
                ax.set_xlabel(col, fontsize=13)
                ax.set_ylabel("Count", fontsize=13)
                plt.xticks(rotation=45, ha="right")
                ax.grid(axis='y', alpha=0.2, linestyle='--', color=self.neutral_color)

                max_count = int(counts.max())
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2,height + max_count * 0.02,f'{int(height)}',ha='center',fontsize=11,
                    fontweight='bold',
                    color=self.primary_color
                )

                sns.despine(left=True, bottom=True)
                fig.tight_layout()
                self._save_plot(fig, f"bar_{col}")


    def plot_time_series_columns(self):
        '''plot time column'''
        if not self.datetime_cols or not self.numeric_cols:
            logger.info(
            "Skipping time series plots | datetime=%d | numeric=%d",len(self.datetime_cols),
            len(self.numeric_cols),)
            return

        # umeric column with highest variance
        variances = {col: float(self.df[col].var() or 0.0) for col in self.numeric_cols}
        best_num = max(variances, key=variances.get)

        for dt_col in self.datetime_cols[:2]:
            with sns.axes_style("whitegrid"):

                time_df = self.df.group_by(dt_col).agg(pl.col(best_num).mean()).sort(dt_col).to_pandas()
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

    def _rank_numeric_by_kruskal(self, cat_col, numeric_cols, top_n=2):
        """Return the top_n numeric columns most associated with the categorical column."""
        pdf = self.df.select([cat_col] + numeric_cols).drop_nulls().to_pandas()
        results = []

        # group by categorical column
        groups = dict(tuple(pdf.groupby(cat_col)))

        for num in numeric_cols:
            num_groups = [g[num].dropna().values for _, g in groups.items() if len(g[num].dropna()) > 1
            ]

            if len(num_groups) <= 1:
                continue

            stat, pval = kruskal(*num_groups)
            results.append((num, stat, pval))

        # sort by highest H-stat
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_n]]


    def plot_categorical_numeric_interactions(self, max_categories=10):
        """
        Plot boxplots for (categorical, numeric) pairs.
        Uses Kruskal ranking to avoid plotting noise.
        """

        if not self.cat_cols or not self.numeric_cols:
            return

        for cat in self.cat_cols[:2]:
            if self.df[cat].n_unique() > max_categories:
                continue

            # Select numeric cols based on Kruskal ranking
            best_numeric = self._rank_numeric_by_kruskal(cat, self.numeric_cols, top_n=2)

            for num in best_numeric:
                df_pd = (
                    self.df.select([cat, num]).drop_nulls().to_pandas())

                if df_pd.empty:
                    continue

                with sns.axes_style("whitegrid"):
                    fig, ax = plt.subplots(figsize=(10, 6))

                    sns.boxplot(data=df_pd,x=cat,y=num,ax=ax,color=self.primary_color,fliersize=3, width=0.6)

                    ax.set_title(
                        f"{num} Distribution by {cat}",
                        fontsize=16, fontweight="bold", color=self.primary_color
                    )

                    ax.set_xlabel(cat, fontsize=13)
                    ax.set_ylabel(num, fontsize=13)
                    plt.xticks(rotation=30, ha="right")

                    ax.grid(axis="y", alpha=0.25, linestyle='--', color=self.neutral_color)
                    sns.despine(left=True, bottom=True)

                    fig.tight_layout()
                    name = f"box_{num}_by_{cat}".replace(" ", "_")
                    self._save_plot(fig, name)



    def run_viz(self):
        logger.info("Starting visualization module")

        self.plot_numeric_distributions()
        self.plot_categorical_columns()
        self.plot_time_series_columns()
        self.plot_categorical_numeric_interactions()

        logger.info("vizs module completed")

        