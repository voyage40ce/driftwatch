# Archive Feature

The `archiver` module compresses and stores `DriftReport` snapshots as `.json.gz` files
under `.driftwatch/archives/`.

## File naming

```
<env>_<unix_timestamp>.json.gz
```

## CLI usage

```bash
# Save a drift report archive
driftwatch archive save source.yaml deployed.yaml --env prod

# List archives (optionally filter by env)
driftwatch archive list --env prod --limit 10

# Clear archives for an environment
driftwatch archive clear --env prod
```

## Payload schema

```json
{
  "env": "prod",
  "timestamp": 1700000000.0,
  "has_drift": true,
  "changes": [
    {"key": "db.host", "source": "prod-db", "deployed": "staging-db", "kind": "changed"}
  ]
}
```
