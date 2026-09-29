import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface Suggestion {
  id: string;
  technology: string;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  loading,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (q: string) => void;
  loading?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [filtered, setFiltered] = useState<Suggestion[]>([]);
  const [highlight, setHighlight] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Загружаем все технологии один раз
  const { data: pool } = useQuery({
    queryKey: ["suggestions-pool"],
    queryFn: async () => {
      const { data } = await axios.get("/api/candidates?limit=200");
      return (data.signals || []) as Suggestion[];
    },
    staleTime: 5 * 60_000,
  });

  // Фильтруем при вводе
  useEffect(() => {
    if (!value.trim() || !pool) {
      setFiltered([]);
      return;
    }
    const q = value.toLowerCase();
    const items = pool
      .filter((s) => s.technology.toLowerCase().includes(q))
      .slice(0, 8);
    setFiltered(items);
    setHighlight(0);
  }, [value, pool]);

  // Клик вне — закрыть
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const pick = (tech: string) => {
    onChange(tech);
    setOpen(false);
    onSubmit(tech);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || filtered.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => (h + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => (h - 1 + filtered.length) % filtered.length);
    } else if (e.key === "Enter" && filtered[highlight]) {
      e.preventDefault();
      pick(filtered[highlight].technology);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} className="relative max-w-3xl mx-auto w-full">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (value.trim()) {
            setOpen(false);
            onSubmit(value.trim());
          }
        }}
      >
        <div className="flex flex-col sm:flex-row gap-3 bg-white rounded-2xl shadow-lg p-3">
          <input
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
            placeholder="Например: quantum, agent, robotics…"
            className="flex-1 px-5 py-4 text-lg rounded-xl border border-gray-200 focus:outline-none focus:border-[#0079C2] focus:ring-2 focus:ring-[#0079C2]/20 transition"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-4 text-lg font-semibold rounded-xl bg-[#0079C2] text-white hover:bg-[#005A91] active:scale-[0.98] transition disabled:opacity-50 shadow-md"
          >
            {loading ? "Поиск…" : "🔍 Найти"}
          </button>
        </div>
      </form>

      {/* Выпадающий список */}
      {open && filtered.length > 0 && (
        <ul className="absolute z-20 left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {filtered.map((s, i) => (
            <li
              key={s.id}
              onMouseEnter={() => setHighlight(i)}
              onClick={() => pick(s.technology)}
              className={`px-5 py-3 cursor-pointer text-sm border-b border-gray-50 last:border-b-0 transition ${
                i === highlight
                  ? "bg-[#E6F2FA] text-[#0079C2]"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              🔎 {s.technology}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}