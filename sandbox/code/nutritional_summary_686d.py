
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "nutritional_summary_686d"

import matplotlib.pyplot as plt
_old_savefig = plt.savefig
def _custom_savefig(path, *args, **kwargs):
    fname = TASK_ID + "_" + os.path.basename(path)
    full = os.path.join(OUTPUT_DIR, fname)
    _old_savefig(full, *args, **kwargs)
plt.savefig = _custom_savefig

import pandas as pd
import numpy as np

df = pd.read_csv('data/cleaned_salad_data.csv')
nutritional_columns = ['Calories', 'Total Fat', 'Saturated Fat', 'Carbohydrates', 'Dietary Fiber', 'Sugar', 'Protein', 'Cholesterol', 'Sodium']
available_columns = [col for col in nutritional_columns if col in df.columns]
summary_stats = df[available_columns].describe()
print(summary_stats)