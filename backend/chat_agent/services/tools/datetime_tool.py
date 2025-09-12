"""DateTime tool for date and time operations."""

import datetime
import pytz
from typing import List, Optional

from chat_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from chat_agent.utils.logger import get_logger

logger = get_logger("datetime_tool")


class DateTimeTool(BaseTool):
    """Tool for date and time operations."""
    
    def get_name(self) -> str:
        return "datetime"
        
    def get_description(self) -> str:
        return "Get current date and time, convert between timezones, or perform date calculations."
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="Operation to perform",
                required=True,
                enum=["current_time", "timezone_convert", "date_diff", "add_time", "format_date"]
            ),
            ToolParameter(
                name="timezone",
                type=ToolParameterType.STRING,
                description="Timezone (e.g., 'UTC', 'Asia/Shanghai', 'America/New_York')",
                required=False,
                default="UTC"
            ),
            ToolParameter(
                name="date_string",
                type=ToolParameterType.STRING,
                description="Date string for operations (ISO format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
                required=False
            ),
            ToolParameter(
                name="target_timezone",
                type=ToolParameterType.STRING,
                description="Target timezone for conversion",
                required=False
            ),
            ToolParameter(
                name="days",
                type=ToolParameterType.INTEGER,
                description="Number of days to add/subtract",
                required=False,
                default=0
            ),
            ToolParameter(
                name="hours",
                type=ToolParameterType.INTEGER,
                description="Number of hours to add/subtract",
                required=False,
                default=0
            ),
            ToolParameter(
                name="format",
                type=ToolParameterType.STRING,
                description="Date format string (e.g., '%Y-%m-%d %H:%M:%S', '%B %d, %Y')",
                required=False,
                default="%Y-%m-%d %H:%M:%S"
            )
        ]
        
    def _parse_datetime(self, date_string: str, timezone_str: str = "UTC") -> datetime.datetime:
        """Parse datetime string."""
        tz = pytz.timezone(timezone_str)
        
        # Try different formats
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
                
        raise ValueError(f"Unable to parse date string: {date_string}")
        
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute the datetime tool."""
        try:
            logger.info(f"Performing datetime operation: {operation}")
            
            if operation == "current_time":
                timezone_str = kwargs.get("timezone", "UTC")
                tz = pytz.timezone(timezone_str)
                now = datetime.datetime.now(tz)
                
                result = {
                    "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "timezone": timezone_str,
                    "iso_format": now.isoformat(),
                    "timestamp": now.timestamp()
                }
                
                summary = f"Current time in {timezone_str}: {result['current_time']}"
                
            elif operation == "timezone_convert":
                date_string = kwargs.get("date_string")
                source_tz = kwargs.get("timezone", "UTC")
                target_tz = kwargs.get("target_timezone")
                
                if not date_string or not target_tz:
                    raise ValueError("date_string and target_timezone are required for timezone conversion")
                    
                # Parse source datetime
                source_dt = self._parse_datetime(date_string, source_tz)
                
                # Convert to target timezone
                target_timezone = pytz.timezone(target_tz)
                target_dt = source_dt.astimezone(target_timezone)
                
                result = {
                    "source_time": source_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "target_time": target_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "source_timezone": source_tz,
                    "target_timezone": target_tz
                }
                
                summary = f"Converted {result['source_time']} to {result['target_time']}"
                
            elif operation == "date_diff":
                date_string = kwargs.get("date_string")
                timezone_str = kwargs.get("timezone", "UTC")
                
                if not date_string:
                    raise ValueError("date_string is required for date difference calculation")
                    
                # Parse target date
                target_dt = self._parse_datetime(date_string, timezone_str)
                
                # Get current time in same timezone
                tz = pytz.timezone(timezone_str)
                now = datetime.datetime.now(tz)
                
                # Calculate difference
                diff = target_dt - now
                days = diff.days
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                result = {
                    "target_date": target_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "current_date": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "difference_days": days,
                    "difference_hours": hours,
                    "difference_minutes": minutes,
                    "total_seconds": diff.total_seconds()
                }
                
                if days > 0:
                    summary = f"The date {target_dt.strftime('%Y-%m-%d')} is {days} days, {hours} hours, and {minutes} minutes in the future"
                elif days < 0:
                    summary = f"The date {target_dt.strftime('%Y-%m-%d')} was {abs(days)} days, {hours} hours, and {minutes} minutes ago"
                else:
                    summary = f"The date is today, {hours} hours and {minutes} minutes from now"
                    
            elif operation == "add_time":
                date_string = kwargs.get("date_string")
                timezone_str = kwargs.get("timezone", "UTC")
                days = kwargs.get("days", 0)
                hours = kwargs.get("hours", 0)
                
                if date_string:
                    base_dt = self._parse_datetime(date_string, timezone_str)
                else:
                    tz = pytz.timezone(timezone_str)
                    base_dt = datetime.datetime.now(tz)
                    
                # Add time
                new_dt = base_dt + datetime.timedelta(days=days, hours=hours)
                
                result = {
                    "original_date": base_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "new_date": new_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "days_added": days,
                    "hours_added": hours
                }
                
                summary = f"Added {days} days and {hours} hours to {base_dt.strftime('%Y-%m-%d %H:%M:%S')}, result: {new_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                
            elif operation == "format_date":
                date_string = kwargs.get("date_string")
                timezone_str = kwargs.get("timezone", "UTC")
                format_str = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
                
                if date_string:
                    dt = self._parse_datetime(date_string, timezone_str)
                else:
                    tz = pytz.timezone(timezone_str)
                    dt = datetime.datetime.now(tz)
                    
                formatted = dt.strftime(format_str)
                
                result = {
                    "original_date": dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "formatted_date": formatted,
                    "format_used": format_str
                }
                
                summary = f"Formatted date: {formatted}"
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
            logger.info(f"DateTime operation '{operation}' completed successfully")
            
            return ToolResult(
                success=True,
                result={
                    "summary": summary,
                    "details": result
                },
                metadata={
                    "operation": operation,
                    "timezone": kwargs.get("timezone", "UTC")
                }
            )
            
        except Exception as e:
            logger.error(f"DateTime tool error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"DateTime operation failed: {str(e)}"
            )