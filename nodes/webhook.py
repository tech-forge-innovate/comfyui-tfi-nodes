import os
import json
import pika
import traceback
import time
from datetime import timedelta

class Webhook:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "job_id": ("STRING",),
                "output_url": ("STRING",),
                "execution_time": ("STRING",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "call_webhook"
    CATEGORY = "TFI"
    OUTPUT_NODE = True

    def call_webhook(self, job_id, output_url, execution_time, prompt=None, extra_pnginfo=None):
        """Publishes a webhook message to RabbitMQ using RABBITMQ_URL."""
        print(f"📡 Calling webhook for job {job_id}")

        message = {
            "job_id": job_id,
            "output_url": output_url,
            "execution_time": execution_time,
            "job_type": "face_swap"
        }
        
        try:
            rabbit_url = "amqps://kgbebiii:jxMzlszSTTM1Wvnn8bNmsP5P2a0dvMZh@puffin.rmq2.cloudamqp.com/kgbebiii"
            if not rabbit_url:
                raise ValueError("RABBITMQ_URL environment variable is not set.")

            QUEUE_NAME = "webhook-queue"
            params = pika.URLParameters(rabbit_url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            body = json.dumps(message)
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )

            print(f"✅ Sent to RabbitMQ [{QUEUE_NAME}]: {body}")
            connection.close()

        except Exception as e:
            print(f"❌ Error sending webhook to RabbitMQ: {e}")
            traceback.print_exc()

        # 👇 Always return an empty tuple to satisfy ComfyUI executor
        return ()
