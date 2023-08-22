from typing import Any, TypeVar, NewType
from enum import Enum
import discord

actions = {
    "Add Role": "add_role"
            }

class ActionInteraction(Enum):
    ACCEPT = "Accept"
    DECLINE = "Decline"

class Action():
    def __init__(self, action: ActionInteraction):
        self.set_type = None
        self.app_result = action

    def add_role(self, role: discord.Role):
        if self.set_type is None:
            self.set_type = "add_role"
            self.add_role_value = role
        else:
            raise ValueError("Action object already set type")

    def get_data(self):
        if self.set_type is not None:
            return {
                "type": self.set_type
            }


