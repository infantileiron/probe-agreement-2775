from sqlalchemy import String,Text,ForeignKey,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class ExclusionRule(RecordMixin,Base):
 __tablename__="exclusion_rules"
 __table_args__=(UniqueConstraint("study_id","pair_id",name="uk_study_pair_exclusion"),)
 study_id:Mapped[str]=mapped_column(ForeignKey("studies.id"))
 pair_id:Mapped[str]=mapped_column(String(80))
 reason:Mapped[str]=mapped_column(Text)
 created_by:Mapped[str]=mapped_column(String(160),default="")
