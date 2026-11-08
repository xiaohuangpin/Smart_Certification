from openai.types.shared import reasoning
import ast
import operator
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import logfire
from app.engine.agent.baseagent import BaseAgent


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError(f"不支持的算式: {ast.dump(node)}")


def calculator(expression: str) -> float:
    """计算器工具：输入算式字符串，返回计算结果。

    Args:
        expression: 算式字符串，如 "100+200*0.06-5"、"1500/1.06"，仅支持数字与 + - * / // % ** 及括号

    Returns:
        计算结果（浮点数）
    """
    expr = expression.replace(",", "").replace(" ", "")
    return float(_eval(ast.parse(expr, mode="eval")))


class CalcRow(BaseModel):
    """参与金额计算的参考行"""
    sheet_name: str = Field(description="参考行所在的 sheet 名")
    row_index: int = Field(description="参考行的行索引（Excel 原生行号，即 row_id）")
    amount: str = Field(description="该行参与计算的金额")


class CalcResult(BaseModel):
    """金额计算结果结构化输出"""
    amount: str = Field(description="计算出的金额，字符串，保留两位小数")
    reason: str = Field(max_length=500, description="计算原因说明，不超过 500 字")
    details: list[CalcRow] = Field(default_factory=list, description="参与计算的行明细")


class AccountingCalcAgent(BaseAgent):
    """专业会计 Agent：根据 Excel 表格与会计科目模板计算金额，并定位取数参考行"""

    SYSTEM_PROMPT = """# Role
你是一名专业会计，负责根据用户提交的 Excel 表格与会计科目模板，计算目标金额，并定位出该金额所取数的参考行。

# 输入说明
- 会计科目模板：说明需要计算的科目、取数口径与计算公式。
- Excel 表格：多个 sheet 的 Markdown 表格，每个表格首列为 row_id（对应 Excel 原生行号）。

# 工作流程
1. 结合会计科目模板，识别需要取数/计算的目标科目及公式；
2. 在 Excel 表格中定位参与计算的行（参考行）；
3. 使用「计算器」工具对算式字符串进行计算，得到最终金额；
4. 输出金额及参与计算的行明细。

# 输出规则
- amount：计算出的最终金额，字符串，保留两位小数；
- reason：计算原因说明，不超过 500 字；
- details：参与计算的行明细列表，每项含 sheet_name（sheet 名称）、row_index（该行 row_id 对应的原生行号，整数）、amount（该行参与计算金额，字符串）；
- 作为取数依据但未直接参与计算的行，也应列入 details 并注明其金额。
"""

    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(base_url=base_url, api_key=api_key, model=model)
        self.agent: Agent[None, CalcResult] = Agent(
            self.llm,
            output_type=CalcResult,
            system_prompt=self.SYSTEM_PROMPT,
            tools=[calculator],
        )

    @staticmethod
    def _format_sheets(excel_md: dict[str, str]) -> str:
        """将 {sheet名: markdown} 拼为分块的输入文本"""
        return "\n\n".join(f"## Sheet: {name}\n{md}" for name, md in excel_md.items())

    def _build_prompt(self, excel_md: dict[str, str], template: str) -> str:
        return (
            f"## 会计科目模板\n{template}\n\n"
            f"## Excel 表格\n{self._format_sheets(excel_md)}\n\n"
            f"请根据会计科目模板定位参考行并计算目标金额，输出结构化结果。"
        )

    def calc(self, excel_md: dict[str, str], template: str) -> tuple[CalcResult, int]:
        """根据 Excel 表格与会计科目模板计算金额并定位参考行

        Args:
            excel_md: {sheet名: markdown内容}
            template: 会计科目模板文本
        Returns:
            (CalcResult, total_tokens)
        """
        result = self.agent.run_sync(self._build_prompt(excel_md, template))
        usage = result.usage
        usage = usage() if callable(usage) else usage
        return result.output, usage.input_tokens + usage.output_tokens


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    logfire.configure(send_to_logfire=False, service_name="agent")

    agent = AccountingCalcAgent(
        base_url=os.getenv("base_url"),
        api_key=os.getenv("api_key"),
        model="CM-Pub-DeepSeek-V4-Flash-0731",
    )

    excel_md = {"示例表": "| row_id | 项目 | 金额 |\n|---|---|---|\n| 2 | 收入 | 100.00 |\n| 5 | 成本 | 30.00 |"}
    template = "计算利润：收入 - 成本，保留两位小数"
    result, tokens = agent.calc(excel_md, template)
    print(result.model_dump())
    print(f"tokens: {tokens}")
