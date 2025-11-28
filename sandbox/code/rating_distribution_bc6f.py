
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "rating_distribution_bc6f"

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
if 'n_star' in df.columns:
    rating_counts = df['n_star'].value_counts().sort_index()
    plt.figure(figsize=(10, 6))
    rating_counts.plot(kind='bar')
    plt.title('Distribution of Recipe Star Ratings')
    plt.xlabel('Star Rating')
    plt.ylabel('Frequency')
    plt.savefig('rating_distribution.png')