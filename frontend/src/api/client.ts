import axios from "axios";
import type { Stats } from "../types";

const api = axios.create({
  baseURL: "/",
  timeout: 120_000,
});

export const getStats = async (): Promise<Stats> => {
  const { data } = await api.get<Stats>("/api/stats");
  return data;
};

export const searchSignals = async (query: string, limit = 15) => {
  const { data: created } = await api.post("/api/search", { query, limit });
  if (created.search_id) {
    const { data } = await api.get(`/api/search/${created.search_id}`);
    return data;
  }
  return created;
};