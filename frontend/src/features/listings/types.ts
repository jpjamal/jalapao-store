/* Tipos do rascunho de anúncio no Mercado Livre (specs 011 e 012), no formato da API. */

export type ValorAtributo = { value_id?: string; value_name: string };
export type Atributos = Record<string, ValorAtributo>;

export type Sugestao = { category_id: string; category_name: string; domain_name: string };
export type Atributo = {
  id: string;
  name: string;
  value_type: string;
  value_max_length: number | null;
  values: { id: string; name: string }[];
  allowed_units: string[];
  default_unit: string | null;
  required: boolean;
  conditional_required: boolean;
};
export type Categoria = {
  id: string;
  name: string;
  path: string[];
  listing_allowed: boolean;
  max_title_length: number | null;
  max_pictures_per_item: number | null;
  minimum_price: number | null;
};
export type Achado = { nivel: string; origem: string; campo: string; mensagem: string; codigo: string };
export type Relatorio = {
  pode_publicar: boolean;
  simulado_no_mercado_livre: boolean;
  causas_de_foto_retiradas: number;
  categoria: { id: string; nome: string; caminho: string[] } | null;
  erros: Achado[];
  avisos: Achado[];
};

export type NoCategoria = {
  id: string;
  name: string;
  path: { id: string; name: string }[];
  listing_allowed: boolean;
  children: { id: string; name: string }[];
};
