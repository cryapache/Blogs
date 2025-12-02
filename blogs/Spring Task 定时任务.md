---
post_id: 19297980
---

# Spring Task 定时任务

## Spring Task使用步骤

### 导入maven坐标Spring-context

```xml
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-context</artifactId>
    <version>5.3.x</version> <!-- 或使用 Spring Boot 管理版本 -->
</dependency>
```

### 添加启动类注解@EnableScheduling

```java
@EnableScheduling
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```



### 自定义定时任务类

- 创建一个定时任务类，注解`@Component`
- 定时任务类中写定时任务方法，注解`@Scheduled(cron = "cron表达式")`

完成后会按照cron表达式定时调用定时任务方法实现方法逻辑，表达式可以直接使用工具生成：[Cron - 在线Cron表达式生成器](https://cron.ciding.cc/)

```java
@Component
public class MyScheduledTask {

    @Scheduled(cron = "0 0 2 * * ?") // 每天凌晨2点执行
    public void dailyTask() {
        System.out.println("执行每日定时任务：" + LocalDateTime.now());
    }

    @Scheduled(fixedRate = 5000) // 每隔5秒执行一次（从上次任务开始算起）
    public void fixedRateTask() {
        System.out.println("fixedRate 任务执行：" + System.currentTimeMillis());
    }

    @Scheduled(fixedDelay = 3000) // 上次任务结束后3秒再执行下一次
    public void fixedDelayTask() {
        System.out.println("fixedDelay 任务执行：" + System.currentTimeMillis());
    }

    @Scheduled(initialDelay = 2000, fixedRate = 6000) // 应用启动后延迟2秒，之后每6秒执行
    public void initialDelayTask() {
        System.out.println("带初始延迟的任务执行");
    }
}
```

### 注意事项

- 定时任务方法必须是 `public void` 且无参

- **默认单线程执行**：所有 `@Scheduled` 任务共享一个线程，若某任务阻塞，会影响其他任务
- **异常处理**：若任务抛出未捕获异常，该任务将停止后续执行！建议在方法内 try-catch