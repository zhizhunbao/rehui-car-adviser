// 汽车相关类型定义

// 汽车品牌类型
export interface CarBrand {
  id: string;
  name: string;
  logo?: string;
  country?: string;
  foundedYear?: number;
  description?: string;
}

// 汽车型号类型
export interface CarModel {
  id: string;
  brandId: string;
  name: string;
  year: number;
  bodyType: CarBodyType;
  fuelType: FuelType;
  transmission: TransmissionType;
  engineSize?: number;
  power?: number;
  torque?: number;
  acceleration?: number;
  topSpeed?: number;
  fuelConsumption?: {
    city: number;
    highway: number;
    combined: number;
  };
  dimensions?: {
    length: number;
    width: number;
    height: number;
    wheelbase: number;
  };
  weight?: number;
  seatingCapacity?: number;
  cargoCapacity?: number;
  safetyRating?: number;
  priceRange?: {
    min: number;
    max: number;
  };
  images?: string[];
  features?: string[];
}

// 车身类型
export type CarBodyType = 
  | 'sedan' | 'hatchback' | 'coupe' | 'convertible' 
  | 'suv' | 'crossover' | 'pickup' | 'van' 
  | 'wagon' | 'minivan' | 'roadster';

// 燃料类型
export type FuelType = 
  | 'gasoline' | 'diesel' | 'hybrid' | 'electric' 
  | 'plug-in-hybrid' | 'natural-gas' | 'ethanol';

// 变速箱类型
export type TransmissionType = 
  | 'manual' | 'automatic' | 'cvt' | 'semi-automatic';

// 汽车详情类型
export interface CarDetails extends CarModel {
  brand: CarBrand;
  variants: CarVariant[];
  reviews: CarReview[];
  specifications: CarSpecification[];
  images: CarImage[];
  videos?: CarVideo[];
  dealerInfo?: DealerInfo;
  financing?: FinancingInfo;
  insurance?: InsuranceInfo;
}

// 汽车变体类型
export interface CarVariant {
  id: string;
  name: string;
  trim: string;
  price: number;
  currency: string;
  year: number;
  features: string[];
  colors: CarColor[];
  availability: 'available' | 'out-of-stock' | 'discontinued';
}

// 汽车颜色类型
export interface CarColor {
  name: string;
  code: string;
  hex: string;
  type: 'solid' | 'metallic' | 'pearl' | 'matte';
  price?: number;
  imageUrl?: string;
}

// 汽车规格类型
export interface CarSpecification {
  category: string;
  items: Array<{
    name: string;
    value: string;
    unit?: string;
  }>;
}

// 汽车图片类型
export interface CarImage {
  id: string;
  url: string;
  thumbnail?: string;
  type: 'exterior' | 'interior' | 'engine' | 'detail';
  angle?: string;
  caption?: string;
  isPrimary?: boolean;
}

// 汽车视频类型
export interface CarVideo {
  id: string;
  url: string;
  thumbnail: string;
  duration: number;
  type: 'review' | 'test-drive' | 'feature' | 'commercial';
  title: string;
  description?: string;
}

// 汽车评价类型
export interface CarReview {
  id: string;
  author: string;
  rating: number;
  title: string;
  content: string;
  pros: string[];
  cons: string[];
  verified: boolean;
  helpful: number;
  notHelpful: number;
  createdAt: number;
  updatedAt: number;
}

// 经销商信息类型
export interface DealerInfo {
  id: string;
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  location: {
    latitude: number;
    longitude: number;
  };
  contact: {
    phone: string;
    email: string;
    website?: string;
  };
  hours: {
    [key: string]: {
      open: string;
      close: string;
      closed?: boolean;
    };
  };
  rating: number;
  reviewCount: number;
  services: string[];
  certifications: string[];
}

// 金融信息类型
export interface FinancingInfo {
  monthlyPayment: number;
  downPayment: number;
  interestRate: number;
  termMonths: number;
  totalCost: number;
  apr: number;
  incentives?: Array<{
    name: string;
    amount: number;
    type: 'cash' | 'percentage' | 'monthly';
    description: string;
  }>;
}

// 保险信息类型
export interface InsuranceInfo {
  annualPremium: number;
  coverage: {
    liability: number;
    collision: number;
    comprehensive: number;
    uninsuredMotorist: number;
  };
  deductible: number;
  discounts: string[];
  factors: Array<{
    factor: string;
    impact: 'positive' | 'negative' | 'neutral';
    description: string;
  }>;
}

// 汽车比较类型
export interface CarComparison {
  cars: CarDetails[];
  comparisonCriteria: string[];
  scores: {
    [carId: string]: {
      [criterion: string]: number;
    };
  };
  winner?: string;
  summary: string;
}

// 汽车推荐类型
export interface CarRecommendation {
  car: CarDetails;
  score: number;
  reasons: string[];
  alternatives: CarDetails[];
  matchPercentage: number;
}

// 汽车搜索参数类型
export interface CarSearchParams {
  query?: string;
  brand?: string[];
  model?: string[];
  year?: {
    min: number;
    max: number;
  };
  price?: {
    min: number;
    max: number;
  };
  mileage?: {
    min: number;
    max: number;
  };
  fuelType?: FuelType[];
  transmission?: TransmissionType[];
  bodyType?: CarBodyType[];
  location?: {
    latitude: number;
    longitude: number;
    radius: number;
  };
  features?: string[];
  sortBy?: 'price' | 'year' | 'mileage' | 'rating' | 'distance';
  sortOrder?: 'asc' | 'desc';
}

// 汽车列表项类型
export interface CarListItem {
  id: string;
  title: string;
  price: number;
  currency: string;
  year: number;
  mileage: number;
  location: string;
  imageUrl?: string;
  rating?: number;
  reviewCount?: number;
  features: string[];
  distance?: number;
  isFavorite?: boolean;
  isCompare?: boolean;
}
