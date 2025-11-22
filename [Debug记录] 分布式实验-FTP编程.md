
### 用来结束多行响应的空行没有被读走

服务端发送响应的方法是这么写的

```java
// 发送多行响应，最后以空行结束
private void sendMultiLine(String... lines) {
    for (String l : lines) writer.println(l);
    writer.println(); // 结束空行
}
```

而客户端我一开始是直接按行读取，遇到空行结束：

```java
// 读取多行直到遇到空行
while (line = tcpReader.readLine()) != null && !line.isEmpty()) {
    sb.append(line).append('\n');
    line = tcpReader.readLine();
}
```

但这样写有时会有空行不能被正确读走，测试时输入了下一个命令才返回上一个命令的结果，显然是不对的。

最后在前面加上循环，每次读取时先把前面的空行读完再开始读内容

```java
while ((line = tcpReader.readLine()) != null && line.isEmpty()) {
    // 跳过前导空行
}

// 读取多行直到遇到空行
while (line != null && !line.isEmpty()) {
    sb.append(line).append('\n');
    line = tcpReader.readLine();
}
```



### 保存文件之前没有检查目录是否存在、文件名是否合法

使用`get`命令下载文件时直接写了这么一句，以项目路径+`get`的参数来作为下载路径

```java
Path localFile = Paths.get(fileName).toAbsolutePath().normalize();
```

这里的问题有两个：

#### 文件名不一定合法

前文对命令的校验只检查了命令本身是否合法，对应的文件存不存在是服务端考虑的时，就没有再考虑过，但是文件存在不代表命令参数中的`fileName`是合法的文件名。文件名参数有可能形如`RelativeDir/fileName`，此时相当于在项目目录下创建以此为名称的文件，显然是不可以的。

我的解决方案是在下载文件之前将参数`fileName`改为只保留文件名的形式

```java
fileName = fileName.substring(fileName.lastIndexOf('/') + 1); 
```



#### 下载路径不一定要放在项目目录，不应该写死，并且在设置下载路径时应该检查路径是否存在，如果不存在应该及时创建

我的解决方案是在构造函数中就将文件保存目录确定下来：
```java
// 设置本地文件保存目录
localFileDir = Paths.get(".").toAbsolutePath().normalize().resolve("downloads");
System.out.println("本地文件保存目录: " + localFileDir);
if (!Files.exists(localFileDir)) {
	try {
    	Files.createDirectories(localFileDir);
    } catch (IOException e) {
        System.err.println("无法创建本地文件保存目录: " + e.getMessage());
    }
}
```



### 客户端监听的端口和服务器监听的端口是两码事，不能搞混

服务端中设定好了TCP和UDP端口，但客户端程序编写时只留意设定了服务端的端口。

TCP还好，毕竟是双向连接，但UDP是单向的，服务器监听端口`UDP_PORT`和客户端监听的UDP端口是两码事。于是我的程序里服务端早早发完了文件，而客户端还阻塞在苦苦等待服务端的第一个分片。

但本地运行服务端是`UDP_PORT`是被占用的，而且客户端也不需要固定的UDP端口来确保能被连接上。所以我的解决方案是在发送命令时给结尾附加一个端口参数，确保服务端可以明确需要向哪里发送文件。

### Windows的文件名允许空格，注意分割命令的操作
我最开始对命令简单粗暴直接按照空格分割
```JAVA
String[] seg = line.split("\\s+", 3); // 分割命令和参数  
String cmd = seg[0].toLowerCase();               // 命令，模糊大小写  
String arg = seg.length > 1 ? seg[1] : "";       // 参数  
int clientUdpPort = seg.length > 2 ? Integer.parseInt(seg[2]) : -1; // 客户端UDP端口
```
如果只有命令和对应的一个参数，其实直接按第一个空格分割为两份即可，但是我还跟了Upd监听端口的参数，所以还需要找到最后一个空格对此做分割：
```java
String[] seg = line.split("\\s+", 2); // 分割命令和参数  
String cmd = seg[0].toLowerCase();               // 命令，模糊大小写  
int lastSpace = seg[1].lastIndexOf(' ');  
String arg = lastSpace == -1 ? seg[1] : seg[1].substring(0, lastSpace).trim();   // 参数，第一个和最后一个空格之间的内容  
int clientUdpPort = lastSpace == -1 ?                                            // 客户端UDP端口  
        -1 :  
        Integer.parseInt(seg[1].substring(lastSpace + 1).trim());      // 最后一个空格以后的内容
```
### 创建的Socket连接都应该显式关闭并进行异常处理
否则如果关闭不当可能会占用对应端口

### 目录...可能会被认为是合法目录
因为cd的处理有对.../返回上一级的处理，意外导致`cd ...`不会报任何错误而是进入到一个不存在的`...`目录。显然windows是不允许这种目录名的，加一行判断目录名是否仅由`.`组成的判断解决。