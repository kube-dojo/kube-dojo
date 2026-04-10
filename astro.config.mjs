// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://kube-dojo.github.io',
  trailingSlash: 'always',
  compressHTML: true,

  integrations: [
    starlight({
      title: 'KubeDojo',
      tagline: 'Free, comprehensive cloud native education',
      social: [
        {
          label: 'GitHub',
          icon: 'github',
          href: 'https://github.com/kube-dojo/kube-dojo.github.io',
        },
      ],
      credits: false,
      components: {
        Head: './src/components/Head.astro',
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
        Sidebar: './src/components/Sidebar.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      defaultLocale: 'root',
      locales: {
        root: { label: 'English', lang: 'en' },
        uk: { label: 'Українська', lang: 'uk' },
      },
      customCss: ['./src/css/custom.css'],
      sidebar: [

        // ── 1. Foundations: beginner entry points ──

        {
          label: 'Fundamentals',
          collapsed: true,
          items: [
            { label: 'Fundamentals Hub', link: '/prerequisites/' },
            { label: 'Zero to Terminal', autogenerate: { directory: 'prerequisites/zero-to-terminal' }, collapsed: true },
            { label: 'Everyday Linux', autogenerate: { directory: 'linux/foundations/everyday-use' }, collapsed: true },
            { label: 'Cloud Native 101', autogenerate: { directory: 'prerequisites/cloud-native-101' }, collapsed: true },
            { label: 'Kubernetes Basics', autogenerate: { directory: 'prerequisites/kubernetes-basics' }, collapsed: true },
            { label: 'Git Deep Dive', autogenerate: { directory: 'prerequisites/git-deep-dive' }, collapsed: true },
            { label: 'Philosophy & Design', autogenerate: { directory: 'prerequisites/philosophy-design' }, collapsed: true },
            { label: 'Modern DevOps', autogenerate: { directory: 'prerequisites/modern-devops' }, collapsed: true },
          ],
        },
        {
          label: 'Linux',
          collapsed: true,
          items: [
            { label: 'Linux Hub', link: '/linux/' },
            {
              label: 'Foundations',
              collapsed: true,
              items: [
                { label: 'Everyday Use', autogenerate: { directory: 'linux/foundations/everyday-use' }, collapsed: true },
                { label: 'System Essentials', autogenerate: { directory: 'linux/foundations/system-essentials' }, collapsed: true },
                { label: 'Container Primitives', autogenerate: { directory: 'linux/foundations/container-primitives' }, collapsed: true },
                { label: 'Networking', autogenerate: { directory: 'linux/foundations/networking' }, collapsed: true },
              ],
            },
            {
              label: 'Operations',
              collapsed: true,
              items: [
                { label: 'Shell Scripting', autogenerate: { directory: 'linux/operations/shell-scripting' }, collapsed: true },
                { label: 'Performance', autogenerate: { directory: 'linux/operations/performance' }, collapsed: true },
                { label: 'Troubleshooting', autogenerate: { directory: 'linux/operations/troubleshooting' }, collapsed: true },
              ],
            },
            {
              label: 'Security',
              collapsed: true,
              items: [
                { label: 'Hardening', autogenerate: { directory: 'linux/security/hardening' }, collapsed: true },
              ],
            },
            { label: 'LFCS: Linux SysAdmin', autogenerate: { directory: 'k8s/lfcs' }, collapsed: true },
          ],
        },

        // ── 2. Certifications: core K8s knowledge (before cloud-specific) ──

        {
          label: 'Certifications',
          collapsed: true,
          items: [
            { label: 'Certifications Hub', link: '/k8s/' },
            {
              label: 'Core Kubernetes',
              collapsed: true,
              items: [
                { label: 'KCNA: Cloud Native Associate', autogenerate: { directory: 'k8s/kcna' }, collapsed: true },
                { label: 'KCSA: Security Associate', autogenerate: { directory: 'k8s/kcsa' }, collapsed: true },
                { label: 'CKA: K8s Administrator', autogenerate: { directory: 'k8s/cka' }, collapsed: true },
                { label: 'CKAD: App Developer', autogenerate: { directory: 'k8s/ckad' }, collapsed: true },
                { label: 'CKS: Security Specialist', autogenerate: { directory: 'k8s/cks' }, collapsed: true },
              ],
            },
            { label: 'Extending Kubernetes', autogenerate: { directory: 'k8s/extending' }, collapsed: true },
            {
              label: 'Ecosystem Certifications',
              collapsed: true,
              items: [
                { label: 'PCA: Prometheus', autogenerate: { directory: 'k8s/pca' }, collapsed: true },
                { label: 'ICA: Istio', autogenerate: { directory: 'k8s/ica' }, collapsed: true },
                { label: 'CCA: Cilium', autogenerate: { directory: 'k8s/cca' }, collapsed: true },
                { label: 'CGOA: GitOps', autogenerate: { directory: 'k8s/cgoa' }, collapsed: true },
                { label: 'CBA: Backstage', autogenerate: { directory: 'k8s/cba' }, collapsed: true },
                { label: 'OTCA: OpenTelemetry', autogenerate: { directory: 'k8s/otca' }, collapsed: true },
                { label: 'KCA: Kyverno', autogenerate: { directory: 'k8s/kca' }, collapsed: true },
                { label: 'CAPA: Argo', autogenerate: { directory: 'k8s/capa' }, collapsed: true },
                { label: 'CNPE: Platform Engineer', autogenerate: { directory: 'k8s/cnpe' }, collapsed: true },
                { label: 'CNPA: Platform Associate', autogenerate: { directory: 'k8s/cnpa' }, collapsed: true },
                { label: 'FinOps Practitioner', autogenerate: { directory: 'k8s/finops' }, collapsed: true },
              ],
            },
          ],
        },

        // ── 3. Infrastructure: cloud + bare metal ──

        {
          label: 'Cloud',
          collapsed: true,
          items: [
            { label: 'Cloud Hub', link: '/cloud/' },
            { label: 'Rosetta Stone', link: '/cloud/hyperscaler-rosetta-stone/' },
            {
              label: 'AWS',
              collapsed: true,
              items: [
                { label: 'AWS Essentials', autogenerate: { directory: 'cloud/aws-essentials' }, collapsed: true },
                { label: 'EKS Deep Dive', autogenerate: { directory: 'cloud/eks-deep-dive' }, collapsed: true },
              ],
            },
            {
              label: 'Google Cloud',
              collapsed: true,
              items: [
                { label: 'GCP Essentials', autogenerate: { directory: 'cloud/gcp-essentials' }, collapsed: true },
                { label: 'GKE Deep Dive', autogenerate: { directory: 'cloud/gke-deep-dive' }, collapsed: true },
              ],
            },
            {
              label: 'Azure',
              collapsed: true,
              items: [
                { label: 'Azure Essentials', autogenerate: { directory: 'cloud/azure-essentials' }, collapsed: true },
                { label: 'AKS Deep Dive', autogenerate: { directory: 'cloud/aks-deep-dive' }, collapsed: true },
              ],
            },
            {
              label: 'Architecture & Enterprise',
              collapsed: true,
              items: [
                { label: 'Architecture Patterns', autogenerate: { directory: 'cloud/architecture-patterns' }, collapsed: true },
                { label: 'Advanced Operations', autogenerate: { directory: 'cloud/advanced-operations' }, collapsed: true },
                { label: 'Managed Services', autogenerate: { directory: 'cloud/managed-services' }, collapsed: true },
                { label: 'Enterprise & Hybrid', autogenerate: { directory: 'cloud/enterprise-hybrid' }, collapsed: true },
              ],
            },
          ],
        },
        {
          label: 'AI/ML Engineering',
          collapsed: true,
          items: [
            { label: 'AI/ML Hub', link: '/ai-ml-engineering/' },
            { label: 'Phase 0: Prerequisites', autogenerate: { directory: 'ai-ml-engineering/prerequisites' }, collapsed: true },
            { label: 'Phase 1: AI-Native Development', autogenerate: { directory: 'ai-ml-engineering/ai-native-development' }, collapsed: true },
            { label: 'Phase 2: Generative AI', autogenerate: { directory: 'ai-ml-engineering/generative-ai' }, collapsed: true },
            { label: 'Phase 3: Vector Search & RAG', autogenerate: { directory: 'ai-ml-engineering/vector-rag' }, collapsed: true },
            { label: 'Phase 4: Frameworks & Agents', autogenerate: { directory: 'ai-ml-engineering/frameworks-agents' }, collapsed: true },
            { label: 'Phase 5: Multimodal AI', autogenerate: { directory: 'ai-ml-engineering/multimodal-ai' }, collapsed: true },
            { label: 'Phase 6: Deep Learning', autogenerate: { directory: 'ai-ml-engineering/deep-learning' }, collapsed: true },
            { label: 'Phase 7: Advanced GenAI', autogenerate: { directory: 'ai-ml-engineering/advanced-genai' }, collapsed: true },
            { label: 'Phase 8: Classical ML', autogenerate: { directory: 'ai-ml-engineering/classical-ml' }, collapsed: true },
            { label: 'Phase 9: AI Safety', autogenerate: { directory: 'ai-ml-engineering/ai-safety' }, collapsed: true },
            { label: 'Phase 10: MLOps', autogenerate: { directory: 'ai-ml-engineering/mlops' }, collapsed: true },
            { label: 'Phase 11: AI Infrastructure', autogenerate: { directory: 'ai-ml-engineering/ai-infrastructure' }, collapsed: true },
            { label: 'Phase 12: History', autogenerate: { directory: 'ai-ml-engineering/history' }, collapsed: true },
          ],
        },
        {
          label: 'On-Premises',
          collapsed: true,
          items: [
            { label: 'On-Premises Hub', link: '/on-premises/' },
            { label: 'Planning & Economics', autogenerate: { directory: 'on-premises/planning' }, collapsed: true },
            { label: 'Bare Metal Provisioning', autogenerate: { directory: 'on-premises/provisioning' }, collapsed: true },
            { label: 'Networking', autogenerate: { directory: 'on-premises/networking' }, collapsed: true },
            { label: 'Storage', autogenerate: { directory: 'on-premises/storage' }, collapsed: true },
            { label: 'Multi-Cluster', autogenerate: { directory: 'on-premises/multi-cluster' }, collapsed: true },
            { label: 'Security & Compliance', autogenerate: { directory: 'on-premises/security' }, collapsed: true },
            { label: 'Day-2 Operations', autogenerate: { directory: 'on-premises/operations' }, collapsed: true },
            { label: 'Resilience & Migration', autogenerate: { directory: 'on-premises/resilience' }, collapsed: true },
          ],
        },

        // ── 4. Advanced: practices + tools ──

        {
          label: 'Platform Engineering',
          collapsed: true,
          items: [
            { label: 'Platform Hub', link: '/platform/' },

            // ── Part 1: Foundations (timeless theory) ──
            {
              label: 'Part 1: Foundations',
              collapsed: true,
              autogenerate: { directory: 'platform/foundations' },
            },

            // ── Part 2: Disciplines (applied practices) ──
            {
              label: 'Part 2: Disciplines',
              collapsed: true,
              items: [
                {
                  label: 'Core Platform',
                  collapsed: true,
                  items: [
                    { label: 'SRE', autogenerate: { directory: 'platform/disciplines/core-platform/sre' }, collapsed: true },
                    { label: 'Platform Engineering', autogenerate: { directory: 'platform/disciplines/core-platform/platform-engineering' }, collapsed: true },
                    { label: 'Platform Leadership', autogenerate: { directory: 'platform/disciplines/core-platform/leadership' }, collapsed: true },
                  ],
                },
                {
                  label: 'Delivery & Automation',
                  collapsed: true,
                  items: [
                    { label: 'Release Engineering', autogenerate: { directory: 'platform/disciplines/delivery-automation/release-engineering' }, collapsed: true },
                    { label: 'GitOps', autogenerate: { directory: 'platform/disciplines/delivery-automation/gitops' }, collapsed: true },
                    { label: 'Infrastructure as Code', autogenerate: { directory: 'platform/disciplines/delivery-automation/iac' }, collapsed: true },
                  ],
                },
                {
                  label: 'Reliability & Security',
                  collapsed: true,
                  items: [
                    { label: 'Networking', autogenerate: { directory: 'platform/disciplines/reliability-security/networking' }, collapsed: true },
                    { label: 'Chaos Engineering', autogenerate: { directory: 'platform/disciplines/reliability-security/chaos-engineering' }, collapsed: true },
                    { label: 'DevSecOps', autogenerate: { directory: 'platform/disciplines/reliability-security/devsecops' }, collapsed: true },
                  ],
                },
                {
                  label: 'Data & AI',
                  collapsed: true,
                  items: [
                    { label: 'Data Engineering', autogenerate: { directory: 'platform/disciplines/data-ai/data-engineering' }, collapsed: true },
                    { label: 'MLOps', autogenerate: { directory: 'platform/disciplines/data-ai/mlops' }, collapsed: true },
                    { label: 'AIOps', autogenerate: { directory: 'platform/disciplines/data-ai/aiops' }, collapsed: true },
                    { label: 'AI Infrastructure', autogenerate: { directory: 'platform/disciplines/data-ai/ai-infrastructure' }, collapsed: true },
                  ],
                },
                { label: 'FinOps', autogenerate: { directory: 'platform/disciplines/business-value/finops' }, collapsed: true },
              ],
            },

            // ── Part 3: Toolkits (current tools) ──
            {
              label: 'Part 3: Toolkits',
              collapsed: true,
              items: [
                { label: 'Toolkit Directory', link: '/platform/toolkits/' },
                {
                  label: 'CI/CD & Delivery',
                  collapsed: true,
                  items: [
                    { label: 'CI/CD Pipelines', autogenerate: { directory: 'platform/toolkits/cicd-delivery/ci-cd-pipelines' }, collapsed: true },
                    { label: 'GitOps & Deployments', autogenerate: { directory: 'platform/toolkits/cicd-delivery/gitops-deployments' }, collapsed: true },
                    { label: 'Source Control', autogenerate: { directory: 'platform/toolkits/cicd-delivery/source-control' }, collapsed: true },
                    { label: 'Container Registries', autogenerate: { directory: 'platform/toolkits/cicd-delivery/container-registries' }, collapsed: true },
                  ],
                },
                {
                  label: 'Observability',
                  collapsed: true,
                  items: [
                    { label: 'Observability Stack', autogenerate: { directory: 'platform/toolkits/observability-intelligence/observability' }, collapsed: true },
                    { label: 'AIOps Tools', autogenerate: { directory: 'platform/toolkits/observability-intelligence/aiops-tools' }, collapsed: true },
                  ],
                },
                {
                  label: 'Infrastructure',
                  collapsed: true,
                  items: [
                    { label: 'IaC Tools', autogenerate: { directory: 'platform/toolkits/infrastructure-networking/iac-tools' }, collapsed: true },
                    { label: 'K8s Distributions', autogenerate: { directory: 'platform/toolkits/infrastructure-networking/k8s-distributions' }, collapsed: true },
                    { label: 'Networking Tools', autogenerate: { directory: 'platform/toolkits/infrastructure-networking/networking' }, collapsed: true },
                    { label: 'Platforms', autogenerate: { directory: 'platform/toolkits/infrastructure-networking/platforms' }, collapsed: true },
                    { label: 'Storage', autogenerate: { directory: 'platform/toolkits/infrastructure-networking/storage' }, collapsed: true },
                  ],
                },
                {
                  label: 'Security & Quality',
                  collapsed: true,
                  items: [
                    { label: 'Security Tools', autogenerate: { directory: 'platform/toolkits/security-quality/security-tools' }, collapsed: true },
                    { label: 'Code Quality', autogenerate: { directory: 'platform/toolkits/security-quality/code-quality' }, collapsed: true },
                  ],
                },
                {
                  label: 'Developer Experience',
                  collapsed: true,
                  items: [
                    { label: 'DevEx Tools', autogenerate: { directory: 'platform/toolkits/developer-experience/devex-tools' }, collapsed: true },
                    { label: 'Scaling & Reliability', autogenerate: { directory: 'platform/toolkits/developer-experience/scaling-reliability' }, collapsed: true },
                  ],
                },
                {
                  label: 'Data & AI Platforms',
                  collapsed: true,
                  items: [
                    { label: 'ML Platforms', autogenerate: { directory: 'platform/toolkits/data-ai-platforms/ml-platforms' }, collapsed: true },
                    { label: 'Cloud-Native Databases', autogenerate: { directory: 'platform/toolkits/data-ai-platforms/cloud-native-databases' }, collapsed: true },
                  ],
                },
              ],
            },
          ],
        },

        // ── Utility ──

        { label: "What's New", link: '/changelog/' },
        { label: 'Glossary', link: '/glossary/' },
      ],
    }),
  ],
});
