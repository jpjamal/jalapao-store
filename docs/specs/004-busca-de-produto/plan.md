# Plano

Um componente só, `frontend/src/components/product-picker.tsx`, usado nos três lugares.
Controlado por `value`/`onChange(id, produto)`, para caber tanto no estado de um item de
venda quanto no de um formulário inteiro. Props `somenteAtivos` e `mostrarQuantidade`
preservam as diferenças que já existiam entre as telas.

O `required` fica no input visível, não num campo oculto: campo oculto não participa da
validação do navegador. Junto com o apagamento do texto no blur sem escolha, isso dá a
barreira sem escrever validação própria.

`name` é opcional e, quando informado, renderiza um input oculto para formulários que leem
`FormData`. O estoque, que usava `form.reset()`, passou a guardar o produto em estado e a
limpá-lo no sucesso — `reset()` não limparia um oculto controlado pelo React.

Acessibilidade pelo padrão combobox: `role="combobox"`, `aria-expanded`, `aria-controls`,
`aria-activedescendant` e `role="listbox"`/`option`. A opção reage a `onMouseDown` com
`preventDefault`, senão o blur fecharia a lista antes do clique registrar.
