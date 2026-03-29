---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2: \u041e\u0441\u043d\u043e\u0432\u0438 Docker"
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — потрібна практична робота
>
> **Час на виконання**: 45–50 хвилин
>
> **Передумови**: Модуль 1 (Що таке контейнери?)

---

## Чому цей модуль важливий

Docker — найпоширеніший інструмент для збірки образів контейнерів. Хоча Kubernetes більше не використовує Docker як середовище виконання, Docker залишається стандартом для:
- Збірки образів контейнерів
- Локальної розробки
- Тестування та зневадження <!-- VERIFY: зневадження (= debugging) -->

Вам потрібно «достатньо» Docker, щоб зрозуміти Kubernetes — не повне володіння Docker.

---

## Встановлення Docker

### macOS
```bash
# Install Docker Desktop
# Download from https://docker.com/products/docker-desktop
# Or use Homebrew:
brew install --cask docker
```

### Linux (Ubuntu/Debian)
```bash
# Official installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

### Перевірка встановлення
```bash
docker --version
# Docker version 24.x.x, build xxxxx

docker run hello-world
# Should show "Hello from Docker!" message
```

---

## Ваш перший контейнер

```bash
# Run nginx (a web server)
docker run -d -p 8080:80 nginx

# What happened:
# - Pulled nginx image from Docker Hub
# - Created a container from the image
# - Started the container in detached mode (-d)
# - Mapped port 8080 (host) to port 80 (container)
```

```bash
# Test it
curl http://localhost:8080
# Returns nginx welcome page HTML

# View running containers
docker ps
# CONTAINER ID  IMAGE  COMMAND                 STATUS         PORTS                  NAMES
# a1b2c3d4e5f6  nginx  "/docker-entrypoint.…"  Up 10 seconds  0.0.0.0:8080->80/tcp   tender_tesla

# Stop the container
docker stop a1b2c3d4e5f6

# Remove the container
docker rm a1b2c3d4e5f6
```

---

## Основні команди Docker

### Життєвий цикл контейнера

```bash
# Run a container
docker run [OPTIONS] IMAGE [COMMAND]

# Common options:
docker run -d nginx                    # Detached (background)
docker run -it ubuntu bash             # Interactive terminal
docker run -p 8080:80 nginx           # Port mapping
docker run -v /host/path:/container/path nginx  # Volume mount
docker run --name myapp nginx         # Named container
docker run -e MY_VAR=value nginx      # Environment variable
docker run --rm nginx                 # Remove when stopped

# Container management
docker ps                              # List running containers
docker ps -a                           # List all containers
docker stop CONTAINER                  # Stop gracefully
docker kill CONTAINER                  # Force stop
docker rm CONTAINER                    # Remove stopped container
docker rm -f CONTAINER                 # Force remove (stop + rm)
```

### Інспектування контейнерів

```bash
# View logs
docker logs CONTAINER
docker logs -f CONTAINER               # Follow (tail)
docker logs --tail 100 CONTAINER       # Last 100 lines

# Execute command in running container
docker exec -it CONTAINER bash         # Interactive shell
docker exec CONTAINER ls /app          # Run command

# Inspect container details
docker inspect CONTAINER               # Full JSON details
docker stats                           # Resource usage
docker top CONTAINER                   # Running processes
```

### Керування образами

```bash
# Pull images
docker pull nginx
docker pull nginx:1.25
docker pull gcr.io/project/image:tag

# List images
docker images

# Remove images
docker rmi nginx
docker image prune                     # Remove unused images

# Build images (we'll cover this next)
docker build -t myapp:v1 .
```

---

## Збірка образів контейнерів

### Dockerfile

Dockerfile — це текстовий файл з інструкціями для збірки образу:

```dockerfile
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (documentation)
EXPOSE 8000

# Default command
CMD ["python", "app.py"]
```

### Збірка та запуск

```bash
# Build image
docker build -t myapp:v1 .

# Run container from image
docker run -d -p 8000:8000 myapp:v1
```

### Інструкції Dockerfile

| Інструкція | Призначення |
|------------|-------------|
| `FROM` | Базовий образ, на основі якого будується |
| `WORKDIR` | Встановити робочу директорію |
| `COPY` | Скопіювати файли з хоста до образу |
| `ADD` | Як COPY, але може розпаковувати архіви та завантажувати за URL |
| `RUN` | Виконати команду під час збірки |
| `ENV` | Встановити змінну середовища |
| `EXPOSE` | Задокументувати, який порт використовує застосунок |
| `CMD` | Типова команда при запуску контейнера |
| `ENTRYPOINT` | Команда, що завжди виконується (CMD стає аргументами) |

---

## Практичний приклад: вебзастосунок на Python

Створіть простий застосунок на Python:

**app.py**
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    name = os.getenv('NAME', 'World')
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

**requirements.txt**
```
flask==3.0.0
```

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

EXPOSE 8000

CMD ["python", "app.py"]
```

**Збірка та запуск**
```bash
# Build
docker build -t hello-flask:v1 .

# Run
docker run -d -p 8000:8000 -e NAME=Docker hello-flask:v1

# Test
curl http://localhost:8000
# Hello, Docker!

# Cleanup
docker rm -f $(docker ps -q --filter ancestor=hello-flask:v1)
```

---

## Кешування шарів

Docker кешує шари для пришвидшення збірок. Порядок має значення:

```dockerfile
# BAD: Code changes invalidate dependency cache
FROM python:3.11-slim
WORKDIR /app
COPY . .                              # Any change busts cache
RUN pip install -r requirements.txt   # Reinstalls every time!
CMD ["python", "app.py"]

# GOOD: Dependencies cached separately
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .               # Only changes when deps change
RUN pip install -r requirements.txt   # Cached unless deps change
COPY . .                              # App changes don't bust pip cache
CMD ["python", "app.py"]
```

---

## Docker Compose (локальна робота з кількома контейнерами)

Для локальної розробки з кількома сервісами:

**docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_PASSWORD=secret
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

**Примітка**: Docker Compose призначений для локальної розробки. Для продакшену його замінює Kubernetes.

---

## Візуалізація: робочий процес Docker

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER WORKFLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. WRITE                                                   │
│     ┌─────────────┐                                        │
│     │ Dockerfile  │                                        │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  2. BUILD                                                   │
│     ┌─────────────┐                                        │
│     │docker build │──────► Image (myapp:v1)                │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  3. PUSH (optional)                                        │
│     ┌─────────────┐                                        │
│     │docker push  │──────► Registry (Docker Hub, ECR...)   │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  4. RUN                                                     │
│     ┌─────────────┐                                        │
│     │docker run   │──────► Container (running instance)    │
│     └─────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Найкращі практики

### Розмір образу

```dockerfile
# BAD: Full OS, huge image
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . .
RUN pip3 install -r requirements.txt

# GOOD: Slim base, smaller image
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# BETTER: Alpine (tiny base)
FROM python:3.11-alpine
# Note: Alpine uses apk, not apt, and musl instead of glibc
```

### Безпека

```dockerfile
# BAD: Running as root
FROM python:3.11-slim
COPY . .
CMD ["python", "app.py"]  # Runs as root!

# GOOD: Non-root user
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "app.py"]
```

### Один процес на контейнер

```
# BAD: Multiple services in one container
Container: nginx + python app + redis

# GOOD: Separate containers
Container 1: nginx
Container 2: python app
Container 3: redis
(Use Docker Compose or Kubernetes to orchestrate)
```

---

## Чи знали ви?

- **Образи Docker адресуються за вмістом.** SHA256-хеш образу — це його справжній ідентифікатор. Теги — лише зрозумілі людині псевдоніми.

- **Багатоетапна збірка різко зменшує розмір образу.** Збирайте на одному етапі, копіюйте лише артефакти до фінального етапу.

- **Тег `latest` не є особливим.** Docker не оновлює його автоматично. Це просто домовленість, що означає «те, що було завантажено останнім».

- **Docker Desktop — це не Docker.** Docker (інструмент) безкоштовний. Docker Desktop (GUI/ВМ для Mac/Windows) має ліцензійні вимоги для бізнесу.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Використання тегу `latest` | Непередбачувані версії | Використовуйте конкретні теги (`:1.25.3`) |
| Запуск від імені root | Ризик безпеки | Додайте інструкцію `USER` |
| Ігнорування порядку шарів | Повільні перезбірки | Ставте змінне в кінець |
| Копіювання всього | Великі образи, витік секретів | Використовуйте `.dockerignore` |
| Відсутність очищення | Диск переповнюється | Регулярно виконуйте `docker system prune` |

---

## Тест

1. **Що робить `docker run -d -p 8080:80 nginx`?**
   <details>
   <summary>Відповідь</summary>
   Запускає контейнер nginx у від'єднаному режимі (-d, у фоні), прив'язуючи порт 8080 хоста до порту 80 контейнера. Ви можете отримати доступ до nginx за адресою http://localhost:8080.
   </details>

2. **Чому слід ставити `COPY requirements.txt` перед `COPY . .` у Dockerfile?**
   <details>
   <summary>Відповідь</summary>
   Кешування шарів. Якщо requirements.txt не змінився, Docker використовує кешований шар для `pip install`. Копіювання всіх файлів спочатку руйнує кеш щоразу, коли змінюється будь-який файл, і змушує перевстановлювати залежності.
   </details>

3. **Яка різниця між `CMD` і `RUN`?**
   <details>
   <summary>Відповідь</summary>
   `RUN` виконується під час збірки образу (встановлення пакетів, налаштування). `CMD` визначає типову команду при запуску контейнера. RUN створює шари образу; CMD лише задає метадані.
   </details>

4. **Навіщо використовувати Docker Compose замість кількох команд `docker run`?**
   <details>
   <summary>Відповідь</summary>
   Docker Compose керує кількома контейнерами як єдиним застосунком. Він забезпечує мережу між сервісами, створення томів, порядок залежностей і визначається декларативно в одному файлі.
   </details>

---

## Практична вправа

**Завдання**: Зібрати та запустити власний образ.

1. Створіть директорію проєкту:
```bash
mkdir hello-docker && cd hello-docker
```

2. Створіть `app.py`:
```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello from Docker!\n')

HTTPServer(('', 8000), Handler).serve_forever()
```

3. Створіть `Dockerfile`:
```dockerfile
FROM python:3.11-alpine
WORKDIR /app
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
```

4. Зберіть та запустіть:
```bash
docker build -t hello-docker:v1 .
docker run -d -p 8000:8000 --name hello hello-docker:v1
curl http://localhost:8000
docker rm -f hello
```

**Критерій успіху**: `curl http://localhost:8000` повертає "Hello from Docker!"

---

## Підсумок

Основи Docker для Kubernetes:

**Команди**:
- `docker run` — запуск контейнерів
- `docker ps` — перегляд контейнерів
- `docker logs` — перегляд виводу
- `docker exec` — виконання команд у контейнерах
- `docker build` — створення образів
- `docker push/pull` — обмін образами

**Основи Dockerfile**:
- `FROM` — базовий образ
- `COPY` — додавання файлів
- `RUN` — виконання під час збірки
- `CMD` — типова команда при запуску

**Найкращі практики**:
- Використовуйте конкретні теги образів
- Оптимізуйте кешування шарів
- Запускайте від імені не-root користувача
- Один процес на контейнер

---

## Наступний модуль

[Модуль 3: Що таке Kubernetes?](module-1.3-what-is-kubernetes/) — загальний огляд оркестрації контейнерів.
