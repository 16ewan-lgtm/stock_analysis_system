from config.settings import STOCK_LIST
from utils.data_processor import DataProcessor

processor = DataProcessor()

stock_id, stock_name = STOCK_LIST[0]
data = processor.download_stock_data(stock_id)

print("股票代碼:", stock_id)
print("股票名稱:", stock_name)

if data is None:
    print("❌ 行情下載失敗")
else:
    print("✅ 行情下載成功")
    print("資料筆數:", len(data))
    print("資料欄位:", list(data.columns))
    print(data.tail(3))
