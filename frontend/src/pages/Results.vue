<script setup lang="ts">
import {ref,computed,onMounted,onUnmounted,watch} from 'vue';
import {route} from '../router';
import {runs} from '../stores/runs';
import {reviews} from '../stores/reviews';
import {canWrite} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import {fixed} from '../utils/format';
import PageHeading from '../components/common/PageHeading.vue';
import StatusPill from '../components/common/StatusPill.vue';
import Notice from '../components/common/Notice.vue';
import EmptyState from '../components/common/EmptyState.vue';
import CalibrationMetrics from '../components/CalibrationMetrics.vue';
import AgreementPlot from '../components/AgreementPlot.vue';
import PairTable from '../components/PairTable.vue';
const selected=ref(route.value.query.get('run')||'demo-run'),action=ref('对照量程与重复测量依据复核比例偏倚，检查界限外配对；BA界限不是CI，不据此直接宣称探头可互换。'),notice=ref('');
watch(()=>route.value.query.get('run'),v=>{selected.value=v||'demo-run'});
const {error,busy,act}=useTask();
let timer:ReturnType<typeof setInterval>;
onMounted(()=>{runs.load();timer=setInterval(runs.load,2000)});
onUnmounted(()=>clearInterval(timer));
const run=computed(()=>runs.items.value.find(r=>r.id===selected.value)),result=computed(()=>run.value?.result);
const runLabel=(id:string)=>({'demo-run':'三量程基线','demo-run-excluded':'剔除重算（238组）'}as Record<string,string>)[id]||id.slice(0,8);
const excluded=computed(()=>result.value?.excluded_points||[]);
const previewRows=computed(()=>{const pts=result.value?.points||[];return pts.filter((p:any)=>p.outside_loa).concat(pts.filter((p:any)=>!p.outside_loa).slice(0,12))});
function submit(){act(async()=>{await reviews.create({run_id:selected.value,action:action.value});notice.value='偏倚复核已提交，等待管理员批准。'})}
</script>
<template>
 <PageHeading index="04 / 运行底稿" title="校准关系，与差值分布一并复核。" note="两图都来自同一批持久化Python结果，且仅基于保留配对。Deming不是单侧OLS，BA界限不是偏倚置信区间；剔除配对保留原始读数与原因，不参与统计。"/>
 <div class="result-toolbar"><label>运行记录<select v-model="selected"><option v-for="r in runs.items.value" :key="r.id" :value="r.id">{{runLabel(r.id)}} · {{r.status}}</option></select></label><StatusPill v-if="run" :status="run.status"/></div>
 <Notice :message="error||runs.error.value"/>
 <Notice v-if="run?.status==='failed'" :message="run.error"/>
 <EmptyState v-if="run&&['queued','running'].includes(run.status)" text="独立worker正在计算Deming、BA与比例偏倚，结果每两秒刷新。"/>
 <template v-if="run?.status==='completed'&&result">
  <section v-if="excluded.length" class="exclusion-summary">
   <p class="eyebrow">RETAINED SAMPLE · 规则快照 {{run.exclusion_snapshot?.length||0}} 条</p>
   <p>原始 {{result.total_n}} 组，剔除 <strong>{{result.excluded_n}}</strong> 组，统计与图表仅使用保留的 <strong>{{result.n}}</strong> 组；原始读数保持不变，剔除原因随本运行与归档快照留存。</p>
  </section>
  <CalibrationMetrics :result="result"/>
  <div class="result-plots"><section><h2>Deming校准散点（仅保留配对）</h2><AgreementPlot :result="result" mode="deming"/></section><section><h2>Bland–Altman差值图（仅保留配对）</h2><AgreementPlot :result="result" mode="ba"/></section></div>
  <div class="result-columns">
   <section>
    <h2>界限外配对与读数预览</h2>
    <PairTable :rows="previewRows"/>
    <section v-if="excluded.length" class="excluded-block">
     <h2>已剔除配对（{{excluded.length}} 组，不参与统计）</h2>
     <PairTable :rows="excluded" show-reason/>
    </section>
    <form v-if="canWrite()" class="review-form" @submit.prevent="submit"><label>偏倚复核说明<textarea v-model="action" rows="4" required minlength="8"></textarea></label><button :disabled="busy">提交偏倚复核</button><p class="success" v-if="notice">{{notice}}</p></form>
   </section>
   <aside class="field-note">
    <p class="eyebrow">METHOD & LIMITS</p>
    <h3>比例偏倚回归</h3>
    <p v-if="result.agreement.proportional.estimable">差值={{fixed(result.agreement.proportional.intercept)}} + {{fixed(result.agreement.proportional.slope,4)}} × 均值</p>
    <p v-else>{{result.agreement.proportional.reason}}</p>
    <p>有效 {{result.n}} 组<template v-if="result.total_n">（原始 {{result.total_n}} 组、剔除 {{result.excluded_n||0}} 组）</template>，界限外 {{result.agreement.outside_loa}} 组；讨论容差 ±{{result.tolerance}} {{result.unit}} 外 {{result.outside_tolerance}} 组。</p>
    <p>y方向残差RMSE {{fixed(result.deming.residual_rmse_y)}} {{result.unit}}，仅作拟合残差摘要。</p>
    <p class="note-rule">{{result.agreement.limits_note}} 若差值随均值变化或方差不齐，应先讨论量程/变换口径。</p>
   </aside>
  </div>
 </template>
</template>
