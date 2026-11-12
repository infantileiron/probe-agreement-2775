from uuid import uuid4
from fastapi import HTTPException
from ..models.run import CalibrationRun
from ..models.study import CalibrationStudy
from ..models.dataset import PairedDataset
from ..models.instrument import InstrumentPair
from ..utils.queue import enqueue
from .exclusion_service import snapshot as rule_snapshot
from .paired_data import validate_pairs
from .deming import regress
from .agreement import analyze

MIN_PAIRS=4

def create(db,body):
 if not db.get(CalibrationStudy,body.study_id):raise HTTPException(422,"校准研究不存在")
 # 规则在发起瞬间固化：运行只使用该快照，之后规则更新不影响本运行
 row=CalibrationRun(id=str(uuid4()),study_id=body.study_id,status="queued",result={},error="",exclusion_snapshot=rule_snapshot(db,body.study_id))
 db.add(row);db.commit()
 try:enqueue(row.id)
 except Exception:
  row.status="failed";row.error="Redis队列不可用，请稍后重试";db.commit();raise HTTPException(503,row.error)
 return row

def _partition(dataset_pairs,snapshot):
 reasons={r["pair_id"]:r["reason"] for r in snapshot}
 retained=[p for p in dataset_pairs if p["pair_id"] not in reasons]
 # 原始读数保持不变，仅附加剔除原因，供底稿与归档追溯
 excluded=[{**p,"included":False,"exclusion_reason":reasons[p["pair_id"]]} for p in dataset_pairs if p["pair_id"] in reasons]
 return retained,excluded

def compute(db,run_id):
 row=db.get(CalibrationRun,run_id)
 if row is None or row.status not in ["queued","running"]:return
 row.status="running";db.commit()
 try:
  study=db.get(CalibrationStudy,row.study_id);dataset=db.get(PairedDataset,study.dataset_id);pair=db.get(InstrumentPair,study.instrument_id)
  if dataset.x_unit!=dataset.y_unit or dataset.x_unit!=pair.unit:raise ValueError("单位不一致")
  # 原始读数绝不修改；按发起时规则快照拆分为保留/剔除两组
  retained_pairs,excluded_points=_partition(dataset.pairs,row.exclusion_snapshot or [])
  total_n=len(dataset.pairs);retained_n=len(retained_pairs);excluded_n=len(excluded_points)
  # 不足四组明确失败，而不是返回带偏的统计
  if retained_n<MIN_PAIRS:raise ValueError(f"剔除{excluded_n}组后仅保留{retained_n}组，少于{MIN_PAIRS}组，无法计算；请复核排除规则")
  x,y=validate_pairs(retained_pairs);deming=regress(x,y,study.variance_ratio);ba=analyze(x,y)
  # 统计与图表仅使用保留样本；每个保留点标注 included=True
  points=[{**p,"included":True,"fitted_y":deming["intercept"]+deming["slope"]*p["x"],"residual_y":p["y"]-deming["intercept"]-deming["slope"]*p["x"],"mean":(p["x"]+p["y"])/2,"difference":p["y"]-p["x"],"outside_loa":p["y"]-p["x"]<ba["loa_low"] or p["y"]-p["x"]>ba["loa_high"],"outside_tolerance":abs(p["y"]-p["x"])>study.tolerance} for p in retained_pairs]
  row.result={"dataset_name":dataset.name,"instrument_name":pair.name,"x_serial":pair.x_serial,"y_serial":pair.y_serial,"unit":pair.unit,"n":retained_n,"total_n":total_n,"excluded_n":excluded_n,"deming":deming,"agreement":ba,"points":points,"excluded_points":excluded_points,"exclusion_snapshot":row.exclusion_snapshot or [],"tolerance":study.tolerance,"outside_tolerance":sum(p["outside_tolerance"] for p in points),"sample_basis":"统计与图表仅使用保留配对；原始读数保持不变，剔除配对及原因见excluded_points"};row.status="completed"
 except Exception as e:row.status="failed";row.error=str(e)[:1000]
 db.commit()
