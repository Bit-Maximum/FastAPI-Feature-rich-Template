from typing import Annotated

from aiokafka import AIOKafkaProducer
from fastapi import Request
from taskiq import TaskiqDepends
from taskiq_dependencies import Depends


def get_kafka_producer(
    request: Annotated[Request, Depends(TaskiqDepends)],
) -> AIOKafkaProducer:  # pragma: no cover
    """
    Returns kafka producer.

    :param request: current request.
    :return: kafka producer from the state.
    """
    return request.app.state.kafka_producer
