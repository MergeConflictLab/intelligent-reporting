
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "prep_time_distribution_0108"

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
plt.figure(figsize=(10, 6))
plt.hist(df['prep_time'], bins=20, edgecolor='black', alpha=0.7)
plt.xlabel('Preparation Time')
plt.ylabel('Frequency')
plt.title('Distribution of Preparation Times')
plt.grid(True, alpha=0.3)
plt.savefig('prep_time_distribution.png')