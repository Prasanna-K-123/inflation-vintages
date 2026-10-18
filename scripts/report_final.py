"""Generate final research evidence from saved aggregates, never refit models."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'


def dump(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def run():
    final = json.loads((ROOT/'reports/final.json').read_text())
    development = json.loads((ROOT/'reports/development.json').read_text())
    rows = final['per_release']
    y = np.array([r['first_provisional_actual'] for r in rows])
    lag = np.array([r['forecasts']['persistence'] for r in rows])
    ridge = np.array([r['forecasts']['ridge_ar1'] for r in rows])
    lag_error = lag-y
    adjustment = ridge-lag
    decomposition = {
        'identity': 'Ridge error = (last release minus target) + (Ridge prediction minus last release)',
        'mean_lag_error_pp': float(lag_error.mean()),
        'mean_model_adjustment_pp': float(adjustment.mean()),
        'mean_ar1_error_pp': float((ridge-y).mean()),
        'mse_lag_component': float(np.mean(lag_error**2)),
        'mse_model_adjustment_component': float(np.mean(adjustment**2)),
        'mse_cross_component': float(2*np.mean(lag_error*adjustment)),
        'mse_total': float(np.mean((ridge-y)**2)),
        'interpretation': 'Arithmetic, not causal attribution. Components may offset; cross term can be negative.'}
    assert abs(decomposition['mse_total']-sum(decomposition[k] for k in ['mse_lag_component','mse_model_adjustment_component','mse_cross_component']))<1e-12
    dump('reports/error_decomposition.json', decomposition)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, ax = plt.subplots(2, 1, figsize=(9.8, 6.6), sharex=True, constrained_layout=True)
    dates = [r['target_month'] for r in rows]
    ax[0].plot(dates,y,marker='o',color='#173c58',label='First provisional target')
    ax[0].plot(dates,lag,color='#16796d',label='Frozen selected persistence')
    ax[0].plot(dates,ridge,color='#b05b24',label='Fixed Ridge AR(1)')
    ax[0].set_ylabel('Headline inflation (%)');ax[0].legend(frameon=False,fontsize=8,ncol=3,loc='lower left')
    ax[0].set_title('Old-base CPI: honest one-release-ahead forecasts',loc='left',weight='bold')
    ax[1].bar(dates,lag_error,color='#16796d',label='Lag error')
    ax[1].plot(dates,ridge-y,color='#b05b24',marker='.',label='AR(1) error')
    ax[1].axhline(0,color='#75838b',lw=.7);ax[1].set_ylabel('Forecast minus target (pp)')
    ax[1].legend(frameon=False,fontsize=8);ax[1].tick_params(axis='x',rotation=60,labelsize=8)
    fig.savefig(ROOT/'reports/diagnostics.svg');fig.savefig(ROOT/'reports/diagnostics.png',dpi=160);plt.close(fig)
    m = final['metrics'];contrast = final['primary_paired_squared_error'];ci=contrast['conditional_95_percentile_interval']
    metric_table = '\n'.join(f"| {name} | {v['mae_pp']:.4f} | {v['rmse_pp']:.4f} | {v['mean_error_pp']:+.4f} |" for name,v in m.items())
    full_table = '\n'.join(f"| {r['target_month']} | {r['forecast_cutoff']} | {r['first_provisional_actual']:.2f} | {r['forecasts']['persistence']:.2f} | {r['forecasts']['ridge_ar1']:.4f} | {r['errors_pp']['persistence']:+.2f} |" for r in rows)
    paper = f'''# When a simple inflation forecast survives stricter evidence

Prasanna K | Economic research portfolio | Prepared 17 October 2026

## Result and decision

On 18 held-out monthly releases, July 2024-December 2025, development-selected persistence has RMSE {m['persistence']['rmse_pp']:.4f} percentage points (pp), versus {m['ridge_ar1']['rmse_pp']:.4f} for a fixed Ridge AR(1). The primary paired squared-error difference, AR(1) minus persistence, is {contrast['mean']:.6f} pp squared; its conditional 95% circular-block percentile interval is [{ci[0]:.6f}, {ci[1]:.6f}]. Retain the already selected persistence baseline for this old-base experiment. The test does not trigger model reselection, retuning or a claim about present-day inflation forecasting.

## Measurement before modelling

The release-vintage dataset contains 48 consecutive official PIB/MoSPI releases, January 2022-December 2025, and 144 distinct old-base (2012=100) Combined headline year-on-year observations: current provisional, previous-month final and prior-year reference. Seven of 47 available provisional-to-next-release-final comparisons change, by at most 0.10 pp. Rural, Urban, food, levels and new-base observations cannot enter the headline target by label similarity. Identical desktop/mobile HTML tables are collapsed only after all nine numerical values agree.

Each record carries its reference month, base, metric, sector, status, source URL, exact table-cell XPath, source SHA256 and printed PIB timestamp with IST offset. A forecast is cut one minute after the previous month's release. The as-of query selects only a matching base/metric/sector observation published by that time. A value first disclosed in the target release is unavailable even when it describes the preceding month.

These are retrospectively retrieved, publication-dated documents, not cryptographically authenticated contemporaneous web snapshots. Later document editing cannot be ruled out. Five attached official PDF tables reconcile to the HTML values and were visually checked; this is source agreement, not external independent review. Source content remains attributed to its publisher and is not relicensed with code.

## Frozen design

Training uses 23 pairs, February 2022-December 2023, constructed from first-provisional targets and the previous release's observed lag. Standardization is fitted only on training data. The sole challenger is a Ridge regression of inflation on its lag, alpha 1, with intercept. There is no parameter or lag search, no macro feature whose vintage is unknown, and no refit after December 2023. A separate one-dimensional penalized closed form reconciles the fitted coefficient and intercept.

Development comprises six releases, January-June 2024. Persistence RMSE is {development['metrics']['persistence']['rmse']:.4f}; seasonal-12-month RMSE is {development['metrics']['seasonal_12month']['rmse']:.4f}; AR(1) RMSE is {development['metrics']['ridge_ar1']['rmse']:.4f}. Persistence wins the predeclared selection rule. Eleven frozen file hashes cover protocol, extraction/core/training code, source manifest, panel, model, development results and the 18 final predictions. The evaluation plan fixes 2,000 circular moving-block draws of three monthly dates, seed 20261017, before first final scoring. No outcome is used to revise these choices.

## Held-out performance

Error is forecast minus first-provisional target; positive error means overprediction. MAE, RMSE and signed error use pp, not relative percentage changes. Seasonal-12-month remains a diagnostic comparator; it cannot replace the development-selected baseline after the test.

| Frozen method | MAE (pp) | RMSE (pp) | Mean error (pp) |
|---|---:|---:|---:|
{metric_table}

The primary interval resamples paired errors jointly by release date. It is conditional on this short panel, fixed model and block choice. Eighteen dependent dates and six development dates cannot support a universal superiority claim, reliable regime-specific uncertainty or calibrated individual prediction intervals. The interval is not an inflation forecast range.

## Where the errors arise

AR(1) error equals the persistence lag error plus its model adjustment away from the last observed release. Mean persistence lag error is {decomposition['mean_lag_error_pp']:+.6f} pp; the average AR(1) adjustment is {decomposition['mean_model_adjustment_pp']:+.6f}, summing to AR(1)'s mean error {decomposition['mean_ar1_error_pp']:+.6f}. Its MSE decomposes into lag component {decomposition['mse_lag_component']:.6f}, model-adjustment component {decomposition['mse_model_adjustment_component']:.6f} and cross term {decomposition['mse_cross_component']:+.6f}, summing to {decomposition['mse_total']:.6f}. This is an exact arithmetic identity, not causal attribution to food prices, policy or another driver.

The fixed regression shrinks predictions toward its high-inflation 2022-23 training environment. This is a plausible explanation of its positive adjustment during subsequent lower inflation, not a separately identified causal effect. Year subsets are descriptive only and are not used to choose another model. Their exact scores are in final.json.

## Quantifying hindsight and revisions

Replacing each previous-month provisional lag with its final value, disclosed only with the target release, changes four final-period predictions. The largest change is {final['hindsight_diagnostic']['max_abs_forecast_change_pp']:.6f} pp. With the same frozen coefficients, contaminated AR(1) RMSE is {final['hindsight_diagnostic']['metrics_same_frozen_ar1_with_unavailable_final_lag']['rmse_pp']:.6f}, versus honest {m['ridge_ar1']['rmse_pp']:.6f}; MSE changes by {final['hindsight_diagnostic']['mse_change_contaminated_minus_honest']:+.6f}. Here contamination makes accuracy look slightly better. That direction was not assumed in advance and is not a general law.

A separate later-final-target evaluation changes four of 18 targets, with maximum absolute revision 0.10 pp. Persistence RMSE is {final['later_final_target_diagnostic']['metrics']['persistence']['rmse_pp']:.6f} on that different target. This does not replace the first-release primary score. December 2025's old-base final 1.33 is verified in the pinned February 2026 release as auxiliary evidence; it is not silently added to the sealed vintage panel.

## Series break and stopping rule

The 12 February 2026 release starts base 2024=100. January 2026 new-base headline inflation is 2.75%, while the separate December 2025 final old-base headline is 1.33%. Changes in basket, weights and classification mean these cannot be joined by a cosmetic rescaling. New-base 2025 backcasts first published in 2026 are not available at 2025 origins. This study stops its primary target at December 2025. It does not issue a current October 2026 forecast or claim validation on the new base.

## Reproduction and failure checks

Restore pinned sources if necessary, run the source audit and seven boundary tests, verify the 11 frozen hashes, then run evaluate_final.py and report_final.py. Every primary target, lag, seasonal input and later-final comparison is traced to its numerical HTML cell; the last final uses a separately verified row. Failure checks reject missing vintage/base/timezone, conflicting cells and unavailable values; future revisions leave prior queries unchanged. Two evaluation outputs reproduce byte for byte from the fixed panel in the recorded environment. This is local reproduction, not independent external replication or cross-platform proof.

## Full final release ledger

| Target month | Forecast cutoff (IST) | First target (%) | Persistence (%) | AR(1) (%) | Persistence error (pp) |
|---|---|---:|---:|---:|---:|
{full_table}

## Sources

The complete 49-document official URL/hash ledger is data/source_manifest.json. Observation-level locators are in data/processed/vintages.json and reports/final.json. Five PDF comparisons are documented in reports/source_spot_checks.json. The base-break and final old-base row are in reports/base_break.json and reports/base_break_evidence.json. These are government statistical releases, not third-party numeric summaries. Study protocol and fixed evaluation plan are preserved separately; no raw document is passed off as original research.
'''
    (ROOT/'reports/RESEARCH_PAPER.md').write_text(paper)
    last=rows[-1]
    brief=f'''# December 2025 CPI: a reconstructed forecast and its audit

Prepared 17 October 2026. Historical forecast cutoff: {last['forecast_cutoff']}. This is a retrospective publication-aware reconstruction, not a brief actually issued on that date and not a current forecast.

## Page 1 - Information available at the historical cutoff

The target is the next first-provisional All-India Combined headline year-on-year CPI inflation release, old base 2012, for December 2025. The latest release at the cutoff was November 2025, published 12 December 2025 at 16:00 IST, with headline inflation 0.71%. Frozen selected persistence therefore forecasts **0.71%**. The fixed AR(1) predicts **{last['forecasts']['ridge_ar1']:.4f}%** and the seasonal diagnostic **5.22%**; model disagreement is not a calibrated probability interval.

The baseline was selected on January-June 2024 development results, RMSE 0.2948 pp across only six releases. No reliable 80% or 95% prediction range is established by that sample. A decision maker should avoid treating the point estimate as a tight range. Later revisions and new-base backcasts are absent from this historical information set. The source is {last['lag_source']['source_url']}, exact cell {last['lag_source']['cell_xpath']}.

## Page 2 - After-release audit and error decomposition

The first December target, released {last['target_publication']}, was **{last['first_provisional_actual']:.2f}%**, leaving persistence error **{last['errors_pp']['persistence']:+.2f} pp** and AR(1) error **{last['errors_pp']['ridge_ar1']:+.4f} pp**. For this date, AR(1) error = persistence error ({last['errors_pp']['persistence']:+.2f}) + adjustment away from the observed lag ({last['forecasts']['ridge_ar1']-last['forecasts']['persistence']:+.4f}). The identity explains forecast mechanics, not inflation causes.

Across all 18 final releases, persistence RMSE is 0.8185 pp versus AR(1) 1.6901. The paired squared-error difference is 2.1865 pp squared, with conditional block-bootstrap 95% interval [0.6137, 3.8166]. This summarizes retrospective average-error uncertainty; it is not an interval for this forecast. The larger final error than development error is evidence against assuming stable forecast precision.

Four unavailable lag-final revisions slightly improve apparent AR(1) MSE by 0.01582 pp squared in aggregate. Four target revisions separately change the estimand; they do not replace the primary provisional result. Do not bridge December old-base 1.33% to January new-base 2.75% as a continuous monthly series. Stop this study at December 2025; evaluate any new-base model separately. Short samples, possible later web edits and no external independent review limit conclusions.
'''
    (ROOT/'reports/FORECAST_BRIEF.md').write_text(brief)
    OUT.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Cover',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=colors.HexColor('#173c58'),spaceAfter=16))
    styles.add(ParagraphStyle(name='Deck',fontName='Helvetica',fontSize=11,leading=16,textColor=colors.HexColor('#425866'),spaceAfter=14))
    styles['BodyText'].fontName='Helvetica';styles['BodyText'].fontSize=9.4;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9
    styles['Heading2'].fontSize=13;styles['Heading2'].leading=17;styles['Heading2'].textColor=colors.HexColor('#173c58');styles['Heading2'].spaceBefore=10;styles['Heading2'].spaceAfter=9
    def p(t,style='BodyText'):return Paragraph(t.replace('&','&amp;'),styles[style])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d6e1e5'));canvas.line(44,39,551,39)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526571'))
        canvas.drawString(44,26,'Prasanna K | CPI release-vintage research | 17 October 2026')
        canvas.drawRightString(551,26,str(doc.page));canvas.restoreState()
    def document(path,story):
        SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=44,rightMargin=44,topMargin=43,bottomMargin=52).build(story,onFirstPage=footer,onLaterPages=footer)
    def tbl(data,widths):
        t=Table([[p(str(c)) for c in row] for row in data],colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf1f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#a8bec8')),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6)]))
        return t
    story=[p('When a simple inflation forecast survives stricter evidence','Cover'),p('A release-aware, frozen evaluation of Indian headline CPI inflation. Old base 2012; July 2024-December 2025 final test.','Deck'),p('Prasanna K | Economic research portfolio | Prepared 17 October 2026'),p('Decision','Heading2'),p('Retain development-selected persistence for this bounded old-base experiment. Its held-out RMSE is <b>0.819 pp</b>, versus <b>1.690 pp</b> for the fixed Ridge AR(1). The complex challenger does not earn adoption.'),tbl([['Method','MAE (pp)','RMSE (pp)','Bias (pp)']]+[[k,f"{v['mae_pp']:.4f}",f"{v['rmse_pp']:.4f}",f"{v['mean_error_pp']:+.4f}"]for k,v in m.items()],[177,105,110,115]),p('Evidence strength','Heading2'),p('Primary paired MSE contrast, AR(1) minus persistence: <b>2.186524 pp squared</b>. Conditional 95% moving-block interval: <b>[0.613693, 3.816555]</b>. All 18 release dates are held out from fitting and development selection. Two thousand circular draws use three-month blocks and seed 20261017.'),p('This is uncertainty about average error in a short dependent panel, not a prediction interval or a guarantee about new-base/current forecasting. Publication-dated documents were retrieved retrospectively and may have been edited.'),p('Research contribution','Heading2'),p('A reusable, audited vintage panel; explicit information timing; numerical measurement of hindsight contamination; a rejected challenger; and a stopping rule at the 2026 basket/base break.'),PageBreak()]
    story += [p('1. Measurement and frozen design','Cover'),p('48 official monthly releases yield 144 old-base observations: current provisional, previous-month final and prior-year reference. Every value carries a source hash, exact HTML cell and publication timestamp. Seven of 47 revision pairs change, by at most 0.10 pp.'),p('What the forecast may know','Heading2'),p('Cutoff is one minute after the previous reference month\'s printed PIB publication timestamp, with IST offset. An as-of query must match reference month, base 2012, headline YoY and Combined sector. It cannot use a final revision first published with the target release. Missing or conflicting evidence fails rather than becomes zero.'),p('Training and selection','Heading2'),p('Training: 23 lag/target pairs, February 2022-December 2023. The feature standardizer is fitted only on training observations. Challenger: Ridge AR(1), alpha 1, intercept, no parameter search. Coefficients remain fixed through the entire test; observed lags update when available.'),p('Development: six releases, January-June 2024. Persistence RMSE 0.2948, seasonal-12-month 0.8897, AR(1) 0.5969. The predeclared development rule selects persistence. Final: July 2024-December 2025, 18 releases. No test-based reselection, refit or recalibration occurs.'),p('Audit contract','Heading2'),p('Eleven protected hashes seal protocol, source manifest, data, scientific code, fitted coefficients, development results and final predictions. The evaluation plan is fixed before first final scoring. A separate closed form reconciles the one-variable penalized regression. Five attached official PDFs reconcile with the HTML and were visually checked.'),p('These checks establish source consistency and local reproducibility, not external independent review. They do not authenticate web content as it existed on each original release date.'),PageBreak()]
    story += [p('2. Results and error mechanics','Cover'),Image(str(ROOT/'reports/diagnostics.png'),width=507,height=341.45),p('Arithmetic decomposition','Heading2'),p(f"AR(1) error = last-release lag error + adjustment away from that lag. Mean lag error is {decomposition['mean_lag_error_pp']:+.4f} pp; mean model adjustment {decomposition['mean_model_adjustment_pp']:+.4f}; total mean error {decomposition['mean_ar1_error_pp']:+.4f}. The fixed training environment was substantially above subsequent low observations, so shrinkage can move a forecast in the wrong direction."),p(f"MSE decomposition: lag {decomposition['mse_lag_component']:.6f} + adjustment {decomposition['mse_model_adjustment_component']:.6f} + cross term {decomposition['mse_cross_component']:+.6f} = {decomposition['mse_total']:.6f} pp squared. This is an exact identity, not causal inflation attribution."),p('No regime was chosen after seeing the test. The full 18-date prediction/source ledger, yearly descriptive slices and decomposition are in the accompanying JSON and Markdown paper.'),PageBreak()]
    story += [p('3. Hindsight, revisions and the base break','Cover'),p('Unavailable revised lag','Heading2'),p('For each final forecast, replace only the previous-month lag with the final value disclosed in the target release; hold the regression coefficients fixed. Four predictions change. Maximum absolute forecast change is 0.057558 pp. Contaminated AR(1) RMSE is 1.685431 versus honest 1.690117; MSE falls by 0.015820 pp squared. This small apparent improvement does not validate using unavailable information or rescue the challenger.'),p('A different target is a separate question','Heading2'),p('Four first-provisional targets differ from their next-release final values. Persistence RMSE on those later-final targets is 0.817360 pp versus 0.818518 on the primary targets. Preserve both estimands. December 2025 final old-base 1.33% is independently traced to the pinned February 2026 source row as auxiliary evidence, outside the frozen 144-row panel.'),p('Do not splice measurement systems','Heading2'),p('The 12 February 2026 release starts base 2024=100 and reports January headline 2.75%. The old-base December final 1.33% appears separately. Basket, weight and classification changes make a cosmetic rescaling inappropriate. Backcast 2025 new-base history first published in 2026 cannot enter a 2025 information set.'),p('Stopping rule','Heading2'),p('The primary study ends in December 2025. A new-base study needs separately justified history and future evaluation. No current October 2026 forecast, monetary-policy effect, investment recommendation or ongoing automation is claimed.'),p('Limits','Heading2'),p('Only 23 training pairs, six development releases and 18 dependent test dates; conditional bootstrap uncertainty; publication-dated reconstruction; no official archived-as-of attestation; no external independent replication. Simple forecasts can still have economically material errors.'),PageBreak()]
    sources=json.loads((ROOT/'data/source_manifest.json').read_text())
    story += [p('4. Reproduction and source trail','Cover'),p('Use pinned cached source bytes and pinned requirements. Restore data/raw_sources.tar.xz with scripts/restore_sources.py if required. Run the seven boundary tests, then scripts/evaluate_final.py and scripts/report_final.py. Do not overwrite the original freeze to make an edited model look predeclared.'),p('Checked failure modes','Heading2'),p('Timezone-required timestamps; equality at publication; one-minute-late revision excluded; unavailable month/base rejected; conflicting values rejected; exact duplicates deduplicated; future data unable to alter earlier queries; source-cell equality; independent baseline/regression arithmetic; no training labels from the final period.'),p('Evidence files','Heading2'),p('data/source_manifest.json: all 49 document URLs, hashes and retrieval dates. data/processed/vintages.json: 144 cell-level observations. reports/model_freeze.json: 11 scientific guards. reports/final.json: metrics, paired contrast, every final prediction and source. reports/error_decomposition.json: exact additive identities. reports/source_spot_checks.json: five PDF/HTML checks. reports/final_verification.json: evaluation assertions.'),p('Primary sources','Heading2'),p('PIB / Ministry of Statistics and Programme Implementation monthly CPI releases. Publisher statistical content remains separately attributed; no broader redistribution license is asserted. Representative first source and final source are below; the complete ledger is supplied with the project.'),p(sources[0]['url']),p(sources[-2]['url']),p(sources[-1]['url']),p('The accompanying two-page brief explicitly separates the reconstructed historical information set from the later outcome audit. It is prepared in October 2026 and is never backdated as a publication made in December 2025.')]
    document(OUT/'P6_Inflation_Research_Paper.pdf',story)
    brief_story=[p('December 2025 CPI','Cover'),p('Historical forecast reconstruction','Deck'),p('Prepared 17 October 2026. Historical information cutoff: <b>12 December 2025, 16:01 IST</b>. This brief was not actually issued on that historical date and is not a current forecast.'),p('1 | What was available at the cutoff','Heading2'),p('Target: the next first-provisional All-India Combined headline year-on-year CPI inflation rate, December 2025, old base 2012. The most recent monthly release was November, published on 12 December 2025 at 16:00 IST, reporting 0.71%.'),tbl([['Frozen method','December forecast'],['Selected persistence','0.71%'],['Fixed Ridge AR(1)',f"{last['forecasts']['ridge_ar1']:.4f}%"],['Seasonal diagnostic','5.22%']],[285,222]),p('Recommendation at this historical cutoff','Heading2'),p('Use the already selected persistence point forecast as the transparent reference. Do not treat agreement with a later release as known, substitute a later revised lag or refit the challenger after seeing its test error.'),p('Uncertainty that can be defended','Heading2'),p('The six-release development RMSE was 0.2948 pp. Six dates are insufficient to establish a reliable 80% or 95% prediction range, and model disagreement is not a probability interval. Keep uncertainty explicit instead of presenting an unsupported tight band.'),p('Source and timing','Heading2'),p(last['lag_source']['source_url']),p('November 2025 provisional Combined headline, table cell td[5] in the pinned general-inflation row. Source hash and full XPath are in the forecast ledger. Later revisions and 2026 new-base backcasts are absent from this information set.'),PageBreak(),p('After-release audit','Cover'),p('2 | Outcome, error and stopping rule','Deck'),p(f"The first target was released on 12 January 2026 at 16:00 IST: <b>{last['first_provisional_actual']:.2f}%</b>. Persistence error is <b>{last['errors_pp']['persistence']:+.2f} pp</b>; AR(1) error is <b>{last['errors_pp']['ridge_ar1']:+.4f} pp</b>. Positive error means overprediction."),p('Error decomposition','Heading2'),p(f"For this date, AR(1) error = lag error ({last['errors_pp']['persistence']:+.2f}) + model adjustment ({last['forecasts']['ridge_ar1']-last['forecasts']['persistence']:+.4f}) = {last['errors_pp']['ridge_ar1']:+.4f} pp. This explains model arithmetic; it does not identify the economic causes of inflation."),p('What the complete held-out panel says','Heading2'),p('Across 18 final releases, persistence RMSE is 0.8185 pp and AR(1) RMSE 1.6901. The paired squared-error difference is 2.1865 pp squared, conditional block-bootstrap 95% interval [0.6137, 3.8166]. This is uncertainty about retrospective mean loss, not a range for one future inflation print. Final errors exceed development errors, warning against assuming stable precision.'),p('Hindsight and measurement risk','Heading2'),p('Four unavailable lag-final revisions slightly improve the challenger\'s apparent MSE by 0.01582 pp squared. Target revisions are evaluated separately. Neither operation changes the primary first-release result or the previously selected baseline.'),p('Stop at the base break','Heading2'),p('Do not treat old-base December final 1.33% and new-base January 2.75% as a continuous same-definition monthly series. The 2026 basket/base change requires its own study. No current October 2026 forecast follows from this experiment.'),p('Limits','Heading2'),p('Short dependent panel; publication-dated reconstruction rather than immutable historic snapshots; no calibrated per-forecast interval; no independent external review. Full sources, cell locators and errors accompany the research paper.')]
    document(OUT/'P6_December_2025_Forecast_Brief.pdf',brief_story)
    print(json.dumps({'paper':str(OUT/'P6_Inflation_Research_Paper.pdf'),'brief':str(OUT/'P6_December_2025_Forecast_Brief.pdf'),'error_decomposition':decomposition},indent=2))


if __name__=='__main__':
    run()
