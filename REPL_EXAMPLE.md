## REPL Usage:
 1.1 Add library path:
```python
import sys
sys.path.extend(["<Your Library Path>"])
 ```

 1.2 Import main library:
 ```python
from keepercommander import session
``` 

1.3 Open a Keeper session:
 ```python
myvault = session.KeeperSession(user='user@example.com')
 ```

1.4 Call a method to get specific records
 ```python
for ul, rr in myvault.find_duplicating_username_url():
    break
 ```

1.5 import sub library:
```python
from example import remove_same_loginurl as rsl
```

1.6 use sub library:
```python
i, tbl = rsl.tabulate_records(rr)
i
print(tbl)
```

1.7 execute main library function:
```python
myvault.delete_immediately(['<<uid>>'])
```