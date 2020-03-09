package com.xauvlove.framework.httpframework.pojo;

import lombok.Data;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Import;
import org.springframework.stereotype.Component;

@Data

@Component
public class User implements MyInterfacce{
    private Long userId;
    private String name;

   public void login1() {
       System.out.println("login1");
   }

   public void login2(int param) {
       System.out.println("login2");
   }
}
