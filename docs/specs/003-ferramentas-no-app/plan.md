# Plano

Contas puras em `frontend/src/lib/ferramentas/`: `custo3d.ts` (porte de
`site/assets/custo-3d.js`), `marketplace.ts` (faixas da Shopee, médias do Mercado Livre e
a antecipação de 1º/10/2026 decidida pelo dono) e `etiquetas.ts` (fila de 360 ms do
Labelary, retry no 429, recortes e limiares do OCR, tabela de UF e padrões de nome). Nenhum
desses módulos toca em DOM, então podem ser lidos e conferidos sem subir tela.

Três páginas client em `src/app/(store)/ferramentas/`, uma por ferramenta, com os
componentes já existentes (Card, Input, Button, ErrorMessage) e os tokens do tema. O índice
de ferramentas passa a usar `Link` interno. `next.config.ts` redireciona os endereços
antigos. `frontend/public/ferramentas/` e `scripts/preserve_tools.py` saem do repositório:
viraram duplicata do que agora é código.

Certificado: `apps/common/certificado.py` lê a validade do PEM e devolve
`{expires_at, days_left, alert}`, ou `None` quando não há o que ler. O volume `certificates`
é montado no backend como `/certs:ro`; o limiar vem de `TLS_ALERT_DAYS` e `TLS_CERT_PATH`
força um caminho único.

O certbot cria `live/` e `archive/` com permissão 0700 de root e o backend roda como usuário
sem privilégio — ler direto de lá dá "Permission denied". Em vez de afrouxar a permissão do
certbot, que ele reescreve a cada renovação, o próprio laço do certbot deixa uma cópia
legível em `publico/cert.pem` depois de cada tentativa. O certificado é informação pública:
é o mesmo que o proxy entrega a qualquer visitante. O caminho do certbot continua como
segunda tentativa. O dashboard passa a devolver o campo `certificate`, e o painel mostra uma
linha discreta no rodapé ou um alerta vermelho no topo, conforme o caso.

Decisão consciente: a validade é lida com `ssl._ssl._test_decode_cert`, API privada do
CPython, para não trazer a dependência `cryptography` só por uma data. Fica isolada em um
módulo e dentro de try/except — se sumir numa versão futura, o painel deixa de mostrar o
aviso e nada mais acontece.
