# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：价值平均定投策略
# 策略详细介绍：https://wequant.io/study/strategy.value_averaging.html
# 关键词：长期投资、高抛低吸、分批建仓。
# 方法：
# 1)确定每个周期的目标仓位；
# 2)每一期将仓位调整至目标仓位；


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2015-01-01 00:00:00",
    "end_time": "2016-09-01 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 60000,
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

    # 设置策略参数
    # 每个frequency的持仓总值的增长金额
    context.user_data.pos_value_growth_per_period = 100
    # 记录下当前处于第几个投资周期
    context.user_data.invest_period_count = 0
    # 设置策略期望初始仓位
    context.user_data.initial_pos_value = 0


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 取得最新价格
    latest_close_price = context.data.get_current_price(context.security)
    # 计算当前实时仓位
    current_pos_value = context.account.huobi_cny_btc * latest_close_price

    if context.user_data.initial_pos_value is None:
        context.user_data.initial_pos_value = current_pos_value

    # 计算当前期望仓位
    expected_pos_value = context.user_data.initial_pos_value + context.user_data.pos_value_growth_per_period * (context.user_data.invest_period_count + 1)
    # 当前账户持有的人民币现金
    current_cash_pos = context.account.huobi_cny_cash
    # 当前账户持有的数字货币数量
    current_sec_pos = context.account.huobi_cny_btc
    # 计算本期需要投入的资金(若为负，则是撤回的资金)
    cash_to_spent = cash_to_spent_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos, latest_close_price)
    context.log.info("本期需要投入的现金:%f元" % cash_to_spent)

    # 更新投资周期至下一期
    context.user_data.invest_period_count += 1

    if cash_to_spent >= HUOBI_CNY_BTC_MIN_ORDER_CASH_AMOUNT:
        # 需要加仓，市价单买入
        context.log.info("正在买入%s" % context.security)
        context.log.info("下单金额为 %s 元" % cash_to_spent)
        context.order.buy(context.security, cash_amount=str(cash_to_spent))
    else:
        # 需要减仓，计算需要卖出的数量，市价单卖出
        quantity = min(context.account.huobi_cny_btc, -1 * cash_to_spent / latest_close_price)
        context.log.info("正在卖出 %s" % context.security)
        context.log.info("卖出数量为 %s" % quantity)
        context.order.sell(context.security, quantity=str(quantity))


# # 用户自定义的函数，可以被handle_data调用:计算每一个frequency需要买入/卖出的金额（正为买入，负为卖出）
def cash_to_spent_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos, latest_close_price):
    # 低于目标仓位，需要买入加仓
    if expected_pos_value > current_pos_value:
        result = expected_pos_value - current_pos_value
        if result < current_cash_pos:
            return result
        else:  # 现金不足，投入全部现金加仓
            context.log.warn(
                "现金不足以满足目标仓位, 需要现金：%.2f, 现有现金：%.2f. 本次将用完全部现金" % (result, current_cash_pos))
            return current_cash_pos
    else:  # 当前仓位高于目标仓位，需要卖出减仓
        result = current_pos_value - expected_pos_value
        pos_qty_to_sell = result / latest_close_price
        if pos_qty_to_sell < current_sec_pos:
            return -1 * result
        else:  # 仓位不足，卖出全部仓位
            context.log.warn(
                "现有仓位不足以满足目标仓位, 需要卖出仓位:%.2f, 现有仓位:%.2f. 本次将卖出所有仓位" % (pos_qty_to_sell, current_sec_pos))
            return -1 * latest_close_price * current_sec_pos