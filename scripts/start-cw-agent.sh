#!/bin/bash
sudo mkdir /var/opt/bookbooks
sudo chown ec2-user:ec2-user /var/opt/bookbooks

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/segmenter/config/cw-config.json -s
