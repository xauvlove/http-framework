package com.xauvlove.framework.httpframework.OrderHandlers.handlers;

import com.xauvlove.framework.httpframework.HandleOrderType;
import com.xauvlove.framework.httpframework.OrderHandlers.OrderHandler;
import org.springframework.stereotype.Component;

@HandleOrderType(2)
@Component
public class GroupOrderHandler implements OrderHandler {
    @Override
    public String handleOrder() {
        return "handleOrder";
    }
}
