"""LLM configuration management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ...db.database import get_db
from ...models.user import User
from ...models.llm_config import LLMConfig
from ...core.simple_permissions import require_super_admin, require_authenticated_user
from ...services.auth import AuthService
from ...utils.logger import get_logger
from ...schemas.llm_config import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse,
    LLMConfigTest
)
from open_agent.services.document_processor import get_document_processor
logger = get_logger(__name__)
router = APIRouter(prefix="/llm-configs", tags=["llm-configs"])


@router.get("/", response_model=List[LLMConfigResponse])
async def get_llm_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_embedding: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """获取大模型配置列表."""
    try:
        query = db.query(LLMConfig)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    LLMConfig.name.ilike(f"%{search}%"),
                    LLMConfig.model_name.ilike(f"%{search}%"),
                    LLMConfig.description.ilike(f"%{search}%")
                )
            )
        
        # 服务商筛选
        if provider:
            query = query.filter(LLMConfig.provider == provider)
        
        # 状态筛选
        if is_active is not None:
            query = query.filter(LLMConfig.is_active == is_active)
        
        # 模型类型筛选
        if is_embedding is not None:
            query = query.filter(LLMConfig.is_embedding == is_embedding)
        
        # 排序
        query = query.order_by(LLMConfig.name)
        
        # 分页
        configs = query.offset(skip).limit(limit).all()
        
        return [config.to_dict(include_sensitive=True) for config in configs]
        
    except Exception as e:
        logger.error(f"Error getting LLM configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取大模型配置列表失败"
        )


@router.get("/providers")
async def get_llm_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """获取支持的大模型服务商列表."""
    try:
        providers = db.query(LLMConfig.provider).distinct().all()
        return [provider[0] for provider in providers if provider[0]]
        
    except Exception as e:
        logger.error(f"Error getting LLM providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取服务商列表失败"
        )


@router.get("/active", response_model=List[LLMConfigResponse])
async def get_active_llm_configs(
    is_embedding: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """获取所有激活的大模型配置."""
    try:
        query = db.query(LLMConfig).filter(LLMConfig.is_active == True)
        
        if is_embedding is not None:
            query = query.filter(LLMConfig.is_embedding == is_embedding)
        
        configs = query.order_by(LLMConfig.created_at).all()
        
        return [config.to_dict(include_sensitive=True) for config in configs]
        
    except Exception as e:
        logger.error(f"Error getting active LLM configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取激活配置列表失败"
        )


@router.get("/default", response_model=LLMConfigResponse)
async def get_default_llm_config(
    is_embedding: bool = Query(False, description="是否获取嵌入模型默认配置"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """获取默认大模型配置."""
    try:
        config = db.query(LLMConfig).filter(
            LLMConfig.is_default == True,
            LLMConfig.is_embedding == is_embedding,
            LLMConfig.is_active == True
        ).first()
        
        if not config:
            model_type = "嵌入模型" if is_embedding else "对话模型"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到默认{model_type}配置"
            )
        
        return config.to_dict(include_sensitive=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default LLM config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取默认配置失败"
        )


@router.get("/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """获取大模型配置详情."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        return config.to_dict(include_sensitive=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LLM config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取大模型配置详情失败"
        )


@router.post("/", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    config_data: LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """创建大模型配置."""
    try:
        # 检查配置名称是否已存在
        existing_config = db.query(LLMConfig).filter(
            LLMConfig.name == config_data.name
        ).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="配置名称已存在"
            )
        
        # 创建临时配置对象进行验证
        temp_config = LLMConfig(
            name=config_data.name,
            provider=config_data.provider,
            model_name=config_data.model_name,
            api_key=config_data.api_key,
            base_url=config_data.base_url,
            max_tokens=config_data.max_tokens,
            temperature=config_data.temperature,
            top_p=config_data.top_p,
            frequency_penalty=config_data.frequency_penalty,
            presence_penalty=config_data.presence_penalty,
            description=config_data.description,
            is_active=config_data.is_active,
            is_default=config_data.is_default,
            is_embedding=config_data.is_embedding,
            extra_config=config_data.extra_config or {}
        )
        
        # 验证配置
        validation_result = temp_config.validate_config()
        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result['error']
            )
        
        # 如果设为默认，取消同类型的其他默认配置
        if config_data.is_default:
            db.query(LLMConfig).filter(
                LLMConfig.is_embedding == config_data.is_embedding
            ).update({"is_default": False})
        
        # 创建配置
        config = LLMConfig(
            name=config_data.name,
            provider=config_data.provider,
            model_name=config_data.model_name,
            api_key=config_data.api_key,
            base_url=config_data.base_url,
            max_tokens=config_data.max_tokens,
            temperature=config_data.temperature,
            top_p=config_data.top_p,
            frequency_penalty=config_data.frequency_penalty,
            presence_penalty=config_data.presence_penalty,
            description=config_data.description,
            is_active=config_data.is_active,
            is_default=config_data.is_default,
            is_embedding=config_data.is_embedding,
            extra_config=config_data.extra_config or {}
        )
        config.set_audit_fields(current_user.id)
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        logger.info(f"LLM config created: {config.name} by user {current_user.username}")
        return config.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating LLM config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建大模型配置失败"
        )


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: int,
    config_data: LLMConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """更新大模型配置."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        # 检查配置名称是否已存在（排除自己）
        if config_data.name and config_data.name != config.name:
            existing_config = db.query(LLMConfig).filter(
                LLMConfig.name == config_data.name,
                LLMConfig.id != config_id
            ).first()
            if existing_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="配置名称已存在"
                )
        
        # 如果设为默认，取消同类型的其他默认配置
        if config_data.is_default is True:
            # 获取当前配置的embedding类型，如果更新中包含is_embedding则使用新值
            is_embedding = config_data.is_embedding if config_data.is_embedding is not None else config.is_embedding
            db.query(LLMConfig).filter(
                LLMConfig.is_embedding == is_embedding,
                LLMConfig.id != config_id
            ).update({"is_default": False})
        
        # 更新字段
        update_data = config_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        config.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"LLM config updated: {config.name} by user {current_user.username}")
        return config.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating LLM config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新大模型配置失败"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """删除大模型配置."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        # TODO: 检查是否有对话或其他功能正在使用该配置
        # 这里可以添加相关的检查逻辑
        
        db.delete(config)
        db.commit()
        
        logger.info(f"LLM config deleted: {config.name} by user {current_user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting LLM config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除大模型配置失败"
        )


@router.post("/{config_id}/test")
async def test_llm_config(
    config_id: int,
    test_data: LLMConfigTest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """测试大模型配置."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        # 验证配置
        validation_result = config.validate_config()
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": f"配置验证失败: {validation_result['error']}",
                "details": validation_result
            }
        
        # 尝试创建客户端并发送测试请求
        try:
            # 这里应该根据不同的服务商创建相应的客户端
            # 由于具体的客户端实现可能因服务商而异，这里提供一个通用的框架
            
            test_message = test_data.message or "Hello, this is a test message."
            
            # TODO: 实现具体的测试逻辑
            # 例如：
            # client = config.get_client()
            # response = client.chat.completions.create(
            #     model=config.model_name,
            #     messages=[{"role": "user", "content": test_message}],
            #     max_tokens=100
            # )
            
            # 模拟测试成功
            logger.info(f"LLM config test: {config.name} by user {current_user.username}")
            
            return {
                "success": True,
                "message": "配置测试成功",
                "test_message": test_message,
                "response": "这是一个模拟的测试响应。实际实现中，这里会是大模型的真实响应。",
                "latency_ms": 150,  # 模拟延迟
                "config_info": config.get_client_config()
            }
            
        except Exception as test_error:
            logger.error(f"LLM config test failed: {config.name}, error: {str(test_error)}")
            return {
                "success": False,
                "message": f"配置测试失败: {str(test_error)}",
                "test_message": test_message,
                "config_info": config.get_client_config()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing LLM config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试大模型配置失败"
        )


@router.post("/{config_id}/toggle-status")
async def toggle_llm_config_status(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """切换大模型配置状态."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        # 切换状态
        config.is_active = not config.is_active
        config.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(config)
        
        status_text = "激活" if config.is_active else "禁用"
        logger.info(f"LLM config status toggled: {config.name} {status_text} by user {current_user.username}")
        
        return {
            "message": f"配置已{status_text}",
            "is_active": config.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling LLM config status {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换配置状态失败"
        )


@router.post("/{config_id}/set-default")
async def set_default_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """设置默认大模型配置."""
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="大模型配置不存在"
            )
        
        # 检查配置是否激活
        if not config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能将激活的配置设为默认"
            )
        
        # 取消同类型的其他默认配置
        db.query(LLMConfig).filter(
            LLMConfig.is_embedding == config.is_embedding,
            LLMConfig.id != config_id
        ).update({"is_default": False})
        
        # 设置当前配置为默认
        config.is_default = True
        config.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(config)
        
        model_type = "嵌入模型" if config.is_embedding else "对话模型"
        logger.info(f"Default LLM config set: {config.name} ({model_type}) by user {current_user.username}")
        # 更新文档处理器默认embedding
        get_document_processor()._init_embeddings()
        return {
            "message": f"已将 {config.name} 设为默认{model_type}配置",
            "is_default": config.is_default
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting default LLM config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置默认配置失败"
        )