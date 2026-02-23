from .util import parse_csv as csv

from typing import Protocol, Any

def int_to_str_signed(value: int) -> str:
    return"+" + str(value) if value >= 0 else str(value)

class Passive(Protocol):
    def as_string(self) -> str:
        return "_error_"
    
class CantCatchDiseases:
    onoff: bool

    def __init__(self, onoff: int):
        self.onoff = onoff > 0

    def as_string(self) -> str:
        return "Can't catch diseases" if self.onoff else "Can catch diseases" 
    
class CantSpreadDiseases:
    onoff: bool

    def __init__(self, onoff: int):
        self.onoff = onoff > 0

    def as_string(self) -> str:
        return "Can't spread diseases" if self.onoff else "Can spread diseases" 
    
class KineticSpikes:
    stacks: int

    def __init__(self, stacks: int):
        self.stacks = stacks

    def as_string(self) -> str:
        return f"{int_to_str_signed(self.stacks)} Kinetic Spikes" 

class MeleeRevengeDamage:
    type: str
    damage: int
    knockback: int
    effects: list[Any]
    elements: list[Any]

class SpawnThingOnDamage:
    object: str
    chance: str

    def __init__(self, dataobj: dict[str,str]):
        self.object = dataobj.setdefault("object", "?")
        self.chance = dataobj.setdefault("chance", "?%")

    def as_string(self) -> str:
        return f"{self.chance} to spawn a {self.object} when damage is taken"
    
class Thorns:
    stacks: int

    def __init__(self, stacks: int):
        self.stacks = stacks

    def as_string(self) -> str:
        return f"{int_to_str_signed(self.stacks)} Thorns" 
    





def parse_passive(id: str, data) -> Passive | None:
    match id:
        case "CantCatchDiseases":
            return CantCatchDiseases(data)
        case "CantSpreadDiseases":
            return CantSpreadDiseases(data)
        case "KineticSpikes":
            return KineticSpikes(data)
        case "SpawnThingOnDamage":
            return SpawnThingOnDamage(data)
        case "Thorns":
            return Thorns(data)
        
    return None