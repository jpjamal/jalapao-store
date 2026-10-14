# Validação

## Automatizada (14/10/2026)

- `npm run typecheck`: aprovado.
- `npm run build`: aprovado; 20 rotas geradas.
- Suíte completa do backend (`manage.py test apps`, SQLite no WSL): 330 testes, OK, 6 pulados.

## Conferência da interface (cópia local, usuário e dados de teste descartáveis)

- Ordem do formulário de venda: Produto, Quantidade, Preço unitário, Remover/Adicionar item, Canal,
  Referência, Insumos, descontos e custos, Etiqueta ZPL, Confirmar venda.
- Soltar um `.txt` na zona: carrega o arquivo, mostra "Etiqueta carregada" com o nome, inicia a leitura
  (OCR) e não existe nenhuma caixa de texto com o código ZPL.
- Soltar um arquivo fora da zona não faz o navegador abri-lo (a página bloqueia o comportamento padrão).
- Lista de Vendas: cinco ícones por linha (editar, receber, cancelar, etiqueta, excluir) sem texto, com a
  explicação ao passar o mouse; botões de 44 px no celular e 40 px no computador; sem barra de rolagem
  nova na tabela. Lista de Produtos: ícones de editar e de fotos/anúncios.
- Etiqueta real da Shopee (`thermal_zpl_shipping_label.txt`) solta na zona: só o número do pedido
  (14 caracteres) é lido e vai para a Referência; sem campos de destinatário, cidade, UF ou "pedido identificado".

## Publicação

Ainda não há commit ou deploy desta spec.
