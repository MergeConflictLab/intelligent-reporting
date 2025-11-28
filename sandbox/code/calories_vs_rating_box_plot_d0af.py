
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "calories_vs_rating_box_plot_d0af"

import matplotlib.pyplot as plt
_old_savefig = plt.savefig
def _custom_savefig(path, *args, **kwargs):
    fname = TASK_ID + "_" + os.path.basename(path)
    full = os.path.join(OUTPUT_DIR, fname)
    _old_savefig(full, *args, **kwargs)
plt.savefig = _custom_savefig

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/cleaned_salad_data.csv')
required_cols = ['Calories', 'n_star']
df = df[required_cols].dropna()

plt.figure(figsize=(10, 6))
sns.boxplot(x='n_star', y='Calories', data=df)
plt.title('Calories vs Star Rating')
plt.xlabel('Star Rating')
plt.ylabel('Calories')
plt.savefig('calories_vs_rating_box_plot.png')