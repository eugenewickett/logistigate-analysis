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
import scipy.special as sps
import matplotlib.pyplot as plt
import random
import pickle


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
        roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    elif np.sum(roundMat) < n: # Too few tests; add to lowest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(roundMat, axis=None).tolist()
        for addind in range(int(n-np.sum(roundMat))):
            roundMat[sortinds[addind]] += 1
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
        roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    elif np.sum(roundMat) < n: # Too few tests; add to highest represented traces
        roundMat = roundMat.flatten()
        sortinds = np.argsort(-roundMat, axis=None).tolist()
        for addind in range(int(n-np.sum(roundMat))):
            roundMat[sortinds[addind]] += 1
        roundMat = roundMat.reshape(D.shape[0],D.shape[1])
    return roundMat


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

def bayesianexample1():
    '''
    Use a small example to find the utility from different sampling designs.
    '''

    # Define squared loss function
    def lossfunc1(est,param):
        return np.linalg.norm(est-param,2)

    # Designate number of test and supply nodes
    numTN = 3
    numSN = 2
    s, r = 1., 1.

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=40,
                                            dataType='Tracked',randSeed=24,trueRates=[0.5,0.05,0.1,0.08,0.02])
    exampleDict['diagSens'] = s # bug from older version of logistigate that doesn't affect the data
    exampleDict['diagSpec'] = r

    exampleDict = util.GetVectorForms(exampleDict)

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

    # Different designs
    design1 = np.array([1., 0., 0.])
    design2 = np.array([0., 1., 0.])
    design3 = np.array([0., 0., 1.])
    design4 = np.array([0.4, 0.3, 0.3])
    design5 = np.array([0., 0.5, 0.5])

    ##################################
    ########## REMOVE LATER ##########
    ##################################
    priordatadict = exampleDict.copy()
    estdecision = 'mean'
    numtests = 8
    design = design5.copy()
    lossfunc = lossfunc1

    def bayesutility(priordatadict, lossfunc, estdecision, design, numtests, omeganum):
        '''
        priordatadict: should have posterior draws from initial data set already included
        estdecision: how to form a decision from the posterior samples; one of 'mean', 'mode', or 'median'
        design: a sampling probability vector along all test nodes
        numtests: how many samples will be obtained under the design
        '''

        omeganum = 100    # UPDATE

        (numTN, numSN) = priordatadict['N'].shape
        Q = priordatadict['transMat']
        s, r = priordatadict['diagSens'], priordatadict['diagSpec']

        # Retrieve prior draws
        priordraws = priordatadict['postSamples']

        # Store utility for each omega in an array
        utilityvec = []

        for omega in range(omeganum):
            # Initialize samples to be drawn from test nodes, per the design
            TNsamps = np.round(numtests * design)
            # Grab a draw from the prior
            currpriordraw = priordraws[np.random.choice(priordraws.shape[0], size=1)[0]] # [SN rates, TN rates]
            # Initialize Ntilde and Ytilde
            Ntilde = np.zeros(shape = priordatadict['N'].shape)
            Ytilde = Ntilde.copy()

            while np.sum(TNsamps) > 0.:
                index = [i for i, x in enumerate(TNsamps) if x > 0]
                currTNind = index[0]
                TNsamps[currTNind] -= 1
                # Randomly choose the supply node, per Q
                currSNind = np.random.choice(np.array(list(range(numSN))),size=1,p=Q[currTNind])[0]
                # Generate test result
                currTNrate = currpriordraw[numSN+currTNind]
                currSNrate = currpriordraw[currSNind]
                currrealrate = currTNrate + (1-currTNrate)*currSNrate # z_star for this sample
                currposrate = s*currrealrate+(1-r)*(1-currrealrate) # z for this sample
                result = np.random.binomial(1, p=currposrate)
                Ntilde[currTNind, currSNind] += 1
                Ytilde[currTNind, currSNind] += result

            # We have a new set of data d_tilde
            Nomega = priordatadict['N'] + Ntilde
            Yomega = priordatadict['Y'] + Ytilde

            postdatadict = priordatadict.copy()
            postdatadict['N'] = Nomega
            postdatadict['Y'] = Yomega

            postdatadict = methods.GeneratePostSamples(postdatadict)
            # Get mean of samples as estimate
            currSamps = sps.logit(postdatadict['postSamples'])

            if estdecision == 'mean':
                logitmeans = np.average(currSamps,axis=0)
                currEst = sps.expit(logitmeans)

            # Average loss for all postpost samples
            avgloss = 0
            for currsamp in postdatadict['postSamples']:
                currloss = lossfunc(currEst,currsamp)
                avgloss += currloss
            avgloss = avgloss/len(postdatadict['postSamples'])

            #Append to utility storage vector
            utilityvec.append(avgloss)

        utilvalue = np.average(utilityvec)
        utilsd = np.std(utilityvec)



        return utilvalue, utilsd, utilvalue-2*utilsd,utilvalue+2*utilsd


    return

def bayesianexample2():
    '''
    Use paper example to find the utility from different sampling designs; in this case, we can choose the full trace,
    i.e., we can choose the test node and supply node .
    '''

    # Define squared loss function
    def lossfunc1(est, targ, paramDict={}):
        return np.linalg.norm(est-targ,2)

    # Define classification loss function with threshold t
    def lossfunc2(est, targ, paramDict):
        estClass = np.array([1 if est[i]>=paramDict['t'] else 0 for i in range(len(est))])
        targClass = np.array([1 if targ[i]>=paramDict['t'] else 0 for i in range(len(targ))])
        return np.linalg.norm(estClass-targClass,1)

    # Loss function tailored for PMS
    def lossfunc3(est, targ, paramDict):
        # paramDict should have fields: 'overEstWt', 'rateTarget'
        currloss = 0.
        epsTarg = 0.5 - paramDict['rateTarget']
        for i in range(len(est)):
            errterm = (paramDict['overEstWt']*max(targ[i] - est[i], 0) + max(est[i]-targ[i],0))**2
            if epsTarg < 0:
                wtterm = targ[i]*(1-targ[i]-2*epsTarg)
            else:
                wtterm = (targ[i]+2*epsTarg)*(1-targ[i])
            currloss += errterm * wtterm
        return currloss

    # Designate number of test and supply nodes
    numTN = 3
    numSN = 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5,0.05,0.1,0.08,0.02]

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked',randSeed=86,trueRates=trueSFPrates)
    exampleDict['diagSens'] = s # bug from older version of logistigate that doesn't affect the data
    exampleDict['diagSpec'] = r

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

    # Different designs; they take matrix form as the traces can be selected directly
    design0 = np.array([[0., 0.], [0., 0.], [0., 0.]])
    design1 = np.array([[0., 0.], [0., 0.], [1., 0.]])
    design2 = np.array([[1/3, 0.], [1/3, 1/3], [0., 0.]])
    design3 = np.array([[1/3, 0.], [1/3, 0.], [1/3, 0.]])
    design4 = np.array([[0., 0.], [0., 0.], [0., 1.]])
    design5 = np.array([[1/6, 1/6], [1/6, 1/6], [1/6, 1/6]])
    design6_6 = balancedesign(exampleDict['N'],6)
    design6_30 = balancedesign(exampleDict['N'],30)

    ###############################################
    ########## REMOVE LATER #######################
    # FOR USING WITH THE FUNCTION WHILE CODING IT #
    ###############################################
    priordatadict = exampleDict.copy()
    #priordraws = priordatadict['postSamples']
    #import pickle
    #import os
    #outputFilePath = os.getcwd()
    #outputFileName = os.path.join(outputFilePath, 'priordraws')
    #pickle.dump(priordraws, open(outputFileName, 'wb'))

    import pickle
    import os
    priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'),'rb'))
    numtests = 30
    design = design1.copy()
    estdecision = 'mean'
    t = 0.2
    lossDict = {'overEstWt':2.,'rateTarget':t}
    lossfunc = lossfunc3

    random.seed(35)
    randinds = random.sample(range(0,1000),100)

    def bayesutility(priordatadict, lossfunc, lossDict, estdecision, design, numtests, omeganum, t=0.1,
                     priordraws=[], randinds=[]):
        '''
        priordatadict: should have posterior draws from initial data set already included
        estdecision: how to form a decision from the posterior samples; one of 'mean', 'mode', or 'median'
        design: a sampling probability vector along all test nodes
        numtests: how many samples will be obtained under the design
        '''

        # Retrieve prior draws
        #priordraws = priordatadict['postSamples']

        omeganum = 100    # UPDATE

        (numTN, numSN) = priordatadict['N'].shape
        Q = priordatadict['transMat']
        s, r = priordatadict['diagSens'], priordatadict['diagSpec']

        # Store loss for each omega in an array
        lossvec = []

        # Initialize samples to be drawn from traces, per the design
        sampMat = roundDesignLow(design,numtests)

        for omega in range(omeganum):

            TNsamps = sampMat.copy()
            # Grab a draw from the prior
            #currpriordraw = priordraws[np.random.choice(priordraws.shape[0], size=1)[0]] # [SN rates, TN rates]
            currpriordraw = priordraws[randinds[omega]]  # [SN rates, TN rates]
            # Initialize Ntilde and Ytilde
            Ntilde = np.zeros(shape = priordatadict['N'].shape)
            Ytilde = Ntilde.copy()

            while np.sum(TNsamps) > 0.:
                # Go to first non-empty row of TN samps
                i, j = 0, 0
                while np.sum(TNsamps[i])==0:
                    i += 1
                # Go to first non-empty column of this row
                while TNsamps[i][j]==0:
                    j += 1
                TNsamps[i][j] -= 1
                # Generate test result
                currTNrate = currpriordraw[numSN+i]
                currSNrate = currpriordraw[j]
                currrealrate = currTNrate + (1-currTNrate)*currSNrate # z_star for this sample
                currposrate = s*currrealrate+(1-r)*(1-currrealrate) # z for this sample
                result = np.random.binomial(1, p=currposrate)
                Ntilde[i, j] += 1
                Ytilde[i, j] += result

            # We have a new set of data d_tilde
            Nomega = priordatadict['N'] + Ntilde
            Yomega = priordatadict['Y'] + Ytilde

            postdatadict = priordatadict.copy()
            postdatadict['N'] = Nomega
            postdatadict['Y'] = Yomega

            postdatadict = methods.GeneratePostSamples(postdatadict)
            # Get mean of samples as estimate
            currSamps = sps.logit(postdatadict['postSamples'])

            if estdecision == 'mean':
                logitmeans = np.average(currSamps,axis=0)
                currEst = sps.expit(logitmeans)
            elif estdecision == 'mode':
                currEst = np.array([1 if np.sum(currSamps[:,i]>sps.logit(t))>=(len(currSamps[:,i])/2) else 0 for i in range(numSN+numTN) ])


            # Average loss for all postpost samples
            avgloss = 0
            for currsamp in postdatadict['postSamples']:
                currloss = lossfunc(currEst,currsamp,lossDict)
                avgloss += currloss
            avgloss = avgloss/len(postdatadict['postSamples'])

            #Append to utility storage vector
            lossvec.append(avgloss)
            print('omega '+str(omega) + ' complete')

        lossval = np.average(lossvec)
        losssd = np.std(lossvec)
        print(lossvec)



        return lossvec, lossval, losssd, lossval-2*losssd, lossval+2*losssd

def bayesianexample3():
    '''
    Use paper example to find the utility from different sampling designs; in this case, we can choose the full trace,
    i.e., we can choose the test node and supply node .
    '''

    # Define squared loss function
    def lossfunc1(est,param):
        return np.linalg.norm(est-param,2)

    # Define classification loss function with threshold t
    def lossfunc2(est,param,t):
        estClass = np.array([1 if est[i]>=t else 0 for i in range(len(est))])
        paramClass = np.array([1 if param[i]>=t else 0 for i in range(len(param))])
        return np.linalg.norm(estClass-paramClass,1)

    # Designate number of test and supply nodes
    numTN = 3
    numSN = 2
    # Designate testing accuracy
    s, r = 1., 1.
    # Designate the true SFP rates
    trueSFPrates = [0.5,0.05,0.1,0.08,0.02]

    # Generate a supply chain
    exampleDict = util.generateRandDataDict(numImp=numSN, numOut=numTN, diagSens=s, diagSpec=r, numSamples=0,
                                            dataType='Tracked',randSeed=86,trueRates=trueSFPrates)
    exampleDict['diagSens'] = s # bug from older version of logistigate that doesn't affect the data
    exampleDict['diagSpec'] = r

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

    # Different designs; they take matrix form as the traces can be selected directly
    design0 = np.array([[0., 0.], [0., 0.], [0., 0.]])
    design1 = np.array([[0., 0.], [0., 0.], [1., 0.]])
    design2 = np.array([[1/3, 0.], [1/3, 1/3], [0., 0.]])
    design3 = np.array([[1/3, 0.], [1/3, 0.], [1/3, 0.]])
    design4 = np.array([[0., 0.], [0., 0.], [0., 1.]])
    design5 = np.array([[1/6, 1/6], [1/6, 1/6], [1/6, 1/6]])
    design6_6 = balancedesign(exampleDict['N'],6)
    design6_30 = balancedesign(exampleDict['N'],30)

    ###############################################
    ########## REMOVE LATER #######################
    # FOR USING WITH THE FUNCTION WHILE CODING IT #
    ###############################################
    priordatadict = exampleDict.copy()
    #priordraws = priordatadict['postSamples']
    #import pickle
    #import os
    #outputFilePath = os.getcwd()
    #outputFileName = os.path.join(outputFilePath, 'priordraws')
    #pickle.dump(priordraws, open(outputFileName, 'wb'))

    import pickle
    import os
    priordraws=pickle.load(open(os.path.join(os.getcwd(), 'priordraws'),'rb'))
    numtests = 30
    design = design6_30.copy()
    estdecision = 'mode'
    t = 0.1
    lossfunc = lossfunc2

    random.seed(35)
    randinds = random.sample(range(0,1000),100)

    def bayesutility(priordatadict, lossfunc, estdecision, design, numtests, omeganum, t=0.1):
        '''
        priordatadict: should have posterior draws from initial data set already included
        estdecision: how to form a decision from the posterior samples; one of 'mean', 'mode', or 'median'
        design: a sampling probability vector along all test nodes
        numtests: how many samples will be obtained under the design
        '''

        # Retrieve prior draws
        #priordraws = priordatadict['postSamples']

        omeganum = 100    # UPDATE

        (numTN, numSN) = priordatadict['N'].shape
        Q = priordatadict['transMat']
        s, r = priordatadict['diagSens'], priordatadict['diagSpec']

        # Store loss for each omega in an array
        lossvec = []

        # Initialize samples to be drawn from traces, per the design
        sampMat = roundDesignLow(design,numtests)

        for omega in range(omeganum):

            TNsamps = sampMat.copy()
            # Grab a draw from the prior
            #currpriordraw = priordraws[np.random.choice(priordraws.shape[0], size=1)[0]] # [SN rates, TN rates]
            currpriordraw = priordraws[randinds[omega]]  # [SN rates, TN rates]
            # Initialize Ntilde and Ytilde
            Ntilde = np.zeros(shape = priordatadict['N'].shape)
            Ytilde = Ntilde.copy()

            while np.sum(TNsamps) > 0.:
                # Go to first non-empty row of TN samps
                i, j = 0, 0
                while np.sum(TNsamps[i])==0:
                    i += 1
                # Go to first non-empty column of this row
                while TNsamps[i][j]==0:
                    j += 1
                TNsamps[i][j] -= 1
                # Generate test result
                currTNrate = currpriordraw[numSN+i]
                currSNrate = currpriordraw[j]
                currrealrate = currTNrate + (1-currTNrate)*currSNrate # z_star for this sample
                currposrate = s*currrealrate+(1-r)*(1-currrealrate) # z for this sample
                result = np.random.binomial(1, p=currposrate)
                Ntilde[i, j] += 1
                Ytilde[i, j] += result

            # We have a new set of data d_tilde
            Nomega = priordatadict['N'] + Ntilde
            Yomega = priordatadict['Y'] + Ytilde

            postdatadict = priordatadict.copy()
            postdatadict['N'] = Nomega
            postdatadict['Y'] = Yomega

            postdatadict = methods.GeneratePostSamples(postdatadict)
            # Get mean of samples as estimate
            currSamps = sps.logit(postdatadict['postSamples'])

            if estdecision == 'mean':
                logitmeans = np.average(currSamps,axis=0)
                currEst = sps.expit(logitmeans)
            elif estdecision == 'mode':
                currEst = np.array([1 if np.sum(currSamps[:,i]>sps.logit(t))>=(len(currSamps[:,i])/2) else 0 for i in range(numSN+numTN) ])


            # Average loss for all postpost samples
            avgloss = 0
            for currsamp in postdatadict['postSamples']:
                if estdecision == 'mean':
                    currloss = lossfunc(currEst,currsamp)
                elif estdecision == 'mode':
                    currloss = lossfunc(currEst,currsamp,t)
                avgloss += currloss
            avgloss = avgloss/len(postdatadict['postSamples'])

            #Append to utility storage vector
            lossvec.append(avgloss)
            print('omega '+str(omega) + ' complete')

        lossval = np.average(lossvec)
        losssd = np.std(lossvec)




        return lossval, losssd, lossval-2*losssd, lossval+2*losssd

'''
# Put loss value data as vectors below; this will generate a set of histograms
# FOR 3 TESTS WITH ALIGNED PRIOR DRAWS
lvec1 = [0.13047196168170846, 0.1276038264408392, 0.12449235844276779, 0.13217349422523322, 0.1354759528148989, 0.1360142621802269, 0.12939067614673927, 0.1286761730177714, 0.14169743569010873, 0.12778910630973087, 0.12480889050669584, 0.1349795282762828, 0.12707302246784827, 0.1302957948436728, 0.13157428686120592, 0.14644515788152665, 0.1256991893306132, 0.13194174128845973, 0.12540158735569396, 0.1306203436741542, 0.14261781696505488, 0.150280893284013, 0.14041038641070372, 0.12348282614396186, 0.125911845549212, 0.13469509047043055, 0.135752134309431, 0.13662644692994802, 0.1254239544910863, 0.12405392996605177, 0.1479332529407039, 0.1301525637862641, 0.13497285555377378, 0.15006052733905945, 0.13569726059359477, 0.1522005031687532, 0.13404841406693055, 0.14696558817453664, 0.12978124744622593, 0.1441451377717851, 0.13625775638361956, 0.12837295653070918, 0.12838887495178292, 0.12764654396269842, 0.1300896357023657, 0.12890125184470347, 0.1324589416735074, 0.1324589416735074, 0.15617817508483378, 0.13305267644520485, 0.13021117513543903, 0.1252221764041104, 0.12971953381482387, 0.13302782557514592, 0.1292101726489508, 0.12944675178905107, 0.13495145483950105, 0.1454534859133748, 0.12993801064495875, 0.12462455689054089, 0.137885930960764, 0.12927953773801315, 0.14186420034657476, 0.12448797474967636, 0.14424700849684968, 0.13377822799246095, 0.12956186433758862, 0.1298119199754846, 0.14365063236204537, 0.1433258367246212, 0.14166468096134932, 0.14329245911306435, 0.13570369538569574, 0.1345784605734944, 0.13115039046122184, 0.13679824568726018, 0.13533205174111768, 0.13462419117133795, 0.1287867130550015, 0.13988172816736003, 0.1369139316205147, 0.12329925549938892, 0.13813520486908826, 0.12443559097337117, 0.13126097231720898, 0.14009128941725005, 0.14122534946237164, 0.13287131388033596, 0.11888576012907849, 0.12684374243485486, 0.13216098467054446, 0.12408401197129885, 0.1469222731480437, 0.15100287401554233, 0.1383834377262981, 0.1508454309423051, 0.13058567424510278, 0.1449475078236815, 0.1493445085993241, 0.12616948030359015]
lvec2 = [0.12754209193762045, 0.14031219720978916, 0.13010100439884947, 0.1327246470991515, 0.1332488070741414, 0.17785684814211353, 0.12842574463210446, 0.13181677560053628, 0.1343499195285006, 0.1323374633661742, 0.12836862511602445, 0.13001859567488736, 0.1365527321797588, 0.12775634414907083, 0.14580346329980734, 0.1640785189966381, 0.1311423007944489, 0.13223061726192142, 0.12767395998354436, 0.12429207661021083, 0.1265604764724026, 0.13072937443355737, 0.15671777269777182, 0.12514181892215678, 0.13168644644057526, 0.16274530137939722, 0.16654474484115633, 0.1316258004074624, 0.12731853589008554, 0.13304878913448515, 0.16877064424013738, 0.14011507180814017, 0.13192862095566837, 0.13519505789846187, 0.13002509201899204, 0.13168205990715817, 0.12994389799319672, 0.13038181706740126, 0.13431882708195128, 0.13746970899234498, 0.13539540264916458, 0.13487973988967866, 0.12997782849544973, 0.13673316854940076, 0.1307450174830862, 0.1371005133585724, 0.13924090501043032, 0.13838798514314493, 0.134923406337216, 0.12614519075546998, 0.133023593322859, 0.12576895927705714, 0.13105501260078514, 0.130107013636262, 0.12582858636922473, 0.17248682902645737, 0.1325208788030812, 0.14588921081877704, 0.13541096684538162, 0.1342599964292524, 0.13001699237686787, 0.12756441777691874, 0.13031295552831842, 0.13244792060846697, 0.13228096472940035, 0.12502263561973484, 0.17986885944768705, 0.13162725440466186, 0.13752168808162005, 0.1331347506159003, 0.12797199847337623, 0.1434561233452652, 0.12900276797441673, 0.12992678684060696, 0.1408798044821269, 0.13503855240312046, 0.13693097439732002, 0.12402673487666072, 0.130582714215785, 0.12063979073675954, 0.13055935152289774, 0.13478958511820552, 0.13278513683197604, 0.13339851346118609, 0.13348580758961437, 0.13039165311990222, 0.13077245124761644, 0.13943728199506442, 0.16571263533012898, 0.16363749427459032, 0.1643298773941419, 0.13035993493446266, 0.13451805163720365, 0.12891800101853534, 0.1673501251232175, 0.1319185405640334, 0.14611467424401084, 0.13875906340601532, 0.14211957771532613, 0.14369715743805525]
lvec3 = [0.13697764582012645, 0.12675526883520252, 0.1308251030754902, 0.1408067592248919, 0.12597841552729494, 0.13353369491755498, 0.12429832403437134, 0.13709863103925737, 0.13141996233451253, 0.13085683801927164, 0.131841415917466, 0.13173386238128823, 0.1401340965206679, 0.13324231403453868, 0.13936384861638426, 0.12560101659332082, 0.13580229493907667, 0.133666761503803, 0.12943125269234088, 0.13207189228981028, 0.13642282124061, 0.13462831586183321, 0.127763082680329, 0.13511421110192526, 0.1361333002340311, 0.13597872713804882, 0.14593994372250554, 0.15183977649734026, 0.13044317617938794, 0.134250313662532, 0.13835344794064533, 0.14409107773328075, 0.14061087861520152, 0.12354667007835678, 0.13079558927052282, 0.13009358252378478, 0.13288300606106693, 0.13288300606106693, 0.1337398123298732, 0.13817381445437968, 0.1267033116857319, 0.13501292647925223, 0.145885252133139, 0.12907969312912632, 0.13110323976246913, 0.12761127506408187, 0.11948756266658803, 0.13229452870205766, 0.13646942055844247, 0.13120594005088243, 0.12920145379022513, 0.1351595719685953, 0.14063366039188874, 0.1308125333038432, 0.1519291067594185, 0.1482402111817438, 0.12844284976192133, 0.12929512895939857, 0.12444294177057715, 0.13797803707748096, 0.14169078361098578, 0.12765417575956856, 0.12374824898093927, 0.13663097521203463, 0.13621719862915177, 0.13814639573711598, 0.13318106231629007, 0.1519677075463462, 0.13822681273026283, 0.13469370661433747, 0.14196219996850246, 0.142127274583187, 0.1410232360463834, 0.12847845669028682, 0.13431374906200821, 0.14252571697309935, 0.14481582602784168, 0.12689537302651258, 0.12226290284133942, 0.1443536892393676, 0.1254594853135468, 0.14117895600672078, 0.13256151218842954, 0.1268591399355791, 0.14448117338334976, 0.12930964020146546, 0.1328649287609819, 0.14108330586916737, 0.12993659975971897, 0.13038081242281513, 0.12263687279953689, 0.12906569669579687, 0.13197722926338046, 0.13142804989471524, 0.1272496162487525, 0.13990288456384065, 0.13490202565031886, 0.12521477015095855, 0.12639177772762686, 0.13212715475633424]
lvec4 = [0.13786484978656838, 0.13737504032389106, 0.13655960150728405, 0.13863506287719363, 0.1390705581703513, 0.13977357195661486, 0.13907779150128435, 0.14154022665594576, 0.1341428958677076, 0.14274229913887965, 0.135153287130241, 0.13105271863771872, 0.14252757080839124, 0.13738626083669195, 0.13692611022857448, 0.14374513437638084, 0.14483457186159396, 0.14155897391354638, 0.1359188473783265, 0.13706101460831738, 0.13979885002825704, 0.1415448141063927, 0.1313137305255705, 0.15089531512472276, 0.14429036742745727, 0.1422959481561467, 0.13881377708645065, 0.14029047321001678, 0.13663518876925432, 0.13590736367712508, 0.13677835712305578, 0.13793841714606353, 0.13944242873000565, 0.14007611697718456, 0.1403639882260881, 0.14252672568755467, 0.1353562891255248, 0.14171960127549904, 0.1293170272823765, 0.1346095532222456, 0.13931966248063582, 0.14410737993848613, 0.14382654677774667, 0.14309952551247734, 0.14324284516840627, 0.1365172388969145, 0.14693616687805508, 0.1414564994448689, 0.13876599367433967, 0.13672233725027796, 0.13487708835001072, 0.1445853558104675, 0.13404210108078896, 0.141401212149338, 0.14729279447728044, 0.14872641605297127, 0.1350632140860931, 0.13647976400541914, 0.14088595875175142, 0.13318518358188056, 0.16420408628338357, 0.1348311628333333, 0.14355908259605457, 0.13879174555266596, 0.13764593885442333, 0.14494549026829537, 0.13372496095454733, 0.13925238276068996, 0.13650616726144724, 0.14729058860536992, 0.13443419227721867, 0.14140015437626002, 0.1302318793690348, 0.13556130371659977, 0.1399566138881258, 0.13641516955200297, 0.13717972701081507, 0.1571722438889038, 0.14797517506393126, 0.1319165765189502, 0.1398382095139937, 0.13512441449526305, 0.14837752413841238, 0.13551783243615612, 0.1513266725791105, 0.13797378141194655, 0.141447393548898, 0.1424173974230253, 0.1424173974230253, 0.13861080825626898, 0.1369953352796346, 0.1410452656391854, 0.13453307065354014, 0.14136567133337186, 0.14829498270715696, 0.1369190196918488, 0.14002214895370355, 0.1437387639043145, 0.13225607654813218, 0.13527140622812006]


bins = np.linspace(0.05, 0.2, 100)
fig, axs = plt.subplots(4,figsize=(5,9))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
for i in range(4):
    axs[i].set_ylim([0,20])
fig.tight_layout()
fig.suptitle('Bayesian loss: 3 tests, Omega=100',fontsize=14)
plt.show()

'''

'''
# Put loss value data as vectors below; this will generate a set of histograms
# FOR 30 TESTS WITH ALIGNED PRIOR DRAWS
lvec0 = [0.14335674740847668, 0.13563245422451242, 0.1415963480854923, 0.14477842127227447, 0.1403673820567332, 0.14422281864161265, 0.14329261560423487, 0.1420062342037913, 0.14433295208263913, 0.1403238089040552, 0.13622023914021908, 0.1331215477563341, 0.13985955261052357, 0.13625107480023418, 0.13278830969158803, 0.15104810337007638, 0.1432066934207097, 0.14654590113820598, 0.14155140609144773, 0.13852272271124094, 0.13445127898827322, 0.13908978650635498, 0.1360373375312127, 0.13526163120094575, 0.13351511475872638, 0.1392834993888565, 0.14217784089826874, 0.1377067146937541, 0.13608336613577093, 0.13836213835655492, 0.1425563771081175, 0.13701890404704872, 0.14275701547310093, 0.14037446661784928, 0.135899731846271, 0.14472193099297048, 0.14004487852829342, 0.14100806934369722, 0.13803489989603657, 0.13771365713309786, 0.14139179718653286, 0.13087720270484154, 0.13903043764659487, 0.1451529118187262, 0.14357323831263982, 0.14277614431056324, 0.13806245145666834, 0.1390161454589516, 0.13787407260580362, 0.1298548333936015, 0.1286585066046738, 0.13813220094369869, 0.13870075098025772, 0.134798114071913, 0.14181892280318806, 0.14415150594437046, 0.1401707511122268, 0.13713175719384266, 0.13294292602440483, 0.13685260067190896, 0.14083582503649433, 0.14136240031126082, 0.137865717839781, 0.13393002615490654, 0.1427531689634655, 0.13538762826838718, 0.1496264644252375, 0.13540613334631685, 0.14101331288050714, 0.14671835743546532, 0.14478887242738706, 0.14931950638902403, 0.13283790393728137, 0.12970826512223263, 0.13796919743108113, 0.138645518281725, 0.1376171622310323, 0.13691141612588123, 0.14049677187086496, 0.13977659698381142, 0.13564191745044885, 0.13998212469718388, 0.14584815842274426, 0.14039224867696098, 0.13309154841127116, 0.1440026953609819, 0.1417341702439205, 0.14080983152552431, 0.14814505856180918, 0.1409467537003577, 0.1427572188544298, 0.13285891774806471, 0.13551388876899503, 0.15248278741427487, 0.1405290826335275, 0.13718595570106867, 0.13974116032513081, 0.13990250040610652, 0.1365994485550459, 0.1423325398989005]
lvec1 = [0.10634961174656275, 0.10302512056824153, 0.10573264203096888, 0.10940710352094114, 0.1079996198537457, 0.11386740538578519, 0.10339574572939116, 0.11705737348112238, 0.1046042481657203, 0.09925637880479482, 0.10425024005195677, 0.10352373313627466, 0.10063670495558483, 0.10799571446493482, 0.10836126822711473, 0.12051487450224642, 0.1045375314987425, 0.10439329799781122, 0.10268174950658925, 0.11234612369685851, 0.11234612369685851, 0.11800333845717682, 0.10418129588512696, 0.09703525486762068, 0.11616352612463957, 0.107728523136265, 0.11633564096686878, 0.14649054407733408, 0.10344308352390195, 0.10115707730680844, 0.10282231132299667, 0.10199820867319392, 0.11032410876508615, 0.10706950609289534, 0.10585915421202698, 0.1021843099315789, 0.10141639972518424, 0.10633943015662597, 0.1221172424682917, 0.10957372366455317, 0.13957032579483666, 0.10611496993096368, 0.10990296947641609, 0.11629037552378135, 0.10612435791561563, 0.10242963152014234, 0.10585724486168423, 0.09904601046902506, 0.10417078282127863, 0.11948214224211381, 0.1022160665374903, 0.1003382119019552, 0.12185635853549258, 0.10433125333239412, 0.10762830180763937, 0.1077274211549446, 0.10323979689185256, 0.10958942997651802, 0.10744930711459766, 0.10439667181367551, 0.10586832207215371, 0.10450362736603448, 0.1071311510626874, 0.10542673990664103, 0.10303039852242575, 0.10603698598299861, 0.1106886958276474, 0.11195802212106028, 0.11213153776026705, 0.10369695483929618, 0.09954381801274868, 0.12097884178410417, 0.12277409961119393, 0.09990737564843913, 0.11338768289126687, 0.15036613871870752, 0.10582848369463524, 0.10609097453062596, 0.12057525824788429, 0.127423256991933, 0.09972793858494255, 0.10598418649068067, 0.10864586614576892, 0.09884469447717312, 0.10904726369610386, 0.10290399590203675, 0.12341221567552675, 0.11093605699657906, 0.10921650225520371, 0.10144867949049492, 0.10277198535904514, 0.10424750829055592, 0.1632766996357331, 0.10662150026302795, 0.11551713425926377, 0.10258832038145932, 0.12703072288637893, 0.13534176208647325, 0.10638320675903544, 0.11408565414293617]
lvec2 = [0.08846907100334117, 0.12204653405437324, 0.11134160642351906, 0.138984542650809, 0.1337369860752422, 0.1371240842789891, 0.0971554324870248, 0.09958346985577195, 0.10070951154512953, 0.1303105442447949, 0.09523713865503293, 0.10023565081432302, 0.13808120389705528, 0.09258572338941401, 0.09535686158262739, 0.0989405020611249, 0.0977509560559939, 0.09233369659043171, 0.09186502887081881, 0.10229916568694297, 0.10446139081607504, 0.09833252948729544, 0.09370073654768755, 0.10118830212537351, 0.10323801562791826, 0.09571028646088366, 0.11641418219671133, 0.1001482614667568, 0.0970847128224121, 0.1214891701670199, 0.133204534038947, 0.09815319755985254, 0.1002936933775179, 0.11256089490548762, 0.09745801905562622, 0.11601971501035156, 0.10962601346989359, 0.0933793220288433, 0.09331437554207622, 0.09077959285606141, 0.15245414818948413, 0.09419395594480588, 0.09706474617576887, 0.10008984062064338, 0.14960513112981558, 0.0951139581791243, 0.09516114169655121, 0.09495360874139615, 0.14297128761257477, 0.11420523895286804, 0.09338834414834506, 0.09487621972156311, 0.1503284823843334, 0.09709529172952934, 0.13974139242667244, 0.11358824745871843, 0.09634722324888377, 0.09585720856835372, 0.12350946577094911, 0.11036323660636903, 0.1060997456805723, 0.10028146661742278, 0.09501072192079588, 0.09744867882438121, 0.08642881123426427, 0.0958143651785655, 0.10959436859020148, 0.09085354258311089, 0.09891157466466459, 0.10923513897563925, 0.110797370644161, 0.0971066933944853, 0.09544757522873497, 0.09315381629647514, 0.10715618252977116, 0.1432884402439888, 0.10187255512044427, 0.09537034747487716, 0.11201339933751868, 0.09471477295529196, 0.1017373734719954, 0.09404799962512932, 0.09740298340522555, 0.1067236592961917, 0.1205748753679981, 0.09882357772764515, 0.10667669622767387, 0.09924358806975918, 0.0990024738621961, 0.12995829286857116, 0.11779277896907878, 0.12233044145918576, 0.11989642326551032, 0.0952712402594451, 0.09815837555355965, 0.10329483010975068, 0.09749041083852679, 0.10662786973651314, 0.11014263299374114, 0.09905529546390655]
lvec3 = [0.11098974193332863, 0.10125051232420816, 0.11315345875479645, 0.14824849585948016, 0.12366359215833488, 0.11542909714969321, 0.10183381102989159, 0.10263148538154584, 0.11148631710088726, 0.1084937101564695, 0.10550927756678886, 0.09857013666010819, 0.11347462151166492, 0.11638102843486009, 0.14953441205466078, 0.16984221819246018, 0.16984221819246018, 0.11434691923912824, 0.11744327488708049, 0.12382928134932471, 0.10135108238722856, 0.10646095088922433, 0.11267174450693104, 0.10452698377828328, 0.09998643667474148, 0.10841215679858358, 0.11654286146832589, 0.11325844282086751, 0.12314719169286412, 0.09956359434182292, 0.11888835431978494, 0.10188299816254247, 0.10582320905400318, 0.1043406496092699, 0.10044141640207754, 0.10077252305876916, 0.10049698796349667, 0.09740979559291969, 0.10236601308361748, 0.10659814250463902, 0.15247726856568197, 0.09919174837610781, 0.10163849402694841, 0.11481432724190282, 0.10856790094035465, 0.1114748956445173, 0.10352971388114812, 0.10858561442707555, 0.12329119948704052, 0.11064231694477107, 0.1027685207630217, 0.11217936643228103, 0.11234530737792149, 0.09478842508698913, 0.10700042430667996, 0.11645010937684662, 0.12705002168750693, 0.10700045503345265, 0.11048688365719368, 0.1090621431847006, 0.10319468604112218, 0.1043909446429444, 0.1173314403933393, 0.11883522071079118, 0.10665173334224833, 0.10028275085055974, 0.1372634290037096, 0.11168466708454744, 0.10517656102771333, 0.12288115764386295, 0.11296476127238188, 0.09948237746650039, 0.12040098137010717, 0.09620255719752412, 0.1270244262138782, 0.134629257064983, 0.11153118939648016, 0.10603054028747022, 0.1024523685893314, 0.10412519688945349, 0.10922092562882185, 0.10514128052629228, 0.10603737019736942, 0.09567766033447421, 0.14466657664118415, 0.0984397089939447, 0.10132508254875486, 0.09823073295612572, 0.09847154149921909, 0.1410335938381654, 0.114412858617555, 0.11721596504756412, 0.15588738400060143, 0.16126500233961147, 0.10722058087143405, 0.1121644342687555, 0.10912254820238977, 0.11219291217967348, 0.10065879564721798, 0.0999875760494058]
lvec4 = [0.12755901234498981, 0.1272227641499066, 0.14367923011504508, 0.13053818512938012, 0.1354029707310704, 0.1298842528575228, 0.13556599561283753, 0.12882711757260126, 0.14423171736957027, 0.13096163052233253, 0.12770621594889955, 0.14030751852218828, 0.14035633491785288, 0.13114531238772126, 0.1331719733120443, 0.13567356195481461, 0.1490404304901742, 0.13030520418802785, 0.1387610294589461, 0.13984289095763378, 0.1324402782954368, 0.13172723443993992, 0.14829909361158036, 0.1434638988868053, 0.1307147339895076, 0.13369199138321494, 0.133805303387655, 0.1383671861895898, 0.13434287759205907, 0.13730766604181655, 0.14429296983483866, 0.13605026543510354, 0.1315971516370006, 0.1309955346472841, 0.14759889104242496, 0.14452508582904147, 0.13526105980782366, 0.13459903984755756, 0.13308721478508762, 0.12985762534582457, 0.13359981880406804, 0.1359209175245402, 0.1613232629588759, 0.13690079860486462, 0.1314831574048473, 0.12316615196930092, 0.14862233986449594, 0.15655375795732152, 0.12901679406343564, 0.13698481978942473, 0.140619462714984, 0.15621959699396687, 0.1367373979078948, 0.12862551496544217, 0.16393360638409954, 0.13296180368367813, 0.13551929876600186, 0.1319101905379993, 0.1333090316949643, 0.1489557019224573, 0.151405705927449, 0.1368362163670803, 0.14177224765357524, 0.13495369419410597, 0.13724089638363848, 0.1375429022727169, 0.13085983171046475, 0.14667167570411083, 0.1346887937588043, 0.13636792320858407, 0.1377412890786604, 0.13678690279274874, 0.14591363070804125, 0.1318799000890781, 0.13758805370578153, 0.13658942810948965, 0.126719276404252, 0.13889627014267408, 0.13908027432291317, 0.133998590509244, 0.13302006419665927, 0.13568733437844036, 0.15309171523905088, 0.14100265369227072, 0.14557212187220828, 0.13155229476946237, 0.13532644119538736, 0.1356997400631096, 0.1350185897368059, 0.13340735298659911, 0.1398879561759618, 0.1339859736836097, 0.14178053620692835, 0.1367110914095266, 0.1312977225589154, 0.1337349635710877, 0.13611726994672274, 0.13501726106424652, 0.13501726106424652, 0.1319575215552926]
lvec5 = [0.11872067099237227, 0.09895610022411544, 0.12700099599815784, 0.14712753354401087, 0.11158375608561251, 0.11267349844254829, 0.09931441224344452, 0.10231163474251982, 0.10306619335638965, 0.10099577917947894, 0.11572799753549973, 0.10255876177670847, 0.10673511299827146, 0.13731973208662265, 0.10331814587105605, 0.10188916831876102, 0.16064175940593564, 0.09036995882241274, 0.09936437775189623, 0.10039510988705937, 0.09345788779838007, 0.1061605729270244, 0.11216472246393407, 0.09295858514935548, 0.10425903565388886, 0.11320245050879844, 0.09885332535012906, 0.09944933637837676, 0.09755014875915358, 0.10577022110669429, 0.10975530386113794, 0.12787169722465172, 0.0966744814494863, 0.09609214275403467, 0.09963931425718413, 0.11235135519038737, 0.12064670871724047, 0.10448797341750722, 0.11592521939236976, 0.10407222291503355, 0.13872101618646057, 0.10933240840091268, 0.10512085013757809, 0.1057435988078292, 0.15708449311431877, 0.09485791554512941, 0.11961449525661479, 0.10805094412936338, 0.1008577328853939, 0.13062694148703327, 0.096394872433107, 0.13105596659546428, 0.12956350034806083, 0.11671796988575642, 0.11198920589797214, 0.11068534067187476, 0.12902022041504776, 0.09650605309560743, 0.09596308040247982, 0.12399148621033187, 0.09682917632894236, 0.09945931377364503, 0.11423569062031608, 0.09404760905783782, 0.09847638050056214, 0.11399995739878951, 0.11253401166176878, 0.10320521706938912, 0.09923486172922912, 0.09489160886285936, 0.13907691821162393, 0.1298500910681893, 0.1286073957830775, 0.10263102977204602, 0.1393161170796016, 0.10103989004690013, 0.10280911968074244, 0.1251268249167473, 0.10323530034160695, 0.15214569293930086, 0.10210234396340204, 0.11986066685833294, 0.1048705957725252, 0.14739161595801714, 0.1100903364369919, 0.09428409200279214, 0.09368788764765923, 0.09700318360426592, 0.10614703698983995, 0.1748170688456017, 0.09412375915458952, 0.09538892910733575, 0.09691684176437285, 0.10252822631874349, 0.10726494815620999, 0.0998073001146943, 0.12903506611103932, 0.10898517723745178, 0.12284656046167128, 0.09417709346893337]
lvec6 = [0.09541564947521758, 0.09161902400008325, 0.10235312530707762, 0.09196206240301862, 0.11007526916394288, 0.09253809853804217, 0.0963968081617305, 0.12362163157925166, 0.0922002845907695, 0.10011569470162285, 0.0987552794995027, 0.08976087068464958, 0.11403595385932902, 0.10958919838728497, 0.11032949404631254, 0.1282774491404776, 0.09452485791782178, 0.09213612011490224, 0.12373675733661055, 0.09657141137271266, 0.09369052700203956, 0.11090551809572999, 0.11337577335963916, 0.09423018746000868, 0.10836593603574535, 0.10507098982063674, 0.11966476897350929, 0.09901478925076553, 0.09070335475937656, 0.11196600454576192, 0.125784942576603, 0.09871736285803594, 0.10885636635208487, 0.09243560680582175, 0.09419036701536816, 0.11561744259515228, 0.12714140592169795, 0.09530016693014884, 0.11355024241171885, 0.09401870391743036, 0.15237683720437578, 0.09501893825150261, 0.10343186992976844, 0.11697049810711516, 0.12867076376935277, 0.09369108793836634, 0.08899365388340466, 0.12929060317480318, 0.12262646070672541, 0.10388430332113206, 0.10929495142548187, 0.09466134999595967, 0.13835925726861634, 0.10712674793981844, 0.15747969250172375, 0.13196193542933668, 0.10742359164501694, 0.0911802033912603, 0.11058051068252643, 0.11415236858654586, 0.10767405768400462, 0.10091163748684234, 0.0938177029906322, 0.09195897130041346, 0.09516862356230849, 0.09595288540103072, 0.13984680061505844, 0.09380151307572963, 0.10006534992504172, 0.10604599531979718, 0.09676664479157412, 0.09702179161039555, 0.13755747080698374, 0.10724671787683766, 0.12579572620768223, 0.15023990510487326, 0.09493300525336293, 0.09432462069399948, 0.09495493481987206, 0.0965080425191013, 0.12786737657270744, 0.09429621824266661, 0.1293549734753557, 0.11414116960734043, 0.10835370372919054, 0.09507806911628845, 0.09743645090611554, 0.09343463153806665, 0.09329779989943472, 0.09199857782098182, 0.10757097949806908, 0.1333866607252839, 0.09569078323873571, 0.09352157936457388, 0.132738775489415, 0.12447522814337839, 0.09361941567024173, 0.10865075352101125, 0.10757557812860262, 0.09596880980813018]


bins = np.linspace(0.05, 0.2, 100)
fig, axs = plt.subplots(7,figsize=(5,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.tight_layout()
fig.suptitle('Bayesian loss: 30 tests, Omega=100',fontsize=16)
plt.show()
'''

'''
# Put loss value data as vectors below; this will generate a set of histograms
# FOR 6 TESTS WITH ALIGNED PRIOR DRAWS
lvec0 = [0.14335674740847668, 0.13563245422451242, 0.1415963480854923, 0.14477842127227447, 0.1403673820567332, 0.14422281864161265, 0.14329261560423487, 0.1420062342037913, 0.14433295208263913, 0.1403238089040552, 0.13622023914021908, 0.1331215477563341, 0.13985955261052357, 0.13625107480023418, 0.13278830969158803, 0.15104810337007638, 0.1432066934207097, 0.14654590113820598, 0.14155140609144773, 0.13852272271124094, 0.13445127898827322, 0.13908978650635498, 0.1360373375312127, 0.13526163120094575, 0.13351511475872638, 0.1392834993888565, 0.14217784089826874, 0.1377067146937541, 0.13608336613577093, 0.13836213835655492, 0.1425563771081175, 0.13701890404704872, 0.14275701547310093, 0.14037446661784928, 0.135899731846271, 0.14472193099297048, 0.14004487852829342, 0.14100806934369722, 0.13803489989603657, 0.13771365713309786, 0.14139179718653286, 0.13087720270484154, 0.13903043764659487, 0.1451529118187262, 0.14357323831263982, 0.14277614431056324, 0.13806245145666834, 0.1390161454589516, 0.13787407260580362, 0.1298548333936015, 0.1286585066046738, 0.13813220094369869, 0.13870075098025772, 0.134798114071913, 0.14181892280318806, 0.14415150594437046, 0.1401707511122268, 0.13713175719384266, 0.13294292602440483, 0.13685260067190896, 0.14083582503649433, 0.14136240031126082, 0.137865717839781, 0.13393002615490654, 0.1427531689634655, 0.13538762826838718, 0.1496264644252375, 0.13540613334631685, 0.14101331288050714, 0.14671835743546532, 0.14478887242738706, 0.14931950638902403, 0.13283790393728137, 0.12970826512223263, 0.13796919743108113, 0.138645518281725, 0.1376171622310323, 0.13691141612588123, 0.14049677187086496, 0.13977659698381142, 0.13564191745044885, 0.13998212469718388, 0.14584815842274426, 0.14039224867696098, 0.13309154841127116, 0.1440026953609819, 0.1417341702439205, 0.14080983152552431, 0.14814505856180918, 0.1409467537003577, 0.1427572188544298, 0.13285891774806471, 0.13551388876899503, 0.15248278741427487, 0.1405290826335275, 0.13718595570106867, 0.13974116032513081, 0.13990250040610652, 0.1365994485550459, 0.1423325398989005]
lvec1 = [0.12201050841773795, 0.12043612929780032, 0.13073931438352507, 0.1364518894400282, 0.126623022019832, 0.12129034295509719, 0.1232672454634404, 0.12829647617332493, 0.1204383656377655, 0.12010396716036557, 0.12708881433791652, 0.12059223579432472, 0.12640641713012227, 0.12043747160548378, 0.1317713280271366, 0.13858549031033934, 0.13040661796428832, 0.12372466444805368, 0.12215449081690144, 0.1172009306470824, 0.12802623225846077, 0.1207461516663038, 0.12235892887452496, 0.1237439078162338, 0.14725564258748042, 0.13006245686750906, 0.14111960898512146, 0.17052348372877876, 0.1190717430571908, 0.12839190136479653, 0.1215378659762556, 0.13000799753778808, 0.14087523828697612, 0.12178319944876939, 0.11944931473707801, 0.13614838354520106, 0.1310193249361005, 0.13912347347964416, 0.13463403735188875, 0.12185038633366564, 0.13740933280689316, 0.12913455703853216, 0.1188198890500554, 0.12938061803611323, 0.13219144179335499, 0.1209876416531576, 0.13139604212837558, 0.13945216905042135, 0.12512858752159517, 0.12818879468468689, 0.13252466861777462, 0.12574018916451998, 0.12203959568330597, 0.13923442145341772, 0.12246806165101219, 0.12011562841490274, 0.12643323707555493, 0.118186357124321, 0.12935168572901068, 0.12191470565635104, 0.13134511716605102, 0.1311317978540064, 0.12207860410895834, 0.124199649707826, 0.11923683773905948, 0.11854576204531829, 0.11753594477762297, 0.12656098087414308, 0.1724834600715802, 0.12438430951545777, 0.1229256028188119, 0.11795059660489447, 0.13636488838672947, 0.1254482273206744, 0.12947143515380027, 0.16600685694908843, 0.13088972029296908, 0.11564403011841372, 0.13671181841978577, 0.13171782578024416, 0.12896629513125607, 0.1362756683234587, 0.11843610117102911, 0.12863906985263984, 0.12339918133715126, 0.12634457005632155, 0.12313895622846809, 0.14260811473494, 0.13626616465233088, 0.15372332948843448, 0.1434845627302847, 0.1230299628340709, 0.13176708856049998, 0.1395751781776649, 0.11975090088573094, 0.12361396890224147, 0.13871207590032084, 0.1297945249169143, 0.12117548483589585, 0.12975781998413966]
lvec2 = [0.15238542474736136, 0.12416000145102413, 0.11856185872093881, 0.12545129368105196, 0.11800066341138132, 0.1310749103727152, 0.1215110780178015, 0.11857074405567126, 0.12389455875043998, 0.1530164510573582, 0.12161702328986287, 0.12992232214863692, 0.1252833347448361, 0.12503413557512796, 0.13030466064318882, 0.12301603919333307, 0.12767357715731098, 0.12187376486069143, 0.12839519369532118, 0.12187149680502116, 0.1316911872028336, 0.1670777138626097, 0.12697005698390443, 0.1251608812969274, 0.12321194714345672, 0.12805819638937815, 0.12347895706959296, 0.12187385208205766, 0.13936980037679325, 0.12666746805772217, 0.15235565088686923, 0.1613461530037538, 0.12236035538670618, 0.12684132758695707, 0.1220728161552606, 0.1300059913518878, 0.11716093367861431, 0.13402676288917956, 0.12241962555165883, 0.12264167358758132, 0.16281436208884878, 0.12056146931995634, 0.12290217673851227, 0.16651647434137162, 0.16927325019045486, 0.12944508905261645, 0.12988904262008888, 0.12294224674448281, 0.12110165082456244, 0.13357607455910664, 0.12594857767702744, 0.1269027483049385, 0.12415627402620194, 0.12128567177768446, 0.12737086085310634, 0.1180265010822364, 0.17344564060968254, 0.1293714295644241, 0.12223619639782239, 0.16405124427145734, 0.17084447347450293, 0.12974806157984156, 0.12178804449372693, 0.12604369300039517, 0.12453163835779633, 0.12654454158871623, 0.17713094005456867, 0.1681364617228342, 0.13314289818336425, 0.1281644397708753, 0.12327975016436318, 0.12924059040596117, 0.12164580144421144, 0.11804350443733692, 0.12106292848486871, 0.15226808411335116, 0.12460647669956389, 0.12384383655708565, 0.12061655988946357, 0.1682564257436373, 0.11849829654882289, 0.1237931111023102, 0.12896236813406728, 0.15294569683681017, 0.12456469764409682, 0.11731549903908756, 0.11962179433370436, 0.12643206776930294, 0.1290755183982052, 0.12578900407133392, 0.13417482822356114, 0.12750336687043978, 0.13200614014992354, 0.1301742209724923, 0.11938304339372552, 0.16029317773572618, 0.12203338206476552, 0.12061844773010158, 0.1192011085902017, 0.1168882509688956]
lvec3 = [0.11968945017493399, 0.1325436932290337, 0.14304805439947274, 0.1372543418415863, 0.12290613305555953, 0.14695010942380696, 0.13031555945168918, 0.13531654564770476, 0.1158741789601965, 0.1498587069417706, 0.11779397998017582, 0.1283547211242966, 0.1621151804519011, 0.1257006999953918, 0.11991742811824019, 0.1268546045454344, 0.12394170573349639, 0.12477126178978204, 0.1190782946526823, 0.131038995226777, 0.1324838410920371, 0.126966483959189, 0.1284249126060708, 0.12168406900888132, 0.14376143438692746, 0.13869800542490932, 0.1333019924968027, 0.1208481573363508, 0.13149910016599742, 0.12454346804251852, 0.12416419154401838, 0.13750454604372964, 0.1286813686370034, 0.14028810905728298, 0.1213177352332298, 0.12695929573630096, 0.1433875629602553, 0.13470849533432652, 0.12817395763370265, 0.12285242535964941, 0.13870021451858744, 0.13600244849094315, 0.1270527995828381, 0.12280415161590945, 0.12637045713291722, 0.12141924277310306, 0.1246896370512028, 0.12269154918042903, 0.1287737374226314, 0.12985925749546925, 0.13354916306914855, 0.13795245908487103, 0.14769512635074547, 0.1397037543205498, 0.12308134046357264, 0.14974958664483456, 0.1356718864457288, 0.1253954947931722, 0.11834632002053354, 0.13763653544765558, 0.13683202603444303, 0.13328576005594758, 0.12057438649922828, 0.12482051629691142, 0.12192516990834829, 0.13580861906678587, 0.12071682867720668, 0.13550846627877247, 0.13588277684680278, 0.16369077088013323, 0.1227169568278283, 0.1271825432585842, 0.12522762416783856, 0.1612926181934334, 0.13727307213520676, 0.12942489580816072, 0.13026549173333488, 0.11983336499477812, 0.15224764991568943, 0.13337120600716007, 0.1403182666152804, 0.13139788948796524, 0.13166045104960175, 0.11710496883564678, 0.13108140747205071, 0.1277556031748408, 0.1250926460932209, 0.143131392246206, 0.12396595753727355, 0.13399058931192548, 0.1236393191280366, 0.12780745696316256, 0.13155860738370817, 0.12861567393236803, 0.1415479851588361, 0.12999045002741, 0.1359923098261614, 0.12383469845050561, 0.12866916743505388, 0.12401132881977579]
lvec4 = [0.1352845722566932, 0.14676481273608546, 0.13617179930790266, 0.13111194193337558, 0.13261705480888214, 0.14324954913507976, 0.1407156988441613, 0.13071409341375467, 0.14584916511227436, 0.13904442195739236, 0.13942570538761256, 0.13511782995813032, 0.15741384910797232, 0.14134527072950878, 0.12797589612112317, 0.13240076164430448, 0.14603277628727662, 0.1376266746261868, 0.1372023821870774, 0.13541094989804836, 0.13625487761142846, 0.12447453708396672, 0.1382351680678216, 0.14058101846783105, 0.13389382651385662, 0.13990347747294574, 0.14488860174608864, 0.13856687175919022, 0.137353958602558, 0.13642015110993586, 0.12974855792662338, 0.15408758414245627, 0.13821155691532525, 0.1352709133185309, 0.14170062250351748, 0.1437968978433749, 0.17244173701141183, 0.14552508931270425, 0.13218146746173376, 0.13266303015402042, 0.13564130945252847, 0.1422149899212039, 0.13829300075938372, 0.13900973201268413, 0.13511936285008339, 0.1375824488642537, 0.1383253584553228, 0.14913740132579442, 0.14284340702935014, 0.13451574855649923, 0.14023960229927757, 0.13775515057865548, 0.13927640226181268, 0.1344168495096326, 0.13242825560538227, 0.13468672644975974, 0.15844834745132955, 0.13216370070921776, 0.13943167205203777, 0.14228292777709944, 0.1481298745263082, 0.147229085242329, 0.13826794796438865, 0.14071736778976537, 0.14069831017179463, 0.13987957907623527, 0.13491992218038842, 0.13618380638845887, 0.13677340694471815, 0.13919032228806608, 0.13304153436570285, 0.13973684718318358, 0.1364626444003569, 0.13624335520653014, 0.14040138286659196, 0.15014057228145838, 0.14720994690273764, 0.1386719505841382, 0.1513947884882519, 0.12698156752057949, 0.1400097948280201, 0.13075318688227747, 0.13973938301337638, 0.13814820260866645, 0.1431025063507889, 0.13628003172330858, 0.14455007373473877, 0.1352750432016824, 0.1538728424402952, 0.13659639179914215, 0.13566048995416258, 0.14170515913794587, 0.12987367555904136, 0.13447526430042245, 0.1420619370668284, 0.14273022667987856, 0.13441731071875734, 0.15467886772404668, 0.13124039492598313, 0.13286578526945192]
lvec5 = [0.12191093611978823, 0.12708169743205974, 0.1272636312739816, 0.14103361731286418, 0.12693632576654, 0.13304107664810577, 0.1302975872196582, 0.13256094255129988, 0.12692322287558372, 0.13375235591878326, 0.12025968972902515, 0.1261516981892684, 0.11986502410706971, 0.12138320768684153, 0.1813892352356074, 0.13401682206709115, 0.12669158506368067, 0.11985349037923573, 0.13056358656370937, 0.1356342482734177, 0.1204218168262275, 0.1400747526297201, 0.13675755106631982, 0.11831008430642476, 0.12755393808507823, 0.1593038250647806, 0.13996987224224056, 0.11820675748145908, 0.1271468449259773, 0.12454090031023654, 0.13368031785519457, 0.12007752130071597, 0.13371587422897344, 0.1556396335987057, 0.14523760438506442, 0.13065697246909883, 0.12386942982227049, 0.12402642437575141, 0.12672499429565415, 0.1336400508810701, 0.12390288782713436, 0.12859661542374207, 0.13479812592240617, 0.17728763842220086, 0.20271175247286882, 0.13920968054911512, 0.15309643997132688, 0.12929922262035645, 0.12252606771695293, 0.12115454015934378, 0.12557714817101553, 0.1278999587941183, 0.12612818896832934, 0.1276101793657718, 0.13605125188246692, 0.13625655288186111, 0.13459521031844301, 0.12622357697921396, 0.12130178930914494, 0.11879710682753364, 0.13272920273747954, 0.12233040767844738, 0.13050155418693982, 0.13652882039658154, 0.1393903112484995, 0.14264696944389513, 0.1502599102044462, 0.12708582344193506, 0.1300382126825252, 0.12279958314682231, 0.13570107823705985, 0.1300847399161663, 0.12260123442009686, 0.13061035828398823, 0.13595355056167482, 0.17303456461845537, 0.1214447900240019, 0.13132902212166903, 0.12526856532784453, 0.1340549121066598, 0.12531155098269606, 0.13925232204956975, 0.12837818778151572, 0.13301024305047923, 0.12084300032357848, 0.128619300598818, 0.12478666049535385, 0.12305730026092342, 0.11869881179935267, 0.127185191242855, 0.12459116032053631, 0.12994807480650994, 0.12953497159669972, 0.12205133545614338, 0.11504257424981326, 0.16083365841896502, 0.13833483629434748, 0.13910363830732322, 0.1364123941028384, 0.12807200355649667]
lvec6 = [0.12475497644583944, 0.1386321013935679, 0.1208753412297372, 0.15688250291805805, 0.12083183071126759, 0.13526962263083997, 0.12232458042947052, 0.12346772862205556, 0.12158596803391417, 0.12664952090823417, 0.12522970006424913, 0.123706420361703, 0.11880015458354379, 0.12699231530005928, 0.12262686596504813, 0.13390241032968137, 0.13652605835439396, 0.13769186591432675, 0.11953670579205597, 0.12533318635500146, 0.12902414968714826, 0.12540601949868774, 0.17509188604238196, 0.12225868156154623, 0.16574629330625992, 0.12300936403903032, 0.13494763088967124, 0.12245246666274992, 0.12233289331802301, 0.12839150207297131, 0.1282060877504529, 0.1393682809834952, 0.1254239380523154, 0.11927829024952745, 0.11928392423297908, 0.11902723275230272, 0.12059340731748759, 0.12318861995192346, 0.11368321155184725, 0.11951662661787217, 0.1566939652890786, 0.11728135703106865, 0.15889529838957087, 0.12348039186301266, 0.16512875522579423, 0.12201270489254022, 0.13639955005658538, 0.12211946993422265, 0.1415225617063233, 0.15610802663623036, 0.15573151959997997, 0.1457790620797599, 0.1624898882941196, 0.13090985481725606, 0.12818600780594733, 0.12088855446536372, 0.14437680332888114, 0.1269528795501376, 0.12897512661472918, 0.1473558509233415, 0.13247059623426952, 0.13093752438623257, 0.13341472064259094, 0.11939492882664672, 0.1300606838149642, 0.13321853915165002, 0.15559933860002736, 0.1271223345548175, 0.12601001137643358, 0.12256722591761975, 0.13689565112612762, 0.12844436814336876, 0.17247821767148042, 0.12516487317262992, 0.11908008607474001, 0.13973670445627687, 0.12182055570553972, 0.12582761103969578, 0.13268530311862492, 0.15307261770021477, 0.12349380649330256, 0.1373215278132167, 0.14381270185270073, 0.13777692661572863, 0.12018275758883668, 0.1199307398555828, 0.13016881811720543, 0.12777285283597695, 0.12039360857817911, 0.12713943788777454, 0.15336069214878204, 0.11942313948012324, 0.12416908300280852, 0.14013886517298757, 0.12807446768004763, 0.12032389718180138, 0.12210820075054835, 0.13204462579092932, 0.11645497995108763, 0.1366719345439779]


bins = np.linspace(0.05, 0.2, 100)
fig, axs = plt.subplots(7,figsize=(5,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR DESIGN 2, DIFFERENT BATCH SIZES
# BATCH SIZES: 1,3,6,9,15,30,60,90,120
lvec1 = [0.1382851174053969, 0.14001812171109226, 0.13754892582641817, 0.14319284601145926, 0.13795392990717406, 0.1268831860393539, 0.13223600103532054, 0.1306233249995498, 0.13924652706958165, 0.1283945989188211, 0.14368256557434433, 0.14191766456895744, 0.1469925728560264, 0.1321289876524692, 0.1366371934135474, 0.13468753456757593, 0.13767272693538932, 0.1345128702034592, 0.13505360014551546, 0.13446371958911923, 0.13613065468488791, 0.13894723230325975, 0.13451775636662905, 0.13809931962925306, 0.13714559659227157, 0.13947953429030577, 0.13479306133454735, 0.13489609132095903, 0.1385013978833726, 0.1284548491658115, 0.13836339154918326, 0.12867732693672904, 0.13355659960520164, 0.14104482065648566, 0.14060719555447607, 0.14029681962736493, 0.1429691018617521, 0.1433579493697108, 0.1465888643820997, 0.13954572028655488, 0.1315151451873408, 0.1322133905511833, 0.13677325648827102, 0.13132738129063065, 0.1396219057072618, 0.13282353388666626, 0.14464659775400643, 0.13157413090798625, 0.14290500938721792, 0.13606377714180506, 0.1426863986668447, 0.13815023052139153, 0.1435340749717443, 0.14521104266817897, 0.13825193544202158, 0.14142513625986158, 0.13561307269020076, 0.1377560986712839, 0.13509712322728037, 0.14260994232825824, 0.13385919339080263, 0.1335819901588062, 0.1411477138695957, 0.1335391487542657, 0.14064709078284116, 0.1375111864366289, 0.13436689317995523, 0.1411841349361796, 0.1395267256791663, 0.13203486765745825, 0.14753671004614638, 0.14122911369888672, 0.1353850587486798, 0.13473873721520968, 0.13127212453049972, 0.14660675813920687, 0.13659467867713088, 0.13930576268556452, 0.13780771828542085, 0.14398843148160873, 0.13565742247492057, 0.13034283855672554, 0.14594461044332185, 0.13383305039379773, 0.13924848542633433, 0.13981329678561827, 0.13373203977455253, 0.14400246518386972, 0.1322207240959983, 0.13896453774977602, 0.1344915972060527, 0.12712028508556686, 0.1347847239791129, 0.14007453553053947, 0.13904568927790434, 0.14696243171282175, 0.13874487494336493, 0.1398263250716958, 0.13621489140825105, 0.1412404923181527]
lvec3 = [0.12754209193762045, 0.14031219720978916, 0.13010100439884947, 0.1327246470991515, 0.1332488070741414, 0.17785684814211353, 0.12842574463210446, 0.13181677560053628, 0.1343499195285006, 0.1323374633661742, 0.12836862511602445, 0.13001859567488736, 0.1365527321797588, 0.12775634414907083, 0.14580346329980734, 0.1640785189966381, 0.1311423007944489, 0.13223061726192142, 0.12767395998354436, 0.12429207661021083, 0.1265604764724026, 0.13072937443355737, 0.15671777269777182, 0.12514181892215678, 0.13168644644057526, 0.16274530137939722, 0.16654474484115633, 0.1316258004074624, 0.12731853589008554, 0.13304878913448515, 0.16877064424013738, 0.14011507180814017, 0.13192862095566837, 0.13519505789846187, 0.13002509201899204, 0.13168205990715817, 0.12994389799319672, 0.13038181706740126, 0.13431882708195128, 0.13746970899234498, 0.13539540264916458, 0.13187656307255322, 0.12431849400498717, 0.1359421820996568, 0.1402045525933901, 0.13004588835054184, 0.15541791834086593, 0.14064162552679338, 0.14398776681161168, 0.13098598869805433, 0.13149320194788397, 0.12466650137227676, 0.12558509385287775, 0.12866038302659563, 0.12276005085403116, 0.14072567557070134, 0.1352397865128543, 0.12754968146727946, 0.13486722902716416, 0.13812067525789604, 0.13077164978460684, 0.12421614836506772, 0.13053932787578845, 0.1424602422968631, 0.1356655009144377, 0.12336190397019592, 0.1763291581758909, 0.13485437977146017, 0.13710596579031564, 0.13536365402373685, 0.13468122921665523, 0.12917129059795848, 0.1276483697656916, 0.1323977545839571, 0.12551400367921778, 0.12857307122660724, 0.14361415551003537, 0.1308466649890505, 0.12804604661716115, 0.13949772094922838, 0.13469768774136429, 0.13439317572192727, 0.139571936534967, 0.16138343349345874, 0.1337429322374952, 0.1264559037967682, 0.13287607049071282, 0.12886536830391265, 0.1289458592389802, 0.13972577268180966, 0.16357485389183302, 0.13183066178615818, 0.1286594029985115, 0.14251296512081071, 0.12992524663842345, 0.1276910317582295, 0.13177232012817194, 0.13286285454203875, 0.1286328856645646, 0.1275233927771327]
lvec6 = [0.12433754182667398, 0.12194348461317742, 0.12590870824370903, 0.1650612399274014, 0.11660323939954799, 0.1550012255757987, 0.11851821551745177, 0.11300075272196147, 0.12603735603038183, 0.12759422397869968, 0.12675597702853525, 0.12765058383753056, 0.17304937455387537, 0.12331365028903303, 0.17084474441074896, 0.12217704660509349, 0.12769327218933202, 0.12361541210417527, 0.14987209412511546, 0.12220345346118416, 0.11618055556088235, 0.12317396772104953, 0.1591241772708671, 0.1287501426036278, 0.15999209455379718, 0.13352134588142314, 0.12439835851025323, 0.12552404198207331, 0.15391190905161137, 0.12668131788743184, 0.1276905388836984, 0.13164493503925964, 0.12139037365842506, 0.12346584630474629, 0.11538089543509918, 0.1269439931616859, 0.12959254877434268, 0.12463013733521121, 0.12690442778291264, 0.12770915563434942, 0.11834668515457407, 0.12203489790679796, 0.12464968358416198, 0.16547713090274027, 0.15345171719285375, 0.12843650892478584, 0.15134025143850063, 0.12183171900321203, 0.12896614137077153, 0.12545796647542629, 0.11748932973867503, 0.12102198277823914, 0.13605490663819864, 0.1640974269439278, 0.1315371940008381, 0.13593019290635003, 0.12403400849140193, 0.12558254177597689, 0.13432269089487242, 0.1366098321735959, 0.15287600805506404, 0.12135458181026205, 0.13251252045351086, 0.12120736337653858, 0.12345252567843581, 0.11849174293757815, 0.13204872903719025, 0.12510997166087223, 0.14710924898264116, 0.1218828264663268, 0.13573031596717167, 0.12424194248911892, 0.11933529870096257, 0.13109162013822578, 0.12332355525620181, 0.17477530317815923, 0.12731653315765565, 0.12550689364421475, 0.12427427991209355, 0.1244676977894243, 0.12438542288414496, 0.11158700451513842, 0.12452126100538356, 0.1649556065840589, 0.12188870584145282, 0.12295867250656625, 0.12321345616520511, 0.12934543660444442, 0.1315598952043253, 0.12538777884538446, 0.11930110198822327, 0.12534049573460468, 0.12703960437205986, 0.11903414221469213, 0.12323933245863394, 0.13339834224559424, 0.12633232565946675, 0.13161595636186946, 0.12377157689127248, 0.13250428442928405]
lvec9 = [0.11748928506343179, 0.1460863128067855, 0.11407049155926802, 0.14705880300764398, 0.12019339581428685, 0.14210327984212776, 0.12117708711947142, 0.12542446337237548, 0.11635515037930713, 0.11614602839185952, 0.11640537681412763, 0.11948710527913581, 0.12672512842236047, 0.12027594834758522, 0.11705752492854495, 0.11829839088786694, 0.12770860287185318, 0.11481091575689541, 0.13903419072907655, 0.12287821308478383, 0.11455699727596148, 0.12357160001157354, 0.11801431451229694, 0.11454853602837017, 0.13967124212883272, 0.11892421015290852, 0.12364663673751937, 0.12185928791064343, 0.12067624768201367, 0.13283581858905597, 0.16726099216099857, 0.11755217273047704, 0.14720833212286794, 0.12169006857340385, 0.11577554762326946, 0.11652966139310228, 0.12227003280416099, 0.11482485195643105, 0.12498824916690547, 0.11414833926185687, 0.1183123444337524, 0.12057774564826762, 0.11964287688468388, 0.11321416081404848, 0.15739559050652757, 0.11953752087497012, 0.1456830208414179, 0.13248242768669363, 0.1256804870640552, 0.11644150462784875, 0.11701223929813914, 0.11925410843088004, 0.1193887271700322, 0.115374179889621, 0.1132558823810791, 0.16474111020751955, 0.14172310426915524, 0.11295236029146725, 0.13004867989595828, 0.11892065446918297, 0.12156572679687239, 0.11310809279177945, 0.1266641514065548, 0.11136726069602494, 0.11582608654479677, 0.11432925475383054, 0.11038295993953608, 0.11588890045679161, 0.1175709630608052, 0.12297917702100528, 0.12200921563828447, 0.11054971963042483, 0.1177305128860591, 0.13006524081993515, 0.11355679160189475, 0.1429608734920779, 0.11905624638155204, 0.11758549914063446, 0.14570046523085747, 0.12983117175492204, 0.12968948231215896, 0.1563702202141075, 0.13119106517259513, 0.12087327379758385, 0.11934216184420274, 0.11976654118547068, 0.11945053103727771, 0.12207708728938135, 0.12332228707172388, 0.14519247897275556, 0.1224920596426375, 0.12345624895108928, 0.11308087526474427, 0.1614900264608201, 0.1189529714552026, 0.1291038916022557, 0.12288951505524218, 0.11768090294824644, 0.14288249779541481, 0.12397805969293298]
lvec15 = [0.10772478949943735, 0.1498507501744442, 0.1120621733680482, 0.10393691698361628, 0.14836324690102073, 0.11384881647721916, 0.11134826713307305, 0.11162919692818385, 0.11666161585555063, 0.11303350927438531, 0.11140029928216179, 0.1358503558361647, 0.13068748292009127, 0.10629089004511434, 0.10862315885177481, 0.12957732083492318, 0.11228436236995433, 0.10886980114612207, 0.14722326660750482, 0.1064256403365992, 0.12038824757306509, 0.11427986638346274, 0.12713180293456697, 0.1413560206095047, 0.11139004397950053, 0.12762017441179146, 0.10956181229457412, 0.11053867109786883, 0.14524277006532368, 0.12428461881270848, 0.1412736536245981, 0.10953583434435428, 0.10888655300857414, 0.1088157622125833, 0.1093780440664395, 0.11379711733714785, 0.10930230385659931, 0.11046984222802575, 0.10616130108308247, 0.10914549335823213, 0.14955344324507286, 0.11484662806051446, 0.1181139854545459, 0.15410666170358003, 0.12749821651902288, 0.10909345408557734, 0.1403900068618267, 0.13039691069183443, 0.11432218847207008, 0.10997710131041034, 0.12009474720513151, 0.11422940871410302, 0.12188868155583975, 0.13166315302103518, 0.11923694728001845, 0.10867509079116396, 0.11179738933833926, 0.10975372404295407, 0.13591472634708132, 0.13844275703400163, 0.10848363468677705, 0.11215978383138335, 0.11776186929455223, 0.11015375612190173, 0.12833496487193213, 0.10771053270319808, 0.11304545256153277, 0.13406870027461323, 0.11055141065491172, 0.11566370780744131, 0.11119169159180312, 0.1017007437522097, 0.11803544641620836, 0.1122338898252369, 0.12998943183384984, 0.11287519157212027, 0.1108729984570672, 0.11102059228128512, 0.10910316894403732, 0.12623072355592566, 0.11192255556231677, 0.11053286199953882, 0.12414822036295545, 0.15933744541648798, 0.10813235156385653, 0.10721525819607955, 0.10800105793489968, 0.11303524374950856, 0.1150222414513403, 0.10599061529364426, 0.16621265062982146, 0.15197571932315018, 0.13838379295738407, 0.11403939233615723, 0.1075852100523573, 0.14422958779273082, 0.10922799107389135, 0.11225120578831836, 0.14987536847998922, 0.10900247560295566]
lvec30 = [0.08846907100334117, 0.12204653405437324, 0.11134160642351906, 0.138984542650809, 0.1337369860752422, 0.1371240842789891, 0.0971554324870248, 0.09958346985577195, 0.10070951154512953, 0.1303105442447949, 0.09523713865503293, 0.10023565081432302, 0.13808120389705528, 0.09258572338941401, 0.09535686158262739, 0.0989405020611249, 0.0977509560559939, 0.09233369659043171, 0.09186502887081881, 0.10229916568694297, 0.09769014380636622, 0.12441076071797716, 0.09562348292796775, 0.09894755161291612, 0.09076242632907182, 0.09900120031296175, 0.13508711227563935, 0.09688104831321939, 0.09303130639370566, 0.1002730850489025, 0.11704432618757596, 0.11086064850067875, 0.11421642464999045, 0.11224903432021985, 0.09658854889089168, 0.10155154091477625, 0.11313264385350051, 0.09646812107430189, 0.09448469219696544, 0.09590993358904992, 0.12666938714568207, 0.09323041161282601, 0.10004484549198316, 0.14708347169241295, 0.14215420667058778, 0.09993896998058542, 0.09085638171360762, 0.11144424407429102, 0.13331743110719665, 0.12653346231874676, 0.09625144190427022, 0.09443517157971194, 0.11538233583839862, 0.0942886572545733, 0.15040811652722275, 0.11104973161721125, 0.09544084724554917, 0.09615039404118614, 0.10951213864735798, 0.11443597658031189, 0.09281425125597206, 0.09353004646616962, 0.09189846418203722, 0.09255347949067606, 0.1126293928990595, 0.1020612492075022, 0.11397077467297453, 0.140034614394453, 0.09840195929636918, 0.09249003219794374, 0.09493236263693262, 0.0933496237858881, 0.09543991117379502, 0.09507212307818294, 0.09589540182851948, 0.12808578174114948, 0.09549844612906512, 0.09483262615764278, 0.09136296034539965, 0.10445110774280575, 0.10312559378396463, 0.13468756731500348, 0.09357601173632477, 0.11304264128209, 0.11433368758616862, 0.09403031746493874, 0.0924365093129436, 0.09163430929134851, 0.09714978624654719, 0.11045773385909953, 0.0972889114280848, 0.09245112879973207, 0.12393192749152888, 0.1318607692995051, 0.11037202091156127, 0.11092581456281522, 0.09532457750938307, 0.09564834367807871, 0.09638682641661762, 0.09801396237029503]
lvec60 = [0.11076886244999712, 0.10794217446131417, 0.0779743949369317, 0.11533592014254658, 0.1109052491749487, 0.08308703921016056, 0.08242476592046877, 0.08664817952957622, 0.08063578335260638, 0.10420814412588059, 0.0867210685321189, 0.0880846381993211, 0.10077269105839189, 0.07830684078532081, 0.11322583047002449, 0.10031053487635354, 0.09548000632534111, 0.08295739335098928, 0.1027765095428521, 0.07562388462366086, 0.08318731564822239, 0.08998925134456452, 0.11227434244092038, 0.0844274367853152, 0.08831850308147177, 0.10917756335357795, 0.09884294763886052, 0.08522253349077377, 0.09940397036416689, 0.09011537863787258, 0.12036363234211818, 0.08230636677883602, 0.09443114397439027, 0.07804064987883635, 0.09083367594126371, 0.08435028981000703, 0.08807987920810456, 0.0920598927385618, 0.07770968162666687, 0.07552247977778644, 0.11263165179052372, 0.07756459489367531, 0.0960402832440519, 0.0942223754572371, 0.11580369724967163, 0.08002319293815537, 0.08668627118882896, 0.0890062011203958, 0.09975712313150716, 0.0940727794991163, 0.08406929438162697, 0.08643114961596503, 0.11834969849522493, 0.11414912758461597, 0.11668570979213341, 0.0882518858108295, 0.09124150531180471, 0.09008539969888303, 0.10905194066004607, 0.10050495382148243, 0.08506121635756948, 0.08033997804445821, 0.0879259935958305, 0.10520819416911927, 0.08440209667029251, 0.0805532629897463, 0.11988429052691865, 0.10234225083468755, 0.0992750625243562, 0.09187226918705657, 0.10944106860933689, 0.07701657889480565, 0.07894308660158779, 0.0808844244563463, 0.1191735579746127, 0.10897726990538247, 0.08988844853033495, 0.09236332663015252, 0.0842971371345316, 0.10663824475883597, 0.08261787637620276, 0.07946034114488736, 0.0870167233260839, 0.10662534110960648, 0.08752585706977371, 0.10363996469326044, 0.07925684587221332, 0.08539647031155141, 0.08023070823046631, 0.1356437311947647, 0.10419347107397983, 0.10984757857034978, 0.08542406125519479, 0.08591897094310902, 0.09229280142242025, 0.0964064023564696, 0.07710067717294909, 0.10741884459466787, 0.08536781359745918, 0.1004933307999278]
lvec90 = [0.09642721988155334, 0.10403541227205243, 0.0730133192495076, 0.09145252478484514, 0.08538464089042226, 0.10645872028860473, 0.07598832426694897, 0.06991109749613915, 0.0809250937507537, 0.09962626871849246, 0.0774859475580143, 0.09291977527122923, 0.12193659128651799, 0.08313734871675238, 0.08349192405771613, 0.08233108825516103, 0.08724545180308027, 0.07861120894627445, 0.09882234380662476, 0.07319976682162924, 0.06612385011473994, 0.09180114556146639, 0.1034930884702895, 0.08574279161504825, 0.08997179196047868, 0.07580362503942022, 0.0960375064388277, 0.0782144109123736, 0.07469658701526963, 0.08450800756131763, 0.08162684210491385, 0.09283642613843474, 0.09466209280141015, 0.07051150516229036, 0.07466146217292059, 0.09245888192626373, 0.08650772286603611, 0.07317861463139835, 0.08673948288704378, 0.07843332177090222, 0.10998877413582642, 0.07604552070619229, 0.08664569021110281, 0.10601531128988319, 0.11238235719913221, 0.07548813902813917, 0.08804272409424477, 0.08504537600743395, 0.11128178480225559, 0.07796959313318363, 0.0681705338003573, 0.07369603911074335, 0.10587698706446375, 0.1109514757127799, 0.11223556068322021, 0.08517945682074983, 0.0865974941123515, 0.07819719965926138, 0.10002460175071821, 0.10621134262993664, 0.07528635919493602, 0.08331661757506943, 0.09105838516897896, 0.06866481988328262, 0.08394142524969156, 0.07082295768764296, 0.11569474582189962, 0.10509086052657826, 0.07919763144385919, 0.07714976252864704, 0.08892158234356963, 0.07040217005785754, 0.08717196694431203, 0.07543511483805644, 0.08493036434540689, 0.08890668125478991, 0.08769676241542582, 0.07364444491528684, 0.07942904546957699, 0.08307536983810253, 0.08614151537944313, 0.08155134304624946, 0.08167350968014725, 0.10680910171542128, 0.07913480374635684, 0.07012822699392124, 0.07778821460229014, 0.06971972806210365, 0.07945058979178352, 0.09488802647216683, 0.08394358889555315, 0.10395771769054366, 0.0703614954629504, 0.08327987440648023, 0.08213222251764787, 0.0785126324135433, 0.07756043050559559, 0.07142501334557441, 0.10390080885133889, 0.0814705951512844]
lvec120 = [0.09326514516455957, 0.11729139796395839, 0.06312146197313785, 0.08291708194253167, 0.08881036988449643, 0.07461142748671286, 0.06907526621358095, 0.08857449218721601, 0.06464610946317406, 0.09361255979304942, 0.08143458173948649, 0.09304987304536197, 0.11126974256448698, 0.07311375220065432, 0.08633246218515617, 0.08078307135229243, 0.08000884325611742, 0.06573575876582188, 0.0967110462890727, 0.06752645192483127, 0.061682593190973606, 0.07795380133523934, 0.08068226969750578, 0.06890771994513761, 0.08493247259935836, 0.08128640610566762, 0.07973259998026623, 0.06642605550463118, 0.08079590335268938, 0.07172342278983723, 0.07975693652429418, 0.09604150941179804, 0.070072148542247, 0.08015605869980669, 0.07243994150538886, 0.06441375936386962, 0.07259167110552081, 0.06574406518144081, 0.07862991689056165, 0.08274412646368748, 0.0973568724652092, 0.06598653670774755, 0.07931605438556313, 0.09039866038313019, 0.10813527619973, 0.061530549428849994, 0.09575175214498256, 0.07105241723109902, 0.09152957674966612, 0.0874170224242956, 0.08236575191292138, 0.08304330194665331, 0.09957622664057147, 0.09705973256384544, 0.08683141734514865, 0.07241906107013056, 0.07931192773604237, 0.09478077095855744, 0.08799863477977289, 0.09421569353448485, 0.08096712096995085, 0.06546350420863585, 0.062167275901520415, 0.07004522579413078, 0.07843061715962041, 0.06787180095889336, 0.09101042358785802, 0.07673806160516985, 0.06762351915677993, 0.09348929737377554, 0.10470844368146894, 0.05863126952650698, 0.06561959987448183, 0.073287707950743, 0.10293106203381078, 0.10606658095318984, 0.07184176563636407, 0.07681670982990271, 0.06671801805031552, 0.08827554314813656, 0.07531794357412919, 0.06283790410435862, 0.09091603630183206, 0.09865371701379161, 0.08990505684123234, 0.08507659154918575, 0.10006425781258366, 0.07622774443166253, 0.06946565404574782, 0.0846896194393638, 0.0815911632541146, 0.09244538661698533, 0.05872400220473437, 0.0720257463720226, 0.08694384395185407, 0.07266736831484687, 0.08245955490726943, 0.0798797592810179, 0.09910998340909383, 0.08406730406346817]

qts5 = [np.quantile(lvec1,0.05), np.quantile(lvec3,0.05), np.quantile(lvec6,0.05), np.quantile(lvec9,0.05), 
           np.quantile(lvec15,0.05), np.quantile(lvec30,0.05), np.quantile(lvec60,0.05), np.quantile(lvec90,0.05), 
           np.quantile(lvec120,0.05)]
qts50 = [np.quantile(lvec1,0.5), np.quantile(lvec3,0.5), np.quantile(lvec6,0.5), np.quantile(lvec9,0.5), 
           np.quantile(lvec15,0.5), np.quantile(lvec30,0.5), np.quantile(lvec60,0.5), np.quantile(lvec90,0.5), 
           np.quantile(lvec120,0.5)]
qts95 = [np.quantile(lvec1,0.95), np.quantile(lvec3,0.95), np.quantile(lvec6,0.95), np.quantile(lvec9,0.95), 
           np.quantile(lvec15,0.95), np.quantile(lvec30,0.95), np.quantile(lvec60,0.95), np.quantile(lvec90,0.95), 
           np.quantile(lvec120,0.95)]

fig = plt.figure()
x = [1,3,6,9,15,30,60,90,120]
y = qts50
lowerr = [y[i]-qts5[i] for i in range(len(x))]
upperr = [qts95[i]-y[i] for i in range(len(x))]
err = [lowerr, upperr]
plt.errorbar(x, y, yerr=err, capsize=4, color='orange', ecolor='black', linewidth=3, elinewidth=0.5)
plt.ylim(0,0.2)
plt.xlabel('Batch size', fontsize=12)
plt.ylabel('Bayesian loss', fontsize=12)
plt.suptitle('Bayesian loss vs. batch size: Design 2\n50% quantiles with 5%-95% quantile bars', fontsize=16)
plt.show()
'''

'''
# FOR 6 TESTS WITH ALIGNED PRIOR DRAWS, USING CLASSIFICATION LOSS W/ t=10%
lvec0 = [0.372, 0.38, 0.372, 0.375, 0.334, 0.394, 0.394, 0.397, 0.344, 0.364, 0.372, 0.413, 0.434, 0.358, 0.365, 0.417, 0.411, 0.43, 0.37, 0.42, 0.43, 0.413, 0.372, 0.407, 0.407, 0.361, 0.382, 0.4, 0.403, 0.357, 0.357, 0.361, 0.377, 0.363, 0.379, 0.37, 0.357, 0.437, 0.407, 0.373, 0.356, 0.399, 0.403, 0.414, 0.356, 0.417, 0.357, 0.394, 0.414, 0.406, 0.412, 0.376, 0.351, 0.406, 0.377, 0.396, 0.39, 0.392, 0.404, 0.413, 0.393, 0.409, 0.373, 0.356, 0.389, 0.383, 0.366, 0.362, 0.417, 0.428, 0.374, 0.343, 0.411, 0.361, 0.386, 0.389, 0.333, 0.38, 0.368, 0.365, 0.443, 0.326, 0.399, 0.399, 0.357, 0.394, 0.384, 0.37, 0.419, 0.386, 0.345, 0.384, 0.389, 0.369, 0.4, 0.377, 0.402, 0.419, 0.458, 0.357]
lvec1 = [0.34, 0.373, 0.394, 0.46, 0.348, 0.37, 0.299, 0.366, 0.284, 0.329, 0.362, 0.3, 0.308, 0.321, 0.385, 0.441, 0.404, 0.322, 0.313, 0.309, 0.367, 0.327, 0.329, 0.309, 0.543, 0.372, 0.519, 0.806, 0.335, 0.371, 0.321, 0.37, 0.481, 0.329, 0.3, 0.463, 0.389, 0.483, 0.437, 0.34, 0.441, 0.356, 0.308, 0.396, 0.434, 0.326, 0.384, 0.411, 0.367, 0.393, 0.468, 0.339, 0.31, 0.474, 0.302, 0.317, 0.375, 0.308, 0.351, 0.347, 0.41, 0.411, 0.317, 0.35, 0.323, 0.296, 0.29, 0.335, 0.745, 0.343, 0.323, 0.268, 0.417, 0.355, 0.404, 0.728, 0.382, 0.3, 0.439, 0.403, 0.396, 0.389, 0.321, 0.321, 0.312, 0.331, 0.365, 0.43, 0.432, 0.642, 0.456, 0.299, 0.436, 0.457, 0.295, 0.304, 0.471, 0.389, 0.313, 0.352]
lvec2 = [0.681, 0.293, 0.277, 0.375, 0.284, 0.351, 0.305, 0.293, 0.305, 0.611, 0.301, 0.336, 0.358, 0.318, 0.328, 0.29, 0.348, 0.305, 0.284, 0.289, 0.321, 0.603, 0.312, 0.307, 0.344, 0.353, 0.348, 0.266, 0.573, 0.316, 0.617, 0.679, 0.292, 0.345, 0.293, 0.331, 0.274, 0.376, 0.28, 0.261, 0.635, 0.261, 0.315, 0.681, 0.593, 0.313, 0.335, 0.348, 0.308, 0.344, 0.315, 0.303, 0.317, 0.281, 0.39, 0.259, 0.62, 0.393, 0.3, 0.666, 0.378, 0.363, 0.295, 0.314, 0.29, 0.292, 0.488, 0.652, 0.405, 0.325, 0.27, 0.349, 0.314, 0.25, 0.269, 0.7, 0.352, 0.275, 0.305, 0.653, 0.295, 0.301, 0.378, 0.675, 0.316, 0.271, 0.281, 0.313, 0.327, 0.317, 0.378, 0.355, 0.394, 0.323, 0.293, 0.585, 0.337, 0.3, 0.284, 0.266]
lvec3 = [0.344, 0.393, 0.464, 0.506, 0.318, 0.471, 0.344, 0.442, 0.288, 0.489, 0.308, 0.365, 0.612, 0.338, 0.312, 0.389, 0.336, 0.315, 0.311, 0.381, 0.439, 0.406, 0.405, 0.291, 0.472, 0.386, 0.421, 0.295, 0.411, 0.342, 0.296, 0.486, 0.327, 0.461, 0.322, 0.306, 0.474, 0.406, 0.392, 0.351, 0.522, 0.412, 0.356, 0.32, 0.362, 0.297, 0.355, 0.365, 0.358, 0.381, 0.356, 0.482, 0.487, 0.414, 0.339, 0.486, 0.429, 0.36, 0.316, 0.397, 0.397, 0.372, 0.313, 0.361, 0.365, 0.389, 0.368, 0.431, 0.404, 0.551, 0.318, 0.446, 0.38, 0.585, 0.458, 0.424, 0.35, 0.307, 0.545, 0.446, 0.443, 0.432, 0.385, 0.318, 0.417, 0.365, 0.334, 0.446, 0.312, 0.423, 0.328, 0.352, 0.408, 0.373, 0.496, 0.354, 0.394, 0.332, 0.38, 0.362]
lvec4 = [0.345, 0.417, 0.364, 0.339, 0.365, 0.461, 0.363, 0.355, 0.373, 0.376, 0.361, 0.304, 0.63, 0.388, 0.343, 0.374, 0.389, 0.367, 0.384, 0.353, 0.348, 0.304, 0.346, 0.427, 0.353, 0.395, 0.384, 0.36, 0.319, 0.37, 0.359, 0.581, 0.363, 0.34, 0.372, 0.397, 0.883, 0.371, 0.35, 0.333, 0.33, 0.387, 0.336, 0.374, 0.343, 0.352, 0.367, 0.486, 0.386, 0.342, 0.376, 0.399, 0.392, 0.338, 0.348, 0.328, 0.64, 0.335, 0.387, 0.372, 0.401, 0.478, 0.37, 0.402, 0.321, 0.407, 0.334, 0.377, 0.381, 0.356, 0.345, 0.371, 0.355, 0.333, 0.455, 0.642, 0.41, 0.343, 0.466, 0.319, 0.438, 0.326, 0.338, 0.356, 0.391, 0.349, 0.382, 0.305, 0.621, 0.361, 0.391, 0.405, 0.306, 0.342, 0.386, 0.356, 0.355, 0.496, 0.318, 0.304]
lvec5 = [0.332, 0.306, 0.339, 0.394, 0.336, 0.353, 0.363, 0.341, 0.282, 0.385, 0.291, 0.31, 0.269, 0.298, 0.661, 0.427, 0.303, 0.266, 0.316, 0.377, 0.279, 0.529, 0.428, 0.231, 0.363, 0.555, 0.65, 0.231, 0.345, 0.339, 0.335, 0.297, 0.363, 0.662, 0.54, 0.334, 0.318, 0.286, 0.304, 0.36, 0.301, 0.346, 0.468, 0.526, 0.953, 0.576, 0.613, 0.355, 0.306, 0.292, 0.321, 0.352, 0.308, 0.32, 0.474, 0.41, 0.504, 0.335, 0.308, 0.257, 0.406, 0.258, 0.329, 0.359, 0.418, 0.425, 0.639, 0.304, 0.365, 0.269, 0.332, 0.344, 0.337, 0.355, 0.367, 0.796, 0.324, 0.322, 0.355, 0.344, 0.316, 0.406, 0.423, 0.375, 0.28, 0.318, 0.324, 0.306, 0.261, 0.332, 0.296, 0.324, 0.343, 0.273, 0.258, 0.565, 0.396, 0.374, 0.393, 0.335]
lvec6 = [0.297, 0.475, 0.317, 0.537, 0.266, 0.398, 0.33, 0.318, 0.292, 0.351, 0.327, 0.294, 0.272, 0.317, 0.328, 0.372, 0.463, 0.529, 0.294, 0.303, 0.334, 0.346, 0.784, 0.295, 0.658, 0.325, 0.406, 0.331, 0.311, 0.359, 0.334, 0.538, 0.307, 0.299, 0.259, 0.316, 0.28, 0.318, 0.249, 0.227, 0.543, 0.287, 0.716, 0.309, 0.599, 0.283, 0.517, 0.329, 0.435, 0.583, 0.648, 0.575, 0.567, 0.388, 0.373, 0.337, 0.462, 0.339, 0.35, 0.628, 0.372, 0.436, 0.384, 0.285, 0.318, 0.471, 0.57, 0.31, 0.315, 0.308, 0.409, 0.343, 0.784, 0.351, 0.298, 0.444, 0.319, 0.346, 0.377, 0.638, 0.298, 0.433, 0.474, 0.482, 0.304, 0.296, 0.368, 0.339, 0.282, 0.393, 0.616, 0.263, 0.365, 0.53, 0.38, 0.283, 0.278, 0.34, 0.248, 0.52]

bins = np.linspace(0.1, 0.8, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, Classification',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 30 TESTS WITH ALIGNED PRIOR DRAWS, USING CLASSIFICATION LOSS W/ t=10%
lvec0 = [0.372, 0.38, 0.372, 0.375, 0.334, 0.394, 0.394, 0.397, 0.344, 0.364, 0.372, 0.413, 0.434, 0.358, 0.365, 0.417, 0.411, 0.43, 0.37, 0.42, 0.43, 0.413, 0.372, 0.407, 0.407, 0.361, 0.382, 0.4, 0.403, 0.357, 0.357, 0.361, 0.377, 0.363, 0.379, 0.37, 0.357, 0.437, 0.407, 0.373, 0.356, 0.399, 0.403, 0.414, 0.356, 0.417, 0.357, 0.394, 0.414, 0.406, 0.412, 0.376, 0.351, 0.406, 0.377, 0.396, 0.39, 0.392, 0.404, 0.413, 0.393, 0.409, 0.373, 0.356, 0.389, 0.383, 0.366, 0.362, 0.417, 0.428, 0.374, 0.343, 0.411, 0.361, 0.386, 0.389, 0.333, 0.38, 0.368, 0.365, 0.443, 0.326, 0.399, 0.399, 0.357, 0.394, 0.384, 0.37, 0.419, 0.386, 0.345, 0.384, 0.389, 0.369, 0.4, 0.377, 0.402, 0.419, 0.458, 0.357]
lvec1 = [0.342, 0.289, 0.357, 0.363, 0.324, 0.4, 0.33, 0.387, 0.328, 0.327, 0.308, 0.257, 0.261, 0.355, 0.383, 0.489, 0.28, 0.338, 0.283, 0.368, 0.327, 0.33, 0.316, 0.352, 0.459, 0.272, 0.94, 0.355, 0.497, 0.272, 0.318, 0.256, 0.298, 0.354, 0.285, 0.328, 0.374, 0.296, 0.329, 0.356, 0.985, 0.296, 0.416, 0.435, 0.334, 0.265, 0.325, 0.257, 0.38, 0.412, 0.297, 0.303, 0.344, 0.357, 0.448, 0.402, 0.312, 0.281, 0.372, 0.342, 0.275, 0.365, 0.74, 0.323, 0.478, 0.343, 0.338, 0.282, 0.457, 0.299, 0.357, 0.325, 0.621, 0.308, 0.415, 0.822, 0.391, 0.281, 0.327, 0.484, 0.365, 0.368, 0.323, 0.32, 0.336, 0.318, 0.623, 0.725, 0.346, 0.404, 0.32, 0.376, 0.504, 0.371, 0.316, 0.319, 0.538, 0.719, 0.307, 0.294]
lvec2 = [0.168, 0.606, 0.405, 0.436, 0.578, 0.494, 0.215, 0.236, 0.241, 0.65, 0.187, 0.202, 0.646, 0.175, 0.21, 0.248, 0.202, 0.17, 0.179, 0.237, 0.242, 0.476, 0.174, 0.214, 0.206, 0.211, 0.662, 0.175, 0.189, 0.227, 0.416, 0.35, 0.399, 0.389, 0.194, 0.241, 0.395, 0.225, 0.195, 0.179, 0.769, 0.168, 0.188, 0.458, 0.357, 0.227, 0.173, 0.406, 0.513, 0.618, 0.185, 0.206, 0.426, 0.228, 0.359, 0.366, 0.191, 0.23, 0.358, 0.414, 0.174, 0.197, 0.254, 0.162, 0.335, 0.235, 0.419, 0.567, 0.212, 0.182, 0.191, 0.22, 0.212, 0.199, 0.192, 0.785, 0.229, 0.186, 0.154, 0.269, 0.233, 0.589, 0.18, 0.352, 0.441, 0.169, 0.211, 0.161, 0.21, 0.39, 0.206, 0.175, 0.593, 0.552, 0.354, 0.333, 0.235, 0.223, 0.176, 0.195]
lvec3 = [0.382, 0.304, 0.409, 0.636, 0.483, 0.391, 0.291, 0.325, 0.34, 0.347, 0.35, 0.258, 0.404, 0.405, 0.592, 0.893, 0.278, 0.445, 0.326, 0.443, 0.561, 0.432, 0.307, 0.303, 0.365, 0.389, 0.634, 0.316, 0.387, 0.307, 0.306, 0.416, 0.578, 0.341, 0.301, 0.276, 0.34, 0.486, 0.278, 0.262, 0.386, 0.222, 0.372, 0.449, 0.513, 0.311, 0.362, 0.4, 0.348, 0.276, 0.271, 0.311, 0.397, 0.333, 0.281, 0.284, 0.348, 0.418, 0.297, 0.345, 0.264, 0.327, 0.447, 0.39, 0.395, 0.318, 0.365, 0.396, 0.358, 0.298, 0.347, 0.352, 0.326, 0.306, 0.437, 0.6, 0.455, 0.304, 0.367, 0.321, 0.344, 0.515, 0.408, 0.256, 0.608, 0.286, 0.405, 0.355, 0.355, 0.322, 0.407, 0.33, 0.611, 0.472, 0.361, 0.436, 0.475, 0.396, 0.419, 0.332]
lvec4 = [0.271, 0.287, 0.366, 0.34, 0.341, 0.338, 0.322, 0.312, 0.374, 0.336, 0.307, 0.378, 0.347, 0.305, 0.338, 0.363, 0.69, 0.297, 0.388, 0.387, 0.326, 0.343, 0.441, 0.438, 0.342, 0.341, 0.332, 0.361, 0.322, 0.326, 0.457, 0.34, 0.357, 0.342, 0.461, 0.352, 0.412, 0.322, 0.353, 0.296, 0.316, 0.38, 0.753, 0.354, 0.308, 0.277, 0.561, 0.851, 0.309, 0.334, 0.402, 0.472, 0.354, 0.321, 0.796, 0.296, 0.348, 0.352, 0.322, 0.413, 0.842, 0.297, 0.379, 0.344, 0.353, 0.31, 0.322, 0.456, 0.328, 0.378, 0.328, 0.342, 0.422, 0.314, 0.423, 0.364, 0.304, 0.46, 0.401, 0.313, 0.319, 0.358, 0.614, 0.349, 0.367, 0.29, 0.315, 0.355, 0.368, 0.359, 0.384, 0.352, 0.387, 0.329, 0.298, 0.348, 0.354, 0.35, 0.372, 0.33]
lvec5 = [0.415, 0.19, 0.57, 0.475, 0.307, 0.362, 0.155, 0.256, 0.215, 0.196, 0.363, 0.223, 0.308, 0.545, 0.228, 0.255, 0.349, 0.142, 0.207, 0.319, 0.159, 0.301, 0.357, 0.134, 0.226, 0.387, 0.156, 0.182, 0.208, 0.305, 0.32, 0.477, 0.179, 0.18, 0.177, 0.325, 0.489, 0.279, 0.356, 0.29, 0.216, 0.284, 0.294, 0.236, 0.653, 0.147, 0.47, 0.331, 0.169, 0.588, 0.157, 0.63, 0.555, 0.424, 0.347, 0.422, 0.537, 0.145, 0.163, 0.547, 0.18, 0.196, 0.402, 0.178, 0.205, 0.354, 0.432, 0.294, 0.188, 0.189, 0.56, 0.49, 0.653, 0.223, 0.89, 0.339, 0.278, 0.446, 0.234, 0.841, 0.215, 0.425, 0.249, 0.158, 0.323, 0.154, 0.158, 0.256, 0.292, 0.677, 0.126, 0.182, 0.173, 0.22, 0.33, 0.22, 0.698, 0.325, 0.463, 0.165]
lvec6 = [0.179, 0.175, 0.376, 0.4, 0.662, 0.809, 0.509, 0.197, 0.181, 0.49, 0.204, 0.186, 0.395, 0.182, 0.493, 0.188, 0.433, 0.16, 0.673, 0.181, 0.433, 0.2, 0.664, 0.165, 0.252, 0.444, 0.698, 0.185, 0.414, 0.333, 0.358, 0.203, 0.406, 0.275, 0.171, 0.202, 0.623, 0.198, 0.217, 0.185, 0.787, 0.206, 0.173, 0.484, 0.198, 0.156, 0.399, 0.205, 0.612, 0.206, 0.216, 0.158, 0.549, 0.698, 0.495, 0.369, 0.34, 0.227, 0.409, 0.211, 0.188, 0.203, 0.281, 0.16, 0.197, 0.173, 0.412, 0.354, 0.371, 0.413, 0.463, 0.216, 0.226, 0.195, 0.19, 0.339, 0.322, 0.226, 0.178, 0.459, 0.208, 0.395, 0.186, 0.614, 0.16, 0.154, 0.261, 0.57, 0.322, 0.213, 0.362, 0.225, 0.679, 0.273, 0.478, 0.207, 0.566, 0.24, 0.585, 0.481]

bins = np.linspace(0.1, 0.8, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 30 tests, Omega=100, Classification',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 6 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=20%, overEstWt=1.
lvec0 = [0.01728729014931321, 0.018471918342130782, 0.015683815599280424, 0.015655644941699742, 0.01815963047507897, 0.016801844559582856, 0.015629703051773167, 0.018667554884051873, 0.01694482368386538, 0.014746901954150772, 0.014511976508500144, 0.014327385602907217, 0.015125668584179587, 0.015636987332666597, 0.01729784455744154, 0.014158589944664316, 0.015345482843518337, 0.017517073677329714, 0.015236045719924433, 0.01574874721197197, 0.014811074533242265, 0.016513239471657427, 0.01756957743712494, 0.016526385939271814, 0.014498931361412379, 0.014686115574308909, 0.01814130256363459, 0.013196227539490535, 0.01614853257782514, 0.01464580171145139, 0.016588128618273617, 0.014708487192838866, 0.015229236043196096, 0.015655408973299, 0.01423463657893135, 0.016900325200930457, 0.01526207375456269, 0.017025407848797334, 0.015949368022818693, 0.01672967442520684, 0.015566220069113713, 0.014877788396696788, 0.016532683527538256, 0.01489299676941007, 0.018434805569295786, 0.015626388941818416, 0.018462144367519907, 0.016088292887917178, 0.01598556700861214, 0.01813060697236665, 0.01748285230383631, 0.015952081074120245, 0.015934857447889937, 0.01631107875631688, 0.014395901572940437, 0.016774226164355033, 0.015774822741543643, 0.014651481249148833, 0.015169218184766922, 0.015561234349167211, 0.014852819791934993, 0.015986662328284423, 0.013707709221989365, 0.01432375288443756, 0.017330994747413498, 0.017588973428084402, 0.015934202622139536, 0.017325621081784794, 0.01727693418743328, 0.01958756003914346, 0.0155956147322963, 0.014714654850202928, 0.01515572234174987, 0.015026373261513477, 0.013666265862091635, 0.01641067308567396, 0.01764512718171291, 0.016824135324949682, 0.01604824804692429, 0.014521177936402773, 0.015465804772273165, 0.013949171357429966, 0.016500671732389262, 0.014426041088188981, 0.016149849135599137, 0.016658025535992094, 0.01591683065513411, 0.01393257519035395, 0.016294422425590684, 0.01632693554201407, 0.014330754019540577, 0.014089032583448605, 0.015464704287658384, 0.01474551726808667, 0.016421839985492837, 0.015885368682801344, 0.017222461901998685, 0.01686571720413538, 0.016491702089873047, 0.016079065150581707]
lvec1 = [0.013034480236624683, 0.010953998166691183, 0.011123884891243047, 0.011757754102354454, 0.013139327946536428, 0.010483725254045107, 0.011634906806121285, 0.016776202783798898, 0.01156027966108425, 0.011022063866750515, 0.010144939823046508, 0.01151509882846369, 0.01304972934155684, 0.014352570489641453, 0.011622109175230764, 0.01294899310804929, 0.012884173702605643, 0.012231918957611226, 0.010997726147219045, 0.011079600864542634, 0.019975273042624222, 0.013226173371428146, 0.010664235723483803, 0.011223729789472033, 0.021707843359204726, 0.011716492652959133, 0.016640160180345455, 0.015045967662713225, 0.013026788170032182, 0.01088422986868269, 0.011679938600325894, 0.014684112728179984, 0.010820985671387305, 0.013545626758142106, 0.012858817382362761, 0.013472542733002397, 0.012219639722780213, 0.015850191555103504, 0.012103508580257386, 0.016888081192376853, 0.016758964210055835, 0.014648062938180507, 0.012554820583218189, 0.01298781236171401, 0.011867182451878401, 0.012044830249327818, 0.01301261518538804, 0.010992314213950305, 0.013293625069894312, 0.01397526536233909, 0.011347434324800098, 0.014343810441584337, 0.01544149836150512, 0.013521034366019253, 0.012277037791411056, 0.010400847170174893, 0.011594689199191705, 0.012183401675848013, 0.014452598630496033, 0.011806405981041239, 0.011564060950833488, 0.012567299081328502, 0.015785217485214227, 0.011558058708616805, 0.011729794875411672, 0.010901772374518705, 0.011602656720312595, 0.011372465336086116, 0.011813882831929736, 0.011542960002805474, 0.01054755980242685, 0.01542619033352268, 0.015964970162901524, 0.010751540862297843, 0.012333455388719505, 0.020750728609546056, 0.01479535434301874, 0.012383355360284252, 0.013836372121271633, 0.019031121624159868, 0.014748947617062438, 0.01148771659895242, 0.012332158693198736, 0.012732664444232697, 0.015138186869928119, 0.013707947046563713, 0.0126898049816628, 0.015805296870503513, 0.012177615944060026, 0.011695336575255138, 0.011088022384428952, 0.01652937186835279, 0.020051469262727408, 0.0154430934816399, 0.010829790621178784, 0.016822249529247185, 0.012714180221634822, 0.016585392444701717, 0.011630284315492774, 0.010556027456683612]
lvec2 = [0.01842663237826679, 0.011746266545902186, 0.010802451863965017, 0.012762511299364997, 0.011550506124007678, 0.014009031477793213, 0.011808604051031681, 0.011239345610471569, 0.011776739716958758, 0.017738498152465084, 0.011607247502396072, 0.01318498995858116, 0.012499376759001722, 0.012054109481393821, 0.014051518992704272, 0.011725978218873043, 0.012912681939906351, 0.01178206874457996, 0.012680431935162812, 0.012015652590246286, 0.014297461663807791, 0.020775154554184144, 0.01268843689826071, 0.012475363040803484, 0.012505480727698965, 0.013199879386752416, 0.012403939266593271, 0.011789737300041311, 0.014860754877382814, 0.013569906296234025, 0.017959959966860745, 0.020188568653366216, 0.01218558605225435, 0.013222299289584202, 0.011461682635521492, 0.01442752079960425, 0.01093473273448946, 0.015451667154500338, 0.011737329430542948, 0.01173113293332023, 0.020541429168093903, 0.011548481132740502, 0.011871949196154922, 0.021348051631750707, 0.022374234598915885, 0.013052578522616409, 0.012758453617428788, 0.012900706553134723, 0.011992458337750637, 0.014162585264797113, 0.012414650464678652, 0.012694174070907201, 0.012782567642446379, 0.011399955901956147, 0.01356651634059893, 0.010966367199669052, 0.02226788907542851, 0.014119803392899217, 0.011781219964836585, 0.02076610827166373, 0.021408901567924785, 0.013939128361637411, 0.011831971713537911, 0.01227280417232738, 0.012092897263895267, 0.012949363200981995, 0.023269658004295143, 0.022933858178506922, 0.014516920892992481, 0.013041435496434725, 0.011249533220172515, 0.013401055078899852, 0.011656853808060636, 0.01105147611355686, 0.01225599462290827, 0.018362880504295846, 0.012861928906346047, 0.01206641561463537, 0.01151148130882256, 0.02239212347048722, 0.011331814579607037, 0.012185914866858303, 0.013586644835574578, 0.018402541406202504, 0.011968951140327361, 0.011010060016781256, 0.011503684878074271, 0.013548558671163264, 0.013561370071929995, 0.01222224682244928, 0.014373057889708215, 0.013688563707902123, 0.01471779245111908, 0.013071773223054028, 0.010957099193783569, 0.01960764019457382, 0.011714599552540493, 0.011579869305124972, 0.011099316655742764, 0.010769481129360046]
lvec3 = [0.011840072466162088, 0.014816512031806083, 0.016978498620477227, 0.01544792281737961, 0.01217257117362004, 0.017961607453183183, 0.013445596327839164, 0.01493035866083257, 0.010569165229396407, 0.019331688007710963, 0.011157075908981556, 0.013618674675530271, 0.02180367057078664, 0.012790638075683942, 0.011580054150365393, 0.013054830542030013, 0.011978829149625954, 0.012520315952172663, 0.010780769834936973, 0.013758894845697669, 0.014221104685455656, 0.013390819519575764, 0.013186966621788823, 0.011271368936001051, 0.017159737225563403, 0.015722167995238144, 0.014851788417750086, 0.011839415889042838, 0.014508348627829503, 0.01142254803025384, 0.01221164336406308, 0.01561850698782542, 0.013055864493469245, 0.016463848275918045, 0.011292327605230041, 0.012744857069828459, 0.01728621009283507, 0.01471936846988834, 0.012693723464765418, 0.01244805481082687, 0.016252276330026096, 0.015350246997081924, 0.012603469738636857, 0.011548157546493708, 0.012738334870607517, 0.010903363470515041, 0.012148842260262773, 0.012301280926294615, 0.012683165072514975, 0.013676666885230976, 0.014227495199742634, 0.015530190520629497, 0.018265184162592995, 0.01596098067764406, 0.011946673075555735, 0.019138712930228233, 0.015521605526039874, 0.012603624712193699, 0.010913594565398003, 0.015655945929950097, 0.015512295776918015, 0.013494350357897039, 0.011550824890390311, 0.013399863997497633, 0.012363250119647052, 0.014477520008769068, 0.01137110144800542, 0.01483238103560378, 0.015279016487991924, 0.022484134870721425, 0.011415147882155167, 0.013323903494037795, 0.012511166297490724, 0.021384590943424125, 0.01650080315499638, 0.014434119192735918, 0.013511057378887838, 0.011906198068044011, 0.019139479702679298, 0.014427749774672935, 0.016100166292107806, 0.013482292670601716, 0.013977388571280119, 0.011072250815006424, 0.014425265555371316, 0.013156726258062523, 0.012269608340838565, 0.017295829441875653, 0.012389809570972696, 0.015009691992227656, 0.011967326725698347, 0.013500483530878928, 0.014421005853054674, 0.013825463360917053, 0.016745175259829118, 0.013614736140540658, 0.015632102978024982, 0.012278505839326806, 0.013456740696280382, 0.012328654445365034]
lvec4 = [0.014653666885825868, 0.017723782484209433, 0.014563567787515061, 0.014177141348867443, 0.014451733523992365, 0.01674841408371463, 0.016589013611760833, 0.013498326940678375, 0.018242855556574917, 0.01541009041242396, 0.015186265709122236, 0.01468907440403314, 0.019179243668891482, 0.01591786336182918, 0.013122840930205248, 0.013834482397736828, 0.017797019997617885, 0.015720437761413082, 0.015373177432953659, 0.01513854448401331, 0.015241618962605208, 0.012376592412731677, 0.01616025966655757, 0.016052455392367923, 0.014130430142557979, 0.015239639646248207, 0.01717589088298545, 0.015748358753269933, 0.01513535780658735, 0.014864078848694772, 0.013725826565854348, 0.01843042438846535, 0.015259065968100618, 0.014868205793189069, 0.016191678547699002, 0.01644313676398759, 0.02303802056462083, 0.017546288327829604, 0.014315711980450884, 0.014012759885095984, 0.015442345249930288, 0.016594861295207673, 0.015110411242629632, 0.015571846390458933, 0.014955973522600311, 0.014948367917418756, 0.015201984627985141, 0.017317906556095098, 0.01721664948987128, 0.014236285710067824, 0.016312161915105174, 0.015863171729884894, 0.015815673353019193, 0.014777586840800805, 0.014404708466823714, 0.014775676755352648, 0.018777937514335916, 0.01444944141095575, 0.015394873799298542, 0.01636791849586822, 0.017286353335451712, 0.016977926653255548, 0.015724601565290118, 0.015834363849894194, 0.01615361087982374, 0.015923684738554315, 0.01444924581747224, 0.015556575163000654, 0.015172150759645134, 0.015832178794099736, 0.014418534124851584, 0.015748993031535957, 0.015243041273502903, 0.015022454964309753, 0.015674379966891486, 0.017353551727413673, 0.017971597367822948, 0.015544820703962774, 0.017613392695351136, 0.01278065989175209, 0.015672917755442353, 0.014183957360100726, 0.015418072856654112, 0.01499952017726786, 0.016958109981539186, 0.014908774182529382, 0.01698105188156532, 0.014700281277020097, 0.017493683252976365, 0.015189088890335847, 0.014522995639046616, 0.01690875023386191, 0.01360518990041971, 0.014602973155272349, 0.015917365551647408, 0.01593269126851686, 0.014673705462087246, 0.01954167692888731, 0.013674111777081673, 0.014555280288967147]
lvec5 = [0.011380331105046741, 0.013018077835728331, 0.012794821034931233, 0.01620764018153669, 0.013241139963084642, 0.013967675986167457, 0.014087590098720177, 0.014157143219883678, 0.012221127897060105, 0.014790145526645357, 0.011531140300951537, 0.012552452361360808, 0.011706157021424532, 0.012021920616742435, 0.024684811597508072, 0.015621668715520315, 0.01209554587033104, 0.011423410804992717, 0.013121563490638706, 0.015191882634118333, 0.011635512592825045, 0.014830363311387656, 0.013971088894521762, 0.010991727260015717, 0.012848465710703742, 0.019313918397348095, 0.01556497434814627, 0.011137269095541233, 0.013363998967839252, 0.012718264457420636, 0.015439536622513534, 0.01144041202083957, 0.014764354418311757, 0.018724173246204637, 0.01684062757002458, 0.01354245938794612, 0.01224086624022257, 0.011887034791871389, 0.013159420459701537, 0.014362585591362642, 0.012660121422882323, 0.01326981884576271, 0.013951088268230999, 0.023711845380078648, 0.030422175261672093, 0.0156433380330372, 0.01813273766452835, 0.014046035543083313, 0.011727137476210577, 0.011167026628819451, 0.012155620018249883, 0.012980116206303701, 0.012148870012760377, 0.012913680993246619, 0.014253902761609533, 0.01552323947436067, 0.013698701696581689, 0.012399461805375817, 0.011940845653321422, 0.011116486208144295, 0.013628067666562925, 0.011790514907544845, 0.013984035061295608, 0.015377916336013328, 0.015990291441581792, 0.016601217606062, 0.017424657903304865, 0.012556722212749892, 0.013727038133647269, 0.011119137122903296, 0.015158759196205686, 0.01404533571540001, 0.012434576334314263, 0.01334413946999605, 0.015426599995726526, 0.02345599321868283, 0.01144960145611521, 0.013497839367950466, 0.01277061233360752, 0.013658206123188863, 0.012711614297362797, 0.015825371003821434, 0.012668462832031985, 0.0144246739666844, 0.011385788493908273, 0.01258747471321936, 0.013379083879962334, 0.012210982167600283, 0.010667396522802288, 0.012908199568333016, 0.011807280297636266, 0.01412386275112247, 0.01341817450270147, 0.01147813981815324, 0.010792005907863922, 0.01984912347870992, 0.0156663508385845, 0.015660601349452626, 0.015291658068382454, 0.013049595455748592]
lvec6 = [0.012427907483870064, 0.015627856915497625, 0.011726751528111085, 0.018776494657626677, 0.010726039786221537, 0.01494756545198907, 0.011667739491830425, 0.01225025611066988, 0.011958468749490402, 0.013254086327401205, 0.01167102392429653, 0.012127620981749562, 0.010864955321642231, 0.012993987729093357, 0.011699548613261217, 0.01427319563105918, 0.015862487216497204, 0.014416920776469912, 0.010803871734900663, 0.012496518624241152, 0.013423671993034316, 0.012701237259252582, 0.024927126111048352, 0.011591051195413688, 0.021056979874069074, 0.01193425425625555, 0.015504437553152091, 0.012494686299226326, 0.011938174818505589, 0.013398174141948393, 0.012933829319294527, 0.014542476075554644, 0.012083266392658462, 0.011063310659992722, 0.01090439990704538, 0.011421249616821947, 0.01096251640933731, 0.011894882686971918, 0.009768087135547039, 0.011015260700964128, 0.018418689798966627, 0.010704159077263808, 0.02010257214229351, 0.012605358295959216, 0.020374409535590523, 0.011339134501660488, 0.014580035681454287, 0.011610504727863303, 0.016821110770761115, 0.01900791361201496, 0.01904963917637377, 0.016679835917927904, 0.0204036231471656, 0.013700119064206309, 0.013274539432319116, 0.012438324446595402, 0.0175264220912001, 0.012768432103812549, 0.013186070728792127, 0.01642513164053339, 0.014419392385988284, 0.014490070834783556, 0.015143448325255042, 0.011226887423304507, 0.01367822678824436, 0.013973109309659093, 0.018558770208775388, 0.01256062255004907, 0.012918504076128877, 0.012411084222627024, 0.015549904868063054, 0.013339863447517813, 0.02340171605388548, 0.012278275531137084, 0.011295572144824895, 0.016280558103398138, 0.011092671990496553, 0.011757949612825681, 0.01459221042311207, 0.018232669404723026, 0.012329497884488115, 0.0162582132383625, 0.01787119645448067, 0.016009342106249397, 0.011387651968382163, 0.010644322991564816, 0.01362441294323945, 0.013051652253270993, 0.01126686248992041, 0.012977071540151429, 0.018411334394022937, 0.0107528497829377, 0.012637554448119459, 0.015044764025355416, 0.013024743068976255, 0.011006594078399509, 0.011554468219525375, 0.013931832896941066, 0.010495446101322263, 0.01419518996811685]

bins = np.linspace(0.001, 0.03, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, PMS(1.,0.2)',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 6 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=20%, overEstWt=2.
lvec0 = [0.05340890492585494, 0.05820017119639504, 0.055159621028566225, 0.057705218754149135, 0.05008418734353597, 0.05068222583887698, 0.057256353483709194, 0.04838922623195669, 0.05505163393021836, 0.04829490878044514, 0.04856237371039545, 0.04964113804040521, 0.04821105712194246, 0.047369563952574585, 0.05033829135671399, 0.04837618067469676, 0.05395620043017826, 0.0518434439862483, 0.04680935095027758, 0.04973823308765938, 0.042744926637013556, 0.047825986245281796, 0.04457737798883909, 0.05837179903976296, 0.05299601352220734, 0.047155128271289225, 0.048430817248152846, 0.04951043748671617, 0.05234970762388437, 0.04797153964804197, 0.0511053293087705, 0.05162329325350428, 0.056260694752954504, 0.05147112632544638, 0.04874362138960874, 0.04798347863133063, 0.05108102226137571, 0.06119594659728703, 0.05746380616998718, 0.04734862832927931, 0.05401004213011451, 0.04834687639581981, 0.04152618042916643, 0.04864473653732238, 0.042832424883722305, 0.04733849160331509, 0.05087200969562211, 0.04789446748363723, 0.047818418549174777, 0.04985226336769546, 0.056070022179740484, 0.05520464712180312, 0.04826654900750391, 0.0466577144913161, 0.05034870650359856, 0.05148843739044203, 0.04856768137903386, 0.05468481697643511, 0.047834368298967665, 0.04998374266698511, 0.053775292611699915, 0.044461189309672564, 0.05508323711599948, 0.05042060321776053, 0.05378292732268146, 0.05010994539330754, 0.054864269768104504, 0.048141195855994856, 0.0505201182421093, 0.0565111008072209, 0.050674275121562244, 0.0481058889203885, 0.04772936082272347, 0.04810618988776218, 0.04926513014834792, 0.050936820825523275, 0.05328159174537579, 0.05370889365640707, 0.04832891056845242, 0.051301142318596754, 0.046423711369078, 0.044768906827016404, 0.05041247529558998, 0.04674170581523738, 0.04722664864183755, 0.04589364535246836, 0.04412781155810311, 0.0592162443718002, 0.04607663271768663, 0.05133990997345871, 0.04644193000252004, 0.048587047189224464, 0.04714104542673156, 0.04924516293205036, 0.050729552613539446, 0.04787657656906362, 0.04737779650534382, 0.05545101147544792, 0.04722627325878679, 0.04720880100712451]
lvec1 = [0.03494769683349942, 0.03745438203815055, 0.040710738497247496, 0.053314131953118425, 0.05894483059631831, 0.03501585338462428, 0.03933147773196014, 0.041523089002673, 0.041249820712234035, 0.032744563382978174, 0.04200106965877783, 0.036314735149929944, 0.038959559994164984, 0.0496799310113728, 0.04891170129851833, 0.05254226175165654, 0.05330271689280021, 0.03876560306859897, 0.037726768794083945, 0.05467699702569495, 0.06049557510832722, 0.03243228269112335, 0.04098449036959284, 0.033061818052368845, 0.07903755753157576, 0.03627893549344813, 0.04079101008093126, 0.05188239822153069, 0.0345613585744, 0.038666759608234395, 0.05563143091822059, 0.05390118757446328, 0.045426953532569404, 0.04761204313557038, 0.03305353239122871, 0.03533494257158972, 0.04494540093684156, 0.04310423751424735, 0.03724774634905296, 0.04375447812632395, 0.07391004569395966, 0.03748579140136254, 0.04832542713849167, 0.04032596372645441, 0.05057526916798324, 0.039450572794416605, 0.05098523196613792, 0.0400083412761557, 0.040255158478315144, 0.05900679079778623, 0.03431369935248452, 0.03914259320501822, 0.04741559921482621, 0.030885027190201374, 0.03377257345947926, 0.04556288968634495, 0.04981670784695863, 0.04708535067348992, 0.04375505975841678, 0.037868380636981384, 0.034158151908512624, 0.04313817231485883, 0.033016311287658466, 0.04833618486628397, 0.05035647847756361, 0.03683751928458122, 0.03680811747698635, 0.05679940528353108, 0.05180498091057472, 0.03553712533342519, 0.039983384377681556, 0.04160961150588258, 0.042038226184856683, 0.037243743320742026, 0.05208006300687969, 0.05846683233293117, 0.03521447043384348, 0.03230020641166026, 0.03838261488934957, 0.041904735426430535, 0.04708996198151014, 0.043444599042363495, 0.04385262572955327, 0.04011888165013633, 0.05332017689218975, 0.03723097832401891, 0.040254762520207765, 0.05011585996082748, 0.032730117846033524, 0.037874881434982674, 0.035091550728689136, 0.04911962509337156, 0.05344330012882448, 0.08261448596254796, 0.04485246220034679, 0.043737098007715795, 0.07112545792702955, 0.04563145452257108, 0.07080281328555078, 0.03769764697548434]
lvec2 = [0.03395928008462964, 0.037375915772218694, 0.04588491750491526, 0.03546586272381919, 0.041566274920528785, 0.03802182939769537, 0.04000182727970592, 0.04520824832089842, 0.03234594156436888, 0.032531027432591494, 0.030575651223613005, 0.034634784928100966, 0.03687567475976428, 0.037486744428566254, 0.0684238549077612, 0.03926418439637033, 0.05984920465686762, 0.03519846002477123, 0.03865528624833866, 0.04099451487956695, 0.046863205554288245, 0.036793992913347076, 0.03855917321027414, 0.03166909219971128, 0.06409518400660905, 0.04062648189578011, 0.04127081609066754, 0.037333529676928906, 0.04082612160275242, 0.038618445280672126, 0.034019422121170734, 0.046144201479188844, 0.06882766959258335, 0.04465878231393889, 0.03955048779351943, 0.03483669205853499, 0.0370399897991862, 0.04058027149615809, 0.03649813853090995, 0.04282323859338426, 0.04362711744004486, 0.04286250774598303, 0.038317636512369774, 0.06952001746439218, 0.06943804032662344, 0.0399128417105514, 0.06513966976031058, 0.06529873281619684, 0.044755404391990224, 0.037211272529323776, 0.03266725292521658, 0.03266898887772676, 0.044133869501389, 0.03984988259241432, 0.07536129161515641, 0.04892009889749406, 0.041731151615749126, 0.04046044566933281, 0.0687047724138105, 0.03643551865325991, 0.0369570845829331, 0.0355372302015021, 0.03856337722792037, 0.06324310386791474, 0.04500862303539867, 0.0327161457240251, 0.04323368253313723, 0.03647246476346305, 0.04597836337488415, 0.03842239108213041, 0.042125059117941115, 0.04068931096257856, 0.03981236592162457, 0.039530481076291236, 0.03551829679951213, 0.06888619745825925, 0.03481008181536198, 0.04020523227318419, 0.04159514307659981, 0.03479107563861297, 0.04424722388241151, 0.036569360694581714, 0.03565028720889981, 0.04261506509736115, 0.04134316680284589, 0.04353695457424124, 0.035676928998181826, 0.03879275074965914, 0.04037868993756251, 0.03196774402192244, 0.056742058274222205, 0.06359786809285801, 0.048862235273666337, 0.03819251349180327, 0.03719420463804332, 0.0357853561725558, 0.04131028116265232, 0.06881619860233266, 0.06194601011781141, 0.039078549347914084]
lvec3 = [0.0398274030259982, 0.03651567994106405, 0.036737634889325306, 0.046148048140754724, 0.051107633087718866, 0.05729534970309558, 0.04391799226358912, 0.041744436274928874, 0.06488715478480331, 0.046266441058573145, 0.03437402707908194, 0.04411917678854586, 0.04684034035196654, 0.03452181655195653, 0.043942657424234775, 0.03667425803580897, 0.04665213962754894, 0.04255716375440338, 0.03593548345705218, 0.04194803916344403, 0.04070750684015816, 0.03564101837574478, 0.03611222207313737, 0.03288323830244062, 0.03484458400809616, 0.04046207604938026, 0.03934616666165705, 0.06261783332818853, 0.04088048438934017, 0.04261279720145329, 0.049775508105818364, 0.03440986774419665, 0.04325973522956164, 0.04527333118266067, 0.040805642312755144, 0.05104271395889017, 0.03655217422159469, 0.05781809438274064, 0.04708664543874973, 0.038350583684325, 0.05256959295717973, 0.035570702362710815, 0.05606963770161768, 0.04427097753428657, 0.04368835364850891, 0.043388898770255105, 0.03881298523603689, 0.03907310869926654, 0.031554642039875166, 0.0638455724881529, 0.038436553378067256, 0.044907349941184574, 0.035184023335806995, 0.05083337992451656, 0.04239331649912493, 0.04007057327796457, 0.04219202092707529, 0.03912461454754136, 0.036298990004237516, 0.05588227769915165, 0.04491619267691245, 0.065179124014771, 0.052016099805644034, 0.04867069630399252, 0.04492131877279973, 0.04694937091236743, 0.03988661738190981, 0.046740236898508085, 0.04605714794972209, 0.036547810437320895, 0.044309616428521194, 0.05262688216872877, 0.05391627854870361, 0.03778231482816336, 0.04242533999232818, 0.05566191327776755, 0.042445663853622397, 0.04671154508350938, 0.04801688985985094, 0.0649643035288746, 0.043162876887347816, 0.039109208921127944, 0.038860208378998395, 0.037722264603691345, 0.04186173847177135, 0.0382009097050975, 0.04969935946165572, 0.03841708185642139, 0.04590453205341582, 0.0445615603947439, 0.03770496184992898, 0.03458852355940126, 0.059080365887912836, 0.03660924778889276, 0.04693923152164218, 0.0346291802081886, 0.04850403680085445, 0.03874326981874562, 0.04501913076377568, 0.047815557682627324]
lvec4 = [0.05026580138948399, 0.0485154213571466, 0.043991411368278326, 0.05956474120972691, 0.04859224016216311, 0.053875217052579444, 0.044617551146006046, 0.04746149445301199, 0.04808111281822892, 0.0435000766434218, 0.04648897037340307, 0.04703556406458549, 0.0660361377339512, 0.04427158821795016, 0.04629515508903221, 0.04160454146093861, 0.05045513074264752, 0.048533643871781385, 0.047207208718925385, 0.05077403175342812, 0.05248863422243117, 0.05472303894387443, 0.04946426158981122, 0.04959449765852329, 0.04506573540391792, 0.04480320774633114, 0.04859700142799836, 0.054401107416670154, 0.04638686332803192, 0.04523522090698108, 0.04686906730994533, 0.060282531616497215, 0.0453925644115271, 0.05312053338677412, 0.062057117716469865, 0.048229940512627016, 0.053290722152527205, 0.043025186537196225, 0.05068643125358991, 0.04973627715158236, 0.05413502559816161, 0.0496465740936197, 0.05639447736302812, 0.047599284952506135, 0.04350869046189704, 0.046588745895967794, 0.04486339141539145, 0.05278541785170391, 0.05998687821596576, 0.0431390887513294, 0.05265617551714308, 0.058901192604827964, 0.04018401234682565, 0.049317351063510595, 0.06143593006921431, 0.044490279296841864, 0.045458981752639994, 0.04849749581244092, 0.044836320963383754, 0.045643344089685164, 0.057032407608137235, 0.0503317775692559, 0.05022696024272455, 0.05618444738303047, 0.043471464827225165, 0.04865481327936503, 0.05026575842296338, 0.048986026491297005, 0.044904852471177883, 0.04903942304902857, 0.048956161198160354, 0.04715415595173396, 0.04821386249039574, 0.04442686043937709, 0.043661937768971926, 0.05273163797808048, 0.051462198974356596, 0.041923331808042946, 0.04739265132339634, 0.04789040870772539, 0.044642010405985595, 0.04052433494159179, 0.049497758247332324, 0.048653031897057525, 0.049884626276357216, 0.04614606872004078, 0.054906153789833025, 0.05586232628015512, 0.04839508400652035, 0.04844064596466927, 0.052178542786719746, 0.049230387529856263, 0.051303406837490684, 0.05029774704666407, 0.04438861695042488, 0.0435151151373389, 0.04541041234842678, 0.05116193168404803, 0.04486492909426088, 0.04877343462145681]
lvec5 = [0.05361740635126253, 0.03522507437086625, 0.03869230298287396, 0.05020746540869431, 0.036190582733741386, 0.08672060281959451, 0.03959914401936986, 0.060351426759659536, 0.03960966355376376, 0.06376223392833819, 0.03767114815512938, 0.08947749516571511, 0.03615055696367145, 0.035051911097391864, 0.04535947917137964, 0.07170036477123379, 0.03733782000234458, 0.039960493085615945, 0.03776486025099615, 0.03684020825655132, 0.03457115359589625, 0.045179214042246986, 0.05248454818759891, 0.03626745730183964, 0.03650250355483327, 0.04024073036301285, 0.04777502984671591, 0.05722975474941356, 0.04056970859628775, 0.03981920483359978, 0.06101557381468298, 0.04419757569737313, 0.04082590558035236, 0.03622195638023414, 0.038794985381695624, 0.03309118040382049, 0.03651466280658323, 0.04211334069088557, 0.04031010281523161, 0.03793510159592768, 0.04673802526942076, 0.037238640341038305, 0.03661224702072944, 0.05178654283466254, 0.04884507430779682, 0.029935851358304212, 0.05752988951423174, 0.04904536654533896, 0.0734926241143845, 0.048795933906090175, 0.04163341081112232, 0.03890511651809334, 0.042686875272816414, 0.04623214217862153, 0.06660810953415545, 0.052406790023900834, 0.046654120955112156, 0.047114945230559487, 0.04162073323404789, 0.06356896820355326, 0.04150382057481144, 0.04343806426565282, 0.045472196384339025, 0.04495923940803673, 0.0540192496478883, 0.03509188838148686, 0.035269754243040116, 0.03456909743424706, 0.04081091608261342, 0.04409009722592921, 0.046397874623378875, 0.04444500499448258, 0.061972074042336775, 0.05570589688739792, 0.04488655806810836, 0.07830109934297642, 0.03359548210951414, 0.056574953512972787, 0.03757122453476126, 0.03587855839980185, 0.05690714720301266, 0.03499825641234976, 0.04669183229407319, 0.03867149356091891, 0.04294825284208301, 0.03489419127377095, 0.031582269969316366, 0.042624982516411516, 0.06300214605586679, 0.08242550754213963, 0.03655662181230273, 0.033290955414321165, 0.07431852545665019, 0.0648720974578948, 0.044456092813642614, 0.04984434418937966, 0.04619224989328076, 0.04525634907061931, 0.040018593171920705, 0.03736945577153175]
lvec6 = [0.038855305852582046, 0.05242844740663353, 0.037635097505142316, 0.06282867132062175, 0.032522843351928614, 0.04955447065606831, 0.0362719739297409, 0.03899744514624648, 0.03769368864812251, 0.04257234008772245, 0.03524331710371971, 0.03824054721495672, 0.0326144416660778, 0.04103239342599198, 0.03645592970582175, 0.04626007268032683, 0.05247031560780232, 0.046746302900782945, 0.03368917155342115, 0.03861989348367033, 0.04332079840760135, 0.0412844598148396, 0.0848684093812848, 0.03630646812063554, 0.07071425282923066, 0.037790375710528915, 0.05284987436622104, 0.04070160023313682, 0.038205393422087425, 0.04324823524072468, 0.041031066935650264, 0.04667156924422306, 0.03864138471777243, 0.03555968104173664, 0.033798199833229695, 0.0371094078106881, 0.03341186099205563, 0.03634809825987585, 0.029703312291153763, 0.032901596691561716, 0.06047116353243433, 0.03318516609373084, 0.06865844927420295, 0.04020459026432551, 0.06702538950145423, 0.03478548812175413, 0.046943941858103765, 0.036220585568958207, 0.05550953419056129, 0.06291070807347247, 0.06431047157661085, 0.05592604419471292, 0.06770394127806097, 0.04483020523293156, 0.042999322249694535, 0.04023462321315526, 0.06021631241974339, 0.041267968046780706, 0.041811673557397566, 0.052193617622387986, 0.04677640218104074, 0.04854043378198273, 0.050564749331803126, 0.0354720766794601, 0.044070709986506265, 0.04523897953637904, 0.06107939721027637, 0.039657796427926516, 0.04219574332157082, 0.0408167404517981, 0.05196721638301223, 0.04328356677981461, 0.08133468191390415, 0.038962916089567694, 0.035517829921336, 0.05577691807284322, 0.03391646528054871, 0.03625227818282389, 0.046998928164292936, 0.059855919775582404, 0.039981988344404466, 0.055060547188628725, 0.061764245648384584, 0.05406778349745168, 0.03599418758734163, 0.032761947719629314, 0.044293595294180456, 0.042601632768382074, 0.035647285423761964, 0.04183724459984069, 0.06069852483626367, 0.033039358163757936, 0.041234068153682614, 0.0491937223481964, 0.04200362244948738, 0.03323484672140339, 0.035751346548288966, 0.04518367971518367, 0.032353984975958185, 0.04553383497956681]

bins = np.linspace(0.001, 0.1, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, PMS(2.,0.2)',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 6 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=10%, overEstWt=1.
lvec0 = [0.020035734024549143, 0.02005656193917887, 0.019838639397240693, 0.017560466794934275, 0.021504543036655437, 0.023045427101543486, 0.01783876632503485, 0.01896114458360438, 0.018148308452504765, 0.01963240728159441, 0.019437764398729344, 0.017202316947839073, 0.019047276505884163, 0.01826058953041846, 0.021427059181959928, 0.020474495082370373, 0.02103253767716469, 0.021718029337606387, 0.019182769482559096, 0.019256041164082176, 0.02040860715328469, 0.02123261856392162, 0.01836102089666982, 0.01938819977525935, 0.017732299338895287, 0.018401177570401255, 0.021922651726948527, 0.02039555172621135, 0.018288139900648533, 0.019629707278157757, 0.021256252285283737, 0.019408451058677927, 0.02007780661290464, 0.02014467336854861, 0.019440264377966768, 0.01810461007136605, 0.02035530294271441, 0.019248428049639596, 0.018282830023999743, 0.01889048323953737, 0.0192682091696877, 0.017536671339772544, 0.020161186528483206, 0.018385904065852176, 0.017657366236783396, 0.020255316044950865, 0.021895317593223832, 0.01864019231876829, 0.02016251321309696, 0.021809316111135808, 0.01801960090756191, 0.01837153858434028, 0.01911530737382263, 0.021912200765645033, 0.016983764317013428, 0.020267887124186954, 0.020597627204944603, 0.019572475441050164, 0.01916220548828678, 0.019495534378778538, 0.020925062818310747, 0.01658070169752567, 0.01767826378093967, 0.017581383937292642, 0.018939540599909536, 0.020577395944041788, 0.01714086899063931, 0.019978643118733954, 0.018174670430843993, 0.018805658611580758, 0.0194408322151454, 0.01797371697395821, 0.018329733961094673, 0.0193077393438492, 0.02069589460486727, 0.018841317783546554, 0.018864414940786323, 0.017391695459093456, 0.019490471057075003, 0.02038581575736658, 0.019203295962442177, 0.01694219697199376, 0.01797028438264967, 0.01862586508419463, 0.01821309648265841, 0.02075518930781996, 0.02100968342758268, 0.018052621537725237, 0.01902979324457343, 0.01894675053102696, 0.021930170704035627, 0.019159289358949783, 0.02014448767409621, 0.018070907785676098, 0.018345294639116848, 0.019717700690903058, 0.02218420872743696, 0.01987790855749312, 0.01657476371821114, 0.019748632608619445]
lvec1 = [0.01368838461069973, 0.015520153481345798, 0.014833797680378014, 0.027676201963905432, 0.016531611869346163, 0.016320279132625078, 0.015914934814638525, 0.018372857399674907, 0.013967645325569076, 0.014305640974732097, 0.015352162542109615, 0.012280584837981228, 0.01381203996953617, 0.015574121285586768, 0.013440961934703653, 0.013889572424670711, 0.028529711428171994, 0.015048787073206966, 0.013503939297520745, 0.016097877987227338, 0.014590586299313639, 0.016450080784319646, 0.016791216088824536, 0.013181793482402178, 0.016278337348575866, 0.015826971499953917, 0.015498869853498775, 0.020295996970788953, 0.018379537826323494, 0.015022660488228957, 0.013168336803228847, 0.013142874238793373, 0.016156256046081105, 0.016297662937377298, 0.017232497606036203, 0.019818152516988544, 0.014551647957193882, 0.016645247929158138, 0.01395901672517691, 0.015072166040435384, 0.019925389422003528, 0.01733520367234442, 0.01673854957551999, 0.01517537237507535, 0.01997949058641607, 0.016808956180249236, 0.014522381622222936, 0.014536662801471591, 0.015330388926253146, 0.013841923844351879, 0.01610329062904896, 0.01473474549151482, 0.018775920477540127, 0.02586407695284894, 0.0182869282309497, 0.017075221615269406, 0.014347517495510088, 0.013655978601968093, 0.01836719529015865, 0.01727933529914039, 0.014870488478760626, 0.01859979670767046, 0.014388482550044643, 0.01527275042795832, 0.021823830782746897, 0.01708796878327965, 0.015431486378637425, 0.01609790609658345, 0.017247267692915774, 0.014559040125088804, 0.015317905996461325, 0.01852186619817134, 0.02613548971463588, 0.014344305518089807, 0.019285894083636762, 0.02401352760980135, 0.014584407344231394, 0.019636238926763944, 0.016883489977587308, 0.018541556312965522, 0.01634723900660405, 0.016244016562826168, 0.01657081933970586, 0.014156391729551212, 0.013501309779126128, 0.013744003806776647, 0.017700493824159887, 0.016605259232669336, 0.014506274672045587, 0.014388276541704633, 0.013763875313915128, 0.016976377964521255, 0.02089815311485899, 0.01706732204619577, 0.014564510294124968, 0.0140630922035727, 0.015236457474730266, 0.01681573127653516, 0.01398780675294714, 0.016264707590544582]
lvec2 = [0.024766853278696033, 0.01454198002445993, 0.0161458885139843, 0.016908590726111974, 0.025279700066027474, 0.0175232636207084, 0.016239189364312775, 0.01691502733720573, 0.014579417495716255, 0.014958766018097917, 0.019658791476916217, 0.013579406150684193, 0.02181846855079514, 0.014416824255679644, 0.017533594456837005, 0.01487585183144262, 0.028028886154187405, 0.01685507493642507, 0.014816505818540472, 0.014717772414096116, 0.0152654342835879, 0.0178319089894688, 0.01597177225394316, 0.013042690606654249, 0.019084722101154354, 0.016915857473045304, 0.02060579253854856, 0.018107431799050687, 0.018905117283442286, 0.01441307578885918, 0.015228006914473173, 0.013828226720648394, 0.025609856534886195, 0.01653387017503252, 0.015315754493280547, 0.013066266348003506, 0.015874651989106897, 0.014512939819398487, 0.01609903519607435, 0.015496725103361836, 0.017179510336826652, 0.014965317697111076, 0.014158923204647523, 0.014962064382520188, 0.022232125645825784, 0.016607324479914896, 0.026472365169436414, 0.015701967371705976, 0.015208805909970272, 0.015067699758516658, 0.018428266987087393, 0.016469588391343496, 0.014491671474673097, 0.016691671070986062, 0.01635655406687778, 0.015355392117071601, 0.014592052256620558, 0.016227873664195463, 0.016637088198021604, 0.013569417681883942, 0.01535138966811449, 0.016304515569218726, 0.015850404316867888, 0.015304003677333583, 0.016837597965476136, 0.015849441831984296, 0.01556951610599422, 0.017834765172636893, 0.018286739135325907, 0.01605728544811477, 0.013238323387749875, 0.016266413195633114, 0.01576160319688049, 0.014107041143565742, 0.016441434703794843, 0.021831210896933535, 0.01371392322181837, 0.014761190570606396, 0.017488549554315377, 0.013200920265686263, 0.02616819476831859, 0.016206043263939967, 0.015085535642169027, 0.017988531761294155, 0.015982797007586598, 0.016101304443830365, 0.014714062194647107, 0.014870891081581147, 0.014744957721266076, 0.014797086799666355, 0.014038659515161974, 0.01471815197415115, 0.02698202980487384, 0.014896877304976897, 0.015038064008621128, 0.013973594238386617, 0.018628316377312017, 0.015514385319896592, 0.024708578573507285, 0.014216675177939226]
lvec3 = [0.016459230134232422, 0.014287070613821961, 0.021825050406159365, 0.01815185930008465, 0.014607486842332512, 0.015484190524736043, 0.015821838267261756, 0.015424575990898219, 0.021887690668935044, 0.019015050944321446, 0.013370796955304107, 0.01700799196371329, 0.018820811276503546, 0.01565746235321584, 0.01720520601210335, 0.01835381522159586, 0.013540991984582683, 0.019105972604164693, 0.013106530650273878, 0.015344914757145901, 0.015220790778377888, 0.0154046455828251, 0.019204383775764066, 0.01376637869198713, 0.02455575358100589, 0.01333580680815884, 0.01715999824507916, 0.015190946709242285, 0.022487170387715166, 0.01684430723821976, 0.018245452164076564, 0.015818316162331023, 0.014530043555980345, 0.014104684843861274, 0.014877635245291732, 0.01597366705012942, 0.014195697069316946, 0.015094564249371462, 0.014503165412274399, 0.020356626868590032, 0.01716282723724501, 0.01472519035492352, 0.013868433657901878, 0.014354166935914061, 0.014643165555588825, 0.017098737074502768, 0.015847476826497033, 0.014077134369415252, 0.019532952628637672, 0.021736521698789996, 0.015437630223566671, 0.016601616290311455, 0.017055644881562873, 0.015033105758020367, 0.014695826023711783, 0.020578261225451266, 0.026080614777859144, 0.016207573824929825, 0.013405849980065639, 0.017107527183092823, 0.014483583461587205, 0.016570665089906345, 0.014596322414085249, 0.015764470214075926, 0.015577367385806758, 0.017003078104815092, 0.014210240062481493, 0.014968787564255603, 0.019170797448213164, 0.014079870724386658, 0.019161072017522252, 0.02010241275915394, 0.017796110311646633, 0.020728308144928865, 0.019582402922643075, 0.023373108749443833, 0.016716285864002752, 0.016807189199673906, 0.019170427167093204, 0.01712898433137234, 0.018895598653581706, 0.016437401574634993, 0.014633200269608708, 0.013473354206186438, 0.023770397813563583, 0.013830632749182581, 0.01921755302563948, 0.027168211341788852, 0.015884700286558067, 0.020663317335320366, 0.013489346510451795, 0.01439497089579836, 0.01895813457074343, 0.015232029861189461, 0.014524809525038082, 0.014589349241216128, 0.022089212969029097, 0.019482951860347673, 0.012878966920961443, 0.018427238264868317]
lvec4 = [0.021182408918629398, 0.01832445507318579, 0.01806786118509929, 0.018794453584366287, 0.02024792091830905, 0.018755201084612268, 0.018421702601463506, 0.020595096149644106, 0.019751333571858282, 0.018524790966781588, 0.018545410785263967, 0.019531164100154094, 0.022122691294826087, 0.017495789292451217, 0.020432380841905164, 0.02080369472369352, 0.017929292936005474, 0.019722796597231064, 0.021195874476694295, 0.01795091872658417, 0.018187945918339932, 0.0203114499112587, 0.019465336685766874, 0.01965095792222035, 0.018948535716893103, 0.0180595922197832, 0.017750410473951067, 0.02017766269312228, 0.0190690209582989, 0.018378173495447306, 0.02022123869011454, 0.02050229156295585, 0.020808333140097463, 0.017609397349447626, 0.020814116675301395, 0.018812092201099424, 0.01646423827616787, 0.018262452362930278, 0.01888068123804456, 0.01775585229562266, 0.017819532255556488, 0.01773349345936528, 0.024210996056503797, 0.019756458917665864, 0.017566094279035063, 0.019641229384664168, 0.0183035516778828, 0.021409288633579465, 0.01719796696524052, 0.020186404448030347, 0.01843167929181166, 0.01991393763637761, 0.018659044440893325, 0.018934693028550907, 0.020243991868448507, 0.018457179977491134, 0.021972903319364447, 0.019136139794685612, 0.019938969123752703, 0.01631240142259806, 0.02263144790610495, 0.019699955823627588, 0.021976613975280283, 0.017077464789697367, 0.01806639528874181, 0.01955829787184, 0.018969815660721718, 0.02184584005658448, 0.01897005341116264, 0.018656660599434306, 0.020639283468887035, 0.01947657325682779, 0.019513283118715655, 0.01892513499623692, 0.01816955429641798, 0.017373209663096367, 0.01748214740908714, 0.019184296241283906, 0.017479167864527703, 0.020399134864694763, 0.019212958465399874, 0.01882043498410312, 0.019340008654006497, 0.019790731517372696, 0.0195264997354922, 0.018157334429094844, 0.02054678508732044, 0.018018947082017484, 0.019900159288903378, 0.01669610715715738, 0.019916102153026492, 0.01802096442465314, 0.018488086227508162, 0.01820882979414472, 0.016947508818987902, 0.02091333154408282, 0.018674538575119637, 0.01981674735594602, 0.019755918059097387, 0.018046593772559176]
lvec5 = [0.020576021995382054, 0.014125970160034963, 0.015289198749006257, 0.0188508757976798, 0.014464601884719258, 0.0317511270490917, 0.01597939064754661, 0.02260594191911052, 0.015836198839109306, 0.024134014540861035, 0.014692787882409932, 0.03291671076053293, 0.014301716521285753, 0.014069426539921838, 0.017326391676754854, 0.026410143366564384, 0.014863035860250088, 0.015951806039137595, 0.014895916946232657, 0.01517373751864449, 0.013800600808681155, 0.0171412112433313, 0.01984262350163895, 0.014610173267061146, 0.014081591048333985, 0.015549164690397426, 0.018028168563151082, 0.021439814192121105, 0.01578783828957672, 0.01566038717865255, 0.023401930138330616, 0.016720752063125836, 0.015773999619183382, 0.014761302071763802, 0.015090816682818252, 0.013150110676658921, 0.01475655298306671, 0.016237839860145153, 0.0158897729701401, 0.01559363146781761, 0.017955583737826224, 0.014739828005287507, 0.014762103266121198, 0.019478833828565297, 0.018056986424977314, 0.012552298235827637, 0.021982752259170353, 0.018724305124088785, 0.027150818792069962, 0.017953302776190592, 0.016238097393324463, 0.015470680490619252, 0.016482472971264372, 0.017731504536871914, 0.025262848188978587, 0.019632922146437585, 0.017569239640018258, 0.018270158950241314, 0.016555438369582023, 0.023804672247615805, 0.016481218910417213, 0.017143484737621936, 0.017306932164804053, 0.017322467605761598, 0.020650472041818347, 0.014101343799039004, 0.014481252074032135, 0.013718475949077387, 0.01652453294401741, 0.016823820395598002, 0.01803956748982207, 0.016861010067475084, 0.02256822886570356, 0.02060237598686598, 0.016610935663578925, 0.02822604773961096, 0.013481506237182318, 0.021610115022253816, 0.015286912665586972, 0.014525692988662877, 0.02118802935710763, 0.014115087133164506, 0.01785554957287843, 0.015281116504722164, 0.01705604900460368, 0.0137232223434176, 0.012866197609341315, 0.017069334758243463, 0.02401144335656192, 0.03010902277251383, 0.014335739405538329, 0.013078554150529852, 0.027717585180725715, 0.023730850827713885, 0.01686373175359898, 0.018852002289910068, 0.017587170075941884, 0.017183907701630138, 0.015603945172650121, 0.01527037706697287]
lvec6 = [0.015311423497859588, 0.019326402509575936, 0.014472075075513137, 0.02306713396691687, 0.013156374508323198, 0.018445434020652768, 0.014368572212225175, 0.015102577083132085, 0.014714582286761644, 0.01637026486934384, 0.014323113746705855, 0.014943190074989069, 0.013370825128371382, 0.016002956265069417, 0.014435064981260265, 0.017589754366837507, 0.01959212153925876, 0.017757661957508806, 0.013275615993986923, 0.015386089819434108, 0.0165203651120322, 0.015677188368064282, 0.03075113819972513, 0.014204901085615996, 0.02589057330671301, 0.014716845114405004, 0.019127197615383805, 0.015421463928714097, 0.014753505640364881, 0.01653405415566765, 0.01591629819555193, 0.017912116042776146, 0.01485814100785891, 0.013631762743681004, 0.013402469092263489, 0.014086119814376625, 0.01347523693567273, 0.014632142251223897, 0.011998242654708738, 0.013511338686500058, 0.022666591567698537, 0.01316528078057544, 0.024837024883442003, 0.015551119469020857, 0.02509442724059841, 0.01395179077041428, 0.018029827968850522, 0.014297979485258473, 0.020789551661234206, 0.023358007132500334, 0.023392157154228512, 0.020622029536310756, 0.025080337363939283, 0.016919059317657636, 0.016401953760981455, 0.015355013802754086, 0.02164346771710618, 0.015767302743583747, 0.0162382251367808, 0.02022376155450981, 0.01782145888865995, 0.017923627048444288, 0.018721699435938547, 0.013829128496394325, 0.016835893330841442, 0.017270438236623734, 0.022848575086123955, 0.015456721625877747, 0.015930152812510964, 0.015318393796307589, 0.019209900032497406, 0.01643362012140531, 0.028934819302786196, 0.015174591523403709, 0.0139043560352741, 0.020109286141789705, 0.013647411639143679, 0.014461229672117373, 0.018014307560828675, 0.022440185769296905, 0.015206163603804121, 0.020094787914433823, 0.022028533517128204, 0.019822391228408835, 0.014045393964715727, 0.013059188903063386, 0.016818261603918548, 0.016108470116375295, 0.013863256049214671, 0.01605785876208328, 0.022644096896228903, 0.013173079032773446, 0.015616731117924275, 0.018551976709485486, 0.016065111257250308, 0.013537859570659918, 0.014223157713231415, 0.01717862648320927, 0.012882349771956469, 0.01750816750111687]

bins = np.linspace(0.001, 0.03, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, PMS(1.,0.1)',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 30 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=20%, overEstWt=1.
lvec0 = [0.01728729014931321, 0.018471918342130782, 0.015683815599280424, 0.015655644941699742, 0.01815963047507897, 0.016801844559582856, 0.015629703051773167, 0.018667554884051873, 0.01694482368386538, 0.014746901954150772, 0.014511976508500144, 0.014327385602907217, 0.015125668584179587, 0.015636987332666597, 0.01729784455744154, 0.014158589944664316, 0.015345482843518337, 0.017517073677329714, 0.015236045719924433, 0.01574874721197197, 0.014811074533242265, 0.016513239471657427, 0.01756957743712494, 0.016526385939271814, 0.014498931361412379, 0.014686115574308909, 0.01814130256363459, 0.013196227539490535, 0.01614853257782514, 0.01464580171145139, 0.016588128618273617, 0.014708487192838866, 0.015229236043196096, 0.015655408973299, 0.01423463657893135, 0.016900325200930457, 0.01526207375456269, 0.017025407848797334, 0.015949368022818693, 0.01672967442520684, 0.015566220069113713, 0.014877788396696788, 0.016532683527538256, 0.01489299676941007, 0.018434805569295786, 0.015626388941818416, 0.018462144367519907, 0.016088292887917178, 0.01598556700861214, 0.01813060697236665, 0.01748285230383631, 0.015952081074120245, 0.015934857447889937, 0.01631107875631688, 0.014395901572940437, 0.016774226164355033, 0.015774822741543643, 0.014651481249148833, 0.015169218184766922, 0.015561234349167211, 0.014852819791934993, 0.015986662328284423, 0.013707709221989365, 0.01432375288443756, 0.017330994747413498, 0.017588973428084402, 0.015934202622139536, 0.017325621081784794, 0.01727693418743328, 0.01958756003914346, 0.0155956147322963, 0.014714654850202928, 0.01515572234174987, 0.015026373261513477, 0.013666265862091635, 0.01641067308567396, 0.01764512718171291, 0.016824135324949682, 0.01604824804692429, 0.014521177936402773, 0.015465804772273165, 0.013949171357429966, 0.016500671732389262, 0.014426041088188981, 0.016149849135599137, 0.016658025535992094, 0.01591683065513411, 0.01393257519035395, 0.016294422425590684, 0.01632693554201407, 0.014330754019540577, 0.014089032583448605, 0.015464704287658384, 0.01474551726808667, 0.016421839985492837, 0.015885368682801344, 0.017222461901998685, 0.01686571720413538, 0.016491702089873047, 0.016079065150581707]
lvec1 = [0.008391605533154727, 0.008867692915398762, 0.01235347981023735, 0.010520755527905148, 0.009824725643581507, 0.009113627443215816, 0.008578931729146044, 0.009823466749820842, 0.008015610018936258, 0.009120035356041136, 0.009592994799732604, 0.008680463500052285, 0.009140487276852686, 0.0094363492144605, 0.011836668971563593, 0.009926257193627148, 0.007926548140718404, 0.008352776802650773, 0.007653444452899067, 0.009493109524987504, 0.015862656916880685, 0.009417167373324984, 0.00824375891232307, 0.00820770494929278, 0.01533634552964456, 0.009994384983732039, 0.010884056214420039, 0.009538434170745047, 0.011278067911927685, 0.007468704164020146, 0.00845515665626566, 0.007674533259566625, 0.008870481715271127, 0.009501868434742903, 0.007941711140138998, 0.010703082453916374, 0.010470585186558799, 0.008877269395963321, 0.009004273659678206, 0.011442294922740437, 0.01839170933567517, 0.010011384431986922, 0.009096872815985367, 0.009049021475586507, 0.010631267520059112, 0.008269763355271496, 0.00794868580003554, 0.009158371964665695, 0.008067848730983505, 0.009261430739131224, 0.008774431742415777, 0.009695582478327771, 0.010296565748753185, 0.009501144944291839, 0.010023676194523082, 0.008724919157155848, 0.012035844880253886, 0.010547398407099883, 0.010170407763814284, 0.008174037000176501, 0.009990503781937181, 0.01010148895801915, 0.010408880727384301, 0.011270746506613668, 0.009825759825816589, 0.01120519222445761, 0.007808293877560399, 0.00935853500490824, 0.011617221435826382, 0.0086646115880574, 0.008192402550540734, 0.012025934780471977, 0.017932431042901154, 0.007857337607931239, 0.011710561599298609, 0.018474289040025425, 0.00976246957440904, 0.0096915640358833, 0.010400271487859337, 0.01035172564081102, 0.01008009918012806, 0.009371665494509442, 0.00899337512887673, 0.007801515168438731, 0.009444581258841915, 0.0073973128907510646, 0.011451528071379712, 0.00893154344871807, 0.009715070114127443, 0.009191359230868931, 0.008499607726698907, 0.01030806034170421, 0.014594004520618984, 0.014184825812449795, 0.00940949487397833, 0.012130709579070954, 0.012068315042730433, 0.011161172795762037, 0.00897840649878541, 0.008269550560804943]
lvec2 = [0.006877109316637901, 0.013179602135788001, 0.008465837483962589, 0.013334031837735726, 0.012380130334511054, 0.006424857015871693, 0.006979901529813544, 0.007221924188637552, 0.00903907946240148, 0.006740854286361001, 0.009623908230803186, 0.00688444756921271, 0.008654704169185989, 0.0087906201380175, 0.00737406135537556, 0.010444701696707814, 0.007259024212425955, 0.00676215110591187, 0.01312638167080718, 0.007797016914678759, 0.007842157135745926, 0.009460379450298083, 0.008770116148335488, 0.0070956501102529814, 0.011202585140558876, 0.007249944824907526, 0.010468430697202413, 0.009712189955263835, 0.00732574374864788, 0.011047962315702589, 0.009980564055608862, 0.007051479114819041, 0.008657603018467545, 0.007212499044832867, 0.008755711392075453, 0.007328399624187246, 0.007779422197257905, 0.007466867964075837, 0.010279332197531693, 0.007730996433097717, 0.019425089277929294, 0.007065668451254058, 0.006521945651238206, 0.010215525780199144, 0.012209754204385099, 0.007692383188208813, 0.013497180723962077, 0.012123451896550735, 0.01000439767894141, 0.0076102198813320105, 0.00975779193160731, 0.007101060701625442, 0.009892336401060516, 0.010097513034372391, 0.011109246013397259, 0.010125960267903418, 0.013925664609214012, 0.014244227669805602, 0.012401274421436107, 0.009341695812635534, 0.008750120801769408, 0.006812160002525217, 0.008072493973671775, 0.0072879633858621545, 0.0077001649300828204, 0.0071767483712794206, 0.011092870990126364, 0.007225181789956158, 0.009187633254617295, 0.007662831054673267, 0.011127290247996283, 0.0070631400158141285, 0.007647658001407184, 0.00755339417266755, 0.006718757691364237, 0.009411649995888853, 0.008256513657986924, 0.007996736000209769, 0.00659288037472716, 0.006866160214167135, 0.007889048624701073, 0.007633293695562305, 0.007587803661882176, 0.012554742563830702, 0.011179584951055808, 0.006505618930586171, 0.007225490985040163, 0.00719013380714886, 0.009690571074134551, 0.006697696187556011, 0.007507124040207948, 0.010489478419691277, 0.008761902951026987, 0.007770791622781221, 0.0068097237249886465, 0.008480773691495273, 0.00795942259197447, 0.010984380155486187, 0.014297675874621133, 0.007486985706885072]
lvec3 = [0.008704894299401219, 0.01251608269536652, 0.019969957480827687, 0.008778850406670643, 0.009270050870622071, 0.007638237731191134, 0.009291096169706522, 0.00790597784131658, 0.011909779066634051, 0.013296665360002444, 0.010641374583595691, 0.007919257479208222, 0.011525301292040277, 0.00823666114438279, 0.013036094873758725, 0.012803373610898484, 0.013735749570152396, 0.010877454706844779, 0.007507172492005733, 0.008944514796438836, 0.010722656555888319, 0.009316113248517237, 0.01079262636450678, 0.00979851082712124, 0.009579699072138795, 0.009794932623813733, 0.012109986243450374, 0.008651274161838987, 0.011990293668341133, 0.009135991273147471, 0.009004921396594898, 0.008501910548631784, 0.013697873689539218, 0.010877328624590621, 0.0072528519199907965, 0.008467480347943644, 0.008098207376223047, 0.013480682712185457, 0.010296930560991078, 0.012851214186690746, 0.013187967789639066, 0.011945035847889831, 0.00844323728249091, 0.00837854671131469, 0.013915422955621965, 0.010068827418127617, 0.00961942506447852, 0.009922439506294348, 0.012137900546964762, 0.009203930745882077, 0.008952757593012462, 0.00929396917113039, 0.00967053531959739, 0.010800098295205047, 0.00817463663652617, 0.01035299111072568, 0.007831017462838753, 0.011690616891453889, 0.00928384612510225, 0.011151722534301297, 0.010375499016057185, 0.0095534280184862, 0.012242204555721089, 0.01236603647930396, 0.010596893726302719, 0.00889629358529137, 0.017736917308214827, 0.009090368144728734, 0.013765343360646491, 0.008348238362082773, 0.01117401581261992, 0.011652109273629972, 0.00868412029854486, 0.013436721136965916, 0.009017248800378441, 0.011310156727563447, 0.008968495752270478, 0.008473871610713403, 0.008418897069356428, 0.021598628248068807, 0.010554733477448541, 0.011589237058074195, 0.008662204338243234, 0.009824745228104574, 0.008953206733102, 0.00816571203394725, 0.011166177761758206, 0.009245831994019493, 0.014461832363124861, 0.0079838045239295, 0.010182264415239275, 0.011833515899512561, 0.009146934663475239, 0.0073656870546474655, 0.011448910099155307, 0.007323524457746214, 0.010418893420791513, 0.010125904927763173, 0.009176641595467105, 0.009253891435318767]
lvec4 = [0.01313728434194406, 0.014209787254099623, 0.013582828229842366, 0.016564622364124676, 0.015456649476796654, 0.015234020710421245, 0.014952765606946925, 0.014047163435387927, 0.01316697323831591, 0.013257194978201704, 0.015431073311758435, 0.014914270989156512, 0.014082693491683182, 0.0141812355344424, 0.014290286330093006, 0.015490954090449111, 0.015211553907963528, 0.013353555795092825, 0.013726416989302636, 0.015630208555056497, 0.016084208878214136, 0.015157649244095683, 0.015180944740514582, 0.015031592585199127, 0.014902577540531, 0.014805077647729764, 0.014216146590376465, 0.01399274406323584, 0.014672269088150088, 0.014402756948679851, 0.015527670456972101, 0.016554892841454463, 0.014121675799494488, 0.014458014026406696, 0.01702621003154555, 0.013525856417398396, 0.01612805197647894, 0.014411585448695311, 0.01771761436772946, 0.014029471067672043, 0.014888669658395023, 0.017843862396196317, 0.018840947181238216, 0.015067070654116213, 0.015547297232460459, 0.013509689875926425, 0.016671001822966134, 0.014850645073740091, 0.01447972084071085, 0.014113163706208165, 0.014063862801915716, 0.02056055341250483, 0.017970852368287275, 0.014565212228337837, 0.01458190771211449, 0.013835272196040806, 0.015964797850263657, 0.014395312308500833, 0.015680330958318205, 0.013500048369105466, 0.017517398887550974, 0.014297610905285267, 0.017166520545467565, 0.01276366706852271, 0.016290713087804887, 0.013928197895845054, 0.014213149685924471, 0.016482870380946018, 0.01410778555523349, 0.01541303363486504, 0.014589514081010837, 0.014861932524754604, 0.01694524294398754, 0.013704503855824491, 0.015354771191925692, 0.015572137962320109, 0.014877444301922473, 0.019754825816910012, 0.014876646477063365, 0.017312818009530582, 0.014972840796842923, 0.015671687742587634, 0.017951728687843005, 0.014142248949609712, 0.015002684031329507, 0.015174460913228984, 0.013771326037521996, 0.012298346959153012, 0.01666415443308102, 0.014945269534251519, 0.01438888283019336, 0.012846572711658864, 0.01593516146793305, 0.015266855642109074, 0.014568620113549358, 0.016083686042984126, 0.013859416710623388, 0.014024420095223648, 0.015993993059609857, 0.016436923478425423]
lvec5 = [0.00705897684385838, 0.008583453863977963, 0.00822673299724233, 0.013565984375809716, 0.007635229614938759, 0.006627506503580114, 0.008050343841311026, 0.015717895703363814, 0.007668898512021309, 0.006757898166454954, 0.006537134755125903, 0.010379883135560163, 0.011602619512971188, 0.008833023521846192, 0.007499090336239253, 0.007031684562320429, 0.01546869155058592, 0.006532197360706497, 0.006923154848783764, 0.007653255043206677, 0.008002099829339467, 0.008200091411120042, 0.008006254855676293, 0.00866599740593845, 0.008522696752559133, 0.007779704398812774, 0.013492878622622174, 0.009658038393727376, 0.006798213021634036, 0.008249646010089918, 0.006689761579354938, 0.011272128191378067, 0.009893875820582453, 0.011701509065043332, 0.007720302358216688, 0.0075781464610286614, 0.02188643328942683, 0.009746023447111443, 0.010136129134250242, 0.006589866931495101, 0.008186705455559547, 0.007480513245487152, 0.008383728384335922, 0.012999806922719015, 0.0074844594626065275, 0.0067657051041183375, 0.007791249987940374, 0.015335129942218315, 0.006860903399606504, 0.007526655442220837, 0.00807603078412193, 0.00946083008057908, 0.01126426885281429, 0.008570797641190982, 0.01290100908996034, 0.007090188696605776, 0.008563576946991995, 0.007593046875917991, 0.006553798643705189, 0.008186632417566366, 0.012691379480342317, 0.01144015797044641, 0.011604717567808311, 0.009556810696312635, 0.00802904322793259, 0.008260724777120443, 0.01031818806917972, 0.009352448158637507, 0.014411963467581609, 0.01089833223202352, 0.006670608758788378, 0.008582313328165916, 0.008968743547936586, 0.008204952236707136, 0.014578698084179855, 0.018250643782040714, 0.008711604890481787, 0.006828019069561203, 0.013842474416691768, 0.014200446263629832, 0.009310380807646932, 0.008713365874981938, 0.006998674093556041, 0.01177610059054582, 0.009902918055217865, 0.006483253740461586, 0.006481818642548819, 0.00694752163034347, 0.009851756663543139, 0.012470157453592763, 0.007308162545278951, 0.011598709614056239, 0.011274448738389583, 0.007312734266171595, 0.014871822012607113, 0.008845513382996249, 0.010449702431151151, 0.009387735325017682, 0.012061951784188478, 0.007999544005310852]
lvec6 = [0.007042059630777488, 0.006822614175573789, 0.009695667694790305, 0.009606716671986572, 0.012544471884818905, 0.014946429853576535, 0.0117123643967494, 0.007425356472852058, 0.007403685205447895, 0.012678415510981703, 0.0072122060779232725, 0.00658494420153568, 0.009242523396988792, 0.007083215977486052, 0.010813935894511666, 0.006974617189987063, 0.00935244930227681, 0.006197986326767704, 0.011954158119290709, 0.007353492091119611, 0.009771829478679255, 0.0071805800624448616, 0.012943212770799715, 0.006368757074100224, 0.008360774344183957, 0.010191432540216296, 0.015628514483336707, 0.006975359325896849, 0.009886964351849957, 0.007903344910441444, 0.009031556128687003, 0.006650675462109655, 0.009632990757033062, 0.00780917019668244, 0.006223364260086694, 0.006966982817250484, 0.013843129151467952, 0.007175515986372118, 0.006632229075960022, 0.006495751398786483, 0.016210460714369934, 0.0071179629535057624, 0.006848579276602457, 0.011169786871059078, 0.007096464567273727, 0.0066407390887585046, 0.009663798688972491, 0.007425148215050655, 0.01072751477918369, 0.007507504072422916, 0.00756509003769649, 0.007171557330010366, 0.012102929756980324, 0.01217839333326704, 0.010908914253772254, 0.010265167467251105, 0.008969243863090986, 0.007601956558299698, 0.009789930580015073, 0.007314381504218152, 0.0074790932273756695, 0.0077749018446602435, 0.008093106322705981, 0.007186142540498965, 0.006994495615730398, 0.00746825535086623, 0.014581838929754624, 0.009047996147329885, 0.008672352257142538, 0.010714850395392677, 0.014368805749173909, 0.00739991251117953, 0.007569250350530316, 0.006965266680498088, 0.0070491954111052855, 0.008995720503849359, 0.008737801672075454, 0.0076205051587823845, 0.006304549108367185, 0.009937219142699323, 0.007137731268679045, 0.009333364433423749, 0.007324076552893495, 0.012459924025041695, 0.006981335267440186, 0.006015499517350092, 0.007490081457927423, 0.011500405035150424, 0.008341740109078686, 0.013480684573196, 0.009059275227627105, 0.007962494342602823, 0.0126927628597253, 0.008128467958722442, 0.011342648830491247, 0.007228812093276274, 0.010259101596250248, 0.007918634601128217, 0.011556653549985809, 0.010771856392940087]

bins = np.linspace(0.001, 0.03, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 30 tests, Omega=100, PMS(1.,0.2)',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 30 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=20%, overEstWt=2.
lvec0 = [0.05340890492585494, 0.05820017119639504, 0.055159621028566225, 0.057705218754149135, 0.05008418734353597, 0.05068222583887698, 0.057256353483709194, 0.04838922623195669, 0.05505163393021836, 0.04829490878044514, 0.04856237371039545, 0.04964113804040521, 0.04821105712194246, 0.047369563952574585, 0.05033829135671399, 0.04837618067469676, 0.05395620043017826, 0.0518434439862483, 0.04680935095027758, 0.04973823308765938, 0.042744926637013556, 0.047825986245281796, 0.04457737798883909, 0.05837179903976296, 0.05299601352220734, 0.047155128271289225, 0.048430817248152846, 0.04951043748671617, 0.05234970762388437, 0.04797153964804197, 0.0511053293087705, 0.05162329325350428, 0.056260694752954504, 0.05147112632544638, 0.04874362138960874, 0.04798347863133063, 0.05108102226137571, 0.06119594659728703, 0.05746380616998718, 0.04734862832927931, 0.05401004213011451, 0.04834687639581981, 0.04152618042916643, 0.04864473653732238, 0.042832424883722305, 0.04733849160331509, 0.05087200969562211, 0.04789446748363723, 0.047818418549174777, 0.04985226336769546, 0.056070022179740484, 0.05520464712180312, 0.04826654900750391, 0.0466577144913161, 0.05034870650359856, 0.05148843739044203, 0.04856768137903386, 0.05468481697643511, 0.047834368298967665, 0.04998374266698511, 0.053775292611699915, 0.044461189309672564, 0.05508323711599948, 0.05042060321776053, 0.05378292732268146, 0.05010994539330754, 0.054864269768104504, 0.048141195855994856, 0.0505201182421093, 0.0565111008072209, 0.050674275121562244, 0.0481058889203885, 0.04772936082272347, 0.04810618988776218, 0.04926513014834792, 0.050936820825523275, 0.05328159174537579, 0.05370889365640707, 0.04832891056845242, 0.051301142318596754, 0.046423711369078, 0.044768906827016404, 0.05041247529558998, 0.04674170581523738, 0.04722664864183755, 0.04589364535246836, 0.04412781155810311, 0.0592162443718002, 0.04607663271768663, 0.05133990997345871, 0.04644193000252004, 0.048587047189224464, 0.04714104542673156, 0.04924516293205036, 0.050729552613539446, 0.04787657656906362, 0.04737779650534382, 0.05545101147544792, 0.04722627325878679, 0.04720880100712451]
lvec1 = [0.03094612835315418, 0.030257605877113687, 0.03480553077335599, 0.0380699548362595, 0.034680389566741625, 0.03892570926088197, 0.025335643305804095, 0.028379607989158073, 0.02511955277840401, 0.02688871664779657, 0.039966243486302164, 0.02742863189997424, 0.0327002999620347, 0.0327536338899513, 0.034365378502693465, 0.04244398168502166, 0.033950945301795044, 0.026651925108567367, 0.02626621578862567, 0.035336136101455654, 0.04750984547008351, 0.031911380539757464, 0.02578800748956454, 0.027649995031152903, 0.0471072297329486, 0.03079018957826006, 0.046922512636985, 0.034208523940849965, 0.03886079257836491, 0.03160124961608294, 0.02469613423514184, 0.03365193146166961, 0.03041247494728862, 0.040901515272158184, 0.02547118968522499, 0.0383388876990225, 0.027083714905809672, 0.03176289459230625, 0.03414738833535266, 0.043043153460287586, 0.06138850464847105, 0.03080588243613144, 0.028795059976046377, 0.031675469206856155, 0.04078695806395677, 0.026371152351685793, 0.027192532778686506, 0.028272381301327268, 0.034118719519769414, 0.04099201572851942, 0.03017749477019045, 0.03153752368747238, 0.03609205514628215, 0.03885028021554662, 0.03821302270648234, 0.02897749982997016, 0.03663174266205006, 0.03014145997306539, 0.030779846989158303, 0.0336788674832844, 0.029186010008385072, 0.03438210828707668, 0.044756610651206126, 0.039156149258411106, 0.04288663999534419, 0.030911909496838797, 0.03486907593782982, 0.025153918281819145, 0.04271447157930096, 0.033191827901596145, 0.02890654743562173, 0.05354584543221313, 0.038311934632009874, 0.02962817735661353, 0.03846079104334207, 0.06203780072193532, 0.03406943541511674, 0.028861898764463084, 0.029558152175233672, 0.03677302163647404, 0.037200397728578576, 0.03253483424600359, 0.03379234927412845, 0.03131557094585859, 0.03049691870026881, 0.02510315025680552, 0.04058299541547555, 0.03725894421265139, 0.03488511528061093, 0.03779207628631054, 0.028670156777577834, 0.033497125990465344, 0.05368841357897461, 0.03898363678328693, 0.03179975735370762, 0.03331926646132423, 0.03539111456193399, 0.07266950438748382, 0.027659942995514372, 0.02949830549381525]

lvec2 = [0.044473024192391596, 0.026270161123936774, 0.026571349963975383, 0.0473354269687873, 0.03709193264061455, 0.0288581383515424, 0.02139519955323484, 0.0240611286730907, 0.02377454362086177, 0.038182873951706504, 0.029707530870694516, 0.029901704269522898, 0.02848618750781632, 0.02195776530801455, 0.04744113045674639, 0.02921238750335341, 0.02911903124708006, 0.027016752170503994, 0.03474457159924231, 0.024102439960541427, 0.024408900757754187, 0.030965400358435737, 0.0421925434589638, 0.02093823296818666, 0.02430905652478868, 0.02245912920085211, 0.05479603596134192, 0.035987754365959294, 0.02327859511237957, 0.02887366740225795, 0.04170994627526647, 0.02319685872749705, 0.030541105453570506, 0.028472832381510126, 0.025022056675751633, 0.025346655347548416, 0.02233685652483131, 0.021972848689024535, 0.03122498157941839, 0.02615666600576044, 0.04245848159633734, 0.024807055649670232, 0.03302794002110626, 0.03091436468369191, 0.061598021453863956, 0.03124936524691525, 0.040363408607823247, 0.0318253460514068, 0.024176250537131315, 0.03345652490449575, 0.020450330835195044, 0.022128177062263974, 0.04591309011104436, 0.03561728848248467, 0.04033643559223796, 0.02137376793398877, 0.022796250149145585, 0.03980940797255285, 0.029710631117934476, 0.030432077656512173, 0.024738194249388147, 0.025638239835467234, 0.031429186165666236, 0.03639181754201111, 0.03795304389756812, 0.02200502369529581, 0.050992067688180015, 0.04547579938272329, 0.02323053346195974, 0.01875744814597118, 0.043685969010156714, 0.03621951691150437, 0.03672750655022714, 0.021580752968800288, 0.04278842111393421, 0.03757127586578734, 0.02573523107032383, 0.024722176113965152, 0.04666737080368104, 0.029589228052944925, 0.04296315925913225, 0.033561627359547014, 0.0436116633551935, 0.03525058972352138, 0.02319702722422079, 0.022533305645178546, 0.023400962947590486, 0.022924063812889403, 0.029602355374513126, 0.0439649382179108, 0.03967294708007135, 0.022999057638463927, 0.03234978180313585, 0.02327617176542571, 0.026716507986075083, 0.02613082099751597, 0.04912615583171179, 0.03482252278030555, 0.029983941091874487, 0.030287080079792857]

lvec3 = [0.03433816660405013, 0.0362956023959572, 0.03226846094121976, 0.02939335681570376, 0.0506824977132847, 0.03428759058980326, 0.040720600371290126, 0.028304341445502444, 0.028642851501753126, 0.031712554413840514, 0.026501649036022604, 0.026026383667764486, 0.025085375089780638, 0.03282374093992602, 0.0325814823022389, 0.02694126151946941, 0.03542453166193582, 0.030542582731412058, 0.03148858701532841, 0.0298944828069608, 0.03305614634441167, 0.03708411891937548, 0.04160478749389184, 0.02536697902787464, 0.027310216150442813, 0.03881259372391596, 0.03111547595114105, 0.027592006023762914, 0.06253824603315326, 0.03254247542906669, 0.03291244874805076, 0.025598615602011782, 0.02690853755509903, 0.036569867797944584, 0.026944873734638462, 0.025714057312926843, 0.03784230787171411, 0.03083841602172276, 0.030625711194457263, 0.030075928305301702, 0.04300799450411001, 0.03029164833410612, 0.03369292840229123, 0.038207354940619956, 0.04839138464765889, 0.0387051641419906, 0.029116708956822935, 0.029247031091477572, 0.06316910137523152, 0.026815210266601445, 0.027785702772533907, 0.02854173489377515, 0.0494011619407984, 0.04278929331425377, 0.02833794004443708, 0.027724863106140224, 0.036646135038302774, 0.02831180198827037, 0.03899566424744029, 0.0280415511950528, 0.034349604094312425, 0.03844812786714566, 0.03044562019104477, 0.025085236376715652, 0.03139415072079574, 0.02949097562680032, 0.08757169224683328, 0.03279749687117172, 0.06321082758457548, 0.03224469981938111, 0.038669637295341217, 0.035709898936562304, 0.030134995566322303, 0.051946077076087255, 0.031802204786563586, 0.07969314230049994, 0.025885788825280635, 0.02922666256224963, 0.03144394274112948, 0.038359529644468836, 0.03451070383965132, 0.027021801816584007, 0.03654259052879759, 0.038711231975959826, 0.04903174596616006, 0.027370257208948395, 0.03191554097317989, 0.029091134026932596, 0.03086330508231974, 0.03294689338055566, 0.03163125480385242, 0.03202347815787701, 0.06641511928754558, 0.05179913572457603, 0.029174286714215666, 0.033764549488031426, 0.03779378163654503, 0.05977521750433493, 0.029811994867374413, 0.0264178081507404]

lvec4 = [0.04675498012097751, 0.045806620476635494, 0.04681399596332623, 0.04937683916127961, 0.04680452933651166, 0.04861116552162853, 0.03926372929600427, 0.05079962467031455, 0.04714192051567956, 0.046652264269953385, 0.05385900108766862, 0.03995579282288011, 0.05401564464458795, 0.05040213784084813, 0.04462205580431971, 0.05067336261057559, 0.051991744729103485, 0.04428323735169167, 0.046834339278649655, 0.042973145115758636, 0.047544575402863505, 0.04818518396652716, 0.049724239840735714, 0.051468603929282625, 0.04749434110345636, 0.04899869104157339, 0.045922477222516404, 0.050636031735313225, 0.04808216594041665, 0.05157478979873349, 0.05654727647708807, 0.05197893205275613, 0.04488678215542313, 0.05047336807663794, 0.051105382423273574, 0.04558096710052999, 0.054042064928197, 0.04689312318692302, 0.04550627957429474, 0.04287025160142625, 0.05255586562798485, 0.06145644112619753, 0.05924917015504491, 0.051380932251782245, 0.04356313317964632, 0.04535839181459483, 0.0480259305777795, 0.05370052767806906, 0.04662279394399309, 0.04480009031506934, 0.0481379823228119, 0.04739758394188109, 0.05363083512137488, 0.055452662344538405, 0.05151547106290569, 0.0408520062283841, 0.05182648417586335, 0.04833317680600467, 0.05295067143400464, 0.05282650417090576, 0.056642266549299686, 0.042002770678151814, 0.04677920733297405, 0.04302253007257966, 0.045378726768707627, 0.04153979040320583, 0.04619316281626949, 0.06163460213902131, 0.04667948236246934, 0.054602373288829116, 0.04303148218530421, 0.0488191754248535, 0.051885583997373946, 0.04944164334939023, 0.05244525901516973, 0.050115547878546794, 0.04963227569060555, 0.04811408109899148, 0.048560056143374504, 0.04960921067335613, 0.0480974460956228, 0.04523152624716832, 0.04564212177046784, 0.046521252818547666, 0.04401273551904816, 0.04638668083374129, 0.048370685382226906, 0.044819615737278495, 0.05746052677432293, 0.04993582170025563, 0.04494662737357145, 0.050895451931209354, 0.044300522383970246, 0.049795216749271724, 0.056247256932143816, 0.04915208870954231, 0.04217722961454786, 0.043980860862712655, 0.054087836638843145, 0.045092061379667404]

lvec5 = [0.03290514329649738, 0.037069699734511984, 0.04538826657176474, 0.02729948656737812, 0.030161809222469454, 0.03773243990221078, 0.021024956757439935, 0.05012039930721904, 0.03262670746021611, 0.03563511827704842, 0.020636044275035015, 0.032212728678938506, 0.04760453127723202, 0.021012051814351784, 0.022229053656891696, 0.027642146535808, 0.024266193019010014, 0.02029323716125311, 0.022156307909854744, 0.022060918577354986, 0.02602220914748021, 0.02681871060785103, 0.03066778688070986, 0.019081654057232285, 0.0214544767800819, 0.031121935520260123, 0.04431461333888248, 0.027067297908216065, 0.02926527360459585, 0.02567088824416127, 0.03532928421739828, 0.024164403204495363, 0.025557513025302177, 0.021791464201117588, 0.03828810935095676, 0.0377578749651461, 0.029269527333803756, 0.024299047507482758, 0.05561391161439286, 0.03223161146262972, 0.06356255891176202, 0.025213466407581035, 0.02426613547373158, 0.030668209645638544, 0.06498531643770712, 0.021763435398520742, 0.031992322116304615, 0.02506409998078589, 0.039243212841626886, 0.023220505137086164, 0.025419134900758013, 0.030904871970183528, 0.052886787079166706, 0.026979987785827924, 0.04836290610740696, 0.02329466832665679, 0.022641587789771767, 0.032904965454555554, 0.030268541068914856, 0.041021258164745285, 0.05499613172713657, 0.023301922758528288, 0.025749199537249034, 0.038764589919399475, 0.0341777435758973, 0.027540703470262176, 0.04701681942870271, 0.03765668385424077, 0.03250163968010967, 0.022310368225932565, 0.04446495241477422, 0.02096393715896556, 0.026422864867788425, 0.03164268199278583, 0.029513653514399642, 0.05592620056773317, 0.03203644349124246, 0.032205709407876135, 0.02486941985519047, 0.024261906706886223, 0.038288377401785284, 0.03780997178266264, 0.046596625023343684, 0.030746986420074732, 0.030079778174779262, 0.022836552355112012, 0.02907171972798814, 0.029192042758475763, 0.03798754832954012, 0.029960063598900695, 0.0340948306376529, 0.03285568428350849, 0.05157638341334381, 0.032040116540517624, 0.05168450266599155, 0.023736791076975936, 0.03123105725978803, 0.03109560903865346, 0.04226442964434008, 0.021030479596285335]

lvec6 = [0.029804793424867606, 0.040641706957793795, 0.024244179422277093, 0.04651174738297737, 0.032428812363150594, 0.023459536491797064, 0.025366075280974586, 0.02578695058843841, 0.029599927111125995, 0.027567879679599814, 0.02054312507897707, 0.030211867578733224, 0.02189178142201914, 0.020548901459528434, 0.03145435989051667, 0.027950631071738705, 0.038250308851017475, 0.020434625748569565, 0.04897936772858365, 0.03489191786124935, 0.026045382494145685, 0.02604381776971005, 0.03264352891317386, 0.020061654028469506, 0.04614441910588079, 0.026506990423620837, 0.044142002105194006, 0.02185066946555683, 0.031392935345536305, 0.021771385418308902, 0.03130583859969011, 0.02181005718273604, 0.02565406824940755, 0.025638416377937817, 0.018402196652529273, 0.024214882572145914, 0.04555925311285528, 0.022997043346115492, 0.02954114552414229, 0.024358005578194165, 0.045652365251731324, 0.02740287095504684, 0.02777618376417831, 0.03338693382506874, 0.04857507916216406, 0.023866734536414348, 0.02770450010423948, 0.03495134636745285, 0.05510999042435775, 0.022873605450128037, 0.02191129522742106, 0.02339231724103373, 0.03932792413018525, 0.025547282329682824, 0.0376284472016498, 0.027904345624662857, 0.025649426103666197, 0.0225082077552041, 0.02949735643565646, 0.029237695861739882, 0.04993529898248347, 0.02279946789878314, 0.026166721014173916, 0.02377147971472904, 0.049209645949620864, 0.02080721932415891, 0.030320310241489463, 0.031887070871894, 0.02096028881315225, 0.023386171254537715, 0.02703711137770229, 0.025764012824661224, 0.023356015425569365, 0.022501096967773696, 0.02430656877779669, 0.04685181586775565, 0.018749589317671327, 0.02100716930522016, 0.027037494202994908, 0.023425876868243708, 0.019891479612049668, 0.03277896750408836, 0.02129327547872387, 0.039458589224535184, 0.02815999511444214, 0.018781224177517396, 0.02202212701552719, 0.019852140511552128, 0.032076193682865725, 0.029052303524138658, 0.0402624613725448, 0.034995419175426645, 0.034600337448944564, 0.034841659384959874, 0.01926692000508125, 0.028770447980100044, 0.030770242181674227, 0.05100224045149868, 0.0666664465633771, 0.021101965768194116]


bins = np.linspace(0.001, 0.1, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, PMS(2.,0.2)',fontsize=16)
fig.tight_layout()
plt.show()
'''

'''
# FOR 30 TESTS WITH ALIGNED PRIOR DRAWS, USING PMS LOSS W/ t=10%, overEstWt=1.
lvec0 = [0.020035734024549143, 0.02005656193917887, 0.019838639397240693, 0.017560466794934275, 0.021504543036655437, 0.023045427101543486, 0.01783876632503485, 0.01896114458360438, 0.018148308452504765, 0.01963240728159441, 0.019437764398729344, 0.017202316947839073, 0.019047276505884163, 0.01826058953041846, 0.021427059181959928, 0.020474495082370373, 0.02103253767716469, 0.021718029337606387, 0.019182769482559096, 0.019256041164082176, 0.02040860715328469, 0.02123261856392162, 0.01836102089666982, 0.01938819977525935, 0.017732299338895287, 0.018401177570401255, 0.021922651726948527, 0.02039555172621135, 0.018288139900648533, 0.019629707278157757, 0.021256252285283737, 0.019408451058677927, 0.02007780661290464, 0.02014467336854861, 0.019440264377966768, 0.01810461007136605, 0.02035530294271441, 0.019248428049639596, 0.018282830023999743, 0.01889048323953737, 0.0192682091696877, 0.017536671339772544, 0.020161186528483206, 0.018385904065852176, 0.017657366236783396, 0.020255316044950865, 0.021895317593223832, 0.01864019231876829, 0.02016251321309696, 0.021809316111135808, 0.01801960090756191, 0.01837153858434028, 0.01911530737382263, 0.021912200765645033, 0.016983764317013428, 0.020267887124186954, 0.020597627204944603, 0.019572475441050164, 0.01916220548828678, 0.019495534378778538, 0.020925062818310747, 0.01658070169752567, 0.01767826378093967, 0.017581383937292642, 0.018939540599909536, 0.020577395944041788, 0.01714086899063931, 0.019978643118733954, 0.018174670430843993, 0.018805658611580758, 0.0194408322151454, 0.01797371697395821, 0.018329733961094673, 0.0193077393438492, 0.02069589460486727, 0.018841317783546554, 0.018864414940786323, 0.017391695459093456, 0.019490471057075003, 0.02038581575736658, 0.019203295962442177, 0.01694219697199376, 0.01797028438264967, 0.01862586508419463, 0.01821309648265841, 0.02075518930781996, 0.02100968342758268, 0.018052621537725237, 0.01902979324457343, 0.01894675053102696, 0.021930170704035627, 0.019159289358949783, 0.02014448767409621, 0.018070907785676098, 0.018345294639116848, 0.019717700690903058, 0.02218420872743696, 0.01987790855749312, 0.01657476371821114, 0.019748632608619445]
lvec1 = 
lvec2 = 
lvec3 = 
lvec4 = 
lvec5 = 
lvec6 = 

bins = np.linspace(0.001, 0.03, 100) 
fig, axs = plt.subplots(7,figsize=(6,12))
plt.rcParams["figure.autolayout"] = True
axs[0].hist(lvec1, bins, alpha=0.5, color='red', label='Design 1')
axs[1].hist(lvec2, bins, alpha=0.5, color='green', label='Design 2')
axs[2].hist(lvec3, bins, alpha=0.5, color='blue', label='Design 3')
axs[3].hist(lvec4, bins, alpha=0.5, color='gray', label='Design 4')
axs[4].hist(lvec5, bins, alpha=0.5, color='orange', label='Design 5')
axs[5].hist(lvec6, bins, alpha=0.5, color='purple', label='Design 6')
axs[6].hist(lvec0, bins, alpha=0.5, color='black', label='No Additional Data')
axs[0].set_title('Design 1')
axs[1].set_title('Design 2')
axs[2].set_title('Design 3')
axs[3].set_title('Design 4')
axs[4].set_title('Design 5')
axs[5].set_title('Design 6')
axs[6].set_title('No Additional Data')
for i in range(7):
    axs[i].set_ylim([0,20])
fig.suptitle('Bayesian loss: 6 tests, Omega=100, PMS(1.,0.1)',fontsize=16)
fig.tight_layout()
plt.show()
'''