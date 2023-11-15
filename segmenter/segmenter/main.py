from dataclasses import dataclass
import logging
from typing import List

import click_logging
from lang_sam import LangSAM
import numpy as np
from PIL import Image


BOX_THRESHOLD = 0.25
TEXT_THRESHOLD = 0.25

model = LangSAM()
logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@dataclass
class Segment:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    mask: np.ndarray

    @property
    def size(self):
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)

    def intersection(self, other):
        intersect_x_min = max(self.x_min, other.x_min)
        intersect_y_min = max(self.y_min, other.y_min)
        intersect_x_max = min(self.x_max, other.x_max)
        intersect_y_max = min(self.y_max, other.y_max)

        if intersect_x_min >= intersect_x_max or intersect_y_min >= intersect_y_max:
            return 0
        else:
            return (intersect_x_max - intersect_x_min) * (intersect_y_max - intersect_y_min)

    def intersect(self, other):
        return self.intersection(other) > 0

    def intersection_ratio(self, other):
        return self.intersection(other) / self.size


def process(image: Image.Image, prompt: str) -> List[Image.Image]:
    return segment(image, prompt)


def segment(image: Image.Image, prompt: str) -> List[Image.Image]:
    masks, boxes, phrases, logits = model.predict(image, prompt, BOX_THRESHOLD, TEXT_THRESHOLD)

    segments = []
    for (mask, (x_min, y_min, x_max, y_max)) in zip(masks, boxes):
        s = Segment(
            x_min=float(x_min),
            y_min=float(y_min),
            x_max=float(x_max),
            y_max=float(y_max),
            mask=mask.squeeze().cpu().numpy(),
        )

        segments.append(s)

    logger.info("detected %d segments", len(segments))

    retained = reduce_segments(segments)

    segment_images = [extract_segment(image, s) for s in retained]
    if len(segment_images) <= 1:
        return segment_images
    else:
        logger.info("looking for subsegments")
        final_segments = []
        for segment_image in segment_images:
            subsegments = segment(segment_image, prompt)
            if len(subsegments) <= 1:
                final_segments.append(segment_image)
            else:
                final_segments.extend(subsegments)

        return final_segments


def extract_segment(image: Image.Image, segment: Segment) -> Image.Image:
    blank = image.point(lambda _: 0)

    masked_image = Image.composite(image, blank, Image.fromarray(segment.mask))
    return masked_image.crop((segment.x_min, segment.y_min, segment.x_max, segment.y_max))


def reduce_segments(segments) -> List[Segment]:
    omissions = []

    for i, segment in enumerate(segments):
        if segment in omissions:
            continue

        for other in segments[i+1:]:
            if other in omissions:
                continue

            if segment.intersection_ratio(other) > 0.95:
                if segment.size > 2*other.size:
                    omissions.append(segment)
                    break

                if segment.size < 2*other.size:
                    omissions.append(other)

    logger.info("reducing segments from %d to %d", len(segments), len(segments) - len(omissions))

    return [segment for segment in segments if segment not in omissions]
