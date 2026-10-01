import { apiClient } from "./api-client";
import type { APIResponse } from "@/types";

export interface Brand {
  id: number;
  name: string;
  logo_url: string | null;
}

export interface CarModel {
  id: number;
  name: string;
  brand_id: number;
}

export interface Variant {
  id: number;
  name: string;
  car_model_id: number;
}

export interface City {
  id: number;
  name: string;
  state: string;
}

const FALLBACK_BRANDS: Brand[] = [
  { id: 1, name: "Honda", logo_url: null },
  { id: 2, name: "Mercedes-Benz", logo_url: null },
  { id: 3, name: "Toyota", logo_url: null },
  { id: 4, name: "Ford", logo_url: null },
  { id: 5, name: "Nissan", logo_url: null },
  { id: 6, name: "Kia", logo_url: null },
  { id: 7, name: "Hyundai", logo_url: null },
  { id: 8, name: "Maruti Suzuki", logo_url: null },
  { id: 9, name: "Tata", logo_url: null },
  { id: 10, name: "BMW", logo_url: null },
  { id: 11, name: "Audi", logo_url: null },
  { id: 12, name: "Volkswagen", logo_url: null },
  { id: 13, name: "Mahindra", logo_url: null },
];

const FALLBACK_MODELS: Record<number, CarModel[]> = {
  1: [ // Honda
    { id: 101, brand_id: 1, name: "Odyssey" },
    { id: 102, brand_id: 1, name: "Pilot" },
    { id: 103, brand_id: 1, name: "Civic" },
    { id: 104, brand_id: 1, name: "Accord" },
    { id: 105, brand_id: 1, name: "CR-V" },
    { id: 106, brand_id: 1, name: "City" },
  ],
  2: [ // Mercedes-Benz
    { id: 201, brand_id: 2, name: "A-Class" },
    { id: 202, brand_id: 2, name: "C-Class" },
    { id: 203, brand_id: 2, name: "E-Class" },
    { id: 204, brand_id: 2, name: "G-Class" },
    { id: 205, brand_id: 2, name: "GLC" },
    { id: 206, brand_id: 2, name: "GLE" },
  ],
  3: [ // Toyota
    { id: 301, brand_id: 3, name: "4Runner" },
    { id: 302, brand_id: 3, name: "Camry" },
    { id: 303, brand_id: 3, name: "Corolla" },
    { id: 304, brand_id: 3, name: "RAV4" },
    { id: 305, brand_id: 3, name: "Fortuner" },
    { id: 306, brand_id: 3, name: "Highlander" },
  ],
  4: [ // Ford
    { id: 401, brand_id: 4, name: "F-150" },
    { id: 402, brand_id: 4, name: "Mustang" },
    { id: 403, brand_id: 4, name: "Explorer" },
    { id: 404, brand_id: 4, name: "Escape" },
    { id: 405, brand_id: 4, name: "Bronco" },
  ],
  5: [ // Nissan
    { id: 501, brand_id: 5, name: "Altima" },
    { id: 502, brand_id: 5, name: "Maxima" },
    { id: 503, brand_id: 5, name: "Rogue" },
    { id: 504, brand_id: 5, name: "Pathfinder" },
    { id: 505, brand_id: 5, name: "Sentra" },
  ],
  6: [ // Kia
    { id: 601, brand_id: 6, name: "Telluride" },
    { id: 602, brand_id: 6, name: "Sorento" },
    { id: 603, brand_id: 6, name: "Sportage" },
    { id: 604, brand_id: 6, name: "K5" },
    { id: 605, brand_id: 6, name: "Seltos" },
  ],
  7: [ // Hyundai
    { id: 701, brand_id: 7, name: "Elantra" },
    { id: 702, brand_id: 7, name: "Sonata" },
    { id: 703, brand_id: 7, name: "Tucson" },
    { id: 704, brand_id: 7, name: "Santa Fe" },
    { id: 705, brand_id: 7, name: "Creta" },
    { id: 706, brand_id: 7, name: "i20" },
  ],
  8: [ // Maruti Suzuki
    { id: 801, brand_id: 8, name: "Swift" },
    { id: 802, brand_id: 8, name: "Brezza" },
    { id: 803, brand_id: 8, name: "Baleno" },
    { id: 804, brand_id: 8, name: "Dzire" },
    { id: 805, brand_id: 8, name: "Ertiga" },
  ],
  9: [ // Tata
    { id: 901, brand_id: 9, name: "Nexon" },
    { id: 902, brand_id: 9, name: "Harrier" },
    { id: 903, brand_id: 9, name: "Safari" },
    { id: 904, brand_id: 9, name: "Punch" },
    { id: 905, brand_id: 9, name: "Tiago" },
  ],
  10: [ // BMW
    { id: 1001, brand_id: 10, name: "3 Series" },
    { id: 1002, brand_id: 10, name: "5 Series" },
    { id: 1003, brand_id: 10, name: "X1" },
    { id: 1004, brand_id: 10, name: "X3" },
    { id: 1005, brand_id: 10, name: "X5" },
  ],
  11: [ // Audi
    { id: 1101, brand_id: 11, name: "A3" },
    { id: 1102, brand_id: 11, name: "A4" },
    { id: 1103, brand_id: 11, name: "A6" },
    { id: 1104, brand_id: 11, name: "Q3" },
    { id: 1105, brand_id: 11, name: "Q5" },
  ],
  12: [ // Volkswagen
    { id: 1201, brand_id: 12, name: "Polo" },
    { id: 1202, brand_id: 12, name: "Vento" },
    { id: 1203, brand_id: 12, name: "Taigun" },
    { id: 1204, brand_id: 12, name: "Tiguan" },
    { id: 1205, brand_id: 12, name: "Virtus" },
  ],
  13: [ // Mahindra
    { id: 1301, brand_id: 13, name: "Thar" },
    { id: 1302, brand_id: 13, name: "XUV700" },
    { id: 1303, brand_id: 13, name: "Scorpio" },
    { id: 1304, brand_id: 13, name: "Bolero" },
    { id: 1305, brand_id: 13, name: "XUV300" },
  ],
};

const FALLBACK_VARIANTS: Record<number, Variant[]> = {
  101: [ // Odyssey
    { id: -1001, car_model_id: 101, name: "SE" },
    { id: -1002, car_model_id: 101, name: "EX-L" },
    { id: -1003, car_model_id: 101, name: "Touring" },
    { id: -1004, car_model_id: 101, name: "Elite" },
  ],
  102: [ // Pilot
    { id: -1005, car_model_id: 102, name: "Black Edition" },
    { id: -1006, car_model_id: 102, name: "Trailsport" },
    { id: -1007, car_model_id: 102, name: "Touring" },
  ],
  201: [ // A-Class
    { id: -2001, car_model_id: 201, name: "A 220" },
    { id: -2002, car_model_id: 201, name: "AMG A 35" },
    { id: -2003, car_model_id: 201, name: "A 220 4MATIC" },
  ],
  204: [ // G-Class
    { id: -2004, car_model_id: 204, name: "AMG G 63" },
    { id: -2005, car_model_id: 204, name: "G 550" },
  ],
  301: [ // 4Runner
    { id: -3001, car_model_id: 301, name: "SR5 Premium" },
    { id: -3002, car_model_id: 301, name: "TRD Off-Road" },
    { id: -3003, car_model_id: 301, name: "Limited" },
  ],
  401: [ // F-150
    { id: -4001, car_model_id: 401, name: "FX4" },
    { id: -4002, car_model_id: 401, name: "Lariat" },
    { id: -4003, car_model_id: 401, name: "XLT" },
  ],
  501: [ // Altima
    { id: -5001, car_model_id: 501, name: "S" },
    { id: -5002, car_model_id: 501, name: "SV" },
    { id: -5003, car_model_id: 501, name: "SL" },
  ],
  601: [ // Telluride
    { id: -6001, car_model_id: 601, name: "SX" },
    { id: -6002, car_model_id: 601, name: "EX" },
    { id: -6003, car_model_id: 601, name: "LX" },
  ],
  801: [ // Swift
    { id: -8001, car_model_id: 801, name: "VXI" },
    { id: -8002, car_model_id: 801, name: "ZXI" },
    { id: -8003, car_model_id: 801, name: "ZXI Plus" },
  ],
};

const FALLBACK_CITIES: City[] = [
  { id: -1, name: "Mumbai", state: "Maharashtra" },
  { id: -2, name: "Delhi", state: "Delhi" },
  { id: -3, name: "Bangalore", state: "Karnataka" },
  { id: -4, name: "Hyderabad", state: "Telangana" },
  { id: -5, name: "Chennai", state: "Tamil Nadu" },
  { id: -6, name: "Pune", state: "Maharashtra" },
  { id: -7, name: "Kolkata", state: "West Bengal" },
  { id: -8, name: "Ahmedabad", state: "Gujarat" },
  { id: -9, name: "Jaipur", state: "Rajasthan" },
];

export async function getBrands(): Promise<Brand[]> {
  try {
    const { data } = await apiClient.get<APIResponse<Brand[]>>("/vehicles/brands");
    if (data.data && data.data.length > 0) {
      return data.data;
    }
  } catch (err) {
    console.warn("Failed to fetch brands from backend, using dataset fallback", err);
  }
  return FALLBACK_BRANDS;
}

export async function getModelsByBrand(brandId: number): Promise<CarModel[]> {
  try {
    const { data } = await apiClient.get<APIResponse<CarModel[]>>(`/vehicles/brands/${brandId}/models`);
    if (data.data && data.data.length > 0) {
      return data.data;
    }
  } catch (err) {
    console.warn(`Failed to fetch models for brand ${brandId}, using dataset fallback`, err);
  }
  return FALLBACK_MODELS[brandId] || [];
}

export async function getVariantsByModel(modelId: number): Promise<Variant[]> {
  try {
    const { data } = await apiClient.get<APIResponse<Variant[]>>(`/vehicles/models/${modelId}/variants`);
    if (data.data && data.data.length > 0) {
      return data.data;
    }
  } catch (err) {
    console.warn(`Failed to fetch variants for model ${modelId}, using dataset fallback`, err);
  }
  return FALLBACK_VARIANTS[modelId] || [
    { id: -(modelId * 10 + 1), car_model_id: modelId, name: "Standard" },
    { id: -(modelId * 10 + 2), car_model_id: modelId, name: "Premium" },
  ];
}

export async function getCities(): Promise<City[]> {
  try {
    const { data } = await apiClient.get<APIResponse<City[]>>("/vehicles/cities");
    if (data.data && data.data.length > 0) {
      return data.data;
    }
  } catch (err) {
    console.warn("Failed to fetch cities from backend, using dataset fallback", err);
  }
  return FALLBACK_CITIES;
}

const STATE_NAMES: Record<string, string> = {
  "AN": "Andaman and Nicobar", "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam",
  "BR": "Bihar", "CG": "Chhattisgarh", "CH": "Chandigarh", "DD": "Daman and Diu",
  "DL": "Delhi", "DN": "Dadra and Nagar Haveli", "GA": "Goa", "GJ": "Gujarat",
  "HR": "Haryana", "HP": "Himachal Pradesh", "JH": "Jharkhand", "JK": "Jammu and Kashmir",
  "KA": "Karnataka", "KL": "Kerala", "LD": "Lakshadweep", "MH": "Maharashtra",
  "ML": "Meghalaya", "MN": "Manipur", "MP": "Madhya Pradesh", "MZ": "Mizoram",
  "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab", "PY": "Puducherry",
  "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
  "TS": "Telangana", "UK": "Uttarakhand", "UP": "Uttar Pradesh", "WB": "West Bengal"
};

const MAJOR_CITIES: Record<string, string> = {
  "MH-01": "Mumbai South", "MH-02": "Mumbai West", "MH-03": "Mumbai East", "MH-04": "Thane",
  "MH-12": "Pune", "MH-14": "Pimpri-Chinchwad", "MH-15": "Nashik", "MH-43": "Navi Mumbai", "MH-47": "Mumbai North",
  "KA-01": "Bengaluru Central", "KA-02": "Bengaluru West", "KA-03": "Bengaluru East",
  "KA-04": "Bengaluru North", "KA-05": "Bengaluru South", "KA-51": "Electronic City",
  "KA-53": "K.R. Puram", "DL-1C": "Delhi", "DL-2C": "Delhi", "DL-3C": "Delhi",
  "DL-4C": "Delhi", "DL-5C": "Delhi", "DL-6C": "Delhi", "DL-7C": "Delhi", "DL-8C": "Delhi", "DL-9C": "Delhi", "DL-10": "Delhi",
  "HR-26": "Gurugram", "HR-51": "Faridabad", "HR-98": "Gurugram", "UP-14": "Ghaziabad",
  "UP-16": "Noida", "UP-32": "Lucknow", "UP-78": "Kanpur", "TS-07": "Hyderabad",
  "TS-08": "Hyderabad", "TS-09": "Hyderabad", "TS-10": "Hyderabad", "TS-11": "Hyderabad",
  "TS-12": "Hyderabad", "TS-13": "Hyderabad", "TN-01": "Chennai Central",
  "TN-02": "Chennai North West", "TN-07": "Chennai South", "TN-09": "Chennai West",
  "TN-10": "Chennai South West", "GJ-01": "Ahmedabad", "GJ-05": "Surat", "GJ-06": "Vadodara",
  "BR-01": "Patna", "MP-09": "Indore", "MP-04": "Bhopal", "CH-01": "Chandigarh",
  "RJ-14": "Jaipur", "PB-10": "Ludhiana"
};

import rtoMappingData from "./rto_mapping.json";

const RTO_MAPPING: Record<string, string> = rtoMappingData as Record<string, string>;

export function formatCityName(rtoCode: string): string {
  if (!rtoCode) return "";
  
  const lowerCode = rtoCode.toLowerCase().trim();
  if (RTO_MAPPING[lowerCode]) {
    return RTO_MAPPING[lowerCode];
  }

  const code = rtoCode.toUpperCase().trim();
  
  if (MAJOR_CITIES[code]) {
    const stateCode = code.split('-')[0] ?? "";
    const stateName = STATE_NAMES[stateCode] || "";
    return `${MAJOR_CITIES[code]}, ${stateName}`;
  }
  
  const parts = code.split('-');
  if (parts.length === 2) {
    const stateCode = parts[0] ?? "";
    const stateName = STATE_NAMES[stateCode];
    if (stateName) {
      return `${stateName} (${code})`;
    }
  }
  return rtoCode; // Fallback
}
