/* Quantidade em estoque numa linha de lista. Com saldo zero (ou negativo), a linha recebe a
   classe `sem-estoque` (fundo avermelhado, em globals.css) e a quantidade ganha o selo. */

export const semEstoque = (quantity: number) => quantity <= 0;

export const linhaDeEstoque = (quantity: number) => (semEstoque(quantity) ? "sem-estoque" : undefined);

export function StockQuantity({ quantity }: { quantity: number }) {
  return (
    <span>
      {quantity}
      {semEstoque(quantity) && <span className="selo-sem-estoque">Sem estoque</span>}
    </span>
  );
}
