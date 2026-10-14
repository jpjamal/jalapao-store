# Plano

Criar um componente compartilhado `ListAction`, baseado no botão atual e nos ícones Lucide já instalados.
Ele centraliza tamanho, `aria-label`, `title` e tooltip de mouse/teclado, além de aceitar links. Aplicá-lo
somente às ações repetidas nas linhas de Produtos, Categorias, Entradas, Vendas, Insumos, compras de insumos,
categorias do Caixa, categorias de insumos, Anúncios e Integrações.

No editor da etiqueta da venda, substituir o seletor e a área de texto por uma zona de arquivo acessível.
O mesmo leitor de arquivo alimenta clique e `drop`, preservando limite, validação, OCR, PDF e persistência.
Reordenar apenas os blocos JSX do formulário de venda; manter os nomes dos campos e o corpo enviado à API.

Validar por compilação, busca estrutural das ações e regressão completa. Não criar migração nem alterar o
contrato OpenAPI, pois a mudança é exclusivamente de apresentação.
