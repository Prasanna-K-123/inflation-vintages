const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');const {load}=require('./dom_harness.cjs');
const root=path.resolve(__dirname,'..'),{app,el}=load(path.join(root,'docs/index.html'),'P6Demo'),source=JSON.parse(fs.readFileSync(path.join(root,'reports/final.json'),'utf8'));
assert.deepEqual(JSON.parse(JSON.stringify(app.data)),source);const close=(x,y)=>assert.ok(Math.abs(x-y)<1e-12,`${x} != ${y}`);let releaseViews=0,tableRowsChecked=0;
function checkAccessibleValues(method,target,hindsight,selected){
 const rendered=[...el('forecast-rows').innerHTML.matchAll(/<tr[^>]*><th scope="row">(\d{4}-\d{2})(?:<span class="sr-only"> \(selected month\)<\/span>)?<\/th><td>([^<]+)<\/td><td>([^<]+)<\/td><td>([^<]+)<\/td><\/tr>/g)];
 assert.equal(rendered.length,18);
 source.per_release.forEach((r,i)=>{
  const f=hindsight?r.hindsight_ar1_prediction:r.forecasts[method],a=target==='later'?r.later_final_target:r.first_provisional_actual;
  assert.equal(rendered[i][1],r.target_month);assert.equal(rendered[i][2],f.toFixed(3));assert.equal(rendered[i][3],a.toFixed(3));
  assert.equal(rendered[i][4],(f-a>=0?'+':'')+(f-a).toFixed(3));tableRowsChecked++;
 });
 assert.equal((el('forecast-rows').innerHTML.match(/selected month/g)||[]).length,1);
 assert.ok(el('view-status').textContent.startsWith(selected+'. '));
 assert.ok(el('forecast-table-caption').textContent.includes(target==='later'?'Later-final diagnostic':'First-provisional primary'));
 assert.equal(el('view-status').textContent.includes('not an available forecast'),hindsight);
 assert.ok(el('forecast-chart').innerHTML.includes('stroke-dasharray="6 4"'));
}
for(const row of source.per_release){
 assert.ok(Date.parse(row.lag_source.published_at)<=Date.parse(row.forecast_cutoff));assert.ok(Date.parse(row.hindsight_lag_final.published_at)>Date.parse(row.forecast_cutoff));
 for(const method of ['persistence','ridge_ar1','seasonal_12month'])for(const target of ['first','later']){
  el('month').value=row.target_month;el('method').value=method;el('target').value=target;el('hindsight').checked=false;el('method').fire('change');
  const actual=target==='later'?row.later_final_target:row.first_provisional_actual;
  assert.equal(el('forecast').textContent,row.forecasts[method].toFixed(3));assert.equal(el('actual').textContent,actual.toFixed(3));
  assert.equal(el('source').href,(method==='seasonal_12month'?row.seasonal_source:row.lag_source).source_url);
  const m=app.metric(method,target,false),expected=target==='first'?source.metrics[method]:source.later_final_target_diagnostic.metrics[method];
  close(m.rmse,expected.rmse_pp);close(m.mae,expected.mae_pp);close(m.bias,expected.mean_error_pp);checkAccessibleValues(method,target,false,row.target_month);releaseViews++;
 }
 el('method').value='ridge_ar1';el('target').value='first';el('hindsight').checked=true;el('hindsight').fire('change');
 assert.equal(el('forecast').textContent,row.hindsight_ar1_prediction.toFixed(3));assert.match(el('hindsight-note').textContent,/not an available forecast/);checkAccessibleValues('ridge_ar1','first',true,row.target_month);
}
const hindsight=app.metric('ridge_ar1','first',true),expected=source.hindsight_diagnostic.metrics_same_frozen_ar1_with_unavailable_final_lag;close(hindsight.rmse,expected.rmse_pp);
el('method').value='persistence';el('hindsight').checked=true;el('method').fire('change');assert.equal(el('hindsight').checked,false);assert.equal(el('hindsight').disabled,true);
el('reset').fire('click');assert.equal(el('month').value,'2025-12');assert.equal(el('method').value,'persistence');assert.equal(el('target').value,'first');
assert.equal(source.selected_forecast_frozen_on_development,'persistence');
const result={passed:true,embedded_evidence_matches_source:true,release_method_target_views:releaseViews,hindsight_views:18,aggregate_metrics_match_saved_Python:true,asof_and_unavailable_revision_timing_checked:true,hindsight_disabled_for_other_methods:true,reset_verified:true,accessible_table_rows_checked:tableRowsChecked,selected_month_status_and_diagnostic_labels_checked:true,chart_line_patterns_distinct:true,execution:'Actual inline JavaScript in Node VM with minimal DOM. Not rendered browser/mobile/keyboard verification.',browser_verified:false,public_release_complete:false};
fs.writeFileSync(path.join(root,'reports/demo_verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
