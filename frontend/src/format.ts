export const brl = (v: number | null | undefined) =>
  v == null ? "n/d" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export const monthLabel = (ym: string) => {
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("pt-BR", { month: "short", year: "2-digit" });
};

export const dateBr = (iso: string) => iso.split("-").reverse().join("/");
