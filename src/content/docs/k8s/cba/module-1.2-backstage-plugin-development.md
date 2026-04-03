---
title: "Module 1.2: Backstage Plugin Development \u2014 Customizing Backstage"
slug: k8s/cba/module-1.2-backstage-plugin-development
sidebar:
  order: 3
---
> **Complexity**: `[COMPLEX]` — Heaviest exam domain (32%)
>
> **Time to Complete**: 90-120 minutes
>
> **Prerequisites**: Module 1 (Backstage Development Workflow), familiarity with TypeScript, React basics, npm/yarn
>
> **CBA Domain**: Domain 4 — Customizing Backstage (32% of exam)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Build** a Backstage frontend plugin with React components, Material UI theming, and route registration in the app shell
2. **Build** a backend plugin with Express routes, database migrations, and service-to-service authentication
3. **Create** Software Templates that scaffold new services with cookiecutter/Nunjucks, including CI/CD pipelines and catalog registration
4. **Analyze** plugin extension points, composability APIs, and auth provider integration by reading Backstage TypeScript code

---

## Why This Module Matters

This is the single most important module for the CBA exam. **Domain 4 is worth 32%** — nearly one in three questions will test your understanding of plugin development, Material UI, Software Templates, theming, and auth providers.

Backstage without plugins is an empty shell. The entire value proposition — the software catalog, TechDocs, CI/CD visibility, scaffolding — all of it is delivered through plugins. When Spotify built Backstage, they designed it as a plugin platform first and a portal second. Understanding how plugins work is understanding how Backstage works.

This module is code-heavy by design. The exam shows you TypeScript and React snippets and asks what they do. You will not write code during the exam, but you absolutely need to *read* code fluently.

> **The Restaurant Analogy**
>
> Backstage is a restaurant kitchen. The core framework is the building — walls, plumbing, electricity. Frontend plugins are the dishes on the menu. Backend plugins are the kitchen stations (grill, prep, dessert). Software Templates are the recipes that let line cooks produce consistent meals. Auth providers are the bouncers at the door. You do not run a restaurant by staring at the building — you run it by cooking.

---

## War Story: The Plugin That Broke Production

A platform team at a mid-size fintech company built a custom frontend plugin to display deployment status. It worked perfectly in development. They shipped it to production on a Friday afternoon (mistake number one). The plugin made unauthenticated API calls to their backend plugin, which in turn queried their deployment database with no connection pooling. Monday morning, 400 engineers opened the Backstage portal simultaneously. The backend plugin exhausted the database connection pool within seconds, which cascaded into the Backstage backend process crashing entirely. Every plugin — catalog, TechDocs, scaffolder — went down because one custom plugin had no error boundaries and no resource limits.

The fix took three lines of code: a connection pool limit, a circuit breaker in the backend plugin, and a React error boundary wrapping the frontend component. Three lines. But because nobody understood the plugin architecture deeply enough to diagnose the issue, the portal was down for six hours.

The lesson: plugin development is not just about making things work. It is about understanding how your plugin fits into the larger Backstage runtime. That is exactly what the CBA tests.

---

## Did You Know?

- **Backstage has over 200 open-source plugins** in its marketplace, but most large adopters write 5-15 custom plugins tailored to their internal tools. The real power of Backstage is not the marketplace — it is the plugin SDK.
- **Frontend and backend plugins run in completely different processes.** The frontend is a React single-page app served as static files. The backend is a Node.js/Express server. They communicate only over HTTP. This is why you cannot import backend code in a frontend plugin.
- **Material UI (MUI) version matters.** Backstage uses MUI v5 (the `@mui/material` package). Older tutorials referencing `@material-ui/core` are MUI v4 and will not work without migration. The exam tests MUI v5 patterns.
- **Software Template actions run server-side, not client-side.** When a user fills out a template form and clicks "Create," the form data is sent to the backend scaffolder, which executes each action step sequentially. This means custom actions have access to the filesystem, network, and secrets — but not the browser.

---

## Part 1: Frontend vs Backend Plugin Architecture

Before writing any code, you need to understand where plugins run. This is one of the most commonly tested concepts on the CBA.

```
BACKSTAGE RUNTIME ARCHITECTURE
══════════════════════════════════════════════════════════════════════

  Browser (User's machine)               Server (Node.js process)
 ┌────────────────────────┐             ┌─────────────────────────┐
 │   React SPA (app)      │             │   Express Backend       │
 │                        │   HTTP/     │                         │
 │  ┌──────────────────┐  │   REST      │  ┌───────────────────┐  │
 │  │ Frontend Plugin A │──│────────────│──│ Backend Plugin A   │  │
 │  │ (React component) │  │            │  │ (Express router)   │  │
 │  └──────────────────┘  │            │  └───────────────────┘  │
 │                        │            │                         │
 │  ┌──────────────────┐  │            │  ┌───────────────────┐  │
 │  │ Frontend Plugin B │──│────────────│──│ Backend Plugin B   │  │
 │  │ (React component) │  │            │  │ (Express router)   │  │
 │  └──────────────────┘  │            │  └───────────────────┘  │
 │                        │            │                         │
 │  ┌──────────────────┐  │            │  ┌───────────────────┐  │
 │  │  Backstage Core   │  │            │  │  Catalog / Auth   │  │
 │  │  (routing, theme) │  │            │  │  Scaffolder / ... │  │
 │  └──────────────────┘  │            │  └───────────────────┘  │
 └────────────────────────┘            └──────────┬──────────────┘
                                                   │
                                        ┌──────────▼──────────┐
                                        │   PostgreSQL / SQLite│
                                        └─────────────────────┘

 packages/app/                           packages/backend/
 (built as static JS/CSS)               (runs as Node.js process)
```

### Key Differences

| Aspect | Frontend Plugin | Backend Plugin |
|--------|----------------|----------------|
| **Language** | TypeScript + React + JSX | TypeScript + Express |
| **Runs in** | Browser | Node.js server |
| **Access to** | DOM, browser APIs, user session | Filesystem, database, secrets, network |
| **Package location** | `plugins/my-plugin/` | `plugins/my-plugin-backend/` |
| **Entry point** | `createPlugin()` | `createBackendPlugin()` |
| **Communicates via** | Backstage API client (`fetchApiRef`) | Express routes mounted at `/api/my-plugin` |
| **Testing** | `@testing-library/react` | Supertest + backend test utils |

---

## Part 2: Frontend Plugin Development

### 2.1 Creating a Frontend Plugin

Backstage provides a CLI command to scaffold a new plugin:

```bash
# From the Backstage root directory
yarn new --select plugin

# You'll be prompted for a plugin ID, e.g., "my-dashboard"
# This creates: plugins/my-dashboard/
```

The generated plugin structure:

```
plugins/my-dashboard/
├── src/
│   ├── index.ts              # Public API exports
│   ├── plugin.ts             # Plugin definition (createPlugin)
│   ├── routes.ts             # Route references
│   ├── components/
│   │   ├── MyDashboardPage/
│   │   │   ├── MyDashboardPage.tsx
│   │   │   └── index.ts
│   │   └── ExampleFetchComponent/
│   ├── api/                  # API client definitions
│   └── setupTests.ts
├── package.json
├── README.md
└── dev/                      # Standalone dev setup
    └── index.tsx
```

### 2.2 The Plugin Definition — `createPlugin`

Every frontend plugin starts with `createPlugin`. This is the plugin's identity — it registers the plugin with Backstage and declares its routes, APIs, and extensions.

```typescript
// plugins/my-dashboard/src/plugin.ts
import {
  createPlugin,
  createRoutableExtension,
} from '@backstage/core-plugin-api';
import { rootRouteRef } from './routes';

export const myDashboardPlugin = createPlugin({
  id: 'my-dashboard',
  routes: {
    root: rootRouteRef,
  },
});

export const MyDashboardPage = myDashboardPlugin.provide(
  createRoutableExtension({
    name: 'MyDashboardPage',
    component: () =>
      import('./components/MyDashboardPage').then(m => m.MyDashboardPage),
    mountPoint: rootRouteRef,
  }),
);
```

What this code does, line by line:

- `createPlugin({ id: 'my-dashboard' })` — Registers a plugin with a unique ID. Backstage uses this ID for routing, configuration, and analytics.
- `routes: { root: rootRouteRef }` — Associates named routes with the plugin. `rootRouteRef` is a reference created elsewhere (see below).
- `createRoutableExtension()` — Creates a React component that Backstage can mount at a URL path. The `component` field uses dynamic `import()` for code splitting — the plugin code is only loaded when a user navigates to its page.
- `mountPoint: rootRouteRef` — Ties this component to the route reference.

### 2.3 Route References

```typescript
// plugins/my-dashboard/src/routes.ts
import { createRouteRef } from '@backstage/core-plugin-api';

export const rootRouteRef = createRouteRef({
  id: 'my-dashboard',
});
```

Route references are abstract — they do not contain actual URL paths. The path is assigned when the plugin is mounted in the app (see Section 2.5).

### 2.4 Writing a Frontend Plugin Page

Here is a complete frontend plugin page that fetches data from a backend API and displays it using Backstage's built-in components:

```tsx
// plugins/my-dashboard/src/components/MyDashboardPage/MyDashboardPage.tsx
import React from 'react';
import { useApi, fetchApiRef } from '@backstage/core-plugin-api';
import {
  Header,
  Page,
  Content,
  ContentHeader,
  SupportButton,
  Table,
  TableColumn,
  InfoCard,
  Progress,
  ResponseErrorPanel,
} from '@backstage/core-components';
import { Grid } from '@mui/material';
import useAsync from 'react-use/lib/useAsync';

// Define the shape of data we expect from our backend
interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  lastChecked: string;
  responseTimeMs: number;
}

// Table column definitions — Backstage's Table component uses this pattern
const columns: TableColumn<ServiceHealth>[] = [
  { title: 'Service', field: 'name' },
  {
    title: 'Status',
    field: 'status',
    render: (row: ServiceHealth) => {
      const colors: Record<string, string> = {
        healthy: '#4caf50',
        degraded: '#ff9800',
        down: '#f44336',
      };
      return (
        <span style={{ color: colors[row.status], fontWeight: 'bold' }}>
          {row.status.toUpperCase()}
        </span>
      );
    },
  },
  { title: 'Response Time (ms)', field: 'responseTimeMs', type: 'numeric' },
  { title: 'Last Checked', field: 'lastChecked' },
];

export const MyDashboardPage = () => {
  // useApi hook retrieves a Backstage API implementation by its ref
  const fetchApi = useApi(fetchApiRef);

  // useAsync handles loading/error states for async operations
  const {
    value: services,
    loading,
    error,
  } = useAsync(async (): Promise<ServiceHealth[]> => {
    const response = await fetchApi.fetch(
      '/api/my-dashboard/services/health',
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch: ${response.statusText}`);
    }
    return response.json();
  }, []);

  if (loading) return <Progress />;
  if (error) return <ResponseErrorPanel error={error} />;

  return (
    <Page themeId="tool">
      <Header title="Service Health Dashboard" subtitle="Real-time status" />
      <Content>
        <ContentHeader title="Overview">
          <SupportButton>
            This dashboard shows the health of all registered services.
          </SupportButton>
        </ContentHeader>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <InfoCard title="Service Count">
              {services?.length ?? 0} services monitored
            </InfoCard>
          </Grid>
          <Grid item xs={12}>
            <Table
              title="Service Health"
              options={{ search: true, paging: true, pageSize: 10 }}
              columns={columns}
              data={services ?? []}
            />
          </Grid>
        </Grid>
      </Content>
    </Page>
  );
};
```

### Key Backstage Components Used Above

| Component | Package | Purpose |
|-----------|---------|---------|
| `Page` | `@backstage/core-components` | Top-level layout with sidebar support |
| `Header` | `@backstage/core-components` | Page header with title and subtitle |
| `Content` | `@backstage/core-components` | Main content area with padding |
| `InfoCard` | `@backstage/core-components` | A Material Design card with title |
| `Table` | `@backstage/core-components` | Data table with search, sort, pagination |
| `Progress` | `@backstage/core-components` | Loading spinner |
| `ResponseErrorPanel` | `@backstage/core-components` | Styled error display |
| `Grid` | `@mui/material` | MUI responsive grid layout |

### 2.5 Mounting the Plugin in the App

After building the plugin, you wire it into the app:

```tsx
// packages/app/src/App.tsx
import { MyDashboardPage } from '@internal/plugin-my-dashboard';

// Inside the <FlatRoutes> component:
<Route path="/my-dashboard" element={<MyDashboardPage />} />
```

And add a sidebar entry:

```tsx
// packages/app/src/components/Root/Root.tsx
import DashboardIcon from '@mui/icons-material/Dashboard';

// Inside the <Sidebar> component:
<SidebarItem icon={DashboardIcon} to="my-dashboard" text="Health" />
```

---

## Part 3: Backend Plugin Development

### 3.1 Creating a Backend Plugin

```bash
yarn new --select backend-plugin

# Enter plugin ID: "my-dashboard"
# This creates: plugins/my-dashboard-backend/
```

### 3.2 Backend Plugin Structure (New Backend System)

Backstage has migrated to a "new backend system" (introduced in Backstage 1.x). The exam tests the new pattern. Here is the full structure of a backend plugin:

```typescript
// plugins/my-dashboard-backend/src/plugin.ts
import {
  coreServices,
  createBackendPlugin,
} from '@backstage/backend-plugin-api';
import { createRouter } from './router';

export const myDashboardPlugin = createBackendPlugin({
  pluginId: 'my-dashboard',
  register(env) {
    env.registerInit({
      deps: {
        logger: coreServices.logger,
        http: coreServices.httpRouter,
        database: coreServices.database,
        config: coreServices.rootConfig,
      },
      async init({ logger, http, database, config }) {
        logger.info('Initializing my-dashboard backend plugin');

        const router = await createRouter({
          logger,
          database,
          config,
        });

        // Mount the Express router at /api/my-dashboard
        http.use(router);
      },
    });
  },
});
```

Key concepts:

- **`createBackendPlugin`** — Declares a backend plugin with a unique `pluginId`.
- **`coreServices`** — Dependency injection. Instead of constructing dependencies yourself, you declare what you need and Backstage provides them.
- **`coreServices.httpRouter`** — An Express router scoped to `/api/<pluginId>`.
- **`coreServices.database`** — A Knex.js database client. Backstage manages the connection.
- **`coreServices.logger`** — A Winston logger scoped to the plugin.

### 3.3 Writing an Express Router

```typescript
// plugins/my-dashboard-backend/src/router.ts
import { Router } from 'express';
import { Logger } from 'winston';
import { DatabaseService } from '@backstage/backend-plugin-api';
import { Config } from '@backstage/config';

interface RouterOptions {
  logger: Logger;
  database: DatabaseService;
  config: Config;
}

interface ServiceHealthRecord {
  name: string;
  status: string;
  last_checked: string;
  response_time_ms: number;
}

export async function createRouter(
  options: RouterOptions,
): Promise<Router> {
  const { logger, database } = options;
  const router = Router();

  // Get a Knex database client from Backstage's database service
  const dbClient = await database.getClient();

  // Run migrations on startup (create tables if they don't exist)
  if (!await dbClient.schema.hasTable('service_health')) {
    await dbClient.schema.createTable('service_health', table => {
      table.string('name').primary();
      table.string('status').notNullable();
      table.timestamp('last_checked').defaultTo(dbClient.fn.now());
      table.integer('response_time_ms');
    });
    logger.info('Created service_health table');
  }

  // GET /api/my-dashboard/services/health
  router.get('/services/health', async (_req, res) => {
    try {
      const services = await dbClient<ServiceHealthRecord>(
        'service_health',
      ).select('*');

      res.json(
        services.map(s => ({
          name: s.name,
          status: s.status,
          lastChecked: s.last_checked,
          responseTimeMs: s.response_time_ms,
        })),
      );
    } catch (err) {
      logger.error('Failed to fetch service health', err);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  // POST /api/my-dashboard/services/health
  router.post('/services/health', async (req, res) => {
    const { name, status, responseTimeMs } = req.body;

    if (!name || !status) {
      res.status(400).json({ error: 'name and status are required' });
      return;
    }

    try {
      await dbClient('service_health')
        .insert({
          name,
          status,
          response_time_ms: responseTimeMs ?? 0,
          last_checked: new Date().toISOString(),
        })
        .onConflict('name')
        .merge(); // Upsert: update if exists

      res.status(201).json({ message: 'Service health recorded' });
    } catch (err) {
      logger.error('Failed to record service health', err);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  return router;
}
```

### 3.4 Registering the Backend Plugin

```typescript
// packages/backend/src/index.ts
import { myDashboardPlugin } from '@internal/plugin-my-dashboard-backend';

// In the backend builder:
backend.add(myDashboardPlugin);
```

That single line is all it takes. The new backend system handles dependency injection, router mounting, and lifecycle management automatically.

---

## Part 4: Material UI (MUI) and Theming

### 4.1 Backstage's Relationship with MUI

Backstage uses Material UI v5 (`@mui/material`) as its component library. Every visual element — buttons, cards, tables, dialogs — comes from MUI. The exam tests your ability to recognize MUI components and understand Backstage's theming system.

Commonly tested MUI components in a Backstage context:

| MUI Component | Backstage Usage |
|---------------|-----------------|
| `Grid` | Page layouts, responsive design |
| `Card` / `CardContent` | Content grouping (wrapped by `InfoCard`) |
| `Typography` | Text with semantic meaning (h1-h6, body, caption) |
| `Button` | Actions, form submissions |
| `TextField` | Form inputs in template forms |
| `Table` / `TableBody` / `TableRow` | Data display (Backstage wraps this in its own `Table`) |
| `Tabs` / `Tab` | Entity page tab navigation |
| `Chip` | Status badges, tags |
| `Dialog` | Modal dialogs for confirmations |

### 4.2 Custom Themes

Backstage supports custom themes via `createUnifiedTheme`. This lets organizations brand the portal with their own colors, fonts, and component styles.

```typescript
// packages/app/src/theme.ts
import { createUnifiedTheme, palettes } from '@backstage/theme';

export const myCustomTheme = createUnifiedTheme({
  palette: {
    ...palettes.light,
    primary: {
      main: '#1565c0',       // Your brand blue
    },
    secondary: {
      main: '#f57c00',       // Your brand orange
    },
    navigation: {
      background: '#171717', // Dark sidebar
      indicator: '#1565c0',  // Active item highlight
      color: '#ffffff',      // Sidebar text
      selectedColor: '#ffffff',
    },
  },
  defaultPageTheme: 'home',
  fontFamily: '"Inter", "Helvetica", "Arial", sans-serif',
  components: {
    // Override specific MUI component styles globally
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // No ALL CAPS buttons
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});
```

Register the theme in the app:

```tsx
// packages/app/src/App.tsx
import { myCustomTheme } from './theme';
import { UnifiedThemeProvider } from '@backstage/theme';

// In the app root:
<UnifiedThemeProvider theme={myCustomTheme}>
  <AppRouter>
    {/* ... routes ... */}
  </AppRouter>
</UnifiedThemeProvider>
```

### 4.3 Using the `sx` Prop

MUI v5 uses the `sx` prop for one-off styling. You will see this pattern on the exam:

```tsx
import { Box, Typography, Chip } from '@mui/material';

export const StatusBanner = ({ status }: { status: string }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      gap: 2,
      p: 2,                         // padding: theme.spacing(2)
      bgcolor: 'background.paper',  // uses theme palette
      borderRadius: 1,
    }}
  >
    <Typography variant="h6">Current Status</Typography>
    <Chip
      label={status}
      color={status === 'healthy' ? 'success' : 'error'}
      sx={{ fontWeight: 'bold' }}
    />
  </Box>
);
```

---

## Part 5: Installing Existing Plugins

Not every plugin needs to be built from scratch. The Backstage plugin marketplace at [backstage.io/plugins](https://backstage.io/plugins) has 200+ community plugins.

### 5.1 Installation Pattern

Most plugins follow this pattern:

```bash
# 1. Install the frontend package
yarn --cwd packages/app add @backstage/plugin-tech-radar

# 2. Install the backend package (if the plugin has one)
yarn --cwd packages/backend add @backstage/plugin-tech-radar-backend
```

```tsx
// 3. Wire frontend into packages/app/src/App.tsx
import { TechRadarPage } from '@backstage/plugin-tech-radar';

<Route path="/tech-radar" element={<TechRadarPage />} />
```

```typescript
// 4. Wire backend into packages/backend/src/index.ts
backend.add(import('@backstage/plugin-tech-radar-backend'));
```

```yaml
# 5. Configure in app-config.yaml (if needed)
techRadar:
  url: https://your-org.com/tech-radar-data.json
```

### 5.2 Overriding Plugin Components

You can replace the default implementation of any plugin component. This is how you customize third-party plugins without forking them:

```tsx
// packages/app/src/App.tsx
import { createApp } from '@backstage/app-defaults';
import { catalogPlugin } from '@backstage/plugin-catalog';

const app = createApp({
  // ...
  bindRoutes({ bind }) {
    bind(catalogPlugin.externalRoutes, {
      createComponent: scaffolderPlugin.routes.root,
    });
  },
});
```

---

## Part 6: Software Templates

Software Templates are one of Backstage's most powerful features. They let platform teams define "golden paths" — standardized workflows for creating new services, libraries, or infrastructure.

### 6.1 Template Structure

A Software Template is a YAML file registered in the catalog with `kind: Template`:

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: create-nodejs-service
  title: Create a Node.js Microservice
  description: Creates a new Node.js service with CI/CD, monitoring, and docs
  tags:
    - nodejs
    - recommended
spec:
  owner: platform-team
  type: service

  # Step 1: Collect user input
  parameters:
    - title: Service Details
      required:
        - name
        - owner
      properties:
        name:
          title: Service Name
          type: string
          description: Unique name for the service
          pattern: '^[a-z0-9-]+$'
          ui:autofocus: true
        owner:
          title: Owner
          type: string
          description: Team that owns this service
          ui:field: OwnerPicker
          ui:options:
            catalogFilter:
              kind: Group
        description:
          title: Description
          type: string

    - title: Infrastructure
      properties:
        database:
          title: Database
          type: string
          enum: ['none', 'postgresql', 'mongodb']
          default: 'none'
        port:
          title: Port
          type: number
          default: 3000

  # Step 2: Execute actions
  steps:
    - id: fetch-template
      name: Fetch Skeleton
      action: fetch:template
      input:
        url: ./skeleton     # Directory containing template files
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          description: ${{ parameters.description }}
          database: ${{ parameters.database }}
          port: ${{ parameters.port }}

    - id: publish
      name: Publish to GitHub
      action: publish:github
      input:
        allowedHosts: ['github.com']
        repoUrl: github.com?owner=my-org&repo=${{ parameters.name }}
        description: ${{ parameters.description }}
        defaultBranch: main
        repoVisibility: internal

    - id: register
      name: Register in Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['publish'].output.repoContentsUrl }}
        catalogInfoPath: '/catalog-info.yaml'

  # What to show the user when done
  output:
    links:
      - title: Repository
        url: ${{ steps['publish'].output.remoteUrl }}
      - title: Open in Backstage
        icon: catalog
        entityRef: ${{ steps['register'].output.entityRef }}
```

### 6.2 Built-in Template Actions

| Action | Purpose |
|--------|---------|
| `fetch:template` | Copy and render template files (Nunjucks syntax) |
| `fetch:plain` | Copy files without templating |
| `publish:github` | Create a GitHub repository |
| `publish:gitlab` | Create a GitLab project |
| `publish:bitbucket` | Create a Bitbucket repository |
| `catalog:register` | Register the new entity in the Backstage catalog |
| `catalog:write` | Write a `catalog-info.yaml` file |
| `debug:log` | Log a message (useful for debugging templates) |

### 6.3 Writing a Custom Template Action

When built-in actions are not enough, you write custom actions. This is a heavily tested topic on the CBA.

```typescript
// plugins/scaffolder-backend-custom/src/actions/createJiraTicket.ts
import { createTemplateAction } from '@backstage/plugin-scaffolder-node';
import { Config } from '@backstage/config';

export function createJiraTicketAction(options: { config: Config }) {
  const { config } = options;

  return createTemplateAction<{
    projectKey: string;
    summary: string;
    description: string;
    issueType: string;
  }>({
    id: 'jira:create-ticket',
    description: 'Creates a Jira ticket for tracking the new service',
    schema: {
      input: {
        type: 'object',
        required: ['projectKey', 'summary'],
        properties: {
          projectKey: {
            type: 'string',
            title: 'Jira Project Key',
            description: 'e.g., PLATFORM',
          },
          summary: {
            type: 'string',
            title: 'Ticket Summary',
          },
          description: {
            type: 'string',
            title: 'Ticket Description',
          },
          issueType: {
            type: 'string',
            title: 'Issue Type',
            enum: ['Task', 'Story', 'Bug'],
            default: 'Task',
          },
        },
      },
      output: {
        type: 'object',
        properties: {
          ticketUrl: {
            type: 'string',
            title: 'URL of the created Jira ticket',
          },
          ticketKey: {
            type: 'string',
            title: 'Jira ticket key (e.g., PLATFORM-123)',
          },
        },
      },
    },
    async handler(ctx) {
      const { projectKey, summary, description, issueType } = ctx.input;
      const jiraUrl = config.getString('jira.url');
      const jiraToken = config.getString('jira.apiToken');

      ctx.logger.info(
        `Creating Jira ticket in project ${projectKey}: ${summary}`,
      );

      const response = await fetch(`${jiraUrl}/rest/api/3/issue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Basic ${jiraToken}`,
        },
        body: JSON.stringify({
          fields: {
            project: { key: projectKey },
            summary,
            description: {
              type: 'doc',
              version: 1,
              content: [
                {
                  type: 'paragraph',
                  content: [{ type: 'text', text: description || summary }],
                },
              ],
            },
            issuetype: { name: issueType || 'Task' },
          },
        }),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Jira API error (${response.status}): ${errorBody}`);
      }

      const data = await response.json();

      ctx.logger.info(`Created Jira ticket: ${data.key}`);

      // Output values can be referenced by later template steps
      ctx.output('ticketKey', data.key);
      ctx.output('ticketUrl', `${jiraUrl}/browse/${data.key}`);
    },
  });
}
```

Register the custom action:

```typescript
// plugins/scaffolder-backend-custom/src/plugin.ts
import { scaffolderActionsExtensionPoint } from '@backstage/plugin-scaffolder-node/alpha';
import { createBackendModule } from '@backstage/backend-plugin-api';
import { createJiraTicketAction } from './actions/createJiraTicket';

export const scaffolderModuleJiraAction = createBackendModule({
  pluginId: 'scaffolder',
  moduleId: 'jira-action',
  register(env) {
    env.registerInit({
      deps: {
        scaffolder: scaffolderActionsExtensionPoint,
        config: coreServices.rootConfig,
      },
      async init({ scaffolder, config }) {
        scaffolder.addActions(createJiraTicketAction({ config }));
      },
    });
  },
});
```

Use it in a template:

```yaml
steps:
  # ... other steps ...
  - id: create-jira-ticket
    name: Create Tracking Ticket
    action: jira:create-ticket
    input:
      projectKey: PLATFORM
      summary: 'New service: ${{ parameters.name }}'
      description: 'Service created via Backstage template by ${{ user.entity.metadata.name }}'
      issueType: Task
```

---

## Part 7: Auth Providers

Backstage supports multiple authentication providers out of the box. The exam tests configuration patterns for the most common ones.

### 7.1 GitHub App Auth

```yaml
# app-config.yaml
auth:
  environment: production
  providers:
    github:
      production:
        clientId: ${GITHUB_CLIENT_ID}
        clientSecret: ${GITHUB_CLIENT_SECRET}
        signIn:
          resolvers:
            - resolver: usernameMatchingUserEntityName
```

### 7.2 Okta / OIDC

```yaml
# app-config.yaml
auth:
  providers:
    okta:
      production:
        clientId: ${OKTA_CLIENT_ID}
        clientSecret: ${OKTA_CLIENT_SECRET}
        audience: ${OKTA_AUDIENCE}
        authServerId: ${OKTA_AUTH_SERVER_ID}  # 'default' for org auth server
        signIn:
          resolvers:
            - resolver: emailMatchingUserEntityProfileEmail
```

### 7.3 Sign-in Resolvers

Sign-in resolvers map an external identity (GitHub user, Okta user) to a Backstage user entity in the catalog. The exam commonly tests these resolvers:

| Resolver | What it does |
|----------|-------------|
| `usernameMatchingUserEntityName` | Matches the provider's username to the `metadata.name` of a User entity |
| `emailMatchingUserEntityProfileEmail` | Matches the provider's email to `spec.profile.email` of a User entity |
| `emailLocalPartMatchingUserEntityName` | Matches the part before `@` in the email to `metadata.name` |

Custom sign-in resolver:

```typescript
// packages/backend/src/auth.ts
import { createBackendModule } from '@backstage/backend-plugin-api';
import {
  authProvidersExtensionPoint,
  createOAuthProviderFactory,
} from '@backstage/plugin-auth-node';
import { githubAuthenticator } from '@backstage/plugin-auth-backend-module-github-provider';

export const authModuleGithubCustom = createBackendModule({
  pluginId: 'auth',
  moduleId: 'github-custom-resolver',
  register(reg) {
    reg.registerInit({
      deps: {
        providers: authProvidersExtensionPoint,
      },
      async init({ providers }) {
        providers.registerProvider({
          providerId: 'github',
          factory: createOAuthProviderFactory({
            authenticator: githubAuthenticator,
            async signInResolver(info, ctx) {
              // info.result contains the GitHub profile
              const { fullProfile } = info.result;
              const userId = fullProfile.username;

              if (!userId) {
                throw new Error('GitHub username is required');
              }

              // Issue a Backstage token for this user
              return ctx.signInWithCatalogUser({
                entityRef: { name: userId },
              });
            },
          }),
        });
      },
    });
  },
});
```

---

## Part 8: Testing Plugins

### 8.1 Frontend Plugin Tests

Backstage provides test utilities that wrap `@testing-library/react`:

```tsx
// plugins/my-dashboard/src/components/MyDashboardPage/MyDashboardPage.test.tsx
import React from 'react';
import { screen } from '@testing-library/react';
import { renderInTestApp } from '@backstage/test-utils';
import { MyDashboardPage } from './MyDashboardPage';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock the backend API using MSW (Mock Service Worker)
const server = setupServer(
  rest.get('/api/my-dashboard/services/health', (_req, res, ctx) => {
    return res(
      ctx.json([
        {
          name: 'auth-service',
          status: 'healthy',
          lastChecked: '2025-01-15T10:30:00Z',
          responseTimeMs: 42,
        },
        {
          name: 'payment-service',
          status: 'degraded',
          lastChecked: '2025-01-15T10:30:00Z',
          responseTimeMs: 1500,
        },
      ]),
    );
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MyDashboardPage', () => {
  it('should render the service health table', async () => {
    await renderInTestApp(<MyDashboardPage />);

    // Wait for async data to load
    expect(
      await screen.findByText('Service Health Dashboard'),
    ).toBeInTheDocument();
    expect(await screen.findByText('auth-service')).toBeInTheDocument();
    expect(await screen.findByText('DEGRADED')).toBeInTheDocument();
  });

  it('should show an error panel when the API fails', async () => {
    server.use(
      rest.get('/api/my-dashboard/services/health', (_req, res, ctx) => {
        return res(ctx.status(500));
      }),
    );

    await renderInTestApp(<MyDashboardPage />);

    expect(await screen.findByText(/failed to fetch/i)).toBeInTheDocument();
  });
});
```

Key testing patterns:

- **`renderInTestApp`** — Wraps your component in the full Backstage app context (theme, API providers, routing). Always use this instead of plain `render` from `@testing-library/react`.
- **MSW (Mock Service Worker)** — The standard way to mock backend API calls in Backstage frontend tests.
- **`screen.findByText`** — Use `findBy*` (not `getBy*`) for async content that loads after a fetch.

### 8.2 Backend Plugin Tests

```typescript
// plugins/my-dashboard-backend/src/router.test.ts
import { createRouter } from './router';
import express from 'express';
import request from 'supertest';
import { getVoidLogger } from '@backstage/backend-common';
import Knex from 'knex';

describe('createRouter', () => {
  let app: express.Express;

  beforeAll(async () => {
    // Create an in-memory SQLite database for testing
    const knex = Knex({
      client: 'better-sqlite3',
      connection: ':memory:',
      useNullAsDefault: true,
    });

    const router = await createRouter({
      logger: getVoidLogger(),
      database: {
        getClient: async () => knex,
      } as any,
      config: {} as any,
    });

    app = express();
    app.use(express.json());
    app.use(router);
  });

  it('GET /services/health returns empty array initially', async () => {
    const response = await request(app).get('/services/health');
    expect(response.status).toBe(200);
    expect(response.body).toEqual([]);
  });

  it('POST /services/health creates a record', async () => {
    const response = await request(app)
      .post('/services/health')
      .send({ name: 'test-svc', status: 'healthy', responseTimeMs: 50 });

    expect(response.status).toBe(201);
  });

  it('GET /services/health returns the created record', async () => {
    const response = await request(app).get('/services/health');
    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(1);
    expect(response.body[0].name).toBe('test-svc');
  });

  it('POST /services/health rejects missing fields', async () => {
    const response = await request(app)
      .post('/services/health')
      .send({ status: 'healthy' }); // Missing 'name'

    expect(response.status).toBe(400);
  });
});
```

---

## Common Mistakes

| Mistake | Why It Happens | Fix |
|---------|---------------|-----|
| Importing backend code in a frontend plugin | Looks like regular TypeScript imports | Frontend runs in the browser. It cannot access Node.js APIs, the filesystem, or the database. Use `fetchApiRef` to call your backend plugin over HTTP. |
| Using MUI v4 syntax (`makeStyles`, `@material-ui/core`) | Following outdated tutorials | Backstage uses MUI v5. Use `sx` prop, `styled()`, or `@mui/material` imports. |
| Hardcoding API URLs (`fetch('http://localhost:7007/...')`) | Works in local dev | Use `fetchApiRef` from `@backstage/core-plugin-api`. Backstage handles base URL resolution, auth headers, and proxy routing. |
| Forgetting to register the backend plugin | Plugin code exists but is never loaded | Add `backend.add(myPlugin)` in `packages/backend/src/index.ts`. No registration = no routes mounted. |
| Template actions with no error handling | Happy-path development | If a template action throws, the entire scaffolder run fails with a cryptic error. Always wrap external API calls in try/catch and provide meaningful error messages. |
| Using `getBy*` in tests for async content | Unfamiliar with testing-library patterns | Data that loads from an API is async. Use `findBy*` (which retries) instead of `getBy*` (which asserts immediately). |
| Creating custom themes with `createTheme` | Mixing MUI's `createTheme` with Backstage | Use `createUnifiedTheme` from `@backstage/theme`, not `createTheme` from `@mui/material`. Backstage's version adds page themes, navigation palette, and plugin integration. |
| Not setting `pluginId` on backend plugins | Copy-paste errors | The `pluginId` determines the API route prefix (`/api/<pluginId>`). If two plugins share an ID, routes collide. |

---

## Quiz

Test your understanding. These questions mirror the style and difficulty of CBA exam questions.

**Q1**: What function is used to define a new frontend plugin in Backstage?

<details>
<summary>Answer</summary>

`createPlugin()` from `@backstage/core-plugin-api`. It takes an object with `id`, `routes`, `apis`, and other configuration. It returns a plugin instance that can provide extensions via `.provide()`.
</details>

**Q2**: A frontend plugin needs data from a backend API. What is the correct way to make HTTP requests?

<details>
<summary>Answer</summary>

Use `useApi(fetchApiRef)` to get the Backstage fetch API, then call `fetchApi.fetch('/api/my-plugin/endpoint')`. This ensures the request includes proper auth headers and uses the correct base URL. Never use `window.fetch` or hardcode URLs.
</details>

**Q3**: In the new backend system, what does `coreServices.httpRouter` provide?

<details>
<summary>Answer</summary>

An Express router that is automatically mounted at `/api/<pluginId>`. Routes you add to this router are accessible at `/api/<pluginId>/your-route`. You do not need to manually configure the mount path.
</details>

**Q4**: What is the difference between `fetch:template` and `fetch:plain` in Software Templates?

<details>
<summary>Answer</summary>

`fetch:template` copies files and processes them through the Nunjucks templating engine, replacing `${{ values.name }}` placeholders with actual values. `fetch:plain` copies files as-is without any template processing. Use `fetch:plain` for binary files or when template syntax would conflict with the file content.
</details>

**Q5**: You are writing a custom theme. Which function should you use: `createTheme` from `@mui/material` or `createUnifiedTheme` from `@backstage/theme`?

<details>
<summary>Answer</summary>

`createUnifiedTheme` from `@backstage/theme`. This function extends MUI's theme with Backstage-specific features: page themes (`themeId`), navigation palette colors, and plugin-aware component overrides. Using MUI's `createTheme` directly will produce a theme that is missing Backstage-specific properties.
</details>

**Q6**: A custom scaffolder action needs to create a Jira ticket. Where does this action execute — in the browser or on the server?

<details>
<summary>Answer</summary>

On the server (Node.js backend). All scaffolder actions run server-side in the backend scaffolder process. This is why they can access secrets from `app-config.yaml`, make authenticated API calls, and interact with the filesystem. The browser only collects form input and displays progress.
</details>

**Q7**: In a frontend plugin test, you use `getByText('Loading...')` but the test fails because the API data loads asynchronously. What should you use instead?

<details>
<summary>Answer</summary>

Use `findByText('Loading...')` or more commonly `findByText('expected content after load')`. The `findBy*` queries from `@testing-library/react` retry until the element appears (with a default timeout). `getBy*` queries assert immediately and fail if the element is not in the DOM yet.
</details>

**Q8**: What is the correct way to register a custom scaffolder action in the new backend system?

<details>
<summary>Answer</summary>

Create a backend module using `createBackendModule` with `pluginId: 'scaffolder'`. In the module's `register` function, declare a dependency on `scaffolderActionsExtensionPoint` and call `scaffolder.addActions(yourCustomAction())` in the `init` function. Then add the module to the backend with `backend.add(yourModule)`. This pattern uses Backstage's dependency injection rather than manual wiring.
</details>

**Q9**: A plugin author writes `import { DatabaseService } from '@backstage/backend-plugin-api'` in a frontend plugin file. What happens?

<details>
<summary>Answer</summary>

The build will likely succeed (TypeScript types are just types), but the plugin will fail at runtime. `DatabaseService` and other backend APIs have no implementation in the browser environment. Frontend plugins cannot access the database directly. The author needs to create a backend plugin that exposes the data over an HTTP API and have the frontend plugin call that API using `fetchApiRef`.
</details>

**Q10**: In a Software Template YAML, how do you reference the output of a previous step?

<details>
<summary>Answer</summary>

Use the syntax `${{ steps['step-id'].output.outputName }}`. For example, if a `publish:github` step with `id: publish` outputs `remoteUrl`, you reference it as `${{ steps['publish'].output.remoteUrl }}`. Each action defines its own output schema, and outputs are set in the action handler via `ctx.output('key', value)`.
</details>

---

## Hands-On Exercise: Build a Full-Stack Backstage Plugin

**Objective**: Build a "Team Links" plugin that displays and manages useful links for each team. This exercise covers frontend plugin development, backend plugin development, and plugin integration.

### Setup

```bash
# Ensure you have a Backstage app (if not, create one)
npx @backstage/create-app@latest

cd my-backstage-app
```

### Step 1: Create the Backend Plugin

```bash
yarn new --select backend-plugin
# Name it: team-links
```

Implement a router in `plugins/team-links-backend/src/router.ts` that:
- `GET /links/:teamName` — Returns links for a team
- `POST /links` — Creates a new link `{ teamName, title, url }`
- `DELETE /links/:id` — Removes a link

Use an in-memory array or SQLite for storage.

### Step 2: Create the Frontend Plugin

```bash
yarn new --select plugin
# Name it: team-links
```

Build a page component that:
- Uses `useApi(fetchApiRef)` to call the backend
- Displays links in a Backstage `Table` component
- Has an `InfoCard` showing the team name
- Uses `Grid` layout from MUI

### Step 3: Add a Custom Theme

In `packages/app/src/theme.ts`, create a custom theme with:
- A custom primary color
- `textTransform: 'none'` on buttons
- A dark sidebar with a colored indicator

### Step 4: Write Tests

- Frontend: Use `renderInTestApp` and MSW to test the page renders links
- Backend: Use supertest to test all three endpoints

### Success Criteria

- [ ] `yarn dev` starts both frontend and backend without errors
- [ ] Navigating to `/team-links` shows the plugin page
- [ ] Links can be created and displayed
- [ ] The custom theme is visible (check sidebar color, button casing)
- [ ] `yarn test` passes for both `plugins/team-links` and `plugins/team-links-backend`
- [ ] No direct `window.fetch` calls — all requests go through `fetchApiRef`

### Bonus Challenge

Write a custom scaffolder action `team-links:seed` that pre-populates links for a new team when a service is created via Software Template. Register it as a backend module using `scaffolderActionsExtensionPoint`.

---

## Summary

This module covered the core of CBA Domain 4 — the largest domain on the exam at 32%. Here is what you should be able to do:

| Topic | Key Takeaway |
|-------|-------------|
| Frontend plugins | `createPlugin` + `createRoutableExtension`, mounted in `App.tsx` |
| Backend plugins | `createBackendPlugin` with dependency injection via `coreServices` |
| Communication | Frontend calls backend over HTTP using `fetchApiRef`, never direct imports |
| MUI / Theming | MUI v5 components, `sx` prop, `createUnifiedTheme` for custom branding |
| Software Templates | YAML-defined workflows with `fetch:template`, `publish:github`, `catalog:register` |
| Custom actions | `createTemplateAction` with typed input/output schemas, runs server-side |
| Auth providers | YAML config + sign-in resolvers that map external identity to catalog User entity |
| Testing | `renderInTestApp` + MSW for frontend, supertest + in-memory DB for backend |
| Plugin installation | Install package, wire into app/backend, configure in `app-config.yaml` |

---

## Next Steps

- **Module 3**: [Backstage Catalog Deep Dive](../module-1.3-backstage-catalog-infrastructure/) — Entity processors, providers, annotations, and troubleshooting (Domain 3, 22%)
- **Module 1**: [Backstage Development Workflow](../module-1.1-backstage-dev-workflow/) — Monorepo structure, Docker builds, CLI commands (Domain 1, 24%)
- Review the [Backstage Official Plugin Development Guide](https://backstage.io/docs/plugins/) for additional depth
