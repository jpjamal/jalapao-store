# Validação — spec 036

- Typecheck do frontend sem erros.
- Conferido no navegador (Chromium, página de teste descartada): `123456` → `1.234,56`; backspace → `123,45`;
  inteiro `1234567` → `1.234.567`; peso limita a 3 casas; `-12` aceito no ajuste; máximo 59 recusa `75`;
  mínimo 1 recusa `0` com mensagem; formulário envia `123.45`, `3`, `0.5`; `form.reset()` restaura.
- Pendente: conferir em produção e no celular.
