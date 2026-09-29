import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import axios from "axios";

export function InsightPage() {
  const { id = "" } = useParams<{ id: string }>();
  const docId = decodeURIComponent(id);

  const { data, isLoading, error } = useQuery({
    queryKey: ["insight", docId],
    queryFn: async () => {
      const { data } = await axios.get(`/api/insight/${encodeURIComponent(docId)}`);
      return data;
    },
    enabled: !!docId,
  });

  if (isLoading) return <div className="p-8 text-gray-600">Загрузка инсайта…</div>;
  if (error || !data)
    return (
      <div className="p-8">
        <Link to="/" className="text-[#0079C2] hover:underline">← Назад к поиску</Link>
        <div className="mt-4 text-red-600">Не удалось загрузить инсайт.</div>
      </div>
    );

  return (
    <article className="max-w-4xl mx-auto p-8 space-y-6">
      <Link to="/" className="text-[#0079C2] text-sm hover:underline">
        ← Назад к поиску
      </Link>

      <header className="space-y-2">
        <h1 className="text-3xl font-bold">{data.technology || "—"}</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="inline-block px-2 py-0.5 rounded border bg-green-100 text-green-800 border-green-300">
            {Math.round((data.score ?? 0) * 100)}%
          </span>
          <span className="text-sm text-gray-500">Уверенность модели</span>
          {data.trust_level && (
            <span className="text-sm text-gray-500">· Trust level: {data.trust_level}</span>
          )}
        </div>
      </header>

      <Section title="Описание технологии">
        {data.description || "—"}
      </Section>

      <Section title="Потенциальное преимущество">
        {data.advantage || "—"}
      </Section>

      {data.case_examples?.length > 0 && (
        <Section title="Кейс-примеры">
          <ul className="list-disc list-inside space-y-1">
            {data.case_examples.map((c: string, i: number) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Почему это слабый сигнал">
        {data.why_weak_signal || "—"}
      </Section>

      <Section title="Почему такая уверенность">
        {data.why_this_score || "—"}
      </Section>

      {data.excluded_trends?.length > 0 && (
        <Section title="Похожие зрелые тренды, которые исключены">
          <ul className="list-disc list-inside space-y-1">
            {data.excluded_trends.map((c: string, i: number) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Section>
      )}

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Источники</h2>
        {(data.sources || []).map((s: any) => (
          <div key={s.id} className="rounded-lg border bg-white p-4 space-y-1">
            <a
              href={s.url}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-[#0079C2] hover:underline break-all"
            >
              {s.original_title || s.name || s.url}
            </a>
            <div className="flex flex-wrap gap-2 text-xs">
              {s.type && (
                <span className="px-2 py-0.5 rounded bg-gray-100">Тип: {s.type}</span>
              )}
              {s.language && (
                <span className="px-2 py-0.5 rounded bg-gray-100">
                  Язык: {String(s.language).toUpperCase()}
                </span>
              )}
              {s.trust_level !== undefined && (
                <span className="px-2 py-0.5 rounded bg-gray-100">
                  Доверенность: {s.trust_level}
                </span>
              )}
              {s.publication_date && (
                <span className="px-2 py-0.5 rounded bg-gray-100">
                  Дата: {String(s.publication_date).slice(0, 10)}
                </span>
              )}
            </div>
          </div>
        ))}
      </section>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="text-gray-800 leading-relaxed whitespace-pre-line">{children}</div>
    </section>
  );
}