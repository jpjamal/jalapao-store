/* ============================================================
   Produtos — guarda os produtos da loja no navegador.

   Hoje só os itens impressos em 3D, com nome e os dados de custo.
   O formato é versionado e cada produto tem espaço para crescer
   (foto, categoria, link do anúncio, preço na Shopee...) sem
   quebrar o que já está salvo: campo novo entra com valor padrão
   e a função migrar() cuida dos registros antigos.

   Onde fica: localStorage do navegador, na própria máquina.
   Não sai daqui — por isso existe o backup em .json.
   ============================================================ */

window.Produtos = (function(){
  "use strict";

  const CHAVE   = "jalapao_produtos";
  const VERSAO  = 1;              // versão do formato do arquivo
  const TIPO_3D = "impressao3d";  // tipo do produto; outros tipos podem entrar depois

  /* ---------- acesso ao armazenamento ---------- */

  function disponivel(){
    try {
      const teste = "__jalapao_teste__";
      localStorage.setItem(teste, "1");
      localStorage.removeItem(teste);
      return true;
    } catch(e){ return false; }
  }

  function ler(){
    try {
      const cru = localStorage.getItem(CHAVE);
      if (!cru) return { versao: VERSAO, itens: [] };
      const dados = JSON.parse(cru);
      return migrar(dados);
    } catch(e){
      return { versao: VERSAO, itens: [] };
    }
  }

  function gravar(dados){
    localStorage.setItem(CHAVE, JSON.stringify(dados));
  }

  /* Formato antigo -> formato atual. Enquanto só existe a versão 1,
     o trabalho é garantir os campos mínimos de cada item. */
  function migrar(dados){
    if (!dados || typeof dados !== "object") return { versao: VERSAO, itens: [] };
    if (!Array.isArray(dados.itens)) dados.itens = [];
    dados.versao = VERSAO;
    dados.itens = dados.itens.filter(Boolean).map(function(it){
      it.tipo      = it.tipo || TIPO_3D;
      it.nome      = String(it.nome || "").trim();
      it.entradas  = it.entradas || {};
      it.criadoEm  = it.criadoEm || new Date().toISOString();
      it.atualizadoEm = it.atualizadoEm || it.criadoEm;
      return it;
    });
    return dados;
  }

  function novoId(){
    return "p_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  /* ---------- operações ---------- */

  function listar(tipo){
    const itens = ler().itens;
    return tipo ? itens.filter(function(i){ return i.tipo === tipo; }) : itens;
  }

  function obter(id){
    return ler().itens.find(function(i){ return i.id === id; }) || null;
  }

  /* Salva um produto novo ou atualiza o existente (quando vem com id).
     Devolve o produto salvo, já com id e datas. */
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
    return p;
  }

  function remover(id){
    const dados = ler();
    const antes = dados.itens.length;
    dados.itens = dados.itens.filter(function(i){ return i.id !== id; });
    gravar(dados);
    return dados.itens.length < antes;
  }

  function duplicar(id){
    const p = obter(id);
    if (!p) return null;
    return salvar({ tipo: p.tipo, nome: p.nome + " (cópia)", entradas: p.entradas });
  }

  /* ---------- backup ---------- */

  function exportar(){
    return JSON.stringify(ler(), null, 2);
  }

  /* Junta o backup ao que já existe: id repetido é substituído. */
  function importar(texto){
    let entrada;
    try { entrada = JSON.parse(texto); }
    catch(e){ throw new Error("arquivo não é um backup válido"); }
    entrada = migrar(entrada);

    const dados = ler();
    let novos = 0, atualizados = 0;
    entrada.itens.forEach(function(it){
      if (!it.id) it.id = novoId();
      const i = dados.itens.findIndex(function(x){ return x.id === it.id; });
      if (i >= 0) { dados.itens[i] = it; atualizados++; }
      else        { dados.itens.push(it); novos++; }
    });
    gravar(dados);
    return { novos: novos, atualizados: atualizados };
  }

  /* ---------- semente ----------
     A lista mora no navegador, então não viaja junto no deploy: quem abre o
     site numa máquina nova veria a lista vazia. O arquivo produtos-seed.js
     traz as peças já cadastradas, e elas são plantadas uma vez por versão:
       - item cujo id já existe é ignorado — o que é seu nunca é sobrescrito;
       - depois de plantada, a versão fica marcada, então peça que você apagar
         de propósito não ressuscita no próximo deploy. */
  const MARCA_SEMENTE = CHAVE + "_semente";

  function semear(){
    const s = window.PRODUTOS_SEMENTE;
    if (!s || !Array.isArray(s.itens) || !disponivel()) return null;
    try {
      if (localStorage.getItem(MARCA_SEMENTE) === String(s.versao)) return null;

      const dados = ler();
      const existentes = dados.itens.map(function(i){ return i.id; });
      const novos = s.itens.filter(function(i){ return existentes.indexOf(i.id) < 0; });

      novos.forEach(function(i){
        dados.itens.push(migrar({ versao: VERSAO, itens: [i] }).itens[0]);
      });
      if (novos.length) gravar(dados);

      localStorage.setItem(MARCA_SEMENTE, String(s.versao));
      return { plantados: novos.length, versao: s.versao };
    } catch(e){ return null; }
  }

  return {
    TIPO_3D: TIPO_3D,
    disponivel: disponivel,
    listar: listar,
    obter: obter,
    salvar: salvar,
    remover: remover,
    duplicar: duplicar,
    exportar: exportar,
    importar: importar,
    semear: semear
  };
})();

// planta a semente assim que o módulo carrega, antes de qualquer tela desenhar
if (window.Produtos) window.Produtos.semear();
