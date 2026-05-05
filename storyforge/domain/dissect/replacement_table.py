from pydantic import BaseModel


class ReplacementTable(BaseModel):
    world_setting_replace: dict
    golden_finger_replace: dict
    power_system_replace: dict
    conflict_system_replace: dict
    character_replace: dict
