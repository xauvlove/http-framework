package com.xauvlove.framework.httpframework.components;

import com.xauvlove.framework.httpframework.UserLoginCheck;
import org.springframework.core.MethodParameter;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

public class UserParameterResolver implements HandlerMethodArgumentResolver {

    @Override
    public boolean supportsParameter(MethodParameter methodParameter) {
        return methodParameter.hasParameterAnnotation(UserLoginCheck.class);
    }

    @Override
    public Object resolveArgument(MethodParameter methodParameter,
                                  ModelAndViewContainer modelAndViewContainer,
                                  NativeWebRequest nativeWebRequest,
                                  WebDataBinderFactory webDataBinderFactory) throws Exception {
        System.out.println("判断了参数");
        System.out.println("userId="+nativeWebRequest.getAttribute(
                "userId", RequestAttributes.SCOPE_REQUEST));
        return nativeWebRequest.getAttribute("userId", RequestAttributes.SCOPE_REQUEST);
    }
}