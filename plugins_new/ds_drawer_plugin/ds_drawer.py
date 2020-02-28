from graphviz import Digraph
from io import BytesIO

import copy
import pdb
import tempfile
import os
import collections


class SAMNode:
    link = None
    chds = None
    max_len = 0
    right_size = None
    vtx_id = 0
    node_list = []
    accept = False
    to = None
    chd_on_tree: list = None

    def __str__(self):
        ret = "SAMNode{{ID:{},max_len={},rightsize={},".format(
            self.vtx_id, self.max_len, self.right_size)
        ret += "link={},".format(None if self.link is None else self.link.vtx_id)
        for k, v in self.chds.items():
            ret += "{}->{},".format(k, v.vtx_id)
        return ret+"}}"

    def __repr__(self):
        return self.__str__()

    def __init__(self, node_list, strid, max_len=0):
        self.max_len = max_len
        self.node_list = node_list
        self.node_list.append(self)
        self.vtx_id = len(node_list)
        self.chds = dict()
        self.right_size = collections.OrderedDict()
        self.right_size[strid] = 1
        self.to = list()
        self.chd_on_tree = list()

    def clone(self):
        cloned = SAMNode(self.node_list, self.max_len)
        cloned.link = self.link
        cloned.chds = copy.copy(self.chds)
        cloned.right_size = collections.OrderedDict()
        cloned.accept = False
        return cloned


def append(char: str, last: SAMNode, root: SAMNode, str_id: int)->SAMNode:
    new = SAMNode(root.node_list, str_id, last.max_len+1)
    curr = last
    new.accept = True
    while curr and (char not in curr.chds):
        curr.chds[char] = new
        curr = curr.link
    if curr is None:
        new.link = root
    elif curr.chds[char].max_len == curr.max_len+1:
        new.link = curr.chds[char]
    else:
        oldNode: SAMNode = curr.chds[char]
        newNode: SAMNode = oldNode.clone()
        new.link = oldNode.link = newNode
        newNode.max_len = curr.max_len+1
        while curr is not None and curr.chds[char] == oldNode:
            curr.chds[char] = newNode
            curr = curr.link
    return new


def DFS(node: SAMNode):
    for chd in node.chd_on_tree:
        DFS(chd)
        for k, v in chd.right_size.items():
            if k not in node.right_size:
                node.right_size[k] = v
            else:
                node.right_size[k] += v


def generate_graph(string, format):
    nodes = []
    root = SAMNode(nodes, 0)
    root.right_size = collections.OrderedDict()
    strs = []
    if "|" in string:
        strs = string.split("|")
    else:
        strs.append(string)
    print(strs)
    for idx, curr in enumerate(strs):
        last = root
        for x in curr:
            last = append(x, last, root, idx+1)
    dot = Digraph("SAM")
    nodes.sort(key=lambda x: x.max_len, reverse=True)
    for x in nodes:
        for i in range(1, 1+len(strs)):
            if i not in x.right_size:
                x.right_size[i] = 0
        if x.link is not None:
            x.link.chd_on_tree.append(x)
    DFS(root)
    for x in nodes:
        sorted(x.right_size)
    nodes.sort(key=lambda x: x.vtx_id)
    for node in nodes:
        label = "{}\nMax={}".format(node.vtx_id, node.max_len)
        if len(node.right_size):
            sorted(node.right_size)
            for k, v in node.right_size.items():
                label += "\nsize{}={}".format(k, v)
        dot.node(str(node.vtx_id), label)
        if node.link:
            dot.edge(str(node.vtx_id), str(node.link.vtx_id), color="red")
        for k, v in node.chds.items():
            dot.edge(str(node.vtx_id), str(v.vtx_id), k)
    tmpdir = tempfile.mkdtemp()
    target = os.path.join(tmpdir, "qwq")
    dot.render(filename=target, format=format)
    return target+"."+format
