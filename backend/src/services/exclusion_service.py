from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.exclusion import ExclusionRule
from ..models.study import CalibrationStudy
from ..models.dataset import PairedDataset
from ..models.common import serialize

def list_for_study(db,study_id):
 if db.get(CalibrationStudy,study_id) is None:raise HTTPException(404,"校准研究不存在")
 rows=db.scalars(select(ExclusionRule).where(ExclusionRule.study_id==study_id).order_by(ExclusionRule.created_at.asc(),ExclusionRule.pair_id.asc())).all()
 return [serialize(r) for r in rows]

def create(db,body,user):
 study=db.get(CalibrationStudy,body.study_id)
 if study is None:raise HTTPException(422,"校准研究不存在")
 dataset=db.get(PairedDataset,study.dataset_id)
 if not any(p["pair_id"]==body.pair_id for p in dataset.pairs):raise HTTPException(422,f"配对编号{body.pair_id}不在该研究的原始批次中，无法建立排除规则")
 existing=db.scalar(select(ExclusionRule).where(ExclusionRule.study_id==body.study_id,ExclusionRule.pair_id==body.pair_id))
 if existing:raise HTTPException(409,"该配对已存在排除规则；如需调整原因，请删除后重新保存")
 row=ExclusionRule(id=str(uuid4()),study_id=body.study_id,pair_id=body.pair_id,reason=body.reason,created_by=user.email)
 db.add(row);db.commit();db.refresh(row);return row

def delete(db,row):
 db.delete(row);db.commit()

def snapshot(db,study_id):
 """发起运行时调用：固化当前全部规则，保证运行与之后的规则变更隔离。"""
 rows=db.scalars(select(ExclusionRule).where(ExclusionRule.study_id==study_id).order_by(ExclusionRule.created_at.asc())).all()
 return [{"id":r.id,"pair_id":r.pair_id,"reason":r.reason,"created_by":r.created_by,"created_at":serialize(r)["created_at"]} for r in rows]
