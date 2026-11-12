import csv,io
from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.review import BiasReview
from ..models.run import CalibrationRun
from ..models.report import Report

def create(db,body):
 review=db.get(BiasReview,body.review_id)
 if review is None or review.state!="approved":raise HTTPException(409,"报告必须关联已批准的偏倚复核")
 existing=db.scalar(select(Report).where(Report.review_id==body.review_id))
 if existing:return existing
 run=db.get(CalibrationRun,review.run_id);row=Report(id=str(uuid4()),review_id=review.id,title=body.title,snapshot={"result":run.result,"action":review.action,"reviewer":review.reviewer});db.add(row);db.commit();return row

def export(row):
 result=row.snapshot["result"];unit=result.get("unit","")
 out=io.StringIO();writer=csv.writer(out)
 # 仅当确有剔除配对时新增状态/原因列；无剔除的新快照与缺少该键的历史快照都保持原列结构
 has_exclusions=bool(result.get("excluded_points"))
 header=["sample_status","exclusion_reason","pair_id","range_label","x","y","unit","mean","difference_y_minus_x","deming_fitted_y","residual_y","outside_loa","outside_tolerance"] if has_exclusions else ["pair_id","range_label","x","y","unit","mean","difference_y_minus_x","deming_fitted_y","residual_y","outside_loa","outside_tolerance"]
 writer.writerow(header)
 if has_exclusions:
  for p in result["points"]:
   writer.writerow(["retained","",p["pair_id"],p["range_label"],p["x"],p["y"],unit,p.get("mean"),p.get("difference"),p.get("fitted_y"),p.get("residual_y"),p.get("outside_loa"),p.get("outside_tolerance")])
  for p in result["excluded_points"]:
   writer.writerow(["excluded",p.get("exclusion_reason",""),p["pair_id"],p["range_label"],p["x"],p["y"],unit,"","","","","",""])
 else:
  for p in result["points"]:
   writer.writerow([p["pair_id"],p["range_label"],p["x"],p["y"],unit,p["mean"],p["difference"],p["fitted_y"],p["residual_y"],p["outside_loa"],p["outside_tolerance"]])
 return "﻿"+out.getvalue()
