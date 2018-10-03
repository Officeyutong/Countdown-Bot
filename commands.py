import config
from main import *


@command(name="broadcast", help="进行广播")
def broadcast_cmd(bot, context, args=None):
    # print_log("broadcasting..")
    group_id = context.get("group_id", -1)
    if group_id != -1:
        broadcast_at_group(group_id)


@command(name="reload", help="重新加载配置文件")
def reload_config(bot, context, args=None):
    import importlib
    importlib.reload(config)
    for item in dir(config):
        if item.startswith("__"):
            continue
        print("%s = %s" % (item, getattr(config, item)))


@command(name="help", help="查看帮助")
def help(bot: CQHttp, context=None, args=None):
    bot.send(context, "".join(
        map(lambda x: x[0]+" --- "+x[1][0]+"\n", commands.items())))


@command(name="阿克", help="阿克")
def ak(bot: CQHttp, context=None, args=None):
    bot.send(context, "您阿克了！")


@command(name="爆零", help="qwq")
def zero(bot: CQHttp, context=None, args=None):
    bot.send(context, "您不会爆零的qwq")


@command(name="oier", help="执行oierdb查询(http://bytew.net/OIer),/oier 姓名")
def oier_query(bot: CQHttp, context=None, args=None):
    print_log("querying "+str(args))
    if len(args) < 2:
        bot.send(context, "请输入姓名qwq")
        return
    import threading

    def query():
        from util import print_log
        # print_log("querying "+args[1])
        text = "查询到以下数据:\n"
        # bot.send(context,"查询到以下数据:")
        import oierdb
        count = 0
        for item in oierdb.fetch(args[1]):
            print_log("item:{}".format(item))
            text += "姓名:%s\n性别:%s\n" % (item["name"],
                                        {-1: "女", 1: "男"}.get(int(item["sex"]), "未知"))
            # text+="获得奖项:\n"
            awards = list(enumerate(eval(item["awards"])))
            for index, award in awards:
                # print_log(award)
                # print_log(type(award))
                for k, v in award.items():
                    if type(v) == type(str):
                        award[k] = award[k].strip()
                format_str = "在<{province}>{school}<{grade}>时参加<{contest}>以{score}分(全国排名{rank})的成绩获得<{type}>\n"
                text += format_str.format(grade=award["grade"],
                                          province=award["province"],
                                          rank=award["rank"],
                                          score=award["score"],
                                          school=award["school"],
                                          type=award["award_type"],
                                          contest=award["identity"]
                                          )
            count += 1
            if count >= 3:
                text += "\n余下记录太长，请去原网站查看."
                break
            text+='\n'
        while text[-1] == "\n":
            text = text[:-1]
        bot.send(context, text)
    thread: threading.Thread = threading.Thread(target=query)
    # query()
    thread.start()

@command(name = "wiki", help = "求助 OI Wiki(https://oi-wiki.org/)")
def oiwiki_query(bot: CQHttp, context=None, args=None):
    wikipages = {"枚举": "https://oi-wiki.org/basic/enumerate/", "模拟": "https://oi-wiki.org/basic/simulate/",
    "分治": "https://oi-wiki.org/basic/divide-and-conquer/", "贪心": "https://oi-wiki.org/basic/greedy/",
    "排序": "https://oi-wiki.org/basic/sort/", "表达式求值": "https://oi-wiki.org/basic/expression/",
    "二分": "https://oi-wiki.org/basic/binary/", "构造": "https://oi-wiki.org/basic/construction/",
    "搜索": "https://oi-wiki.org/search/", # 搜索
    "DFS": "https://oi-wiki.org/search/dfs/", "BFS": "https://oi-wiki.org/search/bfs/",
    "双向广搜": "https://oi-wiki.org/search/dbfs/", "启发式搜索": "https://oi-wiki.org/search/heuristic/",
    "A*": "https://oi-wiki.org/search/astar/", "迭代加深搜索": "https://oi-wiki.org/search/iterative/",
    "IDA*": "https://oi-wiki.org/search/idastar/", "回溯": "https://oi-wiki.org/search/backtracking/",
    "DancingLinks": "https://oi-wiki.org/search/dlx/", "搜索优化": "https://oi-wiki.org/search/optimization/",
    "DP": "https://oi-wiki.org/dp/", # DP
    "记搜": "https://oi-wiki.org/dp/memo/", "背包": "https://oi-wiki.org/dp/backpack/",
    "区间DP": "https://oi-wiki.org/dp/interval/", "DAGDP": "https://oi-wiki.org/dp/dag/",
    "树形DP": "https://oi-wiki.org/dp/tree/", "状压DP": "https://oi-wiki.org/dp/state/",
    "数位DP": "https://oi-wiki.org/dp/number/", "插头DP": "https://oi-wiki.org/dp/plug/",
    "DP优化": "https://oi-wiki.org/dp/optimization/", "其他DP": "https://oi-wiki.org/dp/misc/",
    "字串": "https://oi-wiki.org/string/", # 字串
    "字串标准库": "https://oi-wiki.org/string/stl/", "字串匹配": "https://oi-wiki.org/string/match/",
    "哈希": "https://oi-wiki.org/string/hash/", "KMP": "https://oi-wiki.org/string/kmp/",
    "Trie": "https://oi-wiki.org/string/trie/", "回文自动机": "https://oi-wiki.org/string/pam/",
    "回文树": "https://oi-wiki.org/string/palindrome-tree/", "SA": "https://oi-wiki.org/string/sa/",
    "AC自动机": "https://oi-wiki.org/string/ac-automaton/", "SAM": "https://oi-wiki.org/string/sam/",
    "后缀树": "https://oi-wiki.org/string/suffix-tree/", "Manacher": "https://oi-wiki.org/string/manacher/",
    "最小表示法": "https://oi-wiki.org/string/minimal-string/",
    "数学": "https://oi-wiki.org/math/", # 数学
    "进制": "https://oi-wiki.org/math/base/", "位运算": "https://oi-wiki.org/math/bit/",
    "质数": "https://oi-wiki.org/math/prime/", "最大公因数": "https://oi-wiki.org/math/gcd/",
    "贝祖定理": "https://oi-wiki.org/math/bezouts/", "欧拉函数": "https://oi-wiki.org/math/euler/",
    "筛法": "https://oi-wiki.org/math/sieve/", "莫比乌斯反演": "https://oi-wiki.org/math/mobius/",
    "费马小定理": "https://oi-wiki.org/math/fermat/", "快速幂": "https://oi-wiki.org/math/quick-pow/",
    "线性基": "https://oi-wiki.org/math/basis/", "逆元": "https://oi-wiki.org/math/inverse/",
    "线性方程": "https://oi-wiki.org/math/linear-equation/", "高斯消元": "https://oi-wiki.org/math/gauss/",
    "矩阵": "https://oi-wiki.org/math/matrix/", "CRT": "https://oi-wiki.org/math/crt/",
    "复数": "https://oi-wiki.org/math/complex/", "高精": "https://oi-wiki.org/math/bignum/",
    "分段打表": "https://oi-wiki.org/math/dictionary/", "原根": "https://oi-wiki.org/math/primitive-root/",
    "BSGS": "https://oi-wiki.org/math/bsgs/", "博弈论": "https://oi-wiki.org/math/game/",
    "多项式": "https://oi-wiki.org/math/poly/", "FFT": "https://oi-wiki.org/math/fft/",
    "NTT": "https://oi-wiki.org/math/ntt/", "FWT": "https://oi-wiki.org/math/fwt/",
    "组合": "https://oi-wiki.org/math/combination/", "卡特兰数": "https://oi-wiki.org/math/catalan/",
    "斯特林数": "https://oi-wiki.org/math/stirling/", "康托展开": "https://oi-wiki.org/math/cantor/",
    "容斥原理": "https://oi-wiki.org/math/inclusion-exclusion-principle/", 
    "抽屉原理": "https://oi-wiki.org/math/drawer-principle/", "期望": "https://oi-wiki.org/math/expectation/",
    "置换群": "https://oi-wiki.org/math/permutation-group/", "数值积分": "https://oi-wiki.org/math/integral/",
    "线规": "https://oi-wiki.org/math/linear-programming/", "数学杂项": "https://oi-wiki.org/math/misc/",
    "数据结构": "https://oi-wiki.org/ds/", "STL": "https://oi-wiki.org/ds/stl/", # 数构
    "vector": "https://oi-wiki.org/ds/stl/vector/", "map": "https://oi-wiki.org/ds/stl/map/",
    "priority_queue": "https://oi-wiki.org/ds/stl/priority_queue/",
    "pb_ds": "https://oi-wiki.org/ds/pb-ds/",
    "priority_queue(pb_ds)": "https://oi-wiki.org/ds/pb-ds/priority-queue/",
    "栈": "https://oi-wiki.org/ds/stack/", "队列": "https://oi-wiki.org/ds/queue/",
    "链表": "https://oi-wiki.org/ds/linked-list/", "哈希表": "https://oi-wiki.org/ds/hash/",
    "并查集": "https://oi-wiki.org/ds/dsu/", "堆": "https://oi-wiki.org/ds/heap/",
    "分块": "https://oi-wiki.org/ds/square-root-decomposition/",
    "块状链表": "https://oi-wiki.org/ds/block-list/", "块状数组": "https://oi-wiki.org/ds/block-array/",
    "树分块": "https://oi-wiki.org/ds/tree-decompose/", "单调栈": "https://oi-wiki.org/ds/monotonous-stack/",
    "单调队列": "https://oi-wiki.org/ds/monotonous-queue/",
    "倍增": "https://oi-wiki.org/ds/sparse-table/", "树状数组": "https://oi-wiki.org/ds/bit/",
    "线段树": "https://oi-wiki.org/ds/segment/", "划分树": "https://oi-wiki.org/ds/dividing/",
    "虚树": "https://oi-wiki.org/ds/virtual-tree/", "SBT": "https://oi-wiki.org/ds/sbt/",
    "Treap": "https://oi-wiki.org/ds/treap/", "Splay": "https://oi-wiki.org/ds/splay/",
    "AVL树": "https://oi-wiki.org/ds/avl/", "替罪羊树": "https://oi-wiki.org/ds/scapegoat/",
    "线段树套线段树": "https://oi-wiki.org/ds/seg-in-seg/",
    "平衡树套线段树": "https://oi-wiki.org/ds/seg-in-balanced/",
    "线段树套平衡树": "https://oi-wiki.org/ds/balanced-in-seg/",
    "K-DTree": "https://oi-wiki.org/ds/k-dtree/", "可持久化": "https://oi-wiki.org/ds/persistent/",
    "可持久化线段树": "https://oi-wiki.org/ds/persistent-seg/",
    "可持久化块状数组": "https://oi-wiki.org/ds/persistent-block-array/",
    "可持久化平衡树": "https://oi-wiki.org/ds/persistent-balanced/",
    "可持久化Trie": "https://oi-wiki.org/ds/persistent-trie/",
    "LCT": "https://oi-wiki.org/ds/lct/", "EulerTourTree": "https://oi-wiki.org/ds/ett/",
    "图论": "https://oi-wiki.org/graph/", # 图论
    "图论基础": "https://oi-wiki.org/graph/basic/", "树": "https://oi-wiki.org/graph/tree-basic/",
    "树剖": "https://oi-wiki.org/graph/heavy-light-decomposition/",
    "树分治": "https://oi-wiki.org/graph/tree-divide/", "树其他": "https://oi-wiki.org/graph/tree-misc/",
    "动态树分治": "https://oi-wiki.org/graph/dynamic-tree-divide/", "LCA": "https://oi-wiki.org/graph/lca/",
    "图遍历": "https://oi-wiki.org/graph/traverse/", "DAG": "https://oi-wiki.org/graph/dag/",
    "最小生成树": "https://oi-wiki.org/graph/mst/", "拓扑排序": "https://oi-wiki.org/graph/topo/",
    "2-SAT": "https://oi-wiki.org/graph/2-sat/", "欧拉图": "https://oi-wiki.org/graph/euler/",
    "强连通分量": "https://oi-wiki.org/graph/scc/", "双连通分量": "https://oi-wiki.org/graph/bcc/",
    "割点": "https://oi-wiki.org/graph/bridge/", "二分图": "https://oi-wiki.org/graph/bi-graph/",
    "最短路": "https://oi-wiki.org/graph/shortest-path/",
    "差分约束": "https://oi-wiki.org/graph/differential-constraints/",
    "k短路": "https://oi-wiki.org/graph/kth-path/", "最小环": "https://oi-wiki.org/graph/min-circle/",
    "网络流": "https://oi-wiki.org/graph/flow/", "拆点": "https://oi-wiki.org/graph/flow/node/",
    "最大流": "https://oi-wiki.org/graph/flow/max-flow/", "最小割": "https://oi-wiki.org/graph/flow/min-cut/",
    "费用流": "https://oi-wiki.org/graph/flow/min-cost/", "上下界网络流": "https://oi-wiki.org/graph/flow/bound/",
    "计算几何": "https://oi-wiki.org/geometry/", # 计算几何
    "二维计算几何": "https://oi-wiki.org/geometry/2d/", "三维计算几何": "https://oi-wiki.org/geometry/3d/",
    "皮克定理": "https://oi-wiki.org/geometry/pick/", "三角剖分": "https://oi-wiki.org/geometry/triangulation/",
    "凸包": "https://oi-wiki.org/geometry/convex-hull/", "扫描线": "https://oi-wiki.org/geometry/scanning/",
    "旋转卡壳": "https://oi-wiki.org/geometry/rotating-calipers/",
    "半平面交": "https://oi-wiki.org/geometry/half-plane-intersection/",
    "几何其他": "https://oi-wiki.org/geometry/magic/",
    "杂项": "https://oi-wiki.org/misc/", # 杂项
    "非传统题": "https://oi-wiki.org/misc/non-traditional/", "CDQ分治": "https://oi-wiki.org/misc/cdq-divide/",
    "莫队": "https://oi-wiki.org/misc/mo-algo/", "爬山算法": "https://oi-wiki.org/misc/hill-climbing/",
    "分数规划": "https://oi-wiki.org/misc/fractional-programming/",
    "模拟退火": "https://oi-wiki.org/misc/simulated-annealing/",
    "朱刘算法": "https://oi-wiki.org/misc/zhu-liu-algorithm/",
    "矩阵树定理": "https://oi-wiki.org/misc/matrix-tree/",
    "随机增量法": "https://oi-wiki.org/misc/random-incremental/",
    "随机化": "https://oi-wiki.org/misc/random/", "离线": "https://oi-wiki.org/misc/offline/",
    "距离": "https://oi-wiki.org/misc/distance/", "字节顺序": "https://oi-wiki.org/misc/endianness/",
    "复杂度": "https://oi-wiki.org/misc/complexity/", "读入输出优化": "https://oi-wiki.org/misc/io/",
    "离散化": "https://oi-wiki.org/misc/discrete/", "树上启发式合并": "https://oi-wiki.org/misc/dsu-on-tree/" }   
    if args in wikipages:
        bot.send(context, "OI Wiki 中有名为「%s」的页面：%s" % (args, wikipages[args]))
    else:
        bot.send(context, "OI Wiki 中无结果")