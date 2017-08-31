# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：NATR策略
# 关键词：规范真实波幅、价格突破。
# 方法：
# 1)利用规范化的真实波幅来构造上下轨；
# 2)价格突破上轨买入；
# 3)价格突破下轨卖出。

import numpy as np
import talib


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-10-01 00:00:00",  # 回测起始时间
    "end_time": "2017-07-01 00:00:00",  # 回测结束时间
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
    context.frequency = "60m"
    # 设置回测基准, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.security = "huobi_cny_btc"

    # 设定NATR的参数
    # NATR算法回看天数,此处设置为10天
    context.user_data.natr_period = 10
    # 当前价格与之前1天的价格相比较
    context.user_data.pre_period = 1
    # 多头NATR的倍数
    context.user_data.long_multi = 0.1
    # 空头NATR的倍数
    context.user_data.short_multi = 0.1

    # 至此initialize函数定义完毕。


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 获取回看时间窗口内的历史数据
    hist = context.data.get_price(context.security, count=context.user_data.natr_period + 1, frequency="1d")
    if len(hist.index) < context.user_data.natr_period + 1:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return
    # 收盘价
    close = np.array(hist["close"])
    # 最高价
    high = np.array(hist["high"])
    # 最低价
    low = np.array(hist["low"])

    # 使用talib计算NATR
    try:
        # 获取最新的NATR值
        natr = talib.NATR(high, low, close, timeperiod=context.user_data.natr_period)[-1]
    except:
        context.log.error("计算ATR时出现错误...")
        return

    # 获取最新价格
    current_price = context.data.get_current_price(context.security)
    # 获取context.user_data.pre_period个bar前的价格
    prev_price = close[-(context.user_data.pre_period + 1)]
    # 计算上下轨
    upper = prev_price + context.user_data.long_multi * natr
    lower = prev_price - context.user_data.short_multi * natr

    context.log.info("当前价格=%s元, 上轨=%s元, 下轨=%s元" % (current_price, upper, lower))

    # 如果当前价格比之前价格低1个NATR，产生卖出信号
    if current_price < lower:
        context.log.info("价格超过了下轨，产生卖出信号")
        # 若持有仓位，则全仓卖出
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("卖出数量为 %s" % context.account.huobi_cny_btc)
            context.order.sell_limit(context.security, quantity=str(context.account.huobi_cny_btc), price=str(close[-1] * 0.98))
        else:
            context.log.info("仓位不足，无法卖出")
    # 如果当前价格比之前价格高1个NATR，产生买入信号
    elif current_price > upper:
        context.log.info("价格超过了上轨，产生买入信号")
        # 若持有现金，则全仓买入
        if context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % context.account.huobi_cny_cash)
            context.order.buy_limit(context.security, quantity=str(context.account.huobi_cny_cash/close[-1]*0.98), price=str(close[-1]*1.02))
        else:
            context.log.info("现金不足，无法下单")
    else:
        context.log.info("无交易信号，进入下一根bar")