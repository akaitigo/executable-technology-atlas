# 小さな数値API

[構造図](architecture.svg)

## 索引

- [clamp](#api-clamp)
- [add](#api-add)

<a id="api-clamp"></a>
## clamp

値を閉区間へ収める

```python
from api import clamp
print(clamp(-1, 0, 10))
```

期待stdout:
```text
0
```

```python
from api import clamp
print(clamp(0, 0, 10))
```

期待stdout:
```text
0
```

```python
from api import clamp
print(clamp(7, 0, 10))
```

期待stdout:
```text
7
```

```python
from api import clamp
print(clamp(10, 0, 10))
```

期待stdout:
```text
10
```

```python
from api import clamp
print(clamp(11, 0, 10))
```

期待stdout:
```text
10
```


<a id="api-add"></a>
## add

二つの整数を加える

```python
from api import add
print(add(2, 3))
```

期待stdout:
```text
5
```

```python
from api import add
print(add(-2, 2))
```

期待stdout:
```text
0
```

```python
from api import add
print(add(0, 0))
```

期待stdout:
```text
0
```

## 原典

- [examples](https://docs.python.org/3/library/doctest.html#how-it-works)
- [markdown](https://spec.commonmark.org/0.31.2/#fenced-code-blocks)
- [svg](https://www.w3.org/TR/SVG2/struct.html#SVGElement)
- [decisions](https://adr.github.io/)
