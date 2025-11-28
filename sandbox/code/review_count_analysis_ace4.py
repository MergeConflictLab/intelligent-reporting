
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "review_count_analysis_ace4"

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
if 'n_review' in df.columns:
    plt.figure(figsize=(10, 6))
    plt.hist(df['n_review'].dropna(), bins=30, edgecolor='black')
    plt.xlabel('Number of Reviews')
    plt.ylabel('Frequency')
    plt.title('Distribution of Review Counts')
    plt.savefig('review_count_histogram.png')
    plt.close()