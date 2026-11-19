# connector_e2e_20261119 — 纯标准库配置加载器

GitHub 连接器验收交付物（第一轮 2026-11-19，第二轮同日更新）。

* 仅使用 Python 标准库（`json`、`os`），**不依赖任何第三方包**。
* 不修改仓库中已有的任何文件，所有改动都限定在本目录下。
* 不涉及 Maven 构建，不需要安装依赖。

## 目录内容

| 文件 | 说明 |
| --- | --- |
| `config_loader.py` | 配置规范化与加载实现 |
| `test_config_loader.py` | 基于 `unittest` 的四个测试用例 |
| `round2_marker.txt` | 第二轮验收标记，内容为 `ROUND_TWO_ONLY_20261119` |
| `README.md` | 本文档 |

## 第二轮变更

* `timeout` 的默认值由 `5` 调整为 **`7`**（`DEFAULT_TIMEOUT = 7`）。
* 新增第四个测试用例 `test_invalid_retries`，覆盖负数、`bool`、字符串三种非法 `retries`。
* 新增标记文件 `round2_marker.txt`。
* 同步更新既有测试与本文档中的默认值描述。

## 快速开始

```python
import sys

sys.path.insert(0, "connector_e2e_20261119")

from config_loader import load_config, normalize_config

# 1. 直接规范化一个 dict
normalize_config({})                          # {'timeout': 7, 'retries': 0}
normalize_config({"timeout": 30, "retries": 3})  # {'timeout': 30, 'retries': 3}

# 2. 从 JSON 文件加载并规范化
config = load_config("config.json")            # {'timeout': 7, 'retries': 0, ...}
```

## API

### `normalize_config(config) -> dict`

接收一个 `dict`，返回**规范化后的新字典**（不会修改传入的 dict）。

规则：

| 字段 | 默认值 | 约束 |
| --- | --- | --- |
| `timeout` | `7` | 必须是**正整数**（`> 0`），且**不能是 `bool`** |
| `retries` | `0` | 必须是**非负整数**（`>= 0`），且**不能是 `bool`** |

* 字段缺失时使用默认值；字段存在但显式传入 `None` 视为非法（`None` 不是整数）。
* 除 `timeout` / `retries` 之外的其它键原样保留。
* `bool` 被显式排除：Python 中 `isinstance(True, int)` 为 `True`，但布尔值不是有意义的超时/重试次数。
* 非法输入统一抛出 `ValueError`。

示例：

```python
normalize_config({})                        # {'timeout': 7, 'retries': 0}
normalize_config({"timeout": 30})            # {'timeout': 30, 'retries': 0}
normalize_config({"retries": 2})             # {'timeout': 7, 'retries': 2}
normalize_config({"timeout": 0})             # ValueError: timeout must be a positive integer, got 0
normalize_config({"timeout": True})         # ValueError: timeout must be a positive integer, got True
normalize_config({"retries": -1})            # ValueError: retries must be a non-negative integer, got -1
```

### `load_config(path) -> dict`

读取 JSON 文件并返回规范化后的配置。

* `path` 支持 `str` 与 `os.PathLike`（例如 `pathlib.Path`）。
* JSON 顶层必须是对象，否则 `ValueError`。
* 文件内容非法 JSON 时抛出 `json.JSONDecodeError`，它本身是 `ValueError` 的子类，
  因此**所有非法输入统一表现为 `ValueError`**。
* 文件不存在抛出 `OSError`（`FileNotFoundError`），因为那是 IO 问题而非配置内容问题。

示例：

```python
load_config("config.json")
# config.json: {"timeout": 30, "retries": 3}
# -> {'timeout': 30, 'retries': 3}
```

## 测试

在仓库根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s connector_e2e_20261119 -v
```

四个用例分别覆盖：

1. `test_defaults_are_applied_for_missing_values` —— **默认值**：`normalize_config({})` 得到 `timeout=7`、`retries=0`。
2. `test_valid_configuration_is_preserved_and_loadable_from_json` —— **有效配置**：合法值被保留、输入 dict 不被修改，并验证 `load_config` 的 JSON 文件往返（`str` 与 `os.PathLike` 两种路径）。
3. `test_invalid_timeout_raises_value_error` —— **非法 timeout**：`0`、`-1`、`-30`、`1.5`、`"10"`、`None`、`True`、`False` 均抛出 `ValueError`，文件加载路径同样适用。
4. `test_invalid_retries` —— **非法 retries**：负数（`-1`、`-5`）、布尔值（`True`、`False`）、字符串（`"3"`、`"abc"`）均抛出 `ValueError`，文件加载路径同样适用。

测试仅使用 `unittest`、`json`、`os`、`pathlib`、`sys`、`tempfile`，不安装任何依赖。

## 设计说明

* 校验与默认值填充集中在 `normalize_config`，`load_config` 只负责读文件再委派给
  `normalize_config`，因此两条入口的校验规则完全一致。
* 使用显式类型检查（`isinstance(value, bool)` 先于 `isinstance(value, int)`），
  避免 `True` / `False` 被当作 `1` / `0` 静默接受。
* 不引入 `dataclass`、`pydantic` 等外部依赖，保持“零安装”特性。
