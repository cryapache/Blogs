# redis入门
基于内存的Key-Value结构数据库

- 基于内存存储，读写性能高
- 适合存储频繁访问的热点数据

### Redis-x64
**启动命令**： 
```
redis-server.exe redis.conf
```
默认端口号`6379`   

**连接命令**：
```
redis-cli.exe
```
或者显示指定ip与端口
```
redis-cli.exe -h [host] -p [port]
```

> 可以使用带图形界面的`Another Redis Desktop Manager`操作

### 数据类型
- `string` 字符串
- `hash`   类似Map
- `list`   列表，类似链表
- `set`    集合
- `sorted set`    有序集合

### 常用命令
#### 字符串操作
|命令|作用|
|---|---|
|SET key value|设置key的value|
|GET key|获取key的value|
|SETEX key seconds value|设置key的value并指定有效时间为seconds|
|SETNX key value|只在key不存在时设定value|
#### 哈希操作
|命令|作用|
|---|---|
|HSET key field value|设置key中field字段的value|
|HGET key field|获取key中field字段的value|
|HDEL key field|删除field字段|
|HKEYS|获取表中所有字段|
|HVALS|获取表中所有value|
#### 列表操作
|命令|作用|
|--- |---|
|LPUSH key value1 [values...]|从左侧插入一个或多个元素|
|LRANGE key start end|获取start到end范围内的元素|
|RPOP key|获取最右侧的值并删除元素|
|LLEN key|获取列表长度|
#### 集合操作
|命令|作用|
|---|---|
|SADD key member1 [members...]|向集合中添加一个或多个成员|
|SREM key member1 [members...]|在集合中删除一个或多个成员|
|SMEMBERS key|返回集合中所有成员|
|SCARD key|返回集合中成员数|
|SINTER key1 [keys...]|返回给定集合的交集|
|SINTER key1 [keys...]|返回给定集合的并集|
#### 有序集合操作
|命令|作用|
|---|---|
|ZADD key score1 member1 [score2 member2...]|向有序集合中添加一个或多个成员，指定分数score|
|ZREM key member1 [members...]|在有序集合中删除一个或多个成员|
|ZRANGE key start end [WITHSCORES]|返回有序集合中指定范围内的成员，按分数从低到高排序|
|ZINCRBY key increment member|为有序集合中的指定成员的分数加上增量increment|
#### 其他常用命令
|命令|作用|
|---|---|
|TYPE key|返回key的数据类型|
|EXISTS key|检查指定key是否存在|
|DEL key|删除指定key|

## 使用JAVA操作Redis
因为在学习spring，所以下面使用`Spring Data Redis`来操作Redis数据库

### 操作流程
#### 引入依赖
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

#### 配置文件
```properties
# application.yml
spring:
    redis:
        host: localhost
        port: 6379
```
> 注意开发环境和生产环境的配置分离，可以采用引用的方式使用

#### 编写配置类`RedisTemplate`
#### 通过`RedisTemplate`操作Redis

