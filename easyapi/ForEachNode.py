from comfy_execution.graph_utils import GraphBuilder, is_link
from .util import any_type

# 支持的最大参数个数
NUM_FLOW_SOCKETS = 20


class InnerIntMathOperation:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("INT", {"default": 0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
                "b": ("INT", {"default": 0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
                "operation": (["add", "subtract", "multiply", "divide", "modulo", "power"],),
            },
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "calc"

    CATEGORY = "EasyApi/Logic"

    def calc(self, a, b, operation):
        if operation == "add":
            return (a + b,)
        elif operation == "subtract":
            return (a - b,)
        elif operation == "multiply":
            return (a * b,)
        elif operation == "divide":
            return (a // b,)
        elif operation == "modulo":
            return (a % b,)
        elif operation == "power":
            return (a ** b,)


COMPARE_FUNCTIONS = {
    "a == b": lambda a, b: a == b,
    "a != b": lambda a, b: a != b,
    "a < b": lambda a, b: a < b,
    "a > b": lambda a, b: a > b,
    "a <= b": lambda a, b: a <= b,
    "a >= b": lambda a, b: a >= b,
}


class InnerIntCompare:
    @classmethod
    def INPUT_TYPES(s):
        compare_functions = list(COMPARE_FUNCTIONS.keys())
        return {
            "required": {
                "a": ("INT", {"default": 0}),
                "b": ("INT", {"default": 0}),
                "comparison": (compare_functions, {"default": "a == b"}),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "compare"
    CATEGORY = "EasyApi/Logic"

    def compare(self, a, b, comparison):
        return (COMPARE_FUNCTIONS[comparison](a, b),)


class InnerLoopClose:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "flow_control": ("FLOW_CONTROL", {"rawLink": True}),
                "condition": ("BOOLEAN", {"forceInput": True}),
            },
            "optional": {
            },
            "hidden": {
                "dynprompt": "DYNPROMPT",
                "unique_id": "UNIQUE_ID",
            }
        }
        for i in range(NUM_FLOW_SOCKETS):
            inputs["optional"]["initial_value%d" % i] = ("*",)
        return inputs

    RETURN_TYPES = tuple([any_type] * NUM_FLOW_SOCKETS)
    RETURN_NAMES = tuple(["value%d" % i for i in range(NUM_FLOW_SOCKETS)])
    FUNCTION = "while_loop_close"

    CATEGORY = "EasyApi/Logic"

    def explore_dependencies(self, node_id, dynprompt, upstream):
        node_info = dynprompt.get_node(node_id)
        if "inputs" not in node_info:
            return
        for k, v in node_info["inputs"].items():
            if is_link(v):
                parent_id = v[0]
                if parent_id not in upstream:
                    upstream[parent_id] = []
                    self.explore_dependencies(parent_id, dynprompt, upstream)
                upstream[parent_id].append(node_id)

    def collect_contained(self, node_id, upstream, contained):
        if node_id not in upstream:
            return
        for child_id in upstream[node_id]:
            if child_id not in contained:
                contained[child_id] = True
                self.collect_contained(child_id, upstream, contained)


    def while_loop_close(self, flow_control, condition, dynprompt=None, unique_id=None, **kwargs):
        if not condition:
            # We're done with the loop
            values = []
            for i in range(NUM_FLOW_SOCKETS):
                values.append(kwargs.get("initial_value%d" % i, None))
            return tuple(values)

        # We want to loop
        this_node = dynprompt.get_node(unique_id)
        upstream = {}
        # Get the list of all nodes between the open and close nodes
        self.explore_dependencies(unique_id, dynprompt, upstream)

        contained = {}
        open_node = flow_control[0]
        self.collect_contained(open_node, upstream, contained)
        contained[unique_id] = True
        contained[open_node] = True

        # We'll use the default prefix, but to avoid having node names grow exponentially in size,
        # we'll use "Recurse" for the name of the recursively-generated copy of this node.
        graph = GraphBuilder()
        for node_id in contained:
            original_node = dynprompt.get_node(node_id)
            node = graph.node(original_node["class_type"], "Recurse" if node_id == unique_id else node_id)
            node.set_override_display_id(node_id)
        for node_id in contained:
            original_node = dynprompt.get_node(node_id)
            node = graph.lookup_node("Recurse" if node_id == unique_id else node_id)
            for k, v in original_node["inputs"].items():
                if is_link(v) and v[0] in contained:
                    parent = graph.lookup_node(v[0])
                    node.set_input(k, parent.out(v[1]))
                else:
                    node.set_input(k, v)
        new_open = graph.lookup_node(open_node)
        for i in range(NUM_FLOW_SOCKETS):
            key = "initial_value%d" % i
            new_open.set_input(key, kwargs.get(key, None))
        my_clone = graph.lookup_node("Recurse" )
        result = map(lambda x: my_clone.out(x), range(NUM_FLOW_SOCKETS))
        return {
            "result": tuple(result),
            "expand": graph.finalize(),
        }


def find_max_initial_value_number(kwargs, substring):
    # 提取所有键
    keys = list(kwargs.keys())

    # 筛选出形如 'initial_valueX' 的键
    matching_keys = [key for key in keys if key.startswith('initial_value')]

    # 从匹配的键中提取数字部分
    numbers = [int(key[len('initial_value'):]) for key in matching_keys]

    # 找到最大数字
    max_number = max(numbers) if numbers else 1

    return max_number


class ForEachOpen:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "total": ("INT", {"default": 1, "min": 1, "max": 1000, "step": 1, "tooltip": "总循环次数"}),
            },
            "optional": {
                # 必须声明全部，否者循环时只有第一个值能正确传递
                "initial_value%d" % i: (any_type,) for i in range(1, NUM_FLOW_SOCKETS)
            },
            "hidden": {
                "initial_value0": (any_type,)
            }
        }

    RETURN_TYPES = tuple(["FLOW_CONTROL", "INT", "INT"] + [any_type] * (NUM_FLOW_SOCKETS - 1))
    RETURN_NAMES = tuple(["flow_control", "index", "total"] + ["value%d" % i for i in range(1, NUM_FLOW_SOCKETS)])
    OUTPUT_TOOLTIPS = ("开始节点元信息", "循环索引值", "总循环次数，不宜太大，会影响到消息长度",)
    FUNCTION = "for_loop_open"

    CATEGORY = "EasyApi/Logic"

    def for_loop_open(self, total, **kwargs):
        graph = GraphBuilder()

        if "initial_value0" in kwargs:
            index = kwargs["initial_value0"]
        else:
            index = 0

        initial_value_num = find_max_initial_value_number(kwargs, "initial_value")

        # 好像没啥用
        # while_open = graph.node("WhileLoopOpen", condition=total, initial_value0=index, **{("initial_value%d" % i): kwargs.get("initial_value%d" % i, None) for i in range(1, initial_value_num + 1)})

        outputs = [kwargs.get("initial_value%d" % i, None) for i in range(1, initial_value_num + 1)]
        return {
            "result": tuple(["stub", index, total] + outputs),
            "expand": graph.finalize(),
        }


class ForEachClose:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "flow_control": ("FLOW_CONTROL", {"rawLink": True}),
            },
            "optional": {
                # 必须声明全部，否者循环时只有第一个值能正确传递
                "initial_value%d" % i: (any_type, {"rawLink": True}) for i in range(1, NUM_FLOW_SOCKETS)
            },
        }

    RETURN_TYPES = tuple([any_type] * (NUM_FLOW_SOCKETS-1))
    RETURN_NAMES = tuple(["value%d" % i for i in range(1, NUM_FLOW_SOCKETS)])
    FUNCTION = "for_loop_close"

    CATEGORY = "EasyApi/Logic"

    def for_loop_close(self, flow_control, **kwargs):
        graph = GraphBuilder()
        # ForEachOpen node id
        openNodeId = flow_control[0]
        # 计算索引, a传open节点的第3个输出参数，即index参数
        sub = graph.node(InnerIntMathOperation.__name__, operation="add", a=[openNodeId, 1], b=1)
        # 边界条件约束, b传open节点的第3个输出参数，即total参数
        cond = graph.node(InnerIntCompare.__name__, a=sub.out(0), b=[openNodeId, 2], comparison='a < b')
        # 构建循环传递参数
        initial_value_num = find_max_initial_value_number(kwargs, "initial_value")
        input_values = {("initial_value%d" % i): kwargs.get("initial_value%d" % i, None) for i in range(1, initial_value_num + 1)}
        while_close = graph.node(InnerLoopClose.__name__,
                                 flow_control=flow_control,
                                 condition=cond.out(0),
                                 initial_value0=sub.out(0),
                                 **input_values)
        return {
            "result": tuple([while_close.out(i) for i in range(1, initial_value_num + 1)]),
            "expand": graph.finalize(),
        }


NODE_CLASS_MAPPINGS = {
    "InnerIntMathOperation": InnerIntMathOperation,
    "InnerIntCompare": InnerIntCompare,
    "InnerLoopClose": InnerLoopClose,
    "ForEachOpen": ForEachOpen,
    "ForEachClose": ForEachClose,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "InnerIntMathOperation": "InnerIntMathOperation",
    "InnerIntCompare": "InnerIntCompare",
    "InnerLoopClose": "InnerLoopClose",
    "ForEachOpen": "ForEachOpen",
    "ForEachClose": "ForEachClose",
}
