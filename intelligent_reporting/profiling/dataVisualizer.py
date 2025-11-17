import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

class DataViz:
    def __init__(self, df):
        self.df = df
        self.output_dir = "json_output"
        self.figures_dir = "figures"
        self.top_k_categories = 5

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

        # Identify columns once for reuse
        self.numeric_cols = self.df.select_dtypes(include='number').columns.tolist()
        self.cat_cols = self.df.select_dtypes(exclude=['number', 'datetime64']).columns.tolist()
        self.datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()

    def _save_plot(self, fig, name):
        fname = f"{name}.png"
        path = os.path.join(self.figures_dir, fname)
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    # Plot top-variance numeric distributions
    def plot_numeric_distributions(self):
        if not self.numeric_cols:
            print("No numeric columns found.")
            return

        variances = self.df[self.numeric_cols].var().sort_values(ascending=False)
        top_vars = variances.head(2)

        for col in top_vars.index:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.histplot(data=self.df, x=col, kde=True, ax=ax)
            ax.set_title(f"Distribution of {col} (Variance={top_vars[col]:.2f})")
            self._save_plot(fig, f"hist_{col}")

    # Plot top categories for categorical columns
    def plot_categorical_columns(self):
        if not self.cat_cols:
            print("No categorical columns found.")
            return

        for col in self.cat_cols[:2]:
            top_categories = (
                self.df[col].value_counts()
                .head(self.top_k_categories)
                .reset_index()
            )
            top_categories.columns = [col, "count"]

            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=top_categories, x="count", y=col, ax=ax)
            ax.set_title(f"Top {self.top_k_categories} categories for {col}")
            self._save_plot(fig, f"bar_{col}")

    def plot_time_series_columns(self):
        datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if not datetime_cols:
            print("No datetime columns found for time series plotting.")
            return

        os.makedirs(self.figures_dir, exist_ok=True)

        for col in datetime_cols[:2]:  # limit to 2 if too many
            # Choose a numeric column to plot against time
            numeric_cols = self.df.select_dtypes(include='number').columns.tolist()
            if not numeric_cols:
                print(f"No numeric columns found to plot against {col}")
                continue
            
            # Use the first numeric column by default
            num_col = numeric_cols[0]

            # Aggregate by date (if many rows per day)
            time_df = self.df.groupby(col, as_index=False)[num_col].mean().sort_values(col)

            # Plot
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=time_df, x=col, y=num_col, ax=ax, marker="o")
            ax.set_title(f"{num_col} over time ({col})")
            ax.set_xlabel(col)
            ax.set_ylabel(num_col)
            ax.grid(True, linestyle="--", alpha=0.6)

            self._save_plot(fig, f"time_series_{col}")


    # Combined execution method
    def run_viz(self):
        print("Generating numeric plots...")
        self.plot_numeric_distributions()

        print("Generating categorical plots...")
        self.plot_categorical_columns()

        print("Generating time series plots...")
        self.plot_time_series_columns()

        print("All plots saved in:", self.figures_dir)


