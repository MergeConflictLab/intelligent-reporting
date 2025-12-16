import os
import json
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


from sklearn.metrics import mutual_info_score

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())



class DataSummarizer:
    def __init__(self, *, df: pl.DataFrame, summary_dir: str, figures_dir=None, verbose=False):

        self.index_cols = set(self._detect_index_columns(df))
        if self.index_cols:
            logger.info("Detected index columns and excluded from analysis: %s", sorted(self.index_cols))
        
        # extract num and cat cols
        numeric_cols = [col for col, dt in zip(df.columns, df.dtypes) if dt in (
                pl.Int8, pl.Int16, pl.Int32, pl.Int64,pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,pl.Float32, pl.Float64) and col not in self.index_cols]

        categorical_cols = [col for col, dt in zip(df.columns, df.dtypes) if (dt == pl.Utf8 or dt == pl.Boolean) and col not in self.index_cols]

        self.df = df
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols
        self.summary_dir = summary_dir
        self.figures_dir = figures_dir if figures_dir and os.path.isabs(figures_dir) else os.path.join(self.summary_dir, figures_dir or "figures")
        self.verbose = verbose

        self.primary_color = "#2E4057"
        self.secondary_color = "#F5B041"
        self.neutral_color = "#B62B2B"

        os.makedirs(self.summary_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)


    def summary(self, analyze_outliers=True, analyze_skew=True, detect_constants=True):
        '''extracting high level statistics'''

        n_rows, n_cols = self.df.shape
        summary_info = { "num_rows": n_rows, "num_columns": n_cols, "duplicated_rows": int(self.df.height - self.df.unique().height),}

        # Missing values
        nulls_df = self.df.null_count()
        summary_info["missing"] = {}
        for col in self.df.columns:
            missing_count = int(nulls_df[col][0]) if col in nulls_df.columns else 0
            summary_info["missing"][col] = {"missing_count": missing_count, "missing_pct": round((missing_count / n_rows) * 100, 4), }

        # Outliers
        if analyze_outliers and self.numeric_cols:
            outliers = self.detect_outliers()
            summary_info["outliers_per_column"] = outliers
            self.plot_outliers(outliers)

        # Skew nd stats
        if analyze_skew and self.numeric_cols:
            numeric_df = self.df.select(self.numeric_cols)
            stats = self.describe_numeric(numeric_df)
            rounded_stats = {col: {s: round(v, 2) if isinstance(v, (int, float)) else v for s, v in col_stats.items()} for col, col_stats in stats.items()}
            summary_info["statistical_summary"] = rounded_stats
            self.plot_most_extreme_column(numeric_df)

        # Constant columns
        if detect_constants:
            summary_info["constant_columns"] = self.detect_constants()
        #  0 variance columns
        summary_info["near_zero_variance_columns"] = self.detect_near_zero_variance()
        summary_info["top_mutual_info_pairs"] = self.compute_top_mutual_info_pairs(top_k=3)

        # Save
        json_path = os.path.join(self.summary_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, ensure_ascii=False,separators=(",", ":"))

        if self.verbose:
            print(f"Summary saved to: {json_path}")

        return summary_info
    
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
        """Plot outlier counts per numeric column (descending, branded)."""

        if not outlier_counts:
            logger.info("Skipping outlier plot: no outliers detected")
            return None

        # sort descending
        cols, counts = zip(
            *sorted(outlier_counts.items(), key=lambda x: x[1], reverse=True))

        with sns.axes_style("whitegrid"):
            fig, ax = plt.subplots(figsize=(10, 6))

            bars = ax.bar(cols,counts,color=self.primary_color,edgecolor="white",linewidth=1.2,alpha=0.9)

            ax.set_title(
                "Outlier Count per Column",
                fontsize=16,
                fontweight="bold",
                color=self.primary_color
            )
            ax.set_xlabel("Columns", fontsize=13)
            ax.set_ylabel("Outlier Count", fontsize=13)

            ax.grid(axis="y", alpha=0.25, linestyle="--", color=self.neutral_color)
            plt.xticks(rotation=45, ha="right")

            # value labels
            max_count = max(counts)
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + max_count * 0.02,
                    f"{int(height)}",
                    ha="center",
                    fontsize=11,
                    fontweight="bold",
                    color=self.primary_color
                )

            sns.despine(left=True, bottom=True)
            fig.tight_layout()

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
        """Plot the most extreme numeric column based on skewness and kurtosis."""

        skew_kurt = {}

        for col in numeric_df.columns:
            series = numeric_df[col].drop_nulls()
            if series.is_empty():
                continue                                            
            try:
                skew = float(series.skew())
            except Exception:
                skew = 0.0

            try:
                kurt = float(series.kurtosis())
            except Exception:
                kurt = 0.0

            if np.isnan(skew) or np.isnan(kurt):
                continue

            skew_kurt[col] = abs(skew) * abs(kurt)

        if not skew_kurt:
            logger.debug("Skipping extreme column plot bcs no valid numeric columns")

            return None

        extreme_col = max(skew_kurt, key=skew_kurt.get)

        # extract data safely
        series = numeric_df[extreme_col].drop_nulls()
        try:
            data = np.asarray(series.to_numpy(), dtype=float)
        except Exception:
            logger.debug("Failed to extract numeric data for column '%s'", extreme_col)

            return None

        if data.size == 0 or np.all(np.isnan(data)):
            return None

        try:
            skew_val = float(series.skew())
        except Exception:
            skew_val = 0.0

        try:
            kurt_val = float(series.kurtosis())
        except Exception:
            kurt_val = 0.0

        log_scale = False
        if (abs(skew_val) > 1 or abs(kurt_val) > 5) and np.nanmin(data) >= 0:
            try:
                data = np.log1p(data)
                log_scale = True
            except Exception:
                pass  

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))

        sns.boxplot(x=data, ax=axs[0], width=0.5, linewidth=2,fliersize=3,color=self.primary_color)
        axs[0].set_title(
            f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Boxplot)",
            fontsize=14,fontweight='bold',color = self.primary_color
        )
        axs[0].grid(alpha=0.25, linestyle="--", color=self.neutral_color)
        sns.despine(ax=axs[0], left=True, bottom=True)

        sns.histplot(
        data,
        bins=25,
        kde=True,
        color=self.primary_color,
        alpha=0.65,
        edgecolor="white",
        
        ax=axs[1],
        
        line_kws={"color": self.primary_color})

        axs[1].set_title(
        f"{'Log-transformed' if log_scale else 'Column'}: {extreme_col} (Histogram)",
        fontsize=15,
        fontweight="bold",
        color=self.primary_color
    )

        axs[1].set_xlabel(extreme_col, fontsize=13)
        axs[1].set_ylabel("Frequency", fontsize=13)

        axs[1].grid(alpha=0.25, linestyle="--", color=self.neutral_color)
        sns.despine(ax=axs[1], left=True, bottom=True)

        plt.tight_layout()

        path = os.path.join(self.figures_dir, "most_extreme_column.png")
        try:
            plt.savefig(path, dpi=300)
        finally:
            plt.close(fig)

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

    def detect_near_zero_variance(self, *, freq_cut=20, unique_cut=10):
        """
        Detect near zero variance columns.
        freq_cut: ratio between most common value frequency and second one.
        unique_cut: threshold for percentage of unique values relative to number of rows.
        """
        nzv_cols = {}
        n = self.df.height
        if n == 0:
            return nzv_cols

        for col in self.numeric_cols + self.categorical_cols:
            vc = self.df[col].value_counts().sort("count", descending=True)

            if vc.height < 2:
                continue

            most = vc["count"][0]
            second = vc["count"][1]
            freq_ratio = most / second if second != 0 else float("inf")

            percent_unique = (vc.height / n) * 100

            if freq_ratio > freq_cut or percent_unique < unique_cut:
                value_col = [c for c in vc.columns if c != "count"][0]

                nzv_cols[col] = {
                    "freq_ratio": round(freq_ratio, 3),
                    "percent_unique": round(percent_unique, 3),
                    "most_common_value": vc[value_col][0],
                }
        return nzv_cols
    
    def _mutual_info_column_pair(self, col_a, col_b, n_bins=20):
        sub = self.df.select([col_a, col_b]).drop_nulls()
        if sub.is_empty():
            return 0.0

        a = sub[col_a]
        b = sub[col_b]

        def to_labels(s):
            if s.dtype in {pl.Float32, pl.Float64, *pl.INTEGER_DTYPES}:
                arr = s.to_numpy()
                if np.nanstd(arr) == 0:
                    return np.zeros(len(arr), dtype=int)
                bins = np.histogram_bin_edges(arr[~np.isnan(arr)], bins=n_bins)
                labels = np.digitize(arr, bins, right=False)
                return labels.astype(int)
            else:
                vals = s.to_list()
                uniques = sorted({str(v) for v in vals})
                mapping = {u: i for i, u in enumerate(uniques)}
                return np.array([mapping[str(v)] for v in vals], dtype=int)

        a_lbl = to_labels(a)
        b_lbl = to_labels(b)

        try:
            return float(mutual_info_score(a_lbl, b_lbl))
        except Exception as e:
            logger.debug("MI failed for %s,%s: %s", col_a, col_b, e)
            return 0.0
    
    def compute_top_mutual_info_pairs(self, top_k=3):
        results = []
        cols = [c for c in self.df.columns if c not in self.index_cols]

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                a, b = cols[i], cols[j]
                try:
                    mi = self._mutual_info_column_pair(a, b)
                    results.append({"col_a": a, "col_b": b, "mutual_info": round(mi, 5)})
                except Exception as e:
                    logger.debug("skipping pair %s-%s: %s", a, b, e)
                    continue

        results = sorted(results, key=lambda r: r["mutual_info"], reverse=True)
        return results[:top_k]
    









