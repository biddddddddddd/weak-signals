# Weak Signals Detector

Система автоматизированного выявления зарождающихся научно-технологических трендов (слабых сигналов) на основе анализа открытых источников.

## Стек

- Python 3.11
- FastAPI + Uvicorn
- PostgreSQL 16
- LightGBM + scikit-learn
- React (frontend, в разработке)

## Запуск

1. Установить Docker Desktop.
2. Скопировать `.env.example` в `.env`.
3. Запустить:
   ```
   docker compose up --build
   ```
4. Открыть http://localhost:8000/docs

## Структура

- `backend/` — API, парсеры, ML-модели
- `frontend/` — React-интерфейс (в разработке)
- `config/` — веса и множители формулы
- `data/` — сырые и обработанные данные
- `docs/` — документация и схемы

## Документация

- [Методология](docs/methodology.md)
- [Архитектура](docs/architecture.md)