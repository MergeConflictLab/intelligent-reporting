# 📊 Data Profiling & Exploratory Analysis Tool

A modular data-profiling pipeline designed to  generate **data summary**, **visualizations**, **correlation insights**, and a **representative sample** of any dataset.

This helps analysts and data scientists understand the structure, quality, and relationships inside their data before modeling or reporting.

---

## Features


### 4. Representative Data Sampling  

extract a sample depending on the data we have:  
- Random sample  
- Stratified sample (if target column provided)  
- Configurable sample size  
- Ensures similar distribution to the original dataset.

###  Data Summary  
Provides a complete overview of the dataset:  
- Number of rows & columns  
- Data types  
- Missing values per column  
- Descriptive statistics
- Skewness & kurtosis  
- Most skewed columns  
- Unique values count  
- Constant columns detection  

Output saved as JSON (`sample_output.json`).

---

###  Data Visualization  
Automatically generates key visualizations:  
- Histograms  
- Boxplots  
- Bar charts  
- Scatter plots  
- Outlier distribution  


---

###  Correlation Analysis  
Includes:  
- Correlation matrix  
- Correlation heatmap  
- Identification of highly correlated features  
Useful for feature selection and reducing redundancy.

---

