# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：AR指标策略
# 策略详细介绍：https://wequant.io/study/strategy.ar.html
# 关键词：价格波动、超买超卖。
# 方法：
# 1)利用一段时间内开盘价在最高价和最低价中所处的位置构建AR人气指标
# 2)当人气指标过高(人气过热)时卖出，过低(人气过冷)时买入

import numpy as np


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-01-01 00:00:00",
    "end_time": "2016-10-01 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 100000,
                      "huobi_cny_btc": 0},
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

    # 设定回看时间窗口为26天
    context.user_data.period = 26
    # 设定AR的超卖线，低于它则买入
    context.user_data.over_sell = 70
    # 设定AR的超买线，高于它则卖出
    context.user_data.over_buy = 150


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 获取回看时间窗口内的历史数据
    hist = context.data.get_price(context.security, count=context.user_data.period, frequency=context.frequency)
    if len(hist.index) < context.user_data.period:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return
    # 开盘价
    open_prices = np.array(hist["open"])
    # 最高价
    high_prices = np.array(hist["high"])
    # 最低价
    low_prices = np.array(hist["low"])
    # 计算AR值
    ar = sum(high_prices - open_prices) / sum(open_prices - low_prices) * 100

    context.log.info("当前AR值为: %s" % ar)

    # AR值小于超卖线且拥有资金，则全仓买入
    if ar < context.user_data.over_sell:
        context.log.info("AR超过了超卖线，产生买入信号")
        if context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
            # 市价单全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % context.account.huobi_cny_cash)
            context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
        else:
            context.log.info("现金不足，无法下单")
    # AR值大于超买线且有持仓，则全仓卖出
    elif ar > context.user_data.over_buy:
        context.log.info("AR超过了超买线，产生卖出信号")
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            # 市价单全仓卖出
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("卖出数量为 %s" % context.account.huobi_cny_btc)
            context.order.sell(context.security, quantity=str(context.account.huobi_cny_btc))
        else:
            context.log.info("仓位不足，无法卖出")
    else:
        context.log.info("无交易信号，进入下一根bar")