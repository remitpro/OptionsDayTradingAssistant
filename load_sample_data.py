
import os
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.data.database import init_db, get_session, TradeModel

def generate_sample_data():
    """Generate and insert sample trades into the database."""
    print("Initializing database...")
    init_db()
    
    session: Session = get_session()
    
    # Check if we already have data
    count = session.query(TradeModel).count()
    if count > 0:
        print(f"Database already has {count} records. Clearing old data...")
        session.query(TradeModel).delete()
        session.commit()
    
    print("Generating sample trades...")
    
    symbols = ['AAPL', 'MSFT', 'TSLA', 'SPY', 'QQQ', 'AMD', 'NVDA', 'AMZN', 'GOOGL', 'META']
    strategies = ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'IRON_CONDOR', 'CALL_CREDIT_SPREAD', 'PUT_CREDIT_SPREAD']
    biases = ['BULLISH', 'BEARISH', 'NEUTRAL']
    
    trades = []
    
    # Generate 50 sample trades over the last 10 days
    for i in range(50):
        symbol = random.choice(symbols)
        strategy = random.choice(strategies)
        bias = random.choice(biases)
        
        # Calculate random timestamp within last 10 days
        days_offset = random.randint(0, 10)
        hours_offset = random.randint(9, 16) # Market hours roughly
        minutes_offset = random.randint(0, 59)
        trade_time = datetime.now() - timedelta(days=days_offset)
        trade_time = trade_time.replace(hour=hours_offset, minute=minutes_offset)
        
        # Random metrics
        underlying_price = random.uniform(100, 500)
        max_loss = random.uniform(100, 500)
        max_gain = random.uniform(20, 100)
        pop = random.uniform(0.60, 0.90)
        score = random.uniform(60, 95)
        
        trade = TradeModel(
            symbol=symbol,
            strategy=strategy,
            bias=bias,
            status=random.choice(['OPEN', 'CLOSED', 'EXPIRED']),
            timestamp=trade_time,
            underlying_price=round(underlying_price, 2),
            max_loss=round(max_loss, 2),
            max_gain=round(max_gain, 2),
            risk_reward_ratio=round(max_loss / max_gain, 2) if max_gain > 0 else 0,
            probability_of_profit=round(pop, 4),
            score=round(score, 1),
            legs=[
                {"type": "short_put", "strike": round(underlying_price * 0.95, 2)},
                {"type": "long_put", "strike": round(underlying_price * 0.90, 2)}
            ],
            risk_metrics={
                "theta": random.uniform(0.5, 2.0),
                "delta": random.uniform(-0.1, 0.1),
            },
            explanation=f"Sample explanation for {symbol} {strategy}"
        )
        trades.append(trade)
    
    session.add_all(trades)
    session.commit()
    print(f"✅ Successfully inserted {len(trades)} sample trades.")
    
    session.close()

if __name__ == "__main__":
    generate_sample_data()
