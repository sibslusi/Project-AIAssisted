from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class AnswerOption:
    id: str
    text: str
    correct: bool


@dataclass(frozen=True)
class Assignment:
    id: str
    module_id: str
    department_id: str
    due_date: date

    def __post_init__(self):
        if not self.id or not self.module_id or not self.department_id:
            raise ValueError("Zuweisung benötigt ID, Modul und Abteilung")
        if type(self.due_date) is not date:
            raise ValueError("Zuweisung benötigt ein gültiges Fristdatum")


@dataclass(frozen=True)
class EvidenceRecord:
    employee_id: str
    module_id: str
    completed_at: datetime
    department_id: str | None = None


@dataclass(frozen=True)
class Scenario:
    id: str
    situation: str
    explanation: str
    legal_basis: str
    options: tuple[AnswerOption, ...]
    active: bool = True

    @classmethod
    def create(
        cls,
        *,
        id: str,
        situation: str,
        explanation: str,
        legal_basis: str,
        options: tuple[AnswerOption, ...],
        active: bool = True,
    ) -> "Scenario":
        if len(options) not in (3, 4):
            raise ValueError("Ein Szenario benötigt drei oder vier Antwortoptionen")
        if len({option.id for option in options}) != len(options):
            raise ValueError("Antwortoptionen müssen eindeutige IDs haben")
        if sum(option.correct for option in options) != 1:
            raise ValueError("Ein Szenario benötigt genau eine richtige Antwort")
        return cls(id, situation, explanation, legal_basis, tuple(options), active)

    def deactivate(self) -> None:
        object.__setattr__(self, "active", False)


@dataclass(frozen=True)
class RoundAnswer:
    position: int
    option_id: str
    correct: bool
    answered_at: datetime


@dataclass(frozen=True)
class AnswerFeedback:
    correct: bool
    explanation: str
    legal_basis: str
    next_position: int | None


@dataclass(frozen=True)
class CompletionResult:
    score: int
    passed: bool


@dataclass
class GameRound:
    id: str
    employee_id: str
    assignment_id: str
    attempt_number: int
    scenarios: tuple[Scenario, ...]
    answers: dict[int, RoundAnswer] = field(default_factory=dict)
    completed_at: datetime | None = None
    score: int | None = None
    passed: bool | None = None

    @classmethod
    def start(
        cls,
        *,
        id: str,
        employee_id: str,
        assignment_id: str,
        attempt_number: int,
        scenarios: tuple[Scenario, ...],
    ) -> "GameRound":
        if len(scenarios) != 5 or not all(scenario.active for scenario in scenarios):
            raise ValueError("Eine neue Runde benötigt genau fünf aktive Szenarien")
        if len({scenario.id for scenario in scenarios}) != 5:
            raise ValueError("Eine Runde darf keine Szenarien doppelt enthalten")
        return cls(id, employee_id, assignment_id, attempt_number, tuple(scenarios))

    def answer(
        self, position: int, option_id: str, answered_at: datetime
    ) -> AnswerFeedback:
        if self.completed_at is not None:
            raise ValueError("Eine abgeschlossene Runde kann nicht beantwortet werden")
        if position in self.answers:
            raise ValueError("Die Position wurde bereits beantwortet")
        if position not in range(1, len(self.scenarios) + 1):
            raise ValueError("Ungültige Szenarioposition")
        next_position = self.first_open_position
        if position != next_position:
            raise ValueError("Es muss die erste offene Position beantwortet werden")

        scenario = self.scenarios[position - 1]
        option = next(
            (option for option in scenario.options if option.id == option_id), None
        )
        if option is None:
            raise ValueError("Die Antwort gehört nicht zum Szenario")

        answer = RoundAnswer(position, option_id, option.correct, answered_at)
        self.answers[position] = answer
        return AnswerFeedback(
            correct=option.correct,
            explanation=scenario.explanation,
            legal_basis=scenario.legal_basis,
            next_position=self.first_open_position,
        )

    @property
    def first_open_position(self) -> int | None:
        return next(
            (
                position
                for position in range(1, len(self.scenarios) + 1)
                if position not in self.answers
            ),
            None,
        )

    def complete(self, completed_at: datetime) -> CompletionResult:
        if len(self.answers) != len(self.scenarios):
            raise ValueError(
                "Eine Runde kann erst nach allen Antworten abgeschlossen werden"
            )
        if self.completed_at is not None:
            raise ValueError("Die Runde ist bereits abgeschlossen")
        self.completed_at = completed_at
        self.score = sum(answer.correct for answer in self.answers.values())
        self.passed = self.score >= 4
        return CompletionResult(self.score, self.passed)
