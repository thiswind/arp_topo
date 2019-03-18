# ARP TOPO

用arp列表来绘制服务器之间的拓扑关系

# Requirement

推荐用Python3.7，至少也是Python3.6.7

注意：在主目录里先放一个主机列表，一个excel文件，命名为：`pwd.xls`，格式如下：

```bash
-------------------------------------------------------
| 资产名称   | IP              | 帐号名 | 登录密码        |
-------------------------------------------------------
| **系统-** | ***.***.***.*** | root  | ************** |
-------------------------------------------------------
| **系统-** | ***.***.***.*** | root  | ************** |
-------------------------------------------------------        
| **系统-** | ***.***.***.*** | root  | ************** |
-------------------------------------------------------
```

# Usage

安装依赖关系

```bash
pip install --user -r requerements.txt
```
读取ARP列表，构造拓扑图

```bash
python arp_topo.py
```

执行完，会生成一个`graph.json`文件

运行一个本地的flask来看效果

```bash
python app.py
```

然后打开 [http://127.0.0.1:5000](http://127.0.0.1:5000) 就可以看到拓扑图了

# Preview

![](https://github.com/thiswind/arp_topo/raw/master/prevew.png)
