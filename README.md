# App starter

A reusable starter for a Lakebase-backed Databricks App. It runs locally as
you, connects to your Lakebase branch, and proves the database round-trip
works. There are no tables and no app features yet: you build those on top. The
connection plumbing (environment-aware connection, token minting, DABs bundle)
is already built and verified, so your time goes on building features and
learning the local dev loop, not on debugging connection setup.

## How the connection works

`src/app/db.py` is the single connection module. It picks the right path
automatically:

- Local: connects as you, using the endpoint and CLI profile from `.env`.
- Deployed: connects as the app's service principal, using the variables the platform injects.

Either way it mints a short-lived token per connection (1-hour expiry) instead
of storing a password, and the connection pool refreshes before the token
expires. No passwords live in the code or config.

## Dependencies

`pyproject.toml` lists the dependencies, and `uv` installs them:

- Local: `uv sync` installs into `src/app/.venv`.
- Deployed: the start command `uv run streamlit run app.py` installs them on first start.

`uv.lock` is intentionally gitignored. A lockfile pins the exact package index
it was built against (for example a corporate proxy rather than public PyPI),
which then fails in a different environment. Leaving it out lets each
environment resolve packages against its own index.

## What's here

```
databricks.yml              DABs bundle and targets
resources/
  app-starter.app.yml       App resource and Lakebase branch binding
src/app/
  app.py                    Streamlit app: connection panel and DB ping
  db.py                     Environment-aware connection (you locally, SP deployed)
  app.yaml                  Start command and LAKEBASE_ENDPOINT
  pyproject.toml            uv project (Python 3.11) and dependencies
.vscode/launch.json         F5 to run locally with breakpoints
.env.example                Template for local config (copy to .env)
```

## Before you run: fill in the placeholders

A few values are specific to you and your workspace. Replace each placeholder
everywhere it appears:

| Placeholder | What it is | Where it appears |
| --- | --- | --- |
| `<PROFILE>` | your Databricks CLI login profile | `.env`, `databricks.yml` |
| `<PROJECT>` / `<BRANCH>` | your Lakebase project and branch | `.env`, `resources/app-starter.app.yml` |
| `<unique-suffix>` | a short lowercase suffix that makes your app name unique in the shared workspace | `resources/app-starter.app.yml` |

## End to end

1. Cut your branch off `production` and note its read-write endpoint (`primary`):
   ```
   databricks postgres create-branch projects/<PROJECT> <BRANCH> \
     --json '{"spec":{"source_branch":"projects/<PROJECT>/branches/production","ttl":"2592000s"}}' \
     --profile <PROFILE>
   ```
2. `cp .env.example .env` (repo root), then set `LAKEBASE_ENDPOINT` for your
   branch and `DATABRICKS_CONFIG_PROFILE` to your login profile.
3. Run locally, as you, from `src/app`:
   ```
   cd src/app && uv sync
   ```
   Then hit **F5** in VS Code ("Run app locally (Streamlit)"), or run
   `uv run streamlit run app.py`. Ping the database: you connect as your own
   user. A valid connection, nothing more.
4. Build a feature that stores something, and create its table directly on your
   branch, as yourself (Lakebase SQL Editor or `databricks psql`). Because you
   create it, you own it.
5. Deploy:
   ```
   databricks bundle validate --profile <PROFILE>
   databricks bundle deploy   --profile <PROFILE>
   databricks bundle run app-starter --profile <PROFILE>
   ```
6. The identity flip. Deployed, the app connects as its service principal, not
   as you. The table is yours, so the service principal cannot see it: it has
   `CONNECT` and `CREATE` on the database but no access to your schema. The app
   breaks the moment it reads or writes that table. That gap is the main thing
   this starter exists to teach.
7. Fix it with a direct grant: grant the service principal `USAGE` on the
   schema and the privileges it needs on the table, then restart.

## Not in the starter (on purpose)

- No migrations: the schema is hand-created in plain SQL.
- No owning role or groups: grants are direct.
- No tables or app features yet: you build them.
