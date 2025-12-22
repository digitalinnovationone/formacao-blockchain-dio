"""
Data Collector for Polymarket SOL 15-min Markets
Collects historical market data and price history from Polymarket API

IMPORTANT: SOL Up/Down 15-min markets are EVENTS containing multiple MARKETS.
- Use /events endpoint to find event containers
- Each event has multiple markets (time windows like 8:45, 9:00, 9:15, etc.)
- Extract individual markets from within events
"""

import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging
from typing import Optional, List, Dict, Any
import re

from config import settings

logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)


class DataCollector:
    """Collector for Polymarket market data."""

    def __init__(self):
        self.gamma_api = settings.GAMMA_API_BASE
        self.clob_api = settings.CLOB_API_BASE
        self.rate_limit = settings.MAX_REQUESTS_PER_SECOND
        self.last_request_time = 0
        self.client = httpx.Client(timeout=settings.REQUEST_TIMEOUT)

    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        wait_time = 1.0 / self.rate_limit - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def fetch_event_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single event by its slug.

        Args:
            slug: Event slug (e.g., "sol-updown-15m-1765676700")

        Returns:
            Event data with markets inside, or None
        """
        self._rate_limit_wait()

        try:
            response = self.client.get(
                f"{self.gamma_api}/events/slug/{slug}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Error fetching event {slug}: {e}")
            return None

    def fetch_sol_events(
        self,
        start_date: str,
        end_date: str,
        max_events: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch SOL Up/Down 15-min events.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_events: Maximum number of events to fetch

        Returns:
            List of event dictionaries
        """
        logger.info(f"Fetching SOL 15-min events from {start_date} to {end_date}")

        all_events = []
        offset = 0
        limit = 100

        # Strategy 1: Search events with slug containing sol-updown
        search_strategies = [
            {"slug_contains": "sol-updown-15m", "limit": limit},
            {"slug_contains": "sol-updown", "limit": limit},
            {"tag": "solana", "limit": limit},
        ]

        for strategy in search_strategies:
            if all_events:
                break

            logger.info(f"Trying events search: {strategy}")
            offset = 0

            while len(all_events) < max_events:
                self._rate_limit_wait()

                params = strategy.copy()
                params["offset"] = offset

                try:
                    response = self.client.get(
                        f"{self.gamma_api}/events",
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    logger.error(f"Error fetching events: {e}")
                    break

                events = data if isinstance(data, list) else data.get("data", [])

                if not events:
                    break

                # Filter for SOL Up/Down events
                for event in events:
                    slug = (event.get("slug") or "").lower()
                    title = (event.get("title") or "").lower()

                    is_sol_updown = any([
                        "sol-updown" in slug,
                        "sol updown" in slug,
                        "solana" in title and "up" in title and "down" in title,
                    ])

                    if is_sol_updown:
                        # Check if not duplicate
                        event_id = event.get("id")
                        if not any(e.get("id") == event_id for e in all_events):
                            all_events.append(event)
                            if len(all_events) <= 3:
                                logger.info(f"Found event: {event.get('title', slug)[:60]}...")

                offset += limit

                if len(events) < limit:
                    break

                if offset % 500 == 0:
                    logger.info(f"Checked {offset} events, found {len(all_events)} SOL events")

        logger.info(f"Total SOL events found: {len(all_events)}")
        return all_events

    def extract_markets_from_events(
        self,
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract individual markets from events.

        Args:
            events: List of event dictionaries

        Returns:
            List of market dictionaries
        """
        all_markets = []

        for event in events:
            # Markets can be nested in the event or need separate fetch
            markets = event.get("markets", [])

            if not markets:
                # Try to fetch event details to get markets
                event_slug = event.get("slug")
                if event_slug:
                    event_details = self.fetch_event_by_slug(event_slug)
                    if event_details:
                        markets = event_details.get("markets", [])

            for market in markets:
                market_data = self._parse_market(market)
                if market_data:
                    market_data["event_id"] = event.get("id")
                    market_data["event_slug"] = event.get("slug")
                    all_markets.append(market_data)

        logger.info(f"Extracted {len(all_markets)} markets from {len(events)} events")
        return all_markets

    def fetch_sol_15min_markets(
        self,
        start_date: str,
        end_date: str,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch all SOL Up/Down 15-minute markets in the date range.

        This method:
        1. Fetches SOL Up/Down events from /events endpoint
        2. Extracts individual markets from each event
        3. Filters by date range

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            save_path: Optional path to save CSV

        Returns:
            DataFrame with market information
        """
        logger.info(f"Fetching SOL 15-min markets from {start_date} to {end_date}")

        # Step 1: Fetch events
        events = self.fetch_sol_events(start_date, end_date)

        if not events:
            logger.warning("No SOL events found. Trying direct market search as fallback...")
            return self._fetch_markets_fallback(start_date, end_date, save_path)

        # Step 2: Extract markets from events
        all_markets = self.extract_markets_from_events(events)

        if not all_markets:
            logger.warning("No markets extracted from events.")
            return pd.DataFrame()

        # Step 3: Create DataFrame and filter by date
        df = pd.DataFrame(all_markets)

        # Parse dates
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
        df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')

        # Remove rows with invalid dates
        df = df.dropna(subset=['start_time'])

        # Filter by date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df['start_time'] >= start) & (df['start_time'] <= end)]

        # Sort by start time
        df = df.sort_values('start_time').reset_index(drop=True)

        logger.info(f"Total markets after date filter: {len(df)}")

        if save_path and not df.empty:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(save_path, index=False)
            logger.info(f"Saved to {save_path}")

        return df

    def _fetch_markets_fallback(
        self,
        start_date: str,
        end_date: str,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fallback: Try to fetch markets directly (old method).
        """
        logger.info("Using fallback market search...")

        all_markets = []
        offset = 0
        max_pages = 100

        for page in range(max_pages):
            self._rate_limit_wait()

            try:
                response = self.client.get(
                    f"{self.gamma_api}/markets",
                    params={"closed": "true", "limit": 100, "offset": offset}
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Error in fallback: {e}")
                break

            markets = data if isinstance(data, list) else data.get("data", [])

            if not markets:
                break

            for market in markets:
                question = (market.get("question") or "").lower()
                slug = (market.get("slug") or "").lower()

                is_sol = "solana" in question or "sol" in slug
                is_updown = "up" in question and "down" in question

                if is_sol and is_updown:
                    market_data = self._parse_market(market)
                    if market_data:
                        all_markets.append(market_data)

            offset += 100

            if len(markets) < 100:
                break

        df = pd.DataFrame(all_markets)

        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
            df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
            df = df.dropna(subset=['start_time'])

            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['start_time'] >= start) & (df['start_time'] <= end)]
            df = df.sort_values('start_time').reset_index(drop=True)

            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(save_path, index=False)

        return df

    def _parse_market(self, market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse market data into standardized format."""
        try:
            tokens = market.get("tokens", [])

            # Try different token structures
            yes_token = None
            no_token = None

            for t in tokens:
                outcome = (t.get("outcome") or "").lower()
                if outcome == "yes" or outcome == "up":
                    yes_token = t
                elif outcome == "no" or outcome == "down":
                    no_token = t

            # Also check clobTokenIds
            clob_tokens = market.get("clobTokenIds", [])

            return {
                "market_id": market.get("id") or market.get("conditionId") or market.get("condition_id"),
                "condition_id": market.get("conditionId") or market.get("condition_id"),
                "question": market.get("question") or market.get("title"),
                "slug": market.get("slug"),
                "start_time": market.get("startDate") or market.get("start_date") or market.get("createdAt"),
                "end_time": market.get("endDate") or market.get("end_date") or market.get("closedAt"),
                "outcome": market.get("outcome") or market.get("resolution"),
                "yes_token_id": yes_token.get("token_id") if yes_token else (clob_tokens[0] if clob_tokens else None),
                "no_token_id": no_token.get("token_id") if no_token else (clob_tokens[1] if len(clob_tokens) > 1 else None),
                "volume": float(market.get("volume", 0) or 0),
                "liquidity": float(market.get("liquidity", 0) or 0),
            }
        except Exception as e:
            logger.warning(f"Error parsing market: {e}")
            return None

    def fetch_price_history(
        self,
        token_id: str,
        start_ts: int,
        end_ts: int,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Fetch price history for a token.

        Args:
            token_id: Token ID to fetch prices for
            start_ts: Start timestamp (Unix)
            end_ts: End timestamp (Unix)
            interval: Price interval (1m, 5m, 1h, etc.)

        Returns:
            DataFrame with price history
        """
        self._rate_limit_wait()

        try:
            response = self.client.get(
                f"{self.clob_api}/prices-history",
                params={
                    "market": token_id,
                    "interval": interval,
                    "fidelity": 60,
                    "startTs": start_ts,
                    "endTs": end_ts,
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data or "history" not in data:
                return pd.DataFrame()

            history = data["history"]
            df = pd.DataFrame(history)

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['t'], unit='s')
                df['price'] = df['p'].astype(float)
                df = df[['timestamp', 'price']]

            return df

        except Exception as e:
            logger.warning(f"Error fetching price history for {token_id}: {e}")
            return pd.DataFrame()

    def fetch_all_prices(
        self,
        markets_df: pd.DataFrame,
        save_dir: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch price history for all markets.

        Args:
            markets_df: DataFrame with market information
            save_dir: Optional directory to save individual price CSVs

        Returns:
            Consolidated DataFrame with all prices
        """
        all_prices = []

        for idx, market in markets_df.iterrows():
            logger.info(f"Fetching prices for market {idx + 1}/{len(markets_df)}")

            start_ts = int(pd.to_datetime(market['start_time']).timestamp())
            end_ts = int(pd.to_datetime(market['end_time']).timestamp())

            # Fetch YES prices
            yes_prices = self.fetch_price_history(
                market['yes_token_id'], start_ts, end_ts
            )
            if not yes_prices.empty:
                yes_prices['price_yes'] = yes_prices['price']

            # Fetch NO prices
            no_prices = self.fetch_price_history(
                market['no_token_id'], start_ts, end_ts
            )
            if not no_prices.empty:
                no_prices['price_no'] = no_prices['price']

            # Merge YES and NO prices
            if not yes_prices.empty and not no_prices.empty:
                prices = pd.merge(
                    yes_prices[['timestamp', 'price_yes']],
                    no_prices[['timestamp', 'price_no']],
                    on='timestamp',
                    how='outer'
                )
                prices['market_id'] = market['market_id']
                prices['spread'] = prices['price_yes'] + prices['price_no'] - 1.0
                prices['mid_price'] = (prices['price_yes'] + (1 - prices['price_no'])) / 2

                all_prices.append(prices)

                if save_dir:
                    save_path = Path(save_dir) / f"{market['market_id']}.csv"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    prices.to_csv(save_path, index=False)

        if all_prices:
            consolidated = pd.concat(all_prices, ignore_index=True)
            return consolidated

        return pd.DataFrame()

    def close(self):
        """Close the HTTP client."""
        self.client.close()


def main():
    """Main function to collect data."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect Polymarket SOL data")
    parser.add_argument("--asset", default="SOL", help="Asset to collect")
    parser.add_argument("--days", type=int, default=90, help="Days of history")
    args = parser.parse_args()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    collector = DataCollector()

    try:
        # Fetch markets
        markets_df = collector.fetch_sol_15min_markets(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            save_path=f"{settings.DATA_RAW_PATH}/sol_markets.csv"
        )

        if not markets_df.empty:
            # Fetch prices
            prices_df = collector.fetch_all_prices(
                markets_df,
                save_dir=f"{settings.DATA_RAW_PATH}/price_history"
            )

            if not prices_df.empty:
                # Save consolidated prices
                prices_df.to_parquet(
                    f"{settings.DATA_PROCESSED_PATH}/all_prices.parquet",
                    index=False
                )
                logger.info("Data collection complete!")

    finally:
        collector.close()


if __name__ == "__main__":
    main()
