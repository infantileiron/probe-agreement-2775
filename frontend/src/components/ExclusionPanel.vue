<script setup lang="ts">
import {ref,computed,watch} from 'vue';
import {exclusions} from '../stores/exclusions';
import {datasets} from '../stores/datasets';
import {studies} from '../stores/studies';
import {canWrite} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import Notice from './common/Notice.vue';
const props=defineProps<{studyId:string}>();
const pairId=ref(''),reason=ref('');const {error,busy,act}=useTask();
const rules=computed(()=>exclusions.byStudy.value[props.studyId]||[]);
const study=computed(()=>studies.items.value.find(s=>s.id===props.studyId));
const dataset=computed(()=>datasets.items.value.find(d=>d.id===study.value?.dataset_id));
const existingIds=computed(()=>new Set(rules.value.map(r=>r.pair_id)));
const availablePairs=computed(()=>(dataset.value?.pairs||[]).filter((p:any)=>!existingIds.value.has(p.pair_id)));
watch(()=>props.studyId,id=>{if(id)exclusions.load(id)},{immediate:true});
function submit(){act(async()=>{if(!pairId.value||reason.value.trim().length<2)throw new Error('请选择配对编号并填写至少2个字的剔除原因');await exclusions.create({study_id:props.studyId,pair_id:pairId.value,reason:reason.value.trim()});pairId.value='';reason.value=''})}
function remove(id:string){act(async()=>exclusions.remove(props.studyId,id))}
</script>
<template>
 <div class="exclusion-panel">
  <p class="eyebrow">EXCLUSION RULES · 异常配对复核剔除</p>
  <p class="exclusion-hint">规则只影响<strong>之后发起</strong>的运行；已发起运行沿用发起时的规则快照，原始读数不会被修改。图表与统计仅使用保留配对。</p>
  <Notice :message="error||exclusions.error.value"/>
  <table v-if="rules.length" class="table-wrap">
   <thead><tr><th>配对编号</th><th>剔除原因</th><th>登记人</th><th v-if="canWrite()"></th></tr></thead>
   <tbody>
    <tr v-for="r in rules" :key="r.id"><td>{{r.pair_id}}</td><td class="reason-cell">{{r.reason}}</td><td>{{r.created_by}}</td><td v-if="canWrite()"><button class="secondary tiny" :disabled="busy" @click="remove(r.id)">移除规则</button></td></tr>
   </tbody>
  </table>
  <p v-else class="empty">尚未保存排除规则，新运行默认使用全部原始配对。</p>
  <form v-if="canWrite()" class="exclusion-form" @submit.prevent="submit">
   <label>剔除配对
    <select v-model="pairId" required>
     <option value="" disabled>选择复核确认异常的配对编号</option>
     <option v-for="p in availablePairs" :key="p.pair_id" :value="p.pair_id">{{p.pair_id}} · {{p.range_label}} · x={{p.x}} / y={{p.y}}</option>
    </select>
   </label>
   <label>剔除原因（随运行底稿与归档快照留存）<textarea v-model="reason" rows="3" required minlength="2" maxlength="1000" placeholder="例如：现场核查确认采集时段存在瞬时压力冲击，读数不代表稳定配对"></textarea></label>
   <button :disabled="busy">保存排除规则</button>
  </form>
 </div>
</template>
