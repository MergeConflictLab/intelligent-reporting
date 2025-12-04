"""
High-level orchestration pipeline.
"""
import os
import json
from pathlib import Path
from intelligent_reporting.loading import *
from intelligent_reporting.profiling import *
from intelligent_reporting.custom_typing import *
from intelligent_reporting.agents.metadata_agent import metadata_query
from intelligent_reporting.agents.insights_agent import insights_query
from intelligent_reporting.orchestrator.data_pipeline_selector import DataPipelineSelector
from intelligent_reporting.utils.utils import encode_image

class ReportingPipeline:
    def __init__(self, *, file: str = None, db_url: str = None, db_table: str = None, model="deepseek-v3.1:671b-cloud"):
        self.file = file
        self.db_url = db_url
        self.db_table = db_table
        self.model = model

    def load_data_and_schema(self):
        selector = DataPipelineSelector(
            file=self.file,
            db_url=self.db_url,
            db_table=self.db_table
        )
        df, schema = selector.run()
        return df, schema

    def extract_metadata(self, df, schema):
        metadata_raw = metadata_query(
            model=self.model,
            sample_data=df.head(5).to_dicts(),
            schema=schema,
        )
        return metadata_raw
    

    def run(self):
        RESULTS_DIR = "results"
        FIGURES_DIR = "figures"
        FILE_NAME = Path(self.file if self.file else self.table).stem

        insights = []

        # Data loading and schema inference
        df, schema = self.load_data_and_schema()

        # Sample, summary and visualization generation
        sampler = DataSampler(df=df, max_rows=4, sample_dir = RESULTS_DIR)
        summarizer = DataSummarizer(df=df, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR)
        visualizer = DataVisualizer(df=df, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR, top_k_categories=5)
        correlater = DataCorrelater(df=df)

        sample = sampler.run_sample()
        summary = summarizer.summary()
        visualizer.run_viz()
        correlater.run()

        # metadata extraction
        metadata = self.extract_metadata(df, schema)

        # insight generation for each plot in FIGURES_DIR
        path = os.path.join(RESULTS_DIR, FIGURES_DIR)

        for file_name in os.listdir(path):
            if file_name.lower().endswith((".png", ".jpg", ".jpeg")):

                img_path = os.path.join(path, file_name)
                encoded_image = encode_image(img_path)

                insight = insights_query(
                    img=encoded_image,
                    summary_data=summary,
                    sample_data = sample,
                    description=metadata,
                )

                insights.append({
                    "figure": file_name,
                    "insight": insight
                })

            insights_file = f"{RESULTS_DIR}/{FILE_NAME}_insights.json"
            with open(insights_file, "w") as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)

        print(f"\nAll insights generated and saved to: {insights_file}")
        



