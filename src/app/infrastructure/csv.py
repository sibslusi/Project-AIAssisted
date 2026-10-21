import csv
from io import StringIO
from zoneinfo import ZoneInfo

from app.domain.models import EvidenceRecord


class TrainingEvidenceCsvAdapter:
    def render(self, records: tuple[EvidenceRecord, ...]) -> str:
        output = StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(("Person", "Abteilung", "Modul", "Abgeschlossen am"))
        zurich = ZoneInfo("Europe/Zurich")
        for record in records:
            writer.writerow(
                (
                    record.employee_id,
                    record.department_id or "",
                    record.module_id,
                    record.completed_at.astimezone(zurich).isoformat(
                        timespec="seconds"
                    ),
                )
            )
        return "\ufeff" + output.getvalue()
