"""Re-run the actual two golden cases with master/current row-label producers.

Compare every full-precision numeric field in the persisted plot bundles using
R identical(), not displayed rounded strings or numeric tolerances.
"""
from pathlib import Path
import json
import os
import subprocess

root=Path(__file__).resolve().parents[4]
here=Path(__file__).parent
runtime=here/'data-coordinate-runtime'
runtime.mkdir(exist_ok=True)
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(runtime)
os.environ['XDG_CONFIG_HOME']=str(runtime/'config')
from PyQt6.QtWidgets import QApplication
from rc_metastudio import r_bridge
from tests.analysis_regression.golden.support.golden_analysis import curated_golden_bundles
from tests.analysis_regression.golden.support.headless_analysis import run_headless_analysis

app=QApplication([])
r_bridge.RLibraryLoader().load_rcmetar()
source=subprocess.check_output(['git','show','origin/master:r/RCMetaR/R/results_display.R'],cwd=root,text=True)
start=source.index('rcmetar.sequential.labels <- function(')
end=source.index('\n}\n',start)+2
r_bridge.ro.globalenv['master_labels_source']=source[start:end]
r_bridge.ro.r('current_labels <- RCMetaR:::rcmetar.sequential.labels; master_labels <- eval(parse(text=master_labels_source))')
rows=[]
try:
    for bundle in curated_golden_bundles(root):
        if bundle['id'] not in {'amino-binary-leave-one-out','continuous-leave-one-out'}:
            continue
        for version in ['master','current']:
            r_bridge.ro.r(f'assignInNamespace("rcmetar.sequential.labels", {version}_labels, ns="RCMetaR")')
            result=run_headless_analysis(bundle['case'])
            paths=list(result.image_params_paths.values())
            assert len(paths)==1
            r_bridge.ro.globalenv['proof_plotdata_path']=str(paths[0])+'.plotdata'
            r_bridge.ro.r(f'{version}_state <- new.env(); load(proof_plotdata_path, envir={version}_state)')
        result=json.loads(str(r_bridge.ro.r('''local({
            old <- master_state$plot.data; new <- current_state$plot.data
            prefix <- "Study omitted: "
            stopifnot(identical(sub(prefix, "", old$slab, fixed=TRUE), new$slab))
            fields <- c("effect", "effect_display", "weights", "sample_sizes")
            old$effect$slab <- sub(prefix, "", old$effect$slab, fixed=TRUE)
            checks <- setNames(lapply(fields, function(key) identical(old[[key]], new[[key]])), fields)
            fit_fields <- c("b", "beta", "se", "zval", "pval", "ci.lb", "ci.ub", "tau2", "tau2.f", "QE", "QEp", "I2", "H2", "k", "p", "yi", "vi", "weights", "vb", "fit.stats")
            stopifnot(all(vapply(old$res, function(fit) !is.null(fit$b), logical(1))))
            statistics <- function(fits) lapply(fits, function(fit) fit[fit_fields])
            checks$fitted_statistics <- identical(statistics(old$res), statistics(new$res))
            stopifnot(all(unlist(checks)))
            list_rows <- lapply(seq_along(new$slab), function(i) list(
                index=i, old_label=old$slab[[i]], new_label=new$slab[[i]],
                yi=new$effect$yi[[i]], lower=new$effect$ci.lb[[i]], upper=new$effect$ci.ub[[i]],
                se=new$effect$sei[[i]], display_estimate=new$effect_display$y.disp[[i]],
                display_lower=new$effect_display$lb.disp[[i]], display_upper=new$effect_display$ub.disp[[i]]))
            jsonlite::toJSON(list(passed=TRUE, exact_R_identical=checks, row_count=length(new$slab),
                                 rows=list_rows, weights=new$weights),auto_unbox=TRUE,digits=NA,na="null")
        })''')[0]))
        rows.append({'case':bundle['id'],**result})
finally:
    r_bridge.ro.r('assignInNamespace("rcmetar.sequential.labels", current_labels, ns="RCMetaR")')
assert len(rows)==2
(here/'data-coordinates-proof.json').write_text(json.dumps({'passed':True,'cases':rows},indent=2)+'\n')
print('PASS: master/current label producers give R-identical full-precision effects, CIs, SEs, display coordinates, weights and fitted statistics for every row of both actual golden cases.')
