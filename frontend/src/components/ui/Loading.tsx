'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={className}
    >
      <Loader2 className={`${sizes[size]} text-current`} />
    </motion.div>
  );
}

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Memproses...' }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-[#0d1117] border border-white/10 rounded-xl p-8 text-center"
      >
        <Spinner size="lg" className="text-cyan-400 mx-auto mb-4" />
        <p className="text-white font-medium">{message}</p>
      </motion.div>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-white/5 rounded ${className}`}
      style={{
        backgroundImage: 'linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0.03) 75%)',
        backgroundSize: '200% 100%',
      }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-[#0d1117] border border-white/5 rounded-xl p-6 space-y-4">
      <Skeleton className="w-12 h-12 rounded-lg" />
      <Skeleton className="w-3/4 h-6" />
      <Skeleton className="w-full h-4" />
      <Skeleton className="w-2/3 h-4" />
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="bg-[#0d1117] border border-white/5 rounded-xl overflow-hidden">
      <div className="p-4 space-y-4">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="w-full h-12" />
        ))}
      </div>
    </div>
  );
}
