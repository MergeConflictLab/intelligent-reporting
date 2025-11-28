
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "fat_vs_protein_scatter_7e6e"

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
required_cols = ['Total Fat', 'Protein']
df = df[required_cols].dropna()

plt.figure(figsize=(10, 6))
plt.scatter(df['Total Fat'], df['Protein'], alpha=0.7)
plt.xlabel('Total Fat')
plt.ylabel('Protein')
plt.title('Relationship between Total Fat and Protein Content')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('fat_vs_protein_scatter.png')