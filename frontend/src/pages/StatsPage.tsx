import { useQuery } from "@tanstack/react-query";
import { getStats } from "../api/client";

export function StatsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    refetchInterval: 30_000,
  });

  if (isLoading) return <div className="p-8 text-gray-600">Загрузка...</div>;
  if (error) return <div className="p-8 text-red-600">Ошибка загрузки.</div>;

  const items = [
    { label: "Обработано источников", value: data?.processed_sources ?? 0 },
    { label: "Выявлено кандидатов", value: data?.total_candidates ?? 0 },
    { label: "Уверенность >75%", value: data?.signals_above_75 ?? 0 },
  ];

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-[#0079C2] mb-6">Слабые сигналы</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((it) => (
          <div key={it.label} className="rounded-xl border bg-white p-4 shadow-sm">
            <div className="text-sm text-gray-500">{it.label}</div>
            <div className="text-3xl font-bold mt-1 text-[#0079C2]">
              {it.value.toLocaleString("ru-RU")}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}