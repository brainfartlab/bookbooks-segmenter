from dataclasses import dataclass

import click
import json
import time

import boto3

from .main import process


@dataclass
class Config:
    input_queue_url: str
    output_queue_url: str
    image_bucket: str

    @staticmethod
    def from_parameter(parameter_name, client=boto3.client("ssm")):
        response = client.get_parameter(Name=parameter_name)
        data = json.loads(response["Parameter"]["Value"])

        return Config(
            input_queue_url=data["RAW_QUEUE_URL"],
            output_queue_url=data["SEGMENTS_QUEUE_URL"],
            image_bucket=data["IMAGE_BUCKET"],
        )


@click.command()
@click.option("-c", "--config", required=True)
@click.option("-r", "--region", required=True)
#@click.option("-o", "--output-queue-url", required=True)
#@click.option("-b", "--bucket", required=True)
def main(config, region):
    client_ssm = boto3.client("ssm", region_name=region)
    client_sqs = boto3.client("sqs", region_name=region)

    click.echo("Retrieving config")
    config = Config.from_parameter(config, client_ssm)

    while True:
        response = client_sqs.receive_message(
            QueueUrl=config.input_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10,
        )

        for message in response["Messages"]:
            message_body = json.loads(message["Body"])
            click.echo(message_body)

            #client_sqs.delete_message(
            #    QueueUrl=config.input_queue_url,
            #    ReceiptHandle=message["ReceiptHandle"],
            #)

        time.sleep(10)
