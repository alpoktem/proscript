library(polynom)
library(orthopolynom)

legendre.coeff <- function(x,y,l, xlim=range(x)) {
	a <- (xlim[2] - xlim[1])/2
	b <- xlim[1] + a
	x_ <- (x-b)/a

	n <- length(y) 
	coeffs <- NULL	

	for (i in 1:length(l)) { 
		coeffs <- cbind(coeffs, 2 * sum(y * predict(l[[i]], x_))/n)
	}	
	# Return a vector of coefficients
	#print(coeffs)
	coeffs
}

legendre.var <- function(x,y,xlim) {

	n <- length(y)
	k <- ceiling(n/4)
	l <- legendre.polynomials(length(y), normalized=T)
	coeffs <- legendre.coeff(x,y,l,xlim)
	#print(coeffs)
	v <- 4 * sum(coeffs[(n-k+1):n] * coeffs[(n-k+1):n]) 
	print(v)
	v	
} 

legendre.R <- function(J,x,y,xlim) {
	n <- length(y)
	l <- legendre.polynomials(J, normalize=T)
	coeffs <- legendre.coeff(x,y,l,xlim)  
	v <- legendre.var(x,y,xlim)

	j <- c(1:n) 		
	R <- J*(v/n) + sum(coeffs[J+1:n] - (v * j[J+1:n]))     

	R
}

legendre.choose.R <- function(x,y,xlim) {
	Js <- c(1:length(y))	
	print(Js)
	Rs <- sapply(Js, function(j){legendre.R(j,x,y,xlim)}) 	
	print(Rs)	
	J.min <- which.min(Rs) 	
}

legendre.eval <- function(x, coeffs, l, xlim=range(x)) { 
	a <- (xlim[2] - xlim[1])/2
	b <- xlim[1] + a
	x_ <- (x-b)/a

	y <- 0 	
	for (i in 1:length(l)) {
		y <- y + coeffs[i] * predict(l[[i]], x_)
	}	
	y	
}

legendre.trial <- function() {
	x <- seq(2,10,by=0.001)
	y <- sin(2*x)

	plot(x,y)
	l <- legendre.polynomials(3, normalized = TRUE) 
	g <- legendre.coeff(x,y,l)
	lines(x, legendre.eval(x,g,l), col="orange") 

	g <- legendre.coeff(x,y,l)
	lines(x, legendre.eval(x,g,l), col="orange") 

}





