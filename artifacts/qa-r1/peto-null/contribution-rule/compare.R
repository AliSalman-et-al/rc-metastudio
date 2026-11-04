a<-readRDS('artifacts/qa-r1/peto-null/contribution-rule/before.rds')
b<-readRDS('artifacts/qa-r1/peto-null/contribution-rule/after.rds')
stopifnot(identical(names(a),names(b)))
rows<-list()
for(k in names(a)) {
 stopifnot(identical(a[[k]]$fit,b[[k]]$fit),identical(a[[k]]$weights,b[[k]]$weights))
 for(i in 1:6) {
  x<-a[[k]];y<-b[[k]]
  stopifnot(identical(as.numeric(y$weights),as.numeric(y$plotted_weights)))
  w<-as.numeric(y$weights[i]);finite<-is.finite(y$fit$yi.f[i]) && is.finite(y$fit$vi.f[i])
  expected<-!finite && (!is.finite(w) || w<=0)
  stopifnot(identical(y$not_estimable[i],expected))
  display<-function(v) {
   if(v$not_estimable[i]) return('Not estimable')
   sprintf('%.6f [%.6f, %.6f]',v$display$y.disp[i],v$display$lb.disp[i],v$display$ub.disp[i])
  }
  rows[[length(rows)+1]]<-data.frame(fit=k,study=c('Alpha','Beta','Gamma','Delta','Epsilon','Zeta')[i],
    row_before=display(x),row_after=display(y),weight_before=as.numeric(x$weights[i]),weight_after=w,
    not_estimable_before=x$not_estimable[i],not_estimable_after=y$not_estimable[i],
    plotted_weight=if(is.finite(w)) sprintf('%.1f%%',w) else '',
    report_weight=if(is.finite(w)) sprintf('%.1f%%',w) else '')
 }
 cat(k,': all fitted fields and weights exactly unchanged; all six display rows satisfy contribution rule\n')
}
table<-do.call(rbind,rows)
stopifnot(identical(table$row_before,table$row_after),
          identical(table$not_estimable_before,table$not_estimable_after))
write.table(table,'artifacts/qa-r1/peto-null/contribution-rule/ten-fit-table.tsv',sep='\t',row.names=FALSE,quote=FALSE)
gamma<-table[table$study=='Gamma',]
cat('\nDouble-zero Gamma:\n');print(gamma,row.names=FALSE)
