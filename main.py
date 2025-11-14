import json
from intelligent_reporting.agents.metadata_agent import metadata_query
from intelligent_reporting.agents.supervisor_agent import supervisor_query
from scripts.ingest import describe_schema, get_schema
from scripts.load_datasets import load_data
from scripts.clean import clean_dataframe



# TODO: Port over Jamal's improvements for dataset sampling
# NOTE: the cleaning and processing steps here are minimal and meant for basic preparation before metadata querying, it will need to be adapted based on dataset specifics.

df = load_data(source="data/BMW-sales-data.csv")
df = clean_dataframe(df)
schema = get_schema(df)
description = describe_schema(df)
print(description)
print(schema)
raw_response = metadata_query(
    model="mistral",  # TODO: Boubker to test with other models and add support for model selection
    sample_data=df.head(5).to_dicts(),
    schema=schema,
    description=description,
)

try:
    response = json.loads(raw_response)
except json.JSONDecodeError:
    response = {"table_description": raw_response, "columns": []}

print(supervisor_query(
    description=response,
    model= "mistral", 
    sample_data=df.head(5).to_dict(),))

print(json.dumps(response, indent=2))
