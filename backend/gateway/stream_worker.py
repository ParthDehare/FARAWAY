import asyncio
import json
import os
import uuid
from aiokafka import AIOKafkaConsumer
from gateway.websocket.manager import broadcast_event

from shared.database.connection import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shared.models.agent_decision import AgentDecision
from shared.models.train import Train
from sqlalchemy.future import select

KAFKA_BROKER = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
TOPIC = "railnerv_telemetry"

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def start_consumer():
    print("Starting Kafka Stream Consumer...")
    consumer = None
    
    # Wait for Kafka to be ready
    for _ in range(10):
        try:
            consumer = AIOKafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                group_id="railnerv-web-broadcaster",
                auto_offset_reset="latest"
            )
            await consumer.start()
            print("Kafka Consumer connected!")
            break
        except Exception as e:
            print(f"Waiting for Kafka: {e}")
            await asyncio.sleep(2)
            
    if not consumer:
        print("Failed to start Kafka Consumer.")
        return

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode('utf-8'))
                event_type = data.get("event_type")
                payload = data.get("payload")
                
                if event_type and payload:
                    # Broadcast directly to connected clients
                    await broadcast_event(event_type, payload)
                    
                    # Update Database
                    try:
                        async with async_session() as db:
                            if event_type == "agent:decision":
                                decision = AgentDecision(
                                    id=uuid.uuid4(),
                                    agent_name=payload.get("agentId", "unknown"),
                                    action_taken=payload.get("action", "No action"),
                                    confidence=payload.get("confidence", 0.0),
                                    reasoning=f"Automated decision by {payload.get('agentId')} agent"
                                )
                                db.add(decision)
                                await db.commit()
                            elif event_type == "train:position":
                                train_id_str = payload.get("id")
                                if train_id_str:
                                    try:
                                        train_id = uuid.UUID(train_id_str)
                                        stmt = select(Train).filter_by(id=train_id)
                                        result = await db.execute(stmt)
                                        train = result.scalar_one_or_none()
                                        if train:
                                            train.latitude = payload.get("latitude", train.latitude)
                                            train.longitude = payload.get("longitude", train.longitude)
                                            train.speed_kmh = payload.get("speed_kmh", train.speed_kmh)
                                            train.passenger_count = payload.get("passenger_count", train.passenger_count)
                                            train.delay_minutes = payload.get("delay_minutes", train.delay_minutes)
                                            await db.commit()
                                    except ValueError:
                                        pass
                    except Exception as db_e:
                        print(f"DB Error: {db_e}")
            except json.JSONDecodeError:
                print(f"Failed to decode message: {msg.value}")
            except Exception as e:
                print(f"Error processing message: {e}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(start_consumer())
