# ContractSentinel — Contract Structure Extraction Prompt Requirements

## Objective

Extract structured legal information from a full contract text using **a single LLM call**.

The LLM must return **exactly one valid JSON object** containing five top-level fields:

- `clauses`
- `definitions`
- `parties`
- `cross_references`
- `obligations`

The output must be directly parsable using:

```python
json.loads(response)
