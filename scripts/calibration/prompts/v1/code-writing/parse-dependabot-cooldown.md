Implement `parse_dependabot_cooldown(yaml_text: str) -> int | None`.

The function returns the configured Dependabot cooldown days as an `int`, or
`None` if no cooldown is configured.

Constraints:

- Use `yaml.safe_load`.
- Handle malformed input by raising `ValueError`.
- Do not use a bare `except`.
- The output must be ruff-clean Python.
- Return only the implementation code.

Expected behavior:

- `cooldown: { default-days: 7 }` returns `7`.
- Missing `cooldown` returns `None`.
- Non-mapping YAML, non-mapping `cooldown`, negative values, booleans, and
  non-integer values raise `ValueError`.

