/* ============================================================
   Produtos — os produtos da loja.

   Antes a lista vivia só no navegador, e por isso não passava de um aparelho
   para o outro. Agora ela mora no servidor (a API em /api/produtos) e o
   navegador guarda uma cópia. Assim:

     - abre de onde for e a lista está lá;
     - sem internet ou com o servidor fora, continua funcionando com a cópia
       local e envia quando voltar;
     - ler é aberto; gravar pede a senha, guardada no aparelho depois da
       primeira vez.

   O formato é versionado e cada produto tem espaço para crescer (foto,
   categoria, link do anúncio) sem quebrar o que já está salvo.
   ============================================================ */

window.Produtos = (function(){
  "use strict";

  const CHAVE     = "jalapao_produtos";        // cópia local
  const CHAVE_SEN = "jalapao_produtos_senha";  // senha de gravação, por aparelho
  const VERSAO    = 1;
  const TIPO_3D   = "impressao3d";
  const API       = "/api/produtos";

  let modo      = "local";    // "servidor" quando a API respondeu
  let pendente  = false;      // há mudança local ainda não enviada
  let ouvintes  = [];

  /* ---------- armazenamento local (cópia) ---------- */

  function disponivel(){
    try {
      localStorage.setItem("__t__", "1"); localStorage.removeItem("__t__");
      return true;
    } catch(e){ return false; }
  }

  function ler(){
    try {
      const cru = localStorage.getItem(CHAVE);
      return cru ? migrar(JSON.parse(cru)) : { versao: VERSAO, itens: [] };
    } catch(e){ return { versao: VERSAO, itens: [] }; }
  }

  function gravar(dados){
    try { localStorage.setItem(CHAVE, JSON.stringify(dados)); } catch(e){ /* navegador sem espaço */ }
  }

  function migrar(dados){
    if (!dados || typeof dados !== "object") return { versao: VERSAO, itens: [] };
    if (!Array.isArray(dados.itens)) dados.itens = [];
    dados.versao = VERSAO;
    dados.itens = dados.itens.filter(Boolean).map(function(it){
      it.tipo = it.tipo || TIPO_3D;
      it.nome = String(it.nome || "").trim();
      it.entradas = it.entradas || {};
      it.criadoEm = it.criadoEm || new Date().toISOString();
      it.atualizadoEm = it.atualizadoEm || it.criadoEm;
      return it;
    });
    return dados;
  }

  function novoId(){
    return "p_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  function avisar(){ ouvintes.forEach(function(f){ try { f(estado()); } catch(e){} }); }

  /* ---------- servidor ---------- */

  function senha(){ try { return localStorage.getItem(CHAVE_SEN) || ""; } catch(e){ return ""; } }

  /* Puxa a lista do servidor. O servidor manda: a cópia local é substituída. */
  async function sincronizar(){
    try {
      const r = await fetch(API, { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const dados = migrar(await r.json());
      gravar(dados);
      modo = "servidor";
      pendente = false;
      avisar();
      return { ok: true, itens: dados.itens.length };
    } catch(e){
      modo = "local";
      avisar();
      return { ok: false, motivo: e.message };
    }
  }

  /* Manda a lista inteira para o servidor. Sem senha, fica pendente. */
  async function enviar(){
    if (!senha()) { pendente = true; avisar(); return { ok: false, motivo: "sem senha" }; }
    try {
      const r = await fetch(API, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "X-Senha": senha() },
        body: JSON.stringify(ler())
      });
      if (!r.ok) throw new Error(r.status === 401 ? "senha incorreta" : "HTTP " + r.status);
      modo = "servidor";
      pendente = false;
      avisar();
      return { ok: true };
    } catch(e){
      pendente = true;
      avisar();
      return { ok: false, motivo: e.message };
    }
  }

  /* Guarda a senha no aparelho e confirma mandando a lista atual. */
  async function entrar(valor){
    try { localStorage.setItem(CHAVE_SEN, String(valor || "").trim()); } catch(e){}
    const r = await enviar();
    if (!r.ok && r.motivo === "senha incorreta") {
      try { localStorage.removeItem(CHAVE_SEN); } catch(e){}
    }
    return r;
  }

  function sair(){
    try { localStorage.removeItem(CHAVE_SEN); } catch(e){}
    avisar();
  }

  function estado(){
    return {
      modo: modo,                       // "servidor" ou "local"
      autenticado: !!senha(),
      pendente: pendente,
      total: ler().itens.length
    };
  }

  /* ---------- operações ---------- */

  function listar(tipo){
    const itens = ler().itens;
    return tipo ? itens.filter(function(i){ return i.tipo === tipo; }) : itens;
  }

  function obter(id){
    return ler().itens.find(function(i){ return i.id === id; }) || null;
  }

  function salvar(produto){
    const dados = ler();
    const agora = new Date().toISOString();
    const p = {
      id:       produto.id || novoId(),
      tipo:     produto.tipo || TIPO_3D,
      nome:     String(produto.nome || "").trim(),
      entradas: produto.entradas || {},
      criadoEm: produto.criadoEm || agora,
      atualizadoEm: agora
    };
    const i = dados.itens.findIndex(function(x){ return x.id === p.id; });
    if (i >= 0) { p.criadoEm = dados.itens[i].criadoEm; dados.itens[i] = p; }
    else        { dados.itens.push(p); }
    gravar(dados);
    enviar();
    return p;
  }

  function remover(id){
    const dados = ler();
    const antes = dados.itens.length;
    dados.itens = dados.itens.filter(function(i){ return i.id !== id; });
    gravar(dados);
    if (dados.itens.length < antes) { enviar(); return true; }
    return false;
  }

  function duplicar(id){
    const p = obter(id);
    return p ? salvar({ tipo: p.tipo, nome: p.nome + " (cópia)", entradas: p.entradas }) : null;
  }

  /* ---------- backup ---------- */

  function exportar(){ return JSON.stringify(ler(), null, 2); }

  function importar(texto){
    let entrada;
    try { entrada = migrar(JSON.parse(texto)); }
    catch(e){ throw new Error("arquivo não é um backup válido"); }

    const dados = ler();
    let novos = 0, atualizados = 0;
    entrada.itens.forEach(function(it){
      if (!it.id) it.id = novoId();
      const i = dados.itens.findIndex(function(x){ return x.id === it.id; });
      if (i >= 0) { dados.itens[i] = it; atualizados++; }
      else        { dados.itens.push(it); novos++; }
    });
    gravar(dados);
    enviar();
    return { novos: novos, atualizados: atualizados };
  }

  /* ---------- semente ----------
     Só vale para quem abre o arquivo solto, sem servidor: garante que a lista
     não apareça vazia. Quando a API responde, quem manda é o servidor. */
  const MARCA_SEMENTE = CHAVE + "_semente";

  function semear(){
    const s = window.PRODUTOS_SEMENTE;
    if (!s || !Array.isArray(s.itens) || !disponivel()) return null;
    try {
      if (localStorage.getItem(MARCA_SEMENTE) === String(s.versao)) return null;
      const dados = ler();
      const ids = dados.itens.map(function(i){ return i.id; });
      const novos = s.itens.filter(function(i){ return ids.indexOf(i.id) < 0; });
      novos.forEach(function(i){ dados.itens.push(migrar({ itens: [i] }).itens[0]); });
      if (novos.length) gravar(dados);
      localStorage.setItem(MARCA_SEMENTE, String(s.versao));
      return { plantados: novos.length, versao: s.versao };
    } catch(e){ return null; }
  }

  function aoMudar(fn){ if (typeof fn === "function") ouvintes.push(fn); }

  const api = {
    TIPO_3D: TIPO_3D,
    disponivel: disponivel,
    listar: listar, obter: obter, salvar: salvar, remover: remover, duplicar: duplicar,
    exportar: exportar, importar: importar, semear: semear,
    sincronizar: sincronizar, enviar: enviar, entrar: entrar, sair: sair,
    estado: estado, aoMudar: aoMudar
  };

  // semeia a cópia local e, em seguida, tenta o servidor — que tem a palavra final
  semear();
  sincronizar();

  return api;
})();
