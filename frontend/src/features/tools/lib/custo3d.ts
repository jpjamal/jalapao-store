/* Custo de impressão 3D — a conta, sem tocar em tela.
   Porte literal de site/assets/custo-3d.js: mesmas entradas, mesma ordem de
   operações, mesmos arredondamentos (nenhum). O backend repete essa conta em
   apps/catalog/domain.py; as duas precisam continuar dando o mesmo número. */

/* Linha de filamento de uma peça multicolor (spec 024): gramas usadas e o rolo (preço e peso).
   O custo da linha é gramas × preço do rolo ÷ peso do rolo, sem arredondar o preço por grama. */
export type LinhaFilamento = {
  gramas: string | number;
  precoRolo: string | number;
  pesoRolo: string | number;
};

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
  /* com linhas, o filamento é a soma delas e precoKg/gramas são ignorados */
  filamentos?: LinhaFilamento[];
};

export type Resultado3D = {
  filamento: number;
  /* gramas totais: as digitadas, ou a soma das linhas */
  gramasTotal: number;
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
  const linhasFil = (e.filamentos || []).filter((l) => num(l.pesoRolo) > 0);
  const comLinhas = linhasFil.length > 0;
  const gramas = comLinhas
    ? linhasFil.reduce((t, l) => t + num(l.gramas), 0)
    : num(e.gramas);
  const consumo = num(e.consumo);
  const tempo = num(e.horas) + num(e.minutos) / 60;
  const kwh = num(e.kwh);
  const mao = num(e.maoDeObra);
  const fixo = num(e.custoFixo);
  const margem = num(e.margem);

  const filamento = comLinhas
    ? linhasFil.reduce(
        (t, l) => t + (num(l.gramas) * num(l.precoRolo)) / num(l.pesoRolo),
        0,
      )
    : (precoKg / 1000) * gramas;
  const kwhGastos = (consumo * tempo) / 1000;
  const energia = kwhGastos * kwh;
  const custoTotal = filamento + energia + mao + fixo;
  const lucro = margem > 0 ? custoTotal * (margem / 100) : 0;

  return {
    filamento,
    gramasTotal: gramas,
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
      (!comLinhas && precoKg <= 0) ||
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
