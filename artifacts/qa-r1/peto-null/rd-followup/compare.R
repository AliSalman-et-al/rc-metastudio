a<-readRDS('artifacts/qa-r1/peto-null/rd-followup/before.rds');b<-readRDS('artifacts/qa-r1/peto-null/rd-followup/after.rds')
stopifnot(identical(names(a),names(b)))
for(k in names(a)) {
 stopifnot(identical(a[[k]]$fit,b[[k]]$fit),identical(a[[k]]$weights,b[[k]]$weights))
 cat(k,': all fitted fields and weights exactly identical\n')
 cat('Gamma weight:',b[[k]]$weights[3],'; plotted before/after:',a[[k]]$plotted_weights[3],b[[k]]$plotted_weights[3],'; label:',a[[k]]$method_label,'->',b[[k]]$method_label,'\n')
 if(k=='RD binary.fixed.mh') {
 stopifnot(!b[[k]]$not_estimable[3],b[[k]]$display$y.disp[3]==0,
           identical(as.numeric(b[[k]]$plotted_weights),as.numeric(b[[k]]$weights)))
 }
}
