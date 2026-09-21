/* ============================================================
   Semente de produtos — vai junto no deploy.

   A lista de produtos vive no localStorage de cada navegador, então ela não
   viaja sozinha: quem abre o site pela primeira vez veria a lista vazia.
   Este arquivo carrega as peças já cadastradas.

   Regras (implementadas em produtos.js):
   - só entra o que ainda não existe, comparando pelo id;
   - roda uma vez por versão, então peça que você apagar de propósito
     não volta no próximo deploy;
   - o que você cadastrar depois nunca é sobrescrito.

   Para atualizar: na página Produtos, clique em "Baixar backup", cole os
   itens aqui e troque a data em VERSAO.
   ============================================================ */

window.PRODUTOS_SEMENTE = {
  versao: "2026-09-21",
  itens: [
    {
      id: "p_mu1sdfmu_wy865",
      tipo: "impressao3d",
      nome: "Ze pilintra 15cm",
      entradas: { precoKg: "115", gramas: "80", consumo: "200", horas: "4", minutos: "25",
                  kwh: "1.57", maoDeObra: "", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-14T22:00:02.406Z",
      atualizadoEm: "2026-09-14T22:00:02.406Z"
    },
    {
      id: "p_mu33g2qt_gy1hi",
      tipo: "impressao3d",
      nome: "DUMMY ARANHA",
      entradas: { precoKg: "115", gramas: "50", consumo: "200", horas: "4", minutos: "50",
                  kwh: "1.67", maoDeObra: "", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-15T19:57:47.621Z",
      atualizadoEm: "2026-09-15T19:57:47.621Z"
    },
    {
      id: "p_mu4emg2p_x12r5",
      tipo: "impressao3d",
      nome: "Shenlong",
      entradas: { precoKg: "115", gramas: "150", consumo: "200", horas: "10", minutos: "",
                  kwh: "1.67", maoDeObra: "", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-16T17:58:26.785Z",
      atualizadoEm: "2026-09-16T17:58:26.785Z"
    },
    {
      id: "p_mu4ghf5x_11q32",
      tipo: "impressao3d",
      nome: "suporte shenlong",
      entradas: { precoKg: "115", gramas: "110", consumo: "200", horas: "4", minutos: "",
                  kwh: "1.67", maoDeObra: "", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-16T18:50:31.557Z",
      atualizadoEm: "2026-09-16T18:50:31.557Z"
    },
    {
      id: "p_mu5sb0mw_cev7j",
      tipo: "impressao3d",
      nome: "Painel Cego UCG ultra",
      entradas: { precoKg: "115", gramas: "137", consumo: "200", horas: "7", minutos: "",
                  kwh: "1.67", maoDeObra: "", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-17T17:09:14.360Z",
      atualizadoEm: "2026-09-17T17:09:14.360Z"
    },
    {
      id: "p_mu5w9zrx_zx7pl",
      tipo: "impressao3d",
      nome: "Luminaria Air FOrm",
      entradas: { precoKg: "115", gramas: "150", consumo: "198", horas: "14", minutos: "",
                  kwh: "1.67", maoDeObra: "13", custoFixo: "", margem: "100" },
      criadoEm: "2026-09-17T19:00:25.053Z",
      atualizadoEm: "2026-09-17T19:02:36.366Z"
    }
  ]
};
