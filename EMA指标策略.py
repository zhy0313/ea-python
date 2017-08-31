# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：EMA指标策略
# 关键词：指数移动平均、双均线、动态止损。
# 方法：
# 1)用快慢两条指数移动平均线的交叉作为买入卖出信号；
# 2)快线自下而上穿过慢线，买入；自上而下穿过慢线，卖出；
# 3)持仓期间计算净值的回撤，当回撤大于预设值时，全仓卖出止损，等待下一次入场信号

import talib


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-10-01 00:00:00",
    "end_time": "2017-07-01 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 100000,
                      "huobi_cny_btc": 0},
}


# 阅读2，遇到不明白的变量可以跳过，需要的时候回来查阅:
# initialize函数是两大核心函数之一（另一个是handle_data），用于初始化策略变量。
# 策略变量包含：必填变量，以及非必填（用户自己方便使用）的变量
def initialize(context):
    # 设置回测频率, 可选：'1m', '5m', '15m', '30m', '60m', '1d', '1w', '1M', '1y'
    context.frequency = "1d"
    # 设置回测基准, 比特币：'huobi_cny_btc', 莱特币：'huobi_cny_ltc', 以太坊：'huobi_cny_eth'
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币：'huobi_cny_btc', 莱特币：'huobi_cny_ltc', 以太坊：'huobi_cny_eth'
    context.security = "huobi_cny_btc"

    # EMA快线回看时间
    context.user_data.ema_fast_window = 5
    # EMA慢线回看时间
    context.user_data.ema_slow_window = 20
    # 设置回撤止损线 (%)。 如设置为5，则当回撤大于等于5%时，止损退出
    context.user_data.stop_loss_line = 10

    # 记录净值的最大值，用于计算持仓的回撤，判断是否应该止损。每次止损或者全仓卖出后，会被设置为None，重新计算
    context.user_data.max_net = None


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 买入信号
    long_signal_triggered = False
    # 卖出信号
    short_signal_triggered = False
    # 止损信号
    stop_loss_signal_triggered = False

    # 更新净值最大值
    if context.user_data.max_net is None:
        context.user_data.max_net = context.account.huobi_cny_net
    else:
        if context.user_data.max_net < context.account.huobi_cny_net:
            context.user_data.max_net = context.account.huobi_cny_net
    # 计算当前回撤
    current_draw_down = (1 - context.account.huobi_cny_net / context.user_data.max_net) * 100
    context.log.info("当前回撤为 %.2f%%, 止损线为 %.2f%%" % (current_draw_down, context.user_data.stop_loss_line))
    # 当前回撤大于止损线，则产生卖出止损信号
    if current_draw_down > context.user_data.stop_loss_line:
        context.log.info("已经触发止损线，全仓卖出止损，等待下一次买入信号")
        stop_loss_signal_triggered = True

    # 获取历史数据
    hist = context.data.get_price(context.security, count=context.user_data.ema_slow_window+1, frequency=context.frequency)
    if len(hist.index) < context.user_data.ema_slow_window:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return
    # 收盘价
    close_prices = hist["close"].values

    # 计算EMA值
    ema_fast = talib.EMA(close_prices, context.user_data.ema_fast_window)
    ema_slow = talib.EMA(close_prices, context.user_data.ema_slow_window)

    # 当前快线EMA
    current_ema_fast = ema_fast[-1]
    # 当前慢线EMA
    current_ema_slow = ema_slow[-1]
    # 前一个bar的快线EMA
    pre_ema_fast = ema_fast[-2]
    # 前一个bar的慢线EMA
    pre_ema_slow = ema_slow[-2]

    context.log.info("当前EMA 快线 = %.2f, 慢线 = %.2f; 前一个bar EMA 快线 = %.2f, 慢线 = %.2f" % (current_ema_fast, current_ema_slow, pre_ema_fast, pre_ema_slow))

    # EMA快线从下向上穿过EMA慢线时，产生买入信号
    if pre_ema_fast <= pre_ema_slow and current_ema_fast > current_ema_slow:
        context.log.info("EMA快线从下向上穿过EMA慢线时，产生买入信号")
        long_signal_triggered = True
    # EMA快线从上向下穿过EMA慢线时，产生卖出信号
    elif pre_ema_fast >= pre_ema_slow and current_ema_fast < current_ema_slow:
        context.log.info("EMA快线从上向下穿过EMA慢线时，产生卖出信号")
        short_signal_triggered = True

    # 有卖出信号，且持有仓位，则市价单全仓卖出
    if short_signal_triggered or stop_loss_signal_triggered:
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            context.user_data.max_net = None
            # 卖出信号，且不是空仓，则市价单全仓清空
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("卖出数量为 %s" % context.account.huobi_cny_btc)
            context.order.sell(context.security, quantity=str(context.account.huobi_cny_btc))
        else:
            context.log.info("仓位不足，无法卖出")
    # 有买入信号，且持有现金，则市价单全仓买入
    elif long_signal_triggered:
        if context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
            # 买入信号，且持有现金，则市价单全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % context.account.huobi_cny_cash)
            context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
        else:
            context.log.info("现金不足，无法下单")
    else:
        context.log.info("无交易信号，进入下一根bar")