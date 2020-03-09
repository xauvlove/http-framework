package com.xauvlove.framework.httpframework.controller;

import com.xauvlove.framework.httpframework.OrderHandlers.OrderHandler;
import com.xauvlove.framework.httpframework.OrderHandlers.OrderHandlerContext;
import com.xauvlove.framework.httpframework.UserLoginCheck;
import com.xauvlove.framework.httpframework.components.LoginInterceptor;
import com.xauvlove.framework.httpframework.components.UserParameterResolver;
import com.xauvlove.framework.httpframework.pojo.User;
import com.xauvlove.framework.httpframework.service.MyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Import;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("test1")
@Import(User.class)
public class TestController {

    @Autowired
    private MyService myService;
    @Autowired
    private ApplicationContext applicationContext;
    @Autowired
    private OrderHandlerContext handlerContext;

    /**
     * 基础测试
     * 测试自定义注解，检查用户是否登录
     * <>包括拦截器 {@link LoginInterceptor} 参数检查器{@link UserParameterResolver}</>
     * @param userId
     * @param name
     * @return
     */
    @GetMapping("/testMethod")
    public String test(@UserLoginCheck Long userId,
                       @RequestParam("name") String name) {
        int i = 0;
        int a = 1;
        return userId + " " + name;
    }


    /**
     * 测试 AOP
     * @param aop
     * @return
     */
    @GetMapping("/testAop/{aop}")
    public String testAop(@PathVariable("aop") String aop) {
        return aop;
    }

    private void test() {
        System.out.println("重复注入");
    }


    /**
     * 测试 @Import{User.class} 注入
     * @return
     */
    @GetMapping("/testAutowire")
    public String testAutowire() {

        System.out.println(applicationContext.getBean("user"));
        return "testAutowire";
    }


    /**
     * 测试策略模式
     * @param type
     * @return
     */
    @GetMapping("/order/testStrategyMode/{type}")
    public String testStrategyMode(@PathVariable("type") Integer type) {
        OrderHandler orderHandler = handlerContext.getInstance(type);
        System.out.println(orderHandler.handleOrder());
        return "testAutowire";
    }
}
