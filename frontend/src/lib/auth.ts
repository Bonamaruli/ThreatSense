/**
 * auth.ts
 * =======
 * Pengelolaan sesi pengguna di sisi browser.
 *
 * CATATAN KEAMANAN
 * Token disimpan di localStorage. Ini cara paling sederhana dan lazim untuk
 * aplikasi seperti ini, tapi punya kelemahan yang perlu disadari: kalau ada
 * skrip berbahaya berhasil disisipkan ke halaman (serangan XSS), skrip itu
 * bisa membaca localStorage dan mencuri tokennya.
 *
 * Cara yang lebih aman adalah menyimpan token di cookie HttpOnly, yang tidak
 * bisa dibaca JavaScript sama sekali. Itu butuh perubahan di backend juga
 * (menerbitkan cookie, menangani CSRF), jadi belum dikerjakan di tahap ini.
 * Tulis batasan ini di laporan, jangan diklaim sudah aman sepenuhnya.
 */

import apiClient, { TOKEN_KEY } from './api';

export interface AuthUser {
  id: string;
  nama: string;
  email: string;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

// ============================================================
// Penyimpanan token
// ============================================================

export function simpanToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function ambilToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function hapusToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function sedangMasuk(): boolean {
  return !!ambilToken();
}

// ============================================================
// Panggilan ke server
// ============================================================

export async function daftar(
  nama: string,
  email: string,
  sandi: string
): Promise<AuthUser> {
  const res = await apiClient.post<TokenResponse>('/auth/register', {
    nama,
    email,
    sandi,
  });
  simpanToken(res.data.access_token);
  return res.data.user;
}

export async function masuk(email: string, sandi: string): Promise<AuthUser> {
  const res = await apiClient.post<TokenResponse>('/auth/login', {
    email,
    sandi,
  });
  simpanToken(res.data.access_token);
  return res.data.user;
}

/**
 * Ambil profil pemilik token dari server.
 *
 * Sengaja TIDAK menyimpan salinan nama/email di localStorage. Data yang
 * disimpan di browser bisa diubah siapa saja lewat konsol, jadi tampilannya
 * bisa berbohong. Server adalah satu-satunya sumber kebenaran.
 */
export async function profilSaya(): Promise<AuthUser | null> {
  if (!ambilToken()) return null;
  try {
    const res = await apiClient.get<AuthUser>('/auth/me');
    return res.data;
  } catch {
    // Token kedaluwarsa atau tidak sah. Interceptor di api.ts sudah
    // membersihkan token dan mengantar ke halaman masuk.
    return null;
  }
}

export function keluar(): void {
  hapusToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}
