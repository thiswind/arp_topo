import base64
import json
import re
from csv import DictReader
from io import StringIO
from typing import List, Tuple

import xlrd
from paramiko import AutoAddPolicy, SSHClient
from paramiko.channel import ChannelFile, ChannelStderrFile
from paramiko.ssh_exception import SSHException


def isValidIp(ip):
    if re.match(r"^\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$", ip):
        return True
    return False


def isValidMac(mac):
    if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac):
        return True
    return False


class OneSession(object):
    def __init__(self, host: Tuple[str, int, str, str]):
        """One work session in arp topo
        
        Arguments:
            host {Tuple[str, int, str, str]} -- \
                (hostname: str, port: int, username: str, password: str), \
                    used for connect to host with SSH
        """

        self.hostname = host[0]
        self.port = host[1]
        self.username = host[2]
        self.password = host[3]

    def getConnection(self) -> SSHClient:
        client: SSHClient = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.connect(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password)
        return client

    def _getARPList(self) -> List[str]:
        client: SSHClient = None
        try:
            client = self.getConnection()
            stdin: ChannelFile
            stdout: ChannelFile
            stderr: ChannelStderrFile

            stdin, stdout, stderr = client.exec_command('arp -n')
            lines = [line for line in stdout]
            stdin, stdout, stderr = client.exec_command(
                """arp -n|awk '/^[1-9]/{system("arp -d "$1)}'""")

            return lines
        except:
            return []
        finally:
            if client:
                client.close()

    def _parse(self, lines: List[str]):
        arp_list: List[Tuple[str, str]] = []

        buffer: str = ''.join(lines)
        buffer = re.sub(r'\s{2,}', ',', buffer)
        ram_file: StringIO = StringIO(buffer)
        reader: DictReader = DictReader(ram_file)
        # ATTENTION >>>
        # net-tools 1.60
        # arp 1.88 (2001-04-04)
        # for arp -n, the table header is
        # ---------------------------------------------------------------------
        # | Address         | HWtype |  HWaddress        | Flags Mask | Iface |
        # ---------------------------------------------------------------------
        # | 192.168.***.*** |        | (incomplete)      |            | eth0  |
        # | 192.168.***.*** | ether  | 28:**:**:**:**:ad | C          | eth0  |
        # | 192.168.***.*** | ether  | 3c:**:**:**:**:01 | C          | eth0  |
        # | 192.168.***.*** | ether  | 28:**:**:**:**:f5 | C          | eth0  |
        # ---------------------------------------------------------------------
        # ATTENTION <<<
        for row in reader:
            ip = row['Address']
            mac = row['HWaddress']

            if isValidIp(ip) and isValidMac(mac):
                one_arp = (ip, mac)
                arp_list.append(one_arp)

        ram_file.close()

        return (self.hostname, arp_list)

    def readARP(self):
        lines = self._getARPList()
        return self._parse(lines)


class Topo(object):
    def __init__(self):
        self.nodes: List = []
        self.links: List = []
        pass

    def addOneScan(self, scan: Tuple[str, List]):
        host = scan[0]
        arp_list = scan[1]

        self.nodes.append(host)

        host_edge_list = [(host, arp[0]) for arp in arp_list]

        for edge in host_edge_list:
            self.links.append(edge)

    def getTopo(self) -> dict:
        graph_nodes = [{'name': host, 'group': 1} for host in self.nodes]
        graph_links = []
        for link in self.links:
            ip0 = link[0]
            ip1 = link[1]
            id0 = self.nodes.index(ip0) if ip0 in self.nodes else None
            id1 = self.nodes.index(ip1) if ip1 in self.nodes else None
            if id0 and id1:
                # if host 'A' has an arp of host 'B',
                # besides 'B' must also has an arp of 'A',
                # so here the value is 1 on one side
                value = 1
                graph_links.append({
                    'source': id0,
                    'target': id1,
                    'value': value
                })

        return {'nodes': graph_nodes, 'links': graph_links}

    def __str__(self):
        return json.dumps(self.getTopo())


class HostList(object):
    def __init__(self, filename: str):
        self.filename = filename

    def loadFromFile(self) -> List[Tuple[str, int, str, str]]:
        """
        the excel file format is
        -------------------------------------------------------
        | 资产名称   | IP              | 帐号名 | 登录密码        |
        -------------------------------------------------------
        | **系统-** | ***.***.***.*** | root  | ************** |
        -------------------------------------------------------
        | **系统-** | ***.***.***.*** | root  | ************** |
        -------------------------------------------------------        
        | **系统-** | ***.***.***.*** | root  | ************** |
        -------------------------------------------------------
        """

        hosts: List[Tuple[str, int, str, str]] = []

        wb = xlrd.open_workbook(self.filename)
        sheet = wb.sheet_by_index(0)
        nrows = sheet.nrows
        first_row = True
        for i in range(nrows):
            if first_row:
                first_row = False
                continue
            row = sheet.row_values(i)
            description = row[0]
            hostname = row[1]
            username = row[2]
            password = row[3]
            one_host = (hostname, 22, username, password)
            hosts.append(one_host)

        return hosts


class ARPTopo(object):
    def __init__(self, filename: str):
        hostList = HostList(filename)
        self.hosts = hostList.loadFromFile()

    def getTopo(self) -> Topo:
        topo: Topo = Topo()
        for host in self.hosts:
            o: OneSession = OneSession(host)
            result = o.readARP()
            topo.addOneScan(result)

        return topo


if __name__ == '__main__':
    filename = 'pwd.xls'

    gear = ARPTopo(filename)
    topo = gear.getTopo()

    print(topo)

    with open('graph.json', 'w') as file:
        file.write(str(topo))
