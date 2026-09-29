import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { SearchBar } from "../components/SearchBar";

const EXAMPLE_QUERIES = [
  "quantum",
  "memory",
  "teleportation",
  "navigation",
  "learning",
  "magnetometer",
];

const SOURCES = [
  "arXiv",
  "Nature",
  "IEEE Spectrum",
  "PubMed",
  "OpenAlex",
  "HAL Science",
  "TechXplore",
  "Phys.org",
];

export function SearchPage() {
  const [query, setQuery] = useState("");

  const mutation = useMutation({
    mutationFn: async (q: string) => {
      const { data } = await axios.get(
        `/api/candidates?q=${encodeURIComponent(q)}&limit=20`
      );
      return data;
    },
  });

  const { data: stats } = useQuery({
    queryKey: ["stats"],
    queryFn: async () => {
      const { data } = await axios.get("/api/stats");
      return data;
    },
  });

  const { data: preview } = useQuery({
    queryKey: ["preview-signals"],
    queryFn: async () => {
      const { data } = await axios.get("/api/candidates?limit=6");
      return data;
    },
    staleTime: 5 * 60_000,
  });

  const runExample = (q: string) => {
    setQuery(q);
    mutation.mutate(q);
  };

  const signals = mutation.data?.signals ?? [];
  const previewSignals = preview?.signals ?? [];

  // Показываем результаты, если уже был поиск (успешный или с ошибкой)
  const hasSearched = mutation.isSuccess || mutation.isError || mutation.isPending;

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10">
      {/* ============ HERO + SEARCH ============ */}
      <section className="space-y-6">
        <div className="text-center space-y-3">
          <h1 className="text-4xl md:text-5xl font-bold text-[#0079C2]">
            Найдите тренд раньше всех
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Автоматический поиск слабых сигналов в научных публикациях,
            патентах и отраслевых отчётах
          </p>
        </div>

        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={(q) => mutation.mutate(q)}
          loading={mutation.isPending}
        />

        <div className="max-w-3xl mx-auto flex flex-wrap gap-2 justify-center">
          <span className="text-sm text-gray-500 self-center mr-1">
            Популярные запросы:
          </span>
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => runExample(q)}
              className="px-4 py-1.5 text-sm rounded-full bg-white border border-[#0079C2]/30 text-[#0079C2] hover:bg-[#0079C2] hover:text-white transition"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* ============ РЕЗУЛЬТАТЫ ПОИСКА (сразу под чипсами) ============ */}
      {hasSearched && (
        <section className="space-y-4">
          {mutation.isPending && (
            <div className="p-6 rounded-2xl bg-white text-center text-gray-500 shadow-sm">
              Идёт поиск…
            </div>
          )}

          {mutation.isError && (
            <div className="p-4 rounded-xl bg-red-50 text-red-700 text-center">
              Ошибка. Проверь, что бэкенд работает на порту 8000.
            </div>
          )}

          {mutation.isSuccess && signals.length === 0 && (
            <div className="p-6 rounded-2xl bg-white text-center text-gray-600 shadow-sm">
              По запросу «{query}» ничего не найдено. Попробуй другой.
            </div>
          )}

                    {signals.length > 0 && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => {
                      setQuery("");
                      mutation.reset();
                    }}
                    className="inline-flex items-center gap-1.5 text-sm text-[#0079C2] hover:text-[#005A91] font-medium px-3 py-1.5 rounded-lg hover:bg-[#E6F2FA] transition"
                  >
                    ← Назад к главной
                  </button>
                  <h2 className="text-2xl font-bold text-gray-800">
                    Найдено {signals.length} сигналов
                  </h2>
                </div>
                <span className="text-sm text-gray-500">
                  по запросу «{query}»
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {signals.map((s: any) => (
                  <SignalCard key={s.id} signal={s} />
                ))}
              </div>
            </>
          )}
        </section>
      )}

      {/* ============ СТАТИЧНЫЕ БЛОКИ — только если не было поиска ============ */}
      {!hasSearched && (
        <>
          {/* Статистика */}
          {stats && (
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                icon="📚"
                label="Источников обработано"
                value={stats.total_documents ?? 0}
                tint="bg-blue-50 text-blue-700"
              />
              <StatCard
                icon="⭐"
                label="Сигналов с уверенностью >75%"
                value={stats.signals_above_75 ?? 0}
                tint="bg-amber-50 text-amber-700"
              />
              <StatCard
                icon="🎯"
                label="Всего сигналов в базе"
                value={stats.scored_documents ?? 0}
                tint="bg-emerald-50 text-emerald-700"
              />
            </section>
          )}

          {/* Как это работает */}
          <section className="space-y-6">
            <h2 className="text-2xl font-bold text-center text-gray-800">
              Как это работает
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StepCard
                number="1"
                icon="📥"
                title="Собираем"
                text="Более 2 000 статей из arXiv, Nature, IEEE, PubMed и других научных источников"
              />
              <StepCard
                number="2"
                icon="🧠"
                title="Фильтруем"
                text="ML-классификатор + GigaChat отсеивают мусор, хайп и зрелые технологии"
              />
              <StepCard
                number="3"
                icon="⭐"
                title="Показываем"
                text="ТОП зарождающихся сигналов с описанием, преимуществом и источниками"
              />
            </div>
          </section>

          {/* Свежие сигналы */}
          {previewSignals.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h2 className="text-2xl font-bold text-gray-800">
                  Свежие слабые сигналы
                </h2>
                <button
                  onClick={() => {
                    setQuery("quantum");
                    mutation.mutate("quantum");
                  }}
                  className="text-sm text-[#0079C2] hover:underline"
                >
                  Показать все →
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {previewSignals.map((s: any) => (
                  <SignalCard key={s.id} signal={s} />
                ))}
              </div>
            </section>
          )}

          {/* Источники */}
          <section className="space-y-3 text-center">
            <div className="text-sm text-gray-500">
              Данные из проверенных источников
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {SOURCES.map((s) => (
                <span
                  key={s}
                  className="px-3 py-1 text-xs rounded-full bg-white border border-gray-200 text-gray-600"
                >
                  {s}
                </span>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="rounded-2xl bg-gradient-to-r from-[#0079C2] to-[#005A91] text-white p-8 text-center space-y-3">
            <h2 className="text-2xl font-bold">
              Хочешь увидеть полную аналитику?
            </h2>
            <p className="text-white/80">
              Счётчики источников, распределение сигналов по стадиям, метрики
              модели
            </p>
            <a
              href="/stats"
              className="inline-block mt-2 px-6 py-3 rounded-lg bg-white text-[#0079C2] font-semibold hover:bg-[#E6F2FA] transition"
            >
              Открыть панель аналитики →
            </a>
          </section>
        </>
      )}
    </div>
  );
}

/* ============================================================ */

function StatCard({
  icon,
  label,
  value,
  tint,
}: {
  icon: string;
  label: string;
  value: number;
  tint: string;
}) {
  return (
    <div className="rounded-2xl bg-white shadow-sm border border-gray-100 p-5 flex items-center gap-4">
      <div
        className={`w-12 h-12 flex items-center justify-center rounded-xl text-2xl ${tint}`}
      >
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-800">
          {value.toLocaleString("ru-RU")}
        </div>
        <div className="text-sm text-gray-500">{label}</div>
      </div>
    </div>
  );
}

function StepCard({
  number,
  icon,
  title,
  text,
}: {
  number: string;
  icon: string;
  title: string;
  text: string;
}) {
  return (
    <div className="relative rounded-2xl bg-white shadow-sm border border-gray-100 p-6 space-y-2">
      <span className="absolute -top-3 -left-3 w-8 h-8 flex items-center justify-center rounded-full bg-[#0079C2] text-white text-sm font-bold">
        {number}
      </span>
      <div className="text-3xl">{icon}</div>
      <h3 className="font-semibold text-gray-900">{title}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{text}</p>
    </div>
  );
}

function SignalCard({ signal }: { signal: any }) {
  const score = Math.round((signal.score ?? 0) * 100);
  const stageIcon =
    signal.trend_stage === "Пилот"
      ? "🚀"
      : signal.trend_stage === "Прототип"
      ? "🛠"
      : signal.trend_stage === "Раннее внедрение"
      ? "🌱"
      : "🔬";

  const openInsight = () => {
    window.location.href = `/insight/${encodeURIComponent(signal.id)}`;
  };

  return (
    <div
      onClick={openInsight}
      className="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition cursor-pointer p-5 space-y-3"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-gray-900 leading-snug group-hover:text-[#0079C2] transition">
          {signal.technology}
        </h3>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#E6F2FA] text-[#0079C2] whitespace-nowrap">
          {score}%
        </span>
      </div>

      <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#0079C2] to-[#4BA3DB]"
          style={{ width: `${score}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="inline-flex items-center gap-1.5 text-gray-600">
          {stageIcon} {signal.trend_stage || "—"}
        </span>
        <span className="text-[#0079C2] font-medium opacity-0 group-hover:opacity-100 transition">
          Подробнее →
        </span>
      </div>
    </div>
  );
}