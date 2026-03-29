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
        { label: "What's New", link: '/changelog/' },
        {
          label: 'Fundamentals',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/prerequisites/' },
            { label: 'Zero to Terminal', autogenerate: { directory: 'prerequisites/zero-to-terminal' }, collapsed: true },
            { label: 'Philosophy & Design', autogenerate: { directory: 'prerequisites/philosophy-design' }, collapsed: true },
            { label: 'Cloud Native 101', autogenerate: { directory: 'prerequisites/cloud-native-101' }, collapsed: true },
            { label: 'Kubernetes Basics', autogenerate: { directory: 'prerequisites/kubernetes-basics' }, collapsed: true },
            { label: 'Modern DevOps', autogenerate: { directory: 'prerequisites/modern-devops' }, collapsed: true },
          ],
        },
        {
          label: 'Linux Deep Dive',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/linux/' },
            { label: 'Linux Everyday Use', autogenerate: { directory: 'linux/foundations/everyday-use' }, collapsed: true },
            { label: 'System Essentials', autogenerate: { directory: 'linux/foundations/system-essentials' }, collapsed: true },
            { label: 'Container Primitives', autogenerate: { directory: 'linux/foundations/container-primitives' }, collapsed: true },
            { label: 'Networking', autogenerate: { directory: 'linux/foundations/networking' }, collapsed: true },
            { label: 'Security', autogenerate: { directory: 'linux/security' }, collapsed: true },
            { label: 'Operations', autogenerate: { directory: 'linux/operations' }, collapsed: true },
          ],
        },
        {
          label: 'Cloud',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/cloud/' },
            { label: 'Rosetta Stone', link: '/cloud/hyperscaler-rosetta-stone/' },
            { label: 'AWS Essentials', autogenerate: { directory: 'cloud/aws-essentials' }, collapsed: true },
            { label: 'GCP Essentials', autogenerate: { directory: 'cloud/gcp-essentials' }, collapsed: true },
            { label: 'Azure Essentials', autogenerate: { directory: 'cloud/azure-essentials' }, collapsed: true },
            { label: 'Architecture Patterns', autogenerate: { directory: 'cloud/architecture-patterns' }, collapsed: true },
            { label: 'EKS Deep Dive', autogenerate: { directory: 'cloud/eks-deep-dive' }, collapsed: true },
            { label: 'GKE Deep Dive', autogenerate: { directory: 'cloud/gke-deep-dive' }, collapsed: true },
            { label: 'AKS Deep Dive', autogenerate: { directory: 'cloud/aks-deep-dive' }, collapsed: true },
            { label: 'Advanced Operations', autogenerate: { directory: 'cloud/advanced-operations' }, collapsed: true },
            { label: 'Managed Services', autogenerate: { directory: 'cloud/managed-services' }, collapsed: true },
            { label: 'Enterprise & Hybrid', autogenerate: { directory: 'cloud/enterprise-hybrid' }, collapsed: true },
          ],
        },
        {
          label: 'Certifications',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/k8s/' },
            { label: 'KCNA: Cloud Native Associate', autogenerate: { directory: 'k8s/kcna' }, collapsed: true },
            { label: 'KCSA: Security Associate', autogenerate: { directory: 'k8s/kcsa' }, collapsed: true },
            { label: 'CKA: K8s Administrator', autogenerate: { directory: 'k8s/cka' }, collapsed: true },
            { label: 'CKAD: App Developer', autogenerate: { directory: 'k8s/ckad' }, collapsed: true },
            { label: 'CKS: Security Specialist', autogenerate: { directory: 'k8s/cks' }, collapsed: true },
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
                { label: 'LFCS: Linux SysAdmin', autogenerate: { directory: 'k8s/lfcs' }, collapsed: true },
                { label: 'FinOps Practitioner', autogenerate: { directory: 'k8s/finops' }, collapsed: true },
              ],
            },
          ],
        },
        {
          label: 'Platform Engineering',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/platform/' },
            { label: 'Foundations', autogenerate: { directory: 'platform/foundations' }, collapsed: true },
            {
              label: 'Disciplines',
              collapsed: true,
              items: [
                { label: 'Core Platform', autogenerate: { directory: 'platform/disciplines/core-platform' }, collapsed: true },
                { label: 'Delivery & Automation', autogenerate: { directory: 'platform/disciplines/delivery-automation' }, collapsed: true },
                { label: 'Reliability & Security', autogenerate: { directory: 'platform/disciplines/reliability-security' }, collapsed: true },
                { label: 'Data & AI', autogenerate: { directory: 'platform/disciplines/data-ai' }, collapsed: true },
                { label: 'Business Value', autogenerate: { directory: 'platform/disciplines/business-value' }, collapsed: true },
              ],
            },
            {
              label: 'Toolkits',
              collapsed: true,
              items: [
                { label: 'CI/CD & Delivery', autogenerate: { directory: 'platform/toolkits/cicd-delivery' }, collapsed: true },
                { label: 'Observability & Intelligence', autogenerate: { directory: 'platform/toolkits/observability-intelligence' }, collapsed: true },
                { label: 'Infrastructure & Networking', autogenerate: { directory: 'platform/toolkits/infrastructure-networking' }, collapsed: true },
                { label: 'Security & Quality', autogenerate: { directory: 'platform/toolkits/security-quality' }, collapsed: true },
                { label: 'Developer Experience', autogenerate: { directory: 'platform/toolkits/developer-experience' }, collapsed: true },
                { label: 'Data & AI Platforms', autogenerate: { directory: 'platform/toolkits/data-ai-platforms' }, collapsed: true },
              ],
            },
          ],
        },
        {
          label: 'On-Premises',
          collapsed: true,
          items: [
            { label: 'Overview', link: '/on-premises/' },
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
        { label: 'Glossary', link: '/glossary/' },
      ],
    }),
  ],
});
