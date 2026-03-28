---
title: "Модуль 3.1: Безпека подів"
slug: uk/k8s/kcsa/part3-security-fundamentals/module-3.1-pod-security
sidebar:
  order: 2
---
> **Складність**: `[СЕРЕДНЯ]` - Основні знання
>
> **Час на виконання**: 30-35 хвилин
>
> **Передумови**: [Модуль 2.4: PKI та сертифікати](../part2-cluster-component-security/module-2.4-pki-certificates/)

---

## Чому цей модуль важливий

Поди - це місце, де працює ваш код. Вони також є місцем, де атакуючі намагаються отримати доступ та підвищити привілеї. Контролі безпеки подів визначають, чи може контейнер вирватися на хост, отримати доступ до чутливих ресурсів або переміщуватися бічно через ваш кластер.

Розуміння SecurityContext та Pod Security Standards є необхідним як для іспиту KCSA, так і для захисту реальних навантажень Kubernetes.

---

## SecurityContext

SecurityContext визначає параметри привілеїв та контролю доступу:

### SecurityContext контейнера

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  containers:
  - name: app
    image: nginx:1.25
    securityContext:
      # НАЛАШТУВАННЯ КОРИСТУВАЧА
      runAsUser: 1000          # Запуск від не-root
      runAsGroup: 1000         # Основна група
      runAsNonRoot: true       # Збій якщо образ від root

      # ФАЙЛОВА СИСТЕМА
      readOnlyRootFilesystem: true  # Запобігти запису

      # ПІДВИЩЕННЯ ПРИВІЛЕЇВ
      allowPrivilegeEscalation: false  # Блокувати setuid/setgid
      privileged: false                 # Не привілейований

      # CAPABILITIES
      capabilities:
        drop:
          - ALL                # Скинути всі capabilities
        add:
          - NET_BIND_SERVICE   # Додати лише потрібні

      # SECCOMP
      seccompProfile:
        type: RuntimeDefault   # Профіль середовища виконання
```

### Ключові поля SecurityContext

| Поле | Призначення | Безпечне значення |
|------|---------|----------------|
| `runAsNonRoot` | Запобігти запуску від root | `true` |
| `runAsUser` | Конкретний ID користувача | Ненульовий (не root) |
| `readOnlyRootFilesystem` | Запобігти запису | `true` |
| `allowPrivilegeEscalation` | Блокувати setuid/setgid | `false` |
| `privileged` | Повний доступ до хоста | `false` |
| `capabilities.drop` | Видалити Linux capabilities | `["ALL"]` |
| `seccompProfile` | Фільтрація системних викликів | `RuntimeDefault` |

---

## Pod Security Standards (PSS)

Pod Security Standards визначають три профілі безпеки:

```
┌─────────────────────────────────────────────────────────────┐
│              СТАНДАРТИ БЕЗПЕКИ ПОДІВ                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVILEGED (Найдозвільніший)                              │
│  ├── Без обмежень                                          │
│  ├── Для: Довірені системні навантаження, CNI, логування   │
│  └── Ризик: Можливий повний доступ до хоста                │
│                                                             │
│  BASELINE (Помірний)                                       │
│  ├── Запобігає відомим підвищенням привілеїв               │
│  ├── Блокує: hostNetwork, hostPID, privileged              │
│  ├── Дозволяє: root-користувач, більшість capabilities     │
│  └── Для: Більшості застосунків                            │
│                                                             │
│  RESTRICTED (Найбезпечніший)                               │
│  ├── Сильно обмежений, слідує найкращим практикам          │
│  ├── Вимагає: не-root, файлову систему лише для читання    │
│  ├── Блокує: Майже все небезпечне                          │
│  └── Для: Навантажень з вимогами безпеки                   │
│                                                             │
│  РЕКОМЕНДАЦІЯ: Почніть з Restricted, послабте за потреби   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Що блокує кожен стандарт

| Контроль | Privileged | Baseline | Restricted |
|---------|-----------|----------|------------|
| hostNetwork | Дозволено | Заблоковано | Заблоковано |
| hostPID | Дозволено | Заблоковано | Заблоковано |
| privileged | Дозволено | Заблоковано | Заблоковано |
| runAsRoot | Дозволено | Дозволено | Заблоковано |
| allowPrivilegeEscalation | Дозволено | Дозволено | Заблоковано |
| seccompProfile | Дозволено | Дозволено | Обов'язково |

---

## Pod Security Admission (PSA)

PSA - вбудований механізм впровадження Pod Security Standards:

### Режими PSA

```
┌─────────────────────────────────────────────────────────────┐
│              РЕЖИМИ ВПРОВАДЖЕННЯ PSA                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENFORCE                                                   │
│  • Блокує поди, що порушують стандарт                      │
│  • Створення поду не вдається                              │
│  • Для: Впровадження на продакшн                           │
│                                                             │
│  AUDIT                                                     │
│  • Логує порушення, але дозволяє створення поду            │
│  • Записує в лог аудиту                                    │
│  • Для: Виявлення порушень перед впровадженням             │
│                                                             │
│  WARN                                                      │
│  • Показує попередження, але дозволяє створення поду       │
│  • Попередження у відповіді API                            │
│  • Для: Навчання розробників                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Налаштування PSA

PSA налаштовується через мітки простору імен:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

---

## Чи знали ви?

- **Pod Security Admission замінив PodSecurityPolicy** (PSP), який було видалено у 1.25. PSA простіший, але менш гнучкий.

- **Стандарт restricted PSS** базується на CIS Benchmark та практиках зміцнення. Його дотримання значно зменшує поверхню атаки.

- **allowPrivilegeEscalation: false** запобігає роботі бінарних файлів setuid. Тому деякі контейнери, що працюють від root, ламаються з цим налаштуванням.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Запуск від root | Вищий привілей при компрометації | runAsNonRoot: true |
| Не скидати capabilities | Більше привілеїв ніж потрібно | capabilities.drop: ["ALL"] |
| privileged: true | Повний доступ до хоста | Конкретні capabilities замість |
| Файлова система для запису | Атакуючий може зберігати зміни | readOnlyRootFilesystem: true |
| Без профілю seccomp | Всі системні виклики доступні | type: RuntimeDefault |

---

## Тест

1. **Яка різниця між runAsNonRoot та runAsUser?**
   <details>
   <summary>Відповідь</summary>
   runAsNonRoot - булеве значення, що змушує контейнер не запускатися, якщо образ працюватиме від root (UID 0). runAsUser явно встановлює UID. Вони працюють разом - runAsUser: 1000 встановлює UID, runAsNonRoot: true перевіряє, що він не 0.
   </details>

2. **Що запобігає allowPrivilegeEscalation: false?**
   <details>
   <summary>Відповідь</summary>
   Запобігає процесам отримувати більше привілеїв, ніж батьківський, блокуючи роботу бінарних файлів setuid та setgid. Це зупиняє поширені техніки підвищення привілеїв.
   </details>

3. **Який Pod Security Standard підходить для більшості продакшн-застосунків?**
   <details>
   <summary>Відповідь</summary>
   Baseline для більшості застосунків (запобігає відомим підвищенням привілеїв), Restricted для навантажень з вимогами безпеки. Починайте з Restricted та послаблюйте за потреби.
   </details>

4. **Яка різниця між режимами PSA enforce, warn та audit?**
   <details>
   <summary>Відповідь</summary>
   Enforce блокує невідповідні поди. Warn дозволяє під, але показує попередження. Audit дозволяє під, але логує порушення. Можна використовувати різні режими на різних рівнях.
   </details>

5. **Чому privileged: true небезпечний?**
   <details>
   <summary>Відповідь</summary>
   Він надає контейнеру всі Linux capabilities та доступ до всіх пристроїв хоста. Скомпрометований привілейований контейнер може монтувати файлову систему хоста, отримати доступ до всіх ресурсів хоста та фактично має root-доступ до хоста.
   </details>

---

## Підсумок

Безпека подів - це обмеження того, що контейнери можуть робити:

| Контроль | Призначення | Безпечне значення |
|---------|---------|----------------|
| **runAsNonRoot** | Запобігти root | `true` |
| **readOnlyRootFilesystem** | Запобігти запису | `true` |
| **allowPrivilegeEscalation** | Блокувати setuid | `false` |
| **privileged** | Блокувати доступ до хоста | `false` |
| **capabilities** | Обмежити привілеї | `drop: ["ALL"]` |
| **seccompProfile** | Фільтрація syscalls | `RuntimeDefault` |

Pod Security Standards:
- **Privileged**: Без обмежень (системні навантаження)
- **Baseline**: Запобігає відомим підвищенням привілеїв
- **Restricted**: Сильно зміцнений, найкраща практика

---

## Наступний модуль

[Модуль 3.2: Основи RBAC](module-3.2-rbac/) - Контроль доступу на основі ролей для авторизації Kubernetes.
