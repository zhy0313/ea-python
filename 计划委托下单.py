# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：计划委托
# 关键词：触发价格、限价市价。
# 方法：
# 1)预先设置委托（包括委托方向、委托金额、数量、价格、限价单/市价单）和触发条件;
# 2)当最新成交价格达到事先设定的触发价格时，将预先设置的委托送入市场;


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-06-17 00:00:00",
    "end_time": "2016-06-23 00:00:00",
    "commission": 0.002,  # 此处设置交易佣金
    "slippage": 0.001,  # 此处设置交易滑点
    "account_initial": {"huobi_cny_cash": 0,
                      "huobi_cny_btc": 10},
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

    # 设置计划委托下单方向，买入委托："buy", 卖出委托: "sell"
    context.user_data.entrust_direction = "sell"
    # 设置计划委托下单方式, 市价委托："market", 限价委托："limit"
    context.user_data.entrust_type = "limit"

    # 买入设置 （若需要卖出则不用设置）
    # 计划委托-买入-触发价格 （当最新成交价高于触发价格时，会执行委托）
    context.user_data.buy_trigger_price = 5000
    # 计划委托-买入-限价单-下单价格 （若市价单委托则无需设置）
    context.user_data.buy_entrust_price = 5001
    # 计划委托-买入-限价单-下单数量 （若市价单委托则无需设置）
    context.user_data.buy_entrust_quantity = 20
    # 计划委托-买入-市价单-下单金额 （若限价单委托则无需设置）
    context.user_data.buy_market_cash_amount = 100000

    # 卖出设置 (若需要买入则不用设置)
    # 计划委托-卖出-触发价格 （当最新成交价低于触发价格时，会执行委托）
    context.user_data.sell_trigger_price = 4500
    # 计划委托-卖出-限价单-下单价格 （若市价单委托则无需设置）
    context.user_data.sell_entrust_price = 4450
    # 计划委托-卖出-限价单-下单数量 （若市价单委托则无需设置）
    context.user_data.sell_entrust_quantity = 10
    # 计划委托-卖出-市价单-下单数量  (若限价单委托则无需设置)
    context.user_data.sell_market_quantity = 10

    # 记录买入触发价格是否达到（此处无需更改）
    context.user_data.buy_signal_triggered = False
    # 记录卖出触发价格是否达到（此处无需更改）
    context.user_data.sell_signal_triggered = False


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 获取当前最新价格
    current_price = context.data.get_current_price(context.security)

    # 买入计划委托
    if context.user_data.entrust_direction == "buy":
        if not context.user_data.buy_signal_triggered:
            context.log.info("当前价格为 %s 元, 触发价格为 %s 元" % (current_price, context.user_data.buy_trigger_price))
            if current_price >= context.user_data.buy_trigger_price:
                # 当前价格超过了买入的触发价格，将下达买入委托
                context.user_data.buy_signal_triggered = True
                context.log.info("当前价格突破了触发价格, 产生了计划委托买入信号")
                # 限价单买入
                if context.user_data.entrust_type == "limit":
                    context.log.info("正在买入 %s" % context.security)
                    context.log.info("以限价单进行委托，下单价格为 %s 元，下单数量为 %s" % (context.user_data.buy_entrust_price, context.user_data.buy_entrust_quantity))
                    context.order.buy_limit(context.security, str(context.user_data.buy_entrust_price), str(context.user_data.buy_entrust_quantity))
                # 市价单买入
                elif context.user_data.entrust_type == "market":
                    context.log.info("正在买入 %s" % context.security)
                    context.log.info("下单金额为 %s 元，以市价单买入" % context.user_data.buy_market_cash_amount)
                    context.order.buy(context.security, cash_amount=str(context.user_data.buy_market_cash_amount))
                else:
                    context.log.error("下单方式参数 (context.user_data.entrust_type) 设置出错，只能是 'limit' 或者 'market'")
                    context.log.error("请改正后重新运行程序")
            else:
                context.log.info("尚未触发买入信号，进入下一个bar")
        else:
            context.log.info("已经完成买入计划委托订单")
    # 卖出计划委托
    elif context.user_data.entrust_direction == "sell":
        if not context.user_data.sell_signal_triggered:
            context.log.info("当前价格为 %s 元, 触发价格为 %s 元" % (current_price, context.user_data.sell_trigger_price))
            if current_price <= context.user_data.sell_trigger_price:
                # 当前价格跌破了卖出的触发价格，将下达卖出委托
                context.user_data.sell_signal_triggered = True
                context.log.info("当前价格跌破了触发价格, 产生了计划委托卖出信号")
                # 限价单卖出
                if context.user_data.entrust_type == "limit":
                    context.log.info("正在卖出 %s" % context.security)
                    context.log.info("以限价单进行委托，下单价格为 %s 元，下单数量为 %s" % (context.user_data.sell_entrust_price, context.user_data.sell_entrust_quantity))
                    context.order.sell_limit(context.security, str(context.user_data.sell_entrust_price), str(context.user_data.sell_entrust_quantity))
                elif context.user_data.entrust_type == "market":
                    context.log.info("正在卖出 %s" % context.security)
                    context.log.info("以市价单委托卖出，下单数量为 %s 个" % context.user_data.sell_market_quantity)
                    context.order.sell(context.security, quantity=str(context.user_data.sell_market_quantity))
                else:
                    context.log.error("下单方式参数 (context.user_data.entrust_type) 设置出错，只能是 'limit' 或者 'market'")
                    context.log.error("请改正后重新运行程序")
            else:
                context.log.info("尚未触发卖出信号，进入下一个bar")
        else:
            context.log.info("已经完成卖出计划委托订单")
    # 买卖方向参数设置错误
    else:
        context.log.error("委托方向参数 （context.user_data.entrust_direction）设置出错，只能是 'buy' 或者 'sell'")
        context.log.error("请改正后重新运行程序")