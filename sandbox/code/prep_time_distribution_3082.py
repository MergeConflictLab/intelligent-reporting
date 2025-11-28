
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "prep_time_distribution_3082"

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
df = pd.read_csv('data/cleaned_salad_data.csv')
if 'prep_time' in df.columns:
    plt.figure(figsize=(10, 6))
    plt.hist(df['prep_time'].dropna(), bins='auto', edgecolor='black')
    plt.xlabel('Preparation Time')
    plt.ylabel('Frequency')
    plt.title('Distribution of Preparation Times')
    plt.savefig('prep_time_distribution_histogram.png')
    plt.close()