package com.xauvlove.framework.httpframework.OrderHandlers;

import lombok.Data;
import java.util.Map;

@Data
public class OrderHandlerContext {

    private Map<Integer, Class<? extends OrderHandler>> orderHandlerMap;

    public OrderHandlerContext(Map<Integer, Class<? extends OrderHandler>> orderHandlerMap) {
        this.orderHandlerMap = orderHandlerMap;
    }

    public OrderHandler getInstance(Integer type) {
        try {
            return orderHandlerMap.get(type).getConstructor().newInstance();
        } catch (Exception e) {
            return null;
        }
    }
}
