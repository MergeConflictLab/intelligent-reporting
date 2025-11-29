import json
import os
import time
import nbformat as nbf

###
from intelligent_reporting.profiling.dataSummarizer import  AutoExploratory
from intelligent_reporting.profiling.dataVisualizer import DataViz
from intelligent_reporting.profiling.dataCorrelations import DataCorrelations
from intelligent_reporting.profiling.dataSampler import Sampling
import pandas as pd
###

from intelligent_reporting.agents.metadata_agent import metadata_query
from scripts.script import load_data, get_schema, describe_schema, clean_dataframe
from intelligent_reporting.agents.insight_agent import insights_query
from scripts.utils import strip_code_fence, encode_image

from datetime import datetime

def main():
    start = datetime.now()
    
    df = pd.read_csv('data/cleaned_salad_data.csv')
    data_sample = Sampling(df)
    samp = data_sample.run_simple()
    print('sampling is done=========')


    exploratory = AutoExploratory(df)
    summary = exploratory.summary()
    print('summary is done=========')


    data_viz = DataViz(df)
    visualizations = data_viz.run_viz()
    print('visualization is done=========',summary)

    data_corr = DataCorrelations(df)
    correlations = data_corr.run()
    print('correlation is done=========',summary)


    # --- LOAD DATA ---
    df = load_data(source="data/cleaned_salad_data.csv")
    df = clean_dataframe(df)
    schema = get_schema(df)
    description = describe_schema(df)

    print("--------------")

    # --- METADATA AGENT ---
    raw_response = metadata_query(
        #model="deepseek-v3.1:671b-cloud",
        model = 'qwen3-vl:235b-cloud',

        sample_data=df.head(5).to_dicts(),
        schema=schema,
        description=description,
    )

    response = strip_code_fence(raw_response)
    print('response',response)
    try:
        metadata = json.loads(response)
    except:
        metadata = {"table_description": response, "columns": []}

    #print("==============", metadata)
    print('--------------------------')

    # --- LOAD SUMMARY.JSON (IMPORTANT FIX) ---
    with open("EDA_output/data_summary.json", "r") as f:
        summary_data = json.load(f)

    with open("EDA_output/sample_output.json", "r") as s:
        sample_data = json.load(s)

    figures_dir = "EDA_output/figures"
    insights = []

    # Loop over all plots
    for file_name in os.listdir(figures_dir):

        if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        img_path = os.path.join(figures_dir, file_name)
        encoded_image = encode_image(img_path)

        # --- INSIGHT AGENT ---
        insight = insights_query(
            img=encoded_image,
            summary_data=summary_data,
            #sample_data=df.head(2).to_dicts(),
            sample_data = sample_data,
            description=metadata,
        )

        insights.append({
            "figure": file_name,
            "insight": insight
        })

        print("\nInsight generated for:", file_name)
        print(json.dumps(insight, indent=2, ensure_ascii=False))

        time.sleep(3)

    # optional: save final insight json
    with open("EDA_output/insights.json", "w") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)

    print("\nAll insights generated and saved to EDA/insights.json")
    finish = datetime.now()
    print(f"Start: {start}, Finish: {finish}, Duration: {finish - start}")

if __name__ == "__main__":
    main()