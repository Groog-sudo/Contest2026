from pydantic import BaseModel


class DashboardSeriesPoint(BaseModel):
    date: str
    leads: int
    calls: int
    analyses: int
    high_risk: int


class DashboardMetricsResponse(BaseModel):
    total_leads: int
    leads_with_calls: int
    leads_with_analyses: int
    conversion_rate: float
    resolution_rate: float
    high_risk_cases: int
    queued_tasks: int
    processing_tasks: int
    failed_tasks: int
    period_days: int
    series: list[DashboardSeriesPoint]
