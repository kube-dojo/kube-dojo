// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: 'https://kube-dojo.github.io',
  trailingSlash: 'always',
  compressHTML: true,
  redirects: {
    // ML curriculum reorganization (#677): classical-ml/ -> machine-learning/
    '/ai-ml-engineering/classical-ml/': '/ai-ml-engineering/machine-learning/',
    '/ai-ml-engineering/classical-ml/index/': '/ai-ml-engineering/machine-learning/',
    '/ai-ml-engineering/classical-ml/module-1.1-scikit-learn-classical-ml/':
      '/ai-ml-engineering/machine-learning/module-1.1-scikit-learn-api-and-pipelines/',
    '/ai-ml-engineering/classical-ml/module-1.2-xgboost-gradient-boosting/':
      '/ai-ml-engineering/machine-learning/module-1.6-xgboost-gradient-boosting/',
    '/ai-ml-engineering/classical-ml/module-1.3-time-series-forecasting/':
      '/ai-ml-engineering/machine-learning/module-1.12-time-series-forecasting/',
  },
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
  vite: {
    build: {
      rollupOptions: {
        onwarn(warning, defaultWarn) {
          if (
            warning.message?.includes('"matchHostname", "matchPathname", "matchPort" and "matchProtocol"') &&
            warning.message?.includes('@astrojs/internal-helpers/remote') &&
            warning.message?.includes('node_modules/astro/dist/assets/utils/index.js')
          ) {
            return;
          }
          defaultWarn(warning);
        },
      },
    },
  },

  integrations: [
    starlight({
      title: 'KubeDojo',
      tagline: 'Free, comprehensive cloud native education',
      disable404Route: true,
      expressiveCode: {
        shiki: {
          langAlias: {
            ascii: 'txt',
            jinja2: 'jinja',
            kubernetes: 'yaml',
            logql: 'txt',
            promql: 'txt',
            rego: 'txt',
            traceql: 'txt',
            wing: 'typescript',
          },
        },
      },
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
      customCss: ['./src/css/custom.css', 'katex/dist/katex.min.css'],
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
        {
          label: 'AI',
          collapsed: true,
          items: [
            { label: 'AI Hub', link: '/ai/' },
            { label: 'AI Foundations', autogenerate: { directory: 'ai/foundations' }, collapsed: true },
            { label: 'AI-Native Work', autogenerate: { directory: 'ai/ai-native-work' }, collapsed: true },
            { label: 'AI Building', autogenerate: { directory: 'ai/ai-building' }, collapsed: true },
            { label: 'Open Models & Local Inference', autogenerate: { directory: 'ai/open-models-local-inference' }, collapsed: true },
            { label: 'AI for Kubernetes & Platform Work', autogenerate: { directory: 'ai/ai-for-kubernetes-platform-work' }, collapsed: true },
            { label: 'History of AI', collapsed: true, items: [
              { label: 'Overview', link: '/ai-history/' },
              {
                label: 'Part 1: Mathematical Foundations (1840s–1940s)',
                collapsed: true,
                items: [
                  { label: '01: The Laws of Thought', link: '/ai-history/ch-01-the-laws-of-thought/' },
                  { label: '02: The Universal Machine', link: '/ai-history/ch-02-the-universal-machine/' },
                  { label: '03: The Physical Bridge', link: '/ai-history/ch-03-the-physical-bridge/' },
                  { label: '04: The Statistical Roots', link: '/ai-history/ch-04-the-statistical-roots/' },
                  { label: '05: The Neural Abstraction', link: '/ai-history/ch-05-the-neural-abstraction/' },
                ],
              },
              {
                label: 'Part 2: Analog Dream & Digital Blank Slate (1940s–1950s)',
                collapsed: true,
                items: [
                  { label: '06: The Cybernetics Movement', link: '/ai-history/ch-06-the-cybernetics-movement/' },
                  { label: '07: The Analog Bottleneck', link: '/ai-history/ch-07-the-analog-bottleneck/' },
                  { label: '08: The Stored Program', link: '/ai-history/ch-08-the-stored-program/' },
                  { label: '09: The Memory Miracle', link: '/ai-history/ch-09-the-memory-miracle/' },
                  { label: '10: The Imitation Game', link: '/ai-history/ch-10-the-imitation-game/' },
                ],
              },
              {
                label: 'Part 3: Birth of Symbolic AI (1950s–1960s)',
                collapsed: true,
                items: [
                  { label: '11: The Summer AI Named Itself', link: '/ai-history/ch-11-the-summer-ai-named-itself/' },
                  { label: '12: The Logic Theorist and GPS', link: '/ai-history/ch-12-logic-theorist-gps/' },
                  { label: '13: The List Processor', link: '/ai-history/ch-13-the-list-processor/' },
                  { label: '14: The Perceptron', link: '/ai-history/ch-14-the-perceptron/' },
                  { label: '15: The Gradient Descent Concept', link: '/ai-history/ch-15-the-gradient-descent-concept/' },
                  { label: '16: The Cold War Blank Check', link: '/ai-history/ch-16-the-cold-war-blank-check/' },
                ],
              },
              {
                label: 'Part 4: First Winter & Shift to Knowledge (1970s–1980s)',
                collapsed: true,
                items: [
                  { label: "17: The Perceptron's Fall", link: '/ai-history/ch-17-the-perceptron-s-fall/' },
                  { label: '18: The Lighthill Devastation', link: '/ai-history/ch-18-the-lighthill-devastation/' },
                  { label: '19: Rules, Experts, and the Knowledge Bottleneck', link: '/ai-history/ch-19-rules-experts-and-the-knowledge-bottleneck/' },
                  { label: '20: Project MAC', link: '/ai-history/ch-20-project-mac/' },
                  { label: '21: The Rule-Based Fortune', link: '/ai-history/ch-21-the-rule-based-fortune/' },
                  { label: '22: The Lisp Machine Bubble', link: '/ai-history/ch-22-the-lisp-machine-bubble/' },
                  { label: '23: The Japanese Threat', link: '/ai-history/ch-23-the-japanese-threat/' },
                ],
              },
              {
                label: 'Part 5: Mathematical Resurrection (1980s–1990s)',
                collapsed: true,
                items: [
                  { label: '24: The Math That Waited for the Machine', link: '/ai-history/ch-24-the-math-that-waited-for-the-machine/' },
                  { label: '25: The Universal Approximation Theorem', link: '/ai-history/ch-25-the-universal-approximation-theorem-1989/' },
                  { label: '26: Bayesian Networks', link: '/ai-history/ch-26-bayesian-networks/' },
                  { label: '27: The Convolutional Breakthrough', link: '/ai-history/ch-27-the-convolutional-breakthrough/' },
                  { label: '28: The Second AI Winter', link: '/ai-history/ch-28-the-second-ai-winter/' },
                  { label: '29: Support Vector Machines', link: '/ai-history/ch-29-support-vector-machines/' },
                  { label: '30: The Statistical Underground', link: '/ai-history/ch-30-the-statistical-underground/' },
                  { label: '31: Reinforcement Learning Roots', link: '/ai-history/ch-31-reinforcement-learning-roots/' },
                ],
              },
              {
                label: 'Part 6: Rise of Data & Distributed Compute (1990s–2000s)',
                collapsed: true,
                items: [
                  { label: '32: The DARPA SUR Program', link: '/ai-history/ch-32-the-darpa-sur-program/' },
                  { label: '33: Deep Blue', link: '/ai-history/ch-33-deep-blue/' },
                  { label: '34: The Accidental Corpus', link: '/ai-history/ch-34-the-accidental-corpus/' },
                  { label: '35: Indexing the Mind', link: '/ai-history/ch-35-indexing-the-mind/' },
                  { label: '36: The Multicore Wall', link: '/ai-history/ch-36-the-multicore-wall/' },
                  { label: '37: Distributing the Compute', link: '/ai-history/ch-37-distributing-the-compute/' },
                  { label: '38: The Human API', link: '/ai-history/ch-38-the-human-api/' },
                  { label: '39: The Vision Wall', link: '/ai-history/ch-39-the-vision-wall/' },
                  { label: '40: Data Becomes Infrastructure', link: '/ai-history/ch-40-data-becomes-infrastructure/' },
                ],
              },
              {
                label: 'Part 7: Deep Learning Revolution & GPU Coup (2010s)',
                collapsed: true,
                items: [
                  { label: '41: The Graphics Hack', link: '/ai-history/ch-41-the-graphics-hack/' },
                  { label: '42: CUDA', link: '/ai-history/ch-42-cuda/' },
                  { label: '43: The ImageNet Smash', link: '/ai-history/ch-43-the-imagenet-smash/' },
                  { label: '44: The Latent Space', link: '/ai-history/ch-44-the-latent-space/' },
                  { label: '45: Generative Adversarial Networks', link: '/ai-history/ch-45-generative-adversarial-networks/' },
                  { label: '46: The Recurrent Bottleneck', link: '/ai-history/ch-46-the-recurrent-bottleneck/' },
                  { label: '47: The Depths of Vision', link: '/ai-history/ch-47-the-depths-of-vision/' },
                  { label: '48: AlphaGo', link: '/ai-history/ch-48-alphago/' },
                  { label: '49: The Custom Silicon', link: '/ai-history/ch-49-the-custom-silicon/' },
                ],
              },
              {
                label: 'Part 8: Transformer, Scale & Open Source (2017–2022)',
                collapsed: true,
                items: [
                  { label: '50: Attention Is All You Need', link: '/ai-history/ch-50-attention-is-all-you-need/' },
                  { label: '51: The Open Source Distribution Layer', link: '/ai-history/ch-51-the-open-source-distribution-layer/' },
                  { label: '52: Bidirectional Context', link: '/ai-history/ch-52-bidirectional-context/' },
                  { label: '53: The Dawn of Few-Shot Learning', link: '/ai-history/ch-53-the-dawn-of-few-shot-learning/' },
                  { label: '54: The Hub of Weights', link: '/ai-history/ch-54-the-hub-of-weights/' },
                  { label: '55: The Scaling Laws', link: '/ai-history/ch-55-the-scaling-laws/' },
                  { label: '56: The Megacluster', link: '/ai-history/ch-56-the-megacluster/' },
                  { label: '57: The Alignment Problem', link: '/ai-history/ch-57-the-alignment-problem/' },
                  { label: '58: The Math of Noise', link: '/ai-history/ch-58-the-math-of-noise/' },
                ],
              },
              {
                label: 'Part 9: Product Shock & Physical Limits (2022–present)',
                collapsed: true,
                items: [
                  { label: '59: The Product Shock', link: '/ai-history/ch-59-the-product-shock/' },
                  { label: '60: The Agent Turn', link: '/ai-history/ch-60-the-agent-turn/' },
                  { label: '61: The Physics of Scale', link: '/ai-history/ch-61-the-physics-of-scale/' },
                  { label: '62: Multimodal Convergence', link: '/ai-history/ch-62-multimodal-convergence/' },
                  { label: '63: Inference Economics', link: '/ai-history/ch-63-inference-economics/' },
                  { label: '64: The Edge Compute Bottleneck', link: '/ai-history/ch-64-the-edge-compute-bottleneck/' },
                  { label: '65: The Open Weights Rebellion', link: '/ai-history/ch-65-the-open-weights-rebellion/' },
                  { label: '66: Benchmark Wars', link: '/ai-history/ch-66-benchmark-wars/' },
                  { label: '67: The Monopoly', link: '/ai-history/ch-67-the-monopoly/' },
                  { label: '68: Data Labor and the Copyright Reckoning', link: '/ai-history/ch-68-data-labor-and-the-copyright-reckoning/' },
                  { label: '69: The Data Exhaustion Limit', link: '/ai-history/ch-69-the-data-exhaustion-limit/' },
                  { label: '70: The Energy Grid Collision', link: '/ai-history/ch-70-the-energy-grid-collision/' },
                  { label: '71: The Chip War', link: '/ai-history/ch-71-the-chip-war/' },
                  { label: '72: The Infinite Datacenter', link: '/ai-history/ch-72-the-infinite-datacenter/' },
                ],
              },
            ] },
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
            { label: 'Bridges to Other Tracks', autogenerate: { directory: 'k8s/bridges' }, collapsed: true },
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
            { label: 'Prerequisites', autogenerate: { directory: 'ai-ml-engineering/prerequisites' }, collapsed: true },
            { label: 'AI-Native Development', autogenerate: { directory: 'ai-ml-engineering/ai-native-development' }, collapsed: true },
            { label: 'Generative AI', autogenerate: { directory: 'ai-ml-engineering/generative-ai' }, collapsed: true },
            { label: 'Vector Search & RAG', autogenerate: { directory: 'ai-ml-engineering/vector-rag' }, collapsed: true },
            { label: 'Frameworks & Agents', autogenerate: { directory: 'ai-ml-engineering/frameworks-agents' }, collapsed: true },
            { label: 'MLOps & LLMOps', autogenerate: { directory: 'ai-ml-engineering/mlops' }, collapsed: true },
            { label: 'AI Infrastructure', autogenerate: { directory: 'ai-ml-engineering/ai-infrastructure' }, collapsed: true },
            { label: 'Advanced GenAI & Safety', autogenerate: { directory: 'ai-ml-engineering/advanced-genai' }, collapsed: true },
            { label: 'Multimodal AI', autogenerate: { directory: 'ai-ml-engineering/multimodal-ai' }, collapsed: true },
            { label: 'Deep Learning Foundations', autogenerate: { directory: 'ai-ml-engineering/deep-learning' }, collapsed: true },
            { label: 'Machine Learning', autogenerate: { directory: 'ai-ml-engineering/machine-learning' }, collapsed: true },
            { label: 'Reinforcement Learning', autogenerate: { directory: 'ai-ml-engineering/reinforcement-learning' }, collapsed: true },
            { label: 'Bridges to Other Tracks', autogenerate: { directory: 'ai-ml-engineering/bridges' }, collapsed: true },
            { label: 'Appendix A: History of AI/ML', autogenerate: { directory: 'ai-ml-engineering/history' }, collapsed: true },
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
            { label: 'AI/ML Infrastructure', autogenerate: { directory: 'on-premises/ai-ml-infrastructure' }, collapsed: true },
          ],
        },

        // ── 4. Advanced: practices + tools ──

        {
          label: 'Platform Engineering',
          collapsed: true,
          items: [
            { label: 'Platform Hub', link: '/platform/' },

            // ── Foundations (timeless theory) ──
            {
              label: 'Foundations',
              collapsed: true,
              autogenerate: { directory: 'platform/foundations' },
            },

            // ── Disciplines (applied practices) ──
            {
              label: 'Disciplines',
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

            // ── Toolkits (current tools) ──
            {
              label: 'Toolkits',
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
