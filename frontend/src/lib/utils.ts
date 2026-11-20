import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class names conditionally and cleanly.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
