# Модуль 0.3: Vim для YAML

> **Складність**: `[QUICK]` — Вивчіть 10 команд, використовуйте їх завжди
>
> **Час на виконання**: 20-30 хвилин
>
> **Передумови**: Немає (Vim попередньо встановлений на екзаменаційних системах)

---

## Чому цей модуль важливий

Іспит CKA вимагає редагування YAML-файлів. Багато. Ви будете створювати маніфести, виправляти зламані конфіги та модифікувати наявні ресурси — все в терміналі.

Екзаменаційне середовище за замовчуванням використовує **nano** (станом на 2025), але ви можете перемкнутися на vim. Незалежно від того, чи використовуєте ви vim чи nano, вам потрібно бути швидким. Цей модуль охоплює vim, оскільки він потужніший, коли ви знаєте основи.

Якщо вам більше подобається nano — це нормально, він простіший. Але навички vim стануть у пригоді при роботі з продакшном, де nano може бути недоступний.

---

## Частина 1: Набір виживання у Vim

Вам не потрібно бути експертом у vim. Вам потрібні 10 команд.

### 1.1 Режими

Vim має режими. Це спочатку бентежить усіх.

> **Аналогія з коробкою передач**
>
> Режими vim — це як коробка передач автомобіля. У **Звичайному режимі** (рух) ви навігуєте — рухаєтесь, не друкуєте. У **Режимі вставки** (парковка) ви стоїте на місці та друкуєте. У **Командному режимі** (задній хід) ви виконуєте спеціальні операції, як-от збереження. Ви ж не паркуєтесь під час руху. Vim змушує вас свідомо "перемикати передачі". Спочатку це виглядає дивно, але саме це робить vim таким швидким, коли ви це засвоїте.

| Режим | Як увійти | Що робить |
|-------|-----------|-----------|
| Звичайний | `Esc` | Навігація, видалення, копіювання, вставка |
| Вставка | `i`, `a`, `o` | Введення тексту |
| Командний | `:` | Збереження, вихід, пошук |

**Правило**: Коли заплуталися, натисніть `Esc`, щоб повернутися до Звичайного режиму.

### 1.2 Основні команди

```
ВХІД У РЕЖИМ ВСТАВКИ
i     Вставити перед курсором
a     Вставити після курсора
o     Відкрити новий рядок нижче та вставити
O     Відкрити новий рядок вище та вставити

НАВІГАЦІЯ (Звичайний режим)
h     Ліворуч
j     Вниз
k     Вгору
l     Праворуч
gg    Перейти до першого рядка
G     Перейти до останнього рядка
0     Перейти на початок рядка
$     Перейти в кінець рядка
w     Стрибнути вперед на одне слово
b     Стрибнути назад на одне слово

РЕДАГУВАННЯ (Звичайний режим)
x     Видалити символ під курсором
dd    Видалити весь рядок
yy    Копіювати (yank) весь рядок
p     Вставити нижче
P     Вставити вище
u     Скасувати
Ctrl+r  Повторити

ПОШУК
/pattern    Шукати вперед
n           Наступний збіг
N           Попередній збіг

ЗБЕРЕЖЕННЯ ТА ВИХІД
:w          Зберегти (write)
:q          Вийти
:wq         Зберегти та вийти
:q!         Вийти без збереження (відкинути зміни)
```

### 1.3 Мінімум, який вам потрібен

Чесно? Для іспиту ви можете обійтися цим:

```
i       → Почати друкувати
Esc     → Припинити друкувати
:wq     → Зберегти та вийти
dd      → Видалити рядок
u       → Скасувати помилку
```

Це 5 речей. Освойте їх, і ви не провалите іспит через vim.

---

## Частина 2: Налаштування Vim для YAML

### 2.1 Створення ~/.vimrc

YAML чутливий до пробілів. Неправильно налаштований vim зіпсує ваші відступи.

```bash
cat << 'EOF' > ~/.vimrc
" Basic settings
set number              " Show line numbers
set tabstop=2           " Tab = 2 spaces
set shiftwidth=2        " Indent = 2 spaces
set expandtab           " Use spaces, not tabs
set autoindent          " Maintain indentation
set smartindent         " Smart indentation for code
set paste               " Prevent auto-indent on paste (toggle with :set nopaste)

" YAML specific
autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab

" Visual helpers
set cursorline          " Highlight current line
syntax on               " Syntax highlighting
set hlsearch            " Highlight search results
EOF
```

### 2.2 Чому ці налаштування важливі

| Налаштування | Навіщо |
|--------------|--------|
| `tabstop=2` | Kubernetes YAML використовує відступ у 2 пробіли |
| `expandtab` | Перетворює табуляції на пробіли (табуляції ламають YAML) |
| `autoindent` | Нові рядки зберігають відступ |
| `number` | Номери рядків допомагають з повідомленнями про помилки |
| `set paste` | Запобігає проблемам з автовідступом під час вставки |

> **Підводний камінь: Табуляції vs Пробіли**
>
> YAML вимагає послідовних відступів. Один символ табуляції, змішаний з пробілами, зламає ваш маніфест. Завжди використовуйте пробіли. Налаштування `expandtab` автоматично перетворює табуляції на пробіли.

> **Історія з практики: Невидимий символ**
>
> Досвідчений інженер витратив 45 хвилин на з'ясування, чому `kubectl apply` постійно падав з незрозумілою помилкою парсингу YAML. Маніфест виглядав ідеально. Зрештою він запустив `cat -A` на файлі й виявив невидимі символи табуляції, змішані з пробілами — вони з'явилися при копіюванні коду зі сторінки Confluence. Урок: ніколи не довіряйте копіюванню-вставці. Завжди перевіряйте відступи та налаштуйте свій редактор показувати невидимі символи або автоматично перетворювати табуляції.

---

## Частина 3: Робочі процеси редагування YAML

### 3.1 Створення нового файлу

```bash
vim pod.yaml
```

Натисніть `i`, щоб увійти в Режим вставки, потім введіть:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
```

Натисніть `Esc`, потім `:wq`, щоб зберегти та вийти.

### 3.2 Копіювання рядків (швидше, ніж передрукування)

Вам потрібно додати ще один контейнер. Замість того, щоб друкувати з нуля:

1. Перейдіть до блоку контейнера
2. Поставте курсор на `- name: nginx`
3. Натисніть `V` (візуальний рядковий режим)
4. Натисніть `j` двічі, щоб виділити 3 рядки
5. Натисніть `y`, щоб скопіювати (yank)
6. Перейдіть туди, де хочете розмістити новий контейнер
7. Натисніть `p`, щоб вставити

### 3.3 Зміна відступів блоків

Виділили неправильний відступ? Виправте:

1. `V`, щоб увійти у візуальний рядковий режим
2. Виділіть рядки за допомогою `j`/`k`
3. `>`, щоб зсунути праворуч
4. `<`, щоб зсунути ліворуч

Або у Звичайному режимі:
- `>>` зсунути поточний рядок праворуч
- `<<` зсунути поточний рядок ліворуч

### 3.4 Видалення кількох рядків

Потрібно видалити цілу секцію?

1. Перейдіть до початку секції
2. Введіть `5dd`, щоб видалити 5 рядків
3. Або `d}`, щоб видалити до наступного порожнього рядка

### 3.5 Пошук і заміна

Неправильна назва образу по всьому файлу?

```
:%s/nginx:1.19/nginx:1.25/g
```

- `%s` = замінити у всьому файлі
- `/старе/нове/` = шаблон
- `g` = усі входження (не лише перше)

---

## Частина 4: Вставка без спотворення

Коли ви копіюєте YAML з документації та вставляєте у vim, автовідступ може спотворити його.

### Метод 1: Встановити режим вставки

Перед вставкою:
```
:set paste
```

Вставте вміст (зазвичай `Cmd+V` або правий клік).

Після вставки:
```
:set nopaste
```

### Метод 2: Використати термінальну вставку

В екзаменаційному середовищі ви можете вставляти безпосередньо в термінал. Рядок `:set paste` у вашому `.vimrc` допомагає, але будьте уважні.

### Метод 3: Альтернатива — використати `cat`

Якщо вставка через vim проблематична:

```bash
cat << 'EOF' > pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

Це повністю уникає vim для створення файлів.

---

## Частина 5: Картка швидкої довідки

Роздрукуйте це або запам'ятайте:

```
╔════════════════════════════════════════════════════╗
║          КОРОТКА ДОВІДКА VIM ДЛЯ YAML             ║
╠════════════════════════════════════════════════════╣
║ РЕЖИМИ                                            ║
║   Esc       → Звичайний режим (навігація)         ║
║   i         → Режим вставки (друкування)          ║
║   :         → Командний режим (збереження/вихід)  ║
╠════════════════════════════════════════════════════╣
║ ПЕРЕМІЩЕННЯ                                       ║
║   gg        → Початок файлу                       ║
║   G         → Кінець файлу                        ║
║   0         → Початок рядка                       ║
║   $         → Кінець рядка                        ║
║   /pattern  → Пошук                               ║
╠════════════════════════════════════════════════════╣
║ РЕДАГУВАННЯ                                       ║
║   dd        → Видалити рядок                      ║
║   yy        → Копіювати рядок                     ║
║   p         → Вставити нижче                      ║
║   u         → Скасувати                           ║
║   >>        → Відступ праворуч                    ║
║   <<        → Відступ ліворуч                     ║
╠════════════════════════════════════════════════════╣
║ ЗБЕРЕЖЕННЯ/ВИХІД                                  ║
║   :w        → Зберегти                            ║
║   :q        → Вийти                               ║
║   :wq       → Зберегти та вийти                   ║
║   :q!       → Вийти без збереження                ║
╠════════════════════════════════════════════════════╣
║ СПЕЦИФІКА YAML                                    ║
║   :set paste    → Перед вставкою                  ║
║   :set nopaste  → Після вставки                   ║
╚════════════════════════════════════════════════════╝
```

---

## Частина 6: Альтернатива — Nano

Якщо vim здається занадто складним, використовуйте nano. Це тепер редактор за замовчуванням на іспиті.

```bash
nano pod.yaml
```

Nano показує комбінації клавіш внизу:
- `Ctrl+O` = Зберегти (Write Out)
- `Ctrl+X` = Вийти
- `Ctrl+K` = Вирізати рядок
- `Ctrl+U` = Вставити

Для YAML створіть `~/.nanorc`:

```bash
cat << 'EOF' > ~/.nanorc
set tabsize 2
set tabstospaces
set autoindent
set linenumbers
EOF
```

> **Порада для іспиту**
>
> Екзаменаційне середовище (станом на 2025) за замовчуванням використовує nano, але ви можете використовувати vim, якщо бажаєте. Виберіть один і дотримуйтесь його — не витрачайте час на іспиті на дебати щодо редакторів.

---

## Чи знали ви?

- **Vim є на кожному сервері Linux**. Вивчення vim окупиться далеко за межами іспиту — ви будете використовувати його для усунення проблем у продакшні, дебагу контейнерів та скрізь, де GUI недоступний.

- **Творець vim (Bram Moolenaar) помер у 2023 році**. Проєкт продовжує існувати як open-source спільнота. Neovim — популярний сучасний форк.

- **`vimtutor`** вже вбудований. Запустіть `vimtutor` у будь-якому терміналі для інтерактивного посібника з vim. Займає близько 30 хвилин і навчить вас більшому, ніж цей модуль.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Застрягли в режимі вставки | Не вдається навігувати | Натисніть `Esc` |
| Вставлений YAML спотворений | Автовідступ | `:set paste` перед вставкою |
| Символи табуляції в YAML | Синтаксична помилка YAML | Використовуйте `expandtab` у .vimrc |
| Втрачені зміни | Вийшли без збереження | Використовуйте `:wq`, а не `:q!` |
| Неправильні відступи | Парсинг YAML невдалий | `>>` та `<<` для виправлення |

---

## Тест

1. **Як видалити 3 рядки у vim?**
   <details>
   <summary>Відповідь</summary>
   Поставте курсор на перший рядок, введіть `3dd` у Звичайному режимі.
   </details>

2. **Ви вставили YAML, і відступи зламалися. Що сталося і як цьому запобігти?**
   <details>
   <summary>Відповідь</summary>
   Автовідступ vim спотворив вставку. Використовуйте `:set paste` перед вставкою, потім `:set nopaste` після.
   </details>

3. **Яка команда для збереження та виходу з vim?**
   <details>
   <summary>Відповідь</summary>
   `:wq` (write and quit). Або `ZZ` у Звичайному режимі (менш поширений варіант).
   </details>

4. **Чому у YAML потрібно використовувати пробіли замість табуляцій?**
   <details>
   <summary>Відповідь</summary>
   YAML вимагає послідовних відступів. Змішування табуляцій і пробілів (або використання табуляцій, коли парсер очікує пробіли) спричиняє синтаксичні помилки. Маніфести Kubernetes очікують відступ у 2 пробіли.
   </details>

---

## Практична вправа

**Завдання**: Налаштуйте vim і попрактикуйтесь у редагуванні YAML.

**Підготовка**:
```bash
# Create .vimrc with YAML settings
cat << 'EOF' > ~/.vimrc
set number
set tabstop=2
set shiftwidth=2
set expandtab
set autoindent
syntax on
EOF
```

**Практичні завдання**:

1. Створіть маніфест Пода з нуля:
   ```bash
   vim practice-pod.yaml
   # Type a complete Pod manifest
   # Save and exit
   ```

2. Продублюйте блок контейнера:
   - Відкрийте файл
   - Скопіюйте секцію контейнера
   - Вставте та змініть назву

3. Виправте навмисно зламані відступи:
   ```bash
   cat << 'EOF' > broken.yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: test
   spec:
       containers:
         - name: nginx
         image: nginx
   EOF
   # Open in vim and fix indentation
   ```

**Критерії успіху**:
- [ ] Можете створити валідний маніфест Пода у vim
- [ ] Можете копіювати та вставляти блоки всередині vim
- [ ] Можете виправляти проблеми з відступами
- [ ] Знаєте, як зберегти та вийти

**Перевірка**:
```bash
# Validate your YAML
kubectl apply -f practice-pod.yaml --dry-run=client
```

---

## Практичні вправи

### Вправа 1: Тест швидкості Vim (Ціль: 2 хвилини)

Створіть цей маніфест Пода з нуля у vim:

```bash
vim speed-test.yaml
```

Введіть це (не копіюйте-вставляйте):
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

Збережіть і перевірте:
```bash
kubectl apply -f speed-test.yaml --dry-run=client
rm speed-test.yaml
```

### Вправа 2: Виправлення зламаного YAML — Відступи (Ціль: 3 хвилини)

```bash
# Create broken YAML
cat << 'EOF' > broken-indent.yaml
apiVersion: v1
kind: Pod
metadata:
name: broken-pod
  labels:
      app: test
spec:
    containers:
  - name: nginx
      image: nginx
    ports:
        - containerPort: 80
EOF

# Open in vim and fix ALL indentation errors
vim broken-indent.yaml

# Validate your fix
kubectl apply -f broken-indent.yaml --dry-run=client
rm broken-indent.yaml
```

<details>
<summary>Виправлена версія</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod
  labels:
    app: test
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

</details>

### Вправа 3: Виправлення зламаного YAML — Змішані табуляції/пробіли (Ціль: 3 хвилини)

```bash
# Create YAML with hidden tab characters
printf 'apiVersion: v1\nkind: Pod\nmetadata:\n\tname: tab-pod\nspec:\n\tcontainers:\n\t- name: nginx\n\t  image: nginx\n' > broken-tabs.yaml

# Look at it - seems fine visually
cat broken-tabs.yaml

# But kubectl fails!
kubectl apply -f broken-tabs.yaml --dry-run=client

# YOUR TASK: Open in vim and fix
vim broken-tabs.yaml
# Hint: In vim, use :%s/\t/  /g to replace tabs with spaces

kubectl apply -f broken-tabs.yaml --dry-run=client
rm broken-tabs.yaml
```

### Вправа 4: Копіювання та модифікація блоків (Ціль: 2 хвилини)

```bash
# Create a deployment with one container
cat << 'EOF' > multi-container.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 80
EOF

# YOUR TASK in vim:
# 1. Duplicate the container block
# 2. Change second container to: name: sidecar, image: busybox, remove ports
# Target: 2 minutes

vim multi-container.yaml

# Validate
kubectl apply -f multi-container.yaml --dry-run=client
rm multi-container.yaml
```

<details>
<summary>Очікуваний результат</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 80
  - name: sidecar
    image: busybox
```

</details>

### Вправа 5: Пошук і заміна (Ціль: 1 хвилина)

```bash
# Create file with wrong image version
cat << 'EOF' > version-fix.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.19
      - name: log
        image: fluentd:1.19
      - name: cache
        image: redis:1.19
EOF

# YOUR TASK: Change ALL "1.19" to "1.25" using vim search/replace
# Command: :%s/1.19/1.25/g

vim version-fix.yaml

# Verify all changed
grep "1.25" version-fix.yaml  # Should show 3 lines
rm version-fix.yaml
```

### Вправа 6: Виправлення зламаного YAML — Синтаксичні помилки (Ціль: 5 хвилин)

Цей YAML має кілька помилок. Знайдіть і виправте їх усі:

```bash
cat << 'EOF' > broken-syntax.yaml
apiVersion: v1
kind: Pod
metadata:
  name: syntax-errors
  labels:
    app: test
    environment: production  # missing quotes on value with special chars
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DATABASE_URL
      value: postgres://user:p@ssword@db:5432  # @ needs quoting
    - name: DEBUG
      value: true  # boolean should be string
    ports:
    - containerPort: "80"  # should be integer, not string
    resources:
      requests:
        memory: 128Mi  # missing quotes won't break, but...
        cpu: 100  # should be 100m
EOF

vim broken-syntax.yaml

# Test
kubectl apply -f broken-syntax.yaml --dry-run=client
rm broken-syntax.yaml
```

<details>
<summary>Виправлена версія</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: syntax-errors
  labels:
    app: test
    environment: production
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DATABASE_URL
      value: "postgres://user:p@ssword@db:5432"
    - name: DEBUG
      value: "true"
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
```

</details>

### Вправа 7: Випробування — Тест швидкості Nano

Якщо ви надаєте перевагу nano, виконайте Вправу 1 за допомогою nano:

```bash
nano speed-test.yaml
# Ctrl+O to save, Ctrl+X to exit
kubectl apply -f speed-test.yaml --dry-run=client
rm speed-test.yaml
```

Порівняйте свій час з vim. Використовуйте те, що швидше для вас.

---

## Наступний модуль

[Модуль 0.4: Навігація по kubernetes.io](module-0.4-k8s-docs.uk.md) — Як швидко знаходити документацію під час іспиту.
