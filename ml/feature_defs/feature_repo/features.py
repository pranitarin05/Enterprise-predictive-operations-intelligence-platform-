"""
Feast feature view definitions.

A FeatureView binds an entity to a data source and declares which
columns are actual features -- this is what makes daily_tenant_summary
queryable both offline (training) and online (serving) through one
consistent definition.
"""

from datetime import timedelta

from feast import FeatureView, Field, FileSource
from feast.types import Float64, Int64, String

from entities import tenant

daily_summary_source = FileSource(
    name="daily_tenant_summary_source",
    path="s3://epoip-gold/feast_exports/daily_tenant_summary",
    timestamp_field="event_date",
    s3_endpoint_override="http://localhost:9000",
)

daily_tenant_summary_fv = FeatureView(
    name="daily_tenant_summary",
    entities=[tenant],
    ttl=timedelta(days=365),
    schema=[
        Field(name="event_type", dtype=String),
        Field(name="event_count", dtype=Int64),
        Field(name="total_amount_usd", dtype=Float64),
        Field(name="total_delay_days", dtype=Int64),
        Field(name="avg_quantity_remaining", dtype=Float64),
    ],
    source=daily_summary_source,
    online=True,
)
