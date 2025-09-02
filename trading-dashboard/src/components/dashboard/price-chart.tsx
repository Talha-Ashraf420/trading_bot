'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState, useMemo } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Bar
} from 'recharts'
import { format } from 'date-fns'

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
  timestamp: string
  type: 'buy' | 'sell'
  price: number
  quantity: number
}

interface PriceChartProps {
  data: PriceData[]
  trades?: Trade[]
  symbol?: string
}

const timeframes = [
  { label: '1H', value: '1h' },
  { label: '4H', value: '4h' },
  { label: '1D', value: '1d' },
  { label: '1W', value: '1w' },
]

export default function PriceChart({ data, trades = [], symbol = 'ETH/USDT' }: PriceChartProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState('1d')
  const [showVolume, setShowVolume] = useState(true)
  const [showTrades, setShowTrades] = useState(true)

  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp).getTime(),
      formattedTime: format(new Date(item.timestamp), 'HH:mm'),
      formattedDate: format(new Date(item.timestamp), 'MMM dd'),
    }))
  }, [data])

  const currentPrice = data[data.length - 1]?.price || 0
  const priceChange = data.length >= 2 ? currentPrice - data[data.length - 2].price : 0
  const priceChangePercent = data.length >= 2 ? (priceChange / data[data.length - 2].price) * 100 : 0

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {format(new Date(label), 'MMM dd, yyyy HH:mm')}
          </p>
          <p className="font-semibold text-gray-900 dark:text-white">
            Price: ${data.price.toFixed(2)}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Volume: {data.volume.toLocaleString()}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            High: ${data.high.toFixed(2)} | Low: ${data.low.toFixed(2)}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <span>{symbol}</span>
              <span className={`text-lg ${priceChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                ${currentPrice.toFixed(2)}
              </span>
              <span className={`text-sm ${priceChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                ({priceChange >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
              </span>
            </CardTitle>
          </div>
          
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
              {timeframes.map((tf) => (
                <Button
                  key={tf.value}
                  variant={selectedTimeframe === tf.value ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setSelectedTimeframe(tf.value)}
                  className="text-xs"
                >
                  {tf.label}
                </Button>
              ))}
            </div>
            
            <Button
              variant={showVolume ? "default" : "outline"}
              size="sm"
              onClick={() => setShowVolume(!showVolume)}
              className="text-xs"
            >
              Volume
            </Button>
            
            <Button
              variant={showTrades ? "default" : "outline"}
              size="sm"
              onClick={() => setShowTrades(!showTrades)}
              className="text-xs"
            >
              Trades
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="timestamp"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                stroke="#6B7280"
              />
              <YAxis 
                yAxisId="price"
                domain={['dataMin - 5', 'dataMax + 5']}
                stroke="#6B7280"
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              {showVolume && (
                <YAxis 
                  yAxisId="volume"
                  orientation="right"
                  stroke="#6B7280"
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                />
              )}
              <Tooltip content={<CustomTooltip />} />
              
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="price"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, stroke: '#3B82F6', fill: '#3B82F6' }}
              />
              
              {showVolume && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="#374151"
                  opacity={0.3}
                />
              )}
              
              {/* Trade markers */}
              {showTrades && trades.map((trade, index) => (
                <ReferenceLine
                  key={index}
                  x={new Date(trade.timestamp).getTime()}
                  stroke={trade.type === 'buy' ? '#10B981' : '#EF4444'}
                  strokeDasharray="5 5"
                  label={{
                    value: trade.type.toUpperCase(),
                    position: 'top',
                    fill: trade.type === 'buy' ? '#10B981' : '#EF4444'
                  }}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}