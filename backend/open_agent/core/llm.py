"""LLM工厂类，用于创建和管理LLM实例"""

from typing import Optional
from langchain_openai import ChatOpenAI
from .config import get_settings

_global_llm:Optional[ChatOpenAI] = None
_global_streaming_llm:Optional[ChatOpenAI] = None

def create_llm(model: Optional[str] = None, temperature: Optional[float] = None, streaming: bool = False) -> ChatOpenAI:
    """创建LLM实例
    
    Args:
        model: 可选，指定使用的模型名称。如果不指定，将使用配置文件中的默认模型
        temperature: 可选，模型温度参数
        streaming: 是否启用流式响应，默认False
        
    Returns:
        ChatOpenAI实例
    """

    global _global_llm, _global_streaming_llm
    if streaming:
        if  _global_streaming_llm is None:
            _global_streaming_llm = create_new_llm(model,temperature,streaming)
        return _global_streaming_llm
    else:
        if _global_llm is None:
            _global_llm = create_new_llm(model,temperature,streaming)
        return _global_llm

def create_new_llm(model: Optional[str] = None, temperature: Optional[float] = None, streaming: bool = False) -> ChatOpenAI:
    settings = get_settings()
    llm_config = settings.llm.get_current_config()
    if model:
        # 根据指定的模型获取对应配置
        if model.startswith('deepseek'):
            llm_config['model'] = settings.llm.deepseek_model
            llm_config['api_key'] = settings.llm.deepseek_api_key
            llm_config['base_url'] = settings.llm.deepseek_base_url
        elif model.startswith('doubao'):
            llm_config['model'] = settings.llm.doubao_model
            llm_config['api_key'] = settings.llm.doubao_api_key
            llm_config['base_url'] = settings.llm.doubao_base_url
        elif model.startswith('glm'):
            llm_config['model'] = settings.llm.zhipu_model
            llm_config['api_key'] = settings.llm.zhipu_api_key
            llm_config['base_url'] = settings.llm.zhipu_base_url
        elif model.startswith('moonshot'):
            llm_config['model'] = settings.llm.moonshot_model
            llm_config['api_key'] = settings.llm.moonshot_api_key
            llm_config['base_url'] = settings.llm.moonshot_base_url
    return ChatOpenAI(
        model=llm_config['model'],
        api_key=llm_config['api_key'],
        base_url=llm_config['base_url'],
        temperature=temperature if temperature is not None else llm_config['temperature'],
        max_tokens=llm_config['max_tokens'],
        streaming=streaming
    )