# Сертифікації Kubernetes

**Шлях до Kubestronaut** — усі 5 сертифікацій, необхідних для отримання статусу [Kubestronaut](https://www.cncf.io/training/kubestronaut/).

---

## Огляд

```
                        ШЛЯХ ДО KUBESTRONAUT
    ════════════════════════════════════════════════════════

    ПОЧАТКОВИЙ РІВЕНЬ (тестові запитання, 90 хв)
    ┌──────────────────────────────────────────────────────┐
    │  KCNA   Kubernetes & Cloud Native Associate          │
    │         └── Концептуальне розуміння K8s та CNCF      │
    │                                                      │
    │  KCSA   Kubernetes & Cloud Native Security Associate │
    │         └── Концепції безпеки та моделювання загроз  │
    └──────────────────────────────────────────────────────┘
                             │
                             ▼
    РІВЕНЬ ПРАКТИКА (практична лабораторна, 2 години)
    ┌──────────────────────────────────────────────────────┐
    │  CKAD   Certified Kubernetes Application Developer   │
    │         └── Створення та розгортання застосунків     │
    │                                                      │
    │  CKA    Certified Kubernetes Administrator           │
    │         └── Встановлення, налаштування, керування    │
    │              кластерами                              │
    │                                                      │
    │  CKS    Certified Kubernetes Security Specialist     │
    │         └── Наскрізний захист кластерів (потрібен CKA)│
    └──────────────────────────────────────────────────────┘

    ════════════════════════════════════════════════════════
```

---

## Сертифікації

| Серт. | Назва | Тип | Модулі | Програма |
|-------|-------|-----|--------|----------|
| [KCNA](kcna/) | Kubernetes & Cloud Native Associate | Тестові запитання | 21 | [Детальніше](kcna/README.md) |
| [KCSA](kcsa/) | Security Associate | Тестові запитання | 25 | [Детальніше](kcsa/README.md) |
| [CKAD](ckad/) | Application Developer | Практична лабораторна | 28 | [Детальніше](ckad/) |
| [CKA](cka/) | Administrator | Практична лабораторна | 38 | [Детальніше](cka/) |
| [CKS](cks/) | Security Specialist | Практична лабораторна | 30 | [Детальніше](cks/) |
| | **Разом** | | **142** | |

---

## Рекомендований порядок

**Варіант 1: Спочатку широта** (зрозуміти загальну картину)
```
KCNA → KCSA → CKAD → CKA → CKS
```

**Варіант 2: Спочатку глибина** (фокус на адмініструванні)
```
CKA → CKAD → CKS → KCNA → KCSA
```

**Варіант 3: Шлях розробника**
```
KCNA → CKAD → (зупинитися тут або продовжити до CKA)
```

**Варіант 4: Шлях безпеки**
```
CKA → CKS → KCSA
```

---

## Поради до іспитів

Усі іспити мають спільні характеристики:
- **Прокторинг PSI Bridge** — суворі умови, потрібна вебкамера
- **kubernetes.io дозволено** — офіційна документація — ваш найкращий друг
- **Обмежений час** — швидкість важлива не менше, ніж знання

Для практичних іспитів (CKAD, CKA, CKS):
- Тренуйтеся з `kubectl`, доки це не стане звичкою
- Опануйте vim/nano для редагування YAML
- Використовуйте `kubectl explain` та `--dry-run=client -o yaml`
- [killer.sh](https://killer.sh) входить до вартості іспиту — скористайтеся цим

---

## Джерела програм

Ми відстежуємо офіційні програми CNCF:
- [CNCF Curriculum Repository](https://github.com/cncf/curriculum)
- [CKA Program Changes](https://training.linuxfoundation.org/certified-kubernetes-administrator-cka-program-changes/)
- [CKS Program Changes](https://training.linuxfoundation.org/cks-program-changes/)
