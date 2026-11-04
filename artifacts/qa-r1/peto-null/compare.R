a <- readRDS('artifacts/qa-r1/peto-null/before.rds')
b <- readRDS('artifacts/qa-r1/peto-null/after.rds')
for (method in names(a)) {
 # Calls contain library-specific paths only outside the held result; compare every fit field.
 left <- a[[method]]$fit; right <- b[[method]]$fit
 left$data <- right$data <- NULL # captured execution environments include presentation and timing
 left$time <- right$time <- NULL # elapsed runtime
 stopifnot(identical(left, right))
 cat(method, ': every fitted field identical\n')
 cat('heading before:', a[[method]]$heading, '\nafter:', b[[method]]$heading, '\n')
 print(a[[method]]$display); print(b[[method]]$display)
}
