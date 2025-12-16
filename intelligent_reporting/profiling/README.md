# 📊 Automated Data Profiling & Exploratory Analysis Pipeline

A **production-oriented, modular EDA system** that automatically inspects any dataset and produces **statistical summaries, visual insights, correlation analysis, and representative samples** — with **minimal user input** and **robust failure handling**.


---

##  Why This Exists

Exploratory Data Analysis is often:
- Repetitive  
- Error-prone  
- Inconsistent across datasets  
- Too dependent on manual decisions
- time consuming
- need several data analysts depending on data domain knowledge

This pipeline aims to:
- **Standardize EDA outputs**
- **Handle edge cases gracefully**
- **Scale across datasets with different structures**
- **Produce presentation-ready artifacts**

---

##  Engineering Principles Applied

- **Modular design** 
- **Safe defaults & graceful degradation**
- **Brand-consistent visualization styling**
- **Non-technical user experience**

---

##  Architecture Overview

The pipeline is composed of **independent, composable modules**:



Each module:
- Operates independently
- Logs its own execution
- Skips invalid operations instead of failing
- Produces reusable artifacts (JSON / PNG)

---

##  Core Features

---

###  Representative Data Sampling

Extracts a **meaningful subset** of the data while preserving structure.

- Random sampling
- systematic sampling
- Stratified sampling
- Configurable sample size
- Distribution-aware selection

 Output:
- Sample saved to disk for downstream usage

---

###  Data Summary & Quality Profiling

Produces a **high-level and column-level understanding** of the dataset.

Includes:
- Dataset shape (rows / columns)
- Missing values (count & percentage)
- Duplicate row detection
- Descriptive statistics (mean, std, quartiles)
- Skewness & kurtosis analysis
- Near-zero variance detection
- Constant columns
- Mutual information ranking

 Output:
- Compact or pretty JSON summary

---

### 📈 Automated Visual Analysis

Generates **consistent, presentation-ready plots** without manual tuning.

Automatically adapts to:
- Numeric columns
- Categorical columns
- Datetime columns
- Cardinality limits
- Index / ID column exclusion

Visuals include:
- Distribution histograms (variance-driven)
- Boxplots for categorical–numeric relationships
- Time-series trends
- Outlier distributions
- Ranked categorical frequencies

🎨 All plots share:
- Unified color palette
- Consistent typography
- Clean grid & spacing
- Professional defaults suitable for reports

 Output:
- High-resolution PNG figures

---

###  Correlation & Relationship Analysis

Designed to **surface meaningful relationships without noise**.

Includes:
- Pearson correlation heatmap 
- Automatic removal of invalid / constant columns
- Strong correlation detection (positive & negative)
- Regression plots for top correlated pairs
- Spearman correlation for monotonic relationships

Handles edge cases such as:
- Binary columns
- Constant features
- NaN correlations
- Sparse relationships

Output:
- Heatmap
- Scatter + regression plots

---

## Robustness & Safety

This pipeline is built to **not break** when data is imperfect.

- Index / ID columns are auto-detected and excluded
- Invalid plots are skipped, not crashed
- Logging is silent by default, configurable by the caller
- Modules operate independently
- Sensible defaults prevent over-plotting

---

## Logging & Observability

- Internal logging using Python’s `logging` module
- `NullHandler` by default (safe for libraries)
- Caller can enable logging centrally
- Informative lifecycle messages per module

---

##  Tech Stack

- **Python**
- **Polars** 
- **Seaborn & Matplotlib** 
- **NumPy**
- **SciPy**
- **Scikit-learn** 

---

## 🚀 Typical Usage

```python
import polars as pl
from intelligent_reporting.profiling import *

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger(__name__).info("Profiling pipeline started")




df = pl.read_csv('amazon_products.csv')

RESULTS_DIR = "results"
FIGURES_DIR = "figures"
MAX_ROWS = 5

sampler = DataSampler(df=df, max_rows=MAX_ROWS, sample_dir = RESULTS_DIR)
summarizer = DataSummarizer(df=df, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR)
visualizer = DataVisualizer(df=df, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR, top_k_categories=5)
correlater = DataCorrelater(df=df)

sample = sampler.run_sample()
summary = summarizer.summary()
visualizer.run_viz()
correlater.run()
