import seaborn as sns
import os
import matplotlib.pyplot as plt
import json

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

        print("the first three rows of the data \n", self.df.head(3))

        print('-------------------------------')
        print("the last three rows of the data \n", self.df.tail(3))

        summary_info = {
            "num_rows": n_rows,
            "num_columns": n_cols,
            #"first_rows": self.df.head(3).to_dict(orient="records"),
            #"last_rows": self.df.tail(3).to_dict(orient="records"),
        }

        skew_values = self.df.skew(numeric_only=True).sort_values(ascending=False)
        highest_skewed_col = skew_values.index[0]
        lowest_skewed_col = skew_values.index[-1]

        print(f"Most largest skewed column: {skew_values.index[0]} (skew = {skew_values.iloc[0]:.2f})")
        print(f"Most lowest skewed column: {skew_values.index[-1]} (skew = {skew_values.iloc[-1]:.2f})")

        summary_info["largest_skewed"] = { "column": most_pos_col, "skew_value": round(skew_values.iloc[0], 2)}
        summary_info["lowest_skewed"] = {"column": most_neg_col,"skew_value": round(skew_values.iloc[-1], 2)
        }

        print(f'a statistical summary of the data: \n {self.df.describe(exclude="object")}')
        print(f'number of duplicated rows: {self.df.duplicated().sum()}')
    
        summary_info["statistical_summary"] = (self.df.describe(exclude="object").to_dict())

        summary_info["num_duplicated_rows"] = int(self.df.duplicated().sum())

        constant_cols = {}
        for col in self.df.columns:
            top_freq = self.df[col].value_counts(normalize=True, dropna=False).iloc[0]
            if top_freq >= 0.8:
                constant_cols[col] = round(float(top_freq), 2)
        summary_info["constant_columns"] = constant_cols

        most_pos_col = skew_values.index[0]
        most_neg_col = skew_values.index[-1]

        json_path = os.path.join(self.output_dir, "data_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_info, f, indent=4, ensure_ascii=False)

            
        plt.figure(figsize=(10, 5))
        # Most pos skewed
        plt.subplot(1, 2, 1)
        sns.histplot(self.df[most_pos_col], kde=True, color='blue')
        plt.title(f'Most Positively Skewed: {most_pos_col} (Skew={skew_values.iloc[0]:.2f})')


        # Most neg skewed
        plt.subplot(1, 2, 2)
        sns.histplot(self.df[most_neg_col], kde=True, color='red')
        plt.title(f'Most Negatively Skewed: {most_neg_col} (Skew={skew_values.iloc[-1]:.2f})')

        plt.tight_layout()
        plt.savefig("figures/skewed_columns_plot.png")

