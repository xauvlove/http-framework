package com.xauvlove.framework.httpframework;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

@SpringBootApplication
@EnableAspectJAutoProxy
public class HttpFrameworkApplication {
    public static void main(String[] args) {
        SpringApplication.run(HttpFrameworkApplication.class, args);
    }
}
