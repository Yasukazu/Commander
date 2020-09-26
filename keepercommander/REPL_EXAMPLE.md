## REPL Usage:
1.1 Add library path:
 ```python
    import sys
    sys.path.extend(["<Your Library Path>"])
 ```
1.2 Import libraries
 ```python
  import keepercommander.session as k_session
``` 

1.3 Open a Keeper session
 ```python
    ssn = k_session.KeeperSession(user='yskz@example.com')
 ```
1.4 Call a method
 ```python
for ul, rr in ssn.username_url_find_duplicated():
    ul_0 = ul
    rr_0 = rr
    break
 ```
1.5 Inspect variables
```python
 ul_0
 rr_0.to_dictionary()
```