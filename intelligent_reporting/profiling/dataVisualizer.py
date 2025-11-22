import os
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
        self.cat_cols = self.df.select_dtypes(include=['category','object']).columns.tolist()
        self.datetime_cols = self.df.select_dtypes(include=['datetime64[ns]']).columns.tolist()

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

        for col in self.cat_cols[:3]:
            top_categories = (
                self.df[col].value_counts()
                .head(self.top_k_categories)
                .reset_index()
            )
            top_categories.columns = [col, "count"]

            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=top_categories, y="count", x=col, ax=ax)
            ax.set_title(f"Top {self.top_k_categories} categories for {col}")
            plt.xticks(rotation=45, ha="right")

            self._save_plot(fig, f"bar_{col}")

    def plot_time_series_columns(self):
        #datetime_cols = self.df.select_dtypes(include=['datetime64[ns]']).columns.tolist()

        if not self.datetime_cols:
            print("No datetime columns found for time series plotting.")
            return
        
        df_num = self.df.select_dtypes(include='number')
        if df_num.empty:
            print("No numeric columns found to plot against datetime columns.")
            return
        
        best_num = df_num.var().idxmax()

        os.makedirs(self.figures_dir, exist_ok=True)

        for col in self.datetime_cols[:2]: 
            time_df = self.df.groupby(col, as_index=False)[best_num].mean().sort_values(col)

            
            # Use the first numeric column by default
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=time_df, x=col, y=best_num, ax=ax, marker="o")
            ax.set_title(f"{best_num} over time ({col})")
            ax.set_xlabel(col)
            ax.set_ylabel(best_num)
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


