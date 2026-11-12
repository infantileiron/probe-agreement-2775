from sqlalchemy import String,Text,JSON,ForeignKey,Double
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class CalibrationRun(RecordMixin,Base):
 __tablename__="runs"
 study_id:Mapped[str]=mapped_column(ForeignKey("studies.id"))
 status:Mapped[str]=mapped_column(String(20),default="queued")
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default="")
 # 发起运行时生效的排除规则快照；运行计算永远只使用该快照，之后规则变更不影响已发起运行
 exclusion_snapshot:Mapped[list]=mapped_column(JSON,default=list)
