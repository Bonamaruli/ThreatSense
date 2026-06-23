'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Shield, 
  Zap, 
  LayoutDashboard, 
  History, 
  Settings, 
  LogOut,
  ChevronLeft
} from 'lucide-react'

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { 
      name: 'Dashboard', 
      href: '/dashboard', 
      icon: LayoutDashboard,
      color: 'cyan'
    },
    { 
      name: 'Riwayat Scan', 
      href: '/history', 
      icon: History,
      color: 'cyan'
    },
    { 
      name: 'Pengaturan', 
      href: '/settings', 
      icon: Settings,
      color: 'cyan'
    },
  ]

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard'
    if (href === '/history') return pathname === '/history'
    if (href === '/settings') return pathname === '/settings'
    return false
  }

  return (
    <>
      <aside className={`fixed left-0 top-0 h-full bg-[#0d1117] border-r border-white/5 z-20 transition-all duration-300 ${collapsed ? 'w-20' : 'w-64'}`}>
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-cyan-400 flex-shrink-0" />
            {!collapsed && (
              <span className="text-xl font-bold whitespace-nowrap">
                Threat<span className="text-cyan-400">Sense</span>
              </span>
            )}
          </div>
        </div>

        {/* Scan Baru Button */}
        <div className="p-4">
          <Link 
            href="/"
            className={`flex items-center gap-3 px-4 py-3 rounded-lg bg-gradient-to-r from-cyan-500/10 to-cyan-600/10 border border-cyan-500/20 text-cyan-400 hover:from-cyan-500/20 hover:to-cyan-600/20 transition-all ${collapsed ? 'justify-center' : ''}`}
          >
            <Zap className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span className="font-medium">Scan Baru</span>}
          </Link>
        </div>

        {/* Navigation Menu */}
        <nav className="px-4 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  active
                    ? 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                } ${collapsed ? 'justify-center' : ''}`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="font-medium">{item.name}</span>}
                {active && !collapsed && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Collapse Button & Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/5 space-y-2">
          <button 
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all"
          >
            <ChevronLeft className={`w-5 h-5 flex-shrink-0 transition-transform ${collapsed ? 'rotate-180' : ''}`} />
            {!collapsed && <span className="font-medium">Ciutkan</span>}
          </button>
        </div>
      </aside>
    </>
  )
}