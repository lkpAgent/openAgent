"""示例自定义工具 - 文本处理工具。"""

import asyncio
import re
from typing import List, Dict, Any
from chat_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from chat_agent.utils.logger import get_logger

logger = get_logger("example_tool")


class TextProcessorTool(BaseTool):
    """文本处理工具示例 - 提供多种文本处理功能。"""
    
    def get_name(self) -> str:
        """返回工具名称。"""
        return "text_processor"
    
    def get_description(self) -> str:
        """返回工具描述。"""
        return "文本处理工具，支持大小写转换、字符统计、关键词提取等功能"
    
    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数。"""
        return [
            ToolParameter(
                name="text",
                type=ToolParameterType.STRING,
                description="要处理的文本内容",
                required=True
            ),
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="处理操作类型",
                required=True,
                enum=["uppercase", "lowercase", "count", "extract_keywords", "reverse"]
            ),
            ToolParameter(
                name="options",
                type=ToolParameterType.OBJECT,
                description="额外选项配置",
                required=False,
                default={}
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行文本处理操作。"""
        try:
            # 使用基类的参数验证
            validated_params = self.validate_parameters(**kwargs)
            
            # 获取参数
            text = validated_params.get("text")
            operation = validated_params.get("operation")
            options = validated_params.get("options", {})
            
            # 额外的参数验证
            if not text:
                return ToolResult(
                    success=False,
                    result=None,
                    error="text参数是必需的"
                )
            
            if not operation:
                return ToolResult(
                    success=False,
                    result=None,
                    error="operation参数是必需的"
                )
            
            logger.info(f"执行文本处理: {operation} on text length {len(text)}")
            
            # 模拟异步处理
            await asyncio.sleep(0.1)
            
            # 执行不同的处理操作
            result_data = {}
            
            if operation == "uppercase":
                result_data = self._process_uppercase(text, options)
            elif operation == "lowercase":
                result_data = self._process_lowercase(text, options)
            elif operation == "count":
                result_data = self._process_count(text, options)
            elif operation == "extract_keywords":
                result_data = self._process_extract_keywords(text, options)
            elif operation == "reverse":
                result_data = self._process_reverse(text, options)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"不支持的操作类型: {operation}"
                )
            
            return ToolResult(
                success=True,
                result=result_data,
                metadata={
                    "operation": operation,
                    "original_length": len(text),
                    "tool_version": "1.0.0"
                }
            )
            
        except Exception as e:
            logger.error(f"文本处理工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                error=f"工具执行失败: {str(e)}"
            )
    
    def _process_uppercase(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """转换为大写。"""
        result = text.upper()
        return {
            "processed_text": result,
            "operation": "uppercase",
            "changed_characters": sum(1 for c in text if c.islower())
        }
    
    def _process_lowercase(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """转换为小写。"""
        result = text.lower()
        return {
            "processed_text": result,
            "operation": "lowercase",
            "changed_characters": sum(1 for c in text if c.isupper())
        }
    
    def _process_count(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """统计文本信息。"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "line_count": len(text.splitlines()),
            "uppercase_count": sum(1 for c in text if c.isupper()),
            "lowercase_count": sum(1 for c in text if c.islower()),
            "digit_count": sum(1 for c in text if c.isdigit()),
            "space_count": sum(1 for c in text if c.isspace())
        }
    
    def _process_extract_keywords(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键词。"""
        # 简单的关键词提取逻辑
        # 移除标点符号，转换为小写，分割单词
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
        words = cleaned_text.split()
        
        # 过滤常见停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        max_keywords = options.get('max_keywords', 10)
        top_keywords = sorted_keywords[:max_keywords]
        
        return {
            "keywords": [word for word, freq in top_keywords],
            "keyword_frequencies": dict(top_keywords),
            "total_unique_words": len(word_freq),
            "total_words_processed": len(keywords)
        }
    
    def _process_reverse(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """反转文本。"""
        reverse_type = options.get('reverse_type', 'characters')
        
        if reverse_type == 'characters':
            result = text[::-1]
        elif reverse_type == 'words':
            words = text.split()
            result = ' '.join(reversed(words))
        elif reverse_type == 'lines':
            lines = text.splitlines()
            result = '\n'.join(reversed(lines))
        else:
            result = text[::-1]  # 默认字符反转
        
        return {
            "processed_text": result,
            "operation": "reverse",
            "reverse_type": reverse_type,
            "original_text": text
        }


class NumberProcessorTool(BaseTool):
    """数字处理工具示例。"""
    
    def get_name(self) -> str:
        return "number_processor"
    
    def get_description(self) -> str:
        return "数字处理工具，支持数字格式化、进制转换、数学运算等"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="number",
                type=ToolParameterType.FLOAT,
                description="要处理的数字",
                required=True
            ),
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="处理操作",
                required=True,
                enum=["format", "convert_base", "round", "factorial", "prime_check"]
            ),
            ToolParameter(
                name="precision",
                type=ToolParameterType.INTEGER,
                description="小数精度",
                required=False,
                default=2
            ),
            ToolParameter(
                name="target_base",
                type=ToolParameterType.INTEGER,
                description="目标进制（2-36）",
                required=False,
                default=10
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行数字处理操作。"""
        try:
            # 使用基类的参数验证
            validated_params = self.validate_parameters(**kwargs)
            
            number = validated_params.get("number")
            operation = validated_params.get("operation")
            precision = validated_params.get("precision", 2)
            target_base = validated_params.get("target_base", 10)
            
            if number is None:
                return ToolResult(
                    success=False,
                    result=None,
                    error="number参数是必需的"
                )
            
            logger.info(f"执行数字处理: {operation} on {number}")
            
            await asyncio.sleep(0.05)  # 模拟处理时间
            
            if operation == "format":
                result = {
                    "formatted_number": f"{number:.{precision}f}",
                    "scientific_notation": f"{number:.{precision}e}",
                    "percentage": f"{number * 100:.{precision}f}%"
                }
            elif operation == "convert_base":
                if target_base < 2 or target_base > 36:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="目标进制必须在2-36之间"
                    )
                
                int_number = int(number)
                if target_base == 10:
                    converted = str(int_number)
                else:
                    converted = self._convert_to_base(int_number, target_base)
                
                result = {
                    "original_number": int_number,
                    "target_base": target_base,
                    "converted_value": converted
                }
            elif operation == "round":
                result = {
                    "original": number,
                    "rounded": round(number, precision),
                    "floor": int(number),
                    "ceiling": int(number) + (1 if number > int(number) else 0)
                }
            elif operation == "factorial":
                int_number = int(abs(number))
                if int_number > 20:  # 防止计算过大的阶乘
                    return ToolResult(
                        success=False,
                        result=None,
                        error="数字太大，无法计算阶乘（最大支持20）"
                    )
                
                factorial_result = 1
                for i in range(1, int_number + 1):
                    factorial_result *= i
                
                result = {
                    "number": int_number,
                    "factorial": factorial_result
                }
            elif operation == "prime_check":
                int_number = int(abs(number))
                is_prime = self._is_prime(int_number)
                
                result = {
                    "number": int_number,
                    "is_prime": is_prime,
                    "factors": self._get_factors(int_number) if not is_prime else [1, int_number]
                }
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"不支持的操作: {operation}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "operation": operation,
                    "original_number": number
                }
            )
            
        except Exception as e:
            logger.error(f"数字处理工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                error=f"工具执行失败: {str(e)}"
            )
    
    def _convert_to_base(self, number: int, base: int) -> str:
        """转换数字到指定进制。"""
        if number == 0:
            return "0"
        
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = ""
        
        while number > 0:
            result = digits[number % base] + result
            number //= base
        
        return result
    
    def _is_prime(self, n: int) -> bool:
        """检查是否为质数。"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def _get_factors(self, n: int) -> List[int]:
        """获取数字的所有因子。"""
        factors = []
        for i in range(1, int(n**0.5) + 1):
            if n % i == 0:
                factors.append(i)
                if i != n // i:
                    factors.append(n // i)
        return sorted(factors)