import random
import time
import pika
import json
import grpc
import water_quality_pb2


def create_rabbitmq_connection(max_retries=3, retry_delay=1):
    for attempt in range(max_retries):
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters('localhost', heartbeat=600))
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"RabbitMQ connection failed (attempt {attempt + 1}), retrying...")
            time.sleep(retry_delay)


def send_status(sensor_id):
    try:
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.exchange_declare(
            exchange='status_updates',
            exchange_type='fanout')

        message = {
            "sensor_id": sensor_id,
            "status": "alive",
            "timestamp": time.time()
        }

        channel.basic_publish(
            exchange='status_updates',
            routing_key='',
            body=json.dumps(message)
        )
        print(f"Published status update for {sensor_id}")
        connection.close()
    except Exception as e:
        print(f"Status update failed: {e}")


class Sensor:
    def __init__(self, sensor_id, station, count):
        self.sensor_id = f"{station.station_id}-{sensor_id}"
        self.station = station
        self.count = count

    def get_sensor_data(self):
        data = {
            "ph": random.uniform(6.0, 8.5),
            "turbidity": random.uniform(0, 10),
            "pollutants": random.uniform(0, 100)
        }

        if random.random() < 0.2:
            data["ph"] = random.choice([4.5, 9.5])
            data["turbidity"] = random.uniform(9, 15)
            data["pollutants"] = random.uniform(90, 120)

        return data

    def check_contaminants(self):
        try:
            send_status(self.sensor_id)
            data = self.get_sensor_data()
            print(f"Sensor {self.sensor_id} data: {data}")

            issues = []
            if data["pollutants"] > 90:
                issues.append("High Pollution detected")
            if data["ph"] < 6 or data["ph"] > 8:
                issues.append(f"pH imbalance ({data['ph']:.1f})")
            if data["turbidity"] > 9:
                issues.append(f"High Turbidity ({data['turbidity']:.1f})")

            for issue in issues:
                self.report_issue(issue, data)

        except Exception as e:
            print(f"Sensor {self.sensor_id} error: {e}")

    def report_issue(self, issue_type, sensor_data):
        try:
            request = water_quality_pb2.IssueReport(
                station_id=self.station.station_id,
                issue_type=issue_type,
                timestamp=time.time())

            response = self.station.stub.ReportIssue(request)
            print(f"gRPC report: {response.message}")

            connection = create_rabbitmq_connection()
            channel = connection.channel()
            channel.exchange_declare(
                exchange='water_quality_updates',
                exchange_type='fanout')

            message = {
                "type": "alert",
                "station_id": self.station.station_id,
                "message": issue_type,
                "metrics": sensor_data,
                "timestamp": time.time()
            }

            channel.basic_publish(
                exchange='water_quality_updates',
                routing_key='',
                body=json.dumps(message))
            print(f"Alert published to RabbitMQ")
            connection.close()

        except grpc.RpcError as e:
            print(f"gRPC error: {e.code().name}")
        except pika.exceptions.AMQPError as e:
            print(f"RabbitMQ error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    print("Starting sensor test...")


    class MockStation:
        def __init__(self):
            self.station_id = "TEST_STATION"
            self.stub = type('', (), {
                'ReportIssue': lambda *args: type('', (), {'message': 'OK'})()
            })()


    sensor = Sensor("TEST_SENSOR", MockStation(), count=0)

    for i in range(5):
        print(f"\nTest cycle {i + 1}")
        sensor.check_contaminants()
        time.sleep(2)