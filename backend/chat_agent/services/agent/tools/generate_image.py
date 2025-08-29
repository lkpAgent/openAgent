"""Tool for generate image."""

import requests
from typing import Dict, Any, List

from sqlalchemy import desc
from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....utils.logger import get_logger

logger = get_logger("generate_image_tool")


class GenerateImageTool(BaseTool):

    """Tool for generate image with description."""

    
    def get_name(self) -> str:
        return "generate_image"

    
    def get_description(self) -> str:
        return "generate image with description, and return image url"

    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="description",

                type=ToolParameterType.STRING,
                description="description of image",

                required=True
            )]

    async def execute(self, **kwargs) -> ToolResult:
        try:
            # 使用基类的参数验证
            validated_params = self.validate_parameters(**kwargs)
            description = validated_params.get("description")
            
            if not description:
                return ToolResult(
                    success=False,
                    result=None,
                    error="请输入图片描述"
                )
            
            logger.info(f"生成图片: {description}")
            
            # 这里可以集成真实的图片生成API，比如DALL-E、Midjourney等
            # 目前返回一个示例图片URL
            image_url = "https://oss.huangye88.net/live/ueditor/php/upload/2639469/image/20200726/1595750286299915.jpg"
            
            return ToolResult(
                success=True,
                result={
                    "image_url": image_url,
                    "description": description,
                    "message": f"已根据描述'{description}'生成图片"
                },
                metadata={
                    "tool": "generate_image",
                    "description": description
                }
            )
            
        except Exception as e:
            logger.error(f"generate image error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"生成图片失败: {str(e)}"
            )


         