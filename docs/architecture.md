# Архитектура системы

## Компоненты

### Backend (FastAPI)

- POST /api/search — живой поиск и ранжирование слабых сигналов.
- GET /api/search/{search_id} — получение ранее выполненного поиска (в памяти процесса).
- GET /api/insight/{doc_id} — детализация по сигналу.
- GET /api/stats — статистика.
- GET /health — проверка работоспособности.

Скоринг: гибридная схема — (1) Logistic Regression отсеивает junk (confidence > 0.9); (2) для остальных — retrieval + GigaChat.

Retrieval: поиск ближайших записей одновременно в weak_signals и negative_signals.

### Frontend (React + Vite)

- StatsPage — статистика.
- SearchPage — ввод запроса, ТОП-15.
- InsightPage — детализация сигнала.

### PostgreSQL

Таблицы:
- sources — справочник источников
- documents — нормализованные документы
- weak_signals — эталонные weak-сигналы
- negative_signals — эталонные negative-сигналы
- raw_weak_signals — сырые weak-кандидаты
- raw_negative_signals — сырые negative-кандидаты
- raw_junk_signals — сырые junk-кандидаты
- scored_documents — кэш скоринга GigaChat

### GigaChat

1. Скоринг и объяснения для каждого кандидата.
2. Резюме на русском для InsightPage.

### Эмбеддинги

Модель paraphrase-multilingual-MiniLM-L12-v2, 384 числа.

### Классификатор

Logistic Regression, 3 класса: weak, negative, junk.

## Потоки данных

1. Пользователь вводит запрос.
2. Multi-search собирает кандидатов из 21 источника.
3. Дедупликация по doc_id.
4. Классификатор отсеивает junk.
5. Retrieval находит похожие weak и negative.
6. GigaChat скорит кандидатов.
7. Группировка по технологии.
8. API возвращает ТОП-15.
9. Frontend отображает.

## Схема БД

### sources
- id (Integer, PK)
- domain (String(255), unique)
- name (String(255))
- source_type (String(50))
- region (String(50))
- language (String(10))
- trust (Float, default 0.5)
- created_at (DateTime)

### documents
- id (Integer, PK)
- doc_id (String(500), unique)
- source_id (FK → sources.id)
- title (Text)
- abstract (Text, nullable)
- url (String(500), nullable)
- label (Integer, nullable)
- created_at (DateTime)

### weak_signals
- id (Integer, PK)
- name (Text)
- area (String(100))
- why_weak_signal (Text)
- stage (String(100))
- embedding (JSON)

### negative_signals
- id (Integer, PK)
- name (Text)
- description (Text, nullable)
- embedding (JSON, nullable)

### raw_weak_signals / raw_negative_signals
- id (Integer, PK)
- name (Text)
- description (Text, nullable)
- embedding (JSON, nullable)

### raw_junk_signals
- id (Integer, PK)
- name (Text)
- description (Text, nullable)
- category (String(50), nullable)
- embedding (JSON, nullable)

### scored_documents
- id (Integer, PK)
- doc_id (String(500), unique)
- is_weak_signal (Integer)
- confidence (Float)
- technology (Text, nullable)
- description (Text, nullable)
- why_weak_signal (Text, nullable)
- excluded_trends (JSON, nullable)
- retrieval_weak (JSON, nullable)
- retrieval_negative (JSON, nullable)
