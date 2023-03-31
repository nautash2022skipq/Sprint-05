from aws_cdk import (
    Stage,
)
from constructs import Construct

from nautash_ahmad.nautash_ahmad_stack import NautashAhmadStack

class NautashAhmadPipelineStage(Stage):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.stage = NautashAhmadStack(self, "NautashAhmadPipelineStage")