# 注：该策略仅供参考和学习，不保证收益。

# 简单的价格突破策略。当前价格超过最近5个收盘价的均价，则全仓买入；低于均价，则全仓卖出

# PARAMS用于设定程序参数,回测的起始时间、结束时间、滑点误差、初始资金和持仓。
PARAMS = {
    "start_time": "2017-06-01 00:00:00",  # 回测起始时间
    "end_time": "2017-07-01 00:00:00",  # 回测结束时间
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 10000,
                      "huobi_cny_btc": 0},
}

# initialize函数是两大核心函数之一（另一个是handle_data）,用于初始化策略变量。
def initialize(context):
    context.frequency = "1d" # 以30分频率进行回测
    context.benchmark = "huobi_cny_btc" # 设定以比特币为基准
    context.security = "huobi_cny_btc" # 设定操作的标的为比特币

# handle_data函数定义了策略的执行逻辑,按照frequency生成的bar依次读取并执行策略逻辑,直至程序结束。
def handle_data(context):
    hist = context.data.get_price(context.security, count=5, frequency=context.frequency) # 获取最近5个频率周期的历史数据
    ma = hist["close"].rolling(window=5).mean()[-1] # 计算最近5个收盘价的均价
    current_price = context.data.get_current_price(context.security) # 获取当前价格
    if current_price > ma and context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT: # 当前价格大于均价时，全仓买入
        context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
    elif current_price < ma and context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY: # 当前价格小于均价时，全仓卖出
        context.order.sell(context.security, quantity=str(context.account.huobi_cny_btc))