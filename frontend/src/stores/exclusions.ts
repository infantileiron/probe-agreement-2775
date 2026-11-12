import {ref} from 'vue';
import {fetchExclusionRules,createExclusionRule,deleteExclusionRule} from '../api/exclusions';
import type {ExclusionRule,ExclusionInput} from '../types/domain';
// 规则按研究隔离：每个研究维护自己的规则列表，与运行发起时固化的快照相互独立
export function exclusionStore(){
 const byStudy=ref<Record<string,ExclusionRule[]>>({});const error=ref('');const busy=ref(false);
 async function load(studyId:string){busy.value=true;try{byStudy.value={...byStudy.value,[studyId]:await fetchExclusionRules(studyId)};error.value=''}catch(e){error.value=(e as Error).message}finally{busy.value=false}}
 async function create(body:ExclusionInput){await createExclusionRule(body);await load(body.study_id)}
 async function remove(studyId:string,id:string){await deleteExclusionRule(id);await load(studyId)}
 return {byStudy,error,busy,load,create,remove};
}
export const exclusions=exclusionStore();
