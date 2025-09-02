# Trading Dashboard

A beautiful, modern Next.js dashboard for monitoring your cryptocurrency trading bot in real-time.

## Features

✅ **Real-time Dashboard** - Live updates via WebSocket connection
✅ **Portfolio Overview** - Track total balance, P&L, and performance metrics
✅ **Interactive Charts** - Price charts with trade markers and volume
✅ **Trade History** - Filterable table with search and pagination
✅ **Portfolio Analytics** - Profit/loss graphs and strategy performance
✅ **Balance Display** - Real-time account balances and positions
✅ **Responsive Design** - Works perfectly on desktop and mobile
✅ **Dark/Light Theme** - Toggle between themes with system preference
✅ **Modern UI** - Built with Tailwind CSS and shadcn/ui components

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Beautiful charts and data visualization
- **Socket.io** - Real-time WebSocket communication
- **Lucide React** - Beautiful icon library
- **Framer Motion** - Smooth animations (ready for implementation)

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3002](http://localhost:3002)

## Project Structure

```
trading-dashboard/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── api/               # API routes for backend communication
│   │   ├── layout.tsx         # Root layout with theme provider
│   │   └── page.tsx           # Main dashboard page
│   ├── components/
│   │   ├── dashboard/         # Dashboard-specific components
│   │   │   ├── portfolio-overview.tsx
│   │   │   ├── price-chart.tsx
│   │   │   ├── trade-history.tsx
│   │   │   ├── portfolio-analytics.tsx
│   │   │   └── balance-display.tsx
│   │   ├── layout/            # Layout components
│   │   │   └── sidebar.tsx
│   │   ├── ui/                # Reusable UI components
│   │   │   ├── card.tsx
│   │   │   └── button.tsx
│   │   ├── theme-provider.tsx
│   │   └── theme-toggle.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts    # WebSocket connection hook
│   └── lib/
│       ├── api.ts             # API service for backend communication
│       └── utils.ts           # Utility functions
└── package.json
```

## Dashboard Features

### 1. Portfolio Overview
- Total balance and P&L metrics
- Daily performance indicators
- Active trades and success rate
- Animated cards with trend indicators

### 2. Interactive Price Chart
- Real-time price data visualization
- Volume bars and multiple timeframes
- Trade markers showing buy/sell points
- Responsive design with custom tooltips

### 3. Trade History Table
- Filterable by type, status, and symbol
- Search functionality
- Pagination for large datasets
- Export capability (ready for implementation)

### 4. Portfolio Analytics
- Portfolio value over time
- Asset allocation pie chart
- Strategy performance comparison
- Profit/loss trends

### 5. Balance Display
- Real-time account balances
- Active positions overview
- Hide/show balance toggle
- Asset breakdown with 24h changes

## API Integration

The dashboard is designed to connect with your Python trading bot through:

- **HTTP API endpoints** for data fetching
- **WebSocket connection** for real-time updates
- **RESTful architecture** for easy integration

### Environment Variables

Create a `.env.local` file:
```env
TRADING_BOT_API_URL=http://localhost:5000
```

## Connecting to Your Trading Bot

1. **Set up API endpoints** in your Python bot:
   - `/api/status` - Bot status and uptime
   - `/api/balance` - Account balances
   - `/api/positions` - Active positions
   - `/api/trades` - Trade history
   - `/api/portfolio` - Portfolio analytics

2. **WebSocket events** for real-time updates:
   - `market_data` - Price updates
   - `trade_update` - New trades
   - `balance_update` - Balance changes
   - `bot_status` - Status updates

## Build for Production

```bash
npm run build
npm start
```

## Contributing

This dashboard is part of your trading bot project. Feel free to customize and extend it with additional features like:

- Advanced charting with TradingView integration
- Alert system for important events
- Strategy configuration UI
- Mobile app with push notifications
- Historical data analysis tools

## Support

The dashboard is designed to work seamlessly with your existing Python trading bot infrastructure. All components are modular and can be easily customized or extended.
