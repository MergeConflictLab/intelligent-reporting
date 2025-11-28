
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "prep_time_vs_calories_5790"

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
import plotly.express as px

df = pd.read_csv('data/cleaned_salad_data.csv')
required_cols = ['prep_time', 'Calories']
df = df[required_cols].dropna()

plt.figure(figsize=(10, 6))
plt.scatter(df['prep_time'], df['Calories'], alpha=0.7)
plt.xlabel('Preparation Time')
plt.ylabel('Calories')
plt.title('Preparation Time vs Calories')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('prep_time_vs_calories.png')