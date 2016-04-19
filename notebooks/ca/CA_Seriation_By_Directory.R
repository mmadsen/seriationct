install.packages("devtools", dependencies=TRUE)
library(devtools)
library(ca)
library(seriation)
library(plotrix)
library(mmadsenr)

filenameRoot <- function(x){
  substr(x, 0, nchar(x)-4)
}

file_root <- function(x) {
  substr(x,nchar(x)-46,nchar(x)-4)
}
setwd("/Users/clipo/PycharmProjects/seriationct/ca/resample-1/")
file_list <- list_files_for_data_path(directory = "./")
 
for (file in file_list){
  # read data from choosen file
  mydata <- read.table(file, row.names=1, header=T)
  pfg <- data.frame(mydata)
  nrows <- nrow(pfg)
  ncols <- ncol(pfg)
  numb.dim.cols<-ncol(pfg)-1
  numb.dim.rows<-nrow(pfg)-1
  a <- min(numb.dim.cols, numb.dim.rows) #dimensionality of the table
  res.ca<-ca(pfg, nd=a)
  #get the coordinates on the selected CA axis
  row.c<-res.ca$rowcoord[,1]
  col.c<-res.ca$colcoord[,2]
  #sort the table according to the coord of the selected CA dimension and plot seriation chart (Bertin plot)
  print(sorted.table<-pfg[order(row.c), order(col.c)]) #sort the table
  graph_name <- paste(filenameRoot(file),".png")
  png(graph_name)
  dev.copy(png,graph_name)
  battleship.plot(sorted.table, main=file_root(graph_name))
  dev.off()
}

