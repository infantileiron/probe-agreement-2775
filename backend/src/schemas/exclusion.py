from pydantic import BaseModel,Field
class ExclusionRuleCreate(BaseModel):
 study_id:str
 pair_id:str=Field(min_length=1,max_length=80)
 reason:str=Field(min_length=2,max_length=1000)
