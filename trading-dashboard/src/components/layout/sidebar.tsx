'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/theme-toggle'
import { 
  TrendingUp, 
  Activity, 
  Wallet, 
  History, 
  BarChart3, 
  Settings, 
  Menu,
  X,
  DollarSign,
  PieChart
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: TrendingUp },
  { name: 'Portfolio', href: '/portfolio', icon: Wallet },
  { name: 'Live Trading', href: '/trading', icon: Activity },
  { name: 'Trade History', href: '/history', icon: History },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'P&L Report', href: '/pnl', icon: PieChart },
  { name: 'Balance', href: '/balance', icon: DollarSign },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  return (
    <>
      {/* Mobile menu button */}
      <div className="fixed top-4 left-4 z-50 lg:hidden">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-md bg-white dark:bg-gray-900 shadow-lg border border-gray-200 dark:border-gray-800"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed left-0 top-0 z-40 h-full w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">TradingBot</h1>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
                  )}
                  onClick={() => setIsOpen(false)}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Theme toggle and Status */}
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Theme</span>
              <ThemeToggle />
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600 dark:text-gray-300">Bot Active</span>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}