'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'
import { format } from 'date-fns'
import { TrendingUp, TrendingDown, DollarSign, Target } from 'lucide-react'
import { formatCurrency, formatPercentage, getColorForPnL } from '@/lib/utils'

interface PortfolioData {
  timestamp: string
  portfolioValue: number
  pnl: number
  cumulativePnl: number
}

interface AssetAllocation {
  asset: string
  value: number
  percentage: number
  color: string
}

interface StrategyPerformance {
  strategy: string
  trades: number
  winRate: number
  totalPnl: number
  avgPnl: number
}

interface PortfolioAnalyticsProps {
  portfolioHistory: PortfolioData[]
  assetAllocation: AssetAllocation[]
  strategyPerformance: StrategyPerformance[]
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316']

export default function PortfolioAnalytics({ 
  portfolioHistory, 
  assetAllocation, 
  strategyPerformance 
}: PortfolioAnalyticsProps) {
  const [selectedChart, setSelectedChart] = useState<'portfolio' | 'pnl' | 'allocation' | 'strategy'>('portfolio')

  const chartData = portfolioHistory.map(item => ({
    ...item,
    timestamp: new Date(item.timestamp).getTime(),
    formattedTime: format(new Date(item.timestamp), 'MMM dd'),
  }))

  const totalPortfolioValue = assetAllocation.reduce((sum, asset) => sum + asset.value, 0)
  const totalPnL = portfolioHistory[portfolioHistory.length - 1]?.cumulativePnl || 0
  const totalTrades = strategyPerformance.reduce((sum, strategy) => sum + strategy.trades, 0)
  const avgWinRate = strategyPerformance.reduce((sum, strategy) => sum + strategy.winRate, 0) / strategyPerformance.length

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {format(new Date(label), 'MMM dd, yyyy')}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="font-semibold" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const renderChart = () => {
    switch (selectedChart) {
      case 'portfolio':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="timestamp"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                stroke="#6B7280"
              />
              <YAxis 
                tickFormatter={(value) => formatCurrency(value, '').replace(' ', '')}
                stroke="#6B7280"
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="portfolioValue"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )
      
      case 'pnl':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="timestamp"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                stroke="#6B7280"
              />
              <YAxis 
                tickFormatter={(value) => formatCurrency(value, '').replace(' ', '')}
                stroke="#6B7280"
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="cumulativePnl"
                stroke={totalPnL >= 0 ? "#10B981" : "#EF4444"}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )
      
      case 'allocation':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={assetAllocation}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ asset, percentage }) => `${asset} (${percentage.toFixed(1)}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {assetAllocation.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )
      
      case 'strategy':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={strategyPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis dataKey="strategy" stroke="#6B7280" />
              <YAxis tickFormatter={(value) => formatCurrency(value, '').replace(' ', '')} stroke="#6B7280" />
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
              <Bar dataKey="totalPnl" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Chart */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <CardTitle>Portfolio Analytics</CardTitle>
              <div className="flex rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
                {[
                  { key: 'portfolio', label: 'Portfolio' },
                  { key: 'pnl', label: 'P&L' },
                  { key: 'allocation', label: 'Allocation' },
                  { key: 'strategy', label: 'Strategy' }
                ].map((tab) => (
                  <Button
                    key={tab.key}
                    variant={selectedChart === tab.key ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setSelectedChart(tab.key as any)}
                    className="text-xs"
                  >
                    {tab.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {renderChart()}
          </CardContent>
        </Card>
      </div>

      {/* Statistics */}
      <div className="space-y-6">
        {/* Summary Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Total Value</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {formatCurrency(totalPortfolioValue)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Total P&L</span>
              <span className={`font-semibold ${getColorForPnL(totalPnL)}`}>
                {formatCurrency(Math.abs(totalPnL))}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Total Trades</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {totalTrades}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Avg Win Rate</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {formatPercentage(avgWinRate)}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Strategy Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Strategies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {strategyPerformance
                .sort((a, b) => b.totalPnl - a.totalPnl)
                .slice(0, 5)
                .map((strategy, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {strategy.strategy}
                    </div>
                    <div className="text-xs text-gray-500">
                      {strategy.trades} trades • {formatPercentage(strategy.winRate)} win rate
                    </div>
                  </div>
                  <div className={`text-sm font-semibold ${getColorForPnL(strategy.totalPnl)}`}>
                    {formatCurrency(Math.abs(strategy.totalPnl))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}