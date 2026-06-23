'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Link, Mail, File, Loader2 } from 'lucide-react';

interface ScanFormProps {
  onScan: (type: 'url' | 'email' | 'file', value: string, file?: File) => void;
  loading?: boolean;
}

export function ScanForm({ onScan, loading = false }: ScanFormProps) {
  const [activeTab, setActiveTab] = React.useState<'url' | 'email' | 'file'>('url');
  const [inputValue, setInputValue] = React.useState('');
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (loading) return;

    if (activeTab === 'file') {
      if (selectedFile) {
        onScan(activeTab, selectedFile.name, selectedFile);
      }
    } else {
      if (inputValue.trim()) {
        onScan(activeTab, inputValue.trim());
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setInputValue(file.name);
    }
  };

  const getPlaceholder = () => {
    switch (activeTab) {
      case 'url':
        return 'https://suspicious-login.ru';
      case 'email':
        return 'phishing@example.com';
      case 'file':
        return 'Pilih file untuk di-scan';
    }
  };

  const getExampleText = () => {
    switch (activeTab) {
      case 'url':
        return 'Coba: suspicious-login.ru';
      case 'email':
        return 'Coba: phishing@fake-bank.com';
      case 'file':
        return 'Format: PDF, DOCX, EXE, ZIP (max 10MB)';
    }
  };

  const tabColors = {
    url: 'cyan',
    email: 'purple',
    file: 'green',
  };

  const activeColor = tabColors[activeTab];

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {/* Tab Selector */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex bg-white/5 border border-white/10 rounded-lg p-1 gap-1">
          {(['url', 'email', 'file'] as const).map((tab) => {
            const icons = {
              url: <Link className="w-4 h-4" />,
              email: <Mail className="w-4 h-4" />,
              file: <File className="w-4 h-4" />,
            };
            const color = tabColors[tab];
            const isActive = activeTab === tab;

            return (
              <motion.button
                key={tab}
                type="button"
                onClick={() => {
                  setActiveTab(tab);
                  setInputValue('');
                  setSelectedFile(null);
                }}
                disabled={loading}
                className={`flex items-center gap-2 px-6 py-2 rounded-md transition-all capitalize ${
                  isActive
                    ? `bg-${color}-500/20 text-${color}-400 border border-${color}-500/50`
                    : 'text-gray-400 hover:text-white'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {icons[tab]}
                {tab}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Input Field */}
      <motion.div 
        className="flex gap-3"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="flex-1 relative">
          {activeTab === 'file' ? (
            <>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                className="hidden"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.exe,.dll,.zip,.rar,.txt,.js,.vbs,.ps1"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-12 py-4 text-left text-gray-400 hover:border-white/20 transition-colors flex items-center gap-3"
              >
                <File className="w-5 h-5 flex-shrink-0" />
                <span className="truncate">
                  {selectedFile ? selectedFile.name : getPlaceholder()}
                </span>
              </button>
            </>
          ) : (
            <>
              <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={getPlaceholder()}
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-12 pr-4 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
              />
            </>
          )}
        </div>
        <motion.button
          type="submit"
          disabled={loading || (activeTab === 'file' ? !selectedFile : !inputValue.trim())}
          className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: loading ? 1 : 1.05 }}
          whileTap={{ scale: loading ? 1 : 0.95 }}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Memindai...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              Scan Sekarang
            </>
          )}
        </motion.button>
      </motion.div>

      {/* Hidden file input */}
      {activeTab === 'file' && (
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.exe,.dll,.zip,.rar,.txt,.js,.vbs,.ps1"
        />
      )}

      <motion.p 
        className="text-center text-sm text-gray-500 mt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {getExampleText()} · Gratis · Tidak perlu daftar
      </motion.p>
    </form>
  );
}
