# ADR-001 — Monorepo e monólito modular

Aceita em 2026-09-23. Backend e frontend evoluem juntos, têm contratos e deploy coordenados;
manter no mesmo GitHub simplifica revisão e rollback. Cada pasta tem Dockerfile, dependências,
README e specs. Separar repositórios quando houver equipes/ciclos realmente independentes.

DDD pragmático: bounded contexts são apps Django, serviços explícitos para transações e
domínio puro para cálculos. Não introduzir microsserviços, event sourcing ou abstrações de
persistência sem necessidade. Usar auth/permissions Django e SimpleJWT; LTS 5.2 mantida com
patches, validar compatibilidade por testes (a matriz da documentação SimpleJWT pode atrasar).
