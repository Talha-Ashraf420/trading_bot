import { NextRequest, NextResponse } from 'next/server'

// This would connect to your Python trading bot's API
const TRADING_BOT_API_URL = process.env.TRADING_BOT_API_URL || 'http://localhost:5000'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const endpoint = searchParams.get('endpoint')

  try {
    let url = `${TRADING_BOT_API_URL}/api`
    
    switch (endpoint) {
      case 'status':
        url += '/status'
        break
      case 'balance':
        url += '/balance'
        break
      case 'positions':
        url += '/positions'
        break
      case 'trades':
        url += '/trades'
        break
      case 'portfolio':
        url += '/portfolio'
        break
      default:
        return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 })
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Trading API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch data from trading bot' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, ...params } = body

    let url = `${TRADING_BOT_API_URL}/api`
    
    switch (action) {
      case 'start':
        url += '/start'
        break
      case 'stop':
        url += '/stop'
        break
      case 'restart':
        url += '/restart'
        break
      case 'place_order':
        url += '/order'
        break
      case 'cancel_order':
        url += '/order/cancel'
        break
      case 'update_config':
        url += '/config'
        break
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Trading API error:', error)
    return NextResponse.json(
      { error: 'Failed to execute action on trading bot' },
      { status: 500 }
    )
  }
}