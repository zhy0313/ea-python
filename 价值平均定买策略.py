# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)intialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：价值平均定卖策略
# 策略详细介绍：https://wequant.io/study/strategy.value_averaging-sell.html
# 关键词：卖出策略、矿工首选、高抛低吸、分批卖出。
# 方法：
# 1)确定每个周期的目标仓位；
# 2)每一期将仓位调整至目标仓位；


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2014-05-01 00:00:00",
    "end_time": "2014-11-01 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 0,
                        "huobi_cny_btc": 1000},
}


# 阅读2，遇到不明白的变量可以跳过，需要的时候回来查阅:
# initialize函数是两大核心函数之一（另一个是handle_data），用于初始化策略变量。
# 策略变量包含：必填变量，以及非必填（用户自己方便使用）的变量
def initialize(context):
    # 以日为单位进行回测
    context.frequency = "1d"
    # 设置回测基准, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.security = "huobi_cny_btc"

    # 设置策略参数
    # 每个frequency的持仓占净资产减少的比例（%）
    context.user_data.pos_value_decrease_per_period = 0.5464
    # 记录下当前处于第几个投资周期
    context.user_data.invest_period_count = 0
    # 设置策略期望初始仓位（%）
    context.user_data.initial_pos_ratio = 100


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 取得最新价格
    latest_close_price = context.data.get_current_price(context.security)
    # 计算当前实时仓位（元)
    current_pos_value = context.account.huobi_cny_btc * latest_close_price
    # 计算当前实时仓位比例（%）
    current_pos_ratio = current_pos_value / context.account.huobi_cny_net * 100

    if context.user_data.initial_pos_ratio is None:
        context.user_data.initial_pos_ratio = current_pos_ratio

    # 计算当前期望仓位比例 (%)
    expected_pos_ratio = context.user_data.initial_pos_ratio - context.user_data.pos_value_decrease_per_period * (context.user_data.invest_period_count + 1)
    # 计算当前期望仓位 (元)
    expected_pos_value = (expected_pos_ratio / 100) * context.account.huobi_cny_net
    # 当前账户持有的人民币现金
    current_cash_pos = context.account.huobi_cny_cash
    # 当前账户持有的数字货币数量
    current_sec_pos = context.account.huobi_cny_btc

    # 计算本期需要卖出的数量(若为负，则需要买入数字货币)
    quantity_to_sell = quantity_to_sell_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos, latest_close_price)
    context.log.info("目标仓位: %s 元, 现有仓位: %s 元" % (expected_pos_value, current_pos_value))
    # 更新投资周期至下一期
    context.user_data.invest_period_count += 1

    if quantity_to_sell >= HUOBI_CNY_BTC_MIN_ORDER_QUANTITY:
        # 需要卖出仓位，市价单卖出
        context.log.info("正在卖出 %s" % context.security)
        context.log.info("卖出数量为 %s" % quantity_to_sell)
        context.order.sell(context.security, quantity=str(quantity_to_sell))

    elif quantity_to_sell < 0:
        # 需要买入仓位，计算需要买入的金额，市价单买入
        cash_to_buy = -1 * quantity_to_sell * latest_close_price
        context.log.info("正在买入%s" % context.security)
        context.log.info("下单金额为 %s 元" % cash_to_buy)
        context.order.buy(context.security, cash_amount=str(cash_to_buy))
    else:
        context.log.info("无加减仓操作")


def quantity_to_sell_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos, latest_close_price):
    # 高于目标仓位，需要卖出减仓
    if current_pos_value > expected_pos_value:
        result = current_pos_value - expected_pos_value
        pos_qty_to_sell = result / latest_close_price
        # 当前仓位可以满足卖出需求
        if pos_qty_to_sell <= current_sec_pos:
            context.log.info("需要卖出，来达到目标仓位")
            return pos_qty_to_sell
        else:  # 仓位不足，卖出全部仓位
            context.log.warn(
                "现有仓位不足以满足目标仓位, 需要卖出仓位:%.2f, 现有仓位:%.2f. 本次将卖出所有仓位" % (pos_qty_to_sell, current_sec_pos))
            return current_sec_pos
    # 低于目标仓位，需要买入加仓
    elif current_pos_value < expected_pos_value:
        result = expected_pos_value - current_pos_value
        if result < current_cash_pos:
            context.log.info("需要买入，来达到目标仓位")
            quantity_to_buy = result / latest_close_price
            return -1 * quantity_to_buy
        else:  # 现金不足，投入全部现金加仓
            context.log.warn(
                "现金不足以满足目标仓位, 需要现金:%.2f, 现有现金:%.2f. 本次将用完全部现金" % (result, current_cash_pos))
            return -1 * current_cash_pos / latest_close_price
    else:
        return 0