package com.xauvlove.framework.httpframework.myspringboot;

import org.json.JSONObject;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class MySpringApplication {

    final static String url = "http://localhost:9200/goods/docs";
    final static String params = "{\n" +
            "\"all\":\"华为 麦芒5 全网通 4GB+64GB版 华为（HUAWEI）Category(id=74, name=手机, parentId=0, isParent=true, sort=2) Category(id=75, name=手机通讯, parentId=74, isParent=true, sort=1) Category(id=76, name=手机, parentId=75, isParent=false, sort=1)\",\n" +
            "\"subTitle\":\"光学防抖，持久续航！后置1600万像素，金属机身！<a href='http://item.jd.com/5148371.html?from_saf=1' target='_blank'>全面屏麦芒6低至2099元！</a>\",\n" +
            "\"skus\":\"[{image:http://image.leyou.com/images/9/13/1524297318952.jpg,price:139900,id:3234250,title:华为 麦芒5 全网通 4GB+64GB版 香槟金 移动联通电信4G手机 双卡双待},{image:http://image.leyou.com/images/7/11/1524297319511.jpg,price:159900,id:3980563,title:华为 麦芒5 全网通 4GB+64GB版 苍穹灰 移动联通电信4G手机 双卡双待}]\"\n" +
            "}";

    public static void main(String[] args) {

        String res = post(url, params);
        System.out.println(res);

    }


    /**
     * 发送HttpPost请求
     *
     * @param strURL
     *            服务地址
     * @param params
     *            json字符串,例如: "{ \"id\":\"12345\" }" ;其中属性名必须带双引号<br/>
     * @return 成功:返回json字符串<br/>
     */
    public static String post(String strURL, String params) {
        System.out.println(strURL);
        System.out.println(params);
        BufferedReader reader = null;
        try {
            URL url = new URL(strURL);// 创建连接
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setDoOutput(true);
            connection.setDoInput(true);
            connection.setUseCaches(false);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestMethod("POST"); // 设置请求方式
            // connection.setRequestProperty("Accept", "application/json"); // 设置接收数据的格式
            connection.setRequestProperty("Content-Type", "application/json"); // 设置发送数据的格式
            connection.connect();
            //一定要用BufferedReader 来接收响应， 使用字节来接收响应的方法是接收不到内容的
            OutputStreamWriter out = new OutputStreamWriter(connection.getOutputStream(), "UTF-8"); // utf-8编码
            out.append(params);
            out.flush();
            out.close();
            // 读取响应
            reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), "UTF-8"));
            String line;
            String res = "";
            while ((line = reader.readLine()) != null) {
                res += line;
            }
            reader.close();

            //如果一定要使用如下方式接收响应数据， 则响应必须为: response.getWriter().print(StringUtils.join("{\"errCode\":\"1\",\"errMsg\":\"", message, "\"}")); 来返回
//            int length = (int) connection.getContentLength();// 获取长度
//            if (length != -1) {
//                byte[] data = new byte[length];
//                byte[] temp = new byte[512];
//                int readLen = 0;
//                int destPos = 0;
//                while ((readLen = is.read(temp)) > 0) {
//                    System.arraycopy(temp, 0, data, destPos, readLen);
//                    destPos += readLen;
//                }
//                String result = new String(data, "UTF-8"); // utf-8编码
//                System.out.println(result);
//                return result;
//            }

            return res;
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        return "error"; // 自定义错误信息
    }

}
