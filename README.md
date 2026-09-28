# Weak Signal Radar

Сервис для автоматизированного поиска слабых сигналов в научно-технологических отраслях. Анализирует открытые источники (научные базы, препринты, техно-платформы, СМИ), выявляет зарождающиеся технологии, отсеивает мусор (хайп, псевдонауку, философские рассуждения) и уже зрелые/массовые тренды, формирует ТОП-15 сигналов с объяснениями на русском языке.

## Стек технологий

| Слой | Технологии |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| БД | PostgreSQL 16 |
| Frontend | React + Vite, TypeScript |
| ML / NLP | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2), scikit-learn |
| LLM | GigaChat (скоринг, объяснения, резюме) |
| Инфраструктура | Docker, Docker Compose |

## Требования для запуска

- Docker Desktop
- Node.js 20+
- Аккаунт GigaChat (для получения GIGACHAT_API_KEY)

## Пошаговая инструкция развёртывания

1. Клонировать репозиторий:
   git clone <repo_url>
   cd <repo_name>

2. Скопировать файл окружения и заполнить ключи GigaChat:
   cp .env.example .env
   В .env указать:
   GIGACHAT_API_KEY=...
   GIGACHAT_SCOPE=...

3. Поднять инфраструктуру:
   docker compose up -d postgres backend

4. Инициализировать таблицы БД:
   docker compose exec backend python -m src.db.init_db

5. Загрузить golden-датасет:
   docker compose exec backend python -m src.scripts.load_seeds

6. Построить эмбеддинги для датасета:
   docker compose exec backend python -m src.scripts.build_embeddings

7. Запустить фронтенд:
   cd frontend
   npm install
   npm run dev

8. Открыть в браузере: http://localhost:5173

## Проверка работы

Проверка бэкенда:
curl http://localhost:8000/health

Статистика:
curl http://localhost:8000/api/stats

Поиск слабых сигналов:
curl -X POST http://localhost:8000/api/search -H "Content-Type: application/json" -d "{\"query\":\"нейроморфные вычисления\",\"limit\":15}"

## Скрипты сбора данных и обучения модели

Все скрипты находятся в backend/src/scripts/ и запускаются через docker compose exec backend python -m src.scripts.<script_name>.

Обученная модель уже в репозитории: data/models/classifier.pkl и data/models/scaler.pkl.

Сбор сырых данных:
- collect_raw_weak.py — arXiv / OpenAlex / Crossref
- collect_raw_weak_github.py — GitHub
- collect_raw_weak_producthunt.py — Product Hunt
- collect_raw_negative.py — negative-примеры
- collect_dataset.py — общий сбор
- generate_raw_junk.py — генерация junk

Расширение датасета:
- add_negative_batch.py
- add_junk_batch.py
- add_short_weak.py
- add_short_negative_junk.py
- add_irrelevant_negative.py
- add_targeted_fixes.py
- augment_all.py

Подготовка данных и обучение:
- load_seeds.py
- build_embeddings.py
- build_raw_embeddings.py
- deduplicate_raw.py
- report_raw_stats.py
- build_final_dataset.py
- train_classifier.py

Отладка и демонстрация:
- debug_llm.py, debug_retrieval.py, debug_search.py, debug_search2.py
- big_test.py, demo_test.py, demo_test_v2.py

## Зависимости

Полный список см. в backend/requirements.txt.

## Структура проекта

backend/        # FastAPI-приложение
frontend/       # React + Vite приложение
data/           # датасеты и модели
config/         # конфигурация источников
docs/           # техническая документация

## Документация

- docs/architecture.md
- docs/methodology.md
- docs/data_pipeline.md
- docs/sources.md
- docs/metrics.md
- docs/roadmap.md
- docs/demo_script.md
- docs/submission_checklist.md
