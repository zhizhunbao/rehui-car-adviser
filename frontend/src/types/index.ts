export interface CarListing {
  id: string;
  title: string;
  price: string;
  year: number;
  mileage: string;
  city: string;
  link: string;
  image?: string;
}

export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  success: boolean;
  data?: CarListing[];
  total_count?: number;
  error?: string;
  message?: string;
}

export interface SearchContextType {
  searchResults: CarListing[];
  isLoading: boolean;
  error: string | null;
  searchCars: (query: string) => Promise<void>;
}
