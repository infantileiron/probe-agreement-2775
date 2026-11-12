from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user
from ..schemas.exclusion import ExclusionRuleCreate
from ..controllers import exclusion_controller as controller,common
from ..models.exclusion import ExclusionRule
from ..models.common import serialize
router=APIRouter(prefix="/exclusion-rules",tags=["exclusion-rules"])
@router.get("")
def listing(study_id:str,db=Depends(get_db),user=Depends(current)):return controller.list_for_study(db,study_id)
@router.post("",status_code=201)
def create(body:ExclusionRuleCreate,db=Depends(get_db),user=Depends(write_user)):return controller.create(db,body,user)
@router.delete("/{ident}",status_code=204)
def remove(ident:str,db=Depends(get_db),user=Depends(write_user)):
 controller.delete(db,ident);return None
