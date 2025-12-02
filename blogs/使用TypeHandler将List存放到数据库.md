---
post_id: 19297982
---

# 使用 MyBatis TypeHandler 将 `List<String>` 存储为 JSON 字符串到数据库

在实际开发中，我们经常需要将一个列表（如用户标签、年级范围、科目列表等）持久化到数据库。传统做法是新建关联表，但当数据结构简单、无需复杂查询时，**直接将 `List` 序列化为 JSON 字符串存入单个字段**显然更加轻量高效。

## 操作步骤

### 编写 `TypeHandler`

MyBatis 提供 `TypeHandler` 接口，用于处理 Java 类型与 JDBC 类型之间的转换。可以创建`ListToJsonTypeHandler`用于格式转换

```java
package io.tutor.common.utils.typehandler;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedJdbcTypes;
import org.apache.ibatis.type.MappedTypes;

import java.sql.*;
import java.util.Collections;
import java.util.List;

/**
 * 将 List<String> 与数据库中的 JSON 字符串相互转换
 */
@MappedTypes(List.class)
@MappedJdbcTypes({JdbcType.VARCHAR, JdbcType.LONGVARCHAR, JdbcType.CLOB})
public class ListToJsonTypeHandler extends BaseTypeHandler<List<String>> {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    // Java → DB
    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, List<String> parameter, JdbcType jdbcType) throws SQLException {
        try {
            String json = objectMapper.writeValueAsString(parameter);
            ps.setString(i, json);
        } catch (JsonProcessingException e) {
            throw new SQLException("List 转 JSON 失败", e);
        }
    }

    // DB → Java（三种读取方式）
    @Override
    public List<String> getNullableResult(ResultSet rs, String columnName) throws SQLException {
        return parseJson(rs.getString(columnName));
    }

    @Override
    public List<String> getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        return parseJson(rs.getString(columnIndex));
    }

    @Override
    public List<String> getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        return parseJson(cs.getString(columnIndex));
    }

    private List<String> parseJson(String json) throws SQLException {
        if (json == null || json.trim().isEmpty()) {
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            throw new SQLException("JSON 转 List 失败: " + json, e);
        }
    }
}
```

### 在Mapper中使用`TypeHandler`

#### 实体类示例

```java
public class TeacherInfo {
    private Long userId;
    private List<String> grades;   // 如 ["high_1", "high_2"]
    private List<String> subjects; // 如 ["math", "chinese"]
    // getter/setter...
}
```

#### 查询示例（反序列化）

```xml
<resultMap id="TeacherInfoResultMap" type="TeacherInfo">
    <result property="userId" column="user_id"/>
    <result property="grades" column="grades"
            typeHandler="io.tutor.common.utils.typehandler.ListToJsonTypeHandler"/>
    <result property="subjects" column="subjects"
            typeHandler="io.tutor.common.utils.typehandler.ListToJsonTypeHandler"/>
</resultMap>

<select id="selectTeacherInfoByUserId" resultMap="TeacherInfoResultMap">
    SELECT * FROM teacher_info WHERE user_id = #{userId}
</select>
```

#### 插入/更新示例（序列化）

```xml
<insert id="insertTeacherInfo">
    INSERT INTO teacher_info (user_id, grades, subjects)
    VALUES (
        #{userId},
        #{grades, typeHandler=io.tutor.common.utils.typehandler.ListToJsonTypeHandler},
        #{subjects, typeHandler=io.tutor.common.utils.typehandler.ListToJsonTypeHandler}
    )
</insert>

<update id="updateTeacherInfo">
    UPDATE teacher_info
    SET
        grades = #{grades, typeHandler=io.tutor.common.utils.typehandler.ListToJsonTypeHandler},
        subjects = #{subjects, typeHandler=io.tutor.common.utils.typehandler.ListToJsonTypeHandler}
    WHERE user_id = #{userId}
</update>
```

> 🔸 **关键**：必须在 `#{}` 中显式指定 `typeHandler`
