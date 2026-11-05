"""Prove full-precision data invariance under original/current plot producers.

This is a supplemental real-R data proof, not a Linux replacement for Windows
pixels. Windows-only raster comparisons are performed by check_windows.py.
"""
from pathlib import Path
import json,os,subprocess
os.environ['QT_QPA_PLATFORM']='offscreen'
root=Path.cwd();here=root/'artifacts/batch7-windows';work=root/'build/batch7-coordinate-proof';work.mkdir(exist_ok=True)
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work)
from PyQt6.QtWidgets import QApplication
from rc_metastudio import r_bridge
from tests.analysis_regression.golden.support.golden_analysis import curated_golden_bundles
from tests.analysis_regression.golden.support.headless_analysis import run_headless_analysis
app=QApplication([]);r_bridge.RLibraryLoader().load_rcmetar()
files=['forest_metafor.R','forest_summary.R','forest_layout_preflight.R','plotting.R']
for name in files:(work/name).write_bytes(subprocess.check_output(['git','show','a1ae1b49:r/RCMetaR/R/'+name]))
r_bridge.ro.globalenv['proof_sources']=[str(work/f) for f in files]
r_bridge.ro.r('''ns<-asNamespace("RCMetaR"); oldenv<-new.env(parent=ns)
for (p in proof_sources) sys.source(p,envir=oldenv)
keys<-intersect(ls(oldenv,all.names=TRUE),ls(ns,all.names=TRUE))
keys<-keys[vapply(keys,function(k)is.function(get(k,oldenv)),logical(1))]
current<-mget(keys,ns); original<-mget(keys,oldenv)
install <- function(values) for(k in names(values)) {unlockBinding(k,ns);assign(k,values[[k]],ns);lockBinding(k,ns)}
nums<-function(x,path="") {
 if(inherits(x,"numeric_version"))return(list())
 if(is.numeric(x))return(setNames(as.list(as.vector(x)),paste0(path,"[",seq_along(x),"]")))
 if(isS4(x))x<-setNames(lapply(slotNames(x),function(s)slot(x,s)),slotNames(x))
 if(!is.list(x))return(list())
 out<-list();for(i in seq_along(x)){key<-if(length(names(x))&&nzchar(names(x)[i]))names(x)[i] else as.character(i);if(key=="time")next;out<-c(out,nums(x[[i]],paste0(path,"/",key)))};out
}
''')
rows=[]
try:
 for bundle in curated_golden_bundles(root):
  for version in ['original','current']:
   r_bridge.ro.r('install('+version+')')
   result=run_headless_analysis(bundle['case']);paths=list(result.image_params_paths.values());assert paths
   r_bridge.ro.globalenv['proof_path']=str(paths[0])+'.plotdata'
   r_bridge.ro.r(version+'_state<-new.env();load(proof_path,envir='+version+'_state)')
  check=json.loads(str(r_bridge.ro.r('''local({
    a<-original_state$plot.data;b<-current_state$plot.data
    fields<-names(a)
    checks<-lapply(fields,function(k){x<-nums(a[[k]]);y<-nums(b[[k]]);stopifnot(identical(x,y));list(field=k,numeric_leaves=length(x),identical=TRUE)})
    jsonlite::toJSON(list(passed=TRUE,fields=checks),auto_unbox=TRUE)
  })''')[0]));rows.append(dict(id=bundle['id'],**check));print(bundle['id'],'PASS',flush=True)
finally:r_bridge.ro.r('install(current)')
(here/'data-coordinates-proof.json').write_text(json.dumps(dict(passed=True,base='a1ae1b49',cases=rows),indent=2)+'\n')
