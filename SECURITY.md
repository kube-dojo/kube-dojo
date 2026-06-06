# Security Policy

## Reporting a Vulnerability

If you discover a security issue in KubeDojo's content (e.g., a command that could be harmful, credentials in examples, or a misconfigured exercise), please report it by:

1. Opening a [GitHub issue](https://github.com/kube-dojo/kube-dojo.github.io/issues) with the label "security"
2. Or emailing the maintainers directly

## Scope

KubeDojo is primarily educational content (markdown modules), but the repository also has a **CI/build pipeline** and an **npm dependency supply chain** (Astro/Starlight site build). Security concerns include:

- Commands or YAML examples that could be harmful if copy-pasted
- Accidental inclusion of real credentials or tokens in examples
- Links to malicious external resources
- Compromised or malicious npm dependencies and lockfile tampering
- GitHub Actions workflow misconfiguration

There is no production application backend or learner user data stored in this repo.

## Supply-Chain Security

Miasma-class npm supply-chain defenses are tracked in [issue #1812](https://github.com/kube-dojo/kube-dojo.github.io/issues/1812).

- **Maintainers:** [docs/security/detection-runbook.md](docs/security/detection-runbook.md) — what each control detects and how to triage CI failures
- **Developers:** [docs/security/local-dev-supply-chain.md](docs/security/local-dev-supply-chain.md) — `.npmrc` script blocking, local rebuild, token hygiene

## Content Security

- All example credentials use placeholder values (`my-secret`, `changeme`, `example.com`)
- No real API keys, tokens, or passwords are included
- External links are reviewed for legitimacy
