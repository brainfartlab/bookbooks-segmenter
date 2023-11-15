from dataclasses import dataclass
import logging
import io

import click
import click_logging
import json
from PIL import Image
import time

import boto3

from .main import process
from .utilities.data_classes import SQSEvent, S3Record


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


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


def load_image(record: S3Record, client=boto3.client("s3")):
    response = client.get_object(
        Bucket=record.s3.bucket.name,
        Key=record.s3.object.key,
    )

    return Image.open(response["Body"]).convert("RGB")


def write_image(image: Image.Image, bucket: str, key: str, client=boto3.client("s3")):
    data = io.BytesIO()
    image.save(data, format="PNG")

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data.getvalue(),
    )


@click.command()
@click.option("-c", "--config", required=True)
@click_logging.simple_verbosity_option(logger)
def main(config):
    client_s3 = boto3.client("s3")
    client_ssm = boto3.client("ssm")
    client_sqs = boto3.client("sqs")

    logger.info("loading config from %s", config)
    config = Config.from_parameter(config, client=client_ssm)

    while True:
        response = client_sqs.receive_message(
            QueueUrl=config.input_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10,
        )

        for message in response["Messages"]:
            message_body = json.loads(message["Body"])
            event = SQSEvent(**message_body)

            for record in event.records:
                logger.info("retrieving segments from %s", record.location)
                image = load_image(record)

                segments = process(image, "book spine")

                for i, segment in enumerate(segments):
                    logger.info("writing segment %d", i)
                    write_image(
                        segment,
                        record.s3.bucket.name,
                        f"segments/{i}.png",
                        client_s3
                    )

            #client_sqs.delete_message(
            #    QueueUrl=config.input_queue_url,
            #    ReceiptHandle=message["ReceiptHandle"],
            #)

        time.sleep(10)
