from dataclasses import asdict, dataclass


@dataclass
class InvalidRecord:
    row_number: int
    reasons: list[str]
    raw_record: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SatisfactionSummary:
    closed_cases_with_score: int
    average_score: float | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisSummary:
    file_name: str
    processed_at: str
    totals: dict[str, int]
    category_breakdown: dict[str, int]
    status_breakdown: dict[str, int]
    invalid_breakdown: dict[str, int]
    invalid_details: list[InvalidRecord]
    satisfaction: SatisfactionSummary

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "processed_at": self.processed_at,
            "totals": self.totals,
            "category_breakdown": self.category_breakdown,
            "status_breakdown": self.status_breakdown,
            "invalid_breakdown": self.invalid_breakdown,
            "invalid_details": [record.to_dict() for record in self.invalid_details],
            "satisfaction": self.satisfaction.to_dict(),
        }
