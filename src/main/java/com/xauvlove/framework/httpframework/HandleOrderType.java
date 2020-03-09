package com.xauvlove.framework.httpframework;

import java.lang.annotation.*;

@Target(ElementType.TYPE)
@Documented
@Retention(RetentionPolicy.RUNTIME)
public @interface HandleOrderType {
    int value();
}
