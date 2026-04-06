from pydantic import BaseModel


class DashboardSeriesPoint(BaseModel):
    date: str
    leads: int
    calls: int
    assessments: int


class DashboardMetricsResponse(BaseModel):
    total_leads: int
    leads_with_calls: int
    leads_with_assessments: int
    conversion_rate: float
    completion_rate: float
    avg_assessment_score: float
    queued_tasks: int
    processing_tasks: int
    failed_tasks: int
    period_days: int
    series: list[DashboardSeriesPoint]
