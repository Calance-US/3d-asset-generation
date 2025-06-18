import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export const BASE_URL = process.env.REACT_APP_API_BASE_URL || (() => { console.warn('REACT_APP_API_BASE_URL is not set!'); return ''; })(); 