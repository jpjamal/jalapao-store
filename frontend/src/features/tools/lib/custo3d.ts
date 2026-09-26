/* Custo de impressão 3D — a conta, sem tocar em tela.
   Porte literal de site/assets/custo-3d.js: mesmas entradas, mesma ordem de
   operações, mesmos arredondamentos (nenhum). O backend repete essa conta em
   apps/catalog/domain.py; as duas precisam continuar dando o mesmo número. */

export type Entradas3D = {
  precoKg: string | number;
  gramas: string | number;
  consumo: string | number;
  horas: string | number;
  minutos: string | number;
  kwh: string | number;
  maoDeObra: string | number;
  custoFixo: string | number;
  margem: string | number;
};

export type Resultado3D = {
  filamento: number;
  kwhGastos: number;
  energia: number;
  maoDeObra: number;
  custoFixo: number;
  custoTotal: number;
  lucro: number;
  precoFinal: number;
  tempoHoras: number;
  completo: boolean;
};

export function num(v: unknown): number {
  const n =
    typeof v === "number"
      ? v
      : parseFloat(String(v == null ? "" : v).replace(",", "."));
  return isNaN(n) || n < 0 ? 0 : n;
}

export function calcular(entradas: Partial<Entradas3D>): Resultado3D {
  const e = entradas || {};
  const precoKg = num(e.precoKg);
  const gramas = num(e.gramas);
  const consumo = num(e.consumo);
  const tempo = num(e.horas) + num(e.minutos) / 60;
  const kwh = num(e.kwh);
  const mao = num(e.maoDeObra);
  const fixo = num(e.custoFixo);
  const margem = num(e.margem);

  const filamento = (precoKg / 1000) * gramas;
  const kwhGastos = (consumo * tempo) / 1000;
  const energia = kwhGastos * kwh;
  const custoTotal = filamento + energia + mao + fixo;
  const lucro = margem > 0 ? custoTotal * (margem / 100) : 0;

  return {
    filamento,
    kwhGastos,
    energia,
    maoDeObra: mao,
    custoFixo: fixo,
    custoTotal,
    lucro,
    precoFinal: custoTotal + lucro,
    tempoHoras: tempo,
    // true quando todos os campos obrigatórios estão preenchidos
    completo: !(
      precoKg <= 0 ||
      gramas <= 0 ||
      consumo <= 0 ||
      tempo <= 0 ||
      kwh <= 0
    ),
  };
}

export function brl(v: unknown): string {
  return num(v).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function horasTexto(horas: unknown): string {
  const h = Math.floor(num(horas));
  const m = Math.round((num(horas) - h) * 60);
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}
