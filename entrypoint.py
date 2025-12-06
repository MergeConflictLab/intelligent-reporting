from reporting_pipeline import ReportingPipeline

pipe = ReportingPipeline(file="data/cleaned_salad_data.csv")

notebook_path = pipe.run()
