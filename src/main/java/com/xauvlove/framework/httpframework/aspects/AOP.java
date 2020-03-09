package com.xauvlove.framework.httpframework.aspects;

import org.aspectj.lang.annotation.Pointcut;

public class AOP {

    @Pointcut("execution(* com.xauvlove.framework.httpframework.controller.*.testAop(..))")
    public void pointCutMethodAnnotation(){
        System.out.println("pointCutMethodAnnotation");
    }
}
