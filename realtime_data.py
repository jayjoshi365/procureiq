"""
Real-time data integration for ProcureIQ
Provides live market data, news feeds, and economic indicators
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

# Configuration
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")  # Free API key from alpha vantage
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")  # Free API key from newsapi.org

# Optional imports
try:
    import alpha_vantage
    _ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    alpha_vantage = None
    _ALPHA_VANTAGE_AVAILABLE = False

try:
    import newsapi
    _NEWSAPI_AVAILABLE = True
except ImportError:
    newsapi = None
    _NEWSAPI_AVAILABLE = False

class RealTimeDataProvider:
    """Provider for real-time market data and news."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key in self.cache:
            timestamp, _ = self.cache[key]
            return time.time() - timestamp < self.cache_ttl
        return False

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if self._is_cache_valid(key):
            _, data = self.cache[key]
            return data
        return None

    def _set_cache(self, key: str, data: Any):
        """Store data in cache."""
        self.cache[key] = (time.time(), data)

    def get_stock_quote(self, symbol: str) -> Dict:
        """
        Get real-time stock quote from Alpha Vantage.
        Returns current price, volume, and key metrics.
        """
        if not _ALPHA_VANTAGE_AVAILABLE or not ALPHA_VANTAGE_API_KEY:
            return {"error": "Alpha Vantage not available or API key not configured"}
        
        # Check cache first
        cache_key = f"quote_{symbol}"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "Global Quote" not in data:
                return {"error": "Invalid response from Alpha Vantage"}

            quote = data["Global Quote"]

            result = {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%"),
                "volume": int(quote.get("06. volume", 0)),
                "latest_trading_day": quote.get("07. latest trading day", ""),
                "previous_close": float(quote.get("08. previous close", 0)),
                "timestamp": datetime.now().isoformat()
            }

            self._set_cache(cache_key, result)
            return result

        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except (ValueError, KeyError) as e:
            return {"error": f"Data parsing failed: {str(e)}"}

    def get_company_overview(self, symbol: str) -> Dict:
        """
        Get detailed company overview including financial metrics.
        """
        if not _ALPHA_VANTAGE_AVAILABLE or not ALPHA_VANTAGE_API_KEY:
            return {"error": "Alpha Vantage not available or API key not configured"}
        
        cache_key = f"overview_{symbol}"

        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data or "Symbol" not in data:
                return {"error": "Company overview not found"}

            result = {
                "symbol": data.get("Symbol"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "market_cap": data.get("MarketCapitalization"),
                "pe_ratio": data.get("PERatio"),
                "peg_ratio": data.get("PEGRatio"),
                "dividend_yield": data.get("DividendYield"),
                "beta": data.get("Beta"),
                "52w_high": data.get("52WeekHigh"),
                "52w_low": data.get("52WeekLow"),
                "revenue_ttm": data.get("RevenueTTM"),
                "gross_margin_ttm": data.get("GrossMarginTTM"),
                "operating_margin_ttm": data.get("OperatingMarginTTM"),
                "net_income_ttm": data.get("NetIncomeTTM"),
                "eps": data.get("EPS"),
                "quarterly_earnings_growth": data.get("QuarterlyEarningsGrowthYOY"),
                "annual_earnings_growth": data.get("AnnualEarningsGrowthYOY"),
                "timestamp": datetime.now().isoformat()
            }

            self._set_cache(cache_key, result)
            return result

        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def get_market_news(self, query: str = "procurement OR supply chain", language: str = "en") -> List[Dict]:
        """
        Get recent market news related to procurement and supply chain.
        """
        if not _NEWSAPI_AVAILABLE or not NEWS_API_KEY:
            return [{"error": "NewsAPI not available or API key not configured"}]
        
        cache_key = f"news_{query}_{language}"

        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Get news from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language={language}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "ok":
                return [{"error": f"News API error: {data.get('message', 'Unknown error')}"}]

            articles = data.get("articles", [])[:10]  # Limit to 10 articles

            result = []
            for article in articles:
                result.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "author": article.get("author")
                })

            self._set_cache(cache_key, result)
            return result

        except requests.RequestException as e:
            return [{"error": f"News API request failed: {str(e)}"}]

    def get_economic_indicators(self) -> Dict:
        """
        Get key economic indicators that affect procurement decisions.
        """
        cache_key = "economic_indicators"

        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        # Using free APIs for economic data
        indicators = {}

        try:
            # Federal Reserve Economic Data (FRED) - requires API key
            # For demo, we'll use mock data or free alternatives

            # Mock economic indicators (in production, integrate with real APIs)
            indicators = {
                "usd_eur_rate": 0.85,  # Example EUR/USD rate
                "usd_gbp_rate": 0.73,  # Example GBP/USD rate
                "us_inflation_rate": 3.1,  # Example US inflation
                "commodity_price_index": 125.3,  # Example commodity prices
                "timestamp": datetime.now().isoformat(),
                "note": "Using mock data - integrate with real economic APIs for production"
            }

            self._set_cache(cache_key, indicators)
            return indicators

        except Exception as e:
            return {"error": f"Economic data fetch failed: {str(e)}"}

    def get_procurement_market_trends(self) -> Dict:
        """
        Get procurement-specific market trends and insights.
        """
        cache_key = "procurement_trends"

        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Combine multiple data sources
            news = self.get_market_news("procurement OR supply chain OR vendor")
            economic_data = self.get_economic_indicators()

            # Analyze trends from news
            trend_keywords = ["shortage", "inflation", "disruption", "price increase", "supply chain"]
            trend_analysis = {}

            for keyword in trend_keywords:
                count = 0
                for article in news:
                    if isinstance(article, dict):
                        title = article.get("title", "").lower()
                        description = article.get("description", "").lower()
                        if keyword.lower() in title or keyword.lower() in description:
                            count += 1
                trend_analysis[keyword] = count

            result = {
                "news_summary": news[:5],  # Top 5 articles
                "trend_analysis": trend_analysis,
                "economic_indicators": economic_data,
                "risk_level": "HIGH" if trend_analysis.get("disruption", 0) > 2 else "MEDIUM",
                "timestamp": datetime.now().isoformat()
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            return {"error": f"Trend analysis failed: {str(e)}"}


# Global instance
_realtime_provider = None

def get_realtime_provider() -> RealTimeDataProvider:
    """Get global real-time data provider instance."""
    global _realtime_provider
    if _realtime_provider is None:
        _realtime_provider = RealTimeDataProvider()
    return _realtime_provider


# Convenience functions
def get_live_stock_quote(symbol: str) -> Dict:
    """Get live stock quote for a symbol."""
    return get_realtime_provider().get_stock_quote(symbol)

def get_live_company_overview(symbol: str) -> Dict:
    """Get detailed company information."""
    return get_realtime_provider().get_company_overview(symbol)

def get_procurement_news() -> List[Dict]:
    """Get recent procurement-related news."""
    return get_realtime_provider().get_market_news()

def get_market_trends() -> Dict:
    """Get current market trends affecting procurement."""
    return get_realtime_provider().get_procurement_market_trends()
