root <- 'artifacts/batch7/receipts'
pairs <- list(continuous=c('before-continuous','after-continuous'), amino=c('before-amino','after-amino'))
numbers <- function(x, path='') {
 if (is.numeric(x)) return(setNames(as.list(as.vector(x)),paste0(path,'[',seq_along(x),']')))
 if (inherits(x, 'numeric_version')) return(list())
 if (isS4(x)) x <- setNames(lapply(slotNames(x), function(s) slot(x,s)),slotNames(x))
 if (!is.list(x)) return(list())
 out<-list()
 for(i in seq_along(x)) {
  key<-if(length(names(x)) && nzchar(names(x)[i])) names(x)[i] else as.character(i)
  if (key == 'time') next # elapsed runtime is not a fitted value
  out<-c(out,numbers(x[[i]],paste0(path,'/',key)))
 }
 out
}
for (sample in names(pairs)) for (ext in c('res','plotdata')) {
 get <- function(run) {
  e<-new.env(); f<-Sys.glob(file.path(root,run,'workflow/analysis',paste0('*.',ext)));stopifnot(length(f)>=1);load(sort(f)[1],e);numbers(as.list(e))
 }
 a<-get(pairs[[sample]][1]);b<-get(pairs[[sample]][2]);stopifnot(identical(a,b));cat(sample,ext,length(a),'numeric fields IDENTICAL\n')
}
