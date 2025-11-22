import seaborn as sns
import os
import matplotlib.pyplot as plt
import json
import numpy as np

class AutoExploratory:
    def __init__(self, df):
        self.df = df
        self.output_dir = "json_output"
        self.figures_dir = "figures"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

    def summary(self):
        print(f"the data has {self.df.shape[0]} row and {self.df.shape[1]} columns")
        n_rows, n_cols = self.df.shape

        print("the first row of the data \n", self.df.head(1))

        print('-------------------------------')
        print("the last row of the data \n", self.df.tail(1))

        summary_info = {"num_rows": n_rows,"num_columns": n_cols }
        skew = self.df.skew(numeric_only=True).abs()
        if skew.empty:
            print("No numeric columns found — skipping skew/kurtosis analysis.")
            return summary_info

        kurtosis = self.df.kurtosis(numeric_only=True).abs()
        score = skew * kurtosis
        target_col = score.idxmax()

        # Detect if log transform is needed
        log = (kurtosis[target_col] > 5) or (skew[target_col] > 1)

        if log:
            # log1p safely handles 0 values
            data_to_plot = np.log1p(self.df[target_col])
            plot_title = f"Most Extreme Column (Log Scale): {target_col}\nSkew={skew[target_col]:.2f}, Kurtosis={kurtosis[target_col]:.2f}"
        else:
            data_to_plot = self.df[target_col]
            plot_title = f"Most Extreme Column: {target_col}\nSkew={skew[target_col]:.2f}, Kurtosis={kurtosis[target_col]:.2f}"


        '''plt.figure(figsize=(6,4))
        sns.boxplot(x=data_to_plot)
        plt.title(plot_title)
        plt.tight_layout()
        plt.savefig("figures/skewed_kurtosis_column_plot.png")
'''

        top_tail_skew = self.df.skew(numeric_only=True).sort_values(ascending = False)

        print(f"Most largest skewed column: {top_tail_skew.index[0]} (skew = {top_tail_skew.iloc[0]:.2f})")
        print(f"Most lowest skewed column: {top_tail_skew.index[-1]} (skew = {top_tail_skew.iloc[-1]:.2f})")

       
        summary_info["large_skew"] = {"column": top_tail_skew.index[0],"skew_value": round(top_tail_skew.iloc[0], 2)}

        summary_info["low_skew"] = {"column": top_tail_skew.index[-1],"skew_value": round(top_tail_skew.iloc[-1], 2)}


        print('-------------------')
        print(f'a statistical summary of the data: \n {self.df.describe(exclude="object")}')
        print(f'number of duplicated rows: {self.df.duplicated().sum()}')

        summary_info['missing_values'] = self.df.isnull().sum().to_dict()
        summary_info["statistical_summary"] = self.df.describe(exclude="object").to_dict()
        
        constant_cols = {}
        for col in self.df.columns:
            top_freq = self.df[col].value_counts(normalize=True, dropna=False).iloc[0]
            if top_freq >= 0.8:
                constant_cols[col] = round(float(top_freq), 2)
        summary_info["constant_columns"] = constant_cols

        if len(constant_cols) ==0:
            summary_info["constant_columns"] = "there's no constant column"

        json_path = os.path.join(self.output_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, indent=4, ensure_ascii=False)

            
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 2, 1)
        sns.boxplot(x=data_to_plot)
        plt.title(plot_title)

        plt.subplot(1, 2, 2)
        sns.histplot(data_to_plot, kde=True, color='red')
        plt.title(plot_title)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, "skewed_columns_plot.png"))








