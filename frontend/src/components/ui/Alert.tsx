'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

const alertConfig = {
  info: {
    icon: Info,
    colors: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    iconBg: 'bg-cyan-500/20',
  },
  success: {
    icon: CheckCircle,
    colors: 'bg-green-500/10 border-green-500/20 text-green-400',
    iconBg: 'bg-green-500/20',
  },
  warning: {
    icon: AlertTriangle,
    colors: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    iconBg: 'bg-amber-500/20',
  },
  error: {
    icon: AlertCircle,
    colors: 'bg-red-500/10 border-red-500/20 text-red-400',
    iconBg: 'bg-red-500/20',
  },
};

export function Alert({ 
  type = 'info', 
  title, 
  message, 
  onClose, 
  className = '' 
}: AlertProps) {
  const config = alertConfig[type];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`rounded-xl border p-4 ${config.colors} ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${config.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className="font-semibold mb-1">{title}</h4>
          )}
          <p className="text-sm opacity-90 leading-relaxed">{message}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ 
  icon, 
  title, 
  message, 
  action,
  className = '' 
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`text-center py-12 ${className}`}
    >
      {icon && (
        <motion.div
          className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.6, type: "spring", stiffness: 200 }}
        >
          {icon}
        </motion.div>
      )}
      
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-gray-400 mb-6 max-w-md mx-auto text-sm">{message}</p>
      
      {action && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {action}
        </motion.div>
      )}
    </motion.div>
  );
}
