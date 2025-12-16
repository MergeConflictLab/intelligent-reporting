import os
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DataCorrelater:

    def __init__(self, df: pl.DataFrame):
        self.df = df
        self.figures_dir = os.path.join('results', 'figures')
        self.json_path = os.path.join('results', f"{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.json")

        self.primary_color = "#2E4057"
        self.secondary_color = "#F5B041"
        self.neutral_color = "#B62B2B"

        os.makedirs(self.figures_dir, exist_ok=True)
        os.makedirs('results', exist_ok=True)

        logger.info("Correlater initialized | rows=%d | columns=%d",self.df.height,self.df.width,)


    def _numeric_columns(self):
        return [
            col for col, dt in zip(self.df.columns, self.df.dtypes)
            if dt in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64)]


    def correlation_heatmap(self):
        ''''generate heatmap'''
        numeric_cols = self._numeric_columns()
        if not numeric_cols:
            logger.info("Skipping correlation heatmap: no numeric columns")
            return None, None

        df_np = self.df.select(numeric_cols).to_pandas()
        df_np = df_np.loc[:, df_np.std(numeric_only=True) > 0]

        corr_df = df_np.corr(method='pearson')
        corr_df = corr_df.dropna(axis=0, how="all").dropna(axis=1, how="all")


        with sns.axes_style("whitegrid"):

            plt.figure(figsize=(14, 10))
            mask = corr_df.isna()

            sns.heatmap(corr_df,mask=mask, annot=corr_df.shape[0] <= 20,
                         fmt=".2f", cmap=sns.diverging_palette(220, 20, as_cmap=True),
    center=0, square=True, linewidths=0.7, linecolor=self.neutral_color,
                         cbar_kws={"shrink": 0.8}
            )
            plt.title("Pearson Correlation Heatmap", fontsize=16, weight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            heatmap_path = os.path.join(self.figures_dir, "correlation_heatmap.png")
            plt.savefig(heatmap_path, dpi=300)
            plt.close()

        return corr_df, heatmap_path

    def _get_top_pairs(self, corr_df, top_n=5):
        if corr_df is None or corr_df.shape[0] < 2:
            logger.debug("No correlation matrix available for top pairs")
            return []

        corr = corr_df.unstack()
        corr = corr[corr.index.get_level_values(0) != corr.index.get_level_values(1)]
        corr = corr.reindex(corr.abs().sort_values(ascending=False).index)

        top = corr.head(top_n)
        return [(a, b, float(v)) for (a, b), v in top.items()]


    def plot_top_correlations(self, threshold=0.8, top_n=5):
        numeric_cols = self._numeric_columns()
        if not numeric_cols:
            logger.info("Skipping correlation plots: no numeric columns")
            return []

        df_numeric = self.df.select(numeric_cols).to_pandas()
        corr = df_numeric.corr().unstack()
        corr = corr[corr.index.get_level_values(0) != corr.index.get_level_values(1)]
        corr = corr.reindex(corr.abs().sort_values(ascending=False).index)
        corr = corr[~corr.index.map(lambda x: x[0] > x[1])]

        strong_pairs = corr[abs(corr) > threshold].drop_duplicates().head(top_n)

        results = []
        for (col1, col2), value in strong_pairs.items():
            fig, ax = plt.subplots(figsize=(7, 4))

            with sns.axes_style("whitegrid"):

                sns.regplot(
                    x=col1, y=col2, data=df_numeric, ax=ax,
                      scatter_kws={"s": 36, "alpha": 0.6,'facecolor':self.neutral_color,'edgecolor':'white','linewidths':0.6,},
                    line_kws={"linewidth": 2.2, "alpha": 0.9, "color": self.primary_color})
                ax.set_title(f"{col1} vs {col2}  |  r = {value:.2f}", fontsize=14, weight="bold")
                ax.set_xlabel(col1)
                ax.set_ylabel(col2)
                fig.tight_layout()
                ax.grid(alpha=0.25, linestyle="--", color=self.neutral_color)
                sns.despine(left=True, bottom=True)

                path = os.path.join(self.figures_dir, f"corr_{col1}_{col2}.png")
                try:
                    plt.savefig(path, dpi=300)
                except Exception as e:
                    logger.exception("Failed to save correlation plot %s: %s", path, e)
                finally:
                    plt.close(fig)

            results.append({"col1": col1, "col2": col2, "correlation": round(float(value), 2)})
        return results

    def spearman_top_pair(self, pearson_pairs, threshold=0.8):
        numeric_cols = self._numeric_columns()
        if not numeric_cols:
            logger.info("Skipping Spearman correlation: no numeric columns")
            return None

        df = self.df.select(numeric_cols).to_pandas()
        spear_corr = df.corr(method='spearman')

        # Convert to list of non duplicate pairs
        pairs = []
        for i, a in enumerate(spear_corr.columns):
            for j, b in enumerate(spear_corr.columns):
                if j <= i:
                    continue
                val = float(spear_corr.loc[a, b])
                pairs.append((a, b, val))

        # Sort by absolute Spearman correlation
        pairs = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)

        # Remove pairs already plotted by Pearson
        pearson_set = {(a, b) for (a, b, _) in pearson_pairs}
        pearson_set |= {(b, a) for (a, b, _) in pearson_pairs}

        for a, b, spear_val in pairs:
            if abs(spear_val) < threshold:
                return None
            if (a, b) not in pearson_set:
                break
        else:
            return None
        
        if df[a].nunique() < 2 or df[b].nunique() < 2:
            logger.info("Skipping Spearman plot: constant column detected (%s, %s)", a, b)
            return None


        # Plot it
        with sns.axes_style("whitegrid"):

            fig, ax = plt.subplots(figsize=(7, 4))
            sns.regplot(
                x=a, y=b, data=df, ax=ax,ci=None,
                scatter_kws={"s": 35, "alpha": 0.7, "facecolor": self.primary_color,
                            "edgecolor": "white",
                            "linewidths": 0.6,},
                line_kws={"linewidth": 2.2, "alpha": 0.8, "color": self.neutral_color}
            )
            ax.set_title(f"Spearman: {a} vs {b} | ρ = {spear_val:.2f}", fontsize=14, weight="bold")
            ax.set_xlabel(a)
            ax.set_ylabel(b)
            fig.tight_layout()

            path = os.path.join(self.figures_dir, f"spearman_{a}_{b}.png")
            ax.grid(alpha=0.25, linestyle="--", color=self.neutral_color)
            sns.despine(left=True, bottom=True)

            plt.savefig(path, dpi=300)
            plt.close()

        return {"x_column": a, "y_column": b,"spearman": round(spear_val, 2),}


    def run(self, threshold=0.8, top_n=5):
        logger.info("Starting correlation analysis")
        corr_df, heatmap_path = self.correlation_heatmap()

        # Extract top 2 Pearson pairs for duplicate checking
        if corr_df is None:
            pearson_pairs = []
        else:

            pearson_pairs = self._get_top_pairs(corr_df, top_n=2)

        # Generate Pearson scattes
        _ = self.plot_top_correlations(threshold=threshold, top_n=top_n)

        # Generate Spearman
        spearman_result = self.spearman_top_pair(pearson_pairs, threshold=0.6)
        logger.info("Correlation analysis completed")

        return {"heatmap": heatmap_path, "spearman_insight": spearman_result}

