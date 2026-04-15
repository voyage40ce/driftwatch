# driftwatch

> A CLI tool that detects configuration drift between deployed environments and source-of-truth YAML files.

---

## Installation

```bash
pip install driftwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/driftwatch.git && cd driftwatch && pip install .
```

---

## Usage

Compare a deployed environment against a YAML source-of-truth file:

```bash
driftwatch check --source config/production.yaml --env production
```

**Example output:**

```
[DRIFT DETECTED] production
  ✗ database.max_connections: expected 100, got 50
  ✗ cache.ttl: expected 3600, got 300
  ✓ app.debug: OK

2 drift(s) found in production.
```

### Options

| Flag | Description |
|------|-------------|
| `--source` | Path to the source-of-truth YAML file |
| `--env` | Target environment name to inspect |
| `--strict` | Exit with non-zero code if any drift is found |
| `--output` | Output format: `text` (default), `json`, `csv` |

---

## Why driftwatch?

Configuration drift is silent and dangerous. `driftwatch` gives you a fast, scriptable way to catch mismatches before they become incidents — perfect for CI/CD pipelines and routine audits.

---

## License

This project is licensed under the [MIT License](LICENSE).