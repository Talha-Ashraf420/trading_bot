'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { formatCurrency, formatNumber, cn } from '@/lib/utils'
import { 
  Eye, 
  EyeOff, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  Wallet,
  Lock,
  DollarSign
} from 'lucide-react'

interface Balance {
  asset: string
  free: number
  locked: number
  total: number
  usdValue: number
  change24h: number
  change24hPercent: number
}

interface Position {
  symbol: string
  side: 'long' | 'short'
  size: number
  entryPrice: number
  markPrice: number
  pnl: number
  pnlPercent: number
  margin: number
  timestamp: string
}

interface BalanceDisplayProps {
  balances: Balance[]
  positions: Position[]
  totalBalance: number
  totalPnL: number
  isLoading?: boolean
  onRefresh?: () => void
}

export default function BalanceDisplay({ 
  balances, 
  positions, 
  totalBalance, 
  totalPnL,
  isLoading = false,
  onRefresh 
}: BalanceDisplayProps) {
  const [showBalances, setShowBalances] = useState(true)
  const [selectedTab, setSelectedTab] = useState<'balances' | 'positions'>('balances')

  const significantBalances = balances.filter(balance => balance.total > 0.001)
  const totalUsdValue = balances.reduce((sum, balance) => sum + balance.usdValue, 0)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Balance Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Wallet className="w-5 h-5" />
              <span>Account Balance</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowBalances(!showBalances)}
              >
                {showBalances ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {showBalances ? formatCurrency(totalBalance) : '••••••'}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">Total Balance</div>
              </div>
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className={cn(
                  "text-2xl font-bold",
                  totalPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {showBalances ? formatCurrency(Math.abs(totalPnL)) : '••••••'}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">Total P&L</div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-600 dark:text-gray-300">Asset Breakdown</h4>
              {significantBalances.map((balance) => (
                <div key={balance.asset} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {balance.asset.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {balance.asset}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-300">
                        {showBalances ? formatNumber(balance.total, 6) : '••••••'}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {showBalances ? formatCurrency(balance.usdValue) : '••••••'}
                    </div>
                    <div className={cn(
                      "text-sm flex items-center",
                      balance.change24hPercent >= 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {balance.change24hPercent >= 0 ? (
                        <TrendingUp className="w-3 h-3 mr-1" />
                      ) : (
                        <TrendingDown className="w-3 h-3 mr-1" />
                      )}
                      {balance.change24hPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Positions & Details */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
              <Button
                variant={selectedTab === 'balances' ? "default" : "ghost"}
                size="sm"
                onClick={() => setSelectedTab('balances')}
                className="text-xs"
              >
                Balances
              </Button>
              <Button
                variant={selectedTab === 'positions' ? "default" : "ghost"}
                size="sm"
                onClick={() => setSelectedTab('positions')}
                className="text-xs"
              >
                Positions ({positions.length})
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {selectedTab === 'balances' ? (
            <div className="space-y-3">
              {significantBalances.map((balance) => (
                <div key={balance.asset} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {balance.asset}
                      </div>
                      <div className="text-xs text-gray-500">
                        Free: {showBalances ? formatNumber(balance.free, 6) : '••••••'}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-2 text-sm">
                      <Lock className="w-3 h-3 text-gray-400" />
                      <span className="text-gray-600 dark:text-gray-300">
                        {showBalances ? formatNumber(balance.locked, 6) : '••••••'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {positions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No active positions
                </div>
              ) : (
                positions.map((position, index) => (
                  <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {position.symbol}
                        </span>
                        <span className={cn(
                          "px-2 py-1 rounded text-xs font-medium",
                          position.side === 'long' 
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                        )}>
                          {position.side.toUpperCase()}
                        </span>
                      </div>
                      <div className={cn(
                        "text-sm font-medium",
                        position.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      )}>
                        {position.pnl >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300">
                      <div>Size: {formatNumber(position.size, 6)}</div>
                      <div>Entry: {formatCurrency(position.entryPrice)}</div>
                      <div>Mark: {formatCurrency(position.markPrice)}</div>
                      <div>P&L: {formatCurrency(Math.abs(position.pnl))}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}