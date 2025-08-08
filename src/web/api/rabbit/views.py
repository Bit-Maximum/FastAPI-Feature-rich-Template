from typing import Annotated

from aio_pika import Channel, Message
from aio_pika.pool import Pool
from fastapi import APIRouter, Depends

from src.services.rabbit.dependencies import get_rmq_channel_pool
from src.web.api.rabbit.schema import RMQMessageDTO

router = APIRouter()

CommonDeps = Annotated[Pool[Channel], Depends(get_rmq_channel_pool)]


@router.post("/")
async def send_rabbit_message(
    message: RMQMessageDTO,
    pool: CommonDeps,
) -> None:
    """
    Posts a message in a rabbitMQ's exchange.

    :param message: message to publish to rabbitmq.
    :param pool: rabbitmq channel pool
    """
    async with pool.acquire() as conn:
        exchange = await conn.declare_exchange(
            name=message.exchange_name,
            auto_delete=True,
        )
        await exchange.publish(
            message=Message(
                body=message.message.encode("utf-8"),
                content_encoding="utf-8",
                content_type="text/plain",
            ),
            routing_key=message.routing_key,
        )
