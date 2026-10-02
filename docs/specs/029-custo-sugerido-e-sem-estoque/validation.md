# Validação

Em 02/10/2026, com a cópia local (`localhost:8080`) reconstruída: `tsc --noEmit` sem erros e `npm run build` ok.

- Estoque → Ajustar inventário: escolhida a peça 3D "Shenlong" e quantidade 2, o custo veio 20,59 (o custo de
  produção do cadastro, igual ao de produção em 02/10) com a linha "Custo de produção 3D do cadastro: R$ 20,59".
  O movimento não foi registrado.
- Seletor de produto: "Shenlong" e "suporte shenlong" (saldo 0) com "sem estoque" em vermelho.
- Estoque → Posição atual: as 5 peças com saldo 0 com selo "Sem estoque" e fundo avermelhado; "Ze pilintra"
  (5 un.) sem marca. Depois dessa conferência o tom do fundo subiu de 9% para 15%, porque no tema escuro ficava
  discreto demais.
- Não conferido na tela: a lista de Produtos (mesmo componente e mesma classe) e o cartão do celular.
