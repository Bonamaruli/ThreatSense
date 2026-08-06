import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiResponse, ApiError } from '@/types';

// Konfigurasi base URL API - akan digunakan saat backend sudah siap
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Instance axios dengan konfigurasi default
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 detik timeout
});

/** Nama penyimpanan token di browser. Dipakai bersama oleh auth.ts. */
export const TOKEN_KEY = 'threatsense_token';

// Setiap permintaan otomatis membawa token, jadi tidak perlu ditulis satu
// per satu di setiap pemanggilan - dan tidak bisa lupa ditulis.
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // typeof window dicek karena Next.js menjalankan sebagian kode di server,
    // dan localStorage hanya ada di browser. Tanpa penjagaan ini, halaman
    // gagal render dengan "localStorage is not defined".
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor untuk handling error global
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<any>>) => {
    // Handle error responses
    if (error.response) {
      const status = error.response.status;

      // Sesi habis atau token tidak sah: bersihkan token lalu antar ke
      // halaman masuk. Tanpa ini pengguna terjebak di halaman kosong yang
      // terus gagal memuat data tanpa penjelasan.
      if (status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY);
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login?alasan=sesi-habis';
        }
      }

      // FastAPI mengirim pesan kesalahan di field "detail", bukan
      // "error.message". Sebelumnya field itu tidak pernah dibaca sehingga
      // pengguna selalu melihat pesan umum "Terjadi kesalahan pada server"
      // walau server sudah menjelaskan masalahnya dengan rinci.
      const data: any = error.response.data;
      let pesan: string | undefined;

      if (typeof data?.detail === 'string') {
        pesan = data.detail;
      } else if (Array.isArray(data?.detail)) {
        // Kesalahan validasi datang sebagai daftar objek.
        //
        // Awalan "Value error, " dibuang: itu istilah internal Pydantic yang
        // tidak berarti apa-apa bagi pengguna. Tanpa dibuang, pesannya jadi
        // "Value error, Alamat tidak dikenali..." yang terlihat seperti
        // program rusak, padahal cuma salah ketik.
        pesan = data.detail
          .map((d: any) => String(d?.msg ?? '').replace(/^Value error,\s*/i, ''))
          .filter(Boolean)
          .join('. ');
      } else if (typeof data?.error?.message === 'string') {
        pesan = data.error.message;
      }

      const apiError: ApiError = {
        message: pesan || 'Terjadi kesalahan pada server',
        code: String(status),
        details: data,
      };
      return Promise.reject(apiError);
    } else if (error.request) {
      // Request dikirim tapi tidak ada response (network error)
      const networkError: ApiError = {
        message: 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda.',
        code: 'NETWORK_ERROR',
      };
      return Promise.reject(networkError);
    } else {
      // Error lainnya
      const unknownError: ApiError = {
        message: error.message || 'Terjadi kesalahan yang tidak diketahui',
        code: 'UNKNOWN_ERROR',
      };
      return Promise.reject(unknownError);
    }
  }
);

export default apiClient;
