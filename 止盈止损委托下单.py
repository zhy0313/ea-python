# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：止盈止损委托
# 关键词：触发价格、止盈止损。
# 方法：
# 1)预先设置好止盈触发价和止盈委托价，止损触发价和止损委托价；
# 2)当最新的成交价格达到某一触发价格时，即会按对应的委托价格送入市场


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-06-01 00:00:00",
    "end_time": "2016-10-01 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 0,
                      "huobi_cny_btc": 10},
}


# 阅读2，遇到不明白的变量可以跳过，需要的时候回来查阅:
# initialize函数是两大核心函数之一（另一个是handle_data），用于初始化策略变量。
# 策略变量包含：必填变量，以及非必填（用户自己方便使用）的变量
def initialize(context):
    # 设置回测频率, 可选：'1m', '5m', '15m', '30m', '60m', '1d', '1w', '1M', '1y'
    context.frequency = "1d"
    # 设置回测基准, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.benchmark = "huobi_cny_btc"
    # 设置回测标的, 比特币："huobi_cny_btc", 莱特币："huobi_cny_ltc", 以太坊："huobi_cny_eth"
    context.security = "huobi_cny_btc"

    # 设置止盈/止损下单方向，买入委托："buy", 卖出委托: "sell"
    context.user_data.entrust_direction = "sell"

    # 卖出-委托数量 （若为买入方向则无需设置）
    context.user_data.sell_entrust_quantity = 10
    # 买入-委托金额 （若为卖出方向则无需设置）
    context.user_data.buy_entrust_cash_amount = 10000

    # 设置止盈触发价
    context.user_data.take_profit_trigger_price = 5000
    # 设置止盈委托价
    context.user_data.take_profit_entrust_price = 4900
    # 设置止损触发价
    context.user_data.stop_loss_trigger_price = 3000
    # 设置止损委托价
    context.user_data.stop_loss_entrust_price = 2900

    # 记录是否已经止盈/止损（此处无需更改）
    context.user_data.triggered_already = False


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 若已经触发止盈/止损，则委托已经完成，之后不会有任何操作
    if context.user_data.triggered_already:
        context.log.info("已经触发止盈/止损")
        return
    # 获取当前最新价格
    current_price = context.data.get_current_price(context.security)

    # 止盈/止损 买入委托
    if context.user_data.entrust_direction == "buy":
        # 检查参数是否正确: 买入方向时，止盈触发价格应该小于止损触发价格
        if context.user_data.take_profit_trigger_price >= context.user_data.stop_loss_trigger_price:
            context.log.error("止盈/止损 买入委托中，止盈触发价格应该小于止损触发价格")
            context.log.error("请重新设置参数")
            return
        context.log.info("当前价格为 %s 元，止盈触发价为 %s 元，止损触发价为 %s 元" % (current_price, context.user_data.take_profit_trigger_price, context.user_data.stop_loss_trigger_price))
        if current_price <= context.user_data.take_profit_trigger_price:
            context.log.info("触发了买入止盈信号")
            entrust_price = context.user_data.take_profit_entrust_price
        elif current_price >= context.user_data.stop_loss_trigger_price:
            context.log.info("触发了买入止损信号")
            entrust_price = context.user_data.stop_loss_entrust_price
        else:
            context.log.info("未触发止盈/止损信号，进入下一根bar")
            return
        context.user_data.triggered_already = True
        # 执行限价单买入，以止盈/止损
        if context.account.huobi_cny_cash >= context.user_data.buy_entrust_cash_amount:
            # 计算买入数量
            buy_quantity = context.user_data.buy_entrust_cash_amount / entrust_price
            context.log.info("正在买入 %s" % context.security)
            context.log.info("以限价单进行委托，下单价格为 %s 元，下单数量为 %s" % (entrust_price, buy_quantity))
            context.order.buy_limit(context.security, str(entrust_price), str(buy_quantity))
        else:
            context.log.error("现金不足，无法买入，下单失败")
            context.log.error("请重新设置买入金额，不要超过现有资金")
    # 止盈/止损 卖出委托
    elif context.user_data.entrust_direction == "sell":
        # 检查参数是否正确: 卖出方向时，止盈触发价格应该大于止损触发价格
        if context.user_data.take_profit_trigger_price <= context.user_data.stop_loss_trigger_price:
            context.log.error("止盈/止损 卖出委托中，止盈触发价格应该大于止损触发价格")
            context.log.error("请重新设置参数")
            return
        context.log.info("当前价格为 %s 元，止盈触发价为 %s 元，止损触发价为 %s 元" % (current_price, context.user_data.take_profit_trigger_price, context.user_data.stop_loss_trigger_price))
        if current_price >= context.user_data.take_profit_trigger_price:
            context.log.info("触发了卖出止盈信号")
            entrust_price = context.user_data.take_profit_entrust_price
        elif current_price <= context.user_data.stop_loss_trigger_price:
            context.log.info("触发了卖出止损信号")
            entrust_price = context.user_data.stop_loss_entrust_price
        else:
            context.log.info("未触发止盈/止损信号，进入下一根bar")
            return
        context.user_data.triggered_already = True
        # 执行限价单卖出，以止盈/止损
        if context.account.huobi_cny_btc >= context.user_data.sell_entrust_quantity:
            context.log.info("正在卖出 %s" % context.security)
            context.log.info("以限价单进行委托，下单价格为 %s 元，下单数量为 %s" % (entrust_price, context.user_data.sell_entrust_quantity))
            context.order.sell_limit(context.security, str(entrust_price), str(context.user_data.sell_entrust_quantity))
        else:
            context.log.error("持仓不足，无法卖出。下单失败")
            context.log.error("请重新设置卖出数量，不要超过现有持仓")
    # 买卖方向参数设置错误
    else:
        context.log.error("委托方向参数 （context.user_data.entrust_direction）设置出错，只能是 'buy' 或者 'sell'")
        context.log.error("请改正后重新运行程序")