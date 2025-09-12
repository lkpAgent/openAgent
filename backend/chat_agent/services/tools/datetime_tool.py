from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Literal, ClassVar
import datetime
import pytz
import logging

logger = logging.getLogger("datetime_tool")

# 定义输入参数模型（使用Pydantic替代原get_parameters()）
class DateTimeInput(BaseModel):
    operation: Literal["current_time", "timezone_convert", "date_diff", "add_time", "format_date"] = Field(
        description="操作类型: current_time(当前时间), timezone_convert(时区转换), "
                  "date_diff(日期差), add_time(时间加减), format_date(格式化日期)"
    )
    timezone: Optional[str] = Field(
        default="UTC",
        description="时区名称 (e.g., 'UTC', 'Asia/Shanghai')"
    )
    date_string: Optional[str] = Field(
        description="日期字符串 (格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"
    )
    target_timezone: Optional[str] = Field(
        description="目标时区（用于时区转换）"
    )
    days: Optional[int] = Field(
        default=0,
        description="要加减的天数"
    )
    hours: Optional[int] = Field(
        default=0,
        description="要加减的小时数"
    )
    format: Optional[str] = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="日期格式字符串 (e.g., '%Y-%m-%d %H:%M:%S')"
    )

class DateTimeTool(BaseTool):
    """日期时间操作工具（支持时区转换、日期计算等）"""

    name: ClassVar[str] = "datetime_tool"
    description: ClassVar[str] = """执行日期时间相关操作，包括：
    - 获取当前时间
    - 时区转换
    - 计算日期差
    - 日期时间加减
    - 格式化日期
    使用时必须指定operation参数确定操作类型。"""
    args_schema: Type[BaseModel] = DateTimeInput

    def _parse_datetime(self, date_string: str, timezone_str: str = "UTC") -> datetime.datetime:
        """解析日期字符串（私有方法）"""
        tz = pytz.timezone(timezone_str)
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y"
        ]

        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(date_string, fmt)
                return tz.localize(dt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期字符串: {date_string}")

    def _run(self,
             operation: str,
             timezone: str = "UTC",
             date_string: Optional[str] = None,
             target_timezone: Optional[str] = None,
             days: int = 0,
             hours: int = 0,
             format: str = "%Y-%m-%d %H:%M:%S") -> dict:
        """同步执行日期时间操作"""
        logger.info(f"执行日期时间操作: {operation}")

        try:
            if operation == "current_time":
                tz = pytz.timezone(timezone)
                now = datetime.datetime.now(tz)
                return {
                    "status": "success",
                    "result": {
                        "formatted": now.strftime(format),
                        "iso": now.isoformat(),
                        "timestamp": now.timestamp(),
                        "timezone": timezone
                    },
                    "summary": f"当前时间 ({timezone}): {now.strftime(format)}"
                }

            elif operation == "timezone_convert":
                if not date_string or not target_timezone:
                    raise ValueError("必须提供date_string和target_timezone参数")

                source_dt = self._parse_datetime(date_string, timezone)
                target_dt = source_dt.astimezone(pytz.timezone(target_timezone))

                return {
                    "status": "success",
                    "result": {
                        "source": source_dt.strftime(format),
                        "target": target_dt.strftime(format),
                        "source_tz": timezone,
                        "target_tz": target_timezone
                    },
                    "summary": f"时区转换: {source_dt.strftime(format)} → {target_dt.strftime(format)}"
                }

            elif operation == "date_diff":
                if not date_string:
                    raise ValueError("必须提供date_string参数")

                target_dt = self._parse_datetime(date_string, timezone)
                current_dt = datetime.datetime.now(pytz.timezone(timezone))
                delta = target_dt - current_dt

                return {
                    "status": "success",
                    "result": {
                        "days": delta.days,
                        "hours": delta.seconds // 3600,
                        "total_seconds": delta.total_seconds(),
                        "is_future": delta.days > 0
                    },
                    "summary": f"日期差: {abs(delta.days)}天 {delta.seconds//3600}小时"
                }

            elif operation == "add_time":
                base_dt = self._parse_datetime(date_string, timezone) if date_string \
                         else datetime.datetime.now(pytz.timezone(timezone))
                new_dt = base_dt + datetime.timedelta(days=days, hours=hours)

                return {
                    "status": "success",
                    "result": {
                        "original": base_dt.strftime(format),
                        "new": new_dt.strftime(format),
                        "delta": f"{days}天 {hours}小时"
                    },
                    "summary": f"时间计算: {base_dt.strftime(format)} + {days}天 {hours}小时 = {new_dt.strftime(format)}"
                }

            elif operation == "format_date":
                dt = self._parse_datetime(date_string, timezone) if date_string \
                    else datetime.datetime.now(pytz.timezone(timezone))
                formatted = dt.strftime(format)

                return {
                    "status": "success",
                    "result": {
                        "original": dt.isoformat(),
                        "formatted": formatted
                    },
                    "summary": f"格式化结果: {formatted}"
                }

            else:
                raise ValueError(f"未知操作类型: {operation}")

        except Exception as e:
            logger.error(f"操作失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "operation": operation
            }

    async def _arun(self, **kwargs):
        """异步执行"""
        return self._run(**kwargs)