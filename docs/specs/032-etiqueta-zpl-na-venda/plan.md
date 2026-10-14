# Plano

Trocar o parser de OCR por candidatos pontuados. Ler o recorte histórico e uma área ampliada em todas as
etiquetas; usar uma terceira área quando as leituras forem incompletas ou divergentes. Separar o bloco entre
os marcadores destinatário e remetente, ancorar endereço pelo CEP e validar UF brasileira. Incluir o pedido
em todos os padrões automáticos de nome.

Criar `SaleLabel` como relação um para um com `Sale`. Guardar ZPL, nome do arquivo de origem, pedido e os
campos corrigíveis usados no nome do PDF. Aceitar a etiqueta junto da criação da venda e por `GET/PUT` em
`sales/{id}/label/`; manter o conteúdo fora de `SaleSerializer` e carregar a relação sem N+1.

Reutilizar a biblioteca da ferramenta no formulário e numa janela do histórico. A leitura automática deve
respeitar referência digitada pelo usuário. Download e impressão usam o PDF 4 × 6 do Labelary, sem página
em branco. Cobrir persistência, validação e permissões no backend; validar o parser com amostras sintéticas
sem dados pessoais e conferir os fluxos no navegador.
