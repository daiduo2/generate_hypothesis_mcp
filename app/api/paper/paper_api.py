from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from starlette import status

from app.api.common import BaseAPI
from app.core.celery import celery_app
from main import main
from app.task.paper_assistant import paper_assistant

router = APIRouter()


class RAGAPI(BaseAPI):
    """
    RAG API类，提供文档处理和查询接口
    """

    @staticmethod
    @router.post("/generate_paper",
                 summary="生成论文",
                 description="生成论文"
                 )
    async def generate_paper(Keyword: str, user_id: str = "api_user"):
        """
        生成论文

        Args:
            Keyword : 关键词
            user_id : 用户ID，默认为api_user

        Returns:
            创建结果响应
        """
        try:
            task = paper_assistant.delay(user_id=user_id, keyword=Keyword, search_paper_num=2)
            return BaseAPI.success(data={"task_id": task.id})
        except ValueError as e:
            return BaseAPI.error(code=status.HTTP_400_BAD_REQUEST,
                                 message=str(e),
                                 status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return BaseAPI.error(code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 message=f"内部服务器错误: {str(e)}",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @router.post("/get_status",
                 summary="获取结果",
                 description="获取结果"
                 )
    async def get_task_status(task_id: str):
        """
        获取结果

        Args:
            task_id : 任务id

        Returns:
            创建结果响应
        """
        try:
            task_result = AsyncResult(task_id, app=celery_app)
            
            # 构建状态响应
            status_info = {
                "task_id": task_id,
                "status": task_result.status,
                "ready": task_result.ready(),
                "successful": task_result.successful() if task_result.ready() else None,
                "failed": task_result.failed() if task_result.ready() else None,
                "result": task_result.result if task_result.ready() and task_result.successful() else None,
                "error": str(task_result.result) if task_result.ready() and task_result.failed() else None
            }
            
            return BaseAPI.success(data={"task_result": status_info})
        except ValueError as e:
            return BaseAPI.error(code=status.HTTP_400_BAD_REQUEST,
                                 message=str(e),
                                 status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return BaseAPI.error(code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 message=f"内部服务器错误: {str(e)}",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)