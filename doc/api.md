# CRCF API 参考

## 包入口

```python
from crcf import Target, gettarget, Shell, Command
```

---

## Target

`Target` 是一个抽象类，代表一个远程目标设备或主机。CRCF 将每个目标设备抽象为一个 Target 对象，可以是一台服务器、交换机、路由器，甚至一部手机。

### 创建 Target

CRCF 提供两种方式创建 Target 对象：**工厂函数 `gettarget()`**（推荐）和**直接构造子类**。

#### 工厂函数 `gettarget()`

`gettarget()` 自动建立连接、检测目标类型，返回合适的 Target 子类实例。

```python
from crcf import gettarget

# 基本用法：指定主机地址、用户名和密码
target = gettarget("10.1.0.96", "root", "password")

# 指定连接服务类型和超时时间
target = gettarget("10.1.0.96", "root", "password", svc="ssh", timeout=120)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | — | 目标主机 IP 地址或域名 |
| `username` | `str` | `None` | 登录用户名，`None` 时使用当前系统用户 |
| `password` | `str` | `None` | 登录密码 |
| `svc` | `str` | `"ssh"` | 连接服务类型，可选 `"ssh"`、`"telnet"`、`"shell"`（rsh） |
| `timeout` | `int` | `60` | 超时秒数 |

> **注意**：当前 `gettarget()` 的自动检测仅支持 Linux 类型，会返回 `LinuxTarget` 实例。

#### 直接构造

如果已有连接对象，或需要指定特定子类型，可以直接构造：

```python
from crcf.linuxtarget import LinuxTarget

# 直接构造 LinuxTarget
target = LinuxTarget("10.1.0.96", svc="ssh", username="root", password="password")

# 传入已有连接对象
from crcf.sshconnection import SshConnection
conn = SshConnection("10.1.0.96", "root", "password", timeout=30)
target = LinuxTarget("10.1.0.96", svc="ssh", username="root", password="password", conn=conn, timeout=120)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `address` | `str` | — | 目标主机地址 |
| `svc` | `str` | `"ssh"` | 连接服务类型 |
| `username` | `str` | `"root"` | 用户名 |
| `password` | `str` | `None` | 密码 |
| `conn` | `Connection` | `None` | 已有连接对象 |
| `timeout` | `int` | `60` | 超时秒数 |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `address` | `str` | 目标主机地址 |
| `svc` | `str` | 连接服务类型 |
| `username` | `str` | 用户名 |
| `password` | `str` | 密码 |
| `timeout` | `int` | 超时秒数 |
| `hostname` | `str` | 主机名（自动获取） |
| `shell` | `Shell` | 内部默认 Shell 对象 |
| `shs` | `list[Shell]` | 所有 Shell 对象列表 |
| `conn` | `Connection` | 连接对象 |
| `exe` | `Shell.exe` | 委托方法，等价于 `target.shell.exe` |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `newshell` | `(conn: Connection = None) -> Shell` | 创建并返回一个新的 Shell 对象 |
| `__str__` | `() -> str` | 返回 `address - hostname` 或 `address` |
| `gethostname` | `() -> str` | 获取目标主机名 |
| `reboot` | `(wait: bool = True, log: bool = True) -> None` | 优雅重启目标设备 |
| `shutdown` | `(wait: bool = True, log: bool = True) -> None` | 优雅关闭目标设备 |
| `panic` | `(log: bool = True) -> None` | 立即崩溃目标设备（不可恢复） |
| `panicreboot` | `(wait: bool = True, log: bool = True) -> None` | 崩溃后立即重启 |
| `upload` | `(local_path: str, remote_path: str, log: bool = True) -> bool` | 上传文件到目标 |
| `download` | `(local_path: str, remote_path: str, log: bool = True) -> bool` | 从目标下载文件 |
| `wait_alive` | `(svc: str = None, timeout: int = None) -> bool` | 等待目标上线（连接成功） |
| `wait_down` | `(svc: str = None, timeout: int = None) -> bool` | 等待目标下线 |
| `alive` | `(svc: str = None, timeout: int = 1) -> bool` | 检查目标是否在线 |

---

## Connection

`Connection` 是连接对象的基类，代表从主机到目标设备的网络连接。具体实现有 `SshConnection`、`RshConnection`、`TelnetConnection`。

### 创建 Connection

```python
# 通过工厂函数
from crcf.connfactory import connect
conn = connect(host="10.1.0.96", username="root", password="password", svc="ssh", timeout=30, newline="\n")

# 直接构造
from crcf.sshconnection import SshConnection
conn = SshConnection(host="10.1.0.96", username="root", password="password", timeout=30, newline="\n")
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | `"127.0.0.1"` | 目标主机地址 |
| `username` | `str` | `None` | 用户名，`None` 时使用当前系统用户 |
| `password` | `str` | `None` | 密码 |
| `svc` | `str` | `"ssh"` | 连接服务类型，可选 `"ssh"`、`"telnet"`、`"shell"`（rsh） |
| `timeout` | `int` | `30` | 超时秒数 |
| `newline` | `str` | `"\n"` | 换行符 |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `host` | `str` | 目标主机地址 |
| `username` | `str` | 用户名 |
| `password` | `str` | 密码 |
| `timeout` | `int` | 超时秒数 |
| `newline` | `str` | 换行符 |
| `pty_fd` | `int` | 伪终端文件描述符 |
| `child_pid` | `int` | 子进程 PID |
| `txt` | `str` | 已读取的文本缓冲 |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `connect` | `() -> bool` | 建立连接（子类实现） |
| `reconnect` | `() -> None` | 断开后重连 |
| `disconnect` | `() -> None` | 断开连接 |
| `read` | `(timeout: int = None) -> str \| None` | 读取文本，阻塞直到有数据或超时 |
| `write` | `(txt: str) -> int \| None` | 写入文本，返回写入的字节数 |
| `write_newline` | `() -> int \| None` | 写入换行符 |
| `waitfor` | `(pattern: str, timeout: int = 0) -> str \| None` | 等待匹配正则 pattern 的文本 |
| `login` | `() -> bool` | 登录目标（密码认证 + 进入 bash） |
| `connected` | `() -> bool` | 检查连接是否存活 |
| `printlog` | `() -> None` | 打印已读取的文本 |
| `svcalive` | `() -> bool` | 检查服务是否可用（子类实现） |

---

## Shell

`Shell` 代表目标设备上的一个 Shell 会话，内部包含一个命令队列和后台线程，用于异步执行命令。每个 Shell 对象对应一个独立的连接和后台线程，一个 Target 可以有多个 Shell，实现真正的并发。

### 创建 Shell

每个 Target 对象内部已有一个默认 Shell，可通过 `target.shell` 访问。也可以创建额外的 Shell 对象：

```python
# 使用 Target 内部默认的 Shell
shell = target.shell

# 创建一个新 Shell（每次调用创建独立连接和线程）
shell = target.newshell()

# 使用已有连接创建 Shell（注意：SSH 连接在执行命令后通常不可复用，建议创建新连接）
shell = target.newshell(conn=existing_conn)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `conn` | `Connection` | `None` | 复用的已有连接，`None` 则新建连接 |

```python
# 直接构造
from crcf.shell import Shell
shell = Shell(target=target, conn=None, timeout=300)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `target` | `Target` | — | 关联的 Target 对象 |
| `conn` | `Connection` | `None` | 连接对象，`None` 则新建连接 |
| `timeout` | `int` | `300` | 命令执行超时时间（秒） |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `target` | `Target` | 关联的 Target 对象 |
| `conn` | `Connection` | 连接对象 |
| `timeout` | `int` | 超时秒数 |
| `shell_id` | `str` | Shell 唯一标识（短 UUID） |
| `queuq` | `Queue` | 命令队列（内部属性） |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `exe` | `(cmdline: str, wait: bool = True, log: bool = True, longrun_report: int = 1800, wait_report: int = 30) -> Command` | 执行命令，返回 Command 对象 |
| `gettarget` | `() -> Target` | 获取关联的 Target 对象 |
| `interrupt` | `(send: str = "\x03") -> None` | 向当前命令发送中断信号（默认 Ctrl-C） |

#### `exe()` — 执行命令

`shell.exe()` 是 Shell 的核心方法，将命令发送给远程目标执行，返回一个 `Command` 对象。

**同步执行**（默认）：

```python
# wait=True（默认），阻塞等待命令执行完成
command = shell.exe("uname -a")
```

**异步执行**：

```python
# wait=False，立即返回 Command 对象，不阻塞
command = shell.exe("sleep 100", wait=False)

# 后续处理其他任务...

# 等待命令完成
command.wait()
```

**并发执行示例**：

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

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cmdline` | `str` | — | 要执行的命令 |
| `wait` | `bool` | `True` | `True` 阻塞等待完成，`False` 立即返回 |
| `log` | `bool` | `True` | 是否打印执行结果日志 |
| `longrun_report` | `int` | `1800` | 长时间运行命令的进度报告间隔（秒） |
| `wait_report` | `int` | `30` | 等待中的进度报告间隔（秒） |

---

## Command

`Command` 是 `shell.exe()` 返回的命令对象，封装了命令的执行结果。通过 Command 对象可以检查命令是否成功、获取输出内容和退出码。

### 创建 Command

`Command` 由 `shell.exe()` 自动创建并返回，用户无需手动构造。

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `cmdline` | `str` | 命令原文 |
| `stdout` | `str \| None` | 标准输出（原始字符串，包含前后空白） |
| `stderr` | `str \| None` | 标准错误（原始字符串，包含前后空白） |
| `exit` | `str \| None` | 退出码（字符串） |
| `dur` | `float` | 执行耗时（毫秒） |
| `screentext` | `str` | 终端屏幕实时文本 |
| `shell` | `Shell` | 所属 Shell 对象 |
| `start` | `datetime` | 开始执行时间 |
| `_done` | `bool` | 内部状态，是否执行完成（通过 `done()` 方法访问） |
| `cond` | `Condition` | 线程同步条件变量（内部属性） |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `done` | `() -> bool` | 是否执行完成 |
| `succ` | `() -> bool` | 是否成功（退出码为 0） |
| `fail` | `() -> bool` | 是否失败（退出码非 0） |
| `wait` | `(timeout: int = None) -> int \| None` | 等待命令完成，返回退出码，超时时返回 `None` |
| `get_stdout` | `() -> str` | 获取 stdout（自动去除前后空白） |
| `get_stderr` | `() -> str` | 获取 stderr（自动去除前后空白） |
| `get_exitcode` | `() -> int` | 获取退出码 |
| `get_cmdline` | `() -> str` | 获取命令原文（自动去除前后空白） |
| `getint` | `() -> int \| None` | 将 stdout 解析为 int |
| `getfloat` | `() -> float \| None` | 将 stdout 解析为 float |
| `getlist` | `(splitter: str = "\r\n") -> list` | 将 stdout 按分隔符拆为列表 |
| `cmdlog` | `() -> None` | 以日志格式输出命令信息 |
| `__str__` | `() -> str` | 返回命令的格式化字符串，包含结果信息 |
| `setdone` | `() -> None` | 设置命令为完成状态（内部方法） |

#### 基本状态检查

```python
command = shell.exe("ls -l /tmp")

# 是否执行完成
print(command.done())  # True

# 是否成功（退出码为 0）
print(command.succ())  # True / False

# 是否失败（退出码非 0）
print(command.fail())  # True / False

# 打印命令的完整信息（包含 stdout、stderr、exit code、耗时）
print(command)
```

#### 获取命令输出

```python
command = shell.exe("echo hello")

# 获取 stdout 字符串（自动去除前后空白）
stdout = command.get_stdout()

# 获取 stderr 字符串（自动去除前后空白）
stderr = command.get_stderr()

# 获取退出码
exit_code = command.get_exitcode()

# 获取命令原文（自动去除前后空白）
cmdline = command.get_cmdline()

# 获取执行耗时（毫秒）
print(command.dur)
```

#### 按类型解析输出

```python
# 解析为整数
command = shell.exe("echo 42")
result = command.getint()  # 42

# 解析为浮点数
command = shell.exe("echo 3.14")
result = command.getfloat()  # 3.14

# 解析为列表（按指定分隔符，默认 "\r\n"）
command = shell.exe("ls /tmp")
files = command.getlist()  # ['a.txt', 'b.txt', ...]
```

> **提示**：`succ()`、`fail()`、`get_stdout()`、`get_stderr()`、`get_exitcode()`、`getint()`、`getfloat()`、`getlist()` 等读取类方法会自动调用 `wait()` 等待命令完成，无需手动调用。

---

## 其他模块

### `gettarget()` 工厂函数

```python
def gettarget(
    host: str,
    username: str = None,
    password: str = None,
    svc: str = "ssh",
    timeout: int = 60,
) -> Target:
```

自动建立连接、检测目标类型，返回合适的 Target 子类实例。当前仅支持 Linux 类型。

### `connect()` 工厂函数

```python
def connect(
    host: str = "127.0.0.1",
    username: str = None,
    password: str = None,
    svc: str = "ssh",
    timeout: int = 30,
    newline: str = "\n",
) -> Connection:
```

根据 `svc` 参数创建对应类型的 Connection 对象。可选 `svc`：`"ssh"`、`"telnet"`、`"shell"`（rsh）。
