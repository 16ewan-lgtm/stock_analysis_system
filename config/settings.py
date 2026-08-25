# ============================================================
# 【系統配置】
# ============================================================

# LINE 推播設定
LINE_CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"
LINE_USER_ID = "YOUR_USER_ID"

# 股票列表
STOCK_LIST = [
    ('2330.TW', '台積電'),
    ('2308.TW', '台達電'),
    ('2317.TW', '鴻海'),
]

# 數據下載週期
DATA_PERIOD = '6mo'

# 分析權重
TECH_WEIGHT = 0.40
FUNDAMENTAL_WEIGHT = 0.35
CHIPS_WEIGHT = 0.25

# 信號閾值
STRONG_BUY_THRESHOLD = 70
BUY_THRESHOLD = 60
WATCH_THRESHOLD = 50
