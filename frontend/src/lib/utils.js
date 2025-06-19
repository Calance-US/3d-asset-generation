import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
export const BASE_URL = `${API_BASE}/api/v1`;
