# Validação

Em 24/09/2026, contra PostgreSQL 17 real, dentro da suíte de 82 testes:

- Produtos novos recebem SKUs únicos e em ordem; dois produtos de mesmo nome não colidem;
  a quantidade em estoque é independente do número do SKU.
- A API ignora SKU enviado na criação e não deixa alterar na edição.
- SKU manual existente é preservado.

A tela de impressão 3D deixou de enviar SKU próprio (`3D-…`) ao salvar produto: quem gera
agora é o backend.

## Limites da evidência
Os SKUs antigos não foram migrados, de propósito: continuam nos formatos anteriores
(`p_…` do sistema legado). Convivem os dois formatos no catálogo.
