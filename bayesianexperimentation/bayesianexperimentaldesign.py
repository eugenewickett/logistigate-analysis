# -*- coding: utf-8 -*-
'''
Script that generates and analyzes a synthetic set of PMS data. These data differ from the data used in the paper but
capture the important elements of what is presented in the paper.
Inference generation requires use of the logistigate package, available at https://logistigate.readthedocs.io/en/main/.
Running the generateSyntheticData() function generates Figures 2, 3, and 4, as well as the interval widths for Tables
1 and 2, that are analagous to the items produced using the de-identified data.
'''

from logistigate.logistigate import utilities as util # Pull from the submodule "develop" branch
from logistigate.logistigate import methods
from logistigate.logistigate import lg
import numpy as np
from numpy.random import choice
import scipy.special as sps
import scipy.stats as spstat
import scipy.optimize as spo
import matplotlib
import matplotlib.pyplot as plt
import random
import pickle
import time
import math
from math import comb
import matplotlib.cm as cm

# Define computation variables
tol = 1e-8

def balancedesign(N,ntilde):
    '''
    Uses matrix of original batch (N) and next batch (ntilde) to return a balanced design where the target is an even
    number of tests from each (TN,SN) arc for the total tests done
    '''
    n = np.sum(N)
    r,c = N.shape
    D = np.repeat(1/(r*c),r*c)*(n+ntilde)
    D.shape = (r,c)
    D = D - N
    D[D < 0] = 0.
    D = D/np.sum(D)

    return D

def roundDesignLow(D,n):
    '''
    Takes a proposed design, D, and number of new tests, n, to produce an integer tests array by removing tests from
    design traces with the highest number of tests or adding tests to traces with the lowest number of tests.
    '''
    roundMat = np.round(n*D)
    if np.sum(roundMat) > n: # Too many tests; remove from highest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(-roundMat,axis=None).tolist()
        for removeInd in range(int(np.sum(roundMat)-n)):
            roundMat[sortinds[removeInd]] += -1
        if D.ndim == 2:
            roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    elif np.sum(roundMat) < n: # Too few tests; add to lowest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(roundMat, axis=None).tolist()
        for addind in range(int(n-np.sum(roundMat))):
            roundMat[sortinds[addind]] += 1
        if D.ndim == 2:
            roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    return roundMat

def roundDesignHigh(D,n):
    '''
    Takes a proposed design, D, and number of new tests, n, to produce an integer tests array by removing tests from
    design traces with the lowest number of tests or adding tests to traces with the highest number of tests.
    '''
    roundMat = np.round(n*D)
    if np.sum(roundMat) > n: # Too many tests; remove from lowest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(roundMat,axis=None).tolist()
        for removeInd in range(int(np.sum(roundMat)-n)):
            roundMat[sortinds[removeInd]] += -1
        if D.ndim == 2:
            roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    elif np.sum(roundMat) < n: # Too few tests; add to highest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(-roundMat, axis=None).tolist()
        for addind in range(int(n-np.sum(roundMat))):
            roundMat[sortinds[addind]] += 1
        if D.ndim == 2:
            roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    return roundMat

def plotLossVecs(lveclist, lvecnames=[], type='CI', CIalpha = 0.05,legendlabel=[],
                 plottitle='Confidence Intervals for Loss Averages', plotlim=[]):
    '''
    Takes a list of loss vectors and produces either a series of histograms or a single plot marking average confidence
    intervals
    lveclist: list of lists
    type: 'CI' (default) or 'hist'
    CIalpha: alpha for confidence intervals
    '''
    numvecs = len(lveclist)
    # Make dummy names if none entered
    if lvecnames==[]: #empty
        for ind in range(numvecs):
            lvecnames.append('Design '+str(ind+1))
    numDups = 1
    orignamelen = len(lvecnames)
    if orignamelen<len(lveclist): # We have multiple entries per design
        numDups = int(len(lveclist)/len(lvecnames))
        lvecnames = numDups*lvecnames
    # For color palette
    from matplotlib.pyplot import cm

    # Make designated plot type
    if type=='CI':
        lossavgs = []
        lossint_hi = []
        lossint_lo = []
        for lvec in lveclist:
            currN = len(lvec)
            curravg = np.average(lvec)
            lossavgs.append(curravg)
            std = np.std(lvec)
            z = spstat.norm.ppf(1 - (CIalpha / 2))
            intval = z * (std) / np.sqrt(currN)
            lossint_hi.append(curravg + intval)
            lossint_lo.append(curravg - intval)

        # Plot intervals for loss averages
        if lossavgs[0]>0: # We have losses
            xaxislab = 'Loss'
            limmin = 0
            limmax = max(lossint_hi)*1.1
        elif lossavgs[0]<0: # We have utilities
            xaxislab = 'Utility'
            limmin = min(lossint_lo)*1.1
            limmax = 0
        fig, ax = plt.subplots(figsize=(7,7))
        #color = iter(cm.rainbow(np.linspace(0, 1, numvecs/numDups)))
        #for ind in range(numvecs):

        if plotlim==[]:
            plt.xlim([limmin,limmax])
        else:
            plt.xlim(plotlim)
        for ind in range(numvecs):
            if np.mod(ind,orignamelen)==0:
                color = iter(cm.rainbow(np.linspace(0, 1, int(numvecs / numDups))))
            currcolor = next(color)
            if ind<orignamelen:

                plt.plot(lossavgs[ind], lvecnames[ind], 'D', color=currcolor, markersize=6)
            elif ind>=orignamelen and ind<2*orignamelen:
                plt.plot(lossavgs[ind], lvecnames[ind], 'v', color=currcolor, markersize=8)
            elif ind>=2*orignamelen and ind<3*orignamelen:
                plt.plot(lossavgs[ind], lvecnames[ind], 'o', color=currcolor, markersize=6)
            else:
                plt.plot(lossavgs[ind], lvecnames[ind], '^', color=currcolor, markersize=8)
            line = ax.add_line(matplotlib.lines.Line2D(
                 (lossint_hi[ind], lossint_lo[ind]),(lvecnames[ind], lvecnames[ind])))
            line.set(color=currcolor)
            anno_args = {'ha': 'center', 'va': 'center', 'size': 12, 'color': currcolor }
            _ = ax.annotate("|", xy=(lossint_hi[ind], lvecnames[ind]), **anno_args)
            _ = ax.annotate("|", xy=(lossint_lo[ind], lvecnames[ind]), **anno_args)
            #plt.plot((lvecnames[ind], lvecnames[ind]), (lossint_hi[ind], lossint_lo[ind]), '_-',
             #        color=next(color), alpha=0.7, linewidth=3)
        plt.ylabel('Design Name', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
        plt.xlabel(xaxislab, fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontname('Times New Roman')
            label.set_fontsize(12)
        #plt.xticks(rotation=90)
        plt.title(plottitle,fontdict={'fontsize':16,'fontname':'Trebuchet MS'})
        if orignamelen<numvecs: # Add a legend if multiple utilities associated with each design
            import matplotlib.lines as mlines
            diamond = mlines.Line2D([], [], color='black', marker='D', linestyle='None', markersize=8, label=legendlabel[0])
            downtriangle = mlines.Line2D([], [], color='black', marker='v', linestyle='None', markersize=10, label=legendlabel[1])
            if numDups>=3:
                circle = mlines.Line2D([], [], color='black', marker='o', linestyle='None', markersize=8, label=legendlabel[2])
                if numDups>=4:
                    uptriangle = mlines.Line2D([], [], color='black', marker='^', linestyle='None', markersize=10, label=legendlabel[3])
                    plt.legend(handles=[diamond, downtriangle, circle,uptriangle])
                else:
                    plt.legend(handles=[diamond, downtriangle, circle])
            else:
                plt.legend(handles=[diamond, downtriangle],loc='lower right')
        fig.tight_layout()
        plt.show()
        plt.close()
    # HISTOGRAMS
    elif type=='hist':
        maxval = max([max(lveclist[i]) for i in range(numvecs)])
        maxbinnum = max([len(lveclist[i]) for i in range(numvecs)])/5
        bins = np.linspace(0.0, maxval*1.1, 100)
        fig, axs = plt.subplots(numvecs, figsize=(5, 10))
        plt.rcParams["figure.autolayout"] = True
        color = iter(cm.rainbow(np.linspace(0, 1, len(lveclist))))
        for ind in range(numvecs):
            axs[ind].hist(lveclist[ind],bins, alpha=0.5, color=next(color),label=lvecnames[ind])
            axs[ind].set_title(lvecnames[ind])
            axs[ind].set_ylim([0,maxbinnum])
        fig.suptitle(plottitle,fontsize=16)
        fig.tight_layout()
        plt.show()
        plt.close()

    return

def marginalshannoninfo(datadict):
    '''
    Takes a PMS data set and returns a matrix of the Shannon information obtained from a marginal test along each trace;
    for tracked data only
    '''
    tnNum, snNum = datadict['N'].shape
    s, r = datadict['diagSens'], datadict['diagSpec']
    postSamps = datadict['postSamples']

    shannonMat = np.zeros(shape=(tnNum, snNum))

    for samp in postSamps: # Iterate through each posterior sample
        for tnInd in range(tnNum):
            tnRate = samp[tnInd + snNum]
            for snInd in range(snNum):
                snRate = samp[snInd]
                consolRate = tnRate + (1-tnRate)*snRate
                detectRate = s*consolRate+(1-r)*(1-consolRate)
                infobit = detectRate*np.log(detectRate) + (1-detectRate)*np.log(detectRate)
                shannonMat[tnInd,snInd] += infobit

    shannonMat=shannonMat/len(postSamps)
    return shannonMat

def risk_parabolic(SFPratevec, paramDict={'threshold': 0.5}): #### OBSOLETE; REMOVE LATER
    '''Parabolic risk term for vector of SFP rates. Threshold is the top of the parabola. '''
    riskvec = np.empty((len(SFPratevec)))
    for ind in range(len(SFPratevec)):
        currRate = SFPratevec[ind]
        if paramDict['threshold'] <= 0.5:
            currRisk = (currRate+2*(0.5-paramDict['threshold']))*(1-currRate)
        else:
            currRisk = currRate * (1 - currRate - 2*(0.5-paramDict['threshold']))
        riskvec[ind] = currRisk
    return riskvec

def risk_parabolicArr(SFPrateArr, paramDict={'threshold': 0.2}):
    '''Parabolic risk term for vector of SFP rates. Threshold is the top of the parabola. '''
    if paramDict['threshold'] <= 0.5:
        retVal = (SFPrateArr+ 2*(0.5 - paramDict['threshold']))*(1-SFPrateArr)
    else:
        retVal = SFPrateArr * (1 - SFPrateArr - 2*(0.5-paramDict['threshold']))
    return retVal

def risk_parabolicMat(draws,paramDict={'threshold':0.2}, indsforbayes=[]):
    '''Parabolic risk term in matrix form'''
    retArr = risk_parabolicArr(draws,paramDict)
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(len(draws))
    numbayesinds = len(indsforbayes)
    return np.transpose(np.reshape(np.tile(retArr.copy(),numbayesinds),(len(draws),numbayesinds,len(draws[0]))),(1,0,2))

def risk_check(SFPratevec, paramDict={'threshold': 0.5, 'slope': 0.5}): #### OBSOLETE; REMOVE LATER
    '''Check risk term, which has minus 'slope' to the right of 'threshold' and (1-'slope') to the left of threshold'''
    riskvec = np.empty((len(SFPratevec)))
    for i in range(len(SFPratevec)):
        riskvec[i] = (1 - SFPratevec[i]*(paramDict['slope']-(1-paramDict['threshold']/SFPratevec[i]
                      if SFPratevec[i]<paramDict['threshold'] else 0)))
    return riskvec

def risk_checkArr(SFPrateArr, paramDict={'threshold': 0.5, 'slope': 0.5}):
    '''Check risk term for an array, which has minus 'slope' to the right of 'threshold' and (1-'slope') to the left of threshold'''
    return 1 - SFPrateArr*(paramDict['slope']-((1-paramDict['threshold']/SFPrateArr)*np.minimum(np.maximum(paramDict['threshold'] - SFPrateArr, 0),tol)*(1/tol)))

def risk_checkMat(draws, paramDict={'threshold': 0.5, 'slope': 0.5}, indsforbayes=[]):
    '''Check risk term for an array, which has minus 'slope' to the right of 'threshold' and (1-'slope') to the left of threshold'''
    retArr = risk_checkArr(draws,paramDict)
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(len(draws))
    numbayesinds = len(indsforbayes)
    return np.transpose(np.reshape(np.tile(retArr.copy(),numbayesinds),(len(draws),numbayesinds,len(draws[0]))),(1,0,2))

def score_diff(est, targ, paramDict): #### OBSOLETE; REMOVE LATER
    '''
    Returns the difference between vectors est and targ underEstWt, the weight of underestimation error relative to
    overestimation error.
    paramDict requires keys: underEstWt
    '''
    scorevec = np.empty((len(targ)))
    for i in range(len(targ)):
        scorevec[i] = (paramDict['underEstWt']*max(targ[i] - est[i], 0) + max(est[i]-targ[i],0))
    return scorevec

def score_diffArr(est, targArr, paramDict):
    '''
    Returns array of differences between vector est and array of vectors targArr using underEstWt, the weight of
    underestimation error relative to overestimation error.
    paramDict requires keys: underEstWt
    '''
    return np.maximum(est-targArr,0) + paramDict['underEstWt']*np.maximum(targArr-est,0)

def score_diffMat(draws, paramDict, indsforbayes=[]):
    '''
    Returns matrix of pair-wise differences for set of SFP-rate draws using underEstWt, the weight of
    underestimation error relative to overestimation error. Rows correspond to estimates, columns to targets
    paramDict requires keys: underEstWt
    :param indsforbayes: which indices of draws to use as estimates; used for limiting the matrix size
    '''
    numdraws, numnodes = len(draws), len(draws[0])
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(numdraws)
    numbayesinds = len(indsforbayes)
    drawsEstMat = np.reshape(np.tile(draws[indsforbayes].copy(),numdraws),(numbayesinds,numdraws,numnodes))
    drawsTargMat = np.transpose(np.reshape(np.tile(draws.copy(), numbayesinds), (numdraws, numbayesinds, numnodes)),
                                axes=(1, 0, 2))
    return np.maximum(drawsEstMat-drawsTargMat,0) + paramDict['underEstWt']*np.maximum(drawsTargMat-drawsEstMat,0)

def score_class(est, targ, paramDict): #### OBSOLETE; REMOVE LATER
    '''
    Returns the difference between classification of vectors est and targ using threshold, based on underEstWt,
    the weight of underestimation error relative to overestimation error.
    paramDict requires keys: threshold, underEstWt
    '''

    scorevec = np.empty((len(targ)))
    for i in range(len(targ)):
        estClass = np.array([1 if est[i] >= paramDict['threshold'] else 0 for i in range(len(est))])
        targClass = np.array([1 if targ[i] >= paramDict['threshold'] else 0 for i in range(len(targ))])
        scorevec[i] = (paramDict['underEstWt']*max(targClass[i] - estClass[i], 0) + max(estClass[i]-targClass[i],0))
    return scorevec

def score_classArr(est, targArr, paramDict):
    '''
    Returns the difference between classification of vectors est and targ using threshold, based on underEstWt,
    the weight of underestimation error relative to overestimation error.
    paramDict requires keys: threshold, underEstWt
    '''
    estClass = (est-paramDict['threshold'])
    estClass[estClass >= 0.] = 1.
    estClass[estClass < 0.] = 0.
    targClass = (targArr - paramDict['threshold'])
    targClass[targClass >= 0.] = 1.
    targClass[targClass < 0.] = 0.
    return score_diffArr(estClass,targClass,paramDict)

def score_classMat(draws, paramDict, indsforbayes=[]):
    '''
    Returns classification loss for each pairwise combination of draws. Rows correspond to estimates, columns to targets
    :param indsforbayes: which indices of draws to use as estimates; used for limiting the matrix size
    '''
    numdraws, numnodes = len(draws), len(draws[0])
    drawsClass = draws.copy()
    drawsClass[drawsClass >= paramDict['threshold']] = 1.
    drawsClass[drawsClass < paramDict['threshold']] = 0.
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(numdraws)
    numbayesinds = len(indsforbayes)
    drawsEstMat = np.reshape(np.tile(drawsClass[indsforbayes].copy(),numdraws),(numbayesinds,numdraws,numnodes))
    drawsTargMat = np.transpose(np.reshape(np.tile(drawsClass.copy(),numbayesinds),(numdraws,numbayesinds,numnodes)),
                                axes=(1, 0, 2))
    return np.maximum(drawsEstMat-drawsTargMat,0) + paramDict['underEstWt']*np.maximum(drawsTargMat-drawsEstMat,0)

def score_check(est, targ, paramDict): #### OBSOLETE; REMOVE LATER
    '''
    Returns a check difference between vectors est and targ using slope, which can be used to weigh underestimation and
    overestimation differently. Slopes less than 0.5 mean underestimation causes a higher loss than overestimation.
    paramDict requires keys: slope
    '''
    scorevec = np.empty((len(targ)))
    for i in range(len(targ)):
        scorevec[i] = (est[i]-targ[i])*(paramDict['slope']- (1 if est[i]<targ[i] else 0))
    return scorevec

def score_checkArr(est, targArr, paramDict):
    '''
    Returns a check difference between vectors est and targ using slope, which can be used to weigh underestimation and
    overestimation differently. Slopes less than 0.5 mean underestimation causes a higher loss than overestimation.
    paramDict requires keys: slope
    '''
    return (est-targArr) * (paramDict['slope'] - np.minimum(np.maximum(targArr-est,0),1e-8)*1e8)

def score_checkMat(draws, paramDict, indsforbayes=[]):
    '''
    Returns a check difference between vectors est and targ using slope, which can be used to weigh underestimation and
    overestimation differently. Slopes less than 0.5 mean underestimation causes a higher loss than overestimation.
    :param paramDict requires keys: slope
    :param indsforbayes: which indices of draws to use as estimates; used for limiting the matrix size
    '''
    numdraws, numnodes = len(draws), len(draws[0])
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(numdraws)
    numbayesinds = len(indsforbayes)
    drawsEstMat = np.reshape(np.tile(draws[indsforbayes].copy(), numdraws), (numbayesinds, numdraws, numnodes))
    drawsTargMat = np.transpose(np.reshape(np.tile(draws.copy(), numbayesinds), (numdraws, numbayesinds, numnodes)),
                                axes=(1, 0, 2))
    return (drawsEstMat-drawsTargMat) * (paramDict['slope'] - np.minimum(np.maximum(drawsTargMat-drawsEstMat,0),tol)*(1/tol))

def bayesEst(samps, scoredict):
    '''
    Returns the Bayes estimate for a set of SFP rates based on the type of score and parameters used
    scoredict: must have key 'name' and other necessary keys for calculating the associated Bayes estimate
    '''
    scorename = scoredict['name']
    if scorename == 'AbsDiff':
        underEstWt = scoredict['underEstWt']
        est = np.quantile(samps,underEstWt/(1+underEstWt), axis=0)
    elif scorename == 'Check':
        slope = scoredict['slope']
        est = np.quantile(samps,1-slope, axis=0)
    elif scorename == 'Class':
        underEstWt = scoredict['underEstWt']
        critVal = np.quantile(samps, underEstWt / (1 + underEstWt), axis=0)
        classlst = [1 if critVal[i]>=scoredict['threshold'] else 0 for i in range(len(samps[0]))]
        est = np.array(classlst)
    else:
        print('Not a valid score name')

    return est

def bayesEstAdapt(samps, wts, scoredict, printUpdate=True):
    '''
    Returns the Bayes estimate for a set of SFP rates, adjusted for weighting of samples, based on the type of score
        and parameters used
    scoredict: must have key 'name' and other necessary keys for calculating the associated Bayes estimate
    '''
    # First identify the quantile we need
    if scoredict['name'] == 'AbsDiff':
        q =  scoredict['underEstWt']/(1+ scoredict['underEstWt'])
    elif scoredict['name'] == 'Check':
        q = 1-scoredict['slope']
    elif scoredict['name'] == 'Class':
        q = scoredict['underEstWt'] / (1 + scoredict['underEstWt'])
    else:
        print('Not a valid score name')
    # Establish the weight-sum target
    wtTarg = q * np.sum(wts)
    #Initialize return vector
    est = np.empty(shape=(len(samps[0])))
    # Iterate through each node's distribution of SFP rates, sorting the weights accordingly
    for gind in range(len(samps[0])):
        if printUpdate==True:
            print('start '+str(gind)+': '+str(round(time.time())))
        currRates = samps[:,gind]
        sortRatesWts = [(y, x) for y, x in sorted(zip(currRates, wts))]
        sortRates = [x[0] for x in sortRatesWts]
        sortWts = [x[1] for x in sortRatesWts]
        #sortWtsSum = [np.sum(sortWts[:i+1]) for i in range(len(sortWts))]
        #critInd = np.argmax(sortWtsSum>=wtTarg)
        critInd = np.argmax(np.cumsum(sortWts)>=wtTarg)
        est[gind] = sortRates[critInd]
        if printUpdate==True:
            print('end ' + str(gind) + ': ' + str(round(time.time())))

    return est

def bayesEstAdaptArr(sampsArr, wtsArr, scoredict, printUpdate=True):
    '''
    Returns the Bayes estimate for a set of SFP rates, adjusted for weighting of samples, based on the type of score
        and parameters used
    scoredict: must have key 'name' and other necessary keys for calculating the associated Bayes estimate
    '''
    # First identify the quantile we need
    if scoredict['name'] == 'AbsDiff':
        q =  scoredict['underEstWt']/(1+ scoredict['underEstWt'])
    elif scoredict['name'] == 'Check':
        q = 1-scoredict['slope']
    elif scoredict['name'] == 'Class':
        q = scoredict['underEstWt'] / (1 + scoredict['underEstWt'])
    else:
        print('Not a valid score name')
    # Establish the weight-sum target
    wtTargArr = q * np.sum(wtsArr,axis=1)
    numdraws, numnodes = len(sampsArr), len(sampsArr[0])
    estArr = np.zeros((numdraws,numnodes))
    for nodeind in range(len(sampsArr[0])):
        if printUpdate==True:
            print('start '+str(nodeind)+': '+str(round(time.time())))
        currRates = sampsArr[:,nodeind] # Rates for current node
        sortMat = np.stack((wtsArr,np.reshape(np.tile(currRates,numdraws),(numdraws,numdraws))),axis=1)
        #temp=np.transpose(sortMat,(0,2,1))
        sortMat2 = np.array([sortMat[i,:,sortMat[i,1,:].argsort()] for i in range(numdraws)])
        critInds = np.array([np.argmax(np.cumsum(sortMat2[i,:,0])>=wtTargArr[i]) for i in range(numdraws)])
        estArr[:,nodeind] = np.array([sortMat2[i,critInds[i],1] for i in range(numdraws)])

    return estArr

def loss_pms(est, targ, score, scoreDict, risk, riskDict, market):
    '''
    Loss/utility function tailored for PMS.
    score, risk: score and risk functions with associated parameter dictionaries scoreDict, riskDict,
        that return vectors
    market: vector of market weights
    '''
    currloss = 0. # Initialize the loss/utility
    scorevec = score(est, targ, scoreDict)
    riskvec = risk(targ, riskDict)
    for i in range(len(targ)):
        currloss += scorevec[i] * riskvec[i] * market[i]
    return currloss

def loss_pmsArr(est, targArr, lossDict):
    '''
    Loss/utility function tailored for PMS.
    est: estimate vector of SFP rates (supply node rates first)
    targVec: array of SFP-rate vectors; intended to represent a distribution of SFP rates
    score, risk: score and risk functions with associated parameter dictionaries scoreDict, riskDict,
        that return vectors
    market: vector of market weights
    '''
    # Retrieve scores
    if lossDict['scoreDict']['name'] == 'AbsDiff':
        scoreArr = score_diffArr(est, targArr, lossDict['scoreDict'])
    elif lossDict['scoreDict']['name'] == 'Check':
        scoreArr = score_checkArr(est, targArr, lossDict['scoreDict'])
    elif lossDict['scoreDict']['name'] == 'Class':
        scoreArr = score_classArr(est, targArr, lossDict['scoreDict'])
    # Retrieve risks
    if lossDict['riskDict']['name'] == 'Parabolic':
        riskArr = risk_parabolicArr(targArr, lossDict['riskDict'])
    elif lossDict['riskDict']['name'] == 'Check':
        riskArr = risk_checkArr(targArr, lossDict['riskDict'])
    # Add a uniform market term if not in the loss dictionary
    if 'marketVec' not in lossDict.keys():
        lossDict.update({'marketVec':np.ones(len(est))})
    # Return sum loss across all nodes
    return np.sum(scoreArr*riskArr*lossDict['marketVec'],axis=1)

def loss_pmsArr2(estArr, targArr, lossDict):
    '''
    Loss/utility function tailored for PMS.
    est: array of estimate vectors of SFP rates (supply node rates first)
    targVec: array of SFP-rate vectors; intended to represent a distribution of SFP rates
    score, risk: score and risk functions with associated parameter dictionaries scoreDict, riskDict,
        that return vectors
    market: vector of market weights
    '''
    # Retrieve scores
    if lossDict['scoreDict']['name'] == 'AbsDiff':
        scoreArr = score_diffArr(estArr, targArr, lossDict['scoreDict'])
    elif lossDict['scoreDict']['name'] == 'Check':
        scoreArr = score_checkArr(estArr, targArr, lossDict['scoreDict'])
    elif lossDict['scoreDict']['name'] == 'Class':
        scoreArr = score_classArr(estArr, targArr, lossDict['scoreDict'])
    # Retrieve risks
    if lossDict['riskDict']['name'] == 'Parabolic':
        riskArr = risk_parabolicArr(targArr, lossDict['riskDict'])
    elif lossDict['riskDict']['name'] == 'Check':
        riskArr = risk_checkArr(targArr, lossDict['riskDict'])
    # Add a uniform market term if not in the loss dictionary
    if 'marketVec' not in lossDict.keys():
        lossDict.update({'marketVec':np.ones(len(estArr[0]))})
    # Return sum loss across all nodes
    return np.sum(scoreArr*riskArr*lossDict['marketVec'],axis=1)

def lossMatrix(draws,lossdict,indsforbayes=[]):
    '''
    Returns a matrix of losses associated with each pair of SFP-rate draws according to the specifications of lossdict
    :param indsforbayes: which indices of draws to use as estimates; used for limiting the matrix size
    '''
    if len(indsforbayes) == 0:
        indsforbayes = np.arange(len(draws))
    numbayesinds = len(indsforbayes)
    # Get score matrix
    if lossdict['scoreDict']['name'] == 'AbsDiff':
        scoreMat = score_diffMat(draws, lossdict['scoreDict'], indsforbayes)
    elif lossdict['scoreDict']['name'] == 'Class':
        scoreMat = score_classMat(draws, lossdict['scoreDict'], indsforbayes)
    elif lossdict['scoreDict']['name'] == 'Check':
        scoreMat = score_checkMat(draws, lossdict['scoreDict'], indsforbayes)
    # Get risk matrix
    if lossdict['riskDict']['name'] == 'Parabolic':
        riskMat = risk_parabolicMat(draws, lossdict['riskDict'], indsforbayes)
    elif lossdict['riskDict']['name'] == 'Check':
        riskMat = risk_checkMat(draws, lossdict['riskDict'], indsforbayes)

    if 'marketVec' not in lossdict.keys():
        lossdict.update({'marketVec': np.ones(len(draws[0]))})
    marketMat = np.reshape(np.tile(lossdict['marketVec'].copy(),(numbayesinds,len(draws))),(numbayesinds,len(draws),len(draws[0])))
    return np.sum(scoreMat*riskMat*marketMat,axis=2)

def loss_pms2(est, targ, paramDict):
    '''
    Loss/utility function tailored for PMS.
    score, risk: score and risk functions with associated parameter dictionaries scoreDict, riskDict
    market: market weights
    '''
    currloss = 0.
    epsTarg = 0.5 - paramDict['rateTarget']
    if len(paramDict['nodeWtVec'])==0: #
        nodeWtVec = [1. for i in range(len(est))]
    for i in range(len(est)):
        scoreterm = (paramDict['underEstWt']*max(targ[i] - est[i], 0) + max(est[i]-targ[i],0))
        if paramDict['checkloss']==False:
            if epsTarg < 0:
                wtterm = targ[i]*(1-targ[i]-2*epsTarg)
            else:
                wtterm = (targ[i]+2*epsTarg)*(1-targ[i])
        else:
            wtterm = 1 - targ[i]*(paramDict['checkslope']-(1-paramDict['rateTarget']/targ[i] if targ[i]<paramDict['rateTarget'] else 0))
        currloss += scoreterm * wtterm * nodeWtVec[i]
    return currloss

def showRiskVals():
    '''Generate a figure showcasing how the risk changes with different parameter choices'''
    x = np.linspace(0.001,0.999,1000)
    t = 0.3 # Our target
    y1 = (x+2*(0.5-t))*(1-x)
    tauvec = [0.05,0.2,0.4,0.6,0.95]
    fig, ax = plt.subplots(figsize=(8, 7))
    for tau in tauvec:
        newy = [1 - x[i]*(tau-(1-(t/x[i]) if x[i]<t else 0)) for i in range(len(x))]
        plt.plot(x,newy)
    plt.plot(x,y1)
    import matplotlib.ticker as mtick
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.title('Values for Parabolic and selected Check risk terms\n$l=30\%$',fontdict={'fontsize':16,'fontname':'Trebuchet MS'})
    plt.ylabel('Risk term value', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.xlabel('SFP rate', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.97,'Check, $m=0.05$',fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.84, 'Check, $m=0.2$',fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.675, 'Check, $m=0.4$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.50, 'Check, $m=0.6$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.21, 'Check, $m=0.95$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.00, 0.47, 'Parabolic', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    fig.tight_layout()
    plt.show()
    plt.close()

    return

def showScoreVals():
    '''Generate a figure showcasing how the score changes with different parameter choices'''
    gEst = np.linspace(0.001,0.999,50) #gamma_hat
    gStar = 0.4 # gamma_star
    tauvec = [0.05,0.25,0.9] # For check score
    vvec = [0.5,1.2] # For absolute difference and classification scores
    tvec = [0.2]
    fig, ax = plt.subplots(figsize=(8, 7))
    for tau in tauvec: # Check scores
        newy = [(gStar-gEst[i])*(tau-(1 if gEst[i]<gStar else 0)) for i in range(len(gEst))]
        plt.plot(gEst,newy,':')
    for v in vvec: # Absolute difference scores
        newy = [-1*(max(gEst[i]-gStar,0)+v*max(gStar-gEst[i],0)) for i in range(len(gEst))]
        plt.plot(gEst,newy,'-')
        for t in tvec:
            classEst = [1 if gEst[i]>=t else 0 for i in range(len(gEst))]
            classStar = 1 if gStar >= t else 0
            newy = [-1*(max(classEst[i]-classStar,0)+v*max(classStar-classEst[i],0)) for i in range(len(gEst))]
            plt.plot(gEst,newy,'<',)
    import matplotlib.ticker as mtick
    plt.ylim([-1.3,0.1])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.title('Values for selected score terms\n$\gamma^\star=40\%$',fontdict={'fontsize':16,'fontname':'Trebuchet MS'})
    plt.ylabel('Score term value', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.xlabel('SFP rate estimate', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.text(0.16, -0.55,'Class., $l=20\%$, $v=0.5$',fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0.16, -1.17, 'Class., $l=20\%$, $v=1.2$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0.80, -0.07, 'Check, $m=0.05$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0.8, -0.2, 'Check, $m=0.25$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0.81, -0.36, 'Check, $m=0.9$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0., -0.1, 'Abs. Diff., $v=0.5$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    plt.text(0.13, -0.37, 'Abs. Diff., $v=1.2$', fontdict={'fontsize': 10, 'fontname': 'Trebuchet MS'})
    fig.tight_layout()
    plt.show()
    plt.close()

    return

def showScoreAndRiskVals():
    x = np.linspace(0.001, 0.999, 1000)
    t = 0.2  # Our target
    y1 = ((x + 2 * (0.5 - t)) * (1 - x))+0.1
    fig, ax = plt.subplots(figsize=(8, 7))
    plt.plot(x, y1,linewidth=4)

    gEst = np.linspace(0.001, 0.999, 50)  # gamma_hat
    gStar = 0.4  # gamma_star
    tauvec = [0.1]
    for tau in tauvec: # Check scores
        newy = [(gStar-gEst[i])*(tau-(1 if gEst[i]<gStar else 0))+0.5 for i in range(len(gEst))]
        plt.plot(gEst,newy,':',linewidth=5)

    import matplotlib.ticker as mtick
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.title('Values for a selected score and risk',
              fontdict={'fontsize': 20, 'fontname': 'Trebuchet MS'})
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylabel('Score/risk value', fontdict={'fontsize': 16, 'fontname': 'Trebuchet MS'})
    plt.ylim([0.,0.9])
    plt.xlabel('SFP rate', fontdict={'fontsize': 16, 'fontname': 'Trebuchet MS'})

    plt.text(0.00, 0.655, 'Parabolic risk', fontdict={'fontsize': 15, 'fontname': 'Trebuchet MS'})
    plt.text(0.00, 0.32, 'Check score', fontdict={'fontsize': 15, 'fontname': 'Trebuchet MS'})

    fig.tight_layout()
    plt.show()
    plt.close()
    
    return

def utilityOverIncreasingData():
    '''Generate a figure showing the change in utility as n increases'''

    return

def writeObjToPickle(obj, objname='pickleObject'):
    '''HOW TO WRITE PRIOR DRAWS TO A PICKLE OBJECT TO BE LOADED LATER'''
    import pickle
    import os
    outputFilePath = os.getcwd()
    outputFileName = os.path.join(outputFilePath, objname)
    pickle.dump(obj, open(outputFileName, 'wb'))
    return

def getDesignUtility(priordatadict, lossdict, designlist, numtests, designnames=[], utildict={}):
    '''
    Produces a list of loss vectors for entered design choices under a given data set and specified loss. Each loss
        vector has numdatadraws Monte Carlo iterations
    Designed for use with plotLossVecs() to plot Bayesian risk associated with each design.
    priordatadict: dictionary capturing all prior data. should have posterior draws from initial data set already
    included, with keys identical to those provided by logistigate functions
    lossdict: parameter dictionary to pass to lossfunc
    designlist: list of sampling probability vectors along all test nodes or traces
    designnames: list of names for the designs
    numtests: how many samples will be obtained under each design
    utildict: dictionary of utility calculation parameters, which may include the following:
        numdatadraws: number of prior draws to use for generating data and calculating utility
        type: list for the type of sample collection described in each design; one of ['path'] (collect along SN-TN
            trace) or ['node', Qest] (collect along test nodes, along with the estimate of the sourcing probability matrix)
        priordraws: set of prior draws to use for synchronized data collection in different designs
        randinds: the indices with which to iterate through priordraws for all numdatadraws loops
        method: one of 'MCMC', 'MCMCexpec', 'weights' or 'approx'; 'MCMC' completes full MCMC sampling for generating
            posterior probabilities, 'approx' approximates the posterior probabilities, 'weights1' uses a weighting
            equivalence while integraing over all possible data outcomes
    '''
    # Initiate the list to return
    lossveclist = []
    # Retrieve utility parameters or set defaults
    if 'priordraws' in utildict:
        priordraws = utildict['priordraws'].copy()
    else:
        priordraws = priordatadict['postSamples']
    if 'method' in utildict:
        method = utildict['method']
    else:
        method = 'MCMC'
    if 'numdatadraws' in utildict:
        numdatadraws = utildict['numdatadraws']
    else:
        numdatadraws = 1
    if 'priorindstouse' in utildict:
        priorindstouse = utildict['priorindstouse'].copy()
    else:
        priorindstouse = [i for i in range(numdatadraws)]
    if len(designnames)==0:
        for i in range(len(designlist)):
            designnames.append('Design '+str(i))
    if 'numpostdraws' in utildict:
        numpostdraws = utildict['numpostdraws']
    else:
        numpostdraws = priordatadict['numPostSamples']
    if 'numdrawsfordata' in utildict:
        numdrawsfordata = utildict['numdrawsfordata']
    else:
        numdrawsfordata = len(priordraws)
    if 'roundAlg' in utildict:
        roundAlg = utildict['roundAlg'].copy()
    else:
        roundAlg = 'roundDesignLow'
    if 'type' in utildict:
        type = utildict['type'].copy()
    else:
        type = ['path']
    if 'printUpdate' in utildict:
        printUpdate = utildict['printUpdate'].copy()
    else:
        printUpdate = True
    # Get key supply-chain elements from priordatadict
    (numTN, numSN) = priordatadict['N'].shape
    Q = priordatadict['transMat'] #May be empty
    s, r = priordatadict['diagSens'], priordatadict['diagSpec']
    numpriordraws = len(priordraws)

    # Loop through each design and generate loss according to selected method
    for designind, design in enumerate(designlist):
        currlossvec = []
        # Initialize samples to be drawn from traces, per the design
        if roundAlg == 'roundDesignLow':
            sampMat = roundDesignLow(design, numtests)
        elif roundAlg == 'roundDesignHigh':
            sampMat = roundDesignHigh(design, numtests)
        elif roundAlg == 'balancedesign':
            sampMat = balancedesign(design, numtests)
        else:
            print('Nonvalid rounding function entered')
            return

        if method == 'MCMC':
            for omega in range(numdatadraws):
                TNsamps = sampMat.copy()
                # Grab a draw from the prior
                currpriordraw = priordraws[priorindstouse[omega]]  # [SN rates, TN rates]

                # Initialize Ntilde and Ytilde
                Ntilde = np.zeros(shape=priordatadict['N'].shape)
                Ytilde = Ntilde.copy()
                while np.sum(TNsamps) > 0.:
                    # Go to first non-empty row of TN samps
                    i, j = 0, 0
                    while np.sum(TNsamps[i]) == 0:
                        i += 1
                    if type[0] == 'path':
                        # Go to first non-empty column of this row
                        while TNsamps[i][j] == 0:
                            j += 1
                        TNsamps[i][j] -= 1
                    if type[0] == 'node':
                        # Pick a supply node according to Qest
                        j = choice([i for i in range(numSN)], p=type[1][i] / np.sum(type[1][i]).tolist())
                        TNsamps[i] -= 1
                    # Generate test result
                    currTNrate = currpriordraw[numSN + i]
                    currSNrate = currpriordraw[j]
                    currrealrate = currTNrate + (1 - currTNrate) * currSNrate  # z_star for this sample
                    currposrate = s * currrealrate + (1 - r) * (1 - currrealrate)  # z for this sample
                    result = np.random.binomial(1, p=currposrate)
                    Ntilde[i, j] += 1
                    Ytilde[i, j] += result
                # We have a new set of data d_tilde
                Nomega = priordatadict['N'] + Ntilde
                Yomega = priordatadict['Y'] + Ytilde

                postdatadict = priordatadict.copy()
                postdatadict['N'] = Nomega
                postdatadict['Y'] = Yomega

                # Writes over previous MCMC draws
                postdatadict.update({'numPostSamples':numpostdraws})
                postdatadict = methods.GeneratePostSamples(postdatadict)

                # Get the Bayes estimate
                currEst = bayesEst(postdatadict['postSamples'], lossdict['scoreDict'])

                sumloss = 0
                for currsampind, currsamp in enumerate(postdatadict['postSamples']):
                    currloss = loss_pms(currEst, currsamp, lossdict['scoreFunc'], lossdict['scoreDict'],
                                        lossdict['riskFunc'], lossdict['riskDict'], lossdict['marketVec'])
                    sumloss += currloss
                avgloss = sumloss / len(postdatadict['postSamples'])

                # Append to loss storage vector
                currlossvec.append(avgloss)
                if printUpdate==True:
                    print(designnames[designind] + ', ' + 'omega ' + str(omega) + ' complete')

            lossveclist.append(currlossvec)  # Add the loss vector for this design
        # END IF FOR MCMC

        elif method == 'MCMCexpect':
            for omega in range(numdatadraws):
                # Grab a draw from the prior
                currpriordraw = priordraws[priorindstouse[omega]]  # [SN rates, TN rates]

                # Initialize Ntilde and Ytilde
                Ntilde = sampMat.copy()
                Ytilde = np.zeros(shape=priordatadict['N'].shape)

                for currTN in range(numTN):
                    for currSN in range(numSN):
                        currzProb = zProbTr(currTN,currSN,numSN,currpriordraw,priordatadict['diagSens'],priordatadict['diagSpec'])
                        if type[0] == 'path':
                            currTerm = sampMat[currTN][currSN]*currzProb
                        elif type[0] == 'node':
                            currTerm = sampMat[currTN]*type[1][currTN][currSN]*currzProb
                        Ytilde[currTN][currSN] = currTerm

                # We have a new set of data d_tilde
                Nomega = priordatadict['N'] + Ntilde
                Yomega = priordatadict['Y'] + Ytilde

                postdatadict = priordatadict.copy()
                postdatadict['N'] = Nomega
                postdatadict['Y'] = Yomega

                # Writes over previous MCMC draws
                postdatadict.update({'numPostSamples':numpostdraws})
                postdatadict = methods.GeneratePostSamples(postdatadict)

                # Get the Bayes estimate
                currEst = bayesEst(postdatadict['postSamples'], lossdict['scoreDict'])

                sumloss = 0
                for currsampind, currsamp in enumerate(postdatadict['postSamples']):
                    currloss = loss_pms(currEst, currsamp, lossdict['scoreFunc'], lossdict['scoreDict'],
                                        lossdict['riskFunc'], lossdict['riskDict'], lossdict['marketVec'])
                    sumloss += currloss
                avgloss = sumloss / len(postdatadict['postSamples'])

                # Append to loss storage vector
                currlossvec.append(avgloss)
                if printUpdate==True:
                    print(designnames[designind] + ', ' + 'omega ' + str(omega) + ' complete')

            lossveclist.append(currlossvec)  # Add the loss vector for this design
        # END ELIF FOR MCMCEXPECT

        elif method == 'weightsPathEnumerate': # Weight each prior draw by the likelihood of a new data set
            Ntilde = sampMat.copy()
            sumloss = 0
            Yset = possibleYSets(Ntilde)
            for Ytilde in Yset: # Enumerating all possible data sets, so DO NOT normalize weights (they will sum to unity)
                # Get weights for each prior draw
                zMat = zProbTrVec(numSN, priordraws, sens=s, spec=r)[:, :, :]
                wts = np.prod((zMat ** Ytilde) * ((1 - zMat) ** (Ntilde - Ytilde)) * sps.comb(Ntilde, Ytilde), axis=(1,2))
                '''
                wts = []
                for currpriordraw in priordraws:
                    # Use current new data to get a weight for the current prior draw
                    currwt=1.0
                    for TNind in range(numTN):
                        for SNind in range(numSN):
                            curry, currn = int(Ytilde[TNind][SNind]), int(Ntilde[TNind][SNind])
                            currz = zProbTr(TNind,SNind,numSN,currpriordraw,sens=s,spec=r)
                            currwt = currwt * (currz**curry) * ((1-currz)**(currn-curry)) * comb(currn, curry)
                    wts.append(currwt) # Add weight for this gamma draw
                '''
                # Obtain Bayes estimate
                currest = bayesEstAdapt(priordraws,wts,lossdict['scoreDict'],printUpdate=False)
                # Sum the weighted loss under each prior draw
                sumloss += np.sum(loss_pmsArr(currest, priordraws, lossdict) * wts)  # VECTORIZED
                '''
                for currsampind, currsamp in enumerate(priordraws):
                    currloss = loss_pms(currest,currsamp, score_diff, lossdict['scoreDict'],
                                        risk_parabolic, lossdict['riskDict'], lossdict['marketVec'])
                    sumloss += currloss * wts[currsampind]
                '''
            lossveclist.append(sumloss / len(priordraws))  # Add the loss vector for this design
            if printUpdate == True:
                print(designnames[designind] + ' complete')
        # END ELIF FOR WEIGHTSPATHENUMERATE

        elif method == 'weightsNodeEnumerate': # Weight each prior draw by the likelihood of a new data set
            #IMPORTANT!!! CAN ONLY HANDLE DESIGNS WITH 1 TEST NODE
            Ntilde = sampMat.copy()
            sampNodeInd = 0
            for currind in range(numTN):
                if Ntilde[currind] > 0:
                    sampNodeInd = currind
            Ntotal = int(Ntilde[sampNodeInd])
            if printUpdate==True:
                print('Generating possible N sets...')
            NvecSet = nVecs(numSN,Ntotal)
            # Remove any Nset members that have positive tests at supply nodes with no sourcing probability
            removeInds = [j for j in range(numSN) if Q[sampNodeInd][j]==0.]
            if len(removeInds) > 0:
                for currRemoveInd in removeInds:
                    NvecSet = [item for item in NvecSet if item[currRemoveInd]==0]
            # Iterate through each possible data set
            NvecProbs = [] # Initialize a list capturing the probability of each data set
            NvecLosses = [] # Initialize a list for the loss under each N vector
            for Nvec in NvecSet:
                if printUpdate == True:
                    print('Looking at N set: ' + str(Nvec))
                currNprob=math.factorial(Ntotal) # Initialize with n!
                for currSN in range(numSN):
                    Qab, Nab = Q[sampNodeInd][currSN], Nvec[currSN]
                    currNprob = currNprob * (Qab**Nab) / (math.factorial(Nab))
                NvecProbs.append(currNprob)
                # Define the possible data results for the current Nvec
                Yset = possibleYSets(np.array(Nvec).reshape(1,numSN))
                Yset = [i[0] for i in Yset]
                sumloss = 0.
                for Ytilde in Yset:

                    zMat = zProbTrVec(numSN, priordraws, sens=s, spec=r)[:, sampNodeInd, :]
                    wts = np.prod((zMat ** Ytilde) * ((1 - zMat) ** (Nvec - Ytilde)) * sps.comb(Nvec, Ytilde), axis=1)
                    '''
                    wts = []
                    for currpriordraw in priordraws:
                        currwt = 1.0
                        for SNind in range(numSN):
                            curry, currn = int(Ytilde[SNind]), int(Nvec[SNind])
                            currz = zProbTr(sampNodeInd,SNind,numSN,currpriordraw,sens=s,spec=r)
                            currwt = currwt * (currz ** curry) * ((1 - currz) ** (currn - curry)) * comb(currn, curry)
                        wts.append(currwt) # Add weight for this gamma draw
                    '''
                    # Get Bayes estimate
                    currest = bayesEstAdapt(priordraws,wts,lossdict['scoreDict'],printUpdate=False)
                    # Sum the weighted loss under each prior draw
                    sumloss += np.sum(loss_pmsArr(currest, priordraws, lossdict) * wts)  # VECTORIZED
                    '''
                    for currsampind, currsamp in enumerate(priordraws):
                        currloss = loss_pms(currest, currsamp, score_diff, lossdict['scoreDict'],
                                            risk_parabolic, lossdict['riskDict'], lossdict['marketVec'])
                        sumloss += currloss * wts[currsampind]
                    '''
                NvecLosses.append(sumloss / len(priordraws))
            # Weight each Nvec loss by the occurence probability
            finalLoss = 0.
            for Nind in range(len(NvecSet)):
                finalLoss += NvecLosses[Nind] * NvecProbs[Nind]
            lossveclist.append(finalLoss)
            if printUpdate == True:
                print(designnames[designind] + ' complete')
        # END ELIF FOR WEIGHTSNODEENUMERATE

        elif method == 'weightsNodeDraw': # Weight each prior draw by the likelihood of a new data set
            # Differs from 'weightsNodeEnumerate' in that rather than enumerate every possible data set, numdatadraws data
            #   sets are drawn
            #IMPORTANT!!! CAN ONLY HANDLE DESIGNS WITH 1 TEST NODE
            Ntilde = sampMat.copy()
            sampNodeInd = 0
            for currind in range(numTN): # Identify the test node we're analyzing
                if Ntilde[currind] > 0:
                    sampNodeInd = currind
            Ntotal, Qvec = int(Ntilde[sampNodeInd]), Q[sampNodeInd]
            # Initialize NvecSet with numdatadraws different data sets
            NvecSet = []
            for i in range(numdatadraws):
                sampSNvec = choice([j for j in range(numSN)], size=Ntotal, p=Qvec) # Sample according to the sourcing probabilities
                sampSNvecSums = np.array([sampSNvec.tolist().count(j) for j in range(numSN)]) # Consolidate samples by supply node
                NvecSet.append(sampSNvecSums)
            NvecLosses = []  # Initialize a list for the loss under each N vector
            for Nvecind, Nvec in enumerate(NvecSet):
                ''' CODE FOR DOING MULTIPLE Y REALIZATIONS UNDER EACH NVEC
                YvecSet = [] #Initialize a list of possible data outcomes
                if numYdraws > len(priordraws):
                    print('numYdraws exceeds the number of prior draws')
                    return
                priorIndsForY = random.sample(range(len(priordraws)), numYdraws)  # Grab numYdraws gammas from prior
                for i in range(numYdraws):
                    zVec = [zProbTr(sampNodeInd, sn, numSN, priordraws[priorIndsForY[i]], sens=s, spec=r) for sn in range(numSN)]
                    ySNvec = [choice([j for j in range(Nvec[sn])],p=zVec[sn]) for sn in range(numSN)]
                    YvecSet.append(ySNvec)
                '''
                randprior = priordraws[random.sample(range(numpriordraws),k=1)][0]
                zVec = [zProbTr(sampNodeInd, sn, numSN, randprior, sens=s, spec=r) for sn in range(numSN)]
                Yvec = np.array([np.random.binomial(Nvec[sn],zVec[sn]) for sn in range(numSN)])
                # Get weights for each prior draw
                zMat = zProbTrVec(numSN,priordraws,sens=s,spec=r)[:,sampNodeInd,:]
                wts = np.prod((zMat**Yvec)*((1-zMat)**(Nvec-Yvec))*sps.comb(Nvec,Yvec),axis=1) # VECTORIZED
                # Normalize weights to sum to number of prior draws
                currWtsSum = np.sum(wts)
                wts = wts*numpriordraws/currWtsSum
                # Get Bayes estimate
                currest = bayesEstAdapt(priordraws, wts, lossdict['scoreDict'], printUpdate=False)
                # Sum the weighted loss under each prior draw
                #if len(sampsforevalbayes)>0:
                #    zMat = zProbTrVec(numSN, sampsforevalbayes, sens=s, spec=r)[:, sampNodeInd, :]
                #    newwts = np.prod((zMat ** Yvec) * ((1 - zMat) ** (Nvec - Yvec)) * sps.comb(Nvec, Yvec), axis=1)
                #    currWtsSum = np.sum(newwts)
                #    newwts = newwts * len(sampsforevalbayes) / currWtsSum
                #    lossArr = loss_pmsArr(currest, sampsforevalbayes, lossdict) * newwts  # VECTORIZED
                #else:
                lossArr = loss_pmsArr(currest,priordraws,lossdict) * wts # VECTORIZED

                NvecLosses.append(np.average(lossArr))
                if printUpdate == True and Nvecind % 5 == 0:
                    print('Finished Nvecind of '+str(Nvecind))
            currlossvec.append(np.average(NvecLosses))
            lossveclist.append(currlossvec)
            if printUpdate == True:
                print(designnames[designind] + ' complete')
        # END ELIF FOR WEIGHTSNODEDRAW

        elif method == 'weightsNodeDraw2': # Weight each prior draw by the likelihood of a new data set
            # Differs from 'weightsNodeDraw2' in that rather than enumerate every possible data set, numdatadraws data
            #   sets are drawn
            #IMPORTANT!!! CAN ONLY HANDLE DESIGNS WITH 1 TEST NODE
            Ntilde = sampMat.copy()
            sampNodeInd = 0
            for currind in range(numTN): # Identify the test node we're analyzing
                if Ntilde[currind] > 0:
                    sampNodeInd = currind
            Ntotal, Qvec = int(Ntilde[sampNodeInd]), Q[sampNodeInd]

            zMat = zProbTrVec(numSN, priordraws, sens=s, spec=r)[:, sampNodeInd, :]
            NMat = np.random.multinomial(Ntotal,Qvec,size=numpriordraws)
            YMat = np.random.binomial(NMat,zMat)
            bigzMat = np.transpose(np.reshape(np.tile(zMat,numpriordraws),(numpriordraws,numpriordraws,numSN)),axes=(1,0,2))
            bigNMat = np.reshape(np.tile(NMat,numpriordraws), (numpriordraws,numpriordraws,numSN))
            bigYMat = np.reshape(np.tile(YMat,numpriordraws), (numpriordraws,numpriordraws,numSN))
            combNY = np.reshape(np.tile(sps.comb(NMat, YMat),numpriordraws),(numpriordraws,numpriordraws,numSN))
            time1 = time.time()
            # wtsMat=... TAKES 76 SECS. FOR 10K DRAWS
            wtsMat = np.prod((bigzMat ** bigYMat) * ((1 - bigzMat) ** (bigNMat - bigYMat)) * combNY, axis=2)
            time2 = time.time()
            wtsMat = np.divide(wtsMat*numpriordraws,np.reshape(np.tile(np.sum(wtsMat,axis=1),numpriordraws),(numpriordraws,numpriordraws)).T)
            time3 = time.time()
            # estMat=... TAKES 100 SECS. FOR 10K DRAWS
            estMat = bayesEstAdaptArr(priordraws,wtsMat,lossdict['scoreDict'],printUpdate=False)
            time4 = time.time()
            losses = loss_pmsArr2(estMat,priordraws,lossdict)
            lossveclist.append(np.average(losses))

            print(round(time2 - time1))
            print(round(time4 - time3))

            if printUpdate == True:
                print(designnames[designind] + ' complete')
        # END ELIF FOR WEIGHTSNODEDRAW2

        elif method == 'weightsNodeDraw3': # Weight each prior draw by the likelihood of a new data set
            # Differs from 'weightsNodeDraw2' in 3 areas:
            #   1) Able to use a subset of prior draws for generating data
            #   2) Uses log transformation to speed up weight calculation
            #   3) Uses loss and weight matrices to select Bayes estimate
            #IMPORTANT!!! CAN ONLY HANDLE DESIGNS WITH 1 TEST NODE
            Ntilde = sampMat.copy()
            sampNodeInd = 0
            for currind in range(numTN): # Identify the test node we're analyzing
                if Ntilde[currind] > 0:
                    sampNodeInd = currind
            Ntotal, Qvec = int(Ntilde[sampNodeInd]), Q[sampNodeInd]
            # Use numdrawsfordata draws randomly selected from the set of prior draws
            datadrawinds = choice([j for j in range(numpriordraws)], size=numdrawsfordata, replace=False)
            zMat = zProbTrVec(numSN, priordraws, sens=s, spec=r)[:, sampNodeInd, :]
            NMat = np.random.multinomial(Ntotal,Qvec,size=numdrawsfordata)
            YMat = np.random.binomial(NMat, zMat[datadrawinds])
            bigzMat = np.transpose(np.reshape(np.tile(zMat, numdrawsfordata), (numpriordraws, numdrawsfordata,numSN)),
                                   axes=(0,1,2))
            bigNMat = np.transpose(np.reshape(np.tile(NMat, numpriordraws), (numdrawsfordata,numpriordraws, numSN)),
                                   axes=(1,0,2))
            bigYMat = np.transpose(np.reshape(np.tile(YMat, numpriordraws), (numdrawsfordata, numpriordraws, numSN)),
                                    axes=(1, 0, 2))
            combNY = np.transpose(np.reshape(np.tile(sps.comb(NMat, YMat),numpriordraws),
                                              (numdrawsfordata,numpriordraws,numSN)),axes=(1,0,2))
            wtsMat = np.exp(np.sum((bigYMat*np.log(bigzMat))+((bigNMat-bigYMat)*np.log(1-bigzMat))+np.log(combNY),axis=2))
            # Normalize so that each column sums to 1
            wtsMat = np.divide(wtsMat * 1, np.reshape(np.tile(np.sum(wtsMat, axis=0), numpriordraws),
                                                                  (numpriordraws, numdrawsfordata)))
            #lossMat = lossMatrix(priordraws,lossdict) # MOVE TO INPUT OF LOSSDICT
            wtLossMat = np.matmul(lossdict['lossMat'],wtsMat)
            wtLossMins = wtLossMat.min(axis=0)
            lossveclist.append(np.average(wtLossMins))
        # END ELIF FOR WEIGHTSNODEDRAW3

        elif method == 'weightsNodeDraw4': # Weight each prior draw by the likelihood of a new data set
            # Differs from 'weightsNodeDraw3' in that it allows any type of design, not just one test node designs
            # Use numdrawsfordata draws randomly selected from the set of prior draws
            datadrawinds = choice([j for j in range(numpriordraws)], size=numdrawsfordata, replace=False)
            zMat2 = zProbTrVec(numSN, priordraws, sens=s, spec=r)[:, :, :]
            if sampMat.ndim == 1: # Node sampling
                NMat2 = np.moveaxis( np.array([np.random.multinomial(sampMat[tnInd], Q[tnInd], size=numdrawsfordata) for tnInd in range(len(sampMat))]),1,0)
                YMat2 = np.random.binomial(NMat2.astype(int), zMat2[datadrawinds])
            elif sampMat.ndim == 2: # Path sampling
                NMat2 = np.moveaxis(np.reshape(np.tile(sampMat, numdrawsfordata),(numTN,numdrawsfordata,numSN)),1,0)
                YMat2 = np.random.binomial(NMat2.astype(int), zMat2[datadrawinds])
            bigZMat2 = np.transpose(np.reshape(np.tile(zMat2, numdrawsfordata), (numpriordraws, numTN, numdrawsfordata, numSN)),
                                   axes=(0,2,1,3))
            bigNMat2 = np.transpose(np.reshape(np.tile(NMat2, numpriordraws), (numdrawsfordata,numTN, numpriordraws, numSN)),
                                   axes=(2,0,1,3))
            bigYMat2 = np.transpose(np.reshape(np.tile(YMat2, numpriordraws),
                                    (numdrawsfordata, numTN, numpriordraws, numSN)), axes=(2, 0, 1, 3))
            combNY2 = np.transpose(np.reshape(np.tile(sps.comb(NMat2, YMat2),numpriordraws),
                                              (numdrawsfordata,numTN, numpriordraws,numSN)),axes=(2,0,1,3))
            wtsMat2 = np.exp(np.sum((bigYMat2 * np.log(bigZMat2)) + ((bigNMat2 - bigYMat2) * np.log(1 - bigZMat2))
                                    + np.log(combNY2), axis=(2,3)))
            # Normalize so that each column sums to 1
            wtsMat2 = np.divide(wtsMat2 * 1, np.reshape(np.tile(np.sum(wtsMat2, axis=0), numpriordraws),
                                                        (numpriordraws, numdrawsfordata)))
            wtLossMat = np.matmul(lossdict['lossMat'],wtsMat2)
            wtLossMins = wtLossMat.min(axis=0)
            lossveclist.append(np.average(wtLossMins))
        # END ELIF FOR WEIGHTSNODEDRAW4

        elif method == 'weightsNodeEnumerateY': # Weight each prior draw by the likelihood of a new data set
            # Differs from 'weightsNodeEnumerate' in that only possible data sets (Y) are enumerated, and N is randomly drawn
            #IMPORTANT!!! CAN ONLY HANDLE DESIGNS WITH 1 TEST NODE
            Ntilde = sampMat.copy()
            sampNodeInd = 0
            for currind in range(numTN):
                if Ntilde[currind] > 0:
                    sampNodeInd = currind
            Ntotal, Qvec = int(Ntilde[sampNodeInd]), Q[sampNodeInd]
            # Initialize NvecSet with numdatadraws different data sets
            NvecSet = []
            for i in range(numdatadraws):
                sampSNvec = choice([i for i in range(numSN)], size=Ntotal, p=Qvec) # Sample according to the sourcing probabilities
                sampSNvecSums = [sampSNvec.tolist().count(j) for j in range(numSN)] # Consolidate samples by supply node
                NvecSet.append(sampSNvecSums)
            NvecLosses = []  # Initialize a list for the loss under each N vector
            for Nvecind, Nvec in enumerate(NvecSet):
                ''' CODE FOR DOING MULTIPLE Y REALIZATIONS UNDER EACH NVEC
                YvecSet = [] #Initialize a list of possible data outcomes
                if numYdraws > len(priordraws):
                    print('numYdraws exceeds the number of prior draws')
                    return
                priorIndsForY = random.sample(range(len(priordraws)), numYdraws)  # Grab numYdraws gammas from prior
                for i in range(numYdraws):
                    zVec = [zProbTr(sampNodeInd, sn, numSN, priordraws[priorIndsForY[i]], sens=s, spec=r) for sn in range(numSN)]
                    ySNvec = [choice([j for j in range(Nvec[sn])],p=zVec[sn]) for sn in range(numSN)]
                    YvecSet.append(ySNvec)
                '''
                Yset = possibleYSets(np.array(Nvec).reshape(1, numSN))
                Yset = [i[0] for i in Yset]
                sumloss = 0.
                for Ytilde in Yset:
                    wts = []
                    for currpriordraw in priordraws:
                        currwt = 1.0
                        for SNind in range(numSN):
                            curry, currn = int(Ytilde[SNind]), int(Nvec[SNind])
                            currz = zProbTr(sampNodeInd, SNind, numSN, currpriordraw, sens=s, spec=r)
                            currwt = currwt * (currz ** curry) * ((1 - currz) ** (currn - curry)) * comb(currn, curry)
                        wts.append(currwt)  # Add weight for this gamma draw
                    # Get Bayes estimate
                    currest = bayesEstAdapt(priordraws, wts, lossdict['scoreDict'], printUpdate=False)
                    # Sum the weighted loss under each prior draw
                    for currsampind, currsamp in enumerate(priordraws):
                        currloss = loss_pms(currest, currsamp, lossdict['scoreFunc'], lossdict['scoreDict'],
                                            lossdict['riskFunc'], lossdict['riskDict'], lossdict['marketVec'])
                        sumloss += currloss * wts[currsampind]
                NvecLosses.append(sumloss / len(priordraws))
                if printUpdate == True and Nvecind % 5 == 0:
                    print('Finished Nvecind of '+str(Nvecind))
            lossveclist.append(np.average(NvecLosses))
            if printUpdate == True:
                print(designnames[designind] + ' complete')
        # END ELIF FOR WEIGHTSNODEENUMERATEY
    # END LOOP FOR DESIGNS

    return lossveclist

def timingbreakdown():
    rd3_N = np.array([[1., 1., 10., 1., 3., 0., 1., 6., 7., 5., 0., 0., 4.],
                      [1., 1., 4., 2., 0., 1., 1., 2., 0., 4., 0., 0., 1.],
                      [3., 17., 31., 4., 2., 0., 1., 6., 0., 23., 1., 2., 5.],
                      [1., 1., 15., 2., 0., 0., 0., 1., 0., 6., 0., 0., 0.]])
    rd3_Y = np.array([[0., 0., 7., 0., 3., 0., 1., 0., 1., 0., 0., 0., 4.],
                      [0., 0., 2., 2., 0., 1., 1., 0., 0., 1., 0., 0., 1.],
                      [0., 0., 15., 3., 2., 0., 0., 2., 0., 1., 1., 2., 5.],
                      [0., 0., 5., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0.]])

    # Some summaries
    TNtesttotals = np.sum(rd3_N, axis=1)
    TNsfptotals = np.sum(rd3_Y, axis=1)
    TNrates = np.divide(TNsfptotals, TNtesttotals)

    (numTN, numSN) = rd3_N.shape
    s, r = 1., 1.,
    CSdict3 = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r,
                                        numSamples=0, dataType='Tracked', randSeed=2)
    CSdict3['diagSens'] = s
    CSdict3['diagSpec'] = r
    CSdict3 = util.GetVectorForms(CSdict3)
    CSdict3['N'] = rd3_N
    CSdict3['Y'] = rd3_Y
    CSdict3['prior'] = methods.prior_normal()  # Evalutate choice here
    # MCMC settings
    CSdict3['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    CSdict3['importerNum'] = numSN
    CSdict3['outletNum'] = numTN
    # Generate posterior draws
    numdraws = 20000  # Evaluate choice here
    CSdict3['numPostSamples'] = numdraws
    CSdict3 = methods.GeneratePostSamples(CSdict3)
    # Sourcing-probability matrix; EVALUATE CHOICE HERE
    CSdict3['transMat'] = np.tile(np.sum(CSdict3['N'], axis=0) / np.sum(CSdict3['N']), (4, 1))

    # Utility specification
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(numTN + numSN)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}

    Ndraws = 50
    TNind = 1
    design = np.zeros((numTN))
    design[TNind] = 1.

    numtests = 20

    # COPIED FROM DESIGNUTILITYFUNCTION
    lossveclist = []
    priordatadict, lossdict, designlist = CSdict3.copy(), lossDict.copy(), [design]
    designnames = ['Design 1']


    printUpdate = True
    numNdraws = Ndraws
    # Retrieve prior draws if empty
    priordraws = priordatadict['postSamples']
    Q = priordatadict['transMat']
    currlossvec = []
    # Initialize samples to be drawn from traces, per the design
    sampMat = roundDesignLow(design, numtests)
    Ntilde = sampMat.copy()
    sampNodeInd = 0
    for currind in range(numTN):  # Identify the test node we're analyzing
        if Ntilde[currind] > 0:
            sampNodeInd = currind
    Ntotal, Qvec = int(Ntilde[sampNodeInd]), Q[sampNodeInd]

    time1vec,time2vec, time3vec, time4vec, time5vec = [], [], [], [], []
    numIters=10
    for iter in range(numIters):
        starttime=time.time()
        # Initialize NvecSet with numdatadraws different data sets
        NvecSet = []
        for i in range(numNdraws):
            sampSNvec = choice([i for i in range(numSN)], size=Ntotal,
                               p=Qvec)  # Sample according to the sourcing probabilities
            sampSNvecSums = [sampSNvec.tolist().count(j) for j in range(numSN)]  # Consolidate samples by supply node
            NvecSet.append(sampSNvecSums)
        time1 = time.time() - starttime
        time1vec.append(time1)
        NvecLosses = []  # Initialize a list for the loss under each N vector
        for Nvecind, Nvec in enumerate(NvecSet):
            starttime=time.time()
            randprior = priordraws[random.sample(range(len(priordraws)), k=1)][0]
            zVec = [zProbTr(sampNodeInd, sn, numSN, randprior, sens=s, spec=r) for sn in range(numSN)]
            Yvec = [np.random.binomial(Nvec[sn], zVec[sn]) for sn in range(numSN)]
            sumloss = 0.
            wts = []
            time2=time.time()
            time2vec.append(time2-starttime)
            for currpriordraw in priordraws:  # Get weights for each prior draw
                currwt = 1.0
                for SNind in range(numSN):
                    curry, currn = int(Yvec[SNind]), int(Nvec[SNind])
                    currz = zProbTr(sampNodeInd, SNind, numSN, currpriordraw, sens=s, spec=r)
                    currwt = currwt * (currz ** curry) * ((1 - currz) ** (currn - curry)) * comb(currn, curry)
                wts.append(currwt)  # Add weight for this gamma draw
            # Normalize weights to sum to number of prior draws
            currWtsSum = np.sum(wts)
            wts = [wts[i] * len(priordraws) / currWtsSum for i in range(len(priordraws))]
            time3=time.time()
            time3vec.append(time3-time2)
            # Get Bayes estimate
            currest = bayesEstAdapt(priordraws, wts, lossdict['scoreDict'], printUpdate=False)
            time4=time.time()
            time4vec.append(time4-time3)
            # Sum the weighted loss under each prior draw
            for currsampind, currsamp in enumerate(priordraws):
                currloss = loss_pms(currest, currsamp, lossdict['scoreFunc'], lossdict['scoreDict'],
                                    lossdict['riskFunc'], lossdict['riskDict'], lossdict['marketVec'])
                sumloss += currloss * wts[currsampind]
            NvecLosses.append(sumloss / len(priordraws))
            time5=time.time()
            time5vec.append(time5-time4)
            if printUpdate == True and Nvecind % 5 == 0:
                print('Finished Nvecind of ' + str(Nvecind))
        currlossvec.append(np.average(NvecLosses))
        lossveclist.append(currlossvec)
        print(str(iter)+' done')

    '''
    numtests=5
    time1vec5 = [0.002991199493408203, 0.0019636154174804688, 0.001995086669921875, 0.00193023681640625, 0.002360820770263672, 0.0019922256469726562, 0.0019986629486083984, 0.002994537353515625, 0.002919912338256836, 0.002992868423461914]
    time2vec5 = [0.00035953521728515625, 0.0, 0.000997304916381836, 0.0, 0.0, 7.081031799316406e-05, 0.0, 0.0, 0.0, 0.0006744861602783203, 0.0009975433349609375, 0.0, 0.000997781753540039, 0.0012590885162353516, 0.000997304916381836, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0011074542999267578, 0.0, 0.0, 0.0, 0.0, 0.0009953975677490234, 0.0, 0.0, 0.0, 0.0009622573852539062, 0.0003008842468261719, 0.0, 0.0, 0.0009999275207519531, 0.0010027885437011719, 0.0009996891021728516, 0.0, 0.0, 0.0009970664978027344, 0.0, 0.0, 0.0, 0.0002300739288330078, 0.0009596347808837891, 0.0009431838989257812, 0.0, 0.0, 0.0, 0.0009436607360839844, 0.0, 0.0, 0.0009984970092773438, 0.0, 0.0, 0.0, 0.0, 0.0009241104125976562, 0.0, 0.0, 0.00044083595275878906, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0, 0.0004734992980957031, 0.0009984970092773438, 0.0, 0.0008902549743652344, 0.0, 0.0007011890411376953, 0.001001596450805664, 0.0, 0.0, 0.0010554790496826172, 0.00023102760314941406, 0.0, 0.0, 0.0, 0.001096963882446289, 0.0008590221405029297, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0010731220245361328, 0.000997781753540039, 0.0009982585906982422, 0.0, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0, 0.0002770423889160156, 0.0, 0.0, 0.0, 0.0, 0.000997304916381836, 0.0009980201721191406, 0.0, 0.0009975433349609375, 0.0, 0.00011205673217773438, 0.0, 0.0008654594421386719, 0.0010995864868164062, 0.0011968612670898438, 0.0, 0.0, 0.0009200572967529297, 0.0012538433074951172, 0.0, 0.0009975433349609375, 0.0, 0.0, 0.0011980533599853516, 0.0, 0.000997781753540039, 0.0, 0.0010204315185546875, 0.0, 0.0008943080902099609, 0.0, 0.0010733604431152344, 0.0, 0.0010013580322265625, 0.0, 0.0006532669067382812, 0.0007622241973876953, 0.0015871524810791016, 0.000797271728515625, 0.0, 0.0, 0.0, 0.00021004676818847656, 0.0, 0.0, 0.0009570121765136719, 0.0, 0.0010144710540771484, 0.0, 0.0, 0.0009760856628417969, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0005521774291992188, 0.0008802413940429688, 0.000997304916381836, 0.0, 0.0009584426879882812, 0.0, 0.0, 0.0010001659393310547, 0.0, 0.0002028942108154297, 0.0009975433349609375, 0.000997304916381836, 0.000997781753540039, 0.0009908676147460938, 0.000997304916381836, 0.0, 0.0, 0.0009975433349609375, 0.0, 0.0003287792205810547, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009164810180664062, 0.0, 0.0, 4.482269287109375e-05, 0.000171661376953125, 0.0008454322814941406, 0.0010776519775390625, 0.0, 0.0, 0.0, 0.0, 0.00080108642578125, 0.0, 0.0, 0.0005438327789306641, 0.0, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0009946823120117188, 0.0, 0.0009906291961669922, 0.0009963512420654297, 0.0011262893676757812, 0.0009970664978027344, 0.0, 0.0, 0.0009984970092773438, 0.0, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009975433349609375, 0.0, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009980201721191406, 0.0, 0.0, 0.0009965896606445312, 0.0007023811340332031, 0.0, 0.0007071495056152344, 0.001001119613647461, 0.000997781753540039, 0.0009946823120117188, 0.0, 0.0009970664978027344, 0.0009965896606445312, 0.0, 0.0010342597961425781, 0.0009989738464355469, 0.0, 0.0, 0.0, 0.0009925365447998047, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0010721683502197266, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0008661746978759766, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0008664131164550781, 0.0, 0.0009963512420654297, 0.0009980201721191406, 0.000997781753540039, 0.0009951591491699219, 0.0, 0.0, 0.0009930133819580078, 0.0, 0.0, 0.0, 0.000993490219116211, 0.0009984970092773438, 0.0, 0.0, 0.0008716583251953125, 0.0, 0.0, 0.000993490219116211, 0.0, 0.0, 0.0, 0.0009007453918457031, 0.0, 0.0, 0.0, 0.0, 0.0003695487976074219, 0.0009975433349609375, 0.00046706199645996094, 0.0021736621856689453, 0.0, 0.0009937286376953125, 0.0009970664978027344, 0.0, 0.0, 0.0009961128234863281, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0002276897430419922, 0.0010781288146972656, 0.0, 0.001046895980834961, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00099945068359375, 0.0, 0.0, 0.0, 0.0, 0.0007984638214111328, 0.0009944438934326172, 0.0, 0.0009987354278564453, 0.0009953975677490234, 0.0009968280792236328, 0.0, 0.0009970664978027344, 0.0, 0.000997304916381836, 0.0009949207305908203, 0.0010008811950683594, 0.0, 0.0, 0.0, 0.0010027885437011719, 0.0, 0.0009937286376953125, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0009951591491699219, 0.0, 0.0008795261383056641, 0.0, 0.000997304916381836, 0.0, 0.0009982585906982422, 0.0, 0.0008232593536376953, 0.0, 0.00040531158447265625, 0.0009980201721191406, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.000997304916381836, 0.0, 0.0009975433349609375, 0.0, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0009968280792236328, 0.0001537799835205078, 0.0, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0009062290191650391, 0.0, 0.0, 8.392333984375e-05, 0.0010099411010742188, 0.0010006427764892578, 0.0, 0.0, 0.0, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.0011014938354492188, 0.0009987354278564453, 0.0, 0.0, 0.0, 0.0011081695556640625, 0.0009894371032714844, 0.0, 0.0010409355163574219, 0.0009186267852783203, 0.0, 0.0011286735534667969, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0010976791381835938, 0.0, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0008516311645507812, 0.0, 0.0, 0.0, 0.000995635986328125, 0.0, 0.0, 0.0, 0.000997304916381836, 0.0009982585906982422, 0.0009980201721191406, 0.0, 0.0009951591491699219, 0.0, 0.0, 0.0009980201721191406, 0.0009984970092773438, 0.0, 0.0009970664978027344, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0, 0.000997304916381836, 0.0002315044403076172, 0.000997781753540039, 0.0009961128234863281, 0.0009665489196777344, 0.000152587890625, 0.0, 0.000997781753540039, 0.001087188720703125, 0.000997304916381836, 0.0, 0.0008754730224609375, 0.0010001659393310547, 0.0, 0.0009970664978027344, 0.0, 0.0010967254638671875, 0.0, 0.0, 0.0, 0.0, 0.0010111331939697266, 0.0, 0.0, 0.0, 0.0, 0.0, 0.000997304916381836, 0.001985788345336914, 0.00031948089599609375, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.000990152359008789, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.0]
    time3vec5 = [0.835712194442749, 0.7777602672576904, 0.7691824436187744, 1.9309191703796387, 1.150343894958496, 1.0199816226959229, 1.0850679874420166, 1.0078463554382324, 0.7296266555786133, 1.0041217803955078, 0.7883026599884033, 0.9850068092346191, 2.3697071075439453, 1.3773589134216309, 1.736917495727539, 0.9572305679321289, 0.7989394664764404, 1.0888895988464355, 2.577759027481079, 0.7652192115783691, 0.7313125133514404, 0.738710880279541, 0.7246277332305908, 0.7461574077606201, 0.7292470932006836, 0.7337729930877686, 0.767247200012207, 0.7225437164306641, 0.73274827003479, 0.7546186447143555, 0.7299990653991699, 0.7353529930114746, 0.7372920513153076, 1.0407984256744385, 0.8035709857940674, 0.7302067279815674, 0.775292158126831, 0.7673161029815674, 0.76910400390625, 0.7383415699005127, 0.749321460723877, 0.7985053062438965, 0.7815940380096436, 1.1454851627349854, 0.7219352722167969, 0.7418460845947266, 0.7521398067474365, 0.753258228302002, 0.728395938873291, 0.7391695976257324, 0.7439775466918945, 0.7421529293060303, 0.7310516834259033, 0.7406232357025146, 0.7376563549041748, 0.8137307167053223, 1.3930344581604004, 1.1658711433410645, 1.1811010837554932, 1.4817709922790527, 1.4998784065246582, 1.0083396434783936, 1.0650224685668945, 0.9296731948852539, 1.6640937328338623, 1.0719923973083496, 0.9823689460754395, 0.8707845211029053, 1.070594072341919, 0.7796449661254883, 0.7580695152282715, 0.8534388542175293, 0.9950785636901855, 0.8503179550170898, 1.0248231887817383, 0.9222240447998047, 1.4042339324951172, 1.0806207656860352, 0.9308669567108154, 1.167470932006836, 1.152587890625, 1.1911640167236328, 1.340111494064331, 1.1173484325408936, 1.06339430809021, 1.1130375862121582, 1.0327305793762207, 1.0418083667755127, 1.0392539501190186, 0.9881584644317627, 0.9334774017333984, 0.9310495853424072, 1.0153753757476807, 0.9878063201904297, 0.9770228862762451, 1.036531925201416, 1.2725152969360352, 1.1230168342590332, 1.1362860202789307, 1.103081226348877, 1.0173444747924805, 1.3174083232879639, 0.9800539016723633, 1.0251057147979736, 1.0159127712249756, 1.0790760517120361, 0.989293098449707, 1.044494867324829, 1.1471543312072754, 1.070127248764038, 1.401461124420166, 1.0653693675994873, 0.9282422065734863, 0.992328405380249, 1.3469576835632324, 0.9567978382110596, 1.1909475326538086, 0.9893109798431396, 1.0812230110168457, 1.0319106578826904, 1.0791289806365967, 1.0825541019439697, 1.1018879413604736, 1.0940678119659424, 1.1172077655792236, 1.0828766822814941, 1.1126072406768799, 1.0482070446014404, 1.0543029308319092, 1.0691535472869873, 1.1346523761749268, 1.0422372817993164, 1.1467409133911133, 1.2805695533752441, 1.145003318786621, 1.028123140335083, 1.0794200897216797, 0.995436429977417, 1.041938066482544, 0.8473379611968994, 0.7963180541992188, 0.8238849639892578, 0.8419787883758545, 1.219236135482788, 1.1097097396850586, 1.060288906097412, 1.0568926334381104, 0.8775668144226074, 1.0225589275360107, 1.1177408695220947, 1.0178782939910889, 0.9923810958862305, 0.9605133533477783, 1.1358959674835205, 0.9321584701538086, 0.9479620456695557, 1.3486497402191162, 1.0532922744750977, 0.9562678337097168, 1.0232956409454346, 1.0840625762939453, 1.0233590602874756, 1.0093779563903809, 0.8975965976715088, 1.013288974761963, 1.0092673301696777, 0.9764225482940674, 0.9007096290588379, 1.087095022201538, 0.9893527030944824, 0.9484975337982178, 1.0079748630523682, 0.96750807762146, 0.876654863357544, 0.9405865669250488, 1.0341987609863281, 0.9025819301605225, 0.9496746063232422, 0.7687642574310303, 0.9374597072601318, 0.93245530128479, 0.8904097080230713, 0.8347663879394531, 0.9275538921356201, 0.9604291915893555, 0.9036173820495605, 0.8855390548706055, 0.9554438591003418, 0.8387539386749268, 0.8098349571228027, 0.8766224384307861, 0.9130117893218994, 0.9335026741027832, 0.961463451385498, 1.038222074508667, 0.7711493968963623, 1.1010479927062988, 0.8846275806427002, 1.0531854629516602, 0.999528169631958, 0.8084337711334229, 0.8716661930084229, 0.7439780235290527, 0.8944704532623291, 0.8328070640563965, 0.8437044620513916, 0.994452714920044, 0.7939088344573975, 0.956406831741333, 0.8527193069458008, 0.9185760021209717, 0.8088705539703369, 0.9763875007629395, 0.8297781944274902, 1.0743589401245117, 1.0830683708190918, 0.9025876522064209, 1.1060442924499512, 1.0302093029022217, 0.9584352970123291, 0.8856697082519531, 0.9094698429107666, 1.0203120708465576, 0.9323627948760986, 0.8756582736968994, 0.9463720321655273, 0.926520586013794, 1.019273042678833, 0.8606958389282227, 0.9704113006591797, 0.8587064743041992, 0.8167147636413574, 0.9943404197692871, 0.9932692050933838, 0.9215035438537598, 1.0282447338104248, 0.8078365325927734, 1.0353500843048096, 1.051191806793213, 1.2666335105895996, 0.9923491477966309, 0.7971580028533936, 1.0870890617370605, 0.907573938369751, 0.8497295379638672, 0.9424464702606201, 0.830812931060791, 0.975391149520874, 1.0571391582489014, 0.981342077255249, 0.8586702346801758, 0.919543981552124, 0.8786494731903076, 0.9544472694396973, 0.7968335151672363, 0.8966009616851807, 1.033517599105835, 0.8158528804779053, 0.9234886169433594, 0.9614646434783936, 0.9984643459320068, 1.1857514381408691, 1.0152795314788818, 0.8646876811981201, 0.8607292175292969, 0.8766546249389648, 1.0312066078186035, 0.8656508922576904, 0.9763858318328857, 0.9345476627349854, 0.9853317737579346, 0.9006285667419434, 0.994375467300415, 0.8946092128753662, 0.9704000949859619, 0.981374979019165, 1.087245225906372, 0.8267784118652344, 0.9124894142150879, 0.8357315063476562, 0.8627264499664307, 0.9264805316925049, 0.8327362537384033, 1.2695999145507812, 0.9066035747528076, 0.9125645160675049, 1.0791444778442383, 0.9213225841522217, 0.844628095626831, 0.980377197265625, 0.8855981826782227, 1.012296199798584, 0.9773893356323242, 0.8836078643798828, 0.9903488159179688, 0.9863607883453369, 0.9385221004486084, 0.9345047473907471, 0.800858736038208, 0.899641752243042, 1.0162882804870605, 0.9704368114471436, 1.0182766914367676, 1.0213441848754883, 0.8956053256988525, 1.4620881080627441, 0.839012622833252, 1.2177767753601074, 0.9244375228881836, 1.0797512531280518, 1.1270506381988525, 1.2890243530273438, 1.1982431411743164, 1.1209685802459717, 1.017526388168335, 1.0961005687713623, 1.035231351852417, 1.100027322769165, 1.0013179779052734, 1.152909278869629, 1.0254168510437012, 1.0960321426391602, 1.0562291145324707, 1.092078685760498, 1.0792651176452637, 1.0860495567321777, 1.0162484645843506, 1.2356727123260498, 1.005342960357666, 1.1050775051116943, 1.0391662120819092, 1.1050465106964111, 1.0272176265716553, 1.0830998420715332, 1.0442044734954834, 1.1018917560577393, 1.0332677364349365, 1.1110262870788574, 1.0940709114074707, 1.120145320892334, 1.0621240139007568, 1.1230669021606445, 1.0601685047149658, 1.2496538162231445, 1.0611610412597656, 1.1269845962524414, 1.127004623413086, 1.2307417392730713, 1.1289477348327637, 1.114086389541626, 1.1309661865234375, 1.073974847793579, 1.1339671611785889, 1.040212869644165, 1.1329686641693115, 1.0362281799316406, 1.1170108318328857, 1.016352653503418, 1.128979206085205, 1.0541861057281494, 1.1419553756713867, 1.1446044445037842, 1.2576358318328857, 0.9956951141357422, 1.0602524280548096, 0.8656885623931885, 0.758112907409668, 1.0023729801177979, 1.1319348812103271, 0.7740821838378906, 1.0980279445648193, 1.093749761581421, 1.022228479385376, 0.9067485332489014, 0.8966014385223389, 0.8528022766113281, 0.9404020309448242, 0.8277840614318848, 0.8905329704284668, 1.0432088375091553, 0.9205358028411865, 0.9145534038543701, 0.8397495746612549, 0.7170803546905518, 1.158874273300171, 0.953449010848999, 0.9972779750823975, 1.036226511001587, 0.8706703186035156, 0.8297786712646484, 0.9484624862670898, 1.119006872177124, 0.8876247406005859, 0.8546113967895508, 0.8838121891021729, 1.00419282913208, 0.8526701927185059, 0.8576698303222656, 0.976388692855835, 0.9644198417663574, 0.7968690395355225, 1.00630784034729, 0.8995950222015381, 1.0411581993103027, 1.0900826454162598, 1.068037986755371, 1.305506706237793, 1.0282490253448486, 0.8706686496734619, 1.0102949142456055, 0.9443273544311523, 0.9345130920410156, 1.024259090423584, 0.878605842590332, 0.840752124786377, 0.8985939025878906, 0.9194111824035645, 1.1090734004974365, 0.9189138412475586, 0.873664140701294, 0.7599325180053711, 0.9216670989990234, 0.9694080352783203, 0.9095680713653564, 1.0272846221923828, 0.8626272678375244, 0.9085700511932373, 0.9165844917297363, 0.8935773372650146, 0.7450418472290039, 0.8876245021820068, 0.9155879020690918, 1.0651524066925049, 0.9325072765350342, 0.988349437713623, 1.235694169998169, 1.2048943042755127, 1.200674057006836, 1.217742681503296, 0.7230653762817383, 0.7748916149139404, 0.7350313663482666, 0.725055456161499, 0.7030870914459229, 0.7011241912841797, 0.7809898853302002, 0.7450041770935059, 0.7549793720245361, 0.7190773487091064, 0.7131264209747314, 0.7041153907775879, 0.715085506439209, 0.7679469585418701, 0.919539213180542, 0.7410187721252441, 0.8746597766876221, 0.7380244731903076, 0.741016149520874, 0.738762378692627, 0.694176435470581, 0.731008768081665, 0.7479989528656006, 0.722912073135376, 0.7160792350769043, 0.7750368118286133, 0.8505995273590088, 0.7081377506256104, 0.7091326713562012, 0.7161831855773926, 0.7758851051330566, 0.7390544414520264, 0.7370283603668213, 0.7339613437652588, 0.7349348068237305, 0.7270896434783936, 0.7619514465332031, 0.80484938621521, 1.285560131072998, 1.3862781524658203, 0.9676165580749512, 0.8716695308685303, 0.9760663509368896, 0.746999979019165, 0.763923168182373, 0.7470335960388184, 1.210756778717041, 1.2932507991790771, 1.089085340499878, 0.7398886680603027, 0.7480676174163818, 0.7230656147003174, 0.7368824481964111, 0.7649209499359131, 0.7609620094299316, 0.786933422088623, 0.7619593143463135, 0.7549958229064941, 0.7489316463470459, 0.7290134429931641, 0.7130603790283203]
    time4vec5 = [0.4810800552368164, 0.4533987045288086, 0.47845888137817383, 0.564298152923584, 0.7013795375823975, 0.9736025333404541, 0.5173037052154541, 0.4648599624633789, 0.42061471939086914, 0.5949685573577881, 0.5977444648742676, 0.47650671005249023, 0.8692727088928223, 0.5719814300537109, 2.1473941802978516, 0.4333035945892334, 1.2436137199401855, 0.569441556930542, 0.7031958103179932, 0.42413854598999023, 0.43834733963012695, 0.4171483516693115, 0.42765021324157715, 0.4166727066040039, 0.4388258457183838, 0.40529751777648926, 0.4447977542877197, 0.4206976890563965, 0.4403238296508789, 0.4040665626525879, 0.44274258613586426, 0.41943931579589844, 0.438183069229126, 0.6940619945526123, 0.4381535053253174, 0.4156227111816406, 0.4458310604095459, 0.4765944480895996, 0.4636194705963135, 0.417816162109375, 0.42078590393066406, 0.4437835216522217, 0.42812657356262207, 0.6124160289764404, 0.4365255832672119, 0.42627954483032227, 0.4096865653991699, 0.45209741592407227, 0.4187600612640381, 0.4299051761627197, 0.4124143123626709, 0.43460845947265625, 0.3996574878692627, 0.439028263092041, 0.40117526054382324, 0.5099728107452393, 0.7258114814758301, 1.2410755157470703, 0.8994460105895996, 0.8676989078521729, 0.8001599311828613, 0.6139135360717773, 0.6851773262023926, 0.631892204284668, 1.4428040981292725, 0.5649538040161133, 0.5034809112548828, 0.6484513282775879, 0.5848269462585449, 0.4092717170715332, 0.5216717720031738, 0.5249724388122559, 0.6060101985931396, 0.5508472919464111, 0.5183780193328857, 0.4758646488189697, 0.8530261516571045, 0.5500133037567139, 0.5599684715270996, 0.6761343479156494, 0.6603648662567139, 0.5957298278808594, 0.9882769584655762, 0.6082808971405029, 0.647705078125, 0.5500640869140625, 0.5826449394226074, 0.5480353832244873, 0.9747180938720703, 0.562075138092041, 0.5261242389678955, 0.538830041885376, 0.5758745670318604, 0.5359847545623779, 0.553215742111206, 0.9190776348114014, 0.6523628234863281, 0.6011488437652588, 0.7237787246704102, 0.6209073066711426, 1.1540281772613525, 0.6408200263977051, 0.542736291885376, 0.5470852851867676, 0.55910325050354, 0.5838823318481445, 0.5653221607208252, 0.6989078521728516, 0.6724851131439209, 0.6048591136932373, 0.6288206577301025, 0.5009703636169434, 0.5101542472839355, 0.4907505512237549, 0.7816500663757324, 0.5660703182220459, 0.6865437030792236, 0.5239601135253906, 0.5568609237670898, 0.5560200214385986, 0.9597225189208984, 0.6230266094207764, 0.6341285705566406, 0.6893556118011475, 0.6226208209991455, 0.6393280029296875, 0.7042245864868164, 0.6295719146728516, 0.6169137954711914, 0.629326343536377, 0.6063899993896484, 0.6481232643127441, 0.6386094093322754, 0.7067885398864746, 0.6666288375854492, 0.6589610576629639, 0.6089835166931152, 0.6281998157501221, 0.5529842376708984, 0.4930412769317627, 0.4999873638153076, 0.4965043067932129, 0.5310611724853516, 0.6428964138031006, 0.6030449867248535, 0.5998873710632324, 0.576188325881958, 0.484921932220459, 0.535832405090332, 0.5269207954406738, 0.5270419120788574, 0.4850282669067383, 0.5282843112945557, 0.7166919708251953, 0.49764394760131836, 0.40328335762023926, 0.5946824550628662, 0.6008138656616211, 0.7529878616333008, 0.581899881362915, 0.6492633819580078, 0.4806966781616211, 0.5605533123016357, 0.4769175052642822, 0.5081474781036377, 0.4797484874725342, 0.4589517116546631, 0.4865751266479492, 0.5794506072998047, 0.40395522117614746, 0.43081212043762207, 0.45381951332092285, 0.5154895782470703, 0.8227701187133789, 0.5684092044830322, 0.4298818111419678, 0.4797186851501465, 0.4784717559814453, 0.4946765899658203, 0.43088293075561523, 0.4368009567260742, 0.5066461563110352, 0.4808182716369629, 0.528468132019043, 0.5096704959869385, 0.5146210193634033, 0.4079091548919678, 0.5664846897125244, 0.5325753688812256, 0.4857010841369629, 0.46475696563720703, 0.41887974739074707, 0.4308474063873291, 0.45275354385375977, 0.5315783023834229, 0.8744480609893799, 0.9743928909301758, 0.4498026371002197, 0.6013920307159424, 0.4485938549041748, 0.5385596752166748, 0.5724711418151855, 0.5106339454650879, 0.4976675510406494, 0.5205729007720947, 0.495708703994751, 0.5274748802185059, 0.503650426864624, 0.4617650508880615, 0.4041619300842285, 0.45175719261169434, 0.49767184257507324, 0.42702388763427734, 0.45179152488708496, 0.5991635322570801, 0.5914187431335449, 0.44580626487731934, 0.9305088520050049, 0.5345687866210938, 0.5634934902191162, 0.5315375328063965, 0.5335714817047119, 0.5573992729187012, 0.5226023197174072, 0.537738561630249, 0.4996635913848877, 0.44780421257019043, 0.44381260871887207, 0.502657413482666, 0.5226016044616699, 0.47273921966552734, 0.44078779220581055, 0.57944655418396, 0.48270583152770996, 0.5566790103912354, 0.4417850971221924, 0.5595052242279053, 0.44269537925720215, 0.46076369285583496, 0.4886934757232666, 0.4667506217956543, 0.43793177604675293, 0.5198230743408203, 0.5196104049682617, 0.5265953540802002, 0.4578087329864502, 0.45678162574768066, 0.4288504123687744, 0.46777820587158203, 0.512667179107666, 0.5128459930419922, 0.47472691535949707, 0.5345699787139893, 0.4777534008026123, 0.5056805610656738, 0.5305836200714111, 0.5562317371368408, 0.5246732234954834, 0.4886927604675293, 0.4677438735961914, 0.5095024108886719, 0.5326085090637207, 0.5046513080596924, 0.5634927749633789, 0.5445418357849121, 0.5385274887084961, 0.4059159755706787, 0.5136616230010986, 0.4338076114654541, 0.4527413845062256, 0.4447968006134033, 0.4308459758758545, 0.4717395305633545, 0.5106019973754883, 0.4797194004058838, 0.44082069396972656, 0.40775632858276367, 0.5056495666503906, 0.5335729122161865, 0.5056507587432861, 0.4976680278778076, 0.5495693683624268, 0.4916863441467285, 0.6512911319732666, 0.4477710723876953, 0.4837038516998291, 0.5465402603149414, 0.4589042663574219, 0.5027635097503662, 0.4938802719116211, 0.5166184902191162, 0.5106263160705566, 0.531578779220581, 0.4937131404876709, 0.583442211151123, 0.5086424350738525, 0.5285549163818359, 0.4697084426879883, 0.5056793689727783, 0.5065951347351074, 0.4627232551574707, 0.45474886894226074, 0.5116317272186279, 0.5095269680023193, 0.4956376552581787, 0.5306146144866943, 0.46749234199523926, 0.4866633415222168, 0.45977282524108887, 0.5335707664489746, 0.6846652030944824, 0.5925722122192383, 0.5684754848480225, 0.5287516117095947, 0.58418869972229, 0.548529863357544, 0.5555140972137451, 0.5405540466308594, 0.5574789047241211, 0.559502363204956, 0.5753004550933838, 0.631342887878418, 0.5524327754974365, 0.5255904197692871, 0.8084509372711182, 0.5585403442382812, 0.6812088489532471, 0.5744690895080566, 0.550529956817627, 0.5664889812469482, 0.5585060119628906, 0.5525193214416504, 0.5575089454650879, 0.5834388732910156, 0.5595099925994873, 0.5535256862640381, 0.5425536632537842, 0.5465381145477295, 0.5435454845428467, 0.5683505535125732, 0.48872923851013184, 0.5335729122161865, 0.5455071926116943, 0.8108024597167969, 0.5476293563842773, 0.561464786529541, 0.567497730255127, 0.5705196857452393, 0.5685138702392578, 0.5505280494689941, 0.5654952526092529, 0.5565485954284668, 0.5426979064941406, 0.5784540176391602, 0.5565106868743896, 0.5474996566772461, 0.5535509586334229, 0.5365996360778809, 0.5654864311218262, 0.6123590469360352, 0.8228306770324707, 0.6043820381164551, 0.5954403877258301, 0.5352432727813721, 0.5395240783691406, 0.5235960483551025, 0.7378854751586914, 0.5863771438598633, 0.4777224063873291, 0.4656360149383545, 0.6273207664489746, 0.5679574012756348, 0.5934159755706787, 0.5663089752197266, 0.48171114921569824, 0.5155375003814697, 0.5295524597167969, 0.43184590339660645, 0.4617650508880615, 0.4687464237213135, 0.4996635913848877, 0.3839731216430664, 0.49364757537841797, 0.5425488948822021, 0.5226621627807617, 0.3859679698944092, 0.4327411651611328, 0.47672414779663086, 0.5445454120635986, 0.441021203994751, 0.46299266815185547, 0.5196094512939453, 0.4188809394836426, 0.5216050148010254, 0.46457910537719727, 0.4149515628814697, 0.5734660625457764, 0.43601298332214355, 0.4478025436401367, 0.4797499179840088, 0.47073936462402344, 0.5136263370513916, 0.47073912620544434, 0.4079105854034424, 0.41588759422302246, 0.45179319381713867, 0.5924136638641357, 0.4478018283843994, 0.44496750831604004, 0.5345714092254639, 0.5026543140411377, 0.49666690826416016, 0.5196034908294678, 0.46475744247436523, 0.4597642421722412, 0.5315437316894531, 0.5156147480010986, 0.4547755718231201, 0.43742871284484863, 0.4198775291442871, 0.47775816917419434, 0.547400951385498, 0.46372461318969727, 0.47077107429504395, 0.35801076889038086, 0.4976675510406494, 0.4248623847961426, 0.47971200942993164, 0.8407478332519531, 0.5564758777618408, 0.4537527561187744, 0.6043436527252197, 0.4828357696533203, 0.5048246383666992, 0.5405604839324951, 0.8636913299560547, 0.933518648147583, 0.8028521537780762, 0.43686628341674805, 0.3889617919921875, 0.44580841064453125, 0.40491676330566406, 0.40303945541381836, 0.3999311923980713, 0.42789530754089355, 0.5245969295501709, 0.5375955104827881, 0.39157748222351074, 0.4179213047027588, 0.38903188705444336, 0.4308812618255615, 0.5754642486572266, 0.4469916820526123, 0.4338383674621582, 0.42107319831848145, 0.5206074714660645, 0.41292786598205566, 0.39295029640197754, 0.4109001159667969, 0.392946720123291, 0.4009273052215576, 0.44085693359375, 0.44550609588623047, 0.40890049934387207, 0.41780591011047363, 0.4109337329864502, 0.3919205665588379, 0.3829476833343506, 0.40976929664611816, 0.40192699432373047, 0.4427826404571533, 0.4278876781463623, 0.4089071750640869, 0.4358327388763428, 0.39992809295654297, 0.7270469665527344, 0.7941970825195312, 0.9416182041168213, 0.7210712432861328, 0.45182299613952637, 0.43480873107910156, 0.5245656967163086, 0.4259366989135742, 0.39893484115600586, 0.4310472011566162, 0.8148198127746582, 0.805814266204834, 0.7978670597076416, 0.3820176124572754, 0.4098331928253174, 0.39693689346313477, 0.39098238945007324, 0.41887879371643066, 0.44271111488342285, 0.4520294666290283, 0.4169032573699951, 0.42299365997314453, 0.4078965187072754, 0.39693641662597656, 0.39394593238830566]
    time5vec5 = [1.1147100925445557, 1.0429153442382812, 2.1146433353424072, 1.5752010345458984, 1.2217755317687988, 1.1764640808105469, 3.0027050971984863, 1.0141026973724365, 1.1560289859771729, 1.2367498874664307, 1.0339868068695068, 1.1208462715148926, 2.9180240631103516, 1.103841781616211, 1.5173683166503906, 1.017371416091919, 2.7651400566101074, 1.8720924854278564, 1.287327527999878, 1.005584955215454, 0.9666211605072021, 0.9787611961364746, 0.9913036823272705, 0.9767296314239502, 0.9870502948760986, 0.9873487949371338, 0.9634151458740234, 0.9879207611083984, 0.9860897064208984, 1.0082707405090332, 0.9950876235961914, 1.0035958290100098, 1.064950942993164, 1.3312206268310547, 0.9584362506866455, 1.037938117980957, 1.0097479820251465, 0.9911694526672363, 1.0321662425994873, 1.0047836303710938, 1.0467517375946045, 1.0294787883758545, 2.862985610961914, 1.0583457946777344, 0.9990394115447998, 0.9812684059143066, 1.0176961421966553, 0.9775118827819824, 0.9649786949157715, 1.01997709274292, 0.9972171783447266, 0.9997360706329346, 0.9923291206359863, 1.0593819618225098, 0.9714274406433105, 1.8980371952056885, 1.579890489578247, 1.9761936664581299, 2.055328130722046, 2.0732176303863525, 1.5277178287506104, 1.4947786331176758, 1.491795301437378, 1.837536334991455, 1.4212546348571777, 1.504866361618042, 1.326960802078247, 1.2619247436523438, 0.9942750930786133, 1.006181240081787, 1.2442240715026855, 1.4338788986206055, 1.2288062572479248, 1.2159135341644287, 1.2726695537567139, 1.33180570602417, 1.5379664897918701, 1.260361671447754, 1.281623125076294, 1.52642822265625, 1.4573006629943848, 1.5018196105957031, 1.5504035949707031, 1.4346685409545898, 1.8430092334747314, 1.418360710144043, 1.3031315803527832, 1.4192166328430176, 1.3910183906555176, 1.1829030513763428, 1.3107714653015137, 1.396169900894165, 1.223376750946045, 1.317101240158081, 1.4759001731872559, 1.993812084197998, 1.4809317588806152, 1.4909262657165527, 1.507019281387329, 1.490727186203003, 1.5836601257324219, 1.2819654941558838, 1.451920509338379, 1.3910765647888184, 1.5301520824432373, 1.376399040222168, 1.3933477401733398, 1.8418025970458984, 1.4675893783569336, 1.5728144645690918, 1.522737979888916, 1.2335209846496582, 1.3755805492401123, 1.4300830364227295, 1.7932672500610352, 1.2729573249816895, 1.521500825881958, 1.3946785926818848, 1.3760044574737549, 1.3337936401367188, 1.5635995864868164, 1.4259514808654785, 1.559873342514038, 1.4448132514953613, 1.5302231311798096, 1.3939642906188965, 1.5591707229614258, 1.5117998123168945, 1.5568599700927734, 1.5398640632629395, 1.4950039386749268, 1.5244054794311523, 1.8580138683319092, 1.5201923847198486, 1.5214345455169678, 1.5898408889770508, 1.604663610458374, 1.483327865600586, 1.130422830581665, 1.110093355178833, 1.1159238815307617, 1.0673460960388184, 2.0618903636932373, 1.4994399547576904, 1.3877027034759521, 1.475111961364746, 1.3111770153045654, 1.365039587020874, 1.267822265625, 1.2306602001190186, 1.1240487098693848, 1.3169739246368408, 1.5552818775177002, 1.4793107509613037, 1.1560471057891846, 1.329538106918335, 1.292754888534546, 1.5220584869384766, 1.939807653427124, 1.3888275623321533, 1.5008940696716309, 1.2935070991516113, 1.2525520324707031, 1.3711395263671875, 1.2182374000549316, 1.267577886581421, 1.289370059967041, 1.3523826599121094, 1.2895128726959229, 1.1857917308807373, 1.026254415512085, 1.4361579418182373, 1.3135168552398682, 1.819129228591919, 1.3055083751678467, 1.3284499645233154, 1.231783390045166, 1.3715097904205322, 1.4491546154022217, 1.317476749420166, 1.2117919921875, 1.2557909488677979, 1.3961966037750244, 1.2765519618988037, 1.3473601341247559, 1.2676458358764648, 1.3084971904754639, 1.2887506484985352, 1.337421178817749, 1.2895801067352295, 1.365346908569336, 1.140946865081787, 1.2646162509918213, 1.3543758392333984, 1.2027816772460938, 1.4332613945007324, 1.4900174140930176, 1.2506484985351562, 1.412257194519043, 1.2217371463775635, 1.307541847229004, 1.3204646110534668, 1.2875967025756836, 1.213719129562378, 1.2397222518920898, 1.3384182453155518, 1.2077348232269287, 1.3872897624969482, 1.1758546829223633, 1.0698938369750977, 1.3005213737487793, 1.272589921951294, 1.2444710731506348, 1.4162120819091797, 1.4691026210784912, 1.437185525894165, 1.2246901988983154, 1.5519382953643799, 1.2875547409057617, 1.568802833557129, 1.1689705848693848, 1.2287802696228027, 1.161036491394043, 1.4590950012207031, 1.1727795600891113, 1.321465015411377, 1.2765820026397705, 1.2456684112548828, 1.1819188594818115, 1.3872809410095215, 1.1589930057525635, 1.4770824909210205, 1.3065059185028076, 1.379340648651123, 1.2435088157653809, 1.3254923820495605, 1.1299736499786377, 1.3164775371551514, 1.74261474609375, 1.270592451095581, 1.3633172512054443, 1.4340953826904297, 1.3162593841552734, 1.254643201828003, 1.2326958179473877, 1.1349291801452637, 1.1848227977752686, 1.4032487869262695, 1.3583691120147705, 1.226715326309204, 1.2225422859191895, 1.2656161785125732, 1.2695677280426025, 1.2696106433868408, 1.3214619159698486, 1.2077672481536865, 1.2027475833892822, 1.0940005779266357, 1.2496552467346191, 1.2007911205291748, 1.6704943180084229, 1.3902831077575684, 1.238652229309082, 1.3114910125732422, 1.3174750804901123, 1.434196949005127, 1.2985570430755615, 1.1579012870788574, 1.136958360671997, 1.285640001296997, 1.31358003616333, 1.2865209579467773, 1.2686374187469482, 1.1948387622833252, 1.135960578918457, 1.3085684776306152, 1.3493988513946533, 1.2058079242706299, 1.3583977222442627, 1.1459317207336426, 1.2846994400024414, 1.3683350086212158, 1.4441394805908203, 1.3004884719848633, 1.2147815227508545, 1.224689245223999, 1.1950149536132812, 1.2695856094360352, 1.2854197025299072, 1.3153116703033447, 1.1858618259429932, 1.2895493507385254, 1.2336947917938232, 1.3214621543884277, 1.1927738189697266, 1.1748533248901367, 1.197950839996338, 1.2157456874847412, 1.1857945919036865, 1.4122531414031982, 1.1040470600128174, 1.360396385192871, 1.2416741847991943, 1.2069029808044434, 1.3154809474945068, 1.3274130821228027, 1.2696027755737305, 1.2407689094543457, 1.3466782569885254, 1.293506145477295, 1.540048599243164, 1.3667566776275635, 1.3763206005096436, 1.518805980682373, 1.5139167308807373, 1.5209317207336426, 1.5618159770965576, 1.5359265804290771, 1.5129880905151367, 1.486027717590332, 1.5338966846466064, 1.557835340499878, 1.5089964866638184, 1.5269224643707275, 1.7523164749145508, 1.4650802612304688, 1.797159194946289, 1.4780101776123047, 1.527876853942871, 1.5160624980926514, 1.5309038162231445, 1.4501886367797852, 1.4871256351470947, 1.5338993072509766, 1.4951512813568115, 1.4590580463409424, 1.5588276386260986, 1.402482509613037, 1.5239224433898926, 1.3194615840911865, 1.533893346786499, 1.3822979927062988, 1.5658414363861084, 1.4980268478393555, 1.5767724514007568, 1.3902795314788818, 1.5827946662902832, 1.3703675270080566, 1.5019822120666504, 1.44313645362854, 1.4961130619049072, 1.4620823860168457, 1.556684970855713, 1.5109565258026123, 1.5309484004974365, 1.4421424865722656, 1.4291441440582275, 1.5239202976226807, 1.4920079708099365, 1.6525685787200928, 1.5028398036956787, 1.4580674171447754, 1.402332067489624, 1.3953042030334473, 1.3304378986358643, 0.9933407306671143, 1.298525333404541, 1.4661121368408203, 1.1570792198181152, 1.4351601600646973, 1.259629249572754, 1.5074436664581299, 1.6126830577850342, 1.3683385848999023, 1.1748566627502441, 1.2336986064910889, 1.0312409400939941, 1.1549932956695557, 1.304509162902832, 1.1549110412597656, 1.259629249572754, 1.3105292320251465, 1.19081449508667, 1.7323899269104004, 1.1967382431030273, 1.2187395095825195, 1.075124740600586, 1.313486099243164, 1.258631706237793, 1.291344165802002, 1.245436429977417, 1.2188305854797363, 1.3325350284576416, 1.146932601928711, 1.2177770137786865, 1.2147243022918701, 1.1489579677581787, 1.3362455368041992, 1.189814805984497, 1.316516637802124, 1.3493895530700684, 1.265613079071045, 1.3065602779388428, 1.199789047241211, 1.3144829273223877, 1.2925422191619873, 1.2526471614837646, 1.0870931148529053, 1.3083438873291016, 1.2148246765136719, 1.4002866744995117, 1.1618926525115967, 1.2975006103515625, 1.1859395503997803, 1.3194754123687744, 1.1599304676055908, 1.253615379333496, 1.2366862297058105, 1.259629249572754, 1.2536790370941162, 1.1569044589996338, 1.2277140617370605, 1.2516508102416992, 1.2795453071594238, 1.364346981048584, 1.210726261138916, 1.3414108753204346, 1.4351637363433838, 1.5099592208862305, 1.3683741092681885, 1.2707479000091553, 1.6436355113983154, 1.3592321872711182, 1.3153057098388672, 1.2645840644836426, 1.6540911197662354, 1.680483102798462, 1.634627103805542, 0.9813368320465088, 0.9574713706970215, 1.0122909545898438, 0.9455051422119141, 0.9692935943603516, 0.9614274501800537, 0.9554033279418945, 1.0571715831756592, 1.047166109085083, 0.9368665218353271, 0.95839524269104, 0.9673066139221191, 0.9344656467437744, 1.1997861862182617, 1.2881321907043457, 0.9793810844421387, 0.9642534255981445, 1.1050083637237549, 1.0571403503417969, 0.9943702220916748, 0.9923436641693115, 0.9404873847961426, 1.012876272201538, 0.988318920135498, 1.0532245635986328, 0.9867269992828369, 1.0242598056793213, 0.9743599891662598, 0.9634206295013428, 0.97355055809021, 1.0063438415527344, 0.9604291915893555, 0.9853634834289551, 0.9744353294372559, 1.0133225917816162, 0.9524173736572266, 1.0033018589019775, 1.2825689315795898, 1.6751930713653564, 2.321650981903076, 1.6176741123199463, 0.9987235069274902, 0.9983248710632324, 0.9993255138397217, 0.968367338180542, 1.1768476963043213, 1.2993059158325195, 1.6655433177947998, 1.6705293655395508, 1.1739885807037354, 0.965378999710083, 0.9863624572753906, 0.9725451469421387, 1.002542495727539, 1.0192739963531494, 1.0629286766052246, 1.1066923141479492, 0.9963231086730957, 0.9843168258666992, 0.9524567127227783, 0.9744265079498291, 1.044205904006958]
    
    numtests=20
    time1vec = [0.0020170211791992188, 0.006106138229370117, 0.0029892921447753906, 0.002991914749145508, 0.0039920806884765625, 0.004987955093383789, 0.003991603851318359, 0.0060939788818359375, 0.004988193511962891, 0.0039632320404052734]
    time2vec = [0.0, 0.0, 0.0, 0.0, 0.0009913444519042969, 0.0, 0.0, 0.0009975433349609375, 0.0, 0.0, 0.0, 0.0002231597900390625, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0, 0.0009996891021728516, 0.0, 0.0, 0.0, 0.0, 0.00021982192993164062, 0.0, 0.0, 0.0, 0.0, 0.0009975433349609375, 0.0009975433349609375, 0.0011136531829833984, 0.0, 0.0, 0.0, 0.0009970664978027344, 0.0009989738464355469, 0.0, 0.0, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0003933906555175781, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.000997304916381836, 0.0009984970092773438, 0.0009984970092773438, 0.0, 0.0009980201721191406, 0.0009975433349609375, 0.0, 0.0, 0.0, 6.914138793945312e-05, 0.0, 0.0009028911590576172, 0.0009999275207519531, 0.0007383823394775391, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009634494781494141, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0008873939514160156, 0.0009975433349609375, 0.0010247230529785156, 0.0010442733764648438, 0.0, 0.0009980201721191406, 0.0, 0.0, 0.0, 0.0009632110595703125, 0.0, 0.0009975433349609375, 0.0, 0.0, 0.0004787445068359375, 0.0, 0.000997304916381836, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0007030963897705078, 0.0, 0.0, 0.0009975433349609375, 0.0, 0.0, 7.295608520507812e-05, 0.0009975433349609375, 0.0, 0.000997304916381836, 0.0010523796081542969, 0.0, 0.0009999275207519531, 0.0, 0.0, 0.0, 0.0, 0.0010008811950683594, 0.0001342296600341797, 0.0, 0.0, 0.0010001659393310547, 0.0, 0.0, 0.0, 0.0, 0.0009975433349609375, 0.0006265640258789062, 0.0, 0.0, 0.0009899139404296875, 0.0, 0.0, 0.0009925365447998047, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009965896606445312, 0.0, 0.0009984970092773438, 0.0009975433349609375, 0.0, 0.0009968280792236328, 0.00016236305236816406, 0.0009980201721191406, 0.0, 0.0009918212890625, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00020956993103027344, 0.0009992122650146484, 0.000997304916381836, 0.0, 0.000997781753540039, 0.0, 0.0009946823120117188, 0.0, 0.0008466243743896484, 0.000997304916381836, 0.0010542869567871094, 0.0009965896606445312, 0.0008306503295898438, 0.0, 0.0, 0.0, 0.0009996891021728516, 0.0, 0.0, 0.0010023117065429688, 0.0, 0.00015687942504882812, 0.0, 0.00099945068359375, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0001430511474609375, 0.0009968280792236328, 0.0010495185852050781, 0.0, 0.0, 0.0009968280792236328, 0.0, 0.0, 0.0009970664978027344, 0.0, 0.0, 0.0009965896606445312, 0.00099945068359375, 0.0, 0.0008924007415771484, 0.0, 0.000997781753540039, 0.0010294914245605469, 0.0, 0.0009965896606445312, 0.0, 0.00020360946655273438, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009996891021728516, 0.0, 0.0, 0.0, 0.0009970664978027344, 0.0, 0.0, 0.0, 0.0009927749633789062, 0.0009918212890625, 0.0, 0.0, 0.0009953975677490234, 0.0009059906005859375, 0.0009958744049072266, 0.0002493858337402344, 0.0, 0.0008625984191894531, 0.0009255409240722656, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001378774642944336, 0.0009958744049072266, 0.0, 0.0009906291961669922, 0.0, 0.0, 0.0008935928344726562, 0.0, 0.00012159347534179688, 0.0009868144989013672, 0.0, 0.0009982585906982422, 0.000997781753540039, 0.0009965896606445312, 0.0009999275207519531, 0.0, 0.0, 0.0, 0.0003681182861328125, 0.0009894371032714844, 0.0010001659393310547, 0.000997781753540039, 0.0, 0.0, 0.0006284713745117188, 0.0001544952392578125, 0.0009932518005371094, 0.0, 0.0009963512420654297, 0.0009975433349609375, 0.0010006427764892578, 0.0013577938079833984, 0.0, 0.0009970664978027344, 0.0008356571197509766, 0.0, 0.0, 0.0, 0.0, 0.0010857582092285156, 0.00031280517578125, 0.0009922981262207031, 0.0, 0.0, 0.0, 0.0, 0.0002684593200683594, 0.0, 5.340576171875e-05, 0.0, 0.0009958744049072266, 0.0, 0.0, 0.0, 0.000997304916381836, 0.000997304916381836, 0.0, 0.0009605884552001953, 0.0, 0.001140594482421875, 0.0, 0.0, 0.0, 0.0, 0.00032591819763183594, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009989738464355469, 0.0011610984802246094, 0.0009982585906982422, 4.38690185546875e-05, 0.001308441162109375, 0.0, 0.0010039806365966797, 0.0002090930938720703, 0.00035262107849121094, 0.001878976821899414, 0.0, 0.0, 0.0, 0.0008261203765869141, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0010273456573486328, 0.00034332275390625, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0013053417205810547, 0.0, 0.0, 0.0001354217529296875, 0.0, 0.0006554126739501953, 0.0, 0.0008895397186279297, 0.0, 0.0010335445404052734, 0.001271963119506836, 0.0, 0.0, 0.0, 0.0, 0.0009925365447998047, 0.0, 0.0, 0.0, 0.0009996891021728516, 0.0006113052368164062, 0.0, 0.0009868144989013672, 0.0, 0.0006682872772216797, 0.0005638599395751953, 0.0, 0.0, 0.0004374980926513672, 0.0009968280792236328, 0.0, 7.605552673339844e-05, 0.00039267539978027344, 0.0009582042694091797, 0.0009970664978027344, 0.0022950172424316406, 0.0008618831634521484, 0.0009975433349609375, 0.000997781753540039, 0.0, 0.0010006427764892578, 0.0004918575286865234, 0.0010025501251220703, 0.0, 0.0, 0.0012204647064208984, 0.0009970664978027344, 0.0009975433349609375, 0.0009975433349609375, 0.0006976127624511719, 0.0010077953338623047, 0.0011391639709472656, 0.0009963512420654297, 0.0, 0.0, 0.0, 0.0, 0.00048065185546875, 0.0010416507720947266, 0.0009975433349609375, 0.0009980201721191406, 0.0006351470947265625, 0.00028443336486816406, 0.0008704662322998047, 0.0009989738464355469, 0.0005061626434326172, 0.0, 0.0, 0.0009937286376953125, 0.000997304916381836, 0.0009987354278564453, 0.0009984970092773438, 0.00047326087951660156, 0.0, 0.00016880035400390625, 0.0005583763122558594, 0.0, 0.000997304916381836, 0.0010106563568115234, 0.0009326934814453125, 0.0, 0.0, 0.0009672641754150391, 0.0009970664978027344, 0.0009961128234863281, 0.0009405612945556641, 0.0009975433349609375, 0.0, 0.0010116100311279297, 0.0, 0.0, 0.0, 0.0009937286376953125, 0.0, 0.0010349750518798828, 0.0, 0.0, 0.0, 0.000997781753540039, 0.0, 0.0, 0.0009996891021728516, 0.0009913444519042969, 0.0013484954833984375, 0.0009937286376953125, 0.0009963512420654297, 0.0008080005645751953, 0.000993967056274414, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0009970664978027344, 0.0011074542999267578, 0.0002422332763671875, 0.0009181499481201172, 0.000997781753540039, 0.0008747577667236328, 0.0, 0.0, 0.0010273456573486328, 0.0009720325469970703, 0.0009975433349609375, 0.0009968280792236328, 0.0008273124694824219, 0.000997781753540039, 0.0, 0.0, 0.0, 0.0009968280792236328, 0.0006818771362304688, 0.0010967254638671875, 0.0, 0.0009944438934326172, 0.0010020732879638672, 0.0008292198181152344, 0.0009975433349609375, 0.0, 0.0, 0.0009984970092773438, 0.0, 0.0009350776672363281, 0.0002777576446533203, 0.0, 0.0009968280792236328, 0.0005347728729248047, 0.000997781753540039, 0.0010313987731933594, 0.0, 0.0004420280456542969, 0.0, 0.000997304916381836, 0.0011332035064697266, 0.0, 0.0, 0.0]
    time3vec = [0.8337826728820801, 0.7420153617858887, 0.8048496246337891, 0.7899191379547119, 0.7379910945892334, 0.7871394157409668, 0.7300810813903809, 0.7171218395233154, 0.7429325580596924, 0.7320432662963867, 0.7619614601135254, 0.7527942657470703, 0.733039140701294, 0.7339990139007568, 0.7260267734527588, 0.75797438621521, 0.8666815757751465, 0.7290153503417969, 0.7300820350646973, 0.7310099601745605, 0.7360310554504395, 0.7578737735748291, 1.1280546188354492, 0.7319176197052002, 0.7289445400238037, 0.7410180568695068, 0.7819068431854248, 0.7350349426269531, 0.7370274066925049, 0.7269384860992432, 0.7250301837921143, 0.7348501682281494, 0.7410628795623779, 0.735032320022583, 0.717045783996582, 0.7370281219482422, 0.7430427074432373, 0.7270867824554443, 0.7529854774475098, 0.7252101898193359, 0.7399845123291016, 0.7545578479766846, 0.7748944759368896, 0.7449803352355957, 0.7500247955322266, 0.7220664024353027, 0.7709379196166992, 0.7200424671173096, 0.751988410949707, 0.7430462837219238, 1.1440718173980713, 0.7420132160186768, 0.8227987289428711, 0.7510247230529785, 0.8457670211791992, 0.7330846786499023, 0.7460036277770996, 0.7510271072387695, 0.7330055236816406, 0.7729322910308838, 0.7420485019683838, 0.7239396572113037, 0.7509899139404297, 0.7340025901794434, 0.7460024356842041, 0.7360312938690186, 0.7579970359802246, 0.7480337619781494, 0.747999906539917, 0.7530190944671631, 0.7160859107971191, 0.7360668182373047, 0.7420146465301514, 0.8587019443511963, 0.9444742202758789, 0.7290172576904297, 0.727057933807373, 1.1239938735961914, 0.7629601955413818, 0.736187219619751, 0.7310771942138672, 0.9345009326934814, 0.7400491237640381, 0.7081043720245361, 0.7340071201324463, 0.7399735450744629, 0.744041919708252, 0.7320399284362793, 0.7280375957489014, 0.736997127532959, 0.7470684051513672, 0.7211103439331055, 0.7360785007476807, 0.7350320816040039, 0.7440471649169922, 0.7541604042053223, 0.7374615669250488, 0.7769231796264648, 0.7360310554504395, 0.7390210628509521, 0.7728979587554932, 0.7449831962585449, 0.7330703735351562, 0.7479970455169678, 0.7280211448669434, 0.9394211769104004, 0.7413680553436279, 0.775871992111206, 0.8347327709197998, 0.7300844192504883, 0.7480330467224121, 0.7639575004577637, 0.7339982986450195, 0.7350664138793945, 0.8975992202758789, 1.5525023937225342, 1.4390957355499268, 0.9618661403656006, 0.8938405513763428, 0.972968339920044, 0.832359790802002, 0.8979260921478271, 0.8577883243560791, 0.9425103664398193, 0.9493236541748047, 1.071134090423584, 0.8317725658416748, 1.3054773807525635, 0.9115946292877197, 0.879650354385376, 0.944502592086792, 0.9794821739196777, 1.012326717376709, 0.859074592590332, 0.9913475513458252, 0.7968711853027344, 1.02134108543396, 1.0731282234191895, 1.0312473773956299, 1.1060419082641602, 0.8876688480377197, 1.0501880645751953, 0.8316881656646729, 1.1149883270263672, 1.0481624603271484, 0.9025843143463135, 0.9793782234191895, 0.7928781509399414, 1.0083017349243164, 1.2925407886505127, 0.9983382225036621, 0.8716230392456055, 1.0272173881530762, 0.755014181137085, 0.8049228191375732, 0.9295015335083008, 1.074155330657959, 0.8825399875640869, 0.8896172046661377, 0.86767578125, 0.9036214351654053, 0.9263482093811035, 1.093155860900879, 1.0481936931610107, 0.957442045211792, 0.98439621925354, 0.9993326663970947, 0.9554109573364258, 0.9993910789489746, 0.8467323780059814, 0.8507580757141113, 1.2097055912017822, 0.9893195629119873, 1.0471982955932617, 1.001319408416748, 0.8487348556518555, 0.9614276885986328, 0.8895876407623291, 0.7999169826507568, 0.9634270668029785, 0.9773805141448975, 0.9194717407226562, 0.8076481819152832, 1.0043127536773682, 0.9125664234161377, 1.0601987838745117, 1.0112690925598145, 0.8796064853668213, 0.8786492347717285, 1.1286683082580566, 0.8626971244812012, 1.136094331741333, 0.921532154083252, 1.2475242614746094, 0.9893527030944824, 0.9833195209503174, 1.0149381160736084, 0.9344584941864014, 0.9833345413208008, 1.0102977752685547, 0.9923372268676758, 1.2945380210876465, 1.0103282928466797, 0.9026191234588623, 0.9953019618988037, 0.9284780025482178, 1.090630292892456, 1.2456684112548828, 1.1221747398376465, 0.902550220489502, 0.8247265815734863, 0.8566744327545166, 0.8846304416656494, 1.0022854804992676, 1.296363353729248, 0.8544859886169434, 1.0641250610351562, 0.8477718830108643, 0.9853711128234863, 0.9414503574371338, 0.9255635738372803, 0.9215424060821533, 0.8707108497619629, 1.0092999935150146, 1.039219856262207, 0.9365329742431641, 0.8337316513061523, 1.0810751914978027, 0.9185445308685303, 0.9684102535247803, 1.1429433822631836, 0.8997724056243896, 0.8147697448730469, 1.0521857738494873, 1.0092928409576416, 0.9663815498352051, 0.9282331466674805, 1.025221347808838, 1.024256944656372, 1.078115463256836, 0.9305100440979004, 0.8288991451263428, 0.9564461708068848, 1.0262560844421387, 1.057978868484497, 0.9125247001647949, 1.2482786178588867, 1.2057933807373047, 1.4013049602508545, 1.3446073532104492, 1.2020823955535889, 1.1671829223632812, 1.0641932487487793, 1.4429359436035156, 1.052032232284546, 1.0109872817993164, 1.2363255023956299, 1.087874174118042, 1.1927745342254639, 1.1894912719726562, 1.2811570167541504, 1.1362125873565674, 1.1250016689300537, 1.0688421726226807, 1.2195994853973389, 1.102353572845459, 1.107694387435913, 1.118028163909912, 1.165130376815796, 1.1380341053009033, 1.0966911315917969, 1.5288636684417725, 1.2253377437591553, 1.057190179824829, 1.1088662147521973, 1.0980761051177979, 1.1363656520843506, 1.2263867855072021, 1.1320521831512451, 1.055910348892212, 1.1285629272460938, 1.0422751903533936, 1.0562021732330322, 1.084716558456421, 1.0945916175842285, 0.9974484443664551, 1.3761842250823975, 0.965989351272583, 1.0126190185546875, 1.1321933269500732, 1.0441429615020752, 1.0949184894561768, 1.3293936252593994, 1.140089750289917, 1.1146817207336426, 1.0879054069519043, 1.2907464504241943, 1.2856531143188477, 1.1998100280761719, 1.1898505687713623, 1.097191333770752, 1.1521859169006348, 1.11049222946167, 1.161376953125, 1.0339818000793457, 1.1061937808990479, 1.3219397068023682, 1.084296464920044, 1.117915391921997, 1.2227067947387695, 1.0856430530548096, 1.1461079120635986, 1.0825986862182617, 1.0989618301391602, 1.0357084274291992, 1.1138672828674316, 1.014836072921753, 1.2340271472930908, 1.0701189041137695, 1.1430943012237549, 1.1083242893218994, 1.2020344734191895, 1.1445436477661133, 1.2228097915649414, 1.4900238513946533, 1.1807582378387451, 1.1689083576202393, 1.1699626445770264, 1.0868475437164307, 1.207627534866333, 1.285722255706787, 1.350071668624878, 1.5042405128479004, 1.0477564334869385, 1.1629292964935303, 1.0994455814361572, 1.1870410442352295, 1.1041884422302246, 1.1584630012512207, 1.086087942123413, 1.1327641010284424, 1.515810489654541, 1.340216875076294, 1.3292896747589111, 1.3864965438842773, 1.2577402591705322, 1.1572139263153076, 1.1000874042510986, 1.14418625831604, 1.0900075435638428, 1.2305123805999756, 1.1060817241668701, 1.2205626964569092, 1.2104992866516113, 1.0902156829833984, 1.2368888854980469, 1.1375958919525146, 1.0593366622924805, 1.789022445678711, 1.159801959991455, 1.3277108669281006, 1.1171133518218994, 1.2479777336120605, 1.149521827697754, 1.1628267765045166, 1.221090316772461, 1.5628769397735596, 1.1668810844421387, 1.171297550201416, 1.1402952671051025, 1.174455165863037, 1.180314064025879, 1.1391398906707764, 1.131983995437622, 1.012634515762329, 1.3643527030944824, 1.0730140209197998, 1.3741629123687744, 1.3267412185668945, 1.1242947578430176, 1.018829107284546, 1.1555280685424805, 1.1019763946533203, 1.1103627681732178, 1.0945830345153809, 1.0957465171813965, 1.0744082927703857, 1.085533857345581, 1.128962755203247, 1.2111752033233643, 1.1988389492034912, 1.11399507522583, 1.433901309967041, 1.125103235244751, 1.102262258529663, 1.2286322116851807, 1.2082035541534424, 1.2607381343841553, 1.131861686706543, 1.1399028301239014, 1.133976697921753, 1.1389009952545166, 1.1181957721710205, 1.1937651634216309, 1.119896411895752, 1.0783898830413818, 1.141361951828003, 1.1536641120910645, 1.1954700946807861, 1.1794188022613525, 1.1206529140472412, 1.0510506629943848, 1.2369701862335205, 0.9992959499359131, 1.077855110168457, 1.1429388523101807, 1.1780083179473877, 1.1617727279663086, 1.1839830875396729, 1.1043524742126465, 1.0903890132904053, 1.0505702495574951, 1.1757698059082031, 1.1114692687988281, 1.2308084964752197, 1.1112146377563477, 1.1545071601867676, 1.4674386978149414, 1.2148442268371582, 1.1701278686523438, 1.1622729301452637, 1.1169099807739258, 1.0816035270690918, 1.0485692024230957, 1.0989868640899658, 1.1582801342010498, 1.0220904350280762, 1.2676329612731934, 1.2069106101989746, 1.380180835723877, 1.11496901512146, 1.150557279586792, 1.046447515487671, 1.1557793617248535, 1.5333619117736816, 1.1533794403076172, 1.0849056243896484, 1.1828362941741943, 1.0421159267425537, 1.1919045448303223, 1.061722755432129, 1.1477341651916504, 0.999666690826416, 1.3396425247192383, 1.3375802040100098, 1.0762557983398438, 1.1862797737121582, 1.2361950874328613, 1.2836496829986572, 1.5050272941589355, 1.3728554248809814, 1.178375005722046, 1.1860156059265137, 1.2012641429901123, 1.2992849349975586, 1.1165223121643066, 1.0979695320129395, 1.1139822006225586, 1.1346023082733154, 1.0809803009033203, 1.090595006942749, 1.094184160232544, 1.1472094058990479, 1.1528491973876953, 1.3588390350341797, 1.0220954418182373, 1.1078870296478271, 1.1495397090911865, 1.303962230682373, 1.264880657196045, 1.253563642501831, 1.0165257453918457, 1.256173849105835, 1.0669152736663818, 1.2507591247558594, 1.2240192890167236, 1.1972463130950928, 1.182685375213623, 1.1377062797546387, 1.2760584354400635, 1.2120075225830078, 1.1810588836669922, 1.2474043369293213, 1.3823480606079102, 1.6126861572265625, 1.137458324432373, 1.1737632751464844, 1.1409130096435547, 1.1259512901306152, 1.3972978591918945]
    time4vec = [0.43379878997802734, 0.4490828514099121, 0.4318094253540039, 0.43280792236328125, 0.4218711853027344, 0.4525463581085205, 0.39690542221069336, 0.39792442321777344, 0.38909912109375, 0.3839714527130127, 0.3889906406402588, 0.39191770553588867, 0.38796353340148926, 0.3911309242248535, 0.39893293380737305, 0.3959040641784668, 0.4009261131286621, 0.39797043800354004, 0.4089081287384033, 0.38098597526550293, 0.41991305351257324, 0.3859686851501465, 0.6282486915588379, 0.3841133117675781, 0.4281175136566162, 0.3979358673095703, 0.43483924865722656, 0.38496875762939453, 0.41791439056396484, 0.39896464347839355, 0.3931567668914795, 0.3869631290435791, 0.38688182830810547, 0.38201045989990234, 0.39593982696533203, 0.41094374656677246, 0.38913583755493164, 0.39291810989379883, 0.40092897415161133, 0.40377140045166016, 0.39295029640197754, 0.4049513339996338, 0.393979549407959, 0.4219982624053955, 0.37699389457702637, 0.4398229122161865, 0.40195608139038086, 0.4428138732910156, 0.39104700088500977, 0.4308149814605713, 0.656987190246582, 0.41193079948425293, 0.5206091403961182, 0.5026204586029053, 0.4248311519622803, 0.4007706642150879, 0.3869647979736328, 0.39690327644348145, 0.4119288921356201, 0.40296006202697754, 0.41585206985473633, 0.4070870876312256, 0.39690566062927246, 0.3999631404876709, 0.4069178104400635, 0.39893293380737305, 0.44478535652160645, 0.39092302322387695, 0.4288516044616699, 0.394909143447876, 0.41891050338745117, 0.3979320526123047, 0.40395665168762207, 0.5395569801330566, 0.564490795135498, 0.4118976593017578, 0.41388988494873047, 0.6662163734436035, 0.40222811698913574, 0.4286963939666748, 0.39391183853149414, 0.5704739093780518, 0.4138631820678711, 0.39797067642211914, 0.3949449062347412, 0.4039499759674072, 0.4038522243499756, 0.4188835620880127, 0.3839728832244873, 0.4308795928955078, 0.3839073181152344, 0.41887497901916504, 0.3929016590118408, 0.4527883529663086, 0.3899216651916504, 0.41172027587890625, 0.4178810119628906, 0.43284034729003906, 0.3829770088195801, 0.38995814323425293, 0.40192461013793945, 0.3919498920440674, 0.38493895530700684, 0.38297581672668457, 0.7620062828063965, 0.4059131145477295, 0.40286922454833984, 0.3929164409637451, 0.48923778533935547, 0.401888370513916, 0.414886474609375, 0.3889596462249756, 0.43879222869873047, 0.4717733860015869, 0.799858808517456, 0.9265217781066895, 1.0054068565368652, 0.5571885108947754, 0.48397278785705566, 0.519873857498169, 0.5381476879119873, 0.4736649990081787, 0.46869730949401855, 0.45079469680786133, 0.4679098129272461, 0.411862850189209, 0.46974730491638184, 0.9415948390960693, 0.5136289596557617, 0.44481778144836426, 0.5056474208831787, 0.45770931243896484, 0.45976781845092773, 0.4996631145477295, 0.5078701972961426, 0.5495338439941406, 0.5195777416229248, 0.4966709613800049, 0.412919282913208, 0.4417846202850342, 0.5605473518371582, 0.5505297183990479, 0.4548146724700928, 0.4687473773956299, 0.38799571990966797, 0.5634615421295166, 0.44876575469970703, 0.5355329513549805, 0.4590260982513428, 0.7085154056549072, 0.4816703796386719, 0.5644946098327637, 0.5385892391204834, 0.5295822620391846, 0.5166172981262207, 0.4886972904205322, 0.41898274421691895, 0.4187812805175781, 0.48670244216918945, 0.5146760940551758, 0.419872522354126, 0.4976634979248047, 0.595407247543335, 0.5525226593017578, 0.49593472480773926, 0.535621166229248, 0.46871089935302734, 0.42087578773498535, 0.5017478466033936, 0.4966752529144287, 0.5893881320953369, 0.482710599899292, 0.5058083534240723, 0.45774340629577637, 0.45677900314331055, 0.5405173301696777, 0.49268150329589844, 0.4887242317199707, 0.5145313739776611, 0.4886939525604248, 0.514592170715332, 0.46774983406066895, 0.46276044845581055, 0.48374104499816895, 0.43383145332336426, 0.41489076614379883, 0.48470330238342285, 0.39322376251220703, 0.4298834800720215, 0.5634567737579346, 0.535529375076294, 0.5945017337799072, 0.5397124290466309, 0.4976637363433838, 0.43480515480041504, 0.3769538402557373, 0.6223359107971191, 0.5536236763000488, 0.5176162719726562, 0.5834088325500488, 0.43779730796813965, 0.6981656551361084, 0.4527568817138672, 0.5395219326019287, 0.4697437286376953, 0.47276997566223145, 0.49367856979370117, 0.691150426864624, 0.6590285301208496, 0.4936797618865967, 0.4308476448059082, 0.4996623992919922, 0.4278249740600586, 0.4268941879272461, 0.539522647857666, 0.45512914657592773, 0.47019314765930176, 0.5375566482543945, 0.5146183967590332, 0.46478939056396484, 0.46375441551208496, 0.5495247840881348, 0.47185611724853516, 0.4866983890533447, 0.5665137767791748, 0.4428126811981201, 0.47273778915405273, 0.5306158065795898, 0.49068689346313477, 0.4749445915222168, 0.42693543434143066, 0.5124542713165283, 0.502655029296875, 0.4288177490234375, 0.5236005783081055, 0.873661994934082, 0.47576141357421875, 0.45381712913513184, 0.6193423271179199, 0.45478343963623047, 0.4996650218963623, 0.4905674457550049, 0.5565090179443359, 0.5764188766479492, 0.565540075302124, 0.7969009876251221, 1.0929527282714844, 1.004546880722046, 0.9505136013031006, 0.9254741668701172, 0.7363388538360596, 0.6598944664001465, 0.6413378715515137, 0.9614477157592773, 0.5754616260528564, 0.6076371669769287, 0.9853653907775879, 0.8109545707702637, 0.741016149520874, 0.7291297912597656, 1.1076958179473877, 0.6102032661437988, 0.6122663021087646, 0.7335038185119629, 0.6710753440856934, 0.7015306949615479, 0.6549942493438721, 0.7371566295623779, 0.740039587020874, 0.6736860275268555, 0.6285829544067383, 0.769263505935669, 0.6457638740539551, 0.6901125907897949, 0.5758821964263916, 0.816037654876709, 0.6434450149536133, 0.9734175205230713, 0.6670577526092529, 0.6649909019470215, 0.6392574310302734, 0.6767394542694092, 0.6356971263885498, 0.8474485874176025, 0.6622068881988525, 0.6550829410552979, 0.6417844295501709, 0.7367887496948242, 0.9103858470916748, 0.8373808860778809, 0.5791208744049072, 0.6188700199127197, 1.0423359870910645, 0.7571194171905518, 0.6602168083190918, 0.8040025234222412, 0.7803480625152588, 0.784905195236206, 0.7186391353607178, 0.6402702331542969, 0.6357097625732422, 0.6240863800048828, 0.6907169818878174, 0.6008720397949219, 0.6122496128082275, 0.5938677787780762, 1.4809668064117432, 0.5920920372009277, 0.7723038196563721, 0.624584436416626, 0.6531732082366943, 0.7950348854064941, 0.6452622413635254, 0.6081070899963379, 0.6071550846099854, 0.6003673076629639, 0.6001906394958496, 0.7371337413787842, 0.650968074798584, 0.6726977825164795, 0.6706726551055908, 0.6674926280975342, 0.6842029094696045, 0.6963226795196533, 0.7881083488464355, 0.6959831714630127, 0.5747613906860352, 0.8503799438476562, 0.6669869422912598, 0.7789714336395264, 0.9780795574188232, 0.7474148273468018, 0.7456438541412354, 0.6533644199371338, 0.7129371166229248, 0.6892256736755371, 0.6889426708221436, 0.7268071174621582, 0.6766483783721924, 0.6671750545501709, 0.6507091522216797, 1.0235812664031982, 0.729276180267334, 0.788071870803833, 0.694178581237793, 0.6937284469604492, 0.6923353672027588, 0.6915154457092285, 0.7650249004364014, 0.6867568492889404, 0.598839282989502, 0.6825072765350342, 0.8526051044464111, 0.68528151512146, 0.6377894878387451, 0.6510186195373535, 0.7278060913085938, 0.6655969619750977, 0.7927951812744141, 0.9913413524627686, 0.8867287635803223, 0.6398820877075195, 0.8231756687164307, 0.6178312301635742, 0.7231016159057617, 1.044947624206543, 0.8439130783081055, 0.6790845394134521, 0.7559823989868164, 0.7435517311096191, 0.6970522403717041, 1.0552711486816406, 0.7248644828796387, 0.6502408981323242, 0.9133620262145996, 0.8468642234802246, 0.6551961898803711, 0.8374271392822266, 0.7649054527282715, 0.6667563915252686, 0.6626551151275635, 0.7758872509002686, 0.7776198387145996, 0.6419556140899658, 0.6524584293365479, 0.6685047149658203, 0.6405465602874756, 0.7289376258850098, 0.829819917678833, 0.6832468509674072, 0.7545630931854248, 0.6771492958068848, 0.9544892311096191, 0.7045202255249023, 0.6148853302001953, 0.7153949737548828, 0.8855257034301758, 0.7422785758972168, 0.7619688510894775, 0.9195482730865479, 0.6574351787567139, 0.7566688060760498, 0.6202316284179688, 0.7463269233703613, 0.7209210395812988, 0.7474985122680664, 0.6907813549041748, 0.6746292114257812, 0.7315418720245361, 1.2339835166931152, 0.6439113616943359, 0.5890026092529297, 0.6881239414215088, 0.6058390140533447, 0.6757493019104004, 0.771216630935669, 0.7876124382019043, 0.787968635559082, 0.9659473896026611, 0.6482021808624268, 0.6663389205932617, 0.6519162654876709, 0.6739296913146973, 0.8225955963134766, 0.6600162982940674, 0.670771598815918, 0.9511508941650391, 0.682553768157959, 0.7233750820159912, 0.7678451538085938, 0.7632369995117188, 0.6970105171203613, 0.878795862197876, 0.4930286407470703, 0.9799609184265137, 0.6824765205383301, 0.7257981300354004, 0.6935989856719971, 0.7966949939727783, 1.1011767387390137, 0.7629780769348145, 0.6988487243652344, 0.6888904571533203, 0.6479191780090332, 0.982227087020874, 0.6776814460754395, 0.8178050518035889, 0.6948299407958984, 0.6100142002105713, 0.7001042366027832, 0.7010114192962646, 0.5990393161773682, 0.6316890716552734, 0.8643569946289062, 1.0803580284118652, 0.7860119342803955, 0.8178548812866211, 0.8713815212249756, 1.0306239128112793, 1.1262569427490234, 1.3144588470458984, 0.7998619079589844, 0.8369290828704834, 0.7871272563934326, 0.8695824146270752, 0.7138879299163818, 0.663266658782959, 0.6716039180755615, 0.6330978870391846, 0.6526668071746826, 0.6414563655853271, 0.7100310325622559, 0.6780893802642822, 0.7970473766326904, 0.687821626663208, 0.6808369159698486, 0.9131615161895752, 1.070098638534546, 0.7349843978881836, 0.8131327629089355, 0.7374422550201416, 0.643681526184082, 0.8040339946746826, 0.6839985847473145, 0.7844498157501221, 0.7122476100921631, 0.7480063438415527, 0.7750167846679688, 0.6566681861877441, 0.9093527793884277, 0.8218121528625488, 0.7929422855377197, 0.8075850009918213, 0.8688735961914062, 1.0910813808441162, 0.673241376876831, 0.7848598957061768, 0.7071099281311035, 0.7191131114959717, 0.8688371181488037]
    time5vec = [0.9524526596069336, 1.009047269821167, 1.0152852535247803, 1.0003652572631836, 0.9564394950866699, 0.9903478622436523, 0.9733941555023193, 0.9435596466064453, 0.9782085418701172, 1.0900838375091553, 0.9663844108581543, 0.976421594619751, 0.9484617710113525, 0.9632782936096191, 0.9594650268554688, 1.0122928619384766, 0.9794113636016846, 0.9484283924102783, 0.9983246326446533, 0.9684052467346191, 0.9713642597198486, 1.105821132659912, 1.0602848529815674, 0.959397554397583, 0.9601681232452393, 0.9634213447570801, 0.9674093723297119, 0.9514548778533936, 0.9903182983398438, 0.9534463882446289, 0.9554202556610107, 0.9644572734832764, 0.9564423561096191, 0.9504604339599609, 0.9783813953399658, 0.9653756618499756, 0.9542386531829834, 0.9584336280822754, 0.9733939170837402, 0.9484958648681641, 0.9484896659851074, 0.9733951091766357, 0.9963605403900146, 0.9911870956420898, 0.9504566192626953, 0.9733643531799316, 0.9644191265106201, 0.9714007377624512, 0.9693145751953125, 1.0821037292480469, 1.3134851455688477, 0.980344295501709, 1.2646150588989258, 1.1060411930084229, 1.0094122886657715, 0.9883551597595215, 0.9803752899169922, 1.0013539791107178, 0.9594006538391113, 0.9613907337188721, 0.9624252319335938, 0.9801986217498779, 0.9745199680328369, 0.9813716411590576, 0.9796009063720703, 0.9824020862579346, 0.9534177780151367, 1.0013155937194824, 0.9604315757751465, 0.951453447341919, 0.9624273777008057, 0.9793479442596436, 1.056135892868042, 1.2666103839874268, 1.1379868984222412, 0.962456226348877, 1.2346644401550293, 0.9973313808441162, 0.9820666313171387, 0.964421272277832, 0.9923443794250488, 1.0223743915557861, 0.9933433532714844, 0.9763538837432861, 0.9823713302612305, 0.9833712577819824, 0.9554443359375, 0.9763834476470947, 0.9714319705963135, 0.9474666118621826, 0.9713993072509766, 0.9673755168914795, 0.9604310989379883, 0.9474649429321289, 0.9723958969116211, 0.951540470123291, 0.9983289241790771, 0.9953367710113525, 0.9783823490142822, 0.9744284152984619, 1.0073301792144775, 0.9614288806915283, 0.9674117565155029, 0.9794116020202637, 1.4212522506713867, 0.972395658493042, 0.9664649963378906, 0.9654502868652344, 1.0775692462921143, 0.9584355354309082, 1.0022859573364258, 0.9923446178436279, 0.9524502754211426, 1.4061696529388428, 1.1678745746612549, 1.769266128540039, 1.4583957195281982, 1.4287898540496826, 1.2134931087493896, 1.3233826160430908, 1.2522003650665283, 1.245661973953247, 1.3593292236328125, 1.2666103839874268, 1.1776902675628662, 1.2087976932525635, 1.2606236934661865, 1.387169361114502, 1.3015127182006836, 1.2625815868377686, 1.189784049987793, 1.2077322006225586, 1.3962314128875732, 1.2157776355743408, 1.4449059963226318, 1.1489269733428955, 1.3025481700897217, 1.2466638088226318, 1.204751968383789, 1.087137222290039, 1.355269432067871, 1.362407922744751, 1.3503837585449219, 1.1998224258422852, 1.4142165184020996, 1.3065376281738281, 1.371363878250122, 1.121032476425171, 1.653292179107666, 1.3230829238891602, 1.2845981121063232, 1.3622329235076904, 1.2077381610870361, 1.399261474609375, 1.1638927459716797, 1.2336971759796143, 1.3305072784423828, 1.3334319591522217, 1.234692096710205, 1.1857452392578125, 1.3663110733032227, 1.4521143436431885, 1.2167458534240723, 1.4172065258026123, 1.1486635208129883, 1.3743171691894531, 1.110065221786499, 1.2087647914886475, 1.1320011615753174, 1.2456321716308594, 1.6525790691375732, 1.2596633434295654, 1.1898527145385742, 1.2018203735351562, 1.166874647140503, 1.323493242263794, 1.1648786067962646, 1.3533823490142822, 1.2347261905670166, 1.2147457599639893, 1.303579568862915, 1.2955679893493652, 1.2167441844940186, 1.2227258682250977, 1.2486248016357422, 1.1489503383636475, 1.2217364311218262, 1.3112173080444336, 1.2519631385803223, 1.1589341163635254, 1.3613924980163574, 1.366084098815918, 1.8150238990783691, 1.3424046039581299, 1.1878564357757568, 1.3786578178405762, 1.3215343952178955, 1.2106618881225586, 1.3025481700897217, 1.2407126426696777, 1.3334324359893799, 1.1798088550567627, 1.3254544734954834, 1.0971002578735352, 1.5050091743469238, 1.3083784580230713, 1.242781162261963, 1.5568649768829346, 1.3853278160095215, 1.2915785312652588, 1.2915785312652588, 1.3072490692138672, 1.3693695068359375, 1.6555328369140625, 1.2339563369750977, 1.264268398284912, 1.1255357265472412, 1.2855582237243652, 1.324453592300415, 1.1508862972259521, 1.103043794631958, 1.4760158061981201, 1.2435495853424072, 1.3453638553619385, 1.2067441940307617, 1.2366907596588135, 1.258662462234497, 1.437119483947754, 1.2137908935546875, 1.349177360534668, 1.2834548950195312, 1.162971019744873, 1.4102253913879395, 1.3295726776123047, 1.2895536422729492, 1.750349760055542, 1.2735927104949951, 1.39341402053833, 1.3663816452026367, 1.314516305923462, 1.3842990398406982, 1.3094968795776367, 1.4521148204803467, 1.5857570171356201, 1.443084478378296, 1.5647821426391602, 1.999725103378296, 1.8015546798706055, 1.9223432540893555, 1.7389888763427734, 1.6172373294830322, 1.4921438694000244, 1.6711690425872803, 2.147705554962158, 1.2855725288391113, 1.3824822902679443, 1.7263789176940918, 1.4977068901062012, 1.5645811557769775, 1.5179760456085205, 1.8694725036621094, 1.3087952136993408, 1.5508813858032227, 1.6474266052246094, 1.44801664352417, 1.4084274768829346, 1.5080127716064453, 1.5688114166259766, 1.6390368938446045, 1.4190187454223633, 1.801985740661621, 1.5437703132629395, 1.470818281173706, 1.5760729312896729, 1.446681022644043, 1.5612390041351318, 1.6629536151885986, 1.5447640419006348, 1.527418613433838, 1.529383659362793, 1.553696632385254, 1.4940495491027832, 1.5091087818145752, 1.4871759414672852, 1.4131896495819092, 2.1911346912384033, 1.341071367263794, 1.5193285942077637, 1.603677749633789, 1.4525022506713867, 1.3248417377471924, 1.4051663875579834, 1.6777570247650146, 1.5182771682739258, 1.3977575302124023, 1.6909756660461426, 1.5352296829223633, 1.6218833923339844, 1.468937635421753, 1.5357551574707031, 1.4150707721710205, 1.5440876483917236, 1.5623431205749512, 1.4699785709381104, 1.4846405982971191, 1.5151565074920654, 1.6297709941864014, 1.5563042163848877, 1.7172541618347168, 1.5765447616577148, 1.5027368068695068, 1.6083340644836426, 1.5827531814575195, 1.4150221347808838, 1.54128098487854, 1.4505953788757324, 1.5461034774780273, 1.4785854816436768, 1.56793212890625, 1.5839693546295166, 1.6651229858398438, 1.4715068340301514, 1.5488758087158203, 1.7258825302124023, 1.581784963607788, 1.4593214988708496, 1.373382568359375, 1.5802533626556396, 1.5705223083496094, 1.533085823059082, 1.6741302013397217, 1.4997272491455078, 1.4661173820495605, 1.4128756523132324, 1.5625452995300293, 1.545898675918579, 1.6955292224884033, 1.54719877243042, 1.5216748714447021, 1.5389044284820557, 1.5379669666290283, 1.6699423789978027, 1.7368354797363281, 1.7845282554626465, 1.813060998916626, 1.4988937377929688, 1.6039540767669678, 1.6155667304992676, 1.5598535537719727, 1.8062708377838135, 1.5467867851257324, 1.5513908863067627, 1.6105258464813232, 1.4917292594909668, 1.6280934810638428, 1.4814584255218506, 1.5672407150268555, 1.5903027057647705, 1.4291999340057373, 1.9872093200683594, 1.5119736194610596, 1.7601053714752197, 1.6330087184906006, 1.516946792602539, 1.4457573890686035, 1.8141858577728271, 1.525346040725708, 1.5916576385498047, 1.5265960693359375, 1.6329200267791748, 1.4669110774993896, 1.9139633178710938, 1.5759830474853516, 1.5405244827270508, 2.0211474895477295, 1.594414234161377, 1.6400344371795654, 1.5921764373779297, 1.5300521850585938, 1.4393999576568604, 1.4355289936065674, 1.5220606327056885, 1.5613882541656494, 1.4381365776062012, 1.5063180923461914, 1.434837818145752, 1.572049856185913, 1.4863166809082031, 1.6236915588378906, 1.3656237125396729, 1.5847220420837402, 1.5240983963012695, 1.4825739860534668, 1.3232917785644531, 1.5531563758850098, 1.4673240184783936, 1.7793364524841309, 1.4823265075683594, 1.974351406097412, 1.5290615558624268, 1.612534999847412, 1.4529273509979248, 1.5723490715026855, 1.4797327518463135, 1.5611507892608643, 1.519892692565918, 1.5665228366851807, 1.515547275543213, 1.494133472442627, 1.9011955261230469, 1.552675485610962, 1.4792189598083496, 1.4646251201629639, 1.4488513469696045, 1.4753897190093994, 1.6034045219421387, 1.4722981452941895, 1.6726858615875244, 1.4568843841552734, 1.5248637199401855, 1.4305551052093506, 1.5567395687103271, 1.4279906749725342, 1.5997259616851807, 1.393951177597046, 1.6131880283355713, 1.7879951000213623, 1.574064016342163, 1.6401889324188232, 1.5807688236236572, 1.4329140186309814, 1.5336122512817383, 1.5068590641021729, 1.4862546920776367, 1.6709208488464355, 1.5461883544921875, 1.5939583778381348, 1.6473512649536133, 1.6501648426055908, 1.5686957836151123, 1.4782218933105469, 1.531653881072998, 1.4485268592834473, 1.5125501155853271, 1.8037614822387695, 1.5380921363830566, 1.7400662899017334, 1.5801162719726562, 1.6460254192352295, 1.4881596565246582, 1.496345043182373, 1.3987526893615723, 1.4786577224731445, 1.5447754859924316, 1.6404364109039307, 1.4726755619049072, 1.55908203125, 1.898106336593628, 1.8995091915130615, 1.6019952297210693, 2.1103577613830566, 1.516162395477295, 1.77996826171875, 1.8405210971832275, 1.5991003513336182, 1.4376683235168457, 1.4826161861419678, 1.5042574405670166, 1.5035643577575684, 1.4709618091583252, 1.4973423480987549, 1.5888786315917969, 1.5260233879089355, 1.8135578632354736, 1.5918209552764893, 1.4571113586425781, 1.590348482131958, 2.4081618785858154, 1.471989393234253, 1.6199185848236084, 1.5131144523620605, 1.6557526588439941, 1.4468004703521729, 1.5309135913848877, 1.4829034805297852, 1.5346438884735107, 1.491612195968628, 1.604428768157959, 1.3717906475067139, 1.9707520008087158, 1.5380957126617432, 1.717714548110962, 1.52675461769104, 1.5386710166931152, 1.5030121803283691, 1.5956900119781494, 1.496030330657959, 1.5429065227508545, 1.6684997081756592, 1.6549792289733887]
    
    plt.title('Trace of time (in secs.) for interval 5 of algorithm')
    plt.ylim([0,5])
    plt.plot(time5vec5,label='$n=5$')
    plt.plot(time5vec,label='$n=20$')
    plt.legend()
    plt.show()
    '''
    
    
    
    
    


    return

def possibleYSets(n, Q=np.array([])):
    '''
    Return all combinatorially possible data outcomes for experiment
    array n. If n is 1-dimensional, Q is used to establish possible outcomes
    along each trace. The returned
    '''
    if len(Q) == 0:
        Y = [np.zeros(n.shape)]
        # Initialize set of indices with positive testing probability
        J = [(a,b) for a in range(n.shape[0]) for b in range(n.shape[1]) if n[a][b]>0]
    else:
        Y = [np.zeros(Q.shape)]
        Qdotn = np.multiply(np.tile(n.reshape(Q.shape[0],1),Q.shape[1]),Q)
        J = [(a, b) for a in range(Qdotn.shape[0]) for b in range(Qdotn.shape[1]) if Qdotn[a][b] > 0]

    for (a,b) in J:
        Ycopy = Y.copy()
        for curry in range(1,int(n[a][b])+1):
            addArray = np.zeros(n.shape)
            addArray[a][b] += curry
            Ynext = [y+addArray for y in Ycopy]
            for y in Ynext:
                Y.append(y)

    return Y

def nVecs(length,target):
    '''Return all possible vectors of 'length' of positive integers that sum to target'''
    if length == 1:
        return [[target]]
    else:
        retSet = []
        for nexttarg in range(target+1):
            for nextset in nVecs(length-1,target-nexttarg):
                retSet.append([nexttarg]+nextset)

    return retSet

def zProbTr(tnInd, snInd, snNum, gammaVec, sens=1., spec=1.):
    '''Provides consolidated SFP probability for the entered TN, SN indices; gammaVec should start with SN rates'''
    zStar = gammaVec[snNum+tnInd]+(1-gammaVec[snNum+tnInd])*gammaVec[snInd]
    return sens*zStar+(1-spec)*zStar

def zProbTrVec(snNum, gammaMat, sens=1., spec=1.):
    '''Provides consolidated SFP probability for the entered TN, SN indices; gammaVec should start with SN rates'''
    th, py = gammaMat[:, :snNum], gammaMat[:, snNum:]
    n, m, k = len(gammaMat[0])-snNum, snNum, gammaMat.shape[0]
    zMat = np.reshape(np.tile(th, (n)), (k, n, m)) + np.reshape(np.tile(1 - th, (n)), (k, n, m)) * \
           np.transpose(np.reshape(np.tile(py, (m)), (k, m, n)), (0, 2, 1))
    # each term is a k-by-n-by-m array
    return sens * zMat + (1 - spec) * (1 - zMat)

def GetMargUtilAtNodes(scDict, testMax, testInt, lossDict, utilDict, printUpdate=True):
    '''
    Returns an array of marginal utility estimates for the PMS data contained in scDict.
    :param testsMax: maximum number of tests at each test node
    :param testsInt: interval of tests, from zero ot testsMax, by which to calculate estimates
    :param lossDict: dictionary containing parameters for how the PMS loss is calculated
    :param utilDict: dictionary of parameters for use with getDesignUtility
    :return margUtilArr: array of size (number of test nodes) by (testsMax/testsInt + 1)
    '''
    (numTN, numSN) = scDict['N'].shape
    design=np.zeros(numTN)
    design[0] = 1.
    # Calculate the loss matrix
    if 'numdrawsforbayes' in utilDict:
        indsforbayes = choice(np.arange(len(scDict['postSamples'])),size=utilDict['numdrawsforbayes'],replace=False)
    else:
        indsforbayes = np.arange(len(scDict['postSamples']))
    if utilDict['method']=='weightsNodeDraw3' or utilDict['method']=='weightsNodeDraw4':
        if printUpdate == True:
            print('Generating loss matrix of size: '+str(len(scDict['postSamples'])*len(indsforbayes)))
        lossMat = lossMatrix(scDict['postSamples'],lossDict.copy(),indsforbayes)
        lossDict.update({'lossMat':lossMat})
    # Establish a baseline loss for comparison with other losses
    if printUpdate == True:
        print('Generating baseline utility...')
    baseLoss = getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict, designlist=[design],
                                numtests=0, utildict=utilDict.copy())[0]
    # Initialize the return array
    margUtilArr = np.zeros((numTN, int(testMax / testInt) + 1))
    # Calculate the marginal utility increase under each iteration of tests for each test node
    for currTN in range(numTN):
        design = np.zeros(numTN)
        design[currTN] = 1.
        for testNum in range(testInt,testMax+1,testInt):
            if printUpdate == True:
                print('Calculating for test node '+str(currTN+1)+' under '+str(testNum)+' tests...')
            margUtilArr[currTN][int(testNum/testInt)] = baseLoss - getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict, designlist=[design],
                                numtests=testNum, utildict=utilDict)[0]
    return margUtilArr

def GetMargUtilForDesigns(designList, scDict, testMax, testInt, lossDict, utilDict, printUpdate=True):
    '''
    Returns an array of marginal utility estimates for the PMS data contained in scDict.
    :param testsMax: maximum number of tests at each test node
    :param testsInt: interval of tests, from zero ot testsMax, by which to calculate estimates
    :param lossDict: dictionary containing parameters for how the PMS loss is calculated
    :param utilDict: dictionary of parameters for use with getDesignUtility
    :return margUtilArr: array of size (number of test nodes) by (testsMax/testsInt + 1)
    '''
    (numTN, numSN) = scDict['N'].shape
    # Calculate the loss matrix
    if 'numdrawsforbayes' in utilDict:
        indsforbayes = choice(np.arange(len(scDict['postSamples'])),size=utilDict['numdrawsforbayes'],replace=False)
    else:
        indsforbayes = np.arange(len(scDict['postSamples']))
    if utilDict['method']=='weightsNodeDraw3' or utilDict['method']=='weightsNodeDraw4':
        if printUpdate == True:
            print('Generating loss matrix of size: '+str(len(scDict['postSamples'])*len(indsforbayes)))
        lossMat = lossMatrix(scDict['postSamples'],lossDict.copy(),indsforbayes)
        lossDict.update({'lossMat':lossMat})
    # Establish a baseline loss for comparison with other losses
    if printUpdate == True:
        print('Generating baseline utility...')
    baseLoss = getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict, designlist=[designList[0]],
                                numtests=0, utildict=utilDict.copy())[0]
    # Initialize the return array
    margUtilArr = np.zeros((numTN, int(testMax / testInt) + 1))
    # Calculate the marginal utility increase under each iteration of tests for each test node
    for designind in range(len(designList)):
        design = designList[designind]
        for testNum in range(testInt,testMax+1,testInt):
            if printUpdate == True:
                print('Calculating for design '+str(designind+1)+' under '+str(testNum)+' tests...')
            margUtilArr[designind][int(testNum/testInt)] = baseLoss - getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict, designlist=[design],
                                numtests=testNum, utildict=utilDict)[0]
    return margUtilArr

def plotMargUtil(margUtilArr,testMax,testInt,al=0.6,titleStr='',colors=[],dashes=[],labels=[]):
    '''Produces a plot of an array of marginal utility increases '''
    x1 = range(0, testMax + 1, testInt)
    if len(colors) == 0:
        colors = cm.rainbow(np.linspace(0, 1, margUtilArr.shape[0]))
    if len(dashes) == 0:
        dashes = [[1,desind] for desind in range(margUtilArr.shape[0])]
    if len(labels) == 0:
        labels = ['Design '+str(desind+1) for desind in range(margUtilArr.shape[0])]
    for desind in range(margUtilArr.shape[0]):
        plt.plot(x1, margUtilArr[desind], dashes=dashes[desind], linewidth=2.5, color=colors[desind],
                 label=labels[desind], alpha=al)
    plt.legend()
    plt.ylim([0., margUtilArr.max()*1.1])
    plt.xlabel('Number of Tests')
    plt.ylabel('Utility Gain')
    plt.title('Marginal Utility with Increasing Tests\n'+titleStr)
    plt.savefig('MARGUTILPLOT.png')
    plt.show()
    plt.close()
    return

def GetOptAllocation(U):
    '''
    :param U
    :return x
    Returns an optimal allocation for maximizing the utility values as captured in U.
    Each row of U should correspond to one test node or trace. U should be 2-dimensional in
    the case of node sampling and 3-dimensional in the case of path sampling.
    '''
    ''' With 200k prior draws, up to ntilde=50, design = np.array([[0., 0.], [1., 0.], [0., 0.]])
Umat = np.array([[[0.16098932, 0.15926648, 0.15765788, 0.15617675, 0.15477563,
         0.15348549, 0.15225739, 0.15110963, 0.1500301 , 0.14900606,
         0.14803931, 0.14712575, 0.14625472, 0.14543112, 0.14464693,
         0.14389572, 0.14317966, 0.1424973 , 0.14184333, 0.14121736,
         0.14061906, 0.14004235, 0.13948944, 0.13895668, 0.13844451,
         0.1379546 , 0.13747691, 0.13702124, 0.13657725, 0.13615013,
         0.13573617, 0.13533675, 0.13494959, 0.13457688, 0.13421297,
         0.13385875, 0.13351799, 0.13318551, 0.13286335, 0.13254984,
         0.13224531, 0.13194758, 0.13165973, 0.13137863, 0.13110483,
         0.13083779, 0.13057652, 0.13032458, 0.13007499, 0.12983474],
        [0.16098932, 0.16050359, 0.16004441, 0.15961104, 0.15920019,
         0.15881279, 0.15844703, 0.15809987, 0.1577686 , 0.15745397,
         0.15715835, 0.15687877, 0.1566124 , 0.15635826, 0.15611412,
         0.15588327, 0.15566128, 0.15544816, 0.15524374, 0.15504709,
         0.1548585 , 0.15467651, 0.15450132, 0.15433268, 0.1541705 ,
         0.15401328, 0.15386185, 0.15371607, 0.15357544, 0.15343897,
         0.15330682, 0.15317997, 0.15305609, 0.15293706, 0.1528204 ,
         0.15270733, 0.15259706, 0.15249011, 0.15238656, 0.15228543,
         0.15218841, 0.15209217, 0.15199949, 0.15190909, 0.15182026,
         0.15173358, 0.15165006, 0.15156812, 0.15148841, 0.15140938]],
       [[0.16098932, 0.15976119, 0.15860766, 0.1575474 , 0.15653261,
         0.15559973, 0.15471447, 0.15388067, 0.1530916 , 0.15234469,
         0.15163571, 0.15096929, 0.1503275 , 0.14971716, 0.14913831,
         0.14858463, 0.14805327, 0.14754521, 0.14705872, 0.14659065,
         0.1461412 , 0.14570923, 0.14529534, 0.144893  , 0.14451055,
         0.14413559, 0.14377903, 0.14342948, 0.14309588, 0.14276969,
         0.14245412, 0.1421502 , 0.14185658, 0.14157105, 0.14129151,
         0.14102223, 0.14075931, 0.14050511, 0.14025716, 0.14001543,
         0.13978049, 0.13955197, 0.13932882, 0.13911313, 0.13890055,
         0.13869456, 0.13849415, 0.13829679, 0.13810486, 0.13791963],
        [0.16098932, 0.15908717, 0.15741709, 0.15594023, 0.15461668,
         0.1534184 , 0.15233326, 0.15133658, 0.15043013, 0.14959103,
         0.14882037, 0.14810896, 0.14744448, 0.14682306, 0.14624621,
         0.14570199, 0.14518813, 0.14470303, 0.14424797, 0.14381987,
         0.1434066 , 0.14301845, 0.14264604, 0.14229303, 0.14195554,
         0.14163387, 0.14132859, 0.14103681, 0.14075392, 0.14048389,
         0.14022569, 0.139976  , 0.13973578, 0.13950557, 0.13928147,
         0.13906428, 0.13885516, 0.13865315, 0.13845647, 0.13826738,
         0.13808469, 0.13790931, 0.13773702, 0.13757194, 0.13741207,
         0.13725517, 0.13710246, 0.13695439, 0.13681016, 0.13667057]],
       [[0.16098932, 0.15908208, 0.15730035, 0.15567289, 0.15412215,
         0.1526926 , 0.15133218, 0.15006174, 0.14885946, 0.14772244,
         0.14664797, 0.145628  , 0.14465938, 0.14373773, 0.14286377,
         0.14202867, 0.14123549, 0.14047947, 0.13975659, 0.13906729,
         0.13840516, 0.13777321, 0.13716596, 0.13658584, 0.13602695,
         0.13549191, 0.13497545, 0.13447982, 0.13400015, 0.13353907,
         0.13309363, 0.13266275, 0.13224647, 0.13184206, 0.13145177,
         0.13107342, 0.1307077 , 0.13035275, 0.1300059 , 0.12967103,
         0.12934572, 0.12902805, 0.12872038, 0.12841978, 0.12812733,
         0.1278437 , 0.12756626, 0.12729608, 0.12703349, 0.1267752 ],
        [0.16098932, 0.16076938, 0.16055744, 0.16035461, 0.1601602 ,
         0.15997435, 0.15979612, 0.1596256 , 0.15946161, 0.15930334,
         0.15915105, 0.15900444, 0.15886331, 0.1587277 , 0.15859688,
         0.15847044, 0.1583487 , 0.15823144, 0.15811732, 0.15800712,
         0.15790033, 0.15779705, 0.15769687, 0.15760021, 0.15750605,
         0.15741478, 0.15732574, 0.15724029, 0.15715674, 0.15707563,
         0.15699647, 0.15691931, 0.15684423, 0.15677114, 0.15670023,
         0.15663087, 0.15656296, 0.15649725, 0.15643284, 0.15637   ,
         0.15630883, 0.15624946, 0.15619138, 0.15613436, 0.15607875,
         0.15602396, 0.15597063, 0.15591828, 0.15586711, 0.15581696]]])
UmatTN = np.average(Umat,axis=1)
UmatTN = np.array([[0.16098932, 0.15988504, 0.15885114, 0.1578939 , 0.15698791,
        0.15614914, 0.15535221, 0.15460475, 0.15389935, 0.15323001,
        0.15259883, 0.15200226, 0.15143356, 0.15089469, 0.15038052,
        0.14988949, 0.14942047, 0.14897273, 0.14854354, 0.14813223,
        0.14773878, 0.14735943, 0.14699538, 0.14664468, 0.14630751,
        0.14598394, 0.14566938, 0.14536866, 0.14507634, 0.14479455,
        0.14452149, 0.14425836, 0.14400284, 0.14375697, 0.14351668,
        0.14328304, 0.14305753, 0.14283781, 0.14262495, 0.14241763,
        0.14221686, 0.14201988, 0.14182961, 0.14164386, 0.14146254,
        0.14128568, 0.14111329, 0.14094635, 0.1407817 , 0.14062206],
       [0.16098932, 0.15942418, 0.15801238, 0.15674382, 0.15557465,
        0.15450907, 0.15352386, 0.15260862, 0.15176086, 0.15096786,
        0.15022804, 0.14953912, 0.14888599, 0.14827011, 0.14769226,
        0.14714331, 0.1466207 , 0.14612412, 0.14565334, 0.14520526,
        0.1447739 , 0.14436384, 0.14397069, 0.14359301, 0.14323305,
        0.14288473, 0.14255381, 0.14223315, 0.1419249 , 0.14162679,
        0.1413399 , 0.1410631 , 0.14079618, 0.14053831, 0.14028649,
        0.14004326, 0.13980724, 0.13957913, 0.13935681, 0.1391414 ,
        0.13893259, 0.13873064, 0.13853292, 0.13834253, 0.13815631,
        0.13797487, 0.13779831, 0.13762559, 0.13745751, 0.1372951 ],
       [0.16098932, 0.15992573, 0.1589289 , 0.15801375, 0.15714118,
        0.15633347, 0.15556415, 0.15484367, 0.15416053, 0.15351289,
        0.15289951, 0.15231622, 0.15176134, 0.15123272, 0.15073032,
        0.15024955, 0.1497921 , 0.14935545, 0.14893696, 0.14853721,
        0.14815275, 0.14778513, 0.14743142, 0.14709302, 0.1467665 ,
        0.14645335, 0.14615059, 0.14586005, 0.14557845, 0.14530735,
        0.14504505, 0.14479103, 0.14454535, 0.1443066 , 0.144076  ,
        0.14385214, 0.14363533, 0.143425  , 0.14321937, 0.14302052,
        0.14282728, 0.14263876, 0.14245588, 0.14227707, 0.14210304,
        0.14193383, 0.14176844, 0.14160718, 0.1414503 , 0.14129608]])
     '''
    Udim = np.ndim(U)
    if Udim == 2: # Node Sampling
        (numTN, numTests) = U.shape
        numTests -= 1 # The first entry of U should denote 0 tests
        # Normalize U so that no data produces no utility
        if U[0][1] > U[0][0]: # We have utility; make into a loss
            #utilNotLoss = True
            pass
        else: # We have loss
            #utilNotLoss = False
            U = U * -1
            pass
        # Add first element (corresponding to no testing) to all elements of U
        addElem = U[0][0]*-1
        U = U + addElem

        # Create pw-linear approximation of U for non-integer number of tests
        def Upw(U,node,n):
            if n > U.shape[1] or n < 0:
                print('n value is outside the feasible range.')
                return
            nflr, nceil = int(np.floor(n)), int(np.ceil(n))
            nrem = n-nflr # decimal remainder
            return U[node][nceil]*(nrem) + U[node][nflr]*(1-nrem)
        def vecUpw(U,x):
            retVal = 0
            for i in range(len(x)):
                retVal += Upw(U,i,x[i])
            return retVal
        def negVecUpw(x,U):
            return vecUpw(U,x)*-1
        # Initialize x
        xinit = np.zeros((numTN))
        # Maximize the utility
        bds = spo.Bounds(np.repeat(0,numTN),np.repeat(numTests,numTN))
        linConstraint = spo.LinearConstraint(np.repeat(1,numTN),0,numTests)
        spoOutput = spo.minimize(negVecUpw,xinit,args=(U),method='SLSQP',constraints=linConstraint,
                                 bounds=bds,options={'ftol': 1e-15}) # Reduce tolerance if not getting integer solutions
        sol = np.round(spoOutput.x,3)
        maxU = spoOutput.fun * -1

    return sol, maxU


def plotAlloc(allocArr,paramList,testInt=1,al=0.6,titleStr='',colors=[],dashes=[],labels=[]):
    '''
    Produces a plot of an array of allocations relative to the parameters in paramList.
    allocArr should have numTN rows and |paramList| columns
    '''
    if len(colors) == 0:
        colors = cm.rainbow(np.linspace(0, 1, allocArr.shape[0]))
    if len(dashes) == 0:
        dashes = [[1,tnind] for tnind in range(allocArr.shape[0])]
    if len(labels) == 0:
        labels = ['Test Node '+str(tnind+1) for tnind in range(allocArr.shape[0])]
    for tnind in range(allocArr.shape[0]):
        plt.plot(paramList, allocArr[tnind]*testInt, dashes=dashes[tnind], linewidth=2.5, color=colors[tnind],
                 label=labels[tnind], alpha=al)
    plt.legend()
    plt.ylim([0., allocArr.max()*testInt*1.1])
    plt.xlabel('Parameter Value')
    plt.ylabel('Test Node Allocation')
    plt.title('Test Node Allocation\n'+titleStr)
    plt.savefig('NODEALLOC.png')
    plt.show()
    plt.close()
    return

def allocationExample():
    '''Use example outputs to create illustration of allocation decision'''
    Umat = np.array([[[0.16098932, 0.15926648, 0.15765788, 0.15617675, 0.15477563,
                       0.15348549, 0.15225739, 0.15110963, 0.1500301, 0.14900606,
                       0.14803931, 0.14712575, 0.14625472, 0.14543112, 0.14464693,
                       0.14389572, 0.14317966, 0.1424973, 0.14184333, 0.14121736,
                       0.14061906, 0.14004235, 0.13948944, 0.13895668, 0.13844451,
                       0.1379546, 0.13747691, 0.13702124, 0.13657725, 0.13615013,
                       0.13573617, 0.13533675, 0.13494959, 0.13457688, 0.13421297,
                       0.13385875, 0.13351799, 0.13318551, 0.13286335, 0.13254984,
                       0.13224531, 0.13194758, 0.13165973, 0.13137863, 0.13110483,
                       0.13083779, 0.13057652, 0.13032458, 0.13007499, 0.12983474],
                      [0.16098932, 0.16050359, 0.16004441, 0.15961104, 0.15920019,
                       0.15881279, 0.15844703, 0.15809987, 0.1577686, 0.15745397,
                       0.15715835, 0.15687877, 0.1566124, 0.15635826, 0.15611412,
                       0.15588327, 0.15566128, 0.15544816, 0.15524374, 0.15504709,
                       0.1548585, 0.15467651, 0.15450132, 0.15433268, 0.1541705,
                       0.15401328, 0.15386185, 0.15371607, 0.15357544, 0.15343897,
                       0.15330682, 0.15317997, 0.15305609, 0.15293706, 0.1528204,
                       0.15270733, 0.15259706, 0.15249011, 0.15238656, 0.15228543,
                       0.15218841, 0.15209217, 0.15199949, 0.15190909, 0.15182026,
                       0.15173358, 0.15165006, 0.15156812, 0.15148841, 0.15140938]],
                     [[0.16098932, 0.15976119, 0.15860766, 0.1575474, 0.15653261,
                       0.15559973, 0.15471447, 0.15388067, 0.1530916, 0.15234469,
                       0.15163571, 0.15096929, 0.1503275, 0.14971716, 0.14913831,
                       0.14858463, 0.14805327, 0.14754521, 0.14705872, 0.14659065,
                       0.1461412, 0.14570923, 0.14529534, 0.144893, 0.14451055,
                       0.14413559, 0.14377903, 0.14342948, 0.14309588, 0.14276969,
                       0.14245412, 0.1421502, 0.14185658, 0.14157105, 0.14129151,
                       0.14102223, 0.14075931, 0.14050511, 0.14025716, 0.14001543,
                       0.13978049, 0.13955197, 0.13932882, 0.13911313, 0.13890055,
                       0.13869456, 0.13849415, 0.13829679, 0.13810486, 0.13791963],
                      [0.16098932, 0.15908717, 0.15741709, 0.15594023, 0.15461668,
                       0.1534184, 0.15233326, 0.15133658, 0.15043013, 0.14959103,
                       0.14882037, 0.14810896, 0.14744448, 0.14682306, 0.14624621,
                       0.14570199, 0.14518813, 0.14470303, 0.14424797, 0.14381987,
                       0.1434066, 0.14301845, 0.14264604, 0.14229303, 0.14195554,
                       0.14163387, 0.14132859, 0.14103681, 0.14075392, 0.14048389,
                       0.14022569, 0.139976, 0.13973578, 0.13950557, 0.13928147,
                       0.13906428, 0.13885516, 0.13865315, 0.13845647, 0.13826738,
                       0.13808469, 0.13790931, 0.13773702, 0.13757194, 0.13741207,
                       0.13725517, 0.13710246, 0.13695439, 0.13681016, 0.13667057]],
                     [[0.16098932, 0.15908208, 0.15730035, 0.15567289, 0.15412215,
                       0.1526926, 0.15133218, 0.15006174, 0.14885946, 0.14772244,
                       0.14664797, 0.145628, 0.14465938, 0.14373773, 0.14286377,
                       0.14202867, 0.14123549, 0.14047947, 0.13975659, 0.13906729,
                       0.13840516, 0.13777321, 0.13716596, 0.13658584, 0.13602695,
                       0.13549191, 0.13497545, 0.13447982, 0.13400015, 0.13353907,
                       0.13309363, 0.13266275, 0.13224647, 0.13184206, 0.13145177,
                       0.13107342, 0.1307077, 0.13035275, 0.1300059, 0.12967103,
                       0.12934572, 0.12902805, 0.12872038, 0.12841978, 0.12812733,
                       0.1278437, 0.12756626, 0.12729608, 0.12703349, 0.1267752],
                      [0.16098932, 0.16076938, 0.16055744, 0.16035461, 0.1601602,
                       0.15997435, 0.15979612, 0.1596256, 0.15946161, 0.15930334,
                       0.15915105, 0.15900444, 0.15886331, 0.1587277, 0.15859688,
                       0.15847044, 0.1583487, 0.15823144, 0.15811732, 0.15800712,
                       0.15790033, 0.15779705, 0.15769687, 0.15760021, 0.15750605,
                       0.15741478, 0.15732574, 0.15724029, 0.15715674, 0.15707563,
                       0.15699647, 0.15691931, 0.15684423, 0.15677114, 0.15670023,
                       0.15663087, 0.15656296, 0.15649725, 0.15643284, 0.15637,
                       0.15630883, 0.15624946, 0.15619138, 0.15613436, 0.15607875,
                       0.15602396, 0.15597063, 0.15591828, 0.15586711, 0.15581696]]])
    Q = np.array([[0.4881994 , 0.5118006 ], [0.72190074, 0.27809926],[0.48207174, 0.51792826]])
    i1, i2, i3 = 0.7, 0.1, 0.3
    Q = np.array([[i1, 1-i1], [i2, 1-i2], [i3, 1-i3]])

    UmatQ = np.zeros((Umat.shape[0],Umat.shape[2]))
    for i in range(len(Umat)):
        for j in range(Umat.shape[2]):
            UmatQ[i][j] = Umat[i][0][j] * Q[i][0] + Umat[i][1][j] * Q[i][1]

    UmatQ1 = UmatQ[:,:41]

    sol,func = GetOptAllocation(UmatQ1)
    print(sol)

    # Evaluate utility of different allocations
    def utilgain(U, node, n):
        if n > U.shape[1] or n < 0:
            print('n value is outside the feasible range.')
            return
        nflr, nceil = int(np.floor(n)), int(np.ceil(n))
        nrem = n - nflr  # decimal remainder
        return (U[node][nceil] * (nrem) + U[node][nflr] * (1 - nrem) -U[node][0])*-1

    def vecUpw(U, x):
        retVal = 0
        for i in range(len(x)):
            retVal += utilgain(U, i, x[i])
        return retVal

    sol1 = np.array([18,16,6])
    vecUpw(UmatQ,sol1)

    # Plot UmatQ for each test node
    import matplotlib.patheffects as pe
    fig, ax = plt.subplots(figsize=(8, 7))
    plt.plot(UmatQ[0]*-1+0.3, 'b-',alpha=0.6, linewidth=5,label='Test Node 1',
                 path_effects=[pe.Stroke(linewidth=7, foreground='b',alpha=0.2), pe.Normal()])
    plt.plot(UmatQ[1]*-1+0.3, 'r-', alpha=0.6, linewidth=5, label='Test Node 2',
             path_effects=[pe.Stroke(linewidth=7, foreground='r', alpha=0.2), pe.Normal()])
    plt.plot(UmatQ[2]*-1+0.3, 'g-', alpha=0.6, linewidth=5, label='Test Node 3',
             path_effects=[pe.Stroke(linewidth=7, foreground='g', alpha=0.2), pe.Normal()])
    plt.title('Utility under data from different test nodes',
              fontdict={'fontsize': 20, 'fontname': 'Trebuchet MS'})
    plt.ylabel('Expected utility', fontdict={'fontsize': 16, 'fontname': 'Trebuchet MS'})
    plt.ylim([0.125, 0.165])
    ax.tick_params(axis='both', which='major', labelsize=12)
    plt.xlabel('Tests', fontdict={'fontsize': 16, 'fontname': 'Trebuchet MS'})
    plt.legend(loc='lower right',fontsize=16)
    fig.tight_layout()
    plt.show()
    plt.close()

    return

def exampleSCscratchForAlgDebug():
    N = np.array([[6, 11], [12, 6], [2, 13]])
    Y = np.array([[3, 0], [6, 0], [0, 0]])
    (numTN, numSN) = N.shape
    s, r = 1., 1.
    scDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r,
                                       numSamples=0, dataType='Tracked', randSeed=2)
    scDict['diagSens'], scDict['diagSpec'] = s, r
    scDict = util.GetVectorForms(scDict)
    scDict['N'], scDict['Y'] = N, Y
    scDict['prior'] = methods.prior_normal()
    scDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    scDict['importerNum'], scDict['outletNum'] = numSN, numTN
    # Generate posterior draws
    numdraws = 80000  # Evaluate choice here
    scDict['numPostSamples'] = numdraws
    scDict = methods.GeneratePostSamples(scDict)
    # Define a loss dictionary
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic', 'threshold': t}
    marketvec = np.ones(numTN + numSN)
    lossDict = {'scoreDict': scoredict, 'riskDict': riskdict, 'marketVec': marketvec}
    #lossMat = lossMatrix(scDict['postSamples'], lossDict)
    #lossDict.update({'lossMat':lossMat})
    # Design
    design = np.array([1.,0.,0.])
    # Sourcing matrix
    Q = np.array([[0.4, 0.6],[0.8, 0.2],[0.5, 0.5]])
    scDict.update({'transMat':Q})
    # Utility dictionary
    numbayesdraws = 6250
    utilDict = {'method':'weightsNodeDraw3'}
    utilDict.update({'numdrawsfordata':6400})
    utilDict.update({'numdrawsforbayes':numbayesdraws})

    testMax, testInt = 100, 10
    numdrawstouse = int(40000000/numbayesdraws)

    scDictTemp = scDict.copy()
    scDictTemp.update({'postSamples':scDict['postSamples'][choice(np.arange(numdraws),size=numdrawstouse,replace=False)],
                       'numPostSamples':numdrawstouse})

    margUtilArr = GetMargUtilAtNodes(scDictTemp, testMax, testInt, lossDict, utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, titleStr='Number of draws for selecting Bayes estimate: '+str(numbayesdraws))
    sol, maxUval = GetOptAllocation(margUtilArr)
    print(sol)





    ###################################################################################################################
    ###################################################################################################################
    ### SET OF RUNS FOR ESTABLISHING NOISE FOR DIFFERENT UTILITY ESTIMATES, UNDER EXAMPLE SC
    ###################################################################################################################
    ###################################################################################################################
    # Get a baseline under 0 tests
    baselineVec=[]
    for i in range(25):
        randinds = choice([i for i in range(numdraws)],size=5000)
        tempDict=scDict.copy()
        newdraws=scDict['postSamples'][randinds]
        tempDict.update({'postSamples':newdraws})
        lossMat = lossMatrix(tempDict['postSamples'], lossDict)
        lossDict.update({'lossMat':lossMat})
        baseUtil = getDesignUtility(priordatadict=tempDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                           numtests=0, utildict=utilDict.copy())[0]
        print(baseUtil)
        baselineVec.append(baseUtil)
    baseAvg = np.average(baselineVec)


    testInt = 5
    testMax = 100
    timeArr = np.zeros((numTN, int(testMax / testInt)+1))
    resArr = np.zeros((numTN,int(testMax/testInt)+1))
    for desInd in range(numTN):
        design=np.zeros(numTN)
        design[desInd]=1.
        for Ntests in range(0,testMax+1,testInt):
            time1=time.time()
            currscDict = scDict.copy()
            randinds = choice([i for i in range(numdraws)], size=1000)
            currscDict.update({'postSamples':scDict['postSamples'][randinds]})
            lossMat = lossMatrix(currscDict['postSamples'], lossDict)
            lossDict.update({'lossMat': lossMat})
            res = baseAvg - getDesignUtility(priordatadict=currscDict.copy(), lossdict=lossDict.copy(),
                                            designlist=[design], numtests=Ntests, utildict=utilDict.copy())[0]
            timeArr[desInd][int(Ntests/testInt)] = round(time.time()-time1)
            resArr[desInd][int(Ntests/testInt)] = res
            print('Design '+str(desInd+1)+', Ntests '+str(Ntests)+' complete; time: '+str(round(time.time()-time1)))


    '''
    for 1000 prior draws:
    timeArr = np.array([[1., 2., 1., 1., 1., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 1., 0.],
       [1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0.,
        0., 1., 0., 1., 0.],
       [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0.]])
    resArr1000 = np.array([[ 0.00159311,  0.00418471,  0.0062269 ,  0.00895704,  0.01323657,
         0.01325995,  0.01839366,  0.02107369,  0.02046441,  0.02249531,
         0.02347999,  0.02218667,  0.02318638,  0.02614432,  0.02686565,
         0.02731426,  0.02932006,  0.02803005,  0.03035949,  0.0299379 ,
         0.03275276],
       [-0.00699   ,  0.00791442,  0.00880313,  0.01171479,  0.01525231,
         0.0163157 ,  0.02201907,  0.02193683,  0.02792523,  0.02662289,
         0.02669167,  0.03019786,  0.029042  ,  0.03088749,  0.03442847,
         0.03430848,  0.03418094,  0.03888811,  0.03765799,  0.03988821,
         0.0408746 ],
       [-0.00017592,  0.00285291,  0.00549835,  0.00843239,  0.01292921,
         0.01452094,  0.01602438,  0.01568046,  0.02107726,  0.02223076,
         0.02307271,  0.02589357,  0.02612889,  0.02753352,  0.02761555,
         0.03111052,  0.03090632,  0.02964345,  0.03179872,  0.03128028,
         0.03337345]])
    for 2000 prior draws:
    timeArr = np.array([[4., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2.,
        2., 2., 2., 2., 2.],
       [2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2.,
        2., 2., 2., 2., 2.],
       [2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2.,
        2., 2., 2., 2., 2.]])
    resArr2000 = np.array([[-0.00167857,  0.00637426,  0.00855596,  0.00976534,  0.01164906,
         0.01487943,  0.01525576,  0.02073503,  0.0190061 ,  0.02372901,
         0.02407007,  0.02525577,  0.02435303,  0.02641542,  0.0280954 ,
         0.02738228,  0.0293965 ,  0.02949504,  0.02941072,  0.03089783,
         0.03171672],
       [-0.00170394,  0.00751629,  0.00816319,  0.01271623,  0.01529189,
         0.01957194,  0.0217479 ,  0.02441013,  0.02636045,  0.02801888,
         0.02785735,  0.02984962,  0.03238839,  0.03145008,  0.03166865,
         0.0348702 ,  0.03698629,  0.03704807,  0.03803051,  0.03879708,
         0.04143042],
       [-0.00016478,  0.00301231,  0.00660184,  0.00974423,  0.01499728,
         0.01793905,  0.01796053,  0.01758067,  0.02091836,  0.02299648,
         0.0233177 ,  0.02370586,  0.02589604,  0.02755232,  0.02709835,
         0.02663809,  0.03262958,  0.03104109,  0.03216134,  0.03189571,
         0.03393449]])
    for 3000 prior draws:
    timeArr = np.array([[7., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5.,
        5., 5., 4., 5., 5.],
       [5., 5., 5., 5., 4., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5.,
        5., 5., 5., 5., 5.],
       [4., 5., 5., 5., 5., 5., 5., 5., 5., 7., 6., 5., 5., 5., 5., 5.,
        5., 5., 5., 5., 5.]])
    resArr3000 = np.array([[-2.13834334e-03,  7.40874028e-03,  6.65411132e-03,
         1.01627335e-02,  1.45420624e-02,  1.49715005e-02,
         1.62628890e-02,  1.71322786e-02,  1.99306632e-02,
         2.35843040e-02,  2.61979321e-02,  2.45403017e-02,
         2.61094519e-02,  2.47844136e-02,  2.62445474e-02,
         2.83188904e-02,  2.84600632e-02,  3.12486701e-02,
         3.08744364e-02,  3.12662379e-02,  3.24095007e-02],
       [-6.02671383e-05,  5.39049310e-03,  7.25757319e-03,
         1.23909949e-02,  1.57591463e-02,  1.94971343e-02,
         2.20110552e-02,  2.59353171e-02,  2.64166397e-02,
         2.77745519e-02,  2.92782719e-02,  2.88195519e-02,
         3.34315880e-02,  3.27045536e-02,  3.44270497e-02,
         3.71100634e-02,  3.68632695e-02,  3.71862966e-02,
         3.69599021e-02,  3.83762973e-02,  3.92994635e-02],
       [ 8.25856064e-04,  5.75927627e-03,  7.49853812e-03,
         1.19071838e-02,  1.15558762e-02,  1.80925833e-02,
         1.76435224e-02,  2.18948729e-02,  2.13119948e-02,
         2.32002908e-02,  2.32411425e-02,  2.62877728e-02,
         2.50494052e-02,  2.67017512e-02,  2.60101225e-02,
         3.07262639e-02,  3.04242972e-02,  3.03481937e-02,
         3.12410146e-02,  3.07281928e-02,  3.28466663e-02]])
    for 4000 prior draws:
    timeArr = np.array([[ 9.,  9., 10.,  9.,  9.,  9., 10.,  9.,  9.,  9.,  9.,  9.,  9.,
         9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.],
       [ 9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,
         9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.],
       [ 9., 10.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.,
         9.,  9.,  9.,  9.,  9.,  9.,  9.,  9.]])
    resArr4000 = np.array([[-0.00125006,  0.00455918,  0.00596942,  0.00959156,  0.01385264,
         0.01497621,  0.01756948,  0.01792961,  0.02150224,  0.0214486 ,
         0.02383869,  0.02524205,  0.02507577,  0.02716952,  0.02795667,
         0.02816161,  0.03143439,  0.03021209,  0.03199355,  0.03219852,
         0.03348309],
       [-0.00018571,  0.0054182 ,  0.01050196,  0.01241348,  0.01647457,
         0.01861406,  0.02154789,  0.0227189 ,  0.02665793,  0.02818191,
         0.02786874,  0.03082077,  0.03237958,  0.03269404,  0.0351905 ,
         0.03600581,  0.03770573,  0.0373656 ,  0.03679003,  0.03855222,
         0.03940719],
       [ 0.00058917,  0.00640784,  0.00936066,  0.01172114,  0.01405519,
         0.01549102,  0.01862859,  0.02103447,  0.01928631,  0.02261242,
         0.022648  ,  0.02425976,  0.02635621,  0.02803802,  0.02794364,
         0.02892531,  0.02974113,  0.03218838,  0.03113268,  0.03289169,
         0.0323915 ]])
    for 5000 prior draws:
    timeArr = np.array([[29., 27., 23., 25., 30., 24., 17., 16., 18., 16., 15., 15., 15.,
        15., 15., 16., 16., 16., 15., 15., 16.],
       [15., 15., 15., 16., 16., 16., 16., 16., 24., 19., 20., 24., 17.,
        16., 16., 17., 20., 19., 17., 16., 19.],
       [18., 19., 20., 19., 18., 17., 17., 18., 17., 17., 18., 17., 16.,
        16., 17., 17., 17., 17., 17., 17., 16.]]
    resArr5000 = np.array([[6.89660644e-05, 4.10008155e-03, 8.05410916e-03, 1.12873831e-02,
        1.39424080e-02, 1.54226618e-02, 1.73034505e-02, 1.81846310e-02,
        2.06818379e-02, 2.21695317e-02, 2.46157877e-02, 2.47610638e-02,
        2.52565608e-02, 2.71944750e-02, 2.86383522e-02, 2.91120950e-02,
        2.92109740e-02, 3.02115822e-02, 3.22780934e-02, 3.17034442e-02,
        3.35250549e-02],
       [1.08889276e-03, 5.91813266e-03, 1.01146011e-02, 1.37066550e-02,
        1.65180788e-02, 1.93990489e-02, 2.14668000e-02, 2.51308676e-02,
        2.62939116e-02, 2.81707128e-02, 2.86727950e-02, 3.07502177e-02,
        3.13708921e-02, 3.32215273e-02, 3.33406986e-02, 3.49946406e-02,
        3.63782803e-02, 3.72631594e-02, 3.75954257e-02, 3.74843946e-02,
        3.93600286e-02],
       [1.69694541e-03, 4.84563878e-03, 7.05934835e-03, 1.14981791e-02,
        1.32252145e-02, 1.70971635e-02, 1.84716717e-02, 1.94952083e-02,
        2.16529222e-02, 2.37018257e-02, 2.33494840e-02, 2.63780620e-02,
        2.61132133e-02, 2.70204491e-02, 2.76134405e-02, 3.04763642e-02,
        2.96451701e-02, 3.12498391e-02, 3.09408894e-02, 3.34448161e-02,
        3.28314890e-02]])
        
    for 6000 prior draws:
    timeArr = np.array([[58., 42., 45., 38., 46., 38., 40., 42., 45., 40., 42., 46., 40.,
        37., 44., 45., 43., 44., 50., 43., 36.],
       [46., 43., 41., 54., 56., 43., 43., 44., 32., 42., 47., 49., 44.,
        45., 45., 48., 45., 53., 37., 37., 40.],
       [55., 48., 40., 48., 44., 39., 58., 47., 41., 51., 36., 49., 52.,
        43., 42., 39., 35., 42., 43., 40., 39.]])
    resArr6000 = np.array([[-8.11146826e-05,  4.71066494e-03,  8.17931663e-03,
         9.71956948e-03,  1.38456486e-02,  1.41687236e-02,
         1.58361499e-02,  1.87968160e-02,  2.11285718e-02,
         2.25592396e-02,  2.46750812e-02,  2.38927669e-02,
         2.58073982e-02,  2.70563219e-02,  2.94438942e-02,
         3.06479700e-02,  3.09371649e-02,  3.21300696e-02,
         3.16848311e-02,  3.26015134e-02,  3.28548809e-02],
       [-2.25461852e-04,  5.46979604e-03,  9.97871659e-03,
         1.36761718e-02,  1.59532232e-02,  1.86941271e-02,
         2.16212905e-02,  2.33833771e-02,  2.56299705e-02,
         2.61149046e-02,  3.01841634e-02,  2.95405078e-02,
         3.22385126e-02,  3.35873444e-02,  3.38901597e-02,
         3.52389982e-02,  3.71442180e-02,  3.73916572e-02,
         3.71822596e-02,  3.82220653e-02,  3.99729121e-02],
       [ 6.75487014e-04,  3.30214603e-03,  8.31503779e-03,
         1.26715321e-02,  1.41274677e-02,  1.59647781e-02,
         1.83714139e-02,  1.95429948e-02,  2.12826167e-02,
         2.34451664e-02,  2.42501368e-02,  2.52256962e-02,
         2.57751529e-02,  2.72398996e-02,  2.85090366e-02,
         2.91266687e-02,  3.10607272e-02,  3.18272571e-02,
         3.13823792e-02,  3.23414072e-02,  3.27573212e-02]])
    '''
    x1 = range(0, testMax + 1, testInt)
    colors = ['blue', 'red', 'green']
    al = 0.3
    for tnind in range(numTN):
        plt.plot(x1, resArr6000[tnind], linewidth=4, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
        #plt.plot(x1, resArr5000[tnind], linewidth=3.5, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
        #plt.plot(x1, resArr4000[tnind], linewidth=3, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
        #plt.plot(x1, resArr3000[tnind], linewidth=2.5, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
        #plt.plot(x1, resArr2000[tnind], linewidth=2, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
        #plt.plot(x1, resArr1000[tnind], linewidth=1.5, color=colors[tnind], label='TN ' + str(tnind + 1),alpha=al)
    plt.legend()
    plt.ylim([-0.01, 0.04])
    plt.xlabel('Number of Tests')
    plt.ylabel('Utility Gain')
    plt.title('Use of Loss Matrices of size $6000^2$')
    plt.show()

    ###################################################################################################################
    ###################################################################################################################
    ###################################################################################################################
    ###################################################################################################################

    resultArr = np.zeros((4,10))
    for run in range(9):
        scDict['numPostSamples'] = 10000
        scDict = methods.GeneratePostSamples(scDict)
        print('Prior draws amount of: '+str(10000))
        res  = getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                         numtests=20, method='weightsNodeDraw2', printUpdate=False)
        resultArr[3,run] = res[0]

    timesArr = [()/10]
    # 1000: 0.1s avg.
    # 4000: 14s
    # 7000: 50s
    # 10000: 150s
    '''
    resultArr=np.array([[0.14638964, 0.1484343 , 0.14046411, 0.14869244, 0.14333638,
        0.14628762, 0.14548798, 0.14313576, 0.15024421, 0.14447308],
       [0.14738599, 0.14381345, 0.14225808, 0.14669578, 0.1450945 ,
        0.14567533, 0.1439226 , 0.14614024, 0.14199987, 0.14464842],
       [0.14410364, 0.14761772, 0.14438702, 0.14349538, 0.14557104,
        0.14497851, 0.14576323, 0.14542397, 0.14650968, 0.14565662],
       [0.14590605, 0.14425943, 0.14619828, 0.14536332, 0.14542653,
        0.14500895, 0.14701813, 0.14651643, 0.14694187, 0.14487658 ]])
    '''

    x = [1000,4000,7000,10000]
    for i in range(10):
        plt.plot(x,resultArr[:,i],'bo')
    plt.show()

    return

def exampleSupplyChainForPaper():
    N = np.array([[6, 9], [10, 5], [2, 13]])
    Y = np.array([[3, 0], [4, 1], [0, 0]])
    (numTN, numSN) = N.shape
    s, r = 1., 1.
    scDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r,
                                       numSamples=0, dataType='Tracked', randSeed=2)
    scDict['diagSens'], scDict['diagSpec'] = s, r
    scDict = util.GetVectorForms(scDict)
    scDict['N'], scDict['Y'] = N, Y
    scDict['prior'] = methods.prior_normal()
    scDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    scDict['importerNum'], scDict['outletNum'] = numSN, numTN
    # Generate posterior draws
    numdraws = 50000  # Evaluate choice here
    scDict['numPostSamples'] = numdraws
    scDict = methods.GeneratePostSamples(scDict)
    # Define a loss dictionary
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic', 'threshold': t}
    marketvec = np.ones(numTN + numSN)
    lossDict = {'scoreDict': scoredict, 'riskDict': riskdict, 'marketVec': marketvec}
    # lossMat = lossMatrix(scDict['postSamples'], lossDict)
    # lossDict.update({'lossMat':lossMat})

    # Sourcing matrix
    #todo: EVALUATE HERE
    Q = np.array([[0.4, 0.6], [0.8, 0.2], [0.5, 0.5]])
    scDict.update({'transMat': Q})

    # Utility dictionary
    numbayesdraws = 4000
    utilDict = {'method': 'weightsNodeDraw4'}
    utilDict.update({'numdrawsfordata': 5000})
    utilDict.update({'numdrawsforbayes': numbayesdraws})

    # PATH SAMPLING
    # Design
    # todo: EVALUATE HERE
    design1 = np.array([[0., 0.],[0., 0.],[1., 0.]])
    design2 = np.array([[1/6, 1/6], [1/6, 1/6], [1/6, 1/6]])
    design3 = np.array([[1/3., 0.], [1/3, 1/3], [0., 0.]])


    testMax, testInt = 90, 6
    numdrawstouse = int(21000000 / numbayesdraws)

    ### INITIAL BASELINE RUN ###
    scDictTemp = scDict.copy()
    scDictTemp.update(
        {'postSamples': scDict['postSamples'][choice(np.arange(numdraws), size=numdrawstouse, replace=False)],
         'numPostSamples': numdrawstouse})
    margUtilArr = GetMargUtilForDesigns([design1,design2,design3],scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue','red','green'],labels=['Focused', 'Balanced', 'Adapted'])
    '''
    margUtilArr = np.array([[0.        , 0.01852929, 0.02953051, 0.03632656, 0.04097865,
        0.04483184, 0.04778626, 0.04974943, 0.05181481, 0.05342801,
        0.05461887, 0.05592533, 0.05690447, 0.0579397 , 0.05863615,
        0.05963775],
       [0.        , 0.01347157, 0.02419357, 0.03336116, 0.04042465,
        0.04700311, 0.0527395 , 0.0579747 , 0.06284166, 0.06661737,
        0.07066176, 0.07367343, 0.07695087, 0.08022942, 0.08311687,
        0.08554483],
       [0.        , 0.0154116 , 0.02665288, 0.03523782, 0.0423525 ,
        0.04779582, 0.05337669, 0.05754389, 0.06058983, 0.06362043,
        0.06717655, 0.0699163 , 0.0725836 , 0.07417217, 0.07686587,
        0.07861654]])
    '''

    ### CHANGE LOSS PARAMETERS RUNS ###
    lossDict['scoreDict'].update({'underEstWt':5.})
    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    '''
    margUtilArr = np.array([[0.        , 0.03442348, 0.05774904, 0.07150046, 0.08239403,
        0.08999229, 0.09596104, 0.10124705, 0.10546559, 0.10948336,
        0.1123805 , 0.11472817, 0.11742127, 0.11967013, 0.12166973,
        0.12293726],
       [0.        , 0.03185775, 0.05921106, 0.07907966, 0.09902923,
        0.11517918, 0.12913951, 0.14299884, 0.1522742 , 0.16172451,
        0.17151435, 0.18029   , 0.18766698, 0.19616199, 0.20189169,
        0.20769016],
       [0.        , 0.03490163, 0.05617731, 0.07737544, 0.09462548,
        0.10807706, 0.11900253, 0.12845375, 0.13603955, 0.14453562,
        0.15306903, 0.15837267, 0.1639823 , 0.16943507, 0.17401165,
        0.17859663]])
     plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='AbsDiff Loss with $v=5$')
    '''
    ### CHANGE LOSS
    lossDict['scoreDict'].update({'underEstWt': 0.2})
    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    '''
    margUtilArr = np.array([[0.        , 0.0061618 , 0.00951152, 0.01180287, 0.01331707,
        0.01460648, 0.01545818, 0.01624678, 0.01677136, 0.01742774,
        0.01775878, 0.01828225, 0.01850621, 0.01876372, 0.01908667,
        0.01940038],
       [0.        , 0.00356379, 0.00630727, 0.00827012, 0.0103652 ,
        0.01225727, 0.0139363 , 0.01513112, 0.01657184, 0.01757065,
        0.01897108, 0.01961579, 0.02071898, 0.02133125, 0.02211464,
        0.02278893],
       [0.        , 0.00383605, 0.00643516, 0.0085795 , 0.01053073,
        0.01211568, 0.0135415 , 0.014919  , 0.01598923, 0.01689425,
        0.01784307, 0.01859931, 0.01919649, 0.01990698, 0.02082598,
        0.02107902]])
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='AbsDiff Loss with $v=0.1$')
    '''
    ### CHANGE RISK
    lossDict['scoreDict'].update({'underEstWt': 1.})
    lossDict['riskDict'].update({'name':'Check','slope':0.3,'threshold':0.8})
    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    '''
    margUtilArr = np.array([[0.        , 0.00940468, 0.01463505, 0.01834134, 0.02077151,
        0.02264891, 0.02420394, 0.0253703 , 0.02637385, 0.02726177,
        0.02803475, 0.02864719, 0.02923242, 0.02977877, 0.03015922,
        0.03062128],
       [0.        , 0.0065018 , 0.01220196, 0.01637743, 0.02003035,
        0.02339057, 0.0260788 , 0.02885167, 0.03104804, 0.03329239,
        0.03479819, 0.0367691 , 0.03785238, 0.03925022, 0.04075274,
        0.04170411],
       [0.        , 0.00801315, 0.0136623 , 0.01808018, 0.02181941,
        0.02461012, 0.02747849, 0.02958177, 0.03115108, 0.03279332,
        0.0344746 , 0.0356603 , 0.03681859, 0.03819007, 0.03919466,
        0.0400835 ]])
        plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='Check risk with $m=0.3,l=0.8$')
    '''
    ### ANOTHER RISK CHANGE
    lossDict['scoreDict'].update({'underEstWt': 1.})
    lossDict['riskDict'].update({'name': 'Check', 'slope': 0.7, 'threshold': 0.2})
    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    print('Changing risk...')
    print(margUtilArr)
    '''
        margUtilArr = np.
  plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='Check risk with $m=0.7,l=0.2$')
    '''
    ### SWITCH TO NODE SAMPLING
    design1 = np.array([0., 0., 1.])
    design2 = np.array([1/3, 2/3, 0.])
    design3 = np.array([1 / 3, 1 / 3, 1/3])

    lossDict['scoreDict'].update({'underEstWt': 1.})
    lossDict['riskDict'].update({'name': 'Parabolic', 'slope': 0.5, 'threshold': 0.2})

    Q = np.array([[0.1, 0.9], [0.8, 0.2], [0.05, 0.95]])
    scDictTemp.update({'transMat': Q})

    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    print('Node sampling, pt. 1...')
    print(margUtilArr)
    '''
    margUtilArr = np.array([[0.        , 0.00184836, 0.00393095, 0.0057281 , 0.00702056,
        0.00783352, 0.00901581, 0.01029807, 0.01056239, 0.01184937,
        0.01263652],
       [0.        , 0.008048  , 0.01560508, 0.02168453, 0.02580308,
        0.02936781, 0.03256634, 0.03582316, 0.03801726, 0.03989399,
        0.04210229],
       [0.        , 0.00595198, 0.01185622, 0.01647211, 0.02071877,
        0.02423783, 0.02788743, 0.03048632, 0.03273938, 0.03543375,
        0.03774866]])
  plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='Node sampling with $Q_1$')
    '''

    ### USE A DIFFERENT Q
    Q = np.array([[0.2, 0.8], [0.4, 0.6], [0.1, 0.9]])
    scDictTemp.update({'transMat': Q})

    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    print('Node sampling, pt. 2...')
    print(margUtilArr)

    '''
        margUtilArr = np.array([[0.  ,       0.00789695, 0.01417126, 0.01970823, 0.0238253,  0.02734,
  0.030068,   0.03258318, 0.03471503, 0.03671753, 0.03811212],
 [0.,         0.01340148, 0.02357268, 0.03100924, 0.03646409, 0.0409849,
  0.0453304,  0.04854183, 0.05144865, 0.05394407, 0.05594722],
 [0.,         0.01192867, 0.02081901, 0.0287546,  0.03455062, 0.03946178,
  0.04381905, 0.04698497, 0.05024865, 0.05319858, 0.05590313]])
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='Node sampling with $Q_2$')
    '''

    ### USE A DIFFERENT Q
    Q = np.array([[0.5, 0.5], [0.2, 0.8], [0.7, 0.3]])
    scDictTemp.update({'transMat': Q})

    margUtilArr = GetMargUtilForDesigns([design1, design2, design3], scDictTemp, testMax, testInt, lossDict,
                                        utilDict, printUpdate=True)
    plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'])
    print('Node sampling, pt. 3...')
    print(margUtilArr)

    '''
        margUtilArr = np.array([[0. ,        0.01204654, 0.02025737, 0.02598926, 0.03022982, 0.03367799,
  0.03646451, 0.03878462, 0.0407654,  0.0426331,  0.04398041],
 [0.,         0.01281711, 0.02175156, 0.02822491, 0.03368783, 0.03808503,
  0.04187413, 0.04466803, 0.04742936, 0.04983957, 0.05220403],
 [0.,         0.0132374,  0.02254596, 0.03029985, 0.03649045, 0.0411599,
  0.04573236, 0.04932833, 0.05242475, 0.05530244, 0.05732164]])
  plotMargUtil(margUtilArr, testMax, testInt, colors=['blue', 'red', 'green'],
                 labels=['Focused', 'Balanced', 'Adapted'],titleStr='Node sampling with $Q_3$')
    '''

    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    #################################################
    testBudget = 50
    Umat = np.zeros((numTN, numSN, testBudget + 1))
    for currTN in range(numTN):
        for currSN in range(numSN):
            for currBudget in range(testBudget+1):
                design = np.zeros((numTN,numSN))
                design[currTN][currSN] = 1.
                lossveclist = getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                                       numtests=currBudget, omeganum=1, type=['path'], method='weightsPathEnumerate',
                                       printUpdate=True, numNdraws=0, numYdraws=1)
                Umat[currTN][currSN][currBudget] = lossveclist[0]
            print('TN '+str(currTN)+', SN '+str(currSN)+ ' done')
    '''
    numdraws = 20,000
    Umat = np.array([[[0.16162506, 0.15991211, 0.15827275, 0.15677638, 0.15535571,
         0.15401869, 0.152782  , 0.15160866, 0.15051908, 0.1494803 ,
         0.14848468, 0.14755943, 0.14668634, 0.14584074, 0.14504542,
         0.14427262, 0.14356134, 0.14286261, 0.14220577, 0.14156216,
         0.14096108, 0.1403832 , 0.13981252, 0.13928642, 0.13875738,
         0.13826823, 0.13778085, 0.13732111, 0.13687307, 0.13644055,
         0.13602625, 0.13562136, 0.13522861, 0.13485416, 0.13448627,
         0.13412522, 0.13378789, 0.13344648, 0.13312428, 0.1328063 ,
         0.13249883, 0.13220124, 0.13190874, 0.13162695, 0.13135044,
         0.13107953, 0.13082037, 0.13056134, 0.13031499, 0.13006981,
         0.12983068],
        [0.16162506, 0.16114222, 0.1606847 , 0.16023739, 0.15981965,
         0.15942688, 0.15906732, 0.15871794, 0.15839521, 0.15807584,
         0.15776852, 0.15748453, 0.15721019, 0.15694651, 0.15669296,
         0.15644549, 0.15622702, 0.15601769, 0.15581336, 0.15561243,
         0.15542613, 0.15524249, 0.15506528, 0.15489558, 0.15472803,
         0.15457274, 0.15442251, 0.15428245, 0.15413381, 0.15399307,
         0.15386272, 0.15372827, 0.15360059, 0.1534805 , 0.15336298,
         0.15324937, 0.15313753, 0.15303105, 0.15292499, 0.15282445,
         0.15272493, 0.15262847, 0.15253223, 0.15244195, 0.15235112,
         0.15226514, 0.15218265, 0.15210046, 0.15201738, 0.15193807,
         0.15185731]],
       [[0.16162506, 0.16039918, 0.15920312, 0.15813527, 0.15710529,
         0.15613899, 0.15523386, 0.15438288, 0.1535749 , 0.15283355,
         0.15208957, 0.15142678, 0.15076923, 0.15016084, 0.14955682,
         0.14900587, 0.14846041, 0.14794435, 0.14746074, 0.1469754 ,
         0.14653467, 0.14608069, 0.14567311, 0.14525879, 0.14487702,
         0.14449097, 0.14413674, 0.143782  , 0.143441  , 0.14311049,
         0.14279929, 0.1424831 , 0.14219066, 0.14189884, 0.14161946,
         0.14134332, 0.14107797, 0.14082397, 0.14057233, 0.14033045,
         0.14009118, 0.13985714, 0.1396351 , 0.13941607, 0.13920245,
         0.13899732, 0.13878876, 0.13859687, 0.13839961, 0.13820959,
         0.1380264 ],
        [0.16162506, 0.15965694, 0.15795532, 0.15644765, 0.15510605,
         0.15389283, 0.15278149, 0.15175933, 0.15084693, 0.15000187,
         0.14921806, 0.14847411, 0.14780015, 0.14715659, 0.14657833,
         0.14602292, 0.14550661, 0.14501948, 0.14455305, 0.1441119 ,
         0.1437004 , 0.14331399, 0.14292539, 0.14257288, 0.14223872,
         0.14190862, 0.14159347, 0.14128707, 0.14100097, 0.14073701,
         0.14047307, 0.14022262, 0.13998429, 0.1397534 , 0.13952919,
         0.13930795, 0.13909404, 0.13888792, 0.13869323, 0.13849927,
         0.1383122 , 0.13813134, 0.13796419, 0.13779666, 0.13762889,
         0.13746823, 0.13731706, 0.13716885, 0.13702401, 0.13688405,
         0.1367474 ]],
       [[0.16162506, 0.1597037 , 0.15786332, 0.15616067, 0.15458338,
         0.15307295, 0.15169439, 0.15036916, 0.14912912, 0.14795588,
         0.14683773, 0.14578936, 0.14480346, 0.14383543, 0.1429532 ,
         0.14209186, 0.14128021, 0.14049573, 0.13975724, 0.13904795,
         0.13836947, 0.13773818, 0.13711375, 0.13653459, 0.13595962,
         0.13542352, 0.13490303, 0.13439241, 0.13391533, 0.13343746,
         0.13299131, 0.13255724, 0.13213734, 0.13172793, 0.13133902,
         0.13095301, 0.1305863 , 0.13022417, 0.12987987, 0.12953891,
         0.1292118 , 0.12889314, 0.12858005, 0.12827771, 0.12798431,
         0.12769931, 0.12742049, 0.12715035, 0.12688139, 0.12662806,
         0.12637267],
        [0.16162506, 0.16141821, 0.16121752, 0.16102516, 0.16084091,
         0.16066314, 0.16049053, 0.16032283, 0.16016169, 0.16000721,
         0.1598583 , 0.15971586, 0.1595776 , 0.15944455, 0.15931565,
         0.15918984, 0.15906974, 0.15895448, 0.15884369, 0.15873447,
         0.1586296 , 0.15852792, 0.15843087, 0.1583344 , 0.1582425 ,
         0.15815098, 0.15806166, 0.1579771 , 0.15789548, 0.15781409,
         0.15773459, 0.15765722, 0.15758191, 0.15750884, 0.15743773,
         0.15736819, 0.15730118, 0.15723509, 0.15717085, 0.15710882,
         0.15704757, 0.15698749, 0.15692844, 0.15687106, 0.15681429,
         0.15675933, 0.15670576, 0.15665457, 0.15660215, 0.15655154,
         0.15650347]]])
    '''
    # Node sampling with enumeration of all data sets
    Q = np.array([[0.4, 0.6], [0.8, 0.2], [0.5, 0.5]])
    scDict.update({'transMat': Q})
    testBudget = 20
    interval = 4
    Umat = np.zeros((numTN, int(testBudget / interval) + 1))
    for currTN in range(numTN):
        for currBudget in range(0, int(testBudget / interval) + 1):
            design = np.zeros(numTN)
            design[currTN] = 1.
            lossveclist = getDesignUtility(priordatadict=scDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                                           numtests=currBudget * interval, omeganum=1, type=['path'],
                                           method='weightsNodeEnumerate', printUpdate=True, numNdraws=0, numYdraws=1)
            Umat[currTN][currBudget] = lossveclist[0]
            print(lossveclist[0])
        print('TN ' + str(currTN) + ' done')

    '''
        testBudget=20, Q=[0.4,0.6] (x3)
        Umat = np.array([[0.16162506, 0.16065018, 0.15968995, 0.15874968, 0.15783654,
            0.15694523, 0.15607927, 0.15523647, 0.15441761, 0.1536191 ,
            0.15284541, 0.15208802, 0.15135014, 0.15062948, 0.14992843,
            0.14924556, 0.14857741, 0.14792525, 0.14728864, 0.14666678,
            0.14605892],
           [0.16162506, 0.15995383, 0.15837397, 0.15688394, 0.15547023,
            0.15411859, 0.15282618, 0.1515936 , 0.15041543, 0.14928394,
            0.14820224, 0.14716349, 0.14616401, 0.14519929, 0.14427106,
            0.14337608, 0.14251185, 0.14167658, 0.1408657 , 0.14008064,
            0.13932017],
           [0.16162506, 0.1607324 , 0.15985349, 0.15899326, 0.15815668,
            0.15733875, 0.15654157, 0.15576492, 0.15500941, 0.15427098,
            0.1535503 , 0.15284653, 0.15216023, 0.1514901 , 0.1508355 ,
            0.15019515, 0.1495701 , 0.14895828, 0.14836051, 0.14777539,
            0.14720368]])
        testBudget=20, Q=np.array([[0.4,0.6],[0.8,0.2],[0.5,0.5]]), numpriordraws=20k
        UmatEnum20k = np.array([[0.16162506, 0.16065018, 0.15968995, 0.15874968, 0.15783654,
            0.15694523, 0.15607927, 0.15523647, 0.15441761, 0.1536191 ,
            0.15284541, 0.15208802, 0.15135014, 0.15062948, 0.14992843,
            0.14924556, 0.14857741, 0.14792525, 0.14728864, 0.14666678,
            0.14605892],
           [0.16162506, 0.16025073, 0.15889991, 0.15763136, 0.156398  ,
            0.1552082 , 0.15407315, 0.15297515, 0.15192187, 0.15090448,
            0.14992187, 0.14897037, 0.1480503 , 0.14716051, 0.14629901,
            0.14546534, 0.14465472, 0.14386482, 0.14310251, 0.14235804,
            0.14163317],
           [0.16162506, 0.16056095, 0.15951714, 0.15850189, 0.15752146,
            0.15656922, 0.15564662, 0.15475266, 0.15388667, 0.15304442,
            0.15222653, 0.15143127, 0.15065886, 0.14990763, 0.14917635,
            0.14846403, 0.14777147, 0.14709593, 0.14643843, 0.1457979 ,
            0.145174  ]])
        testBudget=20, Q=np.array([[0.4,0.6],[0.8,0.2],[0.5,0.5]]), numpriordraws=200k
        UmatEnum = np.array([[0.16116998945702088, 0.15739380829733182, 0.1540141459785618, 0.150977124364397, 
                            0.148236000492868, 0.1457481020676326],
                            [0.16116998945702088, 0.15602379027217192, 0.15162167472484903, 0.14779637857008074, 
                            0.14443163041004733,  0.14143516830183858],
                            [0.16116998945702088, 0.15711369257508015, 0.1535446063329205, 0., 0., 0.]])
        '''
    # Node sampling with data draws
    testBudget = 20
    interval = 4
    M = 1000
    numpriorstouse = int(numdraws/M)
    Umat = np.zeros((numTN, int(testBudget / interval) + 1))
    for currTN in range(numTN):
        for currBudget in range(0, int(testBudget / interval) + 1):
            design = np.zeros(numTN)
            design[currTN] = 1.
            dictToUse = scDict.copy()
            randdrawinds = choice(range(len(dictToUse['postSamples'])), size=numpriorstouse, replace=False)
            dictToUse.update({'postSamples': scDict['postSamples'][randdrawinds]})
            lossveclist = getDesignUtility(priordatadict=dictToUse, lossdict=lossDict.copy(), designlist=[design],
                                           numtests=currBudget * interval, omeganum=1, type=['path'],
                                           method='weightsNodeDraw', printUpdate=False, numNdraws=M, numYdraws=1)
            Umat[currTN][currBudget] = lossveclist[0][0]
            print('TN ' + str(currTN) + ', budget of '+ str(currBudget) + ' done')
    ''' 
    M=100, |\Gamma|=20k, Q=array([[0.4, 0.6],[0.8, 0.2],[0.5, 0.5]])
    UmatDraw = np.array([[0.16162506, 0.15987586, 0.15942751, 0.1588006 , 0.15856284,
        0.15629223, 0.15679014, 0.15807963, 0.15711662, 0.15568468,
        0.15279675, 0.15204552, 0.15122019, 0.14879258, 0.15136532,
        0.15030547, 0.14834178, 0.14796502, 0.14506939, 0.14553268,
        0.14582388],
       [0.16162506, 0.15951043, 0.15817392, 0.15874987, 0.15731457,
        0.15354876, 0.15168321, 0.15252185, 0.15192769, 0.14808545,
        0.15136844, 0.14982353, 0.15179897, 0.14532291, 0.14672466,
        0.14782781, 0.1425962 , 0.14233633, 0.14521699, 0.144314  ,
        0.14282381],
       [0.16162506, 0.16118221, 0.16055612, 0.15955066, 0.15494602,
        0.15413437, 0.15508566, 0.15616625, 0.1521446 , 0.1513354 ,
        0.15175568, 0.15402198, 0.14711149, 0.15130659, 0.14690094,
        0.14820216, 0.14612487, 0.14561699, 0.14410426, 0.14408411,
        0.14616155]])
    M=1000, |\Gamma|=20k, Q=array([[0.4, 0.6],[0.8, 0.2],[0.5, 0.5]]), interval=4
    UmatDraw = np.array([[0.16162506, 0.1582018 , 0.15465051, 0.15090967, 0.1487231 , 0.14502877],
       [0.16162506, 0.15634112, 0.15124967, 0.14851221, 0.14411071, 0.14276236],
       [0.16162506, 0.15745589, 0.15423467, 0.1524026 , 0.14720401, 0.14549113]])
    M=1000, |\Gamma|=200, Q=array([[0.4, 0.6],[0.8, 0.2],[0.5, 0.5]]), interval=4
    UmatDraw = np.array([[0.16432671, 0.16880861, 0.13605453, 0.14376709, 0.14082714, 0.1408841 ],
       [0.15960455, 0.15062354, 0.15766825, 0.15001483, 0.14395483, 0.13094868],
       [0.16306185, 0.16753043, 0.15574705, 0.15247418, 0.13995842, 0.14017979]])
    *****************
    *****************
    M=1000,
    UmatDraw1000 = np.array([[0.1580026 , 0.14686019, 0.15417703, 0.15009638, 0.13873486, 0.14286519],
       [0.15904135, 0.15393042, 0.14945228, 0.15747346, 0.14444115, 0.1416594 ],
       [0.18437353, 0.16153838, 0.15942462, 0.14685183, 0.15066542, 0.1392786 ]])
    M=200,
    UmatDraw200 = np.array([[0.16187053, 0.16202998, 0.15307882, 0.14656344, 0.14470785, 0.14229757],
       [0.15946326, 0.15528552, 0.14870259, 0.14652343, 0.14430842, 0.14228619],
       [0.15713865, 0.15365344, 0.15504863, 0.15049905, 0.14981157, 0.14042644]])
    M=100, |\Gamma|=200k/M, interval=4
    UmatDraw100 = np.array([[0.1620847 , 0.15333765, 0.15352896, 0.14931659, 0.14779341, 0.14838865],
       [0.15865288, 0.15612394, 0.15138619, 0.14368911, 0.14689854, 0.14641033],
       [0.16249019, 0.15737397, 0.15846291, 0.1454049 , 0.14652485, 0.14536325]])
    M=50,
    UmatDraw50 = np.array([[0.16215145, 0.15838087, 0.15401391, 0.14766459, 0.14864274, 0.14496581],
       [0.16214603, 0.15532278, 0.15265559, 0.1480391 , 0.14082181, 0.1391966 ],
       [0.16369567, 0.15692361, 0.15380053, 0.1483534 , 0.14735999, 0.14789328]])
    M=5,  |\Gamma|=200k/M, interval=4
    UmatDraw5 = np.array([[0.16233219, 0.15319598, 0.14435542, 0.15578702, 0.18034174, 0.13988446],
       [0.16143973, 0.1548624 , 0.16723731, 0.13618021, 0.14357954, 0.13104493],
       [0.16145732, 0.15915816, 0.1522039 , 0.1538992 , 0.13732876, 0.15278485]])
    M=1
    UmatDraw1 = np.array([[0.16116999, 0.14766652, 0.13297513, 0.15418132, 0.14472153, 0.14688544],
       [0.16116999, 0.15242834, 0.15119067, 0.14624652, 0.1381395 , 0.12980331],
       [0.16116999, 0.17234957, 0.18757387, 0.13158897, 0.14326916, 0.14126285]])
    '''
    M=1000
    x1 = range(0, testBudget + 1, interval)
    x2 = range(0, testBudget + 1, 1)
    colors=['blue','red','green']
    for tnind in range(numTN):
        plt.plot(x1, UmatDraw1000[tnind], '--',color=colors[tnind], label='TN ' + str(tnind + 1))
        plt.plot(x2, UmatEnum20k[tnind], '-', color=colors[tnind], label='TN ' + str(tnind + 1))
    plt.legend()
    plt.ylim([0.13, 0.17])
    plt.xlabel('Number of tests')
    plt.ylabel('Loss')
    plt.title('Comparison with data enumeration\nM='+str(M))
    plt.show()


    x1 = range(0, testBudget + 1, interval)
    x2 = range(0, testBudget + 1, 1)
    colors = ['blue', 'red', 'green']
    for tnind in range(numTN):
        plt.plot(x2, UmatEnum20k[tnind], '--', color=colors[tnind], label='TN ' + str(tnind + 1))
        plt.plot(x1, UmatEnum[tnind], '-', color=colors[tnind], label='TN ' + str(tnind + 1))
    plt.legend()
    plt.ylim([0.13, 0.17])
    plt.xlabel('Number of tests')
    plt.ylabel('Loss')
    plt.title('Comparing data enumeration for $|\Gamma|\in[20k,200k]$')
    plt.show()

    return

def allocationCaseStudy():
    '''Allocation using case study data'''
    # CITIES-MANUFACTURERS
    rd2_N = np.array([[1., 0., 2., 0., 0., 0., 0., 1., 0., 1., 0., 0., 0.],
       [0., 1., 3., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0.],
       [1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0.],
       [0., 0., 3., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.],
       [0., 1., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 1.],
       [0., 0., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [0., 2., 3., 0., 0., 0., 1., 0., 0., 1., 1., 0., 0.],
       [0., 2., 3., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 2., 2., 0., 0., 1., 0., 0., 2., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [1., 0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [0., 0., 4., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 2., 0., 0., 0.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 3., 0., 0., 1.],
       [0., 3., 4., 1., 1., 0., 0., 4., 0., 5., 0., 0., 2.],
       [0., 0., 0., 1., 0., 0., 0., 1., 0., 0., 0., 0., 0.],
       [0., 4., 0., 1., 0., 0., 0., 0., 0., 4., 0., 0., 0.],
       [0., 2., 4., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 1., 1., 0., 0., 5., 1., 2., 0., 0., 3.],
       [0., 1., 2., 0., 0., 0., 0., 0., 0., 2., 0., 0., 0.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 1., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [1., 2., 7., 2., 1., 0., 0., 0., 0., 3., 0., 1., 0.],
       [1., 0., 3., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
       [0., 0., 6., 0., 0., 0., 1., 1., 6., 1., 0., 0., 1.],
       [0., 0., 3., 0., 0., 0., 0., 0., 0., 2., 0., 0., 0.],
       [0., 1., 0., 0., 0., 1., 0., 2., 0., 1., 0., 0., 1.],
       [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]])
    rd2_Y = np.array([[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 3., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 3., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1.],
           [0., 0., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 2., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 2., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
           [0., 0., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.],
           [0., 0., 3., 1., 1., 0., 0., 2., 0., 0., 0., 0., 2.],
           [0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 1., 0., 0., 0., 1., 0., 0., 0., 3.],
           [0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 2., 2., 1., 0., 0., 0., 0., 0., 0., 1., 0.],
           [0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 3., 0., 0., 0., 1., 0., 0., 0., 0., 0., 1.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
           [0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 1.],
           [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]])

    (numTN, numSN) = rd2_N.shape
    s, r = 1., 1.
    CSdict2 = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r,
                                       numSamples=0, dataType='Tracked', randSeed=2)
    CSdict2['diagSens'], CSdict2['diagSpec'] = s, r
    CSdict2 = util.GetVectorForms(CSdict2)
    CSdict2['N'], CSdict2['Y'] = rd2_N, rd2_Y
    CSdict2['prior'] = methods.prior_normal()
    CSdict2['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    CSdict2['importerNum'], CSdict2['outletNum'] = numSN, numTN
    # Generate posterior draws
    numdraws = 50000  # Evaluate choice here
    CSdict2['numPostSamples'] = numdraws
    CSdict2 = methods.GeneratePostSamples(CSdict2)

    # Create a normalized sourcing matrix with element minimums
    elemMin = 0.01
    normConstant = elemMin/(1-numSN/100) # Only works for numSN<100
    sourceMatNorm = CSdict2['N']/(np.reshape(np.tile(np.sum(CSdict2['N'],axis=1),numSN),(numSN,numTN)).T)
    newSourceMat = sourceMatNorm+normConstant
    newSourceMat = newSourceMat/(np.reshape(np.tile(np.sum(newSourceMat,axis=1),numSN),(numSN,numTN)).T)
    CSdict2['transMat'] = newSourceMat

    # Loss specification
    underWt, t = 1., 0.2
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic', 'threshold': t}
    marketvec = np.ones(numTN + numSN)
    lossDict = {'scoreDict': scoredict, 'riskDict': riskdict, 'marketVec': marketvec}

    # Utility calculation specification
    numbayesdraws, numdrawsfordata = 3000, 3500
    utilDict = {'method': 'weightsNodeDraw3'}
    utilDict.update({'numdrawsfordata': numdrawsfordata})
    utilDict.update({'numdrawsforbayes': numbayesdraws})

    # Set limits of data collection and intervals for calculation
    testMax, testInt = 10, 5
    numdrawstouse = int(11000000 / numbayesdraws)

    # Withdraw a subset of MCMC prior draws
    dictTemp = CSdict2.copy()
    dictTemp.update({'postSamples': CSdict2['postSamples'][choice(np.arange(numdraws), size=numdrawstouse, replace=False)], 'numPostSamples': numdrawstouse})

    # Generate a marginal utility matrix for each parameter adjustment
    estWts = [0.05,0.1,1,10,20]
    for currEstWt in estWts:
        tempLossDict = lossDict.copy()
        tempLossDict['scoreDict'].update({'underEstWt':currEstWt})
        currMargUtilMat = GetMargUtilAtNodes(dictTemp, testMax, testInt, lossDict, utilDict, printUpdate=True)






    ######################################################################
    ######################################################################
    ######################################################################
    ######################################################################

    # PROVINCES-MANUFACTURERS
    rd3_N = np.array([[ 1.,  1., 10.,  1.,  3.,  0.,  1.,  6.,  7.,  5.,  0.,  0.,  4.],
       [ 1.,  1.,  4.,  2.,  0.,  1.,  1.,  2.,  0.,  4.,  0.,  0.,  1.],
       [ 3., 17., 31.,  4.,  2.,  0.,  1.,  6.,  0., 23.,  1.,  2.,  5.],
       [ 1.,  1., 15.,  2.,  0.,  0.,  0.,  1.,  0.,  6.,  0.,  0.,  0.]])
    rd3_Y = np.array([[ 0.,  0.,  7.,  0.,  3.,  0.,  1.,  0.,  1.,  0.,  0.,  0.,  4.],
       [ 0.,  0.,  2.,  2.,  0.,  1.,  1.,  0.,  0.,  1.,  0.,  0.,  1.],
       [ 0.,  0., 15.,  3.,  2.,  0.,  0.,  2.,  0.,  1.,  1.,  2.,  5.],
       [ 0.,  0.,  5.,  2.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.]])

    # Some summaries
    #TNtesttotals = np.sum(rd3_N, axis=1)
    #TNsfptotals = np.sum(rd3_Y, axis=1)
    #TNrates = np.divide(TNsfptotals,TNtesttotals)

    (numTN, numSN) = rd3_N.shape
    s, r = 1., 1.
    CSdict3 = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r,
                                        numSamples=0, dataType='Tracked', randSeed=2)
    CSdict3['diagSens'], CSdict3['diagSpec'] = s, r
    CSdict3 = util.GetVectorForms(CSdict3)
    CSdict3['N'], CSdict3['Y'] = rd3_N, rd3_Y
    CSdict3['prior'] = methods.prior_normal()
    CSdict3['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    CSdict3['importerNum'], CSdict3['outletNum'] = numSN, numTN
    # Generate posterior draws
    numdraws = 50000  # Evaluate choice here
    CSdict3['numPostSamples'] = numdraws
    CSdict3 = methods.GeneratePostSamples(CSdict3)

    # Create a normalized sourcing matrix with element minimums
    elemMin = 0.01
    normConstant = elemMin / (1 - numSN / 100)  # Only works for numSN<100
    sourceMatNorm = CSdict3['N'] / (np.reshape(np.tile(np.sum(CSdict3['N'], axis=1), numSN), (numSN, numTN)).T)
    newSourceMat = sourceMatNorm + normConstant
    newSourceMat = newSourceMat / (np.reshape(np.tile(np.sum(newSourceMat, axis=1), numSN), (numSN, numTN)).T)
    CSdict3['transMat'] = newSourceMat

    # Loss specification
    underWt, t = 1., 0.2
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic', 'threshold': t}
    marketvec = np.ones(numTN + numSN)
    lossDict = {'scoreDict': scoredict, 'riskDict': riskdict, 'marketVec': marketvec}

    # Utility calculation specification
    numbayesdraws, numdrawsfordata = 3000, 3100
    utilDict = {'method': 'weightsNodeDraw3'}
    utilDict.update({'numdrawsfordata': numdrawsfordata})
    utilDict.update({'numdrawsforbayes': numbayesdraws})

    # Set limits of data collection and intervals for calculation
    testMax, testInt = 200, 10
    numdrawstouse = int(10000000 / numbayesdraws)

    # Withdraw a subset of MCMC prior draws
    dictTemp = CSdict3.copy()
    dictTemp.update({'postSamples': CSdict3['postSamples'][choice(np.arange(numdraws), size=numdrawstouse, replace=False)],
         'numPostSamples': numdrawstouse})

    # Generate a marginal utility matrix for each parameter adjustment
    utilList = []
    estWts = [0.05, 0.1, 1, 10, 20]

    for currEstWt in estWts:
        tempLossDict = lossDict.copy()
        tempLossDict['scoreDict'].update({'underEstWt': currEstWt})
        currMargUtilMat = GetMargUtilAtNodes(dictTemp, testMax, testInt, tempLossDict, utilDict, printUpdate=True)
        print('Marginal utilities for estimation error weight of '+str(currEstWt)+':')
        print(repr(currMargUtilMat))
        utilList.append(currMargUtilMat)

    ''' GENERATED 29-NOV
    estWts=0.05
    currMargUtilMat05_1 = np.array([[0.   ,      0.00576185, 0.01100239, 0.01385138, 0.01612649, 0.01832296,
  0.02134625, 0.02360469, 0.02591977, 0.02759011, 0.02943672, 0.03072441,
  0.03229022, 0.03412024, 0.03612216, 0.03716075, 0.03848029, 0.04080149,
  0.04264224, 0.04329342, 0.04515046, 0.04712259, 0.04829025, 0.05098432,
  0.05064744, 0.05347186, 0.05504937, 0.05716478, 0.05754498, 0.0583737,
  0.06097388, 0.06377641, 0.06392104, 0.064814,   0.06746955, 0.06739904,
  0.07007328, 0.07115842, 0.07289314, 0.07371235, 0.07394673],
 [0.,         0.00867514, 0.01466471, 0.01837373, 0.02193253, 0.02513119,
  0.02804945, 0.03027397, 0.03241935, 0.03483767, 0.03777431, 0.0385565,
  0.04108989, 0.04302853, 0.04426304, 0.04635703, 0.04745852, 0.04840028,
  0.05069803, 0.05201403, 0.05311701, 0.05528665, 0.05565639, 0.05811713,
  0.0580791,  0.05983895, 0.06071548, 0.06337236, 0.06378854, 0.06568773,
  0.06636505, 0.06757199, 0.06868632, 0.06987256, 0.07178076, 0.07319505,
  0.07500517, 0.07607656, 0.0778317,  0.07855393, 0.07961158],
 [0.,         0.00520452, 0.00971953, 0.01364587, 0.0167489,  0.01887599,
  0.02074921, 0.02279577, 0.02486231, 0.027188,   0.02958499, 0.03168798,
  0.03248992, 0.0349256,  0.03732637, 0.03856075, 0.03948103, 0.04250011,
  0.04402039, 0.0454288,  0.04678349, 0.04987723, 0.04908477, 0.0521021,
  0.05244709, 0.05392834, 0.05454159, 0.05818366, 0.05834053, 0.05826901,
  0.05985889, 0.06122789, 0.06331188, 0.06395946, 0.06604659, 0.06793778,
  0.06814556, 0.07063863, 0.07181205, 0.07318194, 0.07335385],
 [0.,         0.00470894, 0.00823224, 0.01118718, 0.01329261, 0.01528969,
  0.0172078,  0.01967189, 0.02138792, 0.02241452, 0.02384324, 0.02539123,
  0.02694012, 0.02759345, 0.02906612, 0.02999236, 0.03186161, 0.03198067,
  0.03385147, 0.03470381, 0.03668821, 0.03669794, 0.03760487, 0.03879746,
  0.04012802, 0.04063279, 0.04203949, 0.04217946, 0.04527283, 0.04534564,
  0.04689576, 0.04743839, 0.04813029, 0.04881674, 0.04941262, 0.05228234,
  0.05206925, 0.05371661, 0.05391299, 0.05634011, 0.05598143]])
    currMargUtilMat05_2 = np.array([[0.        , 0.00245564, 0.00558357, 0.00907409, 0.01119174,
        0.01394355, 0.01581534, 0.01847186, 0.01948496, 0.02204755,
        0.02469122, 0.02625219, 0.02816501, 0.02999371, 0.03178436,
        0.03413398, 0.0353829 , 0.03738401, 0.03846131, 0.04046442,
        0.04308452, 0.0428609 , 0.0446552 , 0.04611647, 0.04874875,
        0.05003766, 0.05202896, 0.05232518, 0.05502081, 0.05727677,
        0.05838703, 0.0593761 , 0.06217044, 0.06353622, 0.0647599 ,
        0.06650144, 0.06705036, 0.06861743, 0.07159573, 0.0724062 ,
        0.07331201],
       [0.        , 0.00413962, 0.00891626, 0.01390467, 0.01837365,
        0.02160164, 0.02559941, 0.02726844, 0.03026535, 0.03239124,
        0.03505925, 0.0380851 , 0.03841253, 0.04033222, 0.04299198,
        0.04405612, 0.04548809, 0.04844164, 0.04964644, 0.05112731,
        0.05236056, 0.05433155, 0.05569635, 0.05649603, 0.05927539,
        0.06006903, 0.06160137, 0.06279733, 0.0634611 , 0.06524218,
        0.06671017, 0.06766222, 0.06866863, 0.07071224, 0.07289899,
        0.07260729, 0.07448631, 0.07553354, 0.07848129, 0.07784982,
        0.08086039],
       [0.        , 0.00255993, 0.00511694, 0.00788227, 0.01038603,
        0.01236924, 0.01538368, 0.01807234, 0.01975158, 0.02175123,
        0.02486728, 0.02641199, 0.02942514, 0.03101106, 0.03336011,
        0.03389188, 0.03691459, 0.03811857, 0.04065215, 0.04173541,
        0.04277303, 0.04349438, 0.045682  , 0.04919123, 0.04987797,
        0.05140058, 0.05265511, 0.05402883, 0.05504515, 0.05798159,
        0.05740894, 0.05945211, 0.06114668, 0.06252416, 0.06468694,
        0.06752399, 0.06711773, 0.06923216, 0.06986274, 0.06945356,
        0.07207439],
       [0.        , 0.00149031, 0.00389336, 0.00631881, 0.00825956,
        0.00993069, 0.01184708, 0.01362841, 0.01568003, 0.01626178,
        0.01873783, 0.02039889, 0.0226695 , 0.02278714, 0.02463448,
        0.02633133, 0.02729284, 0.02831201, 0.03038085, 0.03081733,
        0.03307665, 0.03438391, 0.03510885, 0.03628141, 0.03607699,
        0.03770243, 0.04002321, 0.03958502, 0.04177417, 0.04232142,
        0.04386058, 0.04477777, 0.0467264 , 0.04695118, 0.04900154,
        0.04869328, 0.04938808, 0.05143445, 0.05252614, 0.05373184,
        0.05447112]])
    currMargUtilMat05_3 = np.array([[0.        , 0.00601169, 0.0108309 , 0.01355915, 0.01673024,
        0.01928076, 0.02164499, 0.02392497, 0.02596712, 0.02832058,
        0.02947884, 0.03180665, 0.03320108, 0.03613551, 0.03770515,
        0.03856799, 0.0410028 , 0.04214557, 0.04334369, 0.04453244,
        0.04635301, 0.04812485, 0.04907387, 0.05127222, 0.05140429,
        0.05453983, 0.05517881, 0.05757177, 0.0591679 , 0.06030551,
        0.06226179, 0.06375696, 0.06392201, 0.06606418, 0.06753301,
        0.06922053, 0.07083268, 0.07117967, 0.07485609, 0.07505168,
        0.07630949],
       [0.        , 0.00917243, 0.0146688 , 0.01886884, 0.0227943 ,
        0.02620967, 0.02894632, 0.03228571, 0.0341945 , 0.0374255 ,
        0.03849882, 0.04005418, 0.04330325, 0.04413023, 0.04517914,
        0.04821411, 0.0487302 , 0.05098418, 0.05202669, 0.05463323,
        0.05537767, 0.05724306, 0.05842422, 0.05977964, 0.06181523,
        0.0625304 , 0.06424249, 0.06502145, 0.06755836, 0.06866985,
        0.06967059, 0.07034459, 0.07093824, 0.07296039, 0.07438248,
        0.07651179, 0.07680317, 0.07901239, 0.07942372, 0.08045284,
        0.08225545],
       [0.        , 0.00566112, 0.00969647, 0.01332372, 0.01625888,
        0.01871384, 0.02088149, 0.02371345, 0.02548017, 0.02831037,
        0.02950397, 0.03183995, 0.0342302 , 0.03563289, 0.03816063,
        0.04037406, 0.04093243, 0.04309172, 0.04430666, 0.04534428,
        0.04627744, 0.04936543, 0.05053222, 0.05148008, 0.05327159,
        0.05401187, 0.05522744, 0.05754494, 0.0589372 , 0.06006307,
        0.06055305, 0.06202746, 0.06466132, 0.06602554, 0.06615118,
        0.0684922 , 0.0681559 , 0.07017547, 0.07212271, 0.07292587,
        0.07518005],
       [0.        , 0.0049045 , 0.00860365, 0.01134197, 0.01354706,
        0.01566037, 0.0179595 , 0.01922929, 0.02104824, 0.02279682,
        0.02442528, 0.02622876, 0.02661489, 0.0289812 , 0.03012896,
        0.03149374, 0.03263529, 0.03394694, 0.03440262, 0.03632841,
        0.03769419, 0.03841844, 0.03973692, 0.04130814, 0.04197544,
        0.04299327, 0.04478917, 0.04482476, 0.04640051, 0.04684873,
        0.04706124, 0.0499702 , 0.04965964, 0.05174459, 0.05136836,
        0.05342019, 0.05529931, 0.05441994, 0.05502264, 0.0564276 ,
        0.0567394 ]])
    
    estWts=0.1
    currMargUtilMat01_1 = np.array([[0.     ,    0.00538566, 0.00982736, 0.01271866, 0.01614273, 0.0187065,
  0.02148081, 0.02328427, 0.02569313, 0.02816464, 0.02906434, 0.03294419,
  0.03427416, 0.03554839, 0.03802604, 0.0402396,  0.04201208, 0.04370211,
  0.04604508, 0.04701197, 0.04917401, 0.05128647, 0.05331882, 0.05470299,
  0.05646121, 0.05714694, 0.05958611, 0.06187232, 0.06301872, 0.0658529,
  0.06707725, 0.0679311,  0.07006985, 0.07112333, 0.07314746, 0.07463745,
  0.07640722, 0.07792824, 0.07936801, 0.08179071, 0.08359132],
 [0.,         0.00863485, 0.01513486, 0.02022767, 0.02380901, 0.02741131,
  0.03054472, 0.03335944, 0.0361582,  0.0383826,  0.0406964,  0.04351223,
  0.04645155, 0.04752101, 0.04992661, 0.05132612, 0.05318971, 0.05547612,
  0.0578198,  0.05860518, 0.05986239, 0.06267311, 0.06373646, 0.06504439,
  0.06664858, 0.06771715, 0.06903722, 0.07052199, 0.07237003, 0.07344644,
  0.07536122, 0.07728796, 0.07783868, 0.07957023, 0.08149631, 0.08212044,
  0.08420343, 0.08570887, 0.08715367, 0.08829579, 0.09049189],
 [0.,         0.00601553, 0.01016055, 0.0136719,  0.01637864, 0.01871844,
  0.02219235, 0.02427686, 0.02598324, 0.02929276, 0.03095159, 0.03322915,
  0.03583145, 0.03738846, 0.03813133, 0.04155813, 0.04303517, 0.04483378,
  0.04628292, 0.04860435, 0.0497104,  0.0513058,  0.0536671,  0.05443606,
  0.05713999, 0.05860847, 0.05964202, 0.06127876, 0.06297694, 0.06418078,
  0.06574096, 0.06711709, 0.06854069, 0.07014306, 0.07239817, 0.07436774,
  0.0754217,  0.07728019, 0.07646796, 0.07972664, 0.07962869],
 [0.,         0.0057881,  0.00910538, 0.01166496, 0.01406586, 0.01629329,
  0.01788416, 0.01933275, 0.02142486, 0.02387824, 0.02494705, 0.02649628,
  0.02816281, 0.03051678, 0.03056084, 0.03163437, 0.03419674, 0.03481983,
  0.03657959, 0.03688013, 0.03884099, 0.0393707,  0.04172191, 0.04238681,
  0.04320731, 0.04586739, 0.04547022, 0.0469667,  0.0490304,  0.04962204,
  0.04980033, 0.05208073, 0.05129628, 0.05450986, 0.05484775, 0.05543261,
  0.05654688, 0.05867876, 0.05898731, 0.06054159, 0.06113953]])
    currMargUtilMat01_2 = np.array([[0.        , 0.0065222 , 0.01137471, 0.01484503, 0.01761288,
        0.02036377, 0.02220635, 0.02446192, 0.02721195, 0.02954825,
        0.03149108, 0.032154  , 0.03470433, 0.0366802 , 0.03863643,
        0.04003864, 0.04246135, 0.04364091, 0.04549218, 0.04713341,
        0.04939933, 0.04987681, 0.05330581, 0.05321154, 0.0539126 ,
        0.05638364, 0.05863946, 0.0615775 , 0.06301087, 0.06366544,
        0.06606231, 0.06714088, 0.06861267, 0.07115363, 0.07303942,
        0.07313891, 0.07592794, 0.07827541, 0.07946907, 0.07896949,
        0.08232298],
       [0.        , 0.00898633, 0.01558378, 0.01988171, 0.02295113,
        0.02744936, 0.03046333, 0.03235001, 0.03539376, 0.03792729,
        0.03993073, 0.04280441, 0.04352959, 0.04602244, 0.04733458,
        0.04964132, 0.05182275, 0.05295737, 0.05480207, 0.05685569,
        0.05890111, 0.05967429, 0.06196223, 0.06254885, 0.06355567,
        0.06582102, 0.06683844, 0.06783278, 0.0706158 , 0.07112344,
        0.07274744, 0.0753375 , 0.07739431, 0.07814231, 0.07870748,
        0.0792605 , 0.08192149, 0.08253234, 0.08498746, 0.08618384,
        0.08806723],
       [0.        , 0.00596846, 0.00999478, 0.01397644, 0.01673567,
        0.02003198, 0.02225088, 0.02404734, 0.02628639, 0.02910929,
        0.03076184, 0.03317297, 0.03502914, 0.0374572 , 0.03912948,
        0.04062396, 0.04190406, 0.0446836 , 0.04599243, 0.0476463 ,
        0.04937513, 0.05080888, 0.05223569, 0.05554758, 0.05567282,
        0.05739659, 0.05779712, 0.06009498, 0.06188951, 0.06413738,
        0.0640721 , 0.06665092, 0.06847373, 0.07024105, 0.07111303,
        0.07233735, 0.07363092, 0.07529584, 0.07548786, 0.07812124,
        0.07862072],
       [0.        , 0.00510181, 0.00890099, 0.01182565, 0.0138017 ,
        0.01662868, 0.01825042, 0.02015699, 0.02163367, 0.02348325,
        0.0254176 , 0.02668862, 0.02890479, 0.02922331, 0.03107631,
        0.03231241, 0.03339706, 0.03443223, 0.03608551, 0.03743701,
        0.03923804, 0.04027495, 0.04142967, 0.0428522 , 0.0435799 ,
        0.04472833, 0.04607875, 0.04656237, 0.04797535, 0.0483338 ,
        0.04919351, 0.05129355, 0.05303324, 0.05317438, 0.0544222 ,
        0.05572733, 0.05647557, 0.05773062, 0.05989496, 0.05984892,
        0.06162219]])
    currMargUtilMat01_3 = np.array([[0.        , 0.00639391, 0.01136505, 0.01489401, 0.01762907,
        0.02029276, 0.02183615, 0.02526364, 0.02678703, 0.02862861,
        0.03135807, 0.03182461, 0.03458404, 0.03655475, 0.03865938,
        0.03928285, 0.04249975, 0.04258686, 0.04572023, 0.04736341,
        0.04881685, 0.05148298, 0.05275808, 0.05374062, 0.0552097 ,
        0.05814155, 0.05931001, 0.06103467, 0.06299643, 0.06498305,
        0.06585189, 0.06872513, 0.06921488, 0.07126189, 0.07270524,
        0.07322759, 0.07626589, 0.07770516, 0.08122895, 0.08049673,
        0.08215578],
       [0.        , 0.0090664 , 0.01493884, 0.01889667, 0.02373642,
        0.02667673, 0.03017273, 0.03284067, 0.03493844, 0.03780881,
        0.04052884, 0.04214605, 0.04321282, 0.0462698 , 0.04781833,
        0.05046425, 0.05175365, 0.05383571, 0.05557292, 0.05637454,
        0.05859584, 0.06012309, 0.06183396, 0.06285485, 0.06363613,
        0.06626397, 0.0670798 , 0.06967165, 0.07025195, 0.07236018,
        0.07244557, 0.07489036, 0.0760199 , 0.07750106, 0.07964101,
        0.0801884 , 0.08272493, 0.08368749, 0.08420952, 0.08676592,
        0.08812164],
       [0.        , 0.00568012, 0.00970543, 0.01416993, 0.01677766,
        0.01992959, 0.02254338, 0.02465527, 0.02656419, 0.02869913,
        0.03190436, 0.032452  , 0.03502178, 0.03682705, 0.0395962 ,
        0.04039458, 0.04262026, 0.04428826, 0.04743055, 0.04740884,
        0.04955442, 0.05183729, 0.05355826, 0.05435859, 0.0554204 ,
        0.05665143, 0.06008015, 0.06016685, 0.06153244, 0.06463863,
        0.06516169, 0.06675482, 0.06894615, 0.07006292, 0.07148376,
        0.07233864, 0.07415689, 0.07460429, 0.07769104, 0.07900862,
        0.08089908],
       [0.        , 0.00519972, 0.00911248, 0.01236546, 0.01501125,
        0.01609382, 0.01926756, 0.02046771, 0.02208726, 0.02327597,
        0.02515903, 0.02656307, 0.0284272 , 0.02907843, 0.03130281,
        0.03251073, 0.03329943, 0.03487734, 0.03619566, 0.03759394,
        0.03831557, 0.04080038, 0.04065815, 0.04294581, 0.04368997,
        0.04411576, 0.04563693, 0.04670706, 0.04815234, 0.04939909,
        0.04992203, 0.05178766, 0.05156343, 0.053983  , 0.05377245,
        0.05615015, 0.05679538, 0.05771323, 0.05889431, 0.06024397,
        0.0614273 ]])
  
    estWts=1.
    currMargUtilMat1_1 = np.array([[0. ,        0.00635309, 0.01146727, 0.01750851, 0.02223688, 0.0282137,
  0.03494099, 0.04004731, 0.04571702, 0.05272282, 0.05670115, 0.06149046,
  0.06763882, 0.073116,   0.07820467, 0.08417925, 0.08910343, 0.09405799,
  0.10145665, 0.10537144, 0.11120786, 0.11765914, 0.1216731,  0.12984845,
  0.13368414, 0.14218504, 0.148491,   0.15389523, 0.16077149, 0.16724461,
  0.17346745, 0.18365262, 0.18566024, 0.1964114,  0.20238881, 0.20622004,
  0.2133487,  0.22120153, 0.22799116, 0.23549063, 0.24112954],
 [0.,         0.01321384, 0.02315576, 0.03433769, 0.04256696, 0.05158427,
  0.05957543, 0.06647775, 0.07304883, 0.07900064, 0.08581912, 0.0932892,
  0.0975549,  0.10512431, 0.10908753, 0.11470126, 0.12278915, 0.12681922,
  0.13214383, 0.13814203, 0.14306861, 0.15089448, 0.15679435, 0.16129176,
  0.166319 ,  0.17346666, 0.17427643, 0.18474331, 0.19077699, 0.19403518,
  0.20152902, 0.20494782, 0.20970081, 0.21709271, 0.22027235, 0.23185707,
  0.23629373, 0.24130755, 0.24353343, 0.25206908, 0.25686026],
 [0.,         0.00530104, 0.01081633, 0.01637484, 0.02333815, 0.02911523,
  0.03360277, 0.0386099,  0.04387652, 0.04822863, 0.0521965,  0.05716628,
  0.0629104,  0.06845392, 0.07224327, 0.07691966, 0.08176374, 0.08692575,
  0.09275832, 0.09848933, 0.09984012, 0.10648355, 0.11185741, 0.1160837,
  0.11984709, 0.12581725, 0.13055903, 0.13485863, 0.14124683, 0.1498825,
  0.15332067, 0.15684008, 0.16411105, 0.17052175, 0.17700783, 0.18003819,
  0.18126875, 0.19162763, 0.19928545, 0.20512469, 0.20841444],
 [0.,         0.00302252, 0.00734714, 0.01013261, 0.0146666,  0.01747262,
  0.02268771, 0.02624576, 0.02924355, 0.03374536, 0.03685241, 0.04122116,
  0.04418406, 0.04772623, 0.05179196, 0.0548281,  0.05769309, 0.06234947,
  0.065973,   0.06906326, 0.07343699, 0.07640472, 0.08136036, 0.08374869,
  0.08740832, 0.09105511, 0.09348022, 0.09824323, 0.10272419, 0.10776458,
  0.10787868, 0.11361069, 0.11539233, 0.12072527, 0.12462382, 0.1277629,
  0.13078516, 0.13417212, 0.13962726, 0.14012678, 0.14762272]])
  currMargUtilMat1_2 = np.array([[0.        , 0.00628547, 0.01224519, 0.01892325, 0.02298585,
        0.03068836, 0.03526634, 0.04051566, 0.04683534, 0.05325723,
        0.05814995, 0.06237449, 0.06768816, 0.07335556, 0.07671648,
        0.08505744, 0.08990468, 0.09588919, 0.10115374, 0.10728294,
        0.11409251, 0.11773522, 0.1215394 , 0.12911658, 0.1356937 ,
        0.14252935, 0.15090444, 0.1564295 , 0.16214278, 0.16660938,
        0.17481917, 0.1791744 , 0.1896179 , 0.19387575, 0.20251503,
        0.20571691, 0.21233169, 0.2182765 , 0.22922806, 0.23436865,
        0.24128462],
       [0.        , 0.01278458, 0.02479686, 0.03445356, 0.04348023,
        0.05267387, 0.06048168, 0.06646302, 0.0733429 , 0.08106216,
        0.08689198, 0.09250902, 0.09864776, 0.10590333, 0.11003601,
        0.11633969, 0.12086957, 0.1281072 , 0.13102931, 0.1394134 ,
        0.14425059, 0.14965795, 0.15429125, 0.15982296, 0.16529532,
        0.17028218, 0.17639187, 0.18377691, 0.18931632, 0.19344645,
        0.20078383, 0.20893021, 0.20955529, 0.21829119, 0.22323696,
        0.23049733, 0.23351218, 0.23518068, 0.24447384, 0.25250811,
        0.25501402],
       [0.        , 0.00496466, 0.01094796, 0.01708616, 0.02252134,
        0.02774728, 0.03199577, 0.03731148, 0.04293451, 0.04791964,
        0.05254615, 0.05823462, 0.0632428 , 0.06792452, 0.0707776 ,
        0.07796495, 0.08211493, 0.08496884, 0.08976887, 0.09693802,
        0.10108184, 0.10566416, 0.11060068, 0.11539193, 0.11958111,
        0.12681908, 0.13092613, 0.13615053, 0.14254359, 0.14627008,
        0.15317165, 0.15982641, 0.16280541, 0.17154119, 0.17327455,
        0.17804257, 0.18326213, 0.19018548, 0.19786711, 0.20411122,
        0.20993348],
       [0.        , 0.00300518, 0.0071574 , 0.01096526, 0.01376994,
        0.01884918, 0.02128031, 0.02506435, 0.03080106, 0.03426553,
        0.03762385, 0.04125489, 0.04519017, 0.04850447, 0.05171267,
        0.05487099, 0.05878384, 0.06204081, 0.06530922, 0.06950128,
        0.0750362 , 0.07666097, 0.08008817, 0.08314753, 0.08762079,
        0.08955698, 0.09497261, 0.09777727, 0.09985205, 0.1066171 ,
        0.10978083, 0.11304917, 0.11692891, 0.12008756, 0.12524046,
        0.12616514, 0.13074748, 0.13506195, 0.13936209, 0.14475588,
        0.14641561]])
    currMargUtilMat1_3 = np.array([[0.        , 0.00708303, 0.01202703, 0.01760781, 0.0238618 ,
        0.02953405, 0.03500005, 0.04046357, 0.04576374, 0.0525664 ,
        0.05714948, 0.06284042, 0.06713668, 0.07431587, 0.0775439 ,
        0.08429405, 0.08920301, 0.09645633, 0.10003191, 0.10857733,
        0.11310966, 0.11633637, 0.12409586, 0.12836672, 0.13344646,
        0.14050193, 0.1497587 , 0.14946381, 0.15967006, 0.16739316,
        0.17253168, 0.18024853, 0.18630931, 0.19582365, 0.19934008,
        0.20480294, 0.21444437, 0.22132304, 0.22260138, 0.23185276,
        0.23909004],
       [0.        , 0.01329085, 0.02462499, 0.03380493, 0.04226175,
        0.05046993, 0.05932477, 0.06684667, 0.07341225, 0.07996431,
        0.08682482, 0.09155627, 0.09791599, 0.10289822, 0.11087157,
        0.11427473, 0.11902581, 0.12522709, 0.13201416, 0.13705479,
        0.14368302, 0.1498692 , 0.15277716, 0.15971197, 0.16484615,
        0.17218462, 0.17908626, 0.1828527 , 0.18718651, 0.19372938,
        0.19954531, 0.20295784, 0.21171789, 0.21760787, 0.22222669,
        0.22850027, 0.2335897 , 0.2398155 , 0.24463211, 0.25007528,
        0.25750757],
       [0.        , 0.00529348, 0.01123608, 0.01691997, 0.02175003,
        0.02826035, 0.03205964, 0.03768284, 0.0428933 , 0.04780803,
        0.05229358, 0.05752097, 0.06182863, 0.06821374, 0.07070109,
        0.07640331, 0.08149737, 0.08777773, 0.09190038, 0.09639713,
        0.10063606, 0.10643852, 0.11287153, 0.11653095, 0.11904369,
        0.1263043 , 0.13024959, 0.13589724, 0.14153439, 0.14690753,
        0.15236881, 0.15844206, 0.16188635, 0.16772169, 0.17542838,
        0.18079987, 0.18230366, 0.19036298, 0.19682688, 0.20286276,
        0.20888919],
       [0.        , 0.00293124, 0.00625195, 0.0112157 , 0.01427235,
        0.01805878, 0.02183471, 0.02621103, 0.0302594 , 0.03384897,
        0.0369009 , 0.04082603, 0.04366943, 0.04903888, 0.05124203,
        0.05581082, 0.05901962, 0.06338594, 0.06669037, 0.06980079,
        0.07281564, 0.07641951, 0.08087053, 0.08330807, 0.08788097,
        0.09012091, 0.09394309, 0.0969323 , 0.09986965, 0.10502292,
        0.10478722, 0.11088498, 0.11308959, 0.11860284, 0.12381704,
        0.12539139, 0.12937432, 0.13582546, 0.13924364, 0.14128972,
        0.14675736]])
  
  estWts=10.
    currMargUtilMat10_1 = np.array([[ 0.        , 0.00187084,  0.01101145,  0.02365965,  0.01965287,
         0.03823087,  0.05337056,  0.05958397,  0.07286191,  0.07793368,
         0.09127867,  0.10039685,  0.11668969,  0.12878807,  0.14252184,
         0.14208644,  0.1657432 ,  0.17604455,  0.18321657,  0.19980126,
         0.21105289,  0.22425573,  0.23032374,  0.23380864,  0.24886922,
         0.2664309 ,  0.28078168,  0.29054588,  0.3053712 ,  0.3189738 ,
         0.33147267,  0.34854113,  0.36291605,  0.37188109,  0.39417027,
         0.40976565,  0.43168154,  0.44402194,  0.44885242,  0.47648269,
         0.4957011 ],
       [ 0.        ,  0.01186834,  0.03491119,  0.04886208,  0.06695837,
         0.07495542,  0.09197022,  0.10033022,  0.1180585 ,  0.12595512,
         0.13985525,  0.15162101,  0.16600205,  0.17868793,  0.18110014,
         0.19290154,  0.20804011,  0.22065009,  0.23450662,  0.23443267,
         0.24891079,  0.25835339,  0.27534679,  0.28625274,  0.29555394,
         0.30880638,  0.32655813,  0.33351133,  0.34890597,  0.35971161,
         0.37546348,  0.38209098,  0.39748997,  0.41674926,  0.42272661,
         0.43932451,  0.45124973,  0.46730243,  0.48131085,  0.49845187,
         0.51021886],
       [ 0.        ,  0.00342232,  0.0008001 ,  0.00945859,  0.0114537 ,
         0.01208335,  0.01955845,  0.02888311,  0.03419608,  0.04445848,
         0.04432007,  0.05786044,  0.06261182,  0.06905291,  0.07719035,
         0.08281079,  0.0908526 ,  0.10093437,  0.10839934,  0.11982786,
         0.12379783,  0.13607376,  0.14276805,  0.15699965,  0.16146493,
         0.16801934,  0.18431288,  0.19219167,  0.19960688,  0.21229042,
         0.22549028,  0.23609728,  0.24857393,  0.25736121,  0.26711188,
         0.2852789 ,  0.2917238 ,  0.31657368,  0.3152328 ,  0.33292339,
         0.35079498],
       [ 0.        ,  0.00131463,  0.00216888,  0.00233663,  0.00563665,
         0.00807464,  0.01630123,  0.02040699,  0.02348992,  0.0308401 ,
         0.03464561,  0.03600272,  0.04462128,  0.04583562,  0.05382358,
         0.06155156,  0.06316058,  0.07524263,  0.07484466,  0.0832945 ,
         0.09049415,  0.09827902,  0.10515398,  0.10362421,  0.11899321,
         0.1219086 ,  0.12858753,  0.13428234,  0.14596527,  0.1391174 ,
         0.15131183,  0.16128978,  0.16290716,  0.17740661,  0.19389113,
         0.19536222,  0.19819384,  0.21208915,  0.21891271,  0.22802349,
         0.24009162]])
        currMargUtilMat10_2 = np.array([[0.00000000e+00,  4.83668741e-03,  1.45813534e-02,
         1.96326671e-02,  2.31413815e-02,  3.86804520e-02,
         4.61214590e-02,  6.05979327e-02,  6.47738934e-02,
         8.64868920e-02,  9.92929186e-02,  1.05804054e-01,
         1.12973080e-01,  1.21170576e-01,  1.40429083e-01,
         1.53257261e-01,  1.63767139e-01,  1.70604815e-01,
         1.81619072e-01,  1.99590821e-01,  2.13338692e-01,
         2.25911591e-01,  2.34377736e-01,  2.45775901e-01,
         2.59745373e-01,  2.72993016e-01,  2.78790084e-01,
         2.97631741e-01,  3.09436457e-01,  3.23964952e-01,
         3.42375232e-01,  3.45788367e-01,  3.57194664e-01,
         3.84715190e-01,  3.96332889e-01,  4.16247451e-01,
         4.28541876e-01,  4.34327249e-01,  4.53980050e-01,
         4.74170805e-01,  4.96891685e-01],
       [ 0.00000000e+00,  1.25435918e-02,  3.46835893e-02,
         5.14704015e-02,  6.34644991e-02,  7.86829976e-02,
         9.36455476e-02,  1.04531575e-01,  1.15351244e-01,
         1.33511118e-01,  1.42926533e-01,  1.54275667e-01,
         1.68595862e-01,  1.75453250e-01,  1.93091437e-01,
         2.01786113e-01,  2.08583151e-01,  2.23168699e-01,
         2.33445698e-01,  2.47803188e-01,  2.62257876e-01,
         2.72612601e-01,  2.84883194e-01,  2.92827281e-01,
         3.08446368e-01,  3.12135693e-01,  3.30071907e-01,
         3.37860368e-01,  3.52626971e-01,  3.63199875e-01,
         3.78215119e-01,  3.87023349e-01,  4.00623785e-01,
         4.17480205e-01,  4.20415206e-01,  4.39058234e-01,
         4.57015078e-01,  4.68651395e-01,  4.82345173e-01,
         4.99659962e-01,  5.12887297e-01],
       [ 0.00000000e+00, -1.14363827e-04,  3.00073256e-03,
         7.52033566e-03,  1.41309105e-02,  1.56038719e-02,
         1.98573820e-02,  2.65041304e-02,  3.31834383e-02,
         3.84781317e-02,  5.20137657e-02,  5.63313873e-02,
         5.97668753e-02,  6.56409996e-02,  7.83112931e-02,
         8.38300948e-02,  9.42648317e-02,  1.02759743e-01,
         1.07608961e-01,  1.20897671e-01,  1.31922326e-01,
         1.38355693e-01,  1.45524104e-01,  1.57248710e-01,
         1.65996833e-01,  1.69625824e-01,  1.86428574e-01,
         1.90581664e-01,  2.04377770e-01,  2.15262120e-01,
         2.20361103e-01,  2.33466565e-01,  2.43542792e-01,
         2.59297076e-01,  2.72096155e-01,  2.94810139e-01,
         2.96072473e-01,  3.00002099e-01,  3.18898099e-01,
         3.25343744e-01,  3.40574636e-01],
       [ 0.00000000e+00,  1.67433533e-04,  3.10767971e-03,
         3.46355166e-03,  4.81379281e-03,  9.20337705e-03,
         1.41065739e-02,  2.29140849e-02,  2.29260441e-02,
         2.15643411e-02,  3.22765400e-02,  3.44265411e-02,
         3.63665384e-02,  5.18412729e-02,  5.55895491e-02,
         6.17863286e-02,  6.61767549e-02,  8.08018911e-02,
         7.23107185e-02,  7.73928591e-02,  8.77743395e-02,
         9.55472785e-02,  1.04512448e-01,  1.18251703e-01,
         1.08823562e-01,  1.23399304e-01,  1.29593127e-01,
         1.37820681e-01,  1.41696333e-01,  1.48624888e-01,
         1.55571287e-01,  1.63458960e-01,  1.73767662e-01,
         1.82366295e-01,  1.94403165e-01,  1.95413723e-01,
         1.99995171e-01,  2.14937216e-01,  2.22342358e-01,
         2.29868784e-01,  2.32654899e-01]])
    currMargUtilMat10_3 = np.array([[ 0.00000000e+00,  3.67716159e-03,  9.58572101e-03,
         1.93255263e-02,  2.45352363e-02,  3.67152701e-02,
         4.90953174e-02,  6.31365818e-02,  7.47135272e-02,
         8.92910885e-02,  9.50971193e-02,  1.08453053e-01,
         1.13943123e-01,  1.33128468e-01,  1.50304373e-01,
         1.56581639e-01,  1.72743146e-01,  1.81868192e-01,
         1.94261352e-01,  1.99301045e-01,  2.01820856e-01,
         2.31330648e-01,  2.43459807e-01,  2.53392606e-01,
         2.59433359e-01,  2.87330501e-01,  2.91722500e-01,
         3.01050810e-01,  3.14570076e-01,  3.25332400e-01,
         3.41087978e-01,  3.59667596e-01,  3.74694882e-01,
         3.73759261e-01,  4.04220386e-01,  4.10219673e-01,
         4.25812116e-01,  4.40560016e-01,  4.52723093e-01,
         4.72545255e-01,  4.96136652e-01],
       [ 0.00000000e+00,  1.22457326e-02,  3.56012015e-02,
         5.08022918e-02,  6.69209995e-02,  8.20668477e-02,
         8.91927811e-02,  1.07494145e-01,  1.22529285e-01,
         1.32797798e-01,  1.45272302e-01,  1.56675104e-01,
         1.67972264e-01,  1.82179732e-01,  1.96146740e-01,
         2.00720462e-01,  2.11122133e-01,  2.24624795e-01,
         2.36883123e-01,  2.50292709e-01,  2.59161328e-01,
         2.70350991e-01,  2.83886233e-01,  3.04917692e-01,
         3.02742172e-01,  3.19774237e-01,  3.34359386e-01,
         3.46938243e-01,  3.47800881e-01,  3.64649893e-01,
         3.82263396e-01,  3.87696257e-01,  4.02212534e-01,
         4.24265084e-01,  4.41367033e-01,  4.50832874e-01,
         4.52586278e-01,  4.68777555e-01,  4.80548332e-01,
         5.01568891e-01,  5.17341633e-01],
       [ 0.00000000e+00, -1.69332156e-04,  8.45316123e-04,
         8.12189219e-03,  1.19780269e-02,  1.23669561e-02,
         2.27546003e-02,  2.97163684e-02,  3.56550565e-02,
         4.02688437e-02,  4.36931771e-02,  5.43799202e-02,
         5.79590042e-02,  7.04482320e-02,  7.99544605e-02,
         8.71573755e-02,  9.10924680e-02,  1.02054402e-01,
         1.08927124e-01,  1.22748637e-01,  1.29506466e-01,
         1.36049857e-01,  1.43855924e-01,  1.52847115e-01,
         1.64627660e-01,  1.72419243e-01,  1.83370075e-01,
         1.86769264e-01,  2.04881425e-01,  2.17107651e-01,
         2.24299646e-01,  2.31916394e-01,  2.51620545e-01,
         2.58763150e-01,  2.61866504e-01,  2.88615140e-01,
         2.95062568e-01,  3.03796944e-01,  3.25276324e-01,
         3.37129701e-01,  3.46784250e-01],
       [ 0.00000000e+00,  3.16555963e-04,  3.58701738e-03,
         2.07870991e-03,  1.04771905e-02,  1.06240360e-02,
         1.47785411e-02,  1.34368789e-02,  2.36980664e-02,
         2.69802015e-02,  3.42547976e-02,  3.47978815e-02,
         4.34301827e-02,  4.69953555e-02,  4.92589589e-02,
         5.99059598e-02,  7.04083549e-02,  6.87402917e-02,
         7.80178199e-02,  8.02692803e-02,  9.37782120e-02,
         9.02093165e-02,  1.02023399e-01,  1.02348474e-01,
         1.10025426e-01,  1.18452399e-01,  1.22497611e-01,
         1.34374016e-01,  1.35220137e-01,  1.52307108e-01,
         1.56849938e-01,  1.62805632e-01,  1.64408359e-01,
         1.78202759e-01,  1.87026715e-01,  1.93602617e-01,
         2.10064169e-01,  2.05641358e-01,  2.17252370e-01,
         2.22159965e-01,  2.38465943e-01]])
    currMargUtilMat10_4 = np.array([[ 0.        , -0.00326299,  0.01453735,  0.01628512,  0.02586612,
         0.04753874,  0.05591765,  0.05757165,  0.07606291,  0.09240109,
         0.10249128,  0.10878816,  0.11771682,  0.13196049,  0.14124873,
         0.15634636,  0.1675337 ,  0.17075652,  0.18537548,  0.20258862,
         0.21917991,  0.22475422,  0.23718577,  0.2391832 ,  0.26909206,
         0.27934278,  0.28857025,  0.30401379,  0.31273704,  0.33494853,
         0.33888414,  0.35520634,  0.3685704 ,  0.3864484 ,  0.3963973 ,
         0.41314016,  0.42740338,  0.44832572,  0.45974107,  0.48512757,
         0.48608601],
       [ 0.        ,  0.01277454,  0.0341831 ,  0.04999897,  0.06451145,
         0.08112242,  0.09298163,  0.10668204,  0.11756693,  0.13214403,
         0.1476253 ,  0.15606789,  0.16626783,  0.18198117,  0.19642011,
         0.20513747,  0.21216651,  0.21901706,  0.23365039,  0.24885092,
         0.26505896,  0.27114178,  0.28658752,  0.29722849,  0.30775409,
         0.31589646,  0.33363951,  0.34258261,  0.34643554,  0.36982479,
         0.38042382,  0.39605005,  0.40390645,  0.4208388 ,  0.42636612,
         0.43958052,  0.45053472,  0.47731285,  0.47871535,  0.50083907,
         0.50782991],
       [ 0.        ,  0.0007562 ,  0.00358551,  0.00580023,  0.01038144,
         0.01758299,  0.01633052,  0.02748278,  0.03600851,  0.0401659 ,
         0.05237222,  0.0548623 ,  0.05913007,  0.06982566,  0.07714147,
         0.08462955,  0.09437928,  0.10162429,  0.10525623,  0.11667291,
         0.125469  ,  0.13891965,  0.14470481,  0.15418376,  0.16566666,
         0.17060066,  0.18604425,  0.19607424,  0.21002448,  0.21120157,
         0.23104373,  0.24629616,  0.24827763,  0.26287568,  0.27143312,
         0.28059402,  0.29067071,  0.30933815,  0.31915525,  0.33424084,
         0.34215385],
       [ 0.        ,  0.00229334,  0.00253851,  0.00446816,  0.0057453 ,
         0.0099234 ,  0.01035598,  0.01584162,  0.0202078 ,  0.02823991,
         0.03111249,  0.0336205 ,  0.04142276,  0.04347153,  0.05749626,
         0.05930998,  0.06570671,  0.07436107,  0.07610367,  0.08948242,
         0.08933244,  0.1002618 ,  0.10776564,  0.10933119,  0.11788855,
         0.12596371,  0.13209012,  0.1372783 ,  0.14800078,  0.15874893,
         0.16349956,  0.16743287,  0.16841558,  0.18512092,  0.19555775,
         0.20081598,  0.20592032,  0.21484288,  0.22182094,  0.23052392,
         0.23556636]])
         
    estWts=20.
    currMargUtilMat20_1 = np.array([[0.        , 0.03122135, 0.04374608, 0.07953968, 0.10254936,
        0.12161572, 0.13003613, 0.15749448, 0.1719171 , 0.1918125 ,
        0.22777451, 0.23559735, 0.25725892, 0.27445793, 0.30179373,
        0.30699252, 0.32095604, 0.35480799, 0.36816871, 0.39259309,
        0.41425483, 0.4223121 , 0.44518455, 0.44925048, 0.47439546,
        0.50796072, 0.5261675 , 0.5126548 , 0.57405647, 0.57250042,
        0.59500316, 0.62926465, 0.66110119, 0.65077332, 0.68687516,
        0.72492705, 0.71466246, 0.73569888, 0.75516775, 0.80209446,
        0.83343783],
       [0.        , 0.03165166, 0.06755261, 0.09790169, 0.12847424,
        0.1549243 , 0.17449295, 0.209035  , 0.22594135, 0.25013543,
        0.26704438, 0.28450725, 0.30078317, 0.32501482, 0.33638174,
        0.36099922, 0.38349504, 0.39893626, 0.41337632, 0.4294149 ,
        0.45103452, 0.46642913, 0.49198073, 0.48040902, 0.53025723,
        0.53288951, 0.55023925, 0.56902628, 0.59940141, 0.59994838,
        0.62921047, 0.64488971, 0.64732933, 0.67578892, 0.69094282,
        0.71232341, 0.73103274, 0.75803688, 0.77936355, 0.78281719,
        0.81053908],
       [0.        , 0.01349386, 0.01835839, 0.03624902, 0.04888304,
        0.06362281, 0.07838685, 0.09259829, 0.08735801, 0.10382033,
        0.12623277, 0.14468068, 0.14616553, 0.15301426, 0.17052173,
        0.19626283, 0.1997242 , 0.20765328, 0.22308789, 0.23568678,
        0.24199345, 0.26959985, 0.28542297, 0.29309988, 0.30838467,
        0.32690689, 0.33806552, 0.33884005, 0.36212169, 0.37406186,
        0.40354265, 0.42046131, 0.44057251, 0.46350341, 0.4811501 ,
        0.46994932, 0.50223796, 0.52051294, 0.53718143, 0.53079256,
        0.58224753],
       [0.        , 0.00693738, 0.01168812, 0.02614939, 0.04321451,
        0.05624197, 0.0705371 , 0.07974612, 0.07981949, 0.09413495,
        0.10124509, 0.10951591, 0.11970553, 0.12472883, 0.13974492,
        0.15980235, 0.15526957, 0.167716  , 0.17837736, 0.18456617,
        0.19781395, 0.20767611, 0.22679063, 0.23149667, 0.24106193,
        0.24656291, 0.25418944, 0.27595672, 0.29190698, 0.29354732,
        0.30494852, 0.31289544, 0.33511157, 0.32900062, 0.3422699 ,
        0.3795908 , 0.37088947, 0.38801096, 0.39276853, 0.40531781,
        0.41274841]])
    currMargUtilMat20_2 = np.array([[0.        , 0.02125559, 0.04827134, 0.07612011, 0.09900006,
        0.117807  , 0.13044409, 0.14380364, 0.18357705, 0.19352901,
        0.22648457, 0.22481154, 0.25058165, 0.26924929, 0.28408106,
        0.32106815, 0.34665462, 0.35130156, 0.36424857, 0.38222403,
        0.3971678 , 0.41683456, 0.43620454, 0.45841828, 0.48446863,
        0.51869544, 0.51917402, 0.53616076, 0.54384826, 0.58913013,
        0.61063711, 0.60761844, 0.63519711, 0.65703494, 0.68947866,
        0.69176519, 0.72553852, 0.74435918, 0.75250373, 0.80655128,
        0.82154512],
       [0.        , 0.03464929, 0.06648022, 0.10025408, 0.13052071,
        0.15442294, 0.18280851, 0.20638914, 0.22733564, 0.24781017,
        0.26396941, 0.28892964, 0.303294  , 0.323884  , 0.34093355,
        0.35758069, 0.37668851, 0.39187852, 0.41906084, 0.43656527,
        0.44936293, 0.4576348 , 0.48757412, 0.50318421, 0.50066724,
        0.53364626, 0.53653932, 0.57020696, 0.58124552, 0.60765385,
        0.62758798, 0.64375087, 0.64585578, 0.67515882, 0.69020541,
        0.707471  , 0.73724196, 0.74434771, 0.75724537, 0.7946975 ,
        0.79552227],
       [0.        , 0.00619485, 0.02288682, 0.03490385, 0.04759237,
        0.05697106, 0.06481024, 0.08367285, 0.09190088, 0.10918987,
        0.11901948, 0.12479013, 0.14812085, 0.15676291, 0.17020113,
        0.17677885, 0.20078372, 0.20023894, 0.22061875, 0.23996581,
        0.24889135, 0.26038592, 0.28547839, 0.28756778, 0.30107979,
        0.31551105, 0.33329454, 0.35240294, 0.35952505, 0.39054791,
        0.38175423, 0.41727104, 0.41845774, 0.4456186 , 0.46919596,
        0.46697455, 0.4815596 , 0.51216052, 0.51576777, 0.55476507,
        0.57554892],
       [0.        , 0.00667655, 0.02155994, 0.03320599, 0.04447114,
        0.04808501, 0.06544534, 0.07845296, 0.08387959, 0.0957279 ,
        0.11185868, 0.1164262 , 0.12415999, 0.12462307, 0.15221759,
        0.14709231, 0.15970262, 0.16544189, 0.17755409, 0.19083968,
        0.20254612, 0.20965376, 0.21695315, 0.22657548, 0.23740017,
        0.23672327, 0.26592288, 0.25685996, 0.27424787, 0.29433968,
        0.29764033, 0.3176335 , 0.31394635, 0.34277936, 0.34327169,
        0.36504689, 0.36949924, 0.40121726, 0.3804678 , 0.39214342,
        0.41161849]])
    currMargUtilMat20_3 = np.array([[0.        , 0.0189761 , 0.04213055, 0.0692274 , 0.08493518,
        0.10960439, 0.12935544, 0.15422591, 0.1820933 , 0.18605347,
        0.22541907, 0.24211535, 0.27216086, 0.28219   , 0.3031336 ,
        0.31651481, 0.32511504, 0.34052028, 0.36925879, 0.38560417,
        0.40745489, 0.42574937, 0.44538584, 0.47153099, 0.49696906,
        0.48501796, 0.52620456, 0.53600946, 0.55964428, 0.57523679,
        0.61583992, 0.60278173, 0.671152  , 0.67319313, 0.69536721,
        0.70002211, 0.73932198, 0.74938995, 0.77465165, 0.80738389,
        0.83052841],
       [0.        , 0.03462244, 0.06337425, 0.09766331, 0.13278672,
        0.15928553, 0.18140084, 0.2013699 , 0.22447844, 0.25444149,
        0.2703801 , 0.28741308, 0.310366  , 0.32698588, 0.33494323,
        0.35187905, 0.3663132 , 0.39165514, 0.40896314, 0.42619036,
        0.45106067, 0.46259076, 0.47972135, 0.48962602, 0.52389075,
        0.53374889, 0.54816289, 0.57126085, 0.59173295, 0.60042649,
        0.62641779, 0.63514353, 0.65932946, 0.67668017, 0.6976889 ,
        0.72098829, 0.73415278, 0.75966623, 0.77824961, 0.79381525,
        0.8164883 ],
       [0.        , 0.00903942, 0.02413912, 0.03254584, 0.04843705,
        0.05429044, 0.07220407, 0.07831914, 0.10317349, 0.11517455,
        0.1130295 , 0.12720642, 0.1323737 , 0.15361375, 0.17960553,
        0.18124269, 0.19874189, 0.20779291, 0.22725754, 0.24231435,
        0.24495276, 0.25749703, 0.2614105 , 0.28585186, 0.30991459,
        0.32096764, 0.33205682, 0.35415335, 0.37208474, 0.38673517,
        0.41181384, 0.4051197 , 0.42999701, 0.46210158, 0.47565562,
        0.49168729, 0.49006225, 0.52620659, 0.53915191, 0.55329862,
        0.58143864],
       [0.        , 0.00640279, 0.01418766, 0.03185527, 0.04052898,
        0.05813507, 0.07064662, 0.0698798 , 0.08459433, 0.09288537,
        0.10545113, 0.11289766, 0.11777098, 0.135632  , 0.13706071,
        0.16040039, 0.16150063, 0.1817523 , 0.16904969, 0.196118  ,
        0.20220446, 0.20381078, 0.2220336 , 0.22605781, 0.24013266,
        0.25000949, 0.27224234, 0.27808022, 0.28657007, 0.28856113,
        0.30267934, 0.30951681, 0.32110853, 0.33741482, 0.35765025,
        0.36438221, 0.36676315, 0.39707326, 0.40077812, 0.4001125 ,
        0.40735725]])
  '''
    # Get allocation solutions for different budgets and plot WRT parameter
    currMargUtilMat05 = (currMargUtilMat05_1 + currMargUtilMat05_2 + currMargUtilMat05_3) / 3
    sol05, val05 = GetOptAllocation(currMargUtilMat05)
    currMargUtilMat01 = (currMargUtilMat01_1 + currMargUtilMat01_2 + currMargUtilMat01_3) / 3
    sol01, val01 = GetOptAllocation(currMargUtilMat01)
    currMargUtilMat1 = (currMargUtilMat1_1 + currMargUtilMat1_2 + currMargUtilMat1_3) / 3
    sol1, val1 = GetOptAllocation(currMargUtilMat1)
    currMargUtilMat10 = (currMargUtilMat10_1+currMargUtilMat10_2+currMargUtilMat10_3+currMargUtilMat10_4)/4
    sol10, val10 = GetOptAllocation(currMargUtilMat10)
    currMargUtilMat20 = (currMargUtilMat20_1 + currMargUtilMat20_2+ currMargUtilMat20_3) / 3
    sol20, val20 = GetOptAllocation(currMargUtilMat20)

    allocArr = np.vstack((sol05,sol01,sol1,sol10,sol20)).T
    plotAlloc(allocArr, paramList=[str(i) for i in estWts], testInt=5, titleStr='vs. Underestimation Weight $v$')

    plotMargUtil(currMargUtilMat10, 200, 5)

    return

def testApproximation():
    numTN, numSN = 3, 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5, 0.05, 0.1, 0.08, 0.02]

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked', randSeed=86, trueRates=trueSFPrates)
    exampleDict[
        'diagSens'] = s  # bug from older version of logistigate that doesn't affect the data but reports s,r=0.9,0.99
    exampleDict['diagSpec'] = r
    # Update dictionary with needed summary vectors
    exampleDict = util.GetVectorForms(exampleDict)
    # Populate N and Y with numbers from paper example
    exampleDict['N'] = np.array([[6, 11], [12, 6], [2, 13]])
    exampleDict['Y'] = np.array([[3, 0], [6, 0], [0, 0]])
    # Add a prior
    exampleDict['prior'] = methods.prior_normal()
    # MCMC settings
    exampleDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    exampleDict['importerNum'] = numSN
    exampleDict['outletNum'] = numTN

    # Generate posterior draws
    numdraws = 50000
    exampleDict['numPostSamples'] = numdraws
    exampleDict = methods.GeneratePostSamples(exampleDict)

    '''
    # How many unique draws?
    draws1 = exampleDict['postSamples'].copy()
    exampleDict = methods.GeneratePostSamples(exampleDict)
    draws2 = exampleDict['postSamples'].copy()
    combDraws = np.concatenate((draws1,draws2),axis=0)
    combDrawsUnique = np.unique(combDraws,axis=0)
    len(np.unique(draws1,axis=0))
    len(combDrawsUnique)
    #if len(uniqueDraws)<numdraws: # Conduct more MCMC sampling
    #    newDrawNum = round((numdraws-len(uniqueDraws))*(numdraws/len(uniqueDraws))*1.1)
    #    exampleDict['numPostSamples'] = newDrawNum
    #    exampleDict = methods.GeneratePostSamples(exampleDict)
    # Look again
    #nextDraws = np.unique(exampleDict['postSamples'],axis=0)
    #combDraws = np.concatenate((uniqueDraws,nextDraws),axis=0)
    '''

    # Specify the design
    design = np.array([[0., 0.], [1., 0.], [0., 0.]])

    # Specify the score, risk, market
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design]
    designNames = ['Design 1']
    numtests = 5
    omeganum = 200
    #random.seed(35)
    randinds = random.sample(range(numdraws), omeganum)

    # MCMC
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'], randinds=randinds,numpostdraws=1000)
    print(lossveclist)
    # MCMCexpect
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'], randinds=randinds, method='MCMCexpect',
                                   numpostdraws=1000)
    print(lossveclist)
    # APPROXIMATION
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'], method='approx', printUpdate=False)
    print(lossveclist)
    # WEIGHTS
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'], method='weightsPathEnumerate', printUpdate=False)
    print(lossveclist)

    # Node sampling example; ONLY USE SINGLE-NODE DESIGNS
    design = np.array([0., 1., 0.])
    numtests = 5
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node',exampleDict['transMat']], method='weightsNodeEnumerate',
                                   numpostdraws=1000,printUpdate=True)
    print(lossveclist) # [0.15452505205853423]

    # Node sampling, pt. 2; ONLY USE SINGLE-NODE DESIGNS
    design = np.array([0., 1., 0.])
    numtests = 5
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', exampleDict['transMat']], method='weightsNodeDraw',
                                   numNdraws=200, printUpdate=True)
    print(lossveclist) # [[0.15521162653827367]]

    # DEBUGGING; 'weightsNodeEnumerateY'
    design = np.array([0., 1., 0.])
    numtests = 5
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=[design],
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', exampleDict['transMat']], method='weightsNodeEnumerateY',
                                   numNdraws=10, printUpdate=True)
    print(lossveclist) # [[0.1545609615470162]]

    '''
    lossveclist = [[0.1479217305053138, 0.14084809466415085, 0.19228942586836723, 0.1513926702303649, 0.154914290604453, 0.14880778645110954, 0.1458188048481419, 0.147311049218352, 0.16252821816972574, 0.14538552613227212, 0.16215475898072557, 0.20461414492094104, 0.15442966602543431, 0.14791806232589744, 0.14877943353209933, 0.15096074301895857, 0.14990954142013233, 0.14750615635115533, 0.15046452911329908, 0.14484440575096205, 0.15359323910212672, 0.14281387255705968, 0.1452059051392966, 0.20289508289913769, 0.14688942931626645, 0.16581082339540323, 0.14562777480984535, 0.147812394979172, 0.14284414091425504, 0.15434038025076907, 0.14481334773440233, 0.15551891175711657, 0.13235463073932305, 0.1479516296467864, 0.14656046870445663, 0.1402533753140278, 0.15311593130187123, 0.14926214142551245, 0.1812417946995411, 0.15127241250801685, 0.1477984271607804, 0.14057693214949382, 0.15195108920855369, 0.1924987412087236, 0.15444436789414998, 0.1451026594769498, 0.14563162638105243, 0.1456928498139271, 0.15050375247944384, 0.15647167292578865, 0.1488797658669125, 0.14228306894945517, 0.1368217157804952, 0.1600809288959258, 0.1484418591410903, 0.18734031282054986, 0.18919313265702248, 0.14625504676666418, 0.15994129990438488, 0.1542842000112373, 0.15173919525902807, 0.15033048187215345, 0.14461318843904614, 0.14604344228655441, 0.15050915977064988, 0.13423682275897458, 0.15347529527005385, 0.1552861360744961, 0.1475172371159737, 0.15071537996573392, 0.15208395795796503, 0.14540023092025, 0.20344425295631838, 0.2026896440696525, 0.15696445240641366, 0.149726726006842, 0.1420364118284895, 0.16174838029478633, 0.14046530168806223, 0.15030134783657514, 0.16057326290531876, 0.15346674109831163, 0.14137114226526218, 0.1474362291157891, 0.1500514856649408, 0.19805732576085736, 0.150400376429399, 0.1446569628926192, 0.1465217420552684, 0.15540239345904022, 0.1478161510806229, 0.15010809887871, 0.14960469147832126, 0.1435803584141635, 0.1484557372158955, 0.14420619653486777, 0.14361068151734477, 0.14903755212316508, 0.1477490606012085, 0.15283333740010252, 0.1782769537594729, 0.15340835114705104, 0.19133628816851597, 0.14045196015227102, 0.14156735938864098, 0.184791297559425, 0.15480730044909588, 0.15469493222836822, 0.15183770833922774, 0.1439715247169898, 0.18602736330736133, 0.1451864683083161, 0.15827336320123975, 0.15124256244533563, 0.14363936502466362, 0.15295495196316222, 0.14993688431036992, 0.1520090761293855, 0.15735514898723135, 0.15148456290740606, 0.14231544568652638, 0.1432655487032636, 0.1483923613510417, 0.1569148022953203, 0.14914038440487362, 0.15131672759101414, 0.15148457555951733, 0.1542185087141782, 0.1504984539855885, 0.15468412694794065, 0.148736749073621, 0.15904018983593615, 0.1460570882014333, 0.14069738674571883, 0.14412127194821442, 0.14751793740185942, 0.15341015017978543, 0.15237416693378475, 0.14209781448030123, 0.1501339259883911, 0.14578888227908737, 0.15172603345218144, 0.15373296501589315, 0.1477001348420058, 0.15297783757957037, 0.1605458147708352, 0.14691198645974096, 0.16240625143954543, 0.19688829750422188, 0.15092060138316904, 0.1425181799729412, 0.1444645897062611, 0.14968613159781552, 0.18246926464387234, 0.19482147506792433, 0.15364884354422007, 0.1468056078267283, 0.19693533307222197, 0.15733533548048537, 0.14022247982726843, 0.15291913100467486, 0.1925435586942793, 0.15219609954734314, 0.14176260177355782, 0.193113205823978, 0.1425478534265448, 0.14073888500587853, 0.17347794231631308, 0.14967838466761726, 0.14374419982427758, 0.14386981349711486, 0.1522698114436128, 0.1462804344670247, 0.14057772334501395, 0.1565198137440422, 0.14727636719638654, 0.13868293950062843, 0.15069925094211792, 0.1476729445352735, 0.1543956531171222, 0.15225064612530356, 0.14983260424789452, 0.14822202397444603, 0.19133146400673473, 0.15205405251511442, 0.15147396624580864, 0.15333475585936476, 0.14725069099476737, 0.15213301734525242, 0.1436311130653711, 0.1553849380894797, 0.14067100567386273, 0.15697662494931777, 0.14813147249201628, 0.15168838021699174, 0.14085995031712917, 0.14895376227726506, 0.14914654100545321, 0.1534357416986085, 0.1545262282591375]]
    CIalpha = 0.05
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist: # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (mn-intval)
        hiperc = (mn+intval)
        print('['+str(loperc)+', '+str(hiperc)+']')
    
    numtests = 5: [0.15187128426182853, 0.15590740997525168]
    '''
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', exampleDict['transMat']], method='weightsNodeEnumerate',
                                   numpostdraws=1000, printUpdate=False)
    print(lossveclist) # 0.15424065871736511
    # How does that compare with just using Q with the path-sampling results?
    design1 = np.array([[0., 0.], [1., 0.], [0., 0.]])
    design2 = np.array([[0., 0.], [0., 1.], [0., 0.]])
    lossveclist1 = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=[design1],
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'], method='weightsPathEnumerate', printUpdate=False)
    lossveclist2 = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=[design2],
                                    designnames=designNames, numtests=numtests,
                                    omeganum=omeganum, type=['path'], method='weightsPathEnumerate', printUpdate=False)
    sumloss = (Q[1][0]*lossveclist1[0]) + (Q[1][1]*lossveclist2[0]) # 0.15477929886063535




    # Generating utility along different paths
    numdraws = 100000
    exampleDict['numPostSamples'] = numdraws
    exampleDict = methods.GeneratePostSamples(exampleDict)
    numtests = 15
    Umat = np.zeros((numTN,numSN,numtests))
    for currTN in range(numTN):
        for currSN in range(numSN):
            designList = [np.zeros((numTN,numSN))]
            designList[0][currTN][currSN] = 1.0
            for nextn in range(numtests+1):
                lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                           designnames=designNames, numtests=nextn,
                                           omeganum=omeganum, type=['path'], method='weightsPathEnumerate', printUpdate=False)
                print(lossveclist)
                Umat[currTN][currSN][nextn] = lossveclist[0]
    Umatcopy = Umat.copy()
    Umatcopy = np.reshape(Umatcopy,(currTN*currSN,15))

    ''' design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    [0.16139074493480987]
    [0.1596501566793548]
    [0.15802375616532746]
    [0.1565223520781518]
    [0.15511252975619408]
    [0.1538055293808307]
    [0.15256615557418174]
    [0.15140601913401353]
    [0.15032002487439883]
    [0.14928654980934938]
    [0.14831242752860774]
    [0.14739471491476488]
    [0.1465183848408827]
    [0.14568844514986226][0.14489859477321548]
    [0.16139074493480987]
    [0.1608967916998771]
    [0.16043499152734067]
    [0.15999994493681388]
    [0.15958400609864054]
    [0.15919101430828217]
    [0.15881925753404794]
    [0.15847139735927754]
    [0.15814014900432016]
    [0.15782700459394972]
    [0.1575298658924002]
    [0.15724800532406225]
    [0.1569791583001218]
    [0.15672288066940596][0.1564795217982856]
    [0.16139074493480987]
    [0.16014321532478817]
    [0.1589776617456137]
    [0.1578956350706014]
    [0.15686758422970787]
    [0.15592322049081334]
    [0.15502516941821648]
    [0.15417584569200485]
    [0.15337784193116377]
    [0.15261696828128501]
    [0.15189970581270604]
    [0.15122107558975054]
    [0.1505741386377228]
    [0.1499566937481687][0.14936945779827454]
    [0.16139074493480987]
    [0.15948821470363195]
    [0.1578163073540825]
    [0.1563410079119103]
    [0.155011451896549]
    [0.1538112990405619]
    [0.15272739887992173]
    [0.1517407599775022]
    [0.1508344208112568]
    [0.1499989514503542]
    [0.1492336744965466]
    [0.14852556670466024]
    [0.14786767046132052]
    [0.14724748632288975][0.1466711086695393]
    [0.16139074493480987]
    [0.15946597401821425]
    [0.15767181665300625]
    [0.1560243215522587]
    [0.15446837041777794]
    [0.15302631562351934]
    [0.15165594395439458]
    [0.15038129594536073]
    [0.1491737489494751]
    [0.1480336872017237]
    [0.14695596740507816]
    [0.14593522935405087]
    [0.14496276048802334]
    [0.14404259908918202][0.14316708749039267]
    [0.16139074493480987]
    [0.1611694942654438]
    [0.16095674823339448]
    [0.16075301927438757]
    [0.16055687999443743]
    [0.16036873059720103]
    [0.16018878784938906]
    [0.16001640338459258]
    [0.15985069776093686]
    [0.15969115716009624]
    [0.15953692389615756]
    [0.15938880808386977]
    [0.15924595619733142]
    [0.15910937797448071][0.15897733953053905]
    '''


    '''
    # MCMC; numdraws = 1000; omeganum=200, design = design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    # numtests = 0
    lossveclist= [[0.16133017650379533, 0.16035294394907038, 0.1595924662032086, 0.15487830752617793, 0.15650447660787442, 0.15794549467836672, 0.15917288800908097, 0.15834339189737032, 0.15493891974935164, 0.15932141084511853, 0.14518335631454887, 0.15928931278081013, 0.16089537842948348, 0.1695358287264035, 0.17429801319872945, 0.1649763540898995, 0.165626882220875, 0.16089808644869735, 0.1540820532342465, 0.16789816247916398, 0.16138967077311822, 0.16604933602773692, 0.15132286916730903, 0.16433498460548043, 0.1548912271335561, 0.1622247918129544, 0.1670930133645804, 0.15843298354703372, 0.16554671684985706, 0.16869287937739286, 0.16383735818357528, 0.1601698963552796, 0.16553211936245854, 0.1670322307188803, 0.15588599516567084, 0.16570287109150553, 0.1542286367329047, 0.15401544574931406, 0.16334519033571923, 0.16456642842354008, 0.15950392251085885, 0.15877604797395653, 0.1575090347172811, 0.16442085707423137, 0.15600988208722238, 0.16143365840699972, 0.1725031804954956, 0.1548227752874847, 0.15432543190194115, 0.15290411414469304, 0.1625801006923724, 0.15463613819683625, 0.15561204047004454, 0.16034331083329412, 0.16261595034868942, 0.15881294536875173, 0.15558186245080063, 0.1662634390944614, 0.15966790729510807, 0.1519194986845735, 0.16555319604390706, 0.16064199628148199, 0.15487437683214933, 0.15639219447856684, 0.15742991151562524, 0.1661917424997767, 0.15738755939071625, 0.1594045037631456, 0.1719244412818409, 0.16268463407298475, 0.15067488875094834, 0.16020858604961546, 0.1592092411768965, 0.16319829137149008, 0.14573169806031924, 0.1665271959712879, 0.1622476156780807, 0.1649281610281695, 0.16433807296406988, 0.17385406009343038, 0.15453527907254289, 0.16886009018006176, 0.15826188626709292, 0.15664594696469547, 0.16601974368588895, 0.15865293334082356, 0.1557177489183188, 0.14944152746955677, 0.1671752602689376, 0.1610647418390835, 0.1610231928629766, 0.17018978467209805, 0.1638743465282651, 0.1556226178730051, 0.15329101886420485, 0.1591885181950829, 0.16600502283371354, 0.1605672769296792, 0.1575689242639313, 0.16212376255736535, 0.15779354119999683, 0.15993998306841162, 0.15808469033416367, 0.17065255451604908, 0.17203137814649103, 0.16313677581796568, 0.1481915257446885, 0.15624521180709855, 0.16092626752254352, 0.1638024703069324, 0.1510903326718172, 0.15922918180490878, 0.15670635651763457, 0.15481609853695277, 0.15669606724229013, 0.16031991456522512, 0.16088660040143754, 0.16385320710770648, 0.16796160852603736, 0.15459568233873106, 0.1621003077819244, 0.16338172884227875, 0.15671720996231078, 0.1567704653898434, 0.17214732743600758, 0.1691274701453852, 0.1680922656705758, 0.16124480503465366, 0.1584916283792435, 0.16156811503153465, 0.16291600504006074, 0.16221966025654508, 0.16825141534065627, 0.16061561719332765, 0.15875113752365289, 0.1562863670532987, 0.16407261247061478, 0.15176119846758998, 0.16821109499654527, 0.1631305082825532, 0.15996883083774774, 0.16961224284542958, 0.16241966667430655, 0.15070891143348633, 0.15697122060165575, 0.16283571728226173, 0.16249925959486367, 0.15536053790635976, 0.16343033084216146, 0.16998574401357167, 0.1612078365642256, 0.1601739613849356, 0.1588154545106319, 0.1585312223706728, 0.1588294512575155, 0.15967376527466817, 0.16707822575275227, 0.1690830241089197, 0.16044046643450197, 0.1688400518825839, 0.16105387652034195, 0.1632952392558217, 0.16579846628641964, 0.1539571135451126, 0.16796617527983237, 0.15716959592255395, 0.15587355281977683, 0.1534427052411982, 0.15410402035521967, 0.16749609528849954, 0.15547111101288763, 0.15159449803528477, 0.15623792670569955, 0.1547549044554394, 0.15791768346033594, 0.15813903640418397, 0.15823132340446167, 0.1548611982116423, 0.152098155028846, 0.15697310032703501, 0.16612284104409034, 0.16547233470663072, 0.17609506785479667, 0.15830730547763994, 0.16761277811845013, 0.1589530354532047, 0.14981105441307604, 0.1583311813159989, 0.16725862784816542, 0.15511606794270974, 0.1574082682980217, 0.15516593658459538, 0.1605584261856954, 0.1594909920477787, 0.17171756145962197, 0.15978283121255415, 0.15759668019446804, 0.16427578699030096, 0.15879074753830333, 0.15605348792721047]]
    [0.1597614327786745, 0.1613232845995245]
    
    # numtests = 5
    lossveclist = [[0.16040451705744033, 0.15031121945729578, 0.15972071154058132, 0.15736804661824655, 0.1576188661477262, 0.15495285232598813, 0.1509323016699268, 0.14942876163075636, 0.1535630231472643, 0.15169698325223488, 0.15144371246652447, 0.1645409228565071, 0.1555039516566019, 0.15279244386045554, 0.1550162928548847, 0.16115375010661348, 0.15933951489319723, 0.15387171352176404, 0.15152500639277547, 0.1617533964735161, 0.14043732226453995, 0.16070328779816553, 0.15675473068482282, 0.1563746548477993, 0.15121158272870427, 0.1617000882791677, 0.15773665717537738, 0.1534982568200604, 0.15162530148421857, 0.1479363335232301, 0.157682195476292, 0.14842543537277636, 0.16407308473285248, 0.1572656015470402, 0.1550631073361681, 0.1591075357706297, 0.15339062756379962, 0.1598497698685347, 0.15670980642316495, 0.15829786616947075, 0.16375144767993255, 0.15237576693713925, 0.15548888787761886, 0.15608945044919387, 0.1557164475888886, 0.15506973501748614, 0.14735649584995225, 0.15945736851468514, 0.16091994101248222, 0.16027234645688207, 0.16204078223117765, 0.15585999575211484, 0.15393295485740838, 0.1585270866792063, 0.15208260829316278, 0.1536974637146511, 0.153255173737287, 0.14806391133485491, 0.15683398268339596, 0.14579543285053226, 0.159960745806332, 0.15803288666773715, 0.15503812476304915, 0.15135376598186293, 0.15645240637921504, 0.15677340507981102, 0.151681259461289, 0.15015147785005425, 0.16254394780963602, 0.15698766641778314, 0.14808009790756274, 0.16125797501730296, 0.1573160496953113, 0.1550396184470147, 0.14646551458097443, 0.1577506177715445, 0.15958275436438174, 0.1593843385957193, 0.1546936793779228, 0.1540406356617238, 0.15028392686047307, 0.15548274920107752, 0.14911633316913717, 0.14794852855180504, 0.15660665472310226, 0.14905340479012985, 0.14952199184076995, 0.15952922326331984, 0.14631301145426287, 0.15884776326876607, 0.15232868727049856, 0.15677009034603986, 0.1545063436261434, 0.15126124088326784, 0.15108226774976793, 0.15423398811938188, 0.15035268079944514, 0.15144850151271635, 0.15916067050472216, 0.16022372480291616, 0.15594473294352623, 0.1678923340270207, 0.1524234863290381, 0.14966658692993076, 0.15328248361424, 0.14829067683697442, 0.16226987867951645, 0.15318996645023572, 0.15849551966034292, 0.1563525988493093, 0.15414719830162116, 0.16077703048456296, 0.1636999551074953, 0.1530484739450913, 0.149568456124276, 0.14914594458079886, 0.15484876752303403, 0.1665527694667707, 0.15807700158749463, 0.1494596140910415, 0.15346740984665083, 0.16197217386009072, 0.15644842920138796, 0.1660532822644248, 0.16051312159675002, 0.15957350420203195, 0.14854114645467248, 0.15578145921228126, 0.15623943905391383, 0.1632891453206, 0.15228211375405157, 0.1679008544542775, 0.15092003536477183, 0.15296722903493593, 0.1557213105355211, 0.14816536977371209, 0.15977850185411482, 0.14757215250822447, 0.1596965275618382, 0.1572877862312714, 0.15538482953230762, 0.1531060636384303, 0.15713316808290695, 0.15071370903604916, 0.15391796597357973, 0.15649689751959808, 0.15729719065384415, 0.1586722776068459, 0.15655911472460793, 0.1650271151280421, 0.16321362229939954, 0.15478590872304118, 0.15858406585834076, 0.15637815256328588, 0.1584136806634129, 0.1566249582190673, 0.15778351378110356, 0.16244575436629413, 0.14550194278182252, 0.15166614896121455, 0.15234095845085732, 0.1506969686459515, 0.16269017321279902, 0.15246856291775582, 0.15516160518165947, 0.15914058892305438, 0.1593545466204265, 0.15779874992013257, 0.15786653064798642, 0.15812825128086472, 0.16687716507540526, 0.16441307860489293, 0.15423553485918962, 0.1582562049909437, 0.15453968299450493, 0.1576340249538876, 0.15609340704680763, 0.15929621290794344, 0.16192278051664213, 0.15962275335890277, 0.14876692024831872, 0.15359448983632656, 0.14859466859743525, 0.15384065539670522, 0.15743463716339265, 0.15479628447509863, 0.1595982744130878, 0.15883876092612717, 0.15709681506032505, 0.15894812668519462, 0.15718956306111156, 0.15764773730021459, 0.15680675875464223, 0.14511485380597788, 0.14879831377007516, 0.16262976827643333, 0.15313636258123056, 0.15955331415363108, 0.1520202334994558, 0.16009204782600603]]
    [0.15506736184284828, 0.15641337994076746]
    
    # numtests = 10
    lossveclist = [[0.14673825948185226, 0.15178433701332245, 0.1497370325324721, 0.15124081747639304, 0.1462326046157289, 0.14847561404495713, 0.1496673049550425, 0.16410348431275595, 0.1450604326857086, 0.1520017035356987, 0.15421832722842174, 0.14565085177992304, 0.1503889025206848, 0.15425757433693213, 0.15669199687702604, 0.15768006785797622, 0.1543122758798466, 0.15841927412358292, 0.15603383244122507, 0.16292667640092032, 0.14969584138705197, 0.13928596274269975, 0.14811605364333522, 0.15559826334890478, 0.15114753228231584, 0.15079635471979363, 0.16629541487289135, 0.14837555746549716, 0.15097870060592256, 0.1548098277020026, 0.13985952358608342, 0.16022269366764205, 0.15266344331525006, 0.15111863555045202, 0.15167137265481817, 0.1599720561166862, 0.14631539588138764, 0.1528624992955047, 0.16112641085614043, 0.14184095903761115, 0.1513631374666895, 0.14360758225932155, 0.1603451588018429, 0.14309239153388348, 0.14946286808112508, 0.15343161523264778, 0.15704008501977418, 0.15852072346217577, 0.15026692444377138, 0.16396867566665782, 0.1504906210317537, 0.1470999188237132, 0.15216023738387563, 0.15831814713825165, 0.14900269113630407, 0.15409899758000337, 0.1539348035565592, 0.15218899468847968, 0.15215136377073418, 0.1494491909888216, 0.14535223073900116, 0.14683770057231446, 0.151206655702801, 0.1461183107033704, 0.15392763367324797, 0.15014247964488378, 0.15438863427516347, 0.14936009382758156, 0.1610716968476948, 0.15235491263306683, 0.15798009182649722, 0.15686204930998685, 0.14489953266009026, 0.153296512547374, 0.15058428200231105, 0.14820972833679494, 0.15575136413846827, 0.14330412489722702, 0.1555202778094492, 0.1603366558278284, 0.15639814686391276, 0.14739935963855774, 0.15524021128803547, 0.14840808928018379, 0.15203822954335752, 0.14539016689890055, 0.15269354349713735, 0.15484945977662862, 0.15601094701854035, 0.1469904267308603, 0.14646579578010316, 0.15937697667731687, 0.16029436671399072, 0.16027619548122646, 0.1518478934967677, 0.14748060661155865, 0.14825438426276322, 0.15093683960134874, 0.15167724826397128, 0.1504765098710665, 0.13765887012754818, 0.15457811061945412, 0.1529553289416999, 0.1546273986713626, 0.15297555035135135, 0.15195860290695548, 0.14330152695134166, 0.1423078549993534, 0.1462138787734364, 0.15841381111159764, 0.15233335108761387, 0.14698202935053936, 0.14974203706900058, 0.1427480830466954, 0.14737807532123126, 0.16166694861650643, 0.14931072810046872, 0.1496253891790005, 0.14982307205579476, 0.15461833330550634, 0.1450022149193867, 0.15180082731880082, 0.15338573444985606, 0.14518127662141367, 0.1504536109602005, 0.14842652143045926, 0.14848299449139535, 0.1570498085652627, 0.16468780293262728, 0.15479890334360963, 0.1547543360342835, 0.1572630059565484, 0.1489099018113888, 0.15901068958331593, 0.1567904138543914, 0.15317665915748288, 0.1450176224333364, 0.15555632241739942, 0.15660816106839315, 0.15727283463354996, 0.15887720573952047, 0.1472505685949653, 0.15866903538721758, 0.15292724683366957, 0.15006588542121319, 0.1566011994452853, 0.1565840341951643, 0.1474313829676284, 0.15754521533885407, 0.1601171592913776, 0.14476130564578263, 0.15416335008685783, 0.15842935552560933, 0.14329400105848325, 0.1481173194355913, 0.15491392079243999, 0.15925294228738243, 0.1496022669401441, 0.15658123863370227, 0.1426675173400567, 0.15186483781648666, 0.15533425284164348, 0.1443753394203832, 0.16209518741894083, 0.14953170923381354, 0.15004618018240048, 0.15741738776560463, 0.15078939514473028, 0.14210167523177175, 0.1512685607413724, 0.14940933182386879, 0.1590451111163163, 0.14918508498448346, 0.14750300642285924, 0.1470894455223877, 0.15004235788626036, 0.15227124375446308, 0.16398104713338466, 0.14986203917712881, 0.14888308600956016, 0.14810555282926438, 0.15994364796761693, 0.15206247906576778, 0.14231566606861648, 0.15110354833818712, 0.14968244518295742, 0.1454354426879137, 0.15135864488718462, 0.1456829054533047, 0.15342052196378791, 0.14241513910501255, 0.15009935234622845, 0.14678131386651677, 0.14720793316121636, 0.14148274330834604, 0.15044491478780678, 0.15015360148451345, 0.15938788894179895, 0.1562892656431987, 0.15582625465578515]]
    [0.15108957430579725, 0.15261417246493894]
    
    # numtests = 15
    lossveclist = [[0.1452205806405535, 0.1436751024574084, 0.14473642152298782, 0.14210356107137717, 0.14346030655353448, 0.15016067348269968, 0.14722431105754646, 0.14369718736119225, 0.1455971576855333, 0.14208701480770572, 0.15418500365246446, 0.1563811432939331, 0.14870370346373987, 0.14891146573349764, 0.15173559821544982, 0.15567797609055278, 0.14767281684645076, 0.14085793123576756, 0.14212297724196066, 0.1473550845169293, 0.1513789412932941, 0.14783544286953215, 0.1456287217319883, 0.14729902994871147, 0.15023866597865096, 0.1465062436963691, 0.15198811313087263, 0.14358196962671643, 0.1460439454491272, 0.1396721316418116, 0.14803954019201068, 0.14112542642231057, 0.1507532531436912, 0.14648753987553215, 0.14343293472908464, 0.14728953778288892, 0.14900381875580623, 0.14655966356405029, 0.14266994371158429, 0.15366477320310667, 0.14397930972646739, 0.1541886053947848, 0.15949375148351594, 0.13519982259131444, 0.14451398996141637, 0.14563701189042302, 0.1410218795382595, 0.15094043823438663, 0.14451081753434974, 0.14710871689836932, 0.1398457129010194, 0.15169991061142293, 0.14967031290410676, 0.1543673186522482, 0.14143377394271933, 0.1408350397814133, 0.14623755535813182, 0.15058952776001303, 0.14441335032085148, 0.14884431673601053, 0.14998240696566073, 0.1424002513140289, 0.16387767903316802, 0.14516870764969528, 0.13919147062864842, 0.16080883593228598, 0.1474072688180918, 0.13982426906216688, 0.15957404448530224, 0.14314720293640473, 0.14876703077267833, 0.145196498181258, 0.15241115137012312, 0.1504081672651254, 0.1486967468570563, 0.14324822274980786, 0.1482641487723937, 0.15303496893616828, 0.1555331200907896, 0.15296543610454838, 0.1551860390534079, 0.14568494081079855, 0.1504116531073036, 0.14398321227152558, 0.15548538267079776, 0.14618816088792982, 0.14864475079029446, 0.14840759929310857, 0.15035653317807848, 0.1540870875641113, 0.14522558622939463, 0.14532617382859495, 0.15075132947551134, 0.1405918178197357, 0.15292877864888252, 0.13930405520013758, 0.14486608887122032, 0.14674703301389383, 0.1419779060423821, 0.15065117561409389, 0.13767397357261607, 0.14437746521491948, 0.14946311500507573, 0.14272831662626603, 0.14232316148516208, 0.151620845766245, 0.145001461085421, 0.14253631663934926, 0.1444634571893404, 0.14586532351348286, 0.1458251717498947, 0.1407370525762607, 0.1621599749324134, 0.15058020825431134, 0.15032882672574152, 0.15493501480127958, 0.1427589864363228, 0.14350341764331717, 0.14077581858102206, 0.1531688042117255, 0.14699053892297925, 0.13918923118060936, 0.15043653617469918, 0.1472512452689345, 0.14693289954716865, 0.14534737736456496, 0.15741918691107123, 0.1474849988748812, 0.1529923148045982, 0.14492303686667096, 0.15232912217599048, 0.14910235831932164, 0.14775038677097044, 0.14952411113157488, 0.14927920595294494, 0.1528363707617866, 0.14521298160430027, 0.14242936759578215, 0.1452376925546005, 0.14904807993777355, 0.14588014320801512, 0.14188885226041167, 0.15317679525588693, 0.14289637211715076, 0.1386279069345688, 0.1420661462679872, 0.1459175229897949, 0.15151681694239302, 0.14373231245079596, 0.14746026157118583, 0.15075976512703546, 0.1377699293792378, 0.14596620703669225, 0.160115625285284, 0.14559813057566595, 0.13406905281901899, 0.15541206053300066, 0.15707877675313664, 0.1450111985709152, 0.141606497413088, 0.1589770237308354, 0.15562463536588822, 0.1647384157003106, 0.16426713152107553, 0.14965153249179344, 0.14219548485409145, 0.14270858408570347, 0.1456735626413548, 0.14420127167460786, 0.14755392627403904, 0.1409811322716588, 0.1403337199494616, 0.1538023788687809, 0.1445042935514373, 0.14138097435925137, 0.13981271613955185, 0.1447434816267453, 0.1506443209465673, 0.14942713517457445, 0.1475376443201465, 0.15702858063945738, 0.14945836579102073, 0.14684687042851607, 0.1469421306308332, 0.14723413490663353, 0.143573888835764, 0.1501892497232245, 0.1385786797916607, 0.15411270462211837, 0.13812777710125917, 0.1489167482828953, 0.1467765084266721, 0.14178019389685867, 0.14728147066883923, 0.14765287321645423, 0.14151340651827243, 0.1451253653780937, 0.1482326287527276, 0.14435925097913682, 0.13745358492720766]]
    [0.1465841760151503, 0.14812630053969397]
    
    # numtests = 20
    lossveclist = [[0.14230394892810258, 0.13056564810528493, 0.14219914382655546, 0.14657644431629674, 0.1464494274696762, 0.1354846306177635, 0.1376244041434003, 0.1466929109224942, 0.1489783419050483, 0.14509148431525284, 0.14364381532434112, 0.15374136885696288, 0.13877002346600242, 0.14979563967206846, 0.14680903103722678, 0.13823772327164344, 0.14506723876505284, 0.16101095453681188, 0.1353298978374574, 0.14859025051313013, 0.14110769255629818, 0.1443847855565694, 0.14375683851884938, 0.15064563131049608, 0.13622529992330482, 0.1436745661108125, 0.14183121236533203, 0.14729318704186192, 0.14105213834232, 0.14427684145290667, 0.13923713617185815, 0.14608075460970157, 0.1483599150489303, 0.1562432680209362, 0.15077540768199987, 0.1475333949572004, 0.1592924342319322, 0.14281243511474023, 0.15429048496828057, 0.14812295006431836, 0.14507917374256815, 0.14266053898973036, 0.15138256685718177, 0.13807263115443316, 0.15768876459908374, 0.1481115279445833, 0.14058339194317898, 0.15087570767754677, 0.14441921997470325, 0.13777588415719957, 0.14793664500697287, 0.1477087053252295, 0.14994392127084585, 0.15705587983675856, 0.1387056715232942, 0.14812456079217723, 0.13857615455570568, 0.15390062084573328, 0.13814983862707272, 0.15302323372366225, 0.14865689898577744, 0.13967209897518482, 0.14278176872419476, 0.15059555250632897, 0.15081401634034539, 0.14282501791214755, 0.14164199840503905, 0.14067421699684665, 0.15434574922973002, 0.13739719213985485, 0.15474644428426879, 0.1471228865283066, 0.1476779281107017, 0.14824945381527782, 0.147478532078333, 0.14788436113113934, 0.15193778090327414, 0.13974799373858907, 0.14987120716621766, 0.1458925096814678, 0.15224828471962618, 0.154674198630451, 0.14368534617975165, 0.13899819269516053, 0.14412039983926536, 0.1474193556035782, 0.14372673606097783, 0.14518627368136336, 0.14064931854900534, 0.14907283254722534, 0.15979453682501665, 0.14057420941098878, 0.14795038028350432, 0.13643572479610555, 0.1381927502504615, 0.13204324493030975, 0.1483997688537371, 0.12940550576188314, 0.14868210830222967, 0.14852030032637362, 0.13655678274296104, 0.14994991975670016, 0.14525429702070486, 0.16134285126845374, 0.14570366427850406, 0.15453439623681908, 0.151281457660853, 0.15487166743548492, 0.14790900163503723, 0.1542427719315962, 0.14967134247468059, 0.1358823190161352, 0.13717296655371902, 0.14232229281288855, 0.1452023481327636, 0.1491819021545491, 0.1355971173085469, 0.14168207856447254, 0.14764898153213463, 0.14976887855542245, 0.14819204971673589, 0.13993904919592148, 0.14544022042809088, 0.15223376005540284, 0.1485213563130287, 0.1559787728444775, 0.14851864214828275, 0.14144558795346118, 0.14276347614992368, 0.14475503022572508, 0.1529220546254517, 0.14947247003530578, 0.15414405156135114, 0.1481369931585248, 0.15668329994071112, 0.14466842253388643, 0.12835690930068588, 0.14904141605868598, 0.14544797927152303, 0.14187326451692583, 0.1527336638293154, 0.13669903275681322, 0.14415960644574694, 0.1397097315530591, 0.14332283981843502, 0.14492643046229925, 0.14618667396809562, 0.15116736899266464, 0.14262786249292503, 0.15362668602692883, 0.14350047692968027, 0.1500449554523574, 0.15259010715785298, 0.14660284566555828, 0.1455450981883858, 0.13896209008319368, 0.15301467881491787, 0.14410132103031476, 0.14328646876594298, 0.14300586135329144, 0.15624694749866247, 0.14487585420199814, 0.15892036927954353, 0.1518417638882754, 0.1498768293805164, 0.13814061658249677, 0.14122713499692494, 0.15161769004588346, 0.1408284156852228, 0.1415733225317588, 0.15094699424736785, 0.14291589836880658, 0.13894200123717687, 0.14721028258178404, 0.15224101710199905, 0.14156781934720158, 0.15102552138462932, 0.152342768261288, 0.13299527742274628, 0.1459698097492642, 0.14814123185118228, 0.14377776104354625, 0.14460454147797158, 0.13377747532973036, 0.1430103949960004, 0.14107038870400926, 0.14956180894481805, 0.16407484169746414, 0.15365419701985172, 0.14585057285266856, 0.14372305714762496, 0.14776525285034625, 0.14945139943335933, 0.15595942953248204, 0.14259516125800273, 0.14897516626986268, 0.14060994208171793, 0.15131510893961678, 0.14570261514085628, 0.1514339758209857]]
    [0.14525831399887887, 0.14700181315518987]
    
    # numtests = 25
    lossveclist = [[0.13976481119172288, 0.1402721193916987, 0.15548591458956226, 0.1437571446348328, 0.13295950834951595, 0.1352892105009851, 0.14506942321269145, 0.1413483606166796, 0.14661319825032995, 0.14657395954122285, 0.14016620112027045, 0.13280757748547445, 0.14114737525233284, 0.15920372312049624, 0.13788851846595324, 0.14274390602689407, 0.13983006325055644, 0.14910677959636634, 0.13822060157050212, 0.1493989910601474, 0.13714763011443679, 0.14480913677141657, 0.14142599970827652, 0.14080482156111804, 0.1443381497882648, 0.14189754453353468, 0.15423285863918612, 0.1467878604821344, 0.14406080038093438, 0.13896729927557558, 0.13830976517659974, 0.14741165514032784, 0.14509408208270455, 0.1470568182320232, 0.14620391554920217, 0.1454127493093117, 0.14922159612877037, 0.14130832837299304, 0.14317081634310425, 0.14198742541383533, 0.13190953267636488, 0.14244385390278838, 0.14810072342539166, 0.13511240090035767, 0.14001447205799308, 0.14635569530136458, 0.14182961647144832, 0.13726203510348076, 0.14365633817314416, 0.13867543322405954, 0.15132424475388206, 0.14192040146065993, 0.14679781869760772, 0.14513110353950853, 0.14034186169846394, 0.14881396154955537, 0.1560713712678311, 0.13332312905129237, 0.14444647498567068, 0.14190294278629775, 0.14617291762392565, 0.13637430336456485, 0.15143778218276527, 0.14044548149830685, 0.14094467299037836, 0.1431124155267114, 0.1501424956903045, 0.1416253363321605, 0.14898226535433506, 0.1472812434527108, 0.14126655615067205, 0.1459111529255601, 0.14647858031838087, 0.1443543651653473, 0.15081392319686973, 0.1362780748437499, 0.14331992435378615, 0.15012959347277716, 0.13893905816910165, 0.1489161296063529, 0.13764273586098172, 0.1460776410253233, 0.15076771070685743, 0.1403061227138892, 0.13313460201515717, 0.13698290225144302, 0.1385277907078083, 0.13407867130533932, 0.1465255688464108, 0.13721740193707765, 0.14142668825634433, 0.15628084170881096, 0.1482598668911832, 0.14687544118617102, 0.14010032795106322, 0.1452532615550579, 0.1417532708281067, 0.13655869512182522, 0.1411303877604745, 0.14120371218953826, 0.1430384717963851, 0.15630992474477384, 0.13501775822167256, 0.14833473186382634, 0.13972901258754125, 0.1484182982562263, 0.15238078106668967, 0.13762759191247023, 0.14187832835621994, 0.14908824564154077, 0.14255439361532019, 0.14463152879575367, 0.14552721370007884, 0.1359182793828399, 0.14010693715816558, 0.151870482462486, 0.14525142543858857, 0.14129948495469058, 0.14183683795412047, 0.15520386034916062, 0.13959214217418592, 0.1473340137684806, 0.14244725472553318, 0.13728653008028985, 0.13364195193413345, 0.14459008288868566, 0.14339369054158954, 0.13364150800546523, 0.14582649874579548, 0.14026261813717472, 0.16340344430269718, 0.14342685807860922, 0.14066923957050484, 0.14203268267881103, 0.1466643045535809, 0.15182814113668164, 0.14859948491743477, 0.14553019740765405, 0.15108853254472185, 0.13845306835978116, 0.14003746082175128, 0.1467341774550569, 0.13416592650487305, 0.1371454980950849, 0.1498760584745087, 0.14168099255026517, 0.13396974191642355, 0.14337723878792388, 0.1368266599758664, 0.14896011331087092, 0.14660095815249008, 0.1358937008146437, 0.140884804934718, 0.14472144743263052, 0.14502351449757053, 0.14445776650157352, 0.14513288406424063, 0.13580427961036673, 0.1484502839343305, 0.14084125680631132, 0.15519856309522156, 0.1431661072525992, 0.15907982038244084, 0.14821308658080148, 0.14356698353465788, 0.15432839278651503, 0.1409236434902716, 0.14453518946074553, 0.14588053460669403, 0.13913169194343183, 0.14751389115797153, 0.13828621152923162, 0.14009943300198954, 0.1470758822512471, 0.14602365500701311, 0.13366888470994845, 0.1487820920963565, 0.1442479191117537, 0.13698504510064827, 0.1381018991876545, 0.15076103713747738, 0.14140413278506697, 0.14080346181090994, 0.15426292164407263, 0.1536733378033161, 0.1374854066083664, 0.1432104874720429, 0.14136606575187627, 0.15078619449612876, 0.1428640513747599, 0.14350786218933875, 0.15009661024463078, 0.13944128698477087, 0.15169726133570563, 0.1536859773600667, 0.1458554943649039, 0.13821941655326522, 0.14025682887821003, 0.13933813876984136, 0.1387590234041701]]
    [0.1428698188560852, 0.14447382599396227]
    
    lossvec_lo = [0.15506736184284828, 0.15108957430579725, 0.1465841760151503, 0.14525831399887887, 0.1428698188560852]
    lossvec_hi = [0.15641337994076746, 0.15261417246493894, 0.14812630053969397, 0.14700181315518987, 0.14447382599396227]
    
    # WEIGHTS; 10000 prior draws for [5, 10, 15, 20, 25] tests:
    wts10 = [0.15871820009453552,0.1549758143406811,0.15207878808947314,0.1497671277680296,0.14783182923356122]
    wts10_2 = [0.15334045130848906,0.14951740913866263,0.14650183720526574,0.1440848934641734,0.1420839367644994]
    wts10_3 = [0.15480730308161084,0.1509169927993677,0.147888499285501,0.1454684825579922,0.1434762693610001]
    wts10_4 = [0.15518596591968636,0.15136432840127942,0.1484085079656065,0.14602622831430964,0.14404913304220737]
    wts10_5 = [0.15380437904031077,0.1498687912483846,0.1468128475815458,0.1443901817978914,0.14238131107704516]
    wts10_6 = [0.15605713066180557,0.15215429679595938,0.149103506443612,0.1466670354336617,0.1446747148748678]
    wts10_7 = [0.15504531143055814,0.1509765984841767,0.14783297984236965,0.14535698394603244,0.14331895977070472]
    wts10_8 = [0.15590367251825923,0.15198610715838487,0.14897265368972537,0.1465562795687068,0.14458818429085754]
    wts10_9 = [0.1553549600085803,0.15168664294160272,0.14880498345304785,0.14646378662900492,0.1445426989281478]
    wts10_10 = [0.15696947708243258,0.15307818158451875,0.15006211553575582,0.1476467724876715,0.1456528677389103]
    wts10_11 = [0.15555683031398115,0.15165816642723298,0.1486338571119152,0.1462416353815578,0.14425839401169474]
    wts10_12 = [0.15419738778948633,0.15050765923258985,0.14760063014691424,0.14527853066697402,0.1433656453842396]
    wts10_13 = [0.15557834227652906,0.15154075671904338,0.14846475115054758,0.1459960057636065,0.14398070711992594]
    wts10_14 = [0.15420310474651464,0.15044286045470304,0.14750445873610635,0.14513359516637275,0.14318631279660418]
    wts10_15 = [0.15779649998089407,0.15382447966501833,0.15074564369835824,0.14830165377744917,0.14629703584049145]
    wts10_16 = [0.15593623254684777,0.15190317536445214,0.1487883714773173,0.14629602537783945,0.14427929855505311]
    wts10_17 = [0.1546652924691649,0.15086191789697842,0.1478844006098803,0.14552090762409708,0.14357499563875795]
    wts10_18 = [0.15244303494697464,0.14854636041397085,0.14554023564355154,0.14310410434546345,0.14109289661639246]
    wts10_19 = [0.15616312698131207,0.15196718320415858,0.14876136246486896,0.1462236766980204,0.14416179146592095]
    wts10_20 = [0.1545807072363925,0.15063429888584787,0.1475679812541358,0.14513566841187214,0.1431097510320446]
        #50000 prior draws:
    wts50 = [0.15634284977105467,0.15239093186022373,0.1493421799432922,0.14691131384181857,0.1449136946098867]
    wts50_2 = [0.15460533667857285,0.15071284918582994,0.14771909061640634,0.14530858914053746,0.143333176480449]
    wts50_3 = [0.1547746704079875,0.15083775182512457,0.14780849281488537,0.14536834038844537,0.14337173274561957]
    wts50_4 = [0.15468916454939574,0.15074483735488498,0.14769558501211016,0.14525807710131833,0.14325287840959988]
    wts50_5 = [0.15469599978852092,0.1508629085441131,0.14788148491116687,0.14548705180435986,0.14352398845002667] 
    wts50_6 = [0.15536898616169179,0.15135900171728014,0.14826525011191918,0.14580909621664367,0.14378864457251717]
    wts50_7 = [0.1555681765020323,0.1515992395658027,0.14854037941968168,0.14609682247367148,0.1440876736903238] 
    wts50_8 = [0.15621425393058946,0.15233049308711796,0.14933710768348057,0.14693587800582833,0.1449626398269233] 
    wts50_9 = [0.15406622699411163,0.15017494804843315,0.1471514437573615,0.14474394246804306,0.1427584964153624] 
    wts50_10 = [0.1550096429567588,0.1511070971685467,0.14809672903680926,0.14568158440230686,0.14369540095334848]
    wts50_11 = [0.1547225960324398,0.15077834950966496,0.14774836026490512,0.14532593357995244,0.14332732142843654] 
    wts50_12 = [0.15555171513529228,0.15152486381029556,0.14842279507098333,0.14595882116216505,0.14393139828422333]    
    wts50_13 = [0.15477300981062678,0.15085032239672197,0.14780765374497018,0.1453755433218728,0.1433677066461009]
    wts50_14 = [0.15520475879802684,0.15133184623743381,0.14833515246180878,0.14593079249867458,0.14395708042589428]
    wts50_15 = [0.15460586404699178,0.1506522120450011,0.147599326235705,0.14516981514290483,0.1431726232532779]
    wts50_16 = [0.15444891438667188,0.15051680253768035,0.14747231833081248,0.1450318629639167,0.1430266572769793]
    wts50_17 = [0.1548223676594893,0.15096260914823065,0.14796452126811616,0.1455632035043488,0.1435904745178972]
    wts50_18 = [0.1560114056397609,0.1520319002835606,0.14897012167204213,0.14652965714706287,0.14452340680592163]
    wts50_19 = [0.154222171710566,0.15026748499497172,0.14721762857858015,0.14478230941475337,0.14278127672514812] 
    wts50_20 = [0.1564828128636623,0.15248653098878218,0.14940608116567536,0.14695259909944297,0.14493306806373324]
        #200000 prior draws:
    wts200 = [0.1556824914607332,0.15169556728979305, 0.14862528766821606, 0.1461760931219823, 0.14416658451707415]
    wts200_2 = [0.15589403571243574,0.15197836567736628,0.1489520909836286,0.14652881311686944,0.14454304628609052]
    wts200_3 = [0.15544282177070148,0.1514882127428799,0.14843397777746953,0.1459988370307517,0.14400057831522162]
    wts200_4 = [0.1554696897455313,0.15149865336166563,0.14843783055076282,0.14599308143120343,0.14398635353617506]
    wts200_5 = [0.15499584329480406,0.15108902806831792,0.1480746502942479,0.14566253353245767,0.14367944770618046]
    wts200_6 = [0.155704510715483,0.1517788371687623,0.14875126648570872,0.14632762285551232,0.1443386658940193]
    wts200_7 = [0.1548692083896026,0.1509635118618388,0.14794921848540687,0.14553761116291689,0.14355243306312013]
    wts200_8 = [0.15573975737814807,0.1517944680637346,0.14875601912601155,0.14632652750213504,0.1443322450527161] 
    wts200_9 = [0.15518480643590812,0.1512729506347579,0.14824809981105277,0.14583480473188404,0.14384746651530236]
    wts200_10 = [0.15575889341306354,0.15179554111897664,0.148740698855299,0.14630163717680755,0.14429817649019908] # Run 8
    wts200_11 = [0.1553207426757495,0.15139580798872757,0.14836480790644235,0.14594123610762638,0.14395033142640803]
    wts200_12 = [0.15558311553948262,0.15162092579433312,0.14857679177577107,0.1461388852308946,0.14413761271795794]
    wts200_13 = [0.15559972834725125,0.151635706378525,0.14858462649080745,0.14614120066907862,0.14413558663599252]
    wts200_14 = [0.15579848128952845,0.1518694881505956,0.14883502307963842,0.14641428831634223,0.14442173202720734]
    wts200_15 = [0.155692381636969,0.15173657444893626,0.14868526932757384,0.14624948534391824,0.14425120655129994] # Run 2
    wts200_16 = [0.1556837020650656,0.1517485250977994,0.14871377053625462,0.1462841758688025,0.14429005630753158]
    wts200_17 = [0.1555410709083064,0.1515870102464919,0.14853602994048457,0.14609880604419997,0.14409699104820536]
    wts200_18 = [0.1556484104844971,0.151709077097123,0.14866570136150037,0.14623411954103865,0.14423810769393866]
    wts200_19 = [0.1556652777489911,0.15171446782909714,0.14867334902873983,0.14624012428256394,0.14424234681282655]
    wts200_20 = [0.1551934145228243,0.15126010399150583,0.14822282739152062,0.14579489700028675,0.14379719748910014]
    
    mcmcexp_lo = [0.1597614327786745, 0.15506736184284828, 0.15108957430579725, 0.1465841760151503, 0.14525831399887887, 0.1428698188560852]
    mcmcexp_hi = [0.1613232845995245, 0.15641337994076746, 0.15261417246493894, 0.14812630053969397, 0.14700181315518987, 0.14447382599396227]   
        
    # APPROX
    draws100 = [0.17096251909888835, 0.1481330548574234, 0.17047962293359242, 0.14872547351078536, 0.16508938138428117, 0.17095537965185834]
    draws500 = [0.1559392360454287, 0.1668042649471653, 0.16052768465584893, 0.15512831345943953, 0.15885933686450435, 0.17063859384373134]
    draws1000 = [0.16580795389668573, 0.16096495008980835, 0.1575308603477801, 0.1674442559796281, 0.1618666724542025, 0.1599543024805722]
    draws20000 = [0.16133369499491293, 0.16293700812491485, 0.16247429157083842, 0.16243704169610776, 0.16133173435041395, 0.1614570356185007]
    draws50000 = [0.1616567234596208, 0.16274689841949058, 0.16209550283881458, 0.16107551608256937, 0.16182528680125305, 0.16274905516400429]
    draws100000 = [0.16139074493480943, 0.16264269307218213, 0.16185294103912018, 0.16182869617070925, 0.16194445731186236, 0.16211384616042754]
           
    # FOR GENERATING 95% INTERVAL ON LOSS
    CIalpha = 0.05
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist: # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (mn-intval)
        hiperc = (mn+intval)
        print('['+str(loperc)+', '+str(hiperc)+']')   
    '''

    '''
    # MCMCexpect; design [[0.,0.],[1.,0.],[0.,0.]]
    # numtests = 0
    lossveclist = [[0.16358824693077756, 0.15716600956111187, 0.16258879273613197, 0.16398272260296284, 0.16122038843845127, 0.16397457627171752, 0.16062032376791985, 0.15751539835240647, 0.1706072331022544, 0.1518958884814964, 0.1647452151326761, 0.15829419371086134, 0.15885340085328703, 0.1621415405692401, 0.16286049917094025, 0.156625360683157, 0.16554424864204512, 0.16098448483272512, 0.15774425035214798, 0.16589066634004498, 0.15805750492369272, 0.15625470483610535, 0.16710454609683034, 0.16180033826685727, 0.1535613224645323, 0.16481252710372105, 0.15802306210655914, 0.15402900047845952, 0.1610199563172257, 0.16240009318239526, 0.16272502603474087, 0.16736542430447626, 0.1587667376303871, 0.16647563626755663, 0.15580679372898373, 0.15927400679126352, 0.16140681296894016, 0.16177447941010778, 0.1671920264682422, 0.16098151269319616, 0.16184744487177408, 0.15812234669265368, 0.16053496935737244, 0.16268110283831702, 0.15615257064833707, 0.15801881279019062, 0.15273009253420303, 0.1682266740112519, 0.17182022958341783, 0.16050001101745054, 0.1594101088125565, 0.15179666592195476, 0.1660715047775367, 0.1548403794552042, 0.16153382844956457, 0.1544349303045409, 0.15863297075595542, 0.1681405230001371, 0.16476962847216275, 0.16436125874300106, 0.16471945185862066, 0.15588257800134525, 0.15712125288344164, 0.1649332472602849, 0.15858359475214542, 0.16479044192017422, 0.16862329523502487, 0.16930755548142634, 0.1663570222085106, 0.16305120245756752, 0.15966699254170205, 0.16628388440920241, 0.15291389034337866, 0.15501155359570643, 0.15935503288275737, 0.1595379793153437, 0.15721192761549066, 0.1656629389257, 0.1527460456482088, 0.15667962840148203, 0.15823758106723662, 0.15577479937056954, 0.15513364672347751, 0.16073123967151434, 0.15754719288549257, 0.15933233822098505, 0.17062554605957922, 0.1651871733169388, 0.15611476683983816, 0.15999311423873605, 0.17498131457446597, 0.15705146657771674, 0.16280431843214518, 0.15470598608185163, 0.16332286527621165, 0.15510704946110224, 0.15720632735052564, 0.15076408341916772, 0.16364220887152106, 0.16052341438818832, 0.15462575954920524, 0.15845580483691618, 0.15315097091238689, 0.1662325986941184, 0.1685372526769466, 0.15783009992515892, 0.1574483369854052, 0.16071085281187425, 0.1666343989826186, 0.16074958394474648, 0.15011290343969275, 0.16626133432786958, 0.16157254203065957, 0.15031950698812566, 0.15823864134850696, 0.15549440194017963, 0.1567632740818112, 0.15544686267732039, 0.155128549222738, 0.1696074208238554, 0.15710187848368914, 0.16612956983273686, 0.15297201464836654, 0.15576196737052564, 0.15907065766314907, 0.15836870386406676, 0.16138179140196393, 0.16598538933515675, 0.1568876073982065, 0.15967422123579153, 0.16258753328366654, 0.16736357087301504, 0.15029445936462063, 0.16276125755551868, 0.15321238192304135, 0.16233985590331834, 0.15761648379463, 0.160125396749554, 0.17180659587264693, 0.15699820541311904, 0.160726046456122, 0.16550616938229468, 0.1669604943486604, 0.15839114598840126, 0.1673247799902561, 0.16205585672650347, 0.16062613088572156, 0.16504478212020407, 0.16598685839483215, 0.15865244942859325, 0.15606508284582493, 0.16786204750734568, 0.16066436968728123, 0.1634880600352853, 0.15906232643264231, 0.15894793873984384, 0.16931667659361394, 0.16123817919148367, 0.16731853100297062, 0.1585368120909304, 0.16419052464104342, 0.1513773497350315, 0.16936751003373135, 0.15674848623649001, 0.15841755470530944, 0.16050126701952894, 0.16067168728631995, 0.1659097310276372, 0.15922388693988118, 0.16058027345319673, 0.1558956164190545, 0.163506939607734, 0.15840937752488696, 0.1615527505340876, 0.15283465403220284, 0.15758362353381888, 0.1630237696803376, 0.1638157820665923, 0.16167612440802712, 0.16003892083685473, 0.1608514737427389, 0.16892324666188116, 0.166529743131962, 0.1634197690765498, 0.16233880632228212, 0.15818158210461683, 0.15998541043288522, 0.16559488707418696, 0.1666051970254832, 0.150793445838315, 0.16463108872558802, 0.16393595769360952, 0.16278678245750264, 0.16168880201321248, 0.1579010410853301, 0.1628194722465565, 0.16050581761027613, 0.15924474509245884, 0.17341039949459358, 0.17138569178940957]]
    [0.16021197670665502, 0.16158723848900422]
    
    # numtests = 10
    lossveclist = [[0.15936559311497797, 0.15281048483967188, 0.15301648750311905, 0.14819709403201303, 0.15143907753086086, 0.15768824190459624, 0.1487189382867142, 0.1608596365567052, 0.15018893114654477, 0.1561941020508966, 0.1423873845032744, 0.15228608427987478, 0.16420081293894578, 0.14622123643828563, 0.1545836652028223, 0.15534915313462697, 0.14229769372993897, 0.14374523365066869, 0.14811271210122764, 0.1585843191859007, 0.15574787327691267, 0.15573397256002663, 0.15298499555002018, 0.15676000885663927, 0.14883046784308218, 0.1469140714403702, 0.14632402439535774, 0.1475572273149342, 0.15041278841313366, 0.15532400894454573, 0.15442655471815858, 0.14728659008429304, 0.15086595826904228, 0.15110620787906953, 0.14290517448152895, 0.15018782449248266, 0.1484662627514497, 0.1544805167962645, 0.14841073957746448, 0.15611392442128538, 0.1496809584640426, 0.14873796297961286, 0.1524442501184391, 0.15075703391870315, 0.14485528150046492, 0.14661268350166387, 0.14541454518551405, 0.148366460603512, 0.15245754916571921, 0.1415742671953485, 0.14912449143530654, 0.15377306651867914, 0.15030520885903523, 0.1547963992596536, 0.1580817811374872, 0.15441272890833865, 0.15218074624218247, 0.14632806905028217, 0.1511177324756385, 0.15012191606448516, 0.14832041460696768, 0.15310614115225935, 0.14746907423171807, 0.15539405197617095, 0.15121201403332923, 0.14650836220672056, 0.1585197071026352, 0.1564646578868664, 0.14927895352776827, 0.15405069623043793, 0.1523857899595256, 0.1514405415054654, 0.1419975005935354, 0.15649335980468265, 0.15621951117971872, 0.14972595558114873, 0.15330290083133208, 0.16442529660918834, 0.1515239160825881, 0.15607753570490743, 0.14318988293510646, 0.1580934543925378, 0.1517482428939543, 0.15368249740596718, 0.14838000916237007, 0.14821414672433733, 0.14769571944809848, 0.15176681488120575, 0.15092061398227694, 0.1531521152074112, 0.153493458702281, 0.15099774943870795, 0.15375582759853074, 0.1407705039161778, 0.15684774814145916, 0.15283608043761251, 0.14976326792472722, 0.15066256389067217, 0.15069315411354828, 0.15225432865980149, 0.14154349250938297, 0.15772784314900407, 0.15385507832259135, 0.14858411348324777, 0.14136135857870502, 0.14777864909312377, 0.1549002000019437, 0.14239067351969767, 0.13740013961128036, 0.15259343975207457, 0.14751337544337895, 0.15253604411801389, 0.15402338970492493, 0.14619722267841215, 0.15406337272850174, 0.15071762626078503, 0.1595140944025438, 0.14461210407017788, 0.1548707427360153, 0.14141464358366496, 0.14156376057749637, 0.15184625121099693, 0.15254792499695166, 0.1484531762480302, 0.14647811641451805, 0.15334278097861404, 0.14240377015037914, 0.1489544203880496, 0.1514084774968838, 0.15473976975474338, 0.15700465146856146, 0.14508943991296896, 0.1547572001930277, 0.1466869926937184, 0.149192938559423, 0.1514525358873467, 0.1479620927397677, 0.15341153244150948, 0.1566628232751799, 0.1484444349850034, 0.1501043808871011, 0.14683290708718882, 0.14372647847577946, 0.16455504405045043, 0.1488936165500803, 0.15360547141630349, 0.15246357696223997, 0.151237951826925, 0.15125616584678914, 0.15469357369431688, 0.16103479209065727, 0.15010433354804975, 0.1596735992164866, 0.15184962806899102, 0.14929575119961264, 0.15539913886893, 0.160727637189083, 0.15484617694970285, 0.1422813908550581, 0.15011295280475387, 0.15216040317605362, 0.14554115791273026, 0.15181867420816303, 0.15505234430864054, 0.14497000078785272, 0.15662773314098258, 0.15248325913026473, 0.15578572458926584, 0.13876842900341846, 0.13910693612816777, 0.1666805537053591, 0.14335192158894314, 0.1521136203960297, 0.14604590781335836, 0.15005613506564697, 0.14756769152415436, 0.13832444656191864, 0.1460597480228831, 0.1492541519485563, 0.14682510645852373, 0.1439388457489174, 0.1478372289031657, 0.15344413554018718, 0.14965449731425992, 0.14305052084350087, 0.15750229131499022, 0.1630906945559717, 0.14313153334378287, 0.15970113434303485, 0.1546339841826926, 0.14580553338290123, 0.15101310404900511, 0.1427132910408688, 0.15099769685765468, 0.16610708866753096, 0.148702984546183, 0.16085118889525835, 0.1480508183781159, 0.1520854928151383, 0.14348025852573215]]
    [0.15016267023404384, 0.15167878274470148]
    
    # numtests = 15
    lossveclist = [[0.16410929196416632, 0.14465398990669023, 0.14168288970841486, 0.1485446478266021, 0.14794447659552384, 0.14696836111671946, 0.16265798656869632, 0.16465641022117916, 0.14712527710699175, 0.14253078860999163, 0.14160566985615478, 0.1397066451412966, 0.15586107793345946, 0.1414091184083943, 0.15077642869989158, 0.14646507207687426, 0.15163835079821422, 0.15301253395650544, 0.15087720727761408, 0.1415485569290662, 0.1506423908775248, 0.1418934687651676, 0.14538130325202894, 0.14880056474089437, 0.14872655367153087, 0.1470111309361693, 0.1491010175530016, 0.14903302120887177, 0.14444715807642816, 0.15313190335866284, 0.14768659876435106, 0.14485677957735107, 0.15183082486488125, 0.15099334965274747, 0.14940426180138644, 0.1472949073856396, 0.15013991780652594, 0.14461999884209478, 0.13888292845139716, 0.16298823422854225, 0.1507412950795776, 0.1446693390141012, 0.15416182169135334, 0.15035203656658092, 0.14544744776535515, 0.14648478038791626, 0.1520722159378607, 0.1475935560256991, 0.14592289179261092, 0.15169136007688827, 0.1442978316854447, 0.1401994148237808, 0.15267004371501813, 0.144523556832562, 0.14741538315226224, 0.1414640441165797, 0.1495324494649476, 0.14693898534404834, 0.15391198305435425, 0.13841027436075584, 0.14568533008450968, 0.1631364022599949, 0.15271312380006866, 0.14507836741867697, 0.15306663866221284, 0.15340149898046096, 0.14997484512486367, 0.1397077971213084, 0.15796218353143585, 0.14328048537987081, 0.14322833641725657, 0.14624496551586813, 0.14640959629536693, 0.1586290818659108, 0.14490099213741967, 0.14903918563399404, 0.14751335737715598, 0.1527803999643765, 0.15094753356767687, 0.14454937300983786, 0.15430405575621645, 0.14963783321531085, 0.14290212442182387, 0.15164482915150726, 0.13886106904684428, 0.1528069386744492, 0.1507068123552461, 0.14940689251910144, 0.14903207885861045, 0.14984190941913586, 0.13878745138655227, 0.13772347222656348, 0.15295204588122713, 0.1584496013974793, 0.15649283192553412, 0.14465626245672206, 0.14745385163792968, 0.14822591917577904, 0.1415162328488216, 0.1567886478885103, 0.15144687862155515, 0.14664384905683187, 0.149338975096502, 0.15289220164219677, 0.1498288292972931, 0.15475738305051123, 0.14449488001602767, 0.1447030359613033, 0.14207835247139314, 0.14942983792440076, 0.14110088761269954, 0.1508796807759093, 0.14899988134078337, 0.1473882059551492, 0.14535663204837843, 0.13838891055284852, 0.14184472367517634, 0.14600376528435655, 0.15321978636372702, 0.16124453833014213, 0.14482748222376876, 0.15123798518423534, 0.14225919696155984, 0.15474779956488588, 0.16056988873057973, 0.1481915010621652, 0.14929989126658239, 0.15151125489991105, 0.14572325186479626, 0.1507464709880059, 0.1569712737862299, 0.14574448322198905, 0.15224620719708395, 0.16085055280742472, 0.1510797201936358, 0.15338452008859038, 0.15431465789606846, 0.14853763183776741, 0.14586141766387412, 0.14633010770165436, 0.14112754890594356, 0.14848972577243355, 0.1494833746019399, 0.13956921989665352, 0.1488908110292435, 0.16531391243484778, 0.14725224794064748, 0.14777029016193075, 0.1455792872050659, 0.14877587991433144, 0.15613801126654242, 0.14853193517084504, 0.1529155135736609, 0.14681874306475126, 0.16271981187275994, 0.15329313185545385, 0.15075023884550692, 0.14601173228768494, 0.1489254891427093, 0.15053271216199193, 0.14743534578366652, 0.14578984406651796, 0.14330209455311876, 0.1449853695506467, 0.1385257491775937, 0.14815099493322495, 0.13875644755728114, 0.14323023471035906, 0.14272606405972124, 0.14103990096100774, 0.1486601915608013, 0.13536369061926284, 0.14691396412023858, 0.14601045248817943, 0.13251803891325742, 0.14399004048304226, 0.14963580292522077, 0.15350089660870953, 0.1446221378780701, 0.14742353031772457, 0.1544463450497568, 0.1435924367576897, 0.1381058957595342, 0.15068023011248743, 0.13905369914720533, 0.14697072439101788, 0.14769959423036544, 0.1600592223216871, 0.15285592850893048, 0.1486848496405545, 0.15187805638986973, 0.15532325641390962, 0.146492578503281, 0.14572331822611198, 0.14739764370508168, 0.15429828556481812, 0.15043997027561576, 0.14713474763647727, 0.14545479838023204, 0.1473839384163263]]
    [0.14764479788349866, 0.14924724829468644]
    
    # numtests = 20
    lossveclist = [[0.14063618027637526, 0.14497019384804757, 0.14992032538873004, 0.14956269848965678, 0.14555963833293273, 0.14313460022672747, 0.14831316788656554, 0.1413231105869208, 0.15364407323276316, 0.14908682227496342, 0.14193876318311074, 0.13983541749669945, 0.14730298561620692, 0.1463412705168321, 0.15984378588482195, 0.14314226856893483, 0.14054112115544065, 0.14593384429906206, 0.14563739428047248, 0.13670453733818566, 0.14366718665880396, 0.15360323192312658, 0.14022350117578244, 0.14517047550603643, 0.14701885648543345, 0.1465255444706719, 0.1463960590547243, 0.14326831879049615, 0.14446416685962404, 0.14058087864831342, 0.14058859159893153, 0.1461051186342304, 0.14001333128430668, 0.14424151661513288, 0.1520551223352466, 0.14539235695590236, 0.1462935349798536, 0.1412638309265921, 0.1551202222445731, 0.15416565420767242, 0.15264825710132268, 0.15168939484519467, 0.14964962274044855, 0.13890187220346675, 0.1475511373396609, 0.14658795827708057, 0.15625168783076862, 0.13938138195121202, 0.15554844804353365, 0.14994586317337272, 0.13607754866545962, 0.14508937478183379, 0.1402067511386448, 0.13953713152211944, 0.1381466774679414, 0.14920630953674277, 0.148103629111143, 0.14672532155782897, 0.14613835162344255, 0.14390196667496943, 0.15084638610655626, 0.14884141161515124, 0.15311721816594656, 0.14488954855684383, 0.1540479174186076, 0.1548151661574726, 0.14099896690738958, 0.14485411591161818, 0.14571865780234924, 0.16085917162736124, 0.14648787520738776, 0.16247236311251664, 0.1386277574697323, 0.15299286809961943, 0.1368078111369759, 0.151724818084473, 0.1413278658983899, 0.14223248389800225, 0.15337739929783736, 0.13887140154656072, 0.14448475390483265, 0.14649188130442983, 0.14361022129221265, 0.14867411544893652, 0.14539086492857273, 0.14813897173915194, 0.1483332056706462, 0.14097370788749314, 0.14462608319941306, 0.157788447973074, 0.15274929994295353, 0.13199351950713523, 0.1501049746027388, 0.13974684046842614, 0.160500799929978, 0.13464929929775307, 0.1449572142677948, 0.1355319787804546, 0.14603107085058492, 0.13639021926793296, 0.14376948835950734, 0.15146765223993505, 0.13412292192610867, 0.15041299416442466, 0.14425424892353478, 0.1529007630610451, 0.13582625874341636, 0.14400526395706562, 0.1561198730259159, 0.14361157556486268, 0.1354622003799262, 0.14532764740979065, 0.1592376417279971, 0.1464771472200068, 0.14998517444405132, 0.14790303562052512, 0.14368570134992337, 0.14929034029413663, 0.13672068095972317, 0.1453189866004775, 0.1450173132654928, 0.14344373583549308, 0.15058039835957157, 0.1491292674932988, 0.1467574384442782, 0.1474738789022124, 0.1487477049715878, 0.15335482802647402, 0.14603660585435582, 0.15398492668727237, 0.15213934513184443, 0.14148083673594658, 0.1462839284053125, 0.15062152725169856, 0.13934325732158556, 0.14393053420084556, 0.13520810447467158, 0.14920199316779423, 0.14777248713407304, 0.14254034517821337, 0.14353030052562232, 0.13766306791927765, 0.1439597876709399, 0.1498420004763089, 0.15313608805333057, 0.14462352598140366, 0.1442967464241807, 0.14061891143041005, 0.14595342682313667, 0.13523343083218195, 0.14188420442075586, 0.14078012900770684, 0.1475937155979609, 0.1525344575607217, 0.1413896347932014, 0.15192571522662376, 0.14753519776366714, 0.1472618421617101, 0.14536220657434362, 0.14217093740212727, 0.14746464238505635, 0.13603943670612711, 0.14137174404747171, 0.1424531827219881, 0.14162643111590087, 0.13924628033478856, 0.14369964625672885, 0.14504489073613308, 0.133455443899137, 0.14570913477161238, 0.1463296337787307, 0.14818904634003618, 0.14846220122343654, 0.14699684395996787, 0.13674605569276063, 0.14576799793817963, 0.13889905076355827, 0.14662361750173653, 0.1438077399203659, 0.1410915169651403, 0.14802448139324179, 0.1494668559043544, 0.1446495399157382, 0.14975274486873855, 0.14937002327169424, 0.14636933382573697, 0.14701484115916144, 0.13749107722504433, 0.1478858710624566, 0.149941929784292, 0.13777471114319692, 0.145072771778418, 0.1543927482691856, 0.1478920989325957, 0.14167462662171632, 0.14099855717800724, 0.1520190454638978, 0.14932615665611512, 0.15288424941113904, 0.1448098920745502]]
    [0.14500221332988372, 0.1465775519758017]
    
    # numtests = 25
    lossveclist = [[0.14929165654667872, 0.14476989937850052, 0.1431652370531077, 0.13928342106611927, 0.1481105180784011, 0.13212687778026677, 0.14442471079302682, 0.13833841478566206, 0.1469974403749125, 0.13923903662178377, 0.15033524112510596, 0.13808825812365114, 0.14835561494469526, 0.14370932614462167, 0.14900550389264416, 0.1594141247684239, 0.15002817404556096, 0.14419300974464672, 0.13196189230292646, 0.1413433699645824, 0.14140178226259342, 0.14099649395107589, 0.15111420333905323, 0.15000157523296392, 0.13175776558956634, 0.14969978779296814, 0.14410514416086198, 0.1359384372365681, 0.15144471974910564, 0.14662106516829507, 0.14093461494950923, 0.13770764941949995, 0.14119327136599946, 0.14589409818505128, 0.1415483240811351, 0.1549219334652118, 0.15034259909346834, 0.14827012207484405, 0.14164692560721018, 0.1544305553116642, 0.1491928390393004, 0.15559979751475245, 0.14258834122094993, 0.14296986852182667, 0.14649905524130072, 0.15254756039678108, 0.15994415618051708, 0.14499084459976455, 0.142361037157211, 0.14483198686002724, 0.1439363359491464, 0.1435646665084144, 0.13850829466245396, 0.14000509610712158, 0.14623346131986745, 0.1494516029814126, 0.14271096585860724, 0.14412854107536452, 0.14014322090110787, 0.13869901944959287, 0.14120180041825878, 0.15577993176898547, 0.14384750335642657, 0.14953776719289005, 0.1496455539559311, 0.15463190468940383, 0.13847712989961125, 0.1301319778208169, 0.15075948585318785, 0.1480114773194463, 0.13846833559330723, 0.14615607137923692, 0.1433922132868263, 0.15119142790723186, 0.13372822235925866, 0.1481445323960677, 0.14446450623845872, 0.1409791625130278, 0.15031559537249692, 0.14337754978552933, 0.13802068014956187, 0.14715812160275998, 0.14286161737396558, 0.13133563762479933, 0.13758375320461794, 0.1425282323993351, 0.145782457620783, 0.14544392670868025, 0.14907513684331425, 0.14863366104509992, 0.1402379891501884, 0.14210692849790243, 0.1492940022359748, 0.1419568192175121, 0.13891224989153386, 0.15000915693895966, 0.14622641231890063, 0.1468567758799618, 0.14723284683194357, 0.13357613483749012, 0.13764158814030844, 0.14735460081801072, 0.14531422615885684, 0.1410877137098853, 0.14955123787478963, 0.14437540344691446, 0.13284658244740824, 0.14506270997846582, 0.14850826567854256, 0.1431812775611784, 0.14384481547473815, 0.14481933071076525, 0.1411324580567938, 0.14518137836846626, 0.1525484112933519, 0.1445646452854976, 0.14119171916989187, 0.1422687757335097, 0.1360090523827051, 0.15705082407707682, 0.14231460763162426, 0.13963169850936383, 0.14088083546597316, 0.15037981213249726, 0.14373365537002664, 0.13760437727796623, 0.1412161654145318, 0.1402207045843932, 0.14412346433838347, 0.13359463453108592, 0.15047756683574423, 0.14209775103803768, 0.1362625740662616, 0.1563944457342287, 0.14847731663685376, 0.14397137241023067, 0.13687461576703608, 0.1379214577726269, 0.13617923985624802, 0.14486010097709515, 0.1526769708367333, 0.1468635045935116, 0.14996990070362595, 0.14492669562914967, 0.14476325608750784, 0.14766551304979972, 0.14696367195197488, 0.144349622311492, 0.14253858668335967, 0.14530831251179038, 0.14514381934831846, 0.14434054523518214, 0.13919929437775122, 0.14522206547569413, 0.14946907564379974, 0.15600864287211483, 0.1490853089878084, 0.13700172062940272, 0.14438372484976714, 0.14318696505861334, 0.1458700356471285, 0.13212420873237768, 0.14801545116170292, 0.1422719099034142, 0.14966535082215612, 0.15591858153878294, 0.14091959093259815, 0.15280828387489032, 0.1362580458121587, 0.14407309862937712, 0.14211628118488914, 0.15101677042587183, 0.13446984926089095, 0.13566278029735607, 0.14732295869240544, 0.13238096739962563, 0.14595111862146468, 0.15284797297188266, 0.14480113263006086, 0.13872757379713954, 0.15165438450118296, 0.15367250846318617, 0.1449783010598694, 0.14316322244394122, 0.14130173476162014, 0.13906866715806399, 0.1383184667020811, 0.14318420080485017, 0.14819754722664963, 0.14459417877418518, 0.1431395484933866, 0.13581477948314766, 0.14507803989675816, 0.1446772533684341, 0.13577495874140816, 0.1498714129547766, 0.1439814070775627, 0.1474885465752546, 0.13526797312399708, 0.14835854687608543]]
    [0.14348887516365055, 0.1450987291060949]    
    
    # numtests = 30
    lossveclist = [[0.13779317155584295, 0.1466483229412001, 0.1305914744898823, 0.14045340614824023, 0.1415288119190779, 0.13622826693172774, 0.13497195492286918, 0.13323548235270044, 0.14312149428812063, 0.14291500865837162, 0.15042897011969236, 0.14120716596784838, 0.14654649069730336, 0.13800995296903198, 0.14330110167601498, 0.14144132493087655, 0.1401250762277522, 0.14048598520104155, 0.14748754241512915, 0.14584730638913093, 0.1336649302830056, 0.15254917425553255, 0.1412628591738108, 0.1470766655206707, 0.14347017596625594, 0.14749415889033027, 0.14694741982683768, 0.13628623832006861, 0.14796658418077788, 0.13774407603313452, 0.1461084025628362, 0.13548709707569756, 0.1322126927738884, 0.14142479377598974, 0.1452241088437068, 0.16055691114699636, 0.14626575428980232, 0.14263257007790406, 0.13801386844102606, 0.13805470040801132, 0.14921008933880864, 0.14617886425778334, 0.13405056652257677, 0.13735225246901456, 0.14062359360368815, 0.14338408770294347, 0.14918957098019092, 0.14471604441866012, 0.14144312601091963, 0.14670961056585524, 0.13990286726951082, 0.14802488994081053, 0.1388447644527789, 0.12628770824243543, 0.13768782427618306, 0.14268462982574623, 0.13553030414578043, 0.136279460907096, 0.1498124628394062, 0.13623499597391156, 0.14317104035800904, 0.15199253049685393, 0.13777512046069446, 0.14339038192311643, 0.15358234520845634, 0.15423079652496213, 0.14216248752785446, 0.14203615626237148, 0.1515448868392956, 0.1451641014065573, 0.14576450185377826, 0.14767487578752908, 0.13619020865916018, 0.14923488856213302, 0.13824121032854436, 0.14276491320070517, 0.15231190931636698, 0.14396177784850336, 0.14129487729081874, 0.15032541741836966, 0.14782358097425924, 0.14509833304493824, 0.13084363293423165, 0.1490341011948041, 0.1363701117742744, 0.13797400064827425, 0.15064662645327168, 0.1422930919701152, 0.1466355359565519, 0.1482262722141571, 0.14176438935859742, 0.13823162599661654, 0.13902096656587565, 0.1537213606140614, 0.1507645635158129, 0.1394960475280321, 0.14610951011866696, 0.14683566640377324, 0.1350795319697564, 0.1429049875468854, 0.14425414575592294, 0.14706421912952977, 0.13995027338213192, 0.13311598568460895, 0.13763822398602318, 0.14252239438073366, 0.13930370816934687, 0.1301198796956489, 0.14246752449592698, 0.1443933013958118, 0.14037156908575618, 0.15681384208750995, 0.14233272568617852, 0.14337970603672623, 0.14092634556200273, 0.14855847313410575, 0.14033875082552627, 0.14219461728532623, 0.13684301737873666, 0.15159051439464025, 0.14688820055003549, 0.1478724634831737, 0.1361931946565252, 0.14080057740470323, 0.14131805051260463, 0.14416044493572047, 0.14289888462215977, 0.13779572304640297, 0.1452160127260369, 0.1386947493192966, 0.14717006256654538, 0.14213833695315076, 0.15280921895586305, 0.14122714114153803, 0.14798486324394122, 0.1253460325347753, 0.13319603024607746, 0.13788783421453105, 0.14930481973085982, 0.14297397672335596, 0.15499433500025772, 0.14978042701777136, 0.14902742041087935, 0.147606410106089, 0.15863409466233874, 0.14789587841453186, 0.15083050667148976, 0.15096974570837454, 0.14826129081992034, 0.1397727509926425, 0.14102462960123693, 0.13243942361009287, 0.1372346938539054, 0.14218301484177048, 0.1421487613286172, 0.14821577624409576, 0.14325664838541502, 0.14071650100008148, 0.14072223192813418, 0.1378971885132875, 0.15850622201939232, 0.1352645954511013, 0.144967839510987, 0.13614364047358835, 0.15545221706706067, 0.14934081035557115, 0.13989445180391163, 0.14799588888712795, 0.13381807056677292, 0.15181562864218967, 0.1257000263321256, 0.13993634806612892, 0.14020484389713717, 0.14572540522994032, 0.1519304777144703, 0.1434346206614827, 0.13307424067905316, 0.13728972479839868, 0.13705230913880984, 0.1362257918337577, 0.1404684252856191, 0.1340398040393584, 0.15331534569173727, 0.14173303188631228, 0.1545865837431348, 0.14607086054341484, 0.1391204365707075, 0.14301432325537278, 0.14273719131465015, 0.14303334859184433, 0.1436538883542519, 0.13927254242918996, 0.14331809213518512, 0.14760577861266333, 0.13699554440346723, 0.1458494414048793, 0.14484836262546916, 0.1376073063573045, 0.14782388132792662, 0.1414458642792053]]
    [0.14207702112839923, 0.1438092622782047]
    
    # numtests = 35
    lossveclist = [[0.1391762774455899, 0.13264671779963996, 0.14243992663528235, 0.13618781259122667, 0.14580214236327796, 0.14610593419155204, 0.12775263297698142, 0.13291018728092824, 0.14422878336037623, 0.13907971576111622, 0.14086552274591072, 0.12965041928336524, 0.1337899732006856, 0.1343957954738571, 0.1410105280588572, 0.1404404855559816, 0.14930745948638366, 0.1616301455540161, 0.129559918133873, 0.13305861268209185, 0.14521323078301257, 0.1536761845463573, 0.14269551934698127, 0.15391426733858973, 0.14089071392623995, 0.15100018376359342, 0.14825971553200082, 0.13768223260365747, 0.13733929319778004, 0.1445886431094892, 0.14609521549378096, 0.13064338209935217, 0.1377871216806365, 0.141752120375042, 0.14899569210787073, 0.15225236244216475, 0.14074937670678345, 0.13879624979712382, 0.13821462093585435, 0.14076470253115622, 0.14608714832074407, 0.13815409448495994, 0.13753097411729348, 0.13803632423646978, 0.16315072676632833, 0.14640667941890362, 0.13874070052199666, 0.136036542360735, 0.14857111633431538, 0.13890342833592356, 0.13969696992214867, 0.1397384677616832, 0.13277841111494632, 0.13524498856616168, 0.14755298881306192, 0.13649462323179604, 0.13133850795263816, 0.1539899851127854, 0.14246411669612663, 0.13094734387387694, 0.1489486317212698, 0.13737639559321993, 0.1318019966573981, 0.13683682183422233, 0.14181369927842702, 0.13673912433342644, 0.13495898174848625, 0.14058552095733926, 0.14635714798374774, 0.13763503317770062, 0.1360938888335275, 0.14175674425386223, 0.13005145718343267, 0.15449261682283733, 0.14152793417078616, 0.14164117811471644, 0.15529178042523506, 0.13953454575537894, 0.13630892289205546, 0.1540750738653636, 0.1358677970576752, 0.13243091913427948, 0.13958784111394537, 0.15009663788493458, 0.14107365264833932, 0.14168421061414654, 0.1393965020072669, 0.13312516912606273, 0.14535323687437537, 0.13663510439671864, 0.13185141067445197, 0.12796220196948185, 0.13929524907710525, 0.1330997437728412, 0.1425828975306007, 0.14354281288518195, 0.13311365386942342, 0.13792743610631647, 0.13753956902639614, 0.14410487397631566, 0.13083161202174318, 0.13934340104556983, 0.13526048526010537, 0.14090795887798815, 0.13578340866508837, 0.14996892214955035, 0.13335710655013802, 0.14046520762959386, 0.15590150870895836, 0.14501322937423866, 0.13688587213616643, 0.143092089097864, 0.12998145189710872, 0.13456057350398506, 0.13758043650351362, 0.14409095498412244, 0.14227260957680854, 0.13958004727004084, 0.13320855693561667, 0.14887158897887304, 0.13659424500812017, 0.13568495191408464, 0.1354854454739415, 0.1503817289822854, 0.14017461844195844, 0.14814669378333964, 0.13940214477283228, 0.12705583651949973, 0.1493631009372235, 0.13189564624052463, 0.1362073628604805, 0.13248424457092559, 0.14123738001357616, 0.1411232517235755, 0.1407379679535181, 0.1357982878019421, 0.13161175611944237, 0.1398737012663519, 0.1426576839055006, 0.13559460820092398, 0.14817603783859778, 0.1438585543042762, 0.14716994930900243, 0.13908029689168974, 0.14163137988998675, 0.1328318835922843, 0.13960394529540174, 0.14607241624214998, 0.14770321275902976, 0.14550112186811825, 0.13795376906752088, 0.13295669457283907, 0.14005302476798365, 0.1519948870404687, 0.14241800038050778, 0.15616064021204984, 0.14565418403489155, 0.14333961439484594, 0.14756533661191554, 0.14270858092240168, 0.14545752272964566, 0.13938477615471234, 0.14638536258634852, 0.14371377725763856, 0.14275653928428197, 0.14401770347828594, 0.1377798828688195, 0.14328916166120925, 0.13065409197307162, 0.15031396159639843, 0.13148603002872383, 0.1380738878583802, 0.14095921437941308, 0.13772995227478496, 0.14281924778853627, 0.13889192110928741, 0.14443880827941266, 0.13553622934950676, 0.14354101169673475, 0.14073183114705837, 0.14526535349586878, 0.1409372306436658, 0.1469012364041062, 0.1497646143022559, 0.1641668364319192, 0.1396301298215819, 0.1428449374033816, 0.14142042498360072, 0.13842246599198316, 0.13224883784092176, 0.14481325632208944, 0.13805044358737636, 0.1455682251781399, 0.1346717389354257, 0.1318468931606976, 0.13981867396387718, 0.15358637991492713, 0.1348787375674782, 0.1462652471002303, 0.14328813539697563]]
    [0.139945146958225, 0.14182049595968985]
    
    # numtests = 40
    lossveclist = [[0.14923328560431817, 0.14094086026241218, 0.14423356196433082, 0.13030774067034884, 0.13492453624631637, 0.14619328533541556, 0.14106742088799, 0.14188541594910636, 0.14426281868512356, 0.13891021917477997, 0.13675473401987595, 0.1362817656416003, 0.1410106285855479, 0.15181295207832057, 0.1399654499155807, 0.14039654427888326, 0.13912367817224155, 0.13346226399072908, 0.1602012574935667, 0.13948190843073507, 0.1379359119754444, 0.1493148714246625, 0.1339093752348592, 0.14726530165635557, 0.1496696040648137, 0.1384360398897158, 0.13038878841213308, 0.1284213002472483, 0.13517464000085624, 0.14446501775998466, 0.1443563246387758, 0.12395173168130082, 0.12970828180018262, 0.12958649149559937, 0.1370798464455842, 0.13659273001841732, 0.13984082312267798, 0.13244188681721067, 0.13803919719505928, 0.1460306856411136, 0.13698433820821393, 0.14367943470085498, 0.13620902001067348, 0.14242279617844286, 0.13633531350259295, 0.13409406987361244, 0.14410732673957183, 0.12562101410365412, 0.127951614927966, 0.1382430075104935, 0.134149534459074, 0.13079379222726426, 0.1290298972117456, 0.1300870052354584, 0.13716674706332363, 0.14391373268444577, 0.1488081978037174, 0.14614457436176373, 0.144628427117606, 0.1349189505839391, 0.14079049183159315, 0.1436821465616919, 0.15296840194912978, 0.13813358734381853, 0.13945081024128586, 0.1479112715478527, 0.14453069564669985, 0.1383301868988603, 0.13545959515788503, 0.1437965692942241, 0.14132551312934297, 0.13587604288880584, 0.13519814698882787, 0.13763486225418484, 0.13794683844856406, 0.1412064583852822, 0.13846850141835212, 0.14692665398165025, 0.13716557455260445, 0.14464137999095195, 0.14537481674628622, 0.13414287929619484, 0.12367003042090521, 0.1352939471943121, 0.1282226047551616, 0.13754781933719917, 0.13705174516730664, 0.14886601338132857, 0.14061789990656895, 0.153037265464442, 0.1289526518718766, 0.1471663089319128, 0.1444408807576999, 0.147087378262655, 0.13332706052045298, 0.13416413660364654, 0.13293429730771086, 0.14772212346946345, 0.12824165130555756, 0.13469356369756158, 0.1444809462861017, 0.14157881803287942, 0.14659180974292868, 0.14364706940137417, 0.1573128380677149, 0.1536156491398544, 0.1421756488209304, 0.14049937624784667, 0.13107871213167122, 0.13482672181799332, 0.13260591185334503, 0.13231037392992037, 0.13644782010547654, 0.1526207589980754, 0.13917610913001296, 0.14233307425902805, 0.1362641611150689, 0.1362641611150689, 0.14311166031136044, 0.13617550231528616, 0.13096528868037588, 0.13635339720551218, 0.132767310274018, 0.13955887139473924, 0.14475439621827227, 0.13540584050522878, 0.13939129451128132, 0.14483056165084954, 0.13742614695377736, 0.1430718818679417, 0.1475164695438944, 0.13960389830205597, 0.14113619803635663, 0.13649777706898755, 0.1366857545094388, 0.14923232525964159, 0.14916415597103505, 0.14193905564389628, 0.14952199551609935, 0.13626866326827125, 0.14114637656125661, 0.13830039981366707, 0.13377079621224755, 0.13433458157972922, 0.13647522571894644, 0.13347395252243902, 0.13579941185682767, 0.13214268623194964, 0.13760599922053396, 0.13485436504260645, 0.14940834159232264, 0.1397013303789785, 0.1389311317368623, 0.14245787427818823, 0.14962095552699933, 0.14625459838343302, 0.1374313093826791, 0.14267596645476974, 0.1439474372839799, 0.1439241151490966, 0.13954288393231068, 0.1254037682915729, 0.1337024618052971, 0.1473878986226828, 0.14844403741221615, 0.13713008911238622, 0.12992102212044815, 0.14264915673047132, 0.12536380463970936, 0.13212797941213603, 0.15430503118894529, 0.13470464763885098, 0.1308922665676316, 0.14108979373786917, 0.13335498481490596, 0.15550082971397006, 0.13137669453557654, 0.14004793869112095, 0.1453773522296514, 0.1358613783224697, 0.12803824652213244, 0.1305913220766541, 0.13137859701273363, 0.13987664267050867, 0.1335058246361434, 0.14677556598183034, 0.1473810060084061, 0.1387408856251272, 0.13260720266368037, 0.1438673372681265, 0.13156656468065844, 0.1437039653779034, 0.13945917700617447, 0.1577877348925145, 0.14574739995057376, 0.1348175357625629, 0.13886046590666945, 0.13678530057641428, 0.13696221032646672, 0.13463178872408385]]
    [0.1384348150074832, 0.1403359932689587]
    
    # numtests = 45
    lossveclist = [[0.13607454444122516, 0.133750568830303, 0.1316333707431736, 0.13316176005912952, 0.14169600017470088, 0.1372069920822581, 0.13860990489061842, 0.13628793239390602, 0.15157336486068973, 0.12911197159223498, 0.1360792338196829, 0.13661275686607494, 0.1374061907864016, 0.13578736996426166, 0.13645104913750397, 0.14861486661210518, 0.1362460470806112, 0.13268817141744987, 0.14899218792332297, 0.12953245471416502, 0.1354194320178475, 0.13820926690465735, 0.14628161762529465, 0.14109404231565928, 0.14057161099888082, 0.15104588330254307, 0.1422223714461876, 0.13723680134300786, 0.14012591115771286, 0.137284391854731, 0.13805435775661115, 0.13334087598732267, 0.1436773545297151, 0.134761725065622, 0.1375413391187424, 0.1373227756874088, 0.134946056184705, 0.1302822834586717, 0.13453334534522063, 0.14070873149264532, 0.15073314669853002, 0.15075422481108441, 0.140287049953665, 0.13082259878106514, 0.13656560816332203, 0.14194942736636304, 0.14689403000420131, 0.16566254991969523, 0.13780995141190802, 0.13960582927546064, 0.1336217371038833, 0.13417331354119114, 0.1369783952998494, 0.13992640909045098, 0.12423565546992613, 0.1382999992401276, 0.130955512533517, 0.14538466884293336, 0.14404043489689367, 0.13672043300168624, 0.14225097264407224, 0.1386824241330546, 0.128282785498405, 0.14618312999808059, 0.14270740862490833, 0.14249580174202822, 0.12330728894782976, 0.1435217885983476, 0.14635474018498623, 0.1384860601122512, 0.13168807243532502, 0.13809827356001356, 0.138997493607717, 0.1351499592412427, 0.13418574410810047, 0.13834164036206598, 0.14130792845423668, 0.13061740991384438, 0.1330726880649435, 0.13103336670736937, 0.12825844348170268, 0.1467095976216857, 0.12983340101548252, 0.13558832521821423, 0.1408203377903446, 0.13965204370876366, 0.14593381907801928, 0.12848334026616032, 0.1438249302978484, 0.14513580365748086, 0.13442301674811738, 0.12843148667405402, 0.13521795994230248, 0.13547213237637007, 0.13980964533267373, 0.13437982131979417, 0.13405906067622433, 0.13439877159598557, 0.13649397431489926, 0.13701997960877565, 0.1383694393165889, 0.13602685553422028, 0.1326212068084077, 0.12834057639414506, 0.1295475292414255, 0.14081727557932183, 0.12726789123663013, 0.13538130505277732, 0.1473524334737119, 0.1462830824818178, 0.13528765885496966, 0.17085736519486744, 0.1416377895343577, 0.13783823039133736, 0.14132877352551457, 0.14423589338066023, 0.13302661782191877, 0.14455800364546662, 0.12906723197381345, 0.14865309137476296, 0.1473817053613943, 0.1414560836226565, 0.13572476977943887, 0.140958932969139, 0.13332205827947619, 0.14236949610627117, 0.14789297350910802, 0.12440631092023911, 0.14514940232349224, 0.14193465679395487, 0.15127052026791005, 0.15293165883134646, 0.1489022988155383, 0.14002323927357616, 0.14198375193079538, 0.13898412714418343, 0.13208883184294232, 0.13941765865361438, 0.14431936176957205, 0.14147899674320172, 0.13254479413434145, 0.15092203760893927, 0.14759601659084648, 0.14553036666944147, 0.12441390937516324, 0.14293404614221197, 0.14710865429597597, 0.13707589442269671, 0.13960513620523948, 0.141863525576503, 0.1492511027579569, 0.13871235983137672, 0.14754055623161919, 0.13215166554060115, 0.13463155335342972, 0.14188257290413125, 0.1564772572375866, 0.14048738023160032, 0.13815872313130592, 0.13896233560606622, 0.1392227907437793, 0.13767385819730735, 0.1408771691136243, 0.13703669939437366, 0.1456784840273687, 0.14837151357013187, 0.1288249970473656, 0.1426703878211193, 0.12603690189343958, 0.1363048094925155, 0.13813471604964536, 0.13942932940283495, 0.12930909971237042, 0.1336608611232914, 0.13629168205104394, 0.13139661983635134, 0.14348211913454742, 0.1357519088486372, 0.1345755075223913, 0.1223988033881791, 0.1588806085791979, 0.14599781163133363, 0.14462313438093952, 0.13472099580426794, 0.13828072022117188, 0.13522193706872496, 0.1330560316569927, 0.1401199216737999, 0.1306193777789655, 0.13930272156006937, 0.1385699137677469, 0.130777929603073, 0.14257563824209726, 0.1413177931717767, 0.13279477279336943, 0.13698551756087582, 0.1414068265742274, 0.13379838571402333, 0.1411397426391024, 0.13739790968212898]]
    [0.13781609257460764, 0.13977760419667512]
    
    # numtests = 50
    lossveclist = [[0.12896503769883522, 0.1363571855265304, 0.1396810542534607, 0.15147895479315404, 0.14634672026150136, 0.13436576322595328, 0.13254703147549032, 0.12867810564428017, 0.14022234303333966, 0.13601957818329424, 0.14052703859400106, 0.1291924121063265, 0.13805985431745146, 0.13751494172626386, 0.12614880759715227, 0.13859278154248045, 0.1430991624030021, 0.14410217778914736, 0.131174267703647, 0.12464043548949001, 0.14157410305003607, 0.14178942434045383, 0.1425256211094955, 0.15082375405734647, 0.1516384912200797, 0.1358954414075092, 0.14073577540372653, 0.1302420117038025, 0.14268807394802657, 0.1422750193577662, 0.14040745709975538, 0.13052244880336283, 0.13195931121011711, 0.15234748938178325, 0.14727190757393022, 0.14099262297493384, 0.1297786426473996, 0.13715881581253814, 0.13285513256885406, 0.14593928396702086, 0.14311633218207342, 0.15544523733629387, 0.13168705440437778, 0.12853209950634917, 0.14138032052030763, 0.1384717688128257, 0.15054913902730058, 0.13486933737359405, 0.14160685405075485, 0.13928217410257196, 0.13694371596555036, 0.13498758290993337, 0.13308225990864625, 0.13442902386452052, 0.13425594109251068, 0.139558130271446, 0.13685182913730878, 0.14231959440840306, 0.13891659565426984, 0.1291416677938113, 0.13083835772044908, 0.1380877745978223, 0.13180998893017443, 0.13733092754997311, 0.1527637283845932, 0.15070990560171055, 0.12817525709133049, 0.13573258706084693, 0.1453198201070054, 0.1487337473613717, 0.12743024254527782, 0.13970730182537944, 0.13769752147846592, 0.144053013775322, 0.13272621677742005, 0.1354189693601303, 0.1459918001707142, 0.13828907814947874, 0.13424569634171785, 0.14069915089308666, 0.13771180551271034, 0.14412131058934474, 0.13806191000472495, 0.13655021538665435, 0.13557629342455071, 0.12466652998018422, 0.14197321721880046, 0.13407654572566083, 0.15256229729418258, 0.14279867147838657, 0.13121715159241162, 0.13561808412319473, 0.12869593383071015, 0.13469244237522274, 0.13670235066179828, 0.127220355493529, 0.14706852730125552, 0.13768055275874144, 0.13567165025997205, 0.13473642834222097, 0.13197451818404013, 0.13013342251800086, 0.14139493206907147, 0.1350310693093406, 0.12904648298875887, 0.13708228577809378, 0.12659518535732628, 0.1430563246387694, 0.12659518535732628, 0.13848614217067454, 0.13302838000038597, 0.14119046040991737, 0.13836170651156593, 0.1361491162910469, 0.13793879298305448, 0.13651747347037968, 0.14217760038283178, 0.1465189198136137, 0.1313938467517028, 0.1311224289521011, 0.13753266694201507, 0.14107106242530665, 0.1339411377216011, 0.14606159166805155, 0.14449390077429464, 0.13663908219960674, 0.13763051961854655, 0.12731993602953554, 0.14086460832955106, 0.1379355262867124, 0.1397758742861277, 0.13970739448058989, 0.1371668506591707, 0.15121783099964123, 0.14670890443025508, 0.13168041834723287, 0.12803262314377084, 0.12968543747867706, 0.12774475674408325, 0.12571558852380524, 0.141035733821152, 0.13603430603246064, 0.1441226620994775, 0.1418129486351037, 0.13931426481058864, 0.14712980330772135, 0.151199893938582, 0.14537651594018552, 0.13788767872719643, 0.13848237243988654, 0.15109332048583823, 0.1379234321865378, 0.1384706058471915, 0.1403811238450625, 0.135206568344619, 0.14773033113394202, 0.13885749706275805, 0.15098774023757378, 0.13531330606628958, 0.12782212934264883, 0.14641035885926246, 0.1463961097100439, 0.14649586553691463, 0.13162820861899382, 0.1483671721944478, 0.14401288520485522, 0.1329136567914102, 0.13880925742762176, 0.14049679135998586, 0.14416084439289328, 0.1278539612600553, 0.1368922851284948, 0.13438136816668564, 0.14898104831286696, 0.14777777071864134, 0.1496586797802787, 0.13463812101405556, 0.13888662424399167, 0.1360441759786969, 0.1329228201392481, 0.14827099815332287, 0.13280700096773682, 0.135517911679232, 0.1397968729050755, 0.14366584389509404, 0.13900839888271035, 0.13674365922379728, 0.13736398828126878, 0.1484218264695349, 0.13976752833285314, 0.13971647881545818, 0.13811394344698386, 0.13888146434422707, 0.13270220002577066, 0.14492287622508143, 0.14124646200528115, 0.1307159372101115, 0.12757078906519714, 0.12966396799025698, 0.14456757434440948]]
    [0.1374408776994462, 0.13929732674891734]
    
    mcmcexp_lo = [0.16021197670665502, 0.15016267023404384, 0.14764479788349866, 0.14500221332988372, 0.14348887516365055,  0.14207702112839923, 0.139945146958225, 0.1384348150074832]
    mcmcexp_hi = [0.16158723848900422, 0.15167878274470148, 0.14924724829468644, 0.1465775519758017, 0.1450987291060949, 0.1438092622782047, 0.14182049595968985, 0.1403359932689587]
    
    # FOR GENERATING 95% INTERVAL ON LOSS
    CIalpha = 0.05
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist: # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (mn-intval)
        hiperc = (mn+intval)
        print('['+str(loperc)+', '+str(hiperc)+']')
    
    
    # APPROX; sampling draws from 400000 NON-UNIQUE MCMC draws, in [100,250,1000,10000,40000,80000,150000]
    # numtests in range(31)
    
    draws100 = [0.14186260283731253, 0.14955340646680668, 0.1581570807646787, 0.15626291495733963, 0.1530313758663306, 0.1761648649956917, 0.1665808864498618, 0.1632719126001704, 0.16734427743376862, 0.16951959932264013, 0.15458239857560685, 0.16384980405071115, 0.16718052231571087, 0.15524784436840006, 0.1718097196615604, 0.16624415388333005, 0.15814339204240416, 0.15558054613829564, 0.1382255566883434, 0.15485233554391267, 0.1551977377270231, 0.13647779536416518, 0.195645271701333, 0.14643317894378888, 0.08999750831434764, 0.10869190278110134, 0.22069369430237637, 0.13267689548834696, 0.10153456648042218, 0.1475554314624782, 0.12920772229474795]
    draws250 = [0.15145794295807097, 0.1625489346849844, 0.16090753228646448, 0.16725187482385473, 0.1705320347363724, 0.15454370013903224, 0.17499181518515014, 0.1817445467903465, 0.1579639847126176, 0.17698880931205332, 0.16611025618935651, 0.1853130548680134, 0.17252366287223145, 0.17052637297152495, 0.17764245891221309, 0.18375785906090925, 0.15604418761175146, 0.17690433962169777, 0.15332665267710238, 0.15580671533003013, 0.17286335343717732, 0.16027805208798404, 0.1258161018621254, 0.15961372538803403, 0.18805221754737447, 0.14674834287417227, 0.13341362424620173, 0.032775378083841344, 0.18396037541802812, 0.15855303541690194, 0.15441723410609967]
    draws1000 = [0.15804464954025157, 0.15878266199209765, 0.16016690997740363, 0.16517241974004165, 0.15763346827049385, 0.16467872683462736, 0.1658031095269363, 0.16411231933918596, 0.1717276088240643, 0.16833863901853854, 0.17870020902260253, 0.16553883063453834, 0.1797096891423593, 0.16990284920051898, 0.1784786810487418, 0.18836694143682142, 0.1747780568817911, 0.18542532539991274, 0.17130041174126964, 0.18086234773594193, 0.16464066035939282, 0.161535057954879, 0.14699060751796206, 0.15251030931495901, 0.06565260408008507, 0.12328173109904503, 0.08384702728421228, 0.10755022515015063, 0.11399446045282732, 0.11904016402686572, 0.0067184173959996705]
    draws10000 = [0.16131598003961287, 0.16138220371547865, 0.16417685819121172, 0.16434932592842844, 0.1643435078775151, 0.16714215188907489, 0.16861407782629106, 0.1687736795767924, 0.169372975086357, 0.17050065349664636, 0.17296988565107294, 0.17672390931335769, 0.17598734396249616, 0.17994672407259482, 0.1787614900334264, 0.17859610947743626, 0.1795780452496487, 0.17460958418832706, 0.17337858485396018, 0.17654188157031409, 0.174391685229564, 0.1664918890778, 0.18745336967189827, 0.15689394802838452, 0.13250269063686418, 0.1426409905303931, 0.15682886354005762, 0.15530521413329298, 0.14157192228002197, 0.1414201132947558, 0.10666767221523182]
    draws40000 = [0.1606836993114933, 0.16207526003326908, 0.16321927372574024, 0.16372215738551626, 0.16507991658419763, 0.16682818677928837, 0.16715127916180164, 0.16893888795950743, 0.17047949787543892, 0.17174592615826134, 0.17362801617228307, 0.1748462070648831, 0.1761090532286745, 0.17604102263492136, 0.17601704175928243, 0.1782907979640329, 0.18294146925243193, 0.18484582150599738, 0.17992509248599492, 0.1866661518988352, 0.1794259813334131, 0.17612100170491077, 0.17744921769124414, 0.1675505381565602, 0.1947127349388776, 0.15212548700343723, 0.17239954958919101, 0.12697556082556402, 0.15095554112957416, 0.18414293923186267, 0.13127636913669563]
    draws80000 = [0.16099707502505783, 0.16166801601322126, 0.16327298362415155, 0.16386202577970646, 0.1657232425256403, 0.16622329213065729, 0.16796626677539808, 0.16869865997982122, 0.1706374870784891, 0.1726057787831061, 0.17370867059003817, 0.17488863942016575, 0.17655120454849038, 0.17817514476495114, 0.17720149595924523, 0.17874395279152835, 0.1782442631943459, 0.17771846960779789, 0.18179001777686962, 0.17916343379730876, 0.17834033077737343, 0.17386065461860822, 0.17731323990738496, 0.17111160696544028, 0.1714612271191479, 0.15620465007019432, 0.15843265326011796, 0.1471562372064509, 0.15604734986391758, 0.1804718707960711, 0.1451176290366939]
    draws150000 = [0.16102582573911103, 0.16191797489054832, 0.1628241487965926, 0.16416869162886674, 0.16527663998985048, 0.1665171439106238, 0.1677920344957979, 0.1693061922481328, 0.1705631175552832, 0.17171858692176262, 0.17311600426078877, 0.17479849792807403, 0.17603354288586037, 0.17680469062452178, 0.17802915419011955, 0.17932589776175623, 0.18136148790383344, 0.1808446386553556, 0.18029933239645637, 0.180108582028049, 0.17684293355366543, 0.17447830301233008, 0.17869579696446236, 0.16783253083645625, 0.16857530247486852, 0.16723646376310464, 0.15204049643287745, 0.14327002082880813, 0.1445944467091393, 0.15008480524519205, 0.15730376386799713]
    
    
    '''

    # Plot
    intlist = [5,10,15,20,25]
    plt.plot(intlist, lossvec_lo, color='black', linewidth=3, label='MCMC 90% interval - high')
    plt.plot(intlist, lossvec_hi, color='black', linewidth=3, label='MCMC 90% interval - low')
    plt.plot(intlist, wts10, 'r--', linewidth=0.5,label='Alternate: $|\Gamma|=10,000$') # Using weights
    for lst in [wts10_2, wts10_3, wts10_4, wts10_5, wts10_6, wts10_7, wts10_8, wts10_9, wts10_10, wts10_11,
                wts10_12, wts10_13, wts10_14, wts10_15, wts10_16, wts10_17, wts10_18, wts10_19, wts10_20]:
        plt.plot(intlist, lst, 'r--', linewidth=0.5)  # Using weights
    plt.plot(intlist, wts50, 'g--', linewidth=0.5,label='Alternate: $|\Gamma|=50,000$') # Using weights
    for lst in [wts50_2, wts50_3, wts50_4, wts50_5, wts50_6, wts50_7, wts50_8, wts50_9, wts50_10, wts50_11,
                wts50_12, wts50_13, wts50_14, wts50_15, wts50_16, wts50_17, wts50_18, wts50_19, wts50_20]:
        plt.plot(intlist, lst, 'g--', linewidth=0.5)  # Using weights
    plt.plot(intlist, wts200, 'b--', linewidth=0.5, label='Alternate: $|\Gamma|=200,000$')  # Using weights
    for lst in [wts200_2, wts200_3, wts200_4, wts200_5, wts200_6, wts200_7, wts200_8, wts200_9, wts200_10, wts200_11,
                wts200_12, wts200_13, wts200_14, wts200_15, wts200_16, wts200_17, wts200_18, wts200_19, wts200_20]:
        plt.plot(intlist, lst, 'b--', linewidth=0.5)  # Using weights
    plt.ylim(0.135, 0.161)
    plt.xlabel('Batch size', fontsize=12)
    plt.ylabel('Loss estimate', fontsize=12)
    plt.suptitle('Loss estimate vs. Batch size', fontsize=16)
    plt.legend(loc='lower left')
    plt.show()
    plt.close()

    return

def EvalAlgTiming():
    '''
    Script for evaluating the time for running getDesignUtility under the standard MCMC and approximation routines
    '''
    numTN, numSN = 3, 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5, 0.05, 0.1, 0.08, 0.02]

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked', randSeed=86, trueRates=trueSFPrates)
    exampleDict[
        'diagSens'] = s  # bug from older version of logistigate that doesn't affect the data but reports s,r=0.9,0.99
    exampleDict['diagSpec'] = r
    # Update dictionary with needed summary vectors
    exampleDict = util.GetVectorForms(exampleDict)
    # Populate N and Y with numbers from paper example
    exampleDict['N'] = np.array([[6, 11], [12, 6], [2, 13]])
    exampleDict['Y'] = np.array([[3, 0], [6, 0], [0, 0]])
    # Add a prior
    exampleDict['prior'] = methods.prior_normal()
    exampleDict['numPostSamples'] = 10000
    exampleDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    exampleDict['importerNum'] = numSN
    exampleDict['outletNum'] = numTN

    # Store the sourcing probability matrix; assume Q is known, but it could be estimated otherwise
    # Q = exampleDict['transMat']

    # Summarize the data results
    # N_init = exampleDict['N']
    # Y_init = exampleDict['Y']

    # Generate posterior draws
    exampleDict = methods.GeneratePostSamples(exampleDict)

    import pickle
    import os
    import time

    # Different designs; they take matrix form as the traces can be selected directly
    testdesign1 = np.array([[1 / 3, 0.], [1 / 3, 1 / 3], [0., 0.]])
    testdesign2 = np.array([[0., 0.], [1/2, 1/2], [0., 0.]])

    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [testdesign1]
    designNames = ['Test Design']
    numtests = 10
    omeganum = 100
    random.seed(36)
    randinds = random.sample(range(0, len(exampleDict['postSamples'])), omeganum)

    mcmcstart = time.time()
    lossvec_mcmc = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'],
                                   randinds=randinds, method = 'MCMC')[0]
    mcmcsecs = time.time()-mcmcstart

    approxstart = time.time()
    lossvec_approx = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'],
                                   randinds=randinds, method='approx')[0]
    approxsecs = time.time() - approxstart

    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))

    mn_mcmc = np.mean(lossvec_mcmc)
    sd_mcmc = np.std(lossvec_mcmc)
    intval_mcmc = z * sd_mcmc / np.sqrt(len(lossvec_mcmc))
    loint_mcmc, hiint_mcmc = mn_mcmc - intval_mcmc, mn_mcmc + intval_mcmc

    mn_approx = np.mean(lossvec_approx)
    sd_approx = np.std(lossvec_approx)
    intval_approx = z * sd_approx / np.sqrt(len(lossvec_approx))
    loint_approx, hiint_approx = mn_approx - intval_approx, mn_approx + intval_approx

    print('MCMC time: '+ str(mcmcsecs))
    print('approx time: '+ str(approxsecs))
    print(str(loint_mcmc)+', ' + str(hiint_mcmc))
    print(str(loint_approx) + ', ' + str(hiint_approx))


    '''
    TESTDESIGN1, USING NTILDE,YTILDE
    numtests=30:    0.1266, 0.1336
                    0.1511, 0.1539
    mcmc_secs: 805.2s
    approx_secs: 8.9s
                  
    numtests=5:     0.1500, 0.1551
                    0.1490, 0.1494
    mcmc_secs: 3474.2s
    approx_secs: 38.0s
    
    numtests=0:     0.1593, 0.1608
                    0.1514, 0.1514
    mcmc_secs: 5050.7s
    approx_secs: 39.8s
    
    TESTDESIGN2
    numtests=30:    0.1288, 0.1363
                    0.1423, 0.1440
    
    TESTDESIGN1, USING NOMEGA,YOMEGA
    numtests=30:    0.1560, 0.1595
    approx_secs: 8.1s
                  
    numtests=5:     0.1425, 0.1433
    approx_secs: s
    
    numtests=0:     0.1420, 0.1514
    approx_secs: 39.8s
    
    TESTDESIGN1, USING NTILDE,YTILDE W/ LOG-LIKE RATHER THAN LOG-POST; NUMPOSTSAMPLES=1,000
    (MCMClo,MCMChi)
    (approxlo,approxhi)
    numtests=30:        0.1249, 0.1317
                        0.1496, 0.1520
    MCMC time:      877.6s
    approx time:      7.0s
                  
    numtests=5:         0.1486, 0.1541
                        0.1498, 0.1502
    MCMC time:      783.0s
    approx time:      7.0s
    
    numtests=0:     0.1592, 0.1610
                    0.1603, 0.1603    
    mcmc_secs:      
    approx_secs:    6.1s
    
    TESTDESIGN1, USING NTILDE,YTILDE W/ LOG-LIKE; NUMPOSTSAMPLES=10,000
    (MCMClo,MCMChi)
    (approxlo,approxhi)
    numtests=30:        0.1261, 0.1411
                        0.1552, 0.1581
    MCMC time:      0.0s
    approx time:      0.0s
                  
    numtests=10:        0.1456, 0.1525
                        0.1556, 0.1564
    MCMC time:      1949.4s
    approx time:      60.7s
    
    numtests=5:         0.1498, 0.1552
                        0.1567, 0.1572
    MCMC time:      1949.4s
    approx time:      60.7s
    
    numtests=0:     0.1604, 0.1609
                    0.1608, 0.1608    
    MCMC time: 4935.137982368469
    approx time: 72.35974860191345
    '''

def bayesianexample():
    '''
    Use paper example to find the utility from different sampling designs; in this case, we can choose the full trace,
    i.e., we can choose the test node and supply node .
    '''
    # Designate number of test and supply nodes
    numTN, numSN = 3, 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5,0.05,0.1,0.08,0.02]

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked',randSeed=86,trueRates=trueSFPrates)
    exampleDict['diagSens'] = s # bug from older version of logistigate that doesn't affect the data but reports s,r=0.9,0.99
    exampleDict['diagSpec'] = r
    # Update dictionary with needed summary vectors
    exampleDict = util.GetVectorForms(exampleDict)
    # Populate N and Y with numbers from paper example
    exampleDict['N'] = np.array([[6, 11], [12, 6], [2, 13]])
    exampleDict['Y'] = np.array([[3, 0], [6, 0], [0, 0]])
    # Add a prior
    exampleDict['prior'] = methods.prior_normal()
    exampleDict['numPostSamples'] = 1000
    exampleDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    exampleDict['importerNum'] = numSN
    exampleDict['outletNum'] = numTN

    # Store the sourcing probability matrix; assume Q is known, but it could be estimated otherwise
    #Q = exampleDict['transMat']

    # Summarize the data results
    #N_init = exampleDict['N']
    #Y_init = exampleDict['Y']

    # Generate posterior draws
    exampleDict = methods.GeneratePostSamples(exampleDict)

    import pickle
    import os

    # Different designs; they take matrix form as the traces can be selected directly
    design0 = np.array([[0., 0.], [0., 0.], [0., 0.]])
    design1 = np.array([[0., 0.], [0., 0.], [1., 0.]])
    design2 = np.array([[1/3, 0.], [1/3, 1/3], [0., 0.]])
    design3 = np.array([[1/3, 0.], [1/3, 0.], [1/3, 0.]])
    design4 = np.array([[0., 0.], [0., 0.], [0., 1.]])
    design5 = np.array([[1/6, 1/6], [1/6, 1/6], [1/6, 1/6]])
    design6_6 = balancedesign(exampleDict['N'],6)
    design6_30 = balancedesign(exampleDict['N'],30)

    ### overEstWt=1, threshold=0.1 ###
    # Get null first
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt':underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec':marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList, designnames=designNames, numtests=numtests,
                               omeganum=omeganum, type=['path'], priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'),'rb')), randinds=randinds)
    plotLossVecs(lossveclist,lvecnames=designNames)
    # APPROXIMATION
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds, method='approx')
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Design 0']
    lossvec = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598]]
    vecSD = np.std(lossvec[0])
    vecmean = np.mean(lossvec[0])
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    intval = z * (vecSD) / np.sqrt(len(lossvec))
    print('['+str(vecmean-intval)+', '+str(vecmean)+', '+str(vecmean+intval)+']')
    # LOSS VECS: 29-AUG-22
    designNames = ['Design 0']
    lossvec = [[0.1631624760638568, 0.15720307855535465, 0.1608639458015167, 0.16447283684593733, 0.1597308858525191, 0.16530244555035933, 0.16669312810707285, 0.16160074117278947, 0.1653192236072529, 0.16204418974476908, 0.15497871429023474, 0.15467411765416555, 0.1613750771551091, 0.15747074496261462, 0.15227562871749936, 0.17145553434981564, 0.16369361082463926, 0.16692521749216743, 0.16203792928496977, 0.1590776035470591, 0.1551749348303539, 0.16082428779764713, 0.15756807299460315, 0.1550608320048446, 0.15631195454060692, 0.15770983060319332, 0.16414686544787604, 0.15488810166410838, 0.15665288807970829, 0.1603004871311405, 0.16244412648327097, 0.15682117281806454, 0.16354500356802104, 0.16415919851377875, 0.15638019764514263, 0.16670011136232835, 0.15949899115009494, 0.1615188645137574, 0.15735859905742092, 0.15677491970077437, 0.1632770477454912, 0.14924291956044927, 0.1574308890174942, 0.16345504155976637, 0.16461700092995968, 0.16393482231407522, 0.1567846630510756, 0.1592431152969494, 0.15772433382534407, 0.14844073064826993, 0.1480748185152451, 0.15995265165098485, 0.15794841277723592, 0.1572413873265836, 0.1622471046539544, 0.16417357970743476, 0.15887070770145548, 0.1564296671429403, 0.1540633086236506, 0.1574801602328406, 0.1636280978407651, 0.1614998685157631, 0.1577330744011513, 0.15305409049467894, 0.16450330767712035, 0.15431738262912842, 0.1704341250563957, 0.15808855691643203, 0.1624660034460682, 0.16984983201379783, 0.16483379350966765, 0.17121651483881745, 0.15037817832139538, 0.15245994964489948, 0.15922731238943802, 0.1591623946701067, 0.1593963075601854, 0.1566343324544281, 0.16163975965273666, 0.16063162964748812, 0.15588301419308162, 0.16196747619948323, 0.16966545510320571, 0.1608916131441504, 0.15122267730328054, 0.1650651247623661, 0.163162013176352, 0.16165030963215343, 0.16726574770151145, 0.16236020655648817, 0.16454285631917326, 0.15453297321044887, 0.15539168550866006, 0.17099218057510968, 0.1600247961031962, 0.15695387350753648, 0.15969570999392832, 0.15967241534002483, 0.15652864332227961, 0.1649838594051987]]
    vecSD = np.std(lossvec[0])
    vecmean = np.mean(lossvec[0])
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    intval = z * (vecSD) / np.sqrt(len(lossvec))
    print('['+str(vecmean-intval)+', '+str(vecmean)+', '+str(vecmean+intval)+']')
    # VIA APPROXIMATION
    lossvec = [0.15265587864150065]
    '''

    # 6 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4,design5,design6_6]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 6
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    #plotLossVecs(lossveclist,lvecnames=designNames)
    # APPROXIMATION
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds, method='approx')
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossvec0 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598]]
    lossveclist = [[0.14509325259013878, 0.14028874836906774, 0.15305064950853794, 0.16164990223848158, 0.14600334611479598, 0.14222540439564113, 0.13819926446274894, 0.14888751519994395, 0.13601042925395454, 0.13705411416940977, 0.15017616990619576, 0.1312379783345067, 0.1399484932259146, 0.13867950539952534, 0.15473940085023505, 0.16492083747756797, 0.15266627729906476, 0.14303711984400314, 0.13944081571793362, 0.1351921195153755, 0.15000995864717762, 0.13785200299246733, 0.13972241307192595, 0.1390171111021526, 0.1741896010859611, 0.1523797619746385, 0.16802109843462054, 0.2031044061496549, 0.13994207470188078, 0.1493886304687554, 0.1421754071608363, 0.14819472020134955, 0.16730339147588053, 0.14273239657853296, 0.13527345028311655, 0.161211796889484, 0.15418280898428968, 0.1660452606865663, 0.16150255257113955, 0.14213185150950894, 0.16426791944900046, 0.14820635833013102, 0.1379348973871464, 0.15140720104735936, 0.15692154621266824, 0.13800025303241972, 0.15247775657441595, 0.1644960062364241, 0.14578730342459145, 0.15137928900502245, 0.15856592647467407, 0.1452533446898607, 0.13957331327211198, 0.16653186540898943, 0.1414586386472211, 0.13863761618792944, 0.15044269753193415, 0.13513057159191263, 0.1504710967707737, 0.14143042379029486, 0.15663931070287654, 0.15513959857473436, 0.14020565695676762, 0.14589390237896285, 0.13989413525049613, 0.13558801438885254, 0.1306796412110928, 0.1454250416842359, 0.20039562872768904, 0.1464782403034093, 0.13988968170112726, 0.13273908598086082, 0.15927546532370224, 0.1489380419506682, 0.1531876733846838, 0.19678434779440154, 0.1530507244232428, 0.13319105520055818, 0.16125454610296305, 0.15576736897330287, 0.1528635292552078, 0.15762210764858464, 0.1372813163402822, 0.14506678236295964, 0.14274206157870375, 0.14123908436351088, 0.14406353557244958, 0.16702307800312768, 0.1615712677311207, 0.1824616590030932, 0.16768892695608154, 0.14098816716858714, 0.15737226104821228, 0.16533306200044573, 0.13715882215889497, 0.13977599897006332, 0.16550965937549797, 0.15297115712622983, 0.13816762272816197, 0.15015491385978758], [0.1956720067072222, 0.14582796025959086, 0.14133445883143342, 0.13394655273850037, 0.13791919305559774, 0.138730151294858, 0.15371050494373478, 0.1456021292190366, 0.1319250425240813, 0.1375072722049538, 0.1406140990828101, 0.1430055713089789, 0.13864205313828826, 0.13642487696153238, 0.1320614169852181, 0.1509248475087068, 0.13883910409639413, 0.14106540277145516, 0.146049546262876, 0.14334167052496277, 0.1339629372619241, 0.1926185003922003, 0.17758016346464042, 0.1491920333226552, 0.1603667400841546, 0.14280464001872467, 0.14464054922598446, 0.13800030314514808, 0.1493951468764879, 0.16806266838451314, 0.14859748429027228, 0.14231805555086274, 0.13587399464732944, 0.14243874399036224, 0.13670126255638165, 0.14583242858737505, 0.13950632813003996, 0.15562689824634332, 0.1423824250921553, 0.14924298096580296, 0.20697724389322608, 0.1460949487371343, 0.14795469421707771, 0.17430622572129983, 0.14512408492436776, 0.14113554048451676, 0.1537327241751154, 0.17359019459290578, 0.14384879531657424, 0.13959524672300969, 0.15202862152043561, 0.16001697660533684, 0.14846979499789756, 0.1499948669564118, 0.14153124537601383, 0.13772954596303044, 0.14363990972940935, 0.15136808141021244, 0.15613361392220237, 0.13712612253914788, 0.14544337170121016, 0.1432567876747141, 0.1421231957675725, 0.1440786800322997, 0.14538080276408763, 0.13789373750997735, 0.14974069165058337, 0.14076995929686056, 0.14993724186362994, 0.1507901760606768, 0.14004777471082522, 0.15229461354075305, 0.15401760694398595, 0.13710387516752534, 0.1414647027018001, 0.1417456053989467, 0.13354422744653818, 0.14838051421855789, 0.14542395289822482, 0.13991452019243594, 0.15267712632022873, 0.1319640120066646, 0.19650216761649236, 0.13600378730311732, 0.1372221655227576, 0.1390037888795752, 0.1517864602234419, 0.1484784157053542, 0.1410903815585296, 0.14279428667847313, 0.13497946413351267, 0.13466488752669525, 0.15250378644344884, 0.13730303466512367, 0.14912483467418075, 0.1322794152417043, 0.15093638487304123, 0.17621673919998143, 0.13674616172311452, 0.21453883679539418], [0.14450478574527914, 0.1457143474187369, 0.1555370981899616, 0.1436391164732043, 0.14857559892626956, 0.14882189288086745, 0.1468705171288977, 0.16955452187913334, 0.13678532897290058, 0.14089234072321258, 0.1480948847152767, 0.13408940045780832, 0.14579931689397393, 0.13470361790227603, 0.1604917736468268, 0.15336044842290794, 0.1582792226313595, 0.1409912236554027, 0.16070248968400108, 0.15597374264108038, 0.17114745066651715, 0.16362716893034554, 0.1386492317960576, 0.12841458294632446, 0.1496342265676232, 0.15706739426707889, 0.1635651869248081, 0.14458245478630619, 0.14985985580724623, 0.152739890793786, 0.14331329916092353, 0.14298431898321634, 0.1610973259502271, 0.15033029775958864, 0.15221396502935186, 0.13476101510453106, 0.1446673785642301, 0.14537611295308397, 0.13510235171044357, 0.14139872392421085, 0.17265276844730165, 0.15799714500574427, 0.13803596102655175, 0.14706843794819147, 0.17662834672154415, 0.14457045643981284, 0.15080936317524393, 0.1463998860311117, 0.17334334486694544, 0.14094555664159603, 0.17259544597055865, 0.1526627366421763, 0.15557536132580305, 0.17213248558696104, 0.14161228583453916, 0.14646505277949956, 0.17774920347798973, 0.13670674182184786, 0.15978646755911594, 0.14770762046928476, 0.17358979688044174, 0.15290403607434955, 0.14134147884928439, 0.13394596987460397, 0.15485249022234834, 0.13729610280077378, 0.14184233903692803, 0.17034585190186982, 0.14969869836856, 0.14801731555270858, 0.18734475216381527, 0.15692385007131002, 0.14745834051628964, 0.15660488679513565, 0.16224726292320088, 0.17979346151839826, 0.14440590510365417, 0.137562469988272, 0.13574327684035703, 0.17861265829993286, 0.15377183633705652, 0.15079136517331784, 0.1478563827709796, 0.14199839532078198, 0.14706775289001064, 0.14472975755647252, 0.14123002859089054, 0.1502795549442268, 0.14758879610022602, 0.16404339003224105, 0.1434100492836244, 0.13764483215417767, 0.16907631888713312, 0.15129202812043474, 0.14932455989775428, 0.16070251252503212, 0.16074988006598118, 0.15143565239369516, 0.13411982238435155, 0.14487272835960785], [0.15676788250313917, 0.1506111750240834, 0.146119047503663, 0.1531480010744943, 0.15891325553072025, 0.16364789811653932, 0.15138967055471977, 0.15232381776558696, 0.16727705090831244, 0.15365314898559324, 0.1614937835047277, 0.1671729947155535, 0.16834838360903145, 0.1555428431945245, 0.14413711094373374, 0.15297226203477665, 0.1452906868106968, 0.15514675672133005, 0.14883802429867538, 0.15449594618400184, 0.14954692024150854, 0.1468915783804781, 0.16541539622582993, 0.15039639571322477, 0.17431970983768832, 0.15957521947678688, 0.14994130138707149, 0.15574744645838834, 0.15719276362609919, 0.147071947241242, 0.15227145676000942, 0.18620768640824592, 0.1528031184993807, 0.16361215384154876, 0.17189493779090312, 0.157757354432221, 0.15889015229728912, 0.15414096349868017, 0.16862155409976415, 0.156557255063309, 0.15476400805618065, 0.17449627649891436, 0.15845889352308407, 0.16129636565785072, 0.15966690917865856, 0.1572434563962841, 0.15335467182368062, 0.16777616839051446, 0.15699630080635574, 0.15193324740363875, 0.1553303530070425, 0.164390703556413, 0.16347272025784904, 0.15687150028329705, 0.14935728365626375, 0.14754505277673502, 0.14909242318743854, 0.16007571421698163, 0.15391919623818737, 0.15625400008453574, 0.18723545710653547, 0.17213040034699215, 0.15609940501998898, 0.15926549287751007, 0.14567163899063548, 0.16274685080372306, 0.1545960065613862, 0.15633139001406512, 0.15892652999415324, 0.15303934766400776, 0.15059631552493977, 0.15403889891706862, 0.1539022259095633, 0.16253783488461218, 0.1470592387583713, 0.17417077612357532, 0.15750294445046722, 0.15827036163578195, 0.19232291219935202, 0.1709760048004654, 0.15998399198004493, 0.16008795236419954, 0.14577048153026603, 0.15559226733553214, 0.18426932674713797, 0.1575517601905409, 0.16265525389002614, 0.15688122546641214, 0.1449458311711252, 0.14189507294938142, 0.16548916510685419, 0.15712464113055735, 0.15688293182205262, 0.1483154536793583, 0.15759530378933792, 0.15243641076069614, 0.158700820353922, 0.1633138552220091, 0.18171188056649712, 0.1523011145605004], [0.15064835242739164, 0.20116666607354042, 0.15043956564726252, 0.14466675394693784, 0.15637998128337444, 0.15741822782432005, 0.13977683219367534, 0.1957412289440031, 0.13923360970699244, 0.1446182371621637, 0.13834016444465763, 0.19903707647390437, 0.15266927000749647, 0.1577752914338156, 0.1545287056546679, 0.14619779489477683, 0.18224028244463764, 0.1449362110746292, 0.14841518733616862, 0.14981980583887486, 0.14439088742722198, 0.15432571128956407, 0.14431185452551523, 0.1494474987670734, 0.1499296451748242, 0.1792709265788088, 0.15179620307033861, 0.14046119839668175, 0.1589951986714733, 0.1587971986838449, 0.16179333596288084, 0.14496687634342334, 0.1427064543647107, 0.1463452103669078, 0.19098869318145137, 0.1423410099162198, 0.13606055877363937, 0.15730215390106178, 0.1549993938710938, 0.15824924988456524, 0.15445091794423874, 0.16005178277938328, 0.1389694667076749, 0.14465356705709778, 0.19681848479017147, 0.16208120246861274, 0.13682343115838388, 0.14264250690168176, 0.1346243061450475, 0.15213623560499884, 0.15188804310584791, 0.16307429906602688, 0.18608934612902422, 0.15008991311402242, 0.15346980937051286, 0.1513904047600632, 0.138051413083824, 0.14444643879336055, 0.14293866624276227, 0.14493318641123032, 0.15073820451093442, 0.16209066222935622, 0.15609492424577898, 0.15339065156215131, 0.13894327416962535, 0.13706537389074008, 0.1454998798966734, 0.14816572062116629, 0.16048427962479048, 0.15868248935977627, 0.1433096077699594, 0.15765934927980016, 0.1445478165092159, 0.13537088967258903, 0.16484692239636423, 0.15681327978953305, 0.13823553836367322, 0.15720133449390905, 0.1426446097947524, 0.14257951544909594, 0.1428863212311613, 0.1572940811926901, 0.13806761812474513, 0.1708951499407444, 0.1497420224881769, 0.15279538896895953, 0.1513420762936911, 0.15307931975940578, 0.16577586008319378, 0.14025460327410805, 0.1587351406153104, 0.13412322669933777, 0.14769282479997062, 0.14592683075271304, 0.17153813510024377, 0.15053994597308007, 0.18731208881356295, 0.19872610671513688, 0.1841662522331951, 0.13422272693053547], [0.18181722019501215, 0.13875190346067637, 0.1434974174522277, 0.15056958156680675, 0.19827204377214533, 0.15921230878495077, 0.1386356089299053, 0.1510407025688063, 0.14337780219542212, 0.1410132198224032, 0.13271982492164613, 0.15893605155993584, 0.16640501776760439, 0.14563240579388123, 0.14045729078900115, 0.15651224676956504, 0.13695008439302267, 0.15157098201166191, 0.14881164301028307, 0.14409529838958476, 0.15213301195228676, 0.157048839738969, 0.13661235724713386, 0.14050145437177985, 0.14427626025663914, 0.15313316158120382, 0.14641473340092118, 0.14423881930033242, 0.15487425897069923, 0.13493039638028476, 0.14265930334976998, 0.13926964709849904, 0.15517305682143215, 0.156840168973403, 0.14120398891609437, 0.14258982720768837, 0.16224171521813027, 0.1487020658844222, 0.13593975162293093, 0.13552402374835276, 0.14435497567590433, 0.14551984656396055, 0.16925695038026414, 0.12532000473876634, 0.18787707719901314, 0.14494349346856306, 0.1460512700361367, 0.13764790699935003, 0.13205003919786196, 0.14312726436538106, 0.17641827595770393, 0.13281619405067382, 0.21002640920684798, 0.14321731551404313, 0.17479177096737247, 0.1421983860486019, 0.1421886281551943, 0.15029200646874508, 0.1473593591348698, 0.1461791592183094, 0.14995947075456567, 0.1697644130822565, 0.1510501770415216, 0.1400723544027716, 0.1460962022509319, 0.13876860340920166, 0.14118568961155942, 0.15033228824650205, 0.13811125545597394, 0.14858503827371414, 0.20975600554784413, 0.16307940402624038, 0.15869262164160572, 0.13700591045887486, 0.13700591045887486, 0.20220167392624913, 0.14708098803722688, 0.1412210489031462, 0.14796775532369322, 0.13488335442887064, 0.13772982826965108, 0.13449131824271635, 0.145407529841331, 0.2042208435093412, 0.152977855852745, 0.13525574446942762, 0.14041395660614236, 0.1458328358296098, 0.14631114120221003, 0.1342305386963775, 0.16227988289823334, 0.1431539862980931, 0.15060583592754204, 0.15952910939003356, 0.1566258669244816, 0.1537752727590032, 0.1539086023339344, 0.16598925365010353, 0.17507586529075203, 0.13986227065308077]]
    lossveclist = lossvec0+lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.1$, $n=6$')
    
    lossvec0 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598]]
    lossveclist = [[0.14509325259013878, 0.14028874836906774, 0.15305064950853794, 0.16164990223848158, 0.14600334611479598, 0.14222540439564113, 0.13819926446274894, 0.14888751519994395, 0.13601042925395454, 0.13705411416940977, 0.15017616990619576, 0.1312379783345067, 0.1399484932259146, 0.13867950539952534, 0.15473940085023505, 0.16492083747756797, 0.15266627729906476, 0.14303711984400314, 0.13944081571793362, 0.1351921195153755, 0.15000995864717762, 0.13785200299246733, 0.13972241307192595, 0.1390171111021526, 0.1741896010859611, 0.1523797619746385, 0.16802109843462054, 0.2031044061496549, 0.13994207470188078, 0.1493886304687554, 0.1421754071608363, 0.14819472020134955, 0.16730339147588053, 0.14273239657853296, 0.13527345028311655, 0.161211796889484, 0.15418280898428968, 0.1660452606865663, 0.16150255257113955, 0.14213185150950894, 0.16426791944900046, 0.14820635833013102, 0.1379348973871464, 0.15140720104735936, 0.15692154621266824, 0.13800025303241972, 0.15247775657441595, 0.1644960062364241, 0.14578730342459145, 0.15137928900502245, 0.15856592647467407, 0.1452533446898607, 0.13957331327211198, 0.16653186540898943, 0.1414586386472211, 0.13863761618792944, 0.15044269753193415, 0.13513057159191263, 0.1504710967707737, 0.14143042379029486, 0.15663931070287654, 0.15513959857473436, 0.14020565695676762, 0.14589390237896285, 0.13989413525049613, 0.13558801438885254, 0.1306796412110928, 0.1454250416842359, 0.20039562872768904, 0.1464782403034093, 0.13988968170112726, 0.13273908598086082, 0.15927546532370224, 0.1489380419506682, 0.1531876733846838, 0.19678434779440154, 0.1530507244232428, 0.13319105520055818, 0.16125454610296305, 0.15576736897330287, 0.1528635292552078, 0.15762210764858464, 0.1372813163402822, 0.14506678236295964, 0.14274206157870375, 0.14123908436351088, 0.14406353557244958, 0.16702307800312768, 0.1615712677311207, 0.1824616590030932, 0.16768892695608154, 0.14098816716858714, 0.15737226104821228, 0.16533306200044573, 0.13715882215889497, 0.13977599897006332, 0.16550965937549797, 0.15297115712622983, 0.13816762272816197, 0.15015491385978758], [0.1956720067072222, 0.14582796025959086, 0.14133445883143342, 0.13394655273850037, 0.13791919305559774, 0.138730151294858, 0.15371050494373478, 0.1456021292190366, 0.1319250425240813, 0.1375072722049538, 0.1406140990828101, 0.1430055713089789, 0.13864205313828826, 0.13642487696153238, 0.1320614169852181, 0.1509248475087068, 0.13883910409639413, 0.14106540277145516, 0.146049546262876, 0.14334167052496277, 0.1339629372619241, 0.1926185003922003, 0.17758016346464042, 0.1491920333226552, 0.1603667400841546, 0.14280464001872467, 0.14464054922598446, 0.13800030314514808, 0.1493951468764879, 0.16806266838451314, 0.14859748429027228, 0.14231805555086274, 0.13587399464732944, 0.14243874399036224, 0.13670126255638165, 0.14583242858737505, 0.13950632813003996, 0.15562689824634332, 0.1423824250921553, 0.14924298096580296, 0.20697724389322608, 0.1460949487371343, 0.14795469421707771, 0.17430622572129983, 0.14512408492436776, 0.14113554048451676, 0.1537327241751154, 0.17359019459290578, 0.14384879531657424, 0.13959524672300969, 0.15202862152043561, 0.16001697660533684, 0.14846979499789756, 0.1499948669564118, 0.14153124537601383, 0.13772954596303044, 0.14363990972940935, 0.15136808141021244, 0.15613361392220237, 0.13712612253914788, 0.14544337170121016, 0.1432567876747141, 0.1421231957675725, 0.1440786800322997, 0.14538080276408763, 0.13789373750997735, 0.14974069165058337, 0.14076995929686056, 0.14993724186362994, 0.1507901760606768, 0.14004777471082522, 0.15229461354075305, 0.15401760694398595, 0.13710387516752534, 0.1414647027018001, 0.1417456053989467, 0.13354422744653818, 0.14838051421855789, 0.14542395289822482, 0.13991452019243594, 0.15267712632022873, 0.1319640120066646, 0.19650216761649236, 0.13600378730311732, 0.1372221655227576, 0.1390037888795752, 0.1517864602234419, 0.1484784157053542, 0.1410903815585296, 0.14279428667847313, 0.13497946413351267, 0.13466488752669525, 0.15250378644344884, 0.13730303466512367, 0.14912483467418075, 0.1322794152417043, 0.15093638487304123, 0.17621673919998143, 0.13674616172311452, 0.21453883679539418], [0.14450478574527914, 0.1457143474187369, 0.1555370981899616, 0.1436391164732043, 0.14857559892626956, 0.14882189288086745, 0.1468705171288977, 0.16955452187913334, 0.13678532897290058, 0.14089234072321258, 0.1480948847152767, 0.13408940045780832, 0.14579931689397393, 0.13470361790227603, 0.1604917736468268, 0.15336044842290794, 0.1582792226313595, 0.1409912236554027, 0.16070248968400108, 0.15597374264108038, 0.17114745066651715, 0.16362716893034554, 0.1386492317960576, 0.12841458294632446, 0.1496342265676232, 0.15706739426707889, 0.1635651869248081, 0.14458245478630619, 0.14985985580724623, 0.152739890793786, 0.14331329916092353, 0.14298431898321634, 0.1610973259502271, 0.15033029775958864, 0.15221396502935186, 0.13476101510453106, 0.1446673785642301, 0.14537611295308397, 0.13510235171044357, 0.14139872392421085, 0.17265276844730165, 0.15799714500574427, 0.13803596102655175, 0.14706843794819147, 0.17662834672154415, 0.14457045643981284, 0.15080936317524393, 0.1463998860311117, 0.17334334486694544, 0.14094555664159603, 0.17259544597055865, 0.1526627366421763, 0.15557536132580305, 0.17213248558696104, 0.14161228583453916, 0.14646505277949956, 0.17774920347798973, 0.13670674182184786, 0.15978646755911594, 0.14770762046928476, 0.17358979688044174, 0.15290403607434955, 0.14134147884928439, 0.13394596987460397, 0.15485249022234834, 0.13729610280077378, 0.14184233903692803, 0.17034585190186982, 0.14969869836856, 0.14801731555270858, 0.18734475216381527, 0.15692385007131002, 0.14745834051628964, 0.15660488679513565, 0.16224726292320088, 0.17979346151839826, 0.14440590510365417, 0.137562469988272, 0.13574327684035703, 0.17861265829993286, 0.15377183633705652, 0.15079136517331784, 0.1478563827709796, 0.14199839532078198, 0.14706775289001064, 0.14472975755647252, 0.14123002859089054, 0.1502795549442268, 0.14758879610022602, 0.16404339003224105, 0.1434100492836244, 0.13764483215417767, 0.16907631888713312, 0.15129202812043474, 0.14932455989775428, 0.16070251252503212, 0.16074988006598118, 0.15143565239369516, 0.13411982238435155, 0.14487272835960785], [0.15676788250313917, 0.1506111750240834, 0.146119047503663, 0.1531480010744943, 0.15891325553072025, 0.16364789811653932, 0.15138967055471977, 0.15232381776558696, 0.16727705090831244, 0.15365314898559324, 0.1614937835047277, 0.1671729947155535, 0.16834838360903145, 0.1555428431945245, 0.14413711094373374, 0.15297226203477665, 0.1452906868106968, 0.15514675672133005, 0.14883802429867538, 0.15449594618400184, 0.14954692024150854, 0.1468915783804781, 0.16541539622582993, 0.15039639571322477, 0.17431970983768832, 0.15957521947678688, 0.14994130138707149, 0.15574744645838834, 0.15719276362609919, 0.147071947241242, 0.15227145676000942, 0.18620768640824592, 0.1528031184993807, 0.16361215384154876, 0.17189493779090312, 0.157757354432221, 0.15889015229728912, 0.15414096349868017, 0.16862155409976415, 0.156557255063309, 0.15476400805618065, 0.17449627649891436, 0.15845889352308407, 0.16129636565785072, 0.15966690917865856, 0.1572434563962841, 0.15335467182368062, 0.16777616839051446, 0.15699630080635574, 0.15193324740363875, 0.1553303530070425, 0.164390703556413, 0.16347272025784904, 0.15687150028329705, 0.14935728365626375, 0.14754505277673502, 0.14909242318743854, 0.16007571421698163, 0.15391919623818737, 0.15625400008453574, 0.18723545710653547, 0.17213040034699215, 0.15609940501998898, 0.15926549287751007, 0.14567163899063548, 0.16274685080372306, 0.1545960065613862, 0.15633139001406512, 0.15892652999415324, 0.15303934766400776, 0.15059631552493977, 0.15403889891706862, 0.1539022259095633, 0.16253783488461218, 0.1470592387583713, 0.17417077612357532, 0.15750294445046722, 0.15827036163578195, 0.19232291219935202, 0.1709760048004654, 0.15998399198004493, 0.16008795236419954, 0.14577048153026603, 0.15559226733553214, 0.18426932674713797, 0.1575517601905409, 0.16265525389002614, 0.15688122546641214, 0.1449458311711252, 0.14189507294938142, 0.16548916510685419, 0.15712464113055735, 0.15688293182205262, 0.1483154536793583, 0.15759530378933792, 0.15243641076069614, 0.158700820353922, 0.1633138552220091, 0.18171188056649712, 0.1523011145605004], [0.15064835242739164, 0.20116666607354042, 0.15043956564726252, 0.14466675394693784, 0.15637998128337444, 0.15741822782432005, 0.13977683219367534, 0.1957412289440031, 0.13923360970699244, 0.1446182371621637, 0.13834016444465763, 0.19903707647390437, 0.15266927000749647, 0.1577752914338156, 0.1545287056546679, 0.14619779489477683, 0.18224028244463764, 0.1449362110746292, 0.14841518733616862, 0.14981980583887486, 0.14439088742722198, 0.15432571128956407, 0.14431185452551523, 0.1494474987670734, 0.1499296451748242, 0.1792709265788088, 0.15179620307033861, 0.14046119839668175, 0.1589951986714733, 0.1587971986838449, 0.16179333596288084, 0.14496687634342334, 0.1427064543647107, 0.1463452103669078, 0.19098869318145137, 0.1423410099162198, 0.13606055877363937, 0.15730215390106178, 0.1549993938710938, 0.15824924988456524, 0.15445091794423874, 0.16005178277938328, 0.1389694667076749, 0.14465356705709778, 0.19681848479017147, 0.16208120246861274, 0.13682343115838388, 0.14264250690168176, 0.1346243061450475, 0.15213623560499884, 0.15188804310584791, 0.16307429906602688, 0.18608934612902422, 0.15008991311402242, 0.15346980937051286, 0.1513904047600632, 0.138051413083824, 0.14444643879336055, 0.14293866624276227, 0.14493318641123032, 0.15073820451093442, 0.16209066222935622, 0.15609492424577898, 0.15339065156215131, 0.13894327416962535, 0.13706537389074008, 0.1454998798966734, 0.14816572062116629, 0.16048427962479048, 0.15868248935977627, 0.1433096077699594, 0.15765934927980016, 0.1445478165092159, 0.13537088967258903, 0.16484692239636423, 0.15681327978953305, 0.13823553836367322, 0.15720133449390905, 0.1426446097947524, 0.14257951544909594, 0.1428863212311613, 0.1572940811926901, 0.13806761812474513, 0.1708951499407444, 0.1497420224881769, 0.15279538896895953, 0.1513420762936911, 0.15307931975940578, 0.16577586008319378, 0.14025460327410805, 0.1587351406153104, 0.13412322669933777, 0.14769282479997062, 0.14592683075271304, 0.17153813510024377, 0.15053994597308007, 0.18731208881356295, 0.19872610671513688, 0.1841662522331951, 0.13422272693053547], [0.18181722019501215, 0.13875190346067637, 0.1434974174522277, 0.15056958156680675, 0.19827204377214533, 0.15921230878495077, 0.1386356089299053, 0.1510407025688063, 0.14337780219542212, 0.1410132198224032, 0.13271982492164613, 0.15893605155993584, 0.16640501776760439, 0.14563240579388123, 0.14045729078900115, 0.15651224676956504, 0.13695008439302267, 0.15157098201166191, 0.14881164301028307, 0.14409529838958476, 0.15213301195228676, 0.157048839738969, 0.13661235724713386, 0.14050145437177985, 0.14427626025663914, 0.15313316158120382, 0.14641473340092118, 0.14423881930033242, 0.15487425897069923, 0.13493039638028476, 0.14265930334976998, 0.13926964709849904, 0.15517305682143215, 0.156840168973403, 0.14120398891609437, 0.14258982720768837, 0.16224171521813027, 0.1487020658844222, 0.13593975162293093, 0.13552402374835276, 0.14435497567590433, 0.14551984656396055, 0.16925695038026414, 0.12532000473876634, 0.18787707719901314, 0.14494349346856306, 0.1460512700361367, 0.13764790699935003, 0.13205003919786196, 0.14312726436538106, 0.17641827595770393, 0.13281619405067382, 0.21002640920684798, 0.14321731551404313, 0.17479177096737247, 0.1421983860486019, 0.1421886281551943, 0.15029200646874508, 0.1473593591348698, 0.1461791592183094, 0.14995947075456567, 0.1697644130822565, 0.1510501770415216, 0.1400723544027716, 0.1460962022509319, 0.13876860340920166, 0.14118568961155942, 0.15033228824650205, 0.13811125545597394, 0.14858503827371414, 0.20975600554784413, 0.16307940402624038, 0.15869262164160572, 0.13700591045887486, 0.13700591045887486, 0.20220167392624913, 0.14708098803722688, 0.1412210489031462, 0.14796775532369322, 0.13488335442887064, 0.13772982826965108, 0.13449131824271635, 0.145407529841331, 0.2042208435093412, 0.152977855852745, 0.13525574446942762, 0.14041395660614236, 0.1458328358296098, 0.14631114120221003, 0.1342305386963775, 0.16227988289823334, 0.1431539862980931, 0.15060583592754204, 0.15952910939003356, 0.1566258669244816, 0.1537752727590032, 0.1539086023339344, 0.16598925365010353, 0.17507586529075203, 0.13986227065308077]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist: # FOR INTERVAL ON PERCENT IMPROVEMENT FROM NULL DESIGN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    for lst in lossveclist: # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = ((mn-intval))
        hiperc = ((mn+intval))
        print('['+str(loperc)+', '+str(hiperc)+']')
    # VIA APPROXIMATION
    lossvec = [0.1921631393187371, 0.1496456552426906, 0.17465394927838565, 0.14176718850304493, 0.1477586080539812, 0.15747761746906022]
        
    '''

    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.12847026958561233, 0.11986732398951072, 0.13060367191347091, 0.13456141828997675, 0.1274179951384851, 0.1395853466736562, 0.11949711627700356, 0.14222439398953382, 0.12650237999957095, 0.11742182455737671, 0.125807002876967, 0.1184952562133039, 0.11595927744994752, 0.13241341970960263, 0.1330365092362536, 0.14702475658549582, 0.12372548979744037, 0.12326210162435598, 0.11596437064058449, 0.1360079427634559, 0.13490036368964048, 0.12857099981465742, 0.12546313943515863, 0.12160934132043706, 0.1462538289015319, 0.12058229113278009, 0.1906528527577479, 0.12731827990432867, 0.15162017453679544, 0.11729449808267677, 0.1190441940260026, 0.11461052983150097, 0.12314952671527217, 0.13401586619002537, 0.11792195626961513, 0.12672867159599627, 0.13739567825608845, 0.12373221054427508, 0.1297344567932947, 0.13560544320405665, 0.19761742209602334, 0.12606856696655194, 0.1379339281846113, 0.1374334378123528, 0.1306824291013811, 0.11803407486284032, 0.12967267696704565, 0.11771991263021934, 0.1346792598792127, 0.1409915447125594, 0.12118391932460561, 0.12343177753491975, 0.12827072105544465, 0.13515099777805797, 0.1419930223266828, 0.13708165525755409, 0.12851654777366114, 0.12072503892420437, 0.13588302574565375, 0.12763095569671912, 0.11770390994278485, 0.1337648303433984, 0.1717760059155993, 0.12769012395302703, 0.14218244225977397, 0.12415284258856643, 0.12592778571793506, 0.12462257842242966, 0.14994368569109445, 0.1184717062250044, 0.127352890061241, 0.1261733842087149, 0.1553400615115116, 0.12521722674144753, 0.140173063194675, 0.17588188191245271, 0.13714986387224123, 0.1271717829247304, 0.12247977824019007, 0.145766957774525, 0.13598255520000507, 0.13351997498557475, 0.12627843146354406, 0.12668244354246871, 0.13096893060481926, 0.12175318020999325, 0.16310087594160333, 0.16095717672883847, 0.1300863114218935, 0.14288872177752412, 0.12794333127672622, 0.13113273545611268, 0.14831587955772, 0.1331221376427609, 0.12098932922272174, 0.12482044143706773, 0.15980859235266884, 0.16760616557412308, 0.12400024308665411, 0.12109142757996429], [0.10706549287250079, 0.11575611710588574, 0.11657755694309162, 0.16261739870199468, 0.13044543811112205, 0.13597871423477614, 0.1162521924230518, 0.11451468777257316, 0.11977597197875277, 0.14706270459984383, 0.11710752464564515, 0.10042574426077899, 0.13200671674442208, 0.11956001986469626, 0.14352235169529448, 0.13941878520513282, 0.11014525523119775, 0.10043722950557356, 0.12029623451868249, 0.13085447101444728, 0.11453146422406418, 0.17624798196585864, 0.14802263895111217, 0.10563726772450745, 0.11133843244043405, 0.17849680482103586, 0.14070005356490364, 0.14096922814148977, 0.156119362323945, 0.11431832309758867, 0.1347037871678656, 0.10827995515121462, 0.12991595333241354, 0.11288800385497598, 0.1087194394506875, 0.13957184220395502, 0.11433250028736858, 0.1154339703968407, 0.13531303685378834, 0.1181845974938699, 0.1624782253808026, 0.10785906088538802, 0.11187337490987176, 0.1490282005501971, 0.16584111420698566, 0.10409255587349321, 0.1531767083995999, 0.13969790265815368, 0.15893111057070325, 0.1350896551679034, 0.11223328144029465, 0.11122693364823041, 0.156758751098658, 0.13926181585327896, 0.12928728514951857, 0.14880967338603854, 0.11426618162572089, 0.12765392949835094, 0.16174518844820734, 0.12906559110102445, 0.11659937296517346, 0.10805969683894634, 0.1124038253730161, 0.11256266423435923, 0.13337769706865218, 0.12564355984905443, 0.15759371095454633, 0.1334435348161012, 0.11424065270941168, 0.10670547781120827, 0.1340283971088839, 0.11229038996424014, 0.13919071089398244, 0.11865267981990554, 0.19434057273740335, 0.16108895386440805, 0.1339694198446523, 0.1444760773776637, 0.11576840064181515, 0.15682787631356135, 0.1333306475033713, 0.11269576857300377, 0.105196751357552, 0.14939289076638698, 0.11654199774278479, 0.10779133744224585, 0.11893456865733175, 0.11701383813184087, 0.11127528879372119, 0.16543984467098882, 0.18119717818983047, 0.11419431420662064, 0.16719167236741772, 0.11701261937403842, 0.11162983384442594, 0.11346742968022439, 0.12262265636152543, 0.1353553759373205, 0.13483725103248212, 0.10472127378800088], [0.11678330073853264, 0.1483791506375431, 0.14301199387015806, 0.15291720046764978, 0.12932617682376016, 0.11415161831739352, 0.13594132427209848, 0.12851750912928456, 0.11248114383222577, 0.12569532953866397, 0.13116045541080357, 0.11350277061595218, 0.12389588123048184, 0.12255118084248208, 0.12284882809920945, 0.13101887036737578, 0.138084520666699, 0.1222912567850896, 0.11060620781755158, 0.13532426606855924, 0.12088575345283185, 0.1385368374689929, 0.11619970130129674, 0.12457753959628065, 0.13055800683995697, 0.13538545412131597, 0.14276802801025254, 0.1374871166073497, 0.15312490598902023, 0.1311127947083507, 0.12509808772524494, 0.12665143866605372, 0.14334383550981983, 0.13091911295528422, 0.12893982634754697, 0.11608514495001748, 0.11858905120451496, 0.1250175749211199, 0.11806106548991627, 0.15243464137467358, 0.16870203684370985, 0.12830671483036343, 0.11548252484653072, 0.1505001008801831, 0.15115493328869029, 0.11667149774132125, 0.1243792772803687, 0.1280739476470694, 0.1300164370813426, 0.12132283907291189, 0.12093929338546512, 0.12594551117214187, 0.16804669258024021, 0.15495788201033703, 0.13710339770258398, 0.12687569415258093, 0.12563536725886024, 0.1585903134223614, 0.13340856579979055, 0.13097073330511214, 0.1322598244909756, 0.12497751366881622, 0.16082242067367697, 0.13102265922097037, 0.13999650830061847, 0.12940941740665673, 0.13611910200945787, 0.13426229500361453, 0.12467430197220103, 0.1280500475944258, 0.13499429373161861, 0.12933260074498812, 0.12918639683395922, 0.14038571042123474, 0.16182826356035337, 0.17207014456170683, 0.14677207023614533, 0.1267900443293803, 0.14383984254649396, 0.14359682121981873, 0.12230830793897036, 0.11839440032337135, 0.12801523418544866, 0.12754693512342496, 0.1429154338734327, 0.12006421074473932, 0.13423051645822143, 0.13556868485588958, 0.12954861499487944, 0.12082549577064108, 0.12580973946180612, 0.12625040853445754, 0.15050355161408746, 0.12750415834131537, 0.1351781983382809, 0.13302548918098675, 0.13871047053836819, 0.15974484376388454, 0.12162680349486192, 0.11474779719424359], [0.1465059056453364, 0.17355428874149662, 0.15328000856689084, 0.15894192282782818, 0.17324043716825477, 0.15296093718557302, 0.1476807779826612, 0.15667981267214043, 0.14473882938402513, 0.147041241266836, 0.15386320059016986, 0.16552708813511469, 0.1540470583169911, 0.14328984608230924, 0.14375082683266385, 0.16617922349383918, 0.16088134938666387, 0.14765605602145176, 0.17435801311728671, 0.14827551829661414, 0.15329763697303322, 0.14472953426787188, 0.17125010340584843, 0.14572248129073692, 0.1336153120653446, 0.14582927809867732, 0.14848843370764533, 0.1747603051372686, 0.14383653678616662, 0.1619096631813556, 0.15540647378180358, 0.17265403646729033, 0.16111132921561488, 0.1467410645444637, 0.16665112559753137, 0.13917985697713006, 0.1734736031717337, 0.1581829967982839, 0.17158968955526813, 0.14506370061665497, 0.14202851635371547, 0.16475734273539983, 0.19468669913179526, 0.13759816729071742, 0.13796843994938945, 0.14376524182355194, 0.15355883720603658, 0.1925442891993296, 0.15769448639185818, 0.15132611280032016, 0.14602854920007455, 0.17288197778989967, 0.16947775151741457, 0.14431249870861976, 0.16104860701090984, 0.14727555923722968, 0.1649651566116195, 0.14752840612486381, 0.15137804508655991, 0.14569669080603223, 0.1886501083563279, 0.14774107101103773, 0.1846084498196342, 0.14349051783817388, 0.15687810389800352, 0.15317412505174166, 0.15008903035618867, 0.17266662696106372, 0.1408409323301772, 0.14412658538385037, 0.16184467539954767, 0.15487166636429472, 0.16349459098795593, 0.15432584946619862, 0.16286403507204014, 0.1484365267435558, 0.1462836172990036, 0.1805471712448447, 0.15163430576165168, 0.15715392809565756, 0.15185956501014095, 0.167501148591377, 0.1505870181461255, 0.15521711585069486, 0.17353187983092488, 0.14289005591572185, 0.14327479126262316, 0.15733999784282526, 0.1775225130507548, 0.16616768296254153, 0.15145744171131506, 0.16047095595386854, 0.15183626179124074, 0.13189694008126293, 0.15654448895545303, 0.1679146473604498, 0.14783128588845795, 0.16074508329785836, 0.1567832983396268, 0.14849840354821386], [0.12239399036962419, 0.1197086261601347, 0.12424211859793748, 0.1635220026458285, 0.1089637048993127, 0.16846708251443296, 0.14408634583360755, 0.13476450629262407, 0.11544993460130562, 0.13529244488181053, 0.11647890705496407, 0.10200788055334584, 0.16852112557916435, 0.13583524212164005, 0.10852897248325585, 0.11539355039000641, 0.15837853318146086, 0.12535002633620215, 0.16430813553052098, 0.13408645758854704, 0.1195983896918656, 0.11342568957821446, 0.13988713376969597, 0.11522263111548936, 0.15333439620507017, 0.10592083797633782, 0.1430609118897678, 0.13407771983393496, 0.16303638545416438, 0.10562893541059999, 0.10842261745442096, 0.1313201522438386, 0.1278049059720508, 0.12847973230537013, 0.09723977354309747, 0.13368493891311553, 0.1391343390695247, 0.11255785309292166, 0.12849223015610456, 0.10683901254437689, 0.23481491316234634, 0.12559433428323516, 0.16953349833124, 0.11491023421346894, 0.23360709780496078, 0.13194388057949516, 0.13419796101246945, 0.12912481742791232, 0.14903923016798754, 0.1116636429006959, 0.10944792225755616, 0.11074028882316397, 0.15258821863270447, 0.10664872937864546, 0.153635299569851, 0.12622624343937944, 0.13601994904646622, 0.1400035845719506, 0.13092231410371158, 0.1302476074911012, 0.13787212755683526, 0.11278520625311116, 0.11887383965717363, 0.11023236202258775, 0.11533475599376847, 0.16877783236693417, 0.16175066398667418, 0.11019125719897276, 0.11772698704897126, 0.11369291537738112, 0.11249057684541804, 0.12793067463774582, 0.12150863658112937, 0.13143969474767958, 0.1150784722196714, 0.18883632340292317, 0.1094204301469329, 0.12313822834051655, 0.13523720497236436, 0.14721144228801009, 0.1429131576440633, 0.1291553627751315, 0.14144920583947618, 0.15086967794831527, 0.1141639502689692, 0.10964170484455242, 0.11429630650151062, 0.14081298926214164, 0.143604712493729, 0.14652441772489064, 0.1657315644452783, 0.13329970819074438, 0.15431912827034824, 0.1474714170079802, 0.16782388055185915, 0.12368815625903269, 0.1141116077252593, 0.12379776726011253, 0.14272541108036985, 0.14555897805050658], [0.1502025437845887, 0.10954743001641694, 0.11752810843747293, 0.136925599190986, 0.12995982060526312, 0.11158516795697226, 0.10528831651041211, 0.10418835960384869, 0.13634588459644836, 0.14767260654584083, 0.11293964487100557, 0.10530301140382549, 0.11070578921442562, 0.11717973799649849, 0.12946781165682497, 0.13707974727474354, 0.11212882962495944, 0.10520842234487214, 0.12593143718837302, 0.10736313890807066, 0.1297720124959698, 0.11716177301879234, 0.10630349758541678, 0.11207591281794525, 0.1386097206467458, 0.11182755361043692, 0.14577850108694873, 0.13981342638865632, 0.10714386490894132, 0.11299092864245504, 0.11740393306141846, 0.116486774066614, 0.11309897013903854, 0.11108143017195383, 0.10739738617028358, 0.10603954095836655, 0.14723912576358572, 0.11138088070907391, 0.13193374185687462, 0.11546370811414708, 0.14968279066957121, 0.10728093887363854, 0.11224933379927363, 0.1531536916122009, 0.21130165374224438, 0.10790067438979271, 0.145274298151255, 0.10809409659846259, 0.16454685959707555, 0.11986873258641192, 0.1093919508048078, 0.15214492456046252, 0.12241689007127254, 0.15233828520794385, 0.1477002670266664, 0.11682125160422556, 0.1612450145107434, 0.11462144119638207, 0.17029741429213843, 0.17666313203034684, 0.13046982628625792, 0.11452315015346587, 0.11159108337844098, 0.11278996481683422, 0.13407981337896288, 0.14060699419859812, 0.17046302556931262, 0.19509018799805197, 0.12598638724298403, 0.11466884915425202, 0.1607359447695591, 0.12116741727689816, 0.12279811064457224, 0.11340971826279163, 0.1303229762303293, 0.1722897020405344, 0.1148431646196073, 0.11229024346021345, 0.13169130404526172, 0.16578175283619956, 0.14908639876681473, 0.114158475241508, 0.14060348197898215, 0.1769387683187289, 0.12257616509694474, 0.1102774362877409, 0.13969536569060098, 0.11971147899497465, 0.11235779184303205, 0.1506955870487662, 0.11301449885252206, 0.12023191288769444, 0.11889625471725013, 0.11195282415528253, 0.10796394387973061, 0.1241821107589637, 0.15486676574005767, 0.14209648959527185, 0.16354623814002167, 0.10783557610989845]]
    lossvec0 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598]]
    lossveclist = lossvec0+lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.1$, $n=30$')
    
    lossveclist = [[0.12847026958561233, 0.11986732398951072, 0.13060367191347091, 0.13456141828997675, 0.1274179951384851, 0.1395853466736562, 0.11949711627700356, 0.14222439398953382, 0.12650237999957095, 0.11742182455737671, 0.125807002876967, 0.1184952562133039, 0.11595927744994752, 0.13241341970960263, 0.1330365092362536, 0.14702475658549582, 0.12372548979744037, 0.12326210162435598, 0.11596437064058449, 0.1360079427634559, 0.13490036368964048, 0.12857099981465742, 0.12546313943515863, 0.12160934132043706, 0.1462538289015319, 0.12058229113278009, 0.1906528527577479, 0.12731827990432867, 0.15162017453679544, 0.11729449808267677, 0.1190441940260026, 0.11461052983150097, 0.12314952671527217, 0.13401586619002537, 0.11792195626961513, 0.12672867159599627, 0.13739567825608845, 0.12373221054427508, 0.1297344567932947, 0.13560544320405665, 0.19761742209602334, 0.12606856696655194, 0.1379339281846113, 0.1374334378123528, 0.1306824291013811, 0.11803407486284032, 0.12967267696704565, 0.11771991263021934, 0.1346792598792127, 0.1409915447125594, 0.12118391932460561, 0.12343177753491975, 0.12827072105544465, 0.13515099777805797, 0.1419930223266828, 0.13708165525755409, 0.12851654777366114, 0.12072503892420437, 0.13588302574565375, 0.12763095569671912, 0.11770390994278485, 0.1337648303433984, 0.1717760059155993, 0.12769012395302703, 0.14218244225977397, 0.12415284258856643, 0.12592778571793506, 0.12462257842242966, 0.14994368569109445, 0.1184717062250044, 0.127352890061241, 0.1261733842087149, 0.1553400615115116, 0.12521722674144753, 0.140173063194675, 0.17588188191245271, 0.13714986387224123, 0.1271717829247304, 0.12247977824019007, 0.145766957774525, 0.13598255520000507, 0.13351997498557475, 0.12627843146354406, 0.12668244354246871, 0.13096893060481926, 0.12175318020999325, 0.16310087594160333, 0.16095717672883847, 0.1300863114218935, 0.14288872177752412, 0.12794333127672622, 0.13113273545611268, 0.14831587955772, 0.1331221376427609, 0.12098932922272174, 0.12482044143706773, 0.15980859235266884, 0.16760616557412308, 0.12400024308665411, 0.12109142757996429], [0.10706549287250079, 0.11575611710588574, 0.11657755694309162, 0.16261739870199468, 0.13044543811112205, 0.13597871423477614, 0.1162521924230518, 0.11451468777257316, 0.11977597197875277, 0.14706270459984383, 0.11710752464564515, 0.10042574426077899, 0.13200671674442208, 0.11956001986469626, 0.14352235169529448, 0.13941878520513282, 0.11014525523119775, 0.10043722950557356, 0.12029623451868249, 0.13085447101444728, 0.11453146422406418, 0.17624798196585864, 0.14802263895111217, 0.10563726772450745, 0.11133843244043405, 0.17849680482103586, 0.14070005356490364, 0.14096922814148977, 0.156119362323945, 0.11431832309758867, 0.1347037871678656, 0.10827995515121462, 0.12991595333241354, 0.11288800385497598, 0.1087194394506875, 0.13957184220395502, 0.11433250028736858, 0.1154339703968407, 0.13531303685378834, 0.1181845974938699, 0.1624782253808026, 0.10785906088538802, 0.11187337490987176, 0.1490282005501971, 0.16584111420698566, 0.10409255587349321, 0.1531767083995999, 0.13969790265815368, 0.15893111057070325, 0.1350896551679034, 0.11223328144029465, 0.11122693364823041, 0.156758751098658, 0.13926181585327896, 0.12928728514951857, 0.14880967338603854, 0.11426618162572089, 0.12765392949835094, 0.16174518844820734, 0.12906559110102445, 0.11659937296517346, 0.10805969683894634, 0.1124038253730161, 0.11256266423435923, 0.13337769706865218, 0.12564355984905443, 0.15759371095454633, 0.1334435348161012, 0.11424065270941168, 0.10670547781120827, 0.1340283971088839, 0.11229038996424014, 0.13919071089398244, 0.11865267981990554, 0.19434057273740335, 0.16108895386440805, 0.1339694198446523, 0.1444760773776637, 0.11576840064181515, 0.15682787631356135, 0.1333306475033713, 0.11269576857300377, 0.105196751357552, 0.14939289076638698, 0.11654199774278479, 0.10779133744224585, 0.11893456865733175, 0.11701383813184087, 0.11127528879372119, 0.16543984467098882, 0.18119717818983047, 0.11419431420662064, 0.16719167236741772, 0.11701261937403842, 0.11162983384442594, 0.11346742968022439, 0.12262265636152543, 0.1353553759373205, 0.13483725103248212, 0.10472127378800088], [0.11678330073853264, 0.1483791506375431, 0.14301199387015806, 0.15291720046764978, 0.12932617682376016, 0.11415161831739352, 0.13594132427209848, 0.12851750912928456, 0.11248114383222577, 0.12569532953866397, 0.13116045541080357, 0.11350277061595218, 0.12389588123048184, 0.12255118084248208, 0.12284882809920945, 0.13101887036737578, 0.138084520666699, 0.1222912567850896, 0.11060620781755158, 0.13532426606855924, 0.12088575345283185, 0.1385368374689929, 0.11619970130129674, 0.12457753959628065, 0.13055800683995697, 0.13538545412131597, 0.14276802801025254, 0.1374871166073497, 0.15312490598902023, 0.1311127947083507, 0.12509808772524494, 0.12665143866605372, 0.14334383550981983, 0.13091911295528422, 0.12893982634754697, 0.11608514495001748, 0.11858905120451496, 0.1250175749211199, 0.11806106548991627, 0.15243464137467358, 0.16870203684370985, 0.12830671483036343, 0.11548252484653072, 0.1505001008801831, 0.15115493328869029, 0.11667149774132125, 0.1243792772803687, 0.1280739476470694, 0.1300164370813426, 0.12132283907291189, 0.12093929338546512, 0.12594551117214187, 0.16804669258024021, 0.15495788201033703, 0.13710339770258398, 0.12687569415258093, 0.12563536725886024, 0.1585903134223614, 0.13340856579979055, 0.13097073330511214, 0.1322598244909756, 0.12497751366881622, 0.16082242067367697, 0.13102265922097037, 0.13999650830061847, 0.12940941740665673, 0.13611910200945787, 0.13426229500361453, 0.12467430197220103, 0.1280500475944258, 0.13499429373161861, 0.12933260074498812, 0.12918639683395922, 0.14038571042123474, 0.16182826356035337, 0.17207014456170683, 0.14677207023614533, 0.1267900443293803, 0.14383984254649396, 0.14359682121981873, 0.12230830793897036, 0.11839440032337135, 0.12801523418544866, 0.12754693512342496, 0.1429154338734327, 0.12006421074473932, 0.13423051645822143, 0.13556868485588958, 0.12954861499487944, 0.12082549577064108, 0.12580973946180612, 0.12625040853445754, 0.15050355161408746, 0.12750415834131537, 0.1351781983382809, 0.13302548918098675, 0.13871047053836819, 0.15974484376388454, 0.12162680349486192, 0.11474779719424359], [0.1465059056453364, 0.17355428874149662, 0.15328000856689084, 0.15894192282782818, 0.17324043716825477, 0.15296093718557302, 0.1476807779826612, 0.15667981267214043, 0.14473882938402513, 0.147041241266836, 0.15386320059016986, 0.16552708813511469, 0.1540470583169911, 0.14328984608230924, 0.14375082683266385, 0.16617922349383918, 0.16088134938666387, 0.14765605602145176, 0.17435801311728671, 0.14827551829661414, 0.15329763697303322, 0.14472953426787188, 0.17125010340584843, 0.14572248129073692, 0.1336153120653446, 0.14582927809867732, 0.14848843370764533, 0.1747603051372686, 0.14383653678616662, 0.1619096631813556, 0.15540647378180358, 0.17265403646729033, 0.16111132921561488, 0.1467410645444637, 0.16665112559753137, 0.13917985697713006, 0.1734736031717337, 0.1581829967982839, 0.17158968955526813, 0.14506370061665497, 0.14202851635371547, 0.16475734273539983, 0.19468669913179526, 0.13759816729071742, 0.13796843994938945, 0.14376524182355194, 0.15355883720603658, 0.1925442891993296, 0.15769448639185818, 0.15132611280032016, 0.14602854920007455, 0.17288197778989967, 0.16947775151741457, 0.14431249870861976, 0.16104860701090984, 0.14727555923722968, 0.1649651566116195, 0.14752840612486381, 0.15137804508655991, 0.14569669080603223, 0.1886501083563279, 0.14774107101103773, 0.1846084498196342, 0.14349051783817388, 0.15687810389800352, 0.15317412505174166, 0.15008903035618867, 0.17266662696106372, 0.1408409323301772, 0.14412658538385037, 0.16184467539954767, 0.15487166636429472, 0.16349459098795593, 0.15432584946619862, 0.16286403507204014, 0.1484365267435558, 0.1462836172990036, 0.1805471712448447, 0.15163430576165168, 0.15715392809565756, 0.15185956501014095, 0.167501148591377, 0.1505870181461255, 0.15521711585069486, 0.17353187983092488, 0.14289005591572185, 0.14327479126262316, 0.15733999784282526, 0.1775225130507548, 0.16616768296254153, 0.15145744171131506, 0.16047095595386854, 0.15183626179124074, 0.13189694008126293, 0.15654448895545303, 0.1679146473604498, 0.14783128588845795, 0.16074508329785836, 0.1567832983396268, 0.14849840354821386], [0.12239399036962419, 0.1197086261601347, 0.12424211859793748, 0.1635220026458285, 0.1089637048993127, 0.16846708251443296, 0.14408634583360755, 0.13476450629262407, 0.11544993460130562, 0.13529244488181053, 0.11647890705496407, 0.10200788055334584, 0.16852112557916435, 0.13583524212164005, 0.10852897248325585, 0.11539355039000641, 0.15837853318146086, 0.12535002633620215, 0.16430813553052098, 0.13408645758854704, 0.1195983896918656, 0.11342568957821446, 0.13988713376969597, 0.11522263111548936, 0.15333439620507017, 0.10592083797633782, 0.1430609118897678, 0.13407771983393496, 0.16303638545416438, 0.10562893541059999, 0.10842261745442096, 0.1313201522438386, 0.1278049059720508, 0.12847973230537013, 0.09723977354309747, 0.13368493891311553, 0.1391343390695247, 0.11255785309292166, 0.12849223015610456, 0.10683901254437689, 0.23481491316234634, 0.12559433428323516, 0.16953349833124, 0.11491023421346894, 0.23360709780496078, 0.13194388057949516, 0.13419796101246945, 0.12912481742791232, 0.14903923016798754, 0.1116636429006959, 0.10944792225755616, 0.11074028882316397, 0.15258821863270447, 0.10664872937864546, 0.153635299569851, 0.12622624343937944, 0.13601994904646622, 0.1400035845719506, 0.13092231410371158, 0.1302476074911012, 0.13787212755683526, 0.11278520625311116, 0.11887383965717363, 0.11023236202258775, 0.11533475599376847, 0.16877783236693417, 0.16175066398667418, 0.11019125719897276, 0.11772698704897126, 0.11369291537738112, 0.11249057684541804, 0.12793067463774582, 0.12150863658112937, 0.13143969474767958, 0.1150784722196714, 0.18883632340292317, 0.1094204301469329, 0.12313822834051655, 0.13523720497236436, 0.14721144228801009, 0.1429131576440633, 0.1291553627751315, 0.14144920583947618, 0.15086967794831527, 0.1141639502689692, 0.10964170484455242, 0.11429630650151062, 0.14081298926214164, 0.143604712493729, 0.14652441772489064, 0.1657315644452783, 0.13329970819074438, 0.15431912827034824, 0.1474714170079802, 0.16782388055185915, 0.12368815625903269, 0.1141116077252593, 0.12379776726011253, 0.14272541108036985, 0.14555897805050658], [0.1502025437845887, 0.10954743001641694, 0.11752810843747293, 0.136925599190986, 0.12995982060526312, 0.11158516795697226, 0.10528831651041211, 0.10418835960384869, 0.13634588459644836, 0.14767260654584083, 0.11293964487100557, 0.10530301140382549, 0.11070578921442562, 0.11717973799649849, 0.12946781165682497, 0.13707974727474354, 0.11212882962495944, 0.10520842234487214, 0.12593143718837302, 0.10736313890807066, 0.1297720124959698, 0.11716177301879234, 0.10630349758541678, 0.11207591281794525, 0.1386097206467458, 0.11182755361043692, 0.14577850108694873, 0.13981342638865632, 0.10714386490894132, 0.11299092864245504, 0.11740393306141846, 0.116486774066614, 0.11309897013903854, 0.11108143017195383, 0.10739738617028358, 0.10603954095836655, 0.14723912576358572, 0.11138088070907391, 0.13193374185687462, 0.11546370811414708, 0.14968279066957121, 0.10728093887363854, 0.11224933379927363, 0.1531536916122009, 0.21130165374224438, 0.10790067438979271, 0.145274298151255, 0.10809409659846259, 0.16454685959707555, 0.11986873258641192, 0.1093919508048078, 0.15214492456046252, 0.12241689007127254, 0.15233828520794385, 0.1477002670266664, 0.11682125160422556, 0.1612450145107434, 0.11462144119638207, 0.17029741429213843, 0.17666313203034684, 0.13046982628625792, 0.11452315015346587, 0.11159108337844098, 0.11278996481683422, 0.13407981337896288, 0.14060699419859812, 0.17046302556931262, 0.19509018799805197, 0.12598638724298403, 0.11466884915425202, 0.1607359447695591, 0.12116741727689816, 0.12279811064457224, 0.11340971826279163, 0.1303229762303293, 0.1722897020405344, 0.1148431646196073, 0.11229024346021345, 0.13169130404526172, 0.16578175283619956, 0.14908639876681473, 0.114158475241508, 0.14060348197898215, 0.1769387683187289, 0.12257616509694474, 0.1102774362877409, 0.13969536569060098, 0.11971147899497465, 0.11235779184303205, 0.1506955870487662, 0.11301449885252206, 0.12023191288769444, 0.11889625471725013, 0.11195282415528253, 0.10796394387973061, 0.1241821107589637, 0.15486676574005767, 0.14209648959527185, 0.16354623814002167, 0.10783557610989845]]
    lossvec0 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    
    # COMBINE n=6 WITH n=30
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist6 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598], [0.14509325259013878, 0.14028874836906774, 0.15305064950853794, 0.16164990223848158, 0.14600334611479598, 0.14222540439564113, 0.13819926446274894, 0.14888751519994395, 0.13601042925395454, 0.13705411416940977, 0.15017616990619576, 0.1312379783345067, 0.1399484932259146, 0.13867950539952534, 0.15473940085023505, 0.16492083747756797, 0.15266627729906476, 0.14303711984400314, 0.13944081571793362, 0.1351921195153755, 0.15000995864717762, 0.13785200299246733, 0.13972241307192595, 0.1390171111021526, 0.1741896010859611, 0.1523797619746385, 0.16802109843462054, 0.2031044061496549, 0.13994207470188078, 0.1493886304687554, 0.1421754071608363, 0.14819472020134955, 0.16730339147588053, 0.14273239657853296, 0.13527345028311655, 0.161211796889484, 0.15418280898428968, 0.1660452606865663, 0.16150255257113955, 0.14213185150950894, 0.16426791944900046, 0.14820635833013102, 0.1379348973871464, 0.15140720104735936, 0.15692154621266824, 0.13800025303241972, 0.15247775657441595, 0.1644960062364241, 0.14578730342459145, 0.15137928900502245, 0.15856592647467407, 0.1452533446898607, 0.13957331327211198, 0.16653186540898943, 0.1414586386472211, 0.13863761618792944, 0.15044269753193415, 0.13513057159191263, 0.1504710967707737, 0.14143042379029486, 0.15663931070287654, 0.15513959857473436, 0.14020565695676762, 0.14589390237896285, 0.13989413525049613, 0.13558801438885254, 0.1306796412110928, 0.1454250416842359, 0.20039562872768904, 0.1464782403034093, 0.13988968170112726, 0.13273908598086082, 0.15927546532370224, 0.1489380419506682, 0.1531876733846838, 0.19678434779440154, 0.1530507244232428, 0.13319105520055818, 0.16125454610296305, 0.15576736897330287, 0.1528635292552078, 0.15762210764858464, 0.1372813163402822, 0.14506678236295964, 0.14274206157870375, 0.14123908436351088, 0.14406353557244958, 0.16702307800312768, 0.1615712677311207, 0.1824616590030932, 0.16768892695608154, 0.14098816716858714, 0.15737226104821228, 0.16533306200044573, 0.13715882215889497, 0.13977599897006332, 0.16550965937549797, 0.15297115712622983, 0.13816762272816197, 0.15015491385978758], [0.1956720067072222, 0.14582796025959086, 0.14133445883143342, 0.13394655273850037, 0.13791919305559774, 0.138730151294858, 0.15371050494373478, 0.1456021292190366, 0.1319250425240813, 0.1375072722049538, 0.1406140990828101, 0.1430055713089789, 0.13864205313828826, 0.13642487696153238, 0.1320614169852181, 0.1509248475087068, 0.13883910409639413, 0.14106540277145516, 0.146049546262876, 0.14334167052496277, 0.1339629372619241, 0.1926185003922003, 0.17758016346464042, 0.1491920333226552, 0.1603667400841546, 0.14280464001872467, 0.14464054922598446, 0.13800030314514808, 0.1493951468764879, 0.16806266838451314, 0.14859748429027228, 0.14231805555086274, 0.13587399464732944, 0.14243874399036224, 0.13670126255638165, 0.14583242858737505, 0.13950632813003996, 0.15562689824634332, 0.1423824250921553, 0.14924298096580296, 0.20697724389322608, 0.1460949487371343, 0.14795469421707771, 0.17430622572129983, 0.14512408492436776, 0.14113554048451676, 0.1537327241751154, 0.17359019459290578, 0.14384879531657424, 0.13959524672300969, 0.15202862152043561, 0.16001697660533684, 0.14846979499789756, 0.1499948669564118, 0.14153124537601383, 0.13772954596303044, 0.14363990972940935, 0.15136808141021244, 0.15613361392220237, 0.13712612253914788, 0.14544337170121016, 0.1432567876747141, 0.1421231957675725, 0.1440786800322997, 0.14538080276408763, 0.13789373750997735, 0.14974069165058337, 0.14076995929686056, 0.14993724186362994, 0.1507901760606768, 0.14004777471082522, 0.15229461354075305, 0.15401760694398595, 0.13710387516752534, 0.1414647027018001, 0.1417456053989467, 0.13354422744653818, 0.14838051421855789, 0.14542395289822482, 0.13991452019243594, 0.15267712632022873, 0.1319640120066646, 0.19650216761649236, 0.13600378730311732, 0.1372221655227576, 0.1390037888795752, 0.1517864602234419, 0.1484784157053542, 0.1410903815585296, 0.14279428667847313, 0.13497946413351267, 0.13466488752669525, 0.15250378644344884, 0.13730303466512367, 0.14912483467418075, 0.1322794152417043, 0.15093638487304123, 0.17621673919998143, 0.13674616172311452, 0.21453883679539418], [0.14450478574527914, 0.1457143474187369, 0.1555370981899616, 0.1436391164732043, 0.14857559892626956, 0.14882189288086745, 0.1468705171288977, 0.16955452187913334, 0.13678532897290058, 0.14089234072321258, 0.1480948847152767, 0.13408940045780832, 0.14579931689397393, 0.13470361790227603, 0.1604917736468268, 0.15336044842290794, 0.1582792226313595, 0.1409912236554027, 0.16070248968400108, 0.15597374264108038, 0.17114745066651715, 0.16362716893034554, 0.1386492317960576, 0.12841458294632446, 0.1496342265676232, 0.15706739426707889, 0.1635651869248081, 0.14458245478630619, 0.14985985580724623, 0.152739890793786, 0.14331329916092353, 0.14298431898321634, 0.1610973259502271, 0.15033029775958864, 0.15221396502935186, 0.13476101510453106, 0.1446673785642301, 0.14537611295308397, 0.13510235171044357, 0.14139872392421085, 0.17265276844730165, 0.15799714500574427, 0.13803596102655175, 0.14706843794819147, 0.17662834672154415, 0.14457045643981284, 0.15080936317524393, 0.1463998860311117, 0.17334334486694544, 0.14094555664159603, 0.17259544597055865, 0.1526627366421763, 0.15557536132580305, 0.17213248558696104, 0.14161228583453916, 0.14646505277949956, 0.17774920347798973, 0.13670674182184786, 0.15978646755911594, 0.14770762046928476, 0.17358979688044174, 0.15290403607434955, 0.14134147884928439, 0.13394596987460397, 0.15485249022234834, 0.13729610280077378, 0.14184233903692803, 0.17034585190186982, 0.14969869836856, 0.14801731555270858, 0.18734475216381527, 0.15692385007131002, 0.14745834051628964, 0.15660488679513565, 0.16224726292320088, 0.17979346151839826, 0.14440590510365417, 0.137562469988272, 0.13574327684035703, 0.17861265829993286, 0.15377183633705652, 0.15079136517331784, 0.1478563827709796, 0.14199839532078198, 0.14706775289001064, 0.14472975755647252, 0.14123002859089054, 0.1502795549442268, 0.14758879610022602, 0.16404339003224105, 0.1434100492836244, 0.13764483215417767, 0.16907631888713312, 0.15129202812043474, 0.14932455989775428, 0.16070251252503212, 0.16074988006598118, 0.15143565239369516, 0.13411982238435155, 0.14487272835960785], [0.15676788250313917, 0.1506111750240834, 0.146119047503663, 0.1531480010744943, 0.15891325553072025, 0.16364789811653932, 0.15138967055471977, 0.15232381776558696, 0.16727705090831244, 0.15365314898559324, 0.1614937835047277, 0.1671729947155535, 0.16834838360903145, 0.1555428431945245, 0.14413711094373374, 0.15297226203477665, 0.1452906868106968, 0.15514675672133005, 0.14883802429867538, 0.15449594618400184, 0.14954692024150854, 0.1468915783804781, 0.16541539622582993, 0.15039639571322477, 0.17431970983768832, 0.15957521947678688, 0.14994130138707149, 0.15574744645838834, 0.15719276362609919, 0.147071947241242, 0.15227145676000942, 0.18620768640824592, 0.1528031184993807, 0.16361215384154876, 0.17189493779090312, 0.157757354432221, 0.15889015229728912, 0.15414096349868017, 0.16862155409976415, 0.156557255063309, 0.15476400805618065, 0.17449627649891436, 0.15845889352308407, 0.16129636565785072, 0.15966690917865856, 0.1572434563962841, 0.15335467182368062, 0.16777616839051446, 0.15699630080635574, 0.15193324740363875, 0.1553303530070425, 0.164390703556413, 0.16347272025784904, 0.15687150028329705, 0.14935728365626375, 0.14754505277673502, 0.14909242318743854, 0.16007571421698163, 0.15391919623818737, 0.15625400008453574, 0.18723545710653547, 0.17213040034699215, 0.15609940501998898, 0.15926549287751007, 0.14567163899063548, 0.16274685080372306, 0.1545960065613862, 0.15633139001406512, 0.15892652999415324, 0.15303934766400776, 0.15059631552493977, 0.15403889891706862, 0.1539022259095633, 0.16253783488461218, 0.1470592387583713, 0.17417077612357532, 0.15750294445046722, 0.15827036163578195, 0.19232291219935202, 0.1709760048004654, 0.15998399198004493, 0.16008795236419954, 0.14577048153026603, 0.15559226733553214, 0.18426932674713797, 0.1575517601905409, 0.16265525389002614, 0.15688122546641214, 0.1449458311711252, 0.14189507294938142, 0.16548916510685419, 0.15712464113055735, 0.15688293182205262, 0.1483154536793583, 0.15759530378933792, 0.15243641076069614, 0.158700820353922, 0.1633138552220091, 0.18171188056649712, 0.1523011145605004], [0.15064835242739164, 0.20116666607354042, 0.15043956564726252, 0.14466675394693784, 0.15637998128337444, 0.15741822782432005, 0.13977683219367534, 0.1957412289440031, 0.13923360970699244, 0.1446182371621637, 0.13834016444465763, 0.19903707647390437, 0.15266927000749647, 0.1577752914338156, 0.1545287056546679, 0.14619779489477683, 0.18224028244463764, 0.1449362110746292, 0.14841518733616862, 0.14981980583887486, 0.14439088742722198, 0.15432571128956407, 0.14431185452551523, 0.1494474987670734, 0.1499296451748242, 0.1792709265788088, 0.15179620307033861, 0.14046119839668175, 0.1589951986714733, 0.1587971986838449, 0.16179333596288084, 0.14496687634342334, 0.1427064543647107, 0.1463452103669078, 0.19098869318145137, 0.1423410099162198, 0.13606055877363937, 0.15730215390106178, 0.1549993938710938, 0.15824924988456524, 0.15445091794423874, 0.16005178277938328, 0.1389694667076749, 0.14465356705709778, 0.19681848479017147, 0.16208120246861274, 0.13682343115838388, 0.14264250690168176, 0.1346243061450475, 0.15213623560499884, 0.15188804310584791, 0.16307429906602688, 0.18608934612902422, 0.15008991311402242, 0.15346980937051286, 0.1513904047600632, 0.138051413083824, 0.14444643879336055, 0.14293866624276227, 0.14493318641123032, 0.15073820451093442, 0.16209066222935622, 0.15609492424577898, 0.15339065156215131, 0.13894327416962535, 0.13706537389074008, 0.1454998798966734, 0.14816572062116629, 0.16048427962479048, 0.15868248935977627, 0.1433096077699594, 0.15765934927980016, 0.1445478165092159, 0.13537088967258903, 0.16484692239636423, 0.15681327978953305, 0.13823553836367322, 0.15720133449390905, 0.1426446097947524, 0.14257951544909594, 0.1428863212311613, 0.1572940811926901, 0.13806761812474513, 0.1708951499407444, 0.1497420224881769, 0.15279538896895953, 0.1513420762936911, 0.15307931975940578, 0.16577586008319378, 0.14025460327410805, 0.1587351406153104, 0.13412322669933777, 0.14769282479997062, 0.14592683075271304, 0.17153813510024377, 0.15053994597308007, 0.18731208881356295, 0.19872610671513688, 0.1841662522331951, 0.13422272693053547], [0.18181722019501215, 0.13875190346067637, 0.1434974174522277, 0.15056958156680675, 0.19827204377214533, 0.15921230878495077, 0.1386356089299053, 0.1510407025688063, 0.14337780219542212, 0.1410132198224032, 0.13271982492164613, 0.15893605155993584, 0.16640501776760439, 0.14563240579388123, 0.14045729078900115, 0.15651224676956504, 0.13695008439302267, 0.15157098201166191, 0.14881164301028307, 0.14409529838958476, 0.15213301195228676, 0.157048839738969, 0.13661235724713386, 0.14050145437177985, 0.14427626025663914, 0.15313316158120382, 0.14641473340092118, 0.14423881930033242, 0.15487425897069923, 0.13493039638028476, 0.14265930334976998, 0.13926964709849904, 0.15517305682143215, 0.156840168973403, 0.14120398891609437, 0.14258982720768837, 0.16224171521813027, 0.1487020658844222, 0.13593975162293093, 0.13552402374835276, 0.14435497567590433, 0.14551984656396055, 0.16925695038026414, 0.12532000473876634, 0.18787707719901314, 0.14494349346856306, 0.1460512700361367, 0.13764790699935003, 0.13205003919786196, 0.14312726436538106, 0.17641827595770393, 0.13281619405067382, 0.21002640920684798, 0.14321731551404313, 0.17479177096737247, 0.1421983860486019, 0.1421886281551943, 0.15029200646874508, 0.1473593591348698, 0.1461791592183094, 0.14995947075456567, 0.1697644130822565, 0.1510501770415216, 0.1400723544027716, 0.1460962022509319, 0.13876860340920166, 0.14118568961155942, 0.15033228824650205, 0.13811125545597394, 0.14858503827371414, 0.20975600554784413, 0.16307940402624038, 0.15869262164160572, 0.13700591045887486, 0.13700591045887486, 0.20220167392624913, 0.14708098803722688, 0.1412210489031462, 0.14796775532369322, 0.13488335442887064, 0.13772982826965108, 0.13449131824271635, 0.145407529841331, 0.2042208435093412, 0.152977855852745, 0.13525574446942762, 0.14041395660614236, 0.1458328358296098, 0.14631114120221003, 0.1342305386963775, 0.16227988289823334, 0.1431539862980931, 0.15060583592754204, 0.15952910939003356, 0.1566258669244816, 0.1537752727590032, 0.1539086023339344, 0.16598925365010353, 0.17507586529075203, 0.13986227065308077]]
    lossveclist30 = [[0.16316247614417786, 0.15720308016518392, 0.160863945888904, 0.16447283110683764, 0.1597308862650217, 0.16530244384804657, 0.16669312853832846, 0.16160074183245418, 0.16531921860847268, 0.16204418983966884, 0.15497871109482528, 0.15467411380815202, 0.16137507788563935, 0.15747074719610993, 0.15227562888307283, 0.17145553421385715, 0.1636936109540728, 0.1669252130711022, 0.16203792902518932, 0.1590776036970198, 0.15517493597181414, 0.16082428825129408, 0.15756807318592914, 0.15506083185262165, 0.1563119571699612, 0.1577098321842063, 0.1641468650148215, 0.15488810176193077, 0.15665288809662717, 0.1603004792908751, 0.16244412649356446, 0.15682117334200987, 0.16354500425841928, 0.16415919785812233, 0.15638019835364242, 0.16670010935518434, 0.15949899127054123, 0.16151886488912792, 0.15735859935171637, 0.15677491976724814, 0.1632770479674153, 0.14924292022848828, 0.15743089052516365, 0.16345503460451294, 0.16461700092997042, 0.16393482215356434, 0.1567846630229211, 0.15924311538390307, 0.15772433401103705, 0.14844073078598255, 0.14807481745813092, 0.15995264676230736, 0.1579484132093352, 0.15724138753152508, 0.16224710472251716, 0.1641735756558422, 0.15887070821169746, 0.15642966735431305, 0.15406330865539522, 0.1574801626153325, 0.16362808604206897, 0.16149986707782518, 0.15773307449644686, 0.1530540907925208, 0.1645033073394543, 0.15431738379696006, 0.1704341251141459, 0.15808855709519426, 0.16246600430741387, 0.1698498306376867, 0.1648337933683812, 0.17121651335895544, 0.1503781786512441, 0.1524599498085908, 0.15922731157919556, 0.15916234372331206, 0.15939630765108154, 0.15663433246236877, 0.1616397543298343, 0.16063162982298979, 0.1558830142365766, 0.1619674732314209, 0.1696654499763426, 0.16089161339847177, 0.15122267732630387, 0.1650651236958853, 0.16316201297091332, 0.16165031167909902, 0.16726574771516814, 0.16236019915686473, 0.1645428564195015, 0.1545329722426662, 0.15539168558736072, 0.17099218135813946, 0.16002479505594225, 0.15695387354065177, 0.15969571027275462, 0.1596724155733717, 0.15652864335844877, 0.16498385967878598], [0.12847026958561233, 0.11986732398951072, 0.13060367191347091, 0.13456141828997675, 0.1274179951384851, 0.1395853466736562, 0.11949711627700356, 0.14222439398953382, 0.12650237999957095, 0.11742182455737671, 0.125807002876967, 0.1184952562133039, 0.11595927744994752, 0.13241341970960263, 0.1330365092362536, 0.14702475658549582, 0.12372548979744037, 0.12326210162435598, 0.11596437064058449, 0.1360079427634559, 0.13490036368964048, 0.12857099981465742, 0.12546313943515863, 0.12160934132043706, 0.1462538289015319, 0.12058229113278009, 0.1906528527577479, 0.12731827990432867, 0.15162017453679544, 0.11729449808267677, 0.1190441940260026, 0.11461052983150097, 0.12314952671527217, 0.13401586619002537, 0.11792195626961513, 0.12672867159599627, 0.13739567825608845, 0.12373221054427508, 0.1297344567932947, 0.13560544320405665, 0.19761742209602334, 0.12606856696655194, 0.1379339281846113, 0.1374334378123528, 0.1306824291013811, 0.11803407486284032, 0.12967267696704565, 0.11771991263021934, 0.1346792598792127, 0.1409915447125594, 0.12118391932460561, 0.12343177753491975, 0.12827072105544465, 0.13515099777805797, 0.1419930223266828, 0.13708165525755409, 0.12851654777366114, 0.12072503892420437, 0.13588302574565375, 0.12763095569671912, 0.11770390994278485, 0.1337648303433984, 0.1717760059155993, 0.12769012395302703, 0.14218244225977397, 0.12415284258856643, 0.12592778571793506, 0.12462257842242966, 0.14994368569109445, 0.1184717062250044, 0.127352890061241, 0.1261733842087149, 0.1553400615115116, 0.12521722674144753, 0.140173063194675, 0.17588188191245271, 0.13714986387224123, 0.1271717829247304, 0.12247977824019007, 0.145766957774525, 0.13598255520000507, 0.13351997498557475, 0.12627843146354406, 0.12668244354246871, 0.13096893060481926, 0.12175318020999325, 0.16310087594160333, 0.16095717672883847, 0.1300863114218935, 0.14288872177752412, 0.12794333127672622, 0.13113273545611268, 0.14831587955772, 0.1331221376427609, 0.12098932922272174, 0.12482044143706773, 0.15980859235266884, 0.16760616557412308, 0.12400024308665411, 0.12109142757996429], [0.10706549287250079, 0.11575611710588574, 0.11657755694309162, 0.16261739870199468, 0.13044543811112205, 0.13597871423477614, 0.1162521924230518, 0.11451468777257316, 0.11977597197875277, 0.14706270459984383, 0.11710752464564515, 0.10042574426077899, 0.13200671674442208, 0.11956001986469626, 0.14352235169529448, 0.13941878520513282, 0.11014525523119775, 0.10043722950557356, 0.12029623451868249, 0.13085447101444728, 0.11453146422406418, 0.17624798196585864, 0.14802263895111217, 0.10563726772450745, 0.11133843244043405, 0.17849680482103586, 0.14070005356490364, 0.14096922814148977, 0.156119362323945, 0.11431832309758867, 0.1347037871678656, 0.10827995515121462, 0.12991595333241354, 0.11288800385497598, 0.1087194394506875, 0.13957184220395502, 0.11433250028736858, 0.1154339703968407, 0.13531303685378834, 0.1181845974938699, 0.1624782253808026, 0.10785906088538802, 0.11187337490987176, 0.1490282005501971, 0.16584111420698566, 0.10409255587349321, 0.1531767083995999, 0.13969790265815368, 0.15893111057070325, 0.1350896551679034, 0.11223328144029465, 0.11122693364823041, 0.156758751098658, 0.13926181585327896, 0.12928728514951857, 0.14880967338603854, 0.11426618162572089, 0.12765392949835094, 0.16174518844820734, 0.12906559110102445, 0.11659937296517346, 0.10805969683894634, 0.1124038253730161, 0.11256266423435923, 0.13337769706865218, 0.12564355984905443, 0.15759371095454633, 0.1334435348161012, 0.11424065270941168, 0.10670547781120827, 0.1340283971088839, 0.11229038996424014, 0.13919071089398244, 0.11865267981990554, 0.19434057273740335, 0.16108895386440805, 0.1339694198446523, 0.1444760773776637, 0.11576840064181515, 0.15682787631356135, 0.1333306475033713, 0.11269576857300377, 0.105196751357552, 0.14939289076638698, 0.11654199774278479, 0.10779133744224585, 0.11893456865733175, 0.11701383813184087, 0.11127528879372119, 0.16543984467098882, 0.18119717818983047, 0.11419431420662064, 0.16719167236741772, 0.11701261937403842, 0.11162983384442594, 0.11346742968022439, 0.12262265636152543, 0.1353553759373205, 0.13483725103248212, 0.10472127378800088], [0.11678330073853264, 0.1483791506375431, 0.14301199387015806, 0.15291720046764978, 0.12932617682376016, 0.11415161831739352, 0.13594132427209848, 0.12851750912928456, 0.11248114383222577, 0.12569532953866397, 0.13116045541080357, 0.11350277061595218, 0.12389588123048184, 0.12255118084248208, 0.12284882809920945, 0.13101887036737578, 0.138084520666699, 0.1222912567850896, 0.11060620781755158, 0.13532426606855924, 0.12088575345283185, 0.1385368374689929, 0.11619970130129674, 0.12457753959628065, 0.13055800683995697, 0.13538545412131597, 0.14276802801025254, 0.1374871166073497, 0.15312490598902023, 0.1311127947083507, 0.12509808772524494, 0.12665143866605372, 0.14334383550981983, 0.13091911295528422, 0.12893982634754697, 0.11608514495001748, 0.11858905120451496, 0.1250175749211199, 0.11806106548991627, 0.15243464137467358, 0.16870203684370985, 0.12830671483036343, 0.11548252484653072, 0.1505001008801831, 0.15115493328869029, 0.11667149774132125, 0.1243792772803687, 0.1280739476470694, 0.1300164370813426, 0.12132283907291189, 0.12093929338546512, 0.12594551117214187, 0.16804669258024021, 0.15495788201033703, 0.13710339770258398, 0.12687569415258093, 0.12563536725886024, 0.1585903134223614, 0.13340856579979055, 0.13097073330511214, 0.1322598244909756, 0.12497751366881622, 0.16082242067367697, 0.13102265922097037, 0.13999650830061847, 0.12940941740665673, 0.13611910200945787, 0.13426229500361453, 0.12467430197220103, 0.1280500475944258, 0.13499429373161861, 0.12933260074498812, 0.12918639683395922, 0.14038571042123474, 0.16182826356035337, 0.17207014456170683, 0.14677207023614533, 0.1267900443293803, 0.14383984254649396, 0.14359682121981873, 0.12230830793897036, 0.11839440032337135, 0.12801523418544866, 0.12754693512342496, 0.1429154338734327, 0.12006421074473932, 0.13423051645822143, 0.13556868485588958, 0.12954861499487944, 0.12082549577064108, 0.12580973946180612, 0.12625040853445754, 0.15050355161408746, 0.12750415834131537, 0.1351781983382809, 0.13302548918098675, 0.13871047053836819, 0.15974484376388454, 0.12162680349486192, 0.11474779719424359], [0.1465059056453364, 0.17355428874149662, 0.15328000856689084, 0.15894192282782818, 0.17324043716825477, 0.15296093718557302, 0.1476807779826612, 0.15667981267214043, 0.14473882938402513, 0.147041241266836, 0.15386320059016986, 0.16552708813511469, 0.1540470583169911, 0.14328984608230924, 0.14375082683266385, 0.16617922349383918, 0.16088134938666387, 0.14765605602145176, 0.17435801311728671, 0.14827551829661414, 0.15329763697303322, 0.14472953426787188, 0.17125010340584843, 0.14572248129073692, 0.1336153120653446, 0.14582927809867732, 0.14848843370764533, 0.1747603051372686, 0.14383653678616662, 0.1619096631813556, 0.15540647378180358, 0.17265403646729033, 0.16111132921561488, 0.1467410645444637, 0.16665112559753137, 0.13917985697713006, 0.1734736031717337, 0.1581829967982839, 0.17158968955526813, 0.14506370061665497, 0.14202851635371547, 0.16475734273539983, 0.19468669913179526, 0.13759816729071742, 0.13796843994938945, 0.14376524182355194, 0.15355883720603658, 0.1925442891993296, 0.15769448639185818, 0.15132611280032016, 0.14602854920007455, 0.17288197778989967, 0.16947775151741457, 0.14431249870861976, 0.16104860701090984, 0.14727555923722968, 0.1649651566116195, 0.14752840612486381, 0.15137804508655991, 0.14569669080603223, 0.1886501083563279, 0.14774107101103773, 0.1846084498196342, 0.14349051783817388, 0.15687810389800352, 0.15317412505174166, 0.15008903035618867, 0.17266662696106372, 0.1408409323301772, 0.14412658538385037, 0.16184467539954767, 0.15487166636429472, 0.16349459098795593, 0.15432584946619862, 0.16286403507204014, 0.1484365267435558, 0.1462836172990036, 0.1805471712448447, 0.15163430576165168, 0.15715392809565756, 0.15185956501014095, 0.167501148591377, 0.1505870181461255, 0.15521711585069486, 0.17353187983092488, 0.14289005591572185, 0.14327479126262316, 0.15733999784282526, 0.1775225130507548, 0.16616768296254153, 0.15145744171131506, 0.16047095595386854, 0.15183626179124074, 0.13189694008126293, 0.15654448895545303, 0.1679146473604498, 0.14783128588845795, 0.16074508329785836, 0.1567832983396268, 0.14849840354821386], [0.12239399036962419, 0.1197086261601347, 0.12424211859793748, 0.1635220026458285, 0.1089637048993127, 0.16846708251443296, 0.14408634583360755, 0.13476450629262407, 0.11544993460130562, 0.13529244488181053, 0.11647890705496407, 0.10200788055334584, 0.16852112557916435, 0.13583524212164005, 0.10852897248325585, 0.11539355039000641, 0.15837853318146086, 0.12535002633620215, 0.16430813553052098, 0.13408645758854704, 0.1195983896918656, 0.11342568957821446, 0.13988713376969597, 0.11522263111548936, 0.15333439620507017, 0.10592083797633782, 0.1430609118897678, 0.13407771983393496, 0.16303638545416438, 0.10562893541059999, 0.10842261745442096, 0.1313201522438386, 0.1278049059720508, 0.12847973230537013, 0.09723977354309747, 0.13368493891311553, 0.1391343390695247, 0.11255785309292166, 0.12849223015610456, 0.10683901254437689, 0.23481491316234634, 0.12559433428323516, 0.16953349833124, 0.11491023421346894, 0.23360709780496078, 0.13194388057949516, 0.13419796101246945, 0.12912481742791232, 0.14903923016798754, 0.1116636429006959, 0.10944792225755616, 0.11074028882316397, 0.15258821863270447, 0.10664872937864546, 0.153635299569851, 0.12622624343937944, 0.13601994904646622, 0.1400035845719506, 0.13092231410371158, 0.1302476074911012, 0.13787212755683526, 0.11278520625311116, 0.11887383965717363, 0.11023236202258775, 0.11533475599376847, 0.16877783236693417, 0.16175066398667418, 0.11019125719897276, 0.11772698704897126, 0.11369291537738112, 0.11249057684541804, 0.12793067463774582, 0.12150863658112937, 0.13143969474767958, 0.1150784722196714, 0.18883632340292317, 0.1094204301469329, 0.12313822834051655, 0.13523720497236436, 0.14721144228801009, 0.1429131576440633, 0.1291553627751315, 0.14144920583947618, 0.15086967794831527, 0.1141639502689692, 0.10964170484455242, 0.11429630650151062, 0.14081298926214164, 0.143604712493729, 0.14652441772489064, 0.1657315644452783, 0.13329970819074438, 0.15431912827034824, 0.1474714170079802, 0.16782388055185915, 0.12368815625903269, 0.1141116077252593, 0.12379776726011253, 0.14272541108036985, 0.14555897805050658], [0.1502025437845887, 0.10954743001641694, 0.11752810843747293, 0.136925599190986, 0.12995982060526312, 0.11158516795697226, 0.10528831651041211, 0.10418835960384869, 0.13634588459644836, 0.14767260654584083, 0.11293964487100557, 0.10530301140382549, 0.11070578921442562, 0.11717973799649849, 0.12946781165682497, 0.13707974727474354, 0.11212882962495944, 0.10520842234487214, 0.12593143718837302, 0.10736313890807066, 0.1297720124959698, 0.11716177301879234, 0.10630349758541678, 0.11207591281794525, 0.1386097206467458, 0.11182755361043692, 0.14577850108694873, 0.13981342638865632, 0.10714386490894132, 0.11299092864245504, 0.11740393306141846, 0.116486774066614, 0.11309897013903854, 0.11108143017195383, 0.10739738617028358, 0.10603954095836655, 0.14723912576358572, 0.11138088070907391, 0.13193374185687462, 0.11546370811414708, 0.14968279066957121, 0.10728093887363854, 0.11224933379927363, 0.1531536916122009, 0.21130165374224438, 0.10790067438979271, 0.145274298151255, 0.10809409659846259, 0.16454685959707555, 0.11986873258641192, 0.1093919508048078, 0.15214492456046252, 0.12241689007127254, 0.15233828520794385, 0.1477002670266664, 0.11682125160422556, 0.1612450145107434, 0.11462144119638207, 0.17029741429213843, 0.17666313203034684, 0.13046982628625792, 0.11452315015346587, 0.11159108337844098, 0.11278996481683422, 0.13407981337896288, 0.14060699419859812, 0.17046302556931262, 0.19509018799805197, 0.12598638724298403, 0.11466884915425202, 0.1607359447695591, 0.12116741727689816, 0.12279811064457224, 0.11340971826279163, 0.1303229762303293, 0.1722897020405344, 0.1148431646196073, 0.11229024346021345, 0.13169130404526172, 0.16578175283619956, 0.14908639876681473, 0.114158475241508, 0.14060348197898215, 0.1769387683187289, 0.12257616509694474, 0.1102774362877409, 0.13969536569060098, 0.11971147899497465, 0.11235779184303205, 0.1506955870487662, 0.11301449885252206, 0.12023191288769444, 0.11889625471725013, 0.11195282415528253, 0.10796394387973061, 0.1241821107589637, 0.15486676574005767, 0.14209648959527185, 0.16354623814002167, 0.10783557610989845]]
    lossveclist = lossveclist6 + lossveclist30
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.1$, $n=6,30$',legendlabel=['$n=6$','$n=30$'])
    '''

    ### overEstWt=5, rateTarget=0.1 ###
    # Get null first
    underWt, t = 5., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Design 0']
    lossvec = [[0.38583050924760964, 0.3805864077666326, 0.3964572768521591, 0.39227940704631165, 0.38564747589892073, 0.4033297784195582, 0.3975594889356481, 0.38863941640280203, 0.39286843713196895, 0.40201595286213565, 0.3778915589617121, 0.3732185650748028, 0.3921299976939237, 0.3846437304838668, 0.370628076035751, 0.4163607349815971, 0.396812865270099, 0.4155841835048091, 0.39587207709718675, 0.3829018469947969, 0.37800872529449936, 0.3963409862604907, 0.3789195541773716, 0.3790216064601415, 0.37228800287802993, 0.387929035196919, 0.39807375276496215, 0.3755987269229184, 0.3777473118766184, 0.38924578912330493, 0.38364387791698773, 0.38336904970923336, 0.3964706086800771, 0.3961262658187449, 0.38351666107797355, 0.40243811863426426, 0.3765660331020353, 0.38636196577719445, 0.3862189193660726, 0.3789616394474292, 0.3994137692631588, 0.3630902987236733, 0.39053855570977764, 0.40471699127502836, 0.39495257051396687, 0.3917768637550916, 0.386662841787641, 0.3820399538295663, 0.38782166421577, 0.3599592083551056, 0.3521884873328863, 0.38801406010871026, 0.3843276063895806, 0.3849402399967776, 0.40050510795022387, 0.4001304747855865, 0.38179263483054254, 0.3883680882622218, 0.37079516976196913, 0.37433781481426415, 0.3971214064327556, 0.3954597264763028, 0.39415072785293254, 0.36578702569154103, 0.3907533573541796, 0.3733732889162066, 0.4162197743753949, 0.38124504576180185, 0.40706208518614867, 0.42404348956088833, 0.3978984991900868, 0.41343299046418513, 0.3723546390001216, 0.36438198681397677, 0.3793977830813166, 0.3797484759869667, 0.38560903524390217, 0.39436162294505395, 0.39678907121771156, 0.3858027079501557, 0.377679219869191, 0.3913883828557191, 0.40750921332915535, 0.3874264156995278, 0.3779728450969454, 0.40969185272006436, 0.3897072956140699, 0.3859038430577251, 0.41547253745821033, 0.39186748425445406, 0.39633032528738044, 0.3795551822745309, 0.38500829485553184, 0.425305775265033, 0.3813767248171227, 0.37723107855392307, 0.3870630517285677, 0.3827646817180149, 0.3744239179978639, 0.38843358384701454]]
    '''
    # 30 tests for all designs
    underWt, t = 5., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossvec0 = [[0.38583050924760964, 0.3805864077666326, 0.3964572768521591, 0.39227940704631165, 0.38564747589892073, 0.4033297784195582, 0.3975594889356481, 0.38863941640280203, 0.39286843713196895, 0.40201595286213565, 0.3778915589617121, 0.3732185650748028, 0.3921299976939237, 0.3846437304838668, 0.370628076035751, 0.4163607349815971, 0.396812865270099, 0.4155841835048091, 0.39587207709718675, 0.3829018469947969, 0.37800872529449936, 0.3963409862604907, 0.3789195541773716, 0.3790216064601415, 0.37228800287802993, 0.387929035196919, 0.39807375276496215, 0.3755987269229184, 0.3777473118766184, 0.38924578912330493, 0.38364387791698773, 0.38336904970923336, 0.3964706086800771, 0.3961262658187449, 0.38351666107797355, 0.40243811863426426, 0.3765660331020353, 0.38636196577719445, 0.3862189193660726, 0.3789616394474292, 0.3994137692631588, 0.3630902987236733, 0.39053855570977764, 0.40471699127502836, 0.39495257051396687, 0.3917768637550916, 0.386662841787641, 0.3820399538295663, 0.38782166421577, 0.3599592083551056, 0.3521884873328863, 0.38801406010871026, 0.3843276063895806, 0.3849402399967776, 0.40050510795022387, 0.4001304747855865, 0.38179263483054254, 0.3883680882622218, 0.37079516976196913, 0.37433781481426415, 0.3971214064327556, 0.3954597264763028, 0.39415072785293254, 0.36578702569154103, 0.3907533573541796, 0.3733732889162066, 0.4162197743753949, 0.38124504576180185, 0.40706208518614867, 0.42404348956088833, 0.3978984991900868, 0.41343299046418513, 0.3723546390001216, 0.36438198681397677, 0.3793977830813166, 0.3797484759869667, 0.38560903524390217, 0.39436162294505395, 0.39678907121771156, 0.3858027079501557, 0.377679219869191, 0.3913883828557191, 0.40750921332915535, 0.3874264156995278, 0.3779728450969454, 0.40969185272006436, 0.3897072956140699, 0.3859038430577251, 0.41547253745821033, 0.39186748425445406, 0.39633032528738044, 0.3795551822745309, 0.38500829485553184, 0.425305775265033, 0.3813767248171227, 0.37723107855392307, 0.3870630517285677, 0.3827646817180149, 0.3744239179978639, 0.38843358384701454]]
    lossveclist = [[0.3329667804058439, 0.3048359499798749, 0.3266234011025496, 0.3300925197530628, 0.32626058972069205, 0.3501823303837523, 0.3019848965597553, 0.367305983682519, 0.31532807586565104, 0.29617613867148274, 0.3202952734221463, 0.2966100919595709, 0.29185844246237985, 0.333494902544, 0.32377699415947875, 0.3648353865755433, 0.31165300232381093, 0.3149377765212943, 0.304713416352935, 0.3369063522218454, 0.3491460413973439, 0.32340668312695464, 0.31643202401811804, 0.30810928025544665, 0.3624048459507057, 0.2991501541974906, 0.40242749072617956, 0.3249012094831088, 0.37535827352207213, 0.3001134934112857, 0.30749366420997354, 0.28951256452255814, 0.3116339157979734, 0.33004294380778293, 0.3005564270778042, 0.32680765996264294, 0.3493550928063728, 0.31078248805487313, 0.32926446623807676, 0.34144524937464726, 0.42689250273150703, 0.3127238410942225, 0.3480688567440682, 0.33734680085678026, 0.33337041256965694, 0.30181968547185545, 0.32324237715916376, 0.28920919026530056, 0.33262757611164456, 0.34130445038968366, 0.30494481906578896, 0.3107883296991158, 0.32721812630874103, 0.3341209256075047, 0.3555900307432099, 0.334480509726279, 0.32154623005739535, 0.30147161679072015, 0.33261109938595884, 0.3160214992502357, 0.2952182071940258, 0.330839120480065, 0.3988745182203615, 0.3248261535979973, 0.3557744279632362, 0.3160436613203665, 0.3235828713468373, 0.31185240516158713, 0.36886219946986043, 0.30617411043042686, 0.323323678954806, 0.3224875359937501, 0.37066699700201405, 0.320431670841849, 0.34105896327818924, 0.40514373951382265, 0.3415263393263826, 0.3238820845567901, 0.2999717157435513, 0.35972502851167487, 0.3401627042310587, 0.32834258132916605, 0.31751592678703944, 0.31495506649014454, 0.3303513406088176, 0.3155825782123415, 0.38613688566146864, 0.3790935177071438, 0.31946500807267375, 0.35364127564523784, 0.32924538917396134, 0.33474552540010605, 0.3624847226467893, 0.34184056372179483, 0.3095423710477023, 0.3160117319932685, 0.38629853216249144, 0.39164687853309227, 0.3041061965463162, 0.30715438430876174], [0.257744672193433, 0.2888282893260882, 0.2901967291431233, 0.36591784640056557, 0.3171150994792345, 0.3268690739537106, 0.2870565638990402, 0.277642628344871, 0.2878614422011107, 0.3416259772147256, 0.2868908924597531, 0.25435820755740235, 0.3201225115254679, 0.28900086827705584, 0.3247122266805658, 0.32274595944547, 0.26974593069837133, 0.24804695511489838, 0.2882192703765516, 0.3085546277656395, 0.2790445687010042, 0.3997654008090266, 0.3431249822718958, 0.2670844048171432, 0.27468736870667443, 0.40811967060997645, 0.3336883830760252, 0.32736895298207463, 0.3638344205700433, 0.28071888985169197, 0.31548301424789127, 0.2658119898358638, 0.3144222219139029, 0.2773339734963488, 0.2643265589305023, 0.3304221468268236, 0.2837543892331195, 0.28207890362419147, 0.3224202772083998, 0.28976518833222786, 0.36489014731529884, 0.26861371461889444, 0.27342079429286814, 0.3485126920581061, 0.373672433886348, 0.2606599306682989, 0.35300058499617565, 0.325378005703378, 0.36421648447543603, 0.3142262070537773, 0.28142678848861485, 0.2648293494978105, 0.3615658768085725, 0.34129474666402204, 0.31278503723393064, 0.3439709275527221, 0.2734962672790807, 0.30320827464067623, 0.36685898022551244, 0.3119651950581767, 0.28414994474494887, 0.2727001264787752, 0.2750764175846625, 0.2787894563019702, 0.3111676679988612, 0.30601021299315334, 0.358850091805662, 0.3217321722426368, 0.2869692214909194, 0.2611604824378423, 0.3125289659489906, 0.2716431619596077, 0.3185368782839191, 0.2901512953616564, 0.4265441908943728, 0.3739639860627874, 0.3227704481847098, 0.34918347302843783, 0.28770403595903943, 0.3638759804839394, 0.325876591026501, 0.2743090260974319, 0.26951665102161304, 0.34617002949759795, 0.2879157201496528, 0.2714454872326279, 0.29052393777697727, 0.28497151453611125, 0.2768038752965317, 0.388542890111358, 0.4152627193867274, 0.2809453669098231, 0.37558892553035333, 0.2945813967084882, 0.27362895596173775, 0.2754686138213334, 0.2985831372253059, 0.3205100290338167, 0.3156509354134721, 0.2616404890825223], [0.2971372848085235, 0.35762217155900466, 0.35385325710721877, 0.3702910219950034, 0.3281505564743439, 0.29370397728457054, 0.34385880434475385, 0.3166875848537482, 0.28711821267733917, 0.31960297343124167, 0.3287950717482092, 0.30602032758323067, 0.3245162663731173, 0.30263957146727255, 0.3080288845662064, 0.3191358064157132, 0.3336561111668203, 0.3020049251654214, 0.29366062906390944, 0.3354367136352083, 0.3060617749182091, 0.33765488479915423, 0.2981321730380433, 0.31675537561243855, 0.33144974932492477, 0.3203108931482405, 0.3455339254291077, 0.3390319916489087, 0.35964676417029556, 0.32714633912342217, 0.31180190739014224, 0.3246837449201044, 0.3439460821428756, 0.31834482581395, 0.32410223131351623, 0.29064478849470415, 0.29544324807603084, 0.31643546827222097, 0.3003677785570731, 0.3707633921620287, 0.3705100062938896, 0.3260261944386248, 0.28922043070036013, 0.3727390383977527, 0.3612814309321848, 0.2898347610305933, 0.308655862138811, 0.32068989867480513, 0.3212752732329235, 0.31121845724389424, 0.31146406365419865, 0.32079669555769974, 0.3772586589003442, 0.35774980284852453, 0.33132655200791156, 0.31806753811198374, 0.3180162892195609, 0.379841747323475, 0.32925548863345816, 0.3316329429576724, 0.3254057710175776, 0.3081841541004256, 0.3811282275666344, 0.3253769422189844, 0.34276453427111003, 0.3147585987998821, 0.3323067737413986, 0.32960629319648604, 0.31195743482695343, 0.3265507538043866, 0.34167330292080733, 0.3128289943257615, 0.3083990375579971, 0.34578387156746443, 0.3774411995310438, 0.35844862562115065, 0.35933682391684624, 0.3151991613549101, 0.35597247252921743, 0.3653704537318449, 0.31482451678229534, 0.2993137066904835, 0.3224659035028097, 0.31161008485261216, 0.35080130341923366, 0.31457444985976707, 0.33070790042469406, 0.33060137203603207, 0.32266753715854046, 0.30153067123385163, 0.3126972595959515, 0.32206168540715135, 0.34940405344871583, 0.3175975150190243, 0.3323692871629586, 0.3293087069021818, 0.3437838537557757, 0.36868077210401734, 0.30305061698366426, 0.2909139802412572], [0.35356529701848344, 0.4032892118305581, 0.3666916789174621, 0.37414534220441203, 0.41339754963342606, 0.3650075429475535, 0.3638280528321904, 0.3706117395305753, 0.34484980365998535, 0.34947826787595204, 0.36293118431169896, 0.39777018837995237, 0.37051801439339094, 0.33242757441202636, 0.3454489726144909, 0.3898779359473969, 0.3730032198204712, 0.34560848688438767, 0.3961808984205089, 0.35241029925525186, 0.35449236127665557, 0.3373068261816929, 0.39671977931980557, 0.34742860727554015, 0.321888523157417, 0.3391927991009402, 0.35605200523692454, 0.413418683118677, 0.3448657743992822, 0.384564172750384, 0.3675818480608681, 0.4010914631361711, 0.3836213424474641, 0.35152759162088043, 0.3934390509656022, 0.33072556462828717, 0.39479440057418963, 0.3772873878751645, 0.40354996529455284, 0.3534787425225339, 0.350747846091642, 0.38930146039855285, 0.4371534032728228, 0.33176030733605305, 0.3277196567777504, 0.34526292325712826, 0.3600341299437397, 0.4265450784796103, 0.3768900231158572, 0.3671982579876948, 0.342985361624469, 0.40698902774398743, 0.3974677021826256, 0.34769866808955424, 0.36803630766271117, 0.3480113910200984, 0.38014193271963237, 0.35861685931995674, 0.3660023414834283, 0.3509626893118353, 0.43261471539369434, 0.3434195219556941, 0.43289763330993736, 0.3557562346435377, 0.3677557442907097, 0.3585392512388753, 0.36002509765489094, 0.4039236741719207, 0.3302331347675313, 0.3384302673130634, 0.3912543199252675, 0.36195503076887225, 0.3870612990572529, 0.37169798351745087, 0.37893949945563854, 0.3556280393682289, 0.34067598416874556, 0.4254345854928101, 0.36678465843503866, 0.3698805191641889, 0.36741117053823164, 0.3931359425939009, 0.3610175347813763, 0.3640773097193725, 0.40471306050996353, 0.3396721810313701, 0.34972862648505765, 0.37964392533739, 0.41465348721822215, 0.3765072496999728, 0.3749019098933063, 0.3685258245398581, 0.3578432940643401, 0.32283307778712556, 0.3721612481565758, 0.39342951287169947, 0.3493596187034876, 0.38102720143508045, 0.3802085326063193, 0.35479091039985794], [0.2909535132172833, 0.28639432025279943, 0.31002170348393754, 0.3557225498701889, 0.2701812337849923, 0.3796496905898643, 0.32961006577458096, 0.32101094535898517, 0.2735528291170695, 0.3181618358152692, 0.281477886796332, 0.2533419996154258, 0.38340286078197316, 0.31713695137537357, 0.27198894492752373, 0.27893435571351644, 0.3580507419193977, 0.2937241604166047, 0.36498684648980284, 0.3193224057471958, 0.2787594175632516, 0.27946901574906197, 0.3341249242714609, 0.28290314405912675, 0.34558853585313415, 0.2634440522618092, 0.32333098209529665, 0.32299571883136446, 0.3688137825081031, 0.25893221646762005, 0.26197328080629434, 0.3153340647118162, 0.30358241016471343, 0.29999726539412547, 0.2439868408219093, 0.31541252770210965, 0.3346652956167079, 0.27234267970712567, 0.3020528858079882, 0.25890497325295375, 0.48111604182284945, 0.29828003079817006, 0.3879895771271837, 0.27174447734469226, 0.4875665395288702, 0.3199611689606256, 0.3127659130669512, 0.3061562241037725, 0.32675163074457203, 0.2750079242995154, 0.26558582169471107, 0.2722111481473132, 0.33956816231022036, 0.2511668241445802, 0.34193628128384973, 0.30082588852034176, 0.3194779473415008, 0.3261247520202487, 0.2997072728876144, 0.3165915045530357, 0.32885243150711857, 0.2727439263926215, 0.2885115135747382, 0.2682764781682688, 0.28048394752785544, 0.38310211346995265, 0.35004693520327396, 0.2752434059321424, 0.27822713780706976, 0.27355578916410467, 0.273754010097165, 0.31131086127235885, 0.2978646733211123, 0.314043692798358, 0.27908342684977766, 0.41541712269898273, 0.267822188540555, 0.29591137407231805, 0.317239572463381, 0.33403728358282775, 0.32500302043173446, 0.30077584627937726, 0.32470883157553737, 0.3486453735810313, 0.2723729735032787, 0.26731946506888626, 0.27027713259453584, 0.33131196193872037, 0.33696028182315685, 0.3365637788531622, 0.37858454124556273, 0.3099396029242762, 0.34796764962420057, 0.33908304465345124, 0.3695276257801136, 0.30025985170412967, 0.27605496212734726, 0.29041288820591066, 0.3479162355156688, 0.32860211523162447], [0.34793463649590334, 0.26706073373476114, 0.2944198997673966, 0.32269357102063906, 0.30699320197284036, 0.2736804932800819, 0.2628851121741416, 0.2665887541224424, 0.2627656951148074, 0.3680115508842532, 0.26561764071196453, 0.3489352792164511, 0.48140800445512416, 0.2819965976461444, 0.34328250649121816, 0.34125464938942457, 0.3167919651605555, 0.27278822214789095, 0.33055563334567484, 0.2758995092221616, 0.29083187683627204, 0.31817541704323826, 0.3511722866872512, 0.2595267058068628, 0.2924862024899678, 0.2448737718212477, 0.3188153625886802, 0.3141115354071789, 0.3499493106689039, 0.26267214160180646, 0.27842900307930185, 0.31203925937680843, 0.273888133079002, 0.27808981165018226, 0.24637427384015448, 0.27767008520055914, 0.31591584998777195, 0.2856687687079382, 0.25915766990365674, 0.2824758342956606, 0.424390600761535, 0.2844436801297481, 0.2688860097825145, 0.42715404781335753, 0.48504907244714945, 0.24233730512178725, 0.3475879377286157, 0.26514173098674515, 0.27365921475176963, 0.2626020421737361, 0.2606251275317717, 0.33697669770871735, 0.3692646883491512, 0.2818296916377751, 0.34011528782066486, 0.2750214427590449, 0.2779441751130232, 0.28986558347036895, 0.3360750587601039, 0.34896666182125574, 0.25741678444382654, 0.26992364373844496, 0.2988976168426383, 0.27660576795784403, 0.27506749553060433, 0.2687373843381487, 0.3116717322857473, 0.3430677280034757, 0.3012900321927989, 0.35192554656869585, 0.28176396507171814, 0.28836280087240757, 0.3427865639849126, 0.311909735452995, 0.27518587621049373, 0.34115439109105217, 0.2829736940852685, 0.3250174281180645, 0.2718225828180446, 0.34034663582711416, 0.27929015895430653, 0.28179603621572186, 0.3143326186952946, 0.34732473161012123, 0.27755617983918773, 0.254501765146523, 0.33083470071538124, 0.28812645836642176, 0.26725548044031916, 0.26723153087647683, 0.3489044751946007, 0.295831565237281, 0.3296854527125243, 0.2918831236977706, 0.34755181836759075, 0.30174910051510173, 0.3131761931284442, 0.329102783817209, 0.24091996123984383, 0.30970600337668514]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=5$, $l=0.1$, $n=30$')
    
    lossvec0 = [[0.38583050924760964, 0.3805864077666326, 0.3964572768521591, 0.39227940704631165, 0.38564747589892073, 0.4033297784195582, 0.3975594889356481, 0.38863941640280203, 0.39286843713196895, 0.40201595286213565, 0.3778915589617121, 0.3732185650748028, 0.3921299976939237, 0.3846437304838668, 0.370628076035751, 0.4163607349815971, 0.396812865270099, 0.4155841835048091, 0.39587207709718675, 0.3829018469947969, 0.37800872529449936, 0.3963409862604907, 0.3789195541773716, 0.3790216064601415, 0.37228800287802993, 0.387929035196919, 0.39807375276496215, 0.3755987269229184, 0.3777473118766184, 0.38924578912330493, 0.38364387791698773, 0.38336904970923336, 0.3964706086800771, 0.3961262658187449, 0.38351666107797355, 0.40243811863426426, 0.3765660331020353, 0.38636196577719445, 0.3862189193660726, 0.3789616394474292, 0.3994137692631588, 0.3630902987236733, 0.39053855570977764, 0.40471699127502836, 0.39495257051396687, 0.3917768637550916, 0.386662841787641, 0.3820399538295663, 0.38782166421577, 0.3599592083551056, 0.3521884873328863, 0.38801406010871026, 0.3843276063895806, 0.3849402399967776, 0.40050510795022387, 0.4001304747855865, 0.38179263483054254, 0.3883680882622218, 0.37079516976196913, 0.37433781481426415, 0.3971214064327556, 0.3954597264763028, 0.39415072785293254, 0.36578702569154103, 0.3907533573541796, 0.3733732889162066, 0.4162197743753949, 0.38124504576180185, 0.40706208518614867, 0.42404348956088833, 0.3978984991900868, 0.41343299046418513, 0.3723546390001216, 0.36438198681397677, 0.3793977830813166, 0.3797484759869667, 0.38560903524390217, 0.39436162294505395, 0.39678907121771156, 0.3858027079501557, 0.377679219869191, 0.3913883828557191, 0.40750921332915535, 0.3874264156995278, 0.3779728450969454, 0.40969185272006436, 0.3897072956140699, 0.3859038430577251, 0.41547253745821033, 0.39186748425445406, 0.39633032528738044, 0.3795551822745309, 0.38500829485553184, 0.425305775265033, 0.3813767248171227, 0.37723107855392307, 0.3870630517285677, 0.3827646817180149, 0.3744239179978639, 0.38843358384701454]]
    lossveclist = [[0.3329667804058439, 0.3048359499798749, 0.3266234011025496, 0.3300925197530628, 0.32626058972069205, 0.3501823303837523, 0.3019848965597553, 0.367305983682519, 0.31532807586565104, 0.29617613867148274, 0.3202952734221463, 0.2966100919595709, 0.29185844246237985, 0.333494902544, 0.32377699415947875, 0.3648353865755433, 0.31165300232381093, 0.3149377765212943, 0.304713416352935, 0.3369063522218454, 0.3491460413973439, 0.32340668312695464, 0.31643202401811804, 0.30810928025544665, 0.3624048459507057, 0.2991501541974906, 0.40242749072617956, 0.3249012094831088, 0.37535827352207213, 0.3001134934112857, 0.30749366420997354, 0.28951256452255814, 0.3116339157979734, 0.33004294380778293, 0.3005564270778042, 0.32680765996264294, 0.3493550928063728, 0.31078248805487313, 0.32926446623807676, 0.34144524937464726, 0.42689250273150703, 0.3127238410942225, 0.3480688567440682, 0.33734680085678026, 0.33337041256965694, 0.30181968547185545, 0.32324237715916376, 0.28920919026530056, 0.33262757611164456, 0.34130445038968366, 0.30494481906578896, 0.3107883296991158, 0.32721812630874103, 0.3341209256075047, 0.3555900307432099, 0.334480509726279, 0.32154623005739535, 0.30147161679072015, 0.33261109938595884, 0.3160214992502357, 0.2952182071940258, 0.330839120480065, 0.3988745182203615, 0.3248261535979973, 0.3557744279632362, 0.3160436613203665, 0.3235828713468373, 0.31185240516158713, 0.36886219946986043, 0.30617411043042686, 0.323323678954806, 0.3224875359937501, 0.37066699700201405, 0.320431670841849, 0.34105896327818924, 0.40514373951382265, 0.3415263393263826, 0.3238820845567901, 0.2999717157435513, 0.35972502851167487, 0.3401627042310587, 0.32834258132916605, 0.31751592678703944, 0.31495506649014454, 0.3303513406088176, 0.3155825782123415, 0.38613688566146864, 0.3790935177071438, 0.31946500807267375, 0.35364127564523784, 0.32924538917396134, 0.33474552540010605, 0.3624847226467893, 0.34184056372179483, 0.3095423710477023, 0.3160117319932685, 0.38629853216249144, 0.39164687853309227, 0.3041061965463162, 0.30715438430876174], [0.257744672193433, 0.2888282893260882, 0.2901967291431233, 0.36591784640056557, 0.3171150994792345, 0.3268690739537106, 0.2870565638990402, 0.277642628344871, 0.2878614422011107, 0.3416259772147256, 0.2868908924597531, 0.25435820755740235, 0.3201225115254679, 0.28900086827705584, 0.3247122266805658, 0.32274595944547, 0.26974593069837133, 0.24804695511489838, 0.2882192703765516, 0.3085546277656395, 0.2790445687010042, 0.3997654008090266, 0.3431249822718958, 0.2670844048171432, 0.27468736870667443, 0.40811967060997645, 0.3336883830760252, 0.32736895298207463, 0.3638344205700433, 0.28071888985169197, 0.31548301424789127, 0.2658119898358638, 0.3144222219139029, 0.2773339734963488, 0.2643265589305023, 0.3304221468268236, 0.2837543892331195, 0.28207890362419147, 0.3224202772083998, 0.28976518833222786, 0.36489014731529884, 0.26861371461889444, 0.27342079429286814, 0.3485126920581061, 0.373672433886348, 0.2606599306682989, 0.35300058499617565, 0.325378005703378, 0.36421648447543603, 0.3142262070537773, 0.28142678848861485, 0.2648293494978105, 0.3615658768085725, 0.34129474666402204, 0.31278503723393064, 0.3439709275527221, 0.2734962672790807, 0.30320827464067623, 0.36685898022551244, 0.3119651950581767, 0.28414994474494887, 0.2727001264787752, 0.2750764175846625, 0.2787894563019702, 0.3111676679988612, 0.30601021299315334, 0.358850091805662, 0.3217321722426368, 0.2869692214909194, 0.2611604824378423, 0.3125289659489906, 0.2716431619596077, 0.3185368782839191, 0.2901512953616564, 0.4265441908943728, 0.3739639860627874, 0.3227704481847098, 0.34918347302843783, 0.28770403595903943, 0.3638759804839394, 0.325876591026501, 0.2743090260974319, 0.26951665102161304, 0.34617002949759795, 0.2879157201496528, 0.2714454872326279, 0.29052393777697727, 0.28497151453611125, 0.2768038752965317, 0.388542890111358, 0.4152627193867274, 0.2809453669098231, 0.37558892553035333, 0.2945813967084882, 0.27362895596173775, 0.2754686138213334, 0.2985831372253059, 0.3205100290338167, 0.3156509354134721, 0.2616404890825223], [0.2971372848085235, 0.35762217155900466, 0.35385325710721877, 0.3702910219950034, 0.3281505564743439, 0.29370397728457054, 0.34385880434475385, 0.3166875848537482, 0.28711821267733917, 0.31960297343124167, 0.3287950717482092, 0.30602032758323067, 0.3245162663731173, 0.30263957146727255, 0.3080288845662064, 0.3191358064157132, 0.3336561111668203, 0.3020049251654214, 0.29366062906390944, 0.3354367136352083, 0.3060617749182091, 0.33765488479915423, 0.2981321730380433, 0.31675537561243855, 0.33144974932492477, 0.3203108931482405, 0.3455339254291077, 0.3390319916489087, 0.35964676417029556, 0.32714633912342217, 0.31180190739014224, 0.3246837449201044, 0.3439460821428756, 0.31834482581395, 0.32410223131351623, 0.29064478849470415, 0.29544324807603084, 0.31643546827222097, 0.3003677785570731, 0.3707633921620287, 0.3705100062938896, 0.3260261944386248, 0.28922043070036013, 0.3727390383977527, 0.3612814309321848, 0.2898347610305933, 0.308655862138811, 0.32068989867480513, 0.3212752732329235, 0.31121845724389424, 0.31146406365419865, 0.32079669555769974, 0.3772586589003442, 0.35774980284852453, 0.33132655200791156, 0.31806753811198374, 0.3180162892195609, 0.379841747323475, 0.32925548863345816, 0.3316329429576724, 0.3254057710175776, 0.3081841541004256, 0.3811282275666344, 0.3253769422189844, 0.34276453427111003, 0.3147585987998821, 0.3323067737413986, 0.32960629319648604, 0.31195743482695343, 0.3265507538043866, 0.34167330292080733, 0.3128289943257615, 0.3083990375579971, 0.34578387156746443, 0.3774411995310438, 0.35844862562115065, 0.35933682391684624, 0.3151991613549101, 0.35597247252921743, 0.3653704537318449, 0.31482451678229534, 0.2993137066904835, 0.3224659035028097, 0.31161008485261216, 0.35080130341923366, 0.31457444985976707, 0.33070790042469406, 0.33060137203603207, 0.32266753715854046, 0.30153067123385163, 0.3126972595959515, 0.32206168540715135, 0.34940405344871583, 0.3175975150190243, 0.3323692871629586, 0.3293087069021818, 0.3437838537557757, 0.36868077210401734, 0.30305061698366426, 0.2909139802412572], [0.35356529701848344, 0.4032892118305581, 0.3666916789174621, 0.37414534220441203, 0.41339754963342606, 0.3650075429475535, 0.3638280528321904, 0.3706117395305753, 0.34484980365998535, 0.34947826787595204, 0.36293118431169896, 0.39777018837995237, 0.37051801439339094, 0.33242757441202636, 0.3454489726144909, 0.3898779359473969, 0.3730032198204712, 0.34560848688438767, 0.3961808984205089, 0.35241029925525186, 0.35449236127665557, 0.3373068261816929, 0.39671977931980557, 0.34742860727554015, 0.321888523157417, 0.3391927991009402, 0.35605200523692454, 0.413418683118677, 0.3448657743992822, 0.384564172750384, 0.3675818480608681, 0.4010914631361711, 0.3836213424474641, 0.35152759162088043, 0.3934390509656022, 0.33072556462828717, 0.39479440057418963, 0.3772873878751645, 0.40354996529455284, 0.3534787425225339, 0.350747846091642, 0.38930146039855285, 0.4371534032728228, 0.33176030733605305, 0.3277196567777504, 0.34526292325712826, 0.3600341299437397, 0.4265450784796103, 0.3768900231158572, 0.3671982579876948, 0.342985361624469, 0.40698902774398743, 0.3974677021826256, 0.34769866808955424, 0.36803630766271117, 0.3480113910200984, 0.38014193271963237, 0.35861685931995674, 0.3660023414834283, 0.3509626893118353, 0.43261471539369434, 0.3434195219556941, 0.43289763330993736, 0.3557562346435377, 0.3677557442907097, 0.3585392512388753, 0.36002509765489094, 0.4039236741719207, 0.3302331347675313, 0.3384302673130634, 0.3912543199252675, 0.36195503076887225, 0.3870612990572529, 0.37169798351745087, 0.37893949945563854, 0.3556280393682289, 0.34067598416874556, 0.4254345854928101, 0.36678465843503866, 0.3698805191641889, 0.36741117053823164, 0.3931359425939009, 0.3610175347813763, 0.3640773097193725, 0.40471306050996353, 0.3396721810313701, 0.34972862648505765, 0.37964392533739, 0.41465348721822215, 0.3765072496999728, 0.3749019098933063, 0.3685258245398581, 0.3578432940643401, 0.32283307778712556, 0.3721612481565758, 0.39342951287169947, 0.3493596187034876, 0.38102720143508045, 0.3802085326063193, 0.35479091039985794], [0.2909535132172833, 0.28639432025279943, 0.31002170348393754, 0.3557225498701889, 0.2701812337849923, 0.3796496905898643, 0.32961006577458096, 0.32101094535898517, 0.2735528291170695, 0.3181618358152692, 0.281477886796332, 0.2533419996154258, 0.38340286078197316, 0.31713695137537357, 0.27198894492752373, 0.27893435571351644, 0.3580507419193977, 0.2937241604166047, 0.36498684648980284, 0.3193224057471958, 0.2787594175632516, 0.27946901574906197, 0.3341249242714609, 0.28290314405912675, 0.34558853585313415, 0.2634440522618092, 0.32333098209529665, 0.32299571883136446, 0.3688137825081031, 0.25893221646762005, 0.26197328080629434, 0.3153340647118162, 0.30358241016471343, 0.29999726539412547, 0.2439868408219093, 0.31541252770210965, 0.3346652956167079, 0.27234267970712567, 0.3020528858079882, 0.25890497325295375, 0.48111604182284945, 0.29828003079817006, 0.3879895771271837, 0.27174447734469226, 0.4875665395288702, 0.3199611689606256, 0.3127659130669512, 0.3061562241037725, 0.32675163074457203, 0.2750079242995154, 0.26558582169471107, 0.2722111481473132, 0.33956816231022036, 0.2511668241445802, 0.34193628128384973, 0.30082588852034176, 0.3194779473415008, 0.3261247520202487, 0.2997072728876144, 0.3165915045530357, 0.32885243150711857, 0.2727439263926215, 0.2885115135747382, 0.2682764781682688, 0.28048394752785544, 0.38310211346995265, 0.35004693520327396, 0.2752434059321424, 0.27822713780706976, 0.27355578916410467, 0.273754010097165, 0.31131086127235885, 0.2978646733211123, 0.314043692798358, 0.27908342684977766, 0.41541712269898273, 0.267822188540555, 0.29591137407231805, 0.317239572463381, 0.33403728358282775, 0.32500302043173446, 0.30077584627937726, 0.32470883157553737, 0.3486453735810313, 0.2723729735032787, 0.26731946506888626, 0.27027713259453584, 0.33131196193872037, 0.33696028182315685, 0.3365637788531622, 0.37858454124556273, 0.3099396029242762, 0.34796764962420057, 0.33908304465345124, 0.3695276257801136, 0.30025985170412967, 0.27605496212734726, 0.29041288820591066, 0.3479162355156688, 0.32860211523162447], [0.34793463649590334, 0.26706073373476114, 0.2944198997673966, 0.32269357102063906, 0.30699320197284036, 0.2736804932800819, 0.2628851121741416, 0.2665887541224424, 0.2627656951148074, 0.3680115508842532, 0.26561764071196453, 0.3489352792164511, 0.48140800445512416, 0.2819965976461444, 0.34328250649121816, 0.34125464938942457, 0.3167919651605555, 0.27278822214789095, 0.33055563334567484, 0.2758995092221616, 0.29083187683627204, 0.31817541704323826, 0.3511722866872512, 0.2595267058068628, 0.2924862024899678, 0.2448737718212477, 0.3188153625886802, 0.3141115354071789, 0.3499493106689039, 0.26267214160180646, 0.27842900307930185, 0.31203925937680843, 0.273888133079002, 0.27808981165018226, 0.24637427384015448, 0.27767008520055914, 0.31591584998777195, 0.2856687687079382, 0.25915766990365674, 0.2824758342956606, 0.424390600761535, 0.2844436801297481, 0.2688860097825145, 0.42715404781335753, 0.48504907244714945, 0.24233730512178725, 0.3475879377286157, 0.26514173098674515, 0.27365921475176963, 0.2626020421737361, 0.2606251275317717, 0.33697669770871735, 0.3692646883491512, 0.2818296916377751, 0.34011528782066486, 0.2750214427590449, 0.2779441751130232, 0.28986558347036895, 0.3360750587601039, 0.34896666182125574, 0.25741678444382654, 0.26992364373844496, 0.2988976168426383, 0.27660576795784403, 0.27506749553060433, 0.2687373843381487, 0.3116717322857473, 0.3430677280034757, 0.3012900321927989, 0.35192554656869585, 0.28176396507171814, 0.28836280087240757, 0.3427865639849126, 0.311909735452995, 0.27518587621049373, 0.34115439109105217, 0.2829736940852685, 0.3250174281180645, 0.2718225828180446, 0.34034663582711416, 0.27929015895430653, 0.28179603621572186, 0.3143326186952946, 0.34732473161012123, 0.27755617983918773, 0.254501765146523, 0.33083470071538124, 0.28812645836642176, 0.26725548044031916, 0.26723153087647683, 0.3489044751946007, 0.295831565237281, 0.3296854527125243, 0.2918831236977706, 0.34755181836759075, 0.30174910051510173, 0.3131761931284442, 0.329102783817209, 0.24091996123984383, 0.30970600337668514]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### overEstWt=0.2, rateTarget=0.1 ###
    # Get null first
    underWt, t = 0.2, 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Design 0']
    lossvec = [[0.04874981168155717, 0.04601627598721148, 0.046602509349972523, 0.050586168495252604, 0.047650039131627096, 0.04900758374021014, 0.05083789310453001, 0.04815940526219456, 0.04894303779884694, 0.04872188439052756, 0.04596113107150889, 0.04533036788057144, 0.047702491234585545, 0.04605326438814462, 0.0445759009504151, 0.053495095666269976, 0.04786314057031166, 0.04960261382638776, 0.048985348721622135, 0.04767482107021301, 0.04715583207351171, 0.0476421221058353, 0.04696364472561235, 0.04691241877782879, 0.04513892571546784, 0.04654400401716812, 0.04892125037855425, 0.0455866952254014, 0.046053861253317854, 0.047858963944586455, 0.04881940384220125, 0.04737662377020264, 0.049525288614961915, 0.04957435122175646, 0.04575276971922458, 0.04960007226271745, 0.04824906144665322, 0.04810665616041669, 0.047014452407872546, 0.047600033676595356, 0.04839777879360045, 0.045558118647944186, 0.047518293650248594, 0.05036545697743948, 0.049412171532409094, 0.04856483735481838, 0.04754430576186313, 0.046404639783898714, 0.04646733894411559, 0.04443174099410009, 0.04350771594448622, 0.04825966263047179, 0.04778314333024609, 0.04821113384089001, 0.04797284516136274, 0.048938148885673535, 0.04687477057177605, 0.04670793693255172, 0.04495711920901903, 0.04735873038334376, 0.05014163434178577, 0.047774072750534476, 0.04683807874548834, 0.04655733411954765, 0.048538584046488004, 0.045772918950249715, 0.049308758668981205, 0.04680097274856691, 0.04714223637422627, 0.05147392076156743, 0.04874938178896028, 0.051631306011019514, 0.04493540958584115, 0.04595306111401679, 0.04643543723089674, 0.04715820518602384, 0.04857938775379486, 0.04739208539927517, 0.04798729370505646, 0.04720470339582102, 0.04780471892428656, 0.04721535246277248, 0.050363706530987845, 0.04699765461372573, 0.04592028467371892, 0.04890129988747958, 0.048202645680428875, 0.0487827386622787, 0.049712689106432645, 0.048768532287325035, 0.0482422597277323, 0.04691256438345368, 0.047261297155268917, 0.053601021618157114, 0.04745636245268635, 0.046792417128567285, 0.04759514246217367, 0.04665313645744631, 0.04604447426571351, 0.05065028847795186]]
    '''
    # 30 tests for all designs
    underWt, t = 0.2, 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossvec0 = [[0.04874981168155717, 0.04601627598721148, 0.046602509349972523, 0.050586168495252604, 0.047650039131627096, 0.04900758374021014, 0.05083789310453001, 0.04815940526219456, 0.04894303779884694, 0.04872188439052756, 0.04596113107150889, 0.04533036788057144, 0.047702491234585545, 0.04605326438814462, 0.0445759009504151, 0.053495095666269976, 0.04786314057031166, 0.04960261382638776, 0.048985348721622135, 0.04767482107021301, 0.04715583207351171, 0.0476421221058353, 0.04696364472561235, 0.04691241877782879, 0.04513892571546784, 0.04654400401716812, 0.04892125037855425, 0.0455866952254014, 0.046053861253317854, 0.047858963944586455, 0.04881940384220125, 0.04737662377020264, 0.049525288614961915, 0.04957435122175646, 0.04575276971922458, 0.04960007226271745, 0.04824906144665322, 0.04810665616041669, 0.047014452407872546, 0.047600033676595356, 0.04839777879360045, 0.045558118647944186, 0.047518293650248594, 0.05036545697743948, 0.049412171532409094, 0.04856483735481838, 0.04754430576186313, 0.046404639783898714, 0.04646733894411559, 0.04443174099410009, 0.04350771594448622, 0.04825966263047179, 0.04778314333024609, 0.04821113384089001, 0.04797284516136274, 0.048938148885673535, 0.04687477057177605, 0.04670793693255172, 0.04495711920901903, 0.04735873038334376, 0.05014163434178577, 0.047774072750534476, 0.04683807874548834, 0.04655733411954765, 0.048538584046488004, 0.045772918950249715, 0.049308758668981205, 0.04680097274856691, 0.04714223637422627, 0.05147392076156743, 0.04874938178896028, 0.051631306011019514, 0.04493540958584115, 0.04595306111401679, 0.04643543723089674, 0.04715820518602384, 0.04857938775379486, 0.04739208539927517, 0.04798729370505646, 0.04720470339582102, 0.04780471892428656, 0.04721535246277248, 0.050363706530987845, 0.04699765461372573, 0.04592028467371892, 0.04890129988747958, 0.048202645680428875, 0.0487827386622787, 0.049712689106432645, 0.048768532287325035, 0.0482422597277323, 0.04691256438345368, 0.047261297155268917, 0.053601021618157114, 0.04745636245268635, 0.046792417128567285, 0.04759514246217367, 0.04665313645744631, 0.04604447426571351, 0.05065028847795186]]
    lossveclist = [[0.03600387141169995, 0.0342730895471504, 0.037231245719616474, 0.03821681656593368, 0.036524971635385796, 0.03949410935896119, 0.03446591045419293, 0.0396743369833525, 0.035792210076944615, 0.033537117437739294, 0.03604002814257922, 0.03417521321342557, 0.033347089545724476, 0.03769482474517408, 0.03846517972190049, 0.0413523467226083, 0.036049512120723166, 0.03406534550385596, 0.03394704273824553, 0.03850120087976367, 0.03812376762208605, 0.03652952777060523, 0.03568045219506099, 0.03365921678428877, 0.040797963743401014, 0.03474034286476377, 0.05681018234607664, 0.03642466430890088, 0.042151979721033954, 0.0336656061000447, 0.03321807915010236, 0.03222030432492298, 0.035741544892543525, 0.03838025443578791, 0.033512676132623126, 0.03546218227682308, 0.03889728003774697, 0.0352736552930459, 0.035973969825781035, 0.03755704163857905, 0.06055880514457488, 0.03614881522940921, 0.038411144933868206, 0.03919233964066806, 0.03667805662919395, 0.03413958669579258, 0.03690343099030715, 0.03394220152714762, 0.03751124422446472, 0.040262454415152846, 0.03394337372005103, 0.034812870011651315, 0.035718060541246405, 0.03819795905683452, 0.040033154300366934, 0.03926265471770691, 0.03615325568009378, 0.03365933453732525, 0.039068440027706486, 0.03632450405529403, 0.03327959039466234, 0.0380557669942912, 0.04857213410814255, 0.035188985655768945, 0.04043738663945356, 0.03461658117604629, 0.03575857100926664, 0.03573843165258482, 0.041993840306214, 0.034306677060425186, 0.03628713978405569, 0.035703868798188966, 0.04458347755061121, 0.03624753151316024, 0.03948719381822563, 0.0514030225739673, 0.038867823954609415, 0.03579494111342879, 0.03538579136099024, 0.040838587502597105, 0.03860451142831938, 0.03780565036781205, 0.0364963808518118, 0.03618359146640712, 0.03728674563978707, 0.0342052606993684, 0.045607219514922345, 0.04675837831369056, 0.03679145357401076, 0.04088944957649345, 0.03692985402786966, 0.03721957441070393, 0.042556929527808776, 0.03757894146988101, 0.03353467132919647, 0.03493478178400731, 0.04450977788157231, 0.04781059757709734, 0.03589444014000382, 0.033811352639167375], [0.03247157870333634, 0.03318194492752637, 0.03463007097425255, 0.051049050308552654, 0.03850730819930318, 0.04031901861803653, 0.03427235557674851, 0.034010168412598525, 0.03461466855192819, 0.04494374691651651, 0.035001417462513, 0.030302300847453317, 0.03834485640504798, 0.036675865548538744, 0.04393559480015078, 0.04171363265433519, 0.032376466219710374, 0.02986458157263873, 0.03490510512201936, 0.03878342509033107, 0.03367242870226093, 0.056341030724462164, 0.045020820645025425, 0.030372632377275544, 0.032162543220543065, 0.05401742832969433, 0.041445568653376175, 0.04284420518708859, 0.04765206808932774, 0.03391888757449491, 0.03988226390744916, 0.033000930756513544, 0.038185424287346156, 0.03368507076972996, 0.03233114140824264, 0.04168701037128857, 0.03406393637814948, 0.03418946308678494, 0.03933680556781036, 0.03399084828193904, 0.05074275526585784, 0.032796910349761337, 0.032659712566455654, 0.04539497882900675, 0.05051831094601719, 0.029931880893275625, 0.04796828589248162, 0.04168298058798658, 0.04872696928716215, 0.04069324216312038, 0.03243693579734485, 0.03323599415950701, 0.048568322418253346, 0.042294829590725495, 0.03910458769537142, 0.045775296653764445, 0.03354795525028503, 0.037764855128641764, 0.05015406721005048, 0.03809590534052541, 0.034092449566365424, 0.03192536473147988, 0.03338906979697374, 0.03405221582313484, 0.039050300393319776, 0.03699284053439283, 0.049395076390538695, 0.03939699492630544, 0.03376631330866659, 0.03175395707785087, 0.04166174840370486, 0.03341813377413406, 0.04254266141756018, 0.034659866752009376, 0.06275555188744339, 0.05049307765392174, 0.03998382795544256, 0.04293386300734962, 0.033606869374793354, 0.047297897957060346, 0.03833376298075429, 0.0332286396228541, 0.03158250901388399, 0.04668935395333933, 0.033945699303054584, 0.03147228908338381, 0.035373923564573986, 0.03488084616055411, 0.03228131554947106, 0.0505732397344586, 0.05706422299839914, 0.03369960203925626, 0.052998423043877294, 0.033865538758937094, 0.03286412239080154, 0.033561143488023235, 0.035605295311343946, 0.04184254246240404, 0.04038704504286295, 0.031249250442076954], [0.033017079198157655, 0.04158532422078846, 0.041584553328429245, 0.04378565796802446, 0.03648249332542842, 0.03285357328461722, 0.038337274948866344, 0.03621970705590605, 0.03134156703771401, 0.035769886104954754, 0.037340849467323044, 0.0313665823797126, 0.034185424944983625, 0.0346548574587842, 0.03503335515078644, 0.037647210644051854, 0.03938458639535794, 0.035818627580583, 0.03146852009362715, 0.03854829589823155, 0.03491682633595039, 0.04043411715199262, 0.03332958738501635, 0.03488517732439377, 0.036522183240414854, 0.03878276627088863, 0.040702785667591695, 0.03928052926912373, 0.04460865727437838, 0.03625447097454831, 0.035233226312654305, 0.03604404700950841, 0.0411184144450268, 0.03750206229114288, 0.036314680348407284, 0.03301700243309977, 0.03433712906986775, 0.03555874588534948, 0.033902050694291495, 0.04487873866473983, 0.049715667580449895, 0.036955848547248364, 0.032740287723456794, 0.042622143635322275, 0.0452423713565602, 0.03381648743585423, 0.03484262523639304, 0.036487508684135035, 0.03708003362600682, 0.03503568780671189, 0.034033817891264015, 0.0358573204501911, 0.049648869591577244, 0.044987952671725985, 0.03996986063720047, 0.03646058941378137, 0.035576230729342864, 0.04566123163597354, 0.0387087251236214, 0.037457786875952866, 0.03756700987706567, 0.03616318935573511, 0.04671659726632212, 0.03719334834992154, 0.04039422637036856, 0.03737281399601109, 0.03884991594071239, 0.038929789359679313, 0.035750910560064846, 0.03602774009934691, 0.03952613283758204, 0.037071455923011705, 0.03654932653704365, 0.041694779457145836, 0.048420990544304654, 0.051296976226234685, 0.04090492302306896, 0.036090092170553034, 0.0413647470016485, 0.04173275036967798, 0.03532536020525261, 0.033619708684659896, 0.03719942747580999, 0.03663784706817902, 0.04144032431517964, 0.033895151070847424, 0.038627240821490286, 0.03905010744514432, 0.037019306837756394, 0.03510359335589479, 0.03563129831370164, 0.03587367215302844, 0.04355355805186783, 0.03657673447757109, 0.037700004723844, 0.038454263683708634, 0.03921639876725657, 0.04503020832295625, 0.03517907034431479, 0.033077511202575224], [0.04379407078966705, 0.05305412318148922, 0.04583816667558644, 0.047337872892934174, 0.0517290689775664, 0.045949552657458016, 0.0460782079382982, 0.04714375564778112, 0.043659644263216564, 0.04376589618703744, 0.04525035790520816, 0.04885348398995539, 0.0464080636775798, 0.0430697207499657, 0.04355532886053957, 0.050101923017053906, 0.04980119837337879, 0.045382466690564095, 0.05359484312092717, 0.04569116979755993, 0.04677643528031598, 0.04419515937788168, 0.05143605032176487, 0.04384752182779513, 0.04044578921274152, 0.04413803216675421, 0.04529427074410668, 0.055447921381077535, 0.043915648832631854, 0.048951133981999455, 0.0462388096162442, 0.052548818353136996, 0.049752495856480596, 0.0444371243265047, 0.05038582691162898, 0.04218378014475623, 0.05175916447447992, 0.047780787952355915, 0.05145916832735254, 0.04519185793183949, 0.042987146788644924, 0.0507493243429472, 0.061762590238264956, 0.042503407825992136, 0.042049286894654564, 0.04452911557695291, 0.046277824793847316, 0.0601094980017077, 0.047292175800146635, 0.045916053281276716, 0.044769619817141115, 0.05133190382490209, 0.05169188195253921, 0.04396709424051003, 0.05015185237173614, 0.04443194245608358, 0.05048978410429253, 0.04471712782303962, 0.044438573183524815, 0.04513459184453437, 0.05709265271109162, 0.044763382298039514, 0.058148145935187315, 0.044334705954274294, 0.04747621669217515, 0.046159470310520784, 0.045975625129722524, 0.05197097913829445, 0.043107143009489195, 0.04386236684431435, 0.04834427406983873, 0.046656949433527654, 0.04937132587304585, 0.047112377919507745, 0.049010382552576746, 0.0456998987358388, 0.04563171714112648, 0.054812648450932054, 0.047015222771747536, 0.045994359596999365, 0.047643265181751035, 0.05132410132747876, 0.04574938246312426, 0.04641110753128421, 0.053405069946187426, 0.04380667315544283, 0.042693406426730196, 0.047576529648319314, 0.05354090534467667, 0.049918152479466696, 0.04430353562990423, 0.04991055058053264, 0.045813393648375195, 0.03917351615592717, 0.04644971531696419, 0.05108892218082214, 0.044990386019412826, 0.049450313147062296, 0.04759169818499728, 0.04496219681129428], [0.037057652812811336, 0.035937114666838896, 0.036418754815719274, 0.04998137600951598, 0.032383487210943335, 0.051615359704323134, 0.04395146332174924, 0.03917009318220277, 0.03379712472624289, 0.04048728862447243, 0.03479676288113116, 0.03060548728474418, 0.05305893192806684, 0.040887618862965, 0.03291136650835345, 0.034109380839842, 0.04858443903287711, 0.03720320214137501, 0.05100966237561072, 0.039258666377079324, 0.03582955376561388, 0.033610223477848325, 0.04120585699812694, 0.03485040140526949, 0.04848060846024003, 0.03130856473288647, 0.043490697685169624, 0.039489826052234944, 0.05081409259631775, 0.03156308221321965, 0.03201709671725595, 0.0378480002830186, 0.0385258596749226, 0.03908521380968775, 0.028789456028220858, 0.03911203677596096, 0.04072348908939193, 0.03435122448023628, 0.03882225709852575, 0.032110982357268864, 0.0775222145803899, 0.03810387732421076, 0.05187195542063112, 0.03397518318805308, 0.07699853884999773, 0.03936186213573828, 0.04022632686322773, 0.03863306799264579, 0.048183198078463434, 0.034317139331466594, 0.03231318443878067, 0.032796555594963146, 0.04668260977626428, 0.031208538916614396, 0.047630298527774, 0.037311307067506294, 0.040679856423737525, 0.04254264165885353, 0.038838701083116364, 0.038087348133642035, 0.04044873871974779, 0.033135025003602714, 0.03561986951467849, 0.03172074963458127, 0.03361406630933486, 0.050664324956714295, 0.05013713127934687, 0.03281985414317755, 0.035482295648784974, 0.033949428608136274, 0.033133984241045904, 0.03726782344672396, 0.03500989562073132, 0.03929902253085143, 0.034631913124886504, 0.059384017743973984, 0.03213043925988722, 0.03531971665259015, 0.04131905000989418, 0.04528558582191684, 0.04439627640532285, 0.03824862880881337, 0.043257616890353685, 0.04479226010595114, 0.033881288968361484, 0.03241793685276733, 0.03427990430505567, 0.041535345124885596, 0.04234010644585691, 0.043877453198735254, 0.05124801024964286, 0.039215082891787226, 0.04916849505316357, 0.044771926794602686, 0.05544368836241387, 0.03753117593561701, 0.03497510718541545, 0.03785008790836552, 0.04244160214655629, 0.043081865304832434], [0.04504438414549744, 0.032007347639550286, 0.034567198008157704, 0.040037438226426636, 0.038260972454935906, 0.03279651115654428, 0.031857143050798065, 0.0317152221660294, 0.030419492674772185, 0.049785940971736595, 0.0309369747578923, 0.046637626557350126, 0.06936920423909326, 0.032678915117107264, 0.04905993776621415, 0.0449552022018826, 0.04030479531763029, 0.03182087818432183, 0.04150334157748829, 0.0325383655008692, 0.034581890611656466, 0.04210250602725982, 0.0428750999742645, 0.03068362320893862, 0.03438810481010428, 0.02937094359374039, 0.040395875423927266, 0.0394006077748758, 0.04453773508108354, 0.03169840676495003, 0.033810718336486655, 0.0398553625275625, 0.03398291536197145, 0.03349103132925242, 0.027578152614055856, 0.03392739823559373, 0.04026153809945305, 0.03382667888836688, 0.031237564593356328, 0.03379919663826887, 0.05891556679892013, 0.0335470337682961, 0.031179319278051978, 0.05871877699517557, 0.0775766980403925, 0.02821416565382691, 0.04423675925828131, 0.0328634627773499, 0.03277314206053577, 0.03229216928094897, 0.03150639116800713, 0.04534773632070569, 0.05480725170304846, 0.034040832439223456, 0.04264470806890969, 0.03292222525192653, 0.03364597029691965, 0.03425475633082702, 0.04628824507045611, 0.04351300749027977, 0.03155136384260368, 0.03222199177191704, 0.039347544699728024, 0.03227019382250165, 0.03198771340691302, 0.03133296038121776, 0.03853005114664913, 0.04426062220722953, 0.035905423447104186, 0.04340285876281895, 0.03415142948461233, 0.03429021566556796, 0.041384147825654555, 0.038289134583400566, 0.03243479795744189, 0.04397951875710644, 0.033665467996051836, 0.04094734313855272, 0.03245457715752503, 0.04323960125667464, 0.03414162463983005, 0.0331359286240394, 0.03895731494654217, 0.046332371457561264, 0.03257981155842544, 0.029846340200657132, 0.0425851253047408, 0.03351655149534, 0.03141763363951522, 0.032291479090400546, 0.04507650550919211, 0.034666362602499945, 0.04066689336865024, 0.03433534282749658, 0.04413945028021679, 0.035599594695786, 0.037386604675449284, 0.04124759067575332, 0.028373020155373206, 0.035862795597776165]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=0.2$, $l=0.1$, $n=30$')
    
    lossvec0 = [[0.04874981168155717, 0.04601627598721148, 0.046602509349972523, 0.050586168495252604, 0.047650039131627096, 0.04900758374021014, 0.05083789310453001, 0.04815940526219456, 0.04894303779884694, 0.04872188439052756, 0.04596113107150889, 0.04533036788057144, 0.047702491234585545, 0.04605326438814462, 0.0445759009504151, 0.053495095666269976, 0.04786314057031166, 0.04960261382638776, 0.048985348721622135, 0.04767482107021301, 0.04715583207351171, 0.0476421221058353, 0.04696364472561235, 0.04691241877782879, 0.04513892571546784, 0.04654400401716812, 0.04892125037855425, 0.0455866952254014, 0.046053861253317854, 0.047858963944586455, 0.04881940384220125, 0.04737662377020264, 0.049525288614961915, 0.04957435122175646, 0.04575276971922458, 0.04960007226271745, 0.04824906144665322, 0.04810665616041669, 0.047014452407872546, 0.047600033676595356, 0.04839777879360045, 0.045558118647944186, 0.047518293650248594, 0.05036545697743948, 0.049412171532409094, 0.04856483735481838, 0.04754430576186313, 0.046404639783898714, 0.04646733894411559, 0.04443174099410009, 0.04350771594448622, 0.04825966263047179, 0.04778314333024609, 0.04821113384089001, 0.04797284516136274, 0.048938148885673535, 0.04687477057177605, 0.04670793693255172, 0.04495711920901903, 0.04735873038334376, 0.05014163434178577, 0.047774072750534476, 0.04683807874548834, 0.04655733411954765, 0.048538584046488004, 0.045772918950249715, 0.049308758668981205, 0.04680097274856691, 0.04714223637422627, 0.05147392076156743, 0.04874938178896028, 0.051631306011019514, 0.04493540958584115, 0.04595306111401679, 0.04643543723089674, 0.04715820518602384, 0.04857938775379486, 0.04739208539927517, 0.04798729370505646, 0.04720470339582102, 0.04780471892428656, 0.04721535246277248, 0.050363706530987845, 0.04699765461372573, 0.04592028467371892, 0.04890129988747958, 0.048202645680428875, 0.0487827386622787, 0.049712689106432645, 0.048768532287325035, 0.0482422597277323, 0.04691256438345368, 0.047261297155268917, 0.053601021618157114, 0.04745636245268635, 0.046792417128567285, 0.04759514246217367, 0.04665313645744631, 0.04604447426571351, 0.05065028847795186]]
    lossveclist = [[0.03600387141169995, 0.0342730895471504, 0.037231245719616474, 0.03821681656593368, 0.036524971635385796, 0.03949410935896119, 0.03446591045419293, 0.0396743369833525, 0.035792210076944615, 0.033537117437739294, 0.03604002814257922, 0.03417521321342557, 0.033347089545724476, 0.03769482474517408, 0.03846517972190049, 0.0413523467226083, 0.036049512120723166, 0.03406534550385596, 0.03394704273824553, 0.03850120087976367, 0.03812376762208605, 0.03652952777060523, 0.03568045219506099, 0.03365921678428877, 0.040797963743401014, 0.03474034286476377, 0.05681018234607664, 0.03642466430890088, 0.042151979721033954, 0.0336656061000447, 0.03321807915010236, 0.03222030432492298, 0.035741544892543525, 0.03838025443578791, 0.033512676132623126, 0.03546218227682308, 0.03889728003774697, 0.0352736552930459, 0.035973969825781035, 0.03755704163857905, 0.06055880514457488, 0.03614881522940921, 0.038411144933868206, 0.03919233964066806, 0.03667805662919395, 0.03413958669579258, 0.03690343099030715, 0.03394220152714762, 0.03751124422446472, 0.040262454415152846, 0.03394337372005103, 0.034812870011651315, 0.035718060541246405, 0.03819795905683452, 0.040033154300366934, 0.03926265471770691, 0.03615325568009378, 0.03365933453732525, 0.039068440027706486, 0.03632450405529403, 0.03327959039466234, 0.0380557669942912, 0.04857213410814255, 0.035188985655768945, 0.04043738663945356, 0.03461658117604629, 0.03575857100926664, 0.03573843165258482, 0.041993840306214, 0.034306677060425186, 0.03628713978405569, 0.035703868798188966, 0.04458347755061121, 0.03624753151316024, 0.03948719381822563, 0.0514030225739673, 0.038867823954609415, 0.03579494111342879, 0.03538579136099024, 0.040838587502597105, 0.03860451142831938, 0.03780565036781205, 0.0364963808518118, 0.03618359146640712, 0.03728674563978707, 0.0342052606993684, 0.045607219514922345, 0.04675837831369056, 0.03679145357401076, 0.04088944957649345, 0.03692985402786966, 0.03721957441070393, 0.042556929527808776, 0.03757894146988101, 0.03353467132919647, 0.03493478178400731, 0.04450977788157231, 0.04781059757709734, 0.03589444014000382, 0.033811352639167375], [0.03247157870333634, 0.03318194492752637, 0.03463007097425255, 0.051049050308552654, 0.03850730819930318, 0.04031901861803653, 0.03427235557674851, 0.034010168412598525, 0.03461466855192819, 0.04494374691651651, 0.035001417462513, 0.030302300847453317, 0.03834485640504798, 0.036675865548538744, 0.04393559480015078, 0.04171363265433519, 0.032376466219710374, 0.02986458157263873, 0.03490510512201936, 0.03878342509033107, 0.03367242870226093, 0.056341030724462164, 0.045020820645025425, 0.030372632377275544, 0.032162543220543065, 0.05401742832969433, 0.041445568653376175, 0.04284420518708859, 0.04765206808932774, 0.03391888757449491, 0.03988226390744916, 0.033000930756513544, 0.038185424287346156, 0.03368507076972996, 0.03233114140824264, 0.04168701037128857, 0.03406393637814948, 0.03418946308678494, 0.03933680556781036, 0.03399084828193904, 0.05074275526585784, 0.032796910349761337, 0.032659712566455654, 0.04539497882900675, 0.05051831094601719, 0.029931880893275625, 0.04796828589248162, 0.04168298058798658, 0.04872696928716215, 0.04069324216312038, 0.03243693579734485, 0.03323599415950701, 0.048568322418253346, 0.042294829590725495, 0.03910458769537142, 0.045775296653764445, 0.03354795525028503, 0.037764855128641764, 0.05015406721005048, 0.03809590534052541, 0.034092449566365424, 0.03192536473147988, 0.03338906979697374, 0.03405221582313484, 0.039050300393319776, 0.03699284053439283, 0.049395076390538695, 0.03939699492630544, 0.03376631330866659, 0.03175395707785087, 0.04166174840370486, 0.03341813377413406, 0.04254266141756018, 0.034659866752009376, 0.06275555188744339, 0.05049307765392174, 0.03998382795544256, 0.04293386300734962, 0.033606869374793354, 0.047297897957060346, 0.03833376298075429, 0.0332286396228541, 0.03158250901388399, 0.04668935395333933, 0.033945699303054584, 0.03147228908338381, 0.035373923564573986, 0.03488084616055411, 0.03228131554947106, 0.0505732397344586, 0.05706422299839914, 0.03369960203925626, 0.052998423043877294, 0.033865538758937094, 0.03286412239080154, 0.033561143488023235, 0.035605295311343946, 0.04184254246240404, 0.04038704504286295, 0.031249250442076954], [0.033017079198157655, 0.04158532422078846, 0.041584553328429245, 0.04378565796802446, 0.03648249332542842, 0.03285357328461722, 0.038337274948866344, 0.03621970705590605, 0.03134156703771401, 0.035769886104954754, 0.037340849467323044, 0.0313665823797126, 0.034185424944983625, 0.0346548574587842, 0.03503335515078644, 0.037647210644051854, 0.03938458639535794, 0.035818627580583, 0.03146852009362715, 0.03854829589823155, 0.03491682633595039, 0.04043411715199262, 0.03332958738501635, 0.03488517732439377, 0.036522183240414854, 0.03878276627088863, 0.040702785667591695, 0.03928052926912373, 0.04460865727437838, 0.03625447097454831, 0.035233226312654305, 0.03604404700950841, 0.0411184144450268, 0.03750206229114288, 0.036314680348407284, 0.03301700243309977, 0.03433712906986775, 0.03555874588534948, 0.033902050694291495, 0.04487873866473983, 0.049715667580449895, 0.036955848547248364, 0.032740287723456794, 0.042622143635322275, 0.0452423713565602, 0.03381648743585423, 0.03484262523639304, 0.036487508684135035, 0.03708003362600682, 0.03503568780671189, 0.034033817891264015, 0.0358573204501911, 0.049648869591577244, 0.044987952671725985, 0.03996986063720047, 0.03646058941378137, 0.035576230729342864, 0.04566123163597354, 0.0387087251236214, 0.037457786875952866, 0.03756700987706567, 0.03616318935573511, 0.04671659726632212, 0.03719334834992154, 0.04039422637036856, 0.03737281399601109, 0.03884991594071239, 0.038929789359679313, 0.035750910560064846, 0.03602774009934691, 0.03952613283758204, 0.037071455923011705, 0.03654932653704365, 0.041694779457145836, 0.048420990544304654, 0.051296976226234685, 0.04090492302306896, 0.036090092170553034, 0.0413647470016485, 0.04173275036967798, 0.03532536020525261, 0.033619708684659896, 0.03719942747580999, 0.03663784706817902, 0.04144032431517964, 0.033895151070847424, 0.038627240821490286, 0.03905010744514432, 0.037019306837756394, 0.03510359335589479, 0.03563129831370164, 0.03587367215302844, 0.04355355805186783, 0.03657673447757109, 0.037700004723844, 0.038454263683708634, 0.03921639876725657, 0.04503020832295625, 0.03517907034431479, 0.033077511202575224], [0.04379407078966705, 0.05305412318148922, 0.04583816667558644, 0.047337872892934174, 0.0517290689775664, 0.045949552657458016, 0.0460782079382982, 0.04714375564778112, 0.043659644263216564, 0.04376589618703744, 0.04525035790520816, 0.04885348398995539, 0.0464080636775798, 0.0430697207499657, 0.04355532886053957, 0.050101923017053906, 0.04980119837337879, 0.045382466690564095, 0.05359484312092717, 0.04569116979755993, 0.04677643528031598, 0.04419515937788168, 0.05143605032176487, 0.04384752182779513, 0.04044578921274152, 0.04413803216675421, 0.04529427074410668, 0.055447921381077535, 0.043915648832631854, 0.048951133981999455, 0.0462388096162442, 0.052548818353136996, 0.049752495856480596, 0.0444371243265047, 0.05038582691162898, 0.04218378014475623, 0.05175916447447992, 0.047780787952355915, 0.05145916832735254, 0.04519185793183949, 0.042987146788644924, 0.0507493243429472, 0.061762590238264956, 0.042503407825992136, 0.042049286894654564, 0.04452911557695291, 0.046277824793847316, 0.0601094980017077, 0.047292175800146635, 0.045916053281276716, 0.044769619817141115, 0.05133190382490209, 0.05169188195253921, 0.04396709424051003, 0.05015185237173614, 0.04443194245608358, 0.05048978410429253, 0.04471712782303962, 0.044438573183524815, 0.04513459184453437, 0.05709265271109162, 0.044763382298039514, 0.058148145935187315, 0.044334705954274294, 0.04747621669217515, 0.046159470310520784, 0.045975625129722524, 0.05197097913829445, 0.043107143009489195, 0.04386236684431435, 0.04834427406983873, 0.046656949433527654, 0.04937132587304585, 0.047112377919507745, 0.049010382552576746, 0.0456998987358388, 0.04563171714112648, 0.054812648450932054, 0.047015222771747536, 0.045994359596999365, 0.047643265181751035, 0.05132410132747876, 0.04574938246312426, 0.04641110753128421, 0.053405069946187426, 0.04380667315544283, 0.042693406426730196, 0.047576529648319314, 0.05354090534467667, 0.049918152479466696, 0.04430353562990423, 0.04991055058053264, 0.045813393648375195, 0.03917351615592717, 0.04644971531696419, 0.05108892218082214, 0.044990386019412826, 0.049450313147062296, 0.04759169818499728, 0.04496219681129428], [0.037057652812811336, 0.035937114666838896, 0.036418754815719274, 0.04998137600951598, 0.032383487210943335, 0.051615359704323134, 0.04395146332174924, 0.03917009318220277, 0.03379712472624289, 0.04048728862447243, 0.03479676288113116, 0.03060548728474418, 0.05305893192806684, 0.040887618862965, 0.03291136650835345, 0.034109380839842, 0.04858443903287711, 0.03720320214137501, 0.05100966237561072, 0.039258666377079324, 0.03582955376561388, 0.033610223477848325, 0.04120585699812694, 0.03485040140526949, 0.04848060846024003, 0.03130856473288647, 0.043490697685169624, 0.039489826052234944, 0.05081409259631775, 0.03156308221321965, 0.03201709671725595, 0.0378480002830186, 0.0385258596749226, 0.03908521380968775, 0.028789456028220858, 0.03911203677596096, 0.04072348908939193, 0.03435122448023628, 0.03882225709852575, 0.032110982357268864, 0.0775222145803899, 0.03810387732421076, 0.05187195542063112, 0.03397518318805308, 0.07699853884999773, 0.03936186213573828, 0.04022632686322773, 0.03863306799264579, 0.048183198078463434, 0.034317139331466594, 0.03231318443878067, 0.032796555594963146, 0.04668260977626428, 0.031208538916614396, 0.047630298527774, 0.037311307067506294, 0.040679856423737525, 0.04254264165885353, 0.038838701083116364, 0.038087348133642035, 0.04044873871974779, 0.033135025003602714, 0.03561986951467849, 0.03172074963458127, 0.03361406630933486, 0.050664324956714295, 0.05013713127934687, 0.03281985414317755, 0.035482295648784974, 0.033949428608136274, 0.033133984241045904, 0.03726782344672396, 0.03500989562073132, 0.03929902253085143, 0.034631913124886504, 0.059384017743973984, 0.03213043925988722, 0.03531971665259015, 0.04131905000989418, 0.04528558582191684, 0.04439627640532285, 0.03824862880881337, 0.043257616890353685, 0.04479226010595114, 0.033881288968361484, 0.03241793685276733, 0.03427990430505567, 0.041535345124885596, 0.04234010644585691, 0.043877453198735254, 0.05124801024964286, 0.039215082891787226, 0.04916849505316357, 0.044771926794602686, 0.05544368836241387, 0.03753117593561701, 0.03497510718541545, 0.03785008790836552, 0.04244160214655629, 0.043081865304832434], [0.04504438414549744, 0.032007347639550286, 0.034567198008157704, 0.040037438226426636, 0.038260972454935906, 0.03279651115654428, 0.031857143050798065, 0.0317152221660294, 0.030419492674772185, 0.049785940971736595, 0.0309369747578923, 0.046637626557350126, 0.06936920423909326, 0.032678915117107264, 0.04905993776621415, 0.0449552022018826, 0.04030479531763029, 0.03182087818432183, 0.04150334157748829, 0.0325383655008692, 0.034581890611656466, 0.04210250602725982, 0.0428750999742645, 0.03068362320893862, 0.03438810481010428, 0.02937094359374039, 0.040395875423927266, 0.0394006077748758, 0.04453773508108354, 0.03169840676495003, 0.033810718336486655, 0.0398553625275625, 0.03398291536197145, 0.03349103132925242, 0.027578152614055856, 0.03392739823559373, 0.04026153809945305, 0.03382667888836688, 0.031237564593356328, 0.03379919663826887, 0.05891556679892013, 0.0335470337682961, 0.031179319278051978, 0.05871877699517557, 0.0775766980403925, 0.02821416565382691, 0.04423675925828131, 0.0328634627773499, 0.03277314206053577, 0.03229216928094897, 0.03150639116800713, 0.04534773632070569, 0.05480725170304846, 0.034040832439223456, 0.04264470806890969, 0.03292222525192653, 0.03364597029691965, 0.03425475633082702, 0.04628824507045611, 0.04351300749027977, 0.03155136384260368, 0.03222199177191704, 0.039347544699728024, 0.03227019382250165, 0.03198771340691302, 0.03133296038121776, 0.03853005114664913, 0.04426062220722953, 0.035905423447104186, 0.04340285876281895, 0.03415142948461233, 0.03429021566556796, 0.041384147825654555, 0.038289134583400566, 0.03243479795744189, 0.04397951875710644, 0.033665467996051836, 0.04094734313855272, 0.03245457715752503, 0.04323960125667464, 0.03414162463983005, 0.0331359286240394, 0.03895731494654217, 0.046332371457561264, 0.03257981155842544, 0.029846340200657132, 0.0425851253047408, 0.03351655149534, 0.03141763363951522, 0.032291479090400546, 0.04507650550919211, 0.034666362602499945, 0.04066689336865024, 0.03433534282749658, 0.04413945028021679, 0.035599594695786, 0.037386604675449284, 0.04124759067575332, 0.028373020155373206, 0.035862795597776165]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### overEstWt=1., rateTarget=0.01 ###
    # Get null first
    underWt, t = 1., 0.01
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Design 0']
    lossveclist = [[0.18716330553485447, 0.18860184054407664, 0.19325608589009952, 0.1770557715099232, 0.18909962053862173, 0.18459170372398095, 0.18559537079732366, 0.19418957403161127, 0.19056777303140543, 0.19661722173995794, 0.18615517172133905, 0.18656234789959142, 0.18207911627849313, 0.19136687879390743, 0.19674573354643832, 0.1868874400406348, 0.18707867853840698, 0.1935239829381169, 0.18205086526045547, 0.19672122304180922, 0.18881630904487404, 0.1833803571459253, 0.19315812241755476, 0.1939300012408022, 0.1823919862711381, 0.19573388201746308, 0.18127684565012528, 0.1845268243447256, 0.2064338189794515, 0.20159672625324548, 0.175570766914338, 0.19471220948547244, 0.19506311055926825, 0.20018623541754793, 0.19098447267714874, 0.19502464029641609, 0.17798875406147763, 0.19399013962692402, 0.19200981099081268, 0.1946489101903228, 0.19112257101531924, 0.19993782678396535, 0.18597183732475736, 0.17973046264056863, 0.19279044896209913, 0.18991506529423824, 0.1849965998756091, 0.18460638724691056, 0.187766224917971, 0.18747905139303478, 0.17826392927939785, 0.19325741567524662, 0.18312120450517352, 0.192776652857974, 0.1857877196910409, 0.1858789089584243, 0.18760130405861783, 0.18436246826117497, 0.18657854615884836, 0.20529250618228734, 0.1854399759521401, 0.18781946613353975, 0.19103850589477586, 0.19321925534650095, 0.1833887432242402, 0.19466555433451851, 0.17968140555283613, 0.18826368627863668, 0.18936852542619723, 0.18239636499178297, 0.18166912854423528, 0.1886670787540829, 0.18214968590293265, 0.18688054274220603, 0.2007408440158043, 0.1887733025755799, 0.17529884693459136, 0.1945086526775307, 0.19507746617481378, 0.19771191076229758, 0.1900978061604873, 0.18303813831240057, 0.1848877412408327, 0.1815693595110686, 0.20485972236370922, 0.19125618875026087, 0.18942591264028497, 0.1927734061166825, 0.19628853444448496, 0.18576300190829131, 0.19292331937386653, 0.19252042667402308, 0.19919255729620128, 0.17874313897780772, 0.19420424824610283, 0.19765025474532247, 0.18019946811985466, 0.18734538778408527, 0.18392117311158634, 0.1831644019563764]]
    '''
    # 30 tests for all designs
    underWt, t = 1., 0.01
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.14650254664622714, 0.14945395718824386, 0.14817265992801912, 0.16780559963962108, 0.15015565057421484, 0.1426526674446709, 0.127002701263839, 0.14973599001313034, 0.14379745340214456, 0.139837977683405, 0.14502588322123583, 0.139449297639265, 0.14810411834859855, 0.15197187990784472, 0.15791019249363777, 0.15643605447685077, 0.14765671976379613, 0.13687337021104218, 0.13463438684752851, 0.14846295180230243, 0.16679816334649855, 0.14580028683657037, 0.1478038400866632, 0.14563147804011073, 0.15441590083470796, 0.1564344145623141, 0.1593382152170522, 0.18063524690611607, 0.1670782852909844, 0.13985541309997757, 0.1521875325717327, 0.14825753966584898, 0.16675812235739884, 0.17604370551612047, 0.14514470914049415, 0.16569697103017872, 0.15513959923699175, 0.1444528032396159, 0.1524501638573838, 0.14966713103805857, 0.21339217740516067, 0.1717505430981025, 0.16197688582265382, 0.14879477291575577, 0.17324758971090004, 0.13475689502411448, 0.15952066224395176, 0.1395240818149531, 0.13372823443914056, 0.14626752917298552, 0.14255560367544684, 0.16864603454678168, 0.1675395520468658, 0.16305733505059994, 0.16475180207848314, 0.1555465538253874, 0.15097334496266968, 0.1596651666911441, 0.14908110113270723, 0.13950854179243416, 0.14186888511399237, 0.17709946113486652, 0.21839742071304266, 0.1412147903777371, 0.16901968770351639, 0.15177394305620334, 0.17802333470109044, 0.13737017443790986, 0.16652892954690995, 0.14031458123601576, 0.15461527063584157, 0.15966429894529732, 0.154394638043801, 0.1459457521408128, 0.1832923218320714, 0.2061347031376535, 0.16324217584051984, 0.1534169859177199, 0.16022608027154742, 0.1628399681179009, 0.14533494762138024, 0.16097521054846833, 0.15804829181572244, 0.14210649098126377, 0.16777027956484572, 0.14487665915373688, 0.1583214382403871, 0.15757408855364202, 0.14410097478669381, 0.1655557817674055, 0.15448986549984361, 0.1666104593548441, 0.2320281234815435, 0.16149421956944393, 0.1390202951533169, 0.14055013493578047, 0.2171495850751611, 0.18402861524840328, 0.13812561305510793, 0.15135301286637445], [0.12822586019501847, 0.1321711755229878, 0.14780291045025645, 0.19112732108198258, 0.16460835749376856, 0.20512855801617605, 0.13905743630487483, 0.12991549737465286, 0.12986023761410312, 0.15682962441439094, 0.15617173408981583, 0.18916889825633365, 0.15212586508172765, 0.1361103258060248, 0.13684286337882728, 0.1349381906416406, 0.1441570020654102, 0.15856547089441478, 0.12913389749755522, 0.1333750259016545, 0.13350289606916466, 0.15886633070741857, 0.12926898230236622, 0.13326705145487033, 0.1716497571473108, 0.13139164463427333, 0.1935626638596365, 0.13868435522391082, 0.13426235325259547, 0.11980439053984904, 0.1282176702087814, 0.13674149582020215, 0.15711538053955262, 0.13557976341475253, 0.13150568640905383, 0.13150015832968534, 0.1444623973507264, 0.16416242532876463, 0.15010528483224667, 0.1723917883221508, 0.18454634645090953, 0.13766710248806327, 0.13435774488169153, 0.19383786494230143, 0.20928799956596694, 0.13193350389302197, 0.185304343401545, 0.15817130347005756, 0.1729433508574668, 0.1612704561122801, 0.1547070315354061, 0.16160353671247057, 0.20666092027386476, 0.15233436025005273, 0.16053697665031072, 0.19756549055694927, 0.1782023963051965, 0.13480241581951694, 0.17773748800077005, 0.1369416887968862, 0.1526075769885384, 0.1261822986166664, 0.13865265975850918, 0.12982610455506613, 0.18611607607165134, 0.1411308774753208, 0.20504472163297377, 0.1901091435730258, 0.17181237702186822, 0.11918766659045749, 0.14432961693587548, 0.13753503201927253, 0.14092088902470803, 0.12971933440055586, 0.13681249876336649, 0.2028860498781577, 0.1549730964895876, 0.12690373463942792, 0.1383566781516739, 0.16963981808237397, 0.15641789411864104, 0.17169770649799404, 0.18700527671256195, 0.19065864267818491, 0.1309407474992356, 0.12421216252334584, 0.1710025557453492, 0.13575549986446728, 0.15882914777539564, 0.13421724496738202, 0.18202812515643987, 0.15906333973501838, 0.1841636626578887, 0.1373436010533669, 0.12976290829778933, 0.13138675399128782, 0.15864506874917345, 0.19863290799750477, 0.17376647017387617, 0.13023949278989824], [0.15948700430936635, 0.14881415351029484, 0.1665382543009113, 0.19739384014646436, 0.14279547246593427, 0.1602487290852922, 0.1443502046861278, 0.1477645995216703, 0.14684325626943812, 0.14990244644764686, 0.14016165950457665, 0.13341124326410497, 0.14695877269303975, 0.15227526416044523, 0.15749161164572767, 0.15729223690302188, 0.17221815545678631, 0.14795112917429265, 0.14195110722093066, 0.14277944233436815, 0.2140101235094532, 0.15725194145547766, 0.14708254724843245, 0.14210050867463256, 0.1592661217439993, 0.1412520712506917, 0.1559211435677211, 0.13710481428912988, 0.15442983443747144, 0.1462716055977131, 0.15420765781023116, 0.15049466580589183, 0.15844330611344196, 0.15730163775386505, 0.13719632665171627, 0.1473157278343939, 0.1721010384613611, 0.14233968237993586, 0.16780648469908943, 0.1492351344055081, 0.15765959322331125, 0.16235341894804878, 0.14493121335847772, 0.14589389921317572, 0.17081651987425195, 0.15633121008825107, 0.1479305609682166, 0.14593870864786462, 0.152092534785864, 0.15355355912128726, 0.14434286374829897, 0.1510229795080887, 0.15072913866849413, 0.1494642650707675, 0.16387057416638762, 0.15657492516809682, 0.1538878159711883, 0.15026257442209684, 0.16867977456217942, 0.15113672768320807, 0.16058551730193363, 0.1409273371707429, 0.19357468282904128, 0.16608498159762336, 0.18438814463455766, 0.15231108475675414, 0.14522722828286308, 0.17175235066876413, 0.1857974177693353, 0.15534558453606986, 0.15773736873379368, 0.1491764193562065, 0.15435504236977496, 0.1441683497803102, 0.14629741294381635, 0.19331653657013648, 0.14596771944872128, 0.15143860274713322, 0.16137127041144814, 0.167616707964461, 0.14721037800228215, 0.14974149886198523, 0.16702640806063068, 0.13607495929941996, 0.1710198002388864, 0.14671563891761077, 0.17228400960485835, 0.14747360861474998, 0.13837484929592822, 0.14983993701949844, 0.15192874438016546, 0.210800291105933, 0.1663481371123751, 0.160105628190309, 0.1498394414090056, 0.1505251301163232, 0.16162713515236798, 0.15274782620528793, 0.1462070434707487, 0.14409512840431657], [0.16954625481913121, 0.1901718832551768, 0.19364765772117012, 0.16774955619213022, 0.1709879279384199, 0.1873864099154524, 0.16800038613288693, 0.17146031102016684, 0.1932578565125582, 0.1825115723843282, 0.17563910573113095, 0.1805991194609222, 0.21872448216330007, 0.16615541163012112, 0.17912387972776253, 0.17683514241860326, 0.2074712304366564, 0.1667201774806018, 0.20137746994454503, 0.20172046556992715, 0.18873562539136343, 0.16551425222448643, 0.2103678570826695, 0.2148029259534594, 0.19162833605315965, 0.188215964360798, 0.17737643336816158, 0.182712040180987, 0.18111270486051453, 0.1950686481363047, 0.20807572498200613, 0.23365045823005345, 0.16278356529267482, 0.17409985601202851, 0.19035032723473028, 0.18401884708179825, 0.20483626065550337, 0.17633637851277292, 0.17884612567309285, 0.1790524276221689, 0.16687559462820775, 0.16551655853120426, 0.206778585797234, 0.1717315170803021, 0.16663934126869012, 0.172732005566281, 0.19767059975710108, 0.20947884869266742, 0.20531721260042676, 0.1801119949516722, 0.17960000586146432, 0.17030975955790034, 0.18158202758337436, 0.1934492363690483, 0.17080443982907037, 0.17227865300995154, 0.16295808020635724, 0.17335967307132719, 0.18636540845679442, 0.19308805542779442, 0.19389643145605487, 0.20101712999348448, 0.1931386186431096, 0.17753826550505045, 0.1753950336476594, 0.1733497072817976, 0.18633409640038512, 0.18709204104381216, 0.19312158544133579, 0.16261175753920729, 0.18698021916153518, 0.18023442047035956, 0.20053311344145025, 0.19746230301170137, 0.24064319397807737, 0.18417983171345323, 0.17264348969902368, 0.22006129173634212, 0.18152633986333705, 0.1893185149569937, 0.17501175761817658, 0.19609030686883697, 0.18360964120784243, 0.18184462028283052, 0.20964731718464436, 0.1865260127273663, 0.1600895190121818, 0.18010869589381892, 0.18469217240420463, 0.19363602176455716, 0.21311931629384248, 0.17526706316401044, 0.17581517567359625, 0.18924919629193276, 0.1675528609475671, 0.18333597853796868, 0.17480730186055893, 0.17947291575007915, 0.21004374906240647, 0.18964537163152143], [0.16556888234566478, 0.1542855365452661, 0.13171045437346537, 0.22515718063959847, 0.1871638150635688, 0.21084879604207696, 0.13584147400210997, 0.16901365209078378, 0.12678094619735375, 0.20929235153538567, 0.1615410411632925, 0.12373580059371152, 0.20763958294353171, 0.13411932447274913, 0.15748955307407564, 0.16172036015508454, 0.1563258464284742, 0.12765462751432893, 0.14678717402460714, 0.158933824455612, 0.16484466371386797, 0.14826522168804793, 0.1537785811658445, 0.1268846944561489, 0.16902906345694435, 0.15516187066848797, 0.2125989692086097, 0.13607803032337376, 0.17123074462205154, 0.12353341771676689, 0.13264874447220995, 0.14513724859402746, 0.12611763991080563, 0.15469794202278664, 0.11956405207686889, 0.18990435317450177, 0.1512887162497417, 0.14224948346963717, 0.12924437950298753, 0.17522751403950093, 0.18946108432921774, 0.13309770058129453, 0.22409962798138258, 0.13705240412793485, 0.20528815548880308, 0.1255030218041865, 0.15871383773434533, 0.17341538860959435, 0.154819034256908, 0.1351641267779231, 0.15047050007408552, 0.1771867951157211, 0.13146247412179224, 0.15744292634947019, 0.20755935812924636, 0.1555266510405062, 0.12700866230512273, 0.12919432399308087, 0.16832852360454514, 0.1617620175653375, 0.1738900850870444, 0.12818055476453447, 0.16598976403885946, 0.11573463065115226, 0.13793367837765233, 0.128952557698321, 0.1733299065757096, 0.18323846661577872, 0.1519633497587757, 0.1554289052947499, 0.13362825772232528, 0.1334864427841444, 0.1347836643576305, 0.12894117657907336, 0.1475220433429826, 0.2157213627653278, 0.14810190732924422, 0.14752796987970598, 0.14079578114204855, 0.13514631837280827, 0.15209738570431897, 0.12679777674187553, 0.16395648069730878, 0.16137703834882056, 0.15092646845268748, 0.1410347727059475, 0.14557265605263836, 0.1353881271591467, 0.12594538383963186, 0.16269129972463442, 0.1719459730609683, 0.1697697847791753, 0.15228860610137906, 0.14982602831684774, 0.21084703137930993, 0.17422440205494064, 0.1899229731775834, 0.1870277978960944, 0.18588329625407415, 0.12844614527571546], [0.1894598231055358, 0.13277356275571717, 0.13889863339653638, 0.1621285962686956, 0.13591260887448375, 0.12810067370823977, 0.16251866268512136, 0.166442123415905, 0.12896292716048502, 0.15781427073441573, 0.1523306541449955, 0.12163783256458402, 0.17847831364218555, 0.14091482198895963, 0.14333145620197343, 0.17521367867463383, 0.15884103109302705, 0.13081814938395311, 0.163675463609266, 0.12610954026019577, 0.14344264772836007, 0.1392711796115823, 0.20016092172461772, 0.1310195353738602, 0.1639585650356019, 0.13906282460611474, 0.23956324621062547, 0.12902474370878173, 0.18400885927702507, 0.15879088109109832, 0.12016688480685905, 0.13415782123778275, 0.13290599360965566, 0.15110266415998144, 0.12170398235752643, 0.1361592867343966, 0.1822649624812303, 0.14086891664293014, 0.1314999838503278, 0.13454794764224, 0.13916079848909713, 0.1343677725549534, 0.1507830223780761, 0.12462988122691722, 0.19656789566387126, 0.12787260376258808, 0.17343737371677673, 0.23581427107799494, 0.17973114091404152, 0.12751841475562575, 0.1352489239120318, 0.13719867047872888, 0.19277737769413805, 0.18043775217361838, 0.13371688336003926, 0.16893044787928432, 0.19984670908824864, 0.12607671753429764, 0.16386311065255632, 0.1237143269094767, 0.15993075983870222, 0.16826168214238627, 0.1677582642446411, 0.1346298259813943, 0.14141286276794254, 0.1563206400622418, 0.19579332900313148, 0.13684806356838447, 0.13394577546546602, 0.13198841403617684, 0.1656500351101068, 0.13069728581420353, 0.18706825822485465, 0.13117417236765383, 0.2103800904098541, 0.15789313250519335, 0.1333311480734136, 0.1374074740879396, 0.1376537602670433, 0.13815572333728426, 0.14139245169047537, 0.1663786563641575, 0.1385070291365642, 0.17905247594965065, 0.13808893189418994, 0.11703491283175965, 0.16921414614391042, 0.13271469951766737, 0.16735859847950035, 0.1712028328992981, 0.13020290097599665, 0.1793711973162959, 0.12972729027855906, 0.13526515183495066, 0.16184216729989287, 0.13900252039648722, 0.12898022588702288, 0.2241999903676712, 0.18739026613086757, 0.15751397881353915]]
    lossvec0 = [[0.18716330553485447, 0.18860184054407664, 0.19325608589009952, 0.1770557715099232, 0.18909962053862173, 0.18459170372398095, 0.18559537079732366, 0.19418957403161127, 0.19056777303140543, 0.19661722173995794, 0.18615517172133905, 0.18656234789959142, 0.18207911627849313, 0.19136687879390743, 0.19674573354643832, 0.1868874400406348, 0.18707867853840698, 0.1935239829381169, 0.18205086526045547, 0.19672122304180922, 0.18881630904487404, 0.1833803571459253, 0.19315812241755476, 0.1939300012408022, 0.1823919862711381, 0.19573388201746308, 0.18127684565012528, 0.1845268243447256, 0.2064338189794515, 0.20159672625324548, 0.175570766914338, 0.19471220948547244, 0.19506311055926825, 0.20018623541754793, 0.19098447267714874, 0.19502464029641609, 0.17798875406147763, 0.19399013962692402, 0.19200981099081268, 0.1946489101903228, 0.19112257101531924, 0.19993782678396535, 0.18597183732475736, 0.17973046264056863, 0.19279044896209913, 0.18991506529423824, 0.1849965998756091, 0.18460638724691056, 0.187766224917971, 0.18747905139303478, 0.17826392927939785, 0.19325741567524662, 0.18312120450517352, 0.192776652857974, 0.1857877196910409, 0.1858789089584243, 0.18760130405861783, 0.18436246826117497, 0.18657854615884836, 0.20529250618228734, 0.1854399759521401, 0.18781946613353975, 0.19103850589477586, 0.19321925534650095, 0.1833887432242402, 0.19466555433451851, 0.17968140555283613, 0.18826368627863668, 0.18936852542619723, 0.18239636499178297, 0.18166912854423528, 0.1886670787540829, 0.18214968590293265, 0.18688054274220603, 0.2007408440158043, 0.1887733025755799, 0.17529884693459136, 0.1945086526775307, 0.19507746617481378, 0.19771191076229758, 0.1900978061604873, 0.18303813831240057, 0.1848877412408327, 0.1815693595110686, 0.20485972236370922, 0.19125618875026087, 0.18942591264028497, 0.1927734061166825, 0.19628853444448496, 0.18576300190829131, 0.19292331937386653, 0.19252042667402308, 0.19919255729620128, 0.17874313897780772, 0.19420424824610283, 0.19765025474532247, 0.18019946811985466, 0.18734538778408527, 0.18392117311158634, 0.1831644019563764]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.01$, $n=30$')
    
    lossveclist = [[0.14650254664622714, 0.14945395718824386, 0.14817265992801912, 0.16780559963962108, 0.15015565057421484, 0.1426526674446709, 0.127002701263839, 0.14973599001313034, 0.14379745340214456, 0.139837977683405, 0.14502588322123583, 0.139449297639265, 0.14810411834859855, 0.15197187990784472, 0.15791019249363777, 0.15643605447685077, 0.14765671976379613, 0.13687337021104218, 0.13463438684752851, 0.14846295180230243, 0.16679816334649855, 0.14580028683657037, 0.1478038400866632, 0.14563147804011073, 0.15441590083470796, 0.1564344145623141, 0.1593382152170522, 0.18063524690611607, 0.1670782852909844, 0.13985541309997757, 0.1521875325717327, 0.14825753966584898, 0.16675812235739884, 0.17604370551612047, 0.14514470914049415, 0.16569697103017872, 0.15513959923699175, 0.1444528032396159, 0.1524501638573838, 0.14966713103805857, 0.21339217740516067, 0.1717505430981025, 0.16197688582265382, 0.14879477291575577, 0.17324758971090004, 0.13475689502411448, 0.15952066224395176, 0.1395240818149531, 0.13372823443914056, 0.14626752917298552, 0.14255560367544684, 0.16864603454678168, 0.1675395520468658, 0.16305733505059994, 0.16475180207848314, 0.1555465538253874, 0.15097334496266968, 0.1596651666911441, 0.14908110113270723, 0.13950854179243416, 0.14186888511399237, 0.17709946113486652, 0.21839742071304266, 0.1412147903777371, 0.16901968770351639, 0.15177394305620334, 0.17802333470109044, 0.13737017443790986, 0.16652892954690995, 0.14031458123601576, 0.15461527063584157, 0.15966429894529732, 0.154394638043801, 0.1459457521408128, 0.1832923218320714, 0.2061347031376535, 0.16324217584051984, 0.1534169859177199, 0.16022608027154742, 0.1628399681179009, 0.14533494762138024, 0.16097521054846833, 0.15804829181572244, 0.14210649098126377, 0.16777027956484572, 0.14487665915373688, 0.1583214382403871, 0.15757408855364202, 0.14410097478669381, 0.1655557817674055, 0.15448986549984361, 0.1666104593548441, 0.2320281234815435, 0.16149421956944393, 0.1390202951533169, 0.14055013493578047, 0.2171495850751611, 0.18402861524840328, 0.13812561305510793, 0.15135301286637445], [0.12822586019501847, 0.1321711755229878, 0.14780291045025645, 0.19112732108198258, 0.16460835749376856, 0.20512855801617605, 0.13905743630487483, 0.12991549737465286, 0.12986023761410312, 0.15682962441439094, 0.15617173408981583, 0.18916889825633365, 0.15212586508172765, 0.1361103258060248, 0.13684286337882728, 0.1349381906416406, 0.1441570020654102, 0.15856547089441478, 0.12913389749755522, 0.1333750259016545, 0.13350289606916466, 0.15886633070741857, 0.12926898230236622, 0.13326705145487033, 0.1716497571473108, 0.13139164463427333, 0.1935626638596365, 0.13868435522391082, 0.13426235325259547, 0.11980439053984904, 0.1282176702087814, 0.13674149582020215, 0.15711538053955262, 0.13557976341475253, 0.13150568640905383, 0.13150015832968534, 0.1444623973507264, 0.16416242532876463, 0.15010528483224667, 0.1723917883221508, 0.18454634645090953, 0.13766710248806327, 0.13435774488169153, 0.19383786494230143, 0.20928799956596694, 0.13193350389302197, 0.185304343401545, 0.15817130347005756, 0.1729433508574668, 0.1612704561122801, 0.1547070315354061, 0.16160353671247057, 0.20666092027386476, 0.15233436025005273, 0.16053697665031072, 0.19756549055694927, 0.1782023963051965, 0.13480241581951694, 0.17773748800077005, 0.1369416887968862, 0.1526075769885384, 0.1261822986166664, 0.13865265975850918, 0.12982610455506613, 0.18611607607165134, 0.1411308774753208, 0.20504472163297377, 0.1901091435730258, 0.17181237702186822, 0.11918766659045749, 0.14432961693587548, 0.13753503201927253, 0.14092088902470803, 0.12971933440055586, 0.13681249876336649, 0.2028860498781577, 0.1549730964895876, 0.12690373463942792, 0.1383566781516739, 0.16963981808237397, 0.15641789411864104, 0.17169770649799404, 0.18700527671256195, 0.19065864267818491, 0.1309407474992356, 0.12421216252334584, 0.1710025557453492, 0.13575549986446728, 0.15882914777539564, 0.13421724496738202, 0.18202812515643987, 0.15906333973501838, 0.1841636626578887, 0.1373436010533669, 0.12976290829778933, 0.13138675399128782, 0.15864506874917345, 0.19863290799750477, 0.17376647017387617, 0.13023949278989824], [0.15948700430936635, 0.14881415351029484, 0.1665382543009113, 0.19739384014646436, 0.14279547246593427, 0.1602487290852922, 0.1443502046861278, 0.1477645995216703, 0.14684325626943812, 0.14990244644764686, 0.14016165950457665, 0.13341124326410497, 0.14695877269303975, 0.15227526416044523, 0.15749161164572767, 0.15729223690302188, 0.17221815545678631, 0.14795112917429265, 0.14195110722093066, 0.14277944233436815, 0.2140101235094532, 0.15725194145547766, 0.14708254724843245, 0.14210050867463256, 0.1592661217439993, 0.1412520712506917, 0.1559211435677211, 0.13710481428912988, 0.15442983443747144, 0.1462716055977131, 0.15420765781023116, 0.15049466580589183, 0.15844330611344196, 0.15730163775386505, 0.13719632665171627, 0.1473157278343939, 0.1721010384613611, 0.14233968237993586, 0.16780648469908943, 0.1492351344055081, 0.15765959322331125, 0.16235341894804878, 0.14493121335847772, 0.14589389921317572, 0.17081651987425195, 0.15633121008825107, 0.1479305609682166, 0.14593870864786462, 0.152092534785864, 0.15355355912128726, 0.14434286374829897, 0.1510229795080887, 0.15072913866849413, 0.1494642650707675, 0.16387057416638762, 0.15657492516809682, 0.1538878159711883, 0.15026257442209684, 0.16867977456217942, 0.15113672768320807, 0.16058551730193363, 0.1409273371707429, 0.19357468282904128, 0.16608498159762336, 0.18438814463455766, 0.15231108475675414, 0.14522722828286308, 0.17175235066876413, 0.1857974177693353, 0.15534558453606986, 0.15773736873379368, 0.1491764193562065, 0.15435504236977496, 0.1441683497803102, 0.14629741294381635, 0.19331653657013648, 0.14596771944872128, 0.15143860274713322, 0.16137127041144814, 0.167616707964461, 0.14721037800228215, 0.14974149886198523, 0.16702640806063068, 0.13607495929941996, 0.1710198002388864, 0.14671563891761077, 0.17228400960485835, 0.14747360861474998, 0.13837484929592822, 0.14983993701949844, 0.15192874438016546, 0.210800291105933, 0.1663481371123751, 0.160105628190309, 0.1498394414090056, 0.1505251301163232, 0.16162713515236798, 0.15274782620528793, 0.1462070434707487, 0.14409512840431657], [0.16954625481913121, 0.1901718832551768, 0.19364765772117012, 0.16774955619213022, 0.1709879279384199, 0.1873864099154524, 0.16800038613288693, 0.17146031102016684, 0.1932578565125582, 0.1825115723843282, 0.17563910573113095, 0.1805991194609222, 0.21872448216330007, 0.16615541163012112, 0.17912387972776253, 0.17683514241860326, 0.2074712304366564, 0.1667201774806018, 0.20137746994454503, 0.20172046556992715, 0.18873562539136343, 0.16551425222448643, 0.2103678570826695, 0.2148029259534594, 0.19162833605315965, 0.188215964360798, 0.17737643336816158, 0.182712040180987, 0.18111270486051453, 0.1950686481363047, 0.20807572498200613, 0.23365045823005345, 0.16278356529267482, 0.17409985601202851, 0.19035032723473028, 0.18401884708179825, 0.20483626065550337, 0.17633637851277292, 0.17884612567309285, 0.1790524276221689, 0.16687559462820775, 0.16551655853120426, 0.206778585797234, 0.1717315170803021, 0.16663934126869012, 0.172732005566281, 0.19767059975710108, 0.20947884869266742, 0.20531721260042676, 0.1801119949516722, 0.17960000586146432, 0.17030975955790034, 0.18158202758337436, 0.1934492363690483, 0.17080443982907037, 0.17227865300995154, 0.16295808020635724, 0.17335967307132719, 0.18636540845679442, 0.19308805542779442, 0.19389643145605487, 0.20101712999348448, 0.1931386186431096, 0.17753826550505045, 0.1753950336476594, 0.1733497072817976, 0.18633409640038512, 0.18709204104381216, 0.19312158544133579, 0.16261175753920729, 0.18698021916153518, 0.18023442047035956, 0.20053311344145025, 0.19746230301170137, 0.24064319397807737, 0.18417983171345323, 0.17264348969902368, 0.22006129173634212, 0.18152633986333705, 0.1893185149569937, 0.17501175761817658, 0.19609030686883697, 0.18360964120784243, 0.18184462028283052, 0.20964731718464436, 0.1865260127273663, 0.1600895190121818, 0.18010869589381892, 0.18469217240420463, 0.19363602176455716, 0.21311931629384248, 0.17526706316401044, 0.17581517567359625, 0.18924919629193276, 0.1675528609475671, 0.18333597853796868, 0.17480730186055893, 0.17947291575007915, 0.21004374906240647, 0.18964537163152143], [0.16556888234566478, 0.1542855365452661, 0.13171045437346537, 0.22515718063959847, 0.1871638150635688, 0.21084879604207696, 0.13584147400210997, 0.16901365209078378, 0.12678094619735375, 0.20929235153538567, 0.1615410411632925, 0.12373580059371152, 0.20763958294353171, 0.13411932447274913, 0.15748955307407564, 0.16172036015508454, 0.1563258464284742, 0.12765462751432893, 0.14678717402460714, 0.158933824455612, 0.16484466371386797, 0.14826522168804793, 0.1537785811658445, 0.1268846944561489, 0.16902906345694435, 0.15516187066848797, 0.2125989692086097, 0.13607803032337376, 0.17123074462205154, 0.12353341771676689, 0.13264874447220995, 0.14513724859402746, 0.12611763991080563, 0.15469794202278664, 0.11956405207686889, 0.18990435317450177, 0.1512887162497417, 0.14224948346963717, 0.12924437950298753, 0.17522751403950093, 0.18946108432921774, 0.13309770058129453, 0.22409962798138258, 0.13705240412793485, 0.20528815548880308, 0.1255030218041865, 0.15871383773434533, 0.17341538860959435, 0.154819034256908, 0.1351641267779231, 0.15047050007408552, 0.1771867951157211, 0.13146247412179224, 0.15744292634947019, 0.20755935812924636, 0.1555266510405062, 0.12700866230512273, 0.12919432399308087, 0.16832852360454514, 0.1617620175653375, 0.1738900850870444, 0.12818055476453447, 0.16598976403885946, 0.11573463065115226, 0.13793367837765233, 0.128952557698321, 0.1733299065757096, 0.18323846661577872, 0.1519633497587757, 0.1554289052947499, 0.13362825772232528, 0.1334864427841444, 0.1347836643576305, 0.12894117657907336, 0.1475220433429826, 0.2157213627653278, 0.14810190732924422, 0.14752796987970598, 0.14079578114204855, 0.13514631837280827, 0.15209738570431897, 0.12679777674187553, 0.16395648069730878, 0.16137703834882056, 0.15092646845268748, 0.1410347727059475, 0.14557265605263836, 0.1353881271591467, 0.12594538383963186, 0.16269129972463442, 0.1719459730609683, 0.1697697847791753, 0.15228860610137906, 0.14982602831684774, 0.21084703137930993, 0.17422440205494064, 0.1899229731775834, 0.1870277978960944, 0.18588329625407415, 0.12844614527571546], [0.1894598231055358, 0.13277356275571717, 0.13889863339653638, 0.1621285962686956, 0.13591260887448375, 0.12810067370823977, 0.16251866268512136, 0.166442123415905, 0.12896292716048502, 0.15781427073441573, 0.1523306541449955, 0.12163783256458402, 0.17847831364218555, 0.14091482198895963, 0.14333145620197343, 0.17521367867463383, 0.15884103109302705, 0.13081814938395311, 0.163675463609266, 0.12610954026019577, 0.14344264772836007, 0.1392711796115823, 0.20016092172461772, 0.1310195353738602, 0.1639585650356019, 0.13906282460611474, 0.23956324621062547, 0.12902474370878173, 0.18400885927702507, 0.15879088109109832, 0.12016688480685905, 0.13415782123778275, 0.13290599360965566, 0.15110266415998144, 0.12170398235752643, 0.1361592867343966, 0.1822649624812303, 0.14086891664293014, 0.1314999838503278, 0.13454794764224, 0.13916079848909713, 0.1343677725549534, 0.1507830223780761, 0.12462988122691722, 0.19656789566387126, 0.12787260376258808, 0.17343737371677673, 0.23581427107799494, 0.17973114091404152, 0.12751841475562575, 0.1352489239120318, 0.13719867047872888, 0.19277737769413805, 0.18043775217361838, 0.13371688336003926, 0.16893044787928432, 0.19984670908824864, 0.12607671753429764, 0.16386311065255632, 0.1237143269094767, 0.15993075983870222, 0.16826168214238627, 0.1677582642446411, 0.1346298259813943, 0.14141286276794254, 0.1563206400622418, 0.19579332900313148, 0.13684806356838447, 0.13394577546546602, 0.13198841403617684, 0.1656500351101068, 0.13069728581420353, 0.18706825822485465, 0.13117417236765383, 0.2103800904098541, 0.15789313250519335, 0.1333311480734136, 0.1374074740879396, 0.1376537602670433, 0.13815572333728426, 0.14139245169047537, 0.1663786563641575, 0.1385070291365642, 0.17905247594965065, 0.13808893189418994, 0.11703491283175965, 0.16921414614391042, 0.13271469951766737, 0.16735859847950035, 0.1712028328992981, 0.13020290097599665, 0.1793711973162959, 0.12972729027855906, 0.13526515183495066, 0.16184216729989287, 0.13900252039648722, 0.12898022588702288, 0.2241999903676712, 0.18739026613086757, 0.15751397881353915]]
    lossvec0 = [[0.18716330553485447, 0.18860184054407664, 0.19325608589009952, 0.1770557715099232, 0.18909962053862173, 0.18459170372398095, 0.18559537079732366, 0.19418957403161127, 0.19056777303140543, 0.19661722173995794, 0.18615517172133905, 0.18656234789959142, 0.18207911627849313, 0.19136687879390743, 0.19674573354643832, 0.1868874400406348, 0.18707867853840698, 0.1935239829381169, 0.18205086526045547, 0.19672122304180922, 0.18881630904487404, 0.1833803571459253, 0.19315812241755476, 0.1939300012408022, 0.1823919862711381, 0.19573388201746308, 0.18127684565012528, 0.1845268243447256, 0.2064338189794515, 0.20159672625324548, 0.175570766914338, 0.19471220948547244, 0.19506311055926825, 0.20018623541754793, 0.19098447267714874, 0.19502464029641609, 0.17798875406147763, 0.19399013962692402, 0.19200981099081268, 0.1946489101903228, 0.19112257101531924, 0.19993782678396535, 0.18597183732475736, 0.17973046264056863, 0.19279044896209913, 0.18991506529423824, 0.1849965998756091, 0.18460638724691056, 0.187766224917971, 0.18747905139303478, 0.17826392927939785, 0.19325741567524662, 0.18312120450517352, 0.192776652857974, 0.1857877196910409, 0.1858789089584243, 0.18760130405861783, 0.18436246826117497, 0.18657854615884836, 0.20529250618228734, 0.1854399759521401, 0.18781946613353975, 0.19103850589477586, 0.19321925534650095, 0.1833887432242402, 0.19466555433451851, 0.17968140555283613, 0.18826368627863668, 0.18936852542619723, 0.18239636499178297, 0.18166912854423528, 0.1886670787540829, 0.18214968590293265, 0.18688054274220603, 0.2007408440158043, 0.1887733025755799, 0.17529884693459136, 0.1945086526775307, 0.19507746617481378, 0.19771191076229758, 0.1900978061604873, 0.18303813831240057, 0.1848877412408327, 0.1815693595110686, 0.20485972236370922, 0.19125618875026087, 0.18942591264028497, 0.1927734061166825, 0.19628853444448496, 0.18576300190829131, 0.19292331937386653, 0.19252042667402308, 0.19919255729620128, 0.17874313897780772, 0.19420424824610283, 0.19765025474532247, 0.18019946811985466, 0.18734538778408527, 0.18392117311158634, 0.1831644019563764]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### overEstWt=1., rateTarget=0.4 ###
    # Get null first
    underWt, t = 1., 0.4
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Design 0']
    lossveclist = [[0.05869716357936193, 0.06496469072191993, 0.06445388890620267, 0.061190271263857884, 0.060801952120124174, 0.0628518155011463, 0.06103055368862017, 0.0645339303067024, 0.06345518080997543, 0.06798749988287238, 0.0635577827604388, 0.06448244774348906, 0.06460408960457555, 0.06423479803724086, 0.06346570148697925, 0.0610220274476332, 0.06653268660497995, 0.0637819632898739, 0.06458153281918987, 0.06219370776874488, 0.06158502380780164, 0.06450099815646547, 0.06261581321267679, 0.06241165203529875, 0.06127086472011553, 0.06284592849557297, 0.06433899359307356, 0.06298260297368505, 0.06333552441384119, 0.061629484523442635, 0.06555605978760054, 0.06382096899959443, 0.06501828365590352, 0.06262780410665626, 0.06140928933603194, 0.06260452785273529, 0.06452117625338971, 0.06131657543913682, 0.06331224204223371, 0.059988330185667786, 0.06040264892287001, 0.06288617348285885, 0.06166245680508134, 0.0628351006999992, 0.06251416854556381, 0.06278572087523576, 0.06433018328228853, 0.060095054181502905, 0.0626561852934667, 0.06395959213148232, 0.06599653261118309, 0.06301622084736008, 0.06534010734028481, 0.06182977435688999, 0.060662926582686065, 0.06509633058008522, 0.06571845189114096, 0.06336204765334655, 0.06121765310765021, 0.06212960321981213, 0.06139979355188204, 0.06715352252234444, 0.06494291982692406, 0.0630487850259678, 0.05997319784634728, 0.06093541747803282, 0.062345506188413474, 0.05898777693762918, 0.06426586972711376, 0.06636850613688819, 0.05779544547041826, 0.06434274816921044, 0.06208405024947255, 0.06377646674187719, 0.06871680581791573, 0.06252993209726768, 0.06316452053900942, 0.0640895085756315, 0.06197286743720706, 0.060706810755013996, 0.06439778673649788, 0.06553858203941768, 0.06679639345658742, 0.06140427401580309, 0.06518312241091204, 0.06411355265029997, 0.06358547090601545, 0.06435113477421903, 0.06085434251111577, 0.06343789286904834, 0.06418355308710491, 0.06435364560539769, 0.061155853975873246, 0.06391964006755392, 0.06019878534789032, 0.06399455155349086, 0.0591792232272502, 0.061147998138276795, 0.06630087518492675, 0.063835916003289]]
    '''
    # 30 tests for all designs
    underWt, t = 1., 0.4
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.04718947466709231, 0.046553585017072636, 0.052441688225299425, 0.05142784398450772, 0.046390263414362864, 0.051698049737683556, 0.047687574554680354, 0.0505419556635018, 0.047825610693482186, 0.047304684784099396, 0.05032773327557194, 0.045866836046140835, 0.04731872633796882, 0.04849988735453309, 0.049833875600876903, 0.05328195537423884, 0.05202206828613756, 0.04698807342979201, 0.04530187048423474, 0.04713490395600838, 0.05589074135663584, 0.050074601384535344, 0.046701690276989165, 0.04593018728222049, 0.05643642453230507, 0.04804260259106695, 0.05285151581410675, 0.04852504573649602, 0.05001104938159274, 0.04829438047555947, 0.046032411527801013, 0.048433839785773494, 0.05205737244071572, 0.05245656060786794, 0.044547490664291416, 0.050402855221848696, 0.0520232095764459, 0.05104728442799498, 0.049435110552061304, 0.05040513734288222, 0.058983784498691294, 0.04622636707546684, 0.046203887020108546, 0.049674070038625555, 0.05377995874049181, 0.04272867131056178, 0.048664447648189245, 0.05108022669062065, 0.04808777371555936, 0.04773567155828597, 0.0450558113520085, 0.04959772643375383, 0.04866410298505742, 0.052034115222010735, 0.04996997044282836, 0.04916178365000783, 0.0496805088532744, 0.049017330645103885, 0.04681821650649419, 0.04928261377110753, 0.04647344134530747, 0.04621650629459626, 0.04907718845812723, 0.0505965734401475, 0.054224008336253626, 0.047962683302389536, 0.05047017075775085, 0.04756326814889569, 0.053087459122950535, 0.04943206054309928, 0.0490911212469289, 0.05537001186878515, 0.052115193956457716, 0.04654668529053779, 0.05033283814871047, 0.06491828642516612, 0.04984620149171715, 0.04696845876693901, 0.052696972519148656, 0.04796090608182052, 0.04989275734293907, 0.0474146231424664, 0.047196056872370135, 0.04935695516231519, 0.048711933446900335, 0.04561887327753751, 0.04920745736993924, 0.054215819692971394, 0.0459418596674953, 0.04689973247421375, 0.04962532929275384, 0.04845276012740564, 0.06610363063631257, 0.060747937019962034, 0.05150789510837962, 0.04972581725824374, 0.052775827152395934, 0.0510685154422887, 0.04846971783522132, 0.047901722939409364], [0.04202643550609381, 0.06589450517212515, 0.043377190719077155, 0.059862902521271716, 0.06386016045956844, 0.04296398068290836, 0.03970765683733988, 0.04439803392363333, 0.05156554515835239, 0.07326249907031858, 0.04384704357841969, 0.04976415829662597, 0.055601419363565434, 0.04793100015686585, 0.06933859539248141, 0.0427233892114996, 0.054799886501655945, 0.04390025401749118, 0.04036817034949196, 0.044708069654443766, 0.04334447099807764, 0.04230648572494449, 0.04209920350460376, 0.052455990127224295, 0.044172404899220946, 0.05205554819906337, 0.05199661406598822, 0.0465113616568588, 0.048763746055357264, 0.04696494754945756, 0.0613356521377245, 0.04311738546489749, 0.04457616762342732, 0.05840162444131683, 0.04389920529204706, 0.05095654729267569, 0.044746143872630324, 0.04324502042935202, 0.050261898916394966, 0.04485845693189978, 0.06404627184768251, 0.04248406122614014, 0.04291656692790913, 0.049617111614401535, 0.0677677984530416, 0.04267913904061335, 0.05033123315478716, 0.057283401428623315, 0.05712040014699135, 0.042500230273976376, 0.043475822695473065, 0.04499635354313451, 0.053478980260077816, 0.049534479004213566, 0.05789027015354712, 0.050100573126581706, 0.04325841843879437, 0.04311789564958334, 0.0667746223800157, 0.06919444648680512, 0.05094999365581101, 0.043617255890164165, 0.04012019471628615, 0.045440838820962955, 0.043596933660373906, 0.041854706317297, 0.052224833195818735, 0.04521175529935366, 0.04198122065821659, 0.04695900796407898, 0.042825262728654105, 0.04328952783296294, 0.04504703161377443, 0.05315872068966912, 0.04315115004245762, 0.06377502138233124, 0.05228229264502121, 0.05097086375250558, 0.051179035384482374, 0.046281136548554584, 0.059988497648267775, 0.0529469186163836, 0.0434966641746704, 0.07124195684882738, 0.043262028314717024, 0.03992375414421128, 0.04543022290840141, 0.04360952764864418, 0.04007303438578696, 0.06236830480064966, 0.04178925928829542, 0.06719154470076101, 0.06103951545667047, 0.05283062791484994, 0.043435908679902345, 0.052875944486525016, 0.04178131224495984, 0.041641693893051404, 0.06271528870021247, 0.04506044471943217], [0.056375782535309366, 0.0540164404568614, 0.06142207121137624, 0.08333916108781919, 0.04702345417667515, 0.04630761654708922, 0.05634646121030997, 0.04682124152446064, 0.04978352752023907, 0.04636380493886591, 0.04869848754116311, 0.04468936231514173, 0.05332282663771207, 0.04718398234090467, 0.05190222039683934, 0.047523624905599346, 0.05508253746910051, 0.0468192222360863, 0.07365915645383718, 0.05529786532649205, 0.05455078857931464, 0.05207129555069004, 0.05427197038609077, 0.04550540306670446, 0.05637574898574325, 0.04740855699675642, 0.05679164985149167, 0.05118724470720141, 0.061399334349447825, 0.05435914453080109, 0.050453417636448145, 0.05698062382096072, 0.048348021977917155, 0.05670013450784788, 0.05263234247266128, 0.04953114853201924, 0.044945374415620694, 0.06233847472589005, 0.05910463900508917, 0.0511041237059723, 0.062081755919400725, 0.051337176981404796, 0.04878507732867753, 0.050286527330977736, 0.06548252589907094, 0.055885857616232854, 0.04923185224101348, 0.048199026849183944, 0.051239585026177925, 0.051349416804423904, 0.0538318521148374, 0.0569931992618994, 0.04554032874804494, 0.04954248013130453, 0.04928320615672681, 0.0472163612170336, 0.05673778440821332, 0.04575724829998562, 0.04811606196136697, 0.04635627086347767, 0.04551970771937594, 0.06868034746364289, 0.05649548822498982, 0.05811486447740096, 0.0453318963770274, 0.04956348033187072, 0.04529245536240283, 0.04989037821298754, 0.045519396641266786, 0.047555005381776386, 0.04530123546809766, 0.04328601175164473, 0.05438778908544311, 0.05061164206743058, 0.05243637808180345, 0.06753855094214896, 0.04936519789315764, 0.047272759909694, 0.05488646607014433, 0.04697148836131248, 0.0591261650270494, 0.0487081473811296, 0.04417860365426792, 0.04921702742865538, 0.052954080594235564, 0.0503531079562106, 0.05313215271030215, 0.05073453487341686, 0.04639133189780766, 0.06373618714186649, 0.04763925005600707, 0.045335895520981086, 0.054596180318519524, 0.04691142479493527, 0.047056621681336175, 0.04905121601700016, 0.04452933176775695, 0.05668207167266129, 0.04961786284833492, 0.05825280150820189], [0.061928482311921086, 0.0587581476874802, 0.056148473026565074, 0.06166995515565239, 0.06565779626435884, 0.05980544750085227, 0.05909271269634892, 0.06793258235046004, 0.05703475457171625, 0.06504304169672175, 0.0602574527625619, 0.06456802579600043, 0.07206479627250462, 0.062440123721270786, 0.06492519611970508, 0.06205768778279433, 0.060933552677926626, 0.0560849006290909, 0.06474606752558366, 0.05787250955232471, 0.06064670559238793, 0.05658853795139464, 0.06355919809712081, 0.0667891845245568, 0.06056704134276551, 0.056945472128210675, 0.06387088314474369, 0.05946546261066135, 0.05836864693024579, 0.06624898301047073, 0.05970416952178477, 0.0756323372074193, 0.05914731902802569, 0.06988714949441664, 0.06722556844154236, 0.06371067082828374, 0.0730909780658769, 0.05919535646869778, 0.06130116318412533, 0.05867978154122717, 0.06254818926318269, 0.060321005931503205, 0.06609217229072012, 0.061790033423365635, 0.060818679168426315, 0.057601795235921044, 0.059975299663291376, 0.0677695453653534, 0.061238646018946026, 0.053836385085828525, 0.057911207668327365, 0.06299959274779497, 0.05661947381660562, 0.056703936702377396, 0.07542446608460204, 0.05933371137224752, 0.06853792821681826, 0.05635574727325928, 0.06381232730754664, 0.059362748105546426, 0.07153634720563387, 0.06471665521713847, 0.07424850580984757, 0.06081901171001376, 0.06338576286821111, 0.06522675746078284, 0.06294212831808836, 0.062249098551463954, 0.06440076960587542, 0.06377587086846702, 0.05681749329960772, 0.061003761270497746, 0.060043798780413736, 0.05924611680888631, 0.06776499981444438, 0.07124408238322676, 0.05875534701246783, 0.06621401377555956, 0.06028833225751559, 0.06386002163946665, 0.05798760233068233, 0.06230492200612411, 0.07476821507009576, 0.062482796141876955, 0.05830598429063079, 0.05979813815871211, 0.059741535236514993, 0.05876383246645608, 0.0665503467756949, 0.06860598262493801, 0.07286870483361216, 0.058094102806268734, 0.05781132704327996, 0.06635116887066655, 0.058732348692566314, 0.06352966038863633, 0.05803779536144432, 0.061431418123421386, 0.06589407692005882, 0.06130783688132981], [0.040489321553820526, 0.04244078998180305, 0.04125966074347432, 0.05667209468853502, 0.044225696511919044, 0.04927599223256981, 0.04224237766217725, 0.060950837742035906, 0.038977039787093944, 0.0674208501899324, 0.041850180498087496, 0.043858118989270015, 0.042042116457551446, 0.044755060173182044, 0.05122016456133793, 0.04471540266864987, 0.043701532174481555, 0.04409056571347227, 0.05853504595090346, 0.04047059168317013, 0.042864691018189294, 0.053394472814121074, 0.053686346681494704, 0.04526485814000074, 0.04401526196275226, 0.04762915794587917, 0.0602309627385934, 0.04914290040151967, 0.04414413930695505, 0.05544949991619214, 0.060486706117795094, 0.05306546016244729, 0.05679612061944266, 0.042380391980056484, 0.03826244773170778, 0.04370093592918342, 0.06479867693245595, 0.05088980504293229, 0.04527679229850352, 0.051052289499822615, 0.0553097897910019, 0.044692784017188965, 0.057045323447748916, 0.06416777639064077, 0.06876808947560054, 0.04786405318938938, 0.051604196622558475, 0.07762173809320441, 0.06337059443462839, 0.0415575907100501, 0.04174956317184485, 0.04896049827364559, 0.04417308215353506, 0.06020389487577384, 0.056249980248916795, 0.04845916794865732, 0.043452893561183537, 0.05914347195847798, 0.05984951174250666, 0.04986840231400949, 0.06845115714067525, 0.041836817741971906, 0.05479219477183879, 0.04183408633306046, 0.044618556420927234, 0.054295738860990254, 0.053218465722711605, 0.04451430074143453, 0.048376549299497404, 0.04245751408580303, 0.043719311911518344, 0.05352631085925154, 0.04699906285230979, 0.040184977928674225, 0.04486253275655541, 0.05099136671006231, 0.04198374884484359, 0.04183976052918914, 0.054296000789238866, 0.04220670612743487, 0.04351445217117176, 0.047827918028844146, 0.051114036092779556, 0.043451681565485525, 0.04280973595988829, 0.042541004765868244, 0.0437248854444402, 0.05501642342091162, 0.06416113031242052, 0.06472977784046886, 0.05349957721005731, 0.05174012685278827, 0.05303908699945791, 0.07453312469858808, 0.05086995277909006, 0.042851611524546585, 0.04808428401105628, 0.0485197422613639, 0.0722407547569935, 0.04161740204102268], [0.05197818548931857, 0.04283416780838432, 0.05275307225337346, 0.0626196705953624, 0.05851077997098658, 0.05259595870874338, 0.04504015742426838, 0.04171876706369997, 0.051138309917515834, 0.06337962379048559, 0.0518289147308588, 0.062492123239681056, 0.044082780973521404, 0.04414207122954296, 0.044330476814432994, 0.043683675690194754, 0.05421848561663584, 0.04030282790268034, 0.043860758659854254, 0.04489878686938463, 0.0457607625132273, 0.051613216582683405, 0.04685057825012286, 0.039782893911372144, 0.0416034061510837, 0.04978413984845904, 0.06681992615392633, 0.04852453381773872, 0.042450942844571446, 0.045809513045281094, 0.05105538833316079, 0.052781024592023586, 0.044141608378222195, 0.05817328313228881, 0.04072748896561036, 0.04422682148349758, 0.043930210172144074, 0.04526188882429295, 0.042302668931202304, 0.04316624317728075, 0.06035328968170272, 0.04243423637827852, 0.04238073910532582, 0.045247034733862636, 0.06294793330677213, 0.04290226029304104, 0.05072919812844076, 0.04460952361292469, 0.0453650056951224, 0.04363795747549339, 0.05289023600968533, 0.0423946668295946, 0.061044996351850594, 0.05121697475413964, 0.062309087411169146, 0.04390508295791547, 0.041728948649031525, 0.04182875209138459, 0.06419102265518958, 0.04373679692381783, 0.047552119376513, 0.043805383237774664, 0.040219836839461724, 0.040581250453936416, 0.043812817478909985, 0.04168312753181721, 0.061032179384050596, 0.04182093384536687, 0.04584221604400611, 0.04261003974310658, 0.05775532123884922, 0.04404271999533429, 0.04706827295331688, 0.04293383705509819, 0.04208396963928862, 0.07189412684593975, 0.043245590114054315, 0.04254883876614613, 0.0428727453843279, 0.05881362313255464, 0.05697398424736654, 0.0532204242106488, 0.06575700009065709, 0.04381752623303783, 0.04108377046102695, 0.041303849612705446, 0.0587384378426794, 0.04502196660975431, 0.044209104925344814, 0.054621022899475374, 0.042964824776503915, 0.051812176361804865, 0.041557561444120455, 0.042586058825917206, 0.043068378898926556, 0.04431068129240971, 0.042503391950227884, 0.0607587899777066, 0.05472818866556392, 0.04196667552235796]]
    lossvec0 = [[0.05869716357936193, 0.06496469072191993, 0.06445388890620267, 0.061190271263857884, 0.060801952120124174, 0.0628518155011463, 0.06103055368862017, 0.0645339303067024, 0.06345518080997543, 0.06798749988287238, 0.0635577827604388, 0.06448244774348906, 0.06460408960457555, 0.06423479803724086, 0.06346570148697925, 0.0610220274476332, 0.06653268660497995, 0.0637819632898739, 0.06458153281918987, 0.06219370776874488, 0.06158502380780164, 0.06450099815646547, 0.06261581321267679, 0.06241165203529875, 0.06127086472011553, 0.06284592849557297, 0.06433899359307356, 0.06298260297368505, 0.06333552441384119, 0.061629484523442635, 0.06555605978760054, 0.06382096899959443, 0.06501828365590352, 0.06262780410665626, 0.06140928933603194, 0.06260452785273529, 0.06452117625338971, 0.06131657543913682, 0.06331224204223371, 0.059988330185667786, 0.06040264892287001, 0.06288617348285885, 0.06166245680508134, 0.0628351006999992, 0.06251416854556381, 0.06278572087523576, 0.06433018328228853, 0.060095054181502905, 0.0626561852934667, 0.06395959213148232, 0.06599653261118309, 0.06301622084736008, 0.06534010734028481, 0.06182977435688999, 0.060662926582686065, 0.06509633058008522, 0.06571845189114096, 0.06336204765334655, 0.06121765310765021, 0.06212960321981213, 0.06139979355188204, 0.06715352252234444, 0.06494291982692406, 0.0630487850259678, 0.05997319784634728, 0.06093541747803282, 0.062345506188413474, 0.05898777693762918, 0.06426586972711376, 0.06636850613688819, 0.05779544547041826, 0.06434274816921044, 0.06208405024947255, 0.06377646674187719, 0.06871680581791573, 0.06252993209726768, 0.06316452053900942, 0.0640895085756315, 0.06197286743720706, 0.060706810755013996, 0.06439778673649788, 0.06553858203941768, 0.06679639345658742, 0.06140427401580309, 0.06518312241091204, 0.06411355265029997, 0.06358547090601545, 0.06435113477421903, 0.06085434251111577, 0.06343789286904834, 0.06418355308710491, 0.06435364560539769, 0.061155853975873246, 0.06391964006755392, 0.06019878534789032, 0.06399455155349086, 0.0591792232272502, 0.061147998138276795, 0.06630087518492675, 0.063835916003289]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.4$, $n=30$')
    
    lossveclist = [[0.04718947466709231, 0.046553585017072636, 0.052441688225299425, 0.05142784398450772, 0.046390263414362864, 0.051698049737683556, 0.047687574554680354, 0.0505419556635018, 0.047825610693482186, 0.047304684784099396, 0.05032773327557194, 0.045866836046140835, 0.04731872633796882, 0.04849988735453309, 0.049833875600876903, 0.05328195537423884, 0.05202206828613756, 0.04698807342979201, 0.04530187048423474, 0.04713490395600838, 0.05589074135663584, 0.050074601384535344, 0.046701690276989165, 0.04593018728222049, 0.05643642453230507, 0.04804260259106695, 0.05285151581410675, 0.04852504573649602, 0.05001104938159274, 0.04829438047555947, 0.046032411527801013, 0.048433839785773494, 0.05205737244071572, 0.05245656060786794, 0.044547490664291416, 0.050402855221848696, 0.0520232095764459, 0.05104728442799498, 0.049435110552061304, 0.05040513734288222, 0.058983784498691294, 0.04622636707546684, 0.046203887020108546, 0.049674070038625555, 0.05377995874049181, 0.04272867131056178, 0.048664447648189245, 0.05108022669062065, 0.04808777371555936, 0.04773567155828597, 0.0450558113520085, 0.04959772643375383, 0.04866410298505742, 0.052034115222010735, 0.04996997044282836, 0.04916178365000783, 0.0496805088532744, 0.049017330645103885, 0.04681821650649419, 0.04928261377110753, 0.04647344134530747, 0.04621650629459626, 0.04907718845812723, 0.0505965734401475, 0.054224008336253626, 0.047962683302389536, 0.05047017075775085, 0.04756326814889569, 0.053087459122950535, 0.04943206054309928, 0.0490911212469289, 0.05537001186878515, 0.052115193956457716, 0.04654668529053779, 0.05033283814871047, 0.06491828642516612, 0.04984620149171715, 0.04696845876693901, 0.052696972519148656, 0.04796090608182052, 0.04989275734293907, 0.0474146231424664, 0.047196056872370135, 0.04935695516231519, 0.048711933446900335, 0.04561887327753751, 0.04920745736993924, 0.054215819692971394, 0.0459418596674953, 0.04689973247421375, 0.04962532929275384, 0.04845276012740564, 0.06610363063631257, 0.060747937019962034, 0.05150789510837962, 0.04972581725824374, 0.052775827152395934, 0.0510685154422887, 0.04846971783522132, 0.047901722939409364], [0.04202643550609381, 0.06589450517212515, 0.043377190719077155, 0.059862902521271716, 0.06386016045956844, 0.04296398068290836, 0.03970765683733988, 0.04439803392363333, 0.05156554515835239, 0.07326249907031858, 0.04384704357841969, 0.04976415829662597, 0.055601419363565434, 0.04793100015686585, 0.06933859539248141, 0.0427233892114996, 0.054799886501655945, 0.04390025401749118, 0.04036817034949196, 0.044708069654443766, 0.04334447099807764, 0.04230648572494449, 0.04209920350460376, 0.052455990127224295, 0.044172404899220946, 0.05205554819906337, 0.05199661406598822, 0.0465113616568588, 0.048763746055357264, 0.04696494754945756, 0.0613356521377245, 0.04311738546489749, 0.04457616762342732, 0.05840162444131683, 0.04389920529204706, 0.05095654729267569, 0.044746143872630324, 0.04324502042935202, 0.050261898916394966, 0.04485845693189978, 0.06404627184768251, 0.04248406122614014, 0.04291656692790913, 0.049617111614401535, 0.0677677984530416, 0.04267913904061335, 0.05033123315478716, 0.057283401428623315, 0.05712040014699135, 0.042500230273976376, 0.043475822695473065, 0.04499635354313451, 0.053478980260077816, 0.049534479004213566, 0.05789027015354712, 0.050100573126581706, 0.04325841843879437, 0.04311789564958334, 0.0667746223800157, 0.06919444648680512, 0.05094999365581101, 0.043617255890164165, 0.04012019471628615, 0.045440838820962955, 0.043596933660373906, 0.041854706317297, 0.052224833195818735, 0.04521175529935366, 0.04198122065821659, 0.04695900796407898, 0.042825262728654105, 0.04328952783296294, 0.04504703161377443, 0.05315872068966912, 0.04315115004245762, 0.06377502138233124, 0.05228229264502121, 0.05097086375250558, 0.051179035384482374, 0.046281136548554584, 0.059988497648267775, 0.0529469186163836, 0.0434966641746704, 0.07124195684882738, 0.043262028314717024, 0.03992375414421128, 0.04543022290840141, 0.04360952764864418, 0.04007303438578696, 0.06236830480064966, 0.04178925928829542, 0.06719154470076101, 0.06103951545667047, 0.05283062791484994, 0.043435908679902345, 0.052875944486525016, 0.04178131224495984, 0.041641693893051404, 0.06271528870021247, 0.04506044471943217], [0.056375782535309366, 0.0540164404568614, 0.06142207121137624, 0.08333916108781919, 0.04702345417667515, 0.04630761654708922, 0.05634646121030997, 0.04682124152446064, 0.04978352752023907, 0.04636380493886591, 0.04869848754116311, 0.04468936231514173, 0.05332282663771207, 0.04718398234090467, 0.05190222039683934, 0.047523624905599346, 0.05508253746910051, 0.0468192222360863, 0.07365915645383718, 0.05529786532649205, 0.05455078857931464, 0.05207129555069004, 0.05427197038609077, 0.04550540306670446, 0.05637574898574325, 0.04740855699675642, 0.05679164985149167, 0.05118724470720141, 0.061399334349447825, 0.05435914453080109, 0.050453417636448145, 0.05698062382096072, 0.048348021977917155, 0.05670013450784788, 0.05263234247266128, 0.04953114853201924, 0.044945374415620694, 0.06233847472589005, 0.05910463900508917, 0.0511041237059723, 0.062081755919400725, 0.051337176981404796, 0.04878507732867753, 0.050286527330977736, 0.06548252589907094, 0.055885857616232854, 0.04923185224101348, 0.048199026849183944, 0.051239585026177925, 0.051349416804423904, 0.0538318521148374, 0.0569931992618994, 0.04554032874804494, 0.04954248013130453, 0.04928320615672681, 0.0472163612170336, 0.05673778440821332, 0.04575724829998562, 0.04811606196136697, 0.04635627086347767, 0.04551970771937594, 0.06868034746364289, 0.05649548822498982, 0.05811486447740096, 0.0453318963770274, 0.04956348033187072, 0.04529245536240283, 0.04989037821298754, 0.045519396641266786, 0.047555005381776386, 0.04530123546809766, 0.04328601175164473, 0.05438778908544311, 0.05061164206743058, 0.05243637808180345, 0.06753855094214896, 0.04936519789315764, 0.047272759909694, 0.05488646607014433, 0.04697148836131248, 0.0591261650270494, 0.0487081473811296, 0.04417860365426792, 0.04921702742865538, 0.052954080594235564, 0.0503531079562106, 0.05313215271030215, 0.05073453487341686, 0.04639133189780766, 0.06373618714186649, 0.04763925005600707, 0.045335895520981086, 0.054596180318519524, 0.04691142479493527, 0.047056621681336175, 0.04905121601700016, 0.04452933176775695, 0.05668207167266129, 0.04961786284833492, 0.05825280150820189], [0.061928482311921086, 0.0587581476874802, 0.056148473026565074, 0.06166995515565239, 0.06565779626435884, 0.05980544750085227, 0.05909271269634892, 0.06793258235046004, 0.05703475457171625, 0.06504304169672175, 0.0602574527625619, 0.06456802579600043, 0.07206479627250462, 0.062440123721270786, 0.06492519611970508, 0.06205768778279433, 0.060933552677926626, 0.0560849006290909, 0.06474606752558366, 0.05787250955232471, 0.06064670559238793, 0.05658853795139464, 0.06355919809712081, 0.0667891845245568, 0.06056704134276551, 0.056945472128210675, 0.06387088314474369, 0.05946546261066135, 0.05836864693024579, 0.06624898301047073, 0.05970416952178477, 0.0756323372074193, 0.05914731902802569, 0.06988714949441664, 0.06722556844154236, 0.06371067082828374, 0.0730909780658769, 0.05919535646869778, 0.06130116318412533, 0.05867978154122717, 0.06254818926318269, 0.060321005931503205, 0.06609217229072012, 0.061790033423365635, 0.060818679168426315, 0.057601795235921044, 0.059975299663291376, 0.0677695453653534, 0.061238646018946026, 0.053836385085828525, 0.057911207668327365, 0.06299959274779497, 0.05661947381660562, 0.056703936702377396, 0.07542446608460204, 0.05933371137224752, 0.06853792821681826, 0.05635574727325928, 0.06381232730754664, 0.059362748105546426, 0.07153634720563387, 0.06471665521713847, 0.07424850580984757, 0.06081901171001376, 0.06338576286821111, 0.06522675746078284, 0.06294212831808836, 0.062249098551463954, 0.06440076960587542, 0.06377587086846702, 0.05681749329960772, 0.061003761270497746, 0.060043798780413736, 0.05924611680888631, 0.06776499981444438, 0.07124408238322676, 0.05875534701246783, 0.06621401377555956, 0.06028833225751559, 0.06386002163946665, 0.05798760233068233, 0.06230492200612411, 0.07476821507009576, 0.062482796141876955, 0.05830598429063079, 0.05979813815871211, 0.059741535236514993, 0.05876383246645608, 0.0665503467756949, 0.06860598262493801, 0.07286870483361216, 0.058094102806268734, 0.05781132704327996, 0.06635116887066655, 0.058732348692566314, 0.06352966038863633, 0.05803779536144432, 0.061431418123421386, 0.06589407692005882, 0.06130783688132981], [0.040489321553820526, 0.04244078998180305, 0.04125966074347432, 0.05667209468853502, 0.044225696511919044, 0.04927599223256981, 0.04224237766217725, 0.060950837742035906, 0.038977039787093944, 0.0674208501899324, 0.041850180498087496, 0.043858118989270015, 0.042042116457551446, 0.044755060173182044, 0.05122016456133793, 0.04471540266864987, 0.043701532174481555, 0.04409056571347227, 0.05853504595090346, 0.04047059168317013, 0.042864691018189294, 0.053394472814121074, 0.053686346681494704, 0.04526485814000074, 0.04401526196275226, 0.04762915794587917, 0.0602309627385934, 0.04914290040151967, 0.04414413930695505, 0.05544949991619214, 0.060486706117795094, 0.05306546016244729, 0.05679612061944266, 0.042380391980056484, 0.03826244773170778, 0.04370093592918342, 0.06479867693245595, 0.05088980504293229, 0.04527679229850352, 0.051052289499822615, 0.0553097897910019, 0.044692784017188965, 0.057045323447748916, 0.06416777639064077, 0.06876808947560054, 0.04786405318938938, 0.051604196622558475, 0.07762173809320441, 0.06337059443462839, 0.0415575907100501, 0.04174956317184485, 0.04896049827364559, 0.04417308215353506, 0.06020389487577384, 0.056249980248916795, 0.04845916794865732, 0.043452893561183537, 0.05914347195847798, 0.05984951174250666, 0.04986840231400949, 0.06845115714067525, 0.041836817741971906, 0.05479219477183879, 0.04183408633306046, 0.044618556420927234, 0.054295738860990254, 0.053218465722711605, 0.04451430074143453, 0.048376549299497404, 0.04245751408580303, 0.043719311911518344, 0.05352631085925154, 0.04699906285230979, 0.040184977928674225, 0.04486253275655541, 0.05099136671006231, 0.04198374884484359, 0.04183976052918914, 0.054296000789238866, 0.04220670612743487, 0.04351445217117176, 0.047827918028844146, 0.051114036092779556, 0.043451681565485525, 0.04280973595988829, 0.042541004765868244, 0.0437248854444402, 0.05501642342091162, 0.06416113031242052, 0.06472977784046886, 0.05349957721005731, 0.05174012685278827, 0.05303908699945791, 0.07453312469858808, 0.05086995277909006, 0.042851611524546585, 0.04808428401105628, 0.0485197422613639, 0.0722407547569935, 0.04161740204102268], [0.05197818548931857, 0.04283416780838432, 0.05275307225337346, 0.0626196705953624, 0.05851077997098658, 0.05259595870874338, 0.04504015742426838, 0.04171876706369997, 0.051138309917515834, 0.06337962379048559, 0.0518289147308588, 0.062492123239681056, 0.044082780973521404, 0.04414207122954296, 0.044330476814432994, 0.043683675690194754, 0.05421848561663584, 0.04030282790268034, 0.043860758659854254, 0.04489878686938463, 0.0457607625132273, 0.051613216582683405, 0.04685057825012286, 0.039782893911372144, 0.0416034061510837, 0.04978413984845904, 0.06681992615392633, 0.04852453381773872, 0.042450942844571446, 0.045809513045281094, 0.05105538833316079, 0.052781024592023586, 0.044141608378222195, 0.05817328313228881, 0.04072748896561036, 0.04422682148349758, 0.043930210172144074, 0.04526188882429295, 0.042302668931202304, 0.04316624317728075, 0.06035328968170272, 0.04243423637827852, 0.04238073910532582, 0.045247034733862636, 0.06294793330677213, 0.04290226029304104, 0.05072919812844076, 0.04460952361292469, 0.0453650056951224, 0.04363795747549339, 0.05289023600968533, 0.0423946668295946, 0.061044996351850594, 0.05121697475413964, 0.062309087411169146, 0.04390508295791547, 0.041728948649031525, 0.04182875209138459, 0.06419102265518958, 0.04373679692381783, 0.047552119376513, 0.043805383237774664, 0.040219836839461724, 0.040581250453936416, 0.043812817478909985, 0.04168312753181721, 0.061032179384050596, 0.04182093384536687, 0.04584221604400611, 0.04261003974310658, 0.05775532123884922, 0.04404271999533429, 0.04706827295331688, 0.04293383705509819, 0.04208396963928862, 0.07189412684593975, 0.043245590114054315, 0.04254883876614613, 0.0428727453843279, 0.05881362313255464, 0.05697398424736654, 0.0532204242106488, 0.06575700009065709, 0.04381752623303783, 0.04108377046102695, 0.041303849612705446, 0.0587384378426794, 0.04502196660975431, 0.044209104925344814, 0.054621022899475374, 0.042964824776503915, 0.051812176361804865, 0.041557561444120455, 0.042586058825917206, 0.043068378898926556, 0.04431068129240971, 0.042503391950227884, 0.0607587899777066, 0.05472818866556392, 0.04196667552235796]]
    lossvec0 = [[0.05869716357936193, 0.06496469072191993, 0.06445388890620267, 0.061190271263857884, 0.060801952120124174, 0.0628518155011463, 0.06103055368862017, 0.0645339303067024, 0.06345518080997543, 0.06798749988287238, 0.0635577827604388, 0.06448244774348906, 0.06460408960457555, 0.06423479803724086, 0.06346570148697925, 0.0610220274476332, 0.06653268660497995, 0.0637819632898739, 0.06458153281918987, 0.06219370776874488, 0.06158502380780164, 0.06450099815646547, 0.06261581321267679, 0.06241165203529875, 0.06127086472011553, 0.06284592849557297, 0.06433899359307356, 0.06298260297368505, 0.06333552441384119, 0.061629484523442635, 0.06555605978760054, 0.06382096899959443, 0.06501828365590352, 0.06262780410665626, 0.06140928933603194, 0.06260452785273529, 0.06452117625338971, 0.06131657543913682, 0.06331224204223371, 0.059988330185667786, 0.06040264892287001, 0.06288617348285885, 0.06166245680508134, 0.0628351006999992, 0.06251416854556381, 0.06278572087523576, 0.06433018328228853, 0.060095054181502905, 0.0626561852934667, 0.06395959213148232, 0.06599653261118309, 0.06301622084736008, 0.06534010734028481, 0.06182977435688999, 0.060662926582686065, 0.06509633058008522, 0.06571845189114096, 0.06336204765334655, 0.06121765310765021, 0.06212960321981213, 0.06139979355188204, 0.06715352252234444, 0.06494291982692406, 0.0630487850259678, 0.05997319784634728, 0.06093541747803282, 0.062345506188413474, 0.05898777693762918, 0.06426586972711376, 0.06636850613688819, 0.05779544547041826, 0.06434274816921044, 0.06208405024947255, 0.06377646674187719, 0.06871680581791573, 0.06252993209726768, 0.06316452053900942, 0.0640895085756315, 0.06197286743720706, 0.060706810755013996, 0.06439778673649788, 0.06553858203941768, 0.06679639345658742, 0.06140427401580309, 0.06518312241091204, 0.06411355265029997, 0.06358547090601545, 0.06435113477421903, 0.06085434251111577, 0.06343789286904834, 0.06418355308710491, 0.06435364560539769, 0.061155853975873246, 0.06391964006755392, 0.06019878534789032, 0.06399455155349086, 0.0591792232272502, 0.061147998138276795, 0.06630087518492675, 0.063835916003289]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### rateTarget=0.1, CHECK SCORE, m=0.1 ###
    # Get null first
    mScore, t = 0.1, 0.1
    scoredict = {'name': 'Check', 'slope': mScore}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_check, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Design 0']
    lossveclist = [[0.05141967341150602, 0.050488375800416346, 0.04981603776427598, 0.04764752786354282, 0.05055707866938051, 0.050775369507042215, 0.05047037260382936, 0.05051120458303731, 0.04799348062043705, 0.0497507936561569, 0.04879137858100735, 0.04883946868244083, 0.045910956748735604, 0.048472072618171214, 0.04978500634403664, 0.05101606054952856, 0.05051232661176904, 0.04946272518395998, 0.04949053152654033, 0.047121897142850366, 0.050613432794927714, 0.04872340953947927, 0.04730732974375995, 0.04707379888969331, 0.05026936711418364, 0.0496259790557982, 0.05005177020260493, 0.04558164115846085, 0.04750218707405135, 0.04872077186125756, 0.049864477557876014, 0.048975390346388446, 0.04737853776354648, 0.053897053334010146, 0.04892433440314092, 0.04806983586034234, 0.049401612612163616, 0.04919975785394658, 0.051452607063234485, 0.04861894943595187, 0.04915236197730954, 0.04799461122296129, 0.051187972900031325, 0.048739577379698605, 0.04828325531103462, 0.04685464619629295, 0.04954078801178165, 0.05053827036929954, 0.04776411506228511, 0.05457268338942284, 0.0483221637988486, 0.04861589005291251, 0.05029666993229396, 0.046769460510686436, 0.04997417808215994, 0.04846030442514717, 0.04862335586728392, 0.048397593261808605, 0.0506201938145519, 0.050901545388903714, 0.04605532245901115, 0.048267323233028576, 0.05063036850021813, 0.0500902181154842, 0.04789690100561125, 0.0491534394998639, 0.04814608557898573, 0.05132696414848426, 0.04998554057448066, 0.04866477345081097, 0.04817798082532481, 0.04741883870718274, 0.04954626143276108, 0.05109931822730183, 0.04803866217672809, 0.04880241998252823, 0.051658540280846224, 0.04642040264187238, 0.047685889716944506, 0.0477681546950277, 0.047728490875300095, 0.04844515537490979, 0.04800573966185571, 0.04689480508492717, 0.04956981044342672, 0.04789963195455775, 0.050579824924073154, 0.047878593234791884, 0.04899565710765956, 0.04889107828992235, 0.04850235492334388, 0.04975680873578155, 0.05020298613341479, 0.04784143984868255, 0.04659091953814041, 0.053399696082267245, 0.04897711074096094, 0.05063872728710386, 0.04881581854084665, 0.04870321948150379]]
    '''
    # 30 tests for all designs
    mScore, t = 0.1, 0.1
    scoredict = {'name': 'Check', 'slope': mScore}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_check, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.04190104555276653, 0.042638406456415055, 0.050114911640995116, 0.043337703748643236, 0.04037769057061473, 0.042800567887932614, 0.03867629504379225, 0.039753031958574984, 0.0399515600185753, 0.040095994557639236, 0.040494237346789, 0.038783815926068915, 0.03873784714311815, 0.03816712446780221, 0.038734611218196095, 0.04093163608892898, 0.04089929153975861, 0.038015901176388395, 0.03845252795523308, 0.04138693765919372, 0.04906306003362314, 0.046025751276810585, 0.03596660953131131, 0.03757078717831047, 0.04559469515975417, 0.04213623001184617, 0.04424264370493216, 0.04107218442336022, 0.04174029376501296, 0.03857252110350617, 0.03926616214313116, 0.039256228109224904, 0.046048521857951226, 0.04362606174181843, 0.04344322503534693, 0.03987527904114251, 0.039924546413550574, 0.04178539718312685, 0.040637985684906335, 0.04111027956472964, 0.04881285021807444, 0.04008820458308847, 0.03782153613779288, 0.04121280567542108, 0.04069526963647479, 0.03831317041972452, 0.041669797421274093, 0.03757361804643317, 0.041070682882185794, 0.04215880219566272, 0.04161214103270918, 0.04334558012126977, 0.04541393518041159, 0.040245762999436496, 0.04302336176067074, 0.04417515606146429, 0.04131368545456549, 0.04348651506705213, 0.040881744737416015, 0.03912792018778864, 0.042163810398601786, 0.043506328430270254, 0.049058585142390226, 0.04053587260891177, 0.042988745464871546, 0.041795656264804144, 0.03789652884236195, 0.04147412121955538, 0.046321883702117435, 0.04183568972554154, 0.039507098129056166, 0.050060479804640484, 0.0413890727208952, 0.042061070427489716, 0.04661410149196618, 0.053090722603873076, 0.0423616646801263, 0.03857278254477465, 0.03943898927702687, 0.04279935167302481, 0.042373830693433506, 0.041530282706686523, 0.04111168557937257, 0.04002649623551674, 0.04339225497556752, 0.039986738823449025, 0.044232347331346844, 0.04438968061322869, 0.04084063683585815, 0.045477553037929046, 0.041849596861205055, 0.04459621113922286, 0.04288296281366825, 0.04479944904319051, 0.04036120876257611, 0.03947147851987372, 0.04688190506163185, 0.046931123554572, 0.03759541998762883, 0.039882898048758934], [0.042425156133885325, 0.033863377296484316, 0.036043364893993644, 0.04165867697661706, 0.04393146330868022, 0.04173209524037377, 0.039782215029713776, 0.04728765381759341, 0.03502753202102314, 0.04039612953979622, 0.03408026294091918, 0.037110489461742856, 0.04698115098171874, 0.03317644761918645, 0.035996171419567125, 0.04599601081195377, 0.04373297951856798, 0.03282818470448618, 0.038528554969307086, 0.03687386842668735, 0.036001740500376286, 0.041233631200249934, 0.03834758973668743, 0.03468827950851292, 0.042555524555203554, 0.04624065289686511, 0.04198879922553205, 0.03519043028445858, 0.04142771399956689, 0.03489633044371446, 0.04429830971975487, 0.03188799558104105, 0.03361065405909838, 0.03680771547890033, 0.031623058453419624, 0.035048617788916256, 0.03740783205753665, 0.032746769119646676, 0.041710713982718375, 0.03599179659922748, 0.0411531630694273, 0.0375299750458188, 0.03644648909008507, 0.03963060350297909, 0.04825547965152491, 0.03553495064826336, 0.03383620375580719, 0.038491481551395944, 0.039369765752842144, 0.03508829001695311, 0.0345718865593651, 0.03701973633365099, 0.044286334844030426, 0.0442133788993993, 0.0443488646857971, 0.04216332080128134, 0.03540328016577308, 0.03682491306905045, 0.03783009995586358, 0.03647518651522753, 0.036897123230777026, 0.034174253303209216, 0.034374363793513794, 0.03518964209232047, 0.03487589454844085, 0.04078615037974799, 0.046745441174616924, 0.035478085814305074, 0.03425523363529121, 0.03641677095558293, 0.04687492944830132, 0.03560183774291138, 0.032199812848451574, 0.03530349161569807, 0.04168125597583328, 0.04395904702888886, 0.03636270016145833, 0.03808372327340154, 0.04179229956712697, 0.03482152271866748, 0.03746987605999862, 0.035522033113732907, 0.045905358616497936, 0.04523083551126632, 0.03396351004960368, 0.03550357152621858, 0.04460685047168262, 0.036347979401597855, 0.03888530441728337, 0.04755576731061955, 0.039795719637039234, 0.05155070620471664, 0.0352221984365748, 0.03443598794885387, 0.036040368336239276, 0.03978143178255326, 0.033966626774979226, 0.04482798712224122, 0.03652269385058549, 0.036107653400317706], [0.04164415496155746, 0.041457821768404936, 0.045634688075453164, 0.04330696642837157, 0.03778113630396278, 0.038180739936140504, 0.04607844134391053, 0.04390629912949341, 0.03953639132740114, 0.04110132461320815, 0.04098009076882133, 0.0402068939967276, 0.04028968498329687, 0.04144029659978274, 0.04057933809815282, 0.042830510197017356, 0.050757913544203094, 0.039995271857201656, 0.0393840652605432, 0.042993804088896664, 0.04618686277288413, 0.04192223057424026, 0.041966596170625044, 0.035897467882646854, 0.044830367145415786, 0.04217896900888916, 0.040402185194523356, 0.046126602954967684, 0.03972941939171822, 0.03999784583030041, 0.04069524228092932, 0.041119467686793726, 0.04520412372948027, 0.039021253155059575, 0.04161942992274582, 0.0383419747916236, 0.04150677417273541, 0.042223337958111694, 0.03961517260835058, 0.04316803186133485, 0.04693310102859578, 0.04326900928078274, 0.039695226388900884, 0.04485034573566034, 0.047398574404836046, 0.04051822739579463, 0.04197311590599289, 0.03996152489204583, 0.04233022645206548, 0.039577722976188855, 0.043966928485594796, 0.042063846751492176, 0.04708538057132759, 0.03950542385702507, 0.04573805548740482, 0.04613120056620187, 0.03791740865974129, 0.04124519570819873, 0.03801478054582377, 0.041530247176115496, 0.04097610342837598, 0.04061551657177308, 0.03815891430068598, 0.040299299947354865, 0.04015923378647696, 0.04400079980436187, 0.03894806268398221, 0.0382912750099167, 0.04184046509598251, 0.04084687080225559, 0.0463259814981084, 0.042444248663938686, 0.04257791793064433, 0.039491131035091685, 0.038123052033191496, 0.053751220473689014, 0.04420579563356115, 0.04242647004833428, 0.040410288718529926, 0.04086021875324341, 0.04036588375896679, 0.039640098249579515, 0.03873473530195311, 0.03967006172662319, 0.03997055082372265, 0.041701095965171804, 0.04296992971099752, 0.04175356385362448, 0.041960028026629397, 0.03944201676228052, 0.040801286356756485, 0.05259677907536268, 0.04330456179207548, 0.038083721132053175, 0.04290223841900877, 0.042002366921821674, 0.043361118047490516, 0.04868238489703051, 0.03714582508122746, 0.043436470884047965], [0.04245068456563985, 0.04463458207213338, 0.043024913422648456, 0.04752801987072207, 0.04387460062521562, 0.04473364773713034, 0.04237200108382268, 0.04981576283379314, 0.04088222588123987, 0.04931825201311945, 0.04247911625299222, 0.04551864622675427, 0.04330133822332822, 0.04624100518894291, 0.04691221408536941, 0.03971536364467199, 0.05075692355496023, 0.04588267946890234, 0.047720293232797875, 0.046068808028405725, 0.05095384474738728, 0.047146493340690876, 0.049902530222970594, 0.0461075967754621, 0.04324056125063989, 0.047226510974585585, 0.04712159606563903, 0.044237124289980695, 0.041681675252779674, 0.04593832759342872, 0.04739491571392467, 0.048025673869436854, 0.04448078653089567, 0.04644797958258055, 0.053949360944628634, 0.04696272373655468, 0.05112460524657989, 0.04498033262363156, 0.04827486919653827, 0.04745579264067997, 0.04368085027189842, 0.04806864382088575, 0.054407678765385194, 0.04307189309432506, 0.045756435351949176, 0.04446035942159731, 0.045668542248604255, 0.05671491916018405, 0.04766320142283048, 0.04435291467294752, 0.04399336355850021, 0.05133281477800743, 0.046050925454571894, 0.047865578179910405, 0.04606498323227303, 0.044549910989670316, 0.04597157737417439, 0.04355306312285869, 0.04897046294462772, 0.04527083704363383, 0.05288192019115905, 0.04766260748861184, 0.04819401398818066, 0.04477427418284245, 0.04578573378457153, 0.04294261876744727, 0.04263159038644739, 0.04581102619236585, 0.04459259481709561, 0.04930697653186578, 0.043411115140453205, 0.046321572146284545, 0.05018501760362005, 0.044068895116761854, 0.04795873947185419, 0.05463960165293386, 0.04288360952671259, 0.04763434670197763, 0.04697875048442935, 0.04495972184366811, 0.04438877098604583, 0.04642048822354356, 0.048216829234158605, 0.04415568469069297, 0.05117711522905716, 0.04769617562070032, 0.04336563711507005, 0.051006283052528856, 0.0520271494927239, 0.04446243734643147, 0.04981359954479499, 0.04353133983220956, 0.0505726870027484, 0.04540077322995491, 0.044117813713057036, 0.043263802272700394, 0.04482850107023578, 0.04496066600567296, 0.05281507228994638, 0.043275001349032796], [0.03462739760862808, 0.044886102594633756, 0.03350905295055346, 0.03713450474424246, 0.0455842673168563, 0.04167956642889076, 0.033237991698551884, 0.03269391749476358, 0.033261924151090604, 0.04027292910698906, 0.033175365548654225, 0.033242050695844634, 0.04090054804870786, 0.0367079329987606, 0.038176094147125264, 0.037526696748410804, 0.03927281069300986, 0.03442066752175069, 0.03976544917489012, 0.03372350990468549, 0.035884527826260476, 0.04150474622934896, 0.03711401929342482, 0.04106167514665851, 0.047058774046109704, 0.045484909286715766, 0.040840856112280055, 0.032992087877595146, 0.03635208684818733, 0.03851547981755558, 0.03723727335660887, 0.041250690782203094, 0.03372699290850908, 0.03948008018424946, 0.030584322320092516, 0.03651920899375563, 0.04462935570010397, 0.03716005606105881, 0.037297446621710514, 0.04032709998366924, 0.04980780205331333, 0.03486908354352975, 0.06322414784038889, 0.04342328092332761, 0.04473764186354332, 0.035662236510421615, 0.03236510831082821, 0.04497895015900662, 0.03692660973908365, 0.03460297914934424, 0.034007351776460304, 0.037430014746711204, 0.03974696721436706, 0.035751961173792875, 0.040735643751810414, 0.03404199637528354, 0.03669465232286101, 0.035925778174635145, 0.044400450922128784, 0.032292480329224854, 0.041476381580789146, 0.034231753604650667, 0.039158386793486585, 0.03695085760924472, 0.03367258235218534, 0.03568816566132855, 0.036112448692395105, 0.038545757863918076, 0.03555105679030451, 0.032653579947112835, 0.04082349049946729, 0.033630738041799675, 0.03604528886422054, 0.03739920791283366, 0.03453784456493854, 0.056444400313872475, 0.03269161796648844, 0.0403340337288822, 0.03352218090747728, 0.03911556521509884, 0.0391643682276823, 0.0351720803139224, 0.045312111193155966, 0.049665290489892155, 0.03386001833241178, 0.03830668875852967, 0.03482476777206025, 0.03354559269514429, 0.035349067387333434, 0.04395692083514154, 0.03856594424510277, 0.03998607179947111, 0.045255300327825036, 0.041877483406094644, 0.04532058972645467, 0.045029487668923576, 0.04339734054317102, 0.042051832562676215, 0.04879510519289141, 0.047223585193462196], [0.039501782837203805, 0.04441633345159088, 0.03459293590607108, 0.0433200157113193, 0.04597479760217045, 0.04815884060654332, 0.03289872298240642, 0.03808613681064582, 0.033219255698095786, 0.04257011861478809, 0.03663868723280091, 0.039074693381457457, 0.04724543600358661, 0.036289526280813875, 0.04414637874351868, 0.034223881894454404, 0.03935589538255432, 0.030864504152234497, 0.03866486566089559, 0.03443475467471388, 0.03742272376584788, 0.03447977158606758, 0.04039172441406948, 0.0342323270907812, 0.04162641562441664, 0.0422281214244858, 0.03556566848587841, 0.036609462170274276, 0.04612066835271534, 0.038928728815867876, 0.035015716231559704, 0.034718978118637694, 0.03705135473273945, 0.03512066609903974, 0.037959615438035214, 0.03586319288310158, 0.03396794723461969, 0.03465388876640225, 0.038940986534820886, 0.034228167632629945, 0.04573764473257103, 0.03427658065334294, 0.034569261219822324, 0.036366013600000024, 0.045174415578660705, 0.032493485619043895, 0.039812424039902476, 0.03555720230320878, 0.04262508753637171, 0.034528217486682805, 0.0327567388895314, 0.035803994636206635, 0.044731485884276966, 0.03527979952403814, 0.04300824381331047, 0.034849745611559506, 0.03593431855799131, 0.03777549560916171, 0.041144268067300156, 0.04207780999026448, 0.03997991143203633, 0.03464484394983014, 0.03538204882515407, 0.03898681192540062, 0.040284968624574, 0.03368379275952636, 0.04423681728550799, 0.04081578057349034, 0.037983666956394053, 0.034710083931878626, 0.03774123358110783, 0.03437178841928199, 0.03578159978621291, 0.03447986924860966, 0.04068279174413486, 0.042275168427986475, 0.034310505059182074, 0.03411961080859363, 0.03502998976312125, 0.04086993841570853, 0.03643360112132487, 0.03712853249108974, 0.04157022114146362, 0.03817940080562053, 0.040598015630147075, 0.030455387580937934, 0.03395241279671245, 0.03468357255141507, 0.03450902632898317, 0.04062456967869956, 0.045190249508251484, 0.037117265679111534, 0.046963000393518244, 0.034449469867445195, 0.04180461055825995, 0.034174694054870614, 0.03530304974166931, 0.03999126392019518, 0.04565861335820034, 0.036827699692506294]]
    lossvec0 = [[0.05141967341150602, 0.050488375800416346, 0.04981603776427598, 0.04764752786354282, 0.05055707866938051, 0.050775369507042215, 0.05047037260382936, 0.05051120458303731, 0.04799348062043705, 0.0497507936561569, 0.04879137858100735, 0.04883946868244083, 0.045910956748735604, 0.048472072618171214, 0.04978500634403664, 0.05101606054952856, 0.05051232661176904, 0.04946272518395998, 0.04949053152654033, 0.047121897142850366, 0.050613432794927714, 0.04872340953947927, 0.04730732974375995, 0.04707379888969331, 0.05026936711418364, 0.0496259790557982, 0.05005177020260493, 0.04558164115846085, 0.04750218707405135, 0.04872077186125756, 0.049864477557876014, 0.048975390346388446, 0.04737853776354648, 0.053897053334010146, 0.04892433440314092, 0.04806983586034234, 0.049401612612163616, 0.04919975785394658, 0.051452607063234485, 0.04861894943595187, 0.04915236197730954, 0.04799461122296129, 0.051187972900031325, 0.048739577379698605, 0.04828325531103462, 0.04685464619629295, 0.04954078801178165, 0.05053827036929954, 0.04776411506228511, 0.05457268338942284, 0.0483221637988486, 0.04861589005291251, 0.05029666993229396, 0.046769460510686436, 0.04997417808215994, 0.04846030442514717, 0.04862335586728392, 0.048397593261808605, 0.0506201938145519, 0.050901545388903714, 0.04605532245901115, 0.048267323233028576, 0.05063036850021813, 0.0500902181154842, 0.04789690100561125, 0.0491534394998639, 0.04814608557898573, 0.05132696414848426, 0.04998554057448066, 0.04866477345081097, 0.04817798082532481, 0.04741883870718274, 0.04954626143276108, 0.05109931822730183, 0.04803866217672809, 0.04880241998252823, 0.051658540280846224, 0.04642040264187238, 0.047685889716944506, 0.0477681546950277, 0.047728490875300095, 0.04844515537490979, 0.04800573966185571, 0.04689480508492717, 0.04956981044342672, 0.04789963195455775, 0.050579824924073154, 0.047878593234791884, 0.04899565710765956, 0.04889107828992235, 0.04850235492334388, 0.04975680873578155, 0.05020298613341479, 0.04784143984868255, 0.04659091953814041, 0.053399696082267245, 0.04897711074096094, 0.05063872728710386, 0.04881581854084665, 0.04870321948150379]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.4$, $n=30$')

    lossveclist = [[0.04190104555276653, 0.042638406456415055, 0.050114911640995116, 0.043337703748643236, 0.04037769057061473, 0.042800567887932614, 0.03867629504379225, 0.039753031958574984, 0.0399515600185753, 0.040095994557639236, 0.040494237346789, 0.038783815926068915, 0.03873784714311815, 0.03816712446780221, 0.038734611218196095, 0.04093163608892898, 0.04089929153975861, 0.038015901176388395, 0.03845252795523308, 0.04138693765919372, 0.04906306003362314, 0.046025751276810585, 0.03596660953131131, 0.03757078717831047, 0.04559469515975417, 0.04213623001184617, 0.04424264370493216, 0.04107218442336022, 0.04174029376501296, 0.03857252110350617, 0.03926616214313116, 0.039256228109224904, 0.046048521857951226, 0.04362606174181843, 0.04344322503534693, 0.03987527904114251, 0.039924546413550574, 0.04178539718312685, 0.040637985684906335, 0.04111027956472964, 0.04881285021807444, 0.04008820458308847, 0.03782153613779288, 0.04121280567542108, 0.04069526963647479, 0.03831317041972452, 0.041669797421274093, 0.03757361804643317, 0.041070682882185794, 0.04215880219566272, 0.04161214103270918, 0.04334558012126977, 0.04541393518041159, 0.040245762999436496, 0.04302336176067074, 0.04417515606146429, 0.04131368545456549, 0.04348651506705213, 0.040881744737416015, 0.03912792018778864, 0.042163810398601786, 0.043506328430270254, 0.049058585142390226, 0.04053587260891177, 0.042988745464871546, 0.041795656264804144, 0.03789652884236195, 0.04147412121955538, 0.046321883702117435, 0.04183568972554154, 0.039507098129056166, 0.050060479804640484, 0.0413890727208952, 0.042061070427489716, 0.04661410149196618, 0.053090722603873076, 0.0423616646801263, 0.03857278254477465, 0.03943898927702687, 0.04279935167302481, 0.042373830693433506, 0.041530282706686523, 0.04111168557937257, 0.04002649623551674, 0.04339225497556752, 0.039986738823449025, 0.044232347331346844, 0.04438968061322869, 0.04084063683585815, 0.045477553037929046, 0.041849596861205055, 0.04459621113922286, 0.04288296281366825, 0.04479944904319051, 0.04036120876257611, 0.03947147851987372, 0.04688190506163185, 0.046931123554572, 0.03759541998762883, 0.039882898048758934], [0.042425156133885325, 0.033863377296484316, 0.036043364893993644, 0.04165867697661706, 0.04393146330868022, 0.04173209524037377, 0.039782215029713776, 0.04728765381759341, 0.03502753202102314, 0.04039612953979622, 0.03408026294091918, 0.037110489461742856, 0.04698115098171874, 0.03317644761918645, 0.035996171419567125, 0.04599601081195377, 0.04373297951856798, 0.03282818470448618, 0.038528554969307086, 0.03687386842668735, 0.036001740500376286, 0.041233631200249934, 0.03834758973668743, 0.03468827950851292, 0.042555524555203554, 0.04624065289686511, 0.04198879922553205, 0.03519043028445858, 0.04142771399956689, 0.03489633044371446, 0.04429830971975487, 0.03188799558104105, 0.03361065405909838, 0.03680771547890033, 0.031623058453419624, 0.035048617788916256, 0.03740783205753665, 0.032746769119646676, 0.041710713982718375, 0.03599179659922748, 0.0411531630694273, 0.0375299750458188, 0.03644648909008507, 0.03963060350297909, 0.04825547965152491, 0.03553495064826336, 0.03383620375580719, 0.038491481551395944, 0.039369765752842144, 0.03508829001695311, 0.0345718865593651, 0.03701973633365099, 0.044286334844030426, 0.0442133788993993, 0.0443488646857971, 0.04216332080128134, 0.03540328016577308, 0.03682491306905045, 0.03783009995586358, 0.03647518651522753, 0.036897123230777026, 0.034174253303209216, 0.034374363793513794, 0.03518964209232047, 0.03487589454844085, 0.04078615037974799, 0.046745441174616924, 0.035478085814305074, 0.03425523363529121, 0.03641677095558293, 0.04687492944830132, 0.03560183774291138, 0.032199812848451574, 0.03530349161569807, 0.04168125597583328, 0.04395904702888886, 0.03636270016145833, 0.03808372327340154, 0.04179229956712697, 0.03482152271866748, 0.03746987605999862, 0.035522033113732907, 0.045905358616497936, 0.04523083551126632, 0.03396351004960368, 0.03550357152621858, 0.04460685047168262, 0.036347979401597855, 0.03888530441728337, 0.04755576731061955, 0.039795719637039234, 0.05155070620471664, 0.0352221984365748, 0.03443598794885387, 0.036040368336239276, 0.03978143178255326, 0.033966626774979226, 0.04482798712224122, 0.03652269385058549, 0.036107653400317706], [0.04164415496155746, 0.041457821768404936, 0.045634688075453164, 0.04330696642837157, 0.03778113630396278, 0.038180739936140504, 0.04607844134391053, 0.04390629912949341, 0.03953639132740114, 0.04110132461320815, 0.04098009076882133, 0.0402068939967276, 0.04028968498329687, 0.04144029659978274, 0.04057933809815282, 0.042830510197017356, 0.050757913544203094, 0.039995271857201656, 0.0393840652605432, 0.042993804088896664, 0.04618686277288413, 0.04192223057424026, 0.041966596170625044, 0.035897467882646854, 0.044830367145415786, 0.04217896900888916, 0.040402185194523356, 0.046126602954967684, 0.03972941939171822, 0.03999784583030041, 0.04069524228092932, 0.041119467686793726, 0.04520412372948027, 0.039021253155059575, 0.04161942992274582, 0.0383419747916236, 0.04150677417273541, 0.042223337958111694, 0.03961517260835058, 0.04316803186133485, 0.04693310102859578, 0.04326900928078274, 0.039695226388900884, 0.04485034573566034, 0.047398574404836046, 0.04051822739579463, 0.04197311590599289, 0.03996152489204583, 0.04233022645206548, 0.039577722976188855, 0.043966928485594796, 0.042063846751492176, 0.04708538057132759, 0.03950542385702507, 0.04573805548740482, 0.04613120056620187, 0.03791740865974129, 0.04124519570819873, 0.03801478054582377, 0.041530247176115496, 0.04097610342837598, 0.04061551657177308, 0.03815891430068598, 0.040299299947354865, 0.04015923378647696, 0.04400079980436187, 0.03894806268398221, 0.0382912750099167, 0.04184046509598251, 0.04084687080225559, 0.0463259814981084, 0.042444248663938686, 0.04257791793064433, 0.039491131035091685, 0.038123052033191496, 0.053751220473689014, 0.04420579563356115, 0.04242647004833428, 0.040410288718529926, 0.04086021875324341, 0.04036588375896679, 0.039640098249579515, 0.03873473530195311, 0.03967006172662319, 0.03997055082372265, 0.041701095965171804, 0.04296992971099752, 0.04175356385362448, 0.041960028026629397, 0.03944201676228052, 0.040801286356756485, 0.05259677907536268, 0.04330456179207548, 0.038083721132053175, 0.04290223841900877, 0.042002366921821674, 0.043361118047490516, 0.04868238489703051, 0.03714582508122746, 0.043436470884047965], [0.04245068456563985, 0.04463458207213338, 0.043024913422648456, 0.04752801987072207, 0.04387460062521562, 0.04473364773713034, 0.04237200108382268, 0.04981576283379314, 0.04088222588123987, 0.04931825201311945, 0.04247911625299222, 0.04551864622675427, 0.04330133822332822, 0.04624100518894291, 0.04691221408536941, 0.03971536364467199, 0.05075692355496023, 0.04588267946890234, 0.047720293232797875, 0.046068808028405725, 0.05095384474738728, 0.047146493340690876, 0.049902530222970594, 0.0461075967754621, 0.04324056125063989, 0.047226510974585585, 0.04712159606563903, 0.044237124289980695, 0.041681675252779674, 0.04593832759342872, 0.04739491571392467, 0.048025673869436854, 0.04448078653089567, 0.04644797958258055, 0.053949360944628634, 0.04696272373655468, 0.05112460524657989, 0.04498033262363156, 0.04827486919653827, 0.04745579264067997, 0.04368085027189842, 0.04806864382088575, 0.054407678765385194, 0.04307189309432506, 0.045756435351949176, 0.04446035942159731, 0.045668542248604255, 0.05671491916018405, 0.04766320142283048, 0.04435291467294752, 0.04399336355850021, 0.05133281477800743, 0.046050925454571894, 0.047865578179910405, 0.04606498323227303, 0.044549910989670316, 0.04597157737417439, 0.04355306312285869, 0.04897046294462772, 0.04527083704363383, 0.05288192019115905, 0.04766260748861184, 0.04819401398818066, 0.04477427418284245, 0.04578573378457153, 0.04294261876744727, 0.04263159038644739, 0.04581102619236585, 0.04459259481709561, 0.04930697653186578, 0.043411115140453205, 0.046321572146284545, 0.05018501760362005, 0.044068895116761854, 0.04795873947185419, 0.05463960165293386, 0.04288360952671259, 0.04763434670197763, 0.04697875048442935, 0.04495972184366811, 0.04438877098604583, 0.04642048822354356, 0.048216829234158605, 0.04415568469069297, 0.05117711522905716, 0.04769617562070032, 0.04336563711507005, 0.051006283052528856, 0.0520271494927239, 0.04446243734643147, 0.04981359954479499, 0.04353133983220956, 0.0505726870027484, 0.04540077322995491, 0.044117813713057036, 0.043263802272700394, 0.04482850107023578, 0.04496066600567296, 0.05281507228994638, 0.043275001349032796], [0.03462739760862808, 0.044886102594633756, 0.03350905295055346, 0.03713450474424246, 0.0455842673168563, 0.04167956642889076, 0.033237991698551884, 0.03269391749476358, 0.033261924151090604, 0.04027292910698906, 0.033175365548654225, 0.033242050695844634, 0.04090054804870786, 0.0367079329987606, 0.038176094147125264, 0.037526696748410804, 0.03927281069300986, 0.03442066752175069, 0.03976544917489012, 0.03372350990468549, 0.035884527826260476, 0.04150474622934896, 0.03711401929342482, 0.04106167514665851, 0.047058774046109704, 0.045484909286715766, 0.040840856112280055, 0.032992087877595146, 0.03635208684818733, 0.03851547981755558, 0.03723727335660887, 0.041250690782203094, 0.03372699290850908, 0.03948008018424946, 0.030584322320092516, 0.03651920899375563, 0.04462935570010397, 0.03716005606105881, 0.037297446621710514, 0.04032709998366924, 0.04980780205331333, 0.03486908354352975, 0.06322414784038889, 0.04342328092332761, 0.04473764186354332, 0.035662236510421615, 0.03236510831082821, 0.04497895015900662, 0.03692660973908365, 0.03460297914934424, 0.034007351776460304, 0.037430014746711204, 0.03974696721436706, 0.035751961173792875, 0.040735643751810414, 0.03404199637528354, 0.03669465232286101, 0.035925778174635145, 0.044400450922128784, 0.032292480329224854, 0.041476381580789146, 0.034231753604650667, 0.039158386793486585, 0.03695085760924472, 0.03367258235218534, 0.03568816566132855, 0.036112448692395105, 0.038545757863918076, 0.03555105679030451, 0.032653579947112835, 0.04082349049946729, 0.033630738041799675, 0.03604528886422054, 0.03739920791283366, 0.03453784456493854, 0.056444400313872475, 0.03269161796648844, 0.0403340337288822, 0.03352218090747728, 0.03911556521509884, 0.0391643682276823, 0.0351720803139224, 0.045312111193155966, 0.049665290489892155, 0.03386001833241178, 0.03830668875852967, 0.03482476777206025, 0.03354559269514429, 0.035349067387333434, 0.04395692083514154, 0.03856594424510277, 0.03998607179947111, 0.045255300327825036, 0.041877483406094644, 0.04532058972645467, 0.045029487668923576, 0.04339734054317102, 0.042051832562676215, 0.04879510519289141, 0.047223585193462196], [0.039501782837203805, 0.04441633345159088, 0.03459293590607108, 0.0433200157113193, 0.04597479760217045, 0.04815884060654332, 0.03289872298240642, 0.03808613681064582, 0.033219255698095786, 0.04257011861478809, 0.03663868723280091, 0.039074693381457457, 0.04724543600358661, 0.036289526280813875, 0.04414637874351868, 0.034223881894454404, 0.03935589538255432, 0.030864504152234497, 0.03866486566089559, 0.03443475467471388, 0.03742272376584788, 0.03447977158606758, 0.04039172441406948, 0.0342323270907812, 0.04162641562441664, 0.0422281214244858, 0.03556566848587841, 0.036609462170274276, 0.04612066835271534, 0.038928728815867876, 0.035015716231559704, 0.034718978118637694, 0.03705135473273945, 0.03512066609903974, 0.037959615438035214, 0.03586319288310158, 0.03396794723461969, 0.03465388876640225, 0.038940986534820886, 0.034228167632629945, 0.04573764473257103, 0.03427658065334294, 0.034569261219822324, 0.036366013600000024, 0.045174415578660705, 0.032493485619043895, 0.039812424039902476, 0.03555720230320878, 0.04262508753637171, 0.034528217486682805, 0.0327567388895314, 0.035803994636206635, 0.044731485884276966, 0.03527979952403814, 0.04300824381331047, 0.034849745611559506, 0.03593431855799131, 0.03777549560916171, 0.041144268067300156, 0.04207780999026448, 0.03997991143203633, 0.03464484394983014, 0.03538204882515407, 0.03898681192540062, 0.040284968624574, 0.03368379275952636, 0.04423681728550799, 0.04081578057349034, 0.037983666956394053, 0.034710083931878626, 0.03774123358110783, 0.03437178841928199, 0.03578159978621291, 0.03447986924860966, 0.04068279174413486, 0.042275168427986475, 0.034310505059182074, 0.03411961080859363, 0.03502998976312125, 0.04086993841570853, 0.03643360112132487, 0.03712853249108974, 0.04157022114146362, 0.03817940080562053, 0.040598015630147075, 0.030455387580937934, 0.03395241279671245, 0.03468357255141507, 0.03450902632898317, 0.04062456967869956, 0.045190249508251484, 0.037117265679111534, 0.046963000393518244, 0.034449469867445195, 0.04180461055825995, 0.034174694054870614, 0.03530304974166931, 0.03999126392019518, 0.04565861335820034, 0.036827699692506294]]
    lossvec0 = [[0.05141967341150602, 0.050488375800416346, 0.04981603776427598, 0.04764752786354282, 0.05055707866938051, 0.050775369507042215, 0.05047037260382936, 0.05051120458303731, 0.04799348062043705, 0.0497507936561569, 0.04879137858100735, 0.04883946868244083, 0.045910956748735604, 0.048472072618171214, 0.04978500634403664, 0.05101606054952856, 0.05051232661176904, 0.04946272518395998, 0.04949053152654033, 0.047121897142850366, 0.050613432794927714, 0.04872340953947927, 0.04730732974375995, 0.04707379888969331, 0.05026936711418364, 0.0496259790557982, 0.05005177020260493, 0.04558164115846085, 0.04750218707405135, 0.04872077186125756, 0.049864477557876014, 0.048975390346388446, 0.04737853776354648, 0.053897053334010146, 0.04892433440314092, 0.04806983586034234, 0.049401612612163616, 0.04919975785394658, 0.051452607063234485, 0.04861894943595187, 0.04915236197730954, 0.04799461122296129, 0.051187972900031325, 0.048739577379698605, 0.04828325531103462, 0.04685464619629295, 0.04954078801178165, 0.05053827036929954, 0.04776411506228511, 0.05457268338942284, 0.0483221637988486, 0.04861589005291251, 0.05029666993229396, 0.046769460510686436, 0.04997417808215994, 0.04846030442514717, 0.04862335586728392, 0.048397593261808605, 0.0506201938145519, 0.050901545388903714, 0.04605532245901115, 0.048267323233028576, 0.05063036850021813, 0.0500902181154842, 0.04789690100561125, 0.0491534394998639, 0.04814608557898573, 0.05132696414848426, 0.04998554057448066, 0.04866477345081097, 0.04817798082532481, 0.04741883870718274, 0.04954626143276108, 0.05109931822730183, 0.04803866217672809, 0.04880241998252823, 0.051658540280846224, 0.04642040264187238, 0.047685889716944506, 0.0477681546950277, 0.047728490875300095, 0.04844515537490979, 0.04800573966185571, 0.04689480508492717, 0.04956981044342672, 0.04789963195455775, 0.050579824924073154, 0.047878593234791884, 0.04899565710765956, 0.04889107828992235, 0.04850235492334388, 0.04975680873578155, 0.05020298613341479, 0.04784143984868255, 0.04659091953814041, 0.053399696082267245, 0.04897711074096094, 0.05063872728710386, 0.04881581854084665, 0.04870321948150379]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### rateTarget=0.1, CHECK SCORE, m=0.9 ###
    # Get null first
    mScore, t = 0.9, 0.1
    scoredict = {'name': 'Check', 'slope': mScore}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_check, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Design 0']
    lossveclist = [[0.02560107724424959, 0.0269081801621786, 0.02669660522249634, 0.024729879634511596, 0.025648857312298146, 0.02621274724511835, 0.02664297823115476, 0.027534154570625254, 0.026244620566208486, 0.027881593052699803, 0.02514771882528392, 0.025895062905339265, 0.02455871777661818, 0.027156616863238704, 0.02735149824834501, 0.025705315325367052, 0.025806568293725865, 0.027597040229040144, 0.02538788033694342, 0.027420697680479774, 0.025476306009058022, 0.024608029993090273, 0.026194758004510457, 0.027466699239850206, 0.024961439325118986, 0.026921795586244086, 0.024937067089825887, 0.025422998284085577, 0.030289895527172327, 0.02808349107457011, 0.024561936943751948, 0.026968849333778293, 0.026602448626910736, 0.02829059977337076, 0.026260425878946406, 0.02850330749550472, 0.02451231559113149, 0.027845590886068625, 0.026930801182693493, 0.026330377252314557, 0.026995226987541025, 0.027451621006970028, 0.026367181127762842, 0.02452135147336047, 0.02704915553978583, 0.025228282218213424, 0.026167150545201624, 0.025108869432533893, 0.02606536486296084, 0.025287997631841128, 0.02475351964514969, 0.02647467518363552, 0.025666737801675867, 0.026643570458971793, 0.026059390440933035, 0.025298807652974674, 0.026506798949966857, 0.026024380081188316, 0.02557315791399944, 0.030009943253208392, 0.025153893658539202, 0.0253468193160923, 0.02592543622144289, 0.02641334902509686, 0.025176813756536635, 0.02755753121466075, 0.025124624251483426, 0.025992996261683138, 0.025673998569412985, 0.02581325227760266, 0.025023094332624146, 0.025532723971422838, 0.025590704181495262, 0.026040218656333953, 0.02847555279382509, 0.025378476158844056, 0.02507065180013407, 0.026501962039809663, 0.026412834010457513, 0.02826787001557972, 0.026475103538068246, 0.0245268772293418, 0.02555268533464695, 0.025034599537149413, 0.02796105479569308, 0.026286657790315953, 0.025897425065924642, 0.02705748334863733, 0.028445717798772408, 0.025602823621338675, 0.026492259689535724, 0.027023593306534886, 0.02793286214600318, 0.024594574378462016, 0.026178200371476123, 0.02710415839232178, 0.024512329588119566, 0.025541495439706432, 0.02554922103435433, 0.02540587481027131]]
    '''
    # 30 tests for all designs
    mScore, t = 0.9, 0.1
    scoredict = {'name': 'Check', 'slope': mScore}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_check, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.01812748071917698, 0.018876793914675186, 0.021257685602342084, 0.020459690876102294, 0.018852863867380384, 0.021259359113153086, 0.01897370603149916, 0.02006270285282531, 0.018984942754615344, 0.019161513263085104, 0.02057156961763707, 0.018367258638853627, 0.018965612207244156, 0.019012950586770886, 0.020236255663152944, 0.02159043028497999, 0.021729427177781452, 0.01845943894415715, 0.01796129667118211, 0.01847315012178006, 0.021987185782655558, 0.020128111378433042, 0.018726856897999064, 0.018119249103619332, 0.022808962069408443, 0.019720317415041343, 0.021404376261158334, 0.019782072468996707, 0.020560800418601352, 0.01916063110601593, 0.018792463672390475, 0.020002018930828327, 0.02033638116879233, 0.021432204328884104, 0.017783106942237874, 0.020763153199559334, 0.020866873255472977, 0.0197215178453607, 0.01984572869918766, 0.020422047090861928, 0.024283381380691867, 0.018432873144890276, 0.01821082022601273, 0.02014532316667027, 0.021521042378879033, 0.017390926800459852, 0.01964324038731639, 0.02000631406762651, 0.01900317289587959, 0.01921419218838949, 0.01814081912107971, 0.02052897627536531, 0.019653053792729348, 0.02079293942016379, 0.02012966526500114, 0.019644848565945547, 0.020332028225516104, 0.019409847856650758, 0.019276625729073214, 0.019716122091463287, 0.01889199574064096, 0.018711913763210127, 0.020131886377432802, 0.02052708335660409, 0.021994694427295243, 0.019495164563900984, 0.020613405884402865, 0.019279738338214607, 0.021381807609897763, 0.02031751065833226, 0.019083111154517468, 0.023102957135886965, 0.020845977270873138, 0.01858748022215092, 0.020758222189359576, 0.030733846177539687, 0.01952799339385963, 0.018993371578526253, 0.020919321613045265, 0.01965813249390387, 0.01996494467987496, 0.018832761137595258, 0.01892490309210201, 0.0197858633957759, 0.01949634914027642, 0.018074573901163054, 0.02026931392004915, 0.021742353765380428, 0.019031504034362417, 0.018889026583824284, 0.01970667206503646, 0.019878724491403443, 0.02819718678277317, 0.02606573117020109, 0.0202002960711448, 0.019382493316935135, 0.021178107735956412, 0.020826748653220643, 0.018710690602367557, 0.019217081385916095], [0.017242924142570053, 0.02946449288891925, 0.019194328076912105, 0.02717808342521106, 0.028335241607322727, 0.017741293452439404, 0.016177921458220692, 0.018292712799660542, 0.021276411841702245, 0.0329251761382907, 0.01921155032303231, 0.021088464717309192, 0.025027992902102534, 0.019963261915952348, 0.03146587004209414, 0.019082452506732142, 0.0240806160456614, 0.01818986040052774, 0.016453981495428757, 0.018635305791928323, 0.017670108242837906, 0.018884031912231754, 0.01659989681996534, 0.02174674633015945, 0.018221934701224213, 0.02200483931841161, 0.02437722117931706, 0.019339724267609562, 0.022322862301713264, 0.018637184546346046, 0.02764556180979337, 0.01791101000205525, 0.018407339873149426, 0.028637985079546336, 0.017626723445221894, 0.020706290361268708, 0.018704045485428193, 0.018485759615234378, 0.02134771724616014, 0.01984943740713292, 0.03169009622845424, 0.017124133318241898, 0.01791775072282249, 0.021877557857871283, 0.03139399657126762, 0.01758748440156295, 0.020858167891254133, 0.02647483937188925, 0.027101604351504157, 0.018326738601310445, 0.0175442585533922, 0.019113408596763113, 0.023692468055401254, 0.021701751907165574, 0.02606753365071215, 0.021036682194250998, 0.01903885105975377, 0.01802835515491814, 0.030591505667783327, 0.030263782633526807, 0.024831778862453486, 0.0191023602577076, 0.017692659819896452, 0.018809055602026503, 0.018544608669918267, 0.017494003244483164, 0.022795259982468737, 0.018852230902856367, 0.01856431974976075, 0.018751989170540932, 0.017609500567143947, 0.01840655332887805, 0.019259351748745324, 0.022878102930084677, 0.017994306011463946, 0.030334336848234486, 0.02199297408967497, 0.02093240009442333, 0.022401053143421938, 0.019664811600799467, 0.02922197745188414, 0.022045622721168102, 0.01802915159804679, 0.033850727724821214, 0.019181138493660925, 0.015979058796029427, 0.019255623419254932, 0.019197086361426335, 0.017131107826066555, 0.028522508249157984, 0.018102403887265896, 0.03275293765926531, 0.029095067982623627, 0.022157849219440688, 0.01699317872069141, 0.023341087183141766, 0.01826466480295264, 0.01814738598586747, 0.028556942482181248, 0.0177475371142064], [0.023542479362141017, 0.021034245833247187, 0.02694102655843221, 0.034264102096117965, 0.019164587456230377, 0.018669727984356874, 0.022412193519657685, 0.01857406920605009, 0.019977761068592025, 0.018622994390269734, 0.018743073672487818, 0.01838773767901546, 0.02126723417824426, 0.019470513056083768, 0.02191229276749173, 0.019344827769360674, 0.021603798100591303, 0.01922174811302297, 0.028802937327723942, 0.021804842795837564, 0.023495637346762542, 0.022015273621700224, 0.02202954854088322, 0.017868915910618573, 0.025039701931412583, 0.0193278586143951, 0.02439258680185718, 0.02062764300843308, 0.026521078277870324, 0.021667532730024867, 0.020108646097734002, 0.022916268427705326, 0.01947046417235299, 0.02372535890669548, 0.01993578721679329, 0.019933825180421295, 0.01926945875179087, 0.02585732892121936, 0.023621157945211642, 0.020584881962742003, 0.027627582125544715, 0.02049966100400379, 0.020420121062328545, 0.019486009001262385, 0.02554255230353879, 0.02104823597123129, 0.019308618355301503, 0.019673585224942808, 0.02110214266926285, 0.021173773322821325, 0.02148967795232418, 0.02603398660739978, 0.018772119598852027, 0.021170939734018988, 0.020773316685929192, 0.01862758889268693, 0.023312576121452138, 0.01919817019155011, 0.019340179890049138, 0.018839768628876315, 0.018365706536753415, 0.029355741049012885, 0.025039734195856953, 0.023610664360721182, 0.018485893707598292, 0.01927919767883327, 0.018918051357635614, 0.01977893296901806, 0.01990746241106252, 0.019948477884307876, 0.018615030126412437, 0.01806623379163119, 0.023071480127105425, 0.021250602455927102, 0.02221911662486828, 0.03046534811899472, 0.020591047995765294, 0.019289893447312082, 0.022370476636887748, 0.019946382477933705, 0.024052211705659087, 0.019602121567677242, 0.017003059564600045, 0.018980054942964442, 0.021276539575860984, 0.019255514320625437, 0.02304018800111426, 0.019904727246771566, 0.01867890853087338, 0.02545644621702517, 0.018900260307838947, 0.018299427751838137, 0.022872832760866324, 0.01921480934635435, 0.0186694064891724, 0.019347080289702556, 0.018864651870586762, 0.023711020850386177, 0.01952633424731314, 0.022767402994445626], [0.025698493356494594, 0.024555137662427912, 0.02377368736691741, 0.02545110690919743, 0.02722367280627243, 0.024424901951183933, 0.02539887190654805, 0.028836619181793016, 0.024457534233524866, 0.02743292453725589, 0.026070582793462336, 0.027953402771623663, 0.03206035113735102, 0.02719557797072211, 0.028465817158221, 0.025815331696502342, 0.025411958655102176, 0.022843711623814777, 0.029963531409078228, 0.02522428036469254, 0.025625351557924, 0.02432210537211289, 0.026238108607235293, 0.02803921474569685, 0.02593523858889062, 0.0260800724968954, 0.02666649377230411, 0.0247245099127456, 0.024156083229147148, 0.03046739500371631, 0.024484658083071088, 0.03253797882096315, 0.024551461482682547, 0.03010244373621906, 0.028627086333163895, 0.026008744611390962, 0.03234880268130134, 0.02597450353828824, 0.02814914516766175, 0.02459346648208009, 0.025984032328456825, 0.02613153786248958, 0.02975968915098901, 0.02752908066933788, 0.025426090848461907, 0.023998555089371702, 0.024314155946222337, 0.02860845564265384, 0.02551273240726737, 0.022579628825076345, 0.02381881382795529, 0.02693373754348185, 0.024645384150264037, 0.023841993355502904, 0.032038236285042765, 0.02496324935571206, 0.029112587598778838, 0.02384603112475982, 0.02751513776998946, 0.025055835572159863, 0.03303414360842958, 0.02728430430919463, 0.0319713610044365, 0.025845692733770107, 0.026304722186738863, 0.02722346736817596, 0.027017981860498433, 0.026420195537888772, 0.027362823745645626, 0.02850331286889141, 0.023180915221786915, 0.0254494264290577, 0.026067893232854616, 0.025203161966300396, 0.02948518481630864, 0.030809657364169032, 0.02533678394473645, 0.029404690771683593, 0.02574791274780146, 0.027418199450325142, 0.024902408831709983, 0.025864334996515317, 0.031366953404629264, 0.02625191890962083, 0.0245027955153664, 0.025935789063775673, 0.026222109082776456, 0.02496541362437069, 0.029084365087469102, 0.03011773049471874, 0.031054940376357778, 0.02386589283451919, 0.02465978551248577, 0.02833632218641387, 0.023165506691171265, 0.028252902395366604, 0.025112841392884874, 0.02609227837589042, 0.02782225204732056, 0.025567074281498372], [0.016350853304102908, 0.017384188386155755, 0.016870804159088575, 0.02372984910538565, 0.018882862579953637, 0.021582194772117487, 0.01710580474073211, 0.025639648582136538, 0.015934345953301544, 0.028207925297025847, 0.017506823138699834, 0.01796430813234792, 0.016930275545442526, 0.018666181464226956, 0.023224257966539742, 0.019076921950673457, 0.01816320643209991, 0.018118033983382974, 0.022713706951224554, 0.017065907534021874, 0.018671136405359088, 0.022723491007227124, 0.022516726006388585, 0.01853864382428405, 0.01901957258965063, 0.020244077778870898, 0.027388077859795388, 0.02026740238549639, 0.01891938665109149, 0.02307627008087928, 0.026582325926953605, 0.022517590545958685, 0.02423579607290935, 0.017681151298166366, 0.015631833913183, 0.01887987383043214, 0.028856869527520725, 0.02220302568056124, 0.01942566239067651, 0.022628097262001094, 0.025310848797970593, 0.019462484339686167, 0.023356263772518503, 0.02930966248068627, 0.030745348794722332, 0.020236788078145468, 0.0223401140058202, 0.03284581345919575, 0.028433239643870095, 0.01816351405316449, 0.017306732645515566, 0.021061859340283262, 0.019248169907533037, 0.027264615312499327, 0.025421899541187263, 0.020987802605622177, 0.018277837623851705, 0.025354880628698777, 0.027383184200177033, 0.02091865114439352, 0.029422750963084048, 0.01735882933060455, 0.02341534861406757, 0.017583421796822995, 0.019678215502731668, 0.02204714915242286, 0.02257154781507425, 0.018511153521770036, 0.020593290744795947, 0.017722243782107704, 0.018188555173651897, 0.02315138510549908, 0.02133058285683711, 0.01658201384948988, 0.020083597474429005, 0.02227627822768789, 0.018117866361597866, 0.018152536579170694, 0.025056229706093742, 0.017641701619423345, 0.019029514553202512, 0.020323571053129427, 0.02166415447676049, 0.017966016621941052, 0.018430538741738268, 0.01708106373228107, 0.018559440166808, 0.023413737885939152, 0.027151409730453536, 0.02943447366668932, 0.022524391858745284, 0.020997285249202566, 0.022515559608353032, 0.03469477010016515, 0.022271472355575223, 0.01922654829426734, 0.020649519682330458, 0.021089200095686135, 0.031301172059349465, 0.01674525159956911], [0.020809452051964453, 0.017531851246995443, 0.02270622963316592, 0.0269098107447837, 0.026660235319394286, 0.02183054967646363, 0.018369369477973813, 0.017658592726984158, 0.0213515293539821, 0.027912600236811108, 0.02166374660040715, 0.026408067468096097, 0.018702419087666924, 0.018158541910471962, 0.01884901335906671, 0.019116558746420608, 0.02298243465512765, 0.016664103986766696, 0.01790431783326161, 0.018994245091513807, 0.019766493039658325, 0.02238875336981272, 0.01969174000159229, 0.015992252693153176, 0.018187295878789353, 0.02032839628353958, 0.031866048616723465, 0.020801315829977202, 0.018092041113975915, 0.018436697660519898, 0.021000578713678515, 0.021506953711207855, 0.018679272196435736, 0.025318223420316383, 0.016237985521115227, 0.019394523023550776, 0.017896752936220266, 0.019336312228519583, 0.018198447994879813, 0.017710755576458632, 0.02806422398585089, 0.018141683797760186, 0.017360640066054863, 0.01836577063770503, 0.029065749308100332, 0.01681954510327969, 0.022492923467151916, 0.01829204723992134, 0.01845596377113216, 0.017619018193102673, 0.022173753211684657, 0.018475220833876274, 0.028155293958271137, 0.021924983916235777, 0.0278734680882656, 0.01829462676658939, 0.017530495755698306, 0.017658636523406733, 0.027385047629039264, 0.017524022202908423, 0.020012887032501193, 0.018698043611510427, 0.016724010999107117, 0.016836714597368015, 0.018382929958360716, 0.016722549320060794, 0.027435686161612842, 0.017027949476981784, 0.018745611603430717, 0.01792475818304379, 0.02519980209864064, 0.018565174099094233, 0.02098069167743456, 0.018051158710019805, 0.01829733662671937, 0.031886881769121, 0.017793861346543267, 0.017501857055468858, 0.018782972748926992, 0.026176349334652047, 0.02327153575467277, 0.02162756930538805, 0.02820677605713063, 0.018525041047710543, 0.017924548354201125, 0.016633017738457007, 0.02647435595822223, 0.018999250770189532, 0.0182685502768329, 0.023955723095328053, 0.017784888327246347, 0.02105423530726375, 0.018062929925974254, 0.01846488461299132, 0.01734557498552594, 0.018228038316912408, 0.01870298508018937, 0.026891737589681938, 0.021892412679876308, 0.01696945478315148]]
    lossvec0 = [[0.02560107724424959, 0.0269081801621786, 0.02669660522249634, 0.024729879634511596, 0.025648857312298146, 0.02621274724511835, 0.02664297823115476, 0.027534154570625254, 0.026244620566208486, 0.027881593052699803, 0.02514771882528392, 0.025895062905339265, 0.02455871777661818, 0.027156616863238704, 0.02735149824834501, 0.025705315325367052, 0.025806568293725865, 0.027597040229040144, 0.02538788033694342, 0.027420697680479774, 0.025476306009058022, 0.024608029993090273, 0.026194758004510457, 0.027466699239850206, 0.024961439325118986, 0.026921795586244086, 0.024937067089825887, 0.025422998284085577, 0.030289895527172327, 0.02808349107457011, 0.024561936943751948, 0.026968849333778293, 0.026602448626910736, 0.02829059977337076, 0.026260425878946406, 0.02850330749550472, 0.02451231559113149, 0.027845590886068625, 0.026930801182693493, 0.026330377252314557, 0.026995226987541025, 0.027451621006970028, 0.026367181127762842, 0.02452135147336047, 0.02704915553978583, 0.025228282218213424, 0.026167150545201624, 0.025108869432533893, 0.02606536486296084, 0.025287997631841128, 0.02475351964514969, 0.02647467518363552, 0.025666737801675867, 0.026643570458971793, 0.026059390440933035, 0.025298807652974674, 0.026506798949966857, 0.026024380081188316, 0.02557315791399944, 0.030009943253208392, 0.025153893658539202, 0.0253468193160923, 0.02592543622144289, 0.02641334902509686, 0.025176813756536635, 0.02755753121466075, 0.025124624251483426, 0.025992996261683138, 0.025673998569412985, 0.02581325227760266, 0.025023094332624146, 0.025532723971422838, 0.025590704181495262, 0.026040218656333953, 0.02847555279382509, 0.025378476158844056, 0.02507065180013407, 0.026501962039809663, 0.026412834010457513, 0.02826787001557972, 0.026475103538068246, 0.0245268772293418, 0.02555268533464695, 0.025034599537149413, 0.02796105479569308, 0.026286657790315953, 0.025897425065924642, 0.02705748334863733, 0.028445717798772408, 0.025602823621338675, 0.026492259689535724, 0.027023593306534886, 0.02793286214600318, 0.024594574378462016, 0.026178200371476123, 0.02710415839232178, 0.024512329588119566, 0.025541495439706432, 0.02554922103435433, 0.02540587481027131]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.4$, $n=30$')

    lossveclist = [[0.01812748071917698, 0.018876793914675186, 0.021257685602342084, 0.020459690876102294, 0.018852863867380384, 0.021259359113153086, 0.01897370603149916, 0.02006270285282531, 0.018984942754615344, 0.019161513263085104, 0.02057156961763707, 0.018367258638853627, 0.018965612207244156, 0.019012950586770886, 0.020236255663152944, 0.02159043028497999, 0.021729427177781452, 0.01845943894415715, 0.01796129667118211, 0.01847315012178006, 0.021987185782655558, 0.020128111378433042, 0.018726856897999064, 0.018119249103619332, 0.022808962069408443, 0.019720317415041343, 0.021404376261158334, 0.019782072468996707, 0.020560800418601352, 0.01916063110601593, 0.018792463672390475, 0.020002018930828327, 0.02033638116879233, 0.021432204328884104, 0.017783106942237874, 0.020763153199559334, 0.020866873255472977, 0.0197215178453607, 0.01984572869918766, 0.020422047090861928, 0.024283381380691867, 0.018432873144890276, 0.01821082022601273, 0.02014532316667027, 0.021521042378879033, 0.017390926800459852, 0.01964324038731639, 0.02000631406762651, 0.01900317289587959, 0.01921419218838949, 0.01814081912107971, 0.02052897627536531, 0.019653053792729348, 0.02079293942016379, 0.02012966526500114, 0.019644848565945547, 0.020332028225516104, 0.019409847856650758, 0.019276625729073214, 0.019716122091463287, 0.01889199574064096, 0.018711913763210127, 0.020131886377432802, 0.02052708335660409, 0.021994694427295243, 0.019495164563900984, 0.020613405884402865, 0.019279738338214607, 0.021381807609897763, 0.02031751065833226, 0.019083111154517468, 0.023102957135886965, 0.020845977270873138, 0.01858748022215092, 0.020758222189359576, 0.030733846177539687, 0.01952799339385963, 0.018993371578526253, 0.020919321613045265, 0.01965813249390387, 0.01996494467987496, 0.018832761137595258, 0.01892490309210201, 0.0197858633957759, 0.01949634914027642, 0.018074573901163054, 0.02026931392004915, 0.021742353765380428, 0.019031504034362417, 0.018889026583824284, 0.01970667206503646, 0.019878724491403443, 0.02819718678277317, 0.02606573117020109, 0.0202002960711448, 0.019382493316935135, 0.021178107735956412, 0.020826748653220643, 0.018710690602367557, 0.019217081385916095], [0.017242924142570053, 0.02946449288891925, 0.019194328076912105, 0.02717808342521106, 0.028335241607322727, 0.017741293452439404, 0.016177921458220692, 0.018292712799660542, 0.021276411841702245, 0.0329251761382907, 0.01921155032303231, 0.021088464717309192, 0.025027992902102534, 0.019963261915952348, 0.03146587004209414, 0.019082452506732142, 0.0240806160456614, 0.01818986040052774, 0.016453981495428757, 0.018635305791928323, 0.017670108242837906, 0.018884031912231754, 0.01659989681996534, 0.02174674633015945, 0.018221934701224213, 0.02200483931841161, 0.02437722117931706, 0.019339724267609562, 0.022322862301713264, 0.018637184546346046, 0.02764556180979337, 0.01791101000205525, 0.018407339873149426, 0.028637985079546336, 0.017626723445221894, 0.020706290361268708, 0.018704045485428193, 0.018485759615234378, 0.02134771724616014, 0.01984943740713292, 0.03169009622845424, 0.017124133318241898, 0.01791775072282249, 0.021877557857871283, 0.03139399657126762, 0.01758748440156295, 0.020858167891254133, 0.02647483937188925, 0.027101604351504157, 0.018326738601310445, 0.0175442585533922, 0.019113408596763113, 0.023692468055401254, 0.021701751907165574, 0.02606753365071215, 0.021036682194250998, 0.01903885105975377, 0.01802835515491814, 0.030591505667783327, 0.030263782633526807, 0.024831778862453486, 0.0191023602577076, 0.017692659819896452, 0.018809055602026503, 0.018544608669918267, 0.017494003244483164, 0.022795259982468737, 0.018852230902856367, 0.01856431974976075, 0.018751989170540932, 0.017609500567143947, 0.01840655332887805, 0.019259351748745324, 0.022878102930084677, 0.017994306011463946, 0.030334336848234486, 0.02199297408967497, 0.02093240009442333, 0.022401053143421938, 0.019664811600799467, 0.02922197745188414, 0.022045622721168102, 0.01802915159804679, 0.033850727724821214, 0.019181138493660925, 0.015979058796029427, 0.019255623419254932, 0.019197086361426335, 0.017131107826066555, 0.028522508249157984, 0.018102403887265896, 0.03275293765926531, 0.029095067982623627, 0.022157849219440688, 0.01699317872069141, 0.023341087183141766, 0.01826466480295264, 0.01814738598586747, 0.028556942482181248, 0.0177475371142064], [0.023542479362141017, 0.021034245833247187, 0.02694102655843221, 0.034264102096117965, 0.019164587456230377, 0.018669727984356874, 0.022412193519657685, 0.01857406920605009, 0.019977761068592025, 0.018622994390269734, 0.018743073672487818, 0.01838773767901546, 0.02126723417824426, 0.019470513056083768, 0.02191229276749173, 0.019344827769360674, 0.021603798100591303, 0.01922174811302297, 0.028802937327723942, 0.021804842795837564, 0.023495637346762542, 0.022015273621700224, 0.02202954854088322, 0.017868915910618573, 0.025039701931412583, 0.0193278586143951, 0.02439258680185718, 0.02062764300843308, 0.026521078277870324, 0.021667532730024867, 0.020108646097734002, 0.022916268427705326, 0.01947046417235299, 0.02372535890669548, 0.01993578721679329, 0.019933825180421295, 0.01926945875179087, 0.02585732892121936, 0.023621157945211642, 0.020584881962742003, 0.027627582125544715, 0.02049966100400379, 0.020420121062328545, 0.019486009001262385, 0.02554255230353879, 0.02104823597123129, 0.019308618355301503, 0.019673585224942808, 0.02110214266926285, 0.021173773322821325, 0.02148967795232418, 0.02603398660739978, 0.018772119598852027, 0.021170939734018988, 0.020773316685929192, 0.01862758889268693, 0.023312576121452138, 0.01919817019155011, 0.019340179890049138, 0.018839768628876315, 0.018365706536753415, 0.029355741049012885, 0.025039734195856953, 0.023610664360721182, 0.018485893707598292, 0.01927919767883327, 0.018918051357635614, 0.01977893296901806, 0.01990746241106252, 0.019948477884307876, 0.018615030126412437, 0.01806623379163119, 0.023071480127105425, 0.021250602455927102, 0.02221911662486828, 0.03046534811899472, 0.020591047995765294, 0.019289893447312082, 0.022370476636887748, 0.019946382477933705, 0.024052211705659087, 0.019602121567677242, 0.017003059564600045, 0.018980054942964442, 0.021276539575860984, 0.019255514320625437, 0.02304018800111426, 0.019904727246771566, 0.01867890853087338, 0.02545644621702517, 0.018900260307838947, 0.018299427751838137, 0.022872832760866324, 0.01921480934635435, 0.0186694064891724, 0.019347080289702556, 0.018864651870586762, 0.023711020850386177, 0.01952633424731314, 0.022767402994445626], [0.025698493356494594, 0.024555137662427912, 0.02377368736691741, 0.02545110690919743, 0.02722367280627243, 0.024424901951183933, 0.02539887190654805, 0.028836619181793016, 0.024457534233524866, 0.02743292453725589, 0.026070582793462336, 0.027953402771623663, 0.03206035113735102, 0.02719557797072211, 0.028465817158221, 0.025815331696502342, 0.025411958655102176, 0.022843711623814777, 0.029963531409078228, 0.02522428036469254, 0.025625351557924, 0.02432210537211289, 0.026238108607235293, 0.02803921474569685, 0.02593523858889062, 0.0260800724968954, 0.02666649377230411, 0.0247245099127456, 0.024156083229147148, 0.03046739500371631, 0.024484658083071088, 0.03253797882096315, 0.024551461482682547, 0.03010244373621906, 0.028627086333163895, 0.026008744611390962, 0.03234880268130134, 0.02597450353828824, 0.02814914516766175, 0.02459346648208009, 0.025984032328456825, 0.02613153786248958, 0.02975968915098901, 0.02752908066933788, 0.025426090848461907, 0.023998555089371702, 0.024314155946222337, 0.02860845564265384, 0.02551273240726737, 0.022579628825076345, 0.02381881382795529, 0.02693373754348185, 0.024645384150264037, 0.023841993355502904, 0.032038236285042765, 0.02496324935571206, 0.029112587598778838, 0.02384603112475982, 0.02751513776998946, 0.025055835572159863, 0.03303414360842958, 0.02728430430919463, 0.0319713610044365, 0.025845692733770107, 0.026304722186738863, 0.02722346736817596, 0.027017981860498433, 0.026420195537888772, 0.027362823745645626, 0.02850331286889141, 0.023180915221786915, 0.0254494264290577, 0.026067893232854616, 0.025203161966300396, 0.02948518481630864, 0.030809657364169032, 0.02533678394473645, 0.029404690771683593, 0.02574791274780146, 0.027418199450325142, 0.024902408831709983, 0.025864334996515317, 0.031366953404629264, 0.02625191890962083, 0.0245027955153664, 0.025935789063775673, 0.026222109082776456, 0.02496541362437069, 0.029084365087469102, 0.03011773049471874, 0.031054940376357778, 0.02386589283451919, 0.02465978551248577, 0.02833632218641387, 0.023165506691171265, 0.028252902395366604, 0.025112841392884874, 0.02609227837589042, 0.02782225204732056, 0.025567074281498372], [0.016350853304102908, 0.017384188386155755, 0.016870804159088575, 0.02372984910538565, 0.018882862579953637, 0.021582194772117487, 0.01710580474073211, 0.025639648582136538, 0.015934345953301544, 0.028207925297025847, 0.017506823138699834, 0.01796430813234792, 0.016930275545442526, 0.018666181464226956, 0.023224257966539742, 0.019076921950673457, 0.01816320643209991, 0.018118033983382974, 0.022713706951224554, 0.017065907534021874, 0.018671136405359088, 0.022723491007227124, 0.022516726006388585, 0.01853864382428405, 0.01901957258965063, 0.020244077778870898, 0.027388077859795388, 0.02026740238549639, 0.01891938665109149, 0.02307627008087928, 0.026582325926953605, 0.022517590545958685, 0.02423579607290935, 0.017681151298166366, 0.015631833913183, 0.01887987383043214, 0.028856869527520725, 0.02220302568056124, 0.01942566239067651, 0.022628097262001094, 0.025310848797970593, 0.019462484339686167, 0.023356263772518503, 0.02930966248068627, 0.030745348794722332, 0.020236788078145468, 0.0223401140058202, 0.03284581345919575, 0.028433239643870095, 0.01816351405316449, 0.017306732645515566, 0.021061859340283262, 0.019248169907533037, 0.027264615312499327, 0.025421899541187263, 0.020987802605622177, 0.018277837623851705, 0.025354880628698777, 0.027383184200177033, 0.02091865114439352, 0.029422750963084048, 0.01735882933060455, 0.02341534861406757, 0.017583421796822995, 0.019678215502731668, 0.02204714915242286, 0.02257154781507425, 0.018511153521770036, 0.020593290744795947, 0.017722243782107704, 0.018188555173651897, 0.02315138510549908, 0.02133058285683711, 0.01658201384948988, 0.020083597474429005, 0.02227627822768789, 0.018117866361597866, 0.018152536579170694, 0.025056229706093742, 0.017641701619423345, 0.019029514553202512, 0.020323571053129427, 0.02166415447676049, 0.017966016621941052, 0.018430538741738268, 0.01708106373228107, 0.018559440166808, 0.023413737885939152, 0.027151409730453536, 0.02943447366668932, 0.022524391858745284, 0.020997285249202566, 0.022515559608353032, 0.03469477010016515, 0.022271472355575223, 0.01922654829426734, 0.020649519682330458, 0.021089200095686135, 0.031301172059349465, 0.01674525159956911], [0.020809452051964453, 0.017531851246995443, 0.02270622963316592, 0.0269098107447837, 0.026660235319394286, 0.02183054967646363, 0.018369369477973813, 0.017658592726984158, 0.0213515293539821, 0.027912600236811108, 0.02166374660040715, 0.026408067468096097, 0.018702419087666924, 0.018158541910471962, 0.01884901335906671, 0.019116558746420608, 0.02298243465512765, 0.016664103986766696, 0.01790431783326161, 0.018994245091513807, 0.019766493039658325, 0.02238875336981272, 0.01969174000159229, 0.015992252693153176, 0.018187295878789353, 0.02032839628353958, 0.031866048616723465, 0.020801315829977202, 0.018092041113975915, 0.018436697660519898, 0.021000578713678515, 0.021506953711207855, 0.018679272196435736, 0.025318223420316383, 0.016237985521115227, 0.019394523023550776, 0.017896752936220266, 0.019336312228519583, 0.018198447994879813, 0.017710755576458632, 0.02806422398585089, 0.018141683797760186, 0.017360640066054863, 0.01836577063770503, 0.029065749308100332, 0.01681954510327969, 0.022492923467151916, 0.01829204723992134, 0.01845596377113216, 0.017619018193102673, 0.022173753211684657, 0.018475220833876274, 0.028155293958271137, 0.021924983916235777, 0.0278734680882656, 0.01829462676658939, 0.017530495755698306, 0.017658636523406733, 0.027385047629039264, 0.017524022202908423, 0.020012887032501193, 0.018698043611510427, 0.016724010999107117, 0.016836714597368015, 0.018382929958360716, 0.016722549320060794, 0.027435686161612842, 0.017027949476981784, 0.018745611603430717, 0.01792475818304379, 0.02519980209864064, 0.018565174099094233, 0.02098069167743456, 0.018051158710019805, 0.01829733662671937, 0.031886881769121, 0.017793861346543267, 0.017501857055468858, 0.018782972748926992, 0.026176349334652047, 0.02327153575467277, 0.02162756930538805, 0.02820677605713063, 0.018525041047710543, 0.017924548354201125, 0.016633017738457007, 0.02647435595822223, 0.018999250770189532, 0.0182685502768329, 0.023955723095328053, 0.017784888327246347, 0.02105423530726375, 0.018062929925974254, 0.01846488461299132, 0.01734557498552594, 0.018228038316912408, 0.01870298508018937, 0.026891737589681938, 0.021892412679876308, 0.01696945478315148]]
    lossvec0 = [[0.02560107724424959, 0.0269081801621786, 0.02669660522249634, 0.024729879634511596, 0.025648857312298146, 0.02621274724511835, 0.02664297823115476, 0.027534154570625254, 0.026244620566208486, 0.027881593052699803, 0.02514771882528392, 0.025895062905339265, 0.02455871777661818, 0.027156616863238704, 0.02735149824834501, 0.025705315325367052, 0.025806568293725865, 0.027597040229040144, 0.02538788033694342, 0.027420697680479774, 0.025476306009058022, 0.024608029993090273, 0.026194758004510457, 0.027466699239850206, 0.024961439325118986, 0.026921795586244086, 0.024937067089825887, 0.025422998284085577, 0.030289895527172327, 0.02808349107457011, 0.024561936943751948, 0.026968849333778293, 0.026602448626910736, 0.02829059977337076, 0.026260425878946406, 0.02850330749550472, 0.02451231559113149, 0.027845590886068625, 0.026930801182693493, 0.026330377252314557, 0.026995226987541025, 0.027451621006970028, 0.026367181127762842, 0.02452135147336047, 0.02704915553978583, 0.025228282218213424, 0.026167150545201624, 0.025108869432533893, 0.02606536486296084, 0.025287997631841128, 0.02475351964514969, 0.02647467518363552, 0.025666737801675867, 0.026643570458971793, 0.026059390440933035, 0.025298807652974674, 0.026506798949966857, 0.026024380081188316, 0.02557315791399944, 0.030009943253208392, 0.025153893658539202, 0.0253468193160923, 0.02592543622144289, 0.02641334902509686, 0.025176813756536635, 0.02755753121466075, 0.025124624251483426, 0.025992996261683138, 0.025673998569412985, 0.02581325227760266, 0.025023094332624146, 0.025532723971422838, 0.025590704181495262, 0.026040218656333953, 0.02847555279382509, 0.025378476158844056, 0.02507065180013407, 0.026501962039809663, 0.026412834010457513, 0.02826787001557972, 0.026475103538068246, 0.0245268772293418, 0.02555268533464695, 0.025034599537149413, 0.02796105479569308, 0.026286657790315953, 0.025897425065924642, 0.02705748334863733, 0.028445717798772408, 0.025602823621338675, 0.026492259689535724, 0.027023593306534886, 0.02793286214600318, 0.024594574378462016, 0.026178200371476123, 0.02710415839232178, 0.024512329588119566, 0.025541495439706432, 0.02554922103435433, 0.02540587481027131]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### underEstWt=1., CHECK RISK, m=0.1 ###
    # Get null first
    underWt, mRisk = 1., 0.1
    t = 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Check', 'threshold': t, 'slope': mRisk}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_check, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 09-AUG-22
    designNames = ['Design 0']
    lossveclist = [[0.20818351333430446, 0.19981285653588504, 0.20510718595284982, 0.20984635247607544, 0.2034003249549822, 0.21024687557633845, 0.21078277725917077, 0.20653370198423912, 0.21013932241578603, 0.20505582112496656, 0.19698161102331044, 0.19550270268205727, 0.20498398521223687, 0.2004045472147817, 0.1938799390627333, 0.21772568431732175, 0.2083464340948261, 0.21312427103457943, 0.20674441400411894, 0.20197090673753015, 0.19674417388980864, 0.20320873715142776, 0.20001795522201402, 0.19731847013024467, 0.19853312040101412, 0.20129907350618043, 0.20838641921522089, 0.19830498772912775, 0.19879061907507514, 0.2035717258104826, 0.2071246318183616, 0.19911613689133936, 0.20837133964626825, 0.20733400082767026, 0.1996090026481862, 0.21174315412005834, 0.20255750876325515, 0.20502087246770231, 0.20067829356497618, 0.19911627064069187, 0.20702832251436945, 0.19062101256686145, 0.20061988655929894, 0.20834205780624665, 0.2084570714048183, 0.20801329073256525, 0.1997740355226297, 0.20237710448742754, 0.2006843667433806, 0.18904631172160938, 0.18869161011054442, 0.20306350078420582, 0.20086275950573393, 0.19911989150292886, 0.20728355930120665, 0.20825225333936473, 0.20277188661312381, 0.19901486402762184, 0.19576125972752062, 0.2003416781983626, 0.20685900926340084, 0.20535431418632566, 0.20014654589662578, 0.19353750842864006, 0.20862085650120285, 0.19620696021568787, 0.2171938959481364, 0.20043573679795187, 0.20652926543952865, 0.21575306577144276, 0.20894506769395718, 0.21674504563265906, 0.19200237127934186, 0.192631343530857, 0.20276170950880298, 0.20117767984285972, 0.20228917232107702, 0.19913795365197445, 0.2053118917034573, 0.2041415103259663, 0.1988746636985184, 0.2060420797280611, 0.2156591816397663, 0.2051412500684295, 0.19190375324465064, 0.21039661234083334, 0.20799739772136383, 0.20549524103215222, 0.21305080974941387, 0.2058906120337652, 0.2089697343776439, 0.19586999330899366, 0.19757790116004362, 0.21739047753762414, 0.20433306212483993, 0.19943430194574346, 0.2024540919495018, 0.2032482493316871, 0.1982019813597425, 0.2090213243106029]]
    '''
    # 30 tests for all designs
    underWt, mRisk = 1., 0.1
    t = 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Check', 'threshold': t, 'slope': mRisk}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_check, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 09-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.16128046324006215, 0.1534955735864618, 0.1598244433572646, 0.16572487053029172, 0.16055013431802773, 0.17135385959145977, 0.15588520712339546, 0.17500900693927607, 0.1589642565332563, 0.1515644536704604, 0.15743614700622485, 0.15485572185840935, 0.15005821471524342, 0.16582094550483328, 0.16358095488872104, 0.17960980398260118, 0.156900798444042, 0.15974218400785706, 0.15230225966856248, 0.17011169503266826, 0.16761487680179435, 0.16227610021737018, 0.15756673429837378, 0.15871624665458128, 0.17954688863159887, 0.15509719857139567, 0.23193256445769161, 0.1591611175334134, 0.1856332455115818, 0.15172290660022889, 0.15386788369396712, 0.14735925906701755, 0.15493887188492927, 0.16457670732931684, 0.15410631780253203, 0.1592712993123911, 0.170780059844864, 0.15516752148515717, 0.16121575826541895, 0.16896550536819824, 0.2422280476498597, 0.15866687668660148, 0.16962434514474634, 0.1682979306352954, 0.16205167385249578, 0.14998479375706847, 0.16465277393790018, 0.1488852234705307, 0.1678966997728805, 0.1721145101823836, 0.15483092674528373, 0.15596291070580576, 0.15794974166055242, 0.166333956788314, 0.17369156838060085, 0.16809659933021928, 0.15845941519837967, 0.15692826305176366, 0.1678677391820066, 0.1588580553619429, 0.15141658138571729, 0.1660340292101784, 0.20939979379586096, 0.1596538513664725, 0.17337490192227517, 0.1574009044194363, 0.16031471237713246, 0.15670645860698895, 0.18390196028852399, 0.1532174968450483, 0.15600272569873505, 0.15709720647781478, 0.18868659978262517, 0.158754481363829, 0.17075271799360053, 0.21404889749015968, 0.16896697721633977, 0.15897110871701042, 0.15346351609962988, 0.17770169165711985, 0.1682159521940313, 0.165527211422002, 0.15709065048740437, 0.15829519602284908, 0.16108712309131232, 0.157800929578829, 0.19904283442843207, 0.19557548076812456, 0.16139829107802156, 0.17496450758604443, 0.16193900699079028, 0.1623900835334086, 0.18145775317578164, 0.1637968482599369, 0.15663488295242137, 0.15958879606269727, 0.19508899552830233, 0.20380839420333444, 0.1579234259416651, 0.15521008129785727], [0.1359039100546709, 0.1502435185916458, 0.14473285562372326, 0.198239335465382, 0.16560881968320923, 0.1722037983905823, 0.14528156482720386, 0.14325371508384804, 0.14970926838553908, 0.1913227761898451, 0.1479207278652812, 0.1317063902178966, 0.17043461039052632, 0.1474351440472262, 0.17732861798643923, 0.17139965192347648, 0.1410474347333284, 0.13651853832329058, 0.16295934962178427, 0.16481649537975773, 0.143264829208327, 0.21439035670671988, 0.19310924612208413, 0.1440843768304938, 0.13638844107243875, 0.22242251457446602, 0.17251307984845424, 0.1717870154482948, 0.19214676979145434, 0.14526571095748775, 0.168172360576851, 0.13746950365184024, 0.16726495743992031, 0.14148763103645912, 0.14255273664025803, 0.1754471080274901, 0.14100246230390884, 0.1459086968041366, 0.171619984947047, 0.1460723494861141, 0.1985336400955749, 0.13865034711408972, 0.1402611882768604, 0.1867858679116178, 0.2078522949563755, 0.1415433074208529, 0.18654689535456925, 0.17560551383772552, 0.20365317450806258, 0.16415497532490864, 0.14914208747462832, 0.13780750913632142, 0.19669850045090378, 0.17238512843722315, 0.15949659074884293, 0.18395493670197172, 0.1422570229100149, 0.1623704982671745, 0.2045225946392991, 0.1704201190494518, 0.1452678903392349, 0.1384966938475233, 0.14062205533219607, 0.13810356693256604, 0.16458795066014187, 0.1605313489505847, 0.19483231812935595, 0.1676984333096826, 0.14092224535535913, 0.13705587127069171, 0.16437297670897574, 0.13839033232645037, 0.17086132550729852, 0.1494164540539857, 0.23784976846399675, 0.2002602533634236, 0.16516768838834045, 0.1785209107343623, 0.14304615973961432, 0.19653921191419152, 0.17112291326002113, 0.1411109999574424, 0.136522496662072, 0.18638575453702294, 0.14504671354926665, 0.14280112676060905, 0.14748974336182538, 0.1427846098254798, 0.13830041951183722, 0.2051075135770645, 0.22714559216498847, 0.14375751278812507, 0.2041956495246469, 0.1485405626645498, 0.14211092665258485, 0.1437789834128651, 0.151424016377492, 0.16617527979907276, 0.1709283808219253, 0.13926124620926436], [0.15157911682667888, 0.1865326575438386, 0.17385267833861773, 0.18989837387616765, 0.16011899811105682, 0.1463139134010669, 0.1748952933284981, 0.1595955824335415, 0.14753475956469295, 0.15972602432896474, 0.16638432431698255, 0.14970865174457945, 0.1597254036470066, 0.15085598574960066, 0.15061562350071103, 0.16084189009376346, 0.1711837249783019, 0.15638663062985456, 0.14468740219506868, 0.16691602791878954, 0.15095269072890152, 0.16880667048501846, 0.15241256793202398, 0.16326657212359902, 0.16235261045298746, 0.17008045533079724, 0.17510135259240558, 0.1682960834616401, 0.1857432828028751, 0.1674150661735411, 0.16196395513714523, 0.16191727647577706, 0.17439502119746936, 0.1613572016315564, 0.16427963526067058, 0.1437949485645752, 0.14505023193682307, 0.15504048519043867, 0.15143828118262523, 0.1854701999331783, 0.20230334464658178, 0.1589602604847931, 0.14593590571843432, 0.1898961481487456, 0.18509488450920075, 0.14810456059607868, 0.15822653229080477, 0.16095209626006532, 0.16305830333054133, 0.15495010518323235, 0.1613522226206439, 0.15890694362822885, 0.20617893535840745, 0.1900877430615602, 0.16778086022499664, 0.166402130202129, 0.15683492216281597, 0.19837994730847291, 0.16763184987473795, 0.16849642821131522, 0.16512991959475398, 0.15447151153070443, 0.1968640017595128, 0.16441808854623136, 0.17360001817119328, 0.16177261411199084, 0.16636833831149644, 0.16369762891292594, 0.15337039998032326, 0.1606852337816176, 0.16625655414494037, 0.15718964494127854, 0.15573027887167815, 0.17266396261860387, 0.19653782027896904, 0.20713474742974058, 0.1835464607039273, 0.15905293831711872, 0.1777482711794229, 0.17496871999387464, 0.1558802252836892, 0.14949915140110745, 0.16266443812325435, 0.15946064627290701, 0.17522445128978006, 0.15776928876572108, 0.16474770810893422, 0.16515620484076046, 0.16212670992934577, 0.1517940602686054, 0.16148400329317952, 0.15818292750565993, 0.18091831545501022, 0.15663624828538655, 0.17041273340554522, 0.165128057319708, 0.17041614834282057, 0.19482511861626708, 0.15747166189471107, 0.14306343025369256], [0.18811908558518164, 0.21934862066327498, 0.19510939109092362, 0.20199901232590353, 0.22088504690011132, 0.19457005030345362, 0.18864037580731047, 0.1998949779592681, 0.1848202341540553, 0.1880914388275318, 0.19599061976594193, 0.2112468406640609, 0.19639583502265281, 0.18334492587618667, 0.18366524353671992, 0.2110376531243332, 0.2045190053957147, 0.18833821063623066, 0.21862683595598273, 0.18948037547724794, 0.1954554031359344, 0.18426963187329304, 0.21652527178910788, 0.1861301438716434, 0.17197580041974989, 0.1866882817708748, 0.19050141185040975, 0.22202675277554054, 0.183735946077554, 0.20695089476014009, 0.1965052498421009, 0.21727182258808228, 0.20537226074138018, 0.18725936485545888, 0.2110014594597231, 0.17718960877763326, 0.219786730809935, 0.20026892552857492, 0.21706150250045161, 0.1848561437314398, 0.18228988365021764, 0.20848733247625115, 0.24481225792843592, 0.17604608673185343, 0.17594777317379942, 0.18438187955470256, 0.1967962384308554, 0.24282414783423062, 0.20092062008327077, 0.19292167189266846, 0.1875971733988719, 0.2187936584094861, 0.21568688244593248, 0.1839977880731962, 0.20393564755596327, 0.18814355116993622, 0.20880103488402263, 0.18844519316798297, 0.19323061727869165, 0.18687253013282112, 0.2380694761950305, 0.18857155131856054, 0.23274177879374583, 0.1835506351501335, 0.20071786641834144, 0.19563424738300625, 0.1915047793587807, 0.21894545874144686, 0.18088862100151665, 0.18377694592140534, 0.2054506135652157, 0.19667462656145687, 0.20759516872388736, 0.19558112827081328, 0.2062451946383479, 0.1881499710091324, 0.18686045062624462, 0.22716578616469815, 0.19322067238682816, 0.19953223038109527, 0.19344906685388277, 0.21176738363544845, 0.19344426143338858, 0.19756744151936861, 0.21890570975749085, 0.18296170932344571, 0.18359437566815842, 0.20040403393326284, 0.2250244269672026, 0.20950670454764708, 0.19278834116775026, 0.20407801333741335, 0.1940827910687393, 0.167995074462947, 0.19995532968480512, 0.21268001996522481, 0.18904035093038812, 0.2040606618612378, 0.19911989370456956, 0.19012533083682398], [0.15827257507729528, 0.15582113551088228, 0.15559392793025878, 0.20239374058904572, 0.13743835483564723, 0.20818507029313266, 0.18493431036923297, 0.16697071520873427, 0.15499209714859133, 0.1749134526125417, 0.14949183712601058, 0.1347274887040455, 0.21793032118482658, 0.17077206096619052, 0.13822357313343286, 0.1400068481258136, 0.19537820231656244, 0.1637504016776044, 0.21200782824583794, 0.16732016434227895, 0.14628094326542487, 0.14633288449435253, 0.17353219591962363, 0.1540949006275829, 0.18903064547081896, 0.13883577426404345, 0.17490376307867375, 0.17371732295507403, 0.2012982890456049, 0.135164569627142, 0.13937496756766665, 0.16654832758340535, 0.15908998146428996, 0.15801955110390903, 0.1329773044384674, 0.16871632194520136, 0.1741987485605136, 0.1444389467613179, 0.16046847039248183, 0.13697185192598516, 0.29381257228895075, 0.15670878203454613, 0.2066972989283294, 0.1441221859962293, 0.2936433572550496, 0.16946974388362326, 0.16660587754021355, 0.1589795825441841, 0.18693053852437608, 0.14002177123084483, 0.1427620091729178, 0.13642241440308345, 0.18902558750393625, 0.133122651248456, 0.18777441591793234, 0.15719478598503545, 0.17096735724675768, 0.17225769752391037, 0.16475106377477913, 0.16569348645969656, 0.1727218175691204, 0.14073708353666411, 0.14823111808136047, 0.14348332761650923, 0.14071030456691916, 0.20975917814393522, 0.1978949487587753, 0.1433398206058781, 0.14701780125731023, 0.14493229046552103, 0.1429478566974774, 0.15885490272572123, 0.15102188321054416, 0.16326340845000845, 0.14409286004764996, 0.23230357189168568, 0.1402564305803771, 0.15723135769532415, 0.1647395684115326, 0.1816716247914323, 0.1802294355872763, 0.16147569020320576, 0.17891811872381375, 0.1954627802811629, 0.14461955469985172, 0.14209663109079504, 0.14319440186007615, 0.1735984254033426, 0.18126496400954295, 0.18617884494849374, 0.20885213879460998, 0.1685752430244811, 0.1884629472976591, 0.18101873479529546, 0.21191991184213513, 0.1510864101460429, 0.14463154470267608, 0.15100180125708915, 0.18003068417388635, 0.18450409234789622], [0.19263272104007997, 0.14100710750742584, 0.14407029338073232, 0.1682440880750341, 0.16387620113386192, 0.13878197805810727, 0.1340086266643323, 0.1373052697627711, 0.1382017455657353, 0.20421473594720624, 0.13980272263690643, 0.19206437288830105, 0.2817464463639736, 0.1413458520970173, 0.19031046867053003, 0.1804596028474243, 0.16791767699934454, 0.1388888804912433, 0.179038756604695, 0.13993756801613108, 0.1448179722323464, 0.1722392148016903, 0.19277383151751437, 0.1376985653049388, 0.14551524954396475, 0.13332366419437722, 0.17022903525040048, 0.16697807262856426, 0.18428281426933105, 0.143742501316644, 0.14746930371177291, 0.16688853488255792, 0.13960881277544576, 0.1459550285485862, 0.13349547108599527, 0.14108609382926948, 0.17168230516685007, 0.14340940722485312, 0.13397529972175173, 0.14321219096062815, 0.23517895232938488, 0.14142332457196646, 0.13950269965068288, 0.2425009168725944, 0.2918700343430081, 0.135343230655926, 0.18581311226584254, 0.13553834406366794, 0.1416049410248834, 0.13744530201112576, 0.13506005731575527, 0.18408159284028439, 0.21534102657950407, 0.14378145462660025, 0.17408065150838942, 0.14395829317921513, 0.14149810944905197, 0.1463693545956684, 0.1905600510479834, 0.1924226360234655, 0.1341140498912619, 0.1384883150658107, 0.15963800665167985, 0.14327704915869494, 0.13649155377093636, 0.13671628486718526, 0.16261198901129365, 0.18124573220115456, 0.1495324082863124, 0.18553816470914378, 0.14270918157346374, 0.14370186833369114, 0.17578649073012947, 0.16275475144200818, 0.13514783781218534, 0.1802117249748641, 0.14466751418402238, 0.17316518675538725, 0.13790059064639007, 0.17835782700918498, 0.14695323723064782, 0.14002262868082146, 0.1697708648732214, 0.1951583827169044, 0.13724547964199718, 0.13528916216086645, 0.17414800842275782, 0.1430114581483038, 0.1421848534237272, 0.14002973471219923, 0.18919812802445066, 0.15934151199906063, 0.16610785047874965, 0.14536349384756642, 0.18964478210377825, 0.15365322419369917, 0.15769508095641097, 0.17030517813398593, 0.12982198892592878, 0.15177372485459611]]
    lossvec0 = [[0.20818351333430446, 0.19981285653588504, 0.20510718595284982, 0.20984635247607544, 0.2034003249549822, 0.21024687557633845, 0.21078277725917077, 0.20653370198423912, 0.21013932241578603, 0.20505582112496656, 0.19698161102331044, 0.19550270268205727, 0.20498398521223687, 0.2004045472147817, 0.1938799390627333, 0.21772568431732175, 0.2083464340948261, 0.21312427103457943, 0.20674441400411894, 0.20197090673753015, 0.19674417388980864, 0.20320873715142776, 0.20001795522201402, 0.19731847013024467, 0.19853312040101412, 0.20129907350618043, 0.20838641921522089, 0.19830498772912775, 0.19879061907507514, 0.2035717258104826, 0.2071246318183616, 0.19911613689133936, 0.20837133964626825, 0.20733400082767026, 0.1996090026481862, 0.21174315412005834, 0.20255750876325515, 0.20502087246770231, 0.20067829356497618, 0.19911627064069187, 0.20702832251436945, 0.19062101256686145, 0.20061988655929894, 0.20834205780624665, 0.2084570714048183, 0.20801329073256525, 0.1997740355226297, 0.20237710448742754, 0.2006843667433806, 0.18904631172160938, 0.18869161011054442, 0.20306350078420582, 0.20086275950573393, 0.19911989150292886, 0.20728355930120665, 0.20825225333936473, 0.20277188661312381, 0.19901486402762184, 0.19576125972752062, 0.2003416781983626, 0.20685900926340084, 0.20535431418632566, 0.20014654589662578, 0.19353750842864006, 0.20862085650120285, 0.19620696021568787, 0.2171938959481364, 0.20043573679795187, 0.20652926543952865, 0.21575306577144276, 0.20894506769395718, 0.21674504563265906, 0.19200237127934186, 0.192631343530857, 0.20276170950880298, 0.20117767984285972, 0.20228917232107702, 0.19913795365197445, 0.2053118917034573, 0.2041415103259663, 0.1988746636985184, 0.2060420797280611, 0.2156591816397663, 0.2051412500684295, 0.19190375324465064, 0.21039661234083334, 0.20799739772136383, 0.20549524103215222, 0.21305080974941387, 0.2058906120337652, 0.2089697343776439, 0.19586999330899366, 0.19757790116004362, 0.21739047753762414, 0.20433306212483993, 0.19943430194574346, 0.2024540919495018, 0.2032482493316871, 0.1982019813597425, 0.2090213243106029]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.4$, $n=30$')

    lossveclist = [[0.16128046324006215, 0.1534955735864618, 0.1598244433572646, 0.16572487053029172, 0.16055013431802773, 0.17135385959145977, 0.15588520712339546, 0.17500900693927607, 0.1589642565332563, 0.1515644536704604, 0.15743614700622485, 0.15485572185840935, 0.15005821471524342, 0.16582094550483328, 0.16358095488872104, 0.17960980398260118, 0.156900798444042, 0.15974218400785706, 0.15230225966856248, 0.17011169503266826, 0.16761487680179435, 0.16227610021737018, 0.15756673429837378, 0.15871624665458128, 0.17954688863159887, 0.15509719857139567, 0.23193256445769161, 0.1591611175334134, 0.1856332455115818, 0.15172290660022889, 0.15386788369396712, 0.14735925906701755, 0.15493887188492927, 0.16457670732931684, 0.15410631780253203, 0.1592712993123911, 0.170780059844864, 0.15516752148515717, 0.16121575826541895, 0.16896550536819824, 0.2422280476498597, 0.15866687668660148, 0.16962434514474634, 0.1682979306352954, 0.16205167385249578, 0.14998479375706847, 0.16465277393790018, 0.1488852234705307, 0.1678966997728805, 0.1721145101823836, 0.15483092674528373, 0.15596291070580576, 0.15794974166055242, 0.166333956788314, 0.17369156838060085, 0.16809659933021928, 0.15845941519837967, 0.15692826305176366, 0.1678677391820066, 0.1588580553619429, 0.15141658138571729, 0.1660340292101784, 0.20939979379586096, 0.1596538513664725, 0.17337490192227517, 0.1574009044194363, 0.16031471237713246, 0.15670645860698895, 0.18390196028852399, 0.1532174968450483, 0.15600272569873505, 0.15709720647781478, 0.18868659978262517, 0.158754481363829, 0.17075271799360053, 0.21404889749015968, 0.16896697721633977, 0.15897110871701042, 0.15346351609962988, 0.17770169165711985, 0.1682159521940313, 0.165527211422002, 0.15709065048740437, 0.15829519602284908, 0.16108712309131232, 0.157800929578829, 0.19904283442843207, 0.19557548076812456, 0.16139829107802156, 0.17496450758604443, 0.16193900699079028, 0.1623900835334086, 0.18145775317578164, 0.1637968482599369, 0.15663488295242137, 0.15958879606269727, 0.19508899552830233, 0.20380839420333444, 0.1579234259416651, 0.15521008129785727], [0.1359039100546709, 0.1502435185916458, 0.14473285562372326, 0.198239335465382, 0.16560881968320923, 0.1722037983905823, 0.14528156482720386, 0.14325371508384804, 0.14970926838553908, 0.1913227761898451, 0.1479207278652812, 0.1317063902178966, 0.17043461039052632, 0.1474351440472262, 0.17732861798643923, 0.17139965192347648, 0.1410474347333284, 0.13651853832329058, 0.16295934962178427, 0.16481649537975773, 0.143264829208327, 0.21439035670671988, 0.19310924612208413, 0.1440843768304938, 0.13638844107243875, 0.22242251457446602, 0.17251307984845424, 0.1717870154482948, 0.19214676979145434, 0.14526571095748775, 0.168172360576851, 0.13746950365184024, 0.16726495743992031, 0.14148763103645912, 0.14255273664025803, 0.1754471080274901, 0.14100246230390884, 0.1459086968041366, 0.171619984947047, 0.1460723494861141, 0.1985336400955749, 0.13865034711408972, 0.1402611882768604, 0.1867858679116178, 0.2078522949563755, 0.1415433074208529, 0.18654689535456925, 0.17560551383772552, 0.20365317450806258, 0.16415497532490864, 0.14914208747462832, 0.13780750913632142, 0.19669850045090378, 0.17238512843722315, 0.15949659074884293, 0.18395493670197172, 0.1422570229100149, 0.1623704982671745, 0.2045225946392991, 0.1704201190494518, 0.1452678903392349, 0.1384966938475233, 0.14062205533219607, 0.13810356693256604, 0.16458795066014187, 0.1605313489505847, 0.19483231812935595, 0.1676984333096826, 0.14092224535535913, 0.13705587127069171, 0.16437297670897574, 0.13839033232645037, 0.17086132550729852, 0.1494164540539857, 0.23784976846399675, 0.2002602533634236, 0.16516768838834045, 0.1785209107343623, 0.14304615973961432, 0.19653921191419152, 0.17112291326002113, 0.1411109999574424, 0.136522496662072, 0.18638575453702294, 0.14504671354926665, 0.14280112676060905, 0.14748974336182538, 0.1427846098254798, 0.13830041951183722, 0.2051075135770645, 0.22714559216498847, 0.14375751278812507, 0.2041956495246469, 0.1485405626645498, 0.14211092665258485, 0.1437789834128651, 0.151424016377492, 0.16617527979907276, 0.1709283808219253, 0.13926124620926436], [0.15157911682667888, 0.1865326575438386, 0.17385267833861773, 0.18989837387616765, 0.16011899811105682, 0.1463139134010669, 0.1748952933284981, 0.1595955824335415, 0.14753475956469295, 0.15972602432896474, 0.16638432431698255, 0.14970865174457945, 0.1597254036470066, 0.15085598574960066, 0.15061562350071103, 0.16084189009376346, 0.1711837249783019, 0.15638663062985456, 0.14468740219506868, 0.16691602791878954, 0.15095269072890152, 0.16880667048501846, 0.15241256793202398, 0.16326657212359902, 0.16235261045298746, 0.17008045533079724, 0.17510135259240558, 0.1682960834616401, 0.1857432828028751, 0.1674150661735411, 0.16196395513714523, 0.16191727647577706, 0.17439502119746936, 0.1613572016315564, 0.16427963526067058, 0.1437949485645752, 0.14505023193682307, 0.15504048519043867, 0.15143828118262523, 0.1854701999331783, 0.20230334464658178, 0.1589602604847931, 0.14593590571843432, 0.1898961481487456, 0.18509488450920075, 0.14810456059607868, 0.15822653229080477, 0.16095209626006532, 0.16305830333054133, 0.15495010518323235, 0.1613522226206439, 0.15890694362822885, 0.20617893535840745, 0.1900877430615602, 0.16778086022499664, 0.166402130202129, 0.15683492216281597, 0.19837994730847291, 0.16763184987473795, 0.16849642821131522, 0.16512991959475398, 0.15447151153070443, 0.1968640017595128, 0.16441808854623136, 0.17360001817119328, 0.16177261411199084, 0.16636833831149644, 0.16369762891292594, 0.15337039998032326, 0.1606852337816176, 0.16625655414494037, 0.15718964494127854, 0.15573027887167815, 0.17266396261860387, 0.19653782027896904, 0.20713474742974058, 0.1835464607039273, 0.15905293831711872, 0.1777482711794229, 0.17496871999387464, 0.1558802252836892, 0.14949915140110745, 0.16266443812325435, 0.15946064627290701, 0.17522445128978006, 0.15776928876572108, 0.16474770810893422, 0.16515620484076046, 0.16212670992934577, 0.1517940602686054, 0.16148400329317952, 0.15818292750565993, 0.18091831545501022, 0.15663624828538655, 0.17041273340554522, 0.165128057319708, 0.17041614834282057, 0.19482511861626708, 0.15747166189471107, 0.14306343025369256], [0.18811908558518164, 0.21934862066327498, 0.19510939109092362, 0.20199901232590353, 0.22088504690011132, 0.19457005030345362, 0.18864037580731047, 0.1998949779592681, 0.1848202341540553, 0.1880914388275318, 0.19599061976594193, 0.2112468406640609, 0.19639583502265281, 0.18334492587618667, 0.18366524353671992, 0.2110376531243332, 0.2045190053957147, 0.18833821063623066, 0.21862683595598273, 0.18948037547724794, 0.1954554031359344, 0.18426963187329304, 0.21652527178910788, 0.1861301438716434, 0.17197580041974989, 0.1866882817708748, 0.19050141185040975, 0.22202675277554054, 0.183735946077554, 0.20695089476014009, 0.1965052498421009, 0.21727182258808228, 0.20537226074138018, 0.18725936485545888, 0.2110014594597231, 0.17718960877763326, 0.219786730809935, 0.20026892552857492, 0.21706150250045161, 0.1848561437314398, 0.18228988365021764, 0.20848733247625115, 0.24481225792843592, 0.17604608673185343, 0.17594777317379942, 0.18438187955470256, 0.1967962384308554, 0.24282414783423062, 0.20092062008327077, 0.19292167189266846, 0.1875971733988719, 0.2187936584094861, 0.21568688244593248, 0.1839977880731962, 0.20393564755596327, 0.18814355116993622, 0.20880103488402263, 0.18844519316798297, 0.19323061727869165, 0.18687253013282112, 0.2380694761950305, 0.18857155131856054, 0.23274177879374583, 0.1835506351501335, 0.20071786641834144, 0.19563424738300625, 0.1915047793587807, 0.21894545874144686, 0.18088862100151665, 0.18377694592140534, 0.2054506135652157, 0.19667462656145687, 0.20759516872388736, 0.19558112827081328, 0.2062451946383479, 0.1881499710091324, 0.18686045062624462, 0.22716578616469815, 0.19322067238682816, 0.19953223038109527, 0.19344906685388277, 0.21176738363544845, 0.19344426143338858, 0.19756744151936861, 0.21890570975749085, 0.18296170932344571, 0.18359437566815842, 0.20040403393326284, 0.2250244269672026, 0.20950670454764708, 0.19278834116775026, 0.20407801333741335, 0.1940827910687393, 0.167995074462947, 0.19995532968480512, 0.21268001996522481, 0.18904035093038812, 0.2040606618612378, 0.19911989370456956, 0.19012533083682398], [0.15827257507729528, 0.15582113551088228, 0.15559392793025878, 0.20239374058904572, 0.13743835483564723, 0.20818507029313266, 0.18493431036923297, 0.16697071520873427, 0.15499209714859133, 0.1749134526125417, 0.14949183712601058, 0.1347274887040455, 0.21793032118482658, 0.17077206096619052, 0.13822357313343286, 0.1400068481258136, 0.19537820231656244, 0.1637504016776044, 0.21200782824583794, 0.16732016434227895, 0.14628094326542487, 0.14633288449435253, 0.17353219591962363, 0.1540949006275829, 0.18903064547081896, 0.13883577426404345, 0.17490376307867375, 0.17371732295507403, 0.2012982890456049, 0.135164569627142, 0.13937496756766665, 0.16654832758340535, 0.15908998146428996, 0.15801955110390903, 0.1329773044384674, 0.16871632194520136, 0.1741987485605136, 0.1444389467613179, 0.16046847039248183, 0.13697185192598516, 0.29381257228895075, 0.15670878203454613, 0.2066972989283294, 0.1441221859962293, 0.2936433572550496, 0.16946974388362326, 0.16660587754021355, 0.1589795825441841, 0.18693053852437608, 0.14002177123084483, 0.1427620091729178, 0.13642241440308345, 0.18902558750393625, 0.133122651248456, 0.18777441591793234, 0.15719478598503545, 0.17096735724675768, 0.17225769752391037, 0.16475106377477913, 0.16569348645969656, 0.1727218175691204, 0.14073708353666411, 0.14823111808136047, 0.14348332761650923, 0.14071030456691916, 0.20975917814393522, 0.1978949487587753, 0.1433398206058781, 0.14701780125731023, 0.14493229046552103, 0.1429478566974774, 0.15885490272572123, 0.15102188321054416, 0.16326340845000845, 0.14409286004764996, 0.23230357189168568, 0.1402564305803771, 0.15723135769532415, 0.1647395684115326, 0.1816716247914323, 0.1802294355872763, 0.16147569020320576, 0.17891811872381375, 0.1954627802811629, 0.14461955469985172, 0.14209663109079504, 0.14319440186007615, 0.1735984254033426, 0.18126496400954295, 0.18617884494849374, 0.20885213879460998, 0.1685752430244811, 0.1884629472976591, 0.18101873479529546, 0.21191991184213513, 0.1510864101460429, 0.14463154470267608, 0.15100180125708915, 0.18003068417388635, 0.18450409234789622], [0.19263272104007997, 0.14100710750742584, 0.14407029338073232, 0.1682440880750341, 0.16387620113386192, 0.13878197805810727, 0.1340086266643323, 0.1373052697627711, 0.1382017455657353, 0.20421473594720624, 0.13980272263690643, 0.19206437288830105, 0.2817464463639736, 0.1413458520970173, 0.19031046867053003, 0.1804596028474243, 0.16791767699934454, 0.1388888804912433, 0.179038756604695, 0.13993756801613108, 0.1448179722323464, 0.1722392148016903, 0.19277383151751437, 0.1376985653049388, 0.14551524954396475, 0.13332366419437722, 0.17022903525040048, 0.16697807262856426, 0.18428281426933105, 0.143742501316644, 0.14746930371177291, 0.16688853488255792, 0.13960881277544576, 0.1459550285485862, 0.13349547108599527, 0.14108609382926948, 0.17168230516685007, 0.14340940722485312, 0.13397529972175173, 0.14321219096062815, 0.23517895232938488, 0.14142332457196646, 0.13950269965068288, 0.2425009168725944, 0.2918700343430081, 0.135343230655926, 0.18581311226584254, 0.13553834406366794, 0.1416049410248834, 0.13744530201112576, 0.13506005731575527, 0.18408159284028439, 0.21534102657950407, 0.14378145462660025, 0.17408065150838942, 0.14395829317921513, 0.14149810944905197, 0.1463693545956684, 0.1905600510479834, 0.1924226360234655, 0.1341140498912619, 0.1384883150658107, 0.15963800665167985, 0.14327704915869494, 0.13649155377093636, 0.13671628486718526, 0.16261198901129365, 0.18124573220115456, 0.1495324082863124, 0.18553816470914378, 0.14270918157346374, 0.14370186833369114, 0.17578649073012947, 0.16275475144200818, 0.13514783781218534, 0.1802117249748641, 0.14466751418402238, 0.17316518675538725, 0.13790059064639007, 0.17835782700918498, 0.14695323723064782, 0.14002262868082146, 0.1697708648732214, 0.1951583827169044, 0.13724547964199718, 0.13528916216086645, 0.17414800842275782, 0.1430114581483038, 0.1421848534237272, 0.14002973471219923, 0.18919812802445066, 0.15934151199906063, 0.16610785047874965, 0.14536349384756642, 0.18964478210377825, 0.15365322419369917, 0.15769508095641097, 0.17030517813398593, 0.12982198892592878, 0.15177372485459611]] 
    lossvec0 = [[0.20818351333430446, 0.19981285653588504, 0.20510718595284982, 0.20984635247607544, 0.2034003249549822, 0.21024687557633845, 0.21078277725917077, 0.20653370198423912, 0.21013932241578603, 0.20505582112496656, 0.19698161102331044, 0.19550270268205727, 0.20498398521223687, 0.2004045472147817, 0.1938799390627333, 0.21772568431732175, 0.2083464340948261, 0.21312427103457943, 0.20674441400411894, 0.20197090673753015, 0.19674417388980864, 0.20320873715142776, 0.20001795522201402, 0.19731847013024467, 0.19853312040101412, 0.20129907350618043, 0.20838641921522089, 0.19830498772912775, 0.19879061907507514, 0.2035717258104826, 0.2071246318183616, 0.19911613689133936, 0.20837133964626825, 0.20733400082767026, 0.1996090026481862, 0.21174315412005834, 0.20255750876325515, 0.20502087246770231, 0.20067829356497618, 0.19911627064069187, 0.20702832251436945, 0.19062101256686145, 0.20061988655929894, 0.20834205780624665, 0.2084570714048183, 0.20801329073256525, 0.1997740355226297, 0.20237710448742754, 0.2006843667433806, 0.18904631172160938, 0.18869161011054442, 0.20306350078420582, 0.20086275950573393, 0.19911989150292886, 0.20728355930120665, 0.20825225333936473, 0.20277188661312381, 0.19901486402762184, 0.19576125972752062, 0.2003416781983626, 0.20685900926340084, 0.20535431418632566, 0.20014654589662578, 0.19353750842864006, 0.20862085650120285, 0.19620696021568787, 0.2171938959481364, 0.20043573679795187, 0.20652926543952865, 0.21575306577144276, 0.20894506769395718, 0.21674504563265906, 0.19200237127934186, 0.192631343530857, 0.20276170950880298, 0.20117767984285972, 0.20228917232107702, 0.19913795365197445, 0.2053118917034573, 0.2041415103259663, 0.1988746636985184, 0.2060420797280611, 0.2156591816397663, 0.2051412500684295, 0.19190375324465064, 0.21039661234083334, 0.20799739772136383, 0.20549524103215222, 0.21305080974941387, 0.2058906120337652, 0.2089697343776439, 0.19586999330899366, 0.19757790116004362, 0.21739047753762414, 0.20433306212483993, 0.19943430194574346, 0.2024540919495018, 0.2032482493316871, 0.1982019813597425, 0.2090213243106029]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### underEstWt=1., CHECK RISK, m=0.9 ###
    # Get null first
    underWt, mRisk = 1., 0.9
    t = 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Check', 'threshold': t, 'slope': mRisk}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_check, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Design 0']
    lossveclist = [[0.16597802897111774, 0.15996095375166333, 0.16315377449905738, 0.16709385471740032, 0.16223604504081496, 0.16787038260289883, 0.17025544510198098, 0.163791476432921, 0.16848099488742213, 0.16489627171671106, 0.15760044389575256, 0.15785115369417924, 0.16408198061074042, 0.1598533599278423, 0.15449585943582206, 0.1750598465754737, 0.16614576393745734, 0.16923773527880995, 0.16460620608384577, 0.16190115822727313, 0.15810967664973408, 0.16407909022751818, 0.16026045986764553, 0.15765819153661284, 0.15897563984076873, 0.15975324878659747, 0.1667928400485794, 0.15693699393495145, 0.15941638077253348, 0.1633059031227892, 0.16506569680911848, 0.15991943760302568, 0.16653397794919153, 0.16761769734952817, 0.15862461424004679, 0.16947981397398293, 0.1625175216067931, 0.1642963883159985, 0.1598249118580695, 0.1594821232720838, 0.1663844647792147, 0.151702282305509, 0.16007801184471343, 0.16615560545935965, 0.16747507093841507, 0.1672319351687157, 0.15921699224837965, 0.16144441718727978, 0.16033715326933085, 0.15078390444450038, 0.15043391888197627, 0.16302757251578356, 0.16029584026190669, 0.1606699655143099, 0.16479478158829503, 0.166972897028503, 0.16130367226115588, 0.1589918137109038, 0.1569504494376272, 0.160453788776047, 0.16700743290429812, 0.16405886593323754, 0.16047754170841802, 0.15585029514997822, 0.16752203321332865, 0.15686204768628875, 0.17275253549891784, 0.16140880214989634, 0.16487712914500727, 0.17292740158524705, 0.16790366017474928, 0.17440135689111055, 0.15259069457765256, 0.1560716053293768, 0.16169115849672036, 0.16223075560693828, 0.16239045097898486, 0.1589526036845048, 0.1645686342139668, 0.16352139277796754, 0.15890470106178106, 0.1646775573214811, 0.17278154067224977, 0.16370760674595625, 0.15374220454906015, 0.16732212872716812, 0.16599996075324752, 0.16445547169184174, 0.16966023074880957, 0.1652197324988904, 0.16712485049710307, 0.15751336856591852, 0.15837324173878412, 0.17393491820691703, 0.16245030209982433, 0.1599659017727201, 0.16267526761494608, 0.1620845605509126, 0.159355672994947, 0.1683375276733328]]
    '''
    # 30 tests for all designs
    underWt, mRisk = 1., 0.9
    t = 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Check', 'threshold': t, 'slope': mRisk}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_check, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3, design4, design5, design6_30]
    designNames = ['Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    plotLossVecs(lossveclist, lvecnames=designNames)
    '''
    # LOSS VECS: 10-AUG-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3', 'Design 4', 'Design 5', 'Design 6']
    lossveclist = [[0.1316259081405389, 0.12241469619824905, 0.13595975675152286, 0.1391606376565047, 0.13003734929434396, 0.14450026817222575, 0.12206542321118974, 0.14670344406630845, 0.12953678340854882, 0.12048178898274628, 0.1289335615204511, 0.12071956427464588, 0.11816935380385059, 0.1360536061926024, 0.13775793978387588, 0.15283082143804855, 0.1265269458483293, 0.12593213115885876, 0.11774812074555613, 0.13914598397182232, 0.1379352516009799, 0.13131782032313274, 0.12840137576052144, 0.12463120017110187, 0.15143423547183762, 0.12276596361755064, 0.19959093434531242, 0.13122400672371914, 0.15689856016652023, 0.11976787329665463, 0.12164767165406896, 0.11728691950610347, 0.1259844498198805, 0.13885852956313638, 0.12009514168769946, 0.12954607883296182, 0.1411473261993964, 0.12682193845340567, 0.13345516070695, 0.13905207867225555, 0.20620062195092703, 0.1291868451813161, 0.14259228025462586, 0.14254155316383857, 0.13420701143028071, 0.120556215639047, 0.13227692501563953, 0.12059426073764878, 0.13834209544127352, 0.14647709918603352, 0.12386513383515489, 0.12620709931540525, 0.13254373905772326, 0.13985050065853352, 0.1473386703805468, 0.14235052253294236, 0.13280443907013811, 0.12303633402247593, 0.14037974844197074, 0.13142228123733254, 0.1204610222475023, 0.13767185665114476, 0.17926856366970062, 0.1311229872014409, 0.1484118221134304, 0.1271558138483244, 0.12878896880378787, 0.12770152208877605, 0.15523230170204125, 0.12096466840153444, 0.1323227794786257, 0.1296257359457382, 0.16233646610309896, 0.1277742411018091, 0.1460598316192438, 0.18401080103304535, 0.1419123206550052, 0.13027144906048035, 0.12590564845608904, 0.1517556727865302, 0.13995532118360005, 0.1374436014610329, 0.12991407822077017, 0.13033392693802331, 0.13559070396563627, 0.12400729511254578, 0.16993539013380818, 0.16864361770318548, 0.13382205324217478, 0.14826082147816874, 0.13062199763331914, 0.1355075523260727, 0.15404125276397473, 0.13752029371227115, 0.12357225864953962, 0.12734271212761814, 0.16616348682790988, 0.1750873240830171, 0.12697828802646685, 0.12338885019620685], [0.10903790890103747, 0.11679914187891981, 0.1202501963158447, 0.17016590323032094, 0.13339703911700854, 0.1391489546913259, 0.1193188380403039, 0.1174693662626131, 0.12274286046052152, 0.14909193878515484, 0.11913734989707696, 0.1015197515821045, 0.1345700376998718, 0.12394253140263232, 0.14835613362544778, 0.14511069816205857, 0.11225139627496668, 0.10170566526177287, 0.12283183522660492, 0.13419382798483406, 0.11721366010831194, 0.18523174536304887, 0.15067947103049836, 0.10688090073575604, 0.11607341913886886, 0.1830056986550466, 0.1470930323779514, 0.148213148377557, 0.16199542537662945, 0.11637623831959037, 0.13876387083354452, 0.11033493816715502, 0.13276851669464879, 0.11557096131567757, 0.11053575066045807, 0.14255260253954566, 0.11849615246497665, 0.1176019056403865, 0.13853200086551815, 0.12208866692676594, 0.1696972158425766, 0.10955604006325538, 0.11435208530068997, 0.152565667127096, 0.16966741535667715, 0.1058275194090969, 0.16074268925429683, 0.14288078892516143, 0.1607509490432518, 0.1425198552998309, 0.11334458392244447, 0.11491059651330389, 0.1595052134817906, 0.14418992244742465, 0.13426335590254007, 0.15400838439857653, 0.11756627770067554, 0.1305679853677264, 0.1631104773432233, 0.13144637151466204, 0.11968764949453542, 0.10962289966488774, 0.11526319191802181, 0.11740593973153288, 0.13800616925462156, 0.12725319046191633, 0.16237617238989405, 0.13686328300590758, 0.11819820733668898, 0.1079943387177205, 0.13995588458329097, 0.11643487816512088, 0.14529101150033788, 0.12098588886921799, 0.20248142572218109, 0.16515045838993453, 0.13917622920812578, 0.14954619196210983, 0.11942874882740481, 0.1606102720834637, 0.13587326622624316, 0.11539001808925338, 0.10642752321894096, 0.15319054480668273, 0.12014287458967303, 0.10910148745302882, 0.12282600834547076, 0.12281763987470978, 0.11457149494725866, 0.17075591302803136, 0.18385586288152955, 0.11661473334202269, 0.17484327157415508, 0.11891194654727842, 0.11362279564357838, 0.11570434833803948, 0.12676725228785357, 0.14075696331166915, 0.13816995635834817, 0.10584963874007289], [0.11934589636695833, 0.15106543581539977, 0.15024648937544743, 0.1555301175640814, 0.13312055504426926, 0.11647017573730405, 0.13770240373978718, 0.13254331585546072, 0.11529046674971083, 0.12816808562893886, 0.13399669178460072, 0.1162818176679848, 0.1256856525757671, 0.12751375203612836, 0.12801178205236932, 0.1363705740525829, 0.14210567783521177, 0.12456790364797639, 0.11273703901922887, 0.13969982163507672, 0.1241314413220568, 0.14477810548081538, 0.11829994886496407, 0.12702567531698583, 0.1344691635603848, 0.13858789213497416, 0.14795452884213015, 0.14322313157436228, 0.16069798363783705, 0.13342509703610267, 0.1273440456464081, 0.12858934664511804, 0.15023543504671302, 0.13556354858810643, 0.13151531277141804, 0.1197387809696714, 0.12404970042833934, 0.12913854121205648, 0.1205197197467309, 0.15987060831008915, 0.17962869721502994, 0.13225744589253643, 0.11853057809109632, 0.1524666650811845, 0.15706333827980476, 0.11929203558465865, 0.12715910569520625, 0.13112050929709057, 0.13339563491998427, 0.12372312046133303, 0.12252026496700345, 0.1290720189754229, 0.1735849972333422, 0.1602087101267603, 0.1428049645645243, 0.12837265249844526, 0.12923058121485095, 0.16108805820756142, 0.1360891911896802, 0.13250560253394916, 0.13581768479147588, 0.1294677602416416, 0.16719187697011412, 0.1340542640164839, 0.14326673712513877, 0.13288276465819973, 0.14219420488981005, 0.14020392756958433, 0.12908419978910948, 0.13134350780319654, 0.1392969316996172, 0.13611350869066327, 0.13822326430529006, 0.145296810948529, 0.16966065274457234, 0.18297764585858142, 0.1494188118076114, 0.13005450845762148, 0.1483750432228933, 0.15002141805030425, 0.12476705202200712, 0.12138964642968184, 0.1303562156355201, 0.13089107627280805, 0.14860956375678394, 0.1220691287169845, 0.13961768994410614, 0.14205966010745563, 0.13301216416399117, 0.12435112022358435, 0.1279674732146207, 0.12925654787513532, 0.16018489576551387, 0.13259129516942728, 0.13786854610551563, 0.13673091965278455, 0.1438457936182639, 0.16630124139689595, 0.12397917759614807, 0.11838100901752564], [0.14740309944751787, 0.17799562389842324, 0.1553224592896402, 0.16171796045466488, 0.17604844043333034, 0.15505112559257894, 0.14890372831736398, 0.15858915048026082, 0.14576779891538655, 0.14842133071950508, 0.1552180102061238, 0.16813380602020056, 0.15558023097251925, 0.14462210868354503, 0.14503527479177236, 0.16944027566211076, 0.16430021515669643, 0.14922947092345284, 0.1797144699366921, 0.1496493065535918, 0.155626986732515, 0.14654585219009378, 0.17558079021184647, 0.14680951466852765, 0.13439098731087448, 0.14688823425521882, 0.14938972206257642, 0.17805177692144192, 0.14507642918987418, 0.16411062577423396, 0.15877588364530043, 0.17757836150117726, 0.16269920848996672, 0.1479374928744562, 0.1700221269456827, 0.14054480720089157, 0.17760642338039076, 0.16151959132920776, 0.17507157462399878, 0.14661540849640586, 0.1426184605669872, 0.168297262721314, 0.20039714470767392, 0.13890624537023438, 0.13948910878447598, 0.1445958639971635, 0.15441151006876286, 0.19771448490337806, 0.1596742090662715, 0.1530253270933004, 0.14725158300476962, 0.17718407248038912, 0.17127601160017572, 0.1461646952941327, 0.1639649145398182, 0.1490762639060838, 0.16895109913488462, 0.14867588560553294, 0.1531465806115723, 0.1471645873709389, 0.19347540967810264, 0.14904269550363497, 0.18889436994045647, 0.14455939765699571, 0.15883809594438464, 0.15496891099426044, 0.15144599040147202, 0.17686332393832827, 0.14188825549631867, 0.14533616193803217, 0.16476484967614358, 0.15713776160902568, 0.1661212555462443, 0.1568962844719248, 0.16614484846872057, 0.15082570525258937, 0.148033297905117, 0.1854732102873875, 0.1532159100075933, 0.15954472081437288, 0.15407543282963973, 0.17079721040227555, 0.1515763498493144, 0.15652054314518463, 0.1778557499071949, 0.1441136772494537, 0.14411899719137727, 0.15970252916419037, 0.18155840137802656, 0.17077230711374966, 0.1529781373448898, 0.16219508624168125, 0.15373935931877486, 0.13309600962861126, 0.15828572250864642, 0.17139813375310783, 0.14939786150005208, 0.16431518470385958, 0.15895047116671554, 0.14975528189209947], [0.12488676978727421, 0.12178191619057677, 0.12673223704191564, 0.16747809077777256, 0.11097347036131253, 0.17409807796206758, 0.14487061983560443, 0.13948756180890048, 0.11801318195029811, 0.13651056424039476, 0.11785172263724829, 0.1029125689103356, 0.17048089877927203, 0.1385498079297023, 0.10997707090241984, 0.1220370054962243, 0.16391185183463444, 0.12722604314145872, 0.16469166483824618, 0.13760036218304414, 0.12491250925362911, 0.11448126722934143, 0.14451062197135991, 0.11740632048808355, 0.15818461171241183, 0.10706916875823648, 0.14906594683429264, 0.13587903556737163, 0.16795269753369627, 0.10737708684335319, 0.10959581907749097, 0.1341862223012829, 0.13186967810732128, 0.1330521830394183, 0.09834947307949754, 0.1364929076584685, 0.14355507116156085, 0.11378689393001559, 0.13175714243100306, 0.10816440864962508, 0.23906207711366906, 0.12921817680311923, 0.17797861106103827, 0.11755915864802373, 0.23663248401531273, 0.13398685504021907, 0.13859146754756443, 0.13442562644644693, 0.1511388285975989, 0.1143197073591347, 0.11057129202698344, 0.1146128431926649, 0.15622013719016398, 0.109150925601927, 0.15988524478632007, 0.12920898632335062, 0.13885120950018318, 0.14522478256358493, 0.13375401202549975, 0.13341251372887997, 0.14155884210947803, 0.1156730423097772, 0.1218706518214402, 0.11135727548666094, 0.12086031343518344, 0.17438571094447158, 0.16771693402080556, 0.11108607364940637, 0.12064988548013315, 0.11529003555166142, 0.11408581625640295, 0.1320449864294479, 0.12472159450971707, 0.13452356773730004, 0.11749014221801982, 0.19485532150504767, 0.11087932267367875, 0.1253035792699246, 0.1416414891303947, 0.15182360097156658, 0.14517598140736415, 0.13221544578509703, 0.14304166187852319, 0.15348007705266112, 0.11579762122614516, 0.11032673672005865, 0.11683888627046861, 0.1462202663398809, 0.14758414635206502, 0.150041479755863, 0.16905672741213987, 0.13564967034411246, 0.1615667253067127, 0.15298182571453003, 0.1691787021501899, 0.1294934682338705, 0.11585839364707144, 0.13009520073256006, 0.1456376096532226, 0.1469661968491979], [0.1520893312262227, 0.11100480755415487, 0.12232838038324184, 0.14231991396851598, 0.13292575952673386, 0.11488164950684045, 0.10714279658756636, 0.11003937672348797, 0.10656291933587075, 0.16588111365357167, 0.10919428502356072, 0.1499839753513018, 0.22305300365811004, 0.1146994759618664, 0.15964264219358412, 0.15475984766555254, 0.13753288347857265, 0.11034675817373536, 0.1401331860459149, 0.11384244395125219, 0.12355366203349147, 0.14401699822312858, 0.15221363309030106, 0.10493441140982818, 0.12357230548872852, 0.09933192942260209, 0.1431960587365649, 0.13572399406035396, 0.15669013575531457, 0.11097186747618355, 0.11511126127218088, 0.13729123736532475, 0.11695852379612937, 0.11396179377858537, 0.0995787532016013, 0.1155810736907562, 0.13900802475540758, 0.11827212450559303, 0.1103244471135246, 0.12035998290337442, 0.20242374430644675, 0.11959198930433684, 0.11016583662831285, 0.19742433325381056, 0.24121797100482764, 0.09927642969385418, 0.15139471713100017, 0.11330693939110772, 0.11162626653782069, 0.11142171224645966, 0.10611576636337017, 0.15030704620610152, 0.17161375083745037, 0.1233802763254865, 0.14878113295166143, 0.11351119441942964, 0.11697561617891812, 0.12025319328009942, 0.15171515329207097, 0.15118703698871275, 0.10805450795241628, 0.11186238170238089, 0.1370896260262204, 0.1123192125524258, 0.11308970466411895, 0.10928150054664601, 0.13683453649373628, 0.15111947648986468, 0.12618714208206616, 0.15257089564237658, 0.1187599211217835, 0.1206345017658549, 0.14675276020469777, 0.13334649612359206, 0.11457397303046728, 0.15703775999452607, 0.11831546847814468, 0.14138353137976306, 0.11191905874965248, 0.14763172703445449, 0.11966249405211311, 0.11774148471189422, 0.13431737180038353, 0.15440617741887938, 0.11770529329273297, 0.10289955869718914, 0.14844751315248123, 0.11780062053233492, 0.11116939423996174, 0.11262016610121144, 0.16016303929380873, 0.1239767533309162, 0.14646284145204583, 0.12189566497635329, 0.15161634048323808, 0.12780398624467254, 0.13281489356359988, 0.14448897011620165, 0.09774258893302955, 0.12854513935665182]]
    lossvec0 = [[0.16597802897111774, 0.15996095375166333, 0.16315377449905738, 0.16709385471740032, 0.16223604504081496, 0.16787038260289883, 0.17025544510198098, 0.163791476432921, 0.16848099488742213, 0.16489627171671106, 0.15760044389575256, 0.15785115369417924, 0.16408198061074042, 0.1598533599278423, 0.15449585943582206, 0.1750598465754737, 0.16614576393745734, 0.16923773527880995, 0.16460620608384577, 0.16190115822727313, 0.15810967664973408, 0.16407909022751818, 0.16026045986764553, 0.15765819153661284, 0.15897563984076873, 0.15975324878659747, 0.1667928400485794, 0.15693699393495145, 0.15941638077253348, 0.1633059031227892, 0.16506569680911848, 0.15991943760302568, 0.16653397794919153, 0.16761769734952817, 0.15862461424004679, 0.16947981397398293, 0.1625175216067931, 0.1642963883159985, 0.1598249118580695, 0.1594821232720838, 0.1663844647792147, 0.151702282305509, 0.16007801184471343, 0.16615560545935965, 0.16747507093841507, 0.1672319351687157, 0.15921699224837965, 0.16144441718727978, 0.16033715326933085, 0.15078390444450038, 0.15043391888197627, 0.16302757251578356, 0.16029584026190669, 0.1606699655143099, 0.16479478158829503, 0.166972897028503, 0.16130367226115588, 0.1589918137109038, 0.1569504494376272, 0.160453788776047, 0.16700743290429812, 0.16405886593323754, 0.16047754170841802, 0.15585029514997822, 0.16752203321332865, 0.15686204768628875, 0.17275253549891784, 0.16140880214989634, 0.16487712914500727, 0.17292740158524705, 0.16790366017474928, 0.17440135689111055, 0.15259069457765256, 0.1560716053293768, 0.16169115849672036, 0.16223075560693828, 0.16239045097898486, 0.1589526036845048, 0.1645686342139668, 0.16352139277796754, 0.15890470106178106, 0.1646775573214811, 0.17278154067224977, 0.16370760674595625, 0.15374220454906015, 0.16732212872716812, 0.16599996075324752, 0.16445547169184174, 0.16966023074880957, 0.1652197324988904, 0.16712485049710307, 0.15751336856591852, 0.15837324173878412, 0.17393491820691703, 0.16245030209982433, 0.1599659017727201, 0.16267526761494608, 0.1620845605509126, 0.159355672994947, 0.1683375276733328]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.4$, $n=30$')

    lossveclist = [[0.1316259081405389, 0.12241469619824905, 0.13595975675152286, 0.1391606376565047, 0.13003734929434396, 0.14450026817222575, 0.12206542321118974, 0.14670344406630845, 0.12953678340854882, 0.12048178898274628, 0.1289335615204511, 0.12071956427464588, 0.11816935380385059, 0.1360536061926024, 0.13775793978387588, 0.15283082143804855, 0.1265269458483293, 0.12593213115885876, 0.11774812074555613, 0.13914598397182232, 0.1379352516009799, 0.13131782032313274, 0.12840137576052144, 0.12463120017110187, 0.15143423547183762, 0.12276596361755064, 0.19959093434531242, 0.13122400672371914, 0.15689856016652023, 0.11976787329665463, 0.12164767165406896, 0.11728691950610347, 0.1259844498198805, 0.13885852956313638, 0.12009514168769946, 0.12954607883296182, 0.1411473261993964, 0.12682193845340567, 0.13345516070695, 0.13905207867225555, 0.20620062195092703, 0.1291868451813161, 0.14259228025462586, 0.14254155316383857, 0.13420701143028071, 0.120556215639047, 0.13227692501563953, 0.12059426073764878, 0.13834209544127352, 0.14647709918603352, 0.12386513383515489, 0.12620709931540525, 0.13254373905772326, 0.13985050065853352, 0.1473386703805468, 0.14235052253294236, 0.13280443907013811, 0.12303633402247593, 0.14037974844197074, 0.13142228123733254, 0.1204610222475023, 0.13767185665114476, 0.17926856366970062, 0.1311229872014409, 0.1484118221134304, 0.1271558138483244, 0.12878896880378787, 0.12770152208877605, 0.15523230170204125, 0.12096466840153444, 0.1323227794786257, 0.1296257359457382, 0.16233646610309896, 0.1277742411018091, 0.1460598316192438, 0.18401080103304535, 0.1419123206550052, 0.13027144906048035, 0.12590564845608904, 0.1517556727865302, 0.13995532118360005, 0.1374436014610329, 0.12991407822077017, 0.13033392693802331, 0.13559070396563627, 0.12400729511254578, 0.16993539013380818, 0.16864361770318548, 0.13382205324217478, 0.14826082147816874, 0.13062199763331914, 0.1355075523260727, 0.15404125276397473, 0.13752029371227115, 0.12357225864953962, 0.12734271212761814, 0.16616348682790988, 0.1750873240830171, 0.12697828802646685, 0.12338885019620685], [0.10903790890103747, 0.11679914187891981, 0.1202501963158447, 0.17016590323032094, 0.13339703911700854, 0.1391489546913259, 0.1193188380403039, 0.1174693662626131, 0.12274286046052152, 0.14909193878515484, 0.11913734989707696, 0.1015197515821045, 0.1345700376998718, 0.12394253140263232, 0.14835613362544778, 0.14511069816205857, 0.11225139627496668, 0.10170566526177287, 0.12283183522660492, 0.13419382798483406, 0.11721366010831194, 0.18523174536304887, 0.15067947103049836, 0.10688090073575604, 0.11607341913886886, 0.1830056986550466, 0.1470930323779514, 0.148213148377557, 0.16199542537662945, 0.11637623831959037, 0.13876387083354452, 0.11033493816715502, 0.13276851669464879, 0.11557096131567757, 0.11053575066045807, 0.14255260253954566, 0.11849615246497665, 0.1176019056403865, 0.13853200086551815, 0.12208866692676594, 0.1696972158425766, 0.10955604006325538, 0.11435208530068997, 0.152565667127096, 0.16966741535667715, 0.1058275194090969, 0.16074268925429683, 0.14288078892516143, 0.1607509490432518, 0.1425198552998309, 0.11334458392244447, 0.11491059651330389, 0.1595052134817906, 0.14418992244742465, 0.13426335590254007, 0.15400838439857653, 0.11756627770067554, 0.1305679853677264, 0.1631104773432233, 0.13144637151466204, 0.11968764949453542, 0.10962289966488774, 0.11526319191802181, 0.11740593973153288, 0.13800616925462156, 0.12725319046191633, 0.16237617238989405, 0.13686328300590758, 0.11819820733668898, 0.1079943387177205, 0.13995588458329097, 0.11643487816512088, 0.14529101150033788, 0.12098588886921799, 0.20248142572218109, 0.16515045838993453, 0.13917622920812578, 0.14954619196210983, 0.11942874882740481, 0.1606102720834637, 0.13587326622624316, 0.11539001808925338, 0.10642752321894096, 0.15319054480668273, 0.12014287458967303, 0.10910148745302882, 0.12282600834547076, 0.12281763987470978, 0.11457149494725866, 0.17075591302803136, 0.18385586288152955, 0.11661473334202269, 0.17484327157415508, 0.11891194654727842, 0.11362279564357838, 0.11570434833803948, 0.12676725228785357, 0.14075696331166915, 0.13816995635834817, 0.10584963874007289], [0.11934589636695833, 0.15106543581539977, 0.15024648937544743, 0.1555301175640814, 0.13312055504426926, 0.11647017573730405, 0.13770240373978718, 0.13254331585546072, 0.11529046674971083, 0.12816808562893886, 0.13399669178460072, 0.1162818176679848, 0.1256856525757671, 0.12751375203612836, 0.12801178205236932, 0.1363705740525829, 0.14210567783521177, 0.12456790364797639, 0.11273703901922887, 0.13969982163507672, 0.1241314413220568, 0.14477810548081538, 0.11829994886496407, 0.12702567531698583, 0.1344691635603848, 0.13858789213497416, 0.14795452884213015, 0.14322313157436228, 0.16069798363783705, 0.13342509703610267, 0.1273440456464081, 0.12858934664511804, 0.15023543504671302, 0.13556354858810643, 0.13151531277141804, 0.1197387809696714, 0.12404970042833934, 0.12913854121205648, 0.1205197197467309, 0.15987060831008915, 0.17962869721502994, 0.13225744589253643, 0.11853057809109632, 0.1524666650811845, 0.15706333827980476, 0.11929203558465865, 0.12715910569520625, 0.13112050929709057, 0.13339563491998427, 0.12372312046133303, 0.12252026496700345, 0.1290720189754229, 0.1735849972333422, 0.1602087101267603, 0.1428049645645243, 0.12837265249844526, 0.12923058121485095, 0.16108805820756142, 0.1360891911896802, 0.13250560253394916, 0.13581768479147588, 0.1294677602416416, 0.16719187697011412, 0.1340542640164839, 0.14326673712513877, 0.13288276465819973, 0.14219420488981005, 0.14020392756958433, 0.12908419978910948, 0.13134350780319654, 0.1392969316996172, 0.13611350869066327, 0.13822326430529006, 0.145296810948529, 0.16966065274457234, 0.18297764585858142, 0.1494188118076114, 0.13005450845762148, 0.1483750432228933, 0.15002141805030425, 0.12476705202200712, 0.12138964642968184, 0.1303562156355201, 0.13089107627280805, 0.14860956375678394, 0.1220691287169845, 0.13961768994410614, 0.14205966010745563, 0.13301216416399117, 0.12435112022358435, 0.1279674732146207, 0.12925654787513532, 0.16018489576551387, 0.13259129516942728, 0.13786854610551563, 0.13673091965278455, 0.1438457936182639, 0.16630124139689595, 0.12397917759614807, 0.11838100901752564], [0.14740309944751787, 0.17799562389842324, 0.1553224592896402, 0.16171796045466488, 0.17604844043333034, 0.15505112559257894, 0.14890372831736398, 0.15858915048026082, 0.14576779891538655, 0.14842133071950508, 0.1552180102061238, 0.16813380602020056, 0.15558023097251925, 0.14462210868354503, 0.14503527479177236, 0.16944027566211076, 0.16430021515669643, 0.14922947092345284, 0.1797144699366921, 0.1496493065535918, 0.155626986732515, 0.14654585219009378, 0.17558079021184647, 0.14680951466852765, 0.13439098731087448, 0.14688823425521882, 0.14938972206257642, 0.17805177692144192, 0.14507642918987418, 0.16411062577423396, 0.15877588364530043, 0.17757836150117726, 0.16269920848996672, 0.1479374928744562, 0.1700221269456827, 0.14054480720089157, 0.17760642338039076, 0.16151959132920776, 0.17507157462399878, 0.14661540849640586, 0.1426184605669872, 0.168297262721314, 0.20039714470767392, 0.13890624537023438, 0.13948910878447598, 0.1445958639971635, 0.15441151006876286, 0.19771448490337806, 0.1596742090662715, 0.1530253270933004, 0.14725158300476962, 0.17718407248038912, 0.17127601160017572, 0.1461646952941327, 0.1639649145398182, 0.1490762639060838, 0.16895109913488462, 0.14867588560553294, 0.1531465806115723, 0.1471645873709389, 0.19347540967810264, 0.14904269550363497, 0.18889436994045647, 0.14455939765699571, 0.15883809594438464, 0.15496891099426044, 0.15144599040147202, 0.17686332393832827, 0.14188825549631867, 0.14533616193803217, 0.16476484967614358, 0.15713776160902568, 0.1661212555462443, 0.1568962844719248, 0.16614484846872057, 0.15082570525258937, 0.148033297905117, 0.1854732102873875, 0.1532159100075933, 0.15954472081437288, 0.15407543282963973, 0.17079721040227555, 0.1515763498493144, 0.15652054314518463, 0.1778557499071949, 0.1441136772494537, 0.14411899719137727, 0.15970252916419037, 0.18155840137802656, 0.17077230711374966, 0.1529781373448898, 0.16219508624168125, 0.15373935931877486, 0.13309600962861126, 0.15828572250864642, 0.17139813375310783, 0.14939786150005208, 0.16431518470385958, 0.15895047116671554, 0.14975528189209947], [0.12488676978727421, 0.12178191619057677, 0.12673223704191564, 0.16747809077777256, 0.11097347036131253, 0.17409807796206758, 0.14487061983560443, 0.13948756180890048, 0.11801318195029811, 0.13651056424039476, 0.11785172263724829, 0.1029125689103356, 0.17048089877927203, 0.1385498079297023, 0.10997707090241984, 0.1220370054962243, 0.16391185183463444, 0.12722604314145872, 0.16469166483824618, 0.13760036218304414, 0.12491250925362911, 0.11448126722934143, 0.14451062197135991, 0.11740632048808355, 0.15818461171241183, 0.10706916875823648, 0.14906594683429264, 0.13587903556737163, 0.16795269753369627, 0.10737708684335319, 0.10959581907749097, 0.1341862223012829, 0.13186967810732128, 0.1330521830394183, 0.09834947307949754, 0.1364929076584685, 0.14355507116156085, 0.11378689393001559, 0.13175714243100306, 0.10816440864962508, 0.23906207711366906, 0.12921817680311923, 0.17797861106103827, 0.11755915864802373, 0.23663248401531273, 0.13398685504021907, 0.13859146754756443, 0.13442562644644693, 0.1511388285975989, 0.1143197073591347, 0.11057129202698344, 0.1146128431926649, 0.15622013719016398, 0.109150925601927, 0.15988524478632007, 0.12920898632335062, 0.13885120950018318, 0.14522478256358493, 0.13375401202549975, 0.13341251372887997, 0.14155884210947803, 0.1156730423097772, 0.1218706518214402, 0.11135727548666094, 0.12086031343518344, 0.17438571094447158, 0.16771693402080556, 0.11108607364940637, 0.12064988548013315, 0.11529003555166142, 0.11408581625640295, 0.1320449864294479, 0.12472159450971707, 0.13452356773730004, 0.11749014221801982, 0.19485532150504767, 0.11087932267367875, 0.1253035792699246, 0.1416414891303947, 0.15182360097156658, 0.14517598140736415, 0.13221544578509703, 0.14304166187852319, 0.15348007705266112, 0.11579762122614516, 0.11032673672005865, 0.11683888627046861, 0.1462202663398809, 0.14758414635206502, 0.150041479755863, 0.16905672741213987, 0.13564967034411246, 0.1615667253067127, 0.15298182571453003, 0.1691787021501899, 0.1294934682338705, 0.11585839364707144, 0.13009520073256006, 0.1456376096532226, 0.1469661968491979], [0.1520893312262227, 0.11100480755415487, 0.12232838038324184, 0.14231991396851598, 0.13292575952673386, 0.11488164950684045, 0.10714279658756636, 0.11003937672348797, 0.10656291933587075, 0.16588111365357167, 0.10919428502356072, 0.1499839753513018, 0.22305300365811004, 0.1146994759618664, 0.15964264219358412, 0.15475984766555254, 0.13753288347857265, 0.11034675817373536, 0.1401331860459149, 0.11384244395125219, 0.12355366203349147, 0.14401699822312858, 0.15221363309030106, 0.10493441140982818, 0.12357230548872852, 0.09933192942260209, 0.1431960587365649, 0.13572399406035396, 0.15669013575531457, 0.11097186747618355, 0.11511126127218088, 0.13729123736532475, 0.11695852379612937, 0.11396179377858537, 0.0995787532016013, 0.1155810736907562, 0.13900802475540758, 0.11827212450559303, 0.1103244471135246, 0.12035998290337442, 0.20242374430644675, 0.11959198930433684, 0.11016583662831285, 0.19742433325381056, 0.24121797100482764, 0.09927642969385418, 0.15139471713100017, 0.11330693939110772, 0.11162626653782069, 0.11142171224645966, 0.10611576636337017, 0.15030704620610152, 0.17161375083745037, 0.1233802763254865, 0.14878113295166143, 0.11351119441942964, 0.11697561617891812, 0.12025319328009942, 0.15171515329207097, 0.15118703698871275, 0.10805450795241628, 0.11186238170238089, 0.1370896260262204, 0.1123192125524258, 0.11308970466411895, 0.10928150054664601, 0.13683453649373628, 0.15111947648986468, 0.12618714208206616, 0.15257089564237658, 0.1187599211217835, 0.1206345017658549, 0.14675276020469777, 0.13334649612359206, 0.11457397303046728, 0.15703775999452607, 0.11831546847814468, 0.14138353137976306, 0.11191905874965248, 0.14763172703445449, 0.11966249405211311, 0.11774148471189422, 0.13431737180038353, 0.15440617741887938, 0.11770529329273297, 0.10289955869718914, 0.14844751315248123, 0.11780062053233492, 0.11116939423996174, 0.11262016610121144, 0.16016303929380873, 0.1239767533309162, 0.14646284145204583, 0.12189566497635329, 0.15161634048323808, 0.12780398624467254, 0.13281489356359988, 0.14448897011620165, 0.09774258893302955, 0.12854513935665182]]
    lossvec0 = [[0.16597802897111774, 0.15996095375166333, 0.16315377449905738, 0.16709385471740032, 0.16223604504081496, 0.16787038260289883, 0.17025544510198098, 0.163791476432921, 0.16848099488742213, 0.16489627171671106, 0.15760044389575256, 0.15785115369417924, 0.16408198061074042, 0.1598533599278423, 0.15449585943582206, 0.1750598465754737, 0.16614576393745734, 0.16923773527880995, 0.16460620608384577, 0.16190115822727313, 0.15810967664973408, 0.16407909022751818, 0.16026045986764553, 0.15765819153661284, 0.15897563984076873, 0.15975324878659747, 0.1667928400485794, 0.15693699393495145, 0.15941638077253348, 0.1633059031227892, 0.16506569680911848, 0.15991943760302568, 0.16653397794919153, 0.16761769734952817, 0.15862461424004679, 0.16947981397398293, 0.1625175216067931, 0.1642963883159985, 0.1598249118580695, 0.1594821232720838, 0.1663844647792147, 0.151702282305509, 0.16007801184471343, 0.16615560545935965, 0.16747507093841507, 0.1672319351687157, 0.15921699224837965, 0.16144441718727978, 0.16033715326933085, 0.15078390444450038, 0.15043391888197627, 0.16302757251578356, 0.16029584026190669, 0.1606699655143099, 0.16479478158829503, 0.166972897028503, 0.16130367226115588, 0.1589918137109038, 0.1569504494376272, 0.160453788776047, 0.16700743290429812, 0.16405886593323754, 0.16047754170841802, 0.15585029514997822, 0.16752203321332865, 0.15686204768628875, 0.17275253549891784, 0.16140880214989634, 0.16487712914500727, 0.17292740158524705, 0.16790366017474928, 0.17440135689111055, 0.15259069457765256, 0.1560716053293768, 0.16169115849672036, 0.16223075560693828, 0.16239045097898486, 0.1589526036845048, 0.1645686342139668, 0.16352139277796754, 0.15890470106178106, 0.1646775573214811, 0.17278154067224977, 0.16370760674595625, 0.15374220454906015, 0.16732212872716812, 0.16599996075324752, 0.16445547169184174, 0.16966023074880957, 0.1652197324988904, 0.16712485049710307, 0.15751336856591852, 0.15837324173878412, 0.17393491820691703, 0.16245030209982433, 0.1599659017727201, 0.16267526761494608, 0.1620845605509126, 0.159355672994947, 0.1683375276733328]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    ### type='node', overEstWt=1., rateTarget=0.1 ###
    design0 = np.array([0., 0.,0.])
    design1 = np.array([0.,0.,1.])
    design2 = np.array([1 / 3, 2 / 3, 0.])
    design3 = np.array([1 / 3 , 1 / 3 , 1 / 3])

    # Build list of 1000 Qest matrices, for use in order with each omega
    import numpy.random as nprandom
    Qlist = []
    obsQ = np.array([[ 6, 11], [12,  6], [ 2, 13]])
    nprandom.seed(3)
    for scenind in range(100):
        newQ = np.array([[0.,0.], [0.,0.], [0.,0.]])
        for btsamp in range(50):
            currTNind = choice([i for i in range(numTN)], p=np.sum(obsQ,axis=1)/np.sum(obsQ).tolist())
            currSNind = choice([i for i in range(numSN)], p=obsQ[currTNind]/np.sum(obsQ[currTNind]).tolist())
            newQ[currTNind][currSNind] += 1
        Qlist.append(newQ)

    # Get null first
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    lossveclist=[]
    for scenind in range(100):
        omeganum = 1
        Qest = Qlist[scenind]
        lossvec = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum,
                                   type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
        lossveclist.append(lossvec[0][0])
        print('Scenario '+str(scenind)+' finished')
    '''
    # LOSS VECS: 13-JUL-22
    designNames = ['Design 0']
    lossvec = [0.019690827482368705, 0.021939295393226917, 0.01973505797597416, 0.01973664917591897, 0.01968596345794661, 0.019213398504037166, 0.0173554009770707, 0.020307317093891084, 0.02100404078163349, 0.01988540052204863, 0.019542829877228923, 0.016952922018571237, 0.018409204853519878, 0.01915838415574564, 0.020463347233881886, 0.020548416542314263, 0.01859793359235008, 0.019750168367845863, 0.019274062607812965, 0.017123479731651244, 0.02231418179797019, 0.018001375139415406, 0.020688635191629463, 0.020348464714217744, 0.01784459744393057, 0.018783776068150005, 0.019766346569503938, 0.01697448900668094, 0.020920248448976494, 0.02027714650356037, 0.019540560666221424, 0.017958955844537012, 0.018934398030163647, 0.02096408370343579, 0.019052007841171413, 0.01843385853068612, 0.020248753976433213, 0.02118099287211507, 0.020796528318689805, 0.01871331797330223, 0.01703766582542569, 0.02052184062342226, 0.018137071374459256, 0.0193246561669277, 0.020621859867252092, 0.02118441841969468, 0.018810592194857492, 0.016426974896474964, 0.0193995604538135, 0.020639886224365304, 0.019174425542286173, 0.01928271826593331, 0.019428407387475595, 0.02213510461847484, 0.019579200264899982, 0.02123914683780319, 0.01764080724931094, 0.019462696268650163, 0.01887625928983492, 0.019913453565555368, 0.01793462599372435, 0.018430775692844424, 0.017429193067063795, 0.018424461736909505, 0.019132647338707544, 0.018660564603294405, 0.01888716686181371, 0.020523937811379855, 0.021889551199100847, 0.018697371066856608, 0.018757125708034745, 0.02039464058774375, 0.019611426790288197, 0.019879845752365486, 0.017007188401399323, 0.019063737705063612, 0.01679687014418244, 0.02172763798350237, 0.020706335545170658, 0.020026728629178002, 0.01764716680163704, 0.019512095378609446, 0.01875937455898344, 0.020495269487834006, 0.019298492618681596, 0.02071439717837558, 0.021019799129079014, 0.016600383619317132, 0.021823016698557535, 0.01899468677805621, 0.02134819146200047, 0.01899564159255357, 0.01705620583234051, 0.019413600551352335, 0.020117187742948402, 0.017717850151776474, 0.019529188350926034, 0.019289146887209063, 0.01808582043163517, 0.020987258386175038]
    '''
    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name': 'Parabolic','threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3]
    designNames = ['Design 1', 'Design 2', 'Design 3']
    numtests = 30
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = [[] for i in range(len(designList))]
    for scenind in range(100):
        omeganum = 1
        Qest = Qlist[scenind]
        lossvec = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                                   designlist=designList, designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
        for i in range(len(designList)):
            lossveclist[i].append(lossvec[i][0])
        print('Scenario ' + str(scenind) + ' finished')
    '''
    # LOSS VECS: 13-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3']
    lossveclist = [[0.019690827482368705, 0.021939295393226917, 0.01973505797597416, 0.01973664917591897, 0.01968596345794661, 0.019213398504037166, 0.0173554009770707, 0.020307317093891084, 0.02100404078163349, 0.01988540052204863, 0.019542829877228923, 0.016952922018571237, 0.018409204853519878, 0.01915838415574564, 0.020463347233881886, 0.020548416542314263, 0.01859793359235008, 0.019750168367845863, 0.019274062607812965, 0.017123479731651244, 0.02231418179797019, 0.018001375139415406, 0.020688635191629463, 0.020348464714217744, 0.01784459744393057, 0.018783776068150005, 0.019766346569503938, 0.01697448900668094, 0.020920248448976494, 0.02027714650356037, 0.019540560666221424, 0.017958955844537012, 0.018934398030163647, 0.02096408370343579, 0.019052007841171413, 0.01843385853068612, 0.020248753976433213, 0.02118099287211507, 0.020796528318689805, 0.01871331797330223, 0.01703766582542569, 0.02052184062342226, 0.018137071374459256, 0.0193246561669277, 0.020621859867252092, 0.02118441841969468, 0.018810592194857492, 0.016426974896474964, 0.0193995604538135, 0.020639886224365304, 0.019174425542286173, 0.01928271826593331, 0.019428407387475595, 0.02213510461847484, 0.019579200264899982, 0.02123914683780319, 0.01764080724931094, 0.019462696268650163, 0.01887625928983492, 0.019913453565555368, 0.01793462599372435, 0.018430775692844424, 0.017429193067063795, 0.018424461736909505, 0.019132647338707544, 0.018660564603294405, 0.01888716686181371, 0.020523937811379855, 0.021889551199100847, 0.018697371066856608, 0.018757125708034745, 0.02039464058774375, 0.019611426790288197, 0.019879845752365486, 0.017007188401399323, 0.019063737705063612, 0.01679687014418244, 0.02172763798350237, 0.020706335545170658, 0.020026728629178002, 0.01764716680163704, 0.019512095378609446, 0.01875937455898344, 0.020495269487834006, 0.019298492618681596, 0.02071439717837558, 0.021019799129079014, 0.016600383619317132, 0.021823016698557535, 0.01899468677805621, 0.02134819146200047, 0.01899564159255357, 0.01705620583234051, 0.019413600551352335, 0.020117187742948402, 0.017717850151776474, 0.019529188350926034, 0.019289146887209063, 0.01808582043163517, 0.020987258386175038],[0.01876424448500989, 0.019384564656693887, 0.01509787098237408, 0.013694675216181685, 0.017389956435886984, 0.012704420649905165, 0.018242285246775052, 0.020752272663022577, 0.01858880421469034, 0.020446479525582997, 0.019294249853589268, 0.013653464247033176, 0.011267115760917818, 0.01693517405986635, 0.012907845922354912, 0.017429362725585235, 0.015844331573185245, 0.015324649217068588, 0.016150297145761022, 0.01781435734063786, 0.012214970093439245, 0.019439008851119717, 0.012858253624878543, 0.018765538645996272, 0.012914447246757497, 0.016290570830811712, 0.01426007567849746, 0.013969564018743424, 0.010247796235196442, 0.01303680965505668, 0.014193311492482465, 0.025394905932146578, 0.021704008165108982, 0.014625771963880771, 0.013156710463277975, 0.012545108706289403, 0.016914047658383828, 0.015036719954726769, 0.01685799223298833, 0.013938347300111821, 0.01714751467665077, 0.01714586705680331, 0.016300831322489943, 0.013179625205647555, 0.013740440845777161, 0.01611418194385282, 0.01551485630479084, 0.01870546699874107, 0.01230072900493055, 0.0146582439501738, 0.019721498655650708, 0.012754706909313561, 0.011439072237978404, 0.01452712815279264, 0.012777643774638154, 0.019224106246886037, 0.013714014569424327, 0.02185906886186993, 0.01819843706464749, 0.015881918599126636, 0.021972994008667635, 0.015067363672198427, 0.01600434644253589, 0.018571428727435252, 0.01720273012011972, 0.01730124089449872, 0.015003054830427026, 0.017872375200267514, 0.015597454241696439, 0.01570247199344865, 0.012490658337290635, 0.022164808651384017, 0.014294575950139127, 0.016710044663770993, 0.012683872551962976, 0.014772212359634836, 0.01579923529134294, 0.014881810746497455, 0.016292720318589467, 0.02097020584235558, 0.01952104158187477, 0.019602366551461105, 0.012278906778802194, 0.014527837739345897, 0.014666909583389152, 0.011874768913586829, 0.018000180297507478, 0.015257928104107052, 0.017466553313903354, 0.013559882937303362, 0.018341167936957805, 0.017442771954143257, 0.015686112730263106, 0.011703805614276395, 0.015078935465773978, 0.009274183597021363, 0.015363822038854807, 0.014828436906667334, 0.015286403754080514, 0.0173350098908816], [0.017338187296437664, 0.011996263999644624, 0.02751223641612406, 0.009010387512394623, 0.025868638679699005, 0.008803425104809132, 0.008093256100748103, 0.00931759811755569, 0.011205877792639807, 0.02076793615628927, 0.010285181618384352, 0.018349023034135218, 0.009126311832662999, 0.015014217491277381, 0.01137912198551673, 0.02027689222280233, 0.011496664298063626, 0.018121758054194113, 0.018264197724710635, 0.014887888254905375, 0.009748430866784813, 0.010907574149092651, 0.01169544756027972, 0.015112762674370448, 0.010192131432322908, 0.008333734279322932, 0.01452408405270779, 0.012207837828970256, 0.008640287303863698, 0.011218199352288342, 0.01179024080735601, 0.009046765835953706, 0.009753420000994278, 0.017423616330200033, 0.01154879966090144, 0.019459331407380518, 0.014491755480771312, 0.018065123274366903, 0.011171532851978267, 0.015037156919469143, 0.009699764666687292, 0.009675376359673561, 0.010760948289288913, 0.009508166375146428, 0.014169926520083866, 0.017941952289261754, 0.009669263667389481, 0.013268567509754437, 0.009776076429206585, 0.020981931581459435, 0.009843584283217766, 0.019476727211225054, 0.008383415674186115, 0.015554280688413736, 0.01430757223957079, 0.015618560971838152, 0.011457503604455289, 0.012123139646838404, 0.021484109113439138, 0.02675154147632687, 0.009628026457367203, 0.015289664722831416, 0.016146971830622376, 0.017624726227379664, 0.012811809601693496, 0.018649988648522835, 0.012766589829927311, 0.016747291853733328, 0.014246326572877041, 0.00885696454590718, 0.01430283772732357, 0.013093524334047944, 0.010592128340754766, 0.01626002338382248, 0.013262995173437984, 0.018635361571380276, 0.011738536977944799, 0.012906106141070009, 0.010237077447872583, 0.01584546645734631, 0.010297389477207266, 0.008737020746101045, 0.01752137959775418, 0.008956315145976529, 0.010500757153621908, 0.01760736158255033, 0.008884879348146415, 0.01115403311192902, 0.014592730941792196, 0.020454860498486695, 0.013486818636060932, 0.011537463880487863, 0.008800055876757354, 0.01892626584488564, 0.009722231827567816, 0.017588269276644444, 0.017547012768838573, 0.022042364035046322, 0.01442299341303058, 0.018031874753422265], [0.010726511131175846, 0.011346178266358486, 0.009935765453330187, 0.016671802003800352, 0.01029361178633009, 0.010016617411115609, 0.013741894561144349, 0.014426699000876522, 0.017801579790693012, 0.009919954277856916, 0.010177945766895714, 0.017909469029406364, 0.010529472739837183, 0.011714454053913744, 0.012009063689859233, 0.02482667879602944, 0.009907852153122721, 0.01054031336225788, 0.020410497606308683, 0.010291031089990405, 0.011084689727429183, 0.011297614391491339, 0.017415926365019773, 0.00953720342304, 0.009396312906268491, 0.009257891443253632, 0.009542154338942458, 0.011188553173732331, 0.011786598063388427, 0.009702612369787447, 0.009820809278506863, 0.010631762347839033, 0.01133128431479471, 0.009973993952658366, 0.01142731227932962, 0.016517937325747467, 0.021254847319722207, 0.011246830862202671, 0.012268817427427666, 0.021844268619966748, 0.011861871642527192, 0.01805768412006595, 0.018332377179823587, 0.020701553326614715, 0.009298295385283227, 0.009793513066421997, 0.016367225158725355, 0.013531447020963596, 0.01242868741001709, 0.010463817351543883, 0.02012119271124337, 0.009630992335981676, 0.018105228637089035, 0.011976594100111263, 0.020406874888652612, 0.014020765217039077, 0.015879119453974584, 0.01143192025945281, 0.019718105852585852, 0.0129412021416814, 0.022318443012363444, 0.010188240695242975, 0.01774465846620202, 0.010295417030511442, 0.00853871051266011, 0.010817386325653813, 0.012618486606296433, 0.0101840620900269, 0.01033948287345778, 0.011082129158028439, 0.010711439287346197, 0.009592235753030837, 0.01040163812437106, 0.010434099684464633, 0.015428232525948004, 0.008279268136252939, 0.012998359728623102, 0.011668849909647646, 0.009547713787598097, 0.013331735625917041, 0.01700919479237819, 0.010081543985628426, 0.014870266953092669, 0.018662907549623346, 0.009113328425683985, 0.014258280099234272, 0.021148331766458733, 0.013604572641377426, 0.012323388429136361, 0.011032202822727077, 0.011213843232019242, 0.009260109370351904, 0.013754992460326214, 0.008845404621579987, 0.010681043191548159, 0.008783620703806923, 0.011392583009988367, 0.010249954522106095, 0.010767601844524332, 0.020199899581506496]]
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$\delta=1$, $t=0.1$, $n=30$, test node selection')    
    '''

    ### type='node', overEstWt=1., rateTarget=0.1, KNOWN Q matrix ###
    design0 = np.array([0., 0., 0.])
    design1 = np.array([0., 0., 1.])
    design2 = np.array([1 / 3, 2 / 3, 0.])
    design3 = np.array([1 / 3, 1 / 3, 1 / 3])

    # Use a "known" Q matrix
    Qest = np.array([[6, 11], [12, 6], [2, 13]])
    Qest = np.divide(Qest,np.sum(Qest,axis=1).reshape(3,1))
    Qest = np.array([[0.4,0.6],[0.7,0.3],[0.1,0.9]])

    # Get null first
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design0]
    designNames = ['Design 0']
    numtests = 0
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)
    omeganum = 100
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                               designlist=designList, designnames=designNames, numtests=numtests,
                               omeganum=omeganum, type=['node', Qest],
                               priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                               randinds=randinds)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Design 0']
    lossvec = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    '''
    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3]
    designNames = ['Design 1', 'Design 2', 'Design 3']
    numtests = 30
    omeganum = 100
    Qest = np.array([[0.4, 0.6], [0.7, 0.3], [0.1, 0.9]])
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    omeganum = 100
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                                   designlist=designList, designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    '''
    # LOSS VECS: 19-JUL-22
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3']
    lossveclist = [[0.11988525924311791, 0.15483094799207342, 0.1691899146741856, 0.16337552836098096, 0.12836809481628542, 0.14669632630179033, 0.11673217672810883, 0.1615678558169811, 0.14639554382295497, 0.16747300564678502, 0.14332538699399622, 0.11989719619532264, 0.13829764143478954, 0.14218326930548772, 0.15349822563502824, 0.16445278397470237, 0.1832089506652259, 0.13108422019561075, 0.11942583281115773, 0.18416029888190413, 0.12522863110501536, 0.14891343846169516, 0.1533842561477168, 0.1487084063006343, 0.13809294312785853, 0.12977698758410572, 0.14713777750637713, 0.137727820322727, 0.1512064422954208, 0.14455987258226444, 0.13096217862331147, 0.1827526286573682, 0.15843136147339795, 0.15422791357276375, 0.1483308941875547, 0.13411321454187758, 0.17483195620159936, 0.13380058106005982, 0.13236207459851054, 0.16723313876854307, 0.1686069465606297, 0.14304460011047676, 0.16278760536818096, 0.17360529815423428, 0.14400894994907246, 0.13902007229591232, 0.14832192151804016, 0.19414412050055052, 0.14785250956885154, 0.1264626890714373, 0.15553236788548055, 0.17223453498510718, 0.14820319125656917, 0.13626641083425303, 0.16703073316735492, 0.15857541812356918, 0.16660503458590611, 0.13670733616977424, 0.16490982512927907, 0.177103678040694, 0.16636407459490846, 0.14087917732914293, 0.1944676077882393, 0.17271469499917236, 0.14763454351603286, 0.1306683596330204, 0.13840285734269553, 0.15312543618855268, 0.13895335993652863, 0.1812719131001662, 0.13911076069360112, 0.12444340797507475, 0.16554058039645586, 0.17207766400682561, 0.14989904898669193, 0.15797804259313003, 0.15300560570596847, 0.16957092807969978, 0.16189328120700436, 0.16898643200495722, 0.15453996652138405, 0.12261638744375906, 0.18209533408070028, 0.13077247116314, 0.13235229045141633, 0.14396276099241628, 0.12865196145085744, 0.1626837476527771, 0.13942219889640686, 0.1363365769278614, 0.16586725975413694, 0.13884082923821311, 0.16018427003013302, 0.13770159602147558, 0.1430400080337943, 0.2006619189794636, 0.15707449930030679, 0.14537944246286755, 0.12972673943470378, 0.1505421750304259], [0.1472300548065956, 0.1166861215142654, 0.10837964413442318, 0.13222163997303632, 0.1422851698340475, 0.15723467219784484, 0.10755479051169693, 0.13429086432299317, 0.1148415993667857, 0.1747650836143494, 0.14192810181089352, 0.1825508052004425, 0.1477617339675263, 0.10806877471310265, 0.1523986154590685, 0.12384735983890043, 0.16821718717198209, 0.11293576661290682, 0.14456379240126743, 0.11696360072011025, 0.11616518888669371, 0.14424696710062868, 0.17665701938461995, 0.10465809888935396, 0.13887544211294994, 0.1728664266827154, 0.11275774478794359, 0.13454765070251057, 0.11547879204754727, 0.11315755609924143, 0.19681963827602397, 0.1617768059521509, 0.12049202764735502, 0.14284270306928276, 0.1075597500399225, 0.12445566325387114, 0.18037392331054666, 0.1476608739596347, 0.11386364246223672, 0.11715656892697174, 0.16116887705052715, 0.12362525691369006, 0.13582518185284279, 0.10709266555667693, 0.1832040408522016, 0.152197398609715, 0.15804793855671476, 0.15733785548157161, 0.1426795519770526, 0.11146897862894073, 0.11061316658676637, 0.14123761594015, 0.17937084140284906, 0.11116253780752604, 0.1321008140990299, 0.1385312789179749, 0.15065611524207156, 0.1426958072721677, 0.16969187371944494, 0.1771322309232049, 0.13828179540189942, 0.11726753526948785, 0.11026330329605472, 0.11375950681928489, 0.16316498403502805, 0.1570586932737819, 0.1811777626604328, 0.18942921165342905, 0.11648596008453085, 0.1257820888405002, 0.14133969467382393, 0.12258166029943238, 0.13409511634141114, 0.11588221355255547, 0.18970678872993194, 0.17000249871328738, 0.11461822870248575, 0.12029060796313372, 0.12703042180987253, 0.11874777665997815, 0.10524593194190818, 0.11010780847488297, 0.1295515560461795, 0.10752324520317862, 0.15719604411658386, 0.1140689869639036, 0.12384747070494084, 0.10570732319680635, 0.1499155101747663, 0.15831797765230513, 0.1515263291819585, 0.1648326576258619, 0.1092201637477733, 0.11922657435543979, 0.14851321248324056, 0.14491794691101006, 0.11631680622656992, 0.17337025385689678, 0.17442578671549006, 0.13404353746738115], [0.1307363465094211, 0.11688508719765264, 0.12130739263501931, 0.1215870551317532, 0.1476101088335909, 0.11372400184364896, 0.10669130421162691, 0.14570976894850038, 0.11587960174641866, 0.11094598044314177, 0.10583793809098013, 0.11269047937035834, 0.1779377756367317, 0.12232717428593257, 0.11633710530596518, 0.162540115579796, 0.16782931908901372, 0.12933333996939733, 0.16135025295267685, 0.12227601828564516, 0.11578346884204625, 0.11779019414372596, 0.13821570910248365, 0.1417542722727634, 0.1139243044158987, 0.1457839201436141, 0.14925551102173892, 0.11450098135259963, 0.12254680029822368, 0.14468407151896012, 0.14742521687769217, 0.16450145996369187, 0.12019450442726279, 0.1605522967089975, 0.12164892700461755, 0.1262243910289254, 0.21739512865728103, 0.1300023640156209, 0.10820737008220861, 0.15678931503970353, 0.1345491418548833, 0.13847888452460141, 0.19743945517921485, 0.12120697791363812, 0.1748540524696097, 0.11429339938200792, 0.12885416319788198, 0.21961765642280445, 0.16916290844667872, 0.11710836607563879, 0.11654190857582895, 0.13707872385388806, 0.18417853131541007, 0.18787558671800758, 0.17420203310432897, 0.12151718251541625, 0.15217537166495676, 0.1193841715526868, 0.13642531589601609, 0.14516745041910248, 0.15217218086091025, 0.11411026570206607, 0.12713112603891374, 0.11803224500660064, 0.12098827735173423, 0.14009942962048225, 0.11413248957144295, 0.13101868124106564, 0.1385488767502717, 0.13850403785836002, 0.14087154944563157, 0.14179246428480008, 0.12380268614735247, 0.11875485063817576, 0.1217356206115118, 0.17930080255008238, 0.14970050019102163, 0.1353453779045258, 0.16133754601608974, 0.15066802439972699, 0.1329975195086443, 0.17731342429267136, 0.18893585534739826, 0.12214911999169656, 0.12341827668713416, 0.11445966996263032, 0.17762766546166903, 0.12585588798478242, 0.13589986129181722, 0.14073922503387518, 0.11072483922374399, 0.1042228177492027, 0.1694686794615063, 0.15594340048118013, 0.1649834821011634, 0.13135816502872374, 0.13580358285762284, 0.19893741554378325, 0.11745597812901049, 0.1104876871841372]]
    lossvec0 = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    lossveclist = lossvec0 + lossveclist
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$v=1$, $l=0.1$, $n=30$, test node selection')
    
    lossveclist = [[0.11988525924311791, 0.15483094799207342, 0.1691899146741856, 0.16337552836098096, 0.12836809481628542, 0.14669632630179033, 0.11673217672810883, 0.1615678558169811, 0.14639554382295497, 0.16747300564678502, 0.14332538699399622, 0.11989719619532264, 0.13829764143478954, 0.14218326930548772, 0.15349822563502824, 0.16445278397470237, 0.1832089506652259, 0.13108422019561075, 0.11942583281115773, 0.18416029888190413, 0.12522863110501536, 0.14891343846169516, 0.1533842561477168, 0.1487084063006343, 0.13809294312785853, 0.12977698758410572, 0.14713777750637713, 0.137727820322727, 0.1512064422954208, 0.14455987258226444, 0.13096217862331147, 0.1827526286573682, 0.15843136147339795, 0.15422791357276375, 0.1483308941875547, 0.13411321454187758, 0.17483195620159936, 0.13380058106005982, 0.13236207459851054, 0.16723313876854307, 0.1686069465606297, 0.14304460011047676, 0.16278760536818096, 0.17360529815423428, 0.14400894994907246, 0.13902007229591232, 0.14832192151804016, 0.19414412050055052, 0.14785250956885154, 0.1264626890714373, 0.15553236788548055, 0.17223453498510718, 0.14820319125656917, 0.13626641083425303, 0.16703073316735492, 0.15857541812356918, 0.16660503458590611, 0.13670733616977424, 0.16490982512927907, 0.177103678040694, 0.16636407459490846, 0.14087917732914293, 0.1944676077882393, 0.17271469499917236, 0.14763454351603286, 0.1306683596330204, 0.13840285734269553, 0.15312543618855268, 0.13895335993652863, 0.1812719131001662, 0.13911076069360112, 0.12444340797507475, 0.16554058039645586, 0.17207766400682561, 0.14989904898669193, 0.15797804259313003, 0.15300560570596847, 0.16957092807969978, 0.16189328120700436, 0.16898643200495722, 0.15453996652138405, 0.12261638744375906, 0.18209533408070028, 0.13077247116314, 0.13235229045141633, 0.14396276099241628, 0.12865196145085744, 0.1626837476527771, 0.13942219889640686, 0.1363365769278614, 0.16586725975413694, 0.13884082923821311, 0.16018427003013302, 0.13770159602147558, 0.1430400080337943, 0.2006619189794636, 0.15707449930030679, 0.14537944246286755, 0.12972673943470378, 0.1505421750304259], [0.1472300548065956, 0.1166861215142654, 0.10837964413442318, 0.13222163997303632, 0.1422851698340475, 0.15723467219784484, 0.10755479051169693, 0.13429086432299317, 0.1148415993667857, 0.1747650836143494, 0.14192810181089352, 0.1825508052004425, 0.1477617339675263, 0.10806877471310265, 0.1523986154590685, 0.12384735983890043, 0.16821718717198209, 0.11293576661290682, 0.14456379240126743, 0.11696360072011025, 0.11616518888669371, 0.14424696710062868, 0.17665701938461995, 0.10465809888935396, 0.13887544211294994, 0.1728664266827154, 0.11275774478794359, 0.13454765070251057, 0.11547879204754727, 0.11315755609924143, 0.19681963827602397, 0.1617768059521509, 0.12049202764735502, 0.14284270306928276, 0.1075597500399225, 0.12445566325387114, 0.18037392331054666, 0.1476608739596347, 0.11386364246223672, 0.11715656892697174, 0.16116887705052715, 0.12362525691369006, 0.13582518185284279, 0.10709266555667693, 0.1832040408522016, 0.152197398609715, 0.15804793855671476, 0.15733785548157161, 0.1426795519770526, 0.11146897862894073, 0.11061316658676637, 0.14123761594015, 0.17937084140284906, 0.11116253780752604, 0.1321008140990299, 0.1385312789179749, 0.15065611524207156, 0.1426958072721677, 0.16969187371944494, 0.1771322309232049, 0.13828179540189942, 0.11726753526948785, 0.11026330329605472, 0.11375950681928489, 0.16316498403502805, 0.1570586932737819, 0.1811777626604328, 0.18942921165342905, 0.11648596008453085, 0.1257820888405002, 0.14133969467382393, 0.12258166029943238, 0.13409511634141114, 0.11588221355255547, 0.18970678872993194, 0.17000249871328738, 0.11461822870248575, 0.12029060796313372, 0.12703042180987253, 0.11874777665997815, 0.10524593194190818, 0.11010780847488297, 0.1295515560461795, 0.10752324520317862, 0.15719604411658386, 0.1140689869639036, 0.12384747070494084, 0.10570732319680635, 0.1499155101747663, 0.15831797765230513, 0.1515263291819585, 0.1648326576258619, 0.1092201637477733, 0.11922657435543979, 0.14851321248324056, 0.14491794691101006, 0.11631680622656992, 0.17337025385689678, 0.17442578671549006, 0.13404353746738115], [0.1307363465094211, 0.11688508719765264, 0.12130739263501931, 0.1215870551317532, 0.1476101088335909, 0.11372400184364896, 0.10669130421162691, 0.14570976894850038, 0.11587960174641866, 0.11094598044314177, 0.10583793809098013, 0.11269047937035834, 0.1779377756367317, 0.12232717428593257, 0.11633710530596518, 0.162540115579796, 0.16782931908901372, 0.12933333996939733, 0.16135025295267685, 0.12227601828564516, 0.11578346884204625, 0.11779019414372596, 0.13821570910248365, 0.1417542722727634, 0.1139243044158987, 0.1457839201436141, 0.14925551102173892, 0.11450098135259963, 0.12254680029822368, 0.14468407151896012, 0.14742521687769217, 0.16450145996369187, 0.12019450442726279, 0.1605522967089975, 0.12164892700461755, 0.1262243910289254, 0.21739512865728103, 0.1300023640156209, 0.10820737008220861, 0.15678931503970353, 0.1345491418548833, 0.13847888452460141, 0.19743945517921485, 0.12120697791363812, 0.1748540524696097, 0.11429339938200792, 0.12885416319788198, 0.21961765642280445, 0.16916290844667872, 0.11710836607563879, 0.11654190857582895, 0.13707872385388806, 0.18417853131541007, 0.18787558671800758, 0.17420203310432897, 0.12151718251541625, 0.15217537166495676, 0.1193841715526868, 0.13642531589601609, 0.14516745041910248, 0.15217218086091025, 0.11411026570206607, 0.12713112603891374, 0.11803224500660064, 0.12098827735173423, 0.14009942962048225, 0.11413248957144295, 0.13101868124106564, 0.1385488767502717, 0.13850403785836002, 0.14087154944563157, 0.14179246428480008, 0.12380268614735247, 0.11875485063817576, 0.1217356206115118, 0.17930080255008238, 0.14970050019102163, 0.1353453779045258, 0.16133754601608974, 0.15066802439972699, 0.1329975195086443, 0.17731342429267136, 0.18893585534739826, 0.12214911999169656, 0.12341827668713416, 0.11445966996263032, 0.17762766546166903, 0.12585588798478242, 0.13589986129181722, 0.14073922503387518, 0.11072483922374399, 0.1042228177492027, 0.1694686794615063, 0.15594340048118013, 0.1649834821011634, 0.13135816502872374, 0.13580358285762284, 0.19893741554378325, 0.11745597812901049, 0.1104876871841372]]
    lossvec0 = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    
    # COMBINE test node selection WITH trace selection
    designNames = ['Null design', 'Design 1', 'Design 2', 'Design 3']
    lossveclist_testnode = [[-0.16375364323693128, -0.1598924098297443, -0.16677607930317992, -0.16262309109948725, -0.16188093947140314, -0.157417741665715, -0.15506884850824199, -0.15941718184048764, -0.15282420444100275, -0.15626366688471008, -0.15572577584185382, -0.1575433641097066, -0.15299900810028547, -0.16665926604868425, -0.15828495126999473, -0.15870871088172278, -0.15557799103217498, -0.15833930128595194, -0.16905563020309589, -0.15940674903548974, -0.1608525097363954, -0.15381043349672274, -0.15939318914529807, -0.15545569559840658, -0.15303684755918198, -0.16821064281886222, -0.16245571600502157, -0.16257840155825892, -0.15252489752501308, -0.15433072776901252, -0.16364994795323945, -0.1579890795943676, -0.16436213080867138, -0.1658702895100968, -0.153411180123921, -0.15609545273829709, -0.1618149846666891, -0.16171901079095893, -0.16759210238465078, -0.1533561507927092, -0.1657515925645132, -0.16162558063079147, -0.1655038755360929, -0.1682526500473327, -0.16340195382486064, -0.1541341551722113, -0.16277564260011654, -0.15428475127720326, -0.16089461930114343, -0.1585954843513574, -0.15759429376621722, -0.15989907503786943, -0.1536116293638464, -0.15845502564458225, -0.16052103806227147, -0.16315107870073428, -0.15460359182858768, -0.16485917974241576, -0.15889838329088424, -0.1640656379297554, -0.150144918379174, -0.16377727397633166, -0.16343048272214358, -0.15497442737408612, -0.16053657001895796, -0.1610431061141195, -0.16229444224542286, -0.15972157664991693, -0.15381414185941167, -0.15597832612019064, -0.16562458518880893, -0.15595217942040576, -0.1603847893837301, -0.1611120657905986, -0.1532714356380745, -0.16108526245136187, -0.15630493416137503, -0.15799496190185, -0.15249177037061096, -0.154395096702405, -0.163679403659234, -0.16123106071808255, -0.1566742449677942, -0.15583065139781363, -0.15371728282113395, -0.16451059480697264, -0.15965258390385972, -0.16669918989045673, -0.15856848844392735, -0.15593563711561548, -0.15945917400382678, -0.16444289413535804, -0.16144397531488, -0.16394460887977857, -0.15808940474812164, -0.15516427158986124, -0.16397906625340097, -0.16616934455334773, -0.16338488421250086, -0.16207290278862374], [-0.11988525924311791, -0.15483094799207342, -0.1691899146741856, -0.16337552836098096, -0.12836809481628542, -0.14669632630179033, -0.11673217672810883, -0.1615678558169811, -0.14639554382295497, -0.16747300564678502, -0.14332538699399622, -0.11989719619532264, -0.13829764143478954, -0.14218326930548772, -0.15349822563502824, -0.16445278397470237, -0.1832089506652259, -0.13108422019561075, -0.11942583281115773, -0.18416029888190413, -0.12522863110501536, -0.14891343846169516, -0.1533842561477168, -0.1487084063006343, -0.13809294312785853, -0.12977698758410572, -0.14713777750637713, -0.137727820322727, -0.1512064422954208, -0.14455987258226444, -0.13096217862331147, -0.1827526286573682, -0.15843136147339795, -0.15422791357276375, -0.1483308941875547, -0.13411321454187758, -0.17483195620159936, -0.13380058106005982, -0.13236207459851054, -0.16723313876854307, -0.1686069465606297, -0.14304460011047676, -0.16278760536818096, -0.17360529815423428, -0.14400894994907246, -0.13902007229591232, -0.14832192151804016, -0.19414412050055052, -0.14785250956885154, -0.1264626890714373, -0.15553236788548055, -0.17223453498510718, -0.14820319125656917, -0.13626641083425303, -0.16703073316735492, -0.15857541812356918, -0.16660503458590611, -0.13670733616977424, -0.16490982512927907, -0.177103678040694, -0.16636407459490846, -0.14087917732914293, -0.1944676077882393, -0.17271469499917236, -0.14763454351603286, -0.1306683596330204, -0.13840285734269553, -0.15312543618855268, -0.13895335993652863, -0.1812719131001662, -0.13911076069360112, -0.12444340797507475, -0.16554058039645586, -0.17207766400682561, -0.14989904898669193, -0.15797804259313003, -0.15300560570596847, -0.16957092807969978, -0.16189328120700436, -0.16898643200495722, -0.15453996652138405, -0.12261638744375906, -0.18209533408070028, -0.13077247116314, -0.13235229045141633, -0.14396276099241628, -0.12865196145085744, -0.1626837476527771, -0.13942219889640686, -0.1363365769278614, -0.16586725975413694, -0.13884082923821311, -0.16018427003013302, -0.13770159602147558, -0.1430400080337943, -0.2006619189794636, -0.15707449930030679, -0.14537944246286755, -0.12972673943470378, -0.1505421750304259], [-0.1472300548065956, -0.1166861215142654, -0.10837964413442318, -0.13222163997303632, -0.1422851698340475, -0.15723467219784484, -0.10755479051169693, -0.13429086432299317, -0.1148415993667857, -0.1747650836143494, -0.14192810181089352, -0.1825508052004425, -0.1477617339675263, -0.10806877471310265, -0.1523986154590685, -0.12384735983890043, -0.16821718717198209, -0.11293576661290682, -0.14456379240126743, -0.11696360072011025, -0.11616518888669371, -0.14424696710062868, -0.17665701938461995, -0.10465809888935396, -0.13887544211294994, -0.1728664266827154, -0.11275774478794359, -0.13454765070251057, -0.11547879204754727, -0.11315755609924143, -0.19681963827602397, -0.1617768059521509, -0.12049202764735502, -0.14284270306928276, -0.1075597500399225, -0.12445566325387114, -0.18037392331054666, -0.1476608739596347, -0.11386364246223672, -0.11715656892697174, -0.16116887705052715, -0.12362525691369006, -0.13582518185284279, -0.10709266555667693, -0.1832040408522016, -0.152197398609715, -0.15804793855671476, -0.15733785548157161, -0.1426795519770526, -0.11146897862894073, -0.11061316658676637, -0.14123761594015, -0.17937084140284906, -0.11116253780752604, -0.1321008140990299, -0.1385312789179749, -0.15065611524207156, -0.1426958072721677, -0.16969187371944494, -0.1771322309232049, -0.13828179540189942, -0.11726753526948785, -0.11026330329605472, -0.11375950681928489, -0.16316498403502805, -0.1570586932737819, -0.1811777626604328, -0.18942921165342905, -0.11648596008453085, -0.1257820888405002, -0.14133969467382393, -0.12258166029943238, -0.13409511634141114, -0.11588221355255547, -0.18970678872993194, -0.17000249871328738, -0.11461822870248575, -0.12029060796313372, -0.12703042180987253, -0.11874777665997815, -0.10524593194190818, -0.11010780847488297, -0.1295515560461795, -0.10752324520317862, -0.15719604411658386, -0.1140689869639036, -0.12384747070494084, -0.10570732319680635, -0.1499155101747663, -0.15831797765230513, -0.1515263291819585, -0.1648326576258619, -0.1092201637477733, -0.11922657435543979, -0.14851321248324056, -0.14491794691101006, -0.11631680622656992, -0.17337025385689678, -0.17442578671549006, -0.13404353746738115], [-0.1307363465094211, -0.11688508719765264, -0.12130739263501931, -0.1215870551317532, -0.1476101088335909, -0.11372400184364896, -0.10669130421162691, -0.14570976894850038, -0.11587960174641866, -0.11094598044314177, -0.10583793809098013, -0.11269047937035834, -0.1779377756367317, -0.12232717428593257, -0.11633710530596518, -0.162540115579796, -0.16782931908901372, -0.12933333996939733, -0.16135025295267685, -0.12227601828564516, -0.11578346884204625, -0.11779019414372596, -0.13821570910248365, -0.1417542722727634, -0.1139243044158987, -0.1457839201436141, -0.14925551102173892, -0.11450098135259963, -0.12254680029822368, -0.14468407151896012, -0.14742521687769217, -0.16450145996369187, -0.12019450442726279, -0.1605522967089975, -0.12164892700461755, -0.1262243910289254, -0.21739512865728103, -0.1300023640156209, -0.10820737008220861, -0.15678931503970353, -0.1345491418548833, -0.13847888452460141, -0.19743945517921485, -0.12120697791363812, -0.1748540524696097, -0.11429339938200792, -0.12885416319788198, -0.21961765642280445, -0.16916290844667872, -0.11710836607563879, -0.11654190857582895, -0.13707872385388806, -0.18417853131541007, -0.18787558671800758, -0.17420203310432897, -0.12151718251541625, -0.15217537166495676, -0.1193841715526868, -0.13642531589601609, -0.14516745041910248, -0.15217218086091025, -0.11411026570206607, -0.12713112603891374, -0.11803224500660064, -0.12098827735173423, -0.14009942962048225, -0.11413248957144295, -0.13101868124106564, -0.1385488767502717, -0.13850403785836002, -0.14087154944563157, -0.14179246428480008, -0.12380268614735247, -0.11875485063817576, -0.1217356206115118, -0.17930080255008238, -0.14970050019102163, -0.1353453779045258, -0.16133754601608974, -0.15066802439972699, -0.1329975195086443, -0.17731342429267136, -0.18893585534739826, -0.12214911999169656, -0.12341827668713416, -0.11445966996263032, -0.17762766546166903, -0.12585588798478242, -0.13589986129181722, -0.14073922503387518, -0.11072483922374399, -0.1042228177492027, -0.1694686794615063, -0.15594340048118013, -0.1649834821011634, -0.13135816502872374, -0.13580358285762284, -0.19893741554378325, -0.11745597812901049, -0.1104876871841372]]
    lossveclist_trace = [[-0.16316247614417786, -0.15720308016518392, -0.160863945888904, -0.16447283110683764, -0.1597308862650217, -0.16530244384804657, -0.16669312853832846, -0.16160074183245418, -0.16531921860847268, -0.16204418983966884, -0.15497871109482528, -0.15467411380815202, -0.16137507788563935, -0.15747074719610993, -0.15227562888307283, -0.17145553421385715, -0.1636936109540728, -0.1669252130711022, -0.16203792902518932, -0.1590776036970198, -0.15517493597181414, -0.16082428825129408, -0.15756807318592914, -0.15506083185262165, -0.1563119571699612, -0.1577098321842063, -0.1641468650148215, -0.15488810176193077, -0.15665288809662717, -0.1603004792908751, -0.16244412649356446, -0.15682117334200987, -0.16354500425841928, -0.16415919785812233, -0.15638019835364242, -0.16670010935518434, -0.15949899127054123, -0.16151886488912792, -0.15735859935171637, -0.15677491976724814, -0.1632770479674153, -0.14924292022848828, -0.15743089052516365, -0.16345503460451294, -0.16461700092997042, -0.16393482215356434, -0.1567846630229211, -0.15924311538390307, -0.15772433401103705, -0.14844073078598255, -0.14807481745813092, -0.15995264676230736, -0.1579484132093352, -0.15724138753152508, -0.16224710472251716, -0.1641735756558422, -0.15887070821169746, -0.15642966735431305, -0.15406330865539522, -0.1574801626153325, -0.16362808604206897, -0.16149986707782518, -0.15773307449644686, -0.1530540907925208, -0.1645033073394543, -0.15431738379696006, -0.1704341251141459, -0.15808855709519426, -0.16246600430741387, -0.1698498306376867, -0.1648337933683812, -0.17121651335895544, -0.1503781786512441, -0.1524599498085908, -0.15922731157919556, -0.15916234372331206, -0.15939630765108154, -0.15663433246236877, -0.1616397543298343, -0.16063162982298979, -0.1558830142365766, -0.1619674732314209, -0.1696654499763426, -0.16089161339847177, -0.15122267732630387, -0.1650651236958853, -0.16316201297091332, -0.16165031167909902, -0.16726574771516814, -0.16236019915686473, -0.1645428564195015, -0.1545329722426662, -0.15539168558736072, -0.17099218135813946, -0.16002479505594225, -0.15695387354065177, -0.15969571027275462, -0.1596724155733717, -0.15652864335844877, -0.16498385967878598], [-0.12847026958561233, -0.11986732398951072, -0.13060367191347091, -0.13456141828997675, -0.1274179951384851, -0.1395853466736562, -0.11949711627700356, -0.14222439398953382, -0.12650237999957095, -0.11742182455737671, -0.125807002876967, -0.1184952562133039, -0.11595927744994752, -0.13241341970960263, -0.1330365092362536, -0.14702475658549582, -0.12372548979744037, -0.12326210162435598, -0.11596437064058449, -0.1360079427634559, -0.13490036368964048, -0.12857099981465742, -0.12546313943515863, -0.12160934132043706, -0.1462538289015319, -0.12058229113278009, -0.1906528527577479, -0.12731827990432867, -0.15162017453679544, -0.11729449808267677, -0.1190441940260026, -0.11461052983150097, -0.12314952671527217, -0.13401586619002537, -0.11792195626961513, -0.12672867159599627, -0.13739567825608845, -0.12373221054427508, -0.1297344567932947, -0.13560544320405665, -0.19761742209602334, -0.12606856696655194, -0.1379339281846113, -0.1374334378123528, -0.1306824291013811, -0.11803407486284032, -0.12967267696704565, -0.11771991263021934, -0.1346792598792127, -0.1409915447125594, -0.12118391932460561, -0.12343177753491975, -0.12827072105544465, -0.13515099777805797, -0.1419930223266828, -0.13708165525755409, -0.12851654777366114, -0.12072503892420437, -0.13588302574565375, -0.12763095569671912, -0.11770390994278485, -0.1337648303433984, -0.1717760059155993, -0.12769012395302703, -0.14218244225977397, -0.12415284258856643, -0.12592778571793506, -0.12462257842242966, -0.14994368569109445, -0.1184717062250044, -0.127352890061241, -0.1261733842087149, -0.1553400615115116, -0.12521722674144753, -0.140173063194675, -0.17588188191245271, -0.13714986387224123, -0.1271717829247304, -0.12247977824019007, -0.145766957774525, -0.13598255520000507, -0.13351997498557475, -0.12627843146354406, -0.12668244354246871, -0.13096893060481926, -0.12175318020999325, -0.16310087594160333, -0.16095717672883847, -0.1300863114218935, -0.14288872177752412, -0.12794333127672622, -0.13113273545611268, -0.14831587955772, -0.1331221376427609, -0.12098932922272174, -0.12482044143706773, -0.15980859235266884, -0.16760616557412308, -0.12400024308665411, -0.12109142757996429], [-0.10706549287250079, -0.11575611710588574, -0.11657755694309162, -0.16261739870199468, -0.13044543811112205, -0.13597871423477614, -0.1162521924230518, -0.11451468777257316, -0.11977597197875277, -0.14706270459984383, -0.11710752464564515, -0.10042574426077899, -0.13200671674442208, -0.11956001986469626, -0.14352235169529448, -0.13941878520513282, -0.11014525523119775, -0.10043722950557356, -0.12029623451868249, -0.13085447101444728, -0.11453146422406418, -0.17624798196585864, -0.14802263895111217, -0.10563726772450745, -0.11133843244043405, -0.17849680482103586, -0.14070005356490364, -0.14096922814148977, -0.156119362323945, -0.11431832309758867, -0.1347037871678656, -0.10827995515121462, -0.12991595333241354, -0.11288800385497598, -0.1087194394506875, -0.13957184220395502, -0.11433250028736858, -0.1154339703968407, -0.13531303685378834, -0.1181845974938699, -0.1624782253808026, -0.10785906088538802, -0.11187337490987176, -0.1490282005501971, -0.16584111420698566, -0.10409255587349321, -0.1531767083995999, -0.13969790265815368, -0.15893111057070325, -0.1350896551679034, -0.11223328144029465, -0.11122693364823041, -0.156758751098658, -0.13926181585327896, -0.12928728514951857, -0.14880967338603854, -0.11426618162572089, -0.12765392949835094, -0.16174518844820734, -0.12906559110102445, -0.11659937296517346, -0.10805969683894634, -0.1124038253730161, -0.11256266423435923, -0.13337769706865218, -0.12564355984905443, -0.15759371095454633, -0.1334435348161012, -0.11424065270941168, -0.10670547781120827, -0.1340283971088839, -0.11229038996424014, -0.13919071089398244, -0.11865267981990554, -0.19434057273740335, -0.16108895386440805, -0.1339694198446523, -0.1444760773776637, -0.11576840064181515, -0.15682787631356135, -0.1333306475033713, -0.11269576857300377, -0.105196751357552, -0.14939289076638698, -0.11654199774278479, -0.10779133744224585, -0.11893456865733175, -0.11701383813184087, -0.11127528879372119, -0.16543984467098882, -0.18119717818983047, -0.11419431420662064, -0.16719167236741772, -0.11701261937403842, -0.11162983384442594, -0.11346742968022439, -0.12262265636152543, -0.1353553759373205, -0.13483725103248212, -0.10472127378800088], [-0.11678330073853264, -0.1483791506375431, -0.14301199387015806, -0.15291720046764978, -0.12932617682376016, -0.11415161831739352, -0.13594132427209848, -0.12851750912928456, -0.11248114383222577, -0.12569532953866397, -0.13116045541080357, -0.11350277061595218, -0.12389588123048184, -0.12255118084248208, -0.12284882809920945, -0.13101887036737578, -0.138084520666699, -0.1222912567850896, -0.11060620781755158, -0.13532426606855924, -0.12088575345283185, -0.1385368374689929, -0.11619970130129674, -0.12457753959628065, -0.13055800683995697, -0.13538545412131597, -0.14276802801025254, -0.1374871166073497, -0.15312490598902023, -0.1311127947083507, -0.12509808772524494, -0.12665143866605372, -0.14334383550981983, -0.13091911295528422, -0.12893982634754697, -0.11608514495001748, -0.11858905120451496, -0.1250175749211199, -0.11806106548991627, -0.15243464137467358, -0.16870203684370985, -0.12830671483036343, -0.11548252484653072, -0.1505001008801831, -0.15115493328869029, -0.11667149774132125, -0.1243792772803687, -0.1280739476470694, -0.1300164370813426, -0.12132283907291189, -0.12093929338546512, -0.12594551117214187, -0.16804669258024021, -0.15495788201033703, -0.13710339770258398, -0.12687569415258093, -0.12563536725886024, -0.1585903134223614, -0.13340856579979055, -0.13097073330511214, -0.1322598244909756, -0.12497751366881622, -0.16082242067367697, -0.13102265922097037, -0.13999650830061847, -0.12940941740665673, -0.13611910200945787, -0.13426229500361453, -0.12467430197220103, -0.1280500475944258, -0.13499429373161861, -0.12933260074498812, -0.12918639683395922, -0.14038571042123474, -0.16182826356035337, -0.17207014456170683, -0.14677207023614533, -0.1267900443293803, -0.14383984254649396, -0.14359682121981873, -0.12230830793897036, -0.11839440032337135, -0.12801523418544866, -0.12754693512342496, -0.1429154338734327, -0.12006421074473932, -0.13423051645822143, -0.13556868485588958, -0.12954861499487944, -0.12082549577064108, -0.12580973946180612, -0.12625040853445754, -0.15050355161408746, -0.12750415834131537, -0.1351781983382809, -0.13302548918098675, -0.13871047053836819, -0.15974484376388454, -0.12162680349486192, -0.11474779719424359]]
    lossveclist = lossveclist_testnode + lossveclist_trace
    plotLossVecs(lossveclist, lvecnames=designNames,plottitle='95% CIs for design utility\n$\delta$=1, $t$=0.1, $n=30$, test node and trace selection',legendlabel=['Test node selection','Trace selection'])    
    '''

    # Now use a different Q estimate; shift 30% of market share from TN leader to other supply node
    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3]
    designNames = ['Design 1', 'Design 2', 'Design 3']
    numtests = 30
    omeganum = 100
    Qest = np.array([[0.7, 0.3], [0.4, 0.6], [0.4, 0.6]])
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    omeganum = 100
    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                                   designlist=designList, designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    '''
    lossveclist =[[0.12115009438755228, 0.13461110512884492, 0.1722216130383893, 0.11960971895499706, 0.11986969880423198, 0.1387469483592486, 0.10637471497896413, 0.14075768675367248, 0.11053010265465694, 0.11898031153447819, 0.12182649253221783, 0.12546709732453665, 0.14566358794114181, 0.12291165358830142, 0.12632423629814665, 0.13844715785587744, 0.1359827150513592, 0.12300528691184191, 0.1363459160477962, 0.12265007668860892, 0.14730260046337898, 0.14104361619447311, 0.1310801356030417, 0.1453021473378001, 0.16936519076503334, 0.12549479057661622, 0.18616654691899012, 0.15237832126983022, 0.13867931039547374, 0.13912895623661575, 0.13364441502288119, 0.1651547174206939, 0.11933313530596476, 0.13892032603885546, 0.14052724967255562, 0.14289983599826683, 0.17070889282723736, 0.1271047167971126, 0.1580977315941791, 0.12792877586220888, 0.1868658019711628, 0.14806590016732527, 0.16115816484424453, 0.13301862163080286, 0.13927503970190105, 0.11127744633207685, 0.12085063969884527, 0.18536200300755812, 0.141768171091285, 0.1312310216109566, 0.11236103821661589, 0.13523545581511687, 0.11217305140599704, 0.1277586148975934, 0.13457144743540686, 0.12115891288269691, 0.15112017648553427, 0.12552508852768887, 0.1310784608389094, 0.1106546332169137, 0.14600251867579464, 0.14791863466109248, 0.1470317569602481, 0.12588421784509765, 0.1350118985577273, 0.1373283452450607, 0.11246647766318077, 0.13485269174557718, 0.14792604494600778, 0.14820424727855075, 0.11750408808897744, 0.15516998426041514, 0.17852508655511987, 0.11330770146083034, 0.1513291022967901, 0.20881039171652188, 0.12914660865934724, 0.16713397522990997, 0.11837392401015155, 0.1800579906301695, 0.11032769162757677, 0.14717431813707246, 0.12079954819996869, 0.1176592922550538, 0.15535546469963152, 0.14011632332071156, 0.13535615901393339, 0.1270167610404591, 0.15918693664718211, 0.15919348205063158, 0.10171960979395292, 0.12081638784540838, 0.2090079952235582, 0.14477125377567596, 0.14185012699735966, 0.13962534148872444, 0.15238493972399883, 0.14989487639079063, 0.12809288548959516, 0.11570351183925796], [0.1314931888519746, 0.1505300474400284, 0.11528985301854695, 0.10451556416532552, 0.14876900527362502, 0.11211052687891992, 0.13110760183986897, 0.11272461486145662, 0.1109715145085325, 0.1272576474481824, 0.10844575909476188, 0.11941814028375643, 0.10105428463004498, 0.10169346713072862, 0.12949354194146184, 0.15241920365955614, 0.1417826736994067, 0.12864311567438846, 0.21979318324998623, 0.10281915955422438, 0.1453075419961713, 0.12587524678250336, 0.15875456058830764, 0.10910289355433153, 0.11348088299451752, 0.11053648099012525, 0.13349220067792336, 0.10888626883237473, 0.1305198127309108, 0.10569937042569008, 0.17610053696939756, 0.10525542199748214, 0.13022957531580662, 0.11100263596431463, 0.10164653065250313, 0.1331595651205772, 0.13295480578684155, 0.11016142455422666, 0.12701363682116398, 0.1198758883747071, 0.1699933811126077, 0.11488898481110511, 0.14698898206227842, 0.16608957269600125, 0.19658979188591963, 0.10906670858499384, 0.1546102933330245, 0.10908478813954003, 0.17062814369015147, 0.14979189637405763, 0.10114339889835564, 0.10499322126964893, 0.10475532563280326, 0.12490861715625166, 0.14801871255468452, 0.15075830311546756, 0.1281423542616761, 0.12867633588591693, 0.12716147964505778, 0.1733326222554273, 0.10766779399202417, 0.11242084059316818, 0.12463355284543258, 0.12395229802056762, 0.17704110803411324, 0.10947157779723812, 0.17328031216481302, 0.14917821530344874, 0.15109603777884528, 0.12857014287451285, 0.16540631826151078, 0.10772871425130096, 0.10432814427881058, 0.12432940211476576, 0.11252257064858817, 0.18012880712455354, 0.11525820823438854, 0.13039103881168812, 0.1490496717498257, 0.1522142675165206, 0.1300237058345265, 0.1316735458829273, 0.10725557813477511, 0.16106942311002564, 0.11013671349995913, 0.1180819791692349, 0.12981730056948088, 0.10885305703439736, 0.14082639309240447, 0.12815741282820123, 0.15889412500120492, 0.1289178196638307, 0.1425631595157095, 0.127706112285063, 0.14695983665099996, 0.11184398686635888, 0.11750118310416592, 0.1879213051098772, 0.1676624661607494, 0.15239158347671497], [0.1889125036869928, 0.11260991061977453, 0.11446849719047707, 0.16782784569497525, 0.12900815054826337, 0.13638815850763414, 0.11410618995327353, 0.112278267189228, 0.11325723380763975, 0.1655306736087747, 0.11650187113859797, 0.10864183297055878, 0.16808755768251926, 0.10211987938047257, 0.10546861912569024, 0.1195951046852699, 0.11307446865023776, 0.11550161042471585, 0.10394546664817032, 0.10313478788212213, 0.11004319776253961, 0.12143254091035788, 0.14104043102692082, 0.11283057606806825, 0.14882709869094904, 0.13369235765178167, 0.1194390942860912, 0.12948865737703358, 0.10296332920963425, 0.10651573878412791, 0.16792826677578057, 0.13780707054017324, 0.14093896002403186, 0.12908445872666777, 0.11717581877958087, 0.12047180324056124, 0.1405452595160873, 0.11593185776694177, 0.11030412397315592, 0.10665500233737807, 0.20547851912464388, 0.1288248499849765, 0.14894056897156804, 0.154911286049414, 0.11230031111573986, 0.11226491526568062, 0.1439356950383056, 0.17195699434569825, 0.15855421172034356, 0.11638363727637273, 0.11708753628404249, 0.15118876421030128, 0.12059104329301999, 0.1289447494447829, 0.1373948554497738, 0.13888053078463536, 0.14857005772664078, 0.11604921376091433, 0.16198558365637825, 0.10267320811082346, 0.1109477925131397, 0.10593576726294643, 0.11544050100772772, 0.1084114593882065, 0.13563810981851407, 0.13592836442942313, 0.12370451661323142, 0.10985507897785665, 0.19587633334999002, 0.1304644476082767, 0.11522011286430336, 0.15579312608044452, 0.12741240161296521, 0.11080096107188679, 0.1125692088287127, 0.15832222711412716, 0.11447742529836313, 0.11022776220404057, 0.13030398527557016, 0.14654022040743023, 0.12940871021272302, 0.1106110396562316, 0.1258566368669427, 0.1320505499360573, 0.11569401968811101, 0.10042944047675217, 0.16399779196036632, 0.1494466333553447, 0.1471911499963044, 0.13221280503511085, 0.13855376259254734, 0.12026207494907633, 0.13850896620076553, 0.18393815819650733, 0.14294700441787248, 0.11632861789428603, 0.12988121731331415, 0.1681711837362325, 0.18243456552130455, 0.13347849383281346]]
    lossvec0 = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    # Now use a different Q estimate; shift 60% of market share from TN leader to other supply node
    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3]
    designNames = ['Design 1', 'Design 2', 'Design 3']
    numtests = 30
    omeganum = 100
    Qest = np.array([[1., 0.], [0.1, 0.9], [0.7, 0.3]])
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                                   designlist=designList, designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    '''
    lossveclist = [[0.12620225309764227, 0.14362722156224306, 0.13925899467834388, 0.1316839804652289, 0.1348326999751596, 0.1381360396157157, 0.12344216422421511, 0.12438054269131847, 0.13296952858371489, 0.11480363100002812, 0.12357754362888537, 0.1114857753037955, 0.15361101005350195, 0.12252274107757456, 0.12900829128995878, 0.1530776999202026, 0.12580160015380346, 0.1046801024962892, 0.10493574743898232, 0.11437992817213863, 0.1428134962008454, 0.14487572377264848, 0.12501477029477825, 0.10893314752234166, 0.15135408450585217, 0.1247011484098704, 0.12190777500990334, 0.12439589246413428, 0.14126468666015415, 0.11625846812022167, 0.1292421122250613, 0.15164242231560446, 0.12408019565555542, 0.1315852290206306, 0.11930963680102773, 0.13056029610587583, 0.14234589341052148, 0.12570378405933483, 0.13248520837940062, 0.12317146735849491, 0.14262156500215065, 0.10839215863368461, 0.12785939558690407, 0.1314484794033972, 0.1312282746365712, 0.12442867131530813, 0.12379104044144955, 0.14494668048468543, 0.13424906081823743, 0.13526186869480886, 0.12205014975520066, 0.1627080886017051, 0.156592751067117, 0.13563453643464898, 0.16800806757177741, 0.11438320507007184, 0.13230973474463972, 0.13022732671061732, 0.12880790968282174, 0.12015247877916463, 0.16926429586071853, 0.1324407396024803, 0.16375829540430392, 0.12680644633076463, 0.13322615837473514, 0.14963447690111883, 0.11934904076895093, 0.14554537010483554, 0.1458846222356688, 0.12188161530184932, 0.13204703688501981, 0.1217549658719824, 0.18900609624846487, 0.11221112575425599, 0.16055431215111374, 0.1971978539658249, 0.1356471438752369, 0.10895608157699879, 0.15236288673969317, 0.1371366374236574, 0.11911408490928342, 0.1391058601945861, 0.13168835012389943, 0.12046782399669473, 0.12334677847305803, 0.10294011457872033, 0.13305282514595979, 0.13054503183045346, 0.1215320051037103, 0.1267646154823363, 0.11960536751427922, 0.12466599945137301, 0.1751929515286762, 0.1231170186319233, 0.12615196835143935, 0.11532544649698541, 0.15663175114889225, 0.13961740666848232, 0.14046828837564104, 0.12025475236911155], [0.1418017789209135, 0.1254168145874347, 0.12276889236304836, 0.12125845141337158, 0.13941757697417528, 0.12644036638154124, 0.11010883968500863, 0.14049147169907247, 0.10956921551955029, 0.1571476962511997, 0.10941850745210498, 0.146246317148977, 0.17913167641698086, 0.10920135388974865, 0.15360047159856982, 0.12766511134151545, 0.12469251811409211, 0.10820508013465462, 0.1416215533875236, 0.1061153503038121, 0.1239291215513019, 0.10663526196327612, 0.12790027709780322, 0.11471783664938077, 0.13008366323290171, 0.11181897925787494, 0.17122302121353056, 0.1283261279363284, 0.11165275206904907, 0.1362619324074905, 0.16362883306632026, 0.12590374364636925, 0.13380358541950732, 0.10602261421566526, 0.10729983442595145, 0.1299892858058558, 0.10651833722401699, 0.11006407155306293, 0.12890701171182992, 0.10821997915423748, 0.1439058722035614, 0.12704093474381709, 0.11008206389663042, 0.1817825933202038, 0.1920559575379196, 0.10774084618500851, 0.1221782493814412, 0.13924121317970564, 0.17207835131141888, 0.1507149768235325, 0.1196587427780395, 0.12544183833578204, 0.15329367459816887, 0.1451820131569236, 0.14067644269126373, 0.10871574361218905, 0.15212262164051532, 0.12701763290805954, 0.13950581155664835, 0.12520814744025746, 0.1142953156896037, 0.11082303660326528, 0.14923280847561957, 0.1081304260981485, 0.1256007569039868, 0.11218353747127403, 0.12261460508711947, 0.1474710160474247, 0.10860525561160636, 0.11054302856246385, 0.12049796093954243, 0.1099634501291226, 0.11234600900299664, 0.11086079480947206, 0.10765255524701645, 0.1607793362017592, 0.10998272695037566, 0.11199949740800477, 0.127469342835561, 0.1292919998072768, 0.11206758398532722, 0.1086605296394935, 0.15497153194594118, 0.13651803306137955, 0.1457950808536293, 0.11234235725000248, 0.1240678150850545, 0.11032440176908707, 0.10694350221514644, 0.16051749576399743, 0.13887083078816476, 0.12713023515405392, 0.1679723088244741, 0.11125644163634951, 0.12472420793022186, 0.11877196016739867, 0.10213186234944396, 0.14554317000026717, 0.15474108428006528, 0.11153053639882014], [0.12308784339549932, 0.12902260631483958, 0.12886480049088742, 0.16712129443544255, 0.16752631761171569, 0.12228584532249157, 0.10539862316663093, 0.14978955461669663, 0.11045471809837439, 0.1762168506508236, 0.1100425541205162, 0.12752789697973185, 0.12824393931312403, 0.10971914757447457, 0.16108381538404415, 0.11033701247018474, 0.13756876023950582, 0.11241642265680366, 0.1727748916597516, 0.10861597686615163, 0.11475887809207892, 0.11209728487958061, 0.12597544459235777, 0.10395277604623983, 0.1153987705720796, 0.1307495268741258, 0.14416418669159214, 0.10422532507056981, 0.11519259316187089, 0.13163079949634346, 0.13247172891354506, 0.11707733147114531, 0.1599948379623924, 0.10952884101354053, 0.15250814319577513, 0.13770828406597113, 0.13480245820818432, 0.10950676706705496, 0.11083372575842135, 0.13254461564102588, 0.15942457179407155, 0.11056183049766352, 0.11042187133045124, 0.13184026170870275, 0.15961641155541323, 0.10657096743149784, 0.14419917440035449, 0.15560292570175824, 0.1510908949890016, 0.11386232889970446, 0.1290395741407423, 0.11536591103318139, 0.15394654078800663, 0.11471825519620822, 0.17588123320719895, 0.12944205734772146, 0.1471853288916208, 0.11567201279050267, 0.1714363512533929, 0.12765848610777558, 0.13090124253418986, 0.11480807631212026, 0.12150864392286286, 0.10567227041436929, 0.12696227035678045, 0.12354136632406046, 0.1481732828560903, 0.13271664148348106, 0.13683062689388717, 0.10695513460152432, 0.14387780252684038, 0.11375289883765065, 0.12135482951931267, 0.12361475439177617, 0.1716952616883734, 0.12986120080649619, 0.11226115336702354, 0.10463398955119964, 0.13112233323375957, 0.1565869971589932, 0.14532718775497058, 0.12068757335426322, 0.15719683349593072, 0.10627494687124903, 0.1354719466017762, 0.09541222257662813, 0.11402963426477268, 0.12150592025734142, 0.11213006697424624, 0.11144724915850399, 0.12399660891805296, 0.1106546151498917, 0.11603019474534286, 0.11440581316268267, 0.10150181158882708, 0.13292269940438164, 0.12382725092909407, 0.16117000300799345, 0.12363405312913316, 0.10387318145473569]]
    lossvec0 = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''

    # Now use a different Q estimate; shift 60% of market share from TN leader to other supply node ONLY FOR TEST NODE 2
    # 30 tests for all designs
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design1, design2, design3]
    designNames = ['Design 1', 'Design 2', 'Design 3']
    numtests = 30
    omeganum = 100
    Qest = np.array([[0.4, 0.6], [0.2, 0.8], [0.1, 0.9]])
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    lossveclist = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(),
                                   designlist=designList, designnames=designNames, numtests=numtests,
                                   omeganum=omeganum, type=['node', Qest],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
    '''
    lossveclist = [[0.14041511622659597, 0.1331926365214835, 0.13502020467115539, 0.1600748130920711, 0.13783662439903208, 0.1690038913403125, 0.14891362007963338, 0.1753777289005296, 0.14092990661213714, 0.1533515426472005, 0.13725947445647985, 0.1388005723010352, 0.15751246194033205, 0.15567036758195751, 0.1441730345398434, 0.1464820280417062, 0.15597003415519722, 0.13973628862488652, 0.14775230428826527, 0.14840444941132694, 0.1581271854976226, 0.1313329341102158, 0.1611426411036488, 0.1265317494990795, 0.15089412018205917, 0.1440572830718544, 0.14339090454073417, 0.15691834877619046, 0.13684369361690238, 0.15652807669332394, 0.177851332905445, 0.16283023143013617, 0.1117709211655677, 0.14863917173956798, 0.12639275147269588, 0.15265925963350793, 0.1933853823599346, 0.16015370597622913, 0.1655968162702132, 0.14381568431636754, 0.15104917122292325, 0.1363656864769608, 0.17928576036297972, 0.12018994924502968, 0.13906759716823813, 0.1328123770937688, 0.13551528043713626, 0.17294691392128653, 0.14632796951864882, 0.16134016853046707, 0.13337409858869098, 0.17317570694803536, 0.15133222331936047, 0.16158592945231065, 0.1558621211244873, 0.1480934797351278, 0.1327609551674112, 0.14426854046946616, 0.14658031816349318, 0.12909463156653142, 0.17528119871729173, 0.14697456489332925, 0.1583447073552582, 0.1356680834451272, 0.13324949576284303, 0.15704529781902246, 0.14093353926886865, 0.140975054453624, 0.14697114380996057, 0.12384439031693575, 0.1288100533485225, 0.16784982045203814, 0.13957580770553993, 0.14448359032215735, 0.17941317397868864, 0.1955661814896146, 0.14447019433001745, 0.15949145294227632, 0.17821514867353208, 0.16609764481173178, 0.12671078734277572, 0.12791114473952028, 0.14849676245105692, 0.14875225527024333, 0.19128373306405705, 0.14219266293275143, 0.16633817434682066, 0.15375374994237864, 0.16201194246489284, 0.15794049747741506, 0.13894447533694892, 0.1485903381432227, 0.17533689830774626, 0.15697496446858136, 0.13439067937154867, 0.1441014860944704, 0.17294410165607324, 0.16014058702498243, 0.15766179936078892, 0.15717912036840032], [0.12163404693249581, 0.15758366930162593, 0.1077267856600821, 0.14345994728376643, 0.13913495641252274, 0.1628351435738417, 0.1237922700973976, 0.13377069828833704, 0.12553101623769694, 0.1440337246967679, 0.10463753623096175, 0.13758418983752854, 0.15590183976649183, 0.10689419060080915, 0.15261350750755723, 0.10752545876770003, 0.10766098221760219, 0.10626263361776891, 0.18084661413405886, 0.10629493173454516, 0.10848962397235426, 0.15914814241669534, 0.1397560227806085, 0.1424473039771246, 0.12884254744716497, 0.1409904350272403, 0.1581575975852327, 0.14625746589495514, 0.13576082323033795, 0.12866602555595819, 0.15693221154487713, 0.1258973966904689, 0.10287952995253892, 0.11353886346327006, 0.10977737819075713, 0.1217101499451182, 0.13819564166205603, 0.13048707997284262, 0.102906295565226, 0.10291919615606442, 0.1565396551137654, 0.11294861587414731, 0.14861998815545754, 0.14783261137504358, 0.22949059556374032, 0.11090918951864348, 0.10887026460219044, 0.11375656657136463, 0.1548863210266266, 0.10700157098286088, 0.1352553554793113, 0.1029468231621314, 0.1645855574900723, 0.15418072238061206, 0.14420566465842674, 0.10340441674438025, 0.10704680936080335, 0.1030949219810921, 0.15212971596202254, 0.1521099754994259, 0.14654876498314492, 0.11110742012548558, 0.15262328073614412, 0.10901701995163111, 0.16257899095333206, 0.13204114390458815, 0.15660246319387985, 0.12339995120698488, 0.13798535871913303, 0.12041600392859428, 0.12530079060774638, 0.12405611547993145, 0.12948427292238257, 0.11081441247298829, 0.12369633518375356, 0.22075347523010422, 0.11496350856295473, 0.13647645016993604, 0.12177442586290775, 0.10533150995827051, 0.13927196171466857, 0.12137894514213882, 0.12443735892117173, 0.12294269649879244, 0.10912303855327268, 0.09926275049661312, 0.1010198199789297, 0.11764656912840653, 0.10797965920697232, 0.1559372623004877, 0.1595231205832344, 0.11936728738183308, 0.128794247633241, 0.1236145114035947, 0.16065549934287857, 0.10659815453601128, 0.11872472506897419, 0.14281802371452865, 0.15823035383943776, 0.10960328549891803], [0.14877477425589516, 0.11311576276070683, 0.1216632820533828, 0.1642339830775653, 0.10702395033898648, 0.162787247798613, 0.13168287946312052, 0.16257784331273134, 0.13684408383945124, 0.17568999046571088, 0.10699133665260266, 0.12236343533618228, 0.15776181944278028, 0.11074551871814026, 0.15942133259707778, 0.12145819367260986, 0.15048868631904364, 0.10775163960205442, 0.16511902789690003, 0.10387717415399048, 0.13309835394548195, 0.10617595317010303, 0.12987942066034747, 0.10201645567281042, 0.126907399913905, 0.19823946107620896, 0.12176453865026302, 0.11377618476998211, 0.15597546289288905, 0.14658627913291186, 0.12668473873557837, 0.1127753852961418, 0.13515570134143493, 0.1430153571404359, 0.17427854493369252, 0.1306243457201959, 0.1584840937035551, 0.1161793697871261, 0.12252346139780003, 0.11451741368665348, 0.1654481494741256, 0.11520156397336975, 0.15830495792926375, 0.19916341516498137, 0.18394919805956436, 0.10633951766941033, 0.12354539773706827, 0.2071300520412882, 0.11837194601517449, 0.12863686352834025, 0.13649491635430058, 0.12515542417983877, 0.17142277183136337, 0.14541454363901993, 0.15533124667069542, 0.10940942182100474, 0.12048552392162369, 0.11197003752329027, 0.11151924369819952, 0.13988908786981594, 0.1337819542533619, 0.11729890747105416, 0.13970100924629544, 0.11050957537050118, 0.11284093195130512, 0.13993171562369136, 0.17277400653359148, 0.12071173308408516, 0.12154689418585238, 0.10989445450034718, 0.127278744664179, 0.12105039081557839, 0.13584387975074247, 0.12021569240143247, 0.12644026094083596, 0.15647551939739457, 0.11709013849475347, 0.10817986426940432, 0.17552882504857056, 0.12998710384240839, 0.12254607920793276, 0.16724219915030636, 0.12513365899243925, 0.148952719058311, 0.10739246677612897, 0.1100088078439537, 0.1204170735694258, 0.11044281141191195, 0.17786486428088372, 0.17388276729695681, 0.109965451256382, 0.11155466102925736, 0.1558851193644145, 0.1786979198808784, 0.1422291297201904, 0.1515958926310972, 0.1164744632229547, 0.15968805296811486, 0.22004691449652372, 0.13055913336095995]]
    lossvec0 = [[0.16375364323693128, 0.1598924098297443, 0.16677607930317992, 0.16262309109948725, 0.16188093947140314, 0.157417741665715, 0.15506884850824199, 0.15941718184048764, 0.15282420444100275, 0.15626366688471008, 0.15572577584185382, 0.1575433641097066, 0.15299900810028547, 0.16665926604868425, 0.15828495126999473, 0.15870871088172278, 0.15557799103217498, 0.15833930128595194, 0.16905563020309589, 0.15940674903548974, 0.1608525097363954, 0.15381043349672274, 0.15939318914529807, 0.15545569559840658, 0.15303684755918198, 0.16821064281886222, 0.16245571600502157, 0.16257840155825892, 0.15252489752501308, 0.15433072776901252, 0.16364994795323945, 0.1579890795943676, 0.16436213080867138, 0.1658702895100968, 0.153411180123921, 0.15609545273829709, 0.1618149846666891, 0.16171901079095893, 0.16759210238465078, 0.1533561507927092, 0.1657515925645132, 0.16162558063079147, 0.1655038755360929, 0.1682526500473327, 0.16340195382486064, 0.1541341551722113, 0.16277564260011654, 0.15428475127720326, 0.16089461930114343, 0.1585954843513574, 0.15759429376621722, 0.15989907503786943, 0.1536116293638464, 0.15845502564458225, 0.16052103806227147, 0.16315107870073428, 0.15460359182858768, 0.16485917974241576, 0.15889838329088424, 0.1640656379297554, 0.150144918379174, 0.16377727397633166, 0.16343048272214358, 0.15497442737408612, 0.16053657001895796, 0.1610431061141195, 0.16229444224542286, 0.15972157664991693, 0.15381414185941167, 0.15597832612019064, 0.16562458518880893, 0.15595217942040576, 0.1603847893837301, 0.1611120657905986, 0.1532714356380745, 0.16108526245136187, 0.15630493416137503, 0.15799496190185, 0.15249177037061096, 0.154395096702405, 0.163679403659234, 0.16123106071808255, 0.1566742449677942, 0.15583065139781363, 0.15371728282113395, 0.16451059480697264, 0.15965258390385972, 0.16669918989045673, 0.15856848844392735, 0.15593563711561548, 0.15945917400382678, 0.16444289413535804, 0.16144397531488, 0.16394460887977857, 0.15808940474812164, 0.15516427158986124, 0.16397906625340097, 0.16616934455334773, 0.16338488421250086, 0.16207290278862374]]
    nullmean = -1*np.mean(lossvec0[0])
    lossveclist = [[vec[j]*-1 for j in range(len(vec))]  for vec in lossveclist]
    CIalpha = 0.1
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist:
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (nullmean - (mn-intval))/nullmean
        hiperc = (nullmean - (mn+intval))/nullmean
        print('['+str(loperc)+', '+str(hiperc)+']')
    '''


    # FOR DESIGN 2, DIFFERENT BATCH SIZES
    # BATCH SIZES: 0,3,6,9,15,30,60,90,120
    underWt, mRisk = 1., 0.9
    t = 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design2]
    designNames = ['Design 2']
    omeganum = 100
    random.seed(35)
    randinds = random.sample(range(0, 1000), 100)

    numtestsVec = [0,6,12,24,48,96,192]
    lossveclist = []
    for numtests in numtestsVec:
        lossvec = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                   designnames=designNames, numtests=numtests, omeganum=omeganum, type=['path'],
                                   priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'), 'rb')),
                                   randinds=randinds)
        lossveclist.append(lossvec[0])
    '''
    lossveclist = [[[0.1631624760638568, 0.15720307855535465, 0.1608639458015167, 0.16447283684593733, 0.1597308858525191, 0.16530244555035933, 0.16669312810707285, 0.16160074117278947, 0.1653192236072529, 0.16204418974476908, 0.15497871429023474, 0.15467411765416555, 0.1613750771551091, 0.15747074496261462, 0.15227562871749936, 0.17145553434981564, 0.16369361082463926, 0.16692521749216743, 0.16203792928496977, 0.1590776035470591, 0.1551749348303539, 0.16082428779764713, 0.15756807299460315, 0.1550608320048446, 0.15631195454060692, 0.15770983060319332, 0.16414686544787604, 0.15488810166410838, 0.15665288807970829, 0.1603004871311405, 0.16244412648327097, 0.15682117281806454, 0.16354500356802104, 0.16415919851377875, 0.15638019764514263, 0.16670011136232835, 0.15949899115009494, 0.1615188645137574, 0.15735859905742092, 0.15677491970077437, 0.1632770477454912, 0.14924291956044927, 0.1574308890174942, 0.16345504155976637, 0.16461700092995968, 0.16393482231407522, 0.1567846630510756, 0.1592431152969494, 0.15772433382534407, 0.14844073064826993, 0.1480748185152451, 0.15995265165098485, 0.15794841277723592, 0.1572413873265836, 0.1622471046539544, 0.16417357970743476, 0.15887070770145548, 0.1564296671429403, 0.1540633086236506, 0.1574801602328406, 0.1636280978407651, 0.1614998685157631, 0.1577330744011513, 0.15305409049467894, 0.16450330767712035, 0.15431738262912842, 0.1704341250563957, 0.15808855691643203, 0.1624660034460682, 0.16984983201379783, 0.16483379350966765, 0.17121651483881745, 0.15037817832139538, 0.15245994964489948, 0.15922731238943802, 0.1591623946701067, 0.1593963075601854, 0.1566343324544281, 0.16163975965273666, 0.16063162964748812, 0.15588301419308162, 0.16196747619948323, 0.16966545510320571, 0.1608916131441504, 0.15122267730328054, 0.1650651247623661, 0.163162013176352, 0.16165030963215343, 0.16726574770151145, 0.16236020655648817, 0.16454285631917326, 0.15453297321044887, 0.15539168550866006, 0.17099218057510968, 0.1600247961031962, 0.15695387350753648, 0.15969570999392832, 0.15967241534002483, 0.15652864332227961, 0.1649838594051987]], [[0.13581187716248172, 0.18088862714115198, 0.14489153641861324, 0.1407890279233018, 0.18099237682855351, 0.15058851774690193, 0.14997399229156802, 0.13405129836319882, 0.1442052945685419, 0.13990593804879517, 0.14686913895175827, 0.13689015633381152, 0.15825833334463651, 0.1815645964096146, 0.1392312864075857, 0.15024859546964925, 0.14667756088755204, 0.14088340708901567, 0.14238954947578825, 0.14334681492939508, 0.14183410717710945, 0.14414654634113086, 0.1444406285270409, 0.13975042694172382, 0.15036432400835445, 0.16007652934248065, 0.14755226719130932, 0.14708004565686794, 0.13884124579177187, 0.14808199437738362, 0.15043919026223102, 0.1447327502571794, 0.1404101742113437, 0.14307111180657325, 0.1420086651992926, 0.15240340051086046, 0.1540685557881656, 0.15303892159022828, 0.14174721972850593, 0.15567295973710682, 0.14208117049926242, 0.13543497073953406, 0.1434290143244919, 0.14487970046389403, 0.1451692554592949, 0.14273054643408245, 0.14154632783214213, 0.1509648900603302, 0.14977910684609488, 0.15516179217901366, 0.15569239800788887, 0.13569989975283608, 0.14059720618200708, 0.15964775977376827, 0.14055351842204625, 0.14445754569705252, 0.14552435380923187, 0.15060011430885825, 0.19682336129112152, 0.1903683574375264, 0.1842772537363947, 0.15063892910522259, 0.1382294500548737, 0.15644943240778797, 0.14839469299878627, 0.13895815061869263, 0.1444095705088078, 0.13788217323762736, 0.15468210701031607, 0.14564459557778087, 0.14693029010935366, 0.14528859200546765, 0.16050427169596518, 0.1530289550094832, 0.1495148033249957, 0.213210449112839, 0.13801290826699014, 0.1397220702465254, 0.14627221488870465, 0.1486402228320335, 0.13386334453231388, 0.14637002483055592, 0.15927541239996018, 0.13909176608991983, 0.14393482580935285, 0.13604924855685532, 0.1446532141515603, 0.15002242300858432, 0.13783426467544038, 0.13613361461439094, 0.1497411624166203, 0.20920103718358576, 0.14629665588874954, 0.1422246470857519, 0.14659394524923242, 0.14394487105738138, 0.14183764842635366, 0.19323757398993724, 0.13556382099079836, 0.1451395814757909]], [[0.18250358204412992, 0.16148098124961843, 0.12839932339079688, 0.15672744084363527, 0.1236965873930104, 0.1732208782318235, 0.16444273963228168, 0.1383937539435883, 0.13461374609421037, 0.12464911699160307, 0.13380000131927153, 0.1345942646438583, 0.16222490930144065, 0.1374486203265875, 0.16924316524462518, 0.13602391077235956, 0.19670178193515164, 0.1304784903017601, 0.1855368215016094, 0.12942812562539657, 0.12579055814705958, 0.13072814535600158, 0.1288847727307339, 0.12365249220149874, 0.14475954300849617, 0.1304974813610493, 0.13163237320284552, 0.1362757588501883, 0.14821494389290768, 0.13500820823463172, 0.13529793028374304, 0.13346513967924808, 0.129413822416884, 0.1354694120103084, 0.11691750795007518, 0.14021563306086918, 0.13686511787576583, 0.13349473953440835, 0.12795460504596465, 0.13182268156110855, 0.18032903559200306, 0.13744321271789525, 0.1365412412357825, 0.1264862396557037, 0.17363579626438524, 0.12810388335802037, 0.19156492836423558, 0.1613974791338099, 0.13749925395367715, 0.16864379790131992, 0.12204610523256679, 0.13253489057588766, 0.20036361972145506, 0.18205079662820556, 0.1378226373699295, 0.1667300729686068, 0.13136362971124302, 0.13832406732540026, 0.12947892119556578, 0.13370736362099322, 0.13093123393684697, 0.13483078492074185, 0.13366181365761268, 0.1426682244255122, 0.13198976597000767, 0.13269250216552264, 0.14079333298919827, 0.1311633318368286, 0.13525013341227063, 0.14286439858609642, 0.13790607413260783, 0.12701338386215708, 0.16994924704784165, 0.12531213972928887, 0.13685080325884527, 0.13633526650814323, 0.12744034509470006, 0.17796580695259642, 0.13109099441689367, 0.13770691002294608, 0.12796634554414835, 0.1331673374439455, 0.13440078597581784, 0.18790347655597167, 0.12878761506753905, 0.12468058134705738, 0.12475278052998261, 0.12881583944100122, 0.13135572150594654, 0.17322114423383167, 0.17014296165318699, 0.14245614243153948, 0.13948090010677042, 0.13596371647110053, 0.12795486778809745, 0.13022707616928467, 0.13636115857758888, 0.19657861395814205, 0.15924553913809517, 0.1345624158289855]], [[0.13570451893533322, 0.11635223574434869, 0.1256451024333039, 0.18948313529010136, 0.11559979032588766, 0.10893972772081377, 0.11313580685054267, 0.12370476478519414, 0.13839439611233917, 0.1629628730855595, 0.11974600981702214, 0.11435542228016754, 0.16433463246018323, 0.11955706614376678, 0.16589876740269288, 0.11432966749158172, 0.11551439339645653, 0.12218630591181527, 0.11628324636211212, 0.12395470906913884, 0.11169793772837039, 0.12070611077820546, 0.15141033110468774, 0.11177276572728483, 0.15029610818865607, 0.11374903247222835, 0.162802928424843, 0.11753697183111571, 0.12216549732580197, 0.11474152470517027, 0.14179128892601683, 0.1125132748800997, 0.11973779463359568, 0.12854093452484935, 0.10714570996268372, 0.14503578536079625, 0.11587088671477333, 0.15231125963445186, 0.10973792645125388, 0.11527345640620716, 0.2025767939032954, 0.12289979638040857, 0.11464327172380251, 0.12480868160308102, 0.17674161404261826, 0.11579580157614061, 0.1386445778429723, 0.1169880707554564, 0.1427359095691076, 0.15601841020488802, 0.11772953264711931, 0.1301140698995478, 0.11753850270780004, 0.13982908912711328, 0.15346186382729518, 0.15313671656286498, 0.1197289223167537, 0.11186341731235729, 0.17318799644354838, 0.11683510128917025, 0.17146668299833043, 0.12026935830383821, 0.12232029530514908, 0.1192946894231301, 0.12109914534460886, 0.12452617803225705, 0.17241253310049087, 0.11850239600287675, 0.12293090132133262, 0.10967874322323147, 0.13903479154969348, 0.11725072481657112, 0.11766609832301213, 0.11985197737046831, 0.1221416456601214, 0.1765522951841584, 0.12129733008688068, 0.1134210161749199, 0.11602765149492833, 0.12658745249306133, 0.13762755203193308, 0.11923606665276021, 0.18087580053637842, 0.13719880695624678, 0.12272892186949456, 0.12278166400657407, 0.12403960031104742, 0.11680768902227226, 0.12055971143524773, 0.11934707321956482, 0.18391342726744792, 0.15207662697013485, 0.1451226165990153, 0.14957990099154284, 0.11862251373004483, 0.11632017196762018, 0.12527758250108947, 0.1756748507838016, 0.14211874017383444, 0.11745123129327636]], [[0.13329208393734157, 0.11583100256719034, 0.11699971047050861, 0.1389236237831767, 0.11728088296406526, 0.15927387818506378, 0.09993633454736307, 0.10145099364402332, 0.10446922146352544, 0.09976693815003991, 0.10074011894095757, 0.1530023982640726, 0.1600934263394793, 0.11820980344175945, 0.11644466279786862, 0.11683536671947423, 0.1371583067940968, 0.09479323675314252, 0.12482974726304848, 0.09809522880546265, 0.10760962428190683, 0.1135432581053243, 0.11110714474089285, 0.11372175496873044, 0.09943659885492057, 0.12086045031101444, 0.13866207035871822, 0.11118414883780167, 0.1049355213866362, 0.1054228585489571, 0.12772614946142177, 0.09920909088539452, 0.12510147034192703, 0.11190955115481835, 0.10072978700960758, 0.10157204242927649, 0.14095960695876275, 0.09999014491882113, 0.13415067509446757, 0.13510823726602264, 0.15512749732717276, 0.10165183014286679, 0.1014749537214115, 0.11709633662601626, 0.14265316415106183, 0.10089250448004243, 0.1435554100664769, 0.12085596962959352, 0.14919355764285874, 0.11971624235720744, 0.0972650158682408, 0.10259768991889323, 0.12925654597228753, 0.1199594487766792, 0.1154715265598492, 0.09775157838084517, 0.09675154712163658, 0.12116703276756423, 0.119226290440266, 0.11834869573768328, 0.11733180854795892, 0.10205633911471416, 0.10883229933309704, 0.13583286178813547, 0.10282297489104764, 0.10036882038944343, 0.1547645502041658, 0.11660641862034014, 0.09836694376418521, 0.10239956581284843, 0.1560749231336755, 0.09764611510766617, 0.12408486069106871, 0.09763579266012276, 0.1254653830370869, 0.16514701132909315, 0.1018045064109485, 0.11767443047297492, 0.12541355769670937, 0.10616690663410389, 0.11700474272034976, 0.10522482002330098, 0.15084010535997822, 0.1269140513159294, 0.12324154173248335, 0.08970446102301344, 0.12181409060420273, 0.1073828159144149, 0.10561077761860922, 0.13033592021404597, 0.11926490156097953, 0.150246045622258, 0.10027586077379336, 0.14077517937624118, 0.10568570603126527, 0.09735820773338127, 0.10190673562776277, 0.1471287405273993, 0.14992573624710748, 0.12883472543978747]], [[0.11494506208495954, 0.1337968321798901, 0.10238452347452903, 0.12906741093563373, 0.11986047171662009, 0.1330251076055999, 0.09238037937775384, 0.09197262129900947, 0.07484835963866172, 0.09845783906379947, 0.1020100305024721, 0.11712332135813398, 0.1432112074067134, 0.09344991955945123, 0.12903006658005442, 0.11242077378634843, 0.10295972836665614, 0.08335401564240826, 0.10861634028425433, 0.0814922383954625, 0.0769338126288505, 0.08986126873465908, 0.10013852060860105, 0.09154100344667224, 0.10708104718327785, 0.13192601872046023, 0.14640675020539365, 0.07536560987745247, 0.08942689698627615, 0.09915926678131923, 0.12109153048012979, 0.08085889645635173, 0.09799767945583633, 0.08354492243496325, 0.07385738354979805, 0.1175491220717664, 0.09578426632928301, 0.08589369908630308, 0.10737584960032863, 0.0849276435116206, 0.12577727317469592, 0.11038424682424505, 0.09020077019372354, 0.11345432182432931, 0.24580739531536394, 0.09603283213000918, 0.1364179160205298, 0.08164646458010737, 0.12378060221355881, 0.09888029421675641, 0.08370762321221493, 0.08214472210796538, 0.13991223466048205, 0.11361192561863581, 0.1150973532401751, 0.10257234895492394, 0.1243103446600755, 0.09448803638433781, 0.1274055810369723, 0.0783179018009859, 0.1187084192387218, 0.0958110158759459, 0.13592843047889355, 0.08579380010695789, 0.10094833173172983, 0.07826154518609332, 0.13464212297577446, 0.10529620452614691, 0.10269732943437512, 0.08581252528205399, 0.13508541617985714, 0.09291917203556142, 0.08774903884688831, 0.09093741455449755, 0.08085541876696124, 0.13233491715717366, 0.09660537882155995, 0.07967028239148777, 0.09351945922722224, 0.1408768098975076, 0.09042838899621128, 0.09121814709224821, 0.09476318126264975, 0.1354665294306039, 0.11463809058694811, 0.08036836441013294, 0.10857675617461776, 0.08341317599521254, 0.09757034021292911, 0.10480925007028068, 0.11622411897158384, 0.10774251174768286, 0.11066882418764855, 0.11249061642125523, 0.0897527495148978, 0.11358430648161802, 0.11739009394170238, 0.10523298350338137, 0.13407347454371515, 0.13511955940736783]], [[0.10890848781633254, 0.1133356485696745, 0.07064482127366399, 0.10569264630545602, 0.08922211625187597, 0.09872194453621007, 0.07514003327207945, 0.10814086666187434, 0.07236887458937012, 0.09878848504727773, 0.06441454678278218, 0.10601374491681129, 0.1229642423380818, 0.062213142296897984, 0.11827915281464987, 0.07461681670908228, 0.10198559068668574, 0.05990317094036642, 0.10287535077393598, 0.07020419147531322, 0.07312325644545985, 0.10350480256501712, 0.13796306657388527, 0.07056350151038053, 0.09919369137172204, 0.1733242705057, 0.10002466569575638, 0.07011273603387087, 0.08119330504742452, 0.08381883696467846, 0.08941098371421931, 0.14929470953629198, 0.08220918188410035, 0.08052465617742176, 0.08319065231744295, 0.08999127888027143, 0.11891600717198234, 0.1049012563842765, 0.09161638609116679, 0.08064278577583472, 0.14790011059396543, 0.07584408172234296, 0.0817764831055534, 0.11911911205850889, 0.12851511281388195, 0.07000937352672702, 0.11710772681688797, 0.14895857082688058, 0.09352571393182547, 0.09570707696287445, 0.07357864839129169, 0.10334720065864347, 0.10746693212246393, 0.07707641046478622, 0.1096184511669006, 0.09593522318773293, 0.1040381908892987, 0.06875006171291183, 0.09739883902100333, 0.1066678368657045, 0.07289987815291553, 0.08140529847146624, 0.1071444556310915, 0.0974546336187453, 0.08898324996597545, 0.06329920600418695, 0.10060997637989454, 0.12515544619502458, 0.09082929413442496, 0.08385078760708657, 0.09486932373308271, 0.06416279451985338, 0.0839713247635342, 0.08366495220202823, 0.09689250870167869, 0.13211648302883078, 0.07129381914445027, 0.10484322177744372, 0.08437180728495527, 0.12248003184078611, 0.1148488990927233, 0.06657301662364348, 0.08792659324697018, 0.1065641192011026, 0.08488387420295669, 0.08435463370326114, 0.0922770382030507, 0.0823573207197824, 0.07027300562416364, 0.09940578018224441, 0.1099781380510958, 0.1037303838266235, 0.13650593084081242, 0.09244556463801218, 0.11863693117574707, 0.06913125271764804, 0.10345161868613349, 0.11715768427160357, 0.11628658585177734, 0.08890223275966946]]]
    lossveclist = [lossveclist[i][0] for i in range(len(lossveclist))]
    lvecnames = ['0','6','12','24','48','96','192']
    plotLossVecs(lossveclist, lvecnames,plottitle='Design Utility vs. Batch Size\n$|\Omega|=100$')
    
    qts50 = [np.average(lvec)*-1 for lvec in lossveclist]
    stds = [np.std(lvec) for lvec in lossveclist]
    qts5 = [qts50[i]-1.96*stds[i]/np.sqrt(len(qts50)) for i in range(len(qts50))]
    qts95 = [qts50[i]+1.96*stds[i]/np.sqrt(len(qts50)) for i in range(len(qts50))]
    
    fig = plt.figure()
    x = numtestsVec
    y = qts50
    lowerr = [y[i]-qts5[i] for i in range(len(x))]
    upperr = [qts95[i]-y[i] for i in range(len(x))]
    err = [lowerr, upperr]
    plt.errorbar(x, y, yerr=err, capsize=4, color='orange', ecolor='black', linewidth=3, elinewidth=0.5)
    plt.ylim(-0.2,0)
    plt.xlabel('Batch size', fontsize=12)
    plt.ylabel('Design utility', fontsize=12)
    plt.suptitle('Design utility vs. batch size: Design $x_2$\n95% confidence intervals for $|\Omega|=100$', fontsize=16)
    fig.tight_layout()
    plt.show()
    '''


    return

def designUtilityCaseStudySenegal():
    '''
    Complete design utility calculations for de-identified case study data
    '''
    import os
    import pickle
    #import pandas as pd

    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
    filesPath = os.path.join(SCRIPT_DIR, 'MQDfiles')
    outputFileName = os.path.join(filesPath, 'pickleOutput')

    openFile = open(outputFileName, 'rb')  # Read the file
    dataDict = pickle.load(openFile)

    numPostSamps = 1000
    MCMCdict = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    meanSFPrate = dataDict['df_ALL'][dataDict['df_ALL']['Final_Test_Conclusion'] == 'Fail']['Sample_ID'].count() / \
                  dataDict['df_ALL']['Sample_ID'].count()
    priorMean = sps.logit(meanSFPrate)  # Mean SFP rate of the MQDB data
    priorVar = 1.416197468

    SEN_df = dataDict['df_SEN']
    # 7 unique Province_Name_GROUPED; 23 unique Facility_Location_GROUPED; 66 unique Facility_Name_GROUPED
    # Remove 'Missing' and 'Unknown' labels
    SEN_df_2010 = SEN_df[(SEN_df['Date_Received'] == '7/12/2010') & (SEN_df['Manufacturer_GROUPED'] != 'Unknown') & (
                SEN_df['Facility_Location_GROUPED'] != 'Missing')].copy()

    # Divide Senegal data into operational batches
    SEN_df_2010.pivot_table(index=['Date_Received'],columns=['Final_Test_Conclusion'],aggfunc='size',fill_value=0)
    '''
    Final_Test_Conclusion  Fail  Pass
    Date_Sample_Collected
    BATCH 1: 218 SAMPLES            
    6/4/2010                  0     1
    6/23/2010                 3     5
    6/24/2010                21    51
    6/25/2010                 6    44
    6/26/2010                 0    18
    6/28/2010                 3    29
    6/29/2010                 7    30
    BATCH 2: 16 SAMPLES
    7/13/2010                 0    14
    7/14/2010                 0     2
    BATCH 3: 58 SAMPLES
    9/3/2010                 11    39
    9/4/2010                  0     8
    BATCH 4: 114 SAMPLES
    9/30/2010                 7    51
    10/1/2010                15    41
    '''
    SEN_df_batch1 = SEN_df_2010[(SEN_df_2010['Date_Sample_Collected'].isin(['6/4/2010','6/23/2010','6/24/2010','6/25/2010',
                                                                            '6/26/2010','6/28/2010','6/29/2010']))].copy()
    SEN_df_batch2 = SEN_df_2010[(SEN_df_2010['Date_Sample_Collected'].isin(['7/13/2010', '7/14/2010']))].copy()
    SEN_df_batch3 = SEN_df_2010[(SEN_df_2010['Date_Sample_Collected'].isin(['9/3/2010', '9/4/2010']))].copy()
    SEN_df_batch4 = SEN_df_2010[(SEN_df_2010['Date_Sample_Collected'].isin(['9/30/2010', '10/1/2010']))].copy()

    tblBatch1 = SEN_df_batch1[
        ['Facility_Location_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tblBatch2 = SEN_df_batch2[
        ['Facility_Location_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tblBatch3 = SEN_df_batch3[
        ['Facility_Location_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tblBatch4 = SEN_df_batch4[
        ['Facility_Location_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tblBatch1 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tblBatch1]
    tblBatch2 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tblBatch2]
    tblBatch3 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tblBatch3]
    tblBatch4 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tblBatch4]

    # DEIDENTIFICATION

    # Replace Manufacturers
    orig_MANUF_lst = ['Ajanta Pharma Limited', 'Aurobindo Pharmaceuticals Ltd', 'Bliss Gvis Pharma Ltd', 'Cipla Ltd',
                      'Cupin', 'EGR pharm Ltd', 'El Nasr', 'Emcure Pharmaceuticals Ltd', 'Expharm',
                      'F.Hoffmann-La Roche Ltd', 'Gracure Pharma Ltd', 'Hetdero Drugs Limited', 'Imex Health',
                      'Innothera Chouzy', 'Ipca Laboratories', 'Lupin Limited', 'Macleods Pharmaceuticals Ltd',
                      'Matrix Laboratories Limited', 'Medico Remedies Pvt Ltd', 'Mepha Ltd', 'Novartis', 'Odypharm Ltd',
                      'Pfizer', 'Sanofi Aventis', 'Sanofi Synthelabo']
    shuf_MANUF_lst = orig_MANUF_lst.copy()
    random.seed(333)
    random.shuffle(shuf_MANUF_lst)
    # print(shuf_MANUF_lst)
    for i in range(len(shuf_MANUF_lst)):
        currName = shuf_MANUF_lst[i]
        newName = 'Mnfr. ' + str(i + 1)
        for ind, item in enumerate(tblBatch1):
            if item[1] == currName:
                tblBatch1[ind][1] = newName
        for ind, item in enumerate(tblBatch2):
            if item[1] == currName:
                tblBatch2[ind][1] = newName
        for ind, item in enumerate(tblBatch3):
            if item[1] == currName:
                tblBatch3[ind][1] = newName
        for ind, item in enumerate(tblBatch4):
            if item[1] == currName:
                tblBatch4[ind][1] = newName
    '''
    # Replace Province
    orig_PROV_lst = ['Dakar', 'Kaffrine', 'Kaolack', 'Kedougou', 'Kolda', 'Matam', 'Saint Louis']
    shuf_PROV_lst = orig_PROV_lst.copy()
    random.seed(333)
    random.shuffle(shuf_PROV_lst)
    # print(shuf_PROV_lst)
    for i in range(len(shuf_PROV_lst)):
        currName = shuf_PROV_lst[i]
        newName = 'Province ' + str(i + 1)
        for ind, item in enumerate(tbl_SEN_G1_2010):
            if item[0] == currName:
                tbl_SEN_G1_2010[ind][0] = newName
    '''
    # Replace Facility Location
    orig_LOCAT_lst = ['Dioum', 'Diourbel', 'Fann- Dakar', 'Guediawaye', 'Hann', 'Kaffrine (City)', 'Kanel',
                      'Kaolack (City)', 'Kebemer', 'Kedougou (City)', 'Kolda (City)', 'Koumpantoum', 'Matam (City)',
                      'Mbour-Thies', 'Medina', 'Ouro-Sogui', 'Richard Toll', 'Rufisque-Dakar', 'Saint Louis (City)',
                      'Tambacounda', 'Thies', 'Tivaoune', 'Velingara']
    shuf_LOCAT_lst = orig_LOCAT_lst.copy()
    random.seed(333)
    random.shuffle(shuf_LOCAT_lst)
    '''
    KEY
    for i in range(23):
        print('District '+str(i+1)+': '+shuf_LOCAT_lst[i])
    District 1: Thies
    District 2: Mbour-Thies
    District 3: Kaolack (City)
    District 4: Richard Toll
    District 5: Ouro-Sogui
    District 6: Dioum
    District 7: Diourbel
    District 8: Velingara
    District 9: Medina
    District 10: Saint Louis (City)
    District 11: Kebemer
    District 12: Kaffrine (City)
    District 13: Guediawaye
    District 14: Hann
    District 15: Tambacounda
    District 16: Kolda (City)
    District 17: Kedougou (City)
    District 18: Fann- Dakar
    District 19: Matam (City)
    District 20: Kanel
    District 21: Tivaoune
    District 22: Koumpantoum
    District 23: Rufisque-Dakar    
    '''
    # print(shuf_LOCAT_lst)
    for i in range(len(shuf_LOCAT_lst)):
        currName = shuf_LOCAT_lst[i]
        newName = 'District ' + str(i + 1)
        for ind, item in enumerate(tblBatch1):
            if item[0] == currName:
                tblBatch1[ind][0] = newName
        for ind, item in enumerate(tblBatch2):
            if item[0] == currName:
                tblBatch2[ind][0] = newName
        for ind, item in enumerate(tblBatch3):
            if item[0] == currName:
                tblBatch3[ind][0] = newName
        for ind, item in enumerate(tblBatch4):
            if item[0] == currName:
                tblBatch4[ind][0] = newName
    # Swap Districts 7 & 8
    for ind, item in enumerate(tblBatch1):
        if item[0] == 'District 7':
            tblBatch1[ind][0] = 'District 8'
        elif item[0] == 'District 8':
            tblBatch1[ind][0] = 'District 7'
    for ind, item in enumerate(tblBatch2):
        if item[0] == 'District 7':
            tblBatch1[ind][0] = 'District 8'
        elif item[0] == 'District 8':
            tblBatch1[ind][0] = 'District 7'
    for ind, item in enumerate(tblBatch3):
        if item[0] == 'District 7':
            tblBatch1[ind][0] = 'District 8'
        elif item[0] == 'District 8':
            tblBatch1[ind][0] = 'District 7'
    for ind, item in enumerate(tblBatch4):
        if item[0] == 'District 7':
            tblBatch1[ind][0] = 'District 8'
        elif item[0] == 'District 8':
            tblBatch1[ind][0] = 'District 7'
    '''
    # Replace Facility Name
    orig_NAME_lst = ['CHR', 'CTA-Fann', 'Centre Hospitalier Regional de Thies', 'Centre de Sante Diourbel',
                     'Centre de Sante Mbacke', 'Centre de Sante Ousmane Ngom', 'Centre de Sante Roi Baudouin',
                     'Centre de Sante de Dioum', 'Centre de Sante de Kanel', 'Centre de Sante de Kedougou',
                     'Centre de Sante de Kolda', 'Centre de Sante de Koumpantoum', 'Centre de Sante de Matam',
                     'Centre de Sante de Richard Toll', 'Centre de Sante de Tambacounda',
                     'Centre de Sante de Velingara',
                     'Centre de Traitement de la Tuberculose de Touba', 'District Sanitaire Touba',
                     'District Sanitaire de Mbour',
                     'District Sanitaire de Rufisque', 'District Sanitaire de Tivaoune', 'District Sud',
                     'Hopital Diourbel',
                     'Hopital Regional de Saint Louis', 'Hopital Regionale de Ouro-Sogui', 'Hopital Touba',
                     'Hopital de Dioum',
                     'Hopitale Regionale de Koda', 'Hopitale Regionale de Tambacounda', 'PNA', 'PRA', 'PRA Diourbel',
                     'PRA Thies',
                     'Pharmacie', 'Pharmacie Awa Barry', 'Pharmacie Babacar Sy', 'Pharmacie Boubakh',
                     'Pharmacie Ceikh Ousmane Mbacke', 'Pharmacie Centrale Dr A.C.', "Pharmacie Chateau d'Eau",
                     'Pharmacie Cheikh Tidiane', 'Pharmacie El Hadj Omar Tall', 'Pharmacie Fouladou',
                     'Pharmacie Kancisse',
                     'Pharmacie Keneya', 'Pharmacie Kolda', 'Pharmacie Koldoise',
                     'Pharmacie Mame Diarra Bousso Dr Y.D.D.',
                     'Pharmacie Mame Fatou Diop Yoro', 'Pharmacie Mame Ibrahima Ndour Dr A.N.', 'Pharmacie Mame Madia',
                     'Pharmacie Ndamatou Dr O.N.', 'Pharmacie Oriantale', 'Pharmacie Oumou Khairy Ndiaye',
                     'Pharmacie Ousmane',
                     "Pharmacie Regionale d' Approvisionnement de Saint Louis", 'Pharmacie Saloum', 'Pharmacie Sogui',
                     'Pharmacie Teddungal', 'Pharmacie Thiala', 'Pharmacie Thierno Mouhamadou Seydou Ba',
                     'Pharmacie Touba Mosque Dr A.M.K.', 'Pharmacie Ya Salam', 'Pharmacie du Baool Dr El-B.C.',
                     'Pharmacie du Fleuve', 'Pharmacie du Marche']
    shuf_NAME_lst = orig_NAME_lst.copy()
    random.seed(333)
    random.shuffle(shuf_NAME_lst)
    # print(shuf_NAME_lst)
    for i in range(len(shuf_NAME_lst)):
        currName = shuf_NAME_lst[i]
        newName = 'Facility ' + str(i + 1)
        for ind, item in enumerate(tbl_SEN_G3_2010):
            if item[0] == currName:
                tbl_SEN_G3_2010[ind][0] = newName
    '''

    # Summarize characteristics of each PMS batch
    batch1_Manu_Count = [0 for i in range(len(orig_MANUF_lst))]
    batch1_Dist_Count = [0 for i in range(len(orig_LOCAT_lst))]
    for samp in tblBatch1:
        batch1_Dist_Count[int(samp[0][9:])-1] += 1
        batch1_Manu_Count[int(samp[1][6:]) - 1] += 1
    batch2_Manu_Count = [0 for i in range(len(orig_MANUF_lst))]
    batch2_Dist_Count = [0 for i in range(len(orig_LOCAT_lst))]
    for samp in tblBatch2:
        batch2_Dist_Count[int(samp[0][9:]) - 1] += 1
        batch2_Manu_Count[int(samp[1][6:]) - 1] += 1
    batch3_Manu_Count = [0 for i in range(len(orig_MANUF_lst))]
    batch3_Dist_Count = [0 for i in range(len(orig_LOCAT_lst))]
    for samp in tblBatch3:
        batch3_Dist_Count[int(samp[0][9:]) - 1] += 1
        batch3_Manu_Count[int(samp[1][6:]) - 1] += 1
    batch4_Manu_Count = [0 for i in range(len(orig_MANUF_lst))]
    batch4_Dist_Count = [0 for i in range(len(orig_LOCAT_lst))]
    for samp in tblBatch4:
        batch4_Dist_Count[int(samp[0][9:]) - 1] += 1
        batch4_Manu_Count[int(samp[1][6:]) - 1] += 1

    batchNames = ["Batch 1", "Batch 2", "Batch 3", "Batch 4"]
    distNames = ['District '+str(i+1) for i in range(23)]
    manuNames = ['Mnfr. ' + str(i + 1) for i in range(25)]
    # Print batches and districts
    data = np.array([batch1_Dist_Count,batch2_Dist_Count,
                     batch3_Dist_Count,batch4_Dist_Count]).T
    row_format = "{:>15}" * (len(batchNames) + 1)
    print(row_format.format("", *batchNames)) # Header row
    for dist, row in zip(distNames, data):
        print(row_format.format(dist, *row))
    # Print manufacturers and districts
    data = np.array([batch1_Manu_Count, batch2_Manu_Count,
                     batch3_Manu_Count, batch4_Manu_Count]).T
    row_format = "{:>15}" * (len(batchNames) + 1)
    print(row_format.format("", *batchNames))  # Header row
    for manu, row in zip(manuNames, data):
        print(row_format.format(manu, *row))



    MCMCdict = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    numPostSamps = 1000
    priorMean = -2.5
    priorVar = 3.5

    lgDict = util.testresultsfiletotable(tblBatch1, csvName=False)
    lgDict.update({'diagSens': 1.0, 'diagSpec': 1.0, 'numPostSamples': numPostSamps,
                   'prior': methods.prior_laplace(mu=priorMean, scale=np.sqrt(priorVar / 2)), 'MCMCdict': MCMCdict})
    lgDict = lg.runlogistigate(lgDict)
    numSN, numTN = lgDict['importerNum'], lgDict['outletNum']


    return

def checkMCMCexpectation():
    '''Check that using the expectation of the next data set is providing the right bounds'''
    numTN, numSN = 3, 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5, 0.05, 0.1, 0.08, 0.02]

    # Generate a supply chain, with no testing data
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked', randSeed=86, trueRates=trueSFPrates)
    exampleDict[
        'diagSens'] = s  # bug from older version of logistigate that doesn't affect the data but reports s,r=0.9,0.99
    exampleDict['diagSpec'] = r
    # Update dictionary with needed summary vectors
    exampleDict = util.GetVectorForms(exampleDict)
    # Populate N and Y with numbers from paper example
    exampleDict['N'] = np.array([[6, 11], [12, 6], [2, 13]])
    exampleDict['Y'] = np.array([[3, 0], [6, 0], [0, 0]])
    # Add a prior
    exampleDict['prior'] = methods.prior_normal()
    # MCMC settings
    exampleDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    exampleDict['importerNum'] = numSN
    exampleDict['outletNum'] = numTN

    # Generate posterior draws
    numdraws = 20000
    numdrawspost = 1000
    exampleDict['numPostSamples'] = numdraws
    exampleDict = methods.GeneratePostSamples(exampleDict)

    design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    type = ['path']
    numtests = 10
    sampMat = design * numtests

    omeganum = 1000

    randinds = random.sample(range(numdraws), omeganum)
    randindsold = randinds.copy()
    availrandinds = [i for i in range(numdraws) if not i in randindsold]
    randinds = random.sample(availrandinds, omeganum)

    # Specify the score, risk, market
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'name':'Parabolic', 'threshold': t}
    marketvec = np.ones(5)
    lossDict = {'scoreFunc': score_diffArr, 'scoreDict': scoredict, 'riskFunc': risk_parabolic, 'riskDict': riskdict,
                'marketVec': marketvec}
    designList = [design]
    designNames = ['Design 1']

    # MCMC
    lossveclist1 = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                    designnames=designNames, numtests=numtests,
                                    omeganum=omeganum, type=['path'], randinds=randinds, numpostdraws=numdrawspost)
    # FOR GENERATING 95% INTERVAL ON LOSS
    CIalpha = 0.05
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist1:  # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (mn - intval)
        hiperc = (mn + intval)
        print('[' + str(loperc) + ', ' + str(hiperc) + ']')
    # print(lossveclist1)
    '''
    design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    type = ['path']
    numtests = 25
    underWt, t = 2., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'threshold': t}
    marketvec = np.ones(5)
    lossveclist1 = [[0.17478897520707512, 0.16708343358922592, 0.16017359950903826, 0.17763440364866198, 0.18612522673663937, 0.17019821319931183, 0.17259716939132502, 0.18498861916818107, 0.1721680367649012, 0.17373722601960379, 0.18043613592416716, 0.1935490065581854, 0.17745183559801503, 0.17193996836200248, 0.17464067607427342, 0.1906983361259786, 0.16469455305010594, 0.16859867506801282, 0.1627290402987992, 0.17372202186963645, 0.17369069189402148, 0.19631855172433765, 0.17427274038454532, 0.16158215330897768, 0.18441893193949443, 0.16991136591211692, 0.1826468213116312, 0.18225411809926975, 0.17385929673400838, 0.18598585106328758, 0.17328158422073414, 0.17743057096521142, 0.1778204636961944, 0.17816423003367282, 0.16920864937896649, 0.19314248194697353, 0.1753093222614526, 0.17050314780625764, 0.17348960596476068, 0.17574367966940707, 0.16528746582110126, 0.17605217850602942, 0.16541437603065556, 0.1753039015705461, 0.17575846366425799, 0.18614387039469338, 0.18646008137667336, 0.1907434482383348, 0.17771731680931424, 0.1824380234652812, 0.16477440262090404, 0.1924394107592297, 0.16161276668918428, 0.17251896096987684, 0.18085929595167952, 0.17168960840660197, 0.1692771291710887, 0.18771425389335678, 0.18648605398679183, 0.17591800955915088, 0.17370612912797923, 0.17842234674748775, 0.164942462166284, 0.17729333701348762, 0.17565538830435806, 0.17789487155539918, 0.17161660978362603, 0.1735985672145525, 0.17120617411654077, 0.17634457404502707, 0.17762337493975475, 0.16339709169530278, 0.18348453244388666, 0.19605749050889665, 0.18352403149179922, 0.1617331403593286, 0.17175097734155556, 0.18140679178843408, 0.17097872855145765, 0.17255484179655492, 0.16380509857450848, 0.1789297006032058, 0.1672729059726472, 0.17665146845299334, 0.16132518105157945, 0.170774851643822, 0.18252887009508054, 0.18591791676679686, 0.17300099406753686, 0.16824737147715968, 0.17093020677842832, 0.1735257422253561, 0.17662335208036795, 0.18480088871925474, 0.17058267794159612, 0.1690116575544472, 0.17292713468043658, 0.16010399136782097, 0.1678216749193966, 0.17827730680593915, 0.17008866888009735, 0.1702332263805651, 0.16877240994334197, 0.17123391588525952, 0.17058017959570324, 0.17922114656666724, 0.17823519312199823, 0.1701012038281456, 0.17690981240550166, 0.18256589673193724, 0.17689579174602196, 0.16796259133712227, 0.17220830262284717, 0.17858403372663245, 0.18332166555072282, 0.17057777894714637, 0.17514228570927468, 0.17652633175159926, 0.188031418422593, 0.1777648581090775, 0.168785370546456, 0.17561993876738838, 0.18622599166599244, 0.17567143148007663, 0.15840351975733052, 0.18281184098104056, 0.18788191026845233, 0.17529196931443422, 0.17844732997524554, 0.18711106048955903, 0.16588230381352576, 0.17257195575065692, 0.17061101774784163, 0.1796912125710871, 0.17133563843007119, 0.180542576755474, 0.17835379754830968, 0.16135155255838513, 0.17685512361240194, 0.17207459253769977, 0.1764784742356905, 0.17995301450922332, 0.18691517237203362, 0.16763704048709327, 0.18063268791071335, 0.16845319822335825, 0.17025832917406186, 0.15342654895902508, 0.1831518906909722, 0.1869521655663587, 0.16286077828397805, 0.1680871540958664, 0.18627491142968003, 0.17190629804193405, 0.17404545553736117, 0.17146891828382904, 0.1714332852272796, 0.18045679443013135, 0.17090852207965004, 0.16995578387468085, 0.179058835299655, 0.17997620445438586, 0.1629166727798137, 0.17480194648673217, 0.1611605585581672, 0.17788853806491645, 0.18927843060864818, 0.18075102239373483, 0.1754968094919827, 0.18174822224857487, 0.17039994048849924, 0.18436092926230896, 0.18185037109550423, 0.18612840586947255, 0.16523792712232463, 0.17346673334557325, 0.17431057281601262, 0.19673512402203774, 0.17594711772775207, 0.18044878546135962, 0.16948814607806437, 0.1771899271157031, 0.16725402144612223, 0.16146649806807695, 0.18133079746781045, 0.16763010703208647, 0.16880166650913508, 0.17388936344685169, 0.18505824125342346, 0.1719115936841025, 0.182811483886676, 0.16133579678744575, 0.18120206054956015, 0.16963385278487916, 0.18294083127231128, 0.17441108963156177, 0.1680677522330322, 0.19624743046982984, 0.17254455984262293, 0.16934158204019079, 0.17931344014970518, 0.17408137081420158, 0.18869588905784665, 0.17850180975880836, 0.17095697226889253, 0.15595877509996975, 0.1744689863206535, 0.1608719561590468, 0.17472889943598005, 0.1828644199797822, 0.17660433799648262, 0.16482319978355206, 0.1674077292909562, 0.17154894695837963, 0.1664890673791777, 0.16597002944656927, 0.1789946496899007, 0.17640326689072597, 0.17766933040601612, 0.18473322494861769, 0.17229299001254128, 0.18151878295418808, 0.1658721591292754, 0.16771126609364337, 0.16430932106819926, 0.18744380540640582, 0.16508431454742728, 0.18771007612303942, 0.16466222347488388, 0.17807442307397137, 0.17109121836892335, 0.17117750674484905, 0.1754887857724018, 0.17495545620211905, 0.1766060369464701, 0.16557502053167622, 0.16511525789451229, 0.17024701148734528, 0.17739127754831246, 0.1767089210133802, 0.16338343819937884, 0.1922984817494502, 0.1775504204750422, 0.19373887654761754, 0.16256480064035536, 0.16838480602080108, 0.17942684294175829, 0.17481226854468349, 0.18574311032406957, 0.1761018036368211, 0.20155762156107018, 0.1757759110933566, 0.18725905823830305, 0.1647481258821238, 0.17416107771194334, 0.1863634971149948, 0.17065200649481105, 0.17733824096325662, 0.15959576388429197, 0.17765539026096533, 0.17460757365402427, 0.17632180836198594, 0.1718910985469936, 0.15656675358412514, 0.187257772481352, 0.17209788218179514, 0.16961692889921098, 0.17781321635014097, 0.1730405868738756, 0.16557047027559607, 0.1752361001574934, 0.17396964988836958, 0.17198634791070413, 0.18000489024106084, 0.16831466404614304, 0.1765481769896628, 0.18031545742564548, 0.17172664761528533, 0.1763364415883569, 0.17145846786291472, 0.17431889732804617, 0.16808527984641078, 0.17572443104969174, 0.17874830605975892, 0.1615085466648508, 0.17884587576585145, 0.18848715024092172, 0.1789773115150821, 0.17705637030944932, 0.17019747273643943, 0.18034215859190472, 0.17349017362989003, 0.17626370851897424, 0.18397614361416384, 0.1594787379882482, 0.18210408746839424, 0.1701029760712412, 0.1673757042652016, 0.16653917116411313, 0.18980159402482635, 0.18160502089553954, 0.1787136235666546, 0.17543502952590526, 0.16221836937600992, 0.17623898191777979, 0.172482774481058, 0.1906414362706463, 0.17219617453897, 0.16810703735104146, 0.1699826079097929, 0.17251690358526436, 0.17552294502138704, 0.1699617246506306, 0.1817580791174456, 0.16288817613168302, 0.15360255984857216, 0.16642516799948037, 0.17356643300180738, 0.17124384300156245, 0.182436332139095, 0.18083228563053977, 0.17643117319940893, 0.1647661253821439, 0.1790662090511203, 0.18004201093592284, 0.17441763607802074, 0.16632012190355372, 0.168608477820961, 0.17532880648167076, 0.17032133432304383, 0.169135354295349, 0.1803301948105329, 0.1904109859064672, 0.17590206088116764, 0.17386485619044795, 0.17967369103709865, 0.17684718935382907, 0.17702752646792355, 0.17616123003402145, 0.18893854430997054, 0.16857299067710638, 0.1768815442438422, 0.17355840461677188, 0.18158899552342078, 0.2019479247378795, 0.17146523977704714, 0.19360023972302462, 0.17977314487483323, 0.16718221606222866, 0.17826796572553022, 0.16565060222685876, 0.15513410781029868, 0.16606390024303422, 0.16723274793064793, 0.171745254412792, 0.17409159903001517, 0.16782997609127653, 0.1721514652844221, 0.16970565310707145, 0.17044698717449078, 0.17953392496588605, 0.1645175630622336, 0.1662855838477503, 0.18648143537202355, 0.1739647431241033, 0.18470256607234906, 0.190443629632187, 0.18033993348973007, 0.17200911953512343, 0.16667068194867404, 0.18418022286798622, 0.17197360922521435, 0.1737689729178993, 0.17643383535826368, 0.17628834487888032, 0.16930552360130677, 0.18325001326201001, 0.1694495176146427, 0.17027151343448657, 0.18807619746419713, 0.16660542969642658, 0.18214269140352002, 0.16708311872379075, 0.16890303507943338, 0.17985156083627674, 0.18594296803998525, 0.18022763908465436, 0.16681795572724747, 0.18244299354471627, 0.16204260234298923, 0.15894601926918345, 0.1870778248733162, 0.17689358724210924, 0.1784663376372705, 0.16730647055284184, 0.18189571177796401, 0.15998304774512676, 0.17500996094257867, 0.17899620264354293, 0.17621971127011418, 0.1748037644810344, 0.1722893615345774, 0.1686813228975515, 0.17021031733892347, 0.16132824156625972, 0.1849725029458772, 0.1775614177967211, 0.18322556961204065, 0.16810180875763486, 0.17404689146726757, 0.1771293460547257, 0.16974188544312463, 0.18799358726048956, 0.1780402374543352, 0.20080680924210303, 0.16387567626761068, 0.1812727063249185, 0.17478740330494497, 0.1607609305527386, 0.18353847002261928, 0.18116029542038145, 0.1584288155904812, 0.18585739939850898, 0.1769983983304018, 0.17991790363789767, 0.171002750857757, 0.16820172299917857, 0.17270516949863934, 0.16178444424377383, 0.17546735368662567, 0.17362375089610838, 0.1799745573781648, 0.17839708698648546, 0.1910955713922686, 0.1807746648102084, 0.17355250230966632, 0.16291882902107102, 0.15521753719571924, 0.1785331426768132, 0.15975067906695334, 0.1582547077896294, 0.19068794643035708, 0.1828742965575897, 0.16228743652531416, 0.17904276482886078, 0.1713285498108599, 0.17648973639260832, 0.16982838587586233, 0.1823389392282129, 0.16780714635956345, 0.18634141011096284, 0.17591193771423536, 0.17866876377718505, 0.1911879029072369, 0.15947625608638458, 0.18306084135837797, 0.16521001693740592, 0.1800922033647937, 0.18135664414391234, 0.1753764871119222, 0.18863566213797342, 0.1757607838005683, 0.17508721705052688, 0.16445327441173593, 0.169299924721498, 0.16813407328551092, 0.18433824547043764, 0.17386402143754479, 0.1865527106925061, 0.18237254282737195, 0.17229003666873027, 0.1862018612662109, 0.1804576330512435, 0.17121041829449024, 0.1706598131760911, 0.17643629272901615, 0.1694413602408407, 0.17683043917116778, 0.1725889983413928, 0.16477201398026559, 0.17888604135613914, 0.1635926426012485, 0.17632039517789347, 0.1775718089439338, 0.17597014018716217, 0.1801722203871879, 0.18043601658584993, 0.16518931359947286, 0.17756623573704178, 0.17673525630769155, 0.17004092483921865, 0.1879405018329316, 0.16884226157694962, 0.17430138639566145, 0.16654837731957636, 0.17679802552040288, 0.17426458923268393, 0.16693614134852922, 0.15819861264214893, 0.1841160723906055,0.1710524336747628, 0.17766817258861403, 0.17584947261276224, 0.17923555638777092, 0.17559915129708722, 0.17277683728840573, 0.17799750124742, 0.1806050345823527, 0.17735199812790917, 0.16490038498882478, 0.19230976828627966, 0.173567062822859, 0.1754259826202698, 0.18275859320866095, 0.17386103983457352, 0.17775381977358284, 0.18702822591846216, 0.1799138447872059, 0.16355924708692446, 0.18015531942390997, 0.17134790611302386, 0.18545855993002974, 0.17554246186877126, 0.17284283684200596, 0.1752614748867098, 0.17707279899350553, 0.1757013022136798, 0.18438174152691245, 0.19462467957132507, 0.17080192881556655, 0.16564095716803667, 0.16401442848937564, 0.17277465825005175, 0.18125291405799573, 0.19383884707096516, 0.18795095130657635, 0.16869630458902993, 0.1912361820359299, 0.20687835767782667, 0.1668370147039467, 0.17436521543220684, 0.17934275953579748, 0.1772762845104848, 0.18360325826726961, 0.16672734596740704, 0.1845895241924417, 0.16769289898984915, 0.18310381617259727, 0.17917867841426627, 0.19385206096920252, 0.18487866127856362, 0.168779998733585, 0.20296094058579792, 0.1817473084884952, 0.1945101993690265, 0.1709293329368114, 0.18467470173540682, 0.16918761896696513, 0.18648390437778212, 0.17445287446271732, 0.1681044072924868, 0.18819173983203147, 0.17634674322255084, 0.1740120424505506, 0.17263008160348317, 0.18193887514268614, 0.1817624622808306, 0.1731731161439401, 0.1732425503806535, 0.17324952372527552, 0.15501040611898562, 0.1829289520781617, 0.15483944716586398, 0.17293042127574676, 0.1797742630118193, 0.18482329869897415, 0.15997349466542263, 0.16950179684559571, 0.18264354381596823, 0.17784195434580075, 0.1792524035596786, 0.18355944357222373, 0.18390517838460113, 0.18294361358438743, 0.17925774163691482, 0.18621816075760306, 0.18940244356718347, 0.16581728351740438, 0.16993565121104873, 0.16291225519419494, 0.18523313368635674, 0.18342378206078155, 0.1755882371033784, 0.17179735221602369, 0.1700499707516213, 0.16473144448328936, 0.17035294543091242, 0.17882924956826113, 0.20070498317516822, 0.18073457646573607, 0.18730338771432137, 0.1656601652995799, 0.1810365225400075, 0.16456943967802576, 0.17167639207162913, 0.16384384163817803, 0.19686920118589776, 0.17118093813563207, 0.17208122923845412, 0.17269399557506906, 0.18045638258314933, 0.17150484831875054, 0.17269912887232552, 0.18380363660657012, 0.17863843167984306, 0.17215137462865251, 0.1655047416037901, 0.17642059665320808, 0.18086336646512224, 0.17515935303916408, 0.1773774479053979, 0.1855006808307847, 0.18082238126342, 0.18001058684299684, 0.18029261370696806, 0.16361791532524805, 0.16330299867233142, 0.18540278654494863, 0.17860860137878165, 0.1721871258337108, 0.17765560824092483, 0.17324537137002027, 0.1631572577459688, 0.16200580332399586, 0.185489600422746, 0.18574264356057416, 0.17993289647321895, 0.18429415136149968, 0.16180363176710066, 0.17567991198284, 0.17138645914646936, 0.183687121957246, 0.1726350494766209, 0.19564576089211363, 0.16533281905422084, 0.17948540170729627, 0.17701235251670694, 0.17450391005702046, 0.17233389015512354, 0.17801470143992795, 0.174926701514022, 0.17469747022852955, 0.16200543492554445, 0.1601252439465825, 0.16078775274903684, 0.17702849957748867, 0.17910792859749053, 0.18219101329159487, 0.16831988176495047, 0.17234463584795698, 0.19356648999860682, 0.16589315541906136, 0.18208640697926096, 0.17333796571671678, 0.17530637448684178, 0.18393108232738303, 0.19422470011855514, 0.16704693952550964, 0.17631879312655077, 0.17615403550181744, 0.17611799277076864, 0.1785436968406076, 0.18741622519050335, 0.17332344155480148, 0.17922700519992524, 0.17925984940024273, 0.16650360778192186, 0.18618838732934048, 0.18318240896426774, 0.1713903663113845, 0.1562742991385781, 0.1679154136085799, 0.17356935704811538, 0.17611406591221979, 0.17268230890441083, 0.17739495072207884, 0.17706565643989616, 0.16830090971949774, 0.1610432193778967, 0.18880743195186137, 0.1811341028526564, 0.15711986767116934, 0.17805957483490958, 0.16255406198384953, 0.17104502215838047, 0.1687956491296488, 0.17328797100076804, 0.17214975463651458, 0.1746836386887935, 0.18433419195288112, 0.17846192691195423, 0.1711590113986158, 0.1639675416117778, 0.16942660137329169, 0.1700586257948279, 0.1652928597437569, 0.18799378754381335, 0.18749973705238798, 0.1688977758847746, 0.18209122900463057, 0.18100130932306904, 0.1714567151192396, 0.16121737983160925, 0.1762417966489195, 0.17601523066327512, 0.1880196452257232, 0.17119036534363946, 0.19000936983332536, 0.16856359678316793, 0.1760122026887736, 0.18309700059123382, 0.17258332585666813, 0.17375726059334806, 0.16869887645151027, 0.18408925674006574, 0.1573105648118806, 0.17914497503705687, 0.17142427383791034, 0.16833284651466826, 0.17476705187678643, 0.19397463965217737, 0.17505984259035065, 0.17145382902954306, 0.17924382469168568, 0.18146009111263553, 0.16652173113191648, 0.18352708883933017, 0.18302340150416563, 0.16785721341596696, 0.1787308269856939, 0.16851703149285224, 0.17966140108039724, 0.16928863844586423, 0.1775833011063279, 0.18945781152098645, 0.17778047661814073, 0.1703578258002318, 0.17741550238389422, 0.17936109137134942, 0.15823796342588756, 0.1875894500793932, 0.18115254059745808, 0.1765974822249645, 0.15558032117379436, 0.17256698534252038, 0.19445585824737194, 0.17984412178711726, 0.17215390447749448, 0.18398834258618046, 0.17533481754416738, 0.17663053446370494, 0.16678047777851618, 0.16784505864910476, 0.15980942246472862, 0.16859739610583363, 0.18524521437102467, 0.16250852914887529, 0.18979649474264945, 0.1685284933908294, 0.1815271513858229, 0.18111536809635884, 0.17976371844003214, 0.17651201114637494, 0.1760929930911672, 0.18026646696441828, 0.18775544654136672, 0.1802974545192525, 0.16896514442980745, 0.16034296778016882, 0.17912010220269753, 0.1730866273638073, 0.17293214957261752, 0.17959822917206694, 0.18101751156923981, 0.17482585073265033, 0.1852857501763946, 0.18159853504831272, 0.16974976165703756, 0.18524857653408053, 0.1705878938876453, 0.1764842468596479, 0.17103629835104037, 0.19529763513585024, 0.17091884868086707, 0.1809880565169177, 0.17950114552155905, 0.16780720195055276, 0.191457410633709, 0.1788945474810223, 0.18151717106086104, 0.18009644961158164, 0.17719411583643613, 0.16857284202573838, 0.18708503949197783, 0.19534092730686672, 0.17815488044253533, 0.19004416948158348, 0.16499374552304472, 0.17935172713208383, 0.16872043996003283, 0.19228136813015212, 0.17923184496134564, 0.1662487532777683, 0.17896895073562594, 0.17823145063813872, 0.1611256717860196, 0.16213776743642172, 0.1791249367981474, 0.18379895213411418, 0.1728434704730654, 0.18300906511474765, 0.16660620165717713, 0.17495531093100988, 0.1806944558403042, 0.180566056933618, 0.17351415265947145, 0.182897575463335, 0.17598071938309154, 0.1815425109985247, 0.17729465154640833, 0.17125306464507958, 0.18026690427306977, 0.17693506846688536, 0.18539583558258035, 0.18213733450043215, 0.18848629854834673, 0.18183541015465093, 0.16524849542065048, 0.1821967800572661, 0.17033067470699062, 0.1754527826965785, 0.1915322070578989, 0.16948894083013846, 0.18362873030899077, 0.19539982422849134, 0.1629633401071343, 0.1925847561865572, 0.16839527083427683, 0.1842948560404079, 0.18052762749997256, 0.16540093250545826, 0.17834363039399406, 0.17879697403159703, 0.17847429268723958, 0.17277067455778888, 0.18195196515487308, 0.18215487294353258, 0.17456992205033378, 0.17088676319153787, 0.16501195616020273, 0.15520953882894153, 0.16644888118793427, 0.17559796400402422, 0.17307019436079066, 0.19260566420123726, 0.18744051134666392, 0.16140493355814536, 0.19594120680967972, 0.18092376223347892, 0.1750209169101816, 0.17326923837710775, 0.16921809616068445, 0.16825969064517277, 0.1850735750095027, 0.16858441894901474, 0.18963657154871325, 0.1748411848125565, 0.1787209275758893, 0.1679036254236309, 0.17444970469200813, 0.170868225823292, 0.18602293588270366, 0.1765201719412969, 0.1744187573694735, 0.16843106424628626, 0.17282652055607195, 0.17355831510137426, 0.17811039933976908, 0.18322255042771146, 0.17865280740854803, 0.1734753512670305, 0.164152605407085, 0.1610959382130183, 0.18335282899432764, 0.1795096459797954, 0.17780163006751673, 0.18094372225466726, 0.18416276309266372, 0.18287198953580056, 0.18810887141548863]]
    95% CI: [0.17509563141458226, 0.1762101843303088]
    lossveclist2 = [[0.1803108446130844, 0.17312250918279118, 0.1780119880000122, 0.18031559596683086, 0.183561409392781, 0.16974825173208474, 0.17607082553279876, 0.18141897497907897, 0.1684829872025379, 0.18567775892491267, 0.1719988754094222, 0.1789747156885836, 0.17635993015474533, 0.16798201076204358, 0.16825483424353507, 0.19848166832417177, 0.17305854579331886, 0.16806590820826645, 0.1737792081606946, 0.16417669425793596, 0.1747852815435128, 0.16956149434194995, 0.17844565291126935, 0.179493212359302, 0.1844146562560593, 0.1778262429381474, 0.17788330653742862, 0.17410848801434503, 0.17592779717936602, 0.17965815134655605, 0.18175097998232173, 0.18290471329142968, 0.1775389926043475, 0.18308318345127036, 0.17805174473134275, 0.17791117082257912, 0.17318266446693747, 0.17455920771467634, 0.17934852981013966, 0.17530491356973374, 0.1694324611759745, 0.20215780071971226, 0.17627510482509942, 0.1794499867160388, 0.16857610410782375, 0.1822464309571806, 0.1941603474085748, 0.17402024172075414, 0.17222716254221138, 0.19175304264323412, 0.17604824122445661, 0.19034349883255283, 0.16489831497997276, 0.16915844687050574, 0.17591103568122587, 0.1722475696717731, 0.15675793268534002, 0.17663773910961705, 0.16785689363630588, 0.1782303057798168, 0.17022119062459679, 0.18200423393488235, 0.16587915439193443, 0.1953442387611299, 0.17083784998279528, 0.16784480567676296, 0.1709228295563493, 0.1748308383686674, 0.17679878758427167, 0.17953068261665, 0.17417708051856118, 0.17623981155698953, 0.1689811676706462, 0.17595806280846144, 0.17241093238263241, 0.17113305549366378, 0.1677272519729483, 0.17548084501445302, 0.17402389960754167, 0.1897241988331814, 0.17695048663486299, 0.18757950784835553, 0.1724203664819928, 0.17371482900810217, 0.18490029793163443, 0.1664065321218713, 0.1873212208101347, 0.1721255652962751, 0.16992627324709986, 0.1810410315250907, 0.1787047298550545, 0.17346385428551206, 0.17705113754855778, 0.17843413920388776, 0.18640175330722217, 0.1825767333902945, 0.18143046631602658, 0.17881443067995145, 0.18343573036507263, 0.1711592050857983, 0.17865498490765438, 0.16724567173876473, 0.17918626351195274, 0.16622368674957738, 0.16202205983390927, 0.19568999462044667, 0.1865219051827019, 0.17512248931081564, 0.17526308694245182, 0.18911365864146998, 0.17779347896134862, 0.1684307037165717, 0.16703865150556782, 0.16978423519789962, 0.18637479268635673, 0.16453067460760804, 0.16385699797745382, 0.18498872475849013, 0.1881566306530152, 0.17352037466271533, 0.16204457071573394, 0.16204457071573394, 0.1850880775306425, 0.18305693580313445, 0.18319122505753618, 0.16438634470009791, 0.18454054638865253, 0.17808873126095875, 0.16543194904469427, 0.18082290437127962, 0.17256632419208234, 0.18159764490896702, 0.18397506709451503, 0.1842562135071291, 0.19437968947216278, 0.1718450159812233, 0.18199014053660822, 0.1781401504103083, 0.18509461426547916, 0.16428276598497074, 0.178485697316849, 0.17754058420621022, 0.19210458893658156, 0.1636680544316483, 0.17466802572005147, 0.1720309369574394, 0.16759126737160246, 0.17000487878293266, 0.1739904401653445, 0.16885193780418553, 0.17507418803133173, 0.17981847317437086, 0.16232221334099495, 0.16472283831839862, 0.18064542431717348, 0.17101445590227354, 0.1888826149056275, 0.1702063412226413, 0.1737687096724933, 0.16670877021658562, 0.18230429846731666, 0.1744971074113708, 0.17852867014684526, 0.179463406098017, 0.17239240431831152, 0.17510366645959283, 0.1757523019064548, 0.1736275138852457, 0.17155042110022053, 0.18383901128946403, 0.17265659516897391, 0.17446903829093002, 0.18847353247749823, 0.17751803655162737, 0.17276414548004462, 0.16807676044217473, 0.16721500683353463, 0.17351785796591648, 0.1793999169315873, 0.1663393352689014, 0.1866916996650609, 0.17382614592293225, 0.1752186513917689, 0.17382477478618746, 0.17750639239123447, 0.17357457528504922, 0.17705044399374614, 0.17550954307516978, 0.17668462254159867, 0.17370219055331104, 0.18210578306140454, 0.16562810498114727, 0.18537873571731986, 0.16753671447951315, 0.1811601774751171, 0.16739352142867808, 0.1704140433652054, 0.17598211266998828, 0.1613359574816443, 0.1712895671593607, 0.16315247024710258, 0.17505629007494178, 0.1816717870957307, 0.1809983166405279, 0.16863436140262195, 0.1679601424705018, 0.1759040110122578, 0.17718901312160817, 0.17519839550392868, 0.1807300550466195, 0.16632743339465839, 0.16980094540066526, 0.18261398696500092, 0.17290322810154127, 0.15774147820634574, 0.17863386020239386, 0.18573274346932084, 0.16477454942630207, 0.1824966716269673, 0.18481392123532017, 0.17346442178125593, 0.18257728881198063, 0.17788578130103663, 0.16424489138928458, 0.17311193326290109, 0.17641266023553845, 0.1634178279324944, 0.18762864371112042, 0.18523729917461493, 0.1689409829760406, 0.18036376600479642, 0.1829127995915933, 0.1772644841748614, 0.18275587107199187, 0.17034796904216576, 0.15338696764599347, 0.17813012903482106, 0.16833656840207742, 0.1837707666658566, 0.19316204480486954, 0.18437185485572533, 0.18738557103463582, 0.1702505772339814, 0.18128664974937847, 0.17847132024598641, 0.17093205747715975, 0.17341885806510557, 0.15820000489653424, 0.17940723903805572, 0.16523424945109796, 0.18812414030328883, 0.18278810983212626, 0.18865405637329216, 0.189308142054743, 0.18162382662408416, 0.19026864947672475, 0.183510699974481, 0.17012319000672224, 0.19265343386283745, 0.16925207959221478, 0.19009047888539157, 0.1689446628707243, 0.1708403734584984, 0.16456947007336087, 0.18595011155167096, 0.18080338887599495, 0.160870001461125, 0.16475257674216964, 0.17094867607633432, 0.17498752830347017, 0.18404126174260416, 0.1708485512165421, 0.18171954971137214, 0.18372933579684733, 0.17206890925638293, 0.177694649636433, 0.18226901792470257, 0.17412543002515532, 0.16902366453195594, 0.17904208698013965, 0.17425619803917913, 0.17483729990839328, 0.17231095411860517, 0.17697038878197027, 0.16501090379342023, 0.1751469464735431, 0.18028256258999087, 0.18283506401022365, 0.1796998485334401, 0.17943683049570122, 0.17912979583394645, 0.1783729506895626, 0.17062065892378356, 0.1718636535113693, 0.1771482321660936, 0.17579281299781466, 0.17165296915609146, 0.19271746312926435, 0.17263130273186744, 0.1874945019847396, 0.18567670989189772, 0.16856499323847657, 0.18329326963775894, 0.1643920667709853, 0.1604378805484652, 0.18972989654858352, 0.18086091577288652, 0.18294414185815322, 0.16768717645192788, 0.1816374124260411, 0.1848292608881215, 0.16742963419439374, 0.17681446862424438, 0.17739438975929558, 0.1819699858527335, 0.1573010107564525, 0.1803909428813951, 0.18318055690159646, 0.16731504895147423, 0.16614880033724735, 0.1836953548433797, 0.18511548048225146, 0.18763240943335344, 0.17566448688840022, 0.17994256414614124, 0.18006806158309732, 0.18196877918968096, 0.17828683059981434, 0.16986144213098778, 0.17679486712905207, 0.16808325040192346, 0.16908687984645682, 0.17308507886397823, 0.18068324444155281, 0.17068862835129028, 0.16767005217932537, 0.17120550335185106, 0.18205621771849545, 0.18186318261818984, 0.1809508887659669, 0.18277928001646307, 0.17083576442603965, 0.1705851508151171, 0.17727448619744246, 0.1820132574586436, 0.16673444876461044, 0.18277403906468034, 0.1791680292823741, 0.1671700106650084, 0.1714904887838445, 0.17237835975988813, 0.15982493938171916, 0.17055825465157542, 0.16474100459129298, 0.1702618597582787, 0.17459425822962585, 0.16820123644949417, 0.17181130177101553, 0.17229094689823737, 0.17831685706561157, 0.1794369916690781, 0.16467238421017827, 0.17024187172440367, 0.17435808400550462, 0.1749994957601941, 0.17906557415409924, 0.16484165048084162, 0.16744025532236648, 0.17292258698167365, 0.17219100655815897, 0.18270537487714955, 0.18837844654155483, 0.16406612252619543, 0.17605285025780745, 0.1759190557998683, 0.17102024946860012, 0.19219841558008033, 0.17077342621690977, 0.1761699455324085, 0.17828427365294053, 0.172867814382441, 0.1728118846816062, 0.1739647764406308, 0.17865788768051316, 0.19250348623826088, 0.18394968259143543, 0.16884286773532606, 0.1677977013081496, 0.17235723823439963, 0.17060637565496714, 0.1690346251479, 0.17972976311157515, 0.17378351840794082, 0.17174267312158087, 0.1718592428445981, 0.1792687971673399, 0.17785111580943982, 0.17426410547017998, 0.17125448302516916, 0.17797988003952483, 0.174907381143929, 0.16857330315155225, 0.16915272150153887, 0.19316487629185183, 0.18780826184966506, 0.18573689802466997, 0.17898642181273455, 0.18541193902162842, 0.16893035170577003, 0.1848636078594202, 0.18513571250635985, 0.1705843857792778, 0.16560215755593657, 0.18926425958188686, 0.17722251837993697, 0.17659900065722334, 0.1761627657779624, 0.17157706586588303, 0.1615656376945573, 0.17551933078359663, 0.1774687464205912, 0.1735254847756782, 0.18311653541302134, 0.18920412356971594, 0.1804330798417347, 0.16422870046189156, 0.18783719347641945, 0.18865351184856352, 0.1705916094275045, 0.17792439860116327, 0.18859254180973653, 0.1692085177940481, 0.1827563782725807, 0.18260554927324898, 0.17092636248996917, 0.1738829712883823, 0.17416423512472248, 0.16638551586941847, 0.19128978624408127, 0.17684228841986158, 0.17429385941187234, 0.18014280305061478, 0.19026605401502247, 0.15978012451228427, 0.18183378091387178, 0.17847623755531278, 0.18003444481077438, 0.1703524714096313, 0.1820556490817027, 0.18060793112251683, 0.18223622152553043, 0.16487758437511327, 0.1770949313369457, 0.18797249254866638, 0.17230676340961515, 0.17636380696272336, 0.16477627725353464, 0.17105730293613558, 0.171426653060421, 0.18752712122963938, 0.1776480869068309, 0.17369123633355235, 0.17744704410789222, 0.17782586639428086, 0.1707334075023324, 0.16334741018636878, 0.18285060953544496, 0.19317257336807833, 0.1800207991363361, 0.1881286367624471, 0.17559389215397117, 0.16942216721777353, 0.16996384728901817, 0.1812580622093901, 0.1805845482630746, 0.17655136961618922, 0.1807793019415952, 0.1655421070903925, 0.17857525627955856, 0.1698902780332646, 0.1668135714822074, 0.16855428001765094, 0.17116876766473738, 0.17974009912069885, 0.174099135739103, 0.17396906611174964, 0.1801054386159195, 0.17806657623419858, 0.1676174347377515, 0.19535779353017002, 0.16962183651633397, 0.17671428609115558, 0.17312868412054053, 0.17199736748474512, 0.1721553018386921, 0.16863870055087402, 0.1694153244059132, 0.17573002989042666, 0.17997583021939909, 0.17908176529169265, 0.18186072928847047, 0.18228587481437777, 0.16120592914721693, 0.16784265253189004, 0.18545635165990176, 0.16558390577230953, 0.1806882902425928, 0.18285015492414988, 0.17130619410323444, 0.17603668647629842, 0.1708928113014574, 0.16752095995541308, 0.17681774030734773, 0.19086221432958414, 0.16962715808076306, 0.19013005216081647, 0.17466033943352857, 0.17687541841324678, 0.16532016419625545, 0.19444213143203282, 0.17451931552645553, 0.17506210848114925, 0.18704487888784643, 0.184275840733084, 0.16736121279583382, 0.19114004340428267, 0.19645560541569096, 0.176533746571335, 0.17574407778856857, 0.17240945578287595, 0.15731382580202508, 0.16728817285522726, 0.16421984849362692, 0.17988146725235704, 0.17449587701708882, 0.18235378880867525, 0.16812540529541198, 0.19809707729333786, 0.17593367016199646, 0.17313943868838333, 0.1818603642510086, 0.18324197836932934, 0.18676463260209172, 0.17842210692872126, 0.16915937060332806, 0.18166922088456056, 0.16406024557555357, 0.17187326720455834, 0.1751155076507147, 0.18912616432251134, 0.17058108868779162, 0.17692107828151193, 0.18559147963320033, 0.17716540303416148, 0.16829598482556626, 0.15521330651590984, 0.17699104371874977, 0.16597161324116427, 0.1787528728335843, 0.1758031660968657, 0.16874758852748903, 0.17182020378568016, 0.1690496242137196, 0.17486462722142215, 0.18030098537413006, 0.18641086337662416, 0.1873557943168466, 0.1684855786506083, 0.18694714620346758, 0.17433685765051382, 0.1782968322157994, 0.1788182364979389, 0.17415816377029908, 0.1701448307332478, 0.17292243996777534, 0.1824012160179148, 0.16936486562530328, 0.18609116537036494, 0.1693665036532475, 0.18247042250286316, 0.17154658340688544, 0.1697054294361039, 0.18258824902952583, 0.18600413835557122, 0.17333766307243983, 0.18139652061827935, 0.18109634709212488, 0.1858387321637565, 0.1705278182868215, 0.18510373007436687, 0.17148284504723688, 0.17418364980964893, 0.1741246870111348, 0.17687474737088096, 0.17244219431773494, 0.1711540817367655, 0.16893348297432365, 0.1841994355436083, 0.17796986782689755, 0.17636905295924477, 0.1792290160651938, 0.1833284847945405, 0.1636603172928403, 0.18068209970139848, 0.1935847960876629, 0.18377885898930982, 0.1771165763921887, 0.1854793787392086, 0.1721366308413443, 0.1781522918180977, 0.17302238241007326, 0.17542947773856607, 0.17657196315085788, 0.17797138459923878, 0.1784710242849738, 0.17154592305807592, 0.16808084621137845, 0.19464216317570546, 0.16486225334338137, 0.18028055202658236, 0.17669085705343346, 0.17902931266172722, 0.18230567461636865, 0.18268448555074346, 0.17506427595509316, 0.18014432891515864, 0.17698712690398224, 0.1829176601273743, 0.17445726751180432, 0.17995897857786108, 0.17296998149053597, 0.17372793640953266, 0.17807654360573064, 0.1638605816013306, 0.16614826227282523, 0.17261755415756713, 0.1677294979088937, 0.17312466679216518, 0.1558235527454223, 0.16520525693382832, 0.16914900990869783, 0.17964551409893703, 0.17146919071914493, 0.19902321730793943, 0.17400012668023887, 0.16682843862015995, 0.1687230658381482, 0.16942367155003565, 0.17280372013965672, 0.1712332708676809, 0.16992201632396545, 0.17288264477393742, 0.16902391912111672, 0.1752776007835248, 0.16612457071896564, 0.18883524679114572, 0.18592287678303085, 0.17888139696991906, 0.1688656069416448, 0.17287073618173676, 0.18225085289918785, 0.1794331973082863, 0.17103152799842775, 0.17859688515536074, 0.1728725585584095, 0.17086703040070958, 0.18094960301309235, 0.166908557867228, 0.17066705130575618, 0.1772253900263553, 0.16996521179748417, 0.1762817562495611, 0.19001689755428883, 0.1705074217535779, 0.17310569529799336, 0.16856335408127635, 0.17792972712687719, 0.17313903496823727, 0.17669654818283714, 0.17868180855728052, 0.1640369256850049, 0.17971572682639003, 0.1776609340803019, 0.17865443383058943, 0.1669447583234133, 0.18744310323549687, 0.17635294436777546, 0.16872195089713882, 0.17435897561367025, 0.1778730439562697, 0.18430196429927134, 0.17392281086214714, 0.17985666828176713, 0.17679469536906742, 0.1618159798164631, 0.1819545083783046, 0.16815853325633023, 0.17435005643880466, 0.17560091919677118, 0.18002656775996667, 0.1637629424631523, 0.1782932187971519, 0.17556019468348907, 0.1719106787452632, 0.17939096715305833, 0.18430498453904004, 0.17781121192862692, 0.17858405331607674, 0.1628040350882254, 0.1780711264162252, 0.1707143768839645, 0.17636771247506894, 0.18390236295296358, 0.16809342113153183, 0.18606682925866055, 0.18288880400385832, 0.17261165497530104, 0.17826098634317228, 0.17098949915284092, 0.17998514131310936, 0.17876340618046707, 0.16237147025175214, 0.17590339482134715, 0.16519793898027887, 0.17366619540040368, 0.16760251802608395, 0.17229286784480724, 0.1654541414618499, 0.1697698202802833, 0.19231056580755854, 0.1932014551985128, 0.17636791625860743, 0.17420641971299577, 0.17988960258917888, 0.17464945798858733, 0.16646862350602565, 0.17511762537397838, 0.18245560011654616, 0.16808294709857824, 0.16916567035891486, 0.17203614625712366, 0.1758359771907728, 0.18017627503473813, 0.18000276839922802, 0.1806727394417852, 0.18817304603193885, 0.1823899024610281, 0.17397296597517337, 0.1590183810382466, 0.16459000891808814, 0.18703378486271635, 0.17920024349977848, 0.18431635643441216, 0.1610263409367323, 0.18393693573838846, 0.17612586565991667, 0.1735545852883954, 0.17148611809214132, 0.18294117233254747, 0.18605562825333943, 0.18221989735230815, 0.17356323453727326, 0.1773524609011892, 0.16732021321565077, 0.17035433536897218, 0.17302323753198995, 0.17082218483963715, 0.18409235750356906, 0.17643910120200682, 0.18569273822867008, 0.17114811318696277, 0.1877379088514768, 0.17415656113928188, 0.17429293410503935, 0.18469291765341622, 0.16818907948454004, 0.17772949853980755, 0.18223646374043398, 0.17618541625654413, 0.1706299362351589, 0.17725739458288148, 0.16866901136821805, 0.1766452268132426, 0.1859835160309745, 0.1670656469856031, 0.19553071183982265, 0.167717903308636, 0.1698383307265613, 0.1769444775640914, 0.1692806324805704, 0.19420453272907026, 0.18265008826121973, 0.19238073259025373, 0.1890981733882145, 0.17689992121271986, 0.183628237786967, 0.18118199741783006, 0.1715839677187899, 0.16347759655886088, 0.17511524551614496, 0.1784388966850192, 0.17681032923053006, 0.15946546599123093, 0.16882946653066067, 0.18346369125066853, 0.18055339717521662, 0.18209462383483588, 0.17923826518922512, 0.16690984809470602, 0.17169147925557457, 0.17743074482988344, 0.18872877237862729, 0.17427132990961355, 0.18026973245208133, 0.1757297658413234, 0.16445155626811964, 0.17267036069358163, 0.17120185964077086, 0.1764498124215547, 0.1783329630870615, 0.17052336553106276, 0.17592736589566277, 0.16275492119909118, 0.1692683111095433, 0.17159710972660072, 0.17105802936767991, 0.17394776653905225, 0.1722377046617272, 0.1765162823506499, 0.1907595223333655, 0.1682683542495847, 0.17611196810220017, 0.17044859444753932, 0.18855674159116573, 0.1842528508329355, 0.1798972323253962, 0.18019076262689762, 0.19034593271890948, 0.18732493169314682, 0.16737678475237033, 0.17192737999891464, 0.1762724801900677, 0.17582468264057644, 0.17633749354515493, 0.18590646403968833, 0.16695284719412232, 0.1728548147507093, 0.1888811009357806, 0.17358478056317053, 0.18166809743819334, 0.16081023976665412, 0.1728952383710692, 0.17151275899423876, 0.17716185600473372, 0.184243969692396, 0.1673700026484108, 0.18372108245391008, 0.1634914961272759, 0.18878638673482734, 0.16531898957595884, 0.16343646093147793, 0.17666855073728302, 0.19865273558962546, 0.17672510321443463, 0.18905812194595498, 0.18418758475084882, 0.17303543125647633, 0.17252900207867056, 0.18044265035678886, 0.16589024532367042, 0.17085926759588002, 0.17176701175379372, 0.18251960958039048, 0.16892832947482384, 0.16586893026613062, 0.17188376510847955, 0.17721010006679722, 0.17712372669792512, 0.1887407336244444, 0.18009678323246917, 0.17981794471707638, 0.1832212467410029, 0.18584925502672042, 0.17385503962917814, 0.16828285824858613, 0.17911908956487563, 0.15822611129656103, 0.1861873995246743, 0.17684113944447716, 0.17458236369186494, 0.16288084078209106, 0.1839125181360584, 0.16263529454080974, 0.17282457128531525, 0.16853994943300268, 0.17095559984343844, 0.18510307165607043, 0.1782785160696454, 0.1852751358954774, 0.16464393357361465]]
    95% CI: [0.17554819626038604, 0.17656226534126807]

    design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    type = ['path']
    numtests = 10
    underWt, t = 1., 0.1
    scoredict = {'name': 'AbsDiff', 'underEstWt': underWt}
    riskdict = {'threshold': t}
    marketvec = np.ones(5)
    lossveclist1 = [[0.14569831093518176, 0.15141243819737987, 0.15263406313432154, 0.15306395131241343, 0.15258367276036552, 0.15480545590140937, 0.16926954826179869, 0.148590111389018, 0.15188023264754158, 0.1512637161328664, 0.15083503777599958, 0.15319726226308242, 0.14250102421072278, 0.15590773585314266, 0.1495508614433647, 0.15239816842978862, 0.1605326619117468, 0.13906313161468442, 0.14770462605168344, 0.14821810122609191, 0.15133491312520508, 0.14478109572165984, 0.14956966808454392, 0.1556404223693784, 0.14591398076084122, 0.1620826977454037, 0.16257578624709437, 0.15387008172678732, 0.14852211911203525, 0.1577397603641584, 0.151795514192045, 0.15068119855363338, 0.1582103201711663, 0.1530754940536564, 0.15195281319562454, 0.1559327265884932, 0.1525571741153522, 0.1538576368921155, 0.15994011851892803, 0.17015621754116134, 0.13787617248958453, 0.1404073011928146, 0.1500940474667674, 0.16215281536679738, 0.14909493950118827, 0.15369912099824382, 0.14233654376548296, 0.14910339523163074, 0.15149667295777966, 0.14660256653365988, 0.14808362918148674, 0.15292888654301404, 0.15789096439763384, 0.15462775570055595, 0.15321424750977658, 0.14236149389673652, 0.14455506653731381, 0.1530074745875051, 0.14401962553287856, 0.1467370269801018, 0.16118731503415265, 0.1517866884114435, 0.1512230058739357, 0.15640278991331125, 0.14353533311937106, 0.14704250018907072, 0.15456277073490407, 0.14698229376336536, 0.14143496162819252, 0.1561999123352945, 0.14503697992688638, 0.1492540783994305, 0.15374347525689613, 0.15367960298853334, 0.16082975414515766, 0.1475565067389573, 0.1514521826741259, 0.16134153705036072, 0.1513597250729103, 0.14908364441082997, 0.1584367469924668, 0.151669795263639, 0.1608956707466485, 0.15418649732747286, 0.14783858799152502, 0.14881660531731813, 0.14807446478494193, 0.15237069820050456, 0.15195803016674, 0.15151014708151214, 0.14114960107726207, 0.14572402087682534, 0.14231567985175997, 0.14046802496769917, 0.15230513279075666, 0.15101909308535374, 0.15770052769016435, 0.14701356351783917, 0.15649630437343476, 0.14281086337666446, 0.15011296049073158, 0.15135455413656537, 0.14112136661080188, 0.15206741756524036, 0.1560593615475478, 0.14970256627218437, 0.14486295533721075, 0.15301925339708788, 0.1587873619625404, 0.1500669729841626, 0.17006414104805617, 0.1589799783517872, 0.1466462917123654, 0.14716465392532588, 0.15311371283911526, 0.15612464154008485, 0.15419424737487114, 0.1482532807920151, 0.14574262468218868, 0.1695387473207709, 0.149365187903937, 0.15528422350835502, 0.15268770633435133, 0.14373366798045747, 0.14670529590548204, 0.158428909525973, 0.15300214120463138, 0.1425517782562156, 0.15525060172072794, 0.1568848245878084, 0.1522927384688738, 0.14454638939100262, 0.1552463012995824, 0.14604357660372078, 0.15016281215330426, 0.14605068840102564, 0.15089359764029114, 0.15151878812611666, 0.14869554750131717, 0.16156288346459735, 0.15604076121626453, 0.1600773222824689, 0.1472851549428304, 0.1359520133573433, 0.14944088564861885, 0.14970899369244375, 0.15685100568393326, 0.14674373567789253, 0.14610249468699937, 0.15285622601248963, 0.1514209186081637, 0.14720945695066515, 0.17075886751339303, 0.1500509583949196, 0.1502212535574294, 0.1514928204346778, 0.14206261821212304, 0.15572402836201404, 0.15370030964753814, 0.15421683940702233, 0.14691949419845274, 0.14623021542289422, 0.14593326456088387, 0.15864048811509826, 0.15112865281512192, 0.15085042614949387, 0.1363184935371765, 0.1456940254842878, 0.14872141641940131, 0.1486972943483676, 0.16079619579808496, 0.15278813245929646, 0.1482502120395343, 0.15223637456980882, 0.16189161161349835, 0.15982701469528232, 0.15613168632920701, 0.15104037421855898, 0.1523053672424733, 0.14066088541713262, 0.15671647616053241, 0.1477656478224851, 0.1476448869177104, 0.1528758073405508, 0.15338067389947288, 0.1384336021511807, 0.1526631728881926, 0.14646568004120314, 0.15050540491885755, 0.14794788888860944, 0.15305867833069373, 0.1613771450794928, 0.14707397479388767, 0.14868314112685116, 0.14965542475635085, 0.14896509046967057, 0.15365609114695072, 0.142693288352425, 0.15002959790842768, 0.14838397084665214, 0.1504849433653141, 0.1443387334058128, 0.1470666507571295, 0.1483295482645403, 0.15195475850501602, 0.15256988431351726, 0.14541371948917511, 0.15512344384277635, 0.15420259325838234, 0.15631210751904598, 0.14187428655096332, 0.1743133470030728, 0.14449032211422735, 0.14492088495889507, 0.15508193912132848, 0.15180082875496287, 0.15891130384316998, 0.142478540209136, 0.14835475676172263, 0.1447602275286261, 0.15234088352927563, 0.14852618327780912, 0.14947372801023745, 0.16020616427031717, 0.15292225423487862, 0.15611043707640154, 0.14218642408056545, 0.14550738520667053, 0.14913183905835514, 0.14976388563155538, 0.1420466429860469, 0.15836906773102663, 0.1580188710792859, 0.14991457736043864, 0.16054273518179915, 0.15828320623976985, 0.15236384653468857, 0.15148931007220767, 0.14520382046093097, 0.1512486481367462, 0.15620891439658252, 0.15138352167913444, 0.1552954038291232, 0.16123704607301542, 0.15581456457701506, 0.1469070652957371, 0.15242034976363558, 0.1499009263263978, 0.14658226090072804, 0.14643218124328528, 0.14759366327880638, 0.1522908987501938, 0.14711273632109817, 0.1463090567640207, 0.1556807312347868, 0.15108014309500012, 0.14759962930791085, 0.1545401672089125, 0.15397372474631307, 0.1578864366462721, 0.15115573463813656, 0.14567673630043892, 0.1488972995489002, 0.14846060515664314, 0.14559543073979284, 0.14955114051662394, 0.1423343275052389, 0.15419915183237157, 0.14575974839005246, 0.14675974882005943, 0.15477821195340707, 0.1495863810932962, 0.1539319983854452, 0.15000843015232013, 0.15247042431012015, 0.15566876683320124, 0.16062181235818035, 0.1535118052888365, 0.14314654985538167, 0.1548477921940256, 0.1500919940834729, 0.15047216006206188, 0.14352090060597372, 0.153034644437829, 0.14881733943974365, 0.16570737366145594, 0.15297710057965874, 0.14940176267257513, 0.15961843273139606, 0.1540788417182976, 0.1412703516620947, 0.15603105608563236, 0.15008849180833242, 0.15623548737089696, 0.14826256689640924, 0.14639174571508168, 0.1584010740347405, 0.15340657981086764, 0.14835025872178492, 0.1641215579904728, 0.15442908943636124, 0.15887955970241957, 0.14586152953825965, 0.15854673568960562, 0.14059620580381788, 0.1467014609510626, 0.14108548242028282, 0.15779381712298166, 0.15998149594915673, 0.1464343910572472, 0.14987597113014445, 0.15396820184423016, 0.15322415998532132, 0.1456951091534776, 0.15022963907575568, 0.15384127873802608, 0.14334439941464164, 0.15502338091532314, 0.1500166369175261, 0.14793970993776062, 0.16170091921293428, 0.1473948070438314, 0.15440387763331886, 0.14906850176108113, 0.15621195893347395, 0.14635328173533618, 0.14885301665696335, 0.14940890198677173, 0.14939556804827483, 0.15146449341548807, 0.15870424311872025, 0.15157879032448482, 0.14730775245507818, 0.14629043209807677, 0.137789693579731, 0.15418084313800587, 0.15581131988674832, 0.14667607116546866, 0.14772559874378177, 0.14772410644315628, 0.15764413735553, 0.16442320373369781, 0.15621975581624734, 0.14097157681044728, 0.15360720894354243, 0.14425625702761255, 0.15473703164512007, 0.15267309302989837, 0.1435160963009461, 0.14558084872351568, 0.15198614824080886, 0.1402327883529619, 0.15449677765426845, 0.15663018820316504, 0.146902583544428, 0.14332180353351748, 0.14548030736536097, 0.15385774859330878, 0.1589971971140662, 0.15015163858803807, 0.14574019875314878, 0.15271877690313942, 0.16477820477747, 0.15541050029983303, 0.15090278981074842, 0.14978540466398554, 0.15095079108721962, 0.15863621559397748, 0.1478784238277965, 0.14524340538193892, 0.15193034300597577, 0.14604249496609362, 0.14201276708794727, 0.15489838025756622, 0.14844017225142359, 0.15522932153769586, 0.1512590657044669, 0.1530747489311492, 0.1607057685035168, 0.15246767516497017, 0.15555356695129144, 0.15804359548786173, 0.1488332168005478, 0.15624181899520675, 0.15010903532825914, 0.1442389253794978, 0.14990207633437067, 0.14489262616073975, 0.15345293763308687, 0.14766655546760044, 0.16055367400422027, 0.13976747731584416, 0.1553537500620973, 0.15681652871581303, 0.1574321574708903, 0.14026673568672587, 0.1555918884308081, 0.15298706706919668, 0.14587420987497696, 0.14694489651000187, 0.15419986085351342, 0.14334346831490175, 0.14652158695380663, 0.15461615711229076, 0.14695017933090435, 0.14543998795872337, 0.14676680139575085, 0.16251984841371644, 0.15172373772621983, 0.14976083192608555, 0.15511112127927343, 0.15203549872587874, 0.15689653788651506, 0.15283245049297936, 0.15771455615243382, 0.15599282980525697, 0.15114042698866234, 0.15374893071260795, 0.15074065482866086, 0.14486493699913203, 0.1463230093424572, 0.15386007946237618, 0.15508925400893467, 0.15273916946968252, 0.15023725805599217, 0.15115475930430042, 0.15157962344055656, 0.15432144112168142, 0.1552533776277713, 0.14643145613666678, 0.1451226197485258, 0.1500615103119267, 0.1617992079669943, 0.1549243426750696, 0.15258403695049771, 0.1534351748190437, 0.1488579538545592, 0.1494826435610453, 0.15266546031942882, 0.1578978962257022, 0.15882157309125652, 0.14684971270412486, 0.1516304639935235, 0.14782332313572846, 0.15653952333341808, 0.13784337396336255, 0.15505960295419136, 0.1571794810550029, 0.1478642182804277, 0.15367307183570214, 0.1505660106186155, 0.14706217911801142, 0.14877733395089873, 0.15254154854940535, 0.14997996360501448, 0.1425002721085212, 0.14813763553767734, 0.14600207906995072, 0.15511884358412642, 0.15064872903806406, 0.15460713858540928, 0.1538261248391843, 0.15012231086290498, 0.1514681065936284, 0.15794553212757076, 0.1492689342066005, 0.15727035262330294, 0.1667294335700655, 0.14849902599620407, 0.14986757622570207, 0.14767866817202477, 0.1519089716566269, 0.1553528585852329, 0.15559900204831256, 0.15062800787156094, 0.15574562820011906, 0.1403817628307865, 0.14543031488905825, 0.14841553144799943, 0.15051417057107974, 0.16193534168232046, 0.1479949772035572, 0.14718063437463583, 0.15471155851307303, 0.14529133556351717, 0.15254560979721518, 0.141485553593449, 0.15153419750294178, 0.1485395764608829, 0.1533520103242543, 0.1525894646876932, 0.1490746097944325, 0.15460144269726758, 0.14458146418969814, 0.14190581943410668, 0.14946045202969868, 0.14962382795718, 0.15340707205800097, 0.14919414962689148, 0.15444277069755194, 0.15096271356339017, 0.15140426293366696, 0.1413466242651067, 0.16158215585467717, 0.15079018944725525, 0.14817816269975753, 0.1483939959949686, 0.14865417638464243, 0.14851820310749841, 0.14801882880320286, 0.15187714490753282, 0.15019526853839488, 0.1498217828398538, 0.14724467989185017, 0.15050460074829386, 0.15572138820925055, 0.15375935469973856, 0.1545947111573003, 0.1448685405785475, 0.1472621320922281, 0.1408827227441441, 0.15324748186753134, 0.1543119714438861, 0.15207170820149657, 0.15362002483436302, 0.14857952533106583, 0.15720316883815513, 0.15938421423729432, 0.1562494712214456, 0.15789034919082232, 0.15436778660561218, 0.1441909036809763, 0.15403163592563335, 0.1388636667333871, 0.1560194648744429, 0.14296462342887478, 0.15299847103356332, 0.15470130057928255, 0.15538411064668808, 0.1483939453412843, 0.15036089617591208, 0.1464147661033102, 0.14930044371382067, 0.14655207439553355, 0.1587134813999085, 0.15499277354339125, 0.14622948016645387, 0.1594006302272157, 0.14834176774613567, 0.1453370804862947, 0.14606472804952222, 0.14715243564764804, 0.14994192807478493, 0.15645862562542345, 0.15063995354485557, 0.14585873857485207, 0.16100565086131272, 0.1530214930632812, 0.14377109112162467, 0.15255737905204156, 0.14207639140706235, 0.1512296513411434, 0.15158414479143734, 0.15338568795301333, 0.15074287048839463, 0.14693823686448504, 0.1413772272407418, 0.15418537945829075, 0.15076734319467827, 0.15195139156486637, 0.15391478604382147, 0.1464038802032172, 0.14686892768894386, 0.15974650057224676, 0.14563711840179042, 0.15778692756233242, 0.15079177703749638, 0.14134262591878638, 0.1507147053419439, 0.14743679491452108, 0.14949082094395222, 0.15059698654866494, 0.14782433801852848, 0.14803909237506063, 0.15227941709998202, 0.15112394500071422, 0.16252228970635357, 0.15890428245866586, 0.1512150589939701, 0.15552848307901376, 0.16118080556282569, 0.15228890098215542, 0.14790693995944093, 0.15018103030989274, 0.14970307603800387, 0.1609741704703433, 0.15224158808859645, 0.1483344497069498, 0.1595830534076807, 0.15831317196484226, 0.14737023655536108, 0.16168042141899738, 0.1644553232503035, 0.14855968728146918, 0.14610162965208562, 0.148344332285438, 0.1509278734841446, 0.15650971845537914, 0.15367268136392329, 0.15753335610958322, 0.1497885126025023, 0.1500972599511598, 0.15379835733932112, 0.1544138669251505, 0.14622259236693574, 0.15543690012211656, 0.14729094700017104, 0.15926341843053865, 0.1534225024488196, 0.1512485520497859, 0.15065186970874977, 0.15489266289709552, 0.1539529210351956, 0.1474711329007691, 0.1577489104720313, 0.14978710060710382, 0.13947032843381213, 0.1501698303506713, 0.15571368088072798, 0.14103812950440114, 0.14337450757777648, 0.14820096893449014, 0.15902186435094237, 0.15397469612424072, 0.14710707942437187, 0.14229485583846038, 0.1498116862146427, 0.15155334188148148, 0.1473975405741538, 0.1436408829673144, 0.15136944232362107, 0.15320411741095402, 0.1476923570753227, 0.14600681841519103, 0.1420175256030038, 0.14508516959452894, 0.14597290138476302, 0.15274591315349825, 0.1523568448105959, 0.15360837565778185, 0.15341607425669754, 0.14893444190383065, 0.1461298839142694, 0.1593416407018751, 0.14568974379178992, 0.14342545293714634, 0.144341679442688, 0.15271991244012972, 0.14091167625279122, 0.1482805281798022, 0.14762486999111915, 0.15158804745308144, 0.14507041334073162, 0.14840709417793027, 0.15997742483567165, 0.13688331461266479, 0.15117890685049062, 0.15387160879432596, 0.16026503583719112, 0.16149361375285587, 0.15295025611952606, 0.15568511745233052, 0.15335394429404467, 0.14401898950662786, 0.15224283910736178, 0.15068444720982574, 0.15906790157506207, 0.14620074783673392, 0.1437363609094446, 0.1516389656642782, 0.16045930020070462, 0.16044967428743442, 0.15314703409688946, 0.15428603881801017, 0.15031890593223055, 0.15747883863947018, 0.15228942617392577, 0.14690110421835853, 0.1487329336502797, 0.14890748168500334, 0.154702769977841, 0.14799728779721721, 0.14593080132447075, 0.1557458242808996, 0.14696194360709994, 0.1389371383589166, 0.1518378683270529, 0.15053277023310233, 0.15040979113452668, 0.14599134129584132, 0.14833390691497364, 0.15152988994868996, 0.153260051924747, 0.1723131442286888, 0.15548939912157655, 0.1557247372854344, 0.15018621493303763, 0.15071057192751947, 0.15131379287015087, 0.14914891784224688, 0.14885532151217692, 0.15782321679912978, 0.15300938994660343, 0.14946412401769302, 0.15766633778667025, 0.14882319203155242, 0.15843352868074226, 0.15236515683647628, 0.14270609160279477, 0.14654212339609907, 0.14213829355609608, 0.15191183083033286, 0.14777059542005913, 0.15304963947843486, 0.1502533067384491, 0.15675159020767818, 0.15214395628916125, 0.1527495869691102, 0.14705801569523924, 0.15093780227044473, 0.1455207899651742, 0.15208524041186086, 0.15491089549791973, 0.14628812779432399, 0.14442602158691156, 0.15701988403193085, 0.1614046891069822, 0.1434849267721725, 0.1519301440816349, 0.1502177339053602, 0.14922238242686756, 0.14993879757150838, 0.15396247054257692, 0.14240923852617568, 0.1647804040212473, 0.14335116017770297, 0.15572073162862338, 0.14928019266730672, 0.15276063917946087, 0.14468304018175449, 0.15036616132858108, 0.15291952499551642, 0.15520944469780648, 0.15439102501106092, 0.14513262215069675, 0.14636572360832353, 0.14719895369709224, 0.1528176317213514, 0.13872932167310928, 0.1444231791118739, 0.14930071220775348, 0.1628038180849759, 0.15437273908324758, 0.15233406920918338, 0.14603521557955262, 0.16651151085944638, 0.14762168893997546, 0.14930498029202308, 0.14783159637938792, 0.16104227054126244, 0.15417550791517715, 0.142928939781172, 0.15335594549454024, 0.1499973227887363, 0.1553943934209655, 0.14895076691388115, 0.15171854941546503, 0.15789342394318523, 0.14954385433250664, 0.15739828755686683, 0.15305995029742595, 0.15030949426593412, 0.149367917892737, 0.15270739170427614, 0.15164697226876075, 0.1452348855798176, 0.15197275234898563, 0.15252284260179688, 0.15672281751523967, 0.15328173362885078, 0.15339047779121728, 0.1584284408637009, 0.1500092775579038, 0.15946266573177006, 0.14686905006401485, 0.1480548678476212, 0.14858962447537466, 0.15664890990537797, 0.1499159685405856, 0.16143747280404425, 0.1452358068411856, 0.15383150027357922, 0.14886448741944225, 0.14266761400141031, 0.15461650934060647, 0.14691852082745957, 0.1441569090752751, 0.15509331876336382, 0.1539568244030212, 0.14840821115185313, 0.1526191781417423, 0.1624489497400562, 0.14739118078587987, 0.1531545566410134, 0.15010232292658443, 0.1423342486992544, 0.13535908517431172, 0.1536767260116008, 0.15424722356299, 0.15593452401906707, 0.13808387316268816, 0.16033760335489308, 0.1608813819820779, 0.17202140017432976, 0.14221213292911047, 0.1630985040061682, 0.14063363879002547, 0.15708005273887377, 0.15284721784166985, 0.14477284958159042, 0.14655328914851284, 0.15478585516152696, 0.14905293720315807, 0.1524568973751547, 0.14485356186622772, 0.15699258621463089, 0.15654987896866995, 0.14704476196598476, 0.15329309079906014, 0.15833510784042776, 0.1477021672913241, 0.16085979138575132, 0.1533168274032852, 0.15898113385458718, 0.15072200582238374, 0.15279984085253517, 0.16219192454608644, 0.14955289828377977, 0.15253718769736035, 0.1516537455349811, 0.14996275746847046, 0.14705146900055974, 0.1492707788775597, 0.14480871189264544, 0.13808650336617206, 0.1581834680853513, 0.14986848166893083, 0.15128766463453855, 0.14674721782155442, 0.1413634158587554, 0.15231936997677342, 0.13992533973853075, 0.14305270694554614, 0.158163977991849, 0.1496751893864671, 0.15056091437882504, 0.15129053164689057, 0.16150310189027675, 0.1447023113418553, 0.13879969754642768, 0.14768440091036605, 0.15846692185800457, 0.15143994083649642, 0.1629450878617637, 0.1450697555688025, 0.13088165959821352, 0.15318575138538934, 0.15952416120583413, 0.14895358961468166, 0.14824539564815314, 0.1539125891999192, 0.1617249048402829, 0.15290034206470682, 0.1517793520186282, 0.14213360682084816, 0.16232525584799404, 0.14476432533865985, 0.1709626167812052, 0.15650872038792424, 0.15504321936186582, 0.14845786574549666, 0.16037113238751569, 0.14652792112031238, 0.14842681271414773, 0.1404028465504063, 0.1482761298324058, 0.1567445848680441, 0.14250340965375885, 0.15493486656678473, 0.1508588295315951, 0.15488033860635944, 0.15150267302770926, 0.1505729939617068, 0.15430035246306362, 0.1556596183265976, 0.15879069177807809, 0.1580607265517994, 0.15333320324185448, 0.14657960517579527, 0.14047758373243688, 0.1585243126965317, 0.1607112956707178, 0.15964312919832294, 0.15676416129384982, 0.15490989167084948, 0.15173418481941117, 0.15514322688831536, 0.151586712778684, 0.1553061976800264, 0.15737115077932406, 0.1451319155820197, 0.1412074112003951, 0.14812530848478142, 0.1468017555646551, 0.143941607889617, 0.15717634366218156, 0.14723243419353463, 0.14416747261725063, 0.1542385814686848, 0.15028240723894112, 0.14480483821824175, 0.15605381456792075, 0.15006356514082886, 0.14994849543420966, 0.1419500925556314, 0.15395837870185672, 0.15702216095648153, 0.1404650548520662, 0.16080886802135083, 0.1515034502484147, 0.15927552681658305, 0.15785055381994414, 0.15311753972382477, 0.1580168856067139, 0.16192248171942678, 0.14759280677390538, 0.14475429043645752, 0.15332001560157713, 0.15655478944763726, 0.15374224667690517, 0.14785164136079426, 0.1443193444591529, 0.15794545950886615, 0.16077159001681793, 0.15471148486408268, 0.15101252862721593, 0.15083725215138516, 0.15087763381453956, 0.15499961472663912, 0.14159679010452533, 0.14176842999050696, 0.14930099111141198, 0.14362709076517344, 0.14415101999568355, 0.15549767619043198, 0.14364442646041986, 0.1588298996520975, 0.15183659770023694, 0.15354132600486523, 0.13596148560629195, 0.14722022741734347, 0.1502974414441171, 0.14996678924202145, 0.15119432838429422, 0.14743591760799313, 0.15886508425681253, 0.15048932467043424, 0.14756308021262238, 0.1614150271512456, 0.15731443978861884, 0.1416764523890469, 0.14954437480651328, 0.1449322630915202, 0.14619860941942264, 0.15571746948906795, 0.15586138345882852, 0.1526942674488034, 0.15139364397491972, 0.14609984720264776, 0.15231457037836968, 0.14433668124908924, 0.14690316684614574, 0.14859190966712627, 0.14846732947729402, 0.1463190391478544, 0.14681484539511783, 0.15696267849190731, 0.15897171014233605, 0.1583499323239546, 0.15558640730963083]]
    95% CI: [0.1508590261575976, 0.15158185452017897]
    lossveclist2 = [[0.1510172249187519, 0.15784140211886807, 0.14913824850844376, 0.14361532727314494, 0.15414922143104548, 0.14931291895393936, 0.15349280566552143, 0.14663745851218332, 0.14839646728834394, 0.1548134604648665, 0.15445155672748515, 0.15222726750517088, 0.1482084602996494, 0.14807485804400786, 0.1483742423639356, 0.15288447673747396, 0.15253134144120464, 0.1430622515880808, 0.1477875699874268, 0.1516790210467493, 0.15362121479258942, 0.14934754861719193, 0.15003820528916184, 0.15504853417058514, 0.14614785162981891, 0.14298293854623803, 0.15392988921990505, 0.1538734088094474, 0.1482912904520399, 0.14536935284642372, 0.14337378238162626, 0.15691109906000988, 0.15722243567005037, 0.1514237052516515, 0.14810111793684136, 0.1554698152528317, 0.14094294116908, 0.15473368968395293, 0.15649921007353187, 0.1542670687755772, 0.1473374384934522, 0.1520030435893359, 0.1531126445993387, 0.1545800983872269, 0.15048895745581684, 0.15400824828191445, 0.16569345340072694, 0.15288331896631746, 0.14868465800816877, 0.1483140404174663, 0.14471956496176974, 0.1574411800445795, 0.15699127243523606, 0.15214636023093436, 0.14884475765785543, 0.15798147800172554, 0.1529661431058791, 0.16306048848038376, 0.15619920793634726, 0.14793209673329316, 0.14592819388433173, 0.14444830260866248, 0.1509396571996547, 0.1516677378778901, 0.14465705225184308, 0.15050926048498062, 0.15406065407942293, 0.15526203572128117, 0.1466321858907937, 0.14779486901887073, 0.15740138216794314, 0.15215751631409116, 0.14393351543251262, 0.15188978378304635, 0.14855144564312245, 0.1512332440738341, 0.15049212627257785, 0.1522526052363672, 0.15787124709584716, 0.15431886432155043, 0.1517096510916179, 0.14546910552093312, 0.15498472771024976, 0.1542785162864995, 0.15461277387456848, 0.1395165371101616, 0.15163164444598468, 0.14413274704805898, 0.15795764134033868, 0.15523340951537853, 0.1421950614592551, 0.14492617424848064, 0.1555708087168105, 0.15536309971915574, 0.16596699351092836, 0.15292065700085408, 0.15442836290793874, 0.15184285344335938, 0.15634164751692758, 0.15246482732497718, 0.1550589639815589, 0.14335274976790158, 0.14739273953790932, 0.14532953580899619, 0.15034922452050972, 0.14760781381977767, 0.1567870837305782, 0.1497453233499366, 0.14880552595651153, 0.15376668006643984, 0.15619685711893636, 0.15509328394320168, 0.15072105708609257, 0.16612489127161653, 0.13820379972493863, 0.14135743551203955, 0.1543394194780055, 0.163221462419494, 0.1536524692250953, 0.15475694493067463, 0.1444977760141151, 0.15041423698882184, 0.15178565795399926, 0.15034636730362386, 0.14246162911083501, 0.15095560439575859, 0.14951601654838614, 0.15235266643308046, 0.15722565287067936, 0.15238096058296247, 0.14399060298439495, 0.14899452072799804, 0.1505149882626663, 0.14457944850238694, 0.15648836221561896, 0.14984412193888008, 0.15957719871626416, 0.15160798717781804, 0.14682058408644763, 0.1485464110814521, 0.15055642857385565, 0.14668705332377605, 0.14888805498501836, 0.15236764949319143, 0.1458421543683771, 0.1462831671723277, 0.15156876561353316, 0.1568827553229753, 0.15299856816850832, 0.15130397096422218, 0.15507507298432816, 0.15514940117598255, 0.1455971254123897, 0.1477807758065302, 0.15013947942528605, 0.1496196009708965, 0.1512491980122052, 0.14971455749963125, 0.15032662092736748, 0.15615476497381459, 0.15605423134415056, 0.15197069859895024, 0.15185563551543943, 0.14783153095904314, 0.15532211157883632, 0.14870217770157348, 0.15115221006361979, 0.14665510346381394, 0.15784794044606926, 0.15610110377523712, 0.14470664772951303, 0.15256029504153767, 0.15392834026556362, 0.15726001565288017, 0.15837409288078635, 0.15786406193501573, 0.15500759977559755, 0.15319998777844876, 0.1500545321325828, 0.14837491347310808, 0.15026719011334447, 0.1448013196485817, 0.15653284832088382, 0.14640112628191265, 0.14067449783711866, 0.14761663778196502, 0.1623395169299276, 0.14289522775363983, 0.15504282221377794, 0.1583441582278468, 0.14885575092253675, 0.13696377160018036, 0.15277921595763447, 0.16100990915283248, 0.15361164692512025, 0.14882085527389013, 0.15500365848587622, 0.1368677397134845, 0.15221487673915396, 0.14116465701322423, 0.1435883575062691, 0.15844799959811112, 0.15423086952736545, 0.15176079886765043, 0.14592493379024418, 0.15383464603741898, 0.1527816507552873, 0.15627635393365483, 0.15257825251215948, 0.14679730269043617, 0.1464618527111107, 0.15101789024660275, 0.14114743094511936, 0.1535424761328616, 0.15467012643616085, 0.14830413573159873, 0.14113812574891818, 0.1467021454277896, 0.15549854911471708, 0.16094614427134502, 0.14566823386275402, 0.15199114388218093, 0.15403476767542684, 0.14873201005660602, 0.15801597524283376, 0.14277755376484375, 0.15268845694712377, 0.1386455114948255, 0.14632044379003237, 0.1604130614925816, 0.14649965703323667, 0.14755579499327146, 0.1447969762977525, 0.15122764588528026, 0.1567642146146637, 0.1442873216450115, 0.15669080362302523, 0.15737633412353016, 0.1546779934576212, 0.162191260293751, 0.13948561933099618, 0.15096466711331813, 0.15228044686368633, 0.14845751101050392, 0.1503639641517215, 0.14381719517416308, 0.15386705905855377, 0.149968197135516, 0.15004467240899272, 0.15111719069858875, 0.1403197997191715, 0.1553898247839097, 0.15025029231483383, 0.1516566294432969, 0.14245918799237958, 0.15022653198985425, 0.14684121901192254, 0.15272759210278053, 0.1506230777291918, 0.15119097389352665, 0.15320921013882788, 0.15075218942808008, 0.14838605041103065, 0.1513242599035189, 0.15222270331010881, 0.14873419155068368, 0.15119531621151625, 0.14855551064585865, 0.1466704764720909, 0.1514596066324492, 0.14952077816861598, 0.14903727224496588, 0.15195505670623527, 0.15095037346762025, 0.1515922457440059, 0.1554772396660777, 0.15532107002010465, 0.14677525748748982, 0.15400970221797777, 0.1546304300202022, 0.14925161692247807, 0.14606323364910978, 0.15004976879320553, 0.15570528260987743, 0.15255336998946747, 0.15546325228272842, 0.14539451517215177, 0.15140436054620354, 0.1591729469615784, 0.1563423652752327, 0.15360658953394507, 0.15310236278512904, 0.16142141504312468, 0.1477296048975051, 0.15106734349913573, 0.1463074418942255, 0.1507331111413395, 0.14929336017649977, 0.14121647091404788, 0.1588614290379982, 0.14499881830313033, 0.1490775227217778, 0.1578115372119416, 0.15034714853492828, 0.15024407110574364, 0.15061808843872254, 0.1541855832708683, 0.14810881387592553, 0.15473903846305442, 0.14662997628498614, 0.16070895743174995, 0.16035320462760144, 0.15041524641538026, 0.1541743604899889, 0.15056458490860475, 0.14386342123899973, 0.14517200314822523, 0.15545091336317765, 0.1534769483168961, 0.14577301439542587, 0.14484402269133598, 0.1622424485805067, 0.15081548776142348, 0.1425265347234284, 0.14751036254060212, 0.14628621503607672, 0.16253286392208716, 0.14672195020913012, 0.14525303190694064, 0.15568491774774373, 0.14256155435946596, 0.15644358976551023, 0.14962502305761022, 0.1444722614790749, 0.1535736714010173, 0.16012114726649584, 0.14771749032457565, 0.16268913255788645, 0.1534450938461839, 0.15516626649413653, 0.1460493359929901, 0.15803353552255672, 0.16027407516882414, 0.15273067643423266, 0.14511324676966456, 0.14215338213754475, 0.15013992496546572, 0.14925267123370844, 0.15201454707640635, 0.15449975007992292, 0.14446649332778655, 0.1465102352285297, 0.15680597494027493, 0.15605073668087813, 0.15348165636738662, 0.15390134990499543, 0.1491123043995106, 0.1566063137553523, 0.15895358148180103, 0.14797133482427804, 0.15376888531094682, 0.14584179553773047, 0.14879826781423036, 0.17653798439928342, 0.1481477294884328, 0.15635606054137513, 0.1491619445643885, 0.14436256286012206, 0.14873157256772573, 0.15169401248288028, 0.15530908010588718, 0.1400253252852209, 0.14570514422709938, 0.152217133202893, 0.15527880961029078, 0.15742419254759274, 0.15106524076337136, 0.15343329946577908, 0.15026023573571923, 0.1539804027515278, 0.1544368249660842, 0.1468966330960733, 0.14448827072691828, 0.14727908937871087, 0.15320859450498384, 0.1412005518541027, 0.1525737312132711, 0.14961550578765767, 0.15116316715814163, 0.1510292288297741, 0.15550292626105033, 0.14310865579999224, 0.14243864539332496, 0.14885011576964025, 0.15692513212392248, 0.14673815676192922, 0.15359031883424287, 0.151779524885469, 0.15655076413946262, 0.15912910039999317, 0.14899743674554958, 0.14881745212120345, 0.157329524752248, 0.1413991666597584, 0.14081715383836363, 0.15800006844892647, 0.15139652796797773, 0.15192700008352727, 0.1438389852557735, 0.1407976013508037, 0.15804751692557653, 0.1522391869246996, 0.1514044671874849, 0.1511294396280741, 0.15756234996495636, 0.1492074010779187, 0.14622545653674882, 0.1572756776855729, 0.14861570638116703, 0.14273681898767787, 0.15939329611339997, 0.1440742798707832, 0.1450353466886935, 0.15257483002471034, 0.16639903727533317, 0.1472358651417736, 0.14798079158872207, 0.14875479552099105, 0.14735754638234855, 0.148507129096658, 0.15560560541390023, 0.1501663037502771, 0.14654035617094194, 0.1432779971815578, 0.15433610732062233, 0.15720495744372348, 0.13990049440728825, 0.1447143615771755, 0.14920848646858897, 0.15856555750113085, 0.15014021397452065, 0.15675672491690645, 0.15689959128281042, 0.15093599120631826, 0.14605621207794822, 0.1494905272606829, 0.15476300168882134, 0.14824881156828146, 0.15396822924075323, 0.153360941803429, 0.15136171324460052, 0.15184815031243057, 0.1591123338930641, 0.15118666806135536, 0.13907963795356826, 0.15003172266670595, 0.14055352526912468, 0.15296331220634393, 0.15346700235439242, 0.15117579835688225, 0.15187509169649188, 0.15810886296004859, 0.14765138231705077, 0.15831568412745328, 0.13942301552756853, 0.15296563348047193, 0.15907451250455892, 0.15088396438462617, 0.14155356962957816, 0.16019870373160786, 0.15424848806514246, 0.14988079328873735, 0.15034135632455464, 0.15131297355524173, 0.1497574293827853, 0.1458217614299096, 0.15304181041340364, 0.15752330912850762, 0.16461278204210908, 0.14220562990015861, 0.15356414911775113, 0.15188896124984771, 0.14857988563257019, 0.15298193221585119, 0.15448659069854961, 0.15688479978384776, 0.15026144593954907, 0.1502840418904261, 0.14306896268721161, 0.15233881475376188, 0.1489302783915819, 0.14402899490368604, 0.15588228665526022, 0.15331536746062926, 0.15053794032900733, 0.15515085582174243, 0.15010872738799827, 0.1362899714829469, 0.16042447436693183, 0.15003890441108222, 0.15285021364333778, 0.15107162494764473, 0.15176927277448898, 0.1566375008258758, 0.150480015910532, 0.14854693860565582, 0.14685236434576546, 0.16093832588115842, 0.1423849043815775, 0.15263264537161195, 0.14708912827200277, 0.14786666830419187, 0.1423893086855822, 0.16154101992165, 0.15606096501380787, 0.15307010582332767, 0.14657216509601703, 0.1484857952508889, 0.15541044634899565, 0.15332762596343763, 0.1514598408502035, 0.15526095111555274, 0.14935683276488299, 0.1516602122290716, 0.15650023922020634, 0.15484880829279604, 0.15131316522149063, 0.1528368388190857, 0.15138526126648943, 0.1585985501040794, 0.1521790389353593, 0.15196302661891462, 0.14571863976628183, 0.14926558744299465, 0.14718897522317517, 0.14453774429379465, 0.14259141557462257, 0.1569773729577407, 0.15071943901066315, 0.14440944197707725, 0.1475469998618231, 0.1491614074036052, 0.16831426131359212, 0.15368881560222244, 0.1583201179540896, 0.15145296627534133, 0.14201422667965294, 0.15061440566051132, 0.1435445447772212, 0.155648923137747, 0.15417489094125125, 0.15330689333415662, 0.14795706326645827, 0.15078107811093514, 0.14679799095998272, 0.14954532354562303, 0.15422615486398766, 0.14803082959844588, 0.15271268509955557, 0.14535399723298623, 0.13854382107330565, 0.15845393875583108, 0.15522521691651547, 0.15956774345262806, 0.1512952249254933, 0.1544941729097243, 0.15059150668119753, 0.15195314699865853, 0.15096962316504658, 0.15094849946371064, 0.15275625729021253, 0.14440309230870843, 0.1564183631791449, 0.14763652994324084, 0.14110524252097148, 0.1467455754772445, 0.15058320273383116, 0.15823090452116143, 0.14769137906648155, 0.15045177905251209, 0.15062763778651325, 0.15661684808985735, 0.15973245955441318, 0.14650785191985158, 0.15179707843056597, 0.15461145149859618, 0.1570818676149339, 0.15670283151844078, 0.14360109078255112, 0.14948933335237571, 0.1437934841093563, 0.15348572570359223, 0.14445598167841678, 0.14930535412783275, 0.14808469966324614, 0.1529300816628755, 0.15949145741507656, 0.14387154735120553, 0.15049813556096583, 0.14847984696336922, 0.1468001074572209, 0.15678880060053155, 0.14643933309373575, 0.14796347826929304, 0.14358356868392597, 0.151874935775987, 0.15878073194347628, 0.15000563225088318, 0.1574637261924057, 0.14733957643195003, 0.15800136194581113, 0.14728303648856084, 0.156004125218144, 0.15141268875498795, 0.15160036547126496, 0.1500780844486252, 0.17178487083794342, 0.15146087240586334, 0.14732112784667845, 0.14303399365404432, 0.15383898920952171, 0.15180796134238395, 0.15364235139109805, 0.1607829471500214, 0.1537814676147646, 0.15033308000142864, 0.14696643127916534, 0.15504109000467498, 0.15855703505093163, 0.14677163449650174, 0.15397102034024554, 0.1454357032255379, 0.15298334509999822, 0.15889039788892817, 0.14551972100288074, 0.1500448541982532, 0.15370223629371482, 0.15681610945379437, 0.15855768138469384, 0.1558870116567005, 0.15299257086186593, 0.15028679877992276, 0.14758570989158268, 0.14808628757064393, 0.1577635427295904, 0.15597662363506795, 0.1511802726634183, 0.1509064164322147, 0.15530745516444952, 0.16175489207757807, 0.15617375991165686, 0.15147278636562722, 0.14856818622893503, 0.15295008469834154, 0.15802490064107652, 0.1481641105702482, 0.15640262761931725, 0.15919006022018725, 0.15137043471827039, 0.1480687774509334, 0.1397735641757216, 0.14896895731240672, 0.16050046719150438, 0.15090049446833523, 0.15369929787731795, 0.1475751199026074, 0.14659463733020056, 0.1573237846968317, 0.1541221428894019, 0.1490356953112508, 0.14499172167400903, 0.14624781609771936, 0.1571980750041458, 0.13954836793194986, 0.1468112141244213, 0.15425592880572703, 0.15017291251846734, 0.15305205698174268, 0.15552452419044463, 0.14782992537781484, 0.153178391996323, 0.14649359705073278, 0.14488478924991763, 0.15258151802616976, 0.14871152383534073, 0.15173305225624317, 0.15478900641543972, 0.14552457374194114, 0.16062165437381026, 0.1486893279270273, 0.16040869105340877, 0.15495081751171863, 0.15345530596339763, 0.14333733197847381, 0.15859002506967554, 0.15153871444490571, 0.154391526127755, 0.1483692255790392, 0.14375722189975737, 0.14788944856361583, 0.14754793343388525, 0.16032981255989906, 0.16153142008635013, 0.15406414981030242, 0.14621874022725667, 0.14897567942121323, 0.1672771497163332, 0.15710736158961908, 0.15628239656787435, 0.1516914437971792, 0.15460403731691552, 0.15292938738955555, 0.14843470302157868, 0.1554736165736137, 0.16233154798080449, 0.15013222000701473, 0.1488639074832112, 0.14487645564919005, 0.1580930194412308, 0.1517096452724458, 0.15089990918700014, 0.1499730127877422, 0.15100831863329242, 0.15155239823064878, 0.15630474265153388, 0.14512662780671484, 0.15861404819087968, 0.14496314365711604, 0.14176407485649048, 0.14763382433402, 0.14953747083322777, 0.14612521096474215, 0.15215086457789148, 0.1571944660674445, 0.15551738621624775, 0.14765688488580875, 0.15841871937450205, 0.1466177564270508, 0.14635980872615578, 0.15060331231571758, 0.14666815620481985, 0.1442145382558319, 0.15406136511635607, 0.1443108434822166, 0.14827853318052114, 0.15101883930771404, 0.15668484699416826, 0.15482299336737923, 0.1529464094987321, 0.14707542607450455, 0.14288421325671455, 0.15752057704960945, 0.14875505934014452, 0.14824871421799202, 0.13876208304508672, 0.1544903803838217, 0.15170064430128688, 0.15693148070768007, 0.15461467804963466, 0.14923612442045134, 0.14826676472301228, 0.14744834919025915, 0.1514801078659668, 0.14994449631369483, 0.1586510854656534, 0.16348629143371465, 0.15743555375666302, 0.15919824871547592, 0.14559192213369898, 0.14957073003478474, 0.15465652713289924, 0.15126080490076488, 0.14945553269663778, 0.15971208883487, 0.15129273695509787, 0.14983980466695893, 0.1530904186581511, 0.1496012399140087, 0.14804171801418306, 0.1530487513767841, 0.1593168308267484, 0.1467333361120316, 0.15282283638059205, 0.14829721543945407, 0.15891872227643708, 0.1593427369455411, 0.1495436357353926, 0.1531470802352025, 0.15088854560043813, 0.16825619458694888, 0.149760432051446, 0.15112105529658276, 0.14246358253096653, 0.14903327624900267, 0.1547234120660679, 0.1550761957267354, 0.14942136149986515, 0.1463140459978009, 0.1500260968670169, 0.15481517259366, 0.14716930711991083, 0.15954867249197438, 0.14309915262219317, 0.14272263073596256, 0.15854505264379024, 0.14750216405259617, 0.15767671540174696, 0.1441297827876031, 0.15589565449591336, 0.16206364394715334, 0.1573192354679479, 0.15329725118392695, 0.15405642828444993, 0.14395863393157218, 0.15344432847372974, 0.16543590040927, 0.15842629292831958, 0.154735002356383, 0.1468516063744478, 0.1629430411451836, 0.14154981657273302, 0.15576606206065352, 0.14538691095198175, 0.15349896649471031, 0.15133003193337247, 0.157004056115995, 0.15629435320148713, 0.1513907517762599, 0.15106837093560996, 0.1486674967434607, 0.1524102403333548, 0.1561200973499371, 0.14197303472021858, 0.15684473162882404, 0.15867654212366117, 0.1492616362155116, 0.14578012715809724, 0.1531148872984485, 0.164288409918754, 0.1463886923132682, 0.15246281883163984, 0.15353606552965737, 0.14996316721737066, 0.14474473498783189, 0.14659835702644797, 0.16050904966925103, 0.15434368398701925, 0.1516956744670237, 0.1513178766414819, 0.14118956484640277, 0.14752598511126275, 0.14907563176667224, 0.14958700590939403, 0.15892184303953047, 0.1626224176897715, 0.1515243717572763, 0.1481807320761175, 0.15283899452205407, 0.14910164287653793, 0.14418094012147967, 0.14939805882066254, 0.15474672123552174, 0.14540151583499553, 0.15615457544514533, 0.15100919730321793, 0.15256360565800622, 0.15256606209403115, 0.15369861440045327, 0.14570221172758058, 0.15028485449028414, 0.1528961881749257, 0.14616661983007298, 0.14557901058036649, 0.15643915310031667, 0.1561471179488482, 0.1571967242046278, 0.15209915450697745, 0.16185124261000908, 0.1487210270404336, 0.15635824535376125, 0.14924673695807106, 0.1449349862176633, 0.1451202689589645, 0.15261175558967005, 0.13604159343146008, 0.15034129366006627, 0.16201765464542184, 0.15461178133368825, 0.154969158641223, 0.1538499961161293, 0.15648027517519572, 0.146742126818432, 0.1461975470722311, 0.14651399168470253, 0.1535669758961899, 0.14914916177914025, 0.14541307304625398, 0.14602236850977174, 0.16245057404166904, 0.1525929144441096, 0.15429766770333914, 0.15036844515645403, 0.15105079420832215, 0.1595530989158414, 0.15551538601620019, 0.1464897964166791, 0.14519779864914054, 0.1462314268273229, 0.1603842891615992, 0.14561704119098848, 0.1620091913225356, 0.1618951237950567, 0.16179733301665986, 0.14653581451391479, 0.14928033979326086, 0.14656481118544237, 0.14856397815503053, 0.15527378987846044, 0.14829009568722773, 0.15051950403475406, 0.14829090415978713, 0.1463246503163498, 0.15517653526126907, 0.15136707087638046, 0.15111585249848902, 0.14844635752116225, 0.1468097655354977, 0.15257368215264858, 0.14851150351915435, 0.15749121212619124, 0.14762458568047426, 0.15396391637138956, 0.15565759738235035, 0.15626962127725946, 0.1582858665135038, 0.1462238519901734, 0.14342890466425579, 0.15449190140804117, 0.15542275411931614, 0.14811158556988024, 0.13510206916267153, 0.15124991672522412, 0.15352724014657615, 0.14934053565424976, 0.14793645701619135, 0.16176831043757436, 0.1597644236324412, 0.14997074949146194, 0.1570270591649046, 0.14871087580761128, 0.14280250692244276, 0.14706973213258695, 0.1549459923854138, 0.1468014588824541, 0.14585716570123416, 0.15668937433512267, 0.15359584973156853, 0.1605216380299116, 0.14684222143558895, 0.14768104166551926, 0.14197203599118136, 0.14538997349970104, 0.15054505927134185, 0.15606750083472287, 0.16030512229522884, 0.14339557846382275, 0.1557098919664751, 0.1507035834255781, 0.1547832648704013, 0.15520991968522724, 0.15681579076465765, 0.15344483369151016, 0.1545583091769068, 0.15123620344355193, 0.1491593139848718, 0.14919404606532313, 0.15710998372870907, 0.14672662515973314, 0.147791971805554, 0.1541656798639346, 0.14919725365720202, 0.14186332011408911, 0.1563516998324075, 0.15260442969524743, 0.1436670682013846, 0.15702377947788043, 0.14799410678329286, 0.14845325615570126, 0.15797309637559928, 0.14387219335915766, 0.16072605227956385, 0.15451054491398583, 0.15470595864256223, 0.15145583861627682, 0.1508572779085943, 0.14996754580136792, 0.142897895617698, 0.15389785059535285, 0.1487267994904609, 0.14845225431678485]]
    95% CI: [0.15100307416678901, 0.15167494462601158]
    '''
    # MCMCexpect
    lossveclist2 = getDesignUtility(priordatadict=exampleDict.copy(), lossdict=lossDict.copy(), designlist=designList,
                                    designnames=designNames, numtests=numtests,
                                    omeganum=omeganum, type=['path'], randinds=randinds, method='MCMCexpect',
                                    numpostdraws=numdrawspost)
    # print(lossveclist2)
    # FOR GENERATING 95% INTERVAL ON LOSS
    CIalpha = 0.05
    z = spstat.norm.ppf(1 - (CIalpha / 2))
    for lst in lossveclist2:  # FOR INTERVAL ON MEAN
        mn = np.mean(lst)
        sd = np.std(lst)
        intval = z * (sd) / np.sqrt(len(lst))
        loperc = (mn - intval)
        hiperc = (mn + intval)
        print('[' + str(loperc) + ', ' + str(hiperc) + ']')

    return

def checkDistsAlign():
    numTN, numSN = 3, 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5, 0.05, 0.1, 0.08, 0.02]

    # Generate a supply chain, with no testing data
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked', randSeed=86, trueRates=trueSFPrates)
    exampleDict[
        'diagSens'] = s  # bug from older version of logistigate that doesn't affect the data but reports s,r=0.9,0.99
    exampleDict['diagSpec'] = r
    # Update dictionary with needed summary vectors
    exampleDict = util.GetVectorForms(exampleDict)
    # Populate N and Y with numbers from paper example
    exampleDict['N'] = np.array([[6, 11], [12, 6], [2, 13]])
    exampleDict['Y'] = np.array([[3, 0], [6, 0], [0, 0]])
    # Add a prior
    exampleDict['prior'] = methods.prior_normal()
    # MCMC settings
    exampleDict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
    exampleDict['importerNum'] = numSN
    exampleDict['outletNum'] = numTN

    # Generate posterior draws
    numdraws = 20000
    numdrawspost = 1000
    exampleDict['numPostSamples'] = numdraws
    exampleDict = methods.GeneratePostSamples(exampleDict)

    design = np.array([[0., 0.], [1., 0.], [0., 0.]])
    type = ['path']
    numtests = 25
    sampMat = design * numtests
    omeganum = 200
    randinds = random.sample(range(numdraws), omeganum)

    # Use MCMC to get omeganum scenarios
    sampsArr = np.zeros(shape=(omeganum, numdrawspost, numTN + numSN))
    for drawnum, currpriordraw in enumerate(exampleDict['postSamples'][randinds]):

        # Initialize Ntilde and Ytilde
        Ntilde = sampMat.copy()
        Ytilde = np.zeros(shape=exampleDict['N'].shape)

        for currTN in range(numTN):
            for currSN in range(numSN):
                currzProb = zProbTr(currTN, currSN, numSN, currpriordraw, exampleDict['diagSens'],
                                    exampleDict['diagSpec'])
                if type[0] == 'path':
                    currTerm = sampMat[currTN][currSN] * currzProb
                elif type[0] == 'node':
                    currTerm = sampMat[currTN] * type[1][currTN][currSN] * currzProb
                Ytilde[currTN][currSN] = currTerm

        # We have a new set of data d_tilde
        Nomega = exampleDict['N'] + Ntilde
        Yomega = exampleDict['Y'] + Ytilde

        postdatadict = exampleDict.copy()
        postdatadict['N'] = Nomega
        postdatadict['Y'] = Yomega

        # Writes over previous MCMC draws
        postdatadict.update({'numPostSamples': numdrawspost})
        postdatadict = methods.GeneratePostSamples(postdatadict)
        sampsArr[drawnum] = postdatadict['postSamples']

    # We now have MCMC draws; get draws from weights
    postDensWts = []  # Initialize our weights for each vector of SFP rates
    for currdraw in exampleDict['postSamples']:  # Iterate through each prior draw
        currWt = 0
        '''
        for currTN in range(numTN):
            for currSN in range(numSN):
                currzProb = zProbTr(currTN, currSN, numSN, currdraw, exampleDict['diagSens'],
                                    exampleDict['diagSpec'])
                currzTerm = (currzProb ** currzProb) * ((1 - currzProb) ** (1 - currzProb))
                if type[0] == 'path':
                    currTerm = currzTerm ** (sampMat[currTN][currSN])
                elif type[0] == 'node':
                    currTerm = currzTerm ** (sampMat[currTN] * type[1][currTN][currSN])
                currWt = currWt * currTerm

        '''
        '''
        for currTN in range(numTN):
            for currSN in range(numSN):
                currN = int(sampMat[currTN][currSN])
                currzProb = zProbTr(currTN, currSN, numSN, currdraw, exampleDict['diagSens'],
                                    exampleDict['diagSpec'])
                for currY in range(currN+1):
                    currTerm = (((currzProb ** currY) * ((1 - currzProb) ** (currN - currY)) )  * comb(int(currN),
                        int(currY)))** 2
                    currWt += currTerm

                currY = currzProb * currN
                currYflr, currYceil = math.floor(currY), math.ceil(currY)
                if currYceil > 0:
                    yRem = currY - currYflr
                    flrTerm = (currzProb ** currYflr) * ((1 - currzProb) ** (currN - currYflr)) * comb(int(currN), currYflr)
                    ceilTerm = (currzProb ** currYceil) * ((1 - currzProb) ** (currN - currYceil)) * comb(int(currN),
                                                                                                      currYceil)
                    currTerm = (1 - yRem) * flrTerm + (yRem) * ceilTerm
                else:
                    currTerm = 1
                '''

        postDensWts.append((currWt))
    # Normalize the weights to sum to the number of prior draws
    postWtsSum = np.sum(postDensWts)
    postDensWts = [postDensWts[i] * (len(exampleDict['postSamples']) / postWtsSum) for i in range(len(postDensWts))]

    ###### Generate histograms of MCMC and weight methods
    intrange = np.arange(0., 1., 0.01)
    priorMat = np.zeros(shape=(numTN + numSN, len(intrange)))
    mcmcMat = np.zeros(shape=(omeganum, numTN + numSN, len(intrange)))
    sampsArrComb = sampsArr.reshape((-1, sampsArr.shape[-1]))
    mcmcCombMat = np.zeros(shape=(numTN + numSN, len(intrange)))
    wtMat = np.zeros(shape=(numTN + numSN, len(intrange)))
    for cellind, cell_lo in enumerate(intrange):  # Iterate through each histogram bin
        cell_hi = cell_lo + 0.01
        for draw in exampleDict['postSamples']:
            for nodeind in range(numTN + numSN):
                if (draw[nodeind] >= cell_lo) and (draw[nodeind] < cell_hi):
                    priorMat[nodeind][cellind] += 1
        for omega in range(omeganum):
            for draw in sampsArr[omega]:
                for nodeind in range(numTN + numSN):
                    if (draw[nodeind] >= cell_lo) and (draw[nodeind] < cell_hi):
                        mcmcMat[omega][nodeind][cellind] += 1 * numdraws / numdrawspost
        for draw in sampsArrComb:  # All combined posterior MCMC draws
            for nodeind in range(numTN + numSN):
                if (draw[nodeind] >= cell_lo) and (draw[nodeind] < cell_hi):
                    mcmcCombMat[nodeind][cellind] += 1 * numdraws / (omeganum * numdrawspost)
        for drawind, draw in enumerate(exampleDict['postSamples']):  # The posterior weights
            for nodeind in range(numTN + numSN):
                if (draw[nodeind] >= cell_lo) and (draw[nodeind] < cell_hi):
                    wtMat[nodeind][cellind] += postDensWts[drawind]

    for i in range(numTN + numSN):
        for omega in range(omeganum):
            plt.plot(intrange, mcmcMat[omega][i], color='blue', linewidth=0.05)
        plt.plot(intrange, mcmcCombMat[i], color='darkblue', linewidth=3)
        # plt.plot(intrange,wtMat[i],color='orange',linewidth=3)
        plt.plot(intrange, priorMat[i], color='black', linewidth=2)
        plt.show()

    return