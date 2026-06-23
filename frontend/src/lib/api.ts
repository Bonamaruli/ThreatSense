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

// Request interceptor untuk menambahkan auth token jika ada
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // TODO: Implementasi token authentication nanti
    // const token = localStorage.getItem('auth_token');
    // if (token && config.headers) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor untuk handling error global
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<any>>) => {
    // Handle error responses
    if (error.response) {
      // Server mengembalikan error response
      const apiError: ApiError = {
        message: error.response.data?.error?.message || 'Terjadi kesalahan pada server',
        code: error.response.data?.error?.code,
        details: error.response.data?.error?.details,
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
