# io

This module handles **input/output operations**, including:

- Loading datasets from many file formats.
- Outputing a pandas.DataFrame object.
(Soon)
- Connecting to external data sources such as: PostregSQL, MySQL and Cloud Data Warehouses such as Snowflake, BigQuery ...



need to check the other parameters for read_{format} methods in pandas like:
- seperator detector
- etc

also need to add chunking for really big data file: 
the idea of schema inferer is simple:
ima keep the logic for each chunk
and to determine the final decision about the column type ima caluclate a dict like : {col1: {string: 2, numeric: 4, date: 0, bool: 0}}
and then take the max value of them all the that's the infered schema
when we pass to chunk processing its cool because it doesn't harm memory but we lose visibility over the df

to end the day: ima create a branch and push my project structure on it (to make it visible)
