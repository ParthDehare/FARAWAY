import asyncio
import json
from aiokafka import AIOKafkaConsumer
from gateway.websocket.manager import broadcast_event

import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
TOPIC = "railnerv_telemetry"

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
            except json.JSONDecodeError:
                print(f"Failed to decode message: {msg.value}")
            except Exception as e:
                print(f"Error processing message: {e}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(start_consumer())
