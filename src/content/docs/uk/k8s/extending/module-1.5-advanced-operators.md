---
title: "Модуль 1.5: Просунута розробка операторів"
slug: "uk/k8s/extending/module-1.5-advanced-operators"
sidebar:
  order: 6
revision_pending: false
en_commit: "1c9b04bcf41904149faa0dbeb61b635c351ec080"
en_file: "src/content/docs/k8s/extending/module-1.5-advanced-operators.md"
calque_review:
  reviewed_at: "2026-06-22"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 1
  content_sha: "3689a6c29bd5b2950752cd09716761721bcbc7d9543fc4c47cdd24e704edb7d2"
---

> **Складність**: `[СКЛАДНИЙ]` — патерни операторів продакшн-рівня
>
> **Час на проходження**: 5 годин
>
> **Передумови**: Модуль 1.4 (Kubebuilder), основи тестування на Go та кластер Kubernetes 1.35+ для ручної перевірки

---

## Результати навчання

Після проходження цього модуля ви зможете:

1. **Реалізувати** фіналайзери, які чисто видаляють зовнішні ресурси, такі як DNS-записи, хмарні балансувальники навантаження та об'єкти моніторингу, перш ніж кастомний ресурс буде видалено.
2. **Спроєктувати** структуровані умови статусу (status conditions), які відповідають конвенціям Kubernetes API, щоб користувачі могли діагностувати готовність, розбіжність поколінь (generation drift) та збої узгодження за допомогою `kubectl describe`.
3. **Налаштувати** вибір лідера (leader election), спостереження за власними ресурсами та запис подій так, щоб оператор із кількома репліками залишався спостережуваним і уникав узгодження за схемою «розщеплений мозок» (split-brain).
4. **Побудувати** інтеграційні тести на envtest, які перевіряють створення, оновлення, статус та очищення фіналайзера через увесь життєвий цикл узгодження.

## Чому цей модуль важливий

Гіпотетичний сценарій: ваша платформна команда перевела оператор WebApp із Модуля 1.4 у спільний кластер розробки, і команди тепер покладаються на нього для створення Деплойментів, Сервісів, опціональних об'єктів Ingress, DNS-записів та дашбордів моніторингу. Перше видалення виглядає нешкідливо: розробник запускає `kubectl delete webapp checkout`, кастомний ресурс зникає зі звичного списку, і всі рухаються далі. Згодом DNS-ім'я все ще вказує на стару кінцеву точку, зовнішній дашборд залишається в системі моніторингу, а наступне розгортання провалюється, бо оператор так і не очистив ресурси, якими сам Kubernetes не володів.

Цей збій є межею між демонстраційним контролером і продакшн-оператором. Збирання сміття (garbage collection) у Kubernetes може видаляти залежні об'єкти Kubernetes, коли посилання на власника (owner references) коректні, але воно не може звернутися до вашого DNS-провайдера, видалити керовану базу даних чи прибрати дашборд у іншому API. Фіналайзери дають вашому контролеру навмисне вікно для очищення, перш ніж сервер API остаточно вилучить кастомний ресурс з etcd; умови статусу дають користувачам поточну діагностику, не змушуючи їх занурюватися в логи контролера; події дають коротку операційну хронологію; а вибір лідера не дає двом реплікам контролера змагатися за один і той самий бажаний стан.

Цей модуль переписує оператор WebApp навколо цих продакшн-обов'язків. Ви збережете модель узгодження з Модуля 1.4, але додасте обробку видалення перед звичайним узгодженням, оновлення умов після того, як оператор оцінює дочірні ресурси, генерацію подій у моменти, коли користувачам потрібен аудиторський слід, налаштування високої доступності для менеджера, правила спостереження за пов'язаними ресурсами та покриття envtest, що проганяє контролер проти реального сервера API та etcd. Мета не в тому, щоб завчити фрагменти коду; мета в тому, щоб оцінити, де у життєвому циклі належить кожен патерн, і уникнути проєктів, які виглядають коректними рівно до першого збою чи застряглого видалення.

## Фіналайзери: робимо видалення шляхом узгодження

Фіналайзери працюють тому, що видалення в Kubernetes не є єдиною операцією, коли присутні фіналайзери. Коли користувач видаляє об'єкт, сервер API встановлює `metadata.deletionTimestamp`, залишає об'єкт у сховищі й чекає, доки кожен запис у `metadata.finalizers` не буде видалено. Ваш контролер бачить той самий об'єкт знову, але тепер він представляє запит на очищення, а не звичайний запит бажаного стану. Це означає, що логіка фіналайзера має виконуватися перед рештою узгодження, бо створення чи оновлення дочірніх ресурсів, поки батьківський об'єкт завершується, зазвичай створює більше роботи для шляху очищення.

Корисна ментальна модель — це контрольний список виїзду з квартири. Kubernetes готовий прибрати запис про квартиру, але ваш контролер каже: «притримай запис, поки я не поверну ключі, не скасую комунальні послуги й не переадресую пошту». Якщо очищення вдається, контролер видаляє лише власний фіналайзер і дозволяє серверу API продовжити видалення. Якщо очищення зазнає невдачі, фіналайзер залишається прикріпленим, об'єкт лишається в стані завершення, а controller-runtime повторює запит на узгодження з відкладанням (backoff). Саме така поведінка повторів є причиною, чому очищення фіналайзера має бути ідемпотентним: видалення відсутнього DNS-запису зазвичай слід трактувати як успіх, тоді як тимчасова помилка провайдера має повернути помилку, щоб черга спробувала знову.

```
User runs: kubectl delete webapp my-app
    │
    ▼
API Server sets deletionTimestamp (object is "terminating")
    │
    ├── Finalizers list is NOT empty?
    │       │
    │       ▼
    │   Object stays in etcd with deletionTimestamp set
    │   Controller sees the deletionTimestamp
    │   Controller performs cleanup
    │   Controller removes its finalizer from the list
    │       │
    │       ├── More finalizers remain? → Wait for other controllers
    │       │
    │       └── No finalizers left? ─────────────┐
    │                                             │
    ├── Finalizers list IS empty? ────────────────┤
    │                                             │
    │                                             ▼
    │                                    Object removed from etcd
    │                                    Garbage collector deletes owned resources
    └─────────────────────────────────────────────────────────────
```

Зупиніться й передбачте: якщо логіка очищення зазнає невдачі, а ви все одно видалите фіналайзер, що Kubernetes зробить далі, і яка система все ще пам'ятатиме про зовнішній ресурс? Відповідь — це базове правило безпеки для фіналайзерів. Видалення фіналайзера є підтвердженням того, що очищення завершено, тому це має бути останній успішний крок, а не перший сповнений надії крок.

```go
// internal/controller/webapp_controller.go

const webappFinalizer = "apps.kubedojo.io/finalizer"

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	// Fetch the WebApp
	webapp := &appsv1beta1.WebApp{}
	if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	// ───── Finalizer Logic ─────

	// Check if the object is being deleted
	if !webapp.DeletionTimestamp.IsZero() {
		// Object is being deleted
		if controllerutil.ContainsFinalizer(webapp, webappFinalizer) {
			// Run cleanup logic
			logger.Info("Running finalizer cleanup", "webapp", webapp.Name)

			if err := r.cleanupExternalResources(ctx, webapp); err != nil {
				// If cleanup fails, don't remove the finalizer — retry
				logger.Error(err, "Failed to clean up external resources")
				return ctrl.Result{}, err
			}

			// Cleanup succeeded — remove the finalizer
			controllerutil.RemoveFinalizer(webapp, webappFinalizer)
			if err := r.Update(ctx, webapp); err != nil {
				return ctrl.Result{}, err
			}
			logger.Info("Finalizer removed, object will be deleted")
		}
		// Object is being deleted and our finalizer is gone — nothing to do
		return ctrl.Result{}, nil
	}

	// Object is NOT being deleted — ensure finalizer is present
	if !controllerutil.ContainsFinalizer(webapp, webappFinalizer) {
		controllerutil.AddFinalizer(webapp, webappFinalizer)
		if err := r.Update(ctx, webapp); err != nil {
			return ctrl.Result{}, err
		}
		logger.Info("Added finalizer")
		// Return and let the update trigger a new reconciliation
		return ctrl.Result{}, nil
	}

	// ───── Normal Reconciliation ─────
	// (rest of your reconcile logic from Module 1.4)

	return r.reconcileNormal(ctx, webapp)
}

func (r *WebAppReconciler) cleanupExternalResources(ctx context.Context, webapp *appsv1beta1.WebApp) error {
	logger := log.FromContext(ctx)

	// Example: Clean up external DNS records
	if webapp.Spec.Ingress != nil && webapp.Spec.Ingress.Host != "" {
		logger.Info("Cleaning up DNS record", "host", webapp.Spec.Ingress.Host)
		// In a real operator, call your DNS provider API here
		// if err := dnsClient.DeleteRecord(webapp.Spec.Ingress.Host); err != nil {
		//     return err
		// }
	}

	// Example: Clean up monitoring dashboards
	logger.Info("Cleaning up monitoring resources", "webapp", webapp.Name)
	// if err := monitoringClient.DeleteDashboard(webapp.Name); err != nil {
	//     return err
	// }

	// Example: Clean up external storage
	logger.Info("Cleaning up storage", "webapp", webapp.Name)

	return nil
}
```

Реалізація має дві навмисно розділені гілки. Гілка видалення обробляє об'єкт із `DeletionTimestamp` першою, бо жоден новий бажаний стан не слід створювати, поки очікується демонтаж. Звичайна гілка переконується, що фіналайзер існує, перш ніж буде створено будь-які зовнішні ресурси, а потім повертає керування, щоб подія оновлення запустила чистий другий прохід. Це раннє повернення уникає змішування «я змінив метадані об'єкта» зі «я створив дочірні ресурси» в одному виклику узгодження, що робить конфлікти й повтори простішими для осмислення.

| Практика | Чому |
|----------|-----|
| Використовуйте ім'я з кваліфікованим доменом | Уникає колізій: `apps.kubedojo.io/finalizer` |
| Спершу перевіряйте `DeletionTimestamp` | Завжди обробляйте видалення перед звичайним узгодженням |
| Повертайтеся раніше після додавання фіналайзера | Дозвольте спостереженню запустити чисте повторне узгодження |
| Логуйте дії очищення | Необхідно для діагностики застряглих видалень |
| Коректно обробляйте помилки очищення | Поверніть помилку для повтору, але уникайте нескінченних циклів |
| Встановлюйте тайм-аут на очищення | Зовнішні API можуть зависати; використовуйте контекст із тайм-аутом |

Фіналайзери також змінюють те, як ви думаєте про тайм-аути та часткові збої. Збій хмарного API не повинен спричиняти втрату даних, тому повернення помилки й утримання об'єкта в стані `Terminating` зазвичай є коректною поведінкою. Постійна відповідь «не знайдено» від зовнішнього API — це інша річ: якщо ресурсу вже немає, намір очищення задоволено, і контролер може видалити фіналайзер. Оператор має робити ці розрізнення явно, бо видалення кастомного ресурсу часто є моментом, коли користувачі найменш терплячі до неоднозначної поведінки.

Володіння фіналайзером також має бути вузьким. Ваш контролер повинен видаляти лише той рядок фіналайзера, яким він володіє, залишаючи фіналайзери інших контролерів недоторканими. Це важливо, коли кілька систем координуються навколо одного ресурсу, як-от контролер резервного копіювання, контролер політик і оператор WebApp. Якщо ваш код перезаписує весь список фіналайзерів, ви можете випадково сказати серверу API, що інша робота з очищення завершена, хоча вона ще навіть не починалася. Використовуйте допоміжні функції, які додають або видаляють один запис, і трактуйте конфлікти оновлення як звичайні повтори, а не як виняткове пошкодження.

Найнадійніші функції очищення написані як функції узгодження. Вони читають достатньо зовнішнього стану, щоб визначити, чи лишилася робота, виконують одну безпечну дію й повертають точний результат. Наприклад, допоміжна функція видалення DNS може знайти очікуваний запис, повернути успіх, якщо запису вже немає, видалити його, якщо він існує й відповідає метаданим власника WebApp, та повернути помилку, якщо провайдер не може відповісти. Така структура робить повтори безпечними й робить логи змістовними, бо кожен повтор є ще однією спробою привести зовнішню систему до бажаного стану «відсутній».

Вам слід уникати тривалого блокувального очищення всередині одного виклику узгодження, коли зовнішній API має повільні операції. Якщо видалення керованої бази даних потребує багатохвилинної асинхронної операції, фіналайзер може ініціювати видалення, записати умову на кшталт `CleanupPending`, видати подію типу Normal і повторно поставити в чергу через коротку затримку, щоб опитати прогрес. Об'єкт залишається в стані `Terminating`, але контролер не утримує горутину нескінченно й не приховує прогрес від користувачів. Важливе правило в тому, що фіналайзер залишається присутнім, доки зовнішня система не досягне безпечного термінального стану.

Фіналайзери не є заміною посилань на власника. Посилання на власника збирають як сміття лише об'єкти Kubernetes у тому ж кластері — вони не можуть каскадно видаляти зовнішні чи хмарні ресурси або об'єкти інших кластерів, що саме й є причиною існування фіналайзерів для такого очищення. Для дочірніх ресурсів Kubernetes, як-от Деплойменти та Сервіси, посилання на власника дозволяють вбудованому збиранню сміття зробити правильну річ після видалення батьківського об'єкта. Для ресурсів поза кластером або ресурсів, якими ви навмисно не володієте через метадані Kubernetes, фіналайзери є тим гачком, що дозволяє вашому контролеру брати участь у видаленні. Продакшн-оператори часто використовують обидва підходи: посилання на власника для внутрішньокластерних залежних об'єктів і фіналайзери для зовнішніх систем або порядку очищення, який збирання сміття виразити не може.

Коли видалення застрягає, опирайтеся рефлексу видалити фіналайзер вручну. Ручне видалення інколи є правильною аварійною дією, але до нього слід ставитися як до перевизначення з боку оператора з відомим боргом очищення, а не як до звичайного виправлення. Спершу прочитайте події об'єкта, логи контролера та умови статусу, щоб з'ясувати, чи функція очищення зазнає невдачі, перевищує тайм-аут чи чекає на залежність. Якщо ви все ж приберете фіналайзер під час інциденту, запишіть ідентифікатори зовнішнього ресурсу, щоб людина могла завершити очищення згодом.

Є також аспект досвіду користувача, пов'язаний із фіналайзерами. WebApp, який сидить у стані `Terminating` без оновлення статусу та без події, виглядає зламаним, навіть коли контролер ретельно захищає зовнішні ресурси. Хороший шлях видалення встановлює умову чи фазу, що називає прогрес очищення, видає подію початку очищення, логує зовнішні ідентифікатори, які очищаються, і видає подію завершення очищення перед видаленням фіналайзера. Користувачам не потрібен кожен внутрішній повтор, але їм потрібно достатньо видимості, щоб відрізнити «працює за задумом» від «застрягло назавжди».

## Умови статусу та події: поточний стан плюс хронологія

Умови статусу та події Kubernetes розв'язують пов'язані, але різні проблеми спостережуваності. Умова відповідає на питання: «що є правдою про цей об'єкт прямо зараз, і чи це твердження базується на найновішому поколінні специфікації?» Подія відповідає на питання: «яка помітна дія чи попередження сталося нещодавно?» Якщо ви перевантажите умови історією, статус стане шумним і складним для розбору автоматизацією. Якщо ви покладаєтеся лише на події, користувачі втрачають стабільний сигнал готовності, бо події застарівають і не є тривким контрактом для контролерів чи конвеєрів розгортання.

Kubernetes надає `metav1.Condition` як стандартну форму для сучасних кастомних ресурсів. Найважливіші поля — це не лише `Type` та `Status`; `ObservedGeneration` повідомляє користувачам, чи опрацював контролер найновішу специфікацію, `Reason` дає автоматизації стабільний токен у CamelCase, `Message` дає людям достатньо деталей для дії, а `LastTransitionTime` позначає фактичні зміни статусу, а не кожен цикл узгодження. Коли ці поля встановлено ретельно, `kubectl describe`, дашборди та інструменти GitOps усі можуть відповідати на кращі питання без вишкрібання логів.

```go
type Condition struct {
    // Type of condition (e.g., "Ready", "Available", "Degraded")
    Type string

    // Status: "True", "False", or "Unknown"
    Status ConditionStatus

    // ObservedGeneration: the generation this condition was set for
    ObservedGeneration int64

    // LastTransitionTime: when the status last changed
    LastTransitionTime metav1.Time

    // Reason: machine-readable CamelCase reason
    Reason string

    // Message: human-readable description
    Message string
}
```

Оператор WebApp потребує умов, які віддзеркалюють керовані ним ресурси, та однієї агрегованої умови, яку користувачі можуть трактувати як основну відповідь про готовність. `DeploymentReady` і `ServiceReady` чітко показують, який дочірній ресурс блокує готовність, тоді як `Ready` підсумовує, чи придатний WebApp загалом до використання. Ці назви умов мають позитивну полярність, бо позитивні умови краще поєднуються між собою: `Ready=False` легше осмислити, ніж `NotReady=True`, особливо коли автоматизація чекає, доки умова стане істинною.

```go
const (
	// ConditionTypeReady indicates the WebApp is fully operational.
	ConditionTypeReady = "Ready"

	// ConditionTypeDeploymentReady indicates the Deployment is ready.
	ConditionTypeDeploymentReady = "DeploymentReady"

	// ConditionTypeServiceReady indicates the Service is configured.
	ConditionTypeServiceReady = "ServiceReady"

	// ConditionTypeIngressReady indicates the Ingress is configured.
	ConditionTypeIngressReady = "IngressReady"
)

// Reasons for conditions
const (
	ReasonReconciling      = "Reconciling"
	ReasonAvailable        = "Available"
	ReasonDeploymentFailed = "DeploymentFailed"
	ReasonServiceFailed    = "ServiceFailed"
	ReasonScalingUp        = "ScalingUp"
	ReasonScalingDown      = "ScalingDown"
	ReasonImageUpdating    = "ImageUpdating"
	ReasonCleanupPending   = "CleanupPending"
	ReasonCleanupComplete  = "CleanupComplete"
)
```

Перш ніж прогнати наступну функцію подумки, зупиніться й передбачте: якщо користувач змінює образ WebApp і `metadata.generation` збільшується, що має зрозуміти конвеєр, коли `Ready=True` усе ще має попереднє значення `ObservedGeneration`? Він має трактувати цю готовність як застарілу для нової специфікації. Старий застосунок усе ще може бути справним, але контролер ще не довів новий запитаний стан.

```go
func (r *WebAppReconciler) updateConditions(ctx context.Context,
	webapp *appsv1beta1.WebApp,
	deployment *appsv1.Deployment) error {

	// Deployment condition
	deploymentCondition := metav1.Condition{
		Type:               ConditionTypeDeploymentReady,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
	}

	if deployment == nil {
		deploymentCondition.Status = metav1.ConditionFalse
		deploymentCondition.Reason = ReasonReconciling
		deploymentCondition.Message = "Deployment has not been created yet"
	} else if deployment.Status.ReadyReplicas == *deployment.Spec.Replicas {
		deploymentCondition.Status = metav1.ConditionTrue
		deploymentCondition.Reason = ReasonAvailable
		deploymentCondition.Message = fmt.Sprintf(
			"Deployment has %d/%d replicas ready",
			deployment.Status.ReadyReplicas,
			*deployment.Spec.Replicas)
	} else {
		deploymentCondition.Status = metav1.ConditionFalse
		deploymentCondition.Reason = ReasonScalingUp
		deploymentCondition.Message = fmt.Sprintf(
			"Deployment has %d/%d replicas ready, scaling in progress",
			deployment.Status.ReadyReplicas,
			*deployment.Spec.Replicas)
	}

	// Service condition (always true if we got this far)
	serviceCondition := metav1.Condition{
		Type:               ConditionTypeServiceReady,
		Status:             metav1.ConditionTrue,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
		Reason:             ReasonAvailable,
		Message:            "Service is configured",
	}

	// Overall Ready condition
	readyCondition := metav1.Condition{
		Type:               ConditionTypeReady,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
	}

	allReady := deploymentCondition.Status == metav1.ConditionTrue &&
		serviceCondition.Status == metav1.ConditionTrue

	if allReady {
		readyCondition.Status = metav1.ConditionTrue
		readyCondition.Reason = ReasonAvailable
		readyCondition.Message = "All components are ready"
		webapp.Status.Phase = "Running" // production code would use a typed phase constant
	} else {
		readyCondition.Status = metav1.ConditionFalse
		readyCondition.Reason = ReasonReconciling
		readyCondition.Message = "One or more components are not ready"
		webapp.Status.Phase = "Deploying"
	}

	// Apply conditions using the standard helper
	meta.SetStatusCondition(&webapp.Status.Conditions, deploymentCondition)
	meta.SetStatusCondition(&webapp.Status.Conditions, serviceCondition)
	meta.SetStatusCondition(&webapp.Status.Conditions, readyCondition)

	webapp.Status.ObservedGeneration = webapp.Generation

	return r.Status().Update(ctx, webapp)
}
```

Приклад використовує `meta.SetStatusCondition` замість додавання до зрізу (slice), бо масиви умов на практиці індексуються за `Type`. Додавання на кожному узгодженні створює дублікати, метушню з мітками часу та заплутаний вивід, де одна умова каже `Ready=True`, тоді як пізніша умова того ж типу каже `Ready=False`. Допоміжна функція також захищає семантику `LastTransitionTime`, оновлюючи час переходу, коли значення статусу змінюється, а не лише тому, що контролер перерахував той самий стан.

```bash
# View conditions
kubectl get webapp my-app -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.status}{"\t"}{.reason}{"\t"}{.message}{"\n"}{end}'

# Example output:
# DeploymentReady   True    Available       Deployment has 3/3 replicas ready
# ServiceReady      True    Available       Service is configured
# Ready             True    Available       All components are ready

# Check if ready using JSONPath
kubectl get webapp my-app -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

| Конвенція | Правило |
|-----------|------|
| Позитивна полярність | "Ready", а не "NotReady"; "Available", а не "Unavailable" |
| Reason у CamelCase | `ScalingUp`, а не `scaling_up` чи `Scaling Up` |
| Message читабельний для людини | Повні речення, включайте підрахунки й деталі |
| ObservedGeneration | Завжди встановлюйте на `obj.Generation` |
| LastTransitionTime | Змінюється лише при зміні Status, а не на кожне оновлення |
| Статус Unknown | Використовуйте, коли контролер не може визначити стан |

Події заповнюють розрив між стабільним статусом і детальними логами. Користувач, який запускає `kubectl describe webapp my-app`, має бачити ключові моменти, такі як створення Деплойменту, масштабування реплік, зміну образу, початок очищення, завершення очищення чи помилку, що блокує узгодження. Події навмисно є недовговічними операційними записами, тому вони не повинні бути єдиним джерелом істини, але часто це найшвидший спосіб для SRE побачити, що оператор нещодавно намагався зробити, без доступу до логів Под'а оператора.

```go
// internal/controller/webapp_controller.go
type WebAppReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder record.EventRecorder
}
```

```go
if err = (&controller.WebAppReconciler{
    Client:   mgr.GetClient(),
    Scheme:   mgr.GetScheme(),
    Recorder: mgr.GetEventRecorderFor("webapp-controller"),
}).SetupWithManager(mgr); err != nil {
    os.Exit(1)
}
```

```go
func (r *WebAppReconciler) reconcileNormal(ctx context.Context,
	webapp *appsv1beta1.WebApp) (ctrl.Result, error) {

	// On Deployment creation
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"DeploymentCreated",
		"Created Deployment %s with %d replicas",
		webapp.Name, *webapp.Spec.Replicas)

	// On scaling
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"Scaled",
		"Scaled Deployment from %d to %d replicas",
		oldReplicas, *webapp.Spec.Replicas)

	// On image update
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"ImageUpdated",
		"Updated container image from %s to %s",
		oldImage, webapp.Spec.Image)

	// On errors
	r.Recorder.Eventf(webapp, corev1.EventTypeWarning,
		"ReconcileError",
		"Failed to create Deployment: %v", err)

	// On cleanup
	r.Recorder.Event(webapp, corev1.EventTypeNormal,
		"CleanupComplete",
		"External resources cleaned up successfully")

	// ...
}
```

Таксономія подій має бути нудною та передбачуваною. Використовуйте `Normal` для успішних рутинних операцій, що пояснюють прогрес, і використовуйте `Warning`, коли користувачу, можливо, доведеться діяти, або коли зовнішня залежність перешкоджає узгодженню. Уникайте видачі нової події на кожному циклі узгодження для того самого незмінного стану, бо високочастотні події стають шумом і можуть приховати попередження, яке справді має значення.

Корисний набір умов достатньо малий, щоб його можна було зрозуміти під час інциденту. Спокусливо створити умову для кожної допоміжної функції, бо умови виглядають структурованими й зручними для запитів. Це зазвичай породжує сторінки статусу, де все технічно присутнє, але ніщо не є вирішальним. Віддавайте перевагу умовам, які відображають межі готовності, видимі користувачу: Деплоймент має достатньо готових реплік, Сервіс існує й вказує на правильний селектор, Ingress чи маршрут допущено, очищення очікується, а весь WebApp готовий. Внутрішні деталі належать логам, метрикам чи подіям, якщо тільки користувач не може діяти на їх основі безпосередньо.

Значення Reason заслуговують на ту саму дисципліну, що й назви полів API. Це машинозчитувані рядки, які користувачі можуть розміщувати в оповіщеннях чи дашбордах, тому уникайте вбудовування підрахунків, імен об'єктів чи змінюваного тексту всередину reason. Розміщуйте стабільні категорії, такі як `ScalingUp`, `ImageUpdating`, `DeploymentFailed` чи `CleanupPending`, у `Reason`, а контекстну деталь — у `Message`. Цей поділ дає автоматизації стабільну умову гілки, водночас даючи людям достатньо інформації, щоб вирішити, чи чекати, оглянути дочірній ресурс або ескалювати зовнішню залежність.

`ObservedGeneration` — одне з найлегших полів для встановлення й одне з найлегших для пропуску. Коли користувач редагує специфікацію, Kubernetes збільшує `metadata.generation`, але статус не стає істинним для цього нового покоління, доки контролер його не спостереже й не узгодить. Конвеєр розгортання, який чекає лише на `Ready=True`, може бути обманутий застарілою готовністю з попередньої специфікації. Конвеєр, який також перевіряє `Ready.ObservedGeneration == metadata.generation`, може відрізнити «стара версія справна» від «запитана версія узгоджена».

Оновлення статусу слід відокремлювати від оновлень специфікації у вашій ментальній моделі та, де можливо, у викликах клієнта. Субресурс статусу існує, щоб контролери могли оновлювати спостережений стан, не змагаючись із користувачами, які редагують бажаний стан. Коли ви викликаєте `r.Status().Update`, ви стверджуєте, що специфікація все ще належить користувачу, а статус належить контролеру. Цей поділ є частиною контракту Kubernetes API, і він допомагає уникнути випадкових записів, що перезаписують нещодавню зміну специфікації користувачем.

Події слід видавати під час переходів стану, а не на кожне спостереження того самого стану. Якщо Деплоймент уже існує й усе ще має бажану кількість реплік, ще одна подія "DeploymentCreated" вводить в оману. Якщо цикл узгодження спостерігає, що кількість реплік змінилася з двох на п'ять, і застосовує оновлення, подія корисна, бо пояснює видиму користувачу дію. Те саме правило стосується попереджень: видавайте попередження, коли виклик API провалюється або узгодження заблоковано, але не затоплюйте потік подій ідентичними попередженнями на кожному швидкому повторі, якщо відкладання та логи вже несуть деталі.

Умови, події та логи утворюють багатошаровий шлях діагностики. Умови відповідають на перше питання, яке ставить користувач, події відповідають на те, що нещодавно змінилося, а логи відповідають на те, чому контролер обрав конкретну внутрішню гілку. Вам не потрібно вкладати кожну деталь логу в об'єкт API. Вам потрібно переконатися, що перших двох шарів достатньо, щоб хтось без доступу cluster-admin до логів міг вирішити, чи проблема в тому, що Деплоймент відсутній, є затримка масштабування, невідповідність Сервісу, збій зовнішнього очищення чи застарілий статус після нового покоління специфікації.

| Тип | Коли | Приклад |
|------|------|---------|
| `EventTypeNormal` | Рутинні операції | Created Deployment, Scaled, Updated |
| `EventTypeWarning` | Проблеми, що потребують уваги | Failed to create, Retry limit reached |

```bash
# View events for a specific resource
kubectl describe webapp my-app | grep -A 20 "Events:"

# View all events sorted by time
kubectl get events --sort-by=.lastTimestamp --field-selector involvedObject.kind=WebApp
```

## Вибір лідера та проєктування спостережень

Розгортання контролера з двома репліками не є автоматично високодоступним. Без вибору лідера обидві репліки можуть узгоджувати той самий ресурс одночасно, кожна читає застарілий стан, кожна намагається оновити дочірні ресурси й кожна записує статус. Оптимістичний контроль конкурентності Kubernetes відхилить деякі записи, але це не є проєктом для коректності. Вибір лідера дає менеджеру єдиний активний процес контролера, водночас дозволяючи резервним реплікам перебрати керування після закінчення оренди (lease).

Компроміс безпеки — це коротка затримка переходу. Якщо Под-лідер зникає, не звільнивши Lease, резервний Под має чекати, доки тривалість оренди закінчиться, перш ніж він зможе набути лідерства. Ця пауза навмисна, бо вона запобігає узгодженню «розщеплений мозок», коли лідер повільний, відмежований мережею чи тимчасово не може поновити оренду. Для оператора, який керує зовнішніми ресурсами, коротка пауза зазвичай набагато краща, ніж дві репліки, що видають конфліктні виклики створення й видалення проти зовнішнього API.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Leader Election                                    │
│                                                                     │
│   Pod A (leader)              Pod B (standby)                       │
│   ┌──────────────┐           ┌──────────────┐                      │
│   │ Manager      │           │ Manager      │                      │
│   │              │           │              │                      │
│   │ Controllers: │           │ Controllers: │                      │
│   │ ✓ Running    │           │ ✗ Blocked    │                      │
│   │              │           │              │                      │
│   │ Lease:       │           │ Lease:       │                      │
│   │ HELD ────────┼───────── │ WAITING      │                      │
│   └──────────────┘    │     └──────────────┘                      │
│                       │                                             │
│                       ▼                                             │
│              ┌───────────────────┐                                  │
│              │  Lease Resource   │                                  │
│              │  (in K8s API)     │                                  │
│              │                   │                                  │
│              │  holder: pod-a    │                                  │
│              │  renewTime: now   │                                  │
│              │  leaseDuration: 15s│                                 │
│              └───────────────────┘                                  │
│                                                                     │
│   If Pod A dies:                                                    │
│   1. Pod A stops renewing the lease                                 │
│   2. After leaseDuration (15s), Pod B acquires                      │
│   3. Pod B starts controllers                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Продумайте шлях збою, перш ніж змінювати налаштування оренди: якщо затримка мережі стрибає, а Под-лідер не встигає поновити оренду в межах дедлайну, резервний Под може набути оренди, а старий лідер має зупинити контролери, коли усвідомить, що оренду втрачено. Коротші тривалості покращують час переходу, але збільшують чутливість до затримки сервера API. Довші тривалості зменшують хибні переходи, але подовжують період, протягом якого жоден контролер активно не обробляє роботу після жорсткого збою.

```go
mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
    // ...
    LeaderElection:          true,
    LeaderElectionID:        "webapp-operator.kubedojo.io",
    LeaderElectionNamespace: "webapp-system",  // Optional: defaults to controller namespace
})
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-operator
  namespace: webapp-system
spec:
  replicas: 2          # Two replicas for HA
  selector:
    matchLabels:
      app: webapp-operator
  template:
    spec:
      containers:
      - name: manager
        args:
        - --leader-elect=true
```

| Параметр | Усталене | Опис |
|-----------|---------|-------------|
| LeaderElectionID | `"webapp-operator.kubedojo.io"` (обов'язково) | Унікальний ID для ресурсу оренди |
| LeaseDuration | 15s | Як довго триває оренда |
| RenewDeadline | 10s | Скільки часу лідер має на поновлення |
| RetryPeriod | 2s | Як часто резервні Под'и перевіряють |
| LeaderElectionNamespace | Простір імен Под'а | Де створюється Lease |

Проєктування спостережень — це інша половина продакшн-узгодження. `For(&WebApp{})` каже контролеру узгоджувати, коли змінюється первинний ресурс, тоді як `Owns(&Deployment{})` та `Owns(&Service{})` ставлять у чергу WebApp-власника, коли змінюються власні дочірні ресурси. Кастомні спостереження корисні, коли WebApp залежить від ресурсу, яким не володіє, як-от ConfigMap, обраний за іменем. Ризик — це віяльне розгалуження (fan-out): одне оновлення ConfigMap може поставити в чергу багато WebApp, тому функція відображення має бути простою, обмеженою й зведеною до простору імен, якщо тільки оператор не є навмисно загальнокластерним.

Тип `EnvVar` з WebApp із Модуля 1.4 тут розширено опціональним полем `valueFrom`, яке називає ConfigMap, з якого джерелити значення, щоб функція відображення могла виявляти посилання на ConfigMap, не використовуючи базовий `EnvVarSource`:

```go
type EnvVar struct {
	Name      string `json:"name"`
	Value     string `json:"value,omitempty"`
	ValueFrom string `json:"valueFrom,omitempty"` // ConfigMap name when value is sourced externally
}
```

```go
import (
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1beta1.WebApp{}).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		// Watch ConfigMaps with a custom mapping function
		Watches(
			&corev1.ConfigMap{},
			handler.EnqueueRequestsFromMapFunc(
				r.findWebAppsForConfigMap,
			),
		).
		// Set maximum concurrent reconciliations
		WithOptions(controller.Options{
			MaxConcurrentReconciles: 3,
		}).
		Named("webapp").
		Complete(r)
}

// findWebAppsForConfigMap maps a ConfigMap to WebApps that reference it.
func (r *WebAppReconciler) findWebAppsForConfigMap(
	ctx context.Context,
	configMap client.Object,
) []reconcile.Request {
	logger := log.FromContext(ctx)

	// List all WebApps
	webappList := &appsv1beta1.WebAppList{}
	if err := r.List(ctx, webappList, client.InNamespace(configMap.GetNamespace())); err != nil {
		logger.Error(err, "Unable to list WebApps")
		return nil
	}

	var requests []reconcile.Request
	for _, webapp := range webappList.Items {
		// Check if this WebApp references the ConfigMap
		for _, env := range webapp.Spec.Env {
			if env.ValueFrom == configMap.GetName() {
				requests = append(requests, reconcile.Request{
					NamespacedName: types.NamespacedName{
						Name:      webapp.Name,
						Namespace: webapp.Namespace,
					},
				})
				break
			}
		}
	}

	return requests
}
```

Предикати — це фільтри, а не засоби коректності, і вони легко можуть приховати події, потрібні вашому контролеру. `GenerationChangedPredicate` корисний на первинному кастомному ресурсі, бо оновлення статусу не змінюють покоління й не повинні обов'язково запускати ще один повний прохід. Застосування того самого предиката до власних Деплойментів може бути помилковим, якщо ви очікуєте реагувати на зміни готовності, збої Под'ів чи інші сигнали, керовані статусом. Хороша стратегія спостереження фільтрує шумне джерело подій, а не джерело подій, яке несе докази дрейфу.

```go
func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1beta1.WebApp{},
			builder.WithPredicates(predicate.GenerationChangedPredicate{}),
		).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		Named("webapp").
		Complete(r)
}
```

| Предикат | Ефект |
|-----------|--------|
| `GenerationChangedPredicate` | Узгоджувати лише при зміні специфікації (ігнорує оновлення лише статусу) |
| `LabelChangedPredicate` | Лише при зміні міток |
| `AnnotationChangedPredicate` | Лише при зміні анотацій |
| `ResourceVersionChangedPredicate` | Будь-яка зміна (усталена поведінка) |

```go
builder.WithPredicates(
    predicate.Or(
        predicate.GenerationChangedPredicate{},
        predicate.LabelChangedPredicate{},
    ),
)
```

Який підхід ви б тут обрали й чому: фільтрування оновлень WebApp лише за статусом, фільтрування оновлень статусу Деплойменту чи залишення спостережень за власними ресурсами без фільтрів, доки ви не виміряєте тиск черги? Найбезпечніший усталений варіант — зазвичай фільтрувати лише первинний ресурс, а потім додавати вужчі предикати після того, як ви зможете довести, які події є шумними, а які потрібні для узгодження. Оператори зазнають болючіших невдач, коли пропускають дрейф, ніж коли узгоджують один зайвий раз.

Вибір лідера не робить індивідуальний код узгодження потокобезпечним; він зменшує кількість активних менеджерів, що запускають контролер. Усередині одного менеджера `MaxConcurrentReconciles` усе ще може дозволяти кільком WebApp узгоджуватися одночасно. Це зазвичай бажано, але це означає, що спільні клієнти для зовнішніх систем мають бути безпечними для конкурентного використання, а код очищення повинен уникати глобального змінюваного стану. Якщо API провайдера має суворі обмеження частоти, використовуйте дедлайни контексту на запит та явне регулювання, а не припускайте, що вибір лідера серіалізує всю роботу.

Об'єкт Lease також є операційною залежністю. Якщо ваш оператор втрачає дозвіл створювати чи оновлювати Lease у просторі імен свого вибору лідера, розгортання з кількома репліками може запуститися, але ніколи не запустить контролери. Цей збій має бути видимим у логах Под'а та готовності розгортання, проте він часто застає команди зненацька, бо RBAC для кастомного ресурсу тестують, а ресурси координації забувають. Коли ви вмикаєте вибір лідера, перегляньте Role чи ClusterRole менеджера на доступ до Lease в обраному просторі імен і включіть цей шлях у перевірку розгортання.

Функції відображення спостережень слід проєктувати для найбільшого простору імен, який ви очікуєте підтримувати, а не лише для малого демонстраційного простору. Перелік кожного WebApp на кожне оновлення ConfigMap може бути прийнятним для лабораторії, але стає дорогим, коли сотні WebApp посилаються на різні об'єкти конфігурації. Ви можете зменшити роботу за допомогою міток, індексів чи зв'язку полів, записаного в статусі, залежно від версії controller-runtime та проєкту. Важливе питання в тому, чи масштабується відображення спостереження разом із релевантними залежними об'єктами, чи разом із кожним об'єктом у просторі імен.

Предикати слід переглядати поряд із проєктуванням статусу. Предикат, що відкидає оновлення статусу, може бути коректним, коли статус суто інформаційний, але може бути помилковим, коли статус є сигналом, що має запускати ремонт. Зміни готовності Деплойменту, доступність Под'ів та оновлення кінцевих точок часто керуються статусом, тому предикати власних ресурсів потребують більше уваги, ніж предикати первинного ресурсу. Якщо ви додаєте предикат, запишіть, які події він навмисно відкидає і який інваріант узгодження залишається захищеним без цих подій.

Висока доступність також змінює те, як ви читаєте логи, що виглядають дубльованими. Під час переходу резервний менеджер може запустити контролери й узгодити об'єкти, які вже були в черзі до того, як старий лідер помер. Це нормально, бо черга є механізмом «принаймні один раз» (at-least-once), а не доставкою «точно один раз». Код контролера має толерувати повторювані запити, читаючи поточний стан і застосовуючи ідемпотентні зміни. Якщо дубльоване узгодження спричиняє повторне створення зовнішніх ресурсів, помилка в проєктуванні узгодження чи зовнішньої ідемпотентності, а не у виборі лідера.

Для багатьох операторів найкраще перше значення для тюнінгу — не коротша тривалість оренди; це краща спостережуваність навколо лідерства. Експонуйте метрики менеджера, логуйте переходи лідерства й переконайтеся, що готовність Под'а відображає, чи здоровий менеджер. Потім виміряйте, скільки фактично триває перехід у вашому кластері за нормальної затримки сервера API. Лише після цього вимірювання слід тюнити тривалість оренди, дедлайн поновлення й період повтору, бо агресивні налаштування можуть проміняти видиму паузу переходу на періодичну метушню лідерства, яку важче діагностувати.

## Інтеграційне тестування з envtest

Модульні тести можуть перевіряти допоміжні функції, але вони не можуть довести, що ваша схема CRD, реєстрація схеми (scheme), оновлення субресурсу статусу, запуск менеджера, зв'язки володіння та асинхронне узгодження співпрацюють із Kubernetes API. `envtest` запускає реальний сервер API та etcd локально, а потім дає вашому тестовому процесу REST-конфіг. Це робить тести повільнішими за чисто модульні, але вони ловлять той самий клас помилок, який оператори часто відвантажують: відсутній RBAC, недійсні шляхи CRD, некоректні оновлення статусу, забуті схеми та тести, що припускають синхронність узгодження.

Найважливіша звичка тестування — стверджувати «з часом» (eventually), а не миттєво. Контролер реагує на події спостереження, читає з кешів, записує через сервер API й може повторно ставити в чергу. Прямий `Get` одразу після `Create` — це гонитва, замаскована під тест. `Eventually` від Ginkgo виражає контракт коректно: після створення WebApp Деплоймент має з'явитися протягом розумного тайм-ауту, а тест має опитувати, доки асинхронна система не досягне цього стану або справді не зазнає невдачі.

```go
// internal/controller/suite_test.go
package controller

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
)

var (
	cfg       *rest.Config
	k8sClient client.Client
	testEnv   *envtest.Environment
	ctx       context.Context
	cancel    context.CancelFunc
)

func TestControllers(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Controller Suite")
}

var _ = BeforeSuite(func() {
	logf.SetLogger(zap.New(zap.WriteTo(GinkgoWriter), zap.UseDevMode(true)))

	ctx, cancel = context.WithCancel(context.Background())

	// Start envtest (real API Server + etcd)
	testEnv = &envtest.Environment{
		CRDDirectoryPaths:     []string{filepath.Join("..", "..", "config", "crd", "bases")},
		ErrorIfCRDPathMissing: true,
	}

	var err error
	cfg, err = testEnv.Start()
	Expect(err).NotTo(HaveOccurred())
	Expect(cfg).NotTo(BeNil())

	// Register our types
	err = appsv1beta1.AddToScheme(scheme.Scheme)
	Expect(err).NotTo(HaveOccurred())

	// Create a client
	k8sClient, err = client.New(cfg, client.Options{Scheme: scheme.Scheme})
	Expect(err).NotTo(HaveOccurred())
	Expect(k8sClient).NotTo(BeNil())

	// Start the controller manager
	mgr, err := ctrl.NewManager(cfg, ctrl.Options{
		Scheme: scheme.Scheme,
	})
	Expect(err).NotTo(HaveOccurred())

	err = (&WebAppReconciler{
		Client:   mgr.GetClient(),
		Scheme:   mgr.GetScheme(),
		Recorder: mgr.GetEventRecorderFor("webapp-controller"),
	}).SetupWithManager(mgr)
	Expect(err).NotTo(HaveOccurred())

	// Run the manager in a goroutine
	go func() {
		defer GinkgoRecover()
		err = mgr.Start(ctx)
		Expect(err).NotTo(HaveOccurred())
	}()
})

var _ = AfterSuite(func() {
	cancel()
	err := testEnv.Stop()
	Expect(err).NotTo(HaveOccurred())
})
```

Налаштування набору (suite) — це також місце, де багато тестів операторів випадково стають моками. Якщо ви забудете зареєструвати свій тип API зі схемою, клієнт не зможе декодувати ваш кастомний ресурс. Якщо шлях до каталогу CRD неправильний, а тест не падає на відсутньому шляху, ви можете прогнати тест проти сервера API, який гадки не має про ваш ресурс. Якщо менеджер ніколи не запускається, твердження проти створених дочірніх об'єктів ніколи не пройдуть, бо узгоджувач не працює. Кожен рядок у налаштуванні захищає один із цих контрактів.

```go
// internal/controller/webapp_controller_test.go
package controller

import (
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
)

var _ = Describe("WebApp Controller", func() {
	const (
		timeout  = 30 * time.Second
		interval = 250 * time.Millisecond
	)

	Context("When creating a WebApp", func() {
		It("should create a Deployment and Service", func() {
			webappName := "test-create"
			namespace := "default"
			replicas := int32(3)

			// Create the WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Verify Deployment is created
			deploymentKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			deployment := &appsv1.Deployment{}
			Eventually(func() error {
				return k8sClient.Get(ctx, deploymentKey, deployment)
			}, timeout, interval).Should(Succeed())

			Expect(*deployment.Spec.Replicas).To(Equal(int32(3)))
			Expect(deployment.Spec.Template.Spec.Containers[0].Image).To(Equal("nginx:1.27"))

			// Verify OwnerReference is set
			Expect(deployment.OwnerReferences).To(HaveLen(1))
			Expect(deployment.OwnerReferences[0].Kind).To(Equal("WebApp"))
			Expect(deployment.OwnerReferences[0].Name).To(Equal(webappName))

			// Verify Service is created
			serviceKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			service := &corev1.Service{}
			Eventually(func() error {
				return k8sClient.Get(ctx, serviceKey, service)
			}, timeout, interval).Should(Succeed())

			Expect(service.Spec.Ports[0].Port).To(Equal(int32(80)))
		})
	})

	Context("When updating a WebApp", func() {
		It("should update the Deployment replicas", func() {
			webappName := "test-update"
			namespace := "default"
			replicas := int32(2)

			// Create initial WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Wait for Deployment
			deploymentKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			deployment := &appsv1.Deployment{}
			Eventually(func() error {
				return k8sClient.Get(ctx, deploymentKey, deployment)
			}, timeout, interval).Should(Succeed())

			// Update replicas
			newReplicas := int32(5)
			Eventually(func() error {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return err
				}
				webapp.Spec.Replicas = &newReplicas
				return k8sClient.Update(ctx, webapp)
			}, timeout, interval).Should(Succeed())

			// Verify Deployment updated
			Eventually(func() int32 {
				if err := k8sClient.Get(ctx, deploymentKey, deployment); err != nil {
					return -1
				}
				return *deployment.Spec.Replicas
			}, timeout, interval).Should(Equal(int32(5)))
		})
	})

	Context("When deleting a WebApp with a finalizer", func() {
		It("should clean up and allow deletion", func() {
			webappName := "test-delete"
			namespace := "default"
			replicas := int32(1)

			// Create WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Wait for finalizer to be added
			Eventually(func() []string {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return nil
				}
				return webapp.Finalizers
			}, timeout, interval).Should(ContainElement(webappFinalizer))

			// Delete the WebApp
			Expect(k8sClient.Delete(ctx, webapp)).To(Succeed())

			// Verify it eventually gets deleted
			Eventually(func() bool {
				err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp)
				return errors.IsNotFound(err)
			}, timeout, interval).Should(BeTrue())
		})
	})

	Context("When checking status conditions", func() {
		It("should set conditions correctly", func() {
			webappName := "test-conditions"
			namespace := "default"
			replicas := int32(1)

			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Check that conditions are eventually set
			Eventually(func() int {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return 0
				}
				return len(webapp.Status.Conditions)
			}, timeout, interval).Should(BeNumerically(">=", 2))

			// Verify condition types exist
			condTypes := make([]string, len(webapp.Status.Conditions))
			for i, c := range webapp.Status.Conditions {
				condTypes[i] = c.Type
			}
			Expect(condTypes).To(ContainElement("DeploymentReady"))
			Expect(condTypes).To(ContainElement("ServiceReady"))
		})
	})
})
```

Тест видалення — це той, який багато команд пропускають, і саме він ловить помилки фіналайзера, перш ніж користувачі знайдуть застряглі ресурси. Він чекає на появу фіналайзера, видаляє WebApp, а потім чекає, доки `Get` не поверне `IsNotFound`. У реальному операторі ви б зазвичай додали фейковий зовнішній клієнт і ствердили, що очищення було викликано до зникнення фіналайзера. Для цього модуля структурний тест усе ж доводить, що контролер може увійти в гілку видалення й звільнити об'єкт.

envtest не повинен ставати єдиним рівнем тестування. Допоміжні функції, які будують специфікації Деплойменту, обчислюють мітки чи класифікують зовнішні помилки, зазвичай швидші й зрозуміліші як модульні тести. envtest найсильніший, коли поведінка залежить від машинерії Kubernetes API: валідація CRD, посилання на власника, записи субресурсу статусу, запуск менеджера, видалення фіналайзера та асинхронне узгодження. Збалансований набір тестів тримає чисту логіку швидкою, водночас використовуючи envtest для шляхів життєвого циклу, де фейковий клієнт приховав би важливу поведінку.

Коли envtest падає, читайте збій через хронологію узгодження. Відсутній дочірній Деплоймент може означати, що менеджер ніколи не запустився, тип WebApp не було зареєстровано, CRD не було встановлено, RBAC завадив запису, цикл узгодження повернувся рано після додавання фіналайзера або тест використав неправильний простір імен. Кожна можливість відображається на інше налаштування чи гілку контролера. Додавання логів до тестового менеджера та використання блоків `Eventually`, що повертають корисні помилки, заощадить більше часу, ніж сліпе збільшення тайм-аутів.

Тест фіналайзера можна зробити реалістичнішим, упровадивши колаборатора очищення. Замість виклику реального хмарного API, визначте інтерфейс для зовнішнього очищення й надайте фейкову реалізацію в тестах. Фейк може записувати виклики, один раз повернути тимчасову помилку, а потім вдатися на повторі. Це дозволяє envtest довести, що контролер тримає фіналайзер після збою очищення й видаляє його лише після пізнішого успіху. Урок той самий, що й у продакшн-проєктуванні: зовнішні побічні ефекти належать за інтерфейсами, які можна осмислити в умовах повторів.

Тести умов статусу повинні перевіряти більше, ніж кількість умов. Надійний тест отримує WebApp після узгодження, знаходить умову `Ready` за типом, перевіряє статус і причину та порівнює `ObservedGeneration` із поколінням WebApp. Якщо тест оновлює специфікацію, він може спершу спостерегти застарілий статус, а потім чекати, доки умова не наздожене нове покоління. Цей патерн ловить тонкий, але важливий клас помилок, де оператор повідомляє про готовність, не довівши, що опрацював найновіший бажаний стан.

Тести подій можливі, але мають бути вибірковими. Події корисні для досвіду користувача, проте вони не є тривким джерелом істини, а їхня поведінка зберігання може відрізнятися в різних кластерах. У envtest ви можете ствердити, що рекордер сконфігуровано, або використати фейковий рекордер для перевірок на рівні модулів навколо гілок генерації подій. Для основного інтеграційного шляху цього модуля пріоритезуйте поведінку фіналайзера, створення дочірніх ресурсів, статус та обробку оновлень, бо це тривкі контракти API, що безпосередньо впливають на коректність.

Ручне тестування після envtest усе ще має цінність, бо воно проганяє пакування та дозволи, які локальний набір може не покривати. Встановлення CRD у кластер Kind, запуск менеджера, застосування WebApp, очікування готовності, читання подій та видалення ресурсу показує, чи маніфести, RBAC, прапори вибору лідера та згенерований YAML узгоджені. Трактуйте ручне тестування як димову перевірку (smoke test) пакування, а не як заміну автоматизованих тестів життєвого циклу. Результат, який ви хочете, — це впевненість з обох напрямків: повторювані тести поведінки й швидкий прогін у кластері для з'єднань розгортання.

```bash
# Install envtest binaries (API Server and etcd)
make envtest
ENVTEST=$(go env GOPATH)/bin/setup-envtest

# Download the binaries
$ENVTEST use --print-path latest

# Run tests
make test

# Or run directly with more output
KUBEBUILDER_ASSETS=$($ENVTEST use --print-path latest) \
  go test ./internal/controller/ -v -ginkgo.v
```

### Рівні зрілості оператора

[Модель зрілості оператора (Operator Capability Model)](https://github.com/operator-framework/operator-sdk/blob/master/doc/images/operator-capability-model.svg) описує, наскільки зрілим є оператор за п'ятьма рівнями. Використовуйте її, щоб задати очікування користувачам і спланувати поступові інвестиції:

- **Рівень 1 — Базова інсталяція:** автоматизована інсталяція та конфігурація операнда.
- **Рівень 2 — Безшовні оновлення:** оператор керує оновленнями патч- та мінорних версій операнда.
- **Рівень 3 — Повний життєвий цикл:** життєвий цикл застосунку плюс життєвий цикл сховища — резервні копії, відновлення після збоїв, відновлення.
- **Рівень 4 — Глибокі інсайти:** метрики, оповіщення, обробка логів та аналіз робочих навантажень (спостережуваність операнда).
- **Рівень 5 — Автопілот:** автомасштабування (горизонтальне/вертикальне), автотюнінг, виявлення аномалій, тюнінг планування.

Фіналайзери та структуровані умови в цьому модулі є сходинками до **Рівня 3 (Повний життєвий цикл)**: вони роблять видалення та готовність спостережуваними, а не «за можливості». Шляхи дистрибуції та оновлення лежать у **Operator Framework**, проєкті CNCF зі статусом Incubating: **Operator Lifecycle Manager (OLM)** встановлює, оновлює та керує операторами і їхніми залежностями в кластері, а **[OperatorHub.io](https://operatorhub.io/)** є публічним каталогом, де публікується багато операторів, упакованих через OLM.

## Патерни та антипатерни

Найсильніші проєкти операторів тримають контракт узгодження вузьким: кожен прохід спостерігає поточний стан, порівнює його з бажаним станом, робить один обмежений набір змін, записує статус і виходить. Фіналайзери, умови, події, вибір лідера, спостереження та envtest не є окремими прикрасами навколо цього циклу. Це бар'єри безпеки, які тримають цикл коректним, коли в систему входять видалення, збої, питання користувачів, перехід реплік, дрейф дочірніх ресурсів та асинхронні тести.

| Патерн | Коли використовувати | Чому він працює |
|---------|----------------|--------------|
| Ідемпотентне очищення фіналайзера | Будь-який оператор, що створює ресурси поза збиранням сміття Kubernetes | Повтори стають безпечними, бо повторний виклик очищення досягає того самого кінцевого стану |
| Позитивні умови, обізнані про покоління | Будь-який кастомний ресурс, споживаний людьми, інструментами GitOps чи автоматизацією | Користувачі можуть відрізнити застарілий успіх від поточного успіху після зміни специфікації |
| Запис подій під час переходів життєвого циклу | Створення, масштабування, оновлення образу, очищення та шляхи попереджень | Об'єкт несе нещодавню операційну хронологію, видиму через стандартні інструменти Kubernetes |
| Вибір лідера з принаймні двома репліками | Оператори, що мають пережити збій вузла чи добровільне переривання | Один активний узгоджувач запобігає «розщепленому мозку», тоді як резервні Под'и забезпечують перехід |
| Покриття envtest навколо поведінки життєвого циклу | Контролери з CRD, посиланнями на власника, оновленнями статусу та фіналайзерами | Тести проганяють реальний сервер API замість припущень про поведінку Kubernetes у моках |

Головний антипатерн — трактувати код контролера як звичайний CRUD-код. Контролер є циклом ремонту з відкладеною узгодженістю (eventually consistent), тому він має толерувати дубльовані запити, застарілі читання, повтори через конфлікти, збої зовнішнього API та видалені об'єкти, що все ще існують тимчасово, бо фіналайзери їх утримують. Патерни, які працюють у сервісі типу запит-відповідь, можуть стати небезпечними тут, якщо вони припускають один виклик, одну зміну й одну остаточну відповідь.

Є корисна звичка рев'ю для просунутої роботи з операторами: назвіть інваріант перед рев'ю коду. Для фіналайзерів інваріант полягає в тому, що зовнішні ресурси відсутні до того, як кастомний ресурс буде вилучено. Для умов інваріант полягає в тому, що статус описує найновіше спостережене покоління. Для вибору лідера інваріант полягає в тому, що лише один активний менеджер узгоджує в один момент. Для envtest інваріант полягає в тому, що асинхронна поведінка контролера спостерігається через сервер API. Код набагато легше рев'ювати, коли кожну допоміжну функцію оцінюють проти інваріанта, який вона захищає.

Інша звичка рев'ю — відокремлювати коректність від зручності. Короткий предикат, ручне додавання умови чи патч фіналайзера можуть змусити локальний тест пройти, але продакшн-питання в тому, чи залишається поведінка коректною в умовах повторів, конфліктів та збоїв. Просунута розробка операторів — це переважно про ці незручні межі. Якщо ви можете пояснити, що відбувається, коли сервер API повільний, хмарний провайдер повертає помилку, Под-лідер помирає, а тест працює на повільному CI-воркері, проєкт зазвичай стоїть на твердій основі.

Той самий стандарт застосовується після першого релізу. З погляду користувача оператори стають частиною площини управління кластера, тому регресії у видаленні, готовності чи переході відчуваються як збої платформи, а не як помилки застосунку. Тримайте поряд із кодом невеликий ранбук, що пояснює застряглі фіналайзери, застарілі спостережені покоління, відсутні події, проблеми оренди вибору лідера та збої налаштування envtest. Цей ранбук змушує проєкт залишатися пояснюваним, а пояснювані контролери набагато легше експлуатувати під час реальних інцидентів.

| Антипатерн | Що йде не так | Краща альтернатива |
|--------------|-----------------|--------------------|
| Видалення фіналайзера до очищення | Сервер API видаляє кастомний ресурс, а зовнішній ресурс стає осиротілим | Спершу виконайте очищення, трактуйте not-found-очищення як успіх, потім видаліть лише свій фіналайзер |
| Ручне додавання умов | Дубльовані типи умов накопичуються, а автоматизація готовності читає суперечливий стан | Використовуйте `meta.SetStatusCondition` і підтримуйте одну умову на тип |
| Видача попереджувальних подій для звичайного прогресу | Дашборди й люди вчаться ігнорувати попередження, які мали б указувати на дію | Використовуйте `Normal` для очікуваних переходів і `Warning` для заблокованого узгодження |
| Застосування агресивних предикатів усюди | Зміни статусу чи дрейф дочірніх ресурсів відфільтровуються до того, як контролер може відремонтувати | Фільтруйте первинний ресурс обережно й виміряйте шум власних ресурсів перед фільтруванням |
| Тестування узгодження миттєвими твердженнями | CI стає нестабільним, бо цикл контролера є асинхронним | Використовуйте `Eventually` навколо спостережень API, що залежать від узгодження |

## Каркас прийняття рішень

Використовуйте цей каркас прийняття рішень, коли рев'юєте зміну оператора. Почніть із питання, чи керує оператор будь-чим, що Kubernetes не може зібрати як сміття. Якщо так, додайте фіналайзер перед створенням цього зовнішнього ресурсу й явно протестуйте видалення. Потім запитайте, чи може користувач діагностувати поточну готовність без логів. Якщо ні, додайте структуровані умови з `ObservedGeneration`. Далі запитайте, чи може користувач бачити нещодавню історію дій. Якщо ні, видавайте цілеспрямовані події для переходів життєвого циклу та попереджень.

```
Need to add production behavior?
    │
    ├── External resource outside owner references?
    │       └── Add idempotent finalizer cleanup and deletion tests
    │
    ├── Users or pipelines need current readiness?
    │       └── Add positive conditions with ObservedGeneration
    │
    ├── Users need a recent action timeline?
    │       └── Emit Normal and Warning Events at meaningful transitions
    │
    ├── Operator needs multiple replicas?
    │       └── Enable leader election and tune lease settings conservatively
    │
    ├── Related resources should trigger repair?
    │       └── Add owned or mapped watches with cautious predicates
    │
    └── Behavior crosses API-server boundaries?
            └── Cover it with envtest and Eventually assertions
```

Рішення рідко полягає в тому, щоб «увімкнути кожну просунуту функцію». Просторово-зведений іграшковий контролер, який лише створює власні Деплойменти, може не потребувати кастомних відображених спостережень, а навчальний оператор в одному кластері може не потребувати тюнінгу таймінгів оренди. Продакшн-оператор платформи, який забезпечує зовнішні ресурси, оновлює статус, споживаний автоматизацією розгортання, і працює через вузли, потребує повного набору. Практична навичка — це підбирати функцію до режиму збою, якому ви намагаєтеся запобігти.

| Аспект | Мінімальний оператор | Продакшн-оператор | Питання для рев'ю |
|---------|------------------|---------------------|-----------------|
| Очищення | Лише посилання на власника | Фіналайзери плюс ідемпотентне зовнішнє очищення | Що залишається після видалення кастомного ресурсу? |
| Готовність | Рядок фази чи логи | Стандартні умови зі спостереженим поколінням | Чи може автоматизація визначити, чи статус відповідає найновішій специфікації? |
| Спостережуваність | Логи контролера | Події плюс умови плюс логи | Чи може користувач діагностувати об'єкт без доступу до логів Под'а? |
| Доступність | Одна репліка | Кілька реплік із вибором лідера | Що відбувається, коли активний Под помирає? |
| Тестування | Модульні тести для допоміжних функцій | Тести життєвого циклу envtest | Чи використовує тест ту саму машинерію API, що й контролер? |

## Чи знали ви?

- **Фіналайзери передують багатьом сучасним конвенціям операторів**: це поле є частиною метаданих об'єкта Kubernetes, тому воно широко застосовується до вбудованих та кастомних ресурсів, а не є розширенням, специфічним для операторів.
- **`metav1.Condition` стандартизує шість ключових полів**: `Type`, `Status`, `ObservedGeneration`, `LastTransitionTime`, `Reason` та `Message` дають інструментам спільний контракт для готовності й діагностики; KEP-1623, Standardize Conditions, є посиланням «копнути глибше» щодо історії стандартизації.
- **Вибір лідера в controller-runtime використовує ресурси Lease**: усталені значення таймінгу включають тривалість оренди 15 секунд, дедлайн поновлення 10 секунд і період повтору 2 секунди, якщо ви не сконфігуруєте їх інакше.
- **envtest не є фейковим клієнтом**: він запускає реальні бінарні файли сервера API та etcd, тому й може ловити проблеми валідації CRD, реєстрації схеми, субресурсу статусу та таймінгу узгодження.

## Типові помилки

| Помилка | Чому вона трапляється | Як її виправити |
|---------|----------------|---------------|
| Невидалення фіналайзера при успіху очищення | Код виконує очищення, але ніколи не підтверджує завершення серверу API | Завжди видаляйте свій фіналайзер після успішного очищення й оновлюйте об'єкт |
| Видалення фіналайзера до очищення | Розробник трактує видалення фіналайзера як початок видалення, а не як сигнал завершення | Спершу виконайте очищення, обробіть not-found як успіх і видаляйте фіналайзер останнім |
| Встановлення `LastTransitionTime` на кожне узгодження | Контролер перебудовує умови вручну й скидає мітки часу, навіть коли статус незмінний | Використовуйте `meta.SetStatusCondition` чи еквівалентну логіку, що оновлює час переходу лише при зміні статусу |
| Використання `EventTypeWarning` для звичайних операцій | Кожна подія життєвого циклу здається важливою під час розробки, тому попередження стають шумними | Резервуйте події Warning для проблем і використовуйте події Normal для успішних переходів |
| Невстановлення `ObservedGeneration` на умовах | Статус записується без зв'язку з поколінням специфікації, що його породило | Завжди встановлюйте спостережене покоління умови й верхнього рівня з `obj.Generation` |
| Тести без `Eventually` | Тест припускає синхронність узгодження, бо локальна машина швидка | Опитуйте очікуваний стан API за допомогою `Eventually` з реалістичними тайм-аутами |
| Невтестований шлях видалення | Шляхи створення й оновлення здаються більш видимими, тому помилки фіналайзера ховаються, доки користувач не видалить ресурс | Додайте кейс envtest, що чекає на фіналайзер, видаляє об'єкт і спостерігає остаточне видалення |
| Забування зареєструвати типи зі схемою | envtest запускається, але клієнт не може закодувати чи декодувати кастомний ресурс | Викликайте `AddToScheme` свого пакета API під час налаштування набору перед створенням клієнта |

## Тест

<details><summary>Сценарій: користувач запускає `kubectl delete webapp critical-db`, і WebApp залишається в стані `Terminating` з усе ще присутнім `apps.kubedojo.io/finalizer`. Що слід оглянути першим, і яка поведінка контролера найімовірніше блокує видалення?</summary>

`deletionTimestamp` плюс фіналайзер означають, що Kubernetes чекає, доки ваш контролер завершить очищення й видалить свій фіналайзер. Огляньте логи оператора навколо шляху очищення, потім перевірте будь-які виклики зовнішнього API, від яких залежить видалення, як-от видалення DNS чи балансувальника навантаження. Імовірним блокувальником є те, що `cleanupExternalResources` повертає помилку, зависає без тайм-ауту або ніколи не досягає `controllerutil.RemoveFinalizer`. Правильне виправлення — не сліпо прибрати фіналайзер; виправте або безпечно обійдіть збій очищення, а потім дозвольте контролеру видалити фіналайзер після того, як очищення вдалося або зовнішній ресурс підтверджено відсутній.

</details>

<details><summary>Сценарій: розробник пропонує додавати нову умову `Ready` на кожне узгодження, бо це простіше, ніж використовувати `meta.SetStatusCondition`. Чому вам слід відхилити цей проєкт?</summary>

Умови задумані поводитися як набір, індексований за `Type`, а не як історичний лог. Додавання створює дубльовані записи `Ready`, залишає застарілі значення в масиві й може заплутати користувачів чи автоматизацію, що читає першу збіжну умову. Воно також робить `LastTransitionTime` шумним, бо код схильний скидати мітки часу, навіть коли статус фактично не переходив. `meta.SetStatusCondition` оновлює наявну умову для типу й зберігає конвенції умов Kubernetes, тому це безпечніший проєкт.

</details>

<details><summary>Сценарій: SRE бачить `Ready=False` з причиною `Reconciling`, але йому потрібно знати, чи створив оператор Деплоймент, масштабував його чи натрапив на помилку API. Який сигнал йому слід оглянути, і чому це не все зберігається в умовах?</summary>

Йому слід оглянути події Kubernetes за допомогою `kubectl describe webapp <name>` чи `kubectl get events`, відфільтровані до WebApp. Умови представляють поточний стан, тоді як події представляють нещодавні точкові в часі дії й попередження. Розміщення кожної історичної дії в умовах роздуло б об'єкт статусу й ускладнило б розбір готовності. Оператор має тримати стабільну умову на кшталт `Ready=False` і використовувати події, щоб показати хронологію, що призвела до поточного стану.

</details>

<details><summary>Сценарій: PR додає envtest, який створює WebApp і одразу очікує, що Деплоймент існуватиме, через прямий `Get`. Тест проходить локально, але випадково падає в CI. У чому вада, і як слід переписати тест?</summary>

Тест трактує узгодження як синхронне, але контролер обробляє події асинхронно через менеджер і сервер API. На швидкому ноутбуці Деплоймент може з'явитися до твердження, тоді як повільніше CI-завдання оголює гонитву. Тест має обгорнути `Get` у `Eventually`, використовуючи тайм-аут та інтервал опитування, що дають контролеру час спостерегти WebApp і створити дочірній Деплоймент. Миттєві твердження все ще прийнятні для чистих полів об'єкта після успішного `Get`, але не для стану, що залежить від узгодження.

</details>

<details><summary>Сценарій: ви розгортаєте дві репліки оператора з увімкненим вибором лідера, потім вузол-лідер перезавантажується. Нові WebApp чекають близько 15 секунд до відновлення узгодження. Чи це помилка, і як ви поясните затримку?</summary>

Ця затримка очікувана, коли старий лідер зникає, не звільнивши Lease. Резервний Под має чекати, доки тривалість оренди закінчиться, перш ніж набути лідерства, інакше повільний чи відмежований старий лідер міг би накластися на нового лідера й створити узгодження «розщеплений мозок». Усталений таймінг віддає перевагу коректності над миттєвим переходом. Якщо затримка неприйнятна, тюньте налаштування вибору лідера обережно й тестуйте затримку сервера API, бо надмірно агресивні налаштування можуть спричинити непотрібну метушню лідерства.

</details>

<details><summary>Сценарій: API хмарного провайдера повертає 503, поки фіналайзер видаляє зовнішній балансувальник навантаження. Що має повернути цикл узгодження, і що відбувається з WebApp під час збою?</summary>

Цикл узгодження має повернути помилку й тримати фіналайзер прикріпленим. WebApp залишається в стані `Terminating`, що є безпечним станом, бо Kubernetes не вилучить кастомний ресурс, поки очищення незавершене. controller-runtime повторить запит із відкладанням, даючи провайдеру час відновитися. Щойно очищення вдасться або балансувальник навантаження буде підтверджено вже відсутнім, контролер може видалити фіналайзер і дозволити видаленню завершитися.

</details>

<details><summary>Сценарій: ви додаєте `GenerationChangedPredicate` і до спостереження WebApp, і до спостереження власного Деплойменту. Після ручної зміни Деплойменту оператор не ремонтує дрейф. Чому предикат це спричинив, і що вам слід змінити?</summary>

`GenerationChangedPredicate` пропускає події лише тоді, коли змінюється `metadata.generation`, а це може відкидати події, потрібні вашому контролеру від власних ресурсів. Якщо оператор залежить від статусу Деплойменту чи інших оновлень для виявлення дрейфу, фільтрування власного спостереження не дає узгодженню бути поставленим у чергу. Тримайте предикат на первинному WebApp, коли хочете ігнорувати там оновлення лише статусу, але залишайте спостереження Деплойменту без фільтрів або використовуйте вужчий предикат, що зберігає потрібні вам сигнали дрейфу. Оптимізація має слідувати за виміряним тиском черги, а не усувати сигнали коректності за замовчуванням.

</details>

## Практична вправа

Сценарій вправи: розширте оператор WebApp із Модуля 1.4 фіналайзерами, умовами статусу, подіями Kubernetes, вибором лідера, спостереженнями за власними ресурсами та інтеграційними тестами envtest. Працюйте в одноразовому репозиторії чи гілці, бо ця вправа торкається коду контролера, налаштування менеджера, маніфестів і тестів. Мета — довести, що оператор може безпечно створювати, оновлювати, звітувати та видаляти, а не лише компілюватися.

```bash
# Use the operator from Module 1.4
cd ~/extending-k8s/webapp-operator

# Ensure dependencies are up to date
go mod tidy

# Ensure envtest binaries are installed
make envtest
```

Завдання 1 — додати константу фіналайзера й змінити `Reconcile` так, щоб видалення оброблялося перед звичайним узгодженням. Додайте фіналайзер перед створенням зовнішніх ресурсів, повертайтеся після оновлення метаданих і робіть очищення ідемпотентним. Сигнал успіху — новий WebApp отримує фіналайзер, а видалений WebApp не зникає, доки очищення не завершиться.

Завдання 2 — додати структуровані умови, реалізувавши функцію `updateConditions` із цього модуля. Умови мають включати `DeploymentReady`, `ServiceReady` та агреговану `Ready`, кожну з `ObservedGeneration`, причиною в CamelCase та корисним повідомленням. Сигнал успіху — вивід `kubectl describe` та JSONPath показує поточні значення умов, прив'язані до найновішого покоління.

Завдання 3 — додати `EventRecorder` до узгоджувача й видавати події для створення Деплойменту, оновлень реплік, оновлень образу, початку очищення, завершення очищення та шляхів попереджень. Тримайте події стислими й уникайте видачі повторюваних подій прогресу, коли нічого не змінилося. Сигнал успіху — `kubectl describe webapp advanced-demo` показує корисну нещодавню хронологію.

Завдання 4 — підключити вибір лідера через `cmd/main.go` та розгортання менеджера. Запускайте дві репліки лише тоді, коли контролер розгорнуто в кластері, бо локальна розробка через `make run` зазвичай використовує один процес. Сигнал успіху — одна репліка тримає Lease, поки інша чекає, а узгодження відновлюється після видалення Под'а-лідера.

Завдання 5 — створити набір envtest у `internal/controller/suite_test.go` і написати тести життєвого циклу для створення, оновлень реплік, видалення з фіналайзером та умов статусу. Використовуйте `Eventually` для кожного твердження, що залежить від узгодження. Сигнал успіху — стабільний прогін `make test`, що проходить повторно, а не лише на найшвидшій локальній спробі.

```bash
make test
```

```bash
kind create cluster --name advanced-operator-lab
make install
make run

# In another terminal
cat << 'EOF' | kubectl apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: advanced-demo
spec:
  image: nginx:1.27
  replicas: 2
  port: 80
EOF

# Checkpoint: Wait for the operator to successfully reconcile the resource
kubectl wait --for=condition=Ready webapp/advanced-demo --timeout=60s

# Check events
kubectl describe webapp advanced-demo

# Check conditions
kubectl get webapp advanced-demo -o jsonpath='{range .status.conditions[*]}{.type}: {.status} ({.reason}){"\n"}{end}'

# Delete and watch cleanup
kubectl delete webapp advanced-demo
kubectl get events --sort-by=.lastTimestamp | tail -10
```

```bash
kind delete cluster --name advanced-operator-lab
```

Критерії успіху:

- [ ] Фіналайзер додається при створенні.
- [ ] Фіналайзер запобігає миттєвому видаленню, і очищення виконується першим.
- [ ] Умови статусу включають `DeploymentReady`, `ServiceReady` та `Ready`.
- [ ] `ObservedGeneration` правильно встановлюється на статусі та умовах.
- [ ] Події Kubernetes видимі в `kubectl describe`.
- [ ] Прапор вибору лідера підключено для розгортання з кількома репліками.
- [ ] Принаймні чотири інтеграційні тести envtest покривають створення, оновлення, видалення та умови.
- [ ] `make test` завершується чисто.

## Джерела

- https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/
- https://pkg.go.dev/k8s.io/apimachinery/pkg/apis/meta/v1#Condition
- https://pkg.go.dev/k8s.io/apimachinery/pkg/api/meta#SetStatusCondition
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/envtest
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/manager
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/builder
- https://book.kubebuilder.io/reference/envtest

## Наступний модуль

[Модуль 1.6: Вебхуки допуску](../module-1.6-admission-webhooks/) — Перехоплюйте та модифікуйте запити API за допомогою мутаційних та валідаційних вебхуків.





