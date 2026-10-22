import csv
from io import StringIO
from zoneinfo import ZoneInfo

from app.application.models import EvidenceRow

HEADER = (
    "Person",
    "Abteilung",
    "Modul",
    "Versuch",
    "Status",
    "Punktzahl",
    "Bestanden",
    "Abgeschlossen am",
    "Szenarien",
)


class TrainingEvidenceCsvAdapter:
    def render(self, rows: tuple[EvidenceRow, ...]) -> str:
        output = StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(HEADER)
        zurich = ZoneInfo("Europe/Zurich")
        for row in rows:
            writer.writerow(
                (
                    row.person,
                    row.department,
                    row.module,
                    row.attempt_number,
                    row.status,
                    "" if row.score is None else row.score,
                    "" if row.passed is None else ("ja" if row.passed else "nein"),
                    ""
                    if row.completed_at is None
                    else row.completed_at.astimezone(zurich).strftime("%d.%m.%Y %H:%M"),
                    "|".join(row.scenario_titles or row.scenario_ids),
                )
            )
        return "\ufeff" + output.getvalue()
