import { api, type Product, type Page } from "./api";
export async function allProducts() {
  const result: Product[] = [];
  let page = 1;
  while (true) {
    const data = await api<Page<Product>>(`products?page=${page}`);
    result.push(...data.results);
    if (!data.next) return result;
    page++;
  }
}
