import click
import json
import time

import boto3

from .main import process


@click.command()
@click.option("-i", "--input-queue-url")
@click.option("-o", "--output-queue-url")
@click.option("-b", "--bucket")
def main(input_queue_url, output_queue_url, bucket):
    client_sqs = boto3.client("sqs")

    while True:
        response = client_sqs.receive_message(
            QueueUrl=input_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10,
        )

        for message in response["Messages"]:
            message_body = json.loads(message["Body"])
            click.echo(message_body)

            client_sqs.delete_message(
                QueueUrl=input_queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )

        time.sleep(1)
