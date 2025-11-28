
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "nutrition_correlation_7d07"

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
columns_to_use = ['Calories', 'Total Fat', 'Saturated Fat', 'Carbohydrates', 'Dietary Fiber', 'Sugar', 'Protein', 'Cholesterol', 'Sodium']
available_columns = [col for col in columns_to_use if col in df.columns]
correlation_matrix = df[available_columns].corr()
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Nutritional Components Correlation Matrix')
plt.tight_layout()
plt.savefig('nutrition_correlation_heatmap.png')