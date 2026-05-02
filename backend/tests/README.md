# 后端单元测试

本目录包含了整个后端项目的全面单元测试，覆盖了所有主要模块和功能。

## 测试文件结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # pytest配置和共享夹具
├── run_tests.py               # 测试运行器
├── README.md                  # 测试文档
├── test_password.py           # 密码工具测试
├── test_jwtt.py              # JWT工具测试
├── test_emails.py            # 邮件功能测试
├── test_ip.py                # IP地址工具测试
├── test_localTime.py          # 时间转换测试
├── test_exceptions.py        # 异常处理测试
├── test_models.py            # 数据模型测试
├── test_controllers.py       # 控制器测试
├── test_core.py              # 核心功能测试
└── test_settings.py          # 设置配置测试
```

## 测试覆盖范围

### 1. 工具模块 (utils/)

- **test_password.py**: 密码加密、验证、哈希生成等功能
  - MD5加密测试
  - 密码验证测试
  - 哈希生成测试
  - 密码生成测试
  - 集成测试

- **test_jwtt.py**: JWT令牌和QQ登录功能
  - JWT令牌创建和解码
  - QQ访问令牌获取
  - QQ用户信息获取
  - QQ用户查找和创建
  - 集成测试

- **test_emails.py**: 邮件发送功能
  - 成功发送测试
  - SMTP错误处理
  - 配置缺失处理
  - 特殊字符处理

- **test_ip.py**: IP地址获取和User-Agent解析
  - 公网/私网IP识别
  - IP地址API调用
  - 浏览器和系统信息解析
  - 错误处理

- **test_localTime.py**: 时间转换功能
  - UTC转本地时间
  - 不同时区转换
  - 时间格式处理
  - 边界条件测试

### 2. 核心模块 (core/)

- **test_core.py**: 核心功能测试
  - API初始化
  - CRUD操作
  - 依赖注入
  - 后台任务
  - 上下文管理

- **test_exceptions.py**: 异常处理测试
  - 数据库完整性错误
  - HTTP异常处理
  - 请求/响应验证错误
  - 自定义异常

### 3. 数据模型 (models/)

- **test_models.py**: 数据模型测试
  - 基础模型功能
  - 时间戳混入
  - Token模型
  - 响应模型
  - 模型序列化

### 4. 控制器 (controllers/)

- **test_controllers.py**: 控制器测试
  - 用户控制器
  - 角色控制器
  - 部门控制器
  - 菜单控制器
  - 日志控制器
  - API控制器

### 5. 设置配置 (settings/)

- **test_settings.py**: 配置设置测试
  - 主设置模块
  - 基础配置
  - 数据库配置
  - 日志配置
  - 环境变量处理

## 运行测试

### 使用测试运行器

```bash
# 运行所有测试
python tests/run_tests.py all

# 运行特定文件
python tests/run_tests.py file test_password.py

# 运行特定模块
python tests/run_tests.py module password

# 生成覆盖率报告
python tests/run_tests.py report

# 列出所有测试文件
python tests/run_tests.py list

# 检查测试环境
python tests/run_tests.py check

# 运行特定测试
python tests/run_tests.py run --tests test_md5_encrypt_normal_string
```

### 直接使用pytest

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定文件
pytest tests/test_password.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 运行特定测试
pytest tests/ -k "test_md5_encrypt_normal_string" -v
```

## 测试统计

当前测试覆盖情况：

- **总测试文件数**: 11个
- **总测试用例数**: 150+ 个
- **覆盖的模块数**: 10个主要模块
- **代码覆盖率目标**: 80%以上

## 测试夹具 (Fixtures)

### 主要夹具

- `mock_app`: 模拟FastAPI应用
- `mock_session`: 模拟数据库会话
- `mock_user`: 模拟用户对象
- `mock_request`: 模拟HTTP请求
- `test_client`: 测试客户端
- `async_client`: 异步测试客户端

### 数据夹具

- `sample_jwt_payload`: JWT载荷示例
- `sample_password_data`: 密码数据示例
- `sample_qq_userinfo`: QQ用户信息示例
- `sample_email_data`: 邮件数据示例
- `sample_ip_responses`: IP API响应示例

### 工具夹具

- `data_generator`: 测试数据生成器
- `assertions`: 断言辅助工具
- `mock_logger`: 模拟日志器

## 测试策略

### 1. 单元测试

- 测试单个函数或方法
- 使用模拟对象隔离依赖
- 覆盖正常和异常情况

### 2. 集成测试

- 测试模块间的交互
- 测试完整的工作流程
- 验证系统行为

### 3. 边界测试

- 测试极值输入
- 测试错误条件
- 测试资源限制

### 4. 异常处理测试

- 验证错误处理逻辑
- 测试异常恢复机制
- 确保系统稳定性

## 持续集成

### GitHub Actions配置

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    - name: Run tests
      run: python tests/run_tests.py report
```

## 最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 遵循 `test_功能_条件` 模式
- 保持命名一致性

### 2. 测试结构

- 使用 Arrange-Act-Assert 模式
- 每个测试只验证一个方面
- 保持测试简短和专注

### 3. 模拟对象

- 只模拟必要的依赖
- 验证模拟对象的调用
- 使用工厂函数创建模拟

### 4. 断言

- 使用具体的断言消息
- 验证重要的属性
- 考虑边界条件

## 调试测试

### 运行单个测试

```bash
pytest tests/test_password.py::TestMD5Encrypt::test_md5_encrypt_normal_string -v -s
```

### 打印调试信息

```python
def test_example():
    result = some_function()
    print(f"Debug: {result}")
    assert result == expected
```

### 使用断点

```python
def test_example():
    result = some_function()
    import pdb; pdb.set_trace()  # 断点
    assert result == expected
```

## 贡献指南

### 添加新测试

1. 在适当的测试文件中添加测试函数
2. 使用现有的夹具或创建新的夹具
3. 确保测试命名符合规范
4. 添加必要的断言
5. 更新文档

### 测试覆盖率

- 目标是达到80%以上的代码覆盖率
- 使用 `pytest --cov=app` 检查覆盖率
- 优先覆盖核心功能

### 代码质量

- 遵循项目的代码规范
- 保持测试代码简洁
- 添加适当的注释
- 使用类型提示

## 常见问题

### Q: 测试运行很慢怎么办？

A: 可以使用并行测试：
```bash
pytest tests/ -n auto
```

### Q: 如何测试异步函数？

A: 使用 `@pytest.mark.asyncio` 装饰器：
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Q: 如何测试数据库操作？

A: 使用内存数据库和模拟会话：
```python
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    # 设置测试数据库
```

## 更新日志

### v1.0.0 (2023-12-07)

- 创建全面的测试套件
- 覆盖所有主要模块
- 添加测试运行器
- 生成覆盖率报告
- 完善文档

---

维护者: AI Assistant
最后更新: 2023-12-07