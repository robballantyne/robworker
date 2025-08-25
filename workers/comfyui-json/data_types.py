import os
import sys
import json
import random
import dataclasses
import inspect
from typing import Dict, Any
from functools import cache
from math import ceil

from lib.data_types import ApiPayload, JsonDataException

DEFAULT_TIME_COST = 15.0 # seconds (fallback if not provided by template or user)

with open("workers/comfyui/misc/test_prompts.txt", "r") as f:
    test_prompts = f.readlines()

def count_workload(expected_time: float|None=None) -> float:
    if expected_time is not None:
        time_cost = float(expected_time)
    else:
        time_cost = float(os.getenv('AVG_TIME_COST', DEFAULT_TIME_COST))
    
    return time_cost


@dataclasses.dataclass
class ComfyWorkflowData(ApiPayload):
    input: dict
    expected_time: int | float | None = None

    @classmethod
    def for_test(cls):
        test_prompt = random.choice(test_prompts).rstrip()
        return cls(
            input={
                "request_id": f"test-{random.randint(1000, 9999)}",
                "modifier": "Text2Image",
                "modifications": {
                    "prompt": test_prompt,
                    "width": 1024,
                    "height": 1024,
                    "steps": 28,
                    "seed": random.randint(0, sys.maxsize),
                }
            },
            expected_time=8  # Test data: expect 8 seconds on RTX4090 for a simple text to image workflow
        )

    def generate_payload_json(self) -> Dict[str, Any]:
        # input is already a dict, just return it wrapped in the expected structure
        return {"input": self.input}

    def count_workload(self) -> float:
        # We cannot inspect complex workflows for complexity, but we can use a time-cost estimate
        return count_workload(self.expected_time)

    @classmethod
    def from_json_msg(cls, json_msg: Dict[str, Any]) -> "ComfyWorkflowData":
        # Extract required fields
        if "input" not in json_msg:
            raise JsonDataException({"input": "missing parameter"})
        
        # expected_time is optional, defaults to None if not provided
        expected_time = json_msg.get("expected_time")
        if expected_time is not None:
            expected_time = float(expected_time)
        
        return cls(
            input=json_msg["input"],
            expected_time=expected_time
        )