'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatCurrency, formatPercentage, getColorForPnL, cn } from '@/lib/utils'
import { format } from 'date-fns'
import { ChevronLeft, ChevronRight, Filter, Download, Search } from 'lucide-react'

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

interface TradeHistoryProps {
  trades: Trade[]
}

export default function TradeHistory({ trades }: TradeHistoryProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [filterType, setFilterType] = useState<'all' | 'buy' | 'sell'>('all')
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'pending' | 'failed'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const itemsPerPage = 10

  const filteredTrades = useMemo(() => {
    return trades.filter(trade => {
      const matchesType = filterType === 'all' || trade.type === filterType
      const matchesStatus = filterStatus === 'all' || trade.status === filterStatus
      const matchesSearch = trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          trade.strategy.toLowerCase().includes(searchTerm.toLowerCase())
      return matchesType && matchesStatus && matchesSearch
    })
  }, [trades, filterType, filterStatus, searchTerm])

  const paginatedTrades = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    return filteredTrades.slice(startIndex, startIndex + itemsPerPage)
  }, [filteredTrades, currentPage])

  const totalPages = Math.ceil(filteredTrades.length / itemsPerPage)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20'
      case 'pending': return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20'
      case 'failed': return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20'
      default: return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20'
    }
  }

  const getTypeColor = (type: string) => {
    return type === 'buy' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <CardTitle>Trade History</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search trades..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
            >
              <option value="all">All Types</option>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Date</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Symbol</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Type</th>
                <th className="text-right py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Quantity</th>
                <th className="text-right py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Price</th>
                <th className="text-right py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Total</th>
                <th className="text-right py-3 px-2 font-medium text-gray-600 dark:text-gray-300">P&L</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Strategy</th>
                <th className="text-center py-3 px-2 font-medium text-gray-600 dark:text-gray-300">Status</th>
              </tr>
            </thead>
            <tbody>
              {paginatedTrades.map((trade) => (
                <tr key={trade.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="py-3 px-2 text-sm text-gray-900 dark:text-white">
                    {format(new Date(trade.timestamp), 'MMM dd, HH:mm')}
                  </td>
                  <td className="py-3 px-2 text-sm font-medium text-gray-900 dark:text-white">
                    {trade.symbol}
                  </td>
                  <td className="py-3 px-2">
                    <span className={cn("text-sm font-medium uppercase", getTypeColor(trade.type))}>
                      {trade.type}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-sm text-right text-gray-900 dark:text-white">
                    {trade.quantity.toFixed(6)}
                  </td>
                  <td className="py-3 px-2 text-sm text-right text-gray-900 dark:text-white">
                    {formatCurrency(trade.price)}
                  </td>
                  <td className="py-3 px-2 text-sm text-right text-gray-900 dark:text-white">
                    {formatCurrency(trade.total)}
                  </td>
                  <td className="py-3 px-2 text-sm text-right">
                    {trade.pnl !== undefined ? (
                      <div className="flex flex-col items-end">
                        <span className={getColorForPnL(trade.pnl)}>
                          {formatCurrency(Math.abs(trade.pnl))}
                        </span>
                        {trade.pnlPercentage !== undefined && (
                          <span className={cn("text-xs", getColorForPnL(trade.pnl))}>
                            {formatPercentage(trade.pnlPercentage)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-sm text-gray-600 dark:text-gray-300">
                    {trade.strategy}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-xs font-medium",
                      getStatusColor(trade.status)
                    )}>
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-600 dark:text-gray-300">
              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredTrades.length)} of {filteredTrades.length} trades
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}