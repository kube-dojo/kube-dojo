---
title: "Модуль 1.2: Поглиблене вивчення OTel Collector"
slug: "uk/k8s/otca/module-1.2-otel-collector-advanced"
sidebar:
  order: 3
revision_pending: false
en_commit: "0aa7ee45f0a30f3fe402f4669d39075937ce3865"
en_file: "src/content/docs/k8s/otca/module-1.2-otel-collector-advanced.md"
---
> **Складність**: `[СКЛАДНИЙ]` — кілька взаємодійних компонентів, логіка конвеєра.
>
> **Час на проходження**: 60–75 хвилин.
>
> **Передумови**: Модуль 1 (Основи OpenTelemetry), базові знання Kubernetes.
>
> **Домен OTCA**: Домен 3 — OTel Collector (26% іспиту).

---

## Результати навчання

Після завершення цього модуля ви зможете:

1. **Проєктувати** конфігурації Collector із кількома конвеєрами, що спрямовують трейси, метрики та логи через окремі ланцюги приймачів, процесорів, конекторів та експортерів.
2. **Налаштовувати** просунуті процесори, зокрема `memory_limiter`, `filter`, `transform`, `tail_sampling` та `batch`, щоб зменшити обсяг телеметрії, зберігаючи при цьому критично важливі сигнали.
3. **Розгортати** Collector як агент на основі DaemonSet та шлюз на основі Deployment у Kubernetes 1.35 з обмеженнями ресурсів, перевірками працездатності та поведінкою масштабування, що відповідають навантаженню.
4. **Діагностувати** проблеми конвеєра Collector за допомогою debug-експортера, zpages та внутрішніх метрик Collector, щоб виявити вузькі місця, втрати даних та збої експортерів.
5. **Оцінювати** транспорти OTLP, конектори та дистрибутиви Collector, щоб робити вибір між gRPC, HTTP, метриками, похідними від спанів, а також Core-, Contrib- та власними збірками.

## Чому цей модуль важливий

Гіпотетичний сценарій: ваша платформенна команда щойно замінила три вендорські агенти на OpenTelemetry Collector у кластері Kubernetes 1.35. Поди мають стан Ready, ендпоінт працездатності повертає успіх, а команди застосунків уже надсилають трейси OTLP, метрики у форматі Prometheus та логи контейнерів новим шляхом. У понеділок вранці розбір інциденту запитує, чому повільні трейси оформлення замовлення відсутні, тоді як галасливі перевірки готовності досі з'являються в бекенді. Collector не падав, а Kubernetes не повідомляв про невдале розгортання; збій живе в логіці конвеєра між приймачем, процесором, конектором та експортером.

Це й є та операційна причина, чому цей модуль приділяє стільки уваги формі конфігурації. Collector — це не просто сайдкар, який пересилає все, що бачить. Це програмована площина даних телеметрії: вона приймає дані через кілька протоколів, застосовує впорядковані процесори, перекидає сигнали через конектори, надсилає дані до одного або кількох бекендів та надає власні поверхні працездатності й налагодження. Конфігурація може бути синтаксично коректною, але все одно відкидати саме ті спани, які вам потрібні, дублювати метрики кластера або ухвалювати рішення про tail-семплінг на основі неповних трейсів.

Для іспиту OTCA Домен 3 важливий, бо він перевіряє, чи можете ви міркувати про цю площину даних в умовах обмежень, а не чи можете ви запам'ятати єдиний приклад файлу. Для реальної експлуатації та сама навичка вирішує, чи стане спостережуваність надійним інструментом усунення несправностей, чи ще однією розподіленою системою, яку доводиться налагоджувати під час збою. У цьому уроці ви пройдете шлях від анатомії конфігурації Collector до багатосигнальних продакшн-патернів, а потім попрактикуєтеся у валідації робочого конвеєра за допомогою debug-виводу, zpages та внутрішніх метрик.

## Архітектура Collector та анатомія конфігурації

Конфігурацію Collector найкраще читати як схему з'єднань, а не як довгий YAML-файл. Приймачі описують, як телеметрія входить, процесори описують, що з нею відбувається в пам'яті, експортери описують, куди вона виходить, конектори з'єднують один конвеєр з іншим, розширення надають допоміжні служби, а секція `service` вирішує, які компоненти насправді активні. Визначення компонента саме по собі — лише інвентар; список конвеєрів — це складальна лінія, яка змушує його працювати.

Ця відмінність запобігає поширеній помилці на іспиті та в продакшні. Ви можете оголосити процесор `filter`, експортер `debug` або розширення `zpages` у правильній секції верхнього рівня, але жоден із цих компонентів не впливає на телеметрію, доки секція `service` не посилається на них. Ставтеся до блоків компонентів верхнього рівня як до деталей на верстаку, а потім ставтеся до `service.pipelines` як до точного порядку, в якому ці деталі прикручуються до машини.

```yaml
# The five building blocks of every Collector config
receivers:    # How data gets IN to the Collector
processors:   # How data gets TRANSFORMED inside the Collector
exporters:    # How data gets OUT of the Collector
connectors:   # Bridge between pipelines (output of one, input of another)
extensions:   # Auxiliary services (health checks, auth, debugging)

service:      # Wires everything together into pipelines
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/backend]
    metrics:
      receivers: [otlp, prometheus]
      processors: [batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp, filelog]
      processors: [batch]
      exporters: [otlp/backend]
```

Найважливіше правило проєктування полягає в тому, що процесори виконуються в порядку, наведеному в конвеєрі. `memory_limiter` ближче до кінця менш корисний, бо дані вже накопичилися в попередніх процесорах, тоді як `batch` на початку може збільшити навантаження на пам'ять ще до того, як пізніші фільтри видалять небажану телеметрію. На іспиті це часто подається як просте питання впорядкування, але глибший урок полягає в тому, що кожен процесор змінює профіль ризику наступного компонента.

```
┌─────────────────────────────────────────────────────────────────┐
│                      OTel Collector                             │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │Receivers │──▶│Processors│──▶│Exporters │──▶│ Backends │   │
│  │          │   │          │   │          │   │          │   │
│  │ otlp     │   │ batch    │   │ otlp     │   │ Jaeger   │   │
│  │ prometheus│   │ filter   │   │ prometheus│   │ Prometheus│   │
│  │ filelog   │   │ transform│   │ debug    │   │ Loki     │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Extensions: health_check, zpages, pprof, bearertokenauth  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

Зверніть увагу, що діаграма показує розширення поруч із конвеєром, а не всередині нього. Розширення не перетворюють записи телеметрії, але вони можуть бути необхідними для безпечної експлуатації Collector. Перевірки працездатності роблять проби Kubernetes змістовними, zpages допомагають оглядати живий стан конвеєра, pprof підтримує профілювання, а розширення автентифікації дозволяють приймачам чи експортерам встановлювати базові межі довіри, перш ніж телеметрія перетне межі простору імен або мережі.

Приймачі визначають вхідні двері Collector. Приймач OTLP — це універсальний вхід для трафіку, нативного для OpenTelemetry, і він зазвичай слухає на gRPC-порту 4317 та HTTP-порту 4318. Приймач Prometheus скрейпить ендпоінти метрик, приймач filelog читає файли логів вузла, приймач hostmetrics збирає локальні системні метрики, а приймач кластера Kubernetes читає загальнокластерний стан із сервера API. Ці приймачі вирішують різні завдання збору, тож не слід запускати їх усі скрізь лише тому, що дистрибутив їх містить.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        max_recv_msg_size_mib: 4       # Default: 4 MiB
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins: ["*"]       # For browser-based apps
```

Коли ви обираєте між OTLP/gRPC та OTLP/HTTP, думайте насамперед про мережевий шлях, а не про мову застосунку. gRPC ефективний для трафіку «сервіс — Collector» та «Collector — Collector», коли ви контролюєте маршрутизацію HTTP/2, але HTTP дружніший до браузерів, старших проксі та налагодження звичайними інструментами. Якщо в питанні сказано, що браузер надсилає телеметрію напряму, або проксі не може чисто обробити HTTP/2, OTLP/HTTP зазвичай є прагматичною відповіддю.

| Аспект | gRPC (:4317) | HTTP (:4318) |
|--------|-------------|-------------|
| Продуктивність | Вища пропускна здатність, потокова передача | Дещо нижча |
| Стиснення | Вбудоване (gzip, zstd) | Потребує налаштування |
| Дружній до фаєрволів | Ні (HTTP/2, специфічні порти) | Так (стандартний HTTP) |
| Підтримка браузерів | Ні (потрібен проксі) | Так (для вебзастосунків) |
| Найкраще для | Сервіс — Collector, Collector — Collector | Браузерний RUM, граничний прийом |

Приймачі Prometheus, файлів, хоста та Kubernetes додають корисні вхідні точки, відмінні від OTLP, але вони також прив'язують Collector до місця розгортання. Приймачу filelog потрібен доступ до файлової системи вузла, тож він належить до агентського DaemonSet. Приймач `k8s_cluster` читає глобальний стан Kubernetes, тож його запуск на кожному вузлі дублює метрики й підвищує тиск на API. Перед запуском цього: який вивід ви очікуєте від кожного приймача, якщо його перенести з агента на шлюз, і які приймачі просто перестануть бачити своє джерело даних?

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'k8s-pods'
          scrape_interval: 15s
          kubernetes_sd_configs:
            - role: pod
```

Виявлення сервісів Kubernetes у Prometheus також потребує RBAC для API Kubernetes, зазвичай `get`, `list` та `watch` на тих видах ресурсів, які воно виявляє, як-от поди, ендпоінти та сервіси у просторах імен, які воно скрейпить.

```yaml
receivers:
  filelog:
    include: [/var/log/pods/*/*/*.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'
```

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu: {}
      memory: {}
      disk: {}
      filesystem: {}
      network: {}
      load: {}
```

```yaml
receivers:
  k8s_cluster:
    collection_interval: 30s
    node_conditions_to_report: [Ready, MemoryPressure]
    allocatable_types_to_report: [cpu, memory]
```

Приймач `k8s_cluster` — це чистий приклад «правильний компонент, неправильне розміщення». Йому потрібні дозволи API Kubernetes, і він спостерігає об'єкти, які з погляду простору імен уже є глобальними. Якщо ви запускаєте його як DaemonSet на кожному вузлі, кожен агент повідомляє схожі факти рівня кластера; якщо ви запускаєте один екземпляр-шлюз або один узгоджений Deployment-шлюз, ви отримуєте ту саму інформацію з меншим обсягом дубльованої роботи та меншим розростанням RBAC.

Процесори — це місце, де Collector стає системою формування даних, а не проксі для пересилання. `memory_limiter` захищає процес до того, як буферизація зросте, `batch` покращує ефективність експортера, `filter` видаляє телеметрію, яку ви свідомо не хочете, `attributes` редагує атрибути, `transform` застосовує оператори OTTL, а `tail_sampling` відкладає рішення, доки не зможе оцінити трейс. Усі ці процесори можуть бути коректними, але порядок вирішує, зменшують вони ризик чи посилюють його.

```yaml
processors:
  batch:
    send_batch_size: 8192         # Number of items per batch
    send_batch_max_size: 10000    # Hard upper limit
    timeout: 200ms                # Flush interval even if batch isn't full
```

Процесор batch присутній майже завжди, бо експортери ефективніші, коли надсилають групи елементів телеметрії, а не по одному запису за раз. Пакетування зменшує накладні витрати на запити та покращує стиснення, але це також означає, що Collector ненадовго утримує більше даних у пам'яті. Саме через цей компроміс `batch` зазвичай з'являється пізно в конвеєрі, після того, як процесори обмежили пам'ять, відкинули небажані дані та зредагували поля, які не повинні залишати кластер.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512                # Hard limit
    spike_limit_mib: 128          # Buffer for spikes
```

У цьому прикладі обмежувача пам'яті процесор починає відмовляти у прийнятті даних, коли пам'ять наближається до налаштованого ліміту мінус запас на сплески, та примусово відкидає дані під сильнішим тиском. Така поведінка не замінює коректних запитів і лімітів ресурсів, але дає Collector контрольований режим відмови, перш ніж контейнер буде вбито. Зазвичай краще навмисно та видимо втратити частину телеметрії, ніж дозволити Kubernetes перезапустити весь конвеєр без збереження контексту.

```yaml
processors:
  filter:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'     # Drop health checks
        - 'attributes["http.route"] == "/readyz"'
    metrics:
      metric:
        - 'name == "http.server.duration" and resource.attributes["service.name"] == "debug-svc"'
```

До процесора filter слід ставитися як до правила фаєрвола для даних спостережуваності. Він потужний, бо видаляє низькоцінні сигнали близько до джерела, але широка умова може мовчки відкинути докази, які вам знадобляться пізніше. Використовуйте `error_mode: ignore`, щоб некоректний запис не зупиняв процесор, і валідуйте фільтр за допомогою debug-експортера, перш ніж надсилати трафік лише до довготривалого бекенду.

```yaml
processors:
  attributes:
    actions:
      - key: environment
        value: production
        action: upsert             # Insert or update
      - key: db.password
        action: delete             # Remove sensitive data
      - key: user.email
        action: hash               # Hash PII
```

Обробка атрибутів дає вам передбачуваний спосіб нормалізувати метадані ресурсів та спанів, перш ніж від них почнуть залежати подальші запити. Додавання атрибута `environment` може зробити дашборди узгодженими, видалення атрибута на кшталт пароля запобігає випадковому розкриттю, а хешування адреси електронної пошти зберігає групування без утримання вихідного значення. Ключова операційна звичка — робити ці перетворення явними та перевіреними, бо метадані спостережуваності часто стають частиною оповіщень, зберігання та контролю витрат.

```yaml
processors:
  transform:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - set(attributes["deployment.env"], "prod") where resource.attributes["k8s.namespace.name"] == "production"
          - truncate_all(attributes, 256)           # Limit attribute value length
          - replace_pattern(attributes["http.url"], "token=([^&]*)", "token=***")
    metric_statements:
      - context: datapoint
        statements:
          - convert_sum_to_gauge() where metric.name == "system.cpu.time"
    log_statements:
      - context: log
        statements:
          - merge_maps(attributes, ParseJSON(body), "insert") where IsMatch(body, "^\\{")
```

OTTL, мова перетворень OpenTelemetry (OpenTelemetry Transformation Language), — це високоважлива тема іспиту, бо вона з'являється скрізь, де Collector потребує виразніших змін, ніж прості дії з атрибутами. Функції на кшталт `set`, `delete`, `truncate_all`, `replace_pattern`, `merge_maps`, `ParseJSON` та `IsMatch` дозволяють змінювати телеметрію на основі контексту. Ризик у тому, що виразні правила заслуговують на ту саму дисципліну перевірки, що й код застосунку, особливо коли вони торкаються URL, ідентифікаторів або імен сигналів, на які покладаються дашборди.

```yaml
processors:
  tail_sampling:
    decision_wait: 10s              # Wait for trace to complete
    num_traces: 100000              # Traces held in memory
    policies:
      - name: errors-always
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: low-volume-sample
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

Tail-семплінг відрізняється від head-семплінгу тим, що він чекає, доки надійде достатньо спанів, щоб оцінити трейс. Це робить можливими політики на кшталт «зберегти всі помилки, зберегти всі повільні трейси, семплувати решту», але це також означає, що Collector мусить утримувати трейси в пам'яті та спрямовувати кожен спан трейсу до тієї самої точки ухвалення рішення. Зробіть паузу й передбачте: що, на вашу думку, станеться, якщо трейс розділиться між двома репліками шлюзу до того, як виконається tail-семплінг?

## Експортери, конектори та вибір транспорту OTLP

Експортери — це чорний хід Collector, і їхня поведінка часто визначає, чи справді конвеєр, який виглядає справним, доставляє дані. Експортер OTLP може надсилати до іншого Collector або бекенду спостережуваності, OTLP/HTTP може перетинати середовища, де gRPC незручний, Prometheus може надавати ендпоінт для скрейпінгу, debug може друкувати записи для валідації, а file може писати телеметрію на диск. Кожен експортер має налаштування надійності та безпеки, які важать не менше за назву призначення.

```yaml
exporters:
  otlp:
    endpoint: tempo.observability.svc.cluster.local:4317
    tls:
      insecure: false
      cert_file: /certs/client.crt
      key_file: /certs/client.key
    compression: gzip              # or zstd
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s
```

Експортер OTLP — це відповідь за замовчуванням для комунікації «Collector — Collector» та «Collector — бекенд», бо він чисто зберігає семантику OpenTelemetry. Налаштування TLS та повторних спроб заслуговують на явний огляд: внутрішньокластерний трафік може використовувати service mesh або контролі приватної мережі, тоді як трафік, що залишає кластер, повинен мати транспортну безпеку та чіткі ліміти повторних спроб. Необмежений тиск повторних спроб може погіршити збій бекенду, але відсутність повторних спроб може перетворити коротке переривання мережі на втрату даних, якій можна було б запобігти.

```yaml
exporters:
  otlphttp:
    endpoint: https://ingest.example.com
    compression: gzip
    headers:
      Authorization: "Bearer ${env:API_TOKEN}"
```

OTLP/HTTP — практичний вибір, коли мережевий шлях сприяє звичайній обробці HTTP, але приклад автентифікації також показує, чому в прикладах слід використовувати змінні середовища та заповнювачі, а не вбудовані секрети. ConfigMap Collector часто видимий кільком платформенним ролям, і пхати реальні облікові дані у приклади чи історію Git — і непотрібно, і небезпечно. Тримайте чутливі значення в Kubernetes Secrets або зовнішньому менеджері секретів, а потім свідомо посилайтеся на них.

```yaml
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: otel
    resource_to_telemetry_conversion:
      enabled: true                 # Promote resource attributes to labels
```

Експортер Prometheus перевертає звичний патерн push на патерн scrape. Це може бути корисно, коли Prometheus уже є бекендом метрик, але підвищення атрибутів ресурсу до міток слід робити обережно, бо кардинальність міток впливає на зберігання, швидкість запитів та витрати. Ім'я сервісу та простір імен зазвичай є корисними мітками; ідентифікатори користувачів, сирі URL або значення, специфічні для запиту, майже завжди є проблемою.

```yaml
exporters:
  debug:
    verbosity: detailed            # basic | normal | detailed
    sampling_initial: 5            # First N items logged
    sampling_thereafter: 200       # Then every Nth item
```

Debug-експортер — це не продакшн-бекенд, але це один із найбезпечніших способів довести, що конвеєр працює, перш ніж ви почнете від нього залежати. Додайте його поруч зі справжнім експортером під час розгортання, надішліть відомий трейс або метрику та підтвердьте, що перетворений запис виглядає так, як ви очікуєте. Видаліть або зменшіть багатослівний debug-вивід після валідації, бо детальні логи телеметрії можуть швидко зростати та можуть містити чутливі атрибути, якщо редагування неповне.

```yaml
exporters:
  file:
    path: /data/otel-output.json
    rotation:
      max_megabytes: 100
      max_days: 7
      max_backups: 5
```

Конектори особливі, бо вони поводяться як експортер в одному конвеєрі та як приймач в іншому. Конектор spanmetrics — класичний приклад: трейси входять у конвеєр трейсів, конектор виводить метрики у стилі RED, і ці згенеровані метрики входять у конвеєр метрик. Це дозволяє створювати метрики частоти запитів, помилок та тривалості з даних трейсів, але це також означає, що вибір вимірів може створити метрики високої кардинальності, якщо ви включите поля, які змінюються від запиту до запиту.

```yaml
connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 500ms, 1s, 5s]
    dimensions:
      - name: http.method
      - name: http.status_code
    namespace: traces.spanmetrics

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo, spanmetrics]     # spanmetrics is an exporter here
    metrics:
      receivers: [otlp, spanmetrics]            # spanmetrics is a receiver here
      processors: [batch]
      exporters: [prometheus]
```

Прочитайте цю конфігурацію повільно, бо вона навчає ментальної моделі конектора краще, ніж означення. Конвеєр трейсів експортує і до Tempo, і до `spanmetrics`, тоді як конвеєр метрик приймає і від звичайного OTLP, і від `spanmetrics`. Якщо ви бачите конектор лише в одному боці цих відносин, похідний сигнал не з'явиться там, де ви очікуєте.

```yaml
connectors:
  count:
    spans:
      span.count:
        description: "Count of spans"
    logs:
      log.record.count:
        description: "Count of log records"
```

Сам OTLP має два поширені транспорти, і правильна відповідь залежить від обмежень, а не від уподобань. gRPC використовує HTTP/2 та Protocol Buffers, підтримує патерни потокової передачі та є сильним внутрішнім стандартом за замовчуванням. HTTP може використовувати Protobuf або JSON на шляхах «запит — відповідь», таких як `/v1/traces`, `/v1/metrics` та `/v1/logs`, що полегшує роботу через проксі та огляд звичайними HTTP-інструментами.

| Можливість | OTLP/gRPC | OTLP/HTTP |
|---------|-----------|-----------|
| Транспорт | HTTP/2 з Protocol Buffers | HTTP/1.1 з Protobuf або JSON |
| Порт | 4317 | 4318 |
| Стиснення | gzip, zstd (вбудоване) | gzip (через Content-Encoding) |
| Потокова передача | Так (двоспрямована) | Ні (запит/відповідь) |
| Шлях (трейси) | Н/Д (служба gRPC) | `/v1/traces` |
| Шлях (метрики) | Н/Д | `/v1/metrics` |
| Шлях (логи) | Н/Д | `/v1/logs` |
| Підтримка проксі | Потрібен проксі з підтримкою HTTP/2 | Працює з будь-яким HTTP-проксі |

Стиснення в продакшні має бути свідомим налаштуванням експортера. Дані телеметрії містять повторювані імена атрибутів, імена сервісів та метадані ресурсів, тож стиснення часто дає відчутне зменшення пропускної здатності. zstd може бути привабливим для внутрішнього трафіку, коли він підтримується наскрізно, тоді як gzip є ширше сумісним вибором для зовнішніх ендпоінтів та змішаної інфраструктури.

```yaml
exporters:
  otlp:
    endpoint: gateway:4317
    compression: zstd        # Best ratio for telemetry data
  otlphttp:
    endpoint: https://ingest.example.com
    compression: gzip        # More widely supported
```

Який підхід ви б тут обрали і чому: внутрішній шлях «агент — шлюз» у кластері, який ви контролюєте, чи телеметрію, що походить із браузера та мусить перетинати корпоративний проксі? Перший випадок зазвичай сприяє OTLP/gRPC з ефективним стисненням та виявленням сервісів. Другий зазвичай сприяє OTLP/HTTP, прийому з підтримкою CORS та суворішій увазі до автентифікації й лімітів частоти на межі.

## Патерни розгортання в Kubernetes та Operator

Kubernetes змінює розмову про проєктування Collector, бо розміщення контролює, які дані Collector може бачити. Агент на основі DaemonSet запускає один Collector на вузол, що робить його добрим для локальних логів, метрик хоста та буферизації близько до джерела. Шлюз на основі Deployment запускає спільний пул, що робить його добрим для агрегації, tail-семплінгу, маршрутизації та політики експорту, специфічної для бекенду. Найпоширеніший продакшн-патерн використовує обидва, бо жодне розміщення поодинці не вирішує всіх проблем.

```
Agent Mode (DaemonSet)                Gateway Mode (Deployment)
──────────────────────                ─────────────────────────

┌─────────────────────┐              ┌─────────────────────┐
│      Node 1         │              │      Node 1         │
│ ┌─────┐ ┌────────┐ │              │ ┌─────┐             │
│ │App A│─▶│Collector│─┤              │ │App A│──┐          │
│ └─────┘ │(Agent) │ │              │ └─────┘  │          │
│ ┌─────┐ │        │ │              │ ┌─────┐  │          │
│ │App B│─▶│        │ │              │ │App B│──┤          │
│ └─────┘ └───┬────┘ │              │ └─────┘  │          │
└─────────────┼──────┘              └──────────┼──────────┘
              │                                │
              ▼                                │
┌─────────────────────┐                        │
│      Node 2         │              ┌─────────▼──────────┐
│ ┌─────┐ ┌────────┐ │              │  Gateway Collector  │
│ │App C│─▶│Collector│─┤───▶Backend  │  (Deployment, 2+   │
│ └─────┘ │(Agent) │ │              │   replicas)         │──▶Backend
│         └───┬────┘ │              │                     │
└─────────────┼──────┘              └─────────▲──────────┘
              │                                │
              ▼                     ┌──────────┼──────────┐
         Backend                    │      Node 2         │
                                    │ ┌─────┐  │          │
                                    │ │App C│──┘          │
                                    │ └─────┘             │
                                    └─────────────────────┘
```

Поділ на агент і шлюз також є межею масштабування. Агенти масштабуються разом із вузлами та забезпечують зворотний тиск близько до навантажень, тоді як шлюзи масштабуються разом із обсягом телеметрії та складністю експорту. Tail-семплінг належить шлюзу, бо йому потрібно достатньо спанів від одного трейсу, щоб ухвалити рішення, а збір на рівні хоста належить агенту, бо шлюз не може читати локальні файли чи системні лічильники кожного вузла.

| Аспект | Агент (DaemonSet) | Шлюз (Deployment) |
|--------|-------------------|---------------------|
| Розгортання | Один на вузол | Спільний пул (2+ репліки) |
| Використання ресурсів | Легке на вузол | Важче, але централізоване |
| Tail-семплінг | Неможливий (неповні трейси) | Так (надходять повні трейси) |
| Метрики хоста | Так (локальний доступ) | Ні |
| Filelog | Так (локальні файли) | Ні |
| Масштабування | Масштабується разом із вузлами | HPA за CPU/пам'яттю |
| Найкраще для | Збір, базова обробка | Агрегація, семплінг, маршрутизація |

Простий продакшн-ланцюг — це застосунки до агентів вузлів, агенти до шлюзів та шлюзи до одного чи кількох бекендів. Така форма дозволяє тримати локальний збір на вузлі простим, водночас централізуючи дорогу або політикомістку обробку. Вона також створює чітку модель відмови: якщо бекенд недоступний, шлюзи можуть поглинути поведінку повторних спроб без того, щоб кожен застосунок чи агент вузла потребував повної логіки, специфічної для бекенду.

```
Apps ──▶ Agent (DaemonSet) ──▶ Gateway (Deployment) ──▶ Backends
         - hostmetrics            - tail_sampling
         - filelog                - spanmetrics
         - memory_limiter         - routing
         - batch                  - export to N backends
```

Горизонтальне масштабування шлюзу створює одну тонку проблему з трейсами: усі спани трейсу мусять досягти того самого шлюзу, якщо ввімкнено tail-семплінг. Звичайне балансування навантаження за принципом round-robin може розділити трейс між репліками, тож кожен шлюз бачить неповну історію та ухвалює погане рішення. Експортер балансування навантаження вирішує це, маршрутизуючи на основі ідентифікатора трейсу (trace ID) та виявляючи екземпляри шлюзу через резолвер, як-от DNS.

```yaml
# On the Agent
exporters:
  loadbalancing:
    protocol:
      otlp:
        tls:
          insecure: true
    resolver:
      dns:
        hostname: otel-gateway-headless.observability.svc.cluster.local
        port: 4317
```

OpenTelemetry Operator додає керування, нативне для Kubernetes, поверх цих режимів розгортання. Замість того, щоб вручну писати кожен Deployment, DaemonSet, Service та ConfigMap, ви можете описати кастомний ресурс `OpenTelemetryCollector` і дозволити Operator узгоджувати базові об'єкти. Він також підтримує авто-інструментування через кастомний ресурс `Instrumentation`, що корисно, коли командам застосунків потрібна низькофрикційна відправна точка.

```bash
# Install cert-manager first (required dependency)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.5/cert-manager.yaml

# Install the OTel Operator
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
```

Collector, керовані Operator, — це все одно Collector, тож застосовується те саме міркування про конвеєр. Поле `mode` обирає daemonset, deployment, statefulset або sidecar, тоді як `spec.config` містить конфігурацію приймачів, процесорів, експортерів, конекторів, розширень та служби. Не дозволяйте абстракції кастомного ресурсу приховувати питання про потік даних, які ви вже навчилися ставити.

```yaml
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-agent
  namespace: observability
spec:
  mode: daemonset                    # daemonset | deployment | statefulset | sidecar
  image: otel/opentelemetry-collector-contrib:0.98.0
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      memory_limiter:
        check_interval: 1s
        limit_mib: 512
      batch: {}
    exporters:
      otlp:
        endpoint: otel-gateway.observability.svc.cluster.local:4317
        tls:
          insecure: true
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [otlp]
```

Авто-інструментування потужне, бо Operator може впроваджувати мовні агенти в поди через анотації, але його слід запроваджувати з чітким правом власності. Застосунку все одно потрібні сумісні середовища виконання, передбачувані накладні витрати ресурсів та ендпоінт, який може приймати отриману телеметрію. Почніть з невеликого простору імен або єдиного навантаження, а потім розширюйтеся після того, як перевірите якість трейсів, імена атрибутів та поведінку семплінгу.

Перед копіюванням маніфесту `Instrumentation` підтвердьте версії CRD, які надає встановлений Operator. **Вид `Instrumentation` надається за адресою `opentelemetry.io/v1alpha1`**. **`OpenTelemetryCollector`** — це вид, який запровадив **`v1beta1`** поряд зі старішими наданими версіями — не плутайте ці два CRD, читаючи завдання іспиту чи приклади з upstream.

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: auto-instrumentation
  namespace: observability
spec:
  exporter:
    endpoint: http://otel-agent-collector.observability.svc.cluster.local:4318
  propagators:
    - tracecontext
    - baggage
  sampler:
    type: parentbased_traceidratio
    argument: "0.25"
  java:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:latest
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:latest
  nodejs:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-nodejs:latest
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
spec:
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-java: "true"     # Java auto-instrument
        # Other options:
        # instrumentation.opentelemetry.io/inject-python: "true"
        # instrumentation.opentelemetry.io/inject-nodejs: "true"
        # instrumentation.opentelemetry.io/inject-dotnet: "true"
    spec:
      containers:
        - name: app
          image: my-java-app:latest
```

Дистрибутиви Collector важать більше, коли ви переходите з лабораторії в продакшн. Дистрибутив Core дає вам меншу базу, що супроводжується проєктом; Contrib дає широке покриття інтеграцій; власний дистрибутив, зібраний за допомогою OpenTelemetry Collector Builder, містить лише ті компоненти, які ви обираєте. Іспит очікує, що ви знатимете цей компроміс, а продакшн-огляди безпеки зазвичай ним переймаються, бо кожен невикористаний компонент — це поверхня залежностей.

| Дистрибутив | Компоненти | Сценарій використання |
|-------------|-----------|----------|
| **Core** (`otel/opentelemetry-collector`) | ~20 компонентів (otlp, batch, debug тощо) | Мінімальний слід, середовища, чутливі до безпеки |
| **Contrib** (`otel/opentelemetry-collector-contrib`) | 200+ компонентів (усі приймачі, процесори, експортери спільноти) | Розробка, коли вам потрібні специфічні інтеграції |
| **Custom** (зібраний за допомогою `ocb`) | Точно те, що ви обираєте | Продакшн — включайте лише те, що використовуєте |

Конфігурація Collector Builder — це явне керування залежностями для вашої площини даних телеметрії. Ви оголошуєте метадані дистрибутиву та точні модулі приймачів, процесорів та експортерів, які хочете вкомпілювати. Це може зменшити розмір бінарника, час запуску та обсяг аудиту, але це також означає, що ви володієте процесом збірки та мусите оновлювати обрані компоненти в міру виходу релізів OpenTelemetry.

```yaml
# builder-config.yaml
dist:
  name: my-collector
  description: "Production collector"
  output_path: ./dist
  otelcol_version: "0.98.0"

receivers:
  - gomod: go.opentelemetry.io/collector/receiver/otlpreceiver v0.98.0
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/receiver/filelogreceiver v0.98.0

processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.98.0
  - gomod: go.opentelemetry.io/collector/processor/memorylimiterprocessor v0.98.0

exporters:
  - gomod: go.opentelemetry.io/collector/exporter/otlpexporter v0.98.0
  - gomod: go.opentelemetry.io/collector/exporter/debugexporter v0.98.0
```

```bash
# Build it
ocb --config builder-config.yaml
```

Власний Collector не є автоматично кращим; він кращий, коли у вас є стабільний набір компонентів, процес релізу та причина зменшити слід чи поверхню залежностей. Під час раннього експериментування Contrib часто є швидшим шляхом, бо він містить приймач чи експортер, який ви тестуєте. Щойно конвеєр стабілізується, власний дистрибутив дозволяє видалити компоненти, які були корисними під час дослідження, але непотрібні для довготривалої експлуатації.

## Налагодження та експлуатація багатосигнального конвеєра

Налагодження Collector починається з базового питання: чи увійшла телеметрія, чи змінилася та чи покинула конвеєр так, як ви задумали? Здоров'я пода Kubernetes відповідає лише на те, чи живий процес. Власна телеметрія Collector, debug-експортер та zpages відповідають на те, чи приймачі прийняли дані, чи процесори відкинули або перетворили їх, чи експортери надіслали їх і чи працюють розширення. Ці сигнали повинні бути присутні в кожному серйозному плані розгортання.

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133       # Liveness/readiness probe target

  zpages:
    endpoint: 0.0.0.0:55679       # Internal debug UI at /debug/tracez, /debug/pipelinez

  pprof:
    endpoint: 0.0.0.0:1777        # Go pprof profiling

  bearertokenauth:
    token: "${env:OTEL_AUTH_TOKEN}"

service:
  extensions: [health_check, zpages, pprof, bearertokenauth]
```

| Розширення | Призначення | Порт за замовчуванням |
|-----------|---------|-------------|
| `health_check` | Проби liveness/readiness K8s | 13133 |
| `zpages` | Debug-UI: стан конвеєра, зразки трейсів | 55679 |
| `pprof` | Профілювання продуктивності | 1777 |
| `bearertokenauth` | Автентифікація вхідних/вихідних запитів | Н/Д |

Debug-експортер слід використовувати як тимчасове дзеркало спостережуваності. Коли запроваджується фільтр, перетворення чи конектор, додайте `debug` поруч зі справжнім експортером і надішліть відомий тестовий запис. Якщо запис з'являється до процесора, але не після нього, ви звузили збій, не гадаючи про бекенд, мережеву політику чи запит дашборда.

```yaml
exporters:
  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/backend, debug]    # Add debug alongside real exporter
```

Внутрішня телеметрія — це дашборд Collector про самого себе. Лічильники прийнятого приймачем показують, чи надходить вхід, лічильники відкинутого процесором показують, чи фільтрація або тиск видаляють дані, лічильники надісланого експортером показують успішний вивід, а лічильники невдалого експортера розкривають проблеми з бекендом або мережею. Ці метрики дозволяють відрізнити «застосунок нічого не надіслав» від «Collector це відкинув» від «бекенд це відхилив».

```yaml
service:
  telemetry:
    logs:
      level: debug                  # debug | info | warn | error
      encoding: json                # For structured log parsing
    metrics:
      level: detailed               # none | basic | normal | detailed
      address: 0.0.0.0:8888        # Collector's own /metrics endpoint
```

Імена внутрішніх метрик навмисно операційні: `otelcol_receiver_accepted_spans` каже, що спани надійшли, `otelcol_processor_dropped_spans` каже, що процесор видалив спани, `otelcol_exporter_sent_spans` каже, що спани успішно вийшли, а `otelcol_exporter_send_failed_spans` каже, що експортер не зміг доставити. Коли ви діагностуєте проблеми конвеєра Collector, порівнюйте ці лічильники за сигналом та конвеєром, перш ніж змінювати інструментування застосунку.

| Ендпоінт | Що він показує |
|----------|---------------|
| `/debug/pipelinez` | Активні конвеєри та їхні компоненти |
| `/debug/tracez` | Зразки трейсів, що проходять через Collector |
| `/debug/rpcz` | Статистика викликів gRPC |
| `/debug/extensionz` | Запущені розширення |

```bash
# Port-forward to access zpages
kubectl port-forward svc/otel-collector 55679:55679
# Then open http://localhost:55679/debug/pipelinez
```

Наступна повна конфігурація пов'язує ідеї разом. Вона приймає трейси, метрики та логи, скрейпить Prometheus та метрики хоста, фільтрує перевірки працездатності, редагує чутливі значення, генерує метрики спанів, експортує до окремих бекендів, вмикає health та zpages та надає внутрішні метрики. Вона навмисно багатша за мінімальну відповідь на іспиті, бо продакшн-збої зазвичай трапляються там, де сигнали зустрічаються з політикою.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'k8s-pods'
          scrape_interval: 15s
          kubernetes_sd_configs:
            - role: pod
  filelog:
    include: [/var/log/pods/*/*/*.log]
    operators:
      - type: json_parser
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu: {}
      memory: {}
      disk: {}

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 1024
    spike_limit_mib: 256
  batch:
    send_batch_size: 8192
    timeout: 200ms
  filter/healthz:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'
        - 'attributes["http.route"] == "/readyz"'
  transform/redact:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - replace_pattern(attributes["http.url"], "token=([^&]*)", "token=REDACTED")
    log_statements:
      - context: log
        statements:
          - replace_pattern(body, "password=\\S+", "password=***")

exporters:
  otlp/tempo:
    endpoint: tempo.observability.svc.cluster.local:4317
    tls:
      insecure: true
  otlphttp/loki:
    endpoint: http://loki.observability.svc.cluster.local:3100/otlp
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  debug:
    verbosity: basic

connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 500ms, 1s, 5s]
    dimensions:
      - name: http.method
      - name: http.status_code

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, filter/healthz, transform/redact, batch]
      exporters: [otlp/tempo, spanmetrics, debug]
    metrics:
      receivers: [otlp, prometheus, hostmetrics, spanmetrics]
      processors: [memory_limiter, batch]
      exporters: [prometheus, debug]
    logs:
      receivers: [otlp, filelog]
      processors: [memory_limiter, transform/redact, batch]
      exporters: [otlphttp/loki, debug]
```

Переглядаючи таку конфігурацію, проходьте по одному сигналу за раз. Для трейсів вхід OTLP проходить захист пам'яті, фільтрацію перевірок працездатності, редагування, пакетування, експорт до Tempo, генерацію метрик спанів та debug-вивід. Для метрик OTLP, Prometheus, хост та похідні метрики спанів спільно використовують конвеєр перед експортом до Prometheus та debug. Для логів вхід OTLP та файлів спільно використовує редагування та пакетування перед **експортом OTLP/HTTP до Loki** (`otlphttp/loki` за адресою `http://…:3100/otlp` — Loki приймає OTLP через HTTP, а не OTLP/gRPC на порту 3100) та debug-дзеркалом.

Цей покроковий розбір — найшвидший спосіб знайти приховані помилки. Якщо процесор існує, але його немає у відповідному конвеєрі сигналу, він не може вплинути на цей сигнал. Якщо конектор з'являється як експортер, але не як приймач в іншому конвеєрі, його виводу немає куди корисно подітися. Якщо debug-вивід присутній, але дані бекенду відсутні, наступною ціллю розслідування стає експортер, бекенд, автентифікація або мережевий шлях.

### Розбір на практиці: безпечна зміна конвеєра Collector

Уявіть, що наступний запит на зміну — зменшити витрати на телеметрію, зберігаючи достатньо деталей для реагування на інциденти. Слабкий огляд шукав би лише коректний YAML і, можливо, підтвердив би, що под Collector чисто перезапускається. Сильний огляд простежує трасу даних через конвеєр і запитує, що кожен компонент може відкинути, перетворити, забуферизувати чи продублювати. Такий стиль огляду повільніший на перших кількох спробах, але він запобігає дорогим несподіванкам після того, як Collector стає спільним шляхом для кожної команди.

Почніть із наміру приймача. Якщо застосунки надсилають OTLP напряму до шлюзу, шлюз може приймати спани застосунків, але він не може читати файли логів контейнерів кожного вузла, якщо ці файли не змонтовані з вузла. Якщо агенти скрейплять метрики подів, їм потрібні дозволи виявлення та чітка стратегія міток. Якщо браузер надсилає OTLP/HTTP, CORS та автентифікація — не необов'язкові граничні деталі; вони є частиною контракту приймача, бо приймач відкритий до іншої межі довіри.

Далі перегляньте порядок процесорів як послідовність безпеки. Захист пам'яті має відбуватися до дорогої буферизації, широка фільтрація має відбуватися до експорту в бекенд, редагування має відбуватися до того, як записи перетнуть межу, а пакетування має відбуватися після того, як завершиться більшість роботи з окремими записами. Цей порядок стосується не лише продуктивності. Він також вирішує, які метрики ви можете використати, щоб пояснити втрату даних, бо процесор може звітувати лише про ту роботу, яка до нього доходить.

Потім перегляньте кожен фільтр так, ніби це продакшн-правило доступу. Спани перевірок працездатності зазвичай безпечно відкидати, але умова, яка збігається з іменами сервісів, префіксами URL чи кодами стану, може видалити докази з реальних інцидентів. Використовуйте позитивні та негативні приклади під час тестування фільтра: один запис, який має бути відкинутий, один схожий запис, який мусить вижити, та один некоректний запис, який доводить поведінку `error_mode`. Без цих випадків фільтр може пройти демонстрацію щасливого шляху і все одно зашкодити спостережуваності.

Правила перетворення заслуговують на той самий огляд, бо вони можуть перейменувати атрибути, від яких уже залежать дашборди, оповіщення та карти сервісів. `replace_pattern`, який редагує токен, корисний; широкий `set`, який перезаписує атрибут ресурсу, може зламати групування в усьому бекенді. Коли перетворення змінює імена, запишіть подальший запит або дашборд, який споживатиме результат, а потім провалідуйте цей запит щодо debug-виводу, перш ніж зміна досягне спільного середовища.

Політика семплінгу потребує ще суворішого огляду розміщення. Head-семплінг може відбуватися близько до джерела, бо рішення ухвалюється до того, як існує повний трейс, але tail-семплінг — це турбота шлюзу, бо він використовує факти, виявлені пізніше в трейсі. Політика, яка зберігає помилки та повільні запити, має сенс лише тоді, коли всі спани трейсу надходять до того самого процесора семплінгу. Якщо трафік балансується випадково між шлюзами, політика все одно налаштована, але дані, які вона оцінює, неповні.

Огляд конектора стосується обох напрямків потоку сигналу. Коли `spanmetrics` з'являється у списку експортерів конвеєра трейсів, він приймає спани та створює метрики. Коли той самий конектор з'являється у списку приймачів конвеєра метрик, ці створені метрики входять у шлях метрик і можуть бути експортовані. Якщо одного з боків бракує, конектор може виглядати присутнім, тоді як похідний сигнал ніколи не досягає призначеного бекенду. Саме тому помилки конекторів часто відчуваються як мовчазні збої.

Огляд кардинальності належить поруч із оглядом конектора, бо згенеровані метрики можуть зростати швидше за метрики, написані вручну. Найспокусливіші виміри часто є найнебезпечнішими: сирі URL, ідентифікатори користувачів, імена подів у короткоживучих навантаженнях або ідентифікатори запитів, які змінюються з кожним викликом. Стабільні виміри, такі як метод, код стану, шаблон маршруту, ім'я сервісу та простір імен, зазвичай зберігають корисне групування без створення нового часового ряду для кожного запиту.

Огляд експортера має відділяти питання доставки від питань формування даних. Якщо debug-вивід показує запис після обробки, Collector видав правильне корисне навантаження. Якщо бекенд його не отримує, дослідіть ендпоінт експортера, TLS, автентифікацію, підтримку стиснення, повторні спроби, мережеву політику та ліміти бекенду. Зміна фільтра чи перетворення на цьому етапі може замаскувати справжню проблему, бо шлях даних уже досяг межі експортера.

Налаштування повторних спроб особливо легко проґавити, бо вони звучать як покращення надійності за замовчуванням. Повторні спроби допомагають із тимчасовими збоями мережі чи бекенду, але вони також споживають пам'ять і можуть збільшити тиск, коли бекенд уже нездоровий. Продакшн-шлюз повинен мати поведінку повторних спроб, що відповідає очікуванням бекенду, рішення щодо черг, що відповідають лімітам пам'яті, та оповіщення, що відрізняють тимчасові збої надсилання від тривалого збою експортера.

Перевірки працездатності потребують подібної скромності. Успішна проба liveness означає, що процес Collector може відповісти розширенню працездатності; вона не означає, що кожен приймач приймає дані чи кожен експортер їх доставляє. Проби readiness все одно важливі, бо Kubernetes потребує сигналу для рішень про розгортання та перезапуск, але валідація конвеєра повинна надходити з власної телеметрії Collector та з відомих тестових записів, що проходять налаштованими шляхами.

Розмір ресурсів слід переглядати з огляду на обсяг сигналів, а не копіювати зі зразка. Агент вузла, який читає логи, може зазнавати сплесків під час циклів падіння, тоді як шлюз, що виконує tail-семплінг, утримує стан трейсу, доки не спливе `decision_wait`. Ліміти пам'яті, ліміти сплесків, розміри пакетів та буфери семплінгу взаємодіють, тож конфігурація, яка працює для невеликого простору імен, може не пережити завантажений кластер без налаштування.

RBAC — це ще одна підказка про розміщення. Приймачу filelog потрібен доступ у стилі hostPath та планування на вузлі; приймачу кластера Kubernetes потрібні дозволи API; Collector, керованому Operator, потрібні дозволи, що відповідають об'єктам, які він узгоджує. Якщо дизайн надає кожному екземпляру Collector широкі дозволи, бо вони потрібні одному приймачу, перегляньте розміщення. Поділ обов'язків агента та шлюзу часто зменшує і навантаження під час виконання, і обсяг дозволів.

Огляд версій важливий, бо приклади Collector швидко старіють. Структура в цьому модулі стабільна, але імена компонентів, рівні зрілості та версії образів слід перевіряти за документацією OpenTelemetry перед продакшн-розгортанням. Версія Kubernetes 1.35 не змінює основного міркування про DaemonSet та Deployment, проте кластери можуть відрізнятися політикою допуску, налаштуваннями Pod Security та мережевою політикою, що впливають на те, як Collector дозволено запускати.

Нарешті, напишіть план відкату в термінах потоку даних. Якщо перетворення ламає дашборди, ви маєте знати, чи видаляти лише цей процесор, видаляти його з одного конвеєра сигналу, чи переключити вивід експортера назад на debug для валідації. Якщо семплінг шлюзу втрачає трейси, ви маєте знати, чи виправлення — це афінність маршрутизації, параметри семплінгу, чи тимчасовий обхід tail-семплінгу. Відкат Collector, який просто перерозгортає попередній YAML, може бути достатнім, але огляд має визначити найменше безпечне зворотне діяння.

Цей патерн огляду — це також те, як ви відповідаєте на питання-сценарії під тиском іспиту. Визначте сигнал, знайдіть розміщення Collector, простежте порядок конвеєра, перевірте напрямок конектора, потім огляньте поверхні експортера та діагностики. Деталі різняться від питання до питання, але ця послідовність утримує вас від того, щоб вважати справний под справним шляхом телеметрії чи вважати симптом бекенду помилкою інструментування застосунку.

Є ще одна звичка, варта практики, перш ніж ви залишите огляд: назвіть докази, які змінили б вашу думку. Якщо ви вважаєте, що фільтр відкидає спани, доказом є лічильник відкинутого процесором або порівняння debug до й після цього процесора. Якщо ви вважаєте, що бекенд відхиляє дані, доказом є метрики збоїв експортера або логи відхилення з боку бекенду, тоді як debug-вивід досі показує оброблені записи. Чіткі цілі для доказів утримують усунення несправностей від перетворення на послідовність спекулятивних правок YAML.

Той самий доказовий спосіб мислення покращує комунікацію змін. Замість того щоб казати «ми додали tail-семплінг», скажіть «ми додали tail-семплінг на шлюзі, спрямували трейси за ідентифікатором трейсу, зберегли помилки та повільні трейси та перевірили лічильники прийнятого, відкинутого, надісланого й невдалого під час розгортання». Це речення каже рецензентам, що змінилося, де воно працює, чому це безпечно та як команда це перевірила. Хороша експлуатація Collector часто менше про хитру конфігурацію, а більше про те, щоб зробити кожне припущення про потік даних спостережуваним.

## Патерни та антипатерни

Сильні дизайни Collector зазвичай нудні в найкращому сенсі: агенти вузлів збирають те, що можуть бачити лише вузли, шлюзи виконують централізовану політику, процесори впорядковані за зменшенням ризику, а поверхні налагодження залишаються доступними під час розгортання. Наведені нижче патерни — це не декоративні правила архітектури; це операційні скорочення, які зменшують неоднозначність, коли телеметрія зникає, дублюється чи переповнює бекенд.

| Патерн | Коли його використовувати | Чому він працює | Міркування щодо масштабування |
|---------|----------------|--------------|-----------------------|
| Агент плюс шлюз | Кластери з логами, метриками хоста та розподіленими трейсами | Агенти збирають локальні дані, тоді як шлюзи централізують семплінг та маршрутизацію | Масштабуйте агенти разом із вузлами, а шлюзи — разом із обсягом телеметрії |
| Memory limiter першим, batch останнім | Майже кожен конвеєр трейсів, метрик чи логів | Collector відхиляє тиск до буферизації та ефективно експортує після обробки | Налаштовуйте ліміти щодо запитів пам'яті пода та пропускної здатності бекенду |
| Debug-дзеркало під час розгортання | Нові фільтри, перетворення, конектори чи експортери | Ви можете оглянути записи, перш ніж звинувачувати застосунки чи бекенди | Зменшуйте багатослівність після валідації, щоб контролювати обсяг логів |
| Маршрутизація шлюзу з урахуванням trace ID | Tail-семплінг із більш ніж однією реплікою шлюзу | Усі спани одного трейсу досягають тієї самої точки рішення про семплінг | Використовуйте headless Service або стратегію резолвера, що відкриває репліки |

Антипатерни часто починаються як зручність. Команда запускає Contrib скрізь, бо це легко, розміщує tail-семплінг на агентах, бо агенти вже розгорнуті, або залишає широкий фільтр неперевіреним, бо Collector лишався у стані Ready. Ці вибори зрозумілі під час експериментів, але вони створюють плутанину, коли система стає частиною реагування на інциденти.

| Антипатерн | Що йде не так | Краща альтернатива |
|--------------|-----------------|--------------------|
| Запуск глобальних приймачів на кожному агенті | Дубльовані метрики та зайве навантаження на сервер API | Запускайте загальнокластерні приймачі в шлюзі чи єдиному узгодженому екземплярі |
| Сприйняття перевірок працездатності як валідації конвеєра | Процес живий, навіть коли телеметрія відкидається | Використовуйте debug-експортер, zpages та внутрішні метрики для валідації потоку даних |
| Використання вимірів, специфічних для запиту, у spanmetrics | Кардинальність метрик зростає надто швидко | Використовуйте стабільні виміри, такі як метод, код стану, сервіс та шаблони маршрутів |
| Постійне утримання широких збірок Contrib | Більша поверхня залежностей та невикористані компоненти | Зберіть власний Collector, щойно набір продакшн-компонентів стабілізується |

## Каркас прийняття рішень

Рішення щодо Collector стають керованими, коли ви відділяєте джерело даних, політику обробки та обмеження експорту. Спершу запитайте, звідки походить телеметрія та яке розміщення Collector може її бачити. Потім вирішіть, чи потребують записи локального захисту, центральної агрегації, семплінгу, редагування, похідних метрик чи маршрутизації, специфічної для бекенду. Нарешті, оберіть транспорт та дистрибутив, що відповідають вашій мережі й операційній зрілості.

| Рішення | Оберіть це | Коли обмеження виглядають так |
|----------|-------------|-------------------------------------|
| Розміщення | Агент DaemonSet | Логи вузла, метрики хоста, буферизація на вузлі або збір із низькою латентністю близько до навантажень |
| Розміщення | Шлюз Deployment | Tail-семплінг, централізована маршрутизація, спільна автентифікація, spanmetrics або розгалуження на бекенди |
| Транспорт | OTLP/gRPC | Внутрішній трафік, підтримка HTTP/2, висока пропускна здатність, шляхи «Collector — Collector» |
| Транспорт | OTLP/HTTP | Браузерна телеметрія, проксі лише з HTTP, налагодження JSON, простий граничний прийом |
| Дистрибутив | Core | Мінімальний набір компонентів та чутлива до безпеки база |
| Дистрибутив | Contrib | Дослідження, лабораторії або інтеграції, відсутні в Core |
| Дистрибутив | Custom | Стабільний продакшн-конвеєр із явним контролем залежностей |

Використовуйте цей ментальний потік, коли питання-сценарій дає вам більше інформації, ніж потрібно. Якщо проблема згадує відсутність повних трейсів після масштабування шлюзів, погляньте на маршрутизацію трейсів, перш ніж змінювати політику семплінгу. Якщо вона згадує дубльовані метрики кластера, погляньте на розміщення приймачів, перш ніж торкатися запитів Prometheus. Якщо вона згадує збої експортера, тоді як debug-вивід досі показує записи, зосередьтеся на транспорті, облікових даних, TLS, доступності бекенду та поведінці повторних спроб.

```
Telemetry source?
  ├─ Node-local files or host metrics ──▶ Agent DaemonSet
  │                                      └─ Forward to gateway for shared policy
  ├─ Application OTLP signals ─────────▶ Agent or gateway, based on latency and ownership
  │                                      └─ Use OTLP/gRPC internally when possible
  └─ Cluster-wide API metrics ─────────▶ Gateway or single collector instance
                                         └─ Avoid per-node duplication

Need tail sampling or spanmetrics?
  ├─ Yes ──▶ Gateway with trace-aware routing and enough memory
  └─ No ───▶ Keep processing close to source unless backend policy needs centralization
```

Каркас навмисно компактний, бо реальні інциденти не чекають, доки ви милуєтеся ідеальною діаграмою архітектури. Почніть з видимості, потім розміщення, потім порядок, потім експорт. Ця послідовність утримує вас від виправлення неправильного рівня, що є найпоширенішим режимом відмови, коли конфігурація Collector — це коректний YAML, але некоректна експлуатація.

## Чи знали ви?

- OTLP/gRPC та OTLP/HTTP використовують різні порти за замовчуванням: 4317 для gRPC та 4318 для HTTP, і багато сценаріїв іспиту залежать від розпізнавання того, який транспорт описується.
- Конектор `spanmetrics` перетворює дані трейсів на метрики у стилі RED, тож один конвеєр трейсів може також живити метрики частоти запитів, помилок та тривалості у конвеєр метрик.
- Collector має моделі дистрибутивів Core, Contrib та власну; Contrib включає 200+ компонентів, тоді як `ocb` дозволяє продакшн-командам компілювати лише ті компоненти, які вони використовують.
- zpages відкриває живі шляхи налагодження, такі як `/debug/pipelinez` та `/debug/tracez` на порту 55679, коли розширення ввімкнено.

## Типові помилки

| Помилка | Чому вона трапляється | Як її виправити |
|---------|----------------|---------------|
| Оголошення компонента, але не додавання його до конвеєра | Конфігурація верхнього рівня читається так, ніби компонент активний, але `service.pipelines` — це справжнє з'єднання | Завжди простежуйте відповідний сигнал через приймачі, процесори, конектори та експортери в `service` |
| Розміщення `batch` перед `memory_limiter` | Пакетування відчувається як універсальна оптимізація, тож його додають першим | Розмістіть `memory_limiter` рано, а `batch` пізно, щоб тиск контролювався до зростання буферизації |
| Запуск tail-семплінгу на агентах | Агенти вже розгорнуті на кожному вузлі, тож семплінг здається близьким до джерела | Запускайте tail-семплінг на шлюзах та використовуйте маршрутизацію з урахуванням trace ID між репліками шлюзу |
| Запуск `k8s_cluster` на кожному вузлі | Команди копіюють той самий набір приймачів у кожен режим Collector | Запускайте загальнокластерні приймачі в одному розміщенні у стилі шлюзу з правильним RBAC |
| Забування `error_mode: ignore` на процесорах filter чи transform | Приклади правил працюють на чистих даних під час тестування | Свідомо налаштовуйте обробку помилок та валідуйте некоректні чи неочікувані записи за допомогою debug-виводу |
| Підвищення нестабільних атрибутів до міток Prometheus | Перетворення «ресурс у телеметрію» виглядає зручним для кожного атрибута | Підвищуйте лише обмежені, стабільні виміри, такі як сервіс, простір імен, метод та шаблони маршрутів |
| Сприйняття готовності пода як доказу доставки телеметрії | Kubernetes може лише сказати, що процес Collector відповідає | Перевіряйте вивід debug-експортера, zpages та внутрішні метрики `otelcol_*` на предмет фактичного потоку даних |
| Утримання широкого образу Contrib після стабілізації конвеєра | Це прискорює раннє експериментування і ніколи не переглядається | Перейдіть на власну збірку Collector, коли вибір компонентів та право власності на релізи дозріли |

## Тест

<details>
<summary>Питання 1: Ваша команда проєктує конфігурацію Collector із кількома конвеєрами для трейсів, метрик та логів, але новий процесор `filter/healthz` не змінює вивід трейсів. Що ви перевіряєте першим?</summary>

Перевірте, чи перелічено `filter/healthz` у `service.pipelines.traces.processors`, а не лише оголошено в блоці `processors` верхнього рівня. Компонент Collector існує лише як інвентар, доки конвеєр на нього не посилається. Якщо процесор присутній у неправильному конвеєрі сигналу, він усе одно не вплине на трейси, навіть якщо конфігурація може успішно завантажитися. Підтвердивши з'єднання конвеєра, використайте debug-експортер, щоб порівняти записи до й після процесора.
</details>

<details>
<summary>Питання 2: Deployment-шлюз масштабували до кількох реплік, і tail-семплінг почав пропускати повільні трейси. Політика досі каже зберігати повільні трейси. Яка проблема дизайну найімовірніша?</summary>

Імовірна проблема в тому, що спани з одного трейсу розділяються між репліками шлюзу до того, як їх побачить процесор `tail_sampling`. Tail-семплінгу потрібно достатньо завершеного трейсу, щоб ухвалити правильне рішення, тож шлях «агент — шлюз» повинен використовувати маршрутизацію з урахуванням trace ID, як-от експортер балансування навантаження. Зміна порогу латентності не виправить неповної видимості трейсу. Додавання більшої кількості реплік може погіршити проблему, якщо маршрутизація не зберігає афінність трейсу.
</details>

<details>
<summary>Питання 3: Ви налаштовуєте просунуті процесори для зменшення обсягу, але експортер повідомляє про меншу кількість спанів, ніж очікувалося, після розгортання перетворення. Які сигнали допомагають діагностувати, чи дані були відкинуті всередині Collector, чи відхилені бекендом?</summary>

Порівняйте внутрішні метрики Collector на етапах приймача, процесора та експортера. `otelcol_receiver_accepted_spans` показує, чи спани увійшли, `otelcol_processor_dropped_spans` показує, чи процесор їх видалив, `otelcol_exporter_sent_spans` показує успішний експорт, а `otelcol_exporter_send_failed_spans` вказує на збій бекенду чи мережі. Debug-експортер також може віддзеркалити репрезентативні записи, щоб ви могли оглянути перетворені атрибути. Цей підхід звужує рівень збою, перш ніж ви зміните інструментування застосунку.
</details>

<details>
<summary>Питання 4: Кластеру Kubernetes 1.35 потрібні логи контейнерів, метрики хоста, spanmetrics та tail-семплінг. Як би ви розгорнули Collector і чому?</summary>

Використайте агент DaemonSet для логів контейнерів та метрик хоста, бо ці джерела даних локальні для вузла, потім пересилайте до Deployment-шлюзу для spanmetrics та tail-семплінгу. Шлюз може централізувати похідні метрики, рішення про семплінг, маршрутизацію та автентифікацію бекенду. Tail-семплінг не слід запускати на агентах, бо кожен агент може бачити лише частину розподіленого трейсу. Цей поділ також дозволяє масштабувати шлюзи незалежно від кількості вузлів.
</details>

<details>
<summary>Питання 5: Браузерний застосунок не може надсилати OTLP/gRPC через корпоративний проксі, але команда все одно хоче нативного для OpenTelemetry прийому. Який транспорт OTLP ви оцінюєте і який компроміс приймаєте?</summary>

Оцініть OTLP/HTTP на порту 4318, бо він працює через звичайну HTTP-інфраструктуру та підтримує шляхи на кшталт `/v1/traces`. Компроміс у тому, що він може не давати тих самих характеристик внутрішньої пропускної здатності, що й gRPC, і вам потрібно ретельно налаштувати граничні аспекти, такі як CORS, автентифікація, стиснення та ліміти частоти. Для внутрішнього трафіку «Collector — Collector» OTLP/gRPC лишається сильним стандартом за замовчуванням, коли HTTP/2 підтримується. Вибір транспорту слідує за мережевим обмеженням, а не за універсальним уподобанням.
</details>

<details>
<summary>Питання 6: Ваш конектор spanmetrics виробляє набагато більше рядів метрик, ніж очікувалося, після додавання URL запиту як виміру. Що не так із дизайном?</summary>

Конектор використовує нестабільний вимір високої кардинальності. Сирі URL запитів можуть містити ідентифікатори, рядки запиту та інші значення, специфічні для запиту, тож виведення метрик із них може створити велику кількість часових рядів. Натомість використовуйте стабільні виміри, такі як `http.method`, `http.status_code`, ім'я сервісу та шаблони маршрутів. Конектор корисний, але він успадковує ту саму дисципліну кардинальності, що потрібна для будь-якого конвеєра метрик.
</details>

<details>
<summary>Питання 7: Огляд безпеки запитує, чому продакшн-Collector досі використовують дистрибутив Contrib, хоча конвеєру потрібні лише OTLP, filelog, memory limiter, batch, transform, debug та один експортер OTLP. Що ви запропонуєте?</summary>

Запропонуйте зібрати власний Collector за допомогою `ocb`, щойно набір компонентів та процес релізу стануть стабільними. Contrib корисний під час дослідження, бо включає багато інтеграцій, але він також постачає багато компонентів, які продакшн-конвеєр може ніколи не використати. Власна збірка зменшує розмір бінарника та поверхню залежностей, водночас зберігаючи потрібні приймачі, процесори та експортери явними. Пропозиція має включати право власності на оновлення, бо власний дистрибутив усе одно мусить відстежувати релізи OpenTelemetry.
</details>

## Практична вправа: побудова багатосигнального конвеєра

Сценарій вправи: ви готуєте невеликий простір імен спостережуваності для команди, яка хоче один Collector, що приймає трейси, метрики та логи через OTLP, генерує метрики, похідні від спанів, та надає достатньо діагностики, щоб довести роботу конвеєра, перш ніж буде додано бекенд. Лабораторія використовує debug-вивід замість вендорського бекенду, тож ви можете зосередитися на поведінці Collector. Той самий патерн валідації застосовується, коли ви пізніше заміните `debug` на продакшн-експортери.

### Налаштування

Вам потрібен робочий кластер Kubernetes, `kubectl` та можливість створити простір імен. Наведені нижче команди використовують kind для одноразового локального кластера, але ви можете пропустити першу команду, якщо у вас уже є лабораторний кластер. Тримайте Collector у просторі імен `observability`, щоб подальше очищення було простим, а імена Service збігалися з прикладами.

```bash
# Create a kind cluster (skip if you already have one)
kind create cluster --name otel-lab

# Create namespace
kubectl create namespace observability
```

### Завдання 1: розгорніть Collector

Застосуйте ConfigMap, Deployment та Service однією командою. Конфігурація включає приймачі OTLP для всіх сигналів, процесори `memory_limiter` та `batch`, конектор `spanmetrics`, debug-експортери, перевірки працездатності, zpages та внутрішні метрики. Прочитайте секцію `service.pipelines` перед застосуванням, щоб передбачити, які компоненти активні для кожного сигналу.

```bash
kubectl apply -n observability -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      memory_limiter:
        check_interval: 1s
        limit_mib: 256
        spike_limit_mib: 64
      batch:
        send_batch_size: 1024
        timeout: 1s

    connectors:
      spanmetrics:
        dimensions:
          - name: http.method

    exporters:
      debug:
        verbosity: detailed

    extensions:
      health_check:
        endpoint: 0.0.0.0:13133
      zpages:
        endpoint: 0.0.0.0:55679

    service:
      extensions: [health_check, zpages]
      telemetry:
        metrics:
          address: 0.0.0.0:8888
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [debug, spanmetrics]
        metrics:
          receivers: [otlp, spanmetrics]
          processors: [memory_limiter, batch]
          exporters: [debug]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [debug]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.98.0
          args: ["--config=/etc/otel/config.yaml"]
          ports:
            - containerPort: 4317
            - containerPort: 4318
            - containerPort: 13133
            - containerPort: 55679
          volumeMounts:
            - name: config
              mountPath: /etc/otel
          livenessProbe:
            httpGet:
              path: /
              port: 13133
          readinessProbe:
            httpGet:
              path: /
              port: 13133
      volumes:
        - name: config
          configMap:
            name: otel-collector-config
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
spec:
  selector:
    app: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
    - name: otlp-http
      port: 4318
    - name: health
      port: 13133
    - name: zpages
      port: 55679
EOF
```

<details>
<summary>Нотатки до розв'язання Завдання 1</summary>

Deployment має створити один под Collector, а проба readiness має проходити через розширення перевірки працездатності. Якщо под не переходить у стан Ready, спершу перевірте логи на наявність помилок розбору конфігурації, бо Collector валідує імена компонентів та посилання конвеєра під час запуску. Успішне розгортання ще не доводить, що телеметрія тече; воно лише доводить, що процес завантажився і розширення працездатності відповіло.
</details>

### Завдання 2: надішліть тестову телеметрію

Дочекайтеся готовності, прокиньте порт Service OTLP/HTTP та надішліть мінімальне корисне навантаження трейсу. Навантаження використовує фіксоване ім'я сервісу та атрибут методу HTTP, щоб debug-експортер та конектор spanmetrics мали видимі дані для роботи. Перед запуском команди curl передбачте, де ви очікуєте побачити трейс і який похідний конвеєр метрик також має отримати сигнал.

```bash
# Wait for the collector to be ready
kubectl wait --for=condition=ready pod -l app=otel-collector -n observability --timeout=60s

# Port-forward to send data
kubectl port-forward -n observability svc/otel-collector 4318:4318 &

# Send a test trace via OTLP/HTTP
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test-service"}}]},
      "scopeSpans": [{
        "spans": [{
          "traceId": "5b8aa5a2d2c872e8321cf37308d69df2",
          "spanId": "051581bf3cb55c13",
          "name": "GET /api/users",
          "kind": 2,
          "startTimeUnixNano": "1000000000",
          "endTimeUnixNano": "2000000000",
          "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": "200"}}
          ]
        }]
      }]
    }]
  }'
```

<details>
<summary>Нотатки до розв'язання Завдання 2</summary>

HTTP-запит має повернути успішну відповідь від приймача Collector. Якщо він не вдається, перевірте, чи досі працює прокидання порту і чи Service відкриває порт 4318. Якщо запит успішний, але в логах нічого не з'являється, переконайтеся, що конвеєр трейсів експортує до `debug` і що под Collector, який ви читаєте, — це поточний под у стані Ready.
</details>

### Завдання 3: перевірте поведінку конвеєра

Використайте три незалежні перевірки: debug-логи для запису трейсу, zpages для активних конвеєрів та внутрішні метрики для прийнятих спанів. Така тріангуляція надійніша за єдину перевірку, бо кожна поверхня відповідає на інше питання. Логи показують репрезентативний вміст навантаження, zpages показують структуру конвеєра, а метрики показують лічильники, які можна використати в оповіщеннях.

```bash
# Check collector logs — you should see the trace in debug output
kubectl logs -n observability -l app=otel-collector --tail=50

# Check zpages
kubectl port-forward -n observability svc/otel-collector 55679:55679 &
# Open http://localhost:55679/debug/pipelinez in your browser

# Check Collector's own metrics
kubectl port-forward -n observability svc/otel-collector 8888:8888 &
curl -s http://localhost:8888/metrics | grep otelcol_receiver_accepted
```

<details>
<summary>Нотатки до розв'язання Завдання 3</summary>

Ви маєте побачити тестовий спан у логах Collector, усі три конвеєри, перелічені в zpages, та лічильники прийнятого приймачем у ендпоінті внутрішніх метрик. Якщо debug-логи показують трейс, а внутрішні метрики — ні, переконайтеся, що адресу телеметрії метрик відкрито подом та правильно прокинуто порт. Якщо zpages недосяжні, перевірте, що розширення ввімкнено в `service.extensions`, а не лише оголошено в `extensions`.
</details>

### Завдання 4: поясніть продакшн-зміни

Запишіть зміни, які ви зробили б, перш ніж перенести цей лабораторний патерн у продакшн. Подумайте, де б ви розділили обов'язки агента та шлюзу, чи зберегли б ви Contrib, чи зібрали б власний Collector, який експортер замінив би `debug`, як би ви захистили облікові дані та які метрики стали б оповіщеннями. Це завдання змушує вас пов'язати робочу лабораторію з каркасом проєктування, а не ставитися до неї як до маніфесту для копіювання-вставлення.

<details>
<summary>Нотатки до розв'язання Завдання 4</summary>

Продакшн-дизайн зазвичай запускав би агенти вузлів для файлових логів та метрик хоста, а потім пересилав би до шлюзів для семплінгу, spanmetrics, маршрутизації та експорту в бекенди. Debug-вивід став би тимчасовим чи семпльованим, облікові дані перемістилися б у Secrets або зовнішнє керування секретами, а внутрішні метрики Collector живили б оповіщення для прийнятої, відкинутої, надісланої та невдалої телеметрії. Стабільний конвеєр також має розглянути власний дистрибутив Collector замість постійного утримання широкого образу Contrib.
</details>

### Критерії успіху

- [ ] Проєктувати конфігурації Collector із кількома конвеєрами, простежуючи трейси, метрики та логи лабораторії через активні записи `service.pipelines`.
- [ ] Налаштовувати просунуті процесори, пояснюючи, чому `memory_limiter` з'являється перед `batch` і де б вписалися `filter`, `transform` чи `tail_sampling`.
- [ ] Розгортати навантаження Collector у Kubernetes 1.35 та пояснювати, коли цей Deployment має стати агентом DaemonSet, шлюзом Deployment або обома.
- [ ] Діагностувати проблеми конвеєра Collector за допомогою debug-логів, zpages та внутрішніх метрик `otelcol_*`, а не покладаючись лише на готовність пода.
- [ ] Оцінювати транспорти OTLP, конектори та дистрибутиви, обираючи продакшн-експортер, набір вимірів spanmetrics та пакування Collector Core, Contrib чи власне.

## Джерела

- [Конфігурація OpenTelemetry Collector](https://opentelemetry.io/docs/collector/configuration/)
- [Розгортання OpenTelemetry Collector](https://opentelemetry.io/docs/collector/deployment/)
- [Специфікація протоколу OpenTelemetry](https://opentelemetry.io/docs/specs/otlp/)
- [Документація з перетворення телеметрії OpenTelemetry Collector](https://opentelemetry.io/docs/collector/transforming-telemetry/)
- [Процесор batch OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector/tree/main/processor/batchprocessor)
- [Процесор memory limiter OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector/tree/main/processor/memorylimiterprocessor)
- [Процесор tail sampling OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor)
- [Конектор spanmetrics OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/connector/spanmetricsconnector)
- [OpenTelemetry Operator](https://github.com/open-telemetry/opentelemetry-operator)
- [OpenTelemetry Collector Builder](https://opentelemetry.io/docs/collector/custom-collector/)
- [Документація Kubernetes DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Документація Kubernetes Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

## Перевірка для учня

> Під `connectors.count` імена метрик є ключами мапи (`span.count`, `log.record.count`) безпосередньо під `spans` та `logs` — немає обгортки `traces:` і немає елементів списку з `name:`.

> Instrumentation надається за адресою opentelemetry.io/v1alpha1; OpenTelemetryCollector (не Instrumentation) додав версію API v1beta1.

> Логи експортуються до Loki через otlphttp/loki за адресою http://loki…:3100/otlp, бо Loki приймає OTLP лише через HTTP, а не OTLP/gRPC на :3100.

## Наступний модуль

[Огляд напрямку OTCA](/k8s/otca/) — перегляньте всі чотири домени OTCA та продовжте з модулями інструментарію спостережуваності.







