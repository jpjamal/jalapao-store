# 003 — Ferramentas no app e aviso de certificado

## Comportamento
- As três ferramentas (custo de impressão 3D, taxas de marketplace e gerador de etiquetas)
  passam a ser páginas do Next em `/ferramentas/*`, dentro da sessão e do layout do sistema.
  Deixam de ser HTML copiado para `public/` por script na hora do build.
- **Nenhuma fórmula muda.** As contas são portadas linha a linha para `src/lib/ferramentas/`,
  em módulos puros que não tocam em DOM: mesmas entradas, mesma ordem de operações, mesmos
  limiares de OCR, mesmas regras de nome de arquivo. Continuam sendo simulação: nas vendas
  valem as taxas efetivamente cobradas.
- O custo 3D calculado na tela tem de bater com `apps/catalog/domain.py`, que é quem decide
  o custo gravado no catálogo.
- Salvar produto pela ferramenta 3D continua exigindo autenticação e usando a API.
- Endereços antigos (`/impressao-3d.html`, `/ferramentas/impressao-3d.html` e equivalentes)
  redirecionam permanentemente para as páginas novas.
- O painel informa quantos dias faltam para o certificado HTTPS vencer e **alerta** quando
  faltarem dois dias ou menos. Sem certificado legível, o painel não mostra nada e nada
  quebra.

## Motivação do aviso
O certificado é emitido para IP com o perfil *shortlived*: dura cerca de seis dias e o
certbot tenta renovar a cada doze horas. Uma renovação que falhe em silêncio tira o site do
ar em menos de uma semana, e não havia nenhum sinal disso em lugar nenhum. Dois dias é o
limiar porque a renovação normal acontece bem antes: chegar lá já significa que algo falhou.

## Limites e não objetivos
- Login passa a ser exigido também para as ferramentas, porque elas agora são páginas do
  app. Quem precisar da versão sem login tem `site/` e `originais/` no repositório.
- A leitura da validade usa o PEM montado em volume somente leitura, não uma conexão TLS:
  interessa o certificado que o proxy servirá em seguida, mesmo sem ninguém acessar o site.
- O aviso é visual, no painel. Não há e-mail, push nem monitoramento externo — isso segue
  como tarefa operacional em aberto.
- Não há mudança de layout das ferramentas além da adaptação ao sistema; não foi objetivo
  redesenhar nada.
- O Tesseract e o Labelary continuam sendo serviços externos; sem internet, o OCR e a
  renderização não funcionam, como antes.

## Aceitação
Uma peça de 45 g, filamento a R$ 115/kg, 200 W, 5 h 18 min, kWh a R$ 1,56 e margem 100%
dá o mesmo custo e o mesmo preço da tela antiga e do backend. Um preço de R$ 79,99 na
Shopee cai na faixa de 20% + R$ 4,50. Um ZPL da Shopee com duas etiquetas gera dois cartões
com nome lido e dois PDFs nomeados. `/calculadora.html` leva a `/ferramentas/calculadora`.
Um certificado que vence em 30 dias não alerta; o mesmo certificado, visto a 29 dias de
distância, alerta. Certificado ausente devolve `null` e o painel carrega normalmente.
