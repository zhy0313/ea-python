# 注：该策略仅供参考和学习，不保证收益。

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 策略代码总共分为三大部分，1)PARAMS变量 2)initialize函数 3)handle_data函数
# 请根据指示阅读。或者直接点击运行回测按钮，进行测试，查看策略效果。

# 策略名称：跟踪委托
# 关键词：触发价格、回调幅度。
# 方法：
# 1)预先设置好委托、回调幅度、触发价格；
# 2)当价格达到触发价格以后，若价格回调幅达到预设值，则将预设好的的委托送入市场


# 阅读1，首次阅读可跳过:
# PARAMS用于设定程序参数，回测的起始时间、结束时间、滑点误差、初始资金和持仓。
# 可以仿照格式修改，基本都能运行。如果想了解详情请参考新手学堂的API文档。
PARAMS = {
    "start_time": "2016-01-01 00:00:00",
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

    # 设置跟踪委托下单方向，买入委托："buy", 卖出委托: "sell"
    context.user_data.entrust_direction = "sell"
    # 设置触发价格
    context.user_data.trigger_price = 5000
    # 设置回调幅度 (%) - 如设置为1，则回调幅度为 1%
    context.user_data.tracking_range = 1

    # 卖出数量 （若为买入委托，则无需设置）
    context.user_data.sell_entrust_quantity = 10
    # 买入金额 （若为卖出委托，则无需设置）
    context.user_data.buy_entrust_cash_amount = 100000

    # 记录是否达到了否触发价格（此处无需更改）
    context.user_data.price_triggered_flag = False
    # 记录达到触发价格之后，价格所达到的最高（或者最低）值，以计算回调幅度(买入委托记录最低值，卖出委托记录最高值)（此处无需更改）
    context.user_data.max_or_min_price = None
    # 记录是否已经完成订单（无论成功或者失败）（此处无需更改）
    context.user_data.order_completed_flag = False


# 阅读3，策略核心逻辑：
# handle_data函数定义了策略的执行逻辑，按照frequency生成的bar依次读取并执行策略逻辑，直至程序结束。
# handle_data和bar的详细说明，请参考新手学堂的解释文档。
def handle_data(context):
    # 查看委托是否已经下达
    if context.user_data.order_completed_flag:
        context.log.info("跟踪委托已经完成")
        return

    # 获取当前价格
    current_price = context.data.get_current_price(context.security)

    context.log.info("当前价格为 %s 元，触发价格为 %s 元" % (current_price, context.user_data.trigger_price))

    # 买入跟踪委托
    if context.user_data.entrust_direction == "buy":
        # 已经达到了触发价格
        if context.user_data.price_triggered_flag or current_price <= context.user_data.trigger_price:
            context.log.info("已经达到触发价格")
            context.user_data.price_triggered_flag = True
            # 更新价格最小值
            if context.user_data.max_or_min_price is None:
                context.user_data.max_or_min_price = current_price
            else:
                if context.user_data.max_or_min_price > current_price:
                    context.user_data.max_or_min_price = current_price
            # 计算当前回调幅度
            current_range = (current_price / context.user_data.max_or_min_price - 1) * 100
            context.log.info("当前回调幅度为 %.2f%%, 预设回调幅度为 %.2f%%" % (current_range, context.user_data.tracking_range))
            # 当前回调幅度大于等于设置的幅度，则发出委托
            if current_range >= context.user_data.tracking_range:
                context.user_data.order_completed_flag = True
                context.log.info("回调幅度已经满足条件，发出市价单买入委托信号")
                # 账户金钱足够，则执行市价单买入委托
                if context.account.huobi_cny_cash >= context.user_data.buy_entrust_cash_amount:
                    context.log.info("正在买入 %s" % context.security)
                    context.log.info("下单金额为 %s 元，以市价单买入" % context.user_data.buy_entrust_cash_amount)
                    context.order.buy(context.security, cash_amount=str(context.user_data.buy_entrust_cash_amount))
                else:
                    context.log.error("现金不足，无法买入，下单失败")
                    context.log.error("请重新设置买入金额，不要超过现有资金")
            # 回调幅度尚未满足条件
            else:
                context.log.info("回调幅度尚未满足条件，无交易信号，进入下一根bar")
        else:
            context.log.info("尚未达到触发价格")
    # 卖出跟踪委托
    elif context.user_data.entrust_direction == "sell":
        # 已经达到了触发价格
        if context.user_data.price_triggered_flag or current_price >= context.user_data.trigger_price:
            context.log.info("已经达到触发价格")
            context.user_data.price_triggered_flag = True
            # 更新价格最大值
            if context.user_data.max_or_min_price is None:
                context.user_data.max_or_min_price = current_price
            else:
                if context.user_data.max_or_min_price < current_price:
                    context.user_data.max_or_min_price = current_price
            # 计算当前回调幅度
            current_range = (1 - current_price / context.user_data.max_or_min_price) * 100
            context.log.info("当前回调幅度为 %.2f%%, 预设回调幅度为 %.2f%%" % (current_range, context.user_data.tracking_range))
            # 当前回调幅度大于等于设置的幅度
            if current_range >= context.user_data.tracking_range:
                context.user_data.order_completed_flag = True
                context.log.info("回调幅度已经满足条件，发出市价单卖出委托信号")
                # 账户持仓足够，则执行市价单卖出委托
                if context.account.huobi_cny_btc >= context.user_data.sell_entrust_quantity:
                    context.log.info("正在卖出 %s" % context.security)
                    context.log.info("下单数量为 %s，以市价单卖出" % context.user_data.sell_entrust_quantity)
                    context.order.sell(context.security, quantity=str(context.user_data.sell_entrust_quantity))
                else:
                    context.log.error("持仓不足，无法卖出，下单失败")
                    context.log.error("请重新设置卖出数量，不要超过现有持仓")
            # 回调幅度尚未满足条件
            else:
                context.log.info("回调幅度尚未满足条件，无交易信号，进入下一根bar")
        else:
            context.log.info("尚未达到触发价格")
    else:
        context.log.error("委托方向参数 （context.user_data.entrust_direction）设置出错，只能是 'buy' 或者 'sell'")
        context.log.error("请改正后重新运行程序")