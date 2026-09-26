import { api } from "@/shared/api/client";
import { type Product } from "@/features/catalog/types";
import { type Page } from "@/shared/api/types";
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
