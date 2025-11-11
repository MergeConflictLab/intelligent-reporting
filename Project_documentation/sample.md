| Dataset Feature                              | Recommended Strategy                                                        | Why                                             |
| -------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------- |
| Mostly numeric columns, low cardinality      | **Stratified sampling** by quantiles                                        | Ensures each value range appears proportionally |
| High-cardinality categorical columns         | **Group-weighted sampling**                                                 | Keeps categories proportional to real frequency |
| Mixed numeric + categorical                  | **Hybrid stratified** (numeric bins × category strata)                      | Maintains balance across key segments           |
| Very large time-series data                  | **Time-aware systematic sampling** (every k-th record per period)           | Preserves temporal trends                       |
| Strong class imbalance (target column known) | **Stratified by label**                                                     | Keeps rare classes visible                      |
| Textual / unstructured columns               | **Random sampling with diversity check** (use text embeddings + clustering) | Avoids redundant text samples                   |

