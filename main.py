import json
from intelligent_reporting.agents.metadata_agent import metadata_query
from scripts.ingest import describe_schema, get_schema
from scripts.load_datasets import load_data
from scripts.clean import clean_dataframe


df = load_data(
    source="mysql://root:Anissa222@localhost:3306/test_db",
    table="users",
)
df = clean_dataframe(df)
schema = get_schema(df)
description = describe_schema(df)
print(schema)
print(description)
raw_response = metadata_query(
    model="mistral",
    sample_data=df.head(5).to_dicts(),
    schema=schema,
    description=description,
)

try:
    response = json.loads(raw_response)
except json.JSONDecodeError:
    response = {"table_description": raw_response, "columns": []}

print(json.dumps(response, indent=2))
