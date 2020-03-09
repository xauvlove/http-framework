package com.xauvlove.framework.httpframework.service;

import org.aspectj.lang.annotation.After;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.springframework.stereotype.Service;

@Service
@Aspect
public class MyService {

    @Before("com.xauvlove.framework.httpframework.aspects.AOP.pointCutMethodAnnotation()")
    public void doService() {
        System.out.println("before doService");
    }
    @After("com.xauvlove.framework.httpframework.aspects.AOP.pointCutMethodAnnotation()")
    public void doService2() {
        System.out.println("after doService");
    }
}
