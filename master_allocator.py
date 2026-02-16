import logging
from typing import Dict, List, Optional
import pika
from knowledge_base import KnowledgeBaseAgent
from worker_node_connector import WorkerNodeConnector
from resource_sensor import ResourceSensor
from config import ALLOCATION_QUEUE_NAME, RESOURCE_SENSOR_EXCHANGE

class MasterAllocator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connector = WorkerNodeConnector()
        self.sensor = ResourceSensor()
        self.knowledge_base = KnowledgeBaseAgent()
        
        # Initialize RabbitMQ connection
        self._setup_rabbitmq()

    def _setup_rabbitmq(self) -> None:
        """Initialize RabbitMQ connection and setup necessary exchanges."""
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare exchange for resource sensor data
        self.channel.exchange_declare(exchange=RESOURCE_SENSOR_EXCHANGE, exchange_type='fanout')

        # Setup queue for allocation requests and responses
        self.channel.queue_declare(ALLOCATION_QUEUE_NAME)
        self._setup_allocations_listener()

    def _setup_allocations_listener(self) -> None:
        """Set up listener for resource allocation requests."""
        def callback(ch, method, properties, body):
            allocation_request = body.decode()
            self.logger.info(f"Received allocation request: {allocation_request}")
            self.allocate_resources(allocation_request)

        self.channel.basic_consume(
            queue=ALLOCATION_QUEUE_NAME,
            on_message_callback=callback,
            auto_ack=True
        )

    def allocate_resources(self, request: str) -> None:
        """Allocate resources based on the received request."""
        try:
            resource_demands = self._parse_request(request)
            available_resources = self.sensor.get_resource_usage()
            
            # Perform allocation logic
            allocations = self._greedy_allocation(resource_demands, available_resources)
            self.connector.distribute_allocations(allocations)

            self.logger.info("Resource allocation completed successfully.")
        except Exception as e:
            self.logger.error(f"Allocation failed: {str(e)}")
            self._handle_failure()

    def _parse_request(self, request: str) -> Dict[str, float]:
        """Parse resource request from the worker node."""
        # Simulated parsing logic
        return {'cpu': 2.0, 'memory': 4.0}

    def _greedy_allocation(self, demands: Dict[str, float], resources: Dict[str, float]) -> Dict[str, Dict]:
        """Allocate resources using a greedy algorithm."""
        allocation_plan = {}
        
        # Sort resources by availability
        sorted_resources = sorted(resources.items(), key=lambda x: x[1], reverse=True)
        for resource_type, available in sorted_resources:
            required = demands.get(resource_type, 0.0)
            if available >= required:
                allocation_plan[resource_type] = {'allocated': required}
            else:
                # Handle cases where resources are insufficient
                raise ResourceInsufficientError(f"{resource_type} resources are insufficient.")
        
        return allocation_plan

    def _handle_failure(self) -> None:
        """Handle resource allocation failures."""
        self.sensor.trigger_alarm()
        self.knowledge_base.log_incident("Resource allocation failure")

    def start_listening(self) -> None:
        """Start the resource allocation service."""
        self.logger.info("Starting resource allocation service...")
        self.channel.start_consuming()

if __name__ == "__main__":
    allocator = MasterAllocator()
    try:
        allocator.start_listening()
    except KeyboardInterrupt:
        allocator.connection.close()