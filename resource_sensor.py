import logging
from typing import Dict, Optional

class ResourceSensor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_rabbitmq()

    def _setup_rabbitmq(self) -> None:
        """Initialize RabbitMQ connection for resource sensing."""
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        
        # Declare exchange
        self.channel.exchange_declare(exchange='resource_sensor_exchange', exchange_type='fanout')

    def get_resource_usage(self) -> Dict[str, float]:
        """Retrieve current resource usage metrics."""
        try:
            # Simulated data retrieval
            return {
                'cpu': 4.5,
                'memory': 8.2,
                'storage': 100.5
            }
        except Exception as e:
            self.logger.error(f"Failed to retrieve resource usage: {str(e)}")
            return {}

    def trigger_alarm(self) -> None:
        """Send an alarm signal when resources are critically low."""
        # Implementation for triggering alarms via RabbitMQ
        pass

if __name__ == "__main__":
    sensor = ResourceSensor()
    try:
        while True:
            usage = sensor.get_resource_usage()
            if not usage:
                break  # Simplified for loop control
    except KeyboardInterrupt:
        sensor.connection.close()