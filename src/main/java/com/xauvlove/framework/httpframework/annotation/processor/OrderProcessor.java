package com.xauvlove.framework.httpframework.annotation.processor;

import com.xauvlove.framework.httpframework.HandleOrderType;
import com.xauvlove.framework.httpframework.OrderHandlers.*;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.context.ResourceLoaderAware;
import org.springframework.context.annotation.Import;
import org.springframework.core.annotation.MergedAnnotation;
import org.springframework.core.annotation.MergedAnnotations;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.core.io.support.ResourcePatternResolver;
import org.springframework.core.io.support.ResourcePatternUtils;
import org.springframework.core.type.AnnotationMetadata;
import org.springframework.core.type.ClassMetadata;
import org.springframework.core.type.classreading.CachingMetadataReaderFactory;
import org.springframework.core.type.classreading.MetadataReader;
import org.springframework.core.type.classreading.MetadataReaderFactory;
import org.springframework.stereotype.Component;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@Component
public class OrderProcessor implements BeanFactoryPostProcessor{
    private final static String ORDER_HANDLER_PACKAGE
            = "classpath:com/xauvlove/framework/httpframework/OrderHandlers/handlers/*.class";

    private ResourceLoader resourceLoader = null;
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        Map<Integer, Class<? extends OrderHandler>> orderHandlerMap = new HashMap<>(3);
        /**
         * 此处应该扫描  OrderHandler 的所有实现类，然后获取实现类注解(HandleOrderType)，添加到map
         * 而不是直接填入 1 2 3， class <>直接填入就算没有{@link HandleOrderType}  也是可以的</>
         */
        ResourcePatternResolver resolver = ResourcePatternUtils.getResourcePatternResolver(resourceLoader);
        MetadataReaderFactory metaReader = new CachingMetadataReaderFactory(resourceLoader);
        Resource[] resources;
        try {
             resources = resolver.getResources(ORDER_HANDLER_PACKAGE);
            for (Resource r : resources) {
                MetadataReader reader = metaReader.getMetadataReader(r);
                AnnotationMetadata annotationMetadata = reader.getAnnotationMetadata();
                MergedAnnotations annotations = annotationMetadata.getAnnotations();
                MergedAnnotation<HandleOrderType> handleOrderTypeMergedAnnotation =
                        annotations.get(HandleOrderType.class);
                if (handleOrderTypeMergedAnnotation.isPresent()) {
                    String className = annotationMetadata.getClassName();
                    Class<? extends OrderHandler> clazz =
                            (Class<? extends OrderHandler>) Class.forName(className);
                    int type = clazz.getAnnotation(HandleOrderType.class).value();
                    orderHandlerMap.put(type, clazz);
                }
            }
        } catch (IOException | ClassNotFoundException e) {
            e.printStackTrace();
        }
        OrderHandlerContext orderHandlerContext = new OrderHandlerContext(orderHandlerMap);
        beanFactory.registerSingleton(OrderHandlerContext.class.getName(), orderHandlerContext);
    }
}
