# 计划：从 cctf 抽取 CRCF 项目（Target / Connection / Shell）

## 概述

按照 `doc/design.md` 的描述，CRCF（Concurrent Remote Control Framework）是 CCTF 的裁剪版本：去除测试 harness 部分，保留远程设备并发控制能力并优化日志。本计划从子目录 `cctf/` 中抽取 **Target 及其子类**、**Connection 及其子类**、**Shell**（cctf 中仅有一个 Shell 类，无子类，经用户确认仅抽取该类）以及它们运行所必需的依赖模块，组建新的 `crcf` 包。

### 用户确认的关键决策
1. **命名**：代码中所有 `CCTF`/`cctf2018` 引用全部重命名为 `CRCF`。
2. **Shell**：cctf 中无 Shell 子类，仅抽取现有 `Shell` 类。
3. **日志优化**：引入 Python 标准 `logging` 模块，替代当前 `print()` 式日志，支持日志级别配置与输出目标控制。

---

## 现状分析

### 源码位置与依赖关系
源码位于 `/Users/fred/Downloads/crcf/cctf/cctf/`。CRCF 根目录 `/Users/fred/Downloads/crcf/` 目前仅含 `doc/` 和 `.gitignore`，无包代码。

**抽取范围内模块及其依赖：**

| 模块 | 主要内容 | 依赖 |
|------|---------|------|
| `target.py` | `Target` 基类 + 模块函数 `__execmd` | common, me, shell, connection |
| `uxtarget.py` | `UxTarget`（unix 类目标基类） | target, me |
| `linuxtarget.py` | `LinuxTarget` | uxtarget |
| `aixtarget.py` | `AixTarget` | uxtarget |
| `hpuxtarget.py` | `HpuxTarget` | uxtarget |
| `sunostarget.py` | `SunOSTarget` | uxtarget |
| `connection.py` | `Connection` 基类 + `ConnError` | common, me |
| `sshconnection.py` | `SshConnection` | connection, me |
| `rshconnection.py` | `RshConnection` | connection, me |
| `telnetconnection.py` | `TelnetConnection` | connection, me |
| `shell.py` | `Shell`（线程，命令队列） | common, connfactory, command |
| `command.py` | `Command`（命令结果对象，design.md 列为主对象之一） | common |
| `connfactory.py` | `connect()` 连接工厂 | sshconnection, telnetconnection, rshconnection, common, me, connection |
| `targetfactory.py` | `gettarget()` 目标工厂 | connfactory, target, linuxtarget, common |
| `common.py` | `Common`（日志基类）+ `LockAble` | — |
| `me.py` | 本地命令执行、端口探测、scp 等工具函数 | — |

### 排除的模块（测试 harness，design.md 要求去除）
- `case.py`、`caseunit.py`、`logicunit.py`、`scanner.py`

### 需要 CCTF→CRCF 重命名的点
1. **包/导入名**：`from cctf import` → `from crcf import`（examples 中）；包内相对导入 `from .xxx` 不变。
2. **`common.py`**：`UNIQIDENTIFIER = "CCTF2018_NO_WAY_OF_DUPLICATION:"` → `"CRCF_NO_WAY_OF_DUPLICATION:"`
3. **`target.py` `__execmd`**：`"line_of_cctf2018"`、`"start_line_of_cctf2018"`、`"end_line_of_cctf2018"` → `line_of_crcf` / `start_line_of_crcf` / `end_line_of_crcf`
4. **`connection.py` `_inshell`**：`echo CCTF` → `echo CRCF`
5. **`shell.py`**：临时文件前缀 `CCTF_{thread_id}_{random}` → `CRCF_{thread_id}_{random}`
6. **各文件 docstring/注释** 中的 `CCTF` 文案 → `CRCF`
7. **`__init__.py`**：包 docstring、`__pdoc__`（去除已排除模块的条目）、`__all__`

---

## 目标目录结构

```
/Users/fred/Downloads/crcf/
├── doc/                       （已存在，不动）
│   ├── design.md
│   └── design.png
├── crcf/                      ← 新建包
│   ├── __init__.py
│   ├── common.py
│   ├── me.py
│   ├── command.py
│   ├── connection.py
│   ├── connfactory.py
│   ├── sshconnection.py
│   ├── rshconnection.py
│   ├── telnetconnection.py
│   ├── target.py
│   ├── targetfactory.py
│   ├── uxtarget.py
│   ├── linuxtarget.py
│   ├── aixtarget.py
│   ├── hpuxtarget.py
│   ├── sunostarget.py
│   └── shell.py
└── .gitignore
```

---

## 具体变更

### 1. 新建包目录 `crcf/` 并迁移模块（15 个文件）

从 `cctf/cctf/` 复制以下文件到 `crcf/crcf/`，复制后做 CCTF→CRCF 文案/标记替换（见上方第 6 节）：
`common.py`、`me.py`、`command.py`、`connection.py`、`connfactory.py`、`sshconnection.py`、`rshconnection.py`、`telnetconnection.py`、`target.py`、`targetfactory.py`、`uxtarget.py`、`linuxtarget.py`、`aixtarget.py`、`hpuxtarget.py`、`sunostarget.py`、`shell.py`。

包内相对导入（`from .common import ...` 等）保持不变，无需改动。

### 2. `common.py` — 引入 logging 模块（核心日志优化）

**当前实现**：`Common.log()` 用 `print()` + 全局 `RLock` 输出到 stdout，自定义级别 0/1/2/3/99。

**改造方案**：
- 删除 `g_printlck` 锁（`logging` 自身线程安全，无需自定义锁）。
- 保留 `g_prog_name`。
- 新增模块级 logger：
  ```python
  import logging, sys

  STEP = 25  # 介于 INFO(20) 与 WARNING(30) 之间
  logging.addLevelName(STEP, "STEP")

  logger = logging.getLogger("crcf")
  if not logger.handlers:
      _handler = logging.StreamHandler(sys.stdout)
      _handler.setFormatter(logging.Formatter(
          "[%(levelname)s][%(asctime)s][%(progname)s : %(clsname)s] %(message)s",
          datefmt="%Y-%m-%d %H:%M:%S",
      ))
      logger.addHandler(_handler)
      logger.setLevel(logging.INFO)
      logger.propagate = False
  ```
- 用 `logging.Filter` 注入 `progname`（常量），用 `extra` 传入 `clsname`（每次调用按 `self.__class__.__name__`）：
  ```python
  class _CtxFilter(logging.Filter):
      def filter(self, record):
          record.progname = g_prog_name
          return True
  logger.addFilter(_CtxFilter())
  ```
- `Common.log()` 改为：
  ```python
  _LEVEL_MAP = {0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARNING, 3: logging.INFO}

  def log(self, msg, level=3):
      if level == 99:  # STEP
          Common.step_number += 1
          logger.log(STEP, f"\n\nSTEP {Common.step_number}: {msg}\n\n",
                     extra={"clsname": self.__class__.__name__})
      else:
          logger.log(self._LEVEL_MAP.get(level, logging.INFO), msg,
                     extra={"clsname": self.__class__.__name__})
  ```
- `warn/info/error/critical/step` 透传方法保持不变（它们调用 `self.log()`）。
- `LockAble` 类保持不变（Connection/Command 仍用它做自身互斥）。
- 日志格式输出与原版保持一致：`[LEVEL][time][prog : ClassName] msg`，用户可通过标准 `logging` 配置（`logging.getLogger("crcf")`）自定义级别/Handler/输出文件。

### 3. `__init__.py` — 包入口

- 包 docstring：`CCTF` → `CRCF`，移除"test framework"相关描述，强调并发远程控制定位。
- `__pdoc__`：移除已排除模块（`case/caseunit/logicunit/scanner`）条目；其余模块条目保留，`cctf`→无影响（键名是模块名）。
- 导入与 `__all__` 不变：
  ```python
  from .target import Target
  from .targetfactory import gettarget
  from .shell import Shell
  from .command import Command
  __all__ = ["Target", "gettarget", "Shell", "Command"]
  ```
- docstring 中 `Architect.jpg` 引用路径：原指向 `../doc/Architect.jpg`，crcf 包同级 doc 下无此图，改为指向 `../doc/design.png` 或删除该行（design.md 用的是 design.png）。

### 4. `target.py` — `__execmd` 标记重命名

将 `__execmd` 内的 `line_of_cctf2018` / `start_line_of_cctf2018` / `end_line_of_cctf2018` 改为 `line_of_crcf` / `start_line_of_crcf` / `end_line_of_crcf`（write 与 waitfor 两端必须一致）。
注：`__execmd` 为模块级函数（非类属性，无名称改写问题），`targetfactory.py` 中 `from .target import Target, __execmd` 显式导入可正常工作；为避免双下划线误读，可顺带重命名为 `_execmd` 并同步 `targetfactory.py` 的导入（可选小清理）。

### 5. `connection.py` — `_inshell` 标记重命名

`_inshell` 中 `echo CCTF` 与 `waitfor("CCTF", ...)` 改为 `echo CRCF` / `waitfor("CRCF", ...)`，与 `common.UNIQIDENTIFIER` 的新值保持一致。

### 6. `shell.py` — 临时文件前缀重命名

`run()` 中 `filename = f"CCTF_{threading.current_thread().ident}_{random.randrange(...)}"` → `f"CRCF_{...}"`。其余 `UNIQIDENTIFIER` 引用通过继承自动生效，无需改动。

### 7. `me.py` / `command.py` / `connfactory.py` / `targetfactory.py` / 各 target/connection 子类

- 复制后做 docstring/注释中 `CCTF` → `CRCF` 文案替换。
- 逻辑代码无需改动（相对导入不变）。
- `connfactory.py` 中 `Common().log(...)` 临时实例调用方式保持，依赖 `Common.log` 走 logging，无需改动。

---

## 假设与决策

1. **依赖模块一并抽取**：Target/Connection/Shell 硬依赖 `common.py`、`me.py`、`command.py`、`connfactory.py`、`targetfactory.py`，必须一同迁移，否则无法运行。`command.py` 在 design.md 中被列为四大主对象之一，明确在范围内。
2. **排除测试 harness**：`case.py`、`caseunit.py`、`logicunit.py`、`scanner.py` 按 design.md 去除。
3. **examples/tests/bin/Makefile**：本次不在抽取范围（用户仅要求 Target/Connection/Shell）。`cctf/examples`、`cctf/tests`、`cctf/bin/tcrun`、`cctf/Makefile` 不迁移；后续如需可单独处理。
4. **`__execmd` 重命名**（可选）：双下划线模块函数易误读，建议改为 `_execmd`；若希望最小改动可保留原名。
5. **日志默认输出 stdout**：与原版 `print` 行为一致；用户可通过 `logging.getLogger("crcf")` 重新配置。
6. **STEP 自定义级别**：值为 25，保留 `step()` 的特殊打印格式（`\n\nSTEP N: msg\n\n`）。
7. **`UNIQIDENTIFIER` 取值**：由 `CCTF2018_NO_WAY_OF_DUPLICATION:` 改为 `CRCF_NO_WAY_OF_DUPLICATION:`（去掉年份，避免再绑定特定年份）。

---

## 验证步骤

1. **语法/导入检查**：在 `/Users/fred/Downloads/crcf` 下执行
   ```bash
   python -m py_compile crcf/*.py
   python -c "import crcf; print(crcf.__all__)"
   ```
   确认无语法错误、包可正常导入、`__all__` 输出 `['Target', 'gettarget', 'Shell', 'Command']`。
2. **标记一致性检查**：用 Grep 确认 `crcf/` 内不再出现 `CCTF` / `cctf2018`（除注释历史说明外应全部为 `CRCF` / `crcf`）。
   - 重点核验 `__execmd` 的 write/waitfor 标记配对一致、`_inshell` 的 echo/waitfor 配对一致、`shell.py` 临时文件前缀。
3. **日志验证**：
   ```python
   from crcf.common import Common
   Common().log("test info")
   Common().error("test error")
   Common().step("a step")
   ```
   确认输出格式为 `[LEVEL][time][prog : Common] msg`，且可通过
   ```python
   import logging
   logging.getLogger("crcf").setLevel(logging.WARNING)
   ```
   屏蔽 INFO 级输出，验证级别配置生效。
4. **类继承链验证**：
   ```python
   from crcf import Target, Shell, Command
   from crcf.connection import Connection
   from crcf.linuxtarget import LinuxTarget
   from crcf.sshconnection import SshConnection
   assert issubclass(LinuxTarget, Target)
   assert issubclass(SshConnection, Connection)
   ```
   确认抽取后继承体系完整。
