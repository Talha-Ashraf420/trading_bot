'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

export interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  high: number
  low: number
  timestamp: string
}

export interface TradeUpdate {
  id: string
  symbol: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  timestamp: string
  strategy: string
  status: 'completed' | 'pending' | 'failed'
}

export interface BalanceUpdate {
  asset: string
  free: number
  locked: number
  total: number
}

export interface BotStatus {
  isRunning: boolean
  uptime: number
  activeTrades: number
  totalTrades: number
  lastUpdate: string
}

interface WebSocketData {
  marketData: MarketData[]
  tradeUpdates: TradeUpdate[]
  balanceUpdates: BalanceUpdate[]
  botStatus: BotStatus | null
}

export function useWebSocket(url: string = 'ws://localhost:8000/ws') {
  const [isConnected, setIsConnected] = useState(false)
  const [data, setData] = useState<WebSocketData>({
    marketData: [],
    tradeUpdates: [],
    balanceUpdates: [],
    botStatus: null
  })
  const [error, setError] = useState<string | null>(null)
  
  const socketRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(url)

      socket.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
      }

      socket.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
      }

      socket.onerror = (err) => {
        console.error('WebSocket error:', err)
        setError('WebSocket connection error')
        setIsConnected(false)
      }

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          switch (message.type) {
            case 'market_data':
              setData(prev => ({
                ...prev,
                marketData: [message.data, ...prev.marketData.slice(0, 99)]
              }))
              break
            case 'trade_update':
              setData(prev => ({
                ...prev,
                tradeUpdates: [message.data, ...prev.tradeUpdates.slice(0, 49)]
              }))
              break
            case 'balance_update':
              setData(prev => ({
                ...prev,
                balanceUpdates: message.data
              }))
              break
            case 'bot_status':
              setData(prev => ({
                ...prev,
                botStatus: message.data
              }))
              break
            default:
              console.log('Unknown message type:', message.type)
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      socketRef.current = socket

    } catch (err) {
      console.error('WebSocket connection error:', err)
      setError(err instanceof Error ? err.message : 'Connection failed')
    }
  }, [url])

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
      setIsConnected(false)
    }
  }, [])

  // Send message to server
  const sendMessage = useCallback((event: string, data: any) => {
    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify({ type: event, data }))
    }
  }, [isConnected])

  // Subscribe to specific symbol updates
  const subscribeToSymbol = useCallback((symbol: string) => {
    sendMessage('subscribe_symbol', { symbol })
  }, [sendMessage])

  // Unsubscribe from symbol updates
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    sendMessage('unsubscribe_symbol', { symbol })
  }, [sendMessage])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    data,
    error,
    connect,
    disconnect,
    sendMessage,
    subscribeToSymbol,
    unsubscribeFromSymbol
  }
}