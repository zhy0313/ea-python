# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：网格交易策略
# 策略详细介绍：https://wequant.io/study/strategy.grid_trading.html
# 关键词：高抛低吸、逐步建仓。
# 方法：
# 1)设定一个基础价格，并围绕基础价格设置价格网格;
# 2)在相应价格位置调整仓位至相应水平(高位减仓，低位加仓);
# 3)在价格的波动中赚取收益。

import numpy as np


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2015-01-01 00:00:00",  # 回测起始时间
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

    # 设置策略参数
    # 底仓价格
    context.user_data.base_price = None
    # 计算移动均值所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.sma_window_size = 20
    # 确定当前price可否作为base_price的依据就是当前price是否小于20日均线*price_to_sma_threshold
    context.user_data.price_to_sma_threshold = 0.85
    # 止损线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_loss = 0.00
    # 用户自定义变量，记录下是否已经触发止损
    context.user_data.stop_loss_triggered = False
    # 止盈线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_win = 5.0
    # 用户自定义变量，记录下是否已经触发止盈
    context.user_data.stop_win_triggered = False
    # 设置网格的4个档位的买入价格（相对于基础价的百分比）
    context.user_data.buy4, context.user_data.buy3, context.user_data.buy2, context.user_data.buy1 = 0.88, 0.91, 0.94, 0.97
    # 设置网格的4个档位的卖出价格（相对于基础价的百分比）
    context.user_data.sell4, context.user_data.sell3, context.user_data.sell2, context.user_data.sell1 = 1.2, 1.15, 1.1, 1.05


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    if context.user_data.stop_loss_triggered:
        context.log.warn("已触发止损线, 此bar不会有任何指令 ... ")
        return

    if context.user_data.stop_win_triggered:
        context.log.info("已触发止盈线, 此bar不会有任何指令 ... ")
        return

    # 检查是否到达止损线或者止盈线，如果是，强制平仓，并结束所有操作
    if context.account.huobi_cny_net < context.user_data.portfolio_stop_loss * context.account_initial.huobi_cny_net or context.account.huobi_cny_net > context.user_data.portfolio_stop_win * context.account_initial.huobi_cny_net:
        should_stopped = True
    else:
        should_stopped = False

    # 如果有止盈/止损信号，则强制平仓，并结束所有操作
    if should_stopped:
        # 低于止损线，需要止损
        if context.account.huobi_cny_net < context.user_data.portfolio_stop_loss * context.account_initial.huobi_cny_net:
            context.log.warn(
                "当前净资产:%.2f 位于止损线下方 (%f), 初始资产:%.2f, 触发止损动作" %
                (context.account.huobi_cny_net, context.user_data.portfolio_stop_loss,
                context.account_initial.huobi_cny_net))
            context.user_data.stop_loss_triggered = True
        # 高于止盈线，需要止盈
        else:
            context.log.warn(
                "当前净资产:%.2f 位于止盈线上方 (%f), 初始资产:%.2f, 触发止盈动作" %
                (context.account.huobi_cny_net, context.user_data.portfolio_stop_win,
                context.account_initial.huobi_cny_net))
            context.user_data.stop_win_triggered = True

        if context.user_data.stop_loss_triggered:
            context.log.info("设置 stop_loss_triggered（已触发止损信号）为真")
        else:
            context.log.info("设置 stop_win_triggered （已触发止损信号）为真")

        # 有止盈/止损，且当前有仓位，则强平所有仓位
        if context.account.huobi_cny_btc >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            context.log.info("正在卖出 %s" % context.security)
            context.order.sell(context.security, quantity=str(context.account.huobi_cny_btc))
        return

    # 获取当前价格
    price = context.data.get_current_price(context.security)

    # 设置网格策略基础价格（base_price)
    if context.user_data.base_price is None:
        # 获取历史数据, 取后sma_window_size根bar
        hist = context.data.get_price(context.security, count=context.user_data.sma_window_size, frequency="1d")
        if len(hist.index) < context.user_data.sma_window_size:
            context.log.warn("bar的数量不足, 等待下一根bar...")
            return
        # 计算sma均线值
        sma = np.mean(hist["close"][-1 * context.user_data.sma_window_size:])
        # 若当前价格满足条件，则设置当前价格为基础价
        if price < context.user_data.price_to_sma_threshold * sma and context.user_data.base_price is None:
            context.user_data.base_price = price
            # 在基础价格位置建仓，仓位为50%
            context.log.info("建仓中...")
            cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.5, context.account.huobi_cny_cash)
            context.log.info("正在买入 %s" % context.security)
            context.log.info("下单金额为 %s 元" % cash_to_spent)
            context.order.buy(context.security, cash_amount=str(cash_to_spent))
            return

    # 还没有找到base_price，则继续找，不着急建仓
    if context.user_data.base_price is None:
        context.log.info("尚未找到合适的基准价格，进入下一根bar")
        return

    cash_to_spent = 0

    # 计算为达到目标仓位需要买入/卖出的金额
    # 价格低于buy4所对应的价格时，仓位调至100%
    if price / context.user_data.base_price < context.user_data.buy4:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 1, context.account.huobi_cny_cash)
    # 价格大于等于buy4对应的价格，低于buy3所对应的价格时，仓位调至90%
    elif price / context.user_data.base_price < context.user_data.buy3:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.9, context.account.huobi_cny_cash)
    # 价格大于等于buy3对应的价格，低于buy2所对应的价格时，仓位调至70%
    elif price / context.user_data.base_price < context.user_data.buy2:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.7, context.account.huobi_cny_cash)
    # 价格大于等于buy2对应的价格，低于buy1所对应的价格时，仓位调至60%
    elif price / context.user_data.base_price < context.user_data.buy1:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.6, context.account.huobi_cny_cash)
    # 价格大于sell4对应的价格，仓位调至0%
    elif price / context.user_data.base_price > context.user_data.sell4:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0, context.account.huobi_cny_cash)
    # 价格小于等于sell4对应的价格，大于sell3所对应的价格时，仓位调至10%
    elif price / context.user_data.base_price > context.user_data.sell3:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.1, context.account.huobi_cny_cash)
    # 价格小于等于sell3对应的价格，大于sell2所对应的价格时，仓位调至30%
    elif price / context.user_data.base_price > context.user_data.sell2:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.3, context.account.huobi_cny_cash)
    # 价格小于等于sell2对应的价格，大于sell1所对应的价格时，仓位调至40%
    elif price / context.user_data.base_price > context.user_data.sell1:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.4, context.account.huobi_cny_cash)

    # 根据策略调整仓位
    if cash_to_spent > HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
        #  市价单买入一定金额
        context.log.info("正在买入 %s" % context.security)
        context.log.info("下单金额为 %s 元" % str(cash_to_spent))
        context.order.buy(context.security, cash_amount=str(cash_to_spent))
    elif cash_to_spent < 0:
        #  计算需要卖出的数量，并已市价单卖出
        quantity = min(context.account.huobi_cny_btc, -1 * cash_to_spent / price)
        if quantity >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
            context.log.info("正在卖出 %s" % str(quantity))
            context.order.sell(context.security, quantity=str(quantity))


# 计算为达到目标仓位所需要购买的金额
def cash_to_spent_fn(net_asset, target_ratio, available_cny):
    return available_cny - net_asset * (1 - target_ratio)