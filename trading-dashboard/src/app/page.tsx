'use client'

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { tradingApi } from '@/lib/api'
import Sidebar from '@/components/layout/sidebar'
import PortfolioOverview from '@/components/dashboard/portfolio-overview'
import PriceChart from '@/components/dashboard/price-chart'
import TradeHistory from '@/components/dashboard/trade-history'
import PortfolioAnalytics from '@/components/dashboard/portfolio-analytics'
import BalanceDisplay from '@/components/dashboard/balance-display'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { RefreshCw, AlertCircle, Wifi, WifiOff } from 'lucide-react'

// Real-time data state interfaces
interface PriceData {
  timestamp: string
  price: number
  volume: number
  high: number
  low: number
  open: number
  close: number
}

interface Trade {
  id: string
  timestamp: string
  symbol: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  total: number
  pnl?: number
  pnlPercentage?: number
  strategy: string
  status: 'completed' | 'pending' | 'failed'
}

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true)
  const [portfolioStats, setPortfolioStats] = useState({
    totalBalance: 5000.0,
    totalPnL: 250.75,
    totalPnLPercentage: 5.25,
    dayPnL: 45.30,
    dayPnLPercentage: 0.95,
    activeTrades: 3,
    successRate: 73.5,
    totalTrades: 127,
  })
  const [priceData, setPriceData] = useState<PriceData[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [balances, setBalances] = useState<any[]>([])
  const [portfolioAnalytics, setPortfolioAnalytics] = useState<any>(null)

  const { isConnected, data: wsData, error: wsError } = useWebSocket()

  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true)
      try {
        // Load all data in parallel
        const [portfolioResponse, tradesResponse, balanceResponse, statusResponse] = await Promise.all([
          tradingApi.getPortfolio(),
          tradingApi.getTrades(),
          tradingApi.getBalance(),
          tradingApi.getBotStatus()
        ])

        // Update portfolio stats
        if (portfolioResponse.success && portfolioResponse.data) {
          const portfolio = portfolioResponse.data
          setPortfolioAnalytics(portfolio)
          
          // Generate mock price data based on current market
          const currentPrice = 2965 // Would come from market data API
          const mockPriceData = []
          for (let i = 6; i >= 0; i--) {
            const timestamp = new Date(Date.now() - i * 4 * 60 * 60 * 1000).toISOString()
            const price = currentPrice + (Math.random() - 0.5) * 100
            mockPriceData.push({
              timestamp,
              price: price,
              volume: 1500000 + Math.random() * 500000,
              high: price + 20,
              low: price - 20,
              open: price - 10,
              close: price
            })
          }
          setPriceData(mockPriceData)
        }

        // Update portfolio stats
        if (statusResponse.success && statusResponse.data) {
          const status = statusResponse.data
          setPortfolioStats(prev => ({
            ...prev,
            activeTrades: status.activeTrades,
            totalTrades: status.totalTrades,
            successRate: status.successRate || prev.successRate
          }))
        }

        if (portfolioResponse.success && portfolioResponse.data) {
          setPortfolioStats(prev => ({
            ...prev,
            totalBalance: portfolioResponse.data.totalValue,
            totalPnL: portfolioResponse.data.totalPnL,
            totalPnLPercentage: portfolioResponse.data.totalPnLPercentage,
            dayPnL: portfolioResponse.data.dayPnL,
            dayPnLPercentage: portfolioResponse.data.dayPnLPercentage,
          }))
        }

        // Update trades
        if (tradesResponse.success && tradesResponse.data) {
          setTrades(tradesResponse.data.trades)
        }

        // Update balances
        if (balanceResponse.success && balanceResponse.data) {
          setBalances(balanceResponse.data.balances)
        }

      } catch (error) {
        console.error('Failed to load initial data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadInitialData()
  }, [])

  const refreshData = async () => {
    setIsLoading(true)
    // Refresh all data
    setTimeout(() => setIsLoading(false), 1000)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      
      <div className="pl-0 lg:pl-64">
        <div className="p-4 lg:p-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trading Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Monitor your crypto trading bot performance in real-time
              </p>
            </div>
            
            <div className="flex items-center space-x-4 mt-4 sm:mt-0">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <div className="flex items-center space-x-2 text-green-600">
                    <Wifi className="w-4 h-4" />
                    <span className="text-sm">Connected</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 text-red-600">
                    <WifiOff className="w-4 h-4" />
                    <span className="text-sm">Disconnected</span>
                  </div>
                )}
              </div>

              {/* Bot Status */}
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600 dark:text-gray-300">Bot Active</span>
              </div>

              <Button 
                onClick={refreshData} 
                variant="outline" 
                size="sm"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Error Alert */}
          {wsError && (
            <Card className="mb-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-red-800 dark:text-red-200">
                    WebSocket connection error: {wsError}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-8">
            {/* Portfolio Overview */}
            <PortfolioOverview stats={portfolioStats} />

            {/* Price Chart */}
            <PriceChart 
              data={priceData}
              trades={trades}
              symbol="ETH/USDT"
            />

            {/* Balance and Positions */}
            <BalanceDisplay 
              balances={balances}
              positions={[]}
              totalBalance={portfolioStats.totalBalance}
              totalPnL={portfolioStats.totalPnL}
              isLoading={isLoading}
              onRefresh={refreshData}
            />

            {/* Portfolio Analytics */}
            {portfolioAnalytics && (
              <PortfolioAnalytics 
                portfolioHistory={portfolioAnalytics.portfolioHistory}
                assetAllocation={portfolioAnalytics.assetAllocation}
                strategyPerformance={portfolioAnalytics.strategyPerformance}
              />
            )}

            {/* Trade History */}
            <TradeHistory trades={trades} />
          </div>
        </div>
      </div>
    </div>
  )
}
