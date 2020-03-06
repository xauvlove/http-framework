package com.xauvlove.framework.httpframework.pojo;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class MyProxy implements InvocationHandler {

    Object object;

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        if(method.getName().equals("login1")) {
            System.out.println("代理运行 login1");
            method.invoke(object, args);
        } else {
            System.out.println("代理运行 login2");
            method.invoke(object, args);
        }
        return 1;
    }

    public Object createProxy() {
        return Proxy.newProxyInstance(User.class.getClassLoader(), User.class.getInterfaces(),this);
    }

    public static void main(String[] args) {
        MyProxy myProxy = new MyProxy();
        myProxy.object = new User();
        Object proxyInstance = myProxy.createProxy();
        User user = (User)(proxyInstance);
        user.login1();
    }
}
