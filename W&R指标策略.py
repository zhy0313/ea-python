# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：W%R指标策略
# 策略详细介绍：https://wequant.io/study/strategy.wr.html
# 关键词：逆市指标、高抛低吸、波动行情。
# 方法：
# 1)利用特定时间段内的最高值、最低值以及当前价格确定WR值；
# 2)WR值超过超买线时卖出，超过超卖线时买入。

import numpy as np
import talib

# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2015-02-01 00:00:00",  # 回测起始时间
    "end_time": "2015-10-01 00:00:00",  # 回测结束时间
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 100000,
                      "huobi_cny_btc": 0},  # 设置账户初始状态
}


# 阅读2，遇到不明白的变量可以跳过，需要的时候回来查阅:
# initialize函数是两大核心函数之一（另一个是handle_data），用于初始化策略变量。
# 策略变量包含：必填变量，以及非必填（用户自己方便使用）的变量
def initialize(context):
    # 设置回测频率, 可选："1m", "5m", "15m", "30m", "60m", "4h", "1d", "1w"
    context.frequency = "1d"
    # 设置回测基准, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.security = "huobi_cny_btc"

    # 设置talib计算WR的参数
    # WR算法回看天数
    context.user_data.wr_period = 20
    # 设置超买线
    context.user_data.over_buy = 10
    # 设置超卖线
    context.user_data.over_sell = 90


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 获取历史数据
    hist = context.data.get_price(context.security, count=context.user_data.wr_period, frequency=context.frequency)
    if len(hist.index) < context.user_data.wr_period:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return

    # 收盘价
    close = np.array(hist["close"])
    # 最高价
    high = np.array(hist["high"])
    # 最低价
    low = np.array(hist["low"])

    try:
        # talib计算WR值
        wr_temp = talib.WILLR(high, low, close, timeperiod=context.user_data.wr_period)
        # talib计算的WR为负数，我们在这里变为正值
        wr_current_dt = -1 * wr_temp[-1]
    except:
        context.log.error("计算WR时出现错误...")
        return

    context.log.info("当前 WR = %s" % wr_current_dt)

    # 根据WR值来判断交易：
    if wr_current_dt > context.user_data.over_sell:
        context.log.info("WR值超过了超卖线，产生买入信号")
        if context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
            # WR大于超卖线且有现金，全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % context.account.huobi_cny_cash)
            context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
        else:
            context.log.info("现金不足，无法下单")
    elif wr_current_dt < context.user_data.over_buy:
        context.log.info("WR值超过了超买线，产生卖出信号")
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            # WR小于超买线且持有仓位，全仓卖出
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("卖出数量为 %s" % context.account.huobi_cny_btc)
            context.order.sell(context.security, quantity=str(context.account.huobi_cny_btc))
        else:
            context.log.info("仓位不足，无法卖出")
    else:
        context.log.info("无交易信号，进入下一根bar")