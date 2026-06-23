import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ThreatSense - Deteksi Ancaman Siber Berbasis AI',
  description: 'Platform verifikasi ancaman siber menggunakan machine learning untuk mendeteksi URL, email, dan file berbahaya',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="id">
      <body className="antialiased">{children}</body>
    </html>
  )
}