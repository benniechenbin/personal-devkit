"""analysis_engine 的通用异常定义。"""


class AnalysisEngineError(Exception):
    """所有 analysis_engine 异常的基类。"""

    pass


class NormalizationError(AnalysisEngineError):
    """当数据归一化失败时抛出。"""

    pass


class CalculationError(AnalysisEngineError):
    """当指标计算过程中发生逻辑错误时抛出。"""

    pass


class ValidationError(AnalysisEngineError):
    """当输入数据不符合分析要求时抛出。"""

    pass
