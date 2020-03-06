package com.xauvlove.framework.httpframework.controller;

import com.xauvlove.framework.httpframework.TestAnnotation;
import com.xauvlove.framework.httpframework.pojo.User;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("test")
public class TestController {

    //@RequestMapping(method = RequestMethod.GET, value = "testMethod")
    @GetMapping("/testMethod")
    public String test(@TestAnnotation Long userId,
                     @RequestParam("name") String name) {
        int i = 0;
        int a = 1;
        return userId + " " + name;
    }

    /*@GetMapping("/testMethod2")
    public String test2(@TestAnnotation Long userId,
                       @RequestParam("name") String name) {

    }*/
}
