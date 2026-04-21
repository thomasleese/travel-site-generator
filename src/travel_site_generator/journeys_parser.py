import datetime
from enum import Enum
import re
from typing import NamedTuple, Optional

from .journey import Journey, JourneyLeg, ModeOfTransport, Stop

type Journeys = list[Journey]


class Descriptor(Enum):
    BY = "by"
    FROM = "from"
    ON = "on"
    TO = "to"


class TokenType(Enum):
    DATE = 1
    KEYWORD = 2
    STRING = 3


class Token(NamedTuple):
    type: TokenType
    value: str


KEYWORDS = [descriptor.value for descriptor in Descriptor] + [
    mode.value for mode in ModeOfTransport
]
DATE_PATTERN = r"\d{4}-\d{2}-\d{2}"


def _tokenize(s: str) -> list[Token]:
    tokens = []
    i = 0
    n = len(s)

    while i < n:
        if s[i].isspace():
            i += 1
            continue

        if s[i] == "#":
            while i < n and s[i] != "\n":
                i += 1
            continue

        if i + 9 < n and re.match(DATE_PATTERN, s[i : i + 10]):
            tokens.append(Token(TokenType.DATE, s[i : i + 10]))
            i += 10
            continue

        for keyword in KEYWORDS:
            if s[i : i + len(keyword)].lower() == keyword and (
                i + len(keyword) == n or not s[i + len(keyword)].isalpha()
            ):
                tokens.append(Token(TokenType.KEYWORD, keyword))
                i += len(keyword)
                continue

        j = i
        while j < n and not s[j].isspace() and s[j] not in ["#"]:
            j += 1
        if j > i:
            tokens.append(Token(TokenType.STRING, s[i:j]))
        i = j

    return tokens


class CurrentAction(Enum):
    EXPECTING_DATE = 0
    EXPECTING_DESCRIPTOR = 1
    EXPECTING_DESTINATION = 2
    EXPECTING_MODE_OF_TRANSPORT = 3
    EXPECTING_SOURCE = 4


def _parse(tokens: list[Token]) -> Journeys:
    journeys = []

    current_action = CurrentAction.EXPECTING_DESCRIPTOR

    is_first_from = True
    is_first_to = True

    current_legs: list[JourneyLeg] = []
    current_source_name: Optional[str] = None
    current_source_date: Optional[datetime.date] = None
    current_destination_name: Optional[str] = None
    current_destination_date: Optional[datetime.date] = None
    current_mode_of_transport: Optional[ModeOfTransport] = None

    def append_current_leg():
        nonlocal \
            current_legs, \
            current_source_name, \
            current_source_date, \
            current_destination_name, \
            current_destination_date

        if current_source_name is None:
            raise ValueError("No source stop is defined yet")
        elif current_destination_name is None:
            raise ValueError("No destination stop is defined yet")
        elif current_source_date is None:
            raise ValueError("No source date is defined yet")
        elif current_destination_date is None:
            raise ValueError("No destination date is defined yet")
        elif current_mode_of_transport is None:
            raise ValueError("No mode of transport is defined yet")

        source = Stop(name=current_source_name, date=current_source_date)
        destination = Stop(name=current_destination_name, date=current_destination_date)

        current_legs.append(
            JourneyLeg(
                source=source,
                destination=destination,
                mode_of_transport=current_mode_of_transport,
            )
        )

        current_source_name = current_destination_name
        current_source_date = current_destination_date
        current_destination_name = None

    def append_current_journey():
        nonlocal \
            journeys, \
            is_first_to, \
            current_legs, \
            current_source_name, \
            current_source_date, \
            current_destination_name, \
            current_destination_date, \
            current_mode_of_transport

        append_current_leg()

        journeys.append(Journey(legs=current_legs))

        is_first_to = True
        current_legs = []
        current_source_name = None
        current_source_date = None
        current_destination_name = None
        current_destination_date = None
        current_mode_of_transport = None

    def handle_date(token):
        nonlocal current_action, current_source_date, current_destination_date

        if current_action == CurrentAction.EXPECTING_DATE:
            date = datetime.date.fromisoformat(token.value)
            if current_source_date is None:
                current_source_date = date

            current_destination_date = date
            current_action = CurrentAction.EXPECTING_DESCRIPTOR
        else:
            raise ValueError("Unexpected date")

    def handle_keyword(token):
        nonlocal current_action, current_mode_of_transport, is_first_from, is_first_to

        match current_action:
            case CurrentAction.EXPECTING_DESCRIPTOR:
                match token.value:
                    case Descriptor.BY.value:
                        current_action = CurrentAction.EXPECTING_MODE_OF_TRANSPORT
                    case Descriptor.FROM.value:
                        if not is_first_from:
                            append_current_journey()

                        current_action = CurrentAction.EXPECTING_SOURCE
                        is_first_from = False
                    case Descriptor.ON.value:
                        current_action = CurrentAction.EXPECTING_DATE
                    case Descriptor.TO.value:
                        if not is_first_to:
                            append_current_leg()

                        current_action = CurrentAction.EXPECTING_DESTINATION
                        is_first_to = False
                    case _:
                        raise ValueError(f"Unexpected keyword '{token.value}'")
            case CurrentAction.EXPECTING_MODE_OF_TRANSPORT:
                current_mode_of_transport = ModeOfTransport(token.value)
                current_action = CurrentAction.EXPECTING_DESCRIPTOR
            case _:
                raise ValueError(f"Unexpected keyword '{token.value}'")

    def handle_string(token):
        nonlocal current_action, current_source_name, current_destination_name

        match current_action:
            case CurrentAction.EXPECTING_SOURCE:
                current_source_name = token.value
                current_action = CurrentAction.EXPECTING_DESCRIPTOR
            case CurrentAction.EXPECTING_DESTINATION:
                current_destination_name = token.value
                current_action = CurrentAction.EXPECTING_DESCRIPTOR

    for token in tokens:
        match token.type:
            case TokenType.DATE:
                handle_date(token)
            case TokenType.KEYWORD:
                handle_keyword(token)
            case TokenType.STRING:
                handle_string(token)

    append_current_journey()

    return journeys


def loads(s: str) -> Journeys:
    return _parse(_tokenize(s))
