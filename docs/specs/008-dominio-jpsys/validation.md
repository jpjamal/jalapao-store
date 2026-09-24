# Validação

Em 24/09/2026, em produção.

- `jpsys.duckdns.org` resolve para `217.216.82.25`, de fora e de dentro da VPS; o domínio
  anterior não resolve mais.
- Os dois deploys passaram: loja em `23fd9dc`, traefikproxy em `bf0fe14`.
- Certificado servido para `jpsys.duckdns.org`: emitido pelo Traefik (Let's Encrypt, YR2),
  válido até 23/12/2026.
- De fora, sem `-k`: login 200 e manual em PDF 200 pelo domínio novo; login 200 pelo IP.

## Limites da evidência
A conta do Mercado Livre já conectada continua renovando o token sem depender do endereço
de retorno; uma autorização nova depende do painel do Mercado Livre apontar para o domínio
novo, e isso não foi conferido. Não houve autorização nova depois da troca.
