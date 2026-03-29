---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1: \u0429\u043e \u0442\u0430\u043a\u0435 \u043a\u043e\u043d\u0442\u0435\u0439\u043d\u0435\u0440\u0438?"
sidebar:
  order: 2
---
> **Складність**: `[QUICK]` — базові концепції
>
> **Час на виконання**: 30–35 хвилин
>
> **Передумови**: Немає

---

## Чому цей модуль важливий

Контейнери — це будівельні блоки сучасного розгортання застосунків. Перш ніж зрозуміти Kubernetes (оркестратор контейнерів), потрібно зрозуміти, що таке контейнери і які проблеми вони розв'язують.

Тут ідеться не про заучування технічних деталей, а про розуміння «чому» — і саме воно робить зрозумілим усе інше.

---

## Проблема, яку розв'язують контейнери

### Класична проблема розгортання

```
Developer: "It works on my machine!"
Operations: "But it doesn't work in production."
Developer: "My machine has Python 3.9, the right libraries, correct paths..."
Operations: "Production has Python 3.7, different libraries, different paths..."
Everyone: 😤
```

Це **проблема узгодженості середовища**. Застосунки залежать від:
- Версії операційної системи
- Версій середовищ виконання (Python, Node, Java)
- Версій бібліотек
- Файлів конфігурації
- Змінних середовища
- Шляхів до файлів

Коли будь-що з цього відрізняється між розробкою та продакшеном — щось ламається.

### Традиційні рішення (що не масштабувалися)

**Рішення 1: Детальна документація**
```
README.md:
1. Install Python 3.9.7
2. Run `pip install -r requirements.txt`
3. Set environment variables...
4. Configure paths...
(Nobody reads this. When they do, it's outdated.)
```

**Рішення 2: Віртуальні машини**
```
Ship the entire operating system:
- Works consistently
- But 10GB+ per application
- Minutes to start
- Heavy resource usage
- Hard to manage at scale
```

### Контейнерне рішення

```
What if we could package:
- The application
- Its dependencies
- Its configuration
- Everything it needs to run

Into a lightweight, portable unit that runs the same everywhere?

That's a container.
```

---

## Контейнери проти віртуальних машин

```
┌─────────────────────────────────────────────────────────────┐
│              VMs vs CONTAINERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VIRTUAL MACHINES                 CONTAINERS                │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │ App A │ App B │ App C│         │ App A │ App B │ App C│   │
│  ├───────┼───────┼──────┤         ├───────┼───────┼──────┤   │
│  │Guest  │Guest  │Guest │         │Container Runtime     │   │
│  │OS     │OS     │OS    │         │(containerd)          │   │
│  ├───────┴───────┴──────┤         ├──────────────────────┤   │
│  │    Hypervisor        │         │    Host OS           │   │
│  ├──────────────────────┤         ├──────────────────────┤   │
│  │    Host OS           │         │    Hardware          │   │
│  ├──────────────────────┤         └──────────────────────┘   │
│  │    Hardware          │                                    │
│  └──────────────────────┘                                    │
│                                                             │
│  Each VM: Full OS copy            Containers: Share host OS │
│  Size: Gigabytes                  Size: Megabytes           │
│  Start: Minutes                   Start: Seconds            │
│  Isolation: Hardware-level        Isolation: Process-level  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ключові відмінності

| Аспект | Віртуальна машина | Контейнер |
|--------|-------------------|-----------|
| Розмір | Гігабайти | Мегабайти |
| Запуск | Хвилини | Секунди |
| ОС | Повна гостьова ОС на кожну ВМ | Спільне ядро хоста |
| Ізоляція | Апаратна віртуалізація | Ізоляція процесів |
| Портативність | Формати образів ВМ різняться | Універсальні образи контейнерів |
| Щільність | ~10–20 ВМ на сервер | ~сотні контейнерів на сервер |

---

## Як працюють контейнери

Контейнери використовують можливості ядра Linux для створення ізольованих середовищ:

### 1. Простори імен (ізоляція)

Простори імен змушують процес вважати, що він має власну систему:

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX NAMESPACES                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Namespace    What It Isolates                              │
│  ─────────────────────────────────────────────────────────  │
│  PID          Process IDs (container sees PID 1)           │
│  NET          Network interfaces, IPs, ports               │
│  MNT          Filesystem mounts                             │
│  UTS          Hostname and domain                           │
│  IPC          Inter-process communication                   │
│  USER         User and group IDs                            │
│                                                             │
│  Result: Process thinks it's alone on the system            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Контрольні групи (обмеження ресурсів)

cgroups обмежують, скільки ресурсів може використовувати контейнер:

```
Container A: max 512MB RAM, 0.5 CPU
Container B: max 1GB RAM, 1 CPU
Container C: max 256MB RAM, 0.25 CPU

Each container is limited, can't starve others
```

### 3. Об'єднані файлові системи (шаруваті образи)

Образи контейнерів будуються пошарово:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER IMAGE LAYERS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────┐  ← Your app code  │
│  │ Layer 4: COPY app.py /app           │     (tiny)        │
│  ├─────────────────────────────────────┤                   │
│  │ Layer 3: pip install flask          │  ← Dependencies   │
│  ├─────────────────────────────────────┤     (cached)      │
│  │ Layer 2: apt-get install python3    │  ← Runtime        │
│  ├─────────────────────────────────────┤     (cached)      │
│  │ Layer 1: Ubuntu 22.04 base          │  ← Base OS        │
│  └─────────────────────────────────────┘     (shared)      │
│                                                             │
│  Benefits:                                                  │
│  - Layers are shared between images                        │
│  - Only changed layers need rebuilding                     │
│  - Efficient storage and transfer                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Образи контейнерів і реєстри

### Що таке образ контейнера?

Образ контейнера — це шаблон лише для читання, що містить:
- Мінімальну операційну систему (часто Alpine Linux, ~5 МБ)
- Код вашого застосунку
- Залежності (бібліотеки, середовища виконання)
- Конфігурацію

Уявіть це як **клас** у програмуванні — це креслення.

### Що таке контейнер?

Контейнер — це **запущений екземпляр** образу.

Уявіть це як **об'єкт** — це <!-- VERIFY: інстанціювання --> створення екземпляра.

```
Image → Container
(Class → Object)
(Blueprint → Building)
(Recipe → Meal)
```

### Реєстри контейнерів

Образи зберігаються в реєстрах:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER REGISTRIES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Public Registries:                                        │
│  ┌────────────────────────────────────────────┐            │
│  │ Docker Hub        hub.docker.com           │            │
│  │ GitHub Container  ghcr.io                  │            │
│  │ Quay.io          quay.io                   │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
│  Cloud Registries:                                         │
│  ┌────────────────────────────────────────────┐            │
│  │ AWS ECR          *.dkr.ecr.*.amazonaws.com │            │
│  │ Google GCR       gcr.io                    │            │
│  │ Azure ACR        *.azurecr.io              │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
│  Usage:                                                     │
│  docker pull nginx              # From Docker Hub          │
│  docker pull gcr.io/project/app # From Google              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Іменування образів

Образи контейнерів мають певний формат найменування:

```
[registry/][namespace/]repository[:tag]

Examples:
nginx                           # Docker Hub, library/nginx:latest
nginx:1.25                      # Docker Hub, specific version
mycompany/myapp:v1.0.0         # Docker Hub, custom namespace
gcr.io/myproject/myapp:latest  # Google Container Registry
ghcr.io/username/app:sha-abc123 # GitHub Container Registry
```

### Теги важливі

```
nginx:latest     # Whatever is newest (unpredictable!)
nginx:1.25       # Specific version (better)
nginx:1.25.3     # Exact version (best for production)

Rule: Never use :latest in production
```

---

## Чи знали ви?

- **Контейнери — не новинка.** Unix мав chroot ще в 1979 році. FreeBSD Jails з'явилися в 2000-му. Linux Containers (LXC) — у 2008-му. Docker просто зробив це доступним (2013).

- **Більшість контейнерів використовують Alpine Linux** як базу. Він важить лише 5 МБ. Порівняйте з Ubuntu (~70 МБ) або повною ВМ (гігабайти).

- **Образи контейнерів незмінні.** Після збірки вони ніколи не змінюються. Це ключ до відтворюваності.

- **Кита Docker** звуть Moby Dock. Кит несе контейнери (морські контейнери) на спині.

---

## Поширені хибні уявлення

| Хибне уявлення | Реальність |
|----------------|------------|
| «Контейнери — це легкі ВМ» | Контейнери використовують спільне ядро хоста. ВМ мають власне ядро. Принципово різні речі. |
| «Контейнери менш безпечні» | Інша модель загроз, не гірша. Правильно налаштовані контейнери дуже безпечні. |
| «Docker дорівнює контейнерам» | Docker популяризував контейнери, але це не єдиний варіант. containerd, CRI-O, Podman теж працюють. |
| «Контейнери повністю замінюють ВМ» | ВМ й досі цінні для різних ядер ОС, сильної ізоляції, застарілих застосунків. |

---

## Аналогія: морські контейнери

Назва «контейнер» походить від морських контейнерів:

```
Before Shipping Containers (1950s):
- Each product packed differently
- Manual loading/unloading
- Products damaged in transit
- Ships specialized for cargo types
- Slow, expensive, unreliable

After Shipping Containers:
- Standard size for everything
- Automated loading/unloading
- Protected contents
- Any ship can carry any container
- Fast, cheap, reliable

Software Containers:
- Standard format for any application
- Automated deployment
- Protected from environment differences
- Runs anywhere containers run
- Fast, portable, reliable
```

---

## Тест

1. **Яку проблему насамперед розв'язують контейнери?**
   <details>
   <summary>Відповідь</summary>
   Узгодженість середовища — забезпечення однакової роботи застосунків у середовищах розробки, тестування та продакшену. «Воно працює на моїй машині» стає «воно працює в контейнері».
   </details>

2. **Яка ключова різниця між контейнером і віртуальною машиною?**
   <details>
   <summary>Відповідь</summary>
   Контейнери використовують спільне ядро операційної системи хоста, тоді як ВМ мають власну гостьову ОС. Це робить контейнери значно меншими (МБ проти ГБ), швидшими для запуску (секунди проти хвилин) і ефективнішими (вища щільність на сервер).
   </details>

3. **Які дві можливості ядра Linux забезпечують роботу контейнерів?**
   <details>
   <summary>Відповідь</summary>
   Простори імен (для ізоляції — змушують процеси думати, що вони мають власну систему) і контрольні групи/cgroups (для обмеження ресурсів — контролю ЦП, пам'яті тощо).
   </details>

4. **Яка різниця між образом контейнера і контейнером?**
   <details>
   <summary>Відповідь</summary>
   Образ — це шаблон лише для читання (як клас або креслення). Контейнер — це запущений екземпляр образу (як об'єкт або будівля). З одного образу можна запустити кілька контейнерів.
   </details>

---

## Практична вправа

**Завдання**: Дослідити ізоляцію контейнерів (якщо у вас встановлено Docker).

```bash
# 1. Run a container and explore its isolated view
docker run -it --rm alpine sh

# Inside the container, you'll see:
# - PID 1 is your shell (isolated PID namespace)
# - Only the container's filesystem (isolated mount namespace)
# - Its own hostname (isolated UTS namespace)

# Check processes - you only see container processes
ps aux

# Check hostname
hostname

# Check filesystem
ls /

# Exit the container
exit

# 2. Compare with your host
# On your host, run:
ps aux | wc -l    # Hundreds/thousands of processes
hostname          # Your machine's name
ls /              # Full host filesystem

# 3. See the container from outside
# In one terminal, run a container:
docker run -it --rm --name mycontainer alpine sleep 1000

# In another terminal, see it from host perspective:
docker exec mycontainer ps aux  # Limited view inside
ps aux | grep sleep             # Visible from host!

# The container thinks it's alone, but it's just isolated.
```

**Критерій успіху**: Зрозуміти, що контейнери забезпечують ізоляцію, а не віртуалізацію — процеси все одно працюють на ядрі хоста.

---

## Підсумок

Контейнери розв'язують проблему узгодженості середовища, пакуючи:
- Код застосунку
- Залежності
- Конфігурацію
- Усе необхідне для роботи

Вони досягають цього за допомогою:
- **Просторів імен**: ізоляція процесів
- **Контрольних груп**: обмеження ресурсів
- **Об'єднаних файлових систем**: ефективні шаруваті образи

Контейнери:
- **Легкі**: мегабайти, а не гігабайти
- **Швидкі**: секунди для запуску, а не хвилини
- **Портативні**: працюють скрізь, де працюють контейнери
- **Незмінні**: зібрані одного разу, не змінюються

---

## Наступний модуль

[Модуль 2: Основи Docker](module-1.2-docker-fundamentals/) — практична робота зі збіркою та запуском контейнерів.
