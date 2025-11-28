import json
import os
import glob
import time
import subprocess
import nbformat as nbf
from intelligent_reporting.agents.metadata_agent import metadata_query
from scripts.script import (
    load_data,
    get_schema,
    describe_schema,
    clean_dataframe,
)
from intelligent_reporting.agents.insight_agent import insights_query
from scripts.utils import json_fix, strip_code_fence
from scripts.utils import encode_image


df = load_data(source="data/cleaned_salad_data.csv")
df = clean_dataframe(df)
schema = get_schema(df)
description = describe_schema(df)

print(description)
print('--------------------------------------- \n')
print(schema)

print('-----------')

print(df.head(5))


print('--------------------------------------- \n')

# --- METADATA AGENT ---
raw_response = metadata_query(
    model="deepseek-v3.1:671b-cloud",
    sample_data=df.head(5).to_dicts(),
    schema=schema,
    description=description,
)

response = json_fix(raw_response)
if isinstance(response, str):
    try:
        response = json.loads(response)
    except Exception:
        response = {"table_description": response, "columns": []}