'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, Zap } from 'lucide-react'
import { formatCurrency, formatPercentage, getColorForPnL } from '@/lib/utils'

interface PortfolioStats {
  totalBalance: number
  totalPnL: number
  totalPnLPercentage: number
  dayPnL: number
  dayPnLPercentage: number
  activeTrades: number
  successRate: number
  totalTrades: number
}

interface PortfolioOverviewProps {
  stats: PortfolioStats
}

export default function PortfolioOverview({ stats }: PortfolioOverviewProps) {
  const metrics = [
    {
      title: 'Total Balance',
      value: formatCurrency(stats.totalBalance),
      icon: DollarSign,
      trend: stats.totalPnL,
      trendLabel: formatPercentage(stats.totalPnLPercentage),
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
    {
      title: 'Today\'s P&L',
      value: formatCurrency(Math.abs(stats.dayPnL)),
      icon: stats.dayPnL >= 0 ? TrendingUp : TrendingDown,
      trend: stats.dayPnL,
      trendLabel: formatPercentage(stats.dayPnLPercentage),
      bgColor: stats.dayPnL >= 0 ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20',
      iconColor: stats.dayPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
    },
    {
      title: 'Active Trades',
      value: stats.activeTrades.toString(),
      icon: Activity,
      trend: 0,
      trendLabel: 'Live',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      iconColor: 'text-purple-600 dark:text-purple-400',
    },
    {
      title: 'Success Rate',
      value: formatPercentage(stats.successRate),
      icon: Target,
      trend: 0,
      trendLabel: `${stats.totalTrades} trades`,
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
      iconColor: 'text-orange-600 dark:text-orange-400',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {metrics.map((metric, index) => (
        <Card key={index} className="relative overflow-hidden">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-300">
                {metric.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`w-5 h-5 ${metric.iconColor}`} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {metric.value}
              </div>
              <div className="flex items-center space-x-2">
                {metric.trend !== 0 && (
                  <div className={`flex items-center ${getColorForPnL(metric.trend)}`}>
                    {metric.trend > 0 ? (
                      <TrendingUp className="w-4 h-4 mr-1" />
                    ) : (
                      <TrendingDown className="w-4 h-4 mr-1" />
                    )}
                  </div>
                )}
                <span className={`text-sm ${metric.trend !== 0 ? getColorForPnL(metric.trend) : 'text-gray-500'}`}>
                  {metric.trendLabel}
                </span>
              </div>
            </div>
          </CardContent>
          
          {/* Subtle animation effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -skew-x-12 -translate-x-full animate-pulse" />
        </Card>
      ))}
    </div>
  )
}