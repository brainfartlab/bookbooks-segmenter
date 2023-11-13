from dataclasses import dataclass
from typing import List

from lang_sam import LangSAM
import numpy as np
from PIL import Image


BOX_THRESHOLD = 0.25
TEXT_THRESHOLD = 0.25

model = LangSAM()


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
            return Segment(
                x_min=intersect_x_min,
                y_min=intersect_y_min,
                x_max=intersect_x_max,
                y_max=intersect_y_max,
            ).size

    def intersect(self, other):
        return self.intersection(other) > 0

    def intersection_ratio(self, other):
        return self.intersection(other) / self.size


def process(image: Image, prompt: str) -> List[Image]:
    return segments(image, prompt)


def segments(image: Image, prompt: str) -> List[Image]:
    masks, boxes, phrases, logits = model.predict(image, prompt, BOX_THRESHOLD, TEXT_THRESHOLD)

    segments = []
    for (mask, (x_min, y_min, x_max, y_max)) in zip(masks, boxes):
        segment = Segment(
            x_min=float(x_min),
            y_min=float(y_min),
            x_max=float(x_max),
            y_max=float(y_max),
            mask=mask,
        )

        segments.append(segment)

    retained = reduce_segments(segments)

    segment_images = [extract_segment(image, segment) for segment in retained]
    if len(segment_images) <= 1:
        return segment_images
    else:
        subsegments = []
        for segment_image in segment_images:
            subsegments.extend(segments(segment_image, prompt))

        return subsegments


def extract_segment(image: Image, segment: Segment) -> Image:
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

            if segment.intersect_ratio(other) > 0.95:
                if segment.size > 2*other.size:
                    omissions.append(segment)
                    break

                if segment.size < 2*other.size:
                    omissions.append(other)

    return [segment for segment in segments if segment not in omissions]
