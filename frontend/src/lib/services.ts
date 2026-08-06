import apiClient from './api';
import { ScanResult, DashboardStats, ApiResponse } from '@/types';
import { mapScanResult, mapScanResultList, mapDashboardStats } from './mappers';

// API services untuk ThreatSense

export const scanApi = {
  // Melakukan scan URL, email, atau file
  async performScan(
    type: 'url' | 'email' | 'file',
    input: string,
    file?: File,
    mendalam?: boolean,
  ): Promise<ApiResponse<ScanResult>> {
    try {
      let response;

      if (type === 'file' && file) {
        // Upload file dengan FormData
        const formData = new FormData();
        formData.append('file', file);

        response = await apiClient.post(`/scan/${type}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } else {
        // Field name berbeda tergantung tipe scan, sesuai schema backend.
        // 'mendalam' hanya dikirim untuk URL - backend email/file tidak
        // mengenal field itu dan akan menolak permintaannya.
        const payload = type === 'url'
          ? { url: input, mendalam: Boolean(mendalam) }
          : { email_content: input };

        response = await apiClient.post(`/scan/${type}`, payload);
      }

      return {
        success: true,
        data: mapScanResult(response.data), // <- konversi snake_case -> camelCase di sini
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Mendapatkan hasil scan berdasarkan ID
  async getScanResult(id: string): Promise<ApiResponse<ScanResult>> {
    try {
      const response = await apiClient.get(`/scan/${id}`);
      return {
        success: true,
        data: mapScanResult(response.data),
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  /**
   * Mendapatkan riwayat scan milik akun yang sedang masuk.
   *
   * Dialihkan ke /dashboard/recent karena backend tidak punya endpoint
   * /scan/history — pemanggilan lama selalu menghasilkan 404 tanpa ada yang
   * menyadarinya, sebab halaman riwayat memang belum pernah memanggil fungsi
   * ini.
   *
   * Penyaringan tipe dan status dilakukan di browser (lihat halaman riwayat),
   * jadi parameternya tidak dikirim ke server.
   */
  async getScanHistory(params?: {
    limit?: number;
  }): Promise<ApiResponse<ScanResult[]>> {
    try {
      const response = await apiClient.get('/dashboard/recent', {
        params: { limit: params?.limit ?? 100 },
      });
      return {
        success: true,
        data: mapScanResultList(response.data.scans),
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Menghapus riwayat scan
  async deleteScan(id: string): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/scan/${id}`);
      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },
};

export const dashboardApi = {
  // Mendapatkan statistik dashboard
  async getStats(): Promise<ApiResponse<DashboardStats>> {
    try {
      const response = await apiClient.get('/dashboard/stats');
      return {
        success: true,
        data: mapDashboardStats(response.data),
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Mendapatkan riwayat scan terbaru (endpoint ini SUDAH ada di backend)
  async getRecentScans(limit: number = 10): Promise<ApiResponse<ScanResult[]>> {
    try {
      const response = await apiClient.get('/dashboard/recent', { params: { limit } });
      return {
        success: true,
        data: mapScanResultList(response.data.scans),
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },
};

/**
 * Pengelolaan akun.
 *
 * Sebelumnya bagian ini memanggil /user/profile dan /user/notifications yang
 * TIDAK PERNAH ADA di backend, jadi selalu menghasilkan 404. Tidak ada yang
 * menyadarinya karena halaman Settings memang belum pernah memanggilnya.
 * Sekarang diarahkan ke endpoint yang benar-benar ada.
 */
export const userApi = {
  // Profil pemilik token
  async getProfile(): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get('/auth/me');
      return { success: true, data: response.data };
    } catch (error: any) {
      return { success: false, error: error };
    }
  },

  // Ubah nama dan/atau email
  async updateProfile(data: { nama?: string; email?: string }): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.put('/auth/me', data);
      return { success: true, data: response.data };
    } catch (error: any) {
      return { success: false, error: error };
    }
  },

  // Ganti sandi. Sandi lama wajib benar.
  async changePassword(data: {
    sandi_lama: string;
    sandi_baru: string;
  }): Promise<ApiResponse<void>> {
    try {
      await apiClient.put('/auth/me/password', data);
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error };
    }
  },
};

/**
 * Koreksi pengguna saat sistem salah menilai.
 *
 * Setiap koreksi disimpan bersama fitur yang dipakai saat pemindaian, lalu
 * jadi data latih tambahan pada pelatihan berikutnya. Inilah yang membuat
 * sistem bisa membaik, bukan berhenti di kemampuan saat pertama dilatih.
 */
export const feedbackApi = {
  async kirim(
    scanId: string,
    koreksi: 'safe' | 'suspicious' | 'malicious',
  ): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.post('/feedback', {
        scan_id: scanId,
        koreksi,
      });
      return { success: true, data: response.data };
    } catch (error: any) {
      return { success: false, error: error };
    }
  },

  async statistik(): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get('/feedback/statistik');
      return { success: true, data: response.data };
    } catch (error: any) {
      return { success: false, error: error };
    }
  },
};