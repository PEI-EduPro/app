export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  in_stock: boolean;
}

export interface NewProduct {
  name: string;
  description: string;
  price: number;
  in_stock: boolean;
}
