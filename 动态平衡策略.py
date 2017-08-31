# 注：该策略仅供参考和学习，不保证收益。

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：动态平衡策略
# 关键词：保持平衡、动态调整、降低风险。
# 方法：
# 1)仓位和现金保持在1：1左右（各50%左右）
# 2)当现金和仓位的差值超过账户总资产一定比例时，将仓位重新调整至50%


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
    # 以日为单位进行回测
    context.frequency = "1d"
    # 设置回测基准, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.security = "huobi_cny_btc"

    # 设置触发再平衡的阈值（占总净资产的比例，如设置为0.1，则当 |仓位-现金| > 0.1 * 总资产 时，触发再平衡）
    context.user_data.max_diff = 0.1


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 取得最新价格
    latest_close_price = context.data.get_current_price(context.security)
    # 计算当前实时持仓金额
    current_pos_value = context.account.huobi_cny_btc * latest_close_price
    # 获取当前现金金额
    current_cash = context.account.huobi_cny_cash
    # 计算阈值金额
    diff_threshold = context.account.huobi_cny_net * context.user_data.max_diff
    # 计算当前现金与持仓的差值
    current_diff = current_cash - current_pos_value

    context.log.info("当前仓位占总资产的比例为：%.2f%%" % (current_pos_value/context.account.huobi_cny_net))

    # 现金比持仓大，且超过阈值，买入部分仓位，使二者相等
    if current_diff > diff_threshold:
        cash_to_spent = current_diff / 2
        context.log.info("触发再平衡，需要买入仓位")
        context.log.info("正在买入%s" % context.security)
        context.log.info("下单金额为 %s 元" % cash_to_spent)
        context.order.buy(context.security, cash_amount=str(cash_to_spent))
    # 持仓比现金大，且超过阈值，卖出部分仓位，使二者相等
    elif - current_diff > diff_threshold:
        cash_to_sell = - current_diff / 2
        quantity_to_sell = cash_to_sell / latest_close_price
        context.log.info("触发再平衡，需要卖出仓位")
        context.log.info("正在卖出 %s" % context.security)
        context.log.info("卖出数量为 %s" % quantity_to_sell)
        context.order.sell(context.security, quantity=str(quantity_to_sell))
    # 无交易信号
    else:
        context.log.info('不需要重新平衡，进入下一根bar')