from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SemType:
    name: str = "SemType"

@dataclass
class Top(SemType):
    name: str = "Top"

@dataclass
class Object(Top):
    name: str = "Object"


@dataclass
class Temporal:
    name: str = "Temporal"

@dataclass
class Time(Temporal):
    name: str = "Time"


@dataclass
class Period(Temporal):
    name: str = "Period"
    source: Optional[Time] = None
    dest: Optional[Time] = None


@dataclass
class Event(Top):
    name: str = "Event"
    period: Period = field(default_factory=Period)


@dataclass
class Locational(Top):
    name: str = "Locational"

@dataclass
class Location(Locational):
    name: str = "Location"

@dataclass
class Path(Locational):
    name: str = "Path"
    source : Optional[Location] = None
    dest : Optional[Location] = None

@dataclass
class Animate(Object):
    name: str = "Animate"


@dataclass
class NonAnimate(Object):
    name: str = "NonAnimate"

@dataclass
class Human(Animate):
    name: str = "Human"

@dataclass
class NonHuman(Animate):
    name: str = "NonHuman"

@dataclass
class Role(Top):
    name: str = "Role"
    period: Period = field(default_factory=Period)

@dataclass
class Activity(Event):
    name: str = "Activity"

# accomplishment, achievement

@dataclass
class State(Event):
    name: str = "State"

@dataclass
class Property(Event):
    name: str = "Property"

@dataclass
class Quantity(Top):
    name: str = "Quantity"

@dataclass
class UnKnown:
    name: str = "UnKnown"


@dataclass
class AnyType:
    name: str = "AnyType"

@dataclass
class And:
    options: List[Top]

@dataclass
class Alt:
    options: List[And]



SemType = Top

def alt(semtypelist: List[SemType]) -> Alt:
    return Alt([And([semtype]) for semtype in semtypelist])

def sand(semtypelist: List[SemType]) -> And:
    return And(semtypelist)

def tryhierarchy():
    person = Human()
    r = isinstance(person, Human)
    print(r)
    r = isinstance(person, Animate)
    print(r)
    r = isinstance(person, Object)
    print(r)
    r = isinstance(person, Top)
    print(r)
    christmas = Event()
    r = isinstance(christmas, Object)
    print(r)
    r = isinstance(christmas, Human)
    print(r)
    r = issubclass(Human, Object)
    print(r)
    r = issubclass(Human, Top)
    print(r)


if __name__ == '__main__':
    tryhierarchy()