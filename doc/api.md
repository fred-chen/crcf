# CRCF API 参考

## 包入口

```python
from crcf import Target, gettarget, Shell, Command
```

---

## Target

`Target` 是一个抽象类，代表一个远程目标设备。通过 `gettarget()` 工厂函数或直接构造子类（如 `LinuxTarget`）来创建。

### 创建方式

```python
# 工厂函数
from crcf import gettarget
target = gettarget(host, username=None, password=None, svc="ssh", timeout=60)

# 直接构造
from crcf.linuxtarget import LinuxTarget
target = LinuxTarget(address, svc="ssh", username="root", password=None, conn=None, timeout=60)
```

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

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `newshell` | `(conn: Connection = None) -> Shell` | 创建并返回一个新的 Shell 对象 |
| `__str__` | `() -> str` | 返回 `address - hostname` 或 `address` |
| `gethostname` | `() -> str` | 获取目标主机名 |
| `reboot` | `(wait=True, log=True)` | 优雅重启目标设备 |
| `shutdown` | `(wait=True, log=True)` | 优雅关闭目标设备 |
| `panic` | `(log=True)` | 立即崩溃目标设备（不可恢复） |
| `panicreboot` | `(wait=True, log=True)` | 崩溃后立即重启 |
| `upload` | `(local_path, remote_path, log=True) -> bool` | 上传文件到目标 |
| `download` | `(local_path, remote_path, log=True) -> bool` | 从目标下载文件 |
| `wait_alive` | `(svc=None, timeout=None) -> bool` | 等待目标上线（连接成功） |
| `wait_down` | `(svc=None, timeout=None) -> bool` | 等待目标下线 |
| `alive` | `(svc=None, timeout=1) -> bool` | 检查目标是否在线 |
| `exe` | `(cmdline, ...)` | 委托给 `target.shell.exe()` |

---

## Connection

`Connection` 是连接对象的基类，代表从主机到目标设备的网络连接。具体实现有 `SshConnection`、`RshConnection`、`TelnetConnection`。

### 创建方式

```python
# 通过工厂函数
from crcf.connfactory import connect
conn = connect(host, username=None, password=None, svc="ssh", timeout=30, newline="\n")

# 直接构造
from crcf.sshconnection import SshConnection
conn = SshConnection(host, username=None, password=None, timeout=30, newline="\n")
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `host` | `str` | 目标主机地址 |
| `username` | `str` | 用户名 |
| `password` | `str` | 密码 |
| `timeout` | `int` | 超时秒数 |
| `newline` | `str` | 换行符，默认 `"\n"` |
| `pty_fd` | `int` | 伪终端文件描述符 |
| `child_pid` | `int` | 子进程 PID |
| `txt` | `str` | 已读取的文本缓冲 |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `connect` | `() -> bool` | 建立连接（子类实现） |
| `reconnect` | `()` | 断开后重连 |
| `disconnect` | `()` | 断开连接 |
| `read` | `(timeout: int = None) -> str / None` | 读取文本，阻塞至有数据或超时 |
| `write` | `(txt: str) -> int / None` | 写入文本 |
| `write_newline` | `() -> int / None` | 写入换行符 |
| `waitfor` | `(pattern, timeout=0) -> str / None` | 等待匹配正则 pattern 的文本 |
| `login` | `() -> bool` | 登录目标（密码认证 + 进入 bash） |
| `connected` | `() -> bool` | 检查连接是否存活 |
| `printlog` | `()` | 打印已读取的文本 |

---

## Shell

`Shell` 代表目标设备上的一个 Shell 会话，内部包含一个命令队列和后台线程，用于异步执行命令。

### 创建方式

```python
# 通过 Target 创建
shell = target.newshell()
shell = target.newshell(conn=existing_conn)

# 直接构造
from crcf.shell import Shell
shell = Shell(target, conn=None, timeout=300)
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `target` | `Target` | 关联的 Target 对象 |
| `conn` | `Connection` | 连接对象 |
| `timeout` | `int` | 超时秒数 |
| `shell_id` | `str` | Shell 唯一标识 |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `exe` | `(cmdline, wait=True, log=True, longrun_report=1800, wait_report=30) -> Command` | 执行命令，返回 Command 对象 |
| `gettarget` | `() -> Target` | 获取关联的 Target 对象 |
| `interrupt` | `(send="\x03")` | 向当前命令发送中断信号（默认 Ctrl+C） |

---

## Command

`Command` 是 `shell.exe()` 返回的命令对象，封装了命令的执行结果。

### 创建方式

`Command` 由 `shell.exe()` 自动创建并返回，用户无需手动构造。

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `cmdline` | `str` | 命令原文 |
| `stdout` | `str / None` | 标准输出 |
| `stderr` | `str / None` | 标准错误 |
| `exit` | `str / None` | 退出码（字符串） |
| `dur` | `float` | 执行耗时（毫秒） |
| `screentext` | `str` | 终端屏幕实时文本 |
| `done` | `bool` | 是否执行完成 |
| `shell` | `Shell` | 所属 Shell 对象 |
| `start` | `datetime` | 开始执行时间 |

### 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `done()` | `() -> bool` | 是否执行完成 |
| `succ()` | `() -> bool` | 是否成功（退出码为 0） |
| `fail()` | `() -> bool` | 是否失败（退出码非 0） |
| `wait(timeout=None) -> int / None` | 等待命令完成，返回退出码 |
| `get_stdout() -> str` | 获取 stdout |
| `get_stderr() -> str` | 获取 stderr |
| `get_exitcode() -> int` | 获取退出码 |
| `get_cmdline() -> str` | 获取命令原文 |
| `getint() -> int / None` | 将 stdout 解析为 int |
| `getfloat() -> float / None` | 将 stdout 解析为 float |
| `getlist(splitter="\r\n") -> list` | 将 stdout 按分隔符拆为列表 |
| `cmdlog()` | `()` | 以日志格式输出命令信息 |

---

## 其他模块

### `gettarget()` 工厂函数

```python
def gettarget(host, username=None, password=None, svc="ssh", timeout=60) -> Target
```

自动建立连接、检测目标类型，返回合适的 Target 子类实例。当前仅支持 Linux 类型。

### `connect()` 工厂函数

```python
def connect(host="127.0.0.1", username=None, password=None, svc="ssh", timeout=30, newline="\n") -> Connection
```

根据 `svc` 参数创建对应类型的 Connection 对象。可选 `svc`：`"ssh"`、`"telnet"`、`"shell"`（rsh）。
