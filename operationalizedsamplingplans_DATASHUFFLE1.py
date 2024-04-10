from logistigate.logistigate import utilities as util # Pull from the submodule "develop" branch
from logistigate.logistigate import methods
from logistigate.logistigate.priors import prior_normal_assort
from logistigate.logistigate import lossfunctions as lf
from logistigate.logistigate import samplingplanfunctions as sampf
from logistigate.logistigate import orienteering as opf

import os
import pickle
import time

import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt

import matplotlib.ticker as mtick

import pandas as pd
import numpy as np
from numpy.random import choice
import random
import itertools
import scipy.stats as sps
import scipy.special as spsp

import scipy.optimize as spo
from scipy.optimize import LinearConstraint
from scipy.optimize import milp

plt.rcParams["mathtext.fontset"] = "dejavuserif"
plt.rcParams["font.family"] = "serif"

# Pull data from analysis of first paper
def GetSenegalDataMatrices(deidentify=False):
    # Pull Senegal data from MQDB
    SCRIPT_DIR = os.getcwd()
    filesPath = os.path.join(SCRIPT_DIR, 'MQDfiles')
    outputFileName = os.path.join(filesPath, 'pickleOutput')
    openFile = open(outputFileName, 'rb')  # Read the file
    dataDict = pickle.load(openFile)

    SEN_df = dataDict['df_SEN']
    # 7 unique Province_Name_GROUPED; 23 unique Facility_Location_GROUPED; 66 unique Facility_Name_GROUPED
    # Remove 'Missing' and 'Unknown' labels
    SEN_df_2010 = SEN_df[(SEN_df['Date_Received'] == '7/12/2010') & (SEN_df['Manufacturer_GROUPED'] != 'Unknown') & (
                SEN_df['Facility_Location_GROUPED'] != 'Missing')].copy()
    tbl_SEN_G1_2010 = SEN_df_2010[['Province_Name_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tbl_SEN_G1_2010 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tbl_SEN_G1_2010]
    tbl_SEN_G2_2010 = SEN_df_2010[['Facility_Location_GROUPED', 'Manufacturer_GROUPED', 'Final_Test_Conclusion']].values.tolist()
    tbl_SEN_G2_2010 = [[i[0], i[1], 1] if i[2] == 'Fail' else [i[0], i[1], 0] for i in tbl_SEN_G2_2010]

    SEN_df_2010.pivot_table(index=['Manufacturer_GROUPED'], columns=['Final_Test_Conclusion'],
                            aggfunc='size', fill_value=0)
    SEN_df_2010.pivot_table(index=['Province_Name_GROUPED'], columns=['Final_Test_Conclusion'],
                            aggfunc='size', fill_value=0)
    SEN_df_2010.pivot_table(index=['Facility_Location_GROUPED'], columns=['Final_Test_Conclusion'],
                            aggfunc='size', fill_value=0)
    pivoted = SEN_df_2010.pivot_table(index=['Facility_Name_GROUPED'], columns=['Final_Test_Conclusion'],
                                      aggfunc='size', fill_value=0)
    # pivoted[:15]
    # SEN_df_2010['Province_Name_GROUPED'].unique()
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar', 'Kaffrine', 'Kedougou', 'Kaolack'])].pivot_table(
        index=['Manufacturer_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Matam', 'Kolda', 'Saint Louis'])].pivot_table(
        index=['Manufacturer_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar', 'Kaffrine', 'Kedougou', 'Kaolack']) & SEN_df_2010[
        'Final_Test_Conclusion'].isin(['Fail'])].pivot_table(
        index=['Manufacturer_GROUPED'], columns=['Province_Name_GROUPED', 'Final_Test_Conclusion'],
        aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Matam', 'Kolda', 'Saint Louis']) & SEN_df_2010[
        'Final_Test_Conclusion'].isin(['Fail'])].pivot_table(
        index=['Manufacturer_GROUPED'], columns=['Province_Name_GROUPED', 'Final_Test_Conclusion'],
        aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar', 'Kaffrine', 'Kedougou', 'Kaolack'])].pivot_table(
        index=['Facility_Location_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Matam', 'Kolda', 'Saint Louis'])].pivot_table(
        index=['Facility_Location_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar', 'Kaffrine', 'Kedougou', 'Kaolack'])].pivot_table(
        index=['Facility_Name_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar', 'Kaffrine'])].pivot_table(
        index=['Facility_Name_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Matam', 'Kolda', 'Saint Louis'])].pivot_table(
        index=['Facility_Name_GROUPED'], columns=['Province_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Facility_Name_GROUPED'].isin(['Hopitale Regionale de Koda',
                                                           "Pharmacie Keneya"])].pivot_table(
        index=['Facility_Location_GROUPED'], columns=['Facility_Name_GROUPED'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Province_Name_GROUPED'].isin(['Dakar'])].pivot_table(
        index=['Facility_Location_GROUPED'], columns=['Final_Test_Conclusion'], aggfunc='size', fill_value=0)
    SEN_df_2010[SEN_df_2010['Facility_Location_GROUPED'].isin(['Tambacounda'])].pivot_table(
        index=['Manufacturer_GROUPED'], columns=['Final_Test_Conclusion'], aggfunc='size', fill_value=0)

    SEN_df_2010['Facility_Location_GROUPED'].count()

    orig_MANUF_lst = ['Ajanta Pharma Limited', 'Aurobindo Pharmaceuticals Ltd', 'Bliss Gvis Pharma Ltd', 'Cipla Ltd',
                      'Cupin', 'EGR pharm Ltd', 'El Nasr', 'Emcure Pharmaceuticals Ltd', 'Expharm',
                      'F.Hoffmann-La Roche Ltd', 'Gracure Pharma Ltd', 'Hetdero Drugs Limited', 'Imex Health',
                      'Innothera Chouzy', 'Ipca Laboratories', 'Lupin Limited', 'Macleods Pharmaceuticals Ltd',
                      'Matrix Laboratories Limited', 'Medico Remedies Pvt Ltd', 'Mepha Ltd', 'Novartis', 'Odypharm Ltd',
                      'Pfizer', 'Sanofi Aventis', 'Sanofi Synthelabo']
    orig_PROV_lst = ['Dakar', 'Kaffrine', 'Kaolack', 'Kedougou', 'Kolda', 'Matam', 'Saint Louis']
    orig_LOCAT_lst = ['Dioum', 'Diourbel', 'Fann- Dakar', 'Guediawaye', 'Hann', 'Kaffrine (City)', 'Kanel',
                      'Kaolack (City)', 'Kebemer', 'Kedougou (City)', 'Kolda (City)', 'Koumpantoum', 'Matam (City)',
                      'Mbour-Thies', 'Medina', 'Ouro-Sogui', 'Richard Toll', 'Rufisque-Dakar', 'Saint Louis (City)',
                      'Tambacounda', 'Thies', 'Tivaoune', 'Velingara']
    # DEIDENTIFICATION
    if deidentify == True:
        # Replace Manufacturers
        shuf_MANUF_lst = orig_MANUF_lst.copy()
        random.seed(333)
        random.shuffle(shuf_MANUF_lst)
        # print(shuf_MANUF_lst)
        for i in range(len(shuf_MANUF_lst)):
            currName = shuf_MANUF_lst[i]
            newName = 'Mnfr. ' + str(i + 1)
            for ind, item in enumerate(tbl_SEN_G1_2010):
                if item[1] == currName:
                    tbl_SEN_G1_2010[ind][1] = newName
            for ind, item in enumerate(tbl_SEN_G2_2010):
                if item[1] == currName:
                    tbl_SEN_G2_2010[ind][1] = newName
        # Replace Province
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
        # Replace Facility Location
        shuf_LOCAT_lst = orig_LOCAT_lst.copy()
        random.seed(333)
        random.shuffle(shuf_LOCAT_lst)
        # print(shuf_LOCAT_lst)
        for i in range(len(shuf_LOCAT_lst)):
            currName = shuf_LOCAT_lst[i]
            newName = 'District ' + str(i + 1)
            for ind, item in enumerate(tbl_SEN_G2_2010):
                if item[0] == currName:
                    tbl_SEN_G2_2010[ind][0] = newName
        # Swap Districts 7 & 8
        for ind, item in enumerate(tbl_SEN_G2_2010):
            if item[0] == 'District 7':
                tbl_SEN_G2_2010[ind][0] = 'District 8'
            elif item[0] == 'District 8':
                tbl_SEN_G2_2010[ind][0] = 'District 7'

    # Now form data dictionary
    retDict = util.testresultsfiletotable(tbl_SEN_G2_2010, csvName=False)
    if deidentify == True:
        retlist_MANUF = shuf_MANUF_lst.copy()
        retlist_PROV = shuf_PROV_lst.copy()
        retlist_LOCAT = shuf_LOCAT_lst.copy()
    else:
        retlist_MANUF = orig_MANUF_lst.copy()
        retlist_PROV = orig_PROV_lst.copy()
        retlist_LOCAT = orig_LOCAT_lst.copy()

    return retDict['N'], retDict['Y'], retlist_MANUF, retlist_PROV, retlist_LOCAT

# Pull data from newly constructed CSV files
def GetSenegalCSVData():
    """
    Travel out-and-back times for districts/departments are expressed as the proportion of a 10-hour workday, and
    include a 30-minute collection time; traveling to every region outside the HQ region includes a 2.5 hour fixed cost
    """
    dept_df = pd.read_csv('operationalizedsamplingplans/senegal_csv_files/deptfixedcosts.csv', header=0)
    regcost_mat = pd.read_csv('operationalizedsamplingplans/senegal_csv_files/regarcfixedcosts.csv', header=None)
    regNames = ['Dakar', 'Diourbel', 'Fatick', 'Kaffrine', 'Kaolack', 'Kedougou', 'Kolda', 'Louga', 'Matam',
                'Saint-Louis', 'Sedhiou', 'Tambacounda', 'Thies', 'Ziguinchor']
    # Get testing results
    testresults_df = pd.read_csv('operationalizedsamplingplans/senegal_csv_files/dataresults.csv', header=0)
    manufNames = testresults_df.Manufacturer.sort_values().unique().tolist()
    deptNames = dept_df['Department'].sort_values().tolist()
    testdatadict = {'dataTbl': testresults_df.values.tolist(), 'type': 'Tracked', 'TNnames': deptNames,
                    'SNnames': manufNames}
    testdatadict = util.GetVectorForms(testdatadict)

    return dept_df, regcost_mat, regNames, deptNames, manufNames, len(regNames), testdatadict

dept_df, regcost_mat, regNames, deptNames, manufNames, numReg, testdatadict = GetSenegalCSVData()
(numTN, numSN) = testdatadict['N'].shape # For later use

def GetRegion(dept_str, dept_df):
    """Retrieves the region associated with a department"""
    return dept_df.loc[dept_df['Department']==dept_str,'Region'].values[0]

def GetDeptChildren(reg_str, dept_df):
    """Retrieves the departments associated with a region"""
    return dept_df.loc[dept_df['Region']==reg_str,'Department'].values.tolist()

def PrintDataSummary(datadict):
    """print data summaries for datadict which should have keys 'N' and 'Y' """
    N, Y = datadict['N'], datadict['Y']
    # Overall data
    print('TNs by SNs: ' + str(N.shape) + '\nNumber of Obsvns: ' + str(N.sum()) + '\nNumber of SFPs: ' + str(
        Y.sum()) + '\nSFP rate: ' + str(round(Y.sum() / N.sum(), 4)))
    # TN-specific data
    print('Tests at TNs: ' + str(np.sum(N, axis=1)) + '\nSFPs at TNs: ' + str(np.sum(Y, axis=1)) + '\nSFP rates: '+str(
            (np.sum(Y, axis=1) / np.sum(N, axis=1)).round(4)))
    return
# printDataSummary(testdatadict)

# Set up logistigate dictionary
lgdict = util.initDataDict(testdatadict['N'], testdatadict['Y'])
lgdict.update({'TNnames':deptNames, 'SNnames':manufNames})

# TODO: Shuffle data in N, Y according to fixed random indices
np.random.seed(234)
shufinds = choice(np.arange(numTN), size=numTN, replace=False)
tempN, tempY = lgdict['N'][shufinds], lgdict['Y'][shufinds]
lgdict.update({'N': tempN, 'Y': tempY})
# TODO: END PRIMARY CHANGE OF THIS SCRIPT

def SetupSenegalPriors(lgdict, randseed=15):
    """Set up priors for SFP rates at nodes"""
    numTN, numSN = lgdict['TNnum'], lgdict['SNnum']
    # All SNs are `Moderate'
    SNpriorMean = np.repeat(spsp.logit(0.1), numSN)
    # TNs are randomly assigned risk, such that 5% are in the 1st and 7th levels, 10% are in the 2nd and 6th levels,
    #   20% are in the 3rd and 5th levels, and 30% are in the 4th level
    np.random.seed(randseed)
    tempCategs = np.random.multinomial(n=1, pvals=[0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05], size=numTN)
    riskMeans = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25]
    randriskinds = np.mod(np.where(tempCategs.flatten() == 1), len(riskMeans))[0]
    TNpriorMean = spsp.logit(np.array([riskMeans[randriskinds[i]] for i in range(numTN)]))
    # Concatenate prior means
    priorMean = np.concatenate((SNpriorMean, TNpriorMean))
    TNvar, SNvar = 2., 3.  # Variances for use with prior; supply nodes are wider due to unknown risk assessments
    priorCovar = np.diag(np.concatenate((np.repeat(SNvar, numSN), np.repeat(TNvar, numTN))))
    priorObj = prior_normal_assort(priorMean, priorCovar)
    lgdict['prior'] = priorObj
    return

# Set up priors for SFP rates at nodes

# TODO: Different seed for prior
SetupSenegalPriors(lgdict, randseed=17)

# Use this function to identify good choice of Madapt
def GetMCMCTracePlots(lgdict, numburnindraws=2000, numdraws=10000):
    """
    Provides a grid of trace plots across all nodes for numdraws draws of the corresponding SFP rates
    """
    # Generate MCMC draws
    templgdict = lgdict.copy()
    templgdict['MCMCdict'].update({'Madapt':numburnindraws, 'numPostSamples': numdraws})
    templgdict = methods.GeneratePostSamples(templgdict, maxTime=5000)
    # Make a grid of subplots
    numTN, numSN = lgdict['TNnum'], lgdict['SNnum']
    dim1 = int(np.ceil(np.sqrt(numTN + numSN)))
    dim2 = int(np.ceil((numTN + numSN) / dim1))

    plotrownum, plotcolnum = 4, 4
    numloops = int(np.ceil((numTN + numSN) / (plotrownum * plotcolnum)))

    currnodeind = 0

    for currloop in range(numloops):
        fig, ax = plt.subplots(nrows=plotrownum, ncols=plotcolnum, figsize=(10,10))
        for row in ax:
            for col in row:
                if currnodeind < numTN + numSN:
                    col.plot(templgdict['postSamples'][:, currnodeind], linewidth=0.5)
                    col.title.set_text('Node ' + str(currnodeind))
                    col.xaxis.set_major_locator(matplotlib.ticker.NullLocator())
                    col.yaxis.set_major_locator(matplotlib.ticker.NullLocator())
                    currnodeind += 1
        plt.tight_layout()
        plt.show()

    return
#methods.GetMCMCTracePlots(lgdict, numburnindraws=1000, numdraws=1000)

# Set up MCMC
lgdict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 1000, 'delta': 0.4}

# Generate batch of MCMC samples
def GenerateMCMCBatch(lgdict, batchsize, filedest):
    """Generates a batch of MCMC draws and saves it to the specified file destination"""
    lgdict['numPostSamples'] = batchsize
    lgdict = methods.GeneratePostSamples(lgdict, maxTime=5000)
    np.save(filedest, lgdict['postSamples'])
    return
# GenerateMCMCBatch(lgdict, 5000, 300, os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws_shuf1_1'))

def RetrieveMCMCBatches(lgdict, numbatches, filedest_leadstring):
    """Adds previously generated MCMC draws to lgdict, using the file destination marked by filedest_leadstring"""
    tempobj = np.load(filedest_leadstring + '1.npy')
    for drawgroupind in range(2, numbatches+1):
        newobj = np.load(filedest_leadstring + str(drawgroupind) + '.npy')
        tempobj = np.concatenate((tempobj, newobj))
    lgdict.update({'postSamples': tempobj, 'numPostSamples': tempobj.shape[0]})
    return
# Pull previously generated MCMC draws
RetrieveMCMCBatches(lgdict, 20, os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws_shuf1_'))
# util.plotPostSamples(lgdict, 'int90')

def AddBootstrapQ(lgdict, numboot, randseed):
    """Add bootstrap-sampled sourcing vectors for unvisited test nodes"""

    numvisitedTNs = np.count_nonzero(np.sum(lgdict['Q'], axis=1))
    SNprobs = np.sum(lgdict['N'], axis=0) / np.sum(lgdict['N'])
    np.random.seed(randseed)
    Qvecs = np.random.multinomial(numboot, SNprobs, size=lgdict['TNnum'] - numvisitedTNs) / numboot
    Qindcount = 0
    tempQ = lgdict['Q'].copy()
    for i in range(tempQ.shape[0]):
        if lgdict['Q'][i].sum() == 0:
            tempQ[i] = Qvecs[Qindcount]
            Qindcount += 1
    lgdict.update({'Q': tempQ})
    return
# Add boostrap-sampled sourcing vectors for non-tested test nodes
AddBootstrapQ(lgdict, numboot=20, randseed=44)

# Loss specification
paramdict = lf.build_diffscore_checkrisk_dict(scoreunderestwt=5., riskthreshold=0.15, riskslope=0.6,
                                              marketvec=np.ones(numTN + numSN))

def SetupParameterDictionary(paramdict, numtruthdraws, numdatadraws, randseed):
    """Sets up parameter dictionary with desired truth and data draws"""
    np.random.seed(randseed)
    truthdraws, datadraws = util.distribute_truthdata_draws(lgdict['postSamples'], numtruthdraws, numdatadraws)
    paramdict.update({'truthdraws': truthdraws, 'datadraws': datadraws})
    paramdict.update({'baseloss': sampf.baseloss(paramdict['truthdraws'], paramdict)})
    return
# Set up parameter dictionary
SetupParameterDictionary(paramdict, 100000, 300, randseed=56)
util.print_param_checks(paramdict)  # Check of used parameters

# Non-importance sampling estimate of utility
def getUtilityEstimate(n, lgdict, paramdict, zlevel=0.95):
    """
    Return a utility estimate average and confidence interval for allocation array n
    """
    testnum = int(np.sum(n))
    des = n/testnum
    currlosslist = sampf.sampling_plan_loss_list(des, testnum, lgdict, paramdict)
    currloss_avg, currloss_CI = sampf.process_loss_list(currlosslist, zlevel=zlevel)
    return paramdict['baseloss'] - currloss_avg, (paramdict['baseloss']-currloss_CI[1], paramdict['baseloss']-currloss_CI[0])

# For identifying benchmark allocations
def FindTSPPathForGivenNodes(reglist, f_reg):
    """
    Returns an sequence of indices corresponding to the shortest path through all indices, per the traversal costs
    featured in f_reg; uses brute force, so DO NOT use with lists larger than 10 elements or so
    Uses first index as the HQ region, and assumes all paths must start and end at this region
    """
    HQind = reglist[0]
    nonHQindlist = reglist[1:]
    permutlist = list(itertools.permutations(nonHQindlist))
    currbestcost = np.inf
    currbesttup = 0
    for permuttuple in permutlist:
        currind = HQind
        currpermutcost = 0
        for ind in permuttuple:
            currpermutcost += f_reg[currind, ind]
            currind = ind
        currpermutcost += f_reg[currind,HQind]
        if currpermutcost < currbestcost:
            currbestcost = currpermutcost
            currbesttup = permuttuple
    besttuplist = [currbesttup[i] for i in range(len(currbesttup))]
    besttuplist.insert(0,HQind)
    return besttuplist, currbestcost

def GetAllocVecFromLists(distNames, distList, allocList):
    """Function for generating allocation vector for benchmarks, only using names and a list of test levels"""
    numDist = len(distNames)
    n = np.zeros(numDist)
    for distElem, dist in enumerate(distList):
        distind = distNames.index(dist)
        n[distind] = allocList[distElem]
    return n

# Orienteering parameters
batchcost, batchsize, B, ctest = 0, 700, 700, 2
batchsize = B
bigM = B*ctest

dept_df_sort = dept_df.sort_values('Department')

FTEcostperday = 200
f_dept = np.array(dept_df_sort['DeptFixedCostDays'].tolist())*FTEcostperday
f_reg = np.array(regcost_mat)*FTEcostperday

##########################
##########################
# Calculate utility for candidates and benchmarks
##########################
##########################

util.print_param_checks(paramdict)

######
# B=700
######

# LeastVisited
reglist_LeastVisited = [0, regNames.index('Thies'), regNames.index('Diourbel'), regNames.index('Fatick'),
                        regNames.index('Kaolack')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_LeastVisited, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

deptList_LeastVisited = ['Dakar', 'Guediawaye', 'Keur Massar', 'Rufisque', 'Mbour', 'Tivaoune', 'Guinguineo',
                         'Diourbel', 'Foundiougne', 'Gossas']
allocList_LeastVisited = [4, 4, 4, 4, 4, 4, 3, 3, 3, 3]
n_LeastVisited = GetAllocVecFromLists(deptNames, deptList_LeastVisited, allocList_LeastVisited)
util_LeastVisited_unif, util_LeastVisited_unif_CI = sampf.getImportanceUtilityEstimate(n_LeastVisited, lgdict,
                                                                paramdict, numimportdraws=50000)
print('LeastVisited:',util_LeastVisited_unif, util_LeastVisited_unif_CI)
# 3-APR
# 0.7278474498511986 (0.7147762719858832, 0.7409186277165141)
# 0.7730593679934668 (0.7605848548689256, 0.7855338811180079)

# MostSFPs
reglist_MostSFPs = [0, regNames.index('Thies'), regNames.index('Diourbel'), regNames.index('Kaolack'),
                    regNames.index('Louga')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MostSFPs, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

deptList_MostSFPs = ['Thies', 'Kebemer', 'Kaolack', 'Nioro du Rip', 'Bambey', 'Mbacke']
allocList_MostSFPs_unif = [6, 6, 5, 5, 5, 5]
n_MostSFPs_unif = GetAllocVecFromLists(deptNames, deptList_MostSFPs, allocList_MostSFPs_unif)
util_MostSFPs_unif, util_MostSFPs_unif_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (uniform):',util_MostSFPs_unif, util_MostSFPs_unif_CI)
# 3-APR
# 0.19979340319738448 (0.1941252962122828, 0.20546151018248615)
# 0.1745024941571245 (0.16872464940383658, 0.1802803389104124)

allocList_MostSFPs_wtd = [7, 5, 7, 5, 4, 4]
n_MostSFPs_wtd = GetAllocVecFromLists(deptNames, deptList_MostSFPs, allocList_MostSFPs_wtd)
util_MostSFPs_wtd, util_MostSFPs_wtd_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (weighted):',util_MostSFPs_wtd, util_MostSFPs_wtd_CI)
# 3-APR
# 0.1874164826813356 (0.18149126731374388, 0.1933416980489273)
# 0.1884238005633918 (0.1826504831433926, 0.194197117983391)

# MoreDistricts (uniform)
deptList_MoreDist_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke']
allocList_MoreDist_unif = [9, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8]
n_MoreDist_unif = GetAllocVecFromLists(deptNames, deptList_MoreDist_unif, allocList_MoreDist_unif)
util_MoreDist_unif, util_MoreDist_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (uniform):', util_MoreDist_unif, util_MoreDist_unif_CI)
# 3-APR
# 1.097901374992679 (1.0883369471734898, 1.107465802811868)
# 1.100621111946376 (1.0904241829061174, 1.1108180409866346)

# MoreDistricts (weighted)
deptList_MoreDist_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke']
allocList_MoreDist_unif = [10, 10, 10, 6, 10, 6, 10, 10, 10, 5, 5]
n_MoreDist_unif = GetAllocVecFromLists(deptNames, deptList_MoreDist_unif, allocList_MoreDist_unif)
util_MoreDist_unif, util_MoreDist_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (weighted):', util_MoreDist_unif, util_MoreDist_unif_CI)
# 3-APR
# 1.1499090127184903 (1.1405389375620807, 1.1592790878749)
# 1.1692559434343668 (1.160178594480767, 1.1783332923879666)

# MoreTests (uniform)
deptList_MoreTests_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune']
allocList_MoreTests_unif = [22, 22, 22, 22, 22, 22, 22, 22]
n_MoreTests_unif = GetAllocVecFromLists(deptNames, deptList_MoreTests_unif, allocList_MoreTests_unif)
util_MoreTests_unif, util_MoreTests_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostTests (uniform):', util_MoreTests_unif, util_MoreTests_unif_CI)
# 3-APR
# 1.2634860610115375 (1.2549002545907246, 1.2720718674323503)
# 1.2801337489084634 (1.2708842065197103, 1.2893832912972165)

# MoreTests (weighted)
deptList_MoreTests_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune']
allocList_MoreTests_wtd = [25, 25, 25, 13, 25, 13, 25, 25]
n_MoreTests_wtd = GetAllocVecFromLists(deptNames, deptList_MoreTests_wtd, allocList_MoreTests_wtd)
util_MoreTests_wtd, util_MoreTests_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreTests (weighted):', util_MoreTests_wtd, util_MoreTests_wtd_CI)
# 3-APR
# 1.3578140938057182 (1.3491147209875933, 1.366513466623843)
# 1.3317990083561195 (1.3236876668685973, 1.3399103498436418)

######
# B=1400
######

# LeastVisited
reglist_LeastVisited = [0, regNames.index('Thies'), regNames.index('Diourbel'), regNames.index('Fatick'),
                        regNames.index('Kaolack'), regNames.index('Kaffrine'), regNames.index('Saint-Louis'),
                        regNames.index('Matam')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_LeastVisited, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

deptList_LeastVisited = ['Dakar', 'Guediawaye', 'Keur Massar', 'Rufisque', 'Mbour', 'Tivaoune', 'Guinguineo',
                         'Kaffrine', 'Birkilane', 'Koungheul', 'Malem Hoddar', 'Diourbel', 'Podor',
                         'Foundiougne', 'Gossas', 'Ranerou Ferlo']
allocList_LeastVisited = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3]
n_LeastVisited = GetAllocVecFromLists(deptNames, deptList_LeastVisited, allocList_LeastVisited)
util_LeastVisited_unif, util_LeastVisited_unif_CI = sampf.getImportanceUtilityEstimate(n_LeastVisited, lgdict,
                                                                paramdict, numimportdraws=50000)
print('LeastVisited:',util_LeastVisited_unif, util_LeastVisited_unif_CI)
# 3-APR
# 1.320567052079845 (1.305219961370975, 1.335914142788715)
# 1.3066436075231245 (1.2918677410837915, 1.3214194739624574)

# MostSFPs (uniform)
reglist_MostSFPs = [0, regNames.index('Thies'), regNames.index('Diourbel'), regNames.index('Kaolack'),
                    regNames.index('Louga'), regNames.index('Saint-Louis'), regNames.index('Tambacounda')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MostSFPs, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

deptList_MostSFPs_unif = ['Thies', 'Kebemer', 'Bakel', 'Kaolack', 'Nioro du Rip', 'Bambey', 'Mbacke',
                          'Saint-Louis', 'Dagana']
allocList_MostSFPs_unif = [9, 9, 8, 8, 8, 8, 8, 8, 8]
n_MostSFPs_unif = GetAllocVecFromLists(deptNames, deptList_MostSFPs_unif, allocList_MostSFPs_unif)
util_MostSFPs_unif, util_MostSFPs_unif_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (unform):',util_MostSFPs_unif, util_MostSFPs_unif_CI)
# 2-APR
# 0.3303070425714889 (0.32320823354960737, 0.33740585159337044)
# 0.3430698551334377 (0.3359789629780199, 0.3501607472888555)

# MostSFPs (weighted)
deptList_MostSFPs_wtd = ['Thies', 'Kebemer', 'Bakel', 'Kaolack', 'Nioro du Rip', 'Bambey', 'Mbacke',
                          'Saint-Louis', 'Dagana']
allocList_MostSFPs_wtd = [10, 6, 7, 9, 5, 6, 6, 16, 9]
n_MostSFPs_wtd = GetAllocVecFromLists(deptNames, deptList_MostSFPs_wtd, allocList_MostSFPs_wtd)
util_MostSFPs_wtd, util_MostSFPs_wtd_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (weighted):', util_MostSFPs_wtd, util_MostSFPs_wtd_CI)
# 2-APR
# 0.3657066138154761 (0.3590590841139001, 0.3723541435170521)
# 0.3373247622433002 (0.33071009578692134, 0.3439394286996791)

# MoreDistricts (uniform)
deptList_MoreDist_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Kaolack', 'Guinguineo', 'Nioro du Rip', 'Kaffrine',
                          'Birkilane', 'Koungheul', 'Malem Hoddar',  'Diourbel', 'Bambey', 'Mbacke',
                          'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreDist_unif = [8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 7, 7]
n_MoreDist_unif = GetAllocVecFromLists(deptNames, deptList_MoreDist_unif, allocList_MoreDist_unif)
util_MoreDist_unif, util_MoreDist_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (uniform):', util_MoreDist_unif, util_MoreDist_unif_CI)
# 2-APR
# 1.924807917228767 (1.9127570077576923, 1.9368588266998419)
# 1.899272363954779 (1.8867183172416269, 1.9118264106679312)

# MoreDistricts (weighted)
deptList_MoreDist_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Kaolack', 'Guinguineo', 'Nioro du Rip', 'Kaffrine',
                          'Birkilane', 'Koungheul', 'Malem Hoddar',  'Diourbel', 'Bambey', 'Mbacke',
                          'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreDist_wtd = [9, 9, 9, 5, 9, 5, 9, 9, 5, 9, 4, 9, 9, 9, 9, 9, 4, 4, 5, 9, 9]
n_MoreDist_wtd = GetAllocVecFromLists(deptNames, deptList_MoreDist_wtd, allocList_MoreDist_wtd)
util_MoreDist_wtd, util_MoreDist_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (weighted):', util_MoreDist_wtd, util_MoreDist_wtd_CI)
# 2-APR
# 1.9651710125263655 (1.9539074988060658, 1.9764345262466652)
# 1.9675294800407013 (1.955550487903265, 1.9795084721781375)

# MoreTests (uniform)
deptList_MoreTests_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies', 'Mbour',
                           'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke', 'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreTests_unif = [27, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26]
n_MoreTests_unif = GetAllocVecFromLists(deptNames, deptList_MoreTests_unif, allocList_MoreTests_unif)
util_MoreTests_unif, util_MoreTests_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostTests (uniform):', util_MoreTests_unif, util_MoreTests_unif_CI)
# 2-APR
# 2.230707381240432 (2.221698573185467, 2.2397161892953967)
# 2.2395853657537224 (2.228983114316108, 2.2501876171913366)

# MoreTests (weighted)
deptList_MoreTests_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies', 'Mbour',
                           'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke', 'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreTests_wtd = [32, 32, 32, 15, 32, 15, 32, 32, 32, 14, 14, 16, 32, 32]
n_MoreTests_wtd = GetAllocVecFromLists(deptNames, deptList_MoreTests_wtd, allocList_MoreTests_wtd)
util_MoreTests_wtd, util_MoreTests_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreTests (weighted):', util_MoreTests_wtd, util_MoreTests_wtd_CI)
# 2-APR
# 2.2692339314785706 (2.259691080220824, 2.2787767827363172)
# 2.260540916285702 (2.2515382871631626, 2.2695435454082418)

##########################
##########################
# END calculate utility for candidates and benchmarks
##########################
##########################


##################
##################
# Now set up functions for constraints and variables of our program
##################
##################
optparamdict = {'batchcost':batchcost, 'budget':B, 'pertestcost':ctest, 'Mconstant':bigM, 'batchsize':batchsize,
                'deptfixedcostvec':f_dept, 'arcfixedcostmat': f_reg, 'reghqname':'Dakar', 'reghqind':0,
                'deptnames':deptNames, 'regnames':regNames, 'dept_df':dept_df_sort}

# What are the upper bounds for our allocation variables?
deptallocbds = opf.GetUpperBounds(optparamdict)
# Lower upper bounds to maximum of observed prior tests at any district
maxpriortests = int(np.max(np.sum(lgdict['N'],axis=1)))
deptallocbds = np.array([min(deptallocbds[i], maxpriortests) for i in range(deptallocbds.shape[0])])

print(deptNames[np.argmin(deptallocbds)], min(deptallocbds))
print(deptNames[np.argmax(deptallocbds)], max(deptallocbds))

def GetInterpEvals(deptnames, deptallocbds, paramdict, lgdict, csvpath):
    """
    Evaluate utility at 1 test and deptallocbds tests for each district, and save the resulting data frame as a CSV to
    csvpath. NOTE: This function may take a long time to run, depending on the number of districts and the parameters
    contained in paramdict.
    """
    numTN = lgdict['TNnum']
    util_lo, util_lo_CI = [], []
    util_hi, util_hi_CI = [], []
    for i in range(len(deptnames)):
        currbd = int(deptallocbds[i])
        print('Getting utility for ' + deptnames[i] + ', at 1 test...')
        n = np.zeros(numTN)
        n[i] = 1
        currlo, currlo_CI = getUtilityEstimate(n, lgdict, paramdict)
        print(currlo, currlo_CI)
        util_lo.append(currlo)
        util_lo_CI.append(currlo_CI)
        print('Getting utility for ' + deptnames[i] + ', at ' + str(currbd) + ' tests...')
        n[i] = currbd
        # Use the importance method for the upper allocation bound
        currhi, currhi_CI = sampf.getImportanceUtilityEstimate(n, lgdict, paramdict, numimportdraws=50000)
        print(currhi, currhi_CI)
        util_hi.append(currhi)
        util_hi_CI.append(currhi_CI)

    util_df = pd.DataFrame({'DeptName': deptnames, 'Bounds': deptallocbds, 'Util_lo': util_lo, 'Util_lo_CI': util_lo_CI,
                            'Util_hi': util_hi, 'Util_hi_CI': util_hi_CI})
    util_df.to_csv(csvpath, index=False)
    return

# GetInterpEvals(deptnames, deptallocbds, paramdict, lgdict, os.path.join('operationalizedsamplingplans', 'csv_utility', 'utilevals_BASE.csv'))

# Retrieve previously generated interpolation points
util_df = pd.read_csv(os.path.join('operationalizedsamplingplans', 'csv_utility', 'utilevals_BASE.csv'))
# todo: KEY CHANGE HERE, REARRANGING THE UTILITIES ASSOCIATED WITH EACH DISTRICT
temp_df = util_df.copy()
for ind in range(numTN):
    temp_df.at[ind, 'Bounds'] = util_df.at[shufinds[ind], 'Bounds']
    temp_df.at[ind, 'Util_lo'] = util_df.at[shufinds[ind], 'Util_lo']
    temp_df.at[ind, 'Util_lo_CI'] = util_df.at[shufinds[ind], 'Util_lo_CI']
    temp_df.at[ind, 'Util_hi'] = util_df.at[shufinds[ind], 'Util_hi']
    temp_df.at[ind, 'Util_hi_CI'] = util_df.at[shufinds[ind], 'Util_hi_CI']
util_df = temp_df.copy()
# todo: END KEY CHANGE OF SCRIPT

### GENERATE PATHS FOR CASE STUDY ###
# What is the upper bound on the number of regions in any feasible tour that uses at least one test?
maxregnum = opf.GetSubtourMaxCardinality(optparamdict=optparamdict)
print('Number of regions in any feasible path:',maxregnum)

mastlist = []
for regamt in range(1, maxregnum):
    mastlist = mastlist + list(itertools.combinations(np.arange(1,numReg).tolist(), regamt))
print('Number of feasible region combinations:',len(mastlist))

def GenerateNondominatedPaths(mastlist, optparamdict, csvpath):
    """
    Stores a data frame of non-dominated paths in a CSV file.
    """
    f_reg, deptNames, regNames = optparamdict['arcfixedcostmat'], optparamdict['deptnames'], optparamdict['regnames']
    ctest, dept_df, f_dept = optparamdict['pertestcost'], optparamdict['dept_df'], optparamdict['deptfixedcostvec']
    # For storing best sequences and their corresponding costs
    seqlist, seqcostlist = [], []
    for tup in mastlist:
        tuplist = [tup[i] for i in range(len(tup))]
        tuplist.insert(0, 0)  # Add HQind to front of list
        bestseqlist, bestseqcost = opf.FindTSPPathForGivenNodes(tuplist, f_reg)
        seqlist.append(bestseqlist)
        seqcostlist.append(bestseqcost)
    # For each path, generate a binary vector indicating if each district is accessible on that path
    # First get sorted names of accessible districts
    distaccesslist = []
    for seq in seqlist:
        currdistlist = []
        for ind in seq:
            currdist = opf.GetDeptChildren(regNames[ind], dept_df)
            currdistlist = currdistlist + currdist
        currdistlist.sort()
        distaccesslist.append(currdistlist)
    # Next translate each list of district names to binary vectors
    bindistaccessvectors = []
    for distlist in distaccesslist:
        distbinvec = [int(i in distlist) for i in deptNames]
        bindistaccessvectors.append(distbinvec)
    # Store in a data frame
    paths_df_all = pd.DataFrame({'Sequence': seqlist, 'Cost': seqcostlist, 'DistAccessBinaryVec': bindistaccessvectors})

    # Remove all paths with cost exceeding budget - min{district access} - sampletest
    paths_df = paths_df_all[paths_df_all['Cost'] < optparamdict['budget']].copy()

    # Remaining paths require at least one district and one test in each visited region
    boolevec = [True for i in range(paths_df.shape[0])]
    for i in range(paths_df.shape[0]):
        rowseq, rowcost = paths_df.iloc[i]['Sequence'], paths_df.iloc[i]['Cost']
        mindistcost = 0
        for reg in rowseq:
            if reg != 0: # Pick the least expensive district to access
                mindistcost += f_dept[[deptNames.index(x) for x in opf.GetDeptChildren(regNames[reg], dept_df)]].min()
        # Add district costs, testing costs, and path cost
        mincost = mindistcost + (len(rowseq) - 1) * ctest + rowcost
        if mincost > B:
            boolevec[i] = False

    paths_df = paths_df[boolevec]

    paths_df.to_csv(csvpath, index=False)

    return

# GenerateNondominatedPaths(mastlist, optparamdict, os.path.join('operationalizedsamplingplans', 'csv_paths', 'paths_BASE.csv'))

# Load previously generated paths data frame
paths_df = pd.read_csv(os.path.join('operationalizedsamplingplans', 'csv_paths', 'paths_BASE.csv'))

def GetPathSequenceAndCost(paths_df):
    """Retrieves optimization-ready lists pertaining to path sequences and costs"""
    seqlist = paths_df['Sequence'].copy()
    seqcostlist = paths_df['Cost'].copy()
    bindistaccessvectors = np.array(paths_df['DistAccessBinaryVec'].tolist())
    bindistaccessvectors = np.array([eval(x) for x in bindistaccessvectors])
    seqlist = seqlist.reset_index()
    seqlist = seqlist.drop(columns='index')
    seqcostlist = seqcostlist.reset_index()
    seqcostlist = seqcostlist.drop(columns='index')

    return seqlist, seqcostlist, bindistaccessvectors

seqlist_trim, seqcostlist_trim, bindistaccessvectors_trim = GetPathSequenceAndCost(paths_df)

# Build interpolated objective slopes
def GetInterpVectors(util_df):
    """Build needed interpolation vectors for use with relaxed program"""
    lvec, juncvec, m1vec, m2vec, bds, lovals, hivals = [], [], [], [], [], [], []
    for ind in range(util_df.shape[0]):
        row = util_df.iloc[ind]
        currBound, loval, hival = row['Bounds'], row['Util_lo'], row['Util_hi']
        # Get interpolation values
        _, _, l, k, m1, m2 = opf.GetTriangleInterpolation([0, 1, currBound], [0, loval, hival])
        lvec.append(l)
        juncvec.append(k)
        m1vec.append(m1)
        m2vec.append(m2)
        bds.append(currBound)
        lovals.append(loval)
        hivals.append(hival)

    return lvec, juncvec, m1vec, m2vec, bds, lovals, hivals

# Get vectors of zero intercepts, junctures, and interpolation slopes for each of our Utilde evals at each district
lvec, juncvec, m1vec, m2vec, bds, lovals, hivals = GetInterpVectors(util_df)

def PlotInterpHist(lvec, juncvec, m1vec, m2vec, bds):
    """Make histograms of interpolation values"""
    # What is the curvature, kappa, for our estimates?
    kappavec = [1 - m2vec[i] / m1vec[i] for i in range(len(m2vec))]
    plt.hist(kappavec)
    plt.title('Histogram of $\kappa$ curvature at each district')
    plt.show()

    # Make histograms of our interpolated values
    plt.hist(lvec, color='darkorange', density=True)
    plt.title("Histogram of interpolation intercepts\n($l$ values)",
              fontsize=14)
    plt.xlabel(r'$l$', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.show()

    # interpolated junctures
    plt.hist(juncvec, color='darkgreen', density=True)
    plt.title('Histogram of interpolation slope junctures\n($j$ values)',
              fontsize=14)
    plt.xlabel(r'$j$', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.show()

    # interpolated junctures, as percentage of upper bound
    juncvecperc = [juncvec[i] / bds[i] for i in range(len(juncvec))]
    plt.hist(juncvecperc, color='darkgreen', density=True)
    plt.title('Histogram of interpolation junctures vs. allocation bounds\n($h_d/' + r'n^{max}_d$ values)',
              fontsize=14)
    plt.xlabel(r'$h_d/n^{max}_d$', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.show()

    plt.hist(m1vec, color='purple', density=True)
    plt.title('Histogram of first interpolation slopes\n($m^{(1)}$ values)'
              , fontsize=14)
    plt.xlabel('$m^{(1)}$', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.xlim([0, np.max(m1vec)*1.05])
    plt.show()

    plt.hist(m2vec, color='orchid', density=True)
    plt.title('Histogram of second interpolation slopes\n($m^{(2)}$ values)'
              , fontsize=14)
    plt.xlabel('$m^{(2)}$', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    plt.xlim([0, np.max(m1vec)*1.05])
    plt.show()

    return

#PlotInterpHist(lvec, juncvec, m1vec, m2vec, bds)

###################################
###################################
# MAIN OPTIMIZATION BLOCK
###################################
###################################
# We construct our various program vectors and matrices per the scipy standards
numPath = paths_df.shape[0]

# todo: Variable vectors are in form (z, n, x) [districts, allocations, paths]
# Variable bounds
def GetVarBds(numTN, numPath, juncvec, util_df):
    lbounds = np.concatenate((np.zeros(numTN * 3), np.zeros(numPath)))
    ubounds = np.concatenate((np.ones(numTN),
                              np.array([juncvec[i] - 1 for i in range(numTN)]),
                              np.array(util_df['Bounds'].tolist()) - np.array([juncvec[i] - 1 for i in range(numTN)]),
                              np.ones(numPath)))
    return spo.Bounds(lbounds, ubounds)

optbounds = GetVarBds(numTN, numPath, juncvec, util_df)

# Objective vector
def GetObjective(lvec, m1vec, m2vec, numPath):
    """Negative-ed as milp requires minimization"""
    return -np.concatenate((np.array(lvec), np.array(m1vec), np.array(m2vec), np.zeros(numPath)))

optobjvec = GetObjective(lvec, m1vec, m2vec, numPath)

# Constraints
def GetConstraints(optparamdict, juncvec, seqcostlist, bindistaccessvectors):
    numTN, B, ctest = len(optparamdict['deptnames']), optparamdict['budget'], optparamdict['pertestcost']
    f_dept, bigM = optparamdict['deptfixedcostvec'], optparamdict['Mconstant']
    # Build lower and upper inequality values
    optconstrlower = np.concatenate(( np.ones(numTN*4+1) * -np.inf, np.array([1])))
    optconstrupper = np.concatenate((np.array([B]), np.zeros(numTN*2), np.array(juncvec), np.zeros(numTN), np.array([1])))
    # Build A matrix, from left to right
    # Build z district binaries first
    optconstraintmat1 = np.vstack((f_dept, -bigM * np.identity(numTN), np.identity(numTN), 0 * np.identity(numTN),
                                   np.identity(numTN), np.zeros(numTN)))
    # n^' matrices
    optconstraintmat2 = np.vstack((ctest * np.ones(numTN), np.identity(numTN), -np.identity(numTN), np.identity(numTN),
                                   0 * np.identity(numTN), np.zeros(numTN)))
    # n^'' matrices
    optconstraintmat3 = np.vstack((ctest * np.ones(numTN), np.identity(numTN), -np.identity(numTN),
                                   0 * np.identity(numTN), 0 * np.identity(numTN), np.zeros(numTN)))
    # path matrices
    optconstraintmat4 = np.vstack((np.array(seqcostlist).T, np.zeros((numTN * 3, numPath)),
                                   (-bindistaccessvectors).T, np.ones(numPath)))

    optconstraintmat = np.hstack((optconstraintmat1, optconstraintmat2, optconstraintmat3, optconstraintmat4))
    return spo.LinearConstraint(optconstraintmat, optconstrlower, optconstrupper)

optconstraints = GetConstraints(optparamdict, juncvec, seqcostlist_trim, bindistaccessvectors_trim)

def GetIntegrality(optobjvec):
    return np.ones_like(optobjvec)

# Define integrality for all variables
optintegrality = GetIntegrality(optobjvec)

# Solve
spoOutput = milp(c=optobjvec, constraints=optconstraints, integrality=optintegrality, bounds=optbounds)
initsoln_700, initsoln_700_obj  = spoOutput.x, spoOutput.fun*-1
# 9-APR-24: 1.516004756776774
# Convert solution to legible format
opf.scipytoallocation(initsoln_700, deptNames, regNames, seqlist_trim, eliminateZeros=True)
print('Path cost: '+ str(np.sum(np.array(paths_df['Cost'])*initsoln_700[numTN*3:])))

def GetAllocationFromOpt(soln, numTN):
    """Turn optimization solution into an allocation whose utility can be evaluated"""
    n1, n2 = soln[numTN:numTN * 2], soln[numTN * 2:numTN * 3]
    return n1 + n2

init_n_700 = GetAllocationFromOpt(initsoln_700, numTN)

# todo: COMP2 Evaluate utility with importance sampling
initsoln_700_util, initsoln_700_util_CI = sampf.getImportanceUtilityEstimate(init_n_700, lgdict, paramdict, numimportdraws=50000)
# 9-APR-24:
# (1.1110026350000766, (1.0994794149037226, 1.1225258550964305))

##########################
# Generate additional candidates for 700 budget
##########################
# Solve IP-RP while setting each path to 1
def GetConstraintsWithPathCut(numVar, numTN, pathInd):
    """
    Returns constraint object for use with scipy optimize, where the path variable must be 1 at pathInd
    """
    newconstraintmat = np.zeros((1, numVar)) # size of new constraints matrix
    newconstraintmat[0, numTN*3 + pathInd] = 1.
    return spo.LinearConstraint(newconstraintmat, np.ones(1), np.ones(1))

# Identify candidate paths with sufficiently high IP-RP objectives
def GetEligiblePathInds(paths_df, distNames, regNames, opt_obj, opt_constr, opt_integ, opt_bds, f_dist, LB,
                        seqlist_trim_df, printUpdate=True):
    """Returns list of path indices for paths with upper bounds above the current lower bound"""
    numPath = paths_df.shape[0]
    numTN = len(distNames)
    # Dataframe of paths and their IP-RP objectives
    candpaths_df = paths_df.copy()
    candpaths_df.insert(3, 'IPRPobj', np.zeros(numPath).tolist(), True)
    candpaths_df.insert(4, 'Allocation', np.zeros((numPath,numTN)).tolist(), True)
    candpaths_df.insert(5, 'DistCost', np.zeros(numPath).tolist(), True)  # Add column to store RP district costs
    candpaths_df.insert(6, 'Uoracle', np.zeros(numPath).tolist(), True)  # Add column for oracle evals
    candpaths_df.insert(7, 'UoracleCIlo', np.zeros(numPath).tolist(), True)  # Add column for oracle eval CIs
    candpaths_df.insert(8, 'UoracleCIhi', np.zeros(numPath).tolist(), True)  # Add column for oracle eval CIs
    # IP-RP for each path
    for pathind in range(numPath):
        pathconstraint = GetConstraintsWithPathCut(numPath + numTN * 3, numTN, pathind)
        curr_spoOutput = milp(c=opt_obj, constraints=(opt_constr, pathconstraint),
                              integrality=opt_integ, bounds=opt_bds)
        candpaths_df.at[pathind, 'IPRPobj'] = curr_spoOutput.fun * -1
        candpaths_df.at[pathind, 'Allocation'] = GetAllocationFromOpt(curr_spoOutput.x, numTN)
        candpaths_df.at[pathind, 'DistCost'] = (curr_spoOutput.x[:numTN] * f_dist).sum()
        if curr_spoOutput.fun * -1 > LB:
            opf.scipytoallocation(np.round(curr_spoOutput.x), distNames, regNames, seqlist_trim_df, True)
            if printUpdate:
                print('Path ' + str(pathind) + ' cost: ' + str(candpaths_df.iloc[pathind, 1]))
                print('Path ' + str(pathind) + ' RP utility: ' + str(candpaths_df.iloc[pathind, 3]))
    return candpaths_df

# candpaths_df_700 = GetEligiblePathInds(paths_df, deptNames, regNames, optobjvec, optconstraints, optintegrality,
#                                       optbounds, f_dept, initsoln_700_util, seqlist_trim, printUpdate=True)

# Save to avoid generating later
# candpaths_df_700.to_pickle(os.path.join('operationalizedsamplingplans', 'pkl_paths', 'candpaths_df_700.pkl'))
candpaths_df_700 = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'pkl_paths', 'candpaths_df_700.pkl'))

def EvaluateCandidateUtility(candpaths_df, LB, lgdict, paramdict):
    for pathind in range(candpaths_df.shape[0]):
        # Evaluate the IP-RP allocation for each designated eligible path
        if candpaths_df.at[pathind, 'IPRPobj'] > LB:
            print('Evaluating utility for path ' + candpaths_df.at[pathind, 'Sequence'])
            candsoln_util, candsoln_util_CI = sampf.getImportanceUtilityEstimate(candpaths_df.at[pathind, 'Allocation'], lgdict,
                                                                       paramdict, numimportdraws=50000)
            candpaths_df.at[pathind, 'Uoracle'] = candsoln_util
            candpaths_df.at[pathind, 'UoracleCIlo'] = candsoln_util_CI[0]
            candpaths_df.at[pathind, 'UoracleCIhi'] = candsoln_util_CI[1]
    return
# todo: COMP2 Evaluate utility with importance sampling
EvaluateCandidateUtility(candpaths_df_700, initsoln_700_util, lgdict, paramdict)


###################
###################
# Update to hi budget
###################
###################
B = 1400
bigM = B*ctest

optparamdict = {'batchcost':batchcost, 'budget':B, 'pertestcost':ctest, 'Mconstant':bigM, 'batchsize':batchsize,
                'deptfixedcostvec':f_dept, 'arcfixedcostmat': f_reg, 'reghqname':'Dakar', 'reghqind':0,
                'deptnames':deptNames, 'regnames':regNames, 'dept_df':dept_df_sort}

# Retrieve previously generated interpolation points
util_df = pd.read_csv(os.path.join('operationalizedsamplingplans', 'csv_utility', 'utilevals_BASE.csv'))
# todo: KEY CHANGE HERE, REARRANGING THE UTILITIES ASSOCIATED WITH EACH DISTRICT
temp_df = util_df.copy()
for ind in range(numTN):
    temp_df.at[ind, 'Bounds'] = util_df.at[shufinds[ind], 'Bounds']
    temp_df.at[ind, 'Util_lo'] = util_df.at[shufinds[ind], 'Util_lo']
    temp_df.at[ind, 'Util_lo_CI'] = util_df.at[shufinds[ind], 'Util_lo_CI']
    temp_df.at[ind, 'Util_hi'] = util_df.at[shufinds[ind], 'Util_hi']
    temp_df.at[ind, 'Util_hi_CI'] = util_df.at[shufinds[ind], 'Util_hi_CI']
util_df = temp_df.copy()
# todo: END KEY CHANGE OF SCRIPT

maxregnum = opf.GetSubtourMaxCardinality(optparamdict=optparamdict)
# TODO: UPDATE LATER IF ANY GOOD SOLUTIONS USE 8 REGIONS; OTHERWISE TOO MANY PATHS ARE GENERATED
maxregnum = maxregnum - 1

mastlist = []
for regamt in range(1, maxregnum):
    mastlist = mastlist + list(itertools.combinations(np.arange(1,numReg).tolist(), regamt))
print('Number of feasible region combinations:',len(mastlist))

# Get the data frame of non-dominated paths
# GenerateNondominatedPaths(mastlist, optparamdict, os.path.join('operationalizedsamplingplans', 'csv_paths', 'paths_BASE_1400.csv'))
# Load previously generated paths data frame
paths_df = pd.read_csv(os.path.join('operationalizedsamplingplans', 'csv_paths', 'paths_BASE_1400.csv'))
# Get necessary path vectors for IP-RP
seqlist_trim, seqcostlist_trim, bindistaccessvectors_trim = GetPathSequenceAndCost(paths_df)
# Get interpolation vectors
lvec, juncvec, m1vec, m2vec, bds, lovals, hivals = GetInterpVectors(util_df)
# Build IP-RP
numPath = paths_df.shape[0]
optbounds, optobjvec = GetVarBds(numTN, numPath, juncvec, util_df), GetObjective(lvec, m1vec, m2vec, numPath)
optconstraints, optintegrality = GetConstraints(optparamdict, juncvec, seqcostlist_trim,
                                                bindistaccessvectors_trim), GetIntegrality(optobjvec)

spoOutput = milp(c=optobjvec, constraints=optconstraints, integrality=optintegrality, bounds=optbounds)
initsoln_1400, initsoln_1400_obj  = spoOutput.x, spoOutput.fun*-1
# 9-APR-24: 2.6770081279392812

# Convert solution to legible format
opf.scipytoallocation(initsoln_1400, deptNames, regNames, seqlist_trim, eliminateZeros=True)
print('Path cost: '+ str(np.sum(np.array(paths_df['Cost'])*initsoln_1400[numTN*3:])))

init_n_1400 = GetAllocationFromOpt(initsoln_1400, numTN)

# todo: COMP2 Evaluate utility with importance sampling
initsoln_1400_util, initsoln_1400_util_CI = sampf.getImportanceUtilityEstimate(init_n_1400, lgdict,
                                                                             paramdict, numimportdraws=50000)
# 9-APR-24:
# (2.232150933175948, (2.221701828540091, 2.2426000378118047))
