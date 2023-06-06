import random
from typing import List, Optional, Union

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from datetime import datetime


app = FastAPI()


class TradeDetails(BaseModel):
    buySellIndicator: str = Field(
        description="A value of BUY for buys, SELL for sells."
    )
    price: float = Field(description="The price of the Trade.")
    quantity: int = Field(description="The amount of units traded.")


class Trade(BaseModel):
    asset_class: Optional[str] = Field(
        alias="assetClass",
        default=None,
        description="The asset class of the instrument traded. E.g. Bond, Equity, FX...etc",
    )
    counterparty: Optional[str] = Field(
        default=None,
        description="The counterparty the trade was executed with. May not always be available",
    )
    instrument_id: str = Field(
        alias="instrumentId",
        description="The ISIN/ID of the instrument traded. E.g. TSLA, AAPL, AMZN...etc",
    )
    instrument_name: str = Field(
        alias="instrumentName", description="The name of the instrument traded."
    )
    trade_date_time: datetime = Field(
        alias="tradeDateTime", description="The date-time the Trade was executed"
    )
    trade_details: TradeDetails = Field(
        alias="tradeDetails",
        description="The details of the trade, i.e. price, quantity",
    )
    trade_id: str = Field(
        alias="tradeId", default=None, description="The unique ID of the trade"
    )
    trader: str = Field(description="The name of the Trader")


def generate_db():
    assetClasses = ["Equity", "Bond", "FX"]
    counterParties = [
        "ABC Bank",
        "XYZ Investment",
        "DEF Forex",
        "XYZ Bank",
        "PQR Investment",
    ]
    instrumentIds = ["TSLA", "AAPL", "EURUSD", "AMZN", "GOOG"]
    instrumentNames = ["Tesla", "Apple", "Euro/USD", "Amazon", "Google"]
    buySellIndicators = ["BUY", "SELL"]
    traders = [
        "John Doe",
        "Jane Smith",
        "Bob Johnson",
        "Alice Williams",
        "Robert Johnson",
    ]

    trades_db = []
    for i in range(100):
        trade = Trade(
            assetClass=assetClasses[random.randint(0, len(assetClasses) - 1)],
            counterparty=counterParties[random.randint(0, len(counterParties) - 1)],
            instrumentId=instrumentIds[random.randint(0, len(instrumentIds) - 1)],
            instrumentName=instrumentNames[random.randint(0, len(instrumentNames) - 1)],
            tradeDateTime=datetime(
                2022, random.randint(1, 12), random.randint(1, 28), 14, 30
            ),
            tradeDetails=TradeDetails(
                buySellIndicator=buySellIndicators[
                    random.randint(0, len(buySellIndicators) - 1)
                ],
                price=random.randint(1, 1000),
                quantity=random.randint(1, 50),
            ),
            tradeId=str(i),
            trader=traders[i % len(traders)],
        )
        trades_db.append(trade)
    return trades_db


trades_db: List[Trade] = generate_db()


@app.get("/trades")
def get_trades(
    asset_class: Optional[str] = Query(None, description="Asset class of the trade."),
    end: Optional[datetime] = Query(
        None, description="The maximum date for the tradeDateTime field."
    ),
    max_price: Optional[float] = Query(
        None, description="The maximum value for the tradeDetails.price field."
    ),
    min_price: Optional[float] = Query(
        None, description="The minimum value for the tradeDetails.price field."
    ),
    start: Optional[datetime] = Query(
        None, description="The minimum date for the tradeDateTime field."
    ),
    trade_type: Optional[str] = Query(
        None, description="The tradeDetails.buySellIndicator is a BUY or SELL"
    ),
    page: int = Query(1, description="The page number"),
    limit: int = Query(4, description="The number of trades per page"),
    sort: str = Query("desc", description="Ascending or descending by trade id"),
) -> dict:
    try:
        filtered_trades = trades_db
        if asset_class:
            filtered_trades = [
                trade for trade in filtered_trades if trade.asset_class == asset_class
            ]

        if end:
            filtered_trades = [
                trade for trade in filtered_trades if trade.trade_date_time <= end
            ]

        if max_price:
            filtered_trades = [
                trade
                for trade in filtered_trades
                if trade.trade_details.price <= max_price
            ]

        if min_price:
            filtered_trades = [
                trade
                for trade in filtered_trades
                if trade.trade_details.price >= min_price
            ]

        if start:
            filtered_trades = [
                trade for trade in filtered_trades if trade.trade_date_time >= start
            ]

        if trade_type:
            filtered_trades = [
                trade
                for trade in filtered_trades
                if trade.trade_details.buySellIndicator == trade_type
            ]

        total_trades = len(filtered_trades)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_trades = filtered_trades[start_index:end_index]

        reverse = sort.lower() == "desc"
        paginated_trades.sort(key=lambda trade: trade.trade_date_time, reverse=reverse)

        return {
            "total_count": total_trades,
            "page": page,
            "trades": paginated_trades,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/trades/id/{trade_id}")
def get_trade_by_id(trade_id: str) -> Union[Trade, dict]:
    print("Here")
    for trade in trades_db:
        if trade.trade_id == trade_id:
            return trade
    return {"error": "Trade not found"}


@app.get("/trades/search")
def search_trades(
    q: str = Query("", description="Type your query here"),
    page: int = Query(1, description="The page number"),
    limit: int = Query(4, description="The number of trades per page"),
    sort: str = Query("desc", description="The field to sort by"),
) -> Union[List[Trade], dict]:
    try:
        searched_trades: List[Trade] = []
        for trade in trades_db:
            if (
                (
                    trade.counterparty is not None
                    and q.lower() in trade.counterparty.lower()
                )
                or q.lower() in trade.instrument_id.lower()
                or q.lower() in trade.instrument_name.lower()
                or q.lower() in trade.trader.lower()
            ):
                searched_trades.append(trade)

        total_trades = len(searched_trades)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_trades = searched_trades[start_index:end_index]

        reverse = sort.lower() == "desc"
        paginated_trades.sort(key=lambda trade: trade.trade_date_time, reverse=reverse)

        return {
            "total_count": total_trades,
            "page": page,
            "trades": paginated_trades,
        }
    except Exception as e:
        return {"error": str(e)}
