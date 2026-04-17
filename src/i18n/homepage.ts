/**
 * Homepage translations — add a new locale by adding a key here.
 * The homepage template (src/layouts/Homepage.astro) reads from this.
 */

export interface HomepageStrings {
  lang: string;
  dir: string;
  prefix: string; // URL prefix: '' for root, '/uk' for Ukrainian
  title: string;
  description: string;
  canonical: string;

  // Nav
  navHome: string;
  navFundamentals: string;
  navLinux: string;
  navCloud: string;
  navCertifications: string;
  navPlatform: string;
  navOnPrem: string;
  searchPlaceholder: string;
  langFlag: string; // e.g. '🇬🇧 EN'
  langSwitchHref: string; // e.g. '/uk/'

  // Hero
  heroBadge: string;
  heroUpdated: string;
  heroTitle1: string; // before accent
  heroAccent: string;
  heroTitle2: string; // after accent
  heroSubtitle: string;
  ctaStart: string;
  ctaWhatsNew: string;
  ctaProgress: string;
  statModules: string;
  statTracks: string;
  statCerts: string;
  statTranslations: string;

  // Tracks
  tracksTitle: string;
  tracksDesc: string;
  trackFundTitle: string;
  trackFundDesc: string;
  trackFundMeta: string;
  trackLinuxTitle: string;
  trackLinuxDesc: string;
  trackLinuxMeta: string;
  trackCloudTitle: string;
  trackCloudDesc: string;
  trackCloudMeta: string;
  trackCertTitle: string;
  trackCertDesc: string;
  trackCertMeta: string;
  trackPlatTitle: string;
  trackPlatDesc: string;
  trackPlatMeta: string;
  trackPremTitle: string;
  trackPremDesc: string;
  trackPremMeta: string;
  trackAiTitle: string;
  trackAiDesc: string;
  trackAiMeta: string;

  // Recommended path
  pathTitle: string;
  pathDesc: string;
  pathStep1: string;
  pathStep1Mod: string;
  pathStep2: string;
  pathStep2Mod: string;
  pathStep3: string;
  pathStep3Mod: string;
  pathStep4: string;
  pathStep4Mod: string;
  pathStep5: string;
  pathStep5Mod: string;
  pathStep6: string;
  pathStep6Mod: string;

  // Where to start
  whereTitle: string;
  whereYouAre: string;
  whereStart: string;
  whereRows: Array<[string, string, string]>; // [description, label, href]

  // Philosophy
  philTitle: string;
  philBody: string;
  philBody2: string;

  // Contributing
  contribTitle: string;
  contribBody: string;

  // Dedication
  dedTitle: string;
  dedBody1: string;
  dedBody2: string;
  dedPoemTitle: string;
  dedPoemAuthor: string;
  dedPoem: string;

  // Footer
  footerText: string;
  footerChangelog: string;
  footerProgress: string;
  licenseText: string;
  quoteText: string;
}

export const translations: Record<string, HomepageStrings> = {
  en: {
    lang: 'en',
    dir: 'ltr',
    prefix: '',
    title: 'KubeDojo — Free Cloud Native Education',
    description: 'Free cloud native education from terminal basics to platform engineering, on-prem Kubernetes, and AI/ML systems.',
    canonical: 'https://kube-dojo.github.io/',

    navHome: 'Home',
    navFundamentals: 'Fundamentals',
    navLinux: 'Linux',
    navCloud: 'Cloud',
    navCertifications: 'Certifications',
    navPlatform: 'Platform',
    navOnPrem: 'On-Premises',
    searchPlaceholder: 'Search docs...',
    langFlag: '🇬🇧 EN',
    langSwitchHref: '/uk/',

    heroBadge: 'Free & Open Source',
    heroUpdated: 'Updated April 17, 2026',
    heroTitle1: 'Master ',
    heroAccent: 'Cloud Native',
    heroTitle2: 'from Zero to Production',
    heroSubtitle: 'Free cloud native education from terminal basics to production systems, private infrastructure, and local-first AI/ML. Theory-first, hands-on always.',
    ctaStart: 'Start Learning →',
    ctaWhatsNew: "What's New",
    ctaProgress: 'My Progress',
    statModules: 'Modules',
    statTracks: 'Tracks',
    statCerts: 'K8s track modules',
    statTranslations: 'Ukrainian modules',

    tracksTitle: 'Learning Tracks',
    tracksDesc: 'Seven structured tracks from absolute beginner to production systems, private infrastructure, and AI/ML engineering.',
    trackFundTitle: 'Fundamentals',
    trackFundDesc: "Zero to Terminal, Cloud Native 101, K8s Basics. Start here if you're new.",
    trackFundMeta: '📚 47 modules · ⏱ ~55h',
    trackLinuxTitle: 'Linux',
    trackLinuxDesc: 'Everyday Use + Deep Dive. From basic commands to kernel internals.',
    trackLinuxMeta: '📚 37 modules · ⏱ ~50h',
    trackCloudTitle: 'Cloud',
    trackCloudDesc: 'AWS, GCP, Azure essentials. EKS/GKE/AKS deep dives. Architecture patterns.',
    trackCloudMeta: '📚 116 modules · ⏱ ~150h',
    trackCertTitle: 'Certifications',
    trackCertDesc: 'Core Kubernetes certs plus specialist and platform-oriented learning paths.',
    trackCertMeta: '📚 207 modules · ⏱ ~250h',
    trackPlatTitle: 'Platform Engineering',
    trackPlatDesc: 'SRE, GitOps, DevSecOps, MLOps, FinOps, Chaos Engineering. 96 toolkit modules.',
    trackPlatMeta: '📚 220 modules · ⏱ ~280h',
    trackPremTitle: 'On-Premises',
    trackPremDesc: 'Bare metal K8s from rack to cluster. Networking, storage, operations.',
    trackPremMeta: '📚 59 modules · ⏱ ~80h',
    trackAiTitle: 'AI/ML Engineering',
    trackAiDesc: 'Local-first AI, RAG, MLOps, inference, fine-tuning, and AI platform paths.',
    trackAiMeta: '📚 117 modules · ⏱ ~160h',

    pathTitle: 'Recommended Path',
    pathDesc: 'Not sure where to start? Follow this progression.',
    pathStep1: 'Fundamentals',
    pathStep1Mod: '33 modules',
    pathStep2: 'CKA Certification',
    pathStep2Mod: '47 modules',
    pathStep3: 'CKAD + CKS',
    pathStep3Mod: '60 modules',
    pathStep4: 'Cloud or AI/ML Route',
    pathStep4Mod: '116 / 117 modules',
    pathStep5: 'Platform Engineering',
    pathStep5Mod: '220 modules',
    pathStep6: 'On-Prem / Specialization',
    pathStep6Mod: '59+ modules',

    whereTitle: 'Where to Start',
    whereYouAre: 'You are...',
    whereStart: 'Start here',
    whereRows: [
      ['Never used a terminal before', 'Zero to Terminal (start here!)', '/prerequisites/zero-to-terminal/'],
      ['New to containers/K8s', 'Prerequisites', '/prerequisites/'],
      ['Want K8s admin certification', 'CKA', '/k8s/cka/'],
      ['Want K8s developer certification', 'CKAD', '/k8s/ckad/'],
      ['Want K8s security certification', 'CKS', '/k8s/cks/'],
      ['Entry-level K8s cert', 'KCNA or KCSA', '/k8s/kcna/'],
      ['Platform engineer', 'CNPE Learning Path', '/k8s/cnpe/'],
      ['Multi-cloud Kubernetes', 'Cloud Track (AWS, GCP, Azure)', '/cloud/'],
      ['Building AI systems or local-first ML workflows', 'AI/ML Engineering', '/ai-ml-engineering/'],
      ['Running K8s on bare metal', 'On-Premises Track', '/on-premises/'],
      ['Already certified, want depth', 'Platform Engineering', '/platform/'],
    ],

    philTitle: 'Philosophy',
    philBody: "<strong>Theory before hands-on.</strong> You can't troubleshoot what you don't understand. <strong>Principles over tools.</strong> Tools change; foundations don't. <strong>No memorization.</strong> K8s docs are available during exams — we teach navigation, not YAML memorization.",
    philBody2: 'KubeDojo is free, open-source, and text-based. For exam simulation, use <a href="https://killer.sh">killer.sh</a>. For interactive labs, use <a href="https://killercoda.com">killercoda.com</a>.',

    contribTitle: 'Contributing',
    contribBody: 'We welcome hands-on exercises, production war stories, tool deep-dives, and error fixes. Open an issue to discuss before large PRs, follow existing module structure, and test all commands and YAML before submitting.',

    dedTitle: '🇺🇦 Dedication',
    dedBody1: 'This project is dedicated to Ukrainian IT engineers who gave their lives defending their homeland. They were developers, DevOps engineers, system administrators. They built systems, wrote code, maintained infrastructure. When the war came, they left their keyboards and took up arms.',
    dedBody2: 'Their code lives on. Their sacrifice is not forgotten. Slava Ukraini.',
    dedPoemTitle: 'My Testament (Заповіт)',
    dedPoemAuthor: 'Taras Shevchenko, 1845 — translated by John Weir',
    dedPoem: `When I am dead, bury me<br/>
In my beloved Ukraine,<br/>
My tomb upon a grave mound high<br/>
Amid the spreading plain,<br/>
So that the fields, the boundless steppes,<br/>
The Dnieper's plunging shore<br/>
My eyes could see, my ears could hear<br/>
The mighty river roar.<br/><br/>
When from Ukraine the Dnieper bears<br/>
Into the deep blue sea<br/>
The blood of foes … then will I leave<br/>
These hills and fertile fields —<br/>
I'll leave them all and fly away<br/>
To the abode of God,<br/>
And then I'll pray …<br/>
But until that day I know nothing of God.<br/><br/>
Oh bury me, then rise ye up<br/>
And break your heavy chains<br/>
And water with the tyrants' blood<br/>
The freedom you have gained.<br/>
And in the great new family,<br/>
The family of the free,<br/>
With softly spoken, kindly word<br/>
Remember also me.`,

    footerText: 'KubeDojo — Free, comprehensive cloud native education.',
    footerChangelog: 'Changelog',
    footerProgress: 'My Progress',
    licenseText: 'MIT License. Free to use, share, and modify.',
    quoteText: '"In the dojo, everyone starts as a white belt. What matters is showing up to train."',
  },

  uk: {
    lang: 'uk',
    dir: 'ltr',
    prefix: '/uk',
    title: 'KubeDojo — Безкоштовна хмарна освіта',
    description: 'Безкоштовна cloud native освіта: від терміналу й Kubernetes до платформної інженерії, on-prem та AI/ML.',
    canonical: 'https://kube-dojo.github.io/uk/',

    navHome: 'Головна',
    navFundamentals: 'Основи',
    navLinux: 'Linux',
    navCloud: 'Хмара',
    navCertifications: 'Сертифікації',
    navPlatform: 'Платформа',
    navOnPrem: 'On-Premises',
    searchPlaceholder: 'Пошук...',
    langFlag: '🇺🇦 UK',
    langSwitchHref: '/',

    heroBadge: 'Безкоштовний та відкритий код',
    heroUpdated: 'Оновлено 17 квітня 2026',
    heroTitle1: 'Опануйте ',
    heroAccent: 'Cloud Native',
    heroTitle2: 'від нуля до продакшну',
    heroSubtitle: 'Безкоштовна cloud native освіта: від терміналу до продакшн-систем, приватної інфраструктури та local-first AI/ML. Спочатку теорія, завжди практика.',
    ctaStart: 'Почати навчання →',
    ctaWhatsNew: 'Що нового',
    ctaProgress: 'Мій прогрес',
    statModules: 'Модулів',
    statTracks: 'Треків',
    statCerts: 'Модулів K8s-треку',
    statTranslations: 'Українських модулів',

    tracksTitle: 'Навчальні треки',
    tracksDesc: 'Сім структурованих треків від абсолютного початківця до продакшн-систем, приватної інфраструктури та AI/ML.',
    trackFundTitle: 'Основи',
    trackFundDesc: 'Від нуля до терміналу, Cloud Native 101, основи K8s. Починайте тут, якщо ви новачок.',
    trackFundMeta: '📚 47 модулів · ⏱ ~55 год',
    trackLinuxTitle: 'Linux',
    trackLinuxDesc: 'Повсякденне використання + глибоке занурення. Від базових команд до внутрішньої будови ядра.',
    trackLinuxMeta: '📚 37 модулів · ⏱ ~50 год',
    trackCloudTitle: 'Хмара',
    trackCloudDesc: 'Основи AWS, GCP, Azure. Глибоке занурення в EKS/GKE/AKS. Архітектурні патерни.',
    trackCloudMeta: '📚 116 модулів · ⏱ ~150 год',
    trackCertTitle: 'Сертифікації',
    trackCertDesc: 'Базові Kubernetes-сертифікації плюс спеціалізовані та платформні навчальні шляхи.',
    trackCertMeta: '📚 207 модулів · ⏱ ~250 год',
    trackPlatTitle: 'Платформна інженерія',
    trackPlatDesc: 'SRE, GitOps, DevSecOps, MLOps, FinOps, Chaos Engineering. 96 модулів інструментарію.',
    trackPlatMeta: '📚 220 модулів · ⏱ ~280 год',
    trackPremTitle: 'On-Premises',
    trackPremDesc: 'K8s на bare metal від стійки до кластера. Мережі, сховища, операції.',
    trackPremMeta: '📚 59 модулів · ⏱ ~80 год',
    trackAiTitle: 'AI/ML Engineering',
    trackAiDesc: 'Local-first AI, RAG, MLOps, inference, fine-tuning та AI platform-шляхи.',
    trackAiMeta: '📚 117 модулів · ⏱ ~160 год',

    pathTitle: 'Рекомендований шлях',
    pathDesc: 'Не знаєте, з чого почати? Дотримуйтесь цієї послідовності.',
    pathStep1: 'Основи',
    pathStep1Mod: '33 модулі',
    pathStep2: 'Сертифікація CKA',
    pathStep2Mod: '47 модулів',
    pathStep3: 'CKAD + CKS',
    pathStep3Mod: '60 модулів',
    pathStep4: 'Хмара або AI/ML',
    pathStep4Mod: '116 / 117 модулів',
    pathStep5: 'Платформна інженерія',
    pathStep5Mod: '220 модулів',
    pathStep6: 'On-Prem / Спеціалізація',
    pathStep6Mod: '59+ модулів',

    whereTitle: 'З чого почати',
    whereYouAre: 'Ви...',
    whereStart: 'Починайте тут',
    whereRows: [
      ['Ніколи не користувалися терміналом', 'Від нуля до терміналу (починайте тут!)', '/uk/prerequisites/zero-to-terminal/'],
      ['Новачок у контейнерах/K8s', 'Передумови', '/uk/prerequisites/'],
      ['Хочете сертифікацію адміністратора K8s', 'CKA', '/uk/k8s/cka/'],
      ['Хочете сертифікацію розробника K8s', 'CKAD', '/uk/k8s/ckad/'],
      ['Хочете сертифікацію з безпеки K8s', 'CKS', '/uk/k8s/cks/'],
      ['Початкова сертифікація K8s', 'KCNA або KCSA', '/uk/k8s/kcna/'],
      ['Платформний інженер', 'Навчальний шлях CNPE', '/uk/k8s/cnpe/'],
      ['Мультихмарний Kubernetes', 'Хмарний трек (AWS, GCP, Azure)', '/uk/cloud/'],
      ['Будуєте AI-системи або local-first ML-проєкти', 'AI/ML Engineering', '/uk/ai-ml-engineering/'],
      ['Запуск K8s на bare metal', 'Трек On-Premises', '/uk/on-premises/'],
      ['Вже сертифіковані, хочете глибини', 'Платформна інженерія', '/uk/platform/'],
    ],

    philTitle: 'Філософія',
    philBody: "<strong>Теорія перед практикою.</strong> Не можна діагностувати те, чого не розумієш. <strong>Принципи важливіші за інструменти.</strong> Інструменти змінюються — фундамент залишається. <strong>Без зубріння.</strong> Документація K8s доступна під час іспитів — ми вчимо навігації, а не запам'ятовуванню YAML.",
    philBody2: 'KubeDojo — безкоштовний, з відкритим кодом, текстовий. Для симуляції іспитів використовуйте <a href="https://killer.sh">killer.sh</a>. Для інтерактивних лабораторій — <a href="https://killercoda.com">killercoda.com</a>.',

    contribTitle: 'Як долучитися',
    contribBody: 'Ми вітаємо практичні вправи, історії з продакшну, глибокі огляди інструментів та виправлення помилок. Відкрийте issue для обговорення перед великими PR, дотримуйтесь структури модулів та перевіряйте всі команди й YAML перед надсиланням.',

    dedTitle: '🇺🇦 Присвята',
    dedBody1: "Цей проєкт присвячений українським IT-інженерам, які віддали життя, захищаючи Батьківщину. Вони були розробниками, DevOps-інженерами, системними адміністраторами. Вони будували системи, писали код, підтримували інфраструктуру. Коли прийшла війна, вони залишили клавіатури й узяли до рук зброю.",
    dedBody2: 'Їхній код живе далі. Їхня жертва не забута. Слава Україні.',
    dedPoemTitle: 'Заповіт',
    dedPoemAuthor: 'Тарас Шевченко, 1845',
    dedPoem: `Як умру, то поховайте<br/>
Мене на могилі,<br/>
Серед степу широкого,<br/>
На Вкраїні милій,<br/>
Щоб лани широкополі,<br/>
І Дніпро, і кручі<br/>
Було видно, було чути,<br/>
Як реве ревучий.<br/><br/>
Як понесе з України<br/>
У синєє море<br/>
Кров ворожу... отоді я<br/>
І лани і гори —<br/>
Все покину і полину<br/>
До самого Бога<br/>
Молитися... а до того<br/>
Я не знаю Бога.<br/><br/>
Поховайте та вставайте,<br/>
Кайдани порвіте<br/>
І вражою злою кров'ю<br/>
Волю окропіте.<br/>
І мене в сем'ї великій,<br/>
В сем'ї вольній, новій,<br/>
Не забудьте пом'янути<br/>
Незлим тихим словом.`,

    footerText: 'KubeDojo — Безкоштовна, всеосяжна хмарна освіта.',
    footerChangelog: 'Журнал змін',
    footerProgress: 'Мій прогрес',
    licenseText: 'Ліцензія MIT. Вільне використання, поширення та модифікація.',
    quoteText: '"У доджо кожен починає як білий пояс. Головне — приходити на тренування."',
  },
};
