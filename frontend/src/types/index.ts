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
    /**
     * Alasan berbahasa manusia kenapa URL ini dinilai begitu, sudah urut
     * dari yang paling berat. Contoh isi:
     *   { judul: "Peniruan merek",
     *     alasan: "Menyebut 'bri' padahal ini bukan domain resminya...",
     *     bobot: 0.9 }
     *
     * Tampilkan ini ke pengguna, bukan cuma angka persennya. Skor 90% tanpa
     * keterangan tidak memberi tahu apa pun; "menyebut bri padahal bukan
     * domain resmi BRI" langsung bisa dimengerti dan ditindaklanjuti.
     */
    explanations?: ScanExplanation[];
    /**
     * Bukti hasil pemeriksaan mendalam - umur domain, negara server,
     * sertifikat, dan seterusnya. Kosong kalau pemindaiannya cepat.
     */
    evidenceSummary?: { label: string; nilai: string }[];
    /** true bila alamatnya benar-benar dibuka untuk diperiksa. */
    deepScan?: boolean;
  };
}

/** Satu alasan penilaian, dikirim backend lewat field `explanations`. */
export interface ScanExplanation {
  judul: string;
  alasan: string;
  bobot: number;
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
