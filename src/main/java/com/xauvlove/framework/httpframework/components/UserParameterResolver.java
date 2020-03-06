package com.xauvlove.framework.httpframework.components;

import com.xauvlove.framework.httpframework.TestAnnotation;
import org.springframework.core.MethodParameter;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

import java.util.Arrays;

public class UserParameterResolver implements HandlerMethodArgumentResolver {

    @Override
    public boolean supportsParameter(MethodParameter methodParameter) {
        return methodParameter.hasParameterAnnotation(TestAnnotation.class);
    }

    @Override
    public Object resolveArgument(MethodParameter methodParameter, ModelAndViewContainer modelAndViewContainer, NativeWebRequest nativeWebRequest, WebDataBinderFactory webDataBinderFactory) throws Exception {
        System.out.println("判断了参数");
        //throw new Exception();

        //System.out.println("userId=" + nativeWebRequest.getAttribute("userId", RequestAttributes.SCOPE_REQUEST));
        System.out.println("userId="+nativeWebRequest.getAttribute("userId", RequestAttributes.SCOPE_REQUEST));
        return nativeWebRequest.getAttribute("userId", RequestAttributes.SCOPE_REQUEST);
    }
}
