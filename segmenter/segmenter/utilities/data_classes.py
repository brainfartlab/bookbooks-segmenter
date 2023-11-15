from typing import List

from pydantic import BaseModel, Field


class S3Bucket(BaseModel):
    name: str


class S3Object(BaseModel):
    key: str
    size: int


class S3Event(BaseModel):
    bucket: S3Bucket
    object: S3Object


class S3Record(BaseModel):
    event_time: str = Field(alias="eventTime")
    s3: S3Event

    @property
    def location(self):
        return f"s3://{self.s3.bucket.name}/{self.s3.object.key}"


class SQSEvent(BaseModel):
    records: List[S3Record] = Field(alias="Records")
