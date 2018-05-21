#!/usr/bin/python

# Scott Hazelhurst, University of the Witwatersrand
# (C) 2014. Released under GPL 2 licence.

import sys
import re
import os
import string
import argparse
import glob


def guessQparts(qname):
    m1 = re.search("(.*)(\..*).Q",qname)
    m2 = re.search("(.*)(-\d+)\.outfile",qname)
    m3 = re.search("(.*)\.outfile",qname)
    suf=".outfile"
    if m1:
        K=m1.group(2)
        B=m1.group(1)
        suf=".Q"
    elif m2:
        K=m2.group(2)
        B=m2.group(1)
    elif m3:
        K=""
        B=m3.group(1)
    else:
        K=""
        B=qname
    return (B,K,suf)


def parseArguments():
    parser = argparse.ArgumentParser(description='sort fam and Q files')
    parser.add_argument('fam', metavar='FAM', type=str, 
                   help='fam file name')
    parser.add_argument('phe', metavar='PHE', type=str, 
                   help='phenotype file name'),
    parser.add_argument('--poplist', metavar='POPS', dest="poplist",type=str, 
                   help='list of populations comma separated (default all)',
                   default = ""),
    parser.add_argument('--show-pops-q', dest="show_pop",\
                   action="store_true", default=False,\
                   help='show pops vals'),
    parser.add_argument('Q', metavar='Q', nargs='+',
                   help='Q file name')
    parser.add_argument('--clumpp', dest="clumpp", 
                    action="store_true",default=False,
                   help='Set if a CLUMPP Q file')
    parser.add_argument('--debug',dest="debug",
                        action="store_true",default=False,
                        help="show the chosen pops and Q vals")
    parser.add_argument('--sort-multi-prettily', dest="prettily", 
                    action="store_true",default=False,
                   help='sort multiple Q files sorting for aesthetic value')
    parser.add_argument('--sort-multi-consistently', dest="consistently", 
                    action="store",default="",
                   help='sort multiple Q files consistenly with a fam file (key Q file)')
    parser.add_argument('--output', dest='output', action='store',
                   default = "", 
                        help='output name (default is append _new) ')
    parser.add_argument('--popcol', dest='popcol', action='store',
                   default = -1, type=int, 
                        help='column in popfile (number from 0) default is -1 (rightmost ')
    parser.add_argument('--column-for-order', dest="ordercol",
                        action="store",default=0,
                        help="Use this colour for order"),
    parser.add_argument('--likeness-order', dest="likeness", 
                    action="store_true",default=False,
                   help='sort on closeness to each other')
    args = parser.parse_args()
    if args.prettily and args.consistently:
        sys.exit("Can only specify at most one of sort-multi-prettily and sort-multi-consistently")
    if not(args.prettily or args.consistently):
        if len(args.Q)>1 or len(glob.glob(args.Q[0]))>1:
           sys.exit("Must specify one sort-multi-prettily and sort-multi-consistently for multiple Q files")
    return args
        



def showpopqs(sum):
    tot=0
    for s in sum:
        tot=tot+s
    if tot==0: return None
    return map(lambda x:1.0*x/tot,sum)

def fst(x): return x[0]

def findQweights(tosort_i,qdata):
    sum = [0]*len(qdata[0])
    for qi in tosort_i:
        for (i,v) in enumerate(qdata[qi]):
            sum[i]=sum[i]+float(v)
    if args.show_pop:
        weights =  showpopqs(sum)
    else:
        weights=\
          map(fst,sorted(list(enumerate(sum)),key=lambda x : x[1],reverse=True))
    return weights



def reorder(tosort_i,qdata,weights):
      return\
         sorted(tosort_i, 
              key=lambda x : (qdata[x][weights[0]],qdata[x][weights[1]]))


def orderColFn(col):
    def theOrder(tosort_i,qdata,weights):

      return \
         sorted(tosort_i, \
                key=lambda x : (qdata[x][col],qdata[x][col]))
    col = int(col)-1
    return theOrder


def cdist(qdata,i,j):
    sum=0
    for u in range(len(qdata[0])):
        sum=sum+(abs(qdata[i][u]-qdata[j][u]))**1.5
    return sum

def sortLikeness(tosort_i,qdata,weights):
    """Sort them so that the closest coloured are together"""
    NS=len(tosort_i)
    mdist=0
    for (i,v) in enumerate(tosort_i):
        print ".",
        sys.stdout.flush()
        for (j,w) in enumerate(tosort_i,start=i+1):
            curr=cdist(qdata,v,w)
            if curr>mdist:
                mdist=curr
                the_maxes=(v,w)
    (left,right)=the_maxes
    done=list(the_maxes)
    slist=[left]
    window=[left]
    # 
    for k in range(NS-2):
        mindist=mdist*NS
        print ".",
        sys.stdout.flush()
        for (i,u) in enumerate(tosort_i):
            if u not in done:
                curr=0
                for x in window:
                  curr=curr+cdist(qdata,x,u)
                if curr<=mindist:
                    #print "updating",curr
                    mindist=curr
                    themin=u
                #else:
                #    print "   ",curr
        slist.append(themin) # not redundant -- may change alg
        left=themin
        done.append(themin)
        window.append(themin)
        if len(window)>30:
            del window[0]
    slist.append(right)
    return slist


def j(x):
    return "%s\n"%string.join(map(str,x),sep="\t")




def outputQF(q,famdata,qdata,tosort_i,sorted_i):
    (B,K,suf) = guessQparts(q)
    if args.output:
      args.outfam = "%s.fam"%args.output
      args.outQ   = "%s%s%s"%(args.output,K,suf)
    else:
      args.outfam = "%s_srt.fam"%B
      args.outQ   = "%s_srt%s%s"%(B,K,suf)
    famf = open(args.outfam,"w")
    qf   = open(args.outQ,"w")
    k=0
    for i in range(len(famdata)):
        if i == tosort_i[k]:
            famf.write(j(famdata[sorted_i[k]]))
            qf.write(j(qdata[sorted_i[k]]))
            k=k+1
            if k==len(tosort_i):k=0
        else:
            famf.write(j(famdata[i]))
            qf.write(j(qdata[i]))
    famf.close()
    qf.close()

def outputQ(q,qdata,tosort_i,sorted_i):
    (B,K,suf) = guessQparts(q)
    if args.output:
      outQ   = "%s%s%s"%(args.output,K,suf)
    else:
      outQ   = "%s_srt%s%s"%(B,K,suf)
    qf   = open(outQ,"w")
    k=0
    for i in range(len(qdata)):
        if i == tosort_i[k]:
            #print qdata[sorted_i[k]]
            qf.write(j(qdata[sorted_i[k]]))
            #print j(qdata[sorted_i[k]])
            k=k+1
            if k==len(tosort_i):k=0
        else:
            qf.write(j(qdata[i]))
            #print j(qdata[sorted_i[k]])
    qf.close()


def showDebug(famdata,qdata,allsorted,new_order):
    k=0
    for i in range(len(famdata)):
        if i == allsorted[k]:
            indiv = (famdata[i][0],famdata[i][1])
            print k,"k, %s [%s] %s"%(indiv,pop_indiv[indiv],j(qdata[new_order[k]])),
            k=k+1
            if k==len(allsorted):
               k=0


def print_fam_proper(famdata,q,tosort_i,sorted_i):
    (B,K,suf) = guessQparts(q)
    if args.output:
      outfam = "%s_srt%s.fam"%(args.output,K)
    else:
      outfam = "%s_srt%s.fam"%(B,K)
    famf = open(outfam,"w")
    k=0
    for i in range(len(famdata)):
        if i == tosort_i[k]:
            famf.write(j(famdata[sorted_i[k]]))
            k=k+1
            if k==len(tosort_i):k=0
        else:
            famf.write(j(famdata[i]))
    famf.close()


def print_nothing(famdata,q,tosort_i,sorted_i):
    pass


def readQraw(famname):
   qf = open(famname)
   return qf.readlines()



def readQ(fname):
   qf   = open(fname)
   qdata = []
   for line in qf:
       if args.clumpp:
           data= line.split(":  ")[1].split()
       else:
           data= line.split()
       qdata.append(map(float,data))
   qf.close()
   return qdata


def readPHE(fname):
    phef = open(fname)
    popcat = {}
    pop_indiv = {}
    for x in phef:
        data = x.split()
        the_pop = data[args.popcol]
        if the_pop in popcat:
           popcat[the_pop].append((data[0],data[1]))
        else:
           popcat[the_pop] = [(data[0],data[1])]
        pop_indiv[(data[0],data[1])]=the_pop
    phef.close()
    return (pop_indiv,popcat)


def interleave(old1,new1,old2,new2):
    if len(old2)==0:
        return (old1,new1)
    elif len(old1)==0:
        return (old2,new2)
    if old1[0]<old2[0]:
        (t_old,t_new)=interleave(old1[1:],new1[1:],old2,new2)
        return ([old1[0]]+t_old,[new1[0]]+t_new)
    else:
        (t_old,t_new)=interleave(old1,new1,old2[1:],new2[1:])
        return ([old2[0]]+t_old,[new2[0]]+t_new)



def sortQ(famdata,qdata):
   new_order = []
   allsorted = []
   pops = args.poplist.split(",")
   if args.likeness:
      doOrder=sortLikeness
   elif args.ordercol:
      doOrder=orderColFn(args.ordercol)
   else:
      doOrder=reorder
   for pop in pops:
      tosort   = popcat[pop]
      i=0
      tosort_i = []
      for x in famdata:
         if (x[0],x[1]) in tosort:
             tosort_i.append(i)
         i=i+1
      weights = findQweights(tosort_i,qdata)
      if args.show_pop:
        if weights:
            print "%9s: "%pop,
            for w in weights:
                print "%5.3f"%w,
            print
        continue
      new_order_i = doOrder(tosort_i,qdata,weights)
      (allsorted,new_order)=interleave(tosort_i,new_order_i,allsorted,new_order)

   if args.debug:
       showDebug(famdata,qdata,allsorted,new_order)
       sys.exit(0)
     
   return(allsorted, new_order)







args = parseArguments()

(pop_indiv,popcat) = readPHE(args.phe)
if not args.poplist:
    args.poplist = string.join(popcat.keys(),",")

famdata = []

# read fam file
i=0
famf = open(args.fam)
for x in famf:
    data = x.split()
    famdata.append(data)
famf.close()




qfiles = []
for q in args.Q:
    qfiles = qfiles + glob.glob(q)


if args.consistently:
    qdata = readQ(args.consistently)
    (global_sorted,global_new_order) = sortQ(famdata,qdata)
    def sortAuxQ(famdata,qdata):
       return (global_sorted,global_new_order)
    print_fam_proper(famdata,args.consistently,global_sorted,global_new_order)
    do_sort = sortAuxQ
    print_fam = print_nothing
else:
    print_fam = print_fam_proper
    do_sort = sortQ


for q in qfiles:
   qdata=readQ(q)
   (allsorted,new_order) = do_sort(famdata,qdata)
   if args.show_pop:
       continue
   outputQ(q,qdata,allsorted,new_order)
   print_fam(famdata,q,allsorted,new_order)


# if args.otherq:
#     qfpats = args.otherq.split(",")
#     qfs = []
#     for pat in qfpats:
#         qfs = qfs + glob.glob(pat)
#     for fname in qfs:
#         #if fname == args.Q: continue
#         Q = readQ(fname)
#         outputAuxQ(fname,Q,allsorted,new_order)

