# Метрики классификатора слабых сигналов

## Архитектура

- **Модель:** Logistic Regression (multinomial, `class_weight='balanced'`)
- **Признаки:** эмбеддинги `paraphrase-multilingual-MiniLM-L12-v2` (384 числа)
- **Классы:** `weak` (слабый сигнал), `negative` (зрелая технология), `junk` (мусор)
- **Датасет:** 3145 примеров
  - weak: 1016 (100 golden + 916 augmented)
  - negative: 1344 (250 golden + 1094 augmented)
  - junk: 785 (сгенерировано через GigaChat)
- **Разбиение:** 70% train (2201), 15% val (472), 15% test (472), stratified

## Результаты на Validation (472 примера)

| Класс | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| weak | 0.93 | 0.94 | 0.94 | 152 |
| negative | 0.96 | 0.95 | 0.95 | 202 |
| junk | 0.92 | 0.92 | 0.92 | 118 |
| **Accuracy** | | | **0.939** | 472 |
| **Macro avg** | 0.94 | 0.94 | **0.94** | 472 |
| **Weighted avg** | 0.94 | 0.94 | 0.94 | 472 |

### Confusion matrix (validation)
pred_weak pred_negative pred_junk
true_weak [ 143 3 6 ]
true_neg [ 6 192 4 ]
true_junk [ 4 6 108 ]


## Результаты на Test (472 примера)

| Класс | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| weak | 0.94 | 0.86 | 0.90 | 152 |
| negative | 0.93 | 0.93 | 0.93 | 202 |
| junk | 0.83 | 0.93 | 0.88 | 118 |
| **Accuracy** | | | **0.905** | 472 |
| **Macro avg** | 0.90 | 0.90 | **0.90** | 472 |
| **Weighted avg** | 0.91 | 0.90 | 0.91 | 472 |

### Confusion matrix (test)
pred_weak pred_negative pred_junk
true_weak [ 130 8 14 ]
true_neg [ 6 187 9 ]
true_junk [ 2 6 110 ]


## Соответствие требованиям ТЗ

ТЗ требует точность классификации **не ниже 75–80%**.

| Метрика | Значение | Требование | Статус |
|---|---|---|---|
| Accuracy (test) | **0.905** | ≥ 0.75–0.80 | ✅ выше на 10–15 п.п. |
| F1 macro (test) | **0.900** | ≥ 0.75–0.80 | ✅ выше на 10 п.п. |
| F1 weak (test) | **0.90** | ≥ 0.75 | ✅ |
| F1 negative (test) | **0.93** | ≥ 0.75 | ✅ |
| F1 junk (test) | **0.88** | — | ✅ |

## Интерпретируемость

Logistic Regression даёт **веса признаков** (384 веса на класс). Это позволяет показать, какие компоненты эмбеддинга вносят вклад в решение. Для более глубокой интерпретации используется SHAP (`shap.LinearExplainer`).

Основные источники ошибок (test):
- 14 weak → junk: модель считает часть слабых сигналов мусором (низкая конкретность технологии).
- 8 weak → negative: слабый сигнал похож на зрелый тренд.
- 9 negative → junk: зрелая технология с размытым описанием.
- 6 negative → weak: зрелая технология с признаками новизны.
- 6 junk → negative: мусор, маскирующийся под зрелую технологию.

## Воспроизводимость

```bash
# 1. Собрать финальный датасет
docker compose exec backend python -m src.scripts.build_final_dataset

# 2. Обучить классификатор
docker compose exec backend python -m src.scripts.train_classifier

## Соответствие требованиям ТЗ

ТЗ требует точность классификации **не ниже 75–80%**.

| Метрика | Значение | Требование | Статус |
|---|---|---|---|
| Accuracy (test) | **0.905** | ≥ 0.75–0.80 | ✅ выше на 10–15 п.п. |
| F1 macro (test) | **0.900** | ≥ 0.75–0.80 | ✅ выше на 10 п.п. |
| F1 weak (test) | **0.90** | ≥ 0.75 | ✅ |
| F1 negative (test) | **0.93** | ≥ 0.75 | ✅ |
| F1 junk (test) | **0.88** | — | ✅ |

## Интерпретируемость

Logistic Regression даёт **веса признаков** (384 веса на класс). Это позволяет показать, какие компоненты эмбеддинга вносят вклад в решение. Для более глубокой интерпретации используется SHAP (`shap.LinearExplainer`).

Основные источники ошибок (test):
- 14 weak → junk: модель считает часть слабых сигналов мусором (низкая конкретность технологии).
- 8 weak → negative: слабый сигнал похож на зрелый тренд.
- 9 negative → junk: зрелая технология с размытым описанием.
- 6 negative → weak: зрелая технология с признаками новизны.
- 6 junk → negative: мусор, маскирующийся под зрелую технологию.

## Воспроизводимость

```bash
# 1. Собрать финальный датасет
docker compose exec backend python -m src.scripts.build_final_dataset

# 2. Обучить классификатор
docker compose exec backend python -m src.scripts.train_classifier

---

## Шаг 2. Починить классификатор

**Проблема:** augmented negative **слишком однородные** — все короткие фразы вроде `Kubernetes`, `Docker`, `GPT-4`. А augmented weak — длинные описания технологий. Модель выучила **длину и стиль**, а не смысл.

**Решение:** обучить классификатор **только на golden + augmented weak** (без augmented negative), и использовать **порог уверенности**:

- Если классификатор говорит `weak` с confidence > 0.9 — пропускаем.
- Если `weak` с confidence < 0.9 — зовём LLM для проверки.

**Или** переобучить с **балансировкой**:
- Убрать augmented negative совсем (оставить только golden 250).
- Убрать augmented weak (оставить golden 100 + github 300).
- Обучить на чистом golden + github.

Но тогда метрики упадут.

**Правильный путь:** использовать классификатор **только как фильтр junk**, а weak/negative различать через **retrieval + LLM** (как было раньше).

То есть:
- Классификатор говорит `junk` → отсекаем.
- Классификатор говорит `weak` или `negative` → идём в retrieval + LLM.
- LLM решает: weak или negative.

Это **гибридный подход**: классификатор для junk, LLM для weak/negative.

## Шаг 3. Проверь, что классификатор делает

Выполни:

```cmd
docker compose exec backend python -c "from src.ml.classifier import classify_text; tests = ['Kubernetes', 'Docker', 'GPT-4', 'Transformer architecture', 'нейроморфные чипы на мемристорах', 'квантовое сжатие моделей', 'торсионные поля', 'биополе', 'астрология', 'квантовый ум']; [print(t, '→', classify_text(t)['label'], round(classify_text(t)['confidence'], 3)) for t in tests]"