import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-[#E6F2FA]">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}

function Header() {
  const { pathname } = useLocation();

  const { data: stats } = useQuery({
    queryKey: ["header-stats"],
    queryFn: async () => {
      const { data } = await axios.get("/api/stats");
      return data;
    },
    staleTime: 60_000,
  });

  const link = (to: string, label: string) => (
    <Link
      to={to}
      className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
        pathname === to
          ? "bg-white text-[#0079C2]"
          : "text-white/90 hover:bg-white/15"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="bg-[#0079C2] shadow-md">
      <div className="max-w-6xl mx-auto px-8 py-4 flex items-center gap-6">
        <Link to="/" className="flex items-center gap-3">
          <span className="text-2xl">🛰️</span>
          <div className="leading-tight">
            <div className="text-white font-bold text-lg">Weak Signals</div>
            <div className="text-white/70 text-xs">
              Выявление зарождающихся трендов
            </div>
          </div>
        </Link>

        {/* Счётчики */}
        {stats && (
          <div className="hidden md:flex items-center gap-4 text-white/90 text-sm ml-4 pl-4 border-l border-white/20">
            <span className="flex items-center gap-1.5">
              📚
              <b className="font-semibold">
                {stats.total_documents?.toLocaleString("ru-RU") ?? 0}
              </b>
              <span className="text-white/70 hidden lg:inline">источников</span>
            </span>
            <span className="flex items-center gap-1.5">
              ⭐
              <b className="font-semibold">{stats.signals_above_75 ?? 0}</b>
              <span className="text-white/70 hidden lg:inline">сигналов</span>
            </span>
            <span className="flex items-center gap-1.5">
              🎯
              <b className="font-semibold">
                {stats.scored_documents ?? 0}
              </b>
              <span className="text-white/70 hidden lg:inline">
                оценено LLM
              </span>
            </span>
          </div>
        )}

        <nav className="flex gap-1 ml-auto">
          {link("/", "Поиск")}
          {link("/stats", "Статистика")}
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="bg-[#005A91] text-white mt-12">
      <div className="max-w-6xl mx-auto px-8 py-8 flex flex-col md:flex-row items-center gap-6">
        <div
          className="text-6xl select-none"
          title="Наш маскот — сова-аналитик"
        >
          🦉
        </div>

        <div className="flex-1 text-center md:text-left">
          <div className="font-semibold text-lg mb-1">
            Сова находит слабые сигналы, пока все спят
          </div>
          <div className="text-white/70 text-sm">
            Сервис автоматизированного анализа научно-технологических трендов
          </div>
        </div>

        <a
          href="https://www.gazprombank.ru/"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-white text-[#0079C2] font-semibold hover:bg-[#E6F2FA] transition"
        >
          Перейти на Газпромбанк.ру →
        </a>
      </div>

      <div className="border-t border-white/10">
        <div className="max-w-6xl mx-auto px-8 py-3 text-xs text-white/60 flex flex-wrap gap-3 justify-between">
          <span>© 2026 Газпромбанк.Тех — Хакатон</span>
          <span>Pantone 300 CV · #0079C2</span>
        </div>
      </div>
    </footer>
  );
}