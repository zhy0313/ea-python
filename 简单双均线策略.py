# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：简单双均线策略
# 策略详细介绍：https://wequant.io/study/strategy.simple_moving_average.html
# 关键词：价格突破、趋势跟踪。
# 方法：
# 1)计算一长一短两个时间窗口的价格均线
# 2)利用均线的突破来决定买卖

import numpy as np


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

    # 设置策略参数
    # 计算短线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.window_short = 5
    # 计算长线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.window_long = 20
    # 入场线, 用户自定义的变量，可以被handle_data使用
    context.user_data.enter_threshold = 0.00
    # 出场线, 用户自定义的变量，可以被handle_data使用
    context.user_data.exit_threshold = 0.00


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 获取历史数据, 取后window_long根bar
    hist = context.data.get_price(context.security, count=context.user_data.window_long, frequency=context.frequency)
    if len(hist.index) < context.user_data.window_long:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return
    # 计算短均线值
    close = np.array(hist["close"])
    short_mean = np.mean(hist["close"][-1 * context.user_data.window_short:])
    # 计算长均线值
    long_mean = np.mean(hist["close"][-1 * context.user_data.window_long:])

    # 价格上轨
    upper = long_mean + context.user_data.enter_threshold * long_mean
    # 价格下轨
    lower = long_mean - context.user_data.exit_threshold * long_mean

    context.log.info("当前 短期均线 = %s, 长期均线 = %s, 上轨 = %s, 下轨 = %s" % (short_mean, long_mean, upper, lower))

    # 短期线突破长期线一定比例，产生买入信号
    if short_mean > upper:
        context.log.info("短期均线穿越上轨，产生买入信号")
        if context.account.huobi_cny_cash >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
            # 有买入信号，且持有现金，则市价单全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % context.account.huobi_cny_cash)
            context.order.buy_limit(context.security, quantity=str(context.account.huobi_cny_cash/close[-1]*0.98), price=str(close[-1]*1.02))
        else:
            context.log.info("现金不足，无法下单")
    # 短期线低于长期线一定比例，产生卖出信号
    elif short_mean < lower:
        context.log.info("短期均线穿越下轨，产生卖出信号")
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            # 有卖出信号，且持有仓位，则市价单全仓卖出
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("卖出数量为 %s" % context.account.huobi_cny_btc)
            context.order.sell_limit(context.security, quantity=str(context.account.huobi_cny_btc), price=str(close[-1]*0.98))
        else:
            context.log.info("仓位不足，无法卖出")
    else:
        context.log.info("无交易信号，进入下一根bar")