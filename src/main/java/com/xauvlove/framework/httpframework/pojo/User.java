package com.xauvlove.framework.httpframework.pojo;

import lombok.Data;

@Data
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
