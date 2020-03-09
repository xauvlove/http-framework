package com.xauvlove.framework.httpframework.OrderHandlers.handlers;

import com.xauvlove.framework.httpframework.HandleOrderType;
import com.xauvlove.framework.httpframework.OrderHandlers.OrderHandler;
import org.springframework.stereotype.Component;

@HandleOrderType(3)
@Component
public class PromotionOrderHandler implements OrderHandler {
    @Override
    public String handleOrder() {
        return "handle promotion order";
    }
}
