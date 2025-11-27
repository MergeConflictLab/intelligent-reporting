from intelligent_reporting.profiling.dataSummarizer import  AutoExploratory
from intelligent_reporting.profiling.dataVisualizer import DataViz
from intelligent_reporting.profiling.dataCorrelations import DataCorrelations
from intelligent_reporting.profiling.dataSampler import Sampling
import pandas as pd



df = pd.read_csv('https://raw.githubusercontent.com/jamal-eddine-obeidat/intermediate-real-world-data-cleaning-salad-health/refs/heads/master/cleaned_salad_data.csv')
#df = pd.read_csv('/mnt/c/Users/jamal/Downloads/archive/youtube_recommendation_dataset.csv')

data_sample = Sampling(df)
samp = data_sample.run_simple()

exploratory = AutoExploratory(df)
summary = exploratory.summary()
print(summary)


data_viz = DataViz(df)
visualizations = data_viz.run_viz()

data_corr = DataCorrelations(df)
correlations = data_corr.run()

#data_sample = Sampling(df)
#samp = data_sample.run_simple()