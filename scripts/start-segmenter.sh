#!/bin/bash

# Application variables from SSM
values=$(aws ssm --region eu-west-1 get-parameter --name "/bookbooks/segmenter/config" | jq -r '.Parameter.Value')

for s in $(echo $values | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
    export $s
done

# Infrastructure variables from instance metadata
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
AWS_REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)

export AWS_DEFAULT_REGION=$AWS_REGION

source activate pytorch
segmenter \
  -i $RAW_QUEUE_URL \
  -o $SEGMENTS_QUEUE_URL \
  -b $IMAGE_BUCKET \
  >> /var/opt/bookbooks/segmenter.log
