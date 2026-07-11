"""
Feast entity definitions.

An entity is "the thing features are about" -- the key you look up
features by. Here, that's tenant_id: every feature we serve answers
"what is this metric, for this tenant?"
"""

from feast import Entity

tenant = Entity(
    name="tenant_id",
    description="A tenant (business unit/client organization) in the platform",
)
