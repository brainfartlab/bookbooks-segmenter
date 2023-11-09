#!/bin/bash
values=$(aws ssm --region eu-west-1 get-parameter --name "/bookbooks/segmenter/config" | jq -r '.Parameter.Value')

for s in $(echo $values | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
    export $s
done

echo "$RAW_QUEUE_URL" >> /var/opt/bookbooks/segmenter.log
source activate pytorch
#segmenter >> /var/opt/bookbooks/segmenter.log
