from typing import Annotated

from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends

from src.services.kafka.dependencies import get_kafka_producer
from src.web.api.kafka.schema import KafkaMessage

router = APIRouter()

CommonDeps = Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]


@router.post("/")
async def send_kafka_message(
    kafka_message: KafkaMessage,
    producer: CommonDeps,
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
