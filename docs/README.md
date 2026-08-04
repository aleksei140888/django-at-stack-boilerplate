# Documentation

Hot routing for the most frequent decisions lives in [`../CLAUDE.md`](../CLAUDE.md);
come here when there is no line for what you are doing.

Read what is relevant to the task at hand — do not pull the whole folder in
advance.

## Working with the code

| File | What it is for |
|---|---|
| [`architecture.md`](architecture.md) | Where code belongs, how apps stay decoupled, the request path, the settings layers |
| [`conventions.md`](conventions.md) | Style, commits, versioning, the opt-in gates and what they are for |
| [`testing.md`](testing.md) | Test mechanics: minimum coverage, parallel-run rules, factories, query budgets |
| [`test-environment.md`](test-environment.md) | `make demo-up`: a running site with data, no Docker or API keys |
| [`observability.md`](observability.md) | Request ids, structured logs, health checks, metrics — and what to do during an incident |
| [`deployment.md`](deployment.md) | Docker images, static files, environment variables, the production checklist |

## Playbooks

Step-by-step, for the things done often enough to be worth writing down.

| Playbook | When |
|---|---|
| [`playbooks/add-app.md`](playbooks/add-app.md) | A new Django app in `apps/` |
| [`playbooks/add-seeder.md`](playbooks/add-seeder.md) | A domain needs demo data |
| [`playbooks/add-health-check.md`](playbooks/add-health-check.md) | A new external dependency worth monitoring |

## Memory

| File | What it is for |
|---|---|
| [`agents.md`](agents.md) | **Project memory** — architectural decisions, edge cases, traps that cost time. Start from the index at the top; do not read it end to end |
