'use client';

import { useState, useCallback } from 'react';

interface UseScanState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useScan<T>() {
  const [state, setState] = useState<UseScanState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (scanFn: () => Promise<{ success: boolean; data?: T; error?: any }>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await scanFn();
      
      if (result.success && result.data) {
        setState({ data: result.data, loading: false, error: null });
        return result.data;
      } else {
        const errorMessage = result.error?.message || 'Terjadi kesalahan saat memproses scan';
        setState(prev => ({ ...prev, loading: false, error: errorMessage }));
        return null;
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Terjadi kesalahan yang tidak diketahui';
      setState(prev => ({ ...prev, loading: false, error: errorMessage }));
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

export function useModal() {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  return { isOpen, open, close, toggle };
}

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue] as const;
}
