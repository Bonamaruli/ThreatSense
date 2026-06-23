import apiClient from './api';
import { ScanResult, DashboardStats, ApiResponse } from '@/types';

// API services untuk ThreatSense

export const scanApi = {
  // Melakukan scan URL, email, atau file
  async performScan(type: 'url' | 'email' | 'file', input: string, file?: File): Promise<ApiResponse<ScanResult>> {
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
        // Scan URL atau email dengan JSON
        response = await apiClient.post(`/scan/${type}`, { input });
      }
      
      return {
        success: true,
        data: response.data,
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
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Mendapatkan riwayat scan
  async getScanHistory(params?: {
    type?: 'url' | 'email' | 'file';
    status?: 'aman' | 'mencurigakan' | 'berbahaya';
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<ScanResult[]>> {
    try {
      const response = await apiClient.get('/scan/history', { params });
      return {
        success: true,
        data: response.data,
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
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },
};

export const userApi = {
  // Mendapatkan profil user
  async getProfile(): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get('/user/profile');
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Update profil user
  async updateProfile(data: { name?: string; email?: string }): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.put('/user/profile', data);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },

  // Update preferensi notifikasi
  async updateNotificationSettings(settings: { threatAlerts: boolean; scanComplete: boolean }): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.put('/user/notifications', settings);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error,
      };
    }
  },
};
