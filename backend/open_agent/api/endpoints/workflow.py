"""工作流管理API"""

from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
from datetime import datetime

from ...db.database import get_db
from ...schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowExecuteRequest, WorkflowExecutionResponse, NodeExecutionResponse, WorkflowStatus
)
from ...models.workflow import WorkflowStatus as ModelWorkflowStatus
from ...services.workflow_engine import get_workflow_engine
from ...services.auth import AuthService
from ...models.user import User
from ...utils.logger import get_logger

logger = get_logger("workflow_api")

router = APIRouter()

def convert_workflow_for_response(workflow_dict):
    """转换工作流数据以适配响应模型"""
    if workflow_dict.get('definition') and workflow_dict['definition'].get('connections'):
        for conn in workflow_dict['definition']['connections']:
            if 'from_node' in conn:
                conn['from'] = conn.pop('from_node')
            if 'to_node' in conn:
                conn['to'] = conn.pop('to_node')
    return workflow_dict

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """创建工作流"""
    try:
        from ...models.workflow import Workflow
        
        # 创建工作流
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            definition=workflow_data.definition.dict(),
            version="1.0.0",
            status=workflow_data.status,
            owner_id=current_user.id
        )
        workflow.set_audit_fields(current_user.id)
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        # 转换definition中的字段映射
        workflow_dict = convert_workflow_for_response(workflow.to_dict())
        
        logger.info(f"Created workflow: {workflow.name} by user {current_user.username}")
        return WorkflowResponse(**workflow_dict)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建工作流失败"
        )

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    skip: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=100),
    workflow_status: Optional[WorkflowStatus] = None,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """获取工作流列表"""
    try:
        from ...models.workflow import Workflow
        
        # 构建查询
        query = db.query(Workflow).filter(Workflow.owner_id == current_user.id)
        
        if workflow_status:
            query = query.filter(Workflow.status == workflow_status)
        
        # 添加搜索功能
        if search:
            query = query.filter(Workflow.name.ilike(f"%{search}%"))
        
        # 获取总数
        total = query.count()
        
        # 如果没有传分页参数，返回所有数据
        if skip is None and limit is None:
            workflows = query.all()
            return WorkflowListResponse(
                workflows=[WorkflowResponse(**convert_workflow_for_response(w.to_dict())) for w in workflows],
                total=total,
                page=1,
                size=total
            )
        
        # 使用默认分页参数
        if skip is None:
            skip = 0
        if limit is None:
            limit = 10
            
        # 分页查询
        workflows = query.offset(skip).limit(limit).all()
        
        return WorkflowListResponse(
            workflows=[WorkflowResponse(**convert_workflow_for_response(w.to_dict())) for w in workflows],
            total=total,
            page=skip // limit + 1,  # 计算页码
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工作流列表失败"
        )

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """获取工作流详情"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        return WorkflowResponse(**convert_workflow_for_response(workflow.to_dict()))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工作流失败"
        )

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """更新工作流"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 更新字段
        update_data = workflow_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "definition" and value:
                # 如果value是Pydantic模型，转换为字典；如果已经是字典，直接使用
                if hasattr(value, 'dict'):
                    setattr(workflow, field, value.dict())
                else:
                    setattr(workflow, field, value)
            else:
                setattr(workflow, field, value)
        
        workflow.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(workflow)
        
        logger.info(f"Updated workflow: {workflow.name} by user {current_user.username}")
        return WorkflowResponse(**convert_workflow_for_response(workflow.to_dict()))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新工作流失败"
        )

@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """删除工作流"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        db.delete(workflow)
        db.commit()
        
        logger.info(f"Deleted workflow: {workflow.name} by user {current_user.username}")
        return {"message": "工作流删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除工作流失败"
        )

@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """激活工作流"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        workflow.status = ModelWorkflowStatus.PUBLISHED
        workflow.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        
        logger.info(f"Activated workflow: {workflow.name} by user {current_user.username}")
        return {"message": "工作流激活成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活工作流失败"
        )

@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """停用工作流"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        workflow.status = ModelWorkflowStatus.ARCHIVED
        workflow.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        
        logger.info(f"Deactivated workflow: {workflow.name} by user {current_user.username}")
        return {"message": "工作流停用成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用工作流失败"
        )

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """执行工作流"""
    try:
        from ...models.workflow import Workflow
        
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        if workflow.status != ModelWorkflowStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="工作流未激活，无法执行"
            )
        
        # 获取工作流引擎并执行
        engine = get_workflow_engine()
        execution_result = await engine.execute_workflow(
            workflow=workflow,
            input_data=request.input_data,
            user_id=current_user.id,
            db=db
        )
        
        logger.info(f"Executed workflow: {workflow.name} by user {current_user.username}")
        return execution_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工作流失败: {str(e)}"
        )

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """获取工作流执行历史"""
    try:
        from ...models.workflow import Workflow, WorkflowExecution
        
        # 验证工作流所有权
        workflow = db.query(Workflow).filter(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 获取执行历史
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(WorkflowExecution.created_at.desc()).offset(skip).limit(limit).all()
        
        return [WorkflowExecutionResponse.from_orm(execution) for execution in executions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workflow executions {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取执行历史失败"
        )

@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """获取工作流执行详情"""
    try:
        from ...models.workflow import WorkflowExecution, Workflow
        
        execution = db.query(WorkflowExecution).join(
            Workflow, WorkflowExecution.workflow_id == Workflow.id
        ).filter(
            and_(
                WorkflowExecution.id == execution_id,
                Workflow.owner_id == current_user.id
            )
        ).first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        return WorkflowExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow execution {execution_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取执行详情失败"
        )


@router.post("/{workflow_id}/execute-stream")
async def execute_workflow_stream(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """流式执行工作流，实时推送节点执行状态"""
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        workflow_engine = None
        
        try:
            from ...models.workflow import Workflow
            
            # 验证工作流
            workflow = db.query(Workflow).filter(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.owner_id == current_user.id
                )
            ).first()
            
            if not workflow:
                yield f"data: {json.dumps({'type': 'error', 'message': '工作流不存在'}, ensure_ascii=False)}\n\n"
                return
            
            if workflow.status != ModelWorkflowStatus.PUBLISHED:
                yield f"data: {json.dumps({'type': 'error', 'message': '工作流未激活，无法执行'}, ensure_ascii=False)}\n\n"
                return
            
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'workflow_start', 'workflow_id': workflow_id, 'workflow_name': workflow.name, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 获取工作流引擎
            workflow_engine = get_workflow_engine()
            
            # 执行工作流（流式版本）
            async for step_data in workflow_engine.execute_workflow_stream(
                workflow=workflow,
                input_data=request.input_data,
                user_id=current_user.id,
                db=db
            ):
                # 推送工作流步骤
                yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'workflow_complete', 'message': '工作流执行完成', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式工作流执行异常: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'工作流执行失败: {str(e)}'}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )