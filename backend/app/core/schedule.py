from sqlmodel import Session

from app.core import engine


async def update_expired_orders():
    """定时任务：更新过期订单 — 自管理session生命周期"""
    with Session(engine) as session:
        pass  # 订单逻辑待实现
