/**
 * mappers.ts
 * ==========
 * Lapisan penerjemah antara response backend (snake_case, label Inggris)
 * dan tipe data yang dipakai di seluruh frontend (camelCase, label Indonesia).
 *
 * KENAPA FILE INI ADA:
 * Backend FastAPI mengembalikan field seperti `risk_score`, `threat_label`,
 * `created_at` (konvensi Python). Frontend (types/index.ts) sudah didesain
 * dengan field seperti `score`, `status`, `timestamp` (konvensi JS/TS) dan
 * status berbahasa Indonesia ('aman', 'mencurigakan', 'berbahaya').
 *
 * Daripada mengubah nama field di backend (yang sudah konsisten dipakai di
 * seluruh service layer & database) ATAU mengubah puluhan komponen frontend
 * satu-satu, konversi dilakukan SEKALI di sini. Semua pemanggilan API di
 * services.ts wajib lewat mapper ini sebelum data dipakai komponen manapun.
 */

import {
  ScanResult,
  ScanType,
  ScanStatus,
  DashboardStats,
  ScanExplanation,
} from '@/types';

// ============================================================
// Bentuk mentah response dari backend (sesuai schema Pydantic)
// ============================================================

interface RawScanResponse {
  id: string;
  scan_type: string;
  input_value: string;
  risk_score: number;
  threat_label: string; // "Safe" | "Suspicious" | "Malicious"
  features_json?: Record<string, any>;
  shap_values?: Record<string, any>;
  explanations?: ScanExplanation[] | null;
  created_at: string;
}

interface RawDashboardStats {
  total_scans: number;
  malicious_detected: number;
  safe_detected: number;
  suspicious_detected: number;
}

// ============================================================
// Mapping status: threat_label (Inggris) -> ScanStatus (Indonesia)
// ============================================================

const THREAT_LABEL_TO_STATUS: Record<string, ScanStatus> = {
  Safe: 'aman',
  Suspicious: 'mencurigakan',
  Malicious: 'berbahaya',
};

function mapThreatLabelToStatus(label: string): ScanStatus {
  return THREAT_LABEL_TO_STATUS[label] ?? 'error';
}

// ============================================================
// Mapper utama: 1 hasil scan
// ============================================================

export function mapScanResult(raw: RawScanResponse): ScanResult {
  return {
    id: raw.id,
    type: raw.scan_type as ScanType,
    input: raw.input_value,
    score: raw.risk_score,
    status: mapThreatLabelToStatus(raw.threat_label),
    timestamp: raw.created_at,
    details: {
      shapValues: raw.shap_values,
      metadata: raw.features_json,
      // Alasan berbahasa manusia. Inilah yang sebaiknya ditampilkan ke
      // pengguna - jauh lebih berguna daripada sekadar angka persen.
      explanations: raw.explanations ?? [],
    },
  };
}

export function mapScanResultList(rawList: RawScanResponse[]): ScanResult[] {
  return rawList.map(mapScanResult);
}

// ============================================================
// Mapper: Dashboard Stats
// ============================================================
// CATATAN DESAIN (perlu kamu review):
// Backend punya 3 kategori terpisah: malicious_detected, suspicious_detected,
// safe_detected. Frontend punya field `threatsDetected` yang generik (belum
// jelas apakah ini "malicious saja" atau "malicious + suspicious digabung").
// Untuk sekarang saya asumsikan threatsDetected = TOTAL non-aman
// (malicious + suspicious). Sesuaikan kalau desain UI kamu maksudnya beda.

export function mapDashboardStats(raw: RawDashboardStats): DashboardStats {
  return {
    totalScans: raw.total_scans,
    safeScans: raw.safe_detected,
    dangerousScans: raw.malicious_detected,
    threatsDetected: raw.malicious_detected + raw.suspicious_detected,
  };
}