"""
Halol Crypto AI - Education Module
Offline educational content. No external AI APIs required.
"""

from typing import Dict, List, Optional

# ─── Lesson Categories ────────────────────────────────────────────────────────

CATEGORIES = {
    "basics":      "📚 Crypto Basics",
    "ta":          "📈 Technical Analysis",
    "candles":     "🕯 Candlestick Patterns",
    "indicators":  "📊 Indicators",
    "smc":         "🏦 Smart Money Concepts",
    "risk":        "⚠️ Risk Management",
    "faq":         "❓ FAQ",
}

# ─── Lessons ──────────────────────────────────────────────────────────────────

LESSONS: Dict[str, Dict] = {

    # ── Crypto Basics ──────────────────────────────────────────────────────

    "what_is_bitcoin": {
        "category": "basics",
        "title":    "What is Bitcoin?",
        "emoji":    "₿",
        "content":  """
<b>₿ What is Bitcoin?</b>

Bitcoin (BTC) is the world's first decentralized digital currency, created in 2009 by an anonymous person or group known as <b>Satoshi Nakamoto</b>.

<b>Key Properties:</b>
• <b>Decentralized</b> — No bank or government controls it
• <b>Limited Supply</b> — Only 21 million BTC will ever exist
• <b>Peer-to-peer</b> — Send directly to anyone, anywhere
• <b>Transparent</b> — All transactions are publicly recorded
• <b>Immutable</b> — Transactions cannot be reversed

<b>Why is Bitcoin valuable?</b>
Bitcoin has value because it is scarce (like gold), useful (fast international transfers), and increasingly trusted by institutions.

<b>Halal perspective:</b>
Spot Bitcoin ownership — buying and holding real BTC — is generally considered permissible by many Islamic scholars, as it has utility and real value. Always consult your own scholar for personal rulings.

<b>Current Use Cases:</b>
✅ Store of value (digital gold)
✅ Cross-border payments
✅ Inflation hedge
✅ Institutional investment
""",
    },

    "what_is_blockchain": {
        "category": "basics",
        "title":    "What is Blockchain?",
        "emoji":    "🔗",
        "content":  """
<b>🔗 What is Blockchain?</b>

A blockchain is a <b>distributed ledger</b> — a shared record book that is maintained by thousands of computers worldwide rather than one central authority.

<b>How it works:</b>
1️⃣ A transaction is requested (e.g. send 1 BTC)
2️⃣ The transaction is broadcast to a network of computers (nodes)
3️⃣ Nodes validate the transaction using consensus rules
4️⃣ The transaction is combined with others into a <b>block</b>
5️⃣ The block is added to the <b>chain</b> of previous blocks
6️⃣ The transaction is now permanent and irreversible

<b>Key Properties:</b>
• <b>Immutable</b> — Once written, cannot be changed
• <b>Transparent</b> — Anyone can verify transactions
• <b>Secure</b> — Protected by cryptography and consensus
• <b>Decentralized</b> — No single point of failure

<b>Beyond Bitcoin:</b>
Ethereum uses blockchain to run <b>smart contracts</b> — self-executing programs with no middlemen.
""",
    },

    "what_is_spot_trading": {
        "category": "basics",
        "title":    "What is Spot Trading?",
        "emoji":    "🛒",
        "content":  """
<b>🛒 What is Spot Trading?</b>

Spot trading means <b>buying and owning the actual asset immediately</b> at the current market price.

<b>Example:</b>
You buy 0.1 BTC for $6,000. You now <b>own</b> 0.1 real Bitcoin in your wallet.

<b>Why Spot Trading is Halal:</b>
✅ You own the real asset
✅ No borrowed money (no riba/interest)
✅ No leverage (not betting more than you have)
✅ No short selling (not profiting from decline)
✅ Real value exchange

<b>Spot vs Futures (what we AVOID):</b>
❌ Futures = contracts on future price (speculative)
❌ Leverage = borrowing to trade larger (riba)
❌ Short selling = profiting from price decline

<b>Halol Crypto AI only analyzes spot opportunities.</b>
We never recommend futures, leverage, or short positions.
""",
    },

    # ── Technical Analysis ─────────────────────────────────────────────────

    "what_is_rsi": {
        "category": "indicators",
        "title":    "What is RSI?",
        "emoji":    "📉",
        "content":  """
<b>📉 What is RSI (Relative Strength Index)?</b>

RSI is a momentum indicator that measures the <b>speed and magnitude of price movements</b>, scaled from 0 to 100.

<b>How to read RSI:</b>
• <b>RSI &lt; 30</b> → Oversold (potential buy opportunity)
• <b>RSI 30–70</b> → Neutral zone
• <b>RSI &gt; 70</b> → Overbought (exercise caution)

<b>Optimal Buy Zone for Halal Investors:</b>
RSI between <b>40–65</b> offers the best risk/reward entry in an uptrend.

<b>RSI Divergence:</b>
If price makes a new low but RSI makes a higher low → <b>Bullish Divergence</b> — potential reversal signal!

<b>Formula (simplified):</b>
RSI = 100 – (100 ÷ (1 + Average Gain ÷ Average Loss))
over 14 periods

<b>Tip:</b>
RSI alone is not enough. Always combine with trend, EMA, and volume confirmation.
""",
    },

    "what_is_macd": {
        "category": "indicators",
        "title":    "What is MACD?",
        "emoji":    "📊",
        "content":  """
<b>📊 What is MACD?</b>

MACD (Moving Average Convergence Divergence) shows the <b>relationship between two EMAs</b> to identify trend direction and momentum.

<b>Components:</b>
• <b>MACD Line</b> = EMA(12) – EMA(26)
• <b>Signal Line</b> = EMA(9) of MACD Line
• <b>Histogram</b> = MACD Line – Signal Line

<b>Signals:</b>
🟢 <b>Bullish Crossover:</b> MACD crosses ABOVE signal line → Buy
🔴 <b>Bearish Crossover:</b> MACD crosses BELOW signal line → Caution
📊 <b>Histogram growing positive</b> → Momentum building

<b>MACD Above Zero:</b>
When MACD line is above zero, the short-term average is above the long-term average → bullish trend.

<b>Best Use:</b>
MACD works best on the <b>4H and 1D timeframes</b> for swing trading decisions.
""",
    },

    "what_is_ema": {
        "category": "indicators",
        "title":    "What is EMA?",
        "emoji":    "📈",
        "content":  """
<b>📈 What is EMA (Exponential Moving Average)?</b>

EMA is a moving average that gives <b>more weight to recent prices</b>, making it more responsive to new information than a simple average.

<b>Key EMAs used in Halol Crypto AI:</b>
• <b>EMA 20</b> — Short-term trend (responsive)
• <b>EMA 50</b> — Medium-term trend
• <b>EMA 200</b> — Long-term trend (the "golden line")

<b>The Golden Setup (Bull Alignment):</b>
Price &gt; EMA20 &gt; EMA50 &gt; EMA200 = <b>Strong Uptrend</b> ✅

<b>EMA as Support:</b>
In a strong uptrend, price often bounces off EMA20 or EMA50 — these become <b>dynamic support levels</b>.

<b>EMA200 Strategy:</b>
• Price crossing ABOVE EMA200 = long-term bull signal
• Price pulling back to EMA200 in uptrend = potential buy zone

<b>Tip:</b>
Multiple EMAs in alignment (all pointing up, price above all) = highest confidence setup.
""",
    },

    "what_is_atr": {
        "category": "indicators",
        "title":    "What is ATR?",
        "emoji":    "📏",
        "content":  """
<b>📏 What is ATR (Average True Range)?</b>

ATR measures <b>market volatility</b> — how much a price typically moves in a given period.

<b>Calculation:</b>
ATR = Average of the True Range over 14 periods
True Range = Max of:
  • High – Low
  • |High – Previous Close|
  • |Low – Previous Close|

<b>How Halol uses ATR:</b>
• Set Stop Loss: Entry – 1.5× ATR (gives room to breathe)
• Set Take Profit: Entry + 2–4× ATR
• Gauge position size based on volatility

<b>High ATR:</b> Market is volatile → wider stops needed → smaller position size
<b>Low ATR:</b> Market is quiet → tighter stops OK → can take more

<b>Example:</b>
BTC at $50,000. ATR = $1,500.
Stop Loss = $50,000 – $2,250 = $47,750
TP1 = $50,000 + $2,250 = $52,250
TP2 = $50,000 + $3,750 = $53,750
""",
    },

    "what_is_adx": {
        "category": "indicators",
        "title":    "What is ADX?",
        "emoji":    "💪",
        "content":  """
<b>💪 What is ADX (Average Directional Index)?</b>

ADX measures the <b>strength</b> of a trend, not its direction. It ranges from 0 to 100.

<b>ADX Values:</b>
• <b>0–20</b> → Weak trend or ranging
• <b>20–25</b> → Trend forming
• <b>25–50</b> → Strong trend ✅
• <b>50+</b> → Very strong trend (rare)

<b>Components:</b>
• <b>+DI</b> — Bullish pressure
• <b>-DI</b> — Bearish pressure
• <b>ADX</b> — Strength of the dominant direction

<b>Best Buy Signal:</b>
ADX &gt; 25 AND +DI &gt; -DI = Strong uptrend confirmed ✅

<b>When NOT to enter:</b>
ADX &lt; 20 = ranging market. Breakouts are often fake.

<b>Tip:</b>
Use ADX to <b>confirm</b> other signals. Don't trade MACD crossovers in low-ADX environments.
""",
    },

    "what_is_bollinger": {
        "category": "indicators",
        "title":    "What is Bollinger Bands?",
        "emoji":    "🎯",
        "content":  """
<b>🎯 What are Bollinger Bands?</b>

Bollinger Bands consist of three lines around a 20-period SMA:
• <b>Upper Band</b> = SMA + 2 standard deviations
• <b>Middle Band</b> = SMA (20-period)
• <b>Lower Band</b> = SMA – 2 standard deviations

<b>Key Concepts:</b>

🔵 <b>BB Squeeze:</b> When bands contract = low volatility = <b>breakout incoming</b>

🟢 <b>Lower Band Touch:</b> In an uptrend, touching lower band = buy opportunity

🟡 <b>Upper Band Touch:</b> Price extended — take profits, not a new buy

<b>%B Indicator:</b>
• %B below 0.3 = near lower band = buy zone
• %B above 0.7 = near upper band = caution

<b>The "Squeeze Play":</b>
When bands are very tight (squeezing), a major move is coming. Watch for volume increase to confirm direction.
""",
    },

    # ── Support & Resistance ───────────────────────────────────────────────

    "what_is_support": {
        "category": "ta",
        "title":    "What is Support?",
        "emoji":    "🟩",
        "content":  """
<b>🟩 What is Support?</b>

Support is a <b>price level where buying pressure is strong enough</b> to prevent further price decline — like a floor.

<b>Why Support Forms:</b>
• Buyers previously entered at this price
• They will defend their positions if price returns
• Institutions accumulate at key levels

<b>How to Identify Support:</b>
1. Look for previous <b>swing lows</b>
2. Areas with <b>high volume</b> historically
3. Psychological round numbers ($50,000, $40,000)
4. Previous resistance flipped to support

<b>Support as Buy Zone:</b>
When price returns to a strong support level in an uptrend, it often bounces. This is a <b>high-probability entry point</b>.

<b>Support Flip:</b>
When price breaks below support, that level becomes <b>new resistance</b>.

<b>Tips:</b>
• The more times support holds, the stronger it is
• A bounce from support + high volume = confirmation
• Never put stop loss exactly at support — give it room
""",
    },

    "what_is_resistance": {
        "category": "ta",
        "title":    "What is Resistance?",
        "emoji":    "🟥",
        "content":  """
<b>🟥 What is Resistance?</b>

Resistance is a <b>price level where selling pressure overcomes buying pressure</b> — like a ceiling.

<b>Why Resistance Forms:</b>
• Previous buyers who bought higher are waiting to "break even"
• Sellers who missed the top want to exit at that price
• Institutions distribute (sell) at key levels

<b>Resistance Breakout:</b>
When price breaks ABOVE resistance with strong volume:
• The resistance becomes new <b>support</b>
• Often leads to a significant move up
• This is the <b>Breakout Retest</b> strategy

<b>Take Profit Zones:</b>
Halol uses resistance levels as <b>Take Profit 1, 2, and 3 targets</b>.

<b>Key Levels to Watch:</b>
• Previous all-time highs
• Previous major swing highs
• Round psychological numbers
• Bollinger Band upper band
""",
    },

    # ── Smart Money Concepts ───────────────────────────────────────────────

    "what_is_order_block": {
        "category": "smc",
        "title":    "What is an Order Block?",
        "emoji":    "🏦",
        "content":  """
<b>🏦 What is an Order Block?</b>

An Order Block (OB) is the <b>last opposing candle before a strong impulsive move</b>. It represents where institutions (banks, funds) placed large orders.

<b>Bullish Order Block:</b>
The last <b>bearish candle</b> before a strong upward move.
→ Price often returns to this zone for a bounce.

<b>Bearish Order Block:</b>
The last <b>bullish candle</b> before a strong downward move.
→ If price returns, it may continue falling.

<b>How to Trade Bullish OBs:</b>
1. Identify the last red candle before a major pump
2. Mark its high and low
3. Wait for price to return to this zone
4. Look for confirmation (volume, RSI, MACD)
5. Enter with stop below the Order Block low

<b>Why It Works:</b>
Institutions need to fill large orders. They return to their order blocks to "pick up" remaining liquidity. This creates reliable bounce zones.

<b>Tip:</b>
Order Blocks on higher timeframes (4H, 1D) are more powerful than lower timeframes.
""",
    },

    "what_is_fvg": {
        "category": "smc",
        "title":    "What is Fair Value Gap?",
        "emoji":    "⚡",
        "content":  """
<b>⚡ What is a Fair Value Gap (FVG)?</b>

A Fair Value Gap is a <b>price imbalance</b> — an area where price moved so fast that it left a gap between the wicks of two candles.

<b>How it forms:</b>
• Candle 1: Has a high (e.g. $100)
• Candle 2: Large body, moves fast
• Candle 3: Has a low (e.g. $105)
• Gap from $100 to $105 = FVG

<b>Bullish FVG:</b>
Gap where the low of candle 3 &gt; high of candle 1.
Price tends to return and fill this gap, providing a buy opportunity.

<b>Why Price Returns to FVGs:</b>
Markets are efficient over time. Price fills imbalances (gaps) because orders were never properly executed at those levels.

<b>Trading Strategy:</b>
1. Identify a Bullish FVG in an uptrend
2. Wait for price to pull back into the FVG zone
3. Enter when price shows reversal signs
4. Stop below the bottom of the FVG

<b>Tip:</b>
Combine FVG with Order Block for high-probability entries.
""",
    },

    "what_is_bos": {
        "category": "smc",
        "title":    "What is Break of Structure?",
        "emoji":    "💥",
        "content":  """
<b>💥 What is Break of Structure (BOS)?</b>

BOS occurs when price <b>breaks beyond a key swing high or low</b>, confirming the continuation of a trend.

<b>Bullish BOS:</b>
Price breaks above the previous swing high → Uptrend confirmed ✅

<b>Bearish BOS:</b>
Price breaks below the previous swing low → Downtrend confirmed

<b>BOS in an Uptrend:</b>
In a healthy uptrend, each BOS creates:
• Higher High (HH) after breaking previous high
• Higher Low (HL) during pullbacks

<b>How Halol uses BOS:</b>
A Bullish BOS increases signal score significantly.
It confirms that institutional buyers are in control.

<b>BOS vs CHoCH:</b>
• BOS = trend continuation (same direction)
• CHoCH = trend change (new direction)

<b>Entry Strategy:</b>
After a BOS, wait for price to pull back to the previous swing high (now support) and enter there.
""",
    },

    "what_is_choch": {
        "category": "smc",
        "title":    "What is Change of Character?",
        "emoji":    "🔄",
        "content":  """
<b>🔄 What is Change of Character (CHoCH)?</b>

CHoCH signals a <b>potential trend reversal</b>. It occurs when price breaks against the prevailing trend structure.

<b>Bullish CHoCH:</b>
In a downtrend (lower highs, lower lows) → price suddenly breaks ABOVE a previous swing high
→ Trend may be reversing to bullish

<b>Bearish CHoCH:</b>
In an uptrend → price breaks below a previous swing low
→ Trend may be reversing to bearish

<b>CHoCH vs BOS:</b>
• BOS in uptrend = continues up (higher high)
• CHoCH in downtrend = first sign of reversal

<b>How to Trade CHoCH:</b>
1. Identify a downtrend with lower highs/lows
2. Watch for CHoCH (break above last swing high)
3. Wait for a pullback
4. Enter on the retest with stop below the new low

<b>Important:</b>
CHoCH alone is not enough. Confirm with volume, RSI, and higher timeframe trend.
""",
    },

    "what_is_liquidity_sweep": {
        "category": "smc",
        "title":    "What is a Liquidity Sweep?",
        "emoji":    "🌊",
        "content":  """
<b>🌊 What is a Liquidity Sweep?</b>

A Liquidity Sweep (or stop hunt) happens when <b>price briefly pierces a key level to trigger stop-loss orders</b>, then reverses sharply.

<b>Why It Happens:</b>
Large institutions need liquidity to fill massive orders. They push price beyond obvious levels (previous highs/lows) to trigger retail traders' stops, then reverse.

<b>Signs of a Liquidity Sweep:</b>
• Long wick beyond key level
• Closes back inside the range
• Volume spike on the sweep candle
• Quick reversal after the wick

<b>Bullish Liquidity Sweep:</b>
Price sweeps below a support/swing low, triggers sell stops, then reverses up → Buy opportunity 🟢

<b>How to Trade It:</b>
1. Mark key swing lows (where stops are clustered)
2. Wait for a wick below, followed by bullish close
3. Enter on the candle close or next candle
4. Stop below the wick low

<b>This is the "fake breakdown" or "spring" pattern.</b>
""",
    },

    "what_is_breakout_retest": {
        "category": "smc",
        "title":    "What is Breakout Retest?",
        "emoji":    "🚀",
        "content":  """
<b>🚀 What is a Breakout Retest?</b>

After price <b>breaks above a key resistance level</b>, it often returns to "test" that level as new support before continuing upward.

<b>The Pattern:</b>
1. Price consolidates below resistance
2. Breakout — price closes above resistance with volume
3. Pullback — price returns to test the broken level
4. Bounce — price holds above and continues up ✅

<b>Why It's Reliable:</b>
• Sellers who missed the breakout try to short the retest (providing liquidity to buyers)
• Previous resistance now becomes strong support
• Volume often confirms the bounce

<b>How Halol detects it:</b>
We look for resistance breaks in the last 20 candles, followed by price returning within 1.5% of that level.

<b>Entry:</b>
Buy at the retest zone with tight stop below the resistance turned support.

<b>Risk/Reward:</b>
Often 1:3 or better, because entry is precise and target is the next resistance level.
""",
    },

    # ── Risk Management ────────────────────────────────────────────────────

    "what_is_stop_loss": {
        "category": "risk",
        "title":    "What is Stop Loss?",
        "emoji":    "🛑",
        "content":  """
<b>🛑 What is Stop Loss?</b>

A Stop Loss is a <b>pre-set price level where you exit a trade to limit losses</b> if the market moves against you.

<b>Why Stop Loss is Essential:</b>
• Protects capital
• Removes emotion from decision-making
• Allows you to stay in the game long-term
• Required for proper risk management

<b>How Halol calculates Stop Loss:</b>
Stop Loss = Entry – 1.5× ATR

This gives the trade enough "breathing room" to avoid being stopped out by normal volatility.

<b>Stop Loss Placement Rules:</b>
✅ Below the Order Block or key support
✅ Below the swing low
✅ Allow for normal market noise (1.5× ATR)

❌ Never place stop loss at an obvious level (many traders do, institutions exploit this)
❌ Never move stop loss further away to avoid loss
❌ Never trade without a stop loss

<b>Islamic Perspective:</b>
Having a stop loss is prudent risk management — protecting wealth (hifz al-mal) is a core Islamic value.
""",
    },

    "what_is_take_profit": {
        "category": "risk",
        "title":    "What is Take Profit?",
        "emoji":    "💰",
        "content":  """
<b>💰 What is Take Profit?</b>

A Take Profit is a <b>price target where you exit a trade and lock in gains</b>.

<b>Why Use Multiple TPs:</b>
Halol uses TP1, TP2, and TP3 so you can:
• Lock in early profits at TP1 (secure, high probability)
• Let remaining position ride to TP2 and TP3
• Never give back all profits in a reversal

<b>Recommended Allocation:</b>
• Sell 40% at TP1
• Sell 35% at TP2
• Let 25% ride to TP3

<b>How Halol sets TPs:</b>
• TP1 = Entry + 1.5× Risk
• TP2 = Entry + 2.5× Risk
• TP3 = Entry + 4× Risk
(or at key resistance levels)

<b>After TP1:</b>
Move stop loss to breakeven (entry price).
Now you cannot lose on this trade!

<b>Patience:</b>
Do not take profits too early out of fear. Trust your analysis and let the plan play out.
""",
    },

    "what_is_risk_reward": {
        "category": "risk",
        "title":    "What is Risk Reward Ratio?",
        "emoji":    "⚖️",
        "content":  """
<b>⚖️ What is Risk/Reward Ratio (RRR)?</b>

Risk/Reward Ratio compares <b>how much you risk to how much you can gain</b>.

<b>Formula:</b>
RRR = (Take Profit – Entry) ÷ (Entry – Stop Loss)

<b>Example:</b>
• Entry: $100
• Stop Loss: $95 (risk = $5)
• Take Profit: $115 (reward = $15)
• RRR = 15 ÷ 5 = <b>3:1</b>

<b>Minimum RRR for Halol:</b>
Never take a trade with RRR below 1.5:1.
Aim for 2:1 or better.

<b>The Math:</b>
With 2:1 RRR, you can be RIGHT only 40% of the time and still be profitable:
• 4 wins × $200 = $800
• 6 losses × $100 = $600
• Net profit: $200 ✅

<b>Higher is Better:</b>
• 1:1 = Risky
• 2:1 = Acceptable
• 3:1+ = Excellent
• Halol targets minimum 1.5:1 on all trades
""",
    },

    "what_is_position_sizing": {
        "category": "risk",
        "title":    "What is Position Sizing?",
        "emoji":    "📐",
        "content":  """
<b>📐 What is Position Sizing?</b>

Position sizing determines <b>how much of your capital to invest in each trade</b>.

<b>The Golden Rule:</b>
<b>Never risk more than 1-2% of your total capital on a single trade.</b>

<b>Formula:</b>
Position Size = (Capital × Risk%) ÷ (Entry – Stop Loss)

<b>Example:</b>
• Total Capital: $10,000
• Risk per trade: 1% = $100
• Entry: $50,000 (BTC)
• Stop Loss: $48,000 (risk per coin = $2,000)
• Position Size = $100 ÷ $2,000 = <b>0.05 BTC</b>

<b>Why This Matters:</b>
Even with 10 consecutive losses (rare), you only lose 10% of capital.
Your account survives. You stay in the game.

<b>Common Mistake:</b>
Going "all in" on one trade. Even if you're right 70% of the time, one bad trade can wipe you out.

<b>Islamic Principle:</b>
Moderation and protection of wealth (hifz al-mal) align with conservative position sizing.
""",
    },

    # ── FAQ ────────────────────────────────────────────────────────────────

    "faq_halal": {
        "category": "faq",
        "title":    "Is crypto trading halal?",
        "emoji":    "☪️",
        "content":  """
<b>☪️ Is Crypto Trading Halal?</b>

This is a topic where Islamic scholars have varying opinions. Here is a balanced overview:

<b>Generally Considered Permissible (Spot):</b>
✅ Buying and owning real crypto assets (spot)
✅ Long-term investing (hodling)
✅ Using crypto for actual transactions
✅ Trading without leverage or interest

<b>Generally Considered Not Permissible:</b>
❌ Futures and derivatives trading
❌ Leveraged trading (borrowing = riba)
❌ Short selling (profiting from harm/decline)
❌ Earning interest on crypto (staking with interest)
❌ Highly speculative/gambling behavior

<b>Halol Crypto AI Approach:</b>
We ONLY provide spot analysis. No futures. No leverage. No short signals.

<b>Our Recommendation:</b>
Consult a qualified Islamic scholar who understands modern finance for a personal ruling.

<b>Notable Scholar Opinions:</b>
Some contemporary scholars have permitted spot crypto as a new form of currency/asset with utility. Others advise caution. Scholars generally agree on prohibiting futures and leverage.
""",
    },

    "faq_signals": {
        "category": "faq",
        "title":    "How accurate are the signals?",
        "emoji":    "🎯",
        "content":  """
<b>🎯 How Accurate Are the Signals?</b>

Signals are analytical tools, not guarantees. Here's what you need to know:

<b>Our Signal Engine:</b>
• Combines 8+ indicators
• Uses Smart Money Concepts
• Weighs multiple timeframes
• Scores 0-100% confidence

<b>Historical Performance (typical for TA systems):</b>
Strong Buy signals on 4H timeframe: ~60-65% win rate when combined with proper risk management.

<b>Why Signals Can Fail:</b>
• Unexpected news events
• Market manipulation
• Low liquidity
• Black swan events

<b>Most Important:</b>
Even with a 55% win rate, you can profit with proper risk management (2:1 RRR).

<b>Never:</b>
❌ Risk more than 1-2% per trade
❌ Enter without a stop loss
❌ Ignore the risk level shown

<b>Disclaimer:</b>
Halol Crypto AI is an educational and analytical tool. It does NOT provide financial advice. Always do your own research.
""",
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_lessons_by_category(category: str) -> List[Dict]:
    return [
        {"key": k, **{f: v for f, v in v.items() if f != "content"}}
        for k, v in LESSONS.items()
        if v.get("category") == category
    ]


def get_lesson(key: str) -> Optional[Dict]:
    return LESSONS.get(key)


def get_all_categories() -> Dict[str, str]:
    return CATEGORIES


def search_lessons(query: str) -> List[Dict]:
    query = query.lower()
    results = []
    for key, lesson in LESSONS.items():
        if (query in lesson["title"].lower() or
                query in lesson.get("content", "").lower()):
            results.append({"key": key, "title": lesson["title"], "emoji": lesson.get("emoji", "📖")})
    return results[:5]
