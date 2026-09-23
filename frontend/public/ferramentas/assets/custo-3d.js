/* ============================================================
   Custo3D — a conta do custo de impressão 3D, sem tocar em tela.
   Usada pela calculadora e pela lista de produtos, para que as
   duas mostrem sempre o mesmo número.
   ============================================================ */

window.Custo3D = (function(){
  "use strict";

  function num(v){
    const n = typeof v === "number" ? v : parseFloat(String(v == null ? "" : v).replace(",", "."));
    return isNaN(n) || n < 0 ? 0 : n;
  }

  /* entradas = { precoKg, gramas, consumo, horas, minutos, kwh, maoDeObra, custoFixo, margem } */
  function calcular(entradas){
    const e = entradas || {};
    const precoKg = num(e.precoKg);
    const gramas  = num(e.gramas);
    const consumo = num(e.consumo);
    const tempo   = num(e.horas) + num(e.minutos) / 60;
    const kwh     = num(e.kwh);
    const mao     = num(e.maoDeObra);
    const fixo    = num(e.custoFixo);
    const margem  = num(e.margem);

    const filamento  = (precoKg / 1000) * gramas;
    const kwhGastos  = (consumo * tempo) / 1000;
    const energia    = kwhGastos * kwh;
    const custoTotal = filamento + energia + mao + fixo;
    const lucro      = margem > 0 ? custoTotal * (margem / 100) : 0;

    return {
      filamento:  filamento,
      kwhGastos:  kwhGastos,
      energia:    energia,
      maoDeObra:  mao,
      custoFixo:  fixo,
      custoTotal: custoTotal,
      lucro:      lucro,
      precoFinal: custoTotal + lucro,
      tempoHoras: tempo,
      // true quando todos os campos obrigatórios estão preenchidos
      completo: !(precoKg <= 0 || gramas <= 0 || consumo <= 0 || tempo <= 0 || kwh <= 0)
    };
  }

  function brl(v){
    return num(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function horasTexto(horas){
    const h = Math.floor(num(horas));
    const m = Math.round((num(horas) - h) * 60);
    return m === 0 ? h + " h" : h + " h " + m + " min";
  }

  return { calcular: calcular, num: num, brl: brl, horasTexto: horasTexto };
})();
