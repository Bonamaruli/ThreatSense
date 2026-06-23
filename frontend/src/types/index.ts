// Types untuk ThreatSense

export type ScanType = 'url' | 'email' | 'file';
export type ScanStatus = 'aman' | 'mencurigakan' | 'berbahaya' | 'scanning' | 'error';

export interface ScanResult {
  id: string;
  type: ScanType;
  input: string;
  score: number;
  status: ScanStatus;
  timestamp: string;
  details?: {
    threats?: string[];
    shapValues?: Record<string, number>;
    metadata?: Record<string, any>;
  };
}

export interface DashboardStats {
  totalScans: number;
  threatsDetected: number;
  safeScans: number;
  dangerousScans: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface NotificationSettings {
  threatAlerts: boolean;
  scanComplete: boolean;
}

export interface ThemeSettings {
  theme: 'gelap' | 'terang';
}

export interface UserProfile {
  name: string;
  email: string;
  avatar?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
}
