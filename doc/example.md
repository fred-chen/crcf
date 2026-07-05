# CRCF 使用示例

## 1. 构造一个 Target

CRCF 提供两种方式来创建 Target 对象：**工厂函数** `gettarget()` 和**直接构造**。

### 1.1 使用 `gettarget()` 工厂函数（推荐）

`gettarget()` 会自动建立连接、检测目标类型，并返回合适的 Target 子类实例。

```python
from crcf import gettarget

# 基本用法：指定主机地址、用户名和密码
target = gettarget("10.1.0.96", "root", "password")

# 指定连接服务和超时时间
target = gettarget("10.1.0.96", "root", "password", svc="ssh", timeout=120)
```

`gettarget()` 的参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | — | 目标主机 IP 地址或域名 |
| `username` | `str` | `None` | 登录用户名，`None` 时使用当前系统用户 |
| `password` | `str` | `None` | 登录密码 |
| `svc` | `str` | `"ssh"` | 连接服务类型，可选 `"ssh"`、`"telnet"`、`"shell"` |
| `timeout` | `int` | `60` | 超时秒数 |

> **注意**：当前 `gettarget()` 的自动检测仅支持 Linux 类型，会返回 `LinuxTarget` 实例。

### 1.2 直接构造 Target

如果已有连接对象，或需要指定特定子类型，可以直接构造：

```python
from crcf.linuxtarget import LinuxTarget

# 直接构造 LinuxTarget
target = LinuxTarget("10.1.0.96", svc="ssh", username="root", password="password")

# 传入已有连接对象
from crcf.sshconnection import SshConnection
conn = SshConnection("10.1.0.96", "root", "password", timeout=30)
target = LinuxTarget("10.1.0.96", svc="ssh", username="root", password="password", conn=conn)
```

`Target.__init__()` 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `address` | `str` | — | 目标主机地址 |
| `svc` | `str` | `"ssh"` | 连接服务类型 |
| `username` | `str` | `"root"` | 用户名 |
| `password` | `str` | `None` | 密码 |
| `conn` | `Connection` | `None` | 已有连接对象 |
| `timeout` | `int` | `60` | 超时秒数 |

## 2. 从 Target 中获取 Shell

每个 Target 对象内部已有一个默认 Shell，可通过 `target.shell` 访问。也可以创建额外的 Shell 对象，每个 Shell 对应一个独立的连接和后台线程。

```python
# 使用 Target 内部默认的 Shell
shell = target.shell

# 创建一个新 Shell（每次调用创建独立连接和线程）
shell = target.newshell()

# 使用已有连接创建 Shell（复用连接，节省资源）
shell = target.newshell(conn=existing_conn)
```

`target.newshell(conn=None)` 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `conn` | `Connection` | `None` | 复用的已有连接，`None` 则新建连接 |

每个 Shell 对象内部有一个**命令队列**和**后台线程**，命令按入队顺序依次执行。一个 Target 可以有多个 Shell，实现真正的并发。

## 3. 通过 Shell 执行命令

Shell 的核心方法是 `shell.exe()`，它会将命令发送给远程目标执行，并返回一个 `Command` 对象。

### 3.1 同步执行（默认）

```python
# wait=True（默认），阻塞等待命令执行完成
command = shell.exe("uname -a")
```

### 3.2 异步执行

```python
# wait=False，立即返回 Command 对象，不阻塞
command = shell.exe("sleep 100", wait=False)

# 后续处理其他任务...

# 等待命令完成
command.wait()
```

### 3.3 并发执行示例

```python
# 创建多个 Target
targets = [
    gettarget("host1.example.com", "root", "password", timeout=30),
    gettarget("host2.example.com", "root", "password", timeout=30),
    gettarget("host3.example.com", "root", "password", timeout=30),
]

# 在每个 Target 上创建 Shell 并异步执行命令
commands = []
for t in targets:
    sh = t.newshell()
    cmd = sh.exe("uname -a", wait=False)  # 异步
    commands.append(cmd)

# 其他任务...

# 等待所有命令完成
for cmd in commands:
    cmd.wait()

# 检查每个命令结果
for cmd in commands:
    if cmd.succ():
        print("OK:", cmd.get_cmdline())
    else:
        print("FAIL:", cmd.get_cmdline(), "exit:", cmd.get_exitcode())
```

`shell.exe()` 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cmdline` | `str` | — | 要执行的命令 |
| `wait` | `bool` | `True` | `True` 阻塞等待完成，`False` 立即返回 |
| `log` | `bool` | `True` | 是否打印执行结果日志 |
| `longrun_report` | `int` | `1800` | 长时间运行命令的进度报告间隔（秒） |
| `wait_report` | `int` | `30` | 等待中的进度报告间隔（秒） |

返回值：`Command` 对象。

## 4. 获取命令结果

`shell.exe()` 返回的 `Command` 对象包含命令的完整执行信息。

### 4.1 基本状态检查

```python
command = shell.exe("ls -l /tmp")

# 是否执行完成
print(command.done())  # True

# 是否成功（退出码为 0）
print(command.succ())  # True / False

# 是否失败（退出码非 0）
print(command.fail())  # True / False

# 打印命令的完整信息（含 stdout、stderr、exit code、耗时）
print(command)
```

### 4.2 获取命令输出

```python
command = shell.exe("echo hello")

# 获取 stdout 字符串
stdout = command.get_stdout()

# 获取 stderr 字符串
stderr = command.get_stderr()

# 获取退出码
exit_code = command.get_exitcode()

# 获取命令原文
cmdline = command.get_cmdline()

# 获取执行耗时（毫秒）
print(command.dur)
```

### 4.3 按类型解析输出

```python
# 解析为整数
command = shell.exe("echo 42")
result = command.getint()  # 42

# 解析为浮点数
command = shell.exe("echo 3.14")
result = command.getfloat()  # 3.14

# 解析为列表（按指定分隔符）
command = shell.exe("ls /tmp")
files = command.getlist()  # ['a.txt', 'b.txt', ...]
```

`Command` 主要属性（命令完成后）：

| 属性 | 类型 | 说明 |
|------|------|------|
| `cmdline` | `str` | 命令原文 |
| `stdout` | `str` / `None` | 标准输出 |
| `stderr` | `str` / `None` | 标准错误 |
| `exit` | `str` / `None` | 退出码（字符串） |
| `dur` | `float` | 执行耗时（毫秒） |
| `screentext` | `str` | 终端屏幕实时文本 |
| `done()` | `bool` | 是否执行完成 |
| `succ()` | `bool` | 是否成功 |
| `fail()` | `bool` | 是否失败 |
| `wait(timeout=None)` | `int` / `None` | 等待完成，返回退出码 |
| `get_stdout()` | `str` | 获取 stdout |
| `get_stderr()` | `str` | 获取 stderr |
| `get_exitcode()` | `int` | 获取退出码 |
| `get_cmdline()` | `str` | 获取命令原文 |
| `getint()` | `int` / `None` | 将 stdout 解析为 int |
| `getfloat()` | `float` / `None` | 将 stdout 解析为 float |
| `getlist(splitter)` | `list` | 将 stdout 按分隔符拆为列表 |

> **提示**：`succ()`、`fail()`、`getint()` 等读取类方法会自动调用 `wait()` 等待命令完成，无需手动调用。
