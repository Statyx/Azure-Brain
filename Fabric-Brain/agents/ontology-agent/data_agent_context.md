# Ontology Context in Fabric Data Agent

## The current contract

A new-experience ontology is a **context source** for a Fabric Data Agent. It supplies governed:

- entities, properties, relationships;
- definitions and synonyms;
- metrics and rules;
- mappings and bindings to physical sources.

The Data Agent uses that context to select a relevant underlying source, generates a
source-native query, executes it with the requesting user's permissions, and formats the result.

```text
Question
  → ontology context interprets business meaning
  → Data Agent selects a bound source
  → NL2SQL / NL2KQL / NL2DAX
  → source executes under user permissions
  → answer
```

Ontology is **not** the query execution endpoint in this integration.

## Source routing

| Underlying source | Query language |
| --- | --- |
| Lakehouse, Warehouse, SQL Database, Mirrored Database | T-SQL / SQL |
| Eventhouse / KQL Database | KQL |
| Power BI Semantic Model | DAX |
| Graph Model attached separately | GQL |

GQL is not the default language of an ontology context source. Use GQL only when a Graph Model
is materialized/attached and the relationship path is the question.

## Configuration sequence

1. Open the Data Agent **Sources** experience.
2. Add the ontology.
3. Expand it and review associated ontology data sources.
4. Mount eligible underlying sources when the agent needs source-specific:
   - instructions;
   - descriptions;
   - example queries.
5. Keep shared business definitions and mappings in the ontology.
6. Keep query-engine-specific guidance on the mounted source.
7. Test and inspect the run steps.

The ontology representation in the Data Agent is read-only. Changes flow from the ontology item;
refresh the ontology context in the Data Agent after editing it. Automatic refresh can take up to
10 minutes.

## Important limits

- Entity selection inside an ontology context isn't currently supported.
- One question routes to a relevant underlying source; do not assume federated cross-source joins.
- Sharing the Data Agent does not grant access to the ontology or its underlying sources.
- The requester needs permission on the selected source.
- Power BI semantic models have configuration differences: use Prep for AI for AI instructions,
  schema, and Verified Answers rather than assuming Data-Agent-local examples/descriptions.
- Semantic-model grounding used by the **ontology agent** is not automatically reused by a
  Fabric Data Agent. Attach the semantic model directly when the Data Agent must run DAX.
- A Data Agent supports up to five sources in total.

## Debugging

When an answer is wrong:

1. Inspect the run steps and identify the selected underlying source.
2. Review the generated T-SQL, KQL, or DAX.
3. Run the query against the source.
4. Download the Data Agent's ontology context.
5. Verify definitions, synonyms, mappings, bindings, and source association.
6. Refresh ontology context and retry.

| Observation | Fix |
| --- | --- |
| Wrong source selected | Improve ontology mappings and mounted-source descriptions |
| Wrong table/column/filter | Correct ontology bindings or source-specific guidance |
| Correct query, wrong/empty result | Validate source data and user permissions |
| Recent ontology change absent | Manual refresh; otherwise wait for context refresh |
| Cross-source answer incomplete | Split the question or orchestrate outside the Data Agent |

## REST/definition caution

Microsoft documents the UI integration and behavior, but the public Data Agent item-definition
documentation does not yet provide a stable hand-authored ontology-context part contract.

Do not reuse the old reverse-engineered pattern `type: "ontology"` + GQL few-shots as if it were
the new contract. For automation:

1. configure a working current Data Agent in the portal;
2. retrieve its definition;
3. preserve the emitted part shapes;
4. validate with a round trip in a non-production workspace;
5. record the observed schema before generalizing it.

## Sources

- [Use Ontology as context in Fabric data agent](https://learn.microsoft.com/fabric/data-science/data-agent-ontology-sources)
- [Add and configure data sources in Fabric data agent](https://learn.microsoft.com/fabric/data-science/data-agent-add-datasources)
