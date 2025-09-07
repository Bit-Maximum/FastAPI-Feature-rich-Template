from typing import Annotated

from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends

from app.adapters.kafka.dependencies import get_kafka_producer
from app.controller.api.v1.kafka.schema import KafkaMessage

router = APIRouter()


@router.post("/")
async def send_kafka_message(
    kafka_message: KafkaMessage,
    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
) -> None:
    """
    Sends message to kafka.

    :param producer: kafka's producer.
    :param kafka_message: message to publish.
    """
    await producer.send(
        topic=kafka_message.topic,
        value=kafka_message.message.encode(),
    )
