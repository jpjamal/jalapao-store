# Validação

## Testes automatizados
163 testes (159 + 4 novos em `apps/catalog/tests/test_armazenamento.py`): cópia com a mesma
chave e idempotente, disco antigo intocado, foto sem arquivo avisada sem parar, pasta de
origem inexistente é erro, backup com todas as fotos e aviso das que faltam.

## Ensaio local com o SILO (28/09/2026)
`silo/publicar.sh` rodado duas vezes contra o Traefik local: credenciais geradas na primeira,
nada muda na segunda.

| Checagem | Resultado |
|---|---|
| Painel `/silo/` pelo domínio | 200, `<base href="/silo/">`; login da API do painel 204, senha errada 401 |
| Painel pelo IP | 404 (só pelo domínio) |
| `http://…/silo/` | 301 para HTTPS |
| Chave da loja em `vinculus-arquivos` | Access Denied |
| Foto criada no disco pela versão anterior | migrada (`1 copiadas`); segunda vez `1 já estavam lá` |
| Foto migrada pelo BFF, com login | 200 `image/png`, mesmos bytes |
| Foto nova enviada pelo BFF | grava no bucket; excluir apaga do bucket |
| Foto inexistente | `FileNotFoundError` → 404 |
| `export_media` | tar.gz com a foto, lida do bucket |
| `/manuais/dummy-13.pdf` e nome com espaço | 200 `application/pdf`, domínio e IP |
| `/manuais/` (listar) | 403 |
| Manual inexistente | 404 |
| `PUT` anônimo em `/manuais/` | 403 |
| `/manuais/../jalapao-media/…` | 404 (o Traefik normaliza o caminho) |
| `mc mirror` com PDF já no bucket e diferente no disco | mantém o do bucket |
| Rotas da spec 019 | todas iguais depois da troca |
