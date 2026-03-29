---
title: "Module 1.1: Backstage Developer Workflow"
slug: k8s/cba/module-1.1-backstage-dev-workflow
sidebar:
  order: 2
---
> **Complexity**: `[COMPLEX]` - Full-stack TypeScript project with monorepo tooling
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: Node.js 18+, Docker, basic TypeScript familiarity
>
> **CBA Domain**: Domain 1 - Backstage Developer Workflow (24% of exam)

---

## Why This Module Matters

Backstage is the backbone of the CBA certification. Before you can build plugins, design software catalogs, or integrate with Kubernetes, you need to understand how the Backstage project itself works---its monorepo layout, its build pipeline, its configuration system, and its local development loop.

Domain 1 accounts for nearly a quarter of the exam. Candidates who skip this section tend to stumble on questions about project structure, dependency management, and configuration layering---topics that feel "too basic" until you get them wrong under time pressure.

This module makes sure you do not.

> **The Recording Studio Analogy**
>
> Think of Backstage like a recording studio. The monorepo is the building---it houses every room (package) under one roof. The `packages/app` directory is the mixing console where everything comes together for the listener. The `packages/backend` directory is the sound booth where the real processing happens. Each plugin in `plugins/` is a separate instrument track. Yarn workspaces are the wiring that connects every room so signals flow correctly. The app-config files are the mixing board presets---one for rehearsal (local), one for the live show (production). You would not perform live without a sound check, and you should not deploy Backstage without understanding the studio layout first.

---

## What You'll Learn

By the end of this module, you'll understand:

- How the Backstage monorepo is organized and why
- TypeScript patterns that appear repeatedly in Backstage plugins
- How to scaffold, run, and debug a Backstage app locally
- How to build optimized Docker images for Backstage
- Yarn workspace dependency management and lock files
- The Backstage CLI and its most important commands
- Configuration layering with `app-config.yaml`

---

## Did You Know?

- Backstage was originally built at Spotify to manage over 2,000 microservices across hundreds of teams. It was open-sourced in 2020 and became a CNCF Incubating project in 2022.
- The Backstage monorepo uses Yarn workspaces (not npm workspaces) because Spotify's internal tooling was built around Yarn 1.x---the project later migrated to Yarn 3+ with PnP support.
- A single Backstage instance at a large enterprise can host 100+ plugins. The monorepo structure keeps them all versioned and tested together, avoiding the "dependency hell" of separate repos.
- The `app-config.yaml` system supports environment variable substitution with the `${VAR}` syntax, meaning you never need to hardcode secrets---a pattern the exam tests explicitly.

---

## Part 1: Backstage Monorepo Structure

### 1.1 The Top-Level Layout

When you create a new Backstage app, you get a monorepo with this structure:

```
my-backstage-app/
├── app-config.yaml                 # Base configuration
├── app-config.local.yaml           # Local overrides (gitignored)
├── app-config.production.yaml      # Production overrides
├── catalog-info.yaml               # Self-registration in the catalog
├── package.json                    # Root workspace config
├── packages/
│   ├── app/                        # Frontend React application
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── App.tsx             # Plugin registration & routes
│   │   │   └── components/
│   │   └── public/
│   └── backend/                    # Backend Express application
│       ├── package.json
│       ├── src/
│       │   └── index.ts            # Backend startup & plugin wiring
│       └── Dockerfile              # Production image build
├── plugins/                        # Custom plugins live here
│   ├── my-plugin/                  # Frontend plugin
│   │   ├── package.json
│   │   ├── src/
│   │   └── dev/                    # Isolated dev setup
│   └── my-plugin-backend/          # Corresponding backend plugin
│       ├── package.json
│       └── src/
├── yarn.lock                       # Locked dependency tree
└── tsconfig.json                   # Root TypeScript config
```

### 1.2 Understanding Each Directory

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `packages/app` | Frontend SPA that end-users interact with | `App.tsx` registers routes and plugins |
| `packages/backend` | API server, proxies, catalog ingestion | `index.ts` wires backend plugins together |
| `plugins/` | Custom and forked plugins for your org | Each plugin is its own workspace package |
| Root | Workspace config, shared tooling, configs | `package.json` with `workspaces` field |

### 1.3 Yarn Workspaces in Detail

The root `package.json` declares which directories participate in the workspace:

```json
{
  "name": "root",
  "version": "1.0.0",
  "private": true,
  "workspaces": {
    "packages": [
      "packages/*",
      "plugins/*"
    ]
  }
}
```

This means every `package.json` inside `packages/` and `plugins/` is treated as a linked local dependency. If `packages/app` depends on `@internal/plugin-my-feature`, Yarn resolves it to the local `plugins/my-feature` directory instead of fetching from npm.

**Why workspaces matter for the exam**: You need to know that `yarn install` at the root installs dependencies for every package, and that workspace packages reference each other using the `workspace:^` protocol in their `package.json`.

---

## Part 2: TypeScript Fundamentals for Backstage

### 2.1 Types and Interfaces in Plugin Code

Backstage plugins are written in TypeScript. You do not need to be a TypeScript expert, but you must recognize the patterns that appear everywhere in the codebase.

**Interfaces define the shape of plugin APIs:**

```typescript
// A plugin's API surface is defined via an interface
export interface CatalogApi {
  getEntityByRef(ref: string): Promise<Entity | undefined>;
  getEntities(request?: GetEntitiesRequest): Promise<GetEntitiesResponse>;
}

// Utility references tie an interface to a plugin
export const catalogApiRef = createApiRef<CatalogApi>({
  id: 'plugin.catalog.service',
});
```

**Type aliases define data structures:**

```typescript
type EntityKind = 'Component' | 'API' | 'Resource' | 'System' | 'Domain';

type Entity = {
  apiVersion: string;
  kind: EntityKind;
  metadata: EntityMetadata;
  spec?: Record<string, unknown>;
};
```

### 2.2 Async/Await Patterns

Almost every backend operation in Backstage is asynchronous. Plugin routers, catalog processors, and scaffolder actions all use `async/await`:

```typescript
// Backend plugin router pattern
import { Router } from 'express';

export async function createRouter(
  options: RouterOptions,
): Promise<Router> {
  const { logger, config, database } = options;

  const router = Router();

  router.get('/health', async (_req, res) => {
    const db = await database.getClient();
    const result = await db.select().from('my_table').limit(1);
    res.json({ status: 'ok', rows: result.length });
  });

  return router;
}
```

**Key pattern to memorize**: backend plugin factories return `Promise<Router>` and accept an `options` object containing `logger`, `config`, `database`, and other environment services.

### 2.3 Generics in API Refs

The `createApiRef<T>` function is generic---it ties a type `T` to a reference string so the dependency injection system knows what type to return:

```typescript
// When you call useApi(catalogApiRef), TypeScript knows the return
// type is CatalogApi, not just "any".
const catalogApiRef = createApiRef<CatalogApi>({
  id: 'plugin.catalog.service',
});
```

---

## Part 3: Local Development

### 3.1 Scaffolding a New App

The official way to create a Backstage app:

```bash
# Create a new Backstage app
npx @backstage/create-app@latest

# You'll be prompted for an app name
# This generates the full monorepo structure
```

After scaffolding completes:

```bash
cd my-backstage-app
yarn install    # Install all workspace dependencies
yarn dev        # Start frontend AND backend in parallel
```

### 3.2 What `yarn dev` Actually Does

The `yarn dev` command runs both the frontend dev server (webpack, port 3000) and the backend dev server (Node.js, port 7007) concurrently. Under the hood, the root `package.json` defines:

```json
{
  "scripts": {
    "dev": "concurrently \"yarn start\" \"yarn start-backend\"",
    "start": "yarn workspace app start",
    "start-backend": "yarn workspace backend start"
  }
}
```

The frontend dev server provides **hot module replacement (HMR)**---change a React component and the browser updates without a full page reload. The backend server uses `nodemon` or `ts-node-dev` for automatic restarts on file changes.

### 3.3 Debugging

**Frontend debugging**: Open Chrome DevTools, go to Sources, and find your plugin code under `webpack://`. Set breakpoints directly.

**Backend debugging**: Add a debug script or use the `--inspect` flag:

```bash
# Start backend with Node.js inspector
yarn workspace backend start --inspect
```

Then attach VS Code or Chrome DevTools to `localhost:9229`. You can also add a `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "attach",
      "name": "Attach to Backend",
      "port": 9229,
      "restart": true,
      "skipFiles": ["<node_internals>/**"]
    }
  ]
}
```

---

## Part 4: Docker Builds

### 4.1 Multi-Stage Dockerfile

The generated `packages/backend/Dockerfile` uses a multi-stage build to keep the production image small:

```dockerfile
# Stage 1 - Build
FROM node:18-bookworm-slim AS build

WORKDIR /app

# Copy root workspace files
COPY package.json yarn.lock ./
COPY packages/backend/package.json packages/backend/
COPY plugins/ plugins/

# Install ALL dependencies (including devDependencies for build)
RUN yarn install --frozen-lockfile

# Copy source and build
COPY packages/backend/ packages/backend/
COPY app-config*.yaml ./
RUN yarn workspace backend build

# Stage 2 - Production
FROM node:18-bookworm-slim

WORKDIR /app

# Copy only the built output and production dependencies
COPY --from=build /app/packages/backend/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY app-config.yaml app-config.production.yaml ./

# Run as non-root
USER node

CMD ["node", "dist/index.cjs.js"]
```

### 4.2 Optimizing Image Size

| Technique | Impact | How |
|-----------|--------|-----|
| Multi-stage builds | High | Separate build and runtime stages |
| `--frozen-lockfile` | Medium | Ensures reproducible installs |
| `.dockerignore` | Medium | Exclude `node_modules/`, `.git/`, `*.md` |
| Slim base image | Medium | Use `node:18-bookworm-slim` not `node:18` |
| Non-root user | Security | `USER node` in final stage |

**Exam tip**: The Backstage CLI provides `backstage-cli package build` which bundles the backend into a single distributable. Know the difference between `yarn build` (workspace-level) and `backstage-cli package build` (package-level).

### 4.3 Building and Running

```bash
# Build the image
docker build -t backstage:latest -f packages/backend/Dockerfile .

# Run with config overrides via environment variables
docker run -p 7007:7007 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  backstage:latest
```

Note the build context is the **repo root** (`.`), not `packages/backend/`. This is because the Dockerfile needs access to the root `yarn.lock` and workspace packages.

---

## Part 5: NPM/Yarn Dependency Management

### 5.1 Lock Files

The `yarn.lock` file pins every dependency to an exact version. This guarantees that every developer and CI build gets identical packages.

**Critical rules:**

- Never delete `yarn.lock` to "fix" dependency issues (run `yarn install` instead).
- Always commit `yarn.lock` to version control.
- Use `yarn install --frozen-lockfile` in CI to fail if the lock file is out of date.

### 5.2 Workspace Protocol

When one package depends on another in the same monorepo, use the `workspace:` protocol:

```json
{
  "name": "@internal/plugin-my-feature",
  "dependencies": {
    "@backstage/core-plugin-api": "^1.9.0",
    "@internal/plugin-my-feature-common": "workspace:^"
  }
}
```

`workspace:^` resolves to the local package during development but is replaced with the actual version when publishing. For internal-only plugins that are never published, this keeps dependencies synced automatically.

### 5.3 Adding Dependencies

```bash
# Add a dependency to a specific workspace package
yarn workspace app add @backstage/plugin-catalog

# Add a dev dependency
yarn workspace backend add --dev @types/express

# Add a dependency to the root (shared tooling)
yarn add -W eslint prettier
```

The `-W` flag is required when adding to the root of a workspace. Without it, Yarn refuses the install to prevent accidental root-level dependencies.

---

## Part 6: Backstage CLI

### 6.1 Core Commands

The `@backstage/cli` package provides the `backstage-cli` binary. It is the Swiss Army knife for Backstage development:

| Command | Purpose |
|---------|---------|
| `backstage-cli package build` | Build a single package for production |
| `backstage-cli package lint` | Run ESLint on a package |
| `backstage-cli package test` | Run Jest tests for a package |
| `backstage-cli package start` | Start a package in dev mode |
| `backstage-cli versions:bump` | Bump all `@backstage/*` dependencies to latest |
| `backstage-cli versions:check` | Verify all `@backstage/*` versions are compatible |
| `backstage-cli new` | Scaffold a new plugin or package |

### 6.2 Creating a New Plugin

```bash
# From the repo root, scaffold a frontend plugin
yarn new --select plugin

# Scaffold a backend plugin
yarn new --select backend-plugin
```

This generates the full plugin skeleton inside `plugins/`, including `package.json`, `src/`, dev setup, and test files. The plugin is automatically added to the Yarn workspace.

### 6.3 Version Management

Backstage releases follow a monthly cadence. All `@backstage/*` packages in a release are designed to work together. Mixing versions across releases causes subtle breakage.

```bash
# Check for version mismatches
yarn backstage-cli versions:check

# Bump everything to the latest release
yarn backstage-cli versions:bump
```

**War story**: A team once spent three days debugging a catalog ingestion failure. The backend was on Backstage 1.18, but someone had manually upgraded `@backstage/plugin-catalog-backend` to 1.21 to get a new feature. The schema migrations were incompatible. The fix took five minutes once they ran `versions:check`---the mismatch was immediately obvious. The lesson: never upgrade individual `@backstage/*` packages. Always bump them together.

---

## Part 7: Project Configuration

### 7.1 Configuration Files

Backstage uses a layered configuration system:

```
app-config.yaml                # Base config (committed to git)
app-config.local.yaml          # Local developer overrides (gitignored)
app-config.production.yaml     # Production overrides (committed or injected)
```

Files are merged in order. Later files override earlier ones. The `local` file is for developer-specific settings (database credentials, GitHub tokens) and must never be committed.

### 7.2 Configuration Structure

```yaml
# app-config.yaml
app:
  title: My Backstage Portal
  baseUrl: http://localhost:3000

backend:
  baseUrl: http://localhost:7007
  listen:
    port: 7007
  database:
    client: better-sqlite3
    connection: ':memory:'

catalog:
  locations:
    - type: file
      target: ../../catalog-info.yaml

integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}  # Environment variable substitution
```

### 7.3 Environment Variable Substitution

The `${VAR}` syntax reads from the process environment at startup. This is the recommended way to inject secrets:

```yaml
# Never do this:
integrations:
  github:
    - host: github.com
      token: ghp_abc123hardcoded    # BAD: secret in git

# Always do this:
integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}        # GOOD: injected at runtime
```

### 7.4 Config Includes and Overrides

You can specify which config files to load using the `APP_CONFIG_` environment variable or CLI flags:

```bash
# Load base + production configs
yarn start-backend --config app-config.yaml --config app-config.production.yaml

# In Docker, use environment variables
APP_CONFIG_app_baseUrl=https://backstage.example.com
```

The `--config` flag can be repeated. Files are merged left to right, so the last file wins on conflicts.

---

## Common Mistakes

| Mistake | What Goes Wrong | Fix |
|---------|----------------|-----|
| Running `npm install` instead of `yarn install` | Generates `package-lock.json`, conflicts with `yarn.lock` | Always use `yarn`; delete `package-lock.json` if created |
| Editing `yarn.lock` by hand | Corrupts dependency resolution | Run `yarn install` to regenerate after `package.json` changes |
| Upgrading a single `@backstage/*` package | Version mismatch causes runtime errors | Use `backstage-cli versions:bump` to upgrade all together |
| Committing `app-config.local.yaml` | Leaks developer tokens and credentials | Ensure `.gitignore` includes `app-config.local.yaml` |
| Docker build context set to `packages/backend/` | Build fails because `yarn.lock` and workspace packages are not available | Set build context to repo root: `docker build -f packages/backend/Dockerfile .` |
| Forgetting `--frozen-lockfile` in CI | Non-deterministic builds; CI installs different versions than local | Always use `yarn install --frozen-lockfile` in CI pipelines |
| Hardcoding secrets in `app-config.yaml` | Secrets pushed to git | Use `${ENV_VAR}` substitution and inject at runtime |

---

## Quiz

Test your knowledge of the Backstage developer workflow.

**Q1: What is the purpose of the `packages/app` directory?**

<details>
<summary>Show Answer</summary>

It contains the **frontend React application** that end-users interact with. The `App.tsx` file registers plugin routes and configures the UI shell. It runs on port 3000 during development.
</details>

**Q2: Why does Backstage use Yarn workspaces instead of separate repositories?**

<details>
<summary>Show Answer</summary>

Yarn workspaces allow all packages (frontend, backend, plugins) to be managed, versioned, and tested together in a single repository. Local packages reference each other via the `workspace:^` protocol, avoiding version drift between tightly coupled code.
</details>

**Q3: What happens if you run `docker build` with the build context set to `packages/backend/` instead of the repo root?**

<details>
<summary>Show Answer</summary>

The build **fails** because the Dockerfile copies `yarn.lock` and workspace packages from the repo root. With the wrong context, those files are outside the build context and Docker cannot access them.
</details>

**Q4: How does Backstage handle secrets in configuration files?**

<details>
<summary>Show Answer</summary>

Backstage supports environment variable substitution using the `${VAR_NAME}` syntax in YAML config files. Values are resolved from the process environment at startup. Secrets should never be hardcoded in config files that are committed to git.
</details>

**Q5: What command upgrades all `@backstage/*` dependencies to the latest compatible release?**

<details>
<summary>Show Answer</summary>

`yarn backstage-cli versions:bump` upgrades all Backstage packages together. You should never upgrade individual `@backstage/*` packages because they are designed to work as a coordinated set within each monthly release.
</details>

**Q6: In what order are configuration files merged, and which file wins on conflicts?**

<details>
<summary>Show Answer</summary>

Files are merged in the order they are specified. `app-config.yaml` is loaded first (base), then `app-config.local.yaml` (local overrides), then any `--config` flags in order. The **last** file wins on conflicts---later values override earlier ones.
</details>

**Q7: What does `backstage-cli versions:check` do, and when should you run it?**

<details>
<summary>Show Answer</summary>

It scans all `package.json` files in the monorepo and reports any `@backstage/*` packages with mismatched versions. Run it after adding new Backstage dependencies, after merging branches, or when debugging unexpected runtime errors that might stem from version incompatibilities.
</details>

---

## Hands-On Exercise: Create and Explore a Backstage App

**Objective**: Scaffold a Backstage app, verify the monorepo structure, run it locally, and build a Docker image.

**Estimated time**: 30-40 minutes

### Prerequisites

- Node.js 18+ installed (`node -v`)
- Yarn installed (`npm install -g yarn`)
- Docker installed (`docker --version`)

### Steps

**Step 1: Scaffold the app**

```bash
npx @backstage/create-app@latest
# When prompted, name it: cba-lab
cd cba-lab
```

**Step 2: Verify the monorepo structure**

```bash
# List the top-level directories
ls -la

# Confirm workspace configuration
cat package.json | grep -A 5 '"workspaces"'

# Check that packages/app and packages/backend exist
ls packages/
```

**Success criteria**: You see `packages/app`, `packages/backend`, `app-config.yaml`, and `yarn.lock` in the root.

**Step 3: Examine the frontend entry point**

```bash
cat packages/app/src/App.tsx | head -40
```

Note how plugins are imported and registered as routes. This is where you would add new frontend plugins.

**Step 4: Start the development servers**

```bash
yarn dev
```

Open `http://localhost:3000` in your browser. You should see the Backstage UI with the default software catalog.

**Success criteria**: The browser shows the Backstage home page. The terminal shows both frontend (webpack) and backend (Node.js) logs.

**Step 5: Test hot reload**

With `yarn dev` still running, edit `packages/app/src/App.tsx` and change the app title or add a comment. Watch the browser---it should refresh automatically without a full reload.

**Step 6: Explore the configuration**

```bash
# View the base config
cat app-config.yaml

# Check which database is configured (default: SQLite in-memory)
grep -A 3 'database:' app-config.yaml
```

**Step 7: Create a local config override**

```bash
cat > app-config.local.yaml << 'EOF'
app:
  title: CBA Lab Portal
integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}
EOF
```

Restart `yarn dev` and verify the browser title changes to "CBA Lab Portal".

**Step 8: Build the Docker image**

```bash
# Build the backend for production
yarn workspace backend build

# Build the Docker image from the repo root
docker build -t cba-lab:latest -f packages/backend/Dockerfile .

# Verify image size
docker images cba-lab:latest
```

**Success criteria**: The image builds without errors. Image size should be under 1 GB (typically 500-700 MB depending on plugins).

**Step 9: Run the containerized app**

```bash
docker run -p 7007:7007 cba-lab:latest
```

Open `http://localhost:7007` and confirm the backend health endpoint responds.

### Cleanup

```bash
# Stop any running containers
docker rm -f $(docker ps -q --filter ancestor=cba-lab:latest) 2>/dev/null

# Remove the test app (optional)
cd .. && rm -rf cba-lab
```

---

## Summary

| Topic | Key Takeaway |
|-------|-------------|
| Monorepo structure | `packages/app` (frontend), `packages/backend` (backend), `plugins/` (extensions) |
| TypeScript patterns | Interfaces for APIs, `createApiRef<T>` for DI, `async/await` everywhere |
| Local development | `npx @backstage/create-app`, `yarn dev`, HMR for frontend |
| Docker builds | Multi-stage from repo root, slim base image, non-root user |
| Dependencies | Yarn workspaces, `workspace:^` protocol, `--frozen-lockfile` in CI |
| Backstage CLI | `versions:bump`, `versions:check`, `package build`, `new` |
| Configuration | Layered YAML files, `${ENV_VAR}` substitution, `--config` flag ordering |

---

## Next Module

[Module 2: Backstage Plugins and Extensions](../module-1.2-backstage-plugin-development/) - Build your first frontend and backend plugin, understand the plugin API system, and learn how Backstage's dependency injection works.
