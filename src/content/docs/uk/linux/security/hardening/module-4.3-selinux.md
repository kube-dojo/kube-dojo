---
title: "Модуль 4.3: Контексти SELinux"
slug: uk/linux/security/hardening/module-4.3-selinux
sidebar:
  order: 4
lab:
  id: "linux-4.3-selinux"
  url: "https://killercoda.com/kubedojo/scenario/linux-4.3-selinux"
  duration: "40 min"
  difficulty: "advanced"
  environment: "ubuntu"
en_commit: bf9159a224c23a4dd04882b23d9e86af3e985c98
---
> **Безпека Linux** | Складність: `[COMPLEX]` | Час: 35–40 хв

## Передумови

Перед початком цього модуля:
- **Обов'язково**: [Модуль 2.3: Capabilities та LSM](/uk/linux/foundations/container-primitives/module-2.3-capabilities-lsms/)
- **Бажано**: Доступ до системи на базі RHEL (CentOS, Rocky Linux, Fedora) для практики.

---

## Що ви зможете робити після цього модуля

Після завершення цього модуля ви зможете:
- **Пояснити** контексти SELinux (user:role:type:level) та як вони контролюють доступ
- **Діагностувати** помилки "Permission denied", спричинені SELinux, за допомогою audit2why та sesearch
- **Налаштувати** SELinux для вузлів Kubernetes (контексти container_t, container_file_t)
- **Обрати** між режимами enforcing, permissive та disabled і пояснити компроміси

---

## Чому цей модуль важливий

**SELinux (Security-Enhanced Linux)** — це система обов'язкового контролю доступу, розроблена в NSA. Вона є стандартом для дистрибутивів сімейства Red Hat. SELinux складніший за AppArmor, але надає набагато глибший та точніший контроль над безпекою.

Розуміння SELinux допоможе вам:

- **Адмініструвати вузли Kubernetes на базі RHEL** — там SELinux увімкнено за замовчуванням.
- **Виправляти складні помилки доступу** — коли права на файли вірні, але "Permission denied" залишається.
- **Скласти іспит CKS** — SELinux тестується нарівні з AppArmor.
- **Зрозуміти ізоляцію контейнерів** — SELinux використовує спеціальні мітки (MCS) для розділення контейнерів.

Порада "просто вимкни SELinux" — найгірша в DevOps. Професіонали вчать, як з ним працювати.

---

## Основні концепції

### Контекст безпеки (Labels)
Кожен файл, процес та мережевий порт має мітку:
`користувач : роль : ТИП : рівень`

Найважливішою частиною є **ТИП** (Type). Більшість правил базуються саме на ньому (Type Enforcement).

### Приклади типів:
- `httpd_t` — для процесів вебсервера.
- `httpd_sys_content_t` — для контенту сайту (html, jpg).
- `container_t` — для процесів у контейнерах.

---

## Режими роботи

```bash
# Перевірити поточний режим
getenforce
# Enforcing  - Блокує та логує (безпечно)
# Permissive - Тільки логує (для дебагу)
# Disabled   - Повністю вимкнено (небезпечно)
```

### Тимчасова зміна режиму:
```bash
sudo setenforce 0  # Перейти в Permissive
sudo setenforce 1  # Повернутися в Enforcing
```

---

## Робота з мітками файлів

```bash
# Переглянути мітки файлів (-Z)
ls -Z /var/www/html

# Тимчасово змінити тип файлу
chcon -t httpd_sys_content_t index.html

# Встановити постійне правило для папки
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/myweb(/.*)?"

# Застосувати правила до файлів
sudo restorecon -Rv /srv/myweb
```

---

## SELinux Booleans

Це "вимикачі" в політиці, які дозволяють або забороняють певні дії без написання складного коду.

```bash
# Список усіх вимикачів
getsebool -a

# Дозволити вебсерверу з'єднуватися з базою даних
sudo setsebool -P httpd_can_network_connect_db on
# -P робить зміну постійною (survives reboot)
```

---

## Вирішення проблем (Troubleshooting)

Якщо ви підозрюєте SELinux, перевірте журнал аудиту:

```bash
# Знайти відмови у доступі (AVC denials)
sudo ausearch -m AVC -ts recent

# Отримати людське пояснення причини відмови
sudo ausearch -m AVC -ts recent | audit2why
```

---

## Тест

1. **Яка команда в Linux показує поточний режим роботи SELinux?**
   <details>
   <summary>Відповідь</summary>
   `getenforce`.
   </details>

2. **Що таке Type Enforcement у SELinux?**
   <details>
   <summary>Відповідь</summary>
   Це основний механізм контролю, який визначає, які дії (читання, запис, виконання) дозволені процесу з певним типом (наприклад, `httpd_t`) над об'єктом іншого типу (наприклад, файлом `httpd_sys_content_t`).
   </details>

3. **Яка різниця між `chcon` та `semanage fcontext`?**
   <details>
   <summary>Відповідь</summary>
   `chcon` змінює мітку файлу "тут і зараз", але вона зникне при перемаркуванні системи (relabel). `semanage fcontext` записує правило в базу даних системи, і воно буде діяти завжди після виконання `restorecon`.
   </details>

4. **Як дозволити конкретну дію, на яку SELinux каже "ні", якщо ви впевнені, що вона безпечна?**
   <details>
   <summary>Відповідь</summary>
   Спочатку перевірити наявність відповідного **Boolean** через `getsebool`. Якщо його немає — використати утиліту `audit2allow` для генерації кастомного модуля політики.
   </details>

---

## Практична вправа

**Завдання**: Змінити контекст файлу та перевірити його.

1. Створіть файл у нетиповому місці:
   ```bash
   touch /tmp/test_file
   ```
2. Перегляньте його початковий контекст:
   ```bash
   ls -Z /tmp/test_file
   ```
3. Змініть його тип на `httpd_sys_content_t`:
   ```bash
   chcon -t httpd_sys_content_t /tmp/test_file
   ```
4. Перевірте, що мітка змінилася:
   ```bash
   ls -Z /tmp/test_file
   ```
5. Поверніть стандартну мітку для цієї папки:
   ```bash
   restorecon -v /tmp/test_file
   ```

**Критерії успіху**: Ви розумієте структуру міток SELinux та вмієте їх змінювати.

---

## Підсумок

- **SELinux** — це безпека на основі міток (labels).
- **Enforcing** — єдиний правильний режим для продакшну.
- **Booleans** — швидкий спосіб змінити поведінку політики.
- **ausearch + audit2why** — ваші головні інструменти діагностики.

---

**Далі**: [Модуль 4.4: Профілі Seccomp](../module-4.4-seccomp/) — дізнайтеся, як фільтрувати системні виклики до ядра для максимального захисту.
