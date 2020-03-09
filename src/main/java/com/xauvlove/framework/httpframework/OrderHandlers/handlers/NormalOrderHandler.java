package com.xauvlove.framework.httpframework.OrderHandlers.handlers;

import com.xauvlove.framework.httpframework.HandleOrderType;
import com.xauvlove.framework.httpframework.OrderHandlers.OrderHandler;
import org.springframework.stereotype.Component;

@HandleOrderType(1)
@Component
public class NormalOrderHandler implements OrderHandler {

    @Override
    public String handleOrder() {
        return "handle normal order";
    }
}
