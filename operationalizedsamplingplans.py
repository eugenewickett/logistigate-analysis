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
SetupSenegalPriors(lgdict)

# Use this function to identify good choice of Madapt
def GetMCMCTracePlots(lgdict, numburnindraws=2000, numdraws=1000):
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
def GenerateMCMCBatch(lgdict, batchsize, randseed, filedest):
    """Generates a batch of MCMC draws and saves it to the specified file destination"""
    lgdict['numPostSamples'] = batchsize
    lgdict = methods.GeneratePostSamples(lgdict, maxTime=5000)
    np.save(filedest, lgdict['postSamples'])
    return
# GenerateMCMCBatch(lgdict, 5000, 300, os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws1'))

def RetrieveMCMCBatches(lgdict, numbatches, filedest_leadstring):
    """Adds previously generated MCMC draws to lgdict, using the file destination marked by filedest_leadstring"""
    tempobj = np.load(filedest_leadstring + '1.npy')
    for drawgroupind in range(2, numbatches+1):
        newobj = np.load(filedest_leadstring + str(drawgroupind) + '.npy')
        tempobj = np.concatenate((tempobj, newobj))
    lgdict.update({'postSamples': tempobj, 'numPostSamples': tempobj.shape[0]})
    return
# Pull previously generated MCMC draws
RetrieveMCMCBatches(lgdict, 20, os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws'))
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


##########################
##########################
# Calculate utility for candidates and benchmarks
##########################
##########################
def GetAllocVecFromLists(distNames, distList, allocList):
    """Function for generating allocation vector for benchmarks, only using names and a list of test levels"""
    numDist = len(distNames)
    n = np.zeros(numDist)
    for distElem, dist in enumerate(distList):
        distind = distNames.index(dist)
        n[distind] = allocList[distElem]
    return n

util.print_param_checks(paramdict)

### Benchmarks ###
# IP-RP allocation
deptList_IPRP = ['Dakar', 'Keur Massar', 'Pikine', 'Diourbel', 'Bambey', 'Mbacke', 'Fatick', 'Foundiougne', 'Gossas']
allocList_IPRP = [42, 21, 7, 9, 10, 7, 11, 10, 9]
n_IPRP = GetAllocVecFromLists(deptNames, deptList_IPRP, allocList_IPRP)
util_IPRP, util_IPRP_CI = sampf.getImportanceUtilityEstimate(n_IPRP, lgdict, paramdict,
                                                             numimportdraws=50000)
print('IPRP:',util_IPRP, util_IPRP_CI)
# 1-APR
# 1.3243255437720034 (1.316541769717496, 1.3321093178265109); 30k imp draws
# 1.2904046058091616 (1.2813122416196538, 1.2994969699986694); 30k imp draws
# 1.2760568950591367 (1.2660982924974853, 1.286015497620788); 40k imp draws
# 1.2611624389549885 (1.2501537348147433, 1.2721711430952336) ; 40k imp draws
# 1.2797496694612303 (1.2687891323652405, 1.29071020655722);  50k imp draws
# 1.2545274151656152 (1.2430224985475427, 1.2660323317836877); 50k imp draws
# 1.2744392537611215 (1.2635862899152848, 1.2852922176069583); 50k imp draws

# LeastVisited
deptList_LeastVisited = ['Keur Massar', 'Pikine', 'Bambey', 'Mbacke', 'Fatick', 'Foundiougne', 'Gossas']
allocList_LeastVisited = [20, 20, 20, 19, 19, 19, 19]
n_LeastVisited = GetAllocVecFromLists(deptNames, deptList_LeastVisited, allocList_LeastVisited)
util_LeastVisited_unif, util_LeastVisited_unif_CI = sampf.getImportanceUtilityEstimate(n_LeastVisited, lgdict,
                                                                paramdict, numimportdraws=50000)
print('LeastVisited:',util_LeastVisited_unif, util_LeastVisited_unif_CI)
# 1-APR
# 1.5218729881054482 (1.513759868559136, 1.5299861076517605); 30k imp draws
# 1.437412029402573 (1.427261393737913, 1.4475626650672329); 50k imp draws
# 1.4750530561369661 (1.4649465423867536, 1.4851595698871787); 50k imp draws
# 13-MAR (non-importance method)
# 1.6657163547317921 (1.5262975507763805, 1.8051351586872038)

# MostSFPs (uniform)
deptList_MostSFPs_unif = ['Dakar', 'Guediawaye', 'Diourbel', 'Saint-Louis', 'Podor']
allocList_MostSFPs_unif = [20, 19, 19, 19, 19]
n_MostSFPs_unif = GetAllocVecFromLists(deptNames, deptList_MostSFPs_unif, allocList_MostSFPs_unif)
util_MostSFPs_unif, util_MostSFPs_unif_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (unform):',util_MostSFPs_unif, util_MostSFPs_unif_CI)
# 1-APR
# 0.38828699159535596 (0.3823685276019546, 0.3942054555887573); 30k imp draws
# 0.3816474185896155 (0.37388162429673777, 0.3894132128824932); 50k imp draws
# 0.4057327485117437 (0.39745040526376485, 0.4140150917597225); 50k imp draws
# 13-MAR
# 0.30966532049070494 (0.29526214617659896, 0.3240684948048109)

# MostSFPs (weighted)
deptList_MostSFPs_wtd = ['Dakar', 'Guediawaye', 'Diourbel', 'Saint-Louis', 'Podor']
allocList_MostSFPs_wtd = [15, 19, 12, 14, 36]
n_MostSFPs_wtd = GetAllocVecFromLists(deptNames, deptList_MostSFPs_wtd, allocList_MostSFPs_wtd)
util_MostSFPs_wtd, util_MostSFPs_wtd_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (weighted):', util_MostSFPs_wtd, util_MostSFPs_wtd_CI)
# 1-APR
# 0.34918678364697797 (0.34304262230816285, 0.3553309449857931); 30k imp draws
# 0.35769999295502153 (0.3507887967383443, 0.36461118917169877); 50k imp draws
# 0.34387015916270514 (0.33581437552917137, 0.3519259427962389); 50k imp draws
# 13-MAR
# 0.3204636852594689 (0.30767399388703787, 0.3332533766318999)

# MoreDistricts (uniform)
deptList_MoreDist_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke']
allocList_MoreDist_unif = [9, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8]
n_MoreDist_unif = GetAllocVecFromLists(deptNames, deptList_MoreDist_unif, allocList_MoreDist_unif)
util_MoreDist_unif, util_MoreDist_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (unform):', util_MoreDist_unif, util_MoreDist_unif_CI)
# 1-APR
# 0.710156152751491 (0.7019020118087091, 0.7184102936942729); 30k imp draws
# 0.7240902233604256 (0.7148199316185551, 0.7333605151022962); 50k imp draws
# 0.7142112441221578 (0.7041955514460678, 0.7242269367982477); 50k imp draws
# 13-MAR
# 0.6867008491005695 (0.6669912197701802, 0.7064104784309588)

# MoreDistricts (weighted)
deptList_MoreDist_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke']
allocList_MoreDist_wtd = [6, 5, 13, 13, 6, 5, 6, 7, 5, 13, 13]
n_MoreDist_wtd = GetAllocVecFromLists(deptNames, deptList_MoreDist_wtd, allocList_MoreDist_wtd)
util_MoreDist_wtd, util_MoreDist_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (weighted):', util_MoreDist_wtd, util_MoreDist_wtd_CI)
# 1-APR
# 0.9026503512504966 (0.8959903094438921, 0.9093103930571012); 30k imp draws
# 0.9249762109211606 (0.9174564360443753, 0.9324959857979458); 50k imp draws
# 0.9208077574830948 (0.9133589885267988, 0.9282565264393909); 50k imp draws
# 13-MAR
# 0.7747075043342289 (0.7534452384396939, 0.7959697702287638)

# MoreTests (uniform)
deptList_MoreTests_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune']
allocList_MoreTests_unif = [22, 22, 22, 22, 22, 22, 22, 22]
n_MoreTests_unif = GetAllocVecFromLists(deptNames, deptList_MoreTests_unif, allocList_MoreTests_unif)
util_MoreTests_unif, util_MoreTests_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostTests (unform):', util_MoreTests_unif, util_MoreTests_unif_CI)
# 1-APR
# 0.7721902436053156 (0.7661619199797141, 0.7782185672309172); 30k imp draws
# 0.7498919095152168 (0.741868438680191, 0.7579153803502425); 50k imp draws
# 0.7485808613449549 (0.7404104210065245, 0.7567513016833853); 50k imp draws
# 13-MAR
# 0.7406350853193722 (0.6913757247389984, 0.7898944458997459)

# MoreTests (weighted)
deptList_MoreTests_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune']
allocList_MoreTests_wtd = [13, 14, 43, 43, 15, 14, 15, 19]
n_MoreTests_wtd = GetAllocVecFromLists(deptNames, deptList_MoreTests_wtd, allocList_MoreTests_wtd)
util_MoreTests_wtd, util_MoreTests_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreTests (weighted):', util_MoreTests_wtd, util_MoreTests_wtd_CI)
# 1-APR
# 0.7775824854956621 (0.7709527122132069, 0.7842122587781173); 30k imp draws
# 0.7630215255617667 (0.7546132213855721, 0.7714298297379614); 50k imp draws
# 0.7670376446472407 (0.7598361674775553, 0.774239121816926); 50k imp draws
# 13-MAR
# 0.7494513457669925 (0.721643929353533, 0.7772587621804519)

#######
# B=1400
#######

# IP-RP allocation
deptList_IPRP = ['Dakar', 'Keur Massar', 'Pikine', 'Louga', 'Linguere', 'Kaolack', 'Guinguineo',
                 'Nioro du Rip', 'Kaffrine', 'Birkilane', 'Malem Hoddar', 'Bambey', 'Mbacke',
                 'Fatick', 'Foundiougne', 'Gossas']
allocList_IPRP = [19, 21, 7, 7, 11, 38, 9, 18, 8, 8, 8, 10, 7, 11, 10, 9]
n_IPRP = GetAllocVecFromLists(deptNames, deptList_IPRP, allocList_IPRP)
util_IPRP, util_IPRP_CI = sampf.getImportanceUtilityEstimate(n_IPRP, lgdict, paramdict,
                                                             numimportdraws=50000)
print('IPRP:',util_IPRP, util_IPRP_CI)
# 2-APR
# 2.501114917463534 (2.4907262706226145, 2.511503564304453)

# LeastVisited
deptList_LeastVisited = ['Keur Massar', 'Pikine', 'Louga', 'Linguere', 'Goudiry', 'Guinguineo',
                         'Nioro du Rip', 'Birkilane', 'Koungheul', 'Malem Hoddar', 'Bambey', 'Mbacke',
                         'Fatick', 'Foundiougne', 'Gossas']
allocList_LeastVisited = [5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
n_LeastVisited = GetAllocVecFromLists(deptNames, deptList_LeastVisited, allocList_LeastVisited)
util_LeastVisited_unif, util_LeastVisited_unif_CI = sampf.getImportanceUtilityEstimate(n_LeastVisited, lgdict,
                                                                paramdict, numimportdraws=50000)
print('LeastVisited:',util_LeastVisited_unif, util_LeastVisited_unif_CI)
# 2-APR
# 1.2424693100089677 (1.2265451101386144, 1.2583935098793209)

# MostSFPs (uniform)
deptList_MostSFPs_unif = ['Dakar', 'Guediawaye', 'Tambacounda', 'Koumpentoum', 'Diourbel', 'Saint-Louis',
                          'Podor', 'Kolda', 'Velingara', 'Matam', 'Kanel']
allocList_MostSFPs_unif = [8, 8, 8, 7, 7, 7, 7, 7, 7, 7, 7]
n_MostSFPs_unif = GetAllocVecFromLists(deptNames, deptList_MostSFPs_unif, allocList_MostSFPs_unif)
util_MostSFPs_unif, util_MostSFPs_unif_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (unform):',util_MostSFPs_unif, util_MostSFPs_unif_CI)
# 2-APR
# 0.3526096663592213 (0.34461075498647453, 0.3606085777319681)

# MostSFPs (weighted)
deptList_MostSFPs_wtd = ['Dakar', 'Guediawaye', 'Tambacounda', 'Koumpentoum', 'Diourbel', 'Saint-Louis',
                          'Podor', 'Kolda', 'Velingara', 'Matam', 'Kanel']
allocList_MostSFPs_wtd = [6, 8, 6, 8, 5, 5, 14, 5, 9, 6, 8]
n_MostSFPs_wtd = GetAllocVecFromLists(deptNames, deptList_MostSFPs_wtd, allocList_MostSFPs_wtd)
util_MostSFPs_wtd, util_MostSFPs_wtd_CI = sampf.getImportanceUtilityEstimate(n_MostSFPs_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostSFPs (weighted):', util_MostSFPs_wtd, util_MostSFPs_wtd_CI)
# 2-APR
# 0.39343331638029966 (0.3847083229547188, 0.4021583098058805)

# MoreDistricts (uniform)
deptList_MoreDist_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Kaolack', 'Guinguineo', 'Nioro du Rip', 'Kaffrine',
                          'Birkilane', 'Koungheul', 'Malem Hoddar',  'Diourbel', 'Bambey', 'Mbacke',
                          'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreDist_unif = [8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 7, 7]
n_MoreDist_unif = GetAllocVecFromLists(deptNames, deptList_MoreDist_unif, allocList_MoreDist_unif)
util_MoreDist_unif, util_MoreDist_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (unform):', util_MoreDist_unif, util_MoreDist_unif_CI)
# 2-APR
# 1.7779186722467752 (1.7643080846741288, 1.7915292598194217)

# MoreDistricts (weighted)
deptList_MoreDist_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies',
                          'Mbour', 'Tivaoune', 'Kaolack', 'Guinguineo', 'Nioro du Rip', 'Kaffrine',
                          'Birkilane', 'Koungheul', 'Malem Hoddar',  'Diourbel', 'Bambey', 'Mbacke',
                          'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreDist_wtd = [4, 5, 9, 9, 5, 5, 5, 6, 5, 9, 9, 7, 9, 9, 9, 4, 10, 10, 10, 10, 10]
n_MoreDist_wtd = GetAllocVecFromLists(deptNames, deptList_MoreDist_wtd, allocList_MoreDist_wtd)
util_MoreDist_wtd, util_MoreDist_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreDist_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreDistricts (weighted):', util_MoreDist_wtd, util_MoreDist_wtd_CI)
# 2-APR
#

# MoreTests (uniform)
deptList_MoreTests_unif = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies', 'Mbour',
                           'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke', 'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreTests_unif = [27, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26]
n_MoreTests_unif = GetAllocVecFromLists(deptNames, deptList_MoreTests_unif, allocList_MoreTests_unif)
util_MoreTests_unif, util_MoreTests_unif_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_unif, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MostTests (unform):', util_MoreTests_unif, util_MoreTests_unif_CI)
# 2-APR
#

# MoreTests (weighted)
deptList_MoreTests_wtd = ['Dakar', 'Guediawaye', 'Keur Massar', 'Pikine', 'Rufisque', 'Thies', 'Mbour',
                           'Tivaoune', 'Diourbel', 'Bambey', 'Mbacke' 'Fatick', 'Foundiougne', 'Gossas']
allocList_MoreTests_wtd = [15, 16, 36, 36, 16, 16, 16, 19, 15, 36, 36, 36, 36, 36]
n_MoreTests_wtd = GetAllocVecFromLists(deptNames, deptList_MoreTests_wtd, allocList_MoreTests_wtd)
util_MoreTests_wtd, util_MoreTests_wtd_CI = sampf.getImportanceUtilityEstimate(n_MoreTests_wtd, lgdict,
                                                                paramdict, numimportdraws=50000)
print('MoreTests (weighted):', util_MoreTests_wtd, util_MoreTests_wtd_CI)
# 2-APR
#


##########################
##########################
# END calculate utility for candidates and benchmarks
##########################
##########################



'''
time0 = time.time()
utilavg, (utilCIlo, utilCIhi) = getUtilityEstimate(n, lgdict, paramdict)
print(time.time() - time0)

With numtruthdraws, numdatadraws = 10000, 500:
~160 seconds
utilavg, (utilCIlo, utilCIhi) =
0.4068438943300112, (0.3931478722114097, 0.42053991644861277)
0.42619338638365, (0.40593452427234133, 0.4464522484949587)
'''
##################
# Now set up functions for constraints and variables of our program
##################
# Set these parameters per the program described in the paper
batchcost, batchsize, B, ctest = 0, 700, 700, 2
batchsize = B
bigM = B*ctest

dept_df_sort = dept_df.sort_values('Department')

FTEcostperday = 200
f_dept = np.array(dept_df_sort['DeptFixedCostDays'].tolist())*FTEcostperday
f_reg = np.array(regcost_mat)*FTEcostperday

optparamdict = {'batchcost':batchcost, 'budget':B, 'pertestcost':ctest, 'Mconstant':bigM, 'batchsize':batchsize,
                'deptfixedcostvec':f_dept, 'arcfixedcostmat': f_reg, 'reghqname':'Dakar', 'reghqind':0,
                'deptnames':deptNames, 'regnames':regNames, 'dept_df':dept_df_sort}

# What are the upper bounds for our allocation variables?
def GetUpperBounds(optparamdict, alpha=1.0):
    """
    Returns a numpy vector of upper bounds for an inputted parameter dictionary. alpha determines the proportion of the
    budget that can be dedicated to any one district
    """
    B, f_dept, f_reg = optparamdict['budget']*alpha, optparamdict['deptfixedcostvec'], optparamdict['arcfixedcostmat']
    batchcost, ctest, reghqind = optparamdict['batchcost'], optparamdict['pertestcost'], optparamdict['reghqind']
    deptnames, regnames, dept_df = optparamdict['deptnames'], optparamdict['regnames'], optparamdict['dept_df']
    retvec = np.zeros(f_dept.shape[0])
    for i in range(f_dept.shape[0]):
        regparent = GetRegion(deptnames[i], dept_df)
        regparentind = regnames.index(regparent)
        if regparentind == reghqind:
            retvec[i] = np.floor((B-f_dept[i]-batchcost)/ctest)
        else:
            regfixedcost = f_reg[reghqind,regparentind] + f_reg[regparentind, reghqind]
            retvec[i] = np.floor((B-f_dept[i]-batchcost-regfixedcost)/ctest)
    return retvec

deptallocbds = GetUpperBounds(optparamdict)
# Lower upper bounds to maximum of observed prior tests at any district
maxpriortests = int(np.max(np.sum(lgdict['N'],axis=1)))
deptallocbds = np.array([min(deptallocbds[i], maxpriortests) for i in range(deptallocbds.shape[0])])

print(deptNames[np.argmin(deptallocbds)], min(deptallocbds))
print(deptNames[np.argmax(deptallocbds)], max(deptallocbds))

# TODO: INSPECT CHOICES HERE LATER
# Example set of variables to inspect validity
v_batch = B
n_alloc = np.zeros(numTN)
n_alloc[36] = 20 # Rufisque, Dakar
n_alloc[25] = 20 # Louga, Louga
n_alloc[24] = 20 # Linguere, Louga
n_alloc[2] = 20 # Bignona, Ziguinchor
n_alloc[32] = 20 # Oussouye, Ziguinchor
n_alloc[8] = 10 # Fatick, Fatick
n_alloc[9] = 10 # Foundiougne, Fatick
n_alloc[10] = 0 # Gossas, Fatick
z_reg = np.zeros(numReg)
z_reg[0] = 1 # Dakar
z_reg[7] = 1 # Louga
z_reg[13] = 1 # Ziguinchor
z_reg[2] = 1 # Fatick
z_dept = np.zeros(numTN)
z_dept[36] = 1 # Rufisque, Dakar
z_dept[25] = 1 # Louga, Louga
z_dept[24] = 1 # Linguere, Louga
z_dept[2] = 1 # Bignona, Ziguinchor
z_dept[32] = 1 # Oussouye, Ziguinchor
z_dept[8] = 1 # Fatick, Fatick
z_dept[9] = 1 # Foundiougne, Fatick
z_dept[10] = 0 # Gossas, Fatick

x = np.zeros((numReg, numReg))
x[0, 7] = 1 # Dakar to Louga
x[7, 13] = 1 # Louga to Ziguinchor
x[13, 2] = 1 # Ziguinchor to Fatick
x[2, 0] = 1 # Fatick to Dakar
# Generate a dictionary for variables
varsetdict = {'batch_int':v_batch, 'regaccessvec_bin':z_reg, 'deptaccessvec_bin':z_dept, 'arcmat_bin':x,
              'allocvec_int':n_alloc}
##########
# Add functions for all constraints; they return True if satisfied, False otherwise
##########
def ConstrBudget(varsetdict, optparamdict):
    """Indicates if the budget constraint is satisfied"""
    flag = False
    budgetcost = varsetdict['batch_int']*optparamdict['batchcost'] + \
        np.sum(varsetdict['deptaccessvec_bin']*optparamdict['deptfixedcostvec']) + \
        np.sum(varsetdict['allocvec_int'] * optparamdict['pertestcost']) + \
        np.sum(varsetdict['arcmat_bin'] * optparamdict['arcfixedcostmat'])
    if budgetcost <= optparamdict['budget']: # Constraint satisfied
        flag = True
    return flag

def ConstrRegionAccess(varsetdict, optparamdict):
    """Indicates if the regional access constraints are satisfied"""
    flag = True
    bigM = optparamdict['Mconstant']
    for aind, a in enumerate(optparamdict['deptnames']):
        parentreg = GetRegion(a, optparamdict['dept_df'])
        parentregind = optparamdict['regnames'].index(parentreg)
        if varsetdict['allocvec_int'][aind] > bigM*varsetdict['regaccessvec_bin'][parentregind]:
            flag = False
    return flag

def ConstrHQRegionAccess(varsetdict, optparamdict):
    """Indicates if the regional HQ access is set"""
    flag = True
    reghqind = optparamdict['reghqind']
    if varsetdict['regaccessvec_bin'][reghqind] != 1:
        flag = False
    return flag

def ConstrLocationAccess(varsetdict, optparamdict):
    """Indicates if the location/department access constraints are satisfied"""
    flag = True
    bigM = optparamdict['Mconstant']
    for aind, a in enumerate(optparamdict['deptnames']):
        if varsetdict['allocvec_int'][aind] > bigM*varsetdict['deptaccessvec_bin'][aind]:
            flag = False
    return flag

def ConstrBatching(varsetdict, optparamdict):
    """Indicates if the location/department access constraints are satisfied"""
    flag = True
    if optparamdict['batchsize']*varsetdict['batch_int'] < np.sum(varsetdict['allocvec_int']):
        flag = False
    return flag

def ConstrArcsLeaveOnce(varsetdict, optparamdict):
    """Each region can only be exited once"""
    flag = True
    x =  varsetdict['arcmat_bin']
    for rind in range(len(optparamdict['regnames'])):
        if np.sum(x[rind]) > 1:
            flag = False
    return flag

def ConstrArcsPassThruHQ(varsetdict, optparamdict):
    """Path must pass through the HQ region"""
    flag = True
    x =  varsetdict['arcmat_bin']
    reghqind = optparamdict['reghqind']
    reghqsum = np.sum(x[reghqind])*optparamdict['Mconstant']
    if np.sum(x) > reghqsum:
        flag = False
    return flag

def ConstrArcsFlowBalance(varsetdict, optparamdict):
    """Each region must be entered and exited the same number of times"""
    flag = True
    x =  varsetdict['arcmat_bin']
    for rind in range(len(optparamdict['regnames'])):
        if np.sum(x[rind]) != np.sum(x[:, rind]):
            flag = False
    return flag

def ConstrArcsRegAccess(varsetdict, optparamdict):
    """Accessed regions must be on the path"""
    flag = True
    x =  varsetdict['arcmat_bin']
    reghqind = optparamdict['reghqind']
    for rind in range(len(optparamdict['regnames'])):
        if (rind != reghqind) and varsetdict['regaccessvec_bin'][rind] > np.sum(x[rind]):
            flag = False
    return flag

def CheckSubtour(varsetdict, optparamdict):
    """Checks if matrix x of varsetdict has multiple tours"""
    x = varsetdict['arcmat_bin']
    tourlist = []
    flag = True
    if np.sum(x) == 0:
        return flag
    else:
        # Start from HQ ind
        reghqind = optparamdict['reghqind']
        tourlist.append(reghqind)
        nextregind = np.where(x[reghqind] == 1)[0][0]
        while nextregind not in tourlist:
            tourlist.append(nextregind)
            nextregind = np.where(x[nextregind] == 1)[0][0]
    if len(tourlist) < np.sum(x):
        flag = False
    return flag

def GetTours(varsetdict, optparamdict):
    """Return a list of lists, each of which is a tour of the arcs matrix in varsetdict"""
    x = varsetdict['arcmat_bin']
    tourlist = []
    flag = True
    tempx = x.copy()
    while np.sum(tempx) > 0:
        currtourlist = GetSubtour(tempx)
        tourlist.append(currtourlist)
        tempx[currtourlist] = tempx[currtourlist]*0
    return tourlist

def GetSubtour(x):
    '''
    Returns a subtour for incidence matrix x
    '''
    tourlist = []
    startind = (np.sum(x, axis=1) != 0).argmax()
    tourlist.append(startind)
    nextind = np.where(x[startind] == 1)[0][0]
    while nextind not in tourlist:
        tourlist.append(nextind)
        nextind = np.where(x[nextind] == 1)[0][0]
    return tourlist

def GetSubtourMaxCardinality(optparamdict):
    """Provide an upper bound on the number of regions included in any tour; HQ region is included"""
    mincostvec = [] # initialize
    dept_df = optparamdict['dept_df']
    ctest, B, batchcost = optparamdict['pertestcost'], optparamdict['budget'], optparamdict['batchcost']
    for r in range(len(optparamdict['regnames'])):
        if r != optparamdict['reghqind']:
            currReg = optparamdict['regnames'][r]
            currmindeptcost = np.max(optparamdict['deptfixedcostvec'])
            deptchildren = GetDeptChildren(currReg, dept_df)
            for currdept in deptchildren:
                currdeptind = optparamdict['deptnames'].index(currdept)
                if optparamdict['deptfixedcostvec'][currdeptind] < currmindeptcost:
                    currmindeptcost = optparamdict['deptfixedcostvec'][currdeptind]
            currminentry = optparamdict['arcfixedcostmat'][np.where(optparamdict['arcfixedcostmat'][:, r] > 0,
                                                                    optparamdict['arcfixedcostmat'][:, r],
                                                                    np.inf).argmin(), r]
            currminexit = optparamdict['arcfixedcostmat'][r, np.where(optparamdict['arcfixedcostmat'][r] > 0,
                                                                    optparamdict['arcfixedcostmat'][r],
                                                                    np.inf).argmin()]
            mincostvec.append(currmindeptcost + currminentry + currminexit + ctest)
        else:
            mincostvec.append(0) # HQ is always included
    # Now add regions until the budget is reached
    currsum = 0
    numregions = 0
    nexttoadd = np.array(mincostvec).argmin()
    while currsum + mincostvec[nexttoadd] <= B - batchcost:
        currsum += mincostvec[nexttoadd]
        numregions += 1
        _ = mincostvec.pop(nexttoadd)
        nexttoadd = np.array(mincostvec).argmin()

    return numregions

def GetTriangleInterpolation(xlist, flist):
    """
    Produces a concave interpolation for integers using the inputs x and function evaluations f_x.
    xlist should have three values: [x_0, x_0 + 1, x_max], and f_x should have evaluations corresponding to these
        three points.
    Returns x and f_x lists for the inclusive range x = [x_0, x_max], as well as intercept l, slope juncture k, and
        slopes m1 and m2
    """
    retx = np.arange(xlist[0], xlist[2]+1)
    # First get left line
    leftlineslope = (flist[1]-flist[0]) / (xlist[1]-xlist[0])
    leftline = leftlineslope * np.array([retx[i]-retx[0] for i in range(retx.shape[0])]) + flist[0]
    # Next get bottom line
    bottomlineslope = (flist[2]-flist[1]) / (xlist[2]-xlist[1])
    bottomline = bottomlineslope * np.array([retx[i] - retx[1] for i in range(retx.shape[0])]) + flist[1]
    # Top line is just the largest value
    topline = np.ones(retx.shape[0]) * flist[2]
    # Upper vals is minimum of left and top lines
    uppervals = np.minimum(leftline, topline)
    # Interpolation is midpoint between upper and bottom lines
    retf = np.average(np.vstack((uppervals, bottomline)),axis=0)
    retf[0] = flist[0]  # Otherwise we are changing the first value

    # Identify slope juncture k, where the line "bends", which is where leftline meets topline
    # k is the first index where the new slope takes hold
    k = leftline.tolist().index( next(x for x in leftline if x > topline[0]))
    # Slopes can be identified using this k
    # todo: WARNING: THIS MIGHT BREAK DOWN FOR EITHER VERY STRAIGHT OR VERY CURVED INTERPOLATIONS
    m1 = retf[k-1] - retf[k-2]
    m2 = retf[k+1] - retf[k]
    # l is the zero intercept, using m1
    l = retf[1] - m1

    return retx, retf, l, k, m1, m2

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

'''
# Here we obtain utility evaluations for 1 and n_bound tests at each department
deptallocbds = GetUpperBounds(optparamdict)
util_lo, util_lo_CI = [], []
util_hi, util_hi_CI = [], []
for i in range(len(deptNames)):
    currbd = int(deptallocbds[i])
    print('Getting utility for ' + deptNames[i] + ', at 1 test...')
    n = np.zeros(numTN)
    n[i] = 1
    currlo, currlo_CI = getUtilityEstimate(n, lgdict, paramdict)
    print(currlo, currlo_CI)
    util_lo.append(currlo)
    util_lo_CI.append(currlo_CI)
    print('Getting utility for ' + deptNames[i] + ', at ' + str(currbd) + ' tests...')
    n[i] = currbd
    currhi, currhi_CI = getUtilityEstimate(n, lgdict, paramdict)
    print(currhi, currhi_CI)
    util_hi.append(currhi)
    util_hi_CI.append(currhi_CI)

util_df = pd.DataFrame({'DeptName':deptNames,'Bounds':deptallocbds,'Util_lo':util_lo, 'Util_lo_CI':util_lo_CI,
                        'Util_hi':util_hi, 'Util_hi_CI':util_hi_CI})

util_df.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'utilevals.pkl'))

#####
# ADDED 7-MAR: Add bounds for 81 tests at each department
util_81, util_81_CI = [], []
for i in range(len(deptNames)):
    n = np.zeros(numTN)
    currbd = maxpriortests
    print('Getting utility for ' + deptNames[i] + ', at ' + str(currbd) + ' tests...')
    n[i] = currbd
    curr81, curr81_CI = getUtilityEstimate(n, lgdict, paramdict)
    print(curr81, curr81_CI)
    util_81.append(curr81)
    util_81_CI.append(curr81_CI)
    
util_df.insert(5, 'Util_81', util_81)
util_df.insert(6, 'Util_81_CI', util_81_CI)
######
'''

# Load previously calculated lower and upper utility evaluations
#util_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'utilevals.pkl'))
util_df = pd.read_csv(os.path.join('operationalizedsamplingplans', 'csv_utility', 'utilevals_BASE.csv'))



####
# todo: REMOVE LATER; CHECKING AGAINST OLD UTILITY ESTIMATES
####
util_lo_imp, util_lo_CI_imp = [], []
util_hi_imp, util_hi_CI_imp = [], []
for reps in range(10):
    for i in range(10):
        currbd = int(deptallocbds[i])
        n = np.zeros(numTN)
        '''    
        print('Getting utility for ' + deptNames[i] + ', at 1 test...')    
        n[i] = 1
        currlo_imp, currlo_CI_imp = sampf.getImportanceUtilityEstimate(n, lgdict, paramdict, numimportdraws=30000)
        print(currlo_imp, currlo_CI_imp)
        util_lo_imp.append(currlo_imp)
        util_lo_CI_imp.append(currlo_CI_imp)
        '''
        print('Getting utility for ' + deptNames[i] + ', at ' + str(currbd) + ' tests...')
        n[i] = currbd
        currhi_imp, currhi_CI_imp = sampf.getImportanceUtilityEstimate(n, lgdict, paramdict, numimportdraws=50000)
        print(currhi_imp, currhi_CI_imp)
        util_hi_imp.append(currhi_imp)
        util_hi_CI_imp.append(currhi_CI_imp)
'''
# 1st run: 30k imp draws
util_hi_imp = [0.3906806364519433, 0.37900277450375164, 0.3125001286929532, 0.29495861975553517, 0.1484237775864603, 0.11712893687658266, 0.2491887695057997, 0.18748908632695382, 0.37597343292086194, 0.3138836003083476, 0.37269612148611486, 0.26872878180024884, 0.35535587179775696, 0.16475204125187837, 0.24957612548629804, 0.16849467150581354, 0.16117134264092492, 0.2886873340956626, 0.15584807336130346, 0.19014490579459498, 0.3088897890583908, 0.16660470044417508, 0.12478914780106365, 0.36051397028615995, 0.2885597926524781, 0.3547341887416735, 0.35240183304921757, 0.16846768737411466, 0.28431504530094287, 0.15322035049142357, 0.31073053682450613, 0.3497771893559207, 0.23278279534773816, 0.30563854854423056, 0.2656809525105466, 0.35366903855184617, 0.0806069387652677, 0.1263231406305021, 0.2527240768625827, 0.35659808113103253, 0.25586223074083314, 0.1431744020501, 0.08642080227579108, 0.19829483675732185, 0.2071626763841259, 0.2899497353746412]
util_hi_CI_imp = [(0.38595297319382027, 0.3954082997100663), (0.3737541827074189, 0.3842513663000844), (0.30760789372496156, 0.3173923636609448), (0.28937533040854113, 0.3005419091025292), (0.1453044707311033, 0.1515430844418173), (0.1149831792953222, 0.11927469445784311), (0.2444668838519597, 0.25391065515963973), (0.1827902244125621, 0.19218794824134555), (0.3698319690289136, 0.3821148968128103), (0.3075489483672875, 0.3202182522494077), (0.3675744038969153, 0.3778178390753144), (0.26498536578303344, 0.27247219781746423), (0.35097738641657195, 0.359734357178942), (0.16173954667756085, 0.16776453582619588), (0.2458965718139794, 0.2532556791586167), (0.16611500466456697, 0.17087433834706012), (0.15744929656400686, 0.16489338871784298), (0.2837714137486138, 0.2936032544427114), (0.15367938221318767, 0.15801676450941926), (0.18710790492263385, 0.1931819066665561), (0.30331019705173645, 0.3144693810650452), (0.16192871188237667, 0.17128068900597349), (0.12145381603180816, 0.12812447957031914), (0.3545193854481834, 0.3665085551241365), (0.2840071496511545, 0.29311243565380174), (0.34993061230100153, 0.3595377651823455), (0.347354331763265, 0.3574493343351701), (0.16491138703167785, 0.17202398771655147), (0.28005389912150314, 0.2885761914803826), (0.1489806549171444, 0.15746004606570274), (0.3064495556393023, 0.31501151800970995), (0.34505136122100843, 0.354503017490833), (0.22828351222859844, 0.23728207846687788), (0.30202778632840577, 0.30924931076005535), (0.2618305305709505, 0.26953137445014264), (0.35012701544012614, 0.3572110616635662), (0.0786704100236264, 0.082543467506909), (0.12290000760660647, 0.12974627365439773), (0.2486159239967929, 0.2568322297283725), (0.3512152326217226, 0.36198092964034245), (0.25096023628613295, 0.26076422519553333), (0.13971234526516696, 0.14663645883503307), (0.08370010288294871, 0.08914150166863344), (0.19418115614387332, 0.20240851737077037), (0.20394652854265694, 0.21037882422559484), (0.2860116507042836, 0.2938878200449988)]
# 2nd run: 50k imp draws

'''
util_df = pd.DataFrame({'DeptName':deptNames,'Bounds':deptallocbds,'Util_lo':util_lo_imp, 'Util_lo_CI':util_lo_CI_imp,
                        'Util_hi':util_hi_imp, 'Util_hi_CI':util_hi_CI_imp})

util_df.to_csv(os.path.join('operationalizedsamplingplans', 'csv_utility', 'utilevals_BASE.csv'), index=False)

####
# todo: END REMOVE
####

''' 14-MAR-24 COMPARISON OF INTERPOLATED UTILITY POINTS: 60K/1000 VS 200K/200
util_lo_60 = np.array([0.03344591, 0.03446701, 0.03066869, 0.03730135, 0.00453539,
                       0.00422144, 0.00522252, 0.00231574, 0.03305749, 0.03061265,
                       0.04035724, 0.0223767 , 0.032466  , 0.00347499, 0.02463909,
                       0.01918473, 0.00561556, 0.00807742, 0.01002169, 0.00462278,
                       0.01424308, 0.00203755, 0.00183784, 0.00595836, 0.02330756,
                       0.0446292 , 0.03696385, 0.00171342, 0.03962201, 0.00401421,
                       0.03131379, 0.02061252, 0.01409668, 0.04275234, 0.00901496,
                       0.04311047, 0.00145227, 0.00207412, 0.01286778, 0.03405235,
                       0.01369974, 0.00228068, 0.0017215 , 0.0086946 , 0.00993675,
                       0.03577284])
util_lo_60_CI = np.array([[0.03147292, 0.0354189 ],
       [0.03195029, 0.03698372],
       [0.02772584, 0.03361154],
       [0.03480121, 0.03980148],
       [0.00293373, 0.00613706],
       [0.00364864, 0.00479423],
       [0.00429602, 0.00614902],
       [0.00176791, 0.00286357],
       [0.03050272, 0.03561226],
       [0.02884772, 0.03237758],
       [0.0382347 , 0.04247979],
       [0.01976218, 0.02499121],
       [0.02939688, 0.03553513],
       [0.00289235, 0.00405762],
       [0.02214466, 0.02713352],
       [0.01611166, 0.0222578 ],
       [0.00449114, 0.00673999],
       [0.00698744, 0.00916739],
       [0.00838262, 0.01166076],
       [0.00353465, 0.00571092],
       [0.011471  , 0.01701515],
       [0.00133816, 0.00273694],
       [0.00134013, 0.00233556],
       [0.00323716, 0.00867955],
       [0.02013414, 0.02648098],
       [0.04349307, 0.04576533],
       [0.03432852, 0.03959918],
       [0.00123777, 0.00218906],
       [0.03740724, 0.04183677],
       [0.00322302, 0.0048054 ],
       [0.02909401, 0.03353357],
       [0.01698735, 0.02423769],
       [0.011657  , 0.01653636],
       [0.04106823, 0.04443644],
       [0.00674657, 0.01128336],
       [0.04176224, 0.04445871],
       [0.00123559, 0.00166895],
       [0.00156203, 0.00258622],
       [0.01033355, 0.01540201],
       [0.03179264, 0.03631206],
       [0.01030859, 0.01709089],
       [0.00162424, 0.00293712],
       [0.00127589, 0.00216712],
       [0.00741716, 0.00997203],
       [0.0093994 , 0.0104741 ],
       [0.03402675, 0.03751893]])
util_hi_60 = np.array([0.43105884, 0.70318883, 0.37932139, 0.46840999, 0.19396183,
       0.14442076, 0.73320741, 0.4526506 , 0.78708533, 0.61100776,
       0.77685478, 0.29077391, 0.39911443, 0.35022837, 0.35502769,
       0.1849252 , 0.31661005, 0.76937927, 0.21169124, 0.18660776,
       0.92007944, 0.21282808, 0.16130279, 0.88937613, 0.46542938,
       0.5828677 , 0.47925974, 0.30697219, 0.53908748, 0.29882365,
       0.34785669, 0.7957092 , 0.34415312, 0.60390663, 0.36804362,
       0.45226213, 0.16007126, 0.35734395, 0.30815765, 0.36192727,
       0.44651105, 0.2581032 , 0.17842593, 0.28019711, 0.21054458,
       0.42718289])
util_hi_CI_60 = np.array([[0.42315654, 0.43896114],
       [0.65970264, 0.74667502],
       [0.36999728, 0.38864551],
       [0.44730532, 0.48951467],
       [0.18843369, 0.19948996],
       [0.14172687, 0.14711464],
       [0.68652414, 0.77989068],
       [0.43015147, 0.47514972],
       [0.73794278, 0.83622787],
       [0.5739668 , 0.64804871],
       [0.73134173, 0.82236783],
       [0.28527536, 0.29627246],
       [0.38910398, 0.40912488],
       [0.324663  , 0.37579373],
       [0.34520037, 0.36485501],
       [0.1779138 , 0.1919366 ],
       [0.30659026, 0.32662985],
       [0.71673544, 0.8220231 ],
       [0.20366583, 0.21971664],
       [0.18183733, 0.19137818],
       [0.86480568, 0.9753532 ],
       [0.2065733 , 0.21908285],
       [0.15421666, 0.16838892],
       [0.84154046, 0.93721181],
       [0.43889158, 0.49196718],
       [0.54798307, 0.61775234],
       [0.45752274, 0.50099673],
       [0.29423109, 0.31971329],
       [0.50769694, 0.57047803],
       [0.28595349, 0.31169381],
       [0.34286325, 0.35285012],
       [0.76097627, 0.83044212],
       [0.32833374, 0.3599725 ],
       [0.57631653, 0.63149674],
       [0.36054774, 0.37553949],
       [0.43945515, 0.46506911],
       [0.15167964, 0.16846287],
       [0.3264682 , 0.3882197 ],
       [0.3010332 , 0.3152821 ],
       [0.35467181, 0.36918273],
       [0.43037366, 0.46264845],
       [0.24579102, 0.27041539],
       [0.17022303, 0.18662884],
       [0.2692235 , 0.29117072],
       [0.20662048, 0.21446868],
       [0.41682005, 0.43754573]])
util_lo_200 = np.array([0.02916269, 0.02986046, 0.02280912, 0.03360276, 0.00531194,
       0.00366224, 0.00426673, 0.0024488 , 0.03645808, 0.03191844,
       0.03780569, 0.02099417, 0.03519477, 0.00458397, 0.02389095,
       0.02251109, 0.00710643, 0.0080562 , 0.00832719, 0.00430041,
       0.01436194, 0.00249929, 0.00258331, 0.01075591, 0.01758466,
       0.04457001, 0.03343373, 0.00194465, 0.03831309, 0.00367313,
       0.03336207, 0.02242953, 0.00558529, 0.04466725, 0.01000271,
       0.04286662, 0.00153833, 0.00292113, 0.00863356, 0.03342741,
       0.01438087, 0.00388379, 0.00211993, 0.00559007, 0.01082955,
       0.0345706 ])
util_lo_200_CI = np.array([[ 0.02374176,  0.03458362],
       [ 0.02405018,  0.03567074],
       [ 0.01557861,  0.03003964],
       [ 0.02845014,  0.03875538],
       [ 0.0014258 ,  0.00919808],
       [ 0.00146328,  0.00586119],
       [ 0.00239688,  0.00613658],
       [ 0.00115668,  0.00374091],
       [ 0.03076452,  0.04215164],
       [ 0.02672348,  0.0371134 ],
       [ 0.03347464,  0.04213674],
       [ 0.01526087,  0.02672747],
       [ 0.02966219,  0.04072735],
       [ 0.00352447,  0.00564346],
       [ 0.01801714,  0.02976476],
       [ 0.01646361,  0.02855856],
       [ 0.0054977 ,  0.00871516],
       [ 0.00510191,  0.01101049],
       [ 0.00434285,  0.01231152],
       [ 0.00180327,  0.00679755],
       [ 0.00855906,  0.02016482],
       [ 0.00085589,  0.0041427 ],
       [ 0.00134921,  0.00381741],
       [ 0.0055793 ,  0.01593253],
       [ 0.01086436,  0.02430496],
       [ 0.04177298,  0.04736704],
       [ 0.02785621,  0.03901125],
       [ 0.0003699 ,  0.0035194 ],
       [ 0.0335931 ,  0.04303309],
       [ 0.00192898,  0.00541728],
       [ 0.02766663,  0.03905752],
       [ 0.01510733,  0.02975172],
       [-0.0019367 ,  0.01310729],
       [ 0.04183919,  0.04749531],
       [ 0.0054169 ,  0.01458852],
       [ 0.03947336,  0.04625987],
       [ 0.00088668,  0.00218999],
       [ 0.0018509 ,  0.00399135],
       [ 0.00184258,  0.01542454],
       [ 0.02781397,  0.03904086],
       [ 0.00704583,  0.0217159 ],
       [ 0.00287864,  0.00488894],
       [ 0.00121556,  0.00302431],
       [ 0.00226235,  0.00891779],
       [ 0.01002425,  0.01163484],
       [ 0.02964206,  0.03949914]])

util_hi_200 = np.array([0.37188409, 0.3472088 , 0.29046848, 0.29896709, 0.13418097,
       0.1040221 , 0.21037333, 0.1437602 , 0.34802587, 0.29961495,
       0.36701737, 0.23343354, 0.30578103, 0.12450043, 0.22782834,
       0.16437348, 0.18729798, 0.30628096, 0.1411846 , 0.1462066 ,
       0.28661909, 0.14749196, 0.09411836, 0.34026474, 0.26278081,
       0.34163264, 0.29867486, 0.12684136, 0.29122923, 0.14753854,
       0.34717121, 0.36797902, 0.22149696, 0.31806562, 0.25209148,
       0.33839784, 0.06571512, 0.12146227, 0.27920259, 0.33397687,
       0.24516908, 0.13125581, 0.0767291 , 0.16996685, 0.20791195,
       0.31383499])
util_hi_200_CI = np.array([[0.35990119, 0.38386699],
       [0.33328247, 0.36113513],
       [0.27877266, 0.3021643 ],
       [0.29075496, 0.30717921],
       [0.12802413, 0.14033782],
       [0.09884948, 0.10919472],
       [0.19734519, 0.22340146],
       [0.13395377, 0.15356663],
       [0.33493226, 0.36111948],
       [0.2889594 , 0.31027051],
       [0.35268281, 0.38135194],
       [0.22608113, 0.24078595],
       [0.29370282, 0.31785923],
       [0.11747668, 0.13152417],
       [0.22126998, 0.2343867 ],
       [0.15352857, 0.1752184 ],
       [0.17893702, 0.19565895],
       [0.29396261, 0.31859931],
       [0.1341091 , 0.14826009],
       [0.13693995, 0.15547326],
       [0.27396173, 0.29927645],
       [0.13669349, 0.15829042],
       [0.08835816, 0.09987856],
       [0.324842  , 0.35568747],
       [0.25192751, 0.27363412],
       [0.33101901, 0.35224626],
       [0.28854371, 0.308806  ],
       [0.11753258, 0.13615013],
       [0.2821493 , 0.30030917],
       [0.14135615, 0.15372094],
       [0.33630217, 0.35804026],
       [0.35304913, 0.38290892],
       [0.20834926, 0.23464466],
       [0.30929871, 0.32683253],
       [0.24330177, 0.2608812 ],
       [0.32839709, 0.34839858],
       [0.06079875, 0.07063148],
       [0.11449782, 0.12842671],
       [0.2652926 , 0.29311259],
       [0.32130054, 0.34665319],
       [0.23121661, 0.25912155],
       [0.12284913, 0.13966249],
       [0.0714067 , 0.08205151],
       [0.16448112, 0.17545257],
       [0.20088792, 0.21493597],
       [0.30470123, 0.32296874]])
       
plt.scatter(util_lo_60, util_lo_200)
plt.plot(np.arange(100)/2000,np.arange(100)/2000, color='gray')
plt.title('Scatter plot of 1-test utilities, 60k vs 200k truthdraws')
plt.ylabel('200k truth draws')
plt.xlabel('60k truth draws')
plt.show()

plt.scatter(util_hi_60, util_hi_200)
plt.plot(np.arange(100)/100,np.arange(100)/100, color='gray')
plt.title('Scatter plot of 81-test utilities, 60k vs 200k truthdraws')
plt.ylabel('200k truth draws')
plt.xlabel('60k truth draws')
plt.xlim([0,1])
plt.ylim([0,1])
plt.show()
'''

''' RUNS 7-MAR (81 tests at all districts)
Bakel               0.3804905943479593 (0.37531994211371256, 0.385661246582206)
Bambey              0.3537908316260996 (0.3474585325224755, 0.3601231307297237)
Bignona             0.303304650040106 (0.2975468347532466, 0.30906246532696535)
Birkilane           0.30183608790021665 (0.29794423499694034, 0.30572794080349297)
Bounkiling          0.13796590865289637 (0.13071163145257358, 0.14522018585321916)
Dagana              0.10617503170720077 (0.10383079104924242, 0.10851927236515913)
Dakar               0.22373887063283782 (0.21817512842645392, 0.2293026128392217)
Diourbel            0.15011867225809894 (0.14573581193779894, 0.15450153257839894)
Fatick              0.36544388135986416 (0.35752176288448645, 0.3733659998352419)
Foundiougne         0.3149454272197083 (0.31022985081163945, 0.31966100362777716)
Gossas              0.38013122163191326 (0.3726337331724885, 0.38762871009133804)
Goudiry             0.23679760643748615 (0.23286394366552798, 0.24073126920944432)
Goudoump            0.327926416525667 (0.3222128401148101, 0.3336399929365239)
Guediawaye          0.12678496714767284 (0.1233906005998513, 0.1301793336954944)
Guinguineo          0.22963783064008148 (0.22679676719415554, 0.23247889408600741)
Kaffrine            0.16052526719445837 (0.1562230766027355, 0.16482745778618124)
Kanel               0.1939563786495757 (0.19066492103026178, 0.19724783626888964)
Kaolack             0.3146963006621952 (0.3082350976922825, 0.32115750363210793)
Kebemer             0.1449245487831039 (0.14152012880917297, 0.14832896875703483)
Kedougou            0.15031593463413095 (0.14607722324234196, 0.15455464602591995)
Keur Massar         0.3090183459309941 (0.3027306635924152, 0.315306028269573)
Kolda               0.1564661415465327 (0.15152531714038808, 0.16140696595267734)
Koumpentoum         0.09916213199920776 (0.09633754780882953, 0.10198671618958599)
Koungheul           0.3639154928606363 (0.35134468929145335, 0.37648629642981923)
Linguere            0.27414127359790363 (0.2690590390256844, 0.27922350817012287)
Louga               0.34476435295838925 (0.339767604724031, 0.3497611011927475)
Malem Hoddar        0.3091165949825321 (0.3022180910157495, 0.3160150989493147)
Matam               0.1341658013164153 (0.12862327785507865, 0.13970832477775197)
Mbacke              0.293752165195567 (0.28868280074570407, 0.29882152964542996)
Mbour               0.1461594728108544 (0.1433399413509271, 0.1489790042707817)
Medina Yoro Foulah  0.3765023693473264 (0.37114678736181617, 0.3818579513328366)
Nioro du Rip        0.38460948750299195 (0.3763234905639887, 0.3928954844419952)
Oussouye            0.24461286092555845 (0.23811357237739195, 0.25111214947372495)
Pikine              0.3222567851834839 (0.3179078574511127, 0.32660571291585505)
Podor               0.2742522651800421 (0.26581043772924673, 0.28269409263083745)
Ranerou Ferlo       0.3394313127669566 (0.33297046963369326, 0.34589215590021993)
Rufisque            0.07124513033692992 (0.06922921125947745, 0.07326104941438238)
Saint-Louis         0.12586430746292088 (0.12216911472668102, 0.12955950019916074)
Salemata            0.29759841099845374 (0.2811954020445331, 0.3140014199523744)
Saraya              0.33683449620171935 (0.33037365665778573, 0.34329533574565296)
Sedhiou             0.272007403464686 (0.2628897141959552, 0.2811250927334168)
Tambacounda         0.12905557231962206 (0.12494546402022877, 0.13316568061901535)
Thies               0.08009970771387387 (0.07744959931028816, 0.08274981611745957)
Tivaoune            0.1733016776058509 (0.16927234523031487, 0.17733100998138696)
Velingara           0.2341150853530749 (0.23025985898946466, 0.23797031171668515)
Ziguinchor          0.3201464489800685 (0.3131644019882689, 0.3271284959718681)
'''

''' RUNS 29-DEC
Bakel       0.03344590816593218 (0.03147292119474443, 0.03541889513711993), 
105         0.43105884100510217 (0.4231565417533414, 0.43896114025686295)
Bambey      0.03446700691774751 (0.031950294730139106, 0.03698371910535592)
269         0.7031888278193428 (0.65970263766636, 0.7466750179723256)
Bignona     0.030668690359265227 (0.02772583763711367, 0.033611543081416784)
140         0.37932139488912675 (0.3699972836620251, 0.3886455061162284)
Birkilane   0.03730134595455681 (0.034801214687281146, 0.03980147722183247)
238         0.4684099921669258 (0.4473053150611417, 0.4895146692727099)
Bounkiling  0.00453539247349255 (0.002933726625375499, 0.006137058321609601)
160         0.19396182550914354 (0.18843369234668472, 0.19948995867160235)
Dagana      0.004221436878848905 (0.003648644574480997, 0.004794229183216814)
195         0.14442075719252045 (0.14172686992181838, 0.14711464446322253)
Dakar       0.005222521081899245 (0.00429602215599445, 0.00614902000780404)
345         0.7332074114707208 (0.6865241407062364, 0.7798906822352052)
Diourbel    0.0023157423073154604 (0.0017679128534258126, 0.002863571761205108)
279         0.4526505991558132 (0.43015147401770193, 0.47514972429392444)
Fatick      0.033057486817286375 (0.030502717710007232, 0.03561225592456552)
273         0.7870853278437675 (0.7379427810124408, 0.8362278746750942)
Foundiougne 0.030612648885227856 (0.028847718182849036, 0.032377579587606675)
262         0.6110077584821685 (0.5739668037064192, 0.6480487132579178)

Gossas      0.04035724365910198 (0.03823470069321111, 0.042479786624992855)
257         0.7768547796500158 (0.7313417312562365, 0.8223678280437952)
Goudiry     0.022376695174909145 (0.0197621780011783, 0.02499121234863999)
152         0.29077391079703396 (0.28527535885379685, 0.2962724627402711)
Goudoump    0.03246600245761755 (0.029396877391432596, 0.0355351275238025)
124         0.3991144287361781 (0.3891039816752997, 0.4091248757970565)
Guediawaye  0.003474985346775483 (0.00289235462568449, 0.004057616067866476)
337         0.3502283652990581 (0.32466299834520385, 0.37579373225291235)
Guinguineo  0.02463908710868168 (0.022144656133576746, 0.027133518083786612)
249         0.3550276878136227 (0.34520036788485875, 0.36485500774238666)
Kaffrine    0.019184733052625802 (0.016111662656829395, 0.02225780344842221)
246         0.1849251993905554 (0.1779138024370006, 0.1919365963441102)
Kanel       0.005615564431058928 (0.004491138016824436, 0.00673999084529342)
175         0.3166100525107627 (0.30659025767436177, 0.3266298473471636)
Kaolack     0.008077416250422687 (0.006987441620362134, 0.00916739088048324)
260         0.7693792703784261 (0.7167354411006137, 0.8220230996562385)
Kebemer     0.010021691126443244 (0.008382621588113537, 0.011660760664772951)
244         0.21169123555459635 (0.2036658292848088, 0.21971664182438388)
Kedougou    0.004622782266665126 (0.003534646565491073, 0.00571091796783918)
117         0.18660775557903442 (0.1818373281647503, 0.19137818299331855)

Keur Massar 0.014243077724529485 (0.011471001293502425, 0.017015154155556544)
331         0.9200794423858429 (0.8648056849066883, 0.9753531998649976)
Kolda       0.002037553399144798 (0.0013381624829147398, 0.0027369443153748563)
112         0.21282807614512578 (0.20657330231725624, 0.21908284997299532)
Koumpentoum 0.001837844117927645 (0.0013401330073055107, 0.0023355552285497794)
155         0.16130278944481447 (0.15421666366154518, 0.16838891522808375)
Koungheul   0.005958355996412479 (0.0032371586407347053, 0.008679553352090252)
220         0.8893761338488027 (0.8415404583036743, 0.937211809393931)
Linguere    0.023307561121377773 (0.020134139803062112, 0.026480982439693435)
220         0.4654293821834443 (0.4388915848036472, 0.49196717956324143)
Louga       0.04462919926853459 (0.0434930674904237, 0.045765331046645485)
256         0.5828677042452295 (0.5479830671754176, 0.6177523413150414)
Malem Hoddar 0.036963849376093094 (0.03432851841861506, 0.03959918033357113)
223         0.47925973508820086 (0.4575227352029838, 0.5009967349734179)
Matam       0.0017134181987543684 (0.0012377717127680654, 0.0021890646847406714)
186         0.30697219152920674 (0.29423108868685155, 0.31971329437156193)
Mbacke      0.03962200876619093 (0.03740724300849685, 0.04183677452388501)
262         0.539087483444483 (0.5076969390261539, 0.5704780278628121)
Mbour       0.004014208828177601 (0.0032230176553138534, 0.004805400001041349)
266         0.2988236526257886 (0.2859534915793649, 0.31169381367221227)

Medina Yoro Foulah  0.031313789620442734 (0.029094008390853077, 0.03353357085003239)
70          0.3478566858681411 (0.3428632527540856, 0.35285011898219665)
Nioro du Rip    0.020612520831246428 (0.01698734956440795, 0.024237692098084906)
237         0.7957091962059106 (0.7609762725154461, 0.8304421198963752)
Oussouye    0.014096679242264543 (0.011656996567028344, 0.01653636191750074)
139         0.3441531228927115 (0.32833374427729645, 0.35997250150812654)
Pikine      0.04275233768036024 (0.04106823091015954, 0.04443644445056094)
336         0.6039066333258916 (0.5763165260770453, 0.6314967405747378)
Podor       0.009014961850546399 (0.006746567570228734, 0.011283356130864064)
164         0.36804361762671434 (0.36054774036625226, 0.3755394948871764)
Ranerou Ferlo  0.043110473939085736 (0.04176223564747694, 0.04445871223069453)
156         0.4522621316194151 (0.4394551485590643, 0.46506911467976586)
Rufisque    0.0014522699815096018 (0.001235590164801792, 0.0016689497982174117)
331         0.16007125628290986 (0.15167964313722138, 0.16846286942859834)
Saint-Louis 0.0020741220800317706 (0.001562028404910265, 0.002586215755153276)
236         0.357343950511666 (0.3264681997601997, 0.3882197012631323)
Salemata    0.012867779656367873 (0.010333547338657212, 0.015402011974078533)
88          0.3081576517058906 (0.3010332020937021, 0.3152821013180791)
Saraya      0.03405235123314121 (0.03179264426409212, 0.0363120582021903)
96          0.3619272721051523 (0.35467181345444665, 0.36918273075585795)

Sedhiou     0.013699743194225178 (0.010308593634334784, 0.017090892754115572)
180         0.446511053424965 (0.43037365667027494, 0.46264845017965506)
Tambacounda 0.002280675983080016 (0.0016242354636233358, 0.0029371165025366963)
184         0.258103204929494 (0.24579102463791713, 0.2704153852210709)
Thies       0.0017215048828003177 (0.0012758859177921522, 0.002167123847808483)
286         0.1784259311634564 (0.17022302576640413, 0.18662883656050866)
Tivaoune    0.008694595616617562 (0.007417164487003802, 0.009972026746231322)
273         0.2801971121810034 (0.2692235029128298, 0.291170721449177)
Velingara   0.009936752611013233 (0.00939940371292991, 0.010474101509096556)
69          0.2105445784493476 (0.20662048135186772, 0.21446867554682747)
Ziguinchor  0.0357728378865243 (0.034026750551074514, 0.037518925221974087)
155         0.4271828935412305 (0.41682005238472186, 0.43754573469773916)
'''

# How different are the ultimate h_d*n_d vals when using old bounds vs new bounds (81 tests)?
k_list_old, k_list_new = [], []
utileval_list_old, utileval_list_new = [], []
names_list = []
#lvec, juncvec, m1vec, m2vec, bds, lovals, hivals = [], [], [], [], [], [], []
for ind, row in util_df.iterrows():
    currBound, loval, oldhival, newhival = row[1], row[2], row[6], row[4]
    # Get interpolation values
    _, _, l_old, k_old, m1_old, m2_old = GetTriangleInterpolation([0, 1, currBound], [0, loval, oldhival])
    _, _, l_new, k_new, m1_new, m2_new = GetTriangleInterpolation([0, 1, 81], [0, loval, newhival])
    k_list_old.append(k_old)
    k_list_new.append(k_new)
    utileval_list_old.append(l_old+k_new * m1_old)
    utileval_list_new.append(l_new + k_new * m1_new)
    names_list.append(row[0])

# How do the k values compare?
fig, ax = plt.subplots()
plt.scatter(k_list_old, k_list_new)
plt.plot(np.arange(200),np.arange(200),alpha=0.2,color='gray')
plt.ylim([0,200])
plt.xlim([0,200])
for i in range(numTN):
    ax.text(k_list_old[i], k_list_new[i], names_list[i], size=7)
plt.title('Plot of $h_d$ junctures')
plt.xlabel('Budget-based (hi) bound')
plt.ylabel('Prior data-based (lo) bound')
plt.show()

# How do the resulting separable utility values compare?
fig, ax = plt.subplots()
plt.scatter(utileval_list_old, utileval_list_new)
plt.plot(np.arange(100)/100,np.arange(100)/100,alpha=0.2,color='gray')
plt.ylim([0,0.4])
plt.xlim([0,0.4])
for i in range(numTN):
    ax.text(utileval_list_old[i], utileval_list_new[i], names_list[i], size=7)
plt.title('Plot of separable utility estimates at lo-based $h_d$ junctures')
plt.xlabel('Budget-based (hi) bound')
plt.ylabel('Prior data-based (lo) bound')
plt.show()

### GENERATE PATHS FOR CASE STUDY ###
# What is the upper bound on the number of regions in any feasible tour that uses at least one test?
maxregnum = GetSubtourMaxCardinality(optparamdict=optparamdict)

mastlist = []
for regamt in range(1, maxregnum):
    mastlist = mastlist + list(itertools.combinations(np.arange(1,numReg).tolist(), regamt))

print('Number of feasible region combinations:',len(mastlist))

# For storing best sequences and their corresponding costs
seqlist, seqcostlist = [], []

for tup in mastlist:
    tuplist = [tup[i] for i in range(len(tup))]
    tuplist.insert(0,0) # Add HQind to front of list
    bestseqlist, bestseqcost = FindTSPPathForGivenNodes(tuplist, f_reg)
    seqlist.append(bestseqlist)
    seqcostlist.append(bestseqcost)

# For each path, generate a binary vector indicating if each district is accessible on that path
# First get names of accessible districts
distaccesslist = []
for seq in seqlist:
    currdistlist = []
    for ind in seq:
        currdist = GetDeptChildren(regNames[ind],dept_df)
        currdistlist = currdistlist+currdist
    currdistlist.sort()
    distaccesslist.append(currdistlist)

# Next translate each list of district names to binary vectors
bindistaccessvectors = []
for distlist in distaccesslist:
    distbinvec = [int(i in distlist) for i in deptNames]
    bindistaccessvectors.append(distbinvec)

paths_df_all = pd.DataFrame({'Sequence':seqlist,'Cost':seqcostlist,'DistAccessBinaryVec':bindistaccessvectors})

# Remove all paths with cost exceeding budget - min{district access} - sampletest
paths_df = paths_df_all[paths_df_all['Cost'] < B].copy()
# Remaining paths require at least one district and one test in each visited region
boolevec = [True for i in range(paths_df.shape[0])]
for i in range(paths_df.shape[0]):
    rowseq, rowcost = paths_df.iloc[i]['Sequence'], paths_df.iloc[i]['Cost']
    mindistcost = 0
    for reg in rowseq:
        if reg != 0:
            mindistcost += f_dept[[deptNames.index(x) for x in GetDeptChildren(regNames[reg], dept_df)]].min()
    # Add district costs, testing costs, and path cost
    mincost = mindistcost + (len(rowseq)-1)*ctest + rowcost
    if mincost > B:
        boolevec[i] = False

paths_df = paths_df[boolevec]

# Update cost list and district access vectors to reflect these dropped paths
seqlist_trim = paths_df['Sequence'].copy()
seqcostlist_trim = paths_df['Cost'].copy()
bindistaccessvectors_trim = np.array(paths_df['DistAccessBinaryVec'].tolist())
seqlist_trim = seqlist_trim.reset_index()
seqlist_trim = seqlist_trim.drop(columns='index')
seqcostlist_trim = seqcostlist_trim.reset_index()
seqcostlist_trim = seqcostlist_trim.drop(columns='index')



# Save to avoid generating later
# paths_df.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'paths.pkl'))

# paths_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'paths.pkl'))
###################################
###################################
###################################
# MAIN OPTIMIZATION BLOCK
###################################
###################################
###################################

# First need to obtain vectors of zero intercepts, junctures, and interpolation slopes for each of our Utilde evals
#   at each district
lvec, juncvec, m1vec, m2vec, bds, lovals, hivals = [], [], [], [], [], [], []
for ind, row in util_df.iterrows():
    currBound, loval, hival = row[1], row[2], row[4]
    # Get interpolation values
    _, _, l, k, m1, m2 = GetTriangleInterpolation([0, 1, currBound], [0, loval, hival])
    lvec.append(l)
    juncvec.append(k)
    m1vec.append(m1)
    m2vec.append(m2)
    bds.append(currBound)
    lovals.append(loval)
    hivals.append(hival)

# What is the curvature, kappa, for our estimates?
kappavec = [1-m2vec[i]/m1vec[i] for i in range(len(m2vec))]
plt.hist(kappavec)
plt.title('Histogram of $\kappa$ curvature at each district')
plt.show()

# Make histograms of our interpolated values
plt.hist(lvec,color='darkorange', density=True)
plt.title("Histogram of interpolation intercepts\n($l$ values)",
          fontsize=14)
plt.xlabel(r'$l$',fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.show()

# interpolated junctures
plt.hist(juncvec, color='darkgreen', density=True)
plt.title('Histogram of interpolation slope junctures\n($j$ values)',
          fontsize=14)
plt.xlabel(r'$j$',fontsize=12)
plt.ylabel('Density',fontsize=12)
plt.show()

# interpolated junctures, as percentage of upper bound
juncvecperc = [juncvec[i]/bds[i] for i in range(len(juncvec))]
plt.hist(juncvecperc, color='darkgreen', density=True)
plt.title('Histogram of interpolation junctures vs. allocation bounds\n($h_d/'+r'n^{max}_d$ values)',
          fontsize=14)
plt.xlabel(r'$h_d/n^{max}_d$',fontsize=12)
plt.ylabel('Density',fontsize=12)
plt.show()

plt.hist(m1vec,color='purple', density=True)
plt.title('Histogram of first interpolation slopes\n($m^{(1)}$ values)'
          , fontsize=14)
plt.xlabel('$m^{(1)}$', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.xlim([0,0.025])
plt.show()

plt.hist(m2vec,color='orchid', density=True)
plt.title('Histogram of second interpolation slopes\n($m^{(2)}$ values)'
          , fontsize=14)
plt.xlabel('$m^{(2)}$', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.xlim([0,0.025])
plt.show()

# Now we construct our various program vectors and matrices per the scipy standards
numPath = paths_df.shape[0]

# Variable bounds
# Variable vectors are in form (z, n, x) [districts, allocations, paths]
lbounds = np.concatenate((np.zeros(numTN*3), np.zeros(numPath)))
ubounds = np.concatenate((np.ones(numTN),
                          np.array([juncvec[i]-1 for i in range(numTN)]),
                          np.array(util_df['Bounds'].tolist()) - np.array([juncvec[i] - 1 for i in range(numTN)]),
                          np.ones(numPath)))

optbounds = spo.Bounds(lbounds, ubounds)

# Objective vector; negated as milp requires minimization
optobjvec = -np.concatenate((np.array(lvec), np.array(m1vec), np.array(m2vec), np.zeros(numPath)))

### Constraints
# Build lower and upper inequality values
optconstrlower = np.concatenate(( np.ones(numTN*4+1) * -np.inf, np.array([1])))
optconstrupper = np.concatenate((np.array([B]), np.zeros(numTN*2), np.array(juncvec), np.zeros(numTN), np.array([1])))

# Build A matrix, from left to right
# Build z district binaries first
optconstraintmat1 = np.vstack((f_dept, -bigM*np.identity(numTN), np.identity(numTN), 0*np.identity(numTN),
                              np.identity(numTN), np.zeros(numTN)))
# n^' matrices
optconstraintmat2 = np.vstack((ctest*np.ones(numTN), np.identity(numTN), -np.identity(numTN), np.identity(numTN),
                              0*np.identity(numTN), np.zeros(numTN)))
# n^'' matrices
optconstraintmat3 = np.vstack((ctest*np.ones(numTN), np.identity(numTN), -np.identity(numTN), 0*np.identity(numTN),
                              0*np.identity(numTN), np.zeros(numTN)))
# path matrices
optconstraintmat4 = np.vstack((np.array(seqcostlist_trim).T, np.zeros((numTN*3, numPath)),
                               (-bindistaccessvectors_trim).T, np.ones(numPath)))

optconstraintmat = np.hstack((optconstraintmat1, optconstraintmat2, optconstraintmat3, optconstraintmat4))

optconstraints = spo.LinearConstraint(optconstraintmat, optconstrlower, optconstrupper)

# Define integrality for all variables
optintegrality = np.ones_like(optobjvec)

# Solve
spoOutput = milp(c=optobjvec, constraints=optconstraints, integrality=optintegrality, bounds=optbounds)
soln_loBudget, UB_loBudget = spoOutput.x, spoOutput.fun*-1
# 13-MAR-24: 1.419

# Evaluate utility of solution
n1 = soln_loBudget[numTN:numTN * 2]
n2 = soln_loBudget[numTN * 2:numTN * 3]
n_init = n1+n2
u_init, u_init_CI = getUtilityEstimate(n_init, lgdict, paramdict)
# 13-MAR-24: (1.3250307414145919, (1.2473679675065128, 1.402693515322671))
LB_loBudget = u_init

opf.scipytoallocation(soln_loBudget, deptNames, regNames, seqlist_trim, eliminateZeros=True)

##########################
##########################
# Generate 30 additional candidates for lo budget
##########################
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
    # List of eligible path indices
    eligPathInds = []
    # Dataframe of paths and their IP-RP objectives
    candpaths_df = paths_df.copy()
    candpaths_df.insert(3, 'RPobj', np.zeros(numPath).tolist(), True)
    candpaths_df.insert(4, 'DistCost', np.zeros(numPath).tolist(), True)  # Add column to store RP district costs
    candpaths_df.insert(5, 'Uoracle', np.zeros(numPath).tolist(), True)  # Add column for oracle evals
    candpaths_df.insert(6, 'UoracleCIlo', np.zeros(numPath).tolist(), True)  # Add column for oracle eval CIs
    candpaths_df.insert(7, 'UoracleCIhi', np.zeros(numPath).tolist(), True)  # Add column for oracle eval CIs
    # IP-RP for each path
    for pathind in range(numPath):
        pathconstraint = GetConstraintsWithPathCut(numPath + numTN * 3, numTN, pathind)
        curr_spoOutput = milp(c=opt_obj, constraints=(opt_constr, pathconstraint),
                              integrality=opt_integ, bounds=opt_bds)
        candpaths_df.iloc[pathind, 3] = curr_spoOutput.fun * -1
        candpaths_df.iloc[pathind, 4] = (curr_spoOutput.x[:numTN] * f_dist).sum()
        if curr_spoOutput.fun * -1 > LB:
            eligPathInds.append(pathind)
            opf.scipytoallocation(np.round(curr_spoOutput.x), distNames, regNames, seqlist_trim_df, True)
            if printUpdate:
                print('Path ' + str(pathind) + ' cost: ' + str(candpaths_df.iloc[pathind, 1]))
                print('Path ' + str(pathind) + ' RP utility: ' + str(candpaths_df.iloc[pathind, 3]))
    return eligPathInds, candpaths_df

eligPathInds, candpaths_df_700 = GetEligiblePathInds(paths_df, deptNames, regNames, optobjvec, optconstraints,
                                                     optintegrality, optbounds, f_dept, LB_loBudget, seqlist_trim)

# Save to avoid generating later
candpaths_df_700.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'candpaths_df_700.pkl'))







###################
###################
# Update to hi budget
###################
###################
B = 1400

optparamdict = {'batchcost':batchcost, 'budget':B, 'pertestcost':ctest, 'Mconstant':bigM, 'batchsize':batchsize,
                'deptfixedcostvec':f_dept, 'arcfixedcostmat': f_reg, 'reghqname':'Dakar', 'reghqind':0,
                'deptnames':deptNames, 'regnames':regNames, 'dept_df':dept_df_sort}

maxregnum = GetSubtourMaxCardinality(optparamdict=optparamdict)

# TODO: UPDATE LATER IF ANY GOOD SOLUTIONS USE 9 REGIONS
maxregnum = maxregnum - 1

mastlist = []
for regamt in range(1, maxregnum):
    mastlist = mastlist + list(itertools.combinations(np.arange(1,numReg).tolist(), regamt))

print('Number of feasible region combinations:',len(mastlist))

# For storing best sequences and their corresponding costs
seqlist, seqcostlist = [], []

kiter = 0 #These take longer with more possible regional subsets
for tup in mastlist:
    kiter += 1
    tuplist = [tup[i] for i in range(len(tup))]
    tuplist.insert(0,0) # Add HQind to front of list
    bestseqlist, bestseqcost = FindTSPPathForGivenNodes(tuplist, f_reg)
    seqlist.append(bestseqlist)
    seqcostlist.append(bestseqcost)
    if np.mod(kiter+1,250)==0:
        print('On tuple '+str(kiter+1))

# For each path, generate a binary vector indicating if each district is accessible on that path
# First get names of accessible districts
distaccesslist = []
for seq in seqlist:
    currdistlist = []
    for ind in seq:
        currdist = GetDeptChildren(regNames[ind],dept_df)
        currdistlist = currdistlist+currdist
    currdistlist.sort()
    distaccesslist.append(currdistlist)

# Next translate each list of district names to binary vectors
bindistaccessvectors = []
for distlist in distaccesslist:
    distbinvec = [int(i in distlist) for i in deptNames]
    bindistaccessvectors.append(distbinvec)

paths_df_all_hibudget = pd.DataFrame({'Sequence':seqlist,'Cost':seqcostlist,'DistAccessBinaryVec':bindistaccessvectors})

# Remove all paths with cost exceeding budget - min{district access} - sampletest
paths_df = paths_df_all_hibudget[paths_df_all_hibudget['Cost'] < B].copy()
# Remaining paths require at least one district and one test in each visited region
boolevec = [True for i in range(paths_df.shape[0])]
for i in range(paths_df.shape[0]):
    rowseq, rowcost = paths_df.iloc[i]['Sequence'], paths_df.iloc[i]['Cost']
    mindistcost = 0
    for reg in rowseq:
        if reg != 0:
            mindistcost += f_dept[[deptNames.index(x) for x in GetDeptChildren(regNames[reg], dept_df)]].min()
    # Add district costs, testing costs, and path cost
    mincost = mindistcost + (len(rowseq)-1)*ctest + rowcost
    if mincost > B:
        boolevec[i] = False

paths_df = paths_df[boolevec]

# Update cost list and district access vectors to reflect these dropped paths
seqlist_trim = paths_df['Sequence'].copy()
seqcostlist_trim = paths_df['Cost'].copy()
bindistaccessvectors_trim = np.array(paths_df['DistAccessBinaryVec'].tolist())
seqlist_trim = seqlist_trim.reset_index()
seqlist_trim = seqlist_trim.drop(columns='index')
seqcostlist_trim = seqcostlist_trim.reset_index()
seqcostlist_trim = seqcostlist_trim.drop(columns='index')

# Now we construct our various program vectors and matrices per the scipy standards
numPath = paths_df.shape[0]

# Variable bounds
# Variable vectors are in form (z, n, x) [districts, allocations, paths]
lbounds = np.concatenate((np.zeros(numTN*3), np.zeros(numPath)))
ubounds = np.concatenate((np.ones(numTN),
                          np.array([juncvec[i]-1 for i in range(numTN)]),
                          np.array(util_df['Bounds'].tolist()) - np.array([juncvec[i] - 1 for i in range(numTN)]),
                          np.ones(numPath)))

optbounds = spo.Bounds(lbounds, ubounds)

# Objective vector; negated as milp requires minimization
optobjvec = -np.concatenate((np.array(lvec), np.array(m1vec), np.array(m2vec), np.zeros(numPath)))

### Constraints
# Build lower and upper inequality values
optconstrlower = np.concatenate(( np.ones(numTN*4+1) * -np.inf, np.array([1])))
optconstrupper = np.concatenate((np.array([B]), np.zeros(numTN*2), np.array(juncvec), np.zeros(numTN), np.array([1])))

# Build A matrix, from left to right
# Build z district binaries first
optconstraintmat1 = np.vstack((f_dept, -bigM*np.identity(numTN), np.identity(numTN), 0*np.identity(numTN),
                              np.identity(numTN), np.zeros(numTN)))
# n^' matrices
optconstraintmat2 = np.vstack((ctest*np.ones(numTN), np.identity(numTN), -np.identity(numTN), np.identity(numTN),
                              0*np.identity(numTN), np.zeros(numTN)))
# n^'' matrices
optconstraintmat3 = np.vstack((ctest*np.ones(numTN), np.identity(numTN), -np.identity(numTN), 0*np.identity(numTN),
                              0*np.identity(numTN), np.zeros(numTN)))
# path matrices
optconstraintmat4 = np.vstack((np.array(seqcostlist_trim).T, np.zeros((numTN*3, numPath)),
                               (-bindistaccessvectors_trim).T, np.ones(numPath)))

optconstraintmat = np.hstack((optconstraintmat1, optconstraintmat2, optconstraintmat3, optconstraintmat4))

optconstraints = spo.LinearConstraint(optconstraintmat, optconstrlower, optconstrupper)

# Define integrality for all variables
optintegrality = np.ones_like(optobjvec)

# Solve
spoOutput = milp(c=optobjvec, constraints=optconstraints, integrality=optintegrality, bounds=optbounds)
soln_hiBudget, UB_hiBudget = spoOutput.x, spoOutput.fun*-1

opf.scipytoallocation(soln_hiBudget, deptNames, regNames, seqlist_trim, eliminateZeros=True)


##########################
##########################
# Generate 30 additional candidates
##########################
##########################
numtruthdraws, numdatadraws = 200000, 100
# Get random subsets for truth and data draws
np.random.seed(56)
truthdraws, datadraws = util.distribute_truthdata_draws(lgdict['postSamples'], numtruthdraws, numdatadraws)
paramdict.update({'truthdraws': truthdraws, 'datadraws': datadraws})
# Get base loss
paramdict['baseloss'] = sampf.baseloss(paramdict['truthdraws'], paramdict)
util.print_param_checks(paramdict)

# Calculate current utility to establish a lower bound for comparison with candidates
n1 = soln_hiBudget[numTN:numTN * 2]
n2 = soln_hiBudget[numTN * 2:numTN * 3]
n_init = n1+n2
u_init, u_init_CI = getUtilityEstimate(n_init, lgdict, paramdict)
LB = u_init
#todo: 13-MAR-24: 5.049080819723875 with 60k/1000 draws
#todo: 13-MAR-24: 4.239 with 100k/100 draws
#todo: 13-MAR-24: 4.164 with 200k/100 draws

# todo: TEMPORARY STUDY 13-MAR; REMOVE LATER
z_init = soln_hiBudget[:numTN]
# Get new interpolations with more data draws and see if this helps with inverted gap
util_lo, util_lo_CI = [], []
util_hi, util_hi_CI = [], []
for i in range(len(deptNames)):
    if z_init[i] == 1:
        currbd = int(deptallocbds[i])
        print('Getting utility for ' + deptNames[i] + ', at 1 test...')
        n = np.zeros(numTN)
        n[i] = 1
        currlo, currlo_CI = getUtilityEstimate(n, lgdict, paramdict)
        print(currlo, currlo_CI)
        util_lo.append(currlo)
        util_lo_CI.append(currlo_CI)
        print('Getting utility for ' + deptNames[i] + ', at ' + str(currbd) + ' tests...')
        n[i] = currbd
        currhi, currhi_CI = getUtilityEstimate(n, lgdict, paramdict)
        print(currhi, currhi_CI)
        util_hi.append(currhi)
        util_hi_CI.append(currhi_CI)

# Compare resulting interp values with currently used ones here













# Prep a new paths dataframe

# Or load
# phase2paths_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'phase2paths.pkl'))

phase2paths_df = paths_df.copy()
phase2paths_df.insert(3, 'RPobj', np.zeros(numPath).tolist(), True)
phase2paths_df.insert(4, 'DistCost', np.zeros(numPath).tolist(), True) # Add column to store RP district costs
phase2paths_df.insert(5, 'Uoracle', np.zeros(numPath).tolist(), True) # Add column for oracle evals
phase2paths_df.insert(6, 'UoracleCIlo', [0 for i in range(numPath)], True) # Add column for oracle eval CIs
phase2paths_df.insert(7, 'UoracleCIhi', [0 for i in range(numPath)], True) # Add column for oracle eval CIs

# List of eligible path indices
eligPathInds = []

# IP-RP for each path
for pathind in range(numPath):
    pathconstraint = GetConstraintsWithPathCut(numPath+numTN*3, numTN, pathind)
    curr_spoOutput = milp(c=optobjvec, constraints=(optconstraints, pathconstraint),
                          integrality=optintegrality, bounds=optbounds)
    phase2paths_df.iloc[pathind, 3] = curr_spoOutput.fun*-1
    phase2paths_df.iloc[pathind, 4] = (curr_spoOutput.x[:numTN] * f_dept).sum()
    if curr_spoOutput.fun*-1 > LB:
        eligPathInds.append(pathind)
        opf.scipytoallocation(np.round(curr_spoOutput.x), deptNames, regNames, seqlist_trim, True)
        print('Path ' + str(pathind) + ' cost: ' + str(phase2paths_df.iloc[pathind, 1]))
        print('Path ' + str(pathind) + ' RP utility: ' + str(phase2paths_df.iloc[pathind, 3]))

# Save to avoid generating later
phase2paths_df.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'phase2paths.pkl'))





#todo:############################################################
#todo:####### THINGS BELOW HERE NEED TO BE EDITED ################
#todo:############################################################





### Inspect our solution
# How does our utility value compare with the real utility?
n1 = soln_loBudget[numTN:numTN * 2]
n2 = soln_loBudget[numTN * 2:numTN * 3]
n_init = n1+n2


time0 = time.time()
u_init, u_init_CI = getUtilityEstimate(n_init, lgdict, paramdict)
time1 = time.time() - time0
print(time1)

# This objective is our overall upper bound for the problem
UB = spoOutput.fun*-1

def getUtilityEstimateSequential(n, lgdict, paramdict, zlevel=0.95, datadrawsiter=50, eps=0.2, maxdatadraws=2000):
    """
    Return a utility estimate average and confidence interval for allocation array n that is epsperc of the estimate,
    by running data draws until the confidence interval is sufficiently small
    """
    testnum = int(np.sum(n))
    des = n/testnum

    # Modify paramdict to only have datadrawsiter data draws
    masterlosslist = []
    epsgap = 1.
    itercount = 0
    while len(masterlosslist) < maxdatadraws and epsgap > eps:
        itercount += 1
        print('Total number of data draws: ' + str(itercount*datadrawsiter))
        paramdictcopy = paramdict.copy()

        paramdictcopy.update({'datadraws':truthdraws[choice(np.arange(paramdict['truthdraws'].shape[0] ),
                                                            size=datadrawsiter, replace=False)]})
        util.print_param_checks(paramdictcopy)
        masterlosslist = masterlosslist + sampf.sampling_plan_loss_list(des, testnum, lgdict, paramdictcopy)
        currloss_avg, currloss_CI = sampf.process_loss_list(masterlosslist, zlevel=zlevel)
        # Get current gap
        epsgap = (currloss_CI[1]-currloss_CI[0])/(paramdict['baseloss'] -currloss_avg)
        print('New utility: ' + str(paramdict['baseloss'] - currloss_avg))
        print('New utility range: ' + str(epsgap))

    return paramdict['baseloss'] - currloss_avg, \
           (paramdict['baseloss']-currloss_CI[1], paramdict['baseloss']-currloss_CI[0]), masterlosslist

#############################
#############################
# BENCHMARK CONSTRUCTION (12-MAR-24)
#############################
#############################
# First for B=700
# LeastVisited
reglist_LeastVisited = [0, regNames.index('Diourbel'), regNames.index('Fatick')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_LeastVisited, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MostSFPs
reglist_MostSFP = [0, regNames.index('Diourbel'), regNames.index('Saint-Louis')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MostSFP, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MoreDistricts
reglist_MoreDistrict = [0, regNames.index('Diourbel'), regNames.index('Thies')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MoreDistrict, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MoreTests
reglist_MoreTest = [0, regNames.index('Thies')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MoreTest, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# Now B=1400
# LeastVisited
reglist_LeastVisited = [0, regNames.index('Fatick'), regNames.index('Diourbel'), regNames.index('Kaolack'),
                        regNames.index('Kaffrine'), regNames.index('Louga'), regNames.index('Tambacounda')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_LeastVisited, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MostSFPs
reglist_MostSFP = [0, regNames.index('Tambacounda'), regNames.index('Diourbel'),regNames.index('Saint-Louis'),
                   regNames.index('Kolda'),regNames.index('Matam')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MostSFP, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MoreDistricts
''' INCLUDES LOUGA
reglist_MoreDistricts = [0, regNames.index('Thies'), regNames.index('Diourbel'),regNames.index('Louga'),
                   regNames.index('Kaolack'), regNames.index('Kaffrine'), regNames.index('Fatick')]
FindTSPPathForGivenNodes(reglist_MoreDistricts, f_reg)
'''
reglist_MoreDistricts = [0, regNames.index('Thies'), regNames.index('Diourbel'),
                   regNames.index('Kaolack'), regNames.index('Kaffrine'), regNames.index('Fatick')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MoreDistricts, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# MoreTests
reglist_MoreTests = [0, regNames.index('Thies'), regNames.index('Diourbel'), regNames.index('Fatick')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_MoreTests, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)

# Opt Soln
reglist_optSoln = [0, regNames.index('Louga'), regNames.index('Diourbel'), regNames.index('Fatick'),
                   regNames.index('Kaffrine'), regNames.index('Kaolack')]
currRegList, currRegCost = FindTSPPathForGivenNodes(reglist_optSoln, f_reg)
for regind in currRegList:
    print(regNames[regind])
print(currRegCost)


##########################
##########################
# Evaluate utility of candidates and benchmarks
##########################
##########################







def utilityEstimatesForBenchmarks():
    """Get utility estimates for our benchmark policies"""
    # LeastVisited - h_d tests
    n_LeastVisited_hd = np.zeros(numTN)
    n_LeastVisited_hd[deptNames.index('Keur Massar')] = 64
    n_LeastVisited_hd[deptNames.index('Pikine')] = 14
    n_LeastVisited_hd[deptNames.index('Bambey')] = 20
    n_LeastVisited_hd[deptNames.index('Mbacke')] = 13
    n_LeastVisited_hd[deptNames.index('Fatick')] = 28
    n_LeastVisited_hd[deptNames.index('Foundiougne')] = 19
    n_LeastVisited_20 = np.zeros(numTN)
    n_LeastVisited_20[deptNames.index('Keur Massar')] = 20
    n_LeastVisited_20[deptNames.index('Pikine')] = 20
    n_LeastVisited_20[deptNames.index('Bambey')] = 20
    n_LeastVisited_20[deptNames.index('Mbacke')] = 20
    n_LeastVisited_20[deptNames.index('Fatick')] = 20
    n_LeastVisited_20[deptNames.index('Foundiougne')] = 20
    n_LeastVisited_20[deptNames.index('Gossas')] = 17

    u_LV_hd, u_LV_hd_CI, l_list_LV_hd = getUtilityEstimateSequential(n_LeastVisited_hd, lgdict, paramdict, eps=0.1)
    u_LV_20, u_LV_20_CI, l_list_LV_20 = getUtilityEstimateSequential(n_LeastVisited_20, lgdict, paramdict, eps=0.1)

    return


time0 = time.time()
u_init, u_init_CI, l_list = getUtilityEstimateSequential(n_init, lgdict, paramdict, eps=0.1)
runtime = time.time()-time0
print(runtime)
print(l_list)



###################
# HEURISTIC TO AVOID CORRELATED DISTRICTS
###################
def GetConstraintsWithDistrictCut(numVar, distIndsList):
    """
    Returns constraint object for use with scipy optimize, where each district in distIndsList must be 0
    """
    newconstraintmat = np.zeros((len(distIndsList), numVar)) # size of new constraints matrix
    for rowInd, distInd in enumerate(distIndsList):
        newconstraintmat[rowInd, distInd] = 1.
    return spo.LinearConstraint(newconstraintmat, np.zeros(len(distIndsList)), np.zeros(len(distIndsList)))

cutconstraints = GetConstraintsWithDistrictCut(numPath+numTN*3,[3])
numVar = numPath + numTN*3
solTuple = np.round(spoOutput.x)
solUtil = 2.184450706985116


def AvoidCorrelatedDistricts(solTuple, solUtil, constrToAdd=None):
    """
    Improves a solution by reducing district correlation in the utility
    """
    # Initialize return values
    retTuple = solTuple.copy()
    retUtil = solUtil

    # Initialize list of cut districts
    distCutIndsList = []

    # Loop until the utility drops
    utilDropped = False
    while not utilDropped:
        # Identify most correlated pair of districts
        eligDistInds = [ind for ind, x in enumerate(retTuple[:numTN].tolist()) if x>0]
        eligDistQ = tempQ[eligDistInds]
        # Initialize low pair
        lowpair = (0, 1)
        lownorm = np.linalg.norm(eligDistQ[0]-eligDistQ[1])
        # Identify smallest sourcing vector norm
        for i in range(len(eligDistInds)):
            for j in range(len(eligDistInds)):
                if j > i:
                    currnorm = np.linalg.norm(eligDistQ[i]-eligDistQ[j])
                    if currnorm < lownorm:
                        lownorm = currnorm
                        lowpair = (i, j)
        # Identify district providing least to objective
        ind1, ind2 = eligDistInds[lowpair[0]], eligDistInds[lowpair[1]]
        print('Most correlated pair: ' + str((ind1, ind2)) + ' (' + deptNames[ind1] + ', ' + deptNames[ind2] + ')' )
        nprime1_1 = retTuple[numTN + ind1]
        nprime1_2 = retTuple[numTN * 2 + ind1]
        nprime2_1 = retTuple[numTN + ind2]
        nprime2_2 = retTuple[numTN * 2 + ind2]
        obj1 = lvec[ind1] + m1vec[ind1] * nprime1_1 + m2vec[ind1] * nprime1_2
        obj2 = lvec[ind2] + m1vec[ind2] * nprime2_1 + m2vec[ind2] * nprime2_2
        if obj2 < obj1: # Drop ind2
            print('Cut district: ' + str(ind2) + ' (' + str(deptNames[ind2]) + ')')
            distCutIndsList.append(ind2)
        else: # Drop ind1
            print('Cut district: ' + str(ind1) + ' (' + str(deptNames[ind1]) + ')')
            distCutIndsList.append(ind1)
        # Generate constraints for cut districts
        cutconstraints = GetConstraintsWithDistrictCut(numVar, distCutIndsList)
        if constrToAdd == None:
            curr_spoOutput = milp(c=optobjvec,
                              constraints=(optconstraints, cutconstraints),
                              integrality=optintegrality, bounds=optbounds)
        else:
            curr_spoOutput = milp(c=optobjvec,
                                  constraints=(optconstraints, cutconstraints, constrToAdd),
                                  integrality=optintegrality, bounds=optbounds)
        opf.scipytoallocation(curr_spoOutput.x, deptNames, regNames, seqlist_trim, eliminateZeros=True)
        curr_n1 = curr_spoOutput.x[numTN:numTN * 2]
        curr_n2 = curr_spoOutput.x[numTN * 2:numTN * 3]
        curr_n = curr_n1 + curr_n2

        # Get utility oracle estimate
        curr_u, curr_u_CI, curr_losslist = getUtilityEstimateSequential(curr_n, lgdict, paramdict, maxdatadraws=1000,
                                                                        eps=0.1)
        print('New utility: ' + str(curr_u))
        print('Utility CI: ' + str(curr_u_CI))
        print('Loss list:')
        print(curr_losslist)
        # Exit if utility dropped
        if curr_u < retUtil:
            utilDropped = True
            print('Done trying to improve; new utility is: ' + str(retUtil))
        else:
            retTuple = curr_spoOutput.x.copy()
            retUtil = curr_u
    # END WHILE LOOP

    return retTuple, retUtil, distCutIndsList


impSol, impLB, initdistCutIndsList = AvoidCorrelatedDistricts(solTuple, solUtil)
bestSol, LB = solTuple.copy(), solUtil
'''
AFTER 1 RUN OF AVOIDCORR ON INITIAL FEASIBLE SOLUTION
curr_u, curr_u_CI = 1.8413414217440174, (1.7541682776352108, 1.928514565852824)
distCutIndsList = [9]

[9.825773234186386, 10.391005169488652, 10.773612305089332, 10.731384886880177, 9.962900871944857, 10.238078944222487, 10.541366471286187, 10.16546792735384, 10.002999373802702, 10.695122411240465, 10.109698807950576, 9.981389515395856, 9.900178966821406, 10.501178564512161, 10.238198548817598, 10.270503512715774, 10.343286799030608, 10.157336545745185, 10.482087846325676, 10.483897517749167, 10.310150328639695, 10.425977195088834, 10.654570927555008, 10.363334555548308, 10.250661775416035, 10.203335475382085, 10.0657474051693, 10.15652712142229, 9.907260204459053, 10.168884780737045, 10.481407624942547, 10.091685389025539, 10.334423507187845, 10.599105600468581, 10.691382628782772, 10.63135261838281, 10.456920623869253, 10.605543571451008, 10.2621653270428, 10.39419643526772, 10.472439385323845, 10.393338518539053, 10.27843820822719, 10.720210633148566, 10.281480515069452, 3.0848763376757695, 10.420838501164848, 10.165847827689088, 10.210815923217167, 9.785819364693277, 9.97856644977988, 10.431355886506692, 8.246611034998034, 8.854336180131682, 7.34950001117175, 9.848825014759242, 10.680245786038467, 10.732758671826927, 10.066792123182259, 10.66630770095266, 10.454972443947433, 10.464084365190756, 10.023206030741235, 9.65087112420414, 10.221075041951055, 8.84692757387647, 10.409220473985517, 10.54246978239287, 10.225371582855866, 10.348304903667863, 9.578353130713344, 10.110434093633078, 10.101975948689722, 10.145574043001098, 10.1751565552939, 10.26082936504536, 10.360648757795902, 10.236873204452078, 10.236755457410045, 10.026335210348924, 10.220255144022726, 10.281883415716997, 10.236610487185569, 10.577424938700577, 10.506177932214223, 10.709961191894326, 10.324187227114136, 10.790896437006545, 10.512961017368436, 9.917431724913117, 10.488247159743478, 10.105930732650314, 10.586862153573879, 10.536656602270266, 10.270780726101787, 10.519034392222068, 9.142629026268203, 10.426216731530262, 10.580176775395453, 10.41399587306381, 9.75978977165475, 10.139165418699259, 10.125097894785512, 10.323566761425916, 10.064674834358605, 9.235693057880374, 10.194200324392275, 10.442057570969869, 10.521826491468529, 10.633617193808497, 8.382915587753297, 10.270844572980153, 9.788633855184743, 10.174016064465059, 10.328918681025234, 10.025373479580805, 9.828243165037378, 10.149173206999812, 10.592159757118605, 10.723794141947499, 10.23580292182369, 8.052604400266775, 10.821085704651427, 10.177166683132931, 10.23636726113668, 10.495786292111656, 10.53001366092062, 10.15369456456356, 10.475913653495478, 7.898781193538689, 10.587604442137179, 9.482435628517845, 6.719074910271383, 10.400937985803772, 10.332829192483546, 9.939492231629714, 10.20592908801887, 10.562547152762829, 10.3590814979156, 10.161954113705011, 10.076822027378732, 10.550660562320083, 10.604877287504712, 10.437660744785303, 10.387203734720805, 10.553186255447386, 10.469795930294632, 10.286994651903688, 10.551153292455002, 10.575819737158323, 10.35651805849285, 10.112593091943461, 10.661448333095441, 6.485491815208194, 10.360894672392943, 10.377032784634281, 9.943851451162256, 9.659781663757888, 10.54892396641717, 9.242622836721388, 10.36096163157167, 7.396895475826227, 10.314286851987779, 9.244655852288345, 10.234264044999765, 8.736295889281799, 9.637965148787192, 7.82350702914314, 10.621287069471135, 10.640016385028495, 5.777949223246857, 10.555083972694362, 10.29302062474833, 10.583832202942219, 10.421297209478427, 6.29980319688047, 10.516267189830929, 9.785100742401804, 10.424817231776945, 10.361023231454908, 10.423135035690974, 10.111691964617075, 10.267438609954274, 9.53026607567492, 10.085016063973978, 10.171543350777489, 10.627928934943746, 10.563099165187705, 10.190264985320786, 10.619802437768358, 10.34075267074647, 10.435880258158885, 10.123244284699151, 10.523902986769997, 9.867778394607779, 9.590852490294917, 10.389346569698635, 9.973562331109672, 10.408345413791782, 10.192579160611892, 9.123639014596574, 10.38435163455936, 10.434053625365157, 10.470680409710258, 10.428608884227861, 9.208268363395488, 10.05748332382193, 10.356826328875151, 9.832759789411867, 10.477039505011405, 10.734790368244242, 10.503237620172708, 9.06450735299539, 10.264419118842676, 10.696905193178718, 8.965072365055144, 10.489936679397873, 10.507959491058871, 9.221627472364522, 10.35798359871332, 10.795992765796793, 10.369751746284603, 10.461603202377972, 10.156556725171447, 10.290598194682945, 10.579454250063607, 10.182839482777121, 7.010923351980669, 10.104899306737607, 10.464540741336245, 10.443122594912246, 10.280325508655036, 7.256296944174048, 9.439010510652137, 10.746036347933511, 10.464128453359464, 10.593647237124186, 10.33869814099411, 10.450335861597024, 8.394067379933883, 8.972044186700511, 9.648816048309232, 10.51454650122439, 10.61928303825253, 10.412510703077373, 10.458214440406843, 7.573915281683609, 10.540231337279087, 5.7753486611280165, 10.417807446679204, 10.017500899584633, 9.81406647969116, 9.899841864718562, 10.386914225387182, 10.527472050974321, 10.659864729310318, 9.546616040162851, 10.305892032397196, 10.37775555271429, 10.218341688221203, 9.975163957869771, 10.354649278789008, 10.590178087912681, 10.709175507674216, 10.595501733037409, 8.820128076568595, 9.778581708889604, 10.426345312041635, 10.361158154864146, 10.744543101246782, 9.619885567556352, 9.519255040143635, 10.497782202426103, 10.307487579049525, 9.63826028029475, 10.445666387828604, 10.042694270856645, 9.754923467571702, 10.306412214698202, 10.520209444518716, 10.311940178472815, 10.442950014177958, 9.836404347285159, 10.395258604413995, 9.310136685399815, 10.360251172588455, 10.130488506397258, 10.065626215189386, 10.164637172427861, 8.471965698487551, 10.01851589718981, 10.010695142453113, 10.757811445988567, 10.155044139397816, 10.255712213374077, 10.652297170817508, 10.13358044417637, 6.578782553178418, 8.366074201466958, 10.484284223643119, 7.226797706865861, 10.485610990249777, 10.2109051232786, 9.979051305759645, 10.22446003092555, 10.413583906694996, 10.704909326616853, 8.768243624659844, 9.881623306754783, 9.862586765291264, 10.293997815901115, 10.207081075908928, 10.2799293265173, 10.49692407348616, 10.162409572134, 10.163786669333184, 9.868285375457145, 10.488772503350988, 10.406089381298171, 10.411137912950826, 10.190697427931735, 10.603341805055416, 9.121366362171516, 10.598062794352245, 9.609843282167494, 10.484053293084626, 9.50437661515244, 10.517671170220483, 9.662961789277377, 9.740368428875282, 10.701840835703036, 3.6466598694670593, 10.185119058668754, 10.643672480016837, 10.17459557713747, 9.447057021773414, 9.64401662932763, 10.273918291229107, 6.084082808459919, 10.369573725956991, 10.561611500520913, 10.467398733278017, 10.186534658819674, 10.339837152419548, 10.154611879748824, 10.341489398018956, 10.219938564320865, 10.440681669923938, 7.867892703493563, 10.34155146963826, 10.292986220212807, 10.387549164106023, 10.33734542511024, 10.641427681028343, 9.87672920146698, 10.147390191488956, 9.467743276758428, 10.46864358900711, 9.842968509645052, 10.398660822450465, 10.72099100440957, 10.43235049838453, 10.168565919451407, 10.302433550310946, 10.45923173726344, 10.478583835687717, 10.268972187481536, 10.513072159854515, 10.25141049732545, 10.64204861967272, 10.22329951467955, 10.627671420752794, 10.222587552077263, 10.4464841193687, 9.00474469031327, 10.129030427083418, 8.528374842370265, 10.388527173846699, 5.335419759735769, 10.25946333651918, 10.201598892774555, 10.450884047765284, 10.287625009724573, 10.139252518528304, 8.374457461983488, 10.38367515029997, 10.169748885381557, 10.398707061463943, 10.48947022830289, 10.483282582032096, 10.50475658160532, 10.535088545617128, 7.560941260994328, 10.329723012826497, 9.73361032262798, 10.208799590123201, 10.456157849345697, 10.556081752128463, 10.264677194812975, 10.01681578331467, 10.533128898597402, 10.273165747351769, 10.136343851012976, 10.517931517223705, 10.109884733807773, 10.162476391112575, 10.575771617585032, 10.378720246552486, 10.389614219989788, 10.409509465975612, 10.110339801469522, 8.769112696070962, 10.255753079399872, 10.206446079110979, 10.354996800887388, 10.57160993998134, 10.494064829889027, 10.813485166010935, 10.005005325222331, 10.330953767326426, 9.925214297071472, 9.236968426330133, 10.106134864397296, 10.480584709151659, 8.782983520196652, 10.406948468677852, 9.631199686936874, 10.153064843411839, 10.41328969369035, 2.135301106436855, 10.323050861034218, 10.415770591182834, 10.199579605511715, 10.444624193346376, 10.422819932131128, 10.275150108952213, 10.504979733004165, 10.407407709244854, 10.289618267969738, 2.6282708655990845, 10.002525486621712, 1.694654546556845, 10.092064863239688, 10.620601446852358, 10.146990185422185, 10.696221398080432, 9.938809807548221, 10.534373756635325, 9.169649135279188, 9.905626662599168, 9.544050051196782, 10.043441664867027, 10.16360822371192, 10.474911948326737, 10.023695953068264, 6.876520183274984, 10.512816433315866, 10.411688480349051, 10.506166103516392, 10.701024286700049, 10.394167535175175, 10.443982359227329, 10.551425917044341, 8.622912274198912, 9.949774291905849, 10.517427115160876, 10.270737540737228, 10.56083229324579, 10.306685059751183, 10.498309053889292, 10.200149132730163, 6.393033484480231, 10.265627340483352, 10.168778934442605, 10.185721967976717, 9.715782231531827, 10.44307876494219, 10.108368421922547, 10.534034899495643, 10.0912195577505, 10.721009313742844, 10.500045047497665, 10.009153524915542, 10.359162099063782, 10.272184669843213, 10.308795428008874, 9.538143067648418, 10.446493731600322, 10.246368974645536, 10.437508809033734, 10.477247144322591, 10.551109648472949, 9.901522849268128, 10.335615066406048, 10.52138483125824, 10.280219653107878, 10.729429075704342, 10.473912548512397, 10.557701228092075, 10.20996366797493, 7.555731086250039, 9.779165534208538, 10.678347589904643, 9.494771111029157, 10.581619829154416, 10.474250228244493, 10.27243605346953, 10.692087686417075, 10.727517761933314, 9.982845141159501, 6.9774996440695265, 10.332232309618238, 10.408961836704934, 10.310233592581852, 9.785658771616411, 10.368235885070387, 10.237743567296901, 10.153567702639162, 9.687397206445642, 10.169681195145957, 9.783468048403162, 10.635274278242125, 10.188892923459605, 8.853963879129315, 9.568440623165664, 10.556717754751382, 10.52774123022615, 10.309920082247212, 3.9328754443037868, 9.695541012520598, 9.168346485531847, 9.534959332660224, 9.00443777929374, 10.660584352506948, 10.34082759602271, 10.296619892965813, 10.4325310639694, 10.047473327062036, 9.182063630950493, 8.023516352376678, 10.36489592120471, 5.6507189192573115, 10.617963789952682, 10.126523643557986, 9.736238867568712, 9.900923657230374, 10.752824646085573, 9.890650772070007, 10.071724453473465, 10.244562906338263, 10.100211603528594, 10.522762687421045, 10.064266284320494, 10.178597251117468, 10.326976610657647, 10.139061147793306, 8.847003707869023, 10.469717247582972, 10.261819994362016, 9.720295863522932, 9.199375923794364, 8.195278339727516, 10.593567948392241, 10.117867655944817, 9.915772979117769, 10.778691713803253, 10.50297892519352, 6.716558892524219, 9.705874624310189, 10.084810944297361, 10.077687505700272, 10.062897952911326, 10.391995402540052, 9.998821696223741, 10.111213125742017, 10.464714746587315, 10.373840901770942, 10.338608277564363, 8.88485177092562, 10.54130969768234, 9.984532866541876, 10.060295746215575, 10.066549572580797, 9.996854218221124, 9.8669809605011, 10.373453269563564, 10.722356509608723, 10.524628268542633, 9.91156868500204, 9.549270208088407, 10.763226608392454, 9.93513960516371, 9.770191797348017, 10.529308448368479, 10.378818483958879, 9.466043432292832, 9.922903849498772, 10.695723321736072, 10.705317978722695, 10.386810582661]

'''
####################
# PART 2: TRY SOME RANDOM PATHS AND CHECK THEIR UTILITY
####################
####################
####################
UB = spoOutput.fun*-1


'''
len(eligPathInds) = 30
eligPathInds = [1, 13, 14, 15, 18, 25, 26, 29, 31, 32, 33, 34, 35, 91, 92, 95, 97, 100, 157, 160, 165, 169, 174, 195, 376, 384, 388, 393, 409, 412, 
'''

# Sort 30 remaining eligible paths by transit/collection trade-off distance from initial solution tradeoff
initPathInd = np.where(soln_loBudget[numTN * 3:] == 1)[0][0]
eligPathInds.remove(initPathInd) # Don't need to reevaluate this

initPathCost = phase2paths_df.iloc[initPathInd, 1] + phase2paths_df.iloc[initPathInd, 4]
initSol_transittestPerc = initPathCost / B

# Sort 29 eligible paths by distance from initial transit-testing ratio
eligPathRatioDists, eligPathRatioDists_forHist = [], []
for currpathind in eligPathInds:
    # Get ratio
    currPathCost = phase2paths_df.iloc[currpathind, 1] + phase2paths_df.iloc[currpathind, 4]
    currSol_transittestPerc = currPathCost / B
    eligPathRatioDists_forHist.append(initSol_transittestPerc-currSol_transittestPerc)
    eligPathRatioDists.append(np.abs(initSol_transittestPerc-currSol_transittestPerc))
# Histogram of differences in transit/testing ratio
plt.hist(eligPathRatioDists_forHist, color='darkblue')
plt.title('Histogram of difference of transit-testing ratios for Phase II paths\nSubtracted from initial solution ratio (lower=more transit)')
plt.xlabel('Difference')
plt.ylabel('Count')
plt.show()

# arg sort
eligPathInds_sort = [eligPathInds[x] for x in np.argsort(eligPathRatioDists).tolist()]

#####
# Loop through each eligible path according to the list sorted by testing ratio
# Get utility from oracle; then run AVOIDCORR to attempt to improve
#####

# Load from pickle if needed
# phase2paths_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'phase2paths.pkl'))

for currpathind in eligPathInds_sort:
    print('On path index: '+ str(currpathind)+'...')
    pathconstraint = GetConstraintsWithPathCut(numPath + numTN * 3, numTN, currpathind)
    currpath_spoOutput = milp(c=optobjvec, constraints=(optconstraints, pathconstraint),
                          integrality=optintegrality, bounds=optbounds)
    curr_n = currpath_spoOutput.x[numTN:numTN*2] + currpath_spoOutput.x[numTN*2:numTN*3]
    curr_u, curr_u_CI, curr_losslist = getUtilityEstimateSequential(curr_n, lgdict, paramdict, maxdatadraws=1000,
                                                                    eps=0.1)
    # Run AVOIDCORR to see if we can get a better fit
    print('Current utility: ' + str(curr_u))
    print('Current utility CI: ' + str(curr_u_CI))
    print('Current loss list:')
    print(curr_losslist)
    print('Seeing if we can improve the solution for path index: ' + str(currpathind) + '...')
    curr_impSol, curr_impUtil, curr_cutDists = AvoidCorrelatedDistricts(currpath_spoOutput.x, curr_u,
                                                                        constrToAdd=pathconstraint)
    if curr_impUtil > curr_u:
        print('Improved path index ' + str(currpathind) + 'by cutting districts ' + str(curr_cutDists[:-1]))

    # Save to data frame
    phase2paths_df.iloc[currpathind, 5] = curr_u
    phase2paths_df.iloc[currpathind, 6] = curr_u_CI[0]
    phase2paths_df.iloc[currpathind, 7] = curr_u_CI[1]

    # Save to avoid generating later
    phase2paths_df.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'phase2paths.pkl'))

###########
# For plotting AVOIDCORR results
avoidcorrlist_noGain = [] # Each item is a list of [ind, util, utilCIlo, utilCIhi]
# 'ind' corresponds to order in eligPathInds_sort, AFTER our initial feasible solution
avoidcorrlist_noGain.append([2, 1.1365323217042338, 1.0810216850767471, 1.1920429583317205])
avoidcorrlist_noGain.append([1, 1.8413414217440174, 1.7541682776352108, 1.928514565852824])
avoidcorrlist_noGain.append([3, 1.2764127360273676, 1.216187066780611, 1.3366384052741243])
avoidcorrlist_noGain.append([4, 1.0850895475972102, 1.0344833165187381, 1.1356957786756823])
avoidcorrlist_noGain.append([5, 1.4506570585604877, 1.3793895780617174, 1.521924539059258])
avoidcorrlist_noGain.append([6, 1.474908317427456, 1.4039251553566334, 1.5458914794982785])
avoidcorrlist_noGain.append([7, 1.2897153198917515, 1.2270185964845517, 1.3524120432989513])
avoidcorrlist_noGain.append([8, 1.5191899560186553, 1.4459312340540311, 1.5924486779832794])
avoidcorrlist_noGain.append([9, 1.7771955304311646, 1.6889255960662837, 1.8654654647960456])
avoidcorrlist_noGain.append([10, 1.358353115111278, 1.2938629084789692, 1.4228433217435867])
avoidcorrlist_noGain.append([11, 1.384470354561941, 1.3170862254994464, 1.4518544836244356])
avoidcorrlist_noGain.append([12, 1.159810949490371, 1.1099722219037016, 1.2096496770770404])
avoidcorrlist_noGain.append([13, 1.3929113410344485, 1.3239767748148665, 1.4618459072540304])
avoidcorrlist_noGain.append([14, 1.4227788138682822, 1.3562471558748275, 1.489310471861737])
avoidcorrlist_noGain.append([15, 1.4226324882688086, 1.3539410711811293, 1.491323905356488])
avoidcorrlist_noGain.append([16, 1.5490896524051845, 1.4745067541683117, 1.6236725506420573])
avoidcorrlist_noGain.append([17, 1.4107884525634784, 1.3421672189217553, 1.4794096862052015])
avoidcorrlist_noGain.append([18, 1.3936448242971693, 1.3309104835535948, 1.4563791650407438])
avoidcorrlist_noGain.append([19, 1.357605830559418, 1.2995453701985564, 1.4156662909202797])
avoidcorrlist_noGain.append([20, 1.3506299017532726, 1.2993090609417202, 1.401950742564825])
avoidcorrlist_noGain.append([21, 1.518128082496327, 1.449491637894445, 1.5867645270982091])
avoidcorrlist_noGain.append([22, 1.3766402580796875, 1.3221002505074608, 1.4311802656519141])
avoidcorrlist_noGain.append([23, 1.291210047182048, 1.2280807170489823, 1.3543393773151138])
avoidcorrlist_noGain.append([24, 1.3161767085590235, 1.2597308408861814, 1.3726225762318656])
avoidcorrlist_noGain.append([25, 1.355324837184309, 1.291322751439255, 1.419326922929363])
avoidcorrlist_noGain.append([26, 1.3828002919504883, 1.3167226409362947, 1.4488779429646819])
avoidcorrlist_noGain.append([27, 1.1994347195531656, 1.1399588128009928, 1.2589106263053385])
avoidcorrlist_noGain.append([28, 1.2688401546211114, 1.2199322422560446, 1.3177480669861783])
avoidcorrlist_noGain.append([29, 1.2697834033770796, 1.2156822459149161, 1.323884560839243])
avoidcorrlist_noGain.append([30, 1.2936727204013998, 1.233567581324321, 1.3537778594784786])



avoidcorrlist_Gain = [] # When improvements occur
avoidcorrlist_Gain.append([12, 1.4046122168968633, 1.3362814309248137, 1.472943002868913])
avoidcorrlist_Gain.append([20, 1.7710611380324792, 1.6856646041734447, 1.8564576718915138])
avoidcorrlist_Gain.append([24, 1.3848606156474457, 1.32386079041531, 1.4458604408795814])

'''
path 0
init_u, CI: 1.212514932297184, (1.1539925129541722, 1.2710373516401958)
losslist: [10.681744857240075, 10.21411113157396, 10.487961677590919, 10.361215232801364, 10.899210720569435, 10.844743534397294, 11.134234829940576, 10.772396440485092, 10.529399756661414, 10.66887299092486, 10.701501637110177, 10.620471454030882, 10.735231569195385, 10.582197878249533, 10.640929296888146, 10.69126825677781, 10.547009887726649, 10.688236200907504, 10.679932260924083, 10.683219540133848, 10.84055474641147, 10.85729999307392, 10.954838507869658, 10.885191823733868, 10.362159433629909, 10.08311185172482, 10.629668208710015, 10.712629585479608, 10.893457742498908, 10.707357105796087, 10.821566803009269, 10.877370300906192, 10.802840669305937, 10.698602985657402, 10.529160458845542, 10.467933900723061, 10.888670201597993, 10.473681563972107, 11.023817399117048, 10.74242634372481, 11.073911763310745, 9.14840518031635, 10.84432441885106, 10.628041116188033, 10.525376117359409, 10.86912103565599, 11.003318683269379, 10.572411529166473, 10.607455153292388, 10.806760576922501, 10.812986940900876, 10.76760484941331, 10.797252630940575, 10.81466504044724, 10.620281001215687, 10.875760538687064, 10.827326013721427, 10.858746823681832, 10.868589281710861, 10.703406035273078, 10.866800309139014, 10.465803992861442, 10.689044474312512, 10.274567805075923, 10.501197712273939, 10.997457272671861, 10.735773263932808, 10.876392806700354, 10.230548005375388, 10.814606476957275, 10.877634993198596, 10.574657193725752, 9.834057101979077, 10.78340910797319, 10.771132070998213, 10.782562966901455, 10.777103531180654, 10.683098718035424, 9.559627509906074, 10.797076754241985, 10.813407608222146, 10.675560906307208, 10.06883267179899, 5.416742076826827, 10.450333477313217, 10.634199066608383, 10.86789492323875, 10.715837834234751, 10.329585584676055, 10.510547376586288, 10.81108480160887, 10.790965154883475, 10.889755577878905, 10.729766696660823, 10.458977331930589, 10.719085610847323, 8.002634811622737, 10.649517828871678, 10.634551795360535, 10.501729977017337, 10.54349869607913, 8.088589271828019, 10.752110265573211, 10.75096665150001, 10.758750614604757, 10.231619085667509, 10.991005542422254, 10.71610897815246, 10.593652705991833, 10.538827117678009, 10.754841767656412, 10.982824529200053, 11.201989983167184, 10.672438891943047, 11.023356189638672, 10.87177581614556, 10.80088409458191, 11.01610993888989, 10.638213466665306, 10.86338423014831, 10.797668009777572, 10.222994430466198, 10.602633102486196, 10.498002664319797, 11.045031951170412, 10.3980523023545, 10.61706170105595, 10.924938077009266, 10.71278123972833, 10.686809748558215, 10.371263221655672, 10.829707158127338, 10.915449543531224, 10.845656458636569, 10.56015269531351, 10.323937072298435, 10.623645737961581, 10.895063759422904, 10.26579525601776, 10.573589939707277, 10.822130326250225, 10.917699231152087, 10.87719644532816, 10.751818625643494, 10.558804344472163, 10.839932232065133, 10.750157712039377, 10.86986594664586, 10.594544643421807, 10.676295852146971, 10.963623229615955, 10.380497029769863, 10.558587540158058, 10.791770919777774, 10.726394532732654, 10.908688969499167, 10.787812425104311, 10.766887915344068, 10.448551517134309, 9.80535857435934, 10.721622611938166, 10.354451251142985, 10.731124738489497, 10.526704755463847, 10.182774576364398, 10.357016437385747, 10.629000176197207, 10.653892740130543, 10.487406317418822, 10.82370830093555, 10.813114742292635, 10.881564602207366, 10.534990664232936, 10.625217657159583, 10.810825853438102, 10.986236433807756, 10.174074549768132, 10.787368536083807, 10.671318981067818, 10.778609988402055, 9.229154429181989, 10.859135300584, 10.696450515946877, 10.30330009089967, 10.705056611178986, 10.323157590429691, 10.460032842084253, 10.73420244424768, 9.892703648846618, 10.496704654314621, 10.233944070332734, 10.450268897826707, 10.723254113334304, 10.652461238777253, 10.643575060456275, 10.877730373656636, 10.545105469066963, 10.836604458116284, 10.765995363436618, 10.565162393035406, 10.772489207626634, 10.735262874627852, 10.922463738913597, 10.718189812755753, 10.465214516721064, 10.573324373286383, 10.50611390596604, 10.644779733664368, 10.667811877693325, 10.942956178532908, 10.761482954402636, 10.733211262082724, 10.708899087354343, 10.677645773637728, 10.861364972521898, 10.940315158334332, 10.768101925325741, 10.66452390613911, 10.649705969191253, 10.577207290968406, 10.766361220841578, 10.58534199699945, 10.601763459576018, 10.548111541115434, 10.647933551583874, 10.846444348069086, 11.055529042692497, 11.062584976478538, 10.83647501662963, 10.698606825718704, 9.522941517126263, 10.970828697959675, 10.873150123731728, 10.554686138403103, 10.45802082281694, 10.639191973830098, 10.653123366158075, 10.938669218270686, 10.877196699664793, 10.72720200025526, 10.812555005880924, 10.793143483665753, 10.151450937908486, 10.812504902422594, 10.838567610175584, 10.909544686188513, 10.802203005497997, 10.762461707486105, 10.823421833714143, 10.879710154300886, 10.323621550399015, 10.62785986979706, 10.748075530705512, 10.959163048317178, 10.823589120390405, 10.814175549447349, 10.671360692112657, 10.168178283370032, 10.819711508907666, 10.990567802177257, 10.816624674157179, 10.754026366729786, 10.844302369607737, 10.889548834433848, 10.919160109085569, 10.588604184929595, 10.709804163218086, 10.493778085433098, 10.503978649801052, 10.771589394305975, 10.789813307779722, 10.32953818622898, 10.682731674554809, 10.917803701194808, 11.05932200393881, 10.773303584842841, 10.507321818204444, 10.905929414464646, 10.677095070399393, 10.910482352601406, 10.95880947787257, 10.525570184736257, 10.718768639739514, 10.684759661886138, 10.792824458499803, 10.520756910225415, 10.576273429669067, 10.64842425370564, 10.772504433496465, 10.803818034967763, 10.215420198835279, 10.748398372448474, 10.3723454878518, 10.629623010204966, 1.0916583077391562, 10.758099062571056, 10.919080010264691, 10.765543865499716, 10.904523980891415, 10.314185814823873, 10.844872233051001, 10.840631792861107, 9.622888894257867, 10.89419682166742, 10.635739073506205, 10.774902341247705, 10.731877713066567, 10.906655931023288, 10.763369682056002, 10.532624377046362, 10.2961213087843, 9.296558887872628, 10.82900411506746, 10.691965210297502, 10.790564942924403, 10.613880975644669, 10.318119624271086, 10.37925727502707, 10.338869868245316, 10.840601647887505, 10.784144768457292, 10.277027962856952, 10.866093064888018, 10.28879338968132, 10.41031642028981, 10.603745900634925, 10.53371526503839, 8.961462304999179, 10.726626788609554, 10.710159686287906, 10.669020964249114, 11.004658433914479, 10.654155133266292, 9.711190705564137, 10.654020892077043, 10.664159998499388, 10.77961652189708, 10.849455512913487, 10.57439012219213, 10.738158655149011, 10.269201086405918, 10.898573631160005, 9.945441006558417, 10.719310442768247, 10.608811158528033, 10.644331750388133, 10.688453858316741, 10.831011383793182, 10.602691271904943, 10.859521797574537, 10.599345102240733, 10.471070055074309, 9.726870424105568, 10.694572889769985, 10.883346589547216, 10.68862650489962, 10.85141973562212, 10.866492158999911, 10.571218878441238, 10.58590036754764, 10.849673082584136, 10.805421684574027, 10.297850131707662, 10.845580538434676, 10.844582786408056, 10.441145725599325, 10.466550874454228, 10.779672279168215, 10.617380744890447, 10.88610906920497, 10.870209506685928, 10.402582209120986, 10.716557690332516, 11.027505440698942, 10.876588754813701, 10.83876840372418, 10.752032884381611, 10.878998152182877, 10.908966519472454, 10.581619165057425, 10.319607810615635, 10.557111217706069, 10.60072463840731, 11.000226596508565, 9.593346298453813, 10.70884161138944, 10.747816288279123, 10.653306810058751, 10.868805080626862, 10.824822067625869, 10.909485843852936, 10.864147815261374, 10.925409388365553, 10.617651247591434, 11.155481762492249, 8.636089382676179, 10.837912350214843, 10.649935097100151, 10.558442695333262, 10.792982672347033, 10.967571662508192, 10.750179077789515, 10.472711294990763, 10.588698225871841, 10.954775454378455, 10.778621523904373, 10.271357371237984, 10.748997813073297, 10.784083667797393, 10.980455382815355, 10.729958215554529, 10.627560802603824, 10.504682197666295, 10.661606993017946, 10.280676928518574, 10.777732665155959, 10.795960596935023, 10.682675945398922, 10.74954643505878, 10.766753979799073, 10.713365098603356, 10.948125193389666, 10.946193081177434, 10.661773428954657, 9.373673146198529, 10.652566779275741, 10.86102414005541, 10.885477976305307, 8.672403888695692, 10.518019035275454, 11.016745913827812, 10.759496253782276, 10.862634245596988, 10.786467357659543, 10.681949945950999, 10.766191580160193, 10.799234459353116, 10.659056706277322, 10.812449657456224, 10.782735939710633, 10.447818871517962, 10.392920099434475, 10.60428884624283, 10.900654839736957, 10.16284382860183, 10.375903486549587, 9.933497921537729, 9.209833188366934, 10.87441011042951, 10.740239561577903]
AVOIDCORR
Most correlated pair: (28, 33) (Mbacke, Pikine)
Cut district: 28 (Mbacke)
u, CI: 1.1365323217042338, (1.0810216850767471, 1.1920429583317205)
losslist: [10.752445034879933, 10.835257448460734, 10.777430125329246, 10.725844200620871, 10.963953136271776, 10.704735484907163, 10.900031196135608, 10.773532299458774, 8.117971011722004, 10.73076910962207, 10.644297778244432, 11.002631688699667, 10.638978184248499, 10.765617281417715, 10.82231072897174, 10.63782555044295, 10.741457467113733, 11.411850540325167, 10.755227140787708, 10.977035720139853, 10.820247829282982, 10.472114587796012, 10.741290454884876, 10.845730240843595, 10.98454909372515, 10.910434066821287, 10.65398660969911, 10.62656388735804, 10.83114459298432, 11.05181048832887, 11.036774874779052, 10.947335774133293, 10.372451399967963, 10.375996734376288, 9.193757550141816, 11.026478170495222, 10.787536553180493, 11.008992147822774, 10.858013205802743, 10.4305521049892, 10.71414949275473, 10.366466925432348, 10.960615273405141, 10.983340366921908, 10.87667714103726, 10.618693910907771, 10.799678813822897, 10.68000422602526, 10.927281191178903, 10.710630624002263, 10.847283715439984, 11.006686396063605, 10.817197303299551, 10.778757804960449, 10.79897756091195, 10.893502356721196, 11.116310831938065, 9.963488258354214, 10.2702272085015, 10.967420949019772, 11.005605152986012, 10.183576552118877, 10.83841990871393, 11.138385056799237, 10.765417046158445, 11.03063193071821, 10.990150913438658, 10.711954280756382, 10.881207697426111, 10.950139785093798, 5.0785568323420005, 10.78110476399267, 11.152429916094743, 10.777574067627773, 10.701277351564512, 10.093493149004194, 8.40843117971384, 10.722722263730976, 10.604754207109748, 10.790373029750304, 10.983528403985247, 10.789328696329983, 10.898704286109997, 10.538942858149383, 10.796398576316108, 10.816554708018405, 10.697630421446629, 10.421011750557744, 11.103341517558327, 10.633250331518632, 10.890182419329257, 10.916554218213953, 10.431536035670392, 10.688929255069883, 10.952485639472336, 10.723981679861154, 10.816256796297692, 10.862567502555223, 10.778782763209206, 10.575438682955243, 10.803432965509744, 10.752843361401618, 9.662602999114544, 10.94080923211365, 10.865364515914903, 10.695252521119826, 10.902248651411673, 10.590066828183154, 10.803253493083691, 10.801755440131947, 10.701183808163918, 10.990116911019376, 11.113610518203602, 10.89718305633854, 9.812164227522148, 10.5733012953841, 10.807300579489086, 10.92549965471767, 10.968912137689914, 11.03051601185149, 10.986552342200689, 11.165884283403415, 10.744837561358217, 11.008186915772125, 10.108750065269051, 10.069446749275274, 10.580916055665151, 11.00239793172488, 10.661607173611339, 10.589173255784866, 10.808664347453393, 10.634430433734273, 10.770444318619372, 10.816328819913169, 10.96936097412077, 10.7700554648014, 10.74077164903993, 10.629726651355332, 10.725014697813771, 10.980703684693085, 10.750438567568134, 10.713305123836752, 10.498220001237677, 10.616658293644043, 10.977600584167934, 10.773200495972285, 10.855211693853297, 11.006284409634418, 11.07265419603349, 10.990015490253626, 10.4565381104539, 10.948271075905568, 10.729114605370338, 10.810952958732926, 11.148405128593584, 10.449664165318788, 10.877396489533066, 10.896527709501495, 10.730885794364756, 10.68127405753398, 10.394454904048661, 10.821413748748679, 11.042589004654026, 10.693347233348343, 10.893829163748288, 10.6941878479696, 10.911185254363787, 10.756541669442365, 11.029675656123018, 10.791770014103014, 10.812049122121689, 10.770416349693509, 10.817288913474039, 10.659254871467137, 10.934636859121147, 10.685222222808445, 10.844707382420296, 10.830990463284868, 10.855645739517954, 10.756815887701004, 10.83990605044456, 10.63709790505334, 10.696598093871067, 10.999474483901398, 10.746395906701427, 10.821883124443435, 9.209736841853719, 11.137650200737085, 10.584728967019766, 11.123163834253164, 10.79956939603559, 10.81442409015532, 11.02283614585439, 10.695129322314104, 10.545742320215778, 8.406916644777407, 10.889429410534971, 11.123700357630556, 10.770226678789442, 10.82729735979732, 10.916789420266097, 10.77702737330608, 10.973785148791347, 10.837814208529343, 10.727582564744758, 10.33490996518923, 10.933412647594494, 10.899636771527629, 11.180853108015983, 10.745072606973066, 10.83716034264716, 11.097918787643755, 10.776120581673727, 10.63977237351497, 10.99899630265443, 10.90458706490881, 10.864030037571398, 10.650691235167896, 10.959958874430361, 10.66689564917612, 10.819611391732057, 10.076181938852157, 10.498590894730805, 10.85369997944389, 10.578906647092857, 10.971651923321097, 11.016186271717721, 11.053882661245963, 10.762472735894518, 10.999884923442254, 10.706510889841518, 10.438430478393592, 10.741468333621786, 10.884511324934635, 10.993662652976951, 10.860234248470649, 10.868517532962123, 10.625786167322493, 10.416451357686759, 10.814883186975726, 10.781712394891526, 10.936508380968409, 11.107407104608884, 10.840221529492842, 10.874980600860145, 10.527741114647888, 10.875208949923502, 10.542068715565737, 11.109710774186627, 9.955580360363676, 10.923774373511238, 9.690241419580172, 10.782117106885053, 10.885084394360847, 10.712485823584066, 10.734639379708415, 10.704695983532224, 10.215309866138622, 11.081161940407384, 10.941046252423462, 10.39226032289298, 11.227591856924384, 10.811962921784664, 10.7781936263524, 10.871580928049475, 10.911303446839447, 9.655221883364323, 11.036993936823901, 10.10381152303221, 10.848697240418758, 10.928819929544348, 10.633846349896045, 10.722560717088319, 1.26344343725458, 10.525288866611607, 11.017886749288076, 10.845511542605395, 11.018998879122991, 11.068254847124292, 10.909143634835504, 10.885838501131827, 10.797644240864328, 10.832088333911242, 10.865059564011572, 10.665662332528605, 10.950718554477568, 10.693960251364002, 11.034745886547917, 10.914876550926607, 10.767850334321423, 10.192148521142688, 10.657263732596084, 10.876940128226007, 10.840846323643909, 10.913476500737488, 10.92423211792346, 10.969489955998306, 10.814159330552895, 10.898125607669785, 10.758911512041891, 10.934561643123219, 11.039790746538591, 10.540301804687044, 10.865636981040938, 10.404135707600446, 10.510102121113652, 10.95211686534141, 10.725384661298573, 10.467542839463997, 10.712941557753885, 11.005320346280632, 11.206014704347218, 10.902658731950458, 10.707935367740937, 10.588993701275683, 10.884297311161415, 10.95626128957081, 9.731772842918735, 10.660799184995263, 10.830637365102664, 10.834609280692204, 10.515880472168314, 10.879760967055907, 10.790289063501787, 10.728251714305026, 9.90052004131104, 10.70456061186316, 11.034568940625867, 11.00546015258699, 10.967801935040988, 11.030407199284198, 10.775193684337712, 10.473206962812789, 10.34830775759783, 10.857766065282975, 10.789436317982505, 10.922183322572375, 7.80332044436921, 10.869537230022082, 10.370260101731676, 10.708584305808428, 10.415535423094278, 11.169632974047232, 10.955203061237093, 4.518929990588789, 10.899992785966036, 10.896880631629053, 10.685817754332312, 10.753510296516863, 10.532106925984307, 10.900179768441912, 10.86839284677599, 10.508827898708118, 10.801507263253242, 10.03307567115132, 11.1712426906259, 11.126927552507713, 10.846648028739436, 10.784576431886453, 10.462189364000876, 10.822773470152688, 11.029146113501676, 10.747055327060433, 11.1040917982339, 11.180105116449106, 10.801722045072394, 10.9021123851759, 10.811687944425339, 10.840948085848286, 10.81006196473889, 10.510788552578045, 10.666032386949007, 10.995492400414632, 10.8189380633364, 10.801499562690744, 11.014934240056276, 11.00792499165026, 10.882787164409923, 10.636602789495518, 11.006949931053482, 10.966681870342871, 10.820517004837283, 10.881730129382538, 10.721080290737293, 10.769852051249524, 10.82522267324515, 9.836637686759964, 10.801711002656322, 10.885238444127607, 10.849460398140375, 10.693995674610049, 10.673295822093129, 10.816432482836841, 10.966562248203093, 10.935174500974538, 10.873177958258802, 10.838316992871672, 10.364865250679845, 10.782889604700426, 11.024460772839268, 10.69853025437182, 10.808218308950027, 10.672746148619465, 10.945769099284178, 10.916736898283267, 9.175981823910861, 10.408899268925174, 10.568703482597614, 10.642079477698415, 10.88693841443145, 10.94218292306778, 10.044608867682802, 10.990393813901727, 11.146608279804695, 10.971627707440934, 10.822397228354363, 10.93583839487874, 10.932259521568595, 10.358585649774097, 11.156326323259742, 10.77302928811361, 10.669059852131246, 10.530101788228537, 10.642270574605092, 10.639866961764085, 10.76033981485372, 10.781331285484232, 10.867978254567637, 10.91088668907421, 11.507272845892887, 10.452346377465245, 10.822885116261485, 10.811533785315868, 11.02835961255088, 10.85661499528384, 10.719645900428006, 10.561128981405469, 11.005919584834, 10.97100769711338, 10.882463464177013, 10.912160585961427, 10.6393910230084, 10.115421938057622, 10.529057452765873, 10.981254428830901, 10.723420006161069, 10.654138001532317, 10.958348637078867, 11.016776188643998, 10.74751850933765, 10.938802747364255, 10.02830239675553, 10.858806489128915, 10.57474667005049, 10.724765097891414, 9.85102686623751, 10.96440500264437, 10.705141841511779, 10.73567398135383, 10.803888981458991, 10.594937541073298, 10.970616832887956, 11.145799149210394, 10.642457087726195, 10.983978821050774, 10.788847849598119, 11.048180556560812, 10.209427859906365, 10.98692524045911, 10.702636111924663, 10.605170716284785, 10.54395287245114, 10.83994381943336, 11.082495455171916, 10.384922604770038, 10.829104146157146, 10.658666815617805, 10.973100273639588, 10.654625630122776, 10.777971539277592, 10.83155036581773, 10.725146580409236, 2.1763052930255773, 10.925276505874681, 10.889049695825019, 10.68701067849515, 10.98653288789768, 10.763877321388271, 10.78277069089826, 10.901095287544232, 11.098438422810316, 10.68619358914317, 10.699605507947625, 3.1515088885663514, 10.945926962369938, 10.936387111527822, 10.134681916804844, 10.568735681354331, 10.83770677352116, 10.610969687041877, 10.969524032703404, 10.853856056170795, 10.897726204108046, 11.186145140448877, 10.380689245179804, 10.064199014495724, 10.739374834612903, 10.56587815156541, 10.748243282473737, 10.814477536756568, 10.916529885692887, 10.815306710786412, 10.994519849893841, 10.68354012892506, 11.038078478901014, 10.826989290782072, 11.144480206469902, 8.706921921393606, 10.786198388960841, 10.930234999869175, 10.795710706186194, 11.186415721626748, 10.990903445057821, 10.889349716978822, 10.966358691719327, 10.92396929008553, 10.644555577032653, 10.864197489666942, 10.861474657437988, 10.9430470797389, 11.054402816974058, 10.86872134431484, 11.011460282604604, 10.753815352633593, 11.064326638700775, 10.788955327371477, 10.859730861506613, 10.820109282780432, 10.893441127237706, 10.593679774654909, 10.792528079495495, 10.753979955751086, 10.91456248262346, 10.644653129828322, 10.994224771973478, 10.982054055706067, 10.723700568760703, 10.321738386389582, 10.826770614147797, 10.992533460103644, 10.66034793963373, 10.626840597058147, 10.911691658010405, 10.73195120000621, 10.77508628971632, 10.684702401786833, 10.988267467949102, 10.634491459841723, 10.715793162587067, 10.85255063869418, 11.086113925611315, 10.678836524281888, 10.89195491968007, 10.94537828745827, 10.803608575053564, 10.343888651584443, 11.087723448953476, 10.878258302095634, 11.004722702755027, 10.620761933345111, 10.814412931184446, 10.933996061651701, 11.015736337743133, 10.793608820006295, 10.7077163927331, 10.67376425321501, 10.575627037167731, 10.821259294870178, 10.841865914735312, 10.786831996339762, 10.680936465059453, 10.491921740081889, 10.696321071115305, 10.314421739481533, 10.952726719997463, 11.022789867398684, 10.658994149712344, 10.744913986865793, 10.883510230508957, 10.720590126890484, 10.952065658692817, 10.810170226799073, 10.80489958540341, 10.697218149396095, 10.649756608997706, 10.912514612213549, 10.707087006569022, 11.015967382901756, 10.620460626152049, 10.937977622286335, 10.686228156918787, 10.751706785127332, 10.832217205345664, 10.435310119946394, 10.77133896150428, 10.876708875857968, 8.348571027909815, 10.862431312939448, 10.862510583334275, 10.946641071859485, 10.924430682800155, 11.01275725936122, 10.71039683528317, 10.986327605286416, 11.017365295076283, 10.796756181814676, 10.85293417103602, 10.676186124297866, 10.66895169416955, 10.800526299765501, 10.8119685886012, 10.811261687206851, 10.779847030294585, 11.028001720251691, 10.725714395963672, 11.08493253767573, 10.70266336331905, 10.969713254000172, 10.437368127747634, 11.144903903701362, 10.792890754291758, 10.806882739584497, 10.794332747454499, 10.833141964909235, 5.455950668259359, 10.894125362176183, 10.941577183957575, 10.922366064312149, 10.856383622647297, 10.785888823050222, 11.036649245493289, 10.916282542922952, 10.495920001941132, 10.694426235538156, 10.651781396303416, 10.832528043480835, 10.990575644281481, 9.942089336922031, 10.867626861453168, 11.147013922150444, 10.841309233485102, 10.693545343690891, 10.579043171256874, 10.822011141525525, 10.806041195126076, 10.841514691910243, 10.971924154102338, 10.692400092044684, 11.179022695959091, 10.662351112515902, 10.830106796195423, 10.696770296424651, 10.898237890323848, 9.498262521323722, 10.912171571816607, 10.551242670669666, 10.937216949853568, 10.914439588730772, 10.895549313865237, 10.748318894977785, 11.025622850087403, 11.096921739862168, 10.886150280584468, 10.706973434312394, 10.944125406753926, 10.479272696732759, 10.829335735650849, 10.509052307348151, 8.356943781316929, 10.810904414862732, 10.739216231875123, 11.006307249399596, 10.672094416858014, 10.06911761194887, 10.909228593694163, 10.80565562787574, 11.067997070658556, 10.807266355525863, 9.634535861544512, 10.776665369500638, 10.834529268072892, 10.83394271878505, 10.990914992537562, 11.16806561886337, 10.927506678869886, 10.817395206202411, 10.78783900223109, 10.704685758703917, 10.78850705742691, 8.047283341075484, 11.070556901289697, 8.812491941907155, 10.657556373031467, 10.882633419257106, 10.365284111070395, 11.12656064743213, 10.948647282504075, 10.931902793010503, 10.434266673438792, 10.878245818494534, 10.813423763642392, 10.608966646935585, 10.473207619015541, 9.907223690873936, 5.856589754442581, 10.754283780802826, 10.87685910810369, 11.148356182330463, 10.58310976344597, 10.885940997105022, 10.680111954605993, 11.11604339388412, 11.050757452353299, 10.793100911448413, 10.874643785018538, 10.876707021698925, 10.866026973810206, 10.79360643762932, 10.637829500364944, 10.460893019203777, 11.006067482677834, 10.601177808304561, 10.550394903450403, 10.758672613878577, 10.796966818001751, 10.526886847263569, 11.039117342642593, 10.8858402364727, 10.793457771290159, 10.810091048157709, 10.76411074924851, 10.150849868969674, 10.72490715053014, 9.222615512412974, 11.06768938172057, 10.957407541380391, 10.806959987230519, 10.674305108229264, 10.541888258530806, 10.414581985561501]

path 1
init_u, CI: 1.5988931545712113, (1.5226730983699461, 1.6751132107724764)
losslist: [10.491170232343984, 10.52049623554677, 10.614299200181863, 9.587172963183423, 10.59847246379077, 10.703858920683174, 10.267646442964587, 10.334307507857162, 10.213556111759846, 10.539070126404859, 10.687771005677732, 10.783608162978469, 10.289573787480903, 10.68385532018124, 10.530837355160907, 9.517413961684358, 10.611435126784, 10.59837423242315, 2.222673196745074, 10.413109248785103, 10.505647115431321, 10.058606278228474, 10.626358520237321, 10.366987777425422, 10.378503821086502, 10.57847278613923, 10.922619757858167, 10.370903733787474, 10.456547154920072, 9.820909309594859, 10.586331389349791, 10.66818435914896, 10.650502714998336, 10.727580407814006, 8.256370298380528, 9.899198214891417, 10.453953329387968, 10.15936644824418, 10.601127342774872, 10.58281032901425, 9.70722577873802, 10.252296084669451, 10.464891267509488, 10.643008227466053, 10.053248454026576, 9.807550733975729, 10.421783990691868, 10.531800748534767, 10.557979277676083, 10.057586483944895, 9.210272578635182, 10.706626300377001, 10.749987927434066, 5.313688943170628, 10.581674996731158, 10.4075226020731, 10.272795562410355, 10.457991069846013, 10.380958197333687, 10.104649984545615, 10.70369129421439, 10.364449901113488, 10.360684151155981, 10.510729392876673, 10.606997686197547, 10.06110999398455, 9.971683938394703, 10.670917851795515, 10.461288576506291, 10.366498017033647, 10.633043323007508, 10.726241666479403, 10.063023643672395, 10.14006776618874, 10.520795657163095, 10.55188432000338, 9.534378576627665, 10.352759980655797, 10.468599708509611, 10.136056060473543, 10.438767639046562, 10.39479431304509, 10.489685341009235, 10.783396272683394, 10.541922474330415, 10.682682367349756, 10.051551667752832, 10.598476134984962, 10.33697396624151, 9.18043902932502, 10.451786291975086, 10.616773344411692, 10.491436627077835, 10.555044418861806, 10.773045594047717, 10.724194751614602, 10.657806153229034, 10.599976743493327, 10.288028180902979, 10.180706103267754, 7.849442765683893, 9.486638234693707, 10.443594651591257, 10.603344281355852, 10.567618186679411, 10.73268520465391, 9.783124532209193, 10.557162166584506, 10.25967387620969, 10.632213479006188, 10.417115730057182, 9.915366994886318, 10.911513081128495, 10.583707769833108, 10.339550818316713, 10.648982554671784, 10.7628071138821, 10.145198043302084, 10.59781666168473, 10.502750594844601, 10.944741988787095, 10.455383688575871, 10.631537246792025, 10.449831085384659, 10.68458732367271, 10.930060105081695, 10.863821825167717, 10.57586130634305, 10.504338071483083, 10.635696722036645, 10.725630636995467, 9.150041355928717, 10.655936564132636, 10.863605946657179, 10.65778587163059, 10.402849500331646, 10.278440142675693, 10.524978863939632, 10.364913645591596, 10.29851847835767, 10.577271098942388, 10.14146475883753, 10.577757452535549, 10.580780322450819, 10.776425772085414, 9.858721875808346, 9.643173268886693, 9.8383076727273, 10.538635592224693, 10.14638067681281, 11.046393860892048, 10.525133480916718, 10.597845578819136, 8.87586496964588, 10.784785720612616, 9.158803048951187, 10.360173283121028, 10.929282559784626, 10.420889962612073, 10.605583989901112, 10.766723461360005, 10.206724684671594, 10.842535527699194, 10.68555265408451, 10.55131912176874, 10.032580894084546, 10.605644954412885, 10.20590820543371, 10.423653422034567, 10.326073920819445, 10.722389107510052, 10.191227430146268, 10.602387534347768, 10.360281520397358, 10.21855592775649, 10.819461712368367, 10.344836043766803, 10.596404922795815, 10.547557036687833, 10.415533611098981, 10.626019971456428, 10.571092068811353, 9.54623384526936, 10.49420271756442, 5.042745051206892, 10.194219211747122, 10.650210858836898, 9.868468659703439, 10.512445647217078, 10.5214822557146, 10.50548521080916, 10.126480472850929, 10.659741885208193, 10.561641397326994, 10.527223924221797, 10.37440544309829, 10.653902903994906, 10.603573457808693, 9.93495046278038, 10.193434237350097, 9.368182101500281, 10.546702376593014, 10.872435730649903, 10.599658556034795, 10.495709989263158, 10.324058310970587, 10.385865926748046, 10.032244874896053, 10.566062938119925, 9.978389981584208, 10.574757587294068, 10.737256562763605, 10.562953753336432, 10.124759436207208, 10.696952808587316, 9.944292531472428, 10.280457357051421, 10.68247710710123, 10.39638330840038, 10.591796170348868, 10.547259455304047, 10.641914549568888, 10.61085409062435, 10.54351442327459, 10.49451988920725, 10.33604907686636, 10.145081255224797, 10.74183163611493, 10.503896172133274, 10.56407433960438, 6.983742671999248, 10.592415700498748, 10.515505132940731, 10.299593306056208, 10.593521005671331, 10.88172941116636, 10.793265280008779, 10.135450869716472, 9.341102757318902, 10.364072099955616, 0.2720511343027302, 10.881225922737723, 10.881337727235538, 10.677776236001318, 10.544266445599874, 10.707483773549079, 10.512647020416095, 10.687459823793569, 9.669598025996635, 10.2352166918818, 10.258364651386755, 10.639684135094063, 7.671906827554593, 10.62982790886337, 10.618475602840304, 6.892359800107155, 10.678003401414275, 10.593186959564994, 10.417423020988698, 10.508552639844208, 10.36329496809645, 10.649000260723923, 10.443217919265877, 7.669480367959954, 10.288420897388157, 8.177194399048997, 10.504503944924544, 9.7311872053705, 10.72403618620674, 10.405771544218796, 10.843568173959666, 10.260308068684608, 9.395855001842449, 10.507655324544244, 10.598161447343374, 10.529004873227093, 10.238681483525875, 10.467638379461873, 10.309147200947448, 10.081423217407897, 8.45498657642207, 9.74691829357984, 10.56536191389195, 10.826722084950347, 10.2832761455411, 10.620491250691488, 4.666205506843427, 10.923776334726458, 10.369451611748827, 1.0618979440384149, 10.122804010764298, 10.565838350469365, 10.453327158719668, 10.722392374258156, 10.586747387800065, 10.711182571511436, 9.624339179814731, 10.50027291869185, 10.478536677826407, 10.336903341520964, 10.710796369199285, 3.669874875023079, 10.40907649809808, 10.155171994565421, 10.49377829065147, 8.404503806614084, 10.565671636191778, 8.237746909714879, 10.38795929669997, 10.622119268989774, 10.705564164293108, 6.4132601353677225, 10.62527901061057, 10.704995923989314, 10.114260456729038, 9.679552451804648, 10.15161295255484, 10.808270925044873, 10.532527566707172, 10.408227561789156, 10.436210141115838, 10.811402255260438, 10.496176138514748, 10.531755586064072, 10.454404001998336, 10.582203715469669, 10.524333267715699, 9.753475880658872, 10.58074660620522, 10.469313707591413, 10.48749614498464, 8.783507163152974, 10.343410195313961, 10.342134064624906, 9.864734776584164, 10.557352336639768, 10.563360152008444, 10.395454805570521, 9.410068539752197, 10.771515050969109, 10.648573764381783, 2.3178162475635116, 10.531352881374083, 10.467887899938237, 10.58019849995732, 10.352234926793653, 10.710780237090415, 10.521439753854667, 10.532395426061735, 10.904910231640438, 10.257303683517724, 9.647725238231171, 10.827414885027217, 10.537630697702868, 10.203270946610486, 10.35199711845496, 8.202542031987598, 10.599284616451884, 10.689537915504395, 10.161447902750616, 10.628142079847043, 10.7848027736213, 10.456184675624563, 10.156852730005712, 10.428323936995424, 10.642126926102208, 10.53707669939944, 10.54699974511679, 10.404381325805469, 8.353178118374588, 10.014468780504759, 10.612202798868775, 10.807359978690517, 10.593338283961751, 10.373541954055169, 10.668969852948887, 10.739846438930948, 10.186447121208289, 10.32141587584117, 10.584142845817581, 10.571325788305368, 10.39215988637448, 10.273812010392296, 10.516614557432991, 10.459456790608526, 10.09488550869054, 10.468064052057109, 10.802135523660382, 10.566435281105088, 10.64754561457447, 10.469742790081968, 10.507412555577188, 10.557231470151395, 10.732513594387552, 10.520579152065476, 10.538638039296197, 10.2178865799621, 10.87870754806696, 10.190335132079676, 10.368121953354112, 10.444151367624082, 10.682720975839729, 10.724602372144554, 10.430812090107976, 10.836573448263366, 10.57059606942305, 10.64040371554317, 10.676089122236826, 10.47177546861519, 10.703625415219253, 10.398603458267118, 10.454570714447723, 10.309498540453491, 10.43793599880477, 10.626517207672523, 10.63794505640611, 9.655811508980047, 10.551614563908885, 10.119907603479342, 10.48732815520845, 10.745113581456842, 10.55577049503172, 10.400585535219488, 9.779055984999903, 10.520697598426917, 10.434609741572933, 10.314201117564593, 10.581769125424264, 10.487175894930576, 10.155652168186286, 10.691747458295437, 10.488298847255432, 10.476844076138763, 8.412529497967274, 10.678830633567825, 10.325588785216231, 10.301983309124067, 10.190016823783367, 10.529209566645886, 10.716998748569079, 10.340050158021594, 9.934867169887571, 7.482737029209926, 10.591485368967982, 10.453098379665448, 10.557687712566556, 10.30711854265697, 8.707554824396018, 10.408100051915579, 10.693009558806297, 9.933945152646366, 10.344863398561262, 10.755334704625838, 10.374864543791004, 10.520932264902662, 10.51927120409802, 10.50325614425612, 10.618121749149354, 9.878237861746534, 10.742192379910156, 10.519583609956719, 10.401162057737276, 9.940103733008167, 9.413489844400127, 10.39545995840261, 10.378142605295498, 10.72092794444762, 10.134561536006787, 10.565405817691104, 10.512698965966445, 10.569771753289944, 10.687982250779047, 10.473618262591172, 10.621779917139255, 10.193871580759552, 10.562293827563845, 9.758723167338834, 10.589570080624702, 10.437606731938324, 10.385877890339648, 10.758573731637863, 10.495499145817107, 8.5953822226573, 10.632446167895091, 9.612985000753369, 10.768812756315018, 10.378843932944553, 10.317945493116788, 10.642571050667698, 10.501703983890353, 9.815501225030642, 10.647581793325761, 10.477416177908372, 6.813539366375018, 10.628889847745992, 10.590018749141402, 10.620702256863773, 6.601578386746357, 7.68162391123149, 10.482496574388138, 10.477370137337752, 10.710121267304023, 10.773127158746702, 10.433409146796595, 8.912267079682573, 10.092610500865185, 10.670648892157107, 8.488586547479297, 9.922435540223148, 9.292882712007923, 7.895387610425133, 10.323945195702546, 10.627750507515652, 10.372874704827057, 10.80215017571385, 10.643806783809534, 10.508638752889272, 10.688189073838487, 10.18583737996633, 9.87489246158517, 10.536693601566865, 10.20961527401712, 11.050824030638974, 10.117733268608422, 10.611051100289275, 10.336367230839485, 10.595720253606483, 10.78267764555272, 10.492802293894611, 10.56312766815587, 10.446857565085669, 10.58663154683606, 10.4457846078264, 10.51738368305721, 10.341666197246179, 10.701661598450903, 8.499289502962293, 10.576034738310517, 11.025400823710948, 8.96550396651486, 10.382893330119563, 10.442998313807944, 10.382730738255455, 10.550067097635711, 10.38414053417196, 10.497834513709636, 10.457155968419592, 8.76617495213104, 10.833342723516786, 10.547713103907787, 7.517968906002295, 10.459293996903126, 10.354716845773428, 10.209995580941477, 9.775577658199923, 10.578139341630767, 10.487774587705708, 10.65222168445245, 10.40945488142041, 10.607262806567777, 10.59782254794743, 9.61768111033957, 10.360426893078275, 10.534961931024824, 10.367031403332449, 9.805014904577439, 10.38571719462955, 10.640011182632382, 10.642219520828196, 10.493703534917689, 9.853841601397866, 10.532357063695502, 10.47916289670418, 10.947128240236003, 10.530952617807152, 10.627358595442118, 10.726881109662807, 10.662960404919428, 4.758879363148023, 10.45738187370151, 10.050893672569186, 10.577817815852999, 10.089886591877566, 10.720058574530814, 10.22682229125708, 10.453743584673104, 10.641897574511269, 10.463511161476456, 10.814735747089696, 10.427016780047055, 10.6099701836667, 10.492916629389498, 10.451100489726802, 10.58912288301407, 10.738674325255595, 11.069650594045914, 10.246660092527472, 10.606988345194909, 8.626225703844268, 10.518769124881548, 10.317073587879875, 10.496398282463456, 10.628874201278729, 10.612521567299142, 10.453575402406583, 10.453890825575915, 10.67728411406185, 10.230820017894757, 10.686395531057299, 7.415348658042253, 10.557655910066426, 10.277509258713161, 10.256173985369186, 10.247012379229895, 10.488385887358701, 10.477824318538016, 10.597925165281803, 9.257101033403236, 10.616878088481734, 10.560097362534915, 10.806098978427224, 9.717604113972117, 10.211902970015032, 0.21475392783767755, 10.827870436907649, 10.757789245333472, 10.392812085333953, 10.539083076237803, 10.581299225911938, 10.667781141506074, 10.460373204708425, 10.249615522285447, 10.418480355004483, 10.874663837887262, 10.460712928079056, 10.582345122119136, 10.53578750822741, 9.199567265904774, 10.426637450835035, 10.914307733447718, 10.517653776640412, 10.195968065441502, 10.489239220213069, 9.540782297501009, 10.331775795255941, 10.441109985064328, 10.91222232912103, 10.230177986989986, 10.498688704053265, 10.650280484782956, 9.477222959239688, 2.927268578915126, 10.376533349671355, 10.692843268731057, 10.455435711877513, 10.713042451344222, 10.528797205877801, 10.420872334351351, 10.345773410429059, 10.43808159097643, 10.209276053868486, 10.407133075479972, 10.02320135703749, 10.203648894191396, 10.531718839986466, 10.3880835617859, 10.62350943410736, 10.341750861295054, 9.983628947999076, 10.167816363297035, 10.564605235436705, 10.423334150042399, 10.516579144640817, 10.387919948135615, 10.718086459892827, 10.623596694577985, 10.255263629352825, 10.43480341178346, 10.644586056743965, 10.715013476311938, 10.552190730106188, 10.628614132253986, 10.657145503070543, 10.834341232172907, 10.900589511460383, 10.579850058013838, 7.750260134486241, 10.413578422554222, 10.379424332772185, 10.580762392644862, 10.745074178308274, 10.793744018666347, 9.487270083044596, 10.431738484669685, 8.319197203951298, 4.576554478713939, 10.912288672788506, 9.801043454085177, 10.781725864693964, 10.857059749386114, 10.61534990659439, 10.668099754052177, 10.45409106640308, 9.34734735814392, 10.471209256004174, 5.669846719647225, 10.496465434496429, 10.319020162463223, 9.950952672838975, 10.356841173320591, 10.525954345954451, 10.673379743538202, 10.636955700359724, 10.510381715624845, 10.39059486555018, 10.460193173450886, 10.560081847691006, 9.63086673148408, 10.72489909739979, 10.300546351643675, 10.553878716554497, 10.497719608735409, 10.177667119526308, 10.539895116593165, 10.556309197409197, 10.362194141178513, 10.750963671342276, 11.039329874151566, 10.573565117307606, 10.580415483901563, 10.34697791910632, 10.623828269779354, 10.655437823737893, 10.486456963889834, 10.59774776168444, 10.628772743728248, 10.61713844093872, 10.706110032574093, 10.778408286931759, 10.695347419542728, 10.55838377459736, 10.248792008679484, 10.490922954172742, 10.49127864113987, 10.537449351578095, 10.60177543659457, 10.816398706896656, 10.653609660837018, 10.054357595355118, 10.70589500350066, 9.942378946438955, 9.895815105727548, 10.443210975383483, 8.829508420828558, 10.569900309265314, 10.628759247290919, 10.843038010749268, 10.628630119854646, 10.471869581553086, 10.595324578488896, 10.370439629689963, 10.5984688020181, 10.522849328144778, 10.368484859832138, 10.177021056010572, 9.87596935459396, 10.646969068865005, 10.620118225034854, 10.29855093439762, 10.525455246095937, 10.579420929761733, 10.671882182926245, 10.399458770400715, 10.216723969201485, 9.890761142518778, 10.54921937404258, 10.760599234743772, 10.632971414286061, 10.553832281882713, 10.630098389795814, 10.318797070998329, 10.853354928077998, 10.66482769953744, 10.663910711909054, 9.822456242719227, 10.174929115057632, 10.352135582721141, 10.337927980440318, 10.614612152272441, 10.500097912407607, 8.411246492722725, 8.063898269006028, 9.818584269856453, 10.38369839032423, 10.40446322197636, 10.72488143776222, 10.555647280193662, 10.49646829872395, 10.166449494746065, 10.035521531368225]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: Cut district: 9 (Foundiougne)
u, CI: 1.2764127360273676, (1.216187066780611, 1.3366384052741243)
losslist: [10.921207559894384, 10.765174460945092, 10.154396609489988, 10.718091551856395, 10.926780601548394, 10.980029297172676, 10.227593044461658, 10.101678104069524, 9.974776209516223, 10.923016382433575, 10.99856080568358, 10.938376098177104, 10.739921330963217, 10.760857655054856, 10.882569783067797, 10.69586270135527, 10.726732384028349, 10.169665095615338, 10.644799182306313, 10.887477747567333, 10.799178236045961, 10.711198639747982, 10.719247627179092, 10.535102033020381, 10.063191136400466, 10.406971973292734, 10.883976171559274, 10.785351503254658, 9.029571468192978, 10.536723231458561, 10.641528435732818, 10.476843183973688, 8.646697538816872, 10.773583360685668, 10.694475135104224, 10.560725499123672, 10.54651555050408, 10.132637735717648, 10.116538462439264, 10.917317813536403, 10.574455388240466, 10.688785807651634, 10.478832232987369, 10.842820630062032, 10.572850583377843, 10.86680242080006, 10.578659414179251, 10.221210400768149, 10.515678022299042, 10.659398020608768, 10.57586928495374, 10.674698582738632, 10.471748564391518, 10.5566613188369, 10.874712200884375, 10.65565690094569, 10.380570120378424, 10.67161844074281, 11.21608304267016, 10.447450433562713, 10.459515845012383, 10.555344431594122, 10.725405189675477, 10.877782541815513, 10.43530428224467, 10.85187629315849, 10.594289351563317, 10.585169931991667, 10.311255562297031, 10.652236036053964, 10.59990502020141, 10.783865829850658, 9.801885650662747, 10.63225837958999, 10.3126187792598, 10.323579306520816, 10.51030027167221, 10.141001682027873, 10.716692098458703, 10.646992496872425, 10.72858255182288, 10.705963520231874, 10.32960621998939, 10.672794731591791, 10.912454609089759, 10.534569453513534, 10.653922795278023, 10.51230439264589, 10.549651789822565, 10.686233938030313, 10.664493839029667, 8.734211114451417, 10.61031288020779, 10.695325767740236, 10.713224447761446, 10.837623540551922, 10.88957321624909, 10.57450156549772, 10.915907973093656, 10.598218876777327, 10.68521377599964, 9.939249432902129, 10.419046127923288, 10.300433611411034, 10.31560991943568, 10.557442927896744, 10.615981008832998, 10.13569423936358, 10.619509888429326, 10.778121222621788, 10.529383572782342, 10.602137091724428, 10.410763879782213, 10.588254548611976, 10.78753319688546, 10.773948715953098, 10.829559772298385, 10.618815242179753, 10.529423342291553, 10.786532657590632, 10.405331999498067, 11.02449236874665, 9.80989589278274, 10.586297808457234, 10.280068275519294, 10.532752034902582, 8.514491556604888, 10.292109837399286, 10.224276679690082, 10.799660952324059, 10.594692080928379, 9.92730249912709, 10.671612750743295, 10.533469185511926, 10.75695312299199, 7.589491063718638, 10.759645536434629, 10.788220151744834, 10.502489777846574, 10.77276461007273, 10.663576106229012, 10.742022707488049, 9.690334240004253, 10.742901414613735, 10.441649925938023, 10.54808174476807, 10.97140607158512, 10.837519657847638, 10.977224503375595, 11.04635201299915, 10.214295873630974, 10.484358001779645, 10.777958080271874, 10.955476083137492, 9.856800181019512, 10.812501188040947, 9.655497140530034, 10.69423335615276, 10.753135864243621, 10.657894408793284, 10.746760504247472, 10.763375075428764, 10.760362415202572, 10.588339281950509, 10.717008048449715, 9.7249981593366, 10.361604023790656, 10.631025178574573, 10.377915779330976, 10.84416943023592, 10.53802744476685, 10.875637559587506, 10.020079708028067, 10.769453167805056, 10.327512527267578, 10.383410355360589, 10.787848296406759, 10.635213576635309, 10.85112064856565, 10.648491315566543, 10.81690448936204, 10.814048686496413, 10.374593108579704, 10.436876591130833, 10.48478860059757, 11.01024786681714, 10.407340630847495, 10.53034213933064, 10.510209364809127, 10.797253809849721, 10.943927138293647, 10.422955204196125, 10.774192715220828, 10.689782516409217, 10.27041423649399, 10.757243887634466, 10.567483088921511, 10.66386578746177, 10.66602408581255, 10.84276137838845]

path 2
init_u, CI: 1.1616119907975282, (1.1045601027555385, 1.2186638788395179)
losslist: [11.090545965565976, 10.684749917309334, 10.687530902854634, 10.990602986825525, 10.69329848007258, 10.690241672450895, 10.888733750206459, 10.769708797261938, 10.732306989050908, 10.75689944978663, 10.66024080102558, 10.580114671890561, 10.9076605823383, 5.216991887970009, 10.623394402664545, 10.692295388193505, 10.95029098779358, 10.725734040303259, 10.755198821392023, 10.884721515394045, 10.625167481320572, 10.79851346284922, 10.92279724816807, 10.79321936431187, 10.555274023869819, 10.61207296776714, 10.66956844502148, 10.72682817162523, 10.134896131868652, 10.826431065040126, 10.689120341815357, 10.818100084000104, 9.857443492769423, 10.938324644136022, 10.623988106116652, 10.804753492985867, 10.883325758243044, 10.667753647638843, 10.909003676586334, 10.658601230280048, 10.632540940773806, 10.711988146709988, 10.736422266639932, 10.696921427285288, 10.734565572431682, 10.320385655959434, 10.93117130720091, 10.589570693336514, 10.783362495711867, 10.754470426743001, 10.874570449463073, 10.683009963727043, 10.773439400840513, 10.323422324040676, 10.782898087299516, 10.970469348170814, 10.811017359725266, 10.81561405674407, 10.351156459934229, 10.743823897852142, 10.7646505388545, 10.94562289875044, 10.592139183226987, 10.55472485451957, 10.713103849814074, 8.703191254804397, 11.048751943575095, 10.717618275034333, 10.788853933334853, 10.566019754800028, 10.778912283011715, 10.97522337047457, 10.890205599690582, 10.888910578812853, 10.750803028021942, 10.68227737637479, 10.699169664216958, 10.71739369466621, 10.646897661854052, 11.039593413033785, 10.781909862392155, 10.752990584483689, 10.955760789808048, 10.78370742274363, 5.399771057387333, 10.851768350975178, 10.772120113347285, 10.837067871208145, 10.922498043578505, 10.897757899848205, 10.692523020315786, 10.941109911967297, 10.747732292729456, 10.84341032998254, 10.837545704739155, 10.533001935786162, 10.840689160796972, 10.642507086175813, 10.74307593385904, 10.566868315583248, 10.883024737109485, 10.991720970387444, 10.525014741903693, 10.659685521690326, 10.61493248789484, 10.643104459700309, 10.718736045791514, 10.961071705339348, 10.78350606421239, 10.64368191672065, 10.687002611545102, 10.69121104800978, 10.692830685836011, 10.698365236545714, 10.893112269088473, 10.503157702655736, 10.733274481378386, 10.832025354076245, 10.947222655815729, 10.69178961355448, 10.61096137318715, 10.77641570204047, 10.044072907687832, 10.870730518958146, 10.647048544919105, 10.703441074031213, 11.026819682088032, 9.481995536498518, 10.895458606106919, 10.766350619442811, 10.942967482708958, 10.65764268488336, 10.829961404138206, 10.827015714469411, 10.54867005120905, 10.875431169816672, 10.734772972756122, 10.592750872028274, 10.964618007435568, 10.619075541519267, 10.864728794904305, 10.508741435975919, 10.697767092208263, 11.146498001610244, 11.058229432864596, 10.678783162384772, 11.066984854644447, 10.597722893069372, 10.487836221434303, 10.62252377947809, 10.838394433714607, 10.753471356497887, 10.741110609682973, 10.82622533362051, 10.901011434419823, 10.647801987972498, 10.592437581412874, 10.604518711879667, 10.673493931403899, 10.651909308425068, 10.601943527758234, 10.87484296830792, 10.968034366588322, 10.972299360546678, 10.8101551354866, 10.69316896178437, 10.2483758801511, 10.910153940246131, 10.722477960873768, 9.370829202489208, 10.944305536396563, 10.759410759428311, 10.412985508822429, 10.70451991548074, 10.888476757778221, 11.092322457951209, 10.72427300052998, 10.719184536745784, 10.835363368447037, 10.484679076834237, 10.832305679078031, 10.752857010766627, 10.985551527217343, 10.581962626908489, 10.295706222708953, 10.350274791707305, 10.678745826610392, 10.910229107222523, 10.706037218101905, 10.756372863826789, 10.623553521171168, 10.841102426781625, 10.716944765566211, 10.837381034930305, 10.8658093892142, 11.068655970335245, 10.802180725670436, 10.257168163854917, 10.89598803941567, 10.579476371609703, 11.218123951445996, 10.731980862087731, 10.990317616395819, 10.57026027728632, 10.876750424741878, 10.885683566893942, 11.04525435104995, 10.70895109489298, 10.700314135337882, 10.785176332178562, 10.760680166573263, 10.778344744136092, 10.834276456908771, 10.534771678689893, 10.369491779983697, 9.770640824525337, 10.80167439286053, 10.215493114505588, 10.716033395950808, 10.47077822610393, 10.790518290607798, 10.62621968281134, 10.768402758142777, 10.769931195083108, 10.938118873423265, 10.161969474768421, 10.445301463121446, 10.96488870210868, 10.874072841103935, 10.841350954579168, 10.643522034051383, 10.836761257615628, 9.757245175621263, 10.734652651302005, 10.580976185953665, 10.850862721782478, 10.759345657722424, 10.768184009450536, 10.833422032588391, 10.437557060975431, 9.654609690239418, 10.656393835150618, 10.68997493202706, 10.731564289567126, 11.001453901590711, 10.671264205655465, 10.762726098793198, 10.742723044168644, 10.47341384851646, 11.02501241274095, 10.406030589454275, 10.087164579490796, 10.818120488574145, 10.835535249764344, 10.998272350388168, 10.496384725727745, 10.808585856560804, 10.672738139199394, 10.589344250580687, 10.78850422655036, 10.76018914062614, 11.065088149829355, 10.660322415130404, 10.822192737632324, 10.840477478637203, 10.984386194152808, 10.849397707082673, 10.46814577245018, 10.43008445875439, 11.089690022257779, 10.620939895708773, 10.595449428836883, 10.601645320332748, 10.891584615379319, 10.96805183875852, 10.908385500193956, 10.543253014951295, 10.543794744972063, 10.246920949838593, 10.589634536046376, 10.86014480667619, 10.439920187997922, 10.838179047721239, 10.64421963109433, 10.826013987269734, 10.622342459107449, 10.834496959864447, 10.653203457784533, 10.85235357193895, 10.908368304745151, 9.487814237148777, 10.770014026520048, 10.743243587981926, 10.6142762717158, 10.8324548496657, 10.788373472035314, 10.89786781311028, 10.771465884276873, 10.948372543540712, 10.98763085959491, 10.76436693078766, 10.74100573940127, 10.732015237860084, 10.66456495907938, 10.836924503040228, 10.895767776505997, 10.526184271270415, 10.853142409928495, 10.393467826750165, 10.857091831143714, 10.2285255036157, 10.53932271192463, 10.790726778685139, 10.710304184655351, 10.595062198202834, 10.549965848760923, 10.724886498862611, 10.664859094615164, 10.77058800031603, 10.821110338691014, 1.450699459130054, 10.559399256986795, 10.6141213910533, 10.51415650971516, 10.917287023605079, 10.773890900629974, 10.902779526000717, 10.739132906414785, 11.163670120403422, 10.68629533864847, 10.733897952313168, 10.780394453461064, 10.74822410861257, 10.497002955904817, 10.908817397851406, 10.581319188246608, 10.464258110357694, 10.842902390381662, 8.231333577181701, 10.714347228994505, 10.891226176991148, 10.827459307097184, 10.624620698005867, 10.95227889487437, 10.832377221465428, 10.864305927653975, 11.089286627822576, 10.542092230960275, 9.73724780047912, 10.31486700136033, 10.638424708745427, 10.624973499965138, 10.706838486705903, 10.85319501635971, 10.763332155859207, 10.864053843734638, 10.933189055709247, 10.78536146713394, 10.902662376129644, 10.88193401119001, 10.957761483829154, 10.825380362341312, 10.843662129700968, 10.776554857841646, 10.884034916606302, 10.950777247606112, 10.980721361032638, 10.823900197001219, 10.747721660744265, 10.575576965911923, 10.406007032112468, 10.480334188402658, 9.555344363334314, 10.809002855838735, 10.763882182254106, 10.83564439397518, 10.674164094645846, 9.395255351704117, 10.902401844474088, 11.142808488849061, 10.877124395271094, 11.07169891732756, 10.82398793051172, 11.086541067716782, 10.671666898112665, 10.741370259035971, 10.804269494302472, 10.782948455307315, 11.06213072802745, 10.861308232237025, 10.885979270718256, 10.892251387805668, 10.930271783884072, 10.74636973684985, 10.73211248850514, 10.709068651334372, 9.7075051170658, 11.092274873259433, 10.983151786211044, 10.742354108278528, 10.696836546198284, 6.005525948517048, 10.494129024868114, 10.454470606366145, 10.763020961128722, 11.004796801976406, 10.785196844845396, 10.846759263622761, 10.837318504763516, 10.829311746023155, 10.862554058246106, 10.895002945229814, 10.689995166821621, 10.885154118609679, 10.697040985743259, 10.921286149078648, 10.250820253891586, 10.819890466586049, 10.498327170052, 10.607767770639631, 10.82602828630965, 10.691112054996646, 11.030644834198458, 10.82192551623827, 10.93158277327017, 10.31231095643552, 10.629319685347015, 10.775161366559288, 10.73265199447707, 10.686535073519142, 10.62614171633978, 10.401950971623727, 10.84602190305134, 9.015514521150402, 10.94290060880157, 10.579775343191546, 10.805209674277707, 10.804447894482733, 10.008871129235096, 11.055089057650914, 10.953027621431168, 10.550440380464925, 10.74174676549517, 10.595602502762649, 10.69234853417696, 10.66342382951929, 9.611041466774086, 10.70165407984501, 10.530413514327993, 10.27412706434316, 10.739899433089994, 10.437797211361575, 10.671161688749718, 10.568555256459346, 10.80748164009928, 10.825405130191063, 10.75661627507033, 11.006259511990649, 10.693502181560039, 10.776994091703774, 10.71122467613078, 10.705134666839173, 10.928301182895611, 10.781253494035278, 11.056599666779057, 10.961916288976454, 10.913339739499998, 10.57783824013107, 10.738706390127781, 10.43675558648665, 10.670467031444538, 10.717042818827675, 10.5963117930683, 10.75441648923901, 10.638113475894516, 10.836848697188147, 10.42944220244708, 10.80371573862081, 10.440035661056546, 11.009432898125535, 10.627462373909337, 10.336760656411817, 10.984805756049184, 10.363684011026228, 11.001608673727254, 10.59403922668964, 10.734390923656377, 11.235632287503245, 10.95551919083364, 10.73575739874609, 10.671661461603605, 9.949832547151612, 10.885444354720658, 10.533799184495804, 10.71551177702351, 10.90156950168708, 10.530468598011666, 10.931807283391318, 10.897913617828406, 10.864825303062664]
AVOIDCORR
Most correlated pair: (6, 20) (Dakar, Keur Massar)
Cut district: 6 (Dakar)
u, CI: 1.0850895475972102, (1.0344833165187381, 1.1356957786756823)
losslist: [10.687613149469069, 10.796616775932348, 10.644189715584483, 10.988230036024074, 11.097291650249565, 10.702924644515733, 10.4015051981588, 10.72743693150009, 10.661182511246794, 10.389316598588014, 10.73414398600746, 10.70957315807797, 10.574253476832114, 10.562315977687172, 10.801086964213802, 11.08963711819561, 10.709254901907283, 10.630737157635279, 10.655679356651413, 10.73306786794378, 10.881457131246068, 10.803101845183713, 10.656517827244492, 10.885107672526956, 10.852392035280673, 10.573968589879986, 10.343752298830648, 10.7212961718947, 11.134759437945599, 10.562407846606282, 10.703160731147223, 10.903691148632417, 11.01757600284999, 10.705244425626743, 10.598775577268379, 11.016395775888116, 10.67017962287135, 10.917588122182517, 10.531689306596686, 10.831143595028163, 10.826245242112146, 10.661892631573261, 10.74633539601213, 10.693969569547171, 10.593927468127905, 10.63450532977814, 10.867677022796764, 10.762923786899735, 10.626583906935927, 10.426276251966417]

path 3
init_u, CI: 1.5054090994868403, (1.4349911746252015, 1.575827024348479)
losslist: [10.339353069265863, 10.342504754346221, 10.596360248820977, 10.634553451704981, 10.225192366463059, 10.544405150534695, 10.62103141155875, 10.26103289789526, 10.031120540493495, 10.513766359691793, 10.06109354521619, 10.365324826120599, 10.041156276538397, 10.674624898790785, 10.92870363380845, 10.689069509213432, 10.59758841671925, 10.354081142899036, 10.438514730488826, 10.729706324628069, 10.580366372993643, 10.147365477061651, 10.350588461199145, 10.81750430284497, 10.31751840176173, 10.41884933412241, 10.807192413981396, 10.48420679471945, 10.632606340813439, 10.984966361173871, 10.350899846617748, 10.56468902600252, 10.155078186002275, 10.035663729398037, 10.664407491899457, 10.339794986411256, 10.183232855376291, 10.892492391103634, 10.15143012140376, 10.479183226588237, 10.49441640544185, 10.460251954197842, 9.503708475223936, 10.533302765140931, 10.562478683262437, 9.82616769698435, 10.335676515639001, 9.934812325755749, 10.511740542898643, 10.08313801231646, 10.357782476786241, 10.507466112453955, 10.463891413268161, 9.54222092595047, 10.64126709735877, 9.442296206528265, 9.925906498457673, 10.386749309316293, 10.629046346478134, 10.279884771318, 8.950552296890992, 10.53311168422728, 10.608090607942769, 10.462816437239669, 10.227314281304142, 10.397304608172036, 10.442963801339962, 10.60158992558387, 10.577557774429566, 10.66777444348583, 10.517883982830808, 10.537633596179145, 9.907890553172988, 10.670480704440097, 10.7694984224367, 10.436544362269323, 9.003643063140174, 10.675379598462499, 10.454313712039802, 10.295388060284862, 9.264183908854575, 10.549865350676072, 10.367389360049915, 10.197895946840664, 10.437061697073208, 10.042908650712521, 10.647910779465917, 10.5669038114679, 10.569469027599173, 10.264733095449632, 9.90979009711611, 10.280354839541962, 7.071746414693325, 10.595877707601497, 10.405602650606637, 10.154471690245161, 10.514588225134492, 10.36965375264673, 10.18976320852473, 6.655158199852548, 10.395612000937854, 10.645980713103219, 10.634900216839544, 10.528166837793394, 10.497747785829251, 10.012262800663157, 10.362260414721414, 10.602072719412147, 9.752522375546134, 10.724328553184748, 10.520556099366999, 10.61217678292842, 10.480645476992693, 10.084282488653209, 10.37377859725673, 10.868813709153871, 10.75647113203348, 10.505509962045135, 10.299431724956438, 10.682784319473019, 10.626511477236395, 10.303428611184048, 10.58792574448635, 10.751522927598133, 10.207948794450063, 10.717792324687274, 10.679532183362111, 4.073611451235816, 10.619026678951927, 10.655173237352711, 10.640674805245476, 8.555339336140385, 10.213955486383828, 10.435412426191444, 10.499478543895076, 10.727963181555397, 10.625450450523113, 10.444345905284571, 10.683139524191827, 10.14556937376089, 10.34166034173526, 10.528906502075936, 10.21900538949975, 10.49821642072285, 10.326148518730303, 8.301709667750492, 10.717914392191588, 10.922532406567283, 10.448183435242903, 10.578262996392057, 9.778907187219179, 10.464595023195269, 10.41811689068368, 10.221621699390504, 9.887027023569608, 10.861544683219085, 10.616038888722507, 9.824635684458972, 10.493515308342097, 10.692787852142148, 10.384626445834094, 10.504611535288715, 10.136921933763231, 10.665324504802067, 10.544599856500424, 10.33052210814281, 7.812968592295921, 10.748682041046452, 10.209047429740854, 10.78090554048528, 10.46653240993476, 10.349680191635525, 10.449999677522502, 10.502972615866843, 10.586144318652115, 10.683351801679393, 10.802861397743737, 9.956953673255079, 10.049423502998707, 10.365965336533442, 10.247170501637909, 10.032516919916823, 10.467409488890322, 10.44903933984028, 10.572854081050998, 10.689069234708146, 10.429182284847922, 9.710997516204689, 10.679941736152623, 10.519358693549961, 10.797833020368518, 10.428443114133307, 8.55250114833705, 10.47075663563138, 9.83836472782091, 10.603251372557065, 10.041213146547427, 10.558832186528118, 10.853884205404242, 10.652206323331121, 10.62280196001305, 10.669419829716462, 10.405478193396021, 9.940975716457551, 10.614313753401184, 9.903618786414896, 10.531530093980225, 10.456841832164056, 10.6339900264846, 10.666124061487917, 10.714470801666517, 10.695442442031966, 10.37419401758647, 10.692125934659604, 10.24857450418374, 10.16070212112302, 10.382498657991585, 10.563704614149014, 10.711477308131634, 10.4694251118689, 10.059681167521717, 10.611317155671038, 10.486716820776062, 10.526597638336591, 9.23175344898095, 10.526310046818972, 10.794693839814403, 10.577684859824222, 10.67985634324581, 10.702354903809532, 10.609994958219305, 10.457203571149629, 10.612181045074827, 10.435168412094159, 10.98847422072331, 10.567094565099882, 3.970539992643121, 10.811362398479169, 10.336423025883409, 10.666405122105287, 10.607639276238649, 10.65159876409467, 10.666914156913053, 10.505334885682931, 9.992491620115862, 10.712375071061647, 10.748966057551742, 10.546239184423252, 9.419015108590912, 8.248123167749805, 10.243692768259773, 10.04743784339736, 10.469346769613733, 9.956677145630557, 10.342683018267731, 10.458499896163447, 10.780733702621825, 10.198112123836367, 9.961882455606277, 10.68716194148809, 8.454301685918827, 10.562859406339205, 9.564986782363354, 10.521845991725455, 10.517701399976106, 10.881006734659229, 10.457462190701735, 10.718829838728889, 9.22110583566427, 9.910822420586673, 10.313085987877761, 9.793828423050961, 10.199274841676162, 10.533630365003864, 10.550016868308386, 10.281363066897923, 10.676135388169147, 10.625238504916483, 10.580961191639453, 10.573802514773682, 10.572437126229904, 10.411796659787118, 10.841640322558849, 10.601834823541449, 10.910970780046693, 10.625290507114899, 10.071199334353414, 10.128385811719953, 10.524293851406155, 10.480354360417218, 10.292319747516952, 10.36429375738393, 10.416158445788112, 10.610376145827772, 8.454457026997684, 10.471804903932075, 10.59682887770841, 10.453670903248613, 10.541315934231815, 7.066247926802079, 10.296776343789203, 10.381365660814179, 10.226337724226406, 10.392557287294947, 10.371343583839327, 10.567834594255714, 10.591650901618884, 7.964148617793135, 10.467287859603614, 10.139249011314238, 10.85493770349203, 10.615943946874216, 10.019135136625728, 10.536465673986374, 10.639389713799618, 10.36191121789187, 10.475150110843977, 10.479674726771249, 10.48751386384983, 10.756506513046205, 10.30895001137325, 10.195498840532935, 10.669597518182657, 10.623538999123324, 10.295896683840686, 10.574002275643652, 10.18560666949898, 10.596992598006901, 10.609169577959403, 10.309616395410778, 8.232356384157429, 9.983935035319716, 10.565534616095702, 10.320898618620742, 10.234037598637755, 10.45562017229685, 11.031439561152721, 10.761187302042606, 10.267224244971421, 10.369965480752496, 10.373222218956089, 10.515594309697713, 10.505548246074799, 9.060782603519982, 10.853687278499276, 10.682263452209655, 7.599363809635251, 10.069387624644891, 10.758791156767083, 10.409628672087065, 10.431023855215344, 10.893918884590773, 11.11248233066323, 10.786648246337313, 10.68747461478545, 10.582137543568225, 10.418053897472351, 10.625379117012193, 10.494889489877595, 10.525675885549926, 10.78000049999666, 10.258766019237312, 10.576909144956817, 10.661438030625668, 10.977591037869429, 10.79341967474815, 10.240687328464814, 10.514537832487557, 9.986737576127119, 10.275838164067041, 9.953843572314991, 10.490609510246607, 10.523267641443987, 10.716246122160019, 10.177147403821149, 9.299440097737744, 9.83038303301331, 10.602728587487574, 10.203518389209304, 10.658410265941498, 10.514301748983225, 10.857339911592144, 10.43174396448991, 10.726267798670738, 10.284302508200762, 10.41460676048477, 10.3704308166277, 9.02917255756758, 10.723018341483023, 10.678824752057276, 10.469834007141507, 10.573283500135574, 10.539278772173077, 10.068328049279724, 10.541717149949285, 10.57614609082683, 10.58439853956498, 10.437891942193692, 10.359170725939174, 10.247963372329993]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.4506570585604877, (1.3793895780617174, 1.521924539059258)
losslist: [9.986149071493168, 10.506156746545525, 10.643880388759333, 10.928064280723547, 10.502337696707126, 10.234661690794551, 9.95842274251402, 10.183759179864492, 10.571790392580088, 10.641757534425999, 8.928346326247397, 10.624588951524371, 10.589264907898583, 10.43291852067946, 10.226075043830539, 10.676757767900412, 10.74239023547615, 10.582772560822733, 10.235767693319199, 10.532895645230989, 10.186119333614206, 10.64830968008218, 11.055362639477563, 10.54012160618634, 10.543421069449792, 10.419713515478241, 10.37222808404327, 10.748778165286742, 10.875344846881937, 10.79621563494968, 10.78988261053495, 10.615920287244887, 10.705307001565513, 10.67143936279052, 10.587304914323841, 10.87301548231674, 10.865596882661064, 10.578408603295738, 10.8374087324533, 10.10748589383281, 9.738793740861562, 10.300433523631522, 10.53494980803703, 10.878785516582031, 10.424051388441987, 10.620670836566465, 10.46471081943896, 10.69112266463658, 10.650100532265814, 10.63902144256845, 10.934757535494537, 10.676339910076916, 10.543168827067888, 10.66918935006892, 10.68446087768182, 10.507298758039163, 10.769745867393556, 10.828897589587319, 10.398032339875229, 10.388917103174824, 10.865985108938975, 10.74366398707416, 10.553241424807194, 10.079538338528604, 10.61066673432587, 10.809189823839535, 10.391398888159634, 6.923495838797482, 10.536304564150527, 10.638286285413418, 10.3785583984071, 10.402053777985811, 10.577617125420666, 10.370319539782294, 10.742245839104335, 10.083114273733905, 10.450853242864818, 10.578859733478408, 9.823449193807182, 10.403665914594571, 10.80859136194743, 10.737571139608905, 10.618213323227334, 10.570242881867513, 11.054430925612673, 10.684744858268918, 10.64000319872246, 10.516580396454668, 10.717094640828424, 8.871097302329192, 10.614870942684071, 10.719308884833875, 10.257283328105384, 10.508992037141663, 10.871854987898143, 10.52307443295537, 10.402990136238994, 10.693618724375812, 10.736889634653515, 10.519316340446805, 10.383049485656954, 10.628154900578295, 10.733587607170673, 10.548541170943126, 10.344308988403661, 10.52976484670035, 10.658552004683115, 10.50423089397858, 10.45941996817736, 10.651443615229075, 9.966729769575988, 11.073239632003297, 10.73018662467114, 10.013465297145055, 7.666282943701197, 8.610577052504333, 10.804732702361367, 10.74008464457472, 10.531132271615123, 10.654294161035011, 10.41056532671722, 10.765940245769887, 10.099687384379502, 10.666061361271174, 10.460777114839305, 10.241128163646843, 10.27676744725926, 10.597093106497843, 10.28595663363813, 10.94004682382433, 10.47312211228572, 10.58857423473984, 10.62184724569853, 10.313327417284581, 10.420844692119283, 10.750190956053844, 10.578474126608812, 10.096209301903079, 10.445500512862152, 10.85054448460261, 10.374416684933346, 10.507339118936157, 10.544608508907643, 10.533173659524897, 8.135818372952816, 10.06705686066583, 10.850980936445788, 10.734657437623975, 10.200532669682875, 10.767136767424155, 10.74606948285035, 10.598587654773656, 10.47894962163554, 10.557549947030598, 10.844230068226077, 10.65841297587215, 10.487518071216577, 10.673449078951924, 10.51293216530439, 10.724409533892533, 10.623288058955504, 10.42832469879046, 10.756400544794127, 10.411834910132528, 10.73029730559325, 10.351835985025295, 10.0064323771065, 10.86766599054066, 10.343849920502882, 7.597379253356818, 10.716862230402276, 10.679319209528671, 10.842590189729917, 10.292218564835027, 10.600159776227915, 10.801157972737709, 10.519715554511297, 10.292212178526414, 10.349199017495092, 10.29418421360907, 10.530600914518567, 10.526994510786826, 10.152802725712887, 10.606220440238095, 10.612655705944984, 3.7124747152519912, 10.55447803144926, 10.611062369014766, 10.413677986101995, 4.660972087227968, 10.695951624520214, 10.347280701925836, 8.225434867418134, 8.778158606400973, 8.67311299146501, 10.523458996798826, 10.590387365573777, 10.477137841461856, 10.715366340924874, 10.976984321018227, 10.636333330965055, 10.656497673621828, 10.793544324626808, 10.617815929818594, 10.846137099202894, 10.46805770273898, 10.662826901288932, 10.809885351089747, 10.646468432225618, 10.7210368390221, 10.70134140556978, 10.852146056863795, 10.491156266392826, 10.676941246179776, 10.464680128350617, 10.285552986185058, 3.6910674074334704, 10.561399319983783, 10.207189284219917, 10.609930938999794, 10.14396206760517, 10.560552056340264, 10.427120591198767, 10.26142312074743, 10.521862080420199, 10.829494357770365, 10.591070410213922, 10.434653717848574, 10.531348567038956, 10.548786118178592, 10.406332051756541, 10.732312001837954, 10.283130505263285, 10.71288495645067, 10.649439915367717, 10.234646100281184, 10.805523461731982, 10.72194069425142, 10.655073706561986, 10.474969268751106, 10.526268782217896, 9.731677249536302, 10.419369549757212, 10.261993958463767, 9.668903857378163, 10.435423281075611, 10.909113446357694, 10.691487503439562, 10.511103365430847, 10.830213064631797, 10.420609005899944, 10.600402719988308, 10.519025917743539, 10.769451237040474, 10.623535539746792, 10.526267777064808, 10.666002985942763, 10.572600104586654, 10.610231554041219, 10.280248976701769, 10.48075953243145, 10.538465049990238, 9.127400273522248, 10.731624146435099, 10.530903054994948, 10.625781545358448, 10.981293008330773, 10.776190842002872, 10.582556124818787, 6.981540986650132, 10.637482899857106, 10.580890007273748, 8.778557184284542, 9.027096281822423, 10.340683556842798, 10.368482660062162, 10.584381569338703, 10.734301114485799, 9.537500592919656, 10.676055419801319, 10.777644349518651, 10.676055039160827, 10.416637585576568, 10.56128119266021, 10.600217743473811, 10.800106747505927, 10.734050488079145, 10.66902661916851, 10.408642377605911, 10.555755140846207, 10.47470428180093, 10.629006062785415, 10.856644305970624, 10.81222529814083, 10.373296592892757, 10.735198058715525, 10.501943836445527, 10.563626718803226, 10.336848245805932, 10.618382860302129, 9.959156539040983, 10.891286322768456, 10.516273701085046, 10.747966711973937, 10.63608258928163, 10.374109215390236, 10.535288760985182, 10.660852389139258, 10.66123542574722, 10.784201567045274, 10.788422813867097, 10.691617220682605, 10.180392298367606, 10.506924835879275, 5.7964005850128375, 10.279511261357408, 10.56202189510889, 10.504310009456894, 9.249825017992992, 10.954624306030547, 10.330520108760364, 10.581666909121203, 10.444219901738943, 10.664732144755318, 10.287506389146879, 10.352143284712007, 10.46814176053991, 10.530418207755623, 10.978234070916258, 10.860842152544866, 10.690840913790893, 10.329547232810855, 10.677297091535946, 10.288382498832823, 10.691584993367728, 4.503982603028863, 10.618792976776755, 10.410010814082119, 10.519527148601494, 10.126284583660514, 10.19623735175227, 10.77975507880205, 10.62293306455408, 10.979817735102346, 10.757994056183904, 10.506983133289012, 10.725778065173245, 10.893529819629158, 10.53184296994636, 10.264163197358071, 9.667362411657242, 10.686418891153899, 10.449200278615706, 6.350940440042795, 9.782478602709478, 10.605896596805977, 10.69146721617762, 10.373929872487857, 7.863053469788891, 10.685588170484978, 10.796250393917836, 8.771965880687187, 10.846834348568045, 10.627669155010956, 10.61476279450574, 10.72247771981573, 10.51748810191372, 10.135152525911, 10.29751984792002, 3.5423205021738244, 10.091634501128622, 10.475665551723054, 9.272186592047067, 10.23599290036176, 10.573296655981729, 10.268788687233798, 10.801841039199392, 8.53129928321268, 10.46344635946354, 10.752134871064191, 10.746348039949838, 10.528410175749242, 10.483579206083292, 10.63024565113537, 9.147486490190639, 10.662169977065094, 10.585952608938726, 10.086160170859207, 10.810977968060389, 10.485233212411183, 10.550467582850303, 10.464735052329155, 10.71605370501897, 10.553061871293478, 10.380001836922913, 10.834137103707269, 9.499039918724476, 10.531002310421858, 10.639712185028921, 10.449484644552491, 10.740231591556729, 10.590614554185608, 10.112759521636411, 6.145117065567687, 10.854258260029486, 10.771972208148828, 10.894288909089367, 10.232110674509137, 10.839350725944579, 11.034546976366935, 10.641548994265463, 10.52989580662286, 10.511978721744667, 10.386122163131875, 10.74518592685163, 10.445322170646687, 10.472036214565026, 10.264466813738489, 10.026412027582456, 7.160971387250857, 10.454768658902934, 10.955576948318106, 10.358939828529344, 10.607540839587168, 10.193372890418896, 10.798922807364935, 10.60864584638396, 10.83496760029475, 10.859382779687918, 9.17286232659328, 10.250266395167912, 10.50708004286139, 10.69381250330422, 10.809375592740329, 10.662768983023886, 10.580306092732961, 9.871370245444341, 10.762258051332324, 10.868500018117539, 10.291206425525335, 10.732292108296273, 10.565962415495136, 10.442797128327694, 8.177924538778628, 10.818344053465538, 10.778717882214119, 10.897943555004538, 10.659383340467553, 10.316653074936218, 10.46092627107582, 9.857202508617442, 10.88758100025829, 10.581064169636125, 10.284825310630913, 10.783436050259755, 10.673863001803317, 10.725463556329624, 10.90699057530961, 10.823033495842367, 10.67363136845117, 10.680938522345436, 10.40993363589136, 10.484199933317313, 10.734230715920232, 10.441152475832508, 10.564930836284404, 10.71902731064624, 10.452028862518041, 10.364422406518667, 10.622926504686664, 10.681340717984666, 10.787338090590353, 10.724341638868223, 10.601391182832472, 10.64512059411583, 10.53743847995973, 10.58188863548933, 10.859787711647586, 10.73852190727685, 10.614370776412462, 10.629887999298605, 8.550515122669788, 10.52659969422756, 10.68784582554796, 10.784299743410488, 10.421693805458357, 10.802798792576176, 10.733569824849166, 10.927967090942433, 10.63667027304388, 10.7806200436551, 10.42986583703799, 10.708885755506909, 10.671725768685555, 10.595279284679833, 10.486859005641884, 10.690580964351962, 10.31175997796055, 9.740467027612176, 10.575838429659802, 10.634700344034782, 10.599604701801308, 10.653387762238435, 10.333217111182192, 10.029333441966997, 10.411339561467205, 10.444055592055495, 10.583170042496004, 8.631330750698364, 10.517224556136847, 10.652820482494196, 10.872270097663794, 10.78412831878033, 10.808958663922315, 10.90902200171608, 10.595746572001637, 10.647441168294046, 4.013007237001903, 10.561829819972589, 10.428267935811897, 10.336478880804167, 10.68365290616182, 10.73704679221636, 10.463748411117484, 9.954135433218328, 10.594760459450892, 10.77163291674583, 10.399562659068721, 10.43973019104497, 10.27769997719126, 10.729455044645716, 10.740584918577357, 10.336589901782116, 10.69413470109086, 10.895777950823753, 10.767058546906254, 9.838982348733719, 10.637588937637476, 10.57871284793352, 10.565416180032145, 10.666921385485464, 10.461103614554284, 7.971796308435832, 7.0860977810645, 10.511920380584376, 10.609996623563585, 10.506951480811871, 10.511654104857318, 10.564273814181565, 10.74867226932077, 9.41966294682217, 10.07051441443244, 10.25637308844162, 10.734980629125966, 10.405004495268315, 10.22850471248895, 9.837539060009739, 10.597587747863711, 10.305197279533543, 10.655827040753428, 10.442878433416002, 10.428796220236134, 10.744492221513473, 10.664297864559705, 10.612881935786193, 10.427975253274864, 10.462778370936464, 10.566674537772483, 10.824074176890957, 10.506322011084144, 10.34187844455041, 10.556014113585308, 10.575663098403355, 10.54190801109438, 10.63095562269706, 10.63430968881297, 10.496796849826108, 10.447572080586713, 10.940629162850033, 10.642722764495764, 10.935537601763887, 11.085979834460248, 10.438735445315587, 10.318432686757095, 10.96465643064685, 10.835650261525203, 10.625483749747872, 10.61091967392301, 10.328115098759826, 10.785140431251532, 10.65439696324599, 9.996852677706682, 10.549836520377937, 10.575388490141234, 10.322837304308026, 10.31381908954318, 10.68198292408526, 9.818876694104121, 10.800776942816766, 10.33472715866119]

path 4
init_u, CI: 1.692904950303518, (1.6145134687307134, 1.7712964318763227)
losslist: [10.3866256604009, 10.540128559672956, 7.350452790190475, 9.941786099436728, 10.385670065653432, 10.300205851587732, 10.477625407649517, 10.341349166384092, 10.650485696316755, 9.226720835916256, 10.04156830845485, 10.02185489211578, 10.326227502132728, 10.139632355516927, 10.492850153365005, 10.288692534296988, 5.95503986285228, 10.530183452337518, 10.119537443956164, 10.235158682495209, 10.379071385983712, 10.375384111726877, 10.475777596368761, 10.208106407475418, 10.395745478304859, 10.155907391049324, 10.57316395204537, 9.6714691270073, 8.300698497425527, 10.435020990575167, 10.541208053127813, 7.890502556288192, 10.360718712007928, 10.557755220091725, 8.74624108290123, 10.608582384809663, 10.68353748128091, 10.585558184963359, 10.081377915700688, 10.246528355821457, 9.384854736681941, 10.557568231475253, 10.379075548032674, 10.526552794878784, 7.310933712272925, 9.04651635410003, 9.554842442666294, 10.167097373532718, 10.93933308659551, 10.233143776014236, 10.302340208126761, 10.40465037504135, 9.29130273708349, 10.711300855736873, 6.460914406021087, 10.491338779782813, 10.787962302382919, 10.169303583182806, 10.355748578587544, 10.57343037573611, 10.237211959815792, 10.535451791765611, 10.288260912703796, 10.269878435399772, 9.459605730729866, 10.4675777165733, 10.113675292806754, 10.307050197447827, 10.170845500377027, 10.329505149051798, 10.585238329994732, 7.396424517874173, 10.308924798893083, 8.008319284940962, 9.154506295742307, 10.574557692913054, 10.36370905698904, 10.561211639129002, 10.276805830321614, 10.52434398150331, 10.308126334552071, 10.484575426469334, 10.464846754811871, 10.341851591365343, 10.198125080832543, 9.77624304426678, 10.48777105698275, 10.808693951891884, 10.368406425703649, 10.293819971875653, 10.317472368134418, 10.25585546370499, 10.518814863502143, 10.315659924437348, 10.490307887805162, 4.316765936969777, 10.247756098992006, 10.575385490097897, 7.867756545084887, 10.53557272984884, 10.493743080482174, 10.4333792211898, 9.432990131013538, 10.47737481765249, 10.458930737118912, 7.267555089875937, 10.428766615933682, 10.343674585307237, 10.280468414753333, 10.713011215218888, 9.52935988079968, 10.452645689691913, 10.411617528462356, 9.996179141817478, 10.548323014621255, 10.235709581088281, 9.968073519206126, 10.408399560488526, 10.52087827705703, 10.432614964165468, 10.041927352660156, 10.578006034493319, 10.435947630354287, 8.931467338838369, 9.38889618576295, 10.25969539192568, 9.71911072494934, 9.151528471944623, 10.493883122729942, 9.238051340265937, 10.596378727674713, 10.555702578876746, 10.598269780325497, 9.26515310713473, 10.463277607336897, 10.392552094933572, 10.5287016668428, 10.17819225135009, 10.424736897633705, 10.291971637718534, 10.794658289150922, 10.508023263329536, 10.258539279940065, 10.11958508107093, 10.625841709289128, 10.58993927516336, 10.239887297791286, 10.609726954342346, 10.252520688928506, 10.179116451521478, 10.671860675679707, 10.513270093135596, 10.679659782323144, 10.090372902892021, 9.793549733196821, 10.331158957261245, 9.934035556946274, 10.39605078505411, 10.66267632941692, 10.455617607691119, 10.391449991174772, 10.368754119401594, 10.356030335908821, 4.210535540519057, 10.369183885733001, 10.190878441573771, 9.702687131020335, 10.45604044551426, 10.661488136161102, 10.513954868207467, 10.175622427779956, 8.847976389453224, 10.383894007413472, 9.78544301131299, 10.3322295755185, 10.342085341652401, 10.401731036411197, 9.483690814669716, 10.343483455658252, 10.541309077905497, 10.8070411539716, 10.189411679189543, 10.204324558486114, 10.444337441893465, 10.047435807196901, 10.249471687243805, 10.479515240469404, 10.307883928915462, 10.664040715699949, 10.39693548157392, 5.631347190792263, 9.188667879377057, 10.71442294760057, 10.188841295046116, 10.488378550628923, 10.720363119589814, 8.855779223826678, 10.367099327420146, 10.38850805135072, 9.817865762053138, 10.434035224143306, 10.479910486557847, 10.539386716299823, 10.58411529501836, 9.986610100030271, 10.030831622065218, 10.46769367077996, 7.732297154053078, 10.609000090953451, 10.265555894043793, 10.511968636670762, 10.10563358626531, 9.09923952018024, 10.227626918567497, 10.441629930817749, 10.395649905506342, 9.236435601566006, 10.433561794190975, 10.300221160417152, 10.194156842606752, 10.438263593617727, 9.922284009193751, 10.666106536627664, 10.305707775617604, 10.004696336752547, 10.074850359631824, 10.112709715527584, 10.627306148346163, 9.956692190140295, 10.678200301051797, 10.161882767107885, 10.468734048797387, 10.53785756688365, 10.65919127489877, 10.510401978899834, 10.507771490538103, 10.072303279433111, 10.463424696757189, 10.009502293086324, 10.231577961944534, 10.343143443275238, 10.471681665557051, 10.21001772268001, 10.557635120420546, 10.340967418572898, 9.736860940666498, 10.384338228828605, 9.575227003887317, 10.594689810895552, 10.127657864559295, 9.874894609528864, 10.390025865713401, 10.428414804120068, 10.200481575766737, 9.817976682043055, 10.327124018766987, 10.229352589477424, 10.287281315068858, 9.27017601678728, 10.442093278178447, 9.8100802718579, 10.155630664028395, 10.358516086526535, 10.066570439039431, 10.356001301749055, 10.140472778818799, 10.358183126629104, 10.189891517412738, 10.274322420312496, 10.416548454592524, 10.32709331892391, 10.34849659660193, 10.331221864520824, 10.581165168398641, 10.571786485255313, 10.082897286067826, 10.43270986584159, 10.688663544335718, 10.527406434851432, 9.21623419541374, 9.924325240259028, 10.390644566339827, 9.906076279388618, 10.672403153090668, 10.611683077254305, 9.543103801710991, 10.257862971680805, 9.887683259700829, 9.19537773894588, 10.569328337638868, 9.455235955356398, 10.420240878281914, 9.90490610355032, 10.096722886309447, 10.150385603767733, 10.208818923280681, 10.44618842449956, 10.159407285403379, 10.955216046262375, 10.294524395796328, 10.501829673026865, 9.946335944295813, 10.032184407628927, 10.27318338839814, 10.36685264566213, 9.046019582864785, 10.612947757495633, 10.343609407147559, 10.725471955858469, 10.660730544475413, 10.398290668673653, 10.073623476956602, 10.277440846481142, 10.629436939554799, 10.629096842508833, 10.1807554889231, 9.767328461841045, 9.1841298659272, 10.217190050052313, 10.228331750388904, 10.644817706003069, 10.270674447958031, 10.727176177235343, 10.222338711546561, 10.293955248966776, 10.074888790169569, 10.605846222806681, 9.94211267091909, 10.221943652084734, 10.281472772427556, 10.280323554627785, 6.4071131004244295, 10.507186851327662, 10.612274566840304, 10.472410748510462, 10.044053281240604, 10.56625259565556, 10.147815697097993, 10.402518646735244, 10.523707256444549, 10.229185016562699, 10.435390950101409, 10.33740043792393, 10.509023019884365, 10.199906644600429, 9.93189962332549, 10.036233952421913, 10.27413124507113, 10.568525396106738, 10.271145794781416, 10.401394426004142, 8.38882992530148, 9.5072804420441, 10.207501633735877, 10.640565369686378, 10.30847400621058, 9.550960482275302, 10.429348743535508, 9.070377414836102, 10.309831521232136, 10.327786202935997, 10.271006642846848, 9.964546329893533, 10.471267832241493, 10.397909032564371, 10.410020303757944, 10.650841700873187, 10.41269218761083, 9.879583522105946, 10.228939889056655, 10.422064756124799, 10.070061617189275, 10.481388731089467, 10.455574108664832, 10.299270002726695, 10.195604267072476, 10.32786555288796, 10.529838177185328, 10.373511342770811, 10.499879226747364, 9.60393527875877, 10.45191637334266, 10.548971466646533, 10.219035262934435, 10.478005944703229, 9.94079529068366, 10.628318970777496, 10.324614390331474, 10.661946686298343, 10.612074660614635, 10.370941910727481, 9.577928835247999, 10.153695010755847, 10.662237893289623, 10.47674513426255, 10.332520873715547, 10.352198032764367, 10.32432037512681, 10.682225084191804, 10.38173562320792]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.474908317427456, (1.4039251553566334, 1.5458914794982785)
losslist: [10.137472933141607, 10.223889996725662, 10.487474061655634, 10.355312516607826, 10.810484299146653, 7.896299135453403, 10.096199454344092, 10.224738345957086, 10.584502202345144, 10.629177247602088, 10.597883030875755, 10.29211308530109, 10.60457485336804, 10.806877441262678, 10.602549272817006, 10.42267469150616, 10.322762125682216, 10.511907564952834, 10.735952102716487, 10.571810036837809, 10.378252964243703, 10.302528645626882, 10.59606274557554, 10.329601448013396, 10.102755398023133, 10.82593203328101, 10.689628642282965, 10.574743953328966, 10.407890042322153, 10.575912176735555, 10.30070024149138, 10.2643446341154, 10.658850302816253, 10.609958420436259, 10.493615246628076, 11.005247027492016, 10.567450107336363, 9.703608365370096, 10.226799409885203, 10.57435317955383, 9.332074621590642, 10.478948003483199, 10.272269323570386, 10.615633497267957, 10.70342520010146, 10.411566232018025, 10.74014719802358, 10.45101801130675, 10.302440357113701, 0.17658442450805592, 10.283743153472855, 8.965352524657805, 10.47205395128318, 10.211277245591518, 10.503774854690624, 10.726198205151343, 10.147576353757575, 10.654472933806616, 10.522819382765197, 10.75918084155816, 10.411293862707225, 10.414252828495362, 8.816262584238421, 10.403897579999798, 10.550899368110478, 10.717815616338662, 10.267615406505811, 10.694679709353231, 9.463595441306277, 9.862261648391975, 10.646311530770086, 10.021735423098919, 10.532726792452094, 10.824090401967844, 10.094874890505917, 10.471663865533632, 10.5791768969175, 10.638658107800387, 10.35536995881645, 10.286378414546906, 10.728024159741631, 10.419316760969302, 10.492252284764836, 10.55157451209872, 9.556251672006862, 10.614152031778607, 10.483907022200578, 10.54708347719132, 10.393700017863406, 10.659892448285133, 10.656083604569593, 10.027047858568263, 10.668397304626213, 9.991118179542706, 10.394513844941185, 10.239967577137568, 10.398619702194548, 10.777261495121554, 10.257213848304865, 10.084445411809249, 10.552302910220819, 10.690648745111021, 10.27781373748008, 10.515426733571, 10.81066749422903, 10.52570421441176, 10.32025688085098, 10.387327501574141, 10.31053358892139, 10.385226981810312, 10.251136039297446, 10.492851980542328, 10.502576282419232, 10.212115333457511, 9.885076741213698, 10.78946302914268, 10.727604856435812, 10.43828006434485, 10.763656676698412, 10.572565435318047, 10.421410706771349, 10.501379404960606, 10.353485402051902, 10.324558932896538, 10.321088055689652, 10.188652066305476, 10.155311113940956, 10.331382280218739, 10.742338821467015, 10.164942800624, 10.780099618309336, 10.209042635945934, 10.160799572856735, 10.427290011448703, 10.74753387609176, 10.377690725502317, 10.535665722021927, 10.465372588915514, 10.69479837062642, 10.363933280509114, 10.274755171421845, 10.452308855286084, 10.52665462982208, 10.499202104299307, 9.559988498248188, 10.196717583992005, 10.629387678608694, 10.473219558031305, 10.219232481196533, 10.531107125172618, 10.762369580786125, 10.288897460255912, 10.590616837375773, 10.53074843320757, 10.439040154981143, 10.87371787400922, 10.33009407357574, 10.150465383788074, 10.080999438130833, 10.853779828770918, 10.526197906702683, 10.653422966335622, 10.286082166325066, 10.369284733847742, 10.360022091111873, 10.358476844696627, 9.947846779717125, 10.44427819163116, 10.728369236717544, 9.022783060697213, 10.591161421097882, 10.391171889472572, 10.11349055155748, 10.58316233529862, 10.345195769682137, 10.571935476282551, 10.653462906511779, 10.035389139438204, 10.63448448277098, 10.74344109143083, 10.443690923464928, 10.068260693810249, 10.431740687554473, 10.347206690678163, 10.437696158387519, 10.346972112415418, 10.054251825490304, 10.25209036950234, 10.565831370536666, 10.730924556183435, 10.619733658568851, 10.625781699868448, 10.704633222327756, 10.406035881513468, 10.429119780480045, 10.381106811566772, 10.300365951034248, 10.70962286269458, 10.438892988385874, 9.242489875629792, 10.789605567502417, 10.467259758679914, 9.546009014947058, 10.489295498109627, 10.29139282905234, 10.676141306488033, 10.584550967791138, 10.668741864940902, 10.560809128418931, 10.945550433818692, 10.482883239263275, 9.604932061963334, 10.624577587634123, 10.552379904534492, 10.294653939294728, 10.626350073491047, 10.499211172415993, 10.528077703331137, 10.597349311142752, 10.37372017536865, 10.61515380386813, 9.198730144716937, 10.492642785991274, 10.154129852754755, 10.597457955988391, 10.39219580506905, 10.31816133644198, 10.531675379420998, 10.60508865877048, 10.567636721013999, 10.373769540862613, 10.500512136663511, 9.839749069539522, 10.80257674173711, 10.984394840887875, 10.138390042334725, 10.94124909961748, 10.418675142287524, 10.442544234763647, 9.576011034475394, 10.400355348275943, 10.457509409303896, 10.531743634397177, 10.590786842393745, 10.551286107958344, 10.728638405856412, 10.248368056577, 10.453242345124476, 9.483719438872397, 10.480900822327376, 10.228801289635255, 10.602565831343481, 8.665625305698063, 9.978597674894868, 10.678775496202883, 10.348740045437447, 10.331818520232686, 10.952110316573169, 8.98378776012184, 10.690898364406555, 10.322839518571215, 10.698832920895288, 10.513884404325356, 10.409953801366962, 10.396020996919978, 10.517073474799103, 10.32465164668508, 10.566374029867259, 10.318899186009121, 10.828919871042329, 10.604840477795832, 10.488476095541913, 10.475095248501418, 10.35871757060844, 10.470001321317127, 9.987427039124361, 10.772074506717342, 10.63544268080829, 10.511925165066778, 10.163118244041444, 10.543011056767394, 9.427463626654331, 10.68604994086509, 10.512214888220997, 10.643303639164301, 10.371531163808694, 9.046110859268223, 4.366715615473451, 10.391494986521733, 10.506067770786206, 10.606922142835904, 10.600214410563927, 10.57343276325629, 10.624264941861341, 10.351218240698682, 10.628699388060522, 10.850252759679808, 10.27865459994764, 10.703419950402356, 10.63608792837868, 10.424833720406044, 10.379113019375865, 10.283582553027783, 10.690922014548308, 10.494368263999133, 10.129193491130001, 10.46055053645819, 9.730019751432593, 9.3592281091776, 10.583972738655621, 10.359066521664783, 10.571668873865937, 10.472401881436335, 10.584594942375452, 10.58048762528325, 10.433956337207022, 10.012759598080654, 10.45826282937136, 10.647869595393415, 10.67444816524911, 10.043047190697571, 10.489028479445892, 10.301169640497719, 10.234139988813698, 10.563650033348148, 10.54696346182499, 9.835675558331761, 10.056662815473873, 10.553316802048407, 10.451853812029663, 10.28436137798719, 10.333999579876782, 10.654330060322351, 10.379374141650604, 10.699225511953268, 9.972698220565428, 10.434838584905416, 10.583525773566823, 6.716701489235178, 10.616173845938905, 10.470840147403456, 10.28898800809948, 9.620102491042045, 10.576509864577211, 10.101429637646941, 9.776701987910458, 10.51650236074223, 10.321990123822749, 10.726105547864714, 10.721364409686963, 9.019368253511397, 11.067391327399408, 10.473787572298662, 10.527028417212746, 10.108902217121617, 10.473097582714122, 10.46966604731329, 10.769639195091493, 10.178049823017899, 10.611135413059388, 10.382150676215801, 9.830128534185627, 10.100638613433478, 10.765670542619219, 10.319880866707988, 10.571839181990264, 10.560993936674864, 10.574262440006306, 10.521476982972517, 10.47177975947018, 10.774756035815821, 10.516642940041567, 10.282067270367216, 10.55918675641386, 10.90872325736425, 9.820066001243546, 10.628930706870337, 10.621255222545056, 10.008488702712778, 10.046084504463526, 10.652759567677673, 10.240042934551502, 10.639672217206094, 10.158126318275304, 10.433591254231459, 10.543917313678898, 10.749273298261091, 10.069195853077145, 10.725282357364044, 10.488530891685791, 10.250002151590644, 10.662999818122378, 10.327394361378188, 10.45030033135879, 10.62346600006624, 10.354590213442858, 10.336869383425553, 9.556431728402101, 10.208419037923896, 10.54930219410828]

path 5
init_u, CI: 1.3115487411562174, (1.2480938617544037, 1.3750036205580312)
losslist: [10.061871332666517, 10.485328907155454, 10.236278648380704, 10.801951224291157, 10.552728057470564, 9.674602407746953, 10.617443422481484, 10.550710330054612, 10.579732436320004, 10.337795222005996, 10.107889981321286, 10.66946233144549, 10.88319909929072, 10.675467441992616, 10.772224864732033, 10.846103145292517, 10.844161139948833, 10.477177248449511, 10.61421329020795, 10.28491909249003, 10.54280016034592, 10.55746216678452, 10.600455199304719, 10.124287286647832, 10.501300957274644, 10.633269144709256, 10.582513753318516, 10.821397972067292, 10.609874551822843, 10.581427971987807, 10.824221531559422, 10.178854753346847, 9.96681102640766, 10.53510417205303, 10.480218706244397, 10.45760174983145, 10.350776077084921, 10.178078163252511, 10.748916623707432, 10.468095625560242, 10.563089509713649, 10.220211656466603, 10.377091023802588, 10.715880847448592, 7.378980422002625, 10.995206327250571, 10.775427824773779, 10.600055226773339, 10.659025119844246, 10.611972932269785, 10.95024728046742, 10.557272054407667, 10.794357368884555, 10.505933452073315, 10.73237907895454, 10.52970068014496, 10.755603628349728, 10.63714692516909, 10.029764135738558, 10.271644256644457, 10.766309395178572, 10.645331020776059, 10.432092523825029, 10.619661043662244, 10.60824981947821, 10.625900943034885, 10.386246486048842, 10.453704675658386, 10.624975331653175, 10.674727296189552, 10.032520455184972, 10.794028902924696, 10.786238788445562, 10.717833368711604, 10.692533798889746, 10.338663469281952, 10.64047468761592, 10.352049680063963, 10.716233000226076, 9.78548074064529, 10.571393691707376, 10.098770357281067, 10.669785971955994, 10.189854184625732, 10.855474042864566, 10.423756207137778, 10.265728271487758, 10.510299403158271, 10.885093314317526, 10.559469127671269, 10.579800437304785, 10.285339148774932, 10.436091484701645, 10.718245613282619, 10.239199851621446, 10.88636551498902, 10.743061879555858, 10.974219229197455, 10.446739673887263, 10.617778873712767, 10.75142745448083, 10.313754066122334, 10.55410353982684, 10.71824642675129, 10.547134237301957, 10.6485472735555, 10.737933216591761, 10.47247103677741, 10.567030056320064, 10.35578030114097, 10.73305389606926, 10.621953923332233, 9.91290735491111, 10.092130866095365, 10.329552165285156, 10.686646523740425, 10.125256329976027, 10.621836114314727, 10.40301565400992, 10.783621743796399, 10.688984512495596, 10.440667047044675, 10.587371263440671, 10.681452406483732, 9.848012084573512, 10.646406257682004, 10.71525569186213, 10.557587853087902, 10.611682388082036, 10.536684890427209, 10.522643642022134, 10.512004172901422, 10.188270597352561, 10.911764854664792, 10.526314775440987, 10.40066455409849, 10.629346486809185, 10.97198882708874, 10.353692191704887, 10.821599376048734, 10.69234061616236, 10.660292173725468, 10.691346633120869, 10.769985877687112, 10.653846102082674, 10.337011224361802, 10.572790817551898, 10.628153599116084, 10.633018884770381, 8.475897149597158]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.2897153198917515, (1.2270185964845517, 1.3524120432989513)
losslist: [10.570976059890905, 10.675225055634339, 10.734577104775122, 11.272239441207251, 10.551421636598663, 10.920858330413711, 7.794503265493908, 10.345675715851462, 10.659416873925164, 10.794860387413413, 10.329188100564641, 10.456562785016683, 10.81674936776271, 8.717599861241363, 10.661622326845594, 10.866305129697071, 10.542170550569603, 10.568914290699862, 10.878409708007656, 9.780312161933647, 10.734651803703482, 10.820726882549886, 10.619988439221782, 10.815974463807029, 10.656702526536142, 10.66165997054958, 5.9520826219619, 10.236543050594658, 10.879737972972586, 10.647089212568414, 10.662208737525738, 10.148379503566645, 10.519529250324444, 7.712811575367188, 10.494304246615592, 8.036605067917266, 10.613988822526318, 10.85512520574345, 10.711335919665354, 10.462567679544355, 10.758923335599405, 10.685924966628733, 10.657940103778811, 10.512724368319963, 10.237657462464181, 9.111734418305284, 10.410332476180843, 10.696746008095683, 10.74752288256252, 10.713884865758002, 10.196818313730342, 10.843826165948219, 10.767107812172057, 10.505317171519577, 10.519505349069021, 8.484531096826117, 10.920340412462066, 10.784278945026935, 10.75078509695437, 10.679119871339363, 10.748968292893005, 10.700112158088903, 10.804512614820135, 10.770183772974178, 6.397564965144556, 10.828571566580244, 10.901764301238408, 10.572042285708386, 10.77295216437089, 10.77536767630753, 10.949991997283803, 10.996229578100593, 10.714316196429207, 10.47450304859657, 9.67742997433135, 10.894050323548944, 10.71574571873055, 10.694983069802491, 10.747123474131433, 10.799605975756222, 10.633075019069034, 10.657514021358272, 10.412443031685571, 10.717964081674003, 10.593292629944663, 10.803067395211652, 10.872315605572703, 10.622978490633814, 10.681413909121751, 10.460013021025189, 10.322141087985573, 10.682351436238424, 11.09432471396322, 9.601694588162403, 9.438565033062595, 11.272810882527194, 10.773059376648522, 10.644599962227064, 10.968021061368416, 10.78798445903073, 10.6060466157805, 10.647104298494863, 10.875484774015316, 10.83029854814094, 10.848667582783323, 10.607628961946979, 10.957682299495668, 10.776194024312273, 10.497583765410143, 10.978033789507808, 10.960360870037478, 10.706023106906187, 10.158353401711313, 10.628048463985284, 10.772928755623864, 10.60354539457666, 10.820773548171312, 10.258840614877638, 11.060746140202419, 10.71952345351901, 10.636820203563566, 10.565031729899793, 10.627703303433226, 10.962883328428155, 10.8581576299601, 10.971635510522404, 10.980236625395245, 10.484547989638937, 10.728385074825919, 10.714703387583148, 10.508402306323251, 10.61422240070315, 10.792762648274993, 10.454711419061777, 10.876763523463273, 10.70008576078693, 10.823645991298552, 10.894261476530344, 10.94095167822475, 10.779393441659138, 10.988516639280505, 11.019384019597567, 10.924510951102015, 10.461255523772843, 10.777052147056386, 10.598444126491344, 10.86034718633424, 9.250785542781175, 9.816985118541844, 10.695149015288708, 10.716191680641316, 10.8905853978157, 10.874284956040897, 10.707066198889175, 10.742479417323564, 10.750245581756431, 9.932702342788009, 10.945580236045721, 10.6174918210591, 11.110660221632168, 10.811787040712343, 10.825169564120309, 10.894812903542949, 10.763631809071638, 10.77098978353627, 10.58010471960829, 10.350962668998596, 10.7027880095568, 10.743639506716374, 10.755550282960932, 10.977722338481378, 10.795765354079684, 10.506555860684152, 10.730430351073037, 10.477703127072093, 10.538525146875925, 10.642358972932913, 10.768113489282282, 10.656738796504419, 10.767431156171106, 10.110270037694221, 10.805197857361604, 10.519704457286283, 10.26105034413076, 10.746586093835575, 10.465539882419511, 10.862072438011708, 10.454105982855747, 10.594761724079596, 10.636833515477063, 10.654113010516655, 10.542748502100542, 10.755077690590662, 10.077826401790526, 10.693964124397233, 10.474726115281426, 11.10987304325996, 10.67591015487216, 10.967542147088038, 11.002561095681598, 10.723636555419958, 9.5673978788725, 10.37694464806422, 10.689071009820776, 10.380535017224286, 10.515632289767241, 10.869768447091985, 10.902630392036453, 10.52209736771886, 10.517188105630733, 10.69274585358236, 10.726240826242037, 10.35753306826711, 7.618793966438019, 10.301288244936023, 10.146270492523628, 10.678339373241478, 10.797845041206225, 10.868091508029782, 10.862045832474484, 10.673205161955329, 10.499847724228438, 10.686186566118014, 10.84172027300511, 10.815248114307145, 8.891066642437794, 10.41766651675274, 10.955556219824432, 10.6597774142546, 10.675133176045737, 11.021358823962986, 10.93714789730864, 10.592195832066627, 10.786633893018555, 10.692082285737328, 10.884662479072025, 10.182841529358067, 10.398212096236614, 10.567902752709568, 10.654841501120035, 10.846263671266247, 10.808225251568102, 10.928519001199266, 10.702571713202754, 10.93134287450312, 10.731634346485095, 10.665194121013686, 9.871759985559011, 10.891912118941587, 10.638932306829084, 10.384019589354462, 10.776036009424146, 8.880662230598116, 6.27695755472648, 10.649322295201536, 10.604146528646153, 10.804250441698512, 10.834863093553906, 10.558272074431429, 10.725945115403682, 10.579591817332721, 6.266293635106661, 10.695980764602771, 10.725780950527083, 10.695757890499095, 10.961179971100004, 10.611189917351927, 10.98174851307544, 10.83845725254114, 10.761496082911846, 10.528492364664434, 10.104659214795076, 10.698621770534748, 10.710567572984893, 10.56151326828021, 10.757259029972829, 10.818757590651167, 10.520102535356733, 10.659983720343568, 10.486957796085838, 7.886407622317039, 10.268659372456542, 10.761440374743593, 10.721081531933772, 10.87845738478901, 10.813950786167378, 10.754313673293893, 9.853123404548372, 10.67610497233691, 10.508339560369627, 10.798428357966928, 10.783876990734328, 10.157999170117336, 10.826369286940905, 10.685858378222521, 10.843444562213463, 10.6796305684223, 10.64585134582286, 10.679744359597157, 10.890358091576406, 10.604390926206008, 10.94467715811485, 10.85434258346971, 10.414981825885949, 10.883497622709731, 10.88824465325064, 10.712543874009956, 10.67498073784046, 7.503081319720023, 11.01613484860084, 10.303281796930204, 10.804683767931005, 10.73647834258211, 10.727187737112724, 10.329356885167158, 10.670829996258902, 10.385409425568065, 10.469789089161324, 10.632604471474677, 10.795927788468608, 8.862031424158099, 10.767054421822513, 10.694386674713687, 9.33729698924874, 9.37619518140111, 10.544032792133041, 10.652352607044449, 9.902326678545242, 10.70760847168683, 10.856620224025189, 10.7610094785503, 10.5102321250082, 10.843356559616916, 10.698086685619364, 10.720499348504807, 10.779124273022832, 11.009454104848995, 10.7263212733916, 10.796435693352985, 10.652402240349572, 10.532858782837236, 10.507644786550559, 10.748777692143586, 10.541868234321171, 10.272361792171344, 10.452807586766859, 10.556196468276296, 10.981238307236318, 10.855272393144043, 10.746403068278303, 10.8314734465754, 10.78149756731221, 10.879021299000732, 10.736979153220357, 11.02100764049378, 10.657898904448047, 10.51530155859852, 10.82355983637703, 10.538181682446053, 10.503954547484641, 10.669570584203774, 10.766518645968052, 10.639307119774733, 10.796353964747487, 8.561361452186944, 10.657481678613895, 10.558443197448474, 10.323340042172845, 10.28165688015445, 10.201258281750203, 10.375391602766008, 10.464703831396292, 10.359802898255168, 11.115029451251882, 10.761808055814717, 10.562786327105416, 11.263314632894302, 10.877442807801255, 10.600018955915324, 10.79795576054531, 10.81843868710334, 10.569203738556563, 10.398542439210356, 10.712267190405289, 10.647030562945623, 10.710558936178806, 10.763725078881391, 10.159687256344755, 10.5405512483978, 11.032711586371457, 10.563189287542775, 10.764725978753479, 10.780042690641153, 10.446528462585416, 10.688936169678177, 10.284256343422376, 10.789855681764974, 8.667859000513241, 10.752162203063438, 10.183351553271958, 10.591632634971049, 10.003382497353103, 10.004878795896682, 10.840789494937086, 10.926346545247036, 10.989340648280999, 10.690974365132606, 10.177077346993988, 10.735260642366832, 10.663113351677424, 10.829480737447529, 6.205942237611177, 10.813003644934314, 10.822092197133815, 10.602007809641389, 10.22440186519523, 10.902192036529001, 10.539793353428665, 9.075356641092785, 10.855865813358097, 10.461862147230502, 10.645124141534627, 10.779583819775986, 10.783412063764008, 10.706634077730198, 10.676128228736415, 10.771153719150531, 10.426218863793215, 10.787736243523986, 10.378285887024473, 10.656638989318663, 10.63653922199527, 11.03757335958351, 10.10405794443894, 10.703928035270605, 10.79868013191116, 10.740976126410619, 10.81126986386442, 10.883236920083451, 10.713819635930172, 10.590979088072741, 10.508604735766308, 10.668500880848217, 10.944346428813247, 10.750039924378285, 9.981934651133656, 10.908245981635565, 10.21167312123686, 10.630670468809656, 10.74982526706083]

path 6
init_u, CI: 1.5967286302980845, (1.5186136249978208, 1.6748436355983483)
losslist: [10.654310884901244, 10.634251775418734, 9.885791321713596, 10.400922095452339, 10.227498479891251, 10.512986429069322, 10.445298191836239, 10.315524268405746, 6.397896165944026, 10.502816303355745, 10.494345442270147, 10.445540675421572, 10.108572146028436, 10.294545682249506, 10.385304122742781, 10.296872236952835, 10.418283224510128, 10.531674196888979, 10.527555253927035, 9.819221970089004, 10.486973520607783, 9.90196823409114, 10.278782142485328, 10.64798293608665, 10.656232309976536, 10.307030931371713, 10.451085863454685, 10.365339626568279, 10.4337407895157, 10.072537797257521, 9.920668872876625, 10.178226428570571, 9.428824526187885, 10.511446583394457, 9.444510870694604, 10.220757248329681, 10.176261678190249, 10.302031531316903, 9.540900483656525, 9.927557153880414, 10.704852197273604, 10.50643647703184, 10.466864576661708, 10.189787600235018, 10.599305558674088, 10.708053709074516, 10.628458777747804, 9.409743558049895, 10.550076868217133, 8.99401599113166, 10.458162239671545, 10.506260334994726, 10.409691579352923, 10.390765394531165, 10.503172299950265, 10.075607061266917, 10.71419091070953, 10.759850398928574, 10.00136771033914, 9.692710080529764, 10.46465923686907, 10.594299765800127, 10.395733000394024, 10.419833482344279, 10.917983792129705, 9.997300648365504, 10.211336704884252, 10.178123875799749, 10.471726429056963, 10.30772658939744, 10.544926200005223, 10.583096265533388, 10.607934217799192, 10.367658667376688, 10.59548766800512, 5.408164973511344, 10.607175839315765, 10.359327971755361, 10.583861470480501, 9.926395598686588, 10.522529367070595, 10.511247389800493, 10.554787378390596, 11.23648948765311, 10.156961914958199, 9.687748155595589, 8.120180769462655, 10.48776980500305, 10.476597783004085, 10.489882237346134, 10.38618051953712, 9.872860556543205, 10.765649073879853, 9.914136730812421, 9.246393588537854, 9.978463365470418, 10.273734922294063, 10.432699315703445, 10.707772668317746, 10.375167669817627, 10.46725056810145, 10.925074434842465, 10.550881734955903, 10.244355116843582, 10.670397799040062, 10.335693976243686, 10.527264808846951, 10.351565810312819, 10.491143030583443, 10.75737907685504, 10.63266282292056, 10.343157089548496, 10.813674009441144, 10.165734533689056, 10.36221720871153, 10.079883614580213, 10.521949838250976, 10.172125379835997, 10.643973323743037, 10.537344894965441, 10.526100142992501, 10.492392920092156, 10.360842389160922, 10.416242921628545, 10.3629858301679, 10.422136316167634, 10.406892359481501, 8.984462086718429, 10.501899778394833, 10.447377891533803, 10.441321909967774, 9.967769959936469, 10.1877406843408, 10.415146983850672, 10.251417672850547, 10.31965683164604, 9.97574804953284, 10.824443997322556, 10.660086045969356, 10.438223212289772, 10.18808221741371, 10.67144947365528, 10.338224302621057, 9.716896758385447, 10.359412482403453, 9.290213881861266, 10.30685565149715, 10.299607051890451, 10.269839043343957, 10.56453565948134, 10.446675646414977, 10.287902760024618, 10.502158008857277, 10.678345735421344, 9.934666188396605, 10.316003118568009, 10.516982367193553, 10.267367684044686, 9.572036416883194, 10.65772123632884, 10.328348828123794, 10.36670380050154, 8.933382808060934, 10.392709645280192, 10.435926365372557, 10.746467233453213, 10.42246382678581, 10.630645149577502, 10.430513562059554, 10.430206077915374, 9.631969006932183, 8.943339941266926, 10.528216342561253, 10.689212077820487, 10.056678348035344, 10.32938377741235, 10.453960837882885, 10.638494127906899, 10.338782960633583, 10.360391882055621, 3.6722217085195075, 10.574090593113345, 10.473945395469018, 10.212211655101816, 10.49411662795591, 10.582899520738792, 10.606138795931784, 10.724783978647261, 9.977215566849987, 10.307989868150235, 10.79857871801431, 9.421282659514794, 8.330434150736627, 10.440423356924967, 9.718078072205504, 10.399618602431849, 10.284227540913193, 10.24022622675534, 10.447394018407145, 10.312034755538882, 10.492941466773848, 10.047808995957585, 10.681976256389538, 10.068206573753569, 10.390267410570413, 10.485884999927436, 10.566536798276694, 10.422534390047005, 10.529272464497026, 10.156691306875427, 10.324659567520449, 10.623593916214267, 9.762944804402963, 10.230832442948877, 10.638718388964042, 9.979445774742604, 10.725773085218611, 10.342973066205381, 10.567601146211832, 9.954298251439353, 10.710867603947182, 10.310827867684791, 10.191213208422834, 10.165726305553942, 10.660256073881587, 10.630954210408541, 9.9296250007263, 10.560813102550023, 10.249618089104121, 10.555953671167007, 10.223277134563261, 10.06278266933112, 10.524533480563505, 10.470363068292514, 10.371552196786705, 10.560098386131187, 10.3959018045313, 10.5936055183498, 10.45788573459972, 10.501666962691182, 10.260522551419372, 10.491120941904308, 10.629711897310298, 10.436018405233847, 10.194428496262484, 10.625536201605334, 10.645082000009443, 10.631573191199706, 10.496366319338776, 10.501762766687644, 10.37274080757745, 10.50824436026441, 9.992206622302449, 10.70694213611741, 10.537728522279899, 10.444411591026885, 10.215572013288329, 10.38869888006313, 10.451689585829234, 10.659629362648852, 9.892079652017548, 10.709693999744491, 8.75360306112077, 10.800418600661635, 10.329294916715568, 10.634280773041292, 10.774579402594664, 8.854512637257729, 10.652967667942994, 10.505702176721803, 10.414364677601506, 10.392620049932537, 9.937010951266872, 10.452086393977945, 10.696166606280443, 10.571645539958828, 9.981650990399471, 10.101476302464453, 10.435468897391004, 4.352609807886895, 10.417056552940034, 10.219848719735163, 10.240864437424555, 10.76886802856598, 10.59135051731221, 10.515797181808464, 10.55224703237931, 10.493256364801091, 10.153695176334633, 10.427940172252994, 10.061207994479757, 10.412789247018884, 10.123613935197264, 10.649076687203516, 9.800234273155858, 10.681551973850937, 9.06896007359479, 10.313387878104065, 10.348017979209436, 10.457406603895494, 10.382117458028569, 9.330469656975538, 10.152121054425477, 10.635475129765423, 10.272222154586958, 10.453898863941465, 10.185360036206418, 5.9141900343448315, 10.31315371906564, 10.398004272617078, 9.972423766907532, 10.465561609018442, 10.411365757876432, 10.209511370212276, 10.481648387974833, 9.556458550962665, 9.85888129807979, 9.501584900866167, 10.55891500668274, 10.271485529737452, 8.6851138339915, 10.539253879306413, 10.65047547692576, 10.494392449995468, 10.662659839474316, 8.616841874284415, 9.77834731921767, 10.630972257777964, 10.682682836772273, 10.46955190528705, 10.173439279395057, 10.418106478320242, 10.463345977506227, 10.358402025918215, 10.135186320742255, 10.395108205352603, 10.613495754562356, 9.775916084156778, 10.584865442943942, 10.380534454413196, 10.550674413840557, 10.71457883292206, 8.496832046500925, 10.327072955465548, 10.871812768907501, 10.549897421493794, 9.498098134084263, 10.444191756987927, 9.931221830445168, 10.718687356998561, 10.536986338965892, 10.783034697030255, 9.036423459971893, 10.548055448320751, 3.895920053370271, 9.546932429380956, 10.360995539603646, 9.813919508917769, 7.711252662707225, 10.121481786095643, 10.334005636779922, 10.46136382871289, 10.525037235432675, 10.307471465374217, 10.416637070056359, 10.69661567369874, 10.40724215093242, 10.307982731949979, 10.19073454869885, 10.365959221227126, 10.521822179572426, 10.493211353360403, 10.184548354264042, 9.921951250671015, 9.426944520802307, 10.341833265895776, 10.22193788015662, 9.11216702584688, 10.41398638848239, 10.26492470956667, 10.520877705481206, 10.737935693596274, 10.481397603657626, 10.47592054258266, 10.20461851050898, 10.555603508753231, 10.3294426611336, 10.383408020617168, 10.563539788990477, 10.27054729389657, 11.074361792405625, 10.456839611405302, 10.360403136945012, 10.227081813839396, 10.328668742953875, 10.583781947821254, 10.089916396561966, 10.292483292568106, 10.610233826289962, 10.46348666464028]
AVOIDCORR
Most correlated pair: (3, 28) (Birkilane, Mbacke)
Cut district: 3 (Birkilane)
u, CI: 1.5191899560186553, (1.4459312340540311, 1.5924486779832794)
losslist: [10.377147297192181, 10.506899921832023, 10.72359231253763, 10.6077572244081, 9.489216659025452, 10.573588840373342, 10.94716008473544, 10.736339591615604, 10.544208786843749, 10.429910142042754, 10.367393917726138, 10.4430124844472, 11.170494926641881, 10.703073358016164, 10.7539022499159, 5.597038414746845, 10.281355811278406, 10.573370601783695, 10.741288185680002, 10.443911732229024, 10.637853444754926, 10.688470956012937, 6.521451964181904, 10.37393966534327, 10.563961428040002, 10.439956045498793, 10.905443877939351, 10.67148079649792, 10.365499758059292, 10.665234246974963, 10.529540895518917, 9.885922116060739, 9.926726861844228, 10.716434974241148, 10.726434146104124, 10.593480387405561, 10.373255061764208, 10.293556526625935, 10.095226101396666, 8.299433961545084, 10.537697729331235, 9.933406066698053, 10.22515092528724, 10.743677703912395, 10.288482817453527, 10.711841630026678, 6.031871802617395, 10.861599373238045, 9.867371129022612, 10.412321101021126, 10.641824814795532, 10.51158072069967, 10.681155809415609, 10.619641352886624, 7.897417785604792, 10.542427500835556, 9.789947083135875, 10.302751899703589, 10.765982623718168, 10.606956667816501, 10.109299177222367, 10.797902102963878, 10.861612248252845, 10.473243168581345, 10.424518495695105, 9.384675261417057, 10.428718678921058, 10.454269758445532, 10.20288101815112, 10.717053574806519, 9.37002976788951, 10.479576413007985, 9.455903204988386, 10.430410625355837, 3.304877848632239, 10.493459460426982, 10.362402403148074, 10.232653625999472, 10.395952323706489, 10.593051869319018, 10.63644437160414, 10.841403327373207, 10.617766783227035, 10.405621655433993, 10.500009142209082, 10.675711774889468, 8.466806946169175, 10.623131568878826, 10.620231448019243, 10.354064572442324, 10.53927445836222, 10.258534121528655, 10.331836089829766, 10.607050939581951, 10.303579162011182, 10.371145211956499, 10.338709484935809, 10.494597575919071, 10.410663449284256, 10.63534681215662, 10.802708679926894, 10.653901250195224, 10.560234069870713, 10.58365663605258, 10.456242117357991, 10.596737791579063, 10.554003783436515, 10.350513489672084, 11.03806693784321, 10.701169415391602, 10.813846420936628, 10.472487346481724, 10.615020115010292, 10.839140787915301, 10.598615126090884, 10.305698261821735, 10.426593644814911, 10.411125103277584, 8.879797564810938, 10.673075531472886, 10.708538685960326, 8.14687617238018, 10.749536258009657, 10.623079017560622, 9.680252035689795, 10.618894479410432, 10.396805314578398, 10.532673085621703, 10.239178381654895, 10.553357095938315, 10.112185978421259, 10.693036497697282, 9.803975323948325, 10.65243704171623, 9.2657889330564, 10.338670784991786, 10.462257432772073, 7.645484141969358, 10.905863835036707, 10.88004888035662, 10.367871980786422, 10.469031041933947, 10.416492598407862, 7.886356884113049, 10.375220272228166, 10.384659192380896, 9.402516911687343, 10.636878503072406, 9.70153291106136, 10.92773509429114, 10.796197382943195, 10.426723862154931, 10.288987768444228, 10.318542761178863, 10.900994158463675, 10.682922548128387, 10.694279784469458, 10.371020683212821, 10.797856612133465, 10.334627552935729, 10.900458201601513, 10.784260888210659, 10.180176237126409, 10.852176081862522, 10.429534930517299, 10.290229379711807, 10.65470012826415, 10.36665342864846, 10.22015325773791, 10.55546319008173, 10.453565647609155, 8.749600769468602, 10.897214183959608, 10.50927676949484, 10.031449882433883, 9.882753470806163, 10.412420833136375, 10.44391387350021, 10.386814870870113, 10.030989329609092, 10.245431699751697, 10.412452008642896, 10.60809621218971, 10.545843860166245, 10.382929105117716, 10.028919954213613, 10.478425920940984, 10.612747756675011, 10.436628337679585, 10.802659782494976, 10.254813636274875, 10.801082266324938, 9.773289504460918, 9.77301929084832, 10.697299313993273, 10.618548208512246, 10.771557308623898, 10.40323726418344, 10.276260644491781, 10.58895912687024, 10.353007953467547, 10.274077267197383, 10.528440807494023, 9.429261113403864, 10.440096701743158, 10.405373112914376, 10.715752693114503, 10.62997398327605, 10.49729284456879, 10.514131444249028, 10.748165782413087, 10.518536642048005, 10.56479507821793, 10.452123188994259, 10.468539518236131, 10.480913741348038, 10.668894428830846, 10.461991600890707, 10.372742294239938, 10.7142959417615, 10.581342768178658, 9.668068700239479, 10.218624195814687, 9.907244631152482, 10.520320382839875, 10.742406498656038, 10.248763107557371, 10.533126658160041, 10.400812852864197, 10.753602190652774, 10.509939510125227, 10.143184212635246, 10.09227928776327, 10.684551156657648, 10.365247017228839, 10.622226414283013, 10.413580377154984, 10.437730913134073, 10.636242852968225, 10.345722653010775, 7.9846128618008505, 10.898673397208245, 10.40248727951723, 10.504525016082962, 10.13053928280468, 10.638187009051848, 10.626197896333206, 10.4027314455867, 10.66052280482559, 10.129540495438397, 10.358226080004824, 10.386337331535277, 10.057536240595159, 10.567497716595652, 10.548042533298236, 10.395296343343361, 10.376729136627002, 10.142357125889637, 10.354448195428649, 10.4230693738244, 4.924560268267173, 10.43787534892017, 10.286769758570172, 10.554627454068736, 9.99939469697675, 10.257909325465143, 10.063866398864162, 10.796911469399326, 10.622743550254723, 10.59036520903759, 10.448225189732801, 10.612844904883508, 10.401946072994113, 10.626192521931268, 10.589952687826116, 10.461246842234047, 10.549498867935611, 10.77988450410688, 10.30614321843755, 10.792462990483157, 10.12880665250685, 10.392909806610968, 10.606893734706492, 10.684643327356948, 10.37140347202358, 10.481910812148843, 10.527459884684397, 10.497627701291927, 10.569676526542928, 10.71573010602926, 10.191368397368903, 10.612507079864237, 9.635644221249024, 10.606321903896896, 10.230778545747494, 10.132642548581037, 9.89799058287895, 10.6359690895749, 10.343073563405476, 10.552442878027373, 10.34291608334866, 9.892327744925929, 10.475477834945842, 10.665959698171399, 10.800831338031893, 10.367064869605999, 10.450066735258599, 10.767558849430976, 10.127560885149043, 10.54833785244649, 10.251500230276726, 10.508181195178192, 10.766125624015084, 10.495068507542628, 10.724269743257766, 9.686859678981806, 10.286077182335669, 10.517766295304899, 10.608383218532756, 10.071692339525706, 10.16034912535199, 10.479498819007313, 10.095401556036695, 10.473616861939652, 10.50490700281629, 10.716417383591562, 10.52330641881152, 10.360537255026342, 10.387711203980297, 10.602300735438808, 10.42941624368721, 10.431689739716901, 10.337338055025585, 10.440859789217955, 10.578962267159984, 10.729839316447642, 10.55046591362602, 10.560056883503696, 10.570069323251321, 10.845511931576043, 10.681048259897233, 10.503355026494564, 8.404859000234772, 10.280130948258027, 10.377568825953508, 10.523927225621645, 10.352338450351857, 10.561120511126056, 10.346953349620055, 10.516711910197229, 10.64266882849395, 10.54165461986065, 10.809138036585086, 9.624299540875043, 10.424247391958781, 10.299189304246742, 10.545875777903431, 10.478962846095124, 10.646373005572828, 10.190039713831668, 10.48455637566365, 6.536579107425611, 10.693834440723391, 10.741132357118019, 10.442664723858744, 10.377680101566716, 1.2215649044861907, 10.817895228290404, 10.806680325940553, 10.660310254184347, 10.295691258670594, 11.01306653951568, 10.816754515608023, 10.467770349325328, 10.405108543872172, 10.460570885907531, 10.413190833525723, 10.396881773837473, 10.690204583556268, 10.74702520188568, 9.588892441744152, 10.188513127092136, 10.703620544204648, 10.848160889941735, 10.404018557996618, 10.902580362515645, 10.737559328829509, 10.658155656255678, 2.8920337375396796, 10.528396211404738, 10.233163584283838, 10.462007716486635, 10.25668257704671, 10.632502667025436, 10.445038559067118, 10.533940251151497, 10.636902174381394, 10.466028203373538, 10.531610724272014, 5.002920145659039, 10.639076252558318, 10.1826671083228, 10.352830432354446, 10.858660452942704, 10.32919157437307, 10.321136004718115, 10.640742955022574, 9.414861745480474, 10.548627841868926, 10.575725957869857, 10.543450765187666, 10.786604488239337, 10.55916191812505, 10.264240144776915, 10.649159923794251, 10.689937137994198, 10.67648998213831, 10.068821103116058, 10.739978152104896, 10.438550473418363, 10.536899252189123, 10.144737412817886, 10.632967686691298, 10.625243328898007, 10.594638041879907, 10.289118167589713, 9.367386512456367, 10.743098412861428, 10.14757869093339, 10.800342713428874, 9.706547119106785, 10.665908125023746, 10.140458130144816, 10.783513211079553, 10.350970833811246, 10.346566367258252, 10.828696329263872, 10.314413333304412, 10.766463064927434, 10.101723534832146, 10.164129778396868, 10.583551791431137, 10.555851130932579, 10.16500230323403, 9.216518337261807, 10.113230354877478, 4.99591752431042, 10.380215974610229, 10.45919034085947, 10.035201935899355, 10.725653615307053, 10.63812947062907, 10.811208304460322, 10.312049641399812, 10.174154953021679, 9.085364103671202, 10.522675828840683, 10.521723972200173, 10.661108018150728, 10.1910952013134, 9.887126494346694, 10.541996070382408, 10.560301894865232, 10.429167649963983, 10.781825945066034, 10.264129717268816, 10.53325272492108, 10.924751339842244, 10.561970287121222, 10.111874352740157, 10.186161365088152, 10.594045667689597, 10.39397457825144, 10.702202308982447, 10.813546112391661, 10.423747329965469, 5.296563172337839, 10.397552126438999, 10.359626991810522, 10.456135537091715, 10.609126570544406, 9.834572769035448, 10.536243641447346, 10.583716311564444, 9.981027597571083, 10.578892202751112, 10.62825537801821, 10.579834147505686, 10.289685573351383, 10.273000291433682, 7.159871632960208, 10.27519042498315, 10.142473630450839, 10.067427273799925, 10.666671839819893, 10.142462345148958, 10.591300964786537, 10.394067065971408, 10.458704204521013, 10.252610997789873, 10.325875551013565, 10.399338975726504, 10.254879459077895, 10.589664298753528, 10.555895407389949, 10.553952824385119, 10.519676375497877, 10.32322144857834, 10.715229579140527, 10.307740096378868, 10.404761891783664, 10.074554383661061, 10.13557415528343, 10.491598800889363, 10.446063499728645, 10.389714147122353, 9.585854887208004, 10.215011400693985, 10.69699431625374, 10.656644624016375, 10.890130288765212, 10.72905671008722, 10.410651626675971, 10.46952559034218, 10.679080912095158, 10.673086192650029, 10.455678042332861, 10.65394404916713, 10.53137117369228, 10.289410265258745, 10.799654451359933, 6.48554030488152, 10.517110254357963, 10.73279995550044, 10.538658246235538, 10.669919059950814, 10.533767218815065, 10.798292288120368, 10.739945561894926, 10.383883629295347, 10.675619914581212, 10.617445100168045, 10.975606291120819, 10.85846787721464, 10.770741818475695, 10.51740891653904, 9.897971602193762, 10.49923250628988, 10.067719580025315, 10.395665827385626, 10.504408525984854, 10.903330567072313, 10.510546554965703, 10.725111466152722, 10.16732909207946, 9.543305772714772, 10.648831530372435, 10.56878617864449, 10.508412636910764, 10.720214852440419, 10.56885125305835, 10.487720548522882, 10.547065507052755, 10.493714377755076, 10.484458954515508, 10.338358491363755, 10.397143785148904, 9.953929276188006, 10.435786998979667, 10.52740775173937, 10.581296368266587, 10.15263587032094, 10.657011974811386, 10.70092190860055, 10.477844094551761, 10.474396058520027, 9.542126161553156, 10.682606624284531, 10.500478473077473, 10.282607591728668, 10.6117640542357, 10.623728721691402, 8.78901486521928, 10.539359960786818, 10.349084538440367, 10.743098873111691, 10.432255724172128, 10.282999139081634, 10.173672349158872, 10.490549491896866, 10.598388931994787, 10.241578758828641, 10.744687786150491, 10.724920826556462, 10.459022197401232, 10.528693043811732, 10.957267491250656, 10.514756635876546, 10.903804081834291, 10.137423418518711]

path 7
init_u, CI: 1.9203010691352596, (1.827701755353317, 2.012900382917202)
losslist: [10.135826321715598, 10.31580356926748, 9.966208049657316, 10.490952216676886, 10.156956786063551, 10.494241408572769, 9.27859703382336, 9.514559147876492, 10.240797564065096, 10.245227487542932, 10.55196058691889, 10.079402219572351, 10.504225253179996, 9.935619215291261, 9.305203702544413, 10.191730495571925, 8.94561584235801, 9.97189678680526, 10.731292159627213, 10.389568292614387, 10.293642895248988, 10.095740732925353, 10.407293860019564, 10.440674189617784, 10.48760100484159, 10.147580348422231, 9.9659612402969, 10.16268716970986, 10.120485566068053, 10.570150729788757, 10.082989872695062, 8.20651886323322, 9.779461384994024, 7.469990251801009, 9.930742051402424, 9.856040910533599, 10.44446854390604, 10.134194405318773, 9.868771465922203, 10.430454318127698, 10.632945565497765, 10.569419727090647, 9.699702936885025, 10.182843455418674, 10.387764620690126, 4.567022503439604, 10.383709667371487, 9.712795058064362, 10.43089040213039, 10.48822791321342, 10.263636617250036, 10.178643307245382, 10.421716427060623, 9.460317591227527, 8.96095837273694, 10.264604385453772, 9.84263727653259, 0.15515721101135752, 9.650735124935782, 9.976416932205913, 10.368890413753585, 10.502543903443042, 10.19560836347201, 10.47348774768714, 10.475090699932165, 10.502637884373572, 9.666614076837547, 10.544091509399786, 10.399264702821078, 10.026401428687496, 10.452377556550966, 10.006789729792743, 10.0945345839533, 10.36151211169482, 10.353794257994307, 10.45334744893021, 9.529680740390722, 10.354019196476196, 9.94860097559611, 10.310273954028494, 9.878046329597002, 10.179409680484929, 10.328220964380446, 10.245516587998152, 10.127182715150932, 10.290171650260339, 9.650909584805953, 10.519328941648093, 10.530522278159198, 10.368561786594372, 10.234029117663141, 10.424072967124305, 10.304301126644635, 10.423555202338315, 10.172406986455838, 10.710591865077873, 10.585920080415242, 10.560013596037658, 10.065650736595263, 10.103489049671932, 10.081570980481494, 9.86181970726051, 9.119828152239826, 10.382771180970678, 10.228745919790095, 9.614422648282112, 10.752429192063177, 10.242644588786558, 10.495930257660442, 10.357888471813549, 6.373500591811772, 10.141507428105497, 9.712269622306797, 9.49527118644965, 10.180652850067434, 10.34546110176116, 10.495125259643505, 10.360554122519483, 10.0266330430713, 9.654217984652677, 10.23437432244121, 10.65121704111869, 9.608355813480658, 10.344198170371522, 10.201445396469966, 10.094513950094493, 10.59856063239818, 8.477752010228087, 5.013120680033387, 8.395770542423833, 10.537394804170267, 10.534821003553503, 10.120266755948526, 8.059022124115037, 9.882871182331868, 9.992491285212305, 10.369957206425234, 9.95316690925798, 9.750803071854111, 9.041874336460275, 2.40879771872127, 10.316867677871173, 10.042653191782469, 10.008205756684104, 9.987679372129804, 10.265333858346956, 10.388619963354603, 9.897315232421434, 10.346995471142192, 9.743601986433255, 10.431258078131563, 9.977775014909621, 10.436011848950951, 10.448013422643188, 10.546832766959943, 10.444269098094383, 9.613765928329501, 10.041809396499183, 10.16227317211267, 9.795082127779358, 10.210308929041188, 9.981503687894348, 10.557195414151492, 8.554368959162966, 9.896374756928367, 10.482873494822037, 4.7225503027761615, 10.201155902500558, 10.741547134391979, 9.306849632898494, 9.819508545884272, 10.362791526922623, 10.41774332348862, 10.573132434778989, 9.896908169710544, 10.312736518141449, 10.2094851177925, 10.235990879247357, 10.544718112631756, 10.032223889073778, 10.380658504417488, 10.244877428062853, 9.879946076069077, 9.533700264786779, 9.766311777422418, 10.503635261507627, 10.386533512578707, 10.13915471567907, 10.07379871545947, 10.28626214835168, 10.37885444884278, 10.16198264942474, 10.237674687187925, 10.002324192352049, 9.05516419318025, 10.492839224371194, 9.740337782858994, 10.537022116805316, 10.2386299948728, 9.956648656506387, 10.132128014002944, 6.304722034567034, 10.54580951157693, 9.867571711709095, 9.978418735654586, 10.181443309074597, 10.479048357651983, 8.378718786750776, 10.178095958953921, 8.084134159073448, 9.79789706773268, 10.01559435705028, 10.600103722060483, 10.103183980779066, 10.388915189665905, 10.489682298339192, 10.258459203618921, 10.506389219344955, 10.391627407432535, 9.52509153267545, 9.290425868011841, 10.074762586271396, 3.740193579871205, 10.522606891210323, 6.8627259978409665, 10.390857771029696, 8.441676110714727, 10.26669471249174, 8.926044196664154, 10.655183971301597, 10.419017390747381, 10.48623893674367, 10.316791058500485, 10.024559245256546, 10.252964675862229, 10.521983098734937, 10.419948117591616, 9.910091905246242, 10.118286236858973, 7.540187218430334, 10.306390566588947, 10.076647103194095, 10.38003935930225, 10.199939984939709, 10.448552162212417, 10.522718390713903, 10.191122853787125, 9.185660691603148, 10.192174523709628, 10.39286857558328, 10.009608697161795, 10.628850435037393, 9.905071748593256, 10.074857640881568, 10.293205456121365, 10.17360412028303, 10.303517500008798, 10.309842794655461, 9.94511901213223, 10.140958948570006, 10.297105047442667, 9.38422822554533, 10.436153366193054, 10.160932032521895, 9.942348439693015, 10.39540754524744, 10.183026851038461, 10.447008131860134, 10.3882679674021, 10.671487161106159, 10.120904793126499, 10.134552415198417, 10.538611211934434, 10.135779892373428, 10.332595193499372, 9.588969006565264, 9.944382737332376, 10.56370703536107, 10.154492850258945, 10.305964331159624, 10.33959452977699, 9.562178185610602, 8.223621316428007, 10.245954130499033, 10.355666200052964, 10.442202715889985, 10.457611537612651, 10.153951858849894, 10.360460598619577, 10.316838693938994, 8.042872387558171, 9.549750040107806, 9.634269959916164, 9.264595556834482, 9.519330032720037, 9.568740858218002, 10.301964144338232, 9.992995027772741, 10.458912447030954, 10.159636042494272, 10.469253290349853, 10.452139288831624, 10.190614511508743, 10.05987663742045, 10.422338505721255, 10.031468153315455, 10.473820786136331, 10.363502399558445, 9.895160505234573, 10.306045649132631, 10.53602687989392, 9.715471511578482, 10.446183706450588, 3.797436179598801, 9.913331930048798, 10.301478626805906, 10.199272413224064, 10.124163928127391, 9.011867543942504, 10.407043235524089, 10.242701204220191, 10.185272983309735, 10.06029457403765, 9.964077414491838, 10.587037665533217, 10.445893220879437, 10.14761339611324, 10.439726366132042, 9.695194924907405, 10.124058346310301, 10.499753852936882, 7.665055753050336, 8.728351065613786, 10.410842139990766, 7.5574833418784015, 10.121781679231786, 10.424673110403463, 10.129219677630353, 10.115358141141847, 9.70715284681224, 10.055398774264956, 10.139630627214448, 10.142764145289789, 10.073059163364075, 10.24790549259665, 10.39326865190801, 10.575500840171665, 7.609314783991078, 10.055884548626597, 10.177159039159704, 10.07049197634071, 9.583012633811823, 10.581037867457045, 10.442720417558217, 10.528307373714236, 10.274815186506288, 6.582341961950771, 9.697008867449986, 10.254273349355781, 9.254479657468595, 10.598600153594468, 10.311290120408636, 7.621612956449867, 9.966795550164102, 10.188565285281197, 10.227553381123174, 10.424667010129513, 10.366680670161392, 10.407323236331987, 9.885006361789763, 9.878295521824764, 10.148336971991732, 10.30891078814199, 10.54501364893883, 9.109823308169112, 9.301956089575018, 10.492235260725856, 10.251775761738765, 9.750787124112897, 10.30330081827845, 6.813947828215203, 10.072631466527927, 10.134567896103515, 10.523818185758351, 9.813122526251442, 9.964296740738547, 9.746125192648227, 9.793425688114688, 8.821597765323215, 10.088660070319136, 10.067901881349613, 10.384748614841516, 9.97232003834017, 10.026825303708188, 9.919077957256423, 10.028838686242022, 10.207248303869186, 10.332842449686115, 10.1919275953321, 10.227578752650622, 9.900148680833034, 10.42008840242581, 9.426573020095654, 10.019610608148657, 10.342688151651592, 10.50969202725116, 10.334956542749833, 7.674228890146608, 10.409377056342882, 10.664114768615821, 5.02884462409099, 10.353931747271606, 10.217532404776952, 10.372622337321895, 10.213651408111824, 10.468038760266836, 10.39422463130796, 9.672189320088473, 10.621204588094434, 10.43454764332746, 9.459892499434972, 10.175123396015833, 10.276803744129415, 10.21659605330162, 9.845455346298591, 10.308015505260036, 9.933802711209148, 10.274757377550163, 10.018386016234132, 10.218510413259414, 10.39435819262128, 9.0880069814038, 10.331093803785304, 10.21176711469358, 10.054216521150567, 10.31373641180609, 10.314657763031231, 10.42775891249547, 10.289699817156706, 10.5623856485743, 10.493831880918895, 9.724326592255403, 10.542882153218166, 9.967677511517431, 10.161314392268435, 10.573153714522462, 9.160960271769277, 10.470445738134616, 10.382885058729672, 10.022704938178693, 10.292011859244164, 7.678544367995506, 10.518684795673114, 10.470225407786456, 9.116480155296257, 10.635858230740642, 9.396664195765643, 10.571464536057366, 10.41068487804674, 10.332908485605016, 10.350435246838689, 10.326207987610374, 9.715434916578634, 10.097194478515226, 9.557739881116218, 10.415044097308101, 10.245009198810441, 7.075660885141083, 10.281602977935151, 10.035201651564835, 10.571695486849498, 10.592356381787218, 10.411930129097193, 10.083058824102967, 10.259491693273116, 9.811976279973287, 10.227546467072962, 9.280896281763608, 10.104488152850585, 10.327916285040319, 9.043051131039588, 10.387843701611601, 10.254177877026988, 8.094490074346568, 10.406922448448519, 10.41440448276868, 10.269922107101749, 9.97989255490354, 9.494704402450044, 10.385765518963417, 3.3886456423051405, 10.06943600286224, 10.104335619295727, 9.80259850608326, 10.3226256806464, 10.520768129145768, 10.221504712078033, 9.603570885660561, 10.066136379825945, 10.5588208374314, 9.491219471920836, 10.055801958245429, 4.087005294608662, 10.3403293017077, 10.131068507428186, 10.309626757547912, 10.28021130201579, 10.157471183661178, 10.360335473274025, 10.405856122590528, 11.056442931273239, 10.211711665638196, 10.359103845703924, 8.483515300675606, 10.187704607054174, 10.32603996544201, 10.25294663686263, 8.486565976894834, 10.350435215677116, 10.289706974967398, 9.714970669599898, 5.687044246533406, 10.268376955552903, 10.20581089653091, 10.069885122218722, 8.078551758068707, 10.427744243546668, 10.290593697913843, 9.782241560815924, 9.694780902516028, 7.7330794668751155, 10.038110662322822, 10.260299490266393, 10.100923105461495, 10.180202110148064, 10.519125763586294, 10.742593343254207, 8.923709332552166, 10.285340838409663, 9.836410564901701, 10.296426224112395, 10.05719083389219, 10.204674405364214, 9.228087320503638, 9.267872951235706, 8.859080035873195, 9.920586020050898, 10.89745695999369, 10.032008838856473, 10.132483586418157]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.7771955304311646, (1.6889255960662837, 1.8654654647960456)
losslist: [10.012403145559484, 10.45991098307573, 10.659489146677837, 10.359028169712756, 10.314186665937152, 10.336553269178287, 10.405868272152171, 10.686786122094151, 10.21263360094342, 9.764338402432468, 10.510218243329204, 10.033984541101368, 10.277047251703234, 10.634325791147994, 10.863091792599162, 9.581978562748613, 10.476808122962602, 8.01751382955433, 10.148951780272736, 10.659331048120048, 10.119814728058586, 9.960287117971534, 9.605043917354525, 9.7007227117096, 10.008788826312, 8.555704917038195, 8.985441348900192, 10.383647463810709, 10.327037376980616, 10.4233212186031, 10.451681765098433, 9.830606723244285, 8.038542783312971, 10.358644516639938, 10.66971939652798, 10.318566323697125, 10.499011995289203, 10.634543938665665, 10.40536874088923, 10.971890202934084, 10.387773720621116, 9.679031896086382, 10.610462670722908, 10.481068737431816, 10.295119392983032, 10.461425414689044, 10.57558492437605, 10.248805903481298, 10.1603746062391, 10.573067219929108, 10.678811607868466, 8.187529175715133, 10.418059450715312, 10.341031712387277, 10.198875739735527, 8.137002007212278, 10.524606990570854, 10.36139032485599, 10.324477821188518, 10.486835286049237, 10.273349203408868, 10.668883883169705, 8.173947722551718, 10.418099063106013, 10.190500952471737, 10.394489813463027, 8.623481314210222, 10.438269280384505, 10.195844902158827, 10.395907641208279, 10.561637661537146, 10.135368550599653, 8.787634839573409, 10.144105123415386, 10.445862425006267, 10.229562348974373, 10.268163587258453, 10.433697496101475, 10.7644182779098, 8.257376319756958, 10.147320364983909, 10.562839581773593, 10.634751296811746, 10.30847478531123, 10.322232405286556, 10.374682828969968, 10.331893191577187, 10.113014322792884, 10.274133124008157, 10.155742627318945, 9.433399826535814, 8.38947587272067, 10.187911407813111, 7.756788807552921, 10.550273993820106, 10.38715548944927, 10.311820697862503, 9.981639171055049, 10.47165401194492, 10.590205262598412, 10.148621596789447, 10.603234748751893, 10.566501923426948, 10.185538192228222, 10.588787210778284, 10.451204183322407, 10.500942908800894, 10.558043695658359, 10.589258969035457, 2.1980929384142778, 10.427474928891234, 10.833952733242889, 10.579187313012515, 10.113366703392863, 10.265204955211452, 10.378627776180972, 10.387519371800222, 9.968628362352442, 10.678971773308149, 10.03925633546682, 10.25623381252076, 10.308700731143132, 9.362085029813434, 10.615391539945687, 10.285598482790917, 9.99750510588736, 10.42793631060034, 10.240667360566718, 9.392444536872524, 10.185479151158576, 10.433121074907888, 10.236035776636422, 10.44947095046451, 9.777696949958388, 9.807635385999392, 10.401808621262287, 10.275953808208659, 10.134876273432958, 10.298472646710039, 10.367555419224246, 10.591218588261805, 10.06997702898658, 9.236357375783895, 10.092314282561867, 9.596458627394206, 9.865212842102736, 9.76789310721893, 10.2899458249054, 10.442744839087183, 7.349580413641787, 10.12676218616232, 10.318035303336382, 10.226067811611417, 9.803748984328777, 10.44006725092834, 10.361258010481029, 10.33074575759545, 9.830659825241352, 10.254962596431348, 10.090126063806398, 10.540225787377167, 10.109271273953622, 8.574383848793294, 9.70419460407954, 9.69830660252442, 1.9124255639501084, 10.143594333821662, 9.337158943470001, 10.539984023915842, 10.127892570491023, 10.705180104679991, 10.900350658744768, 10.267445005135697, 10.303982507787124, 9.946460457250069, 9.113097027384315, 10.500085846143863, 10.389897982560838, 8.357469151637153, 10.455156572849683, 10.257277919366228, 10.327702430857405, 10.538813632566907, 10.179165125106877, 9.698992556983743, 10.251633431621682, 10.327122582211004, 10.31917863484255, 10.577835426787834, 9.591666951538802, 10.606420996346197, 10.532092073814342, 10.20047561398386, 9.598914102650122, 10.872704316363594, 10.392816805464266, 10.687704737007913, 10.779848067914608, 10.713263155108558, 9.980981450058893, 10.584967497085996, 10.28204054448733, 10.532865892629781, 10.20069313365198, 10.48714844657047, 10.256786464078727, 10.508231807314502, 8.986618760930128, 10.65495731370493, 10.25986464986767, 10.61754508070626, 10.432953846026647, 10.557328017333893, 10.347925600612568, 10.299548954294435, 10.113404329094863, 9.993456839245832, 10.262726904343529, 10.530120517431861, 10.505215087585096, 10.427873332252148, 10.257464081621144, 10.405789301043013, 9.914917167214814, 10.392574469323046, 9.029644221192457, 10.178935119285859, 10.521526236209247, 10.674246154989948, 10.461773400212964, 10.244183451762316, 10.188197714855441, 9.735684555544458, 9.832211975033438, 10.538293360894203, 9.993263653414571, 10.326594471238145, 10.341203645925889, 9.953832272149677, 10.19797942722316, 10.278721523446695, 10.247669448308345, 10.59750305839503, 10.329654706861888, 9.620355847849765, 10.584446263937005, 9.954276547308593, 10.003833137682417, 10.367180065819305, 10.457406429206634, 10.19531313970686, 10.420906789723265, 10.68963606288253, 2.7286015011194964, 10.467340938710537, 10.233100074779758, 9.115914312755923, 10.173421615359183, 10.208039032741747, 10.318424610616614, 10.488087075246545, 8.086363720661957, 10.241824669439893, 10.25852377171065, 10.328030231315353, 10.62712765326427, 10.504538166242062, 10.530053161059628, 10.077803369702368, 10.102805217215066, 10.096036006210058, 9.580975505716042, 10.439151217433226, 10.504969568871116, 10.36097819333231, 10.62673911337138, 10.270133253772723, 10.509827219416454, 10.108826419227915, 10.40612175265411, 10.545275157018644, 10.24265718823909, 10.437734433434153, 10.565927267928231, 9.53153091856649, 10.017401077201365, 9.726910165511061, 10.7994634796509, 10.10986069390048, 10.450449187449886, 9.619115232968621, 10.460468843458948, 8.318012066569418, 10.258723105280632, 10.489544691823227, 10.398547335159599, 10.447709356456237, 10.490903383972414, 10.518706869757501, 10.585298529589682, 10.127460722183308, 10.343118246914166, 10.431934451547853, 8.759194578673902, 10.476687992386953, 10.46437291256367, 9.885591710725294, 10.610381139813224, 9.800978569019955, 10.477760966177911, 10.463287601363, 10.668461845345083, 10.255561145221836, 10.357908584281551, 10.301623644049476, 10.361960370231463, 9.274578299956005, 10.480987432838782, 10.269161703760759, 10.188969165194333, 10.568145011539983, 9.662929528568329, 10.490872204710735, 10.545238792244545, 10.111143765593573, 10.404871721646908, 10.075939243105003, 10.464649511460575, 9.683503733583628, 10.518456551347033, 10.492718987432815, 10.623484314166957, 4.559198986624808, 10.612414271136412, 9.946746988318491, 10.768722882466243, 10.541393548310854, 10.236439936637941, 10.335953206432984, 10.635968476784448, 10.010805988747963, 10.462632055113875, 10.592311547945268, 1.8676965737169846, 10.186691913959876, 10.257855168473501, 10.177645329590279, 7.588368577210622, 10.562589810605427, 10.106392313134481, 10.334672955855158, 10.71225024201341, 9.999492637729503, 9.61247975719195, 10.012009455571764, 10.824365816043613, 5.441698790182548, 10.33748324061628, 10.546764895645566, 10.313604404499094, 0.04854043549275859, 10.629109816366295, 10.452441027227305, 10.469693715287914, 10.41125074853501, 10.220110561441738, 9.467668393472874, 9.999669006214726, 10.54613964327218, 10.28421383854455, 10.185285284317894, 10.608138923630454, 9.596350113824117, 10.321137527298008, 9.325937984114177, 10.433798476408333, 8.985048242275264, 10.131581220650459, 10.127563440834784, 9.217794650581231, 10.495716706538177, 10.025338912845402, 10.440654101522307, 9.968210508456904, 9.883713100774386, 10.411504693749567, 10.477186334462441, 9.330503008793851, 10.323904674861192, 10.33483778364613, 10.610745506735693, 10.22210197809297, 9.688393125586199, 9.543992728202324, 9.658760214743605, 9.118018693342055, 9.994869708301009, 10.126078740258512, 9.94369052823409, 10.690096976184037, 1.8220884344038029, 9.674627019977482, 10.082675867214911, 10.437172792495154, 9.989752095829871, 10.123312479862433, 10.560477828958641, 10.494876003616433, 10.357442428484122, 10.329880200148544, 9.619305126314442, 10.244907756606505, 10.273908273774564, 9.730784297597753, 10.438932882872002, 10.444506473961136, 10.548400728886861, 10.365443837420477, 10.811384502149814, 9.387957698513683, 10.354378198537791, 10.183176965131358, 10.39424972847232, 10.595918081601766, 10.435913203796847, 10.44471928627362, 10.341779289059568, 10.098368418214516, 10.35210369942846, 10.298992664961144, 10.407767891575608, 10.475995089261287, 9.651715766866412, 10.20270186025926, 10.624809138190063, 10.501506223158167, 10.279668935037808, 10.26210209680262, 10.543608920151765, 10.415577312051928, 10.604096118484016, 10.900516591492298, 10.185325335963935, 10.449184542945407, 9.896683130326323, 10.385662624157113, 10.270536337459122, 6.5855339113288744, 10.625699302732091, 10.340714912616997, 10.145184786258813, 10.854029290918184, 10.0598073679788, 8.55043586787621, 10.388975755848707, 10.45504127414195, 10.158775986294255, 9.430801182896074, 10.218843833872743, 10.898443305335014, 10.355075776048498, 10.544892601963271, 10.23303806094358, 10.209162300065495, 10.497989161783307, 10.409034988426257, 10.137727675894306, 10.191988768007624, 9.92043525614569, 10.499146787034663, 9.886987028895346, 10.293336350383415, 10.53905109150039, 10.001268955272137, 10.347745607108733, 10.430114755563094, 10.290576219685544, 10.420785750810754, 9.874618170283288, 10.451859461037172, 3.6198527493444335, 10.010180074397846, 10.252480447928797, 10.336863806220043, 8.352339377067024, 10.10210490895681, 9.653030299486714, 10.2978199116848, 9.946847178115078, 10.423337796957574, 10.21149177209323, 10.45373733038357, 10.112472074881682, 10.163969608002967, 10.429970410635061, 10.192377575135309, 9.575968429449857, 10.393098472600322, 9.125091622995633, 9.63694470056597, 10.627752144624885, 10.34795674673406, 10.458119272421182, 10.370542196456306, 10.125542377793307, 10.308651559217854, 10.346315746198663, 10.468523523652996, 9.887481274491313, 8.028784368323484, 10.176293882622254, 10.198349931366357, 10.463710106260256, 9.464431055619182, 10.558181518147398, 10.612790467469072, 10.650862629660448, 10.350795874096004, 8.810113421293764, 10.31724439054522, 7.4941613141160195, 10.334525089332848, 7.8304927567149125, 10.253417248823446, 8.054442581933, 8.95894725037334, 10.327848875678107, 10.322022429770774, 10.370365169191608, 10.232047807573892, 10.177826121680168, 10.376377501165326, 10.297647153413534, 9.677222248558367, 10.36181947551608, 10.385030643633073, 10.750413996197045, 10.210086132568584, 10.681332188660862, 10.35835223606307, 9.825874751826946, 10.383561489664205, 10.593352198550338, 10.603535170430128, 10.506601424288647, 10.652090031935993, 10.462747856590749, 10.566227560617934, 10.402593174887398, 9.519664372755734, 10.099453302803834, 8.062359611975074, 10.618477243090535, 10.361526989703103, 10.025275719724934, 10.117959931473994, 10.444025438150044, 10.251867892163933, 9.928281453408445, 10.434988109975793, 10.393546991252789, 8.847481081383767, 10.227704915241757, 10.225136750553578, 10.43220407326546, 10.338957991472645, 10.596243788654903, 9.306521636275889, 10.299207158880362, 9.903357659743389, 5.638163388792365, 9.604626596064838, 10.259392162198543, 10.356488863026597, 10.477202585356206, 10.351633222886253, 10.219430925186845, 9.937374858102244, 10.562100749816596, 10.223268480398414, 10.125209634871975, 9.885239510929251, 10.382871283961077, 10.220208016560814, 9.942307999320661, 10.045034489706813, 10.463250098492605, 10.12853230690601, 10.634042969861845, 10.504305681511772, 9.825122474056155, 9.311383999142624, 10.285216526815946, 10.27999965073956, 9.996228158630968, 10.436497392311116, 10.495249022786307, 10.816801126847185, 10.287515147389856, 10.60682320290763]

path 8
init_u, CI: 1.5151175398479975, (1.4395405105724137, 1.5906945691235812)
losslist: [10.790169962729145, 10.712476016140224, 10.65094541808223, 10.540779240589499, 10.615085675211553, 10.027697219405772, 10.797314718255375, 8.801710627088928, 10.506733991995858, 10.610541955095446, 10.501221213920577, 10.959545134174007, 10.673494044603718, 9.725926771370647, 10.42177153861438, 10.743378338216814, 10.299150754133063, 10.605301283332334, 10.05686475595647, 10.68486238620716, 10.560608734110724, 8.672119614705991, 10.601096837669207, 9.877196899995408, 10.419867726172827, 9.638089624001582, 10.601863766429268, 10.524957700556191, 10.635554327106002, 10.947906626676424, 10.384204475120498, 10.308372295320636, 10.610467674898096, 10.652597859099119, 10.42928299393895, 10.15761714155781, 10.360637421545594, 10.422186892974416, 10.832982967808144, 10.650879344230901, 11.000428148076956, 10.055022422361189, 9.966356767192252, 10.537170092105, 10.231887842852172, 10.589614089851256, 10.328198087495416, 6.275022526912319, 10.371926361228619, 10.534957980826336, 10.773153631600563, 10.16967854281677, 10.402346222630172, 10.404556388639747, 9.504172614675758, 10.509259149068662, 10.5620001109527, 10.461587017746757, 10.426315983003843, 10.494810332499402, 10.56712887954085, 10.152382000994942, 10.222344740933758, 10.482368022201308, 10.37062821232001, 10.505053827881587, 10.401767787581418, 10.580474744717902, 10.694129335085002, 10.131311812785558, 10.500972619380196, 10.67382160741252, 10.55865239815892, 10.648981755534995, 10.362967274883687, 8.688294984232927, 10.287002491674265, 10.32125786517248, 10.54901374231675, 10.584987786282392, 10.736996489580816, 10.518679100767873, 10.4913646899643, 10.651106990043445, 10.6215972988443, 10.76445158901315, 10.825705482349662, 10.144303644099946, 10.378836596533633, 10.523232129257659, 10.729139023779608, 10.060122340544812, 10.038651260655302, 10.56435445405988, 10.393501831411937, 10.63266994930452, 10.208619120096284, 9.680522960218182, 10.353048945758234, 10.402944111326562, 10.41567833553072, 10.638021660845448, 10.633891355544947, 10.327080402305254, 7.882842379321104, 10.811609886327231, 3.1372719673093377, 10.81878682232225, 10.5458126287384, 10.635280480514693, 10.2968074513354, 10.255557675512916, 8.402245567695697, 10.485932619832997, 10.454462822830884, 10.232738661286204, 10.241067881866151, 10.462502189562784, 10.753840251744064, 10.6544438286448, 10.575187615121738, 10.648414884148158, 10.695796409431104, 10.598146016918385, 10.427815275847449, 10.348804173528007, 3.483164861129282, 9.951406346028413, 9.90253273327368, 10.344646474443035, 10.360394972655563, 10.53265934624651, 10.50471385339902, 10.382527494143945, 10.350271014039409, 10.308511693670807, 10.468257615827044, 10.402795966421463, 10.198275236475595, 10.683851632706261, 10.036423995830926, 10.336784053661232, 10.49814879907274, 10.672450027077916, 10.566063968355872, 10.741120208941755, 10.059571127439055, 10.962229501501888, 10.60070378488518, 10.704153305419197, 10.630424165806373, 10.47400140337144, 10.584617117151941, 10.623831979725537, 10.438927223303846, 10.223656566943992, 10.89773834930785, 10.623844626682, 10.352257074363216, 10.49251687527586, 9.248733635922232, 10.578503930547457, 10.613135955648003, 10.648640074239278, 10.69352818823969, 9.604229563972769, 10.31418104506417, 10.143978924468326, 10.628617736316532, 10.000697904008891, 10.626743375396757, 10.20052515626143, 10.563947237817118, 10.692070963160756, 10.472600578984407, 10.36352038343233, 10.515398660117345, 10.350927489961508, 8.728887350962118, 10.933621712935576, 10.506237706418702, 10.392851581575965, 10.655279141603174, 10.2276431432296, 10.81305245701203, 10.15509122404132, 9.832866308679742, 10.733010547066963, 10.137558876111655, 10.15089820070317, 10.72787302720425, 10.376855678472817, 10.43068126847884, 10.508839079979456, 9.752996382120733, 10.523166409170141, 8.178274011327801, 10.3700418702963, 10.590974335838759, 8.99177890242864, 10.495099447977399, 9.28179541018015, 10.386920623429102, 10.561736099832638, 4.68821995627305, 10.605486088160292, 10.662524816769043, 10.55842487464712, 10.499169534134511, 10.499297873841863, 10.38415734931878, 10.649118985104552, 10.519508873158175, 10.749544650499063, 10.42080468185761, 10.010773259645633, 10.659635189853482, 10.75734587580831, 10.645821277496749, 10.42832645009825, 10.540344195115356, 10.423369969873145, 10.541435665891406, 10.690642242557617, 10.420352755135283, 10.350644538496532, 10.371118461879256, 10.80029264461283, 10.320658986970024, 10.42415545144806, 10.856472616636164, 10.62978000150137, 10.641655886025418, 10.76818763126395, 10.779792460496347, 10.476018964744597, 10.722685643979762, 10.21922759923335, 10.433127211620821, 10.488988821398767, 10.725511843425648, 10.398749095875175, 10.379039535253483, 9.951556170613724, 10.574903194444286, 10.364923059660883, 10.513697988327138, 10.810530003041452, 10.50934429490491, 10.481515465645872, 8.956063874065537, 10.889249730429272, 10.542975603671923, 7.033991312250053, 10.745703156588686, 10.57252531941136, 10.491576833681984, 10.532298118279318, 10.290143820381044, 10.464540394142766, 6.835799683494358, 10.479277759493092, 10.378834778554582, 10.350460171504501, 10.442887866621788, 10.592926658383407, 11.07674822158506, 10.251193265346261, 10.653767057588585, 10.61353230118959, 10.754669688815945, 10.352776502896978, 10.36871639238664, 10.678866403606746, 10.493982347546154, 10.641526673849532, 10.400969956475086, 10.698823964823172, 10.587567105019723, 10.36987774085108, 10.498214571301958, 9.997115902738903, 10.59927338771494, 7.364253960546847, 10.454908450183868, 10.53316383012259, 10.530198364396442, 10.55571462232709, 10.414999435842004, 10.431866333504953, 10.484350806002302, 10.571675060822038, 10.586453889986037, 9.850641024493752, 10.290712518062227, 10.607608896289273, 10.601783415844578, 10.349964630909184, 10.47454104317523, 10.568587715535127, 10.445383454400801, 10.405159116985658, 10.569880362191569, 10.523926136049592, 10.6142459422299, 9.561055078800251, 10.861854672289656, 10.49551012453946, 10.257902358835375, 10.560176648217663, 10.502312983769842, 10.582511936120671, 10.277798331674655, 10.74579651325545, 10.148262148072046, 9.536181276912567, 10.084869023845483, 10.700218235565172, 10.680771539750353, 10.883988811055183, 10.647448084548055, 10.401505737694674, 10.828945693630565, 10.432910268480416, 10.813654721548493, 10.507247310079183, 9.82305043502167, 10.179265030652708, 10.511312350386433, 10.599259151068468, 10.271142855235125, 10.057904991436027, 10.652472920740703, 10.481678096180653, 10.652577281795596, 10.60027673912328, 5.741637898832433, 10.687470863721913, 10.408069805798531, 9.813636647359505, 10.61301476707658, 10.05747352635101, 9.477546386804692, 10.088624220330745, 10.194515999888955, 10.418715146134147, 10.389511219555672, 10.535334618262015, 10.323764550019266, 10.604257074311912, 11.049201900307228, 10.16412226404516, 10.2359442990078, 10.704619226143066, 8.857111466817338, 9.415425304280497, 10.750991612780314, 9.056680638599868, 10.373759374499496, 10.22546036301632, 10.697413517212293, 10.588824639986571, 10.409119019922816, 10.180513116065843, 10.405515481161569, 10.832166584481099, 10.09824460252465, 8.714183031757814, 10.550765257112939, 9.766776788282254, 10.546067262885764, 10.970187926665622, 10.333745081300128, 7.749883493166923, 10.580141022096154, 10.599383792996761, 10.741710995751575, 9.56490788054788, 10.332129106575707, 10.644366854513482, 10.943567973406948, 10.431971105371685, 10.391443737912951, 10.393307865477988, 10.48391928435154, 10.498120312405762, 10.215252925736307, 10.503133137810037, 10.578836776773429, 10.543129247655356, 10.609255928454456, 10.477019726113825, 10.369234006831231, 10.710300722874539, 7.394874963221651, 7.649189433935595, 10.530399676824558, 10.280214380659693, 10.472028704036148, 10.338532186587745, 10.47626579843191, 10.100841363565287, 10.422425600608697, 10.42954710217986, 10.349383541334479, 8.999305659837948, 10.45370319268559, 10.896691758495471, 10.285888256996468, 10.753715913020203, 10.227147086835442, 10.418214279026873, 10.241193812646761, 10.539113756041404, 10.491906326144264, 10.556371911614209, 9.758709181113863, 9.289602841331828, 10.663186870649126, 10.262600222873578, 10.714694631755124, 10.61797126170961, 10.643981748811523, 10.58295304252021, 10.471644946357966, 10.556033939052703, 10.36970835529155, 10.644775022370414, 10.430865452322504, 10.68806719102858, 10.468373642693331, 10.332621197668825, 10.48738696118895, 10.522394810775005, 10.52200849536778, 10.149666662382451, 10.834219732325451, 10.606817945825792, 10.60457047374265, 10.664579925433761, 10.536339848757057, 10.35297979031538, 10.470249158679021, 10.776844745156135, 10.656611338444113, 10.90672128209975, 10.76102630150476, 10.634581849168697, 10.66244882200387, 10.266694754461602]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.358353115111278, (1.2938629084789692, 1.4228433217435867)
losslist: [11.089973299874616, 10.70913795803797, 10.844150818959044, 10.872379456150648, 9.753029405516193, 9.599055069474606, 10.7304420441629, 10.629398948084695, 10.579159621111936, 10.718517455404562, 10.604058638251155, 10.347032251892507, 10.875469816367161, 10.605926437384394, 10.214339966611462, 10.955220176984747, 10.500495938181082, 10.626598759124754, 10.548567946486333, 10.77750914438249, 10.40080323927917, 10.714812238328177, 10.706900039730453, 10.80802198336079, 10.763577505980644, 10.781547909611428, 10.111849638709325, 10.64544800690675, 11.10854653506328, 10.706770665040995, 10.54304022968402, 10.107956527093798, 9.490461323646567, 5.945630438610371, 10.634498102312934, 10.761007196286284, 10.578013813726217, 10.471565301512387, 10.63075748462357, 10.711885924179171, 10.578777624016071, 10.748137858165704, 10.752564400827145, 10.847349562695566, 10.700352403387233, 10.809590235716996, 10.513699054316639, 10.892497855604592, 10.651608851773686, 10.997110716162537, 10.629497309588473, 10.78742614585288, 10.541597993140591, 10.572707746958026, 10.480314412646578, 10.624076967324271, 10.450587750171177, 10.533924357504716, 10.558800759928166, 10.420496471945803, 10.762913314929827, 9.321682447973169, 10.71795213668354, 10.671859214664337, 10.895234695908766, 10.451741633992926, 10.735475922315354, 10.838911692418371, 10.579153402353375, 10.666206120494149, 10.859853045663936, 10.468157301625583, 10.428572624342594, 10.502887699864809, 10.677938252855341, 10.782738206239355, 10.449986228114396, 10.807770737686862, 10.147121320477105, 10.241304878698019, 9.672865994077736, 10.68251148001357, 10.417205383082397, 10.665659084199769, 10.53800492794018, 10.57298092752175, 10.491135715279428, 10.652615003838251, 10.926241938120445, 10.895943052069532, 10.785850860143846, 9.697686528638648, 10.448072849045928, 10.536911449006938, 10.480996997908438, 10.379272970509602, 10.746144262110668, 10.649993497788724, 10.69271189838749, 10.879798699114751, 10.727709058316856, 10.750379729925292, 10.715780080191479, 10.31708115333435, 10.58386397478625, 10.872259508148183, 8.092881284302223, 10.671577416341362, 10.674388471173216, 10.912031543978664, 10.751044801831698, 10.696525663918145, 10.693574141582273, 10.928457522369134, 10.76305369173741, 2.426670208022613, 10.443306151019948, 10.577335160584434, 10.833674682144302, 10.567467857184448, 10.723843000954172, 10.81596588117558, 10.357830474243878, 10.465993724278393, 7.76246301549531, 10.805797682458726, 10.69193231585596, 10.43927840892199, 10.25511870879157, 10.55490979572974, 10.326250424930878, 10.634447895676042, 10.608837534352249, 10.897052018475875, 10.56059744195315, 10.657643438182223, 10.472495064953321, 10.558866368804544, 10.520979241605714, 10.461213650758763, 10.46604291480743, 10.749086095131695, 10.599233015341737, 10.54145363453334, 10.615312490627657, 10.640216195979058, 10.665389229501255, 10.605270134082502, 9.698237964863985, 10.637173430370758, 10.784109168079764, 10.6223809950566, 10.918577733271807, 10.641846500119232, 10.333562700069036, 8.938969385921936, 10.590790604409834, 10.448092998088038, 10.591752492356258, 10.644098454872413, 10.641108280375583, 10.703341571796415, 10.27164477089628, 10.77140481518725, 10.922284253102426, 9.856063979733975, 10.384787327326126, 10.51457532907377, 10.88631385035642, 10.671449531829895, 10.308014907293709, 9.912797613910742, 10.564673798477239, 10.350102985394638, 10.705729491293955, 10.759733191979512, 10.765351038621937, 9.954322921084923, 9.49634633481474, 10.986190225386194, 10.531616991394701, 10.696087174455666, 10.895914957826738, 10.55061355340936, 10.580467973114075, 10.349482985199787, 10.359198508983365, 10.647122895623447, 10.752864020702395, 10.562310839910564, 10.818960249710223, 10.603625919549367, 10.57947609781782, 10.694668249903472, 10.830457424051927, 10.485389875761111, 10.73224479950032, 10.900208330727686, 10.607277506887606, 10.897119936298276, 10.854326727628402, 10.402948722701437, 10.68053267481319, 9.798653308210428, 10.246982283853194, 10.74370027039858, 10.774166904958271, 8.859642872124349, 10.783942163594197, 10.80525754001463, 9.364987972437413, 10.214280197765945, 10.616956858044166, 10.475001840484843, 10.64247326557751, 10.95435630543094, 10.11672863853787, 10.970041236968186, 10.177790863511287, 10.561893692655604, 10.450482318609536, 10.810530881777332, 10.984354930723205, 9.158651164051701, 10.76788531538606, 10.755927329495984, 10.628818056788274, 10.481675752249261, 10.411709058488775, 10.440608920638866, 10.600652011612022, 10.597334577454927, 10.308778544412462, 10.759921854158852, 10.94331701941601, 10.534972759796846, 10.428210636787034, 6.940254793508232, 8.23812669525966, 10.569561699398676, 10.633316156895912, 10.031866713837466, 10.457887331916652, 10.153447304406845, 10.383261324083813, 10.407996794173219, 10.48689538831882, 10.681459575144597, 10.659440988553008, 10.594574590388424, 9.516463448696847, 10.63185242053264, 10.683650447874463, 10.876390748890616, 10.415736309057651, 8.737351413149568, 10.595523644936394, 9.686637665514022, 10.936147356785405, 10.581401561755438, 1.1572396137143182, 10.646151141929133, 10.601932628598552, 10.87548349820787, 10.556596714704641, 10.765898609668035, 10.445179964295958, 10.197235885372283, 10.45329088031844, 10.902659048533069, 10.471223332391755, 10.510274082971707, 10.80714398102503, 10.777985123733831, 10.315184188710665, 10.37838285875264, 10.7328398142775, 10.75319371496391, 10.444572364536455, 10.576018356942129, 11.006410225403553, 10.644890454103638, 11.051180602746772, 10.847978518210967, 10.690131723736433, 10.376711123036142, 10.496927547131508, 10.54483218670281, 10.947979598172322, 6.388836771742809, 10.654789660871447, 10.770696084134292, 10.886494915602864, 10.787777972497805, 10.745473569456719, 10.401804507598744, 10.622465216082455, 10.811102237992797, 10.69769991704175, 10.933259770620626, 10.515580380410498, 10.808584801233295, 9.7877081938699, 10.874360914417162, 10.574829010586416, 10.718038252648816, 10.760659224916386, 9.612183465146886, 10.575843247111552, 10.733371747496367, 10.538630599571302, 10.783785555949596, 10.280325610935565, 10.710226857516737, 10.800137820602771, 9.820778846971564, 10.56230046045821, 10.636413697114017, 10.85482370500548, 10.471547047671057, 10.66739494490552, 9.393346551028456, 10.901503128799305, 10.770128563956623, 10.729781797954844, 8.910766997125782, 10.560899469997201, 10.322808373177203, 9.950950395106448, 9.35612776033847, 10.985063755267603, 10.29490263611986, 10.500330859072282, 11.008046654187416, 10.191498074091065, 10.78361956755766, 8.515111469824785, 10.338321460537996, 10.58154554082909, 9.454999914156408, 10.624919757917992, 9.118516242321137, 10.929443532190186, 10.358275443404594, 10.806048387577789, 9.737983872434171, 10.606452554629348, 10.244890255393413, 10.657082074332948, 10.800692556462744, 10.693729331177611, 10.47513943349221, 10.555303397040914, 10.631829307931556, 8.827981647554157, 10.354365725450462, 10.59624566418664, 10.609508937297736, 10.64962934873576, 10.362171720841257, 10.817041219102181, 10.787866628002273, 10.850525472146028, 10.62335061108897, 10.14005157251686, 10.762206615285496, 10.487878259292673, 10.347157743193975, 10.85409024088884, 10.579334737343553, 10.227995131064, 10.174139370484655, 10.711131016629103, 10.666144791568836, 10.861331454574831, 10.671255384546289, 10.645066465441614, 10.61511742427238, 7.964674673977517, 10.894344029819916, 10.757151913682566, 10.426682931193033, 10.423673749307547, 10.758429494048324, 10.640707889695998, 10.688107748834902, 10.753191941200013, 10.476337513486223, 10.63881677761302, 10.53612929332123, 10.381964898519188, 10.108752167512236, 10.79732279724829, 10.771611355457749, 10.634041529799275, 10.698359063342298, 10.538517268479634, 10.237643977311077, 10.856988253313114, 10.578543514704656, 10.779001823798051, 10.768613564231215, 10.817023632737817, 10.24003712081901, 10.914334833255822, 10.713606284152316, 10.986244563581687, 10.770242760298084, 10.64234921183129, 9.49155151851335, 10.533841946987476, 10.77181643614099, 10.925077476243473, 10.445875268434802, 10.227936841654483, 10.755398553877066, 10.920928856603528, 11.121014322660146, 10.363327840125928, 10.828557107529445, 10.744935256602654, 4.611343760567953, 10.658701396872697, 10.664412261554398, 10.632910033323164, 11.011545717965799, 10.751412033894878, 10.620149025179684, 10.838515591016135, 10.701511653948655, 10.086019739215493, 10.719077726007816, 10.891853421924901, 10.689335980644826, 10.865859350268819, 10.694408194126295, 10.508910345373392, 10.155175739129819, 10.572121452641992, 10.49154483026017, 10.798216653779784, 10.644703481758702, 9.462143967360802, 9.499702059880304, 10.461333069018945, 10.833353303208801, 10.262867738261276, 10.884459189773644, 10.96158982258547, 10.237272480993811, 10.353662019547444, 10.904681433705267, 10.38174902576079, 10.556035427030032, 10.731625469510067, 10.545802489037039, 10.769118879197306, 10.656288379395159, 10.70687414135799, 10.510705710059263, 10.88399034292097, 10.757406975441565, 10.626548141892657, 10.371835358465383, 10.574445311525784, 10.430583934736513, 10.679346539173435, 10.706893195140019, 9.808075876692985, 10.911236119888619, 10.530029947481921, 10.79383989521665, 10.556317827637448, 10.329696277633168, 10.84788537994431, 6.658557444497, 10.64535528663916, 10.727713756232363, 10.703746623373604, 10.351406378795156, 10.773736714701046, 10.827672366622739, 9.835513535243695, 10.432954934000565, 10.698315065166357, 10.382797970207498, 10.69213469127218, 10.63847330226713, 10.693317444473351, 10.454454033510755, 10.69636791403598, 10.331605979470643, 10.704694403332896, 10.704407298830997, 10.754364287743602, 10.304374947756909, 10.285794617961816, 9.638742056390223, 10.994032551304294, 11.075123493357427, 10.786228057108483, 10.432844024198104, 10.788638268759987, 10.771873550342312, 10.739096681119387, 10.80082167592948, 10.620363660754139, 10.736189992151573, 10.740400428156795, 10.939593131503141, 10.197079357351953, 10.728310034416486, 10.789203215292783, 10.79751046310665, 10.919280579332698, 10.895814968304313, 10.605476510502797, 10.06998025158834, 10.628724999916754, 10.222891087535029, 10.60786660824108, 10.600329902614895, 10.752830416045347, 10.772024585731211, 10.592832685460783, 10.513658500515541, 10.70001800758341, 10.63154092518445, 10.854774523941968, 10.591603798605624, 10.495261061254102, 10.578433883281903, 10.721899214819388, 10.450969506841506, 5.3264918518664235, 10.464569428910297, 10.880541237374327, 10.329469312293703, 10.924261195197852, 10.546620815434844, 10.38606767360041, 10.313217965889658, 10.056054953239782, 10.52962913415333, 10.72152042864557, 8.377654603691807, 10.310425464724112, 10.04521290668052, 10.892357338794955, 10.329780927302183, 10.568037917742302, 10.470568928451048, 10.675392471818217, 10.675124757837752, 10.807105020809994, 10.943780309542392, 10.789171523265278, 10.800574251203562, 10.434714779943546, 10.246203755518906, 10.423171305296307, 9.80345905408999, 10.404111291522225, 10.520170780276853, 10.539911268297672, 10.414367125120567, 10.642554667629774, 10.795564564990968, 10.685303222059082, 10.727506694396508, 10.921583777609658, 10.727860984699301, 10.70785520873646, 10.582767718389078, 10.877094284855024, 10.664826633553679, 9.200231074226002, 10.800400448094333, 10.708743717444683, 10.343598469487382, 10.6354330897163, 10.775788470781526, 10.484565922384613, 10.803927835966293, 10.676467016087058, 10.860983308653644, 10.691792298169908, 10.450755135995228, 10.855755841282402, 10.923338257264685, 10.745314196560411, 10.832390022852799, 10.279322837046715, 10.042634775482394, 8.9986065784842, 10.722060718183307, 10.606912514179127, 10.909959555265674, 10.593042646005346, 10.936412916398801]

path 9
init_u, CI: 1.4247158818142633, (1.3549259032100203, 1.4945058604185064)
losslist: [10.211682112859112, 10.744600047269067, 10.522588055268145, 10.324751943379352, 10.270724101244014, 10.256826913924598, 10.61938967717843, 10.60897328967027, 10.285332383378824, 10.673035116528698, 10.53041330786351, 10.577624044420006, 9.526747226050832, 10.463893652109409, 10.303504301862652, 10.332821018899882, 10.443662740105285, 10.381575560934584, 10.555307376817778, 10.630008838919283, 10.605742990521838, 10.516982560592057, 10.679545223555307, 10.39181962442648, 10.608836296266826, 10.652335242233494, 10.387605933801868, 10.66598424338534, 10.788109635561177, 10.755694550581465, 10.710331430194763, 10.668752749677035, 10.270666860071358, 10.79556219580678, 10.99816155826184, 10.148276285762474, 10.793272519450623, 10.382135259079055, 9.36573830783964, 10.553546233279251, 10.894513384869233, 10.488842936877953, 10.572002966594054, 10.227422595900515, 10.296847604137767, 9.84761339041668, 10.63039609121954, 10.157194564065335, 10.537089868633585, 10.834352327846183, 10.247905634020622, 10.593104658836033, 10.25121854429012, 10.696535183291902, 10.725971627720167, 10.16663383490739, 10.292905133738786, 10.464551359205057, 10.151579626740693, 7.727975268233716, 10.320578643327833, 10.094808140639316, 10.64836628842869, 10.520571088809794, 10.614160994338265, 10.424004156506204, 10.273489185426238, 10.752506573744986, 10.722585915493385, 10.575686314892023, 10.27130040145813, 10.509716471702696, 10.676985047442829, 10.397914448671264, 10.696960339170538, 10.580026512336925, 10.470832374689758, 10.624712894824102, 10.647583070925617, 10.288860896095889, 9.40506198352197, 10.660515821879898, 10.388696560488897, 10.958150706032358, 10.539785732362008, 10.642742839686864, 10.49351171799928, 10.711537294437578, 10.6567511020693, 10.559829383611865, 10.1047083612651, 8.170388908554333, 10.729838016046882, 10.462087119743062, 10.75197149525504, 10.105550345331421, 10.376972396381488, 10.831806435913197, 10.418869320174336, 10.75927928461066, 10.424960169730626, 10.422263417166462, 9.990128617477094, 10.412258874693114, 10.49508419816562, 10.54018620163422, 10.378574169398627, 10.540435033289985, 10.552073435541763, 10.501468720201792, 10.842314651208799, 10.390739319892893, 10.332641553430857, 10.562871061501708, 10.137772396050647, 10.593078903700047, 7.740197550572851, 10.560904113230213, 10.480756967076235, 10.707889827999184, 10.331045487188565, 9.903024607459766, 10.518230790855982, 10.718851485492038, 10.646240594510243, 10.407998020574748, 10.411541112422668, 10.684175467433302, 10.618590464283765, 10.452450123926914, 10.081779053124233, 10.477170683226413, 10.337919241180975, 10.549274070831771, 10.552332547951034, 10.550579825284188, 10.749430800303447, 10.453659546065138, 10.568239498139581, 9.892125672018615, 10.479515620696477, 9.931213257731415, 10.43392884202618, 10.385493576356179, 8.555236606134226, 10.552085666752165, 10.313094605606034, 10.429071629853272, 10.434579604478587, 10.426396744460778, 1.2966194651926992, 10.650157640267397, 10.67226553372149, 10.662080457045288, 10.396263953365224, 4.22282252054362, 10.60279886612922, 10.585203052966788, 10.825402988899437, 10.685883979454006, 9.751036054668766, 10.246741174028104, 10.621890617438055, 10.577661267324704, 10.596357464758434, 10.444976148103047, 10.36753219371583, 10.165064660941956, 10.575242174586041, 10.41461289892157, 10.640283105018828, 10.641502147039207, 9.981354935485744, 10.528914767699023, 10.41982378187037, 9.481892343399757, 10.90335301633749, 10.267706918075609, 10.370400305827784, 10.30938985366587, 10.360020109102612, 10.45633055783294, 10.680760227027056, 10.695080409294187, 10.976780587764113, 10.064347063130883, 10.348619219053653, 10.58197026320936, 10.052590524270897, 10.377131013653544, 10.618434858913478, 10.364952634594735, 10.213730010657263, 9.965132946032163, 10.66313645189943, 10.416327193766909, 10.841072436245293, 10.388337856187563, 10.43743413850764, 10.652232238260403, 10.35372715627813, 10.591908295669883, 10.666100503902856, 10.604188905115135, 10.577010911752748, 10.373884074450965, 10.611877453720243, 10.449828685102622, 10.312210157421523, 10.42859755337626, 10.47440157100784, 10.28709057200238, 10.694518091580498, 10.726808490182862, 10.507116395838482, 10.58888923913417, 7.787105561039528, 10.308793726480447, 10.63597066227218, 10.648124767405884, 10.182511744185074, 10.130495709103053, 10.750472063018877, 9.82459005418068, 10.415409960730262, 10.315122504398245, 10.51568977930288, 10.692911451351845, 10.768621264257401, 10.705092332182643, 10.566687469708407, 9.35124546279226, 10.597353693359722, 10.719452142852628, 10.535522350421392, 10.609416032840173, 10.462645627195311, 10.347836418236954, 9.573975333364098, 10.451162898539499, 10.288874085126064, 10.429756736818536, 10.713263254067531, 10.636908325985798, 10.586227644965554, 10.486064967961777, 10.954571119803788, 10.595414476825297, 10.72899374528099, 10.582669041363658, 10.583059580309614, 10.31327078774288, 10.651387692049695, 10.756505485606949, 10.66765427267703, 10.695808236508505, 10.465639069364688, 10.289060011441967, 10.308101086790058, 10.816225609211955, 10.691086509209503, 10.342212087989484, 10.722598695713984, 10.506061326113139, 9.454077966463716, 11.121772484423854, 10.423488318838768, 10.6396924172868, 10.62580787818548, 10.717997659925526, 10.446062287262643, 10.781122939964439, 10.815991788113065, 10.759437393761022, 10.394748724118347, 10.51246622179387, 10.71578426900859, 10.483475970686642, 10.561197715910293, 10.535525668523215, 10.810149085582541, 10.374811004663282, 10.678144863032674, 10.567184369107672, 10.362687445526523, 10.896712701630756, 10.59442154928999, 10.681694029208238, 10.476307146000668, 9.572122430761883, 8.72600183147912, 10.601945300874078, 10.9202224137999, 10.623460451131976, 10.628878657583853, 9.083308225261717, 10.685111799985961, 10.709583204921403, 10.512445364560103, 10.304023167628358, 10.727365050902936, 10.424584905874147, 10.33041035453538, 10.59490034465122, 10.498086774857992, 10.488116943250795, 10.589996175473807, 10.3911183903758, 10.560974504713599, 10.59754912390052, 10.42508247585581, 10.54193223649589, 10.605799317159804, 10.578231615530992, 10.690558766844072, 10.417105683277065, 10.665219071543657, 10.508311850905113, 10.725470280154282, 10.855231294164325, 10.714430928023152, 10.731221107905894, 10.363530412594915, 9.892292069825166, 10.526003641175166, 8.463045096197426, 10.573572784979428, 10.650617165755952, 10.7125723441668, 10.796818537891058, 10.636638253988647, 10.287410056628081, 10.486407808656805, 10.536968182758848, 9.837820727092042, 10.400138107026876, 9.79542731195761, 10.569283773059357, 10.609152198039293, 10.334773673566923, 10.700515326144885, 10.504313808638223, 10.536239474628385, 9.726934926206287, 10.595893276437293, 10.508298770218998, 10.158222701745586, 10.309607061419998, 10.6504583929961, 10.823251813598326, 10.357924875930607, 10.311078885765395, 10.608079718005113, 9.828646740161139, 10.382262312444485, 10.042237193076454, 10.417127995913175, 10.378925246637536, 10.563933894104057, 10.466823964958825, 10.53840795956275, 10.26196841529595, 10.76915228919617, 10.102508422707707, 10.438602509267318, 10.4240782407413, 10.398934753428238, 10.720180224422299, 10.827730030091304, 10.006608694731119, 10.133190264852242, 10.358009632147482, 10.442403504212997, 10.652093914672017, 10.532500361703919, 10.703306534925154, 10.577701345301518, 11.07083510343872, 10.609897301415813, 10.867411982653003, 10.80224375090948, 10.3528170680505, 10.44191331082678, 11.00906346687864, 10.475264770185127, 10.909091851188368, 10.21394686355097, 10.529807476373662, 10.69208064537092, 10.266284082215364, 10.489060315119046, 10.180203533042269, 10.328643200370761, 10.678178907965108, 10.533374452929163, 10.427686742119906, 6.996169620047446, 9.976758583097151, 10.561344312357777, 10.505760020159366]
AVOIDCORR
Most correlated pair: (28, 33) (Mbacke, Pikine)
Cut district: 28 (Mbacke)
u, CI: 1.384470354561941, (1.3170862254994464, 1.4518544836244356)
losslist: [10.801681608937928, 10.588584477681849, 10.817004674930937, 10.40458774038886, 10.527904702334782, 10.510254812081847, 10.124619283439763, 10.500455802154146, 9.908945252435604, 10.525180421436222, 10.310333603317533, 10.314960578750739, 10.46435497544499, 10.4605538605638, 10.879332000870463, 10.48308125301006, 10.270626836211337, 10.651222890833182, 10.50844207896714, 10.64709829157807, 10.967349035726157, 10.543375798042257, 9.992344123654853, 10.694680134659698, 10.676073760840127, 10.500061976670244, 10.482389844419522, 10.988117648233812, 10.576624466247587, 10.840414655694731, 3.9827280408526224, 10.552327398432276, 10.604954023222819, 10.735014780474906, 10.445810655900639, 10.452182565076154, 8.184764541955525, 10.711789658600772, 10.831620829749692, 10.667831959142541, 10.552936934630205, 10.814976275781381, 10.365159196269412, 10.65245750179125, 10.456411983799075, 10.673845122460362, 10.516919952677705, 9.780286545870016, 10.831364943562363, 10.74107485727345, 10.643255646190424, 0.6282861859912136, 10.869880075883888, 10.393702319329284, 10.636480240902232, 10.57774021824807, 10.759143473598655, 9.941497176703677, 10.815765123517338, 10.674598786237151, 10.54109340832862, 10.64732938452455, 10.7524069161357, 10.680679717678476, 10.484846395546292, 10.49091915891087, 10.294248865920009, 10.645080900607264, 10.336882045177383, 10.705688654167895, 10.694075515241797, 8.257124312666328, 10.45711097013214, 10.461959896696543, 10.405710620108195, 10.884542589070099, 10.458118301623585, 10.766129788344518, 10.778023796579944, 10.541045697351707, 9.115155035469058, 10.65069196783558, 10.26674666120713, 10.70065122820444, 10.32023263621574, 10.589044687180435, 10.798344054912166, 10.408919064278349, 9.304872342432825, 10.513223190701135, 10.248592142981353, 10.514152000973285, 10.219834959763235, 11.01306376909734, 10.041475692335373, 10.859451956387003, 10.555773314793756, 10.37912122496255, 10.614824535616204, 10.513199782447739, 10.89953391388728, 10.449690755836095, 10.567035527249265, 10.580796216183643, 10.749143321056822, 10.61501157972671, 10.922800695593901, 10.626260963610928, 10.768026627425028, 10.91424272457581, 10.470452675183143, 10.866904520845708, 10.63184951171487, 10.292770744645411, 10.765737969610253, 10.600626424706366, 10.771926040209278, 10.6878045235287, 7.27265008232694, 10.547727171246834, 10.590806053642215, 10.63237234410392, 10.667445001430469, 10.68986321279944, 9.652444478211518, 10.64854028625754, 10.397293234342492, 10.405565844106151, 10.777278681002642, 10.741916289047435, 10.53503212410994, 10.445924577938738, 9.679540403736684, 10.526428560388036, 10.745818855342199, 10.766690244010876, 10.489208876463708, 10.651618201827837, 10.086083486656138, 10.741639136561727, 10.689424494142697, 10.29524896762054, 10.595946901168142, 10.678655379691318, 9.095699638979834, 9.729765008716363, 10.419724262136674, 9.63464938695987, 10.641817818658101, 10.556558846314609, 10.65933652909067, 11.119473934490037, 10.745850614001458, 10.54611675281966, 10.770964394589015, 10.675801382059495, 10.656825579129087, 10.724540304235576, 10.488438507584055, 10.69540864445925, 8.529102195549978, 9.565398807082474, 10.621620986416971, 10.713017034659943, 10.427125418870785, 10.724100184594203, 10.924029741159561, 10.700284211054383, 10.853449446358072, 10.466549637213047, 10.514873960759603, 9.121728153745087, 10.619985257536396, 10.607008164261341, 10.324239715600747, 10.820585536951116, 10.22485371356917, 10.893356764092168, 10.065397012823166, 10.45091299718407, 10.514601194932268, 10.523793926927413, 10.620551792485687, 10.74171510402511, 11.105993107567217, 10.737477761112961, 9.948932900963218, 10.468150834960014, 9.098832075548634, 10.850712155814517, 10.86955006786616, 10.77404260424644, 10.53042510621135, 10.573433384489604, 8.50677696246859, 10.344217227714845, 10.374165776696271, 10.574383844904288, 10.643343250035553, 10.84900324386403, 10.022663561003867, 10.562443434548047, 10.889783134023874, 10.734872476355536, 10.807446861379216, 10.597738026986622, 10.698102291908757, 10.587182505610995, 10.485316315831026, 10.481831794801778, 10.458146898906582, 11.062901377339504, 10.698362845040327, 10.755128916643867, 10.510729857173843, 10.575644515289463, 10.504235559523133, 10.599333459608731, 10.660701915306428, 10.920130969447724, 3.073117200029344, 10.706009755362677, 10.63384280824945, 10.683597719786446, 10.917560230667974, 10.177219596630014, 10.566183006302857, 10.81294973932164, 10.6685068477827, 10.575797096400443, 10.467430567242978, 10.791786315866055, 10.472849418789359, 10.771478635955527, 10.912512649406914, 10.461322055084494, 10.67139704783832, 10.718306525739463, 7.622489112297134, 10.40556630930831, 10.836242392867325, 9.26315465022023, 10.808849239893997, 9.75122826906464, 10.152693638791241, 10.202641710859066, 10.461364760919901, 10.519143204240777, 11.012994196557582, 10.91302107264941, 10.74688831442021, 10.3302128397841, 10.492806390113898, 10.536565330853255, 10.74449396977029, 10.721998518102671, 10.627701921885702, 10.667417741903776, 10.371630688420257, 10.879167533983154, 10.292489301752397, 10.042508827420088, 10.650134310165807, 8.787629404749167, 10.892909520735234, 10.539211442976798, 10.681690668888455, 10.889223833661239, 10.579645095655016, 10.541377110256894, 10.816967504514732, 10.870882407581979, 10.61064821814925, 10.514544682526749, 10.498502418594196, 10.66206396023839, 10.858826895258163, 10.636164849787948, 10.14669425425073, 10.420803302817324, 10.699950895113886, 8.956165682833385, 10.876482878913595, 10.575253931636407, 10.547274981161552, 10.017238674941797, 10.858118909208088, 10.496520755932687, 10.032651268219702, 10.482058734189096, 10.64820244830058, 10.865498983983938, 10.54564592497742, 10.650039009289664, 10.961505212581628, 10.710081158544183, 10.345502766123852, 10.461098131877044, 10.43380883946529, 10.602577596482442, 10.376783690695719, 10.577014736210097, 10.779030403711086, 10.447749800779098, 10.191482930826075, 10.73251431294053, 10.841303995502383, 10.584713156221536, 10.630299537187218, 10.56282989313545, 10.5113024634218, 10.046533905193975, 10.700103448281029, 10.698451664367184, 10.396539694434423, 10.83979213255181, 10.447305154005907, 10.611164350455972, 10.666133003399564, 10.128428601637836, 10.550306908517765, 10.273942091654849, 10.53453266555847, 10.570323519790083, 10.629250302445246, 10.284148812257358, 10.652776627464645, 10.533424167819595, 10.219846458799772, 10.725251546269803, 10.538203217447377, 10.60048662216598, 10.556864686877503, 10.008121600950508, 10.643015370384045, 9.574778361483267, 10.627369422756644, 10.781770650593202, 10.853129894955172, 10.5807342780199, 10.608324414256238, 9.542597349882767, 10.350347575910835, 10.69336290756433, 10.458462635005386, 10.767109813210553, 10.677357859904113, 10.576472415263213, 10.55961157249105, 10.469219854278316, 10.782792435879502, 11.071023438184172, 10.672709785799748, 9.866037634764561, 10.91142353394392, 10.458224367636843, 10.636874260219257, 10.506900859023727, 10.409033871648269, 10.378187878572172, 9.455684374031753, 7.606113629240965, 9.80792747652755, 10.572884150790664, 10.72971781153041, 10.510906038624901, 10.952016224674196, 10.646414579887216, 10.429492381553326, 10.639913456228241, 9.454006430720913, 10.623665820317262, 10.604637442534523, 10.538006957997386, 10.75117399000686, 10.583926342243617, 10.632711549364013, 10.459744065384552, 10.605144674475355, 10.683801347408666, 9.805634084789514, 10.201984477275131, 10.635380021319286, 10.491326811735506, 10.586652600924598, 10.207339072987901, 10.607315675345403, 10.580613175366988, 10.736815018100508, 10.692552925679209, 10.860262045860733, 10.465662619253461, 10.548480415236869, 7.918769792620513, 10.67138572600031, 10.673989888117381, 10.679432071875581, 10.333397031598144, 10.746349014041543, 8.472598352496238, 10.563299612064448, 10.475329713010355, 10.70898321595626, 10.749594543929577, 10.684261979320349, 10.750046199728912, 10.873485812200105, 10.76308866681515, 10.717795466318366, 10.710396256589188, 10.49408841211115, 10.660935183833852, 10.504303813217906, 10.646765678743957, 10.791903017549332, 10.581468531507543, 10.601929029533427, 10.595680422268357, 10.672847051600018, 11.007991255305877, 10.642948782711844, 10.761220436451945, 10.794011640529593, 10.567617634153555, 10.751047178983843, 10.714966851535983, 9.621360344518573, 10.142642132413474, 10.649720838286157, 10.472138337119256, 10.613744714623714, 10.601050767821333, 10.308260736290238, 10.35754732745886, 9.008764413477067, 10.498329217518016, 10.583214852068345, 10.728865375073877, 10.539863390468573, 10.617390873831559, 10.428246896772034, 10.549718326264806, 10.327692877222455, 8.959023936248139, 10.352489568909746, 10.746409275115633, 10.58297322191013, 10.716209793625888, 10.714635956296762, 10.556228981079443, 10.73985623587089, 10.364113946037874, 10.395977405716051, 10.599410142670234, 10.728927418018344, 10.749006729069894, 9.397665105983467, 10.62033523248234, 10.519683866400046, 10.706019873603966, 10.495462664265066, 10.757072327776847, 10.413488937952797, 10.654372503523307, 10.584771717482857, 10.578434499255719, 9.668820564386275, 10.87119339140639, 10.13580709363673, 10.40072867658512, 10.46023700020974, 10.604259967466312, 10.854434695150658, 10.644288627563489, 10.420606433941158, 10.7258520424717, 10.110037485036521, 10.860166495998355, 10.397132554430614, 10.655485146024526, 10.718537351174907, 10.551010714128353, 10.370311771730876, 10.570210418821825, 10.45939808093919, 10.488960492341988, 10.587858553996755, 10.785629987081117, 10.609731265487968, 10.83582329211833, 10.665040565811154, 10.496180909273967, 10.756501014145204, 10.93304716446386, 10.861565065940116, 10.414523299146637, 10.305884578878256, 10.371776976990605, 10.901981785547264, 8.112272566858586, 10.859146289484272, 10.599215033196687, 10.632080232602975, 10.650591642528804, 10.703902393593513, 10.49422919987511, 10.606542544056042, 11.073076013556973, 10.60244691216515, 10.554584400865853, 10.608463207574804, 10.269107135111158, 10.326562888885032, 10.839875326574184, 10.396260646948438, 10.996303363665497, 10.222653834861383, 10.361415748403466, 4.048830199392407, 10.810532308050508, 10.451251856324522, 10.93909427104554, 10.174990864751331, 10.732307748499446, 10.604076951676142, 10.74100419743632, 10.271282915893146, 10.790364743889166, 10.56771952042745, 10.653251974231319, 10.398053044545223, 10.58463886753777, 10.349687094562894, 10.179537784058072, 10.71468943258356, 10.570210075787582, 10.957968560889952, 10.462758842245877, 9.86962524456479, 10.250478697677012, 10.499131728291065, 10.209565163551712, 10.81316721085843, 10.497404299995704, 10.231227609321671, 10.690205281941902, 10.535238506351748, 10.330966932046334, 10.45994962920336, 10.649643118828953]

path 10
init_u, CI: 1.359581302788575, (1.3066834638841218, 1.4124791416930282)
losslist: [10.429967776957671, 10.467103340175042, 10.336049433494441, 10.405089765905322, 10.553673995863878, 10.303005396596014, 10.00797415154574, 10.477937008127036, 10.500147377957692, 10.432799237099191, 10.48275340188063, 10.386749382023323, 10.458061481644851, 10.563121979901265, 10.57065634953074, 10.367896335574402, 10.674224163643668, 10.410400825251566, 10.56441594108728, 10.36630656579374, 10.450896564358878, 10.2308213368706, 10.336878161889235, 10.454898816355128, 10.105335079334308, 10.121954900240219, 10.474353108160535, 10.863834517052236, 10.646701468369923, 10.431600573822182, 10.325129721302906, 10.408946760788654, 10.540652592225804, 10.601101647734952, 10.316536531041244, 10.47091226602893, 10.693772271674602, 10.562846605732835, 10.973041488275133, 10.515671241290592, 10.535936344712484, 10.406452808143255, 10.518500071261249, 9.958647664938725, 10.686170757275669, 10.333038801955551, 10.30294128802243, 10.675459081231622, 10.407828824995512, 10.612815982194071]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.4046122168968633, (1.3362814309248137, 1.472943002868913)
losslist: [10.50317730106733, 10.504845702357589, 10.635962199421304, 10.098513605121036, 10.810474893047205, 7.855589416272605, 10.549136454549707, 10.36343581370695, 10.450141594032845, 10.627355804310035, 10.722499570694652, 10.558465501925031, 10.315721945340115, 10.5272148839588, 10.348588379357041, 10.459745124197552, 10.739878585407387, 10.666429095555161, 10.615281631442013, 10.478486919029097, 10.573874258708308, 10.560713613613741, 10.47839655512112, 10.938106174612564, 10.899127968534977, 10.629619324057467, 10.606220038537776, 10.680737793807575, 10.957389941956974, 10.605758441174203, 10.351484550159661, 10.08125713158524, 10.677224623928907, 11.034345161048297, 10.426780191263957, 10.470385848948117, 10.25255234276169, 10.671094397856168, 10.547690015784413, 10.504814594103973, 10.560503722964494, 10.541787764694533, 8.214534224160015, 10.5585678970527, 10.903797570309438, 10.634131177353783, 10.407935828541127, 10.390839463118695, 10.198074277164437, 9.812722153071444, 9.821118091703985, 10.634710031793087, 10.770205530218899, 10.387391806013424, 10.087565642374454, 10.346079470356802, 10.51801560294, 9.716071760959537, 10.480350822795694, 10.731729992282906, 10.372544544564759, 10.7267228880572, 10.62572499095105, 10.836741381926181, 10.42766785239468, 10.278507186554835, 10.558483317379327, 10.392404336556211, 10.858948557109384, 10.589473046695854, 10.741103319892572, 7.18925800214389, 10.09188254221326, 10.559758106442272, 10.731047407893938, 10.554024897147695, 10.689453956623106, 10.559631213009842, 10.608989976564578, 10.656461661177081, 10.726491205710712, 10.574375888138258, 10.341889089019174, 10.75384040719636, 10.735862781568004, 10.787502372190337, 10.597835482653874, 10.536579502648504, 8.43390133456231, 10.690171472152503, 10.4868138644955, 10.751236008758086, 10.275465767722588, 10.3811645512575, 10.283616546940634, 10.546353869640955, 10.480147170195343, 10.637409559330434, 10.728421213600608, 10.226814786653637, 10.603070725648163, 9.01410557991404, 10.70851474922469, 10.73134637750712, 10.900479604699788, 10.64692524117101, 10.11867591104829, 10.737455103422702, 10.441581101501312, 10.59770043439144, 10.560750809038092, 10.52449320039162, 10.750334968443052, 10.591982612851073, 10.496728982563821, 10.66495566662427, 10.722199053114057, 9.29903730416904, 10.368254026104651, 10.526159685565622, 10.36988497492451, 10.221504694165116, 10.315385642385644, 10.75879749044746, 9.399102038130005, 10.554263035016662, 10.616832911845993, 10.230032913008715, 10.500241122307983, 10.581788051087305, 10.60372032631468, 10.527785594493496, 9.205380914640893, 10.499632870316905, 10.77157954793353, 10.832998582392145, 10.769700961115078, 10.278223214112307, 10.428651175177217, 10.636802925929368, 7.4324378882561914, 10.570361130868688, 8.9350381994996, 10.869411519700343, 10.4225973335648, 10.624751167991532, 10.339092930923192, 10.966572895465067, 10.225324959554621, 10.441491171156255, 10.58718146641125, 10.711845293268395, 10.75815611979274, 10.455993924852747, 10.568430473106622, 10.061992945091612, 10.509925153167707, 10.363885328295023, 10.087513572178048, 10.745008212942487, 10.304934339897565, 10.192682096900233, 10.299276369761587, 10.61612125890447, 10.731830320611774, 10.767231207206617, 10.525383200833266, 10.389683389044762, 10.6786714554909, 10.841315938279598, 10.255841217716297, 10.940317191550067, 10.915927935537876, 9.364632455689799, 10.491930738942303, 10.714868743363953, 10.511513266098637, 10.51305228878624, 10.737210326348587, 10.445664259675926, 10.684344175838735, 10.412081879644512, 10.360451280145547, 10.321250868921656, 9.771137265238206, 10.515943784369306, 10.370413103293382, 10.638826452693836, 10.023871227970705, 10.670036341522925, 10.86020037029131, 10.670281495516116, 10.615105491210343, 10.421025892048018, 10.80572629822733, 10.434622823051573, 10.674956136871245, 10.52967173145669, 10.246221775502521, 10.35195021617014, 10.33828450003194, 10.791677218977092, 10.460740133907112, 10.403387636913385, 10.549856221286605, 9.355254759403648, 10.432360206691452, 10.640986972272236, 9.885310927661656, 10.516088071246596, 10.275754376656264, 8.490629370109604, 10.741366067150809, 10.53946693710983, 10.367163403581412, 10.635775808936136, 10.760625272705878, 10.57867495429729, 10.558860205690019, 8.319299686256677, 10.511581777005025, 10.634684393348135, 10.46249598524211, 10.628860093820151, 10.467069836743697, 10.898965193560443, 10.61947628529847, 10.727144790950426, 10.333960605421426, 10.56897305254418, 10.853295640423251, 10.53989900888702, 10.396440227981424, 10.398663129280955, 10.652452013656106, 10.710365188460953, 10.54711613411121, 10.413864008151682, 10.502520608538374, 10.801095697555587, 9.82573016214709, 10.775016842033802, 10.540275716875414, 7.970873412198842, 10.724277493926094, 10.515798094084653, 10.55533560275645, 9.354640963880305, 10.391223358924538, 10.469018663087814]
Most correlated pair: (8, 20) (Fatick, Keur Massar)
Cut district: 8 (Fatick)
u, CI: 1.159810949490371, (1.1099722219037016, 1.2096496770770404)
losslist: [10.969249398837338, 10.79492847969726, 10.877815918276351, 10.72119039161338, 10.539865619736528, 10.709242530313045, 10.983437139014638, 10.832349164413058, 10.742843027812416, 10.423771373366513, 10.782312508232398, 10.790801968773598, 10.375429480387668, 10.890397720557694, 10.794993050157357, 10.752370921113792, 10.52973690339999, 10.63708476385081, 10.637379817884549, 10.80297936917286, 10.785059172710747, 10.841919524846077, 10.375702357442881, 10.929764651557328, 9.380355261883984, 10.688033995708935, 10.682766904218925, 10.773143443266708, 10.55905355610642, 10.571665143725621, 10.647260808200505, 10.757261262255804, 10.817207158906884, 10.732160100357905, 10.763510472750125, 10.716229991284639, 10.761621602546121, 10.033736676120514, 10.852241719052696, 10.65571552323631, 10.55341332571853, 10.793660996315198, 11.023629075047191, 10.402251156226697, 10.821295912526574, 10.636364307008808, 10.707249311565247, 10.962142315855246, 10.794931916878472, 10.681071298405497, 10.685352968432422, 10.48054374283292, 10.656048357604263, 10.985793449764197, 10.529380046817213, 10.779960786574305, 10.594800606307091, 10.625462191094211, 10.661161228330963, 10.607206971834778, 10.626277059640108, 10.8351945693761, 10.948034182300923, 10.72394499189983, 10.867423001752348, 10.532229595543285, 10.7733708357106, 10.732408948024334, 10.22550634618199, 10.438612444232051, 10.785083782746772, 9.07041029027982, 10.953156138968916, 10.98853211731612, 10.4244001487692, 10.51334859763601, 10.61811670109171, 10.99288419658497, 10.786519817802626, 10.875647486947788, 10.652722553711031, 11.030322979847432, 10.566061373668896, 10.457323544257651, 10.716540503203017, 9.493320648083783, 10.716103827557548, 10.69448842678335, 10.849575734461412, 10.423642071373775, 10.928644072608352, 10.732547180406053, 10.951021398845757, 10.498673909734297, 10.61128247283105, 8.897389190869747, 11.033508041273556, 11.131893994240286, 10.785837030594093, 10.835637388429882, 10.541205919896427, 10.62273410014596, 10.828010677069027, 10.903334925776079, 10.86145862015036, 10.93089051063058, 10.678450579370018, 10.971563409618666, 10.65294406789724, 10.779343729971632, 10.713096100164753, 10.937897653247665, 10.592093848582735, 10.975548414143773, 10.925510309264885, 10.748063854603052, 10.759803945666516, 10.651631171666377, 10.863171843610834, 10.705317145864688, 10.775203117997327, 11.078065937965947, 10.768926200520108, 10.726823213010412, 10.731114720999171, 10.725475019661294, 10.481198847524857, 8.568621890249482, 10.659858959719507, 10.7903383952444, 10.89314176397598, 10.668468868147613, 10.945453003860683, 10.847516451466122, 10.681796567515494, 9.85483230565993, 10.904362569601858, 10.679539829728343, 10.788421904733623, 10.675759884785041, 10.963809936029522, 10.624870349511596, 10.48748879893061, 10.788458399690265, 10.484191987560985, 9.873646157093567, 11.026352805036915, 10.139557939261145, 10.675931370643507, 10.60361745983283, 10.681905515820512, 10.474130868701353, 10.769327507952571, 10.61284969481098, 10.719206701654352, 10.817082420661846, 10.686739540841781, 10.583026248671162, 10.577042223986597, 10.800482380468976, 10.72177165518044, 10.74937945395455, 10.557009517760203, 10.609843765009673, 10.629414613290507, 10.828964070343757, 10.661715409864971, 10.941017679771726, 10.77240094136278, 10.821711098181952, 10.602083266312373, 10.690272125630576, 10.268429966993866, 10.919398724636656, 10.729563992895846, 10.76014015613035, 10.634312542712477, 8.899209820456933, 10.735226906106787, 10.739526823397084, 9.464342272316925, 10.77735168252956, 10.818624889217725, 10.804462263747453, 10.788469289095648, 10.686818669757487, 10.756665767964844, 10.711180575690436, 10.79218663745213, 10.620418608186476, 10.928100952790434, 10.592454558002041, 10.665699299660037, 10.751967981007196, 10.58057090117938, 10.619644408895715, 10.775866163732449, 10.004675188508122, 10.880338786069768, 10.662228962788692]
Improved path index 195 by cutting districts [9]

path 11
init_u, CI: 1.6138151791706825, (1.5347448851631214, 1.6928854731782437)
losslist: [10.966763151898915, 10.658606132807073, 10.168719313973083, 9.940287179094078, 9.768722024969323, 10.03303248014048, 10.302449250202052, 9.912785004647688, 10.50293205285561, 10.50496804843068, 10.504488963106166, 10.657979234821317, 10.946000580099582, 10.875716589763488, 10.495881589604425, 10.38931719566295, 10.520312790071662, 10.514127314447647, 10.57692044378554, 10.538064200810846, 10.236422300365437, 10.692156184667216, 10.392428948517486, 7.509935599224681, 10.614513445616838, 10.473375192705216, 9.203078391765384, 10.300147479604794, 10.606656949309388, 10.796522241538293, 10.672884531107252, 10.156777041413305, 10.759425346179933, 10.321261077378253, 10.138382655449695, 6.999542892880095, 9.880122382525096, 10.442619695884932, 5.600004897369555, 9.913936391599172, 10.088707842508608, 10.528712625498118, 9.897097511783144, 10.293715751039324, 10.494714774391467, 10.241459455894114, 10.741301713609023, 4.3594852191254505, 10.611028779553168, 10.416291608681759, 10.479341090804633, 10.249623046719279, 10.414290108354772, 10.438553750784092, 10.613720174335807, 10.590134463386184, 10.54321180867537, 9.957046285095993, 10.172090087146591, 10.73288521973679, 7.156656937662253, 10.61126712579627, 10.723216222720898, 10.980744545769923, 10.674162263738143, 10.544755356738008, 10.284183393618296, 10.297521070685761, 10.985660117467852, 10.657820875995416, 10.338330595071701, 10.33156716654896, 8.43035435299297, 10.359075807977735, 10.326622127837751, 9.317722989624963, 10.474035016171502, 10.152076393751907, 9.710004761059377, 10.556633996097961, 8.747289126825725, 10.614060939967555, 8.162353437894108, 9.84371534038505, 10.311321210802287, 10.594141433590897, 10.549852553397802, 10.250595329998086, 10.442915571537176, 10.45681988681409, 10.545099995995242, 10.634086102764847, 10.841865033411416, 10.394131102079093, 9.71942471420761, 10.229365248473869, 10.798257003488663, 10.446117645319283, 10.750707927549197, 10.288150773583245, 10.155208169676529, 10.531932770078596, 10.247436623875283, 1.4571934284356565, 10.43793132745262, 10.683473008776327, 10.467239823093838, 10.35979898646311, 10.269840732812863, 10.352795327656846, 10.214818140071229, 10.135728536370786, 10.386220202073762, 10.491549505690369, 10.096403129852916, 10.603860988510478, 10.25076642973855, 10.541155588385783, 10.672242513978484, 10.717554764926357, 10.896266130449035, 10.628377884516578, 10.321060710890698, 10.740260136089804, 10.57912446286066, 10.48216625719395, 10.550812865958676, 10.685192610771308, 10.705056376076525, 9.929533188659931, 10.163788293339184, 10.16234099081225, 10.605726004071899, 10.600862672390093, 10.719446077710954, 10.198398391576896, 10.568118744986492, 10.488776693024157, 10.618763041014844, 10.757929213490087, 10.316111062243733, 10.640512825547217, 10.360148070253722, 10.032752936346135, 10.59421641071599, 10.46430279126278, 10.65412919612817, 10.335308260058282, 10.6390492542618, 10.378242644231086, 10.639691449717956, 9.075732509410619, 10.294245884808257, 10.536631744515958, 10.873991908158358, 8.572307771181418, 9.2637369130108, 9.448900852320127, 10.563359512585833, 10.323258122189973, 10.362323951349858, 10.801194287925906, 10.554559195415491, 9.794029402974571, 10.635427866694215, 10.184923375240889, 7.182814407992702, 10.61977794050297, 10.620541972712495, 10.154113572994769, 10.458417433006618, 10.272918248901638, 10.569931867548748, 9.570190220442116, 10.994143780804132, 10.066990451820953, 10.829953876821063, 10.150778995233784, 10.313500577907929, 10.298398698219204, 10.370081942487714, 9.1428512405688, 9.044049668667327, 10.155209700557046, 10.596288791763499, 10.593672172532221, 10.704999697105338, 11.051364497383847, 10.755531545542933, 10.50743153721436, 10.128400026167482, 10.45686777851524, 10.642163556727503, 10.5253497819759, 10.847941204840048, 10.747643575135685, 10.351184465849327, 9.428931585994837, 10.50461796500208, 10.189201441908835, 10.313323626993725, 9.093575199219895, 9.135552917410012, 10.581999392038945, 10.678154409540205, 10.373657571497603, 10.81171792823024, 10.496975305244368, 10.60285184954521, 10.521944621724176, 9.888816726702629, 10.422390835604675, 4.526637898670481, 10.553081691688822, 9.214297155403255, 10.562752407055141, 10.410056126151979, 10.423828420608288, 10.644292192231378, 10.41030745575563, 10.648134259550762, 10.193439568966916, 10.747907030867934, 10.55856225633904, 10.689832582182783, 10.219955369014864, 9.316201903146029, 10.469634411785863, 10.673713029572841, 10.713754415861384, 10.503416610260116, 10.736619723770607, 10.513037723068594, 10.646819103657819, 9.092802435854074, 10.125232290282497, 9.889545242975494, 10.494565609979983, 9.0747043254365, 10.631501138332485, 10.497033346395906, 10.84634098084398, 8.207798223899935, 10.377654481864855, 9.790216944948689, 7.1517983327231285, 10.675015131942647, 9.489104801129082, 10.471762378498026, 10.822762048532299, 7.323180583208351, 8.678248035245455, 10.033108468355493, 10.51412594993409, 10.475143805376947, 10.273590937669821, 10.621293648164865, 10.137566722462427, 10.933563728082142, 10.013771862324589, 10.192754371856529, 10.247097247644408, 10.219962529752756, 10.151911571517617, 10.579778416601666, 7.414038122134585, 10.693481801676354, 10.24910173684606, 10.208810200247893, 10.36214637578269, 10.44808284844206, 9.334639716541332, 10.53947211896974, 10.050025652913144, 10.320809470256357, 10.497210725590094, 10.711119408266972, 10.795435669981874, 10.270518371268748, 10.214885199469341, 10.755819994202318, 9.916556603560107, 10.721016584539546, 10.067775805185349, 9.58085036388938, 10.561093156532225, 8.299049109628617, 9.093230520017212, 11.010110975322293, 10.549189735867348, 8.968916336990166, 10.665608191470053, 10.830017407645162, 8.025038486334434, 9.71756634957427, 10.391781485139255, 10.91446185924496, 10.455601895226817, 10.463431061364913, 9.070763502687065, 8.970641704816813, 10.45453174193503, 10.48314925641358, 10.696195310133183, 10.413693818916121, 9.654486245352038, 10.503395499927583, 10.25038241065654, 10.457273820586785, 10.416729994799335, 10.437207914978638, 4.993530610914998, 10.675110814371095, 9.041508691575903, 10.704286316268194, 10.657811256719883, 10.302499135191468, 10.477307303585881, 10.651307565382474, 10.166819385031447, 10.902210358385384, 10.289131593408296, 10.62514486659169, 10.480709753799799, 10.384681643859125, 10.006347311840145, 10.796219917747425, 10.590041341354079, 10.54843106445151, 9.999973682536492, 10.671266348405762, 8.59072275263244, 10.65684991589001, 10.34948278061222, 10.67676154445339, 10.348757666458608, 10.604041084024272, 10.628510466876833, 9.628753303974419, 10.76720825523204, 10.550270473288531, 10.476022627907811, 10.679167396999116, 10.519849529225176, 10.268418332241852, 10.406164732333895, 10.550755192527332, 10.653863064883987, 10.728275955796056, 10.056498668715411, 10.61081284108672, 10.744323726839614, 7.655943785130006, 10.584399601113082, 10.34479801482001, 9.605801996924457, 10.06804804232769, 10.545549661955597, 10.253745640327942, 10.409510763029905, 10.614484814783026, 10.206794049508666, 10.493597193761573, 10.522230087976157, 10.861166414332171, 10.686121672367994, 10.499334484100087, 10.37405116934595, 10.361529922254164, 10.43897863080226, 10.588905208449177, 10.65836354725324, 10.6215528389999, 10.510293112383398, 10.572436212456397, 10.537023704039354, 9.96696102656041, 10.463493861183945, 9.890366617215516, 10.585859169369952, 9.098461665884315, 9.085397572416811, 10.479356607869862, 10.124030994982716, 10.699416916803408, 10.59208250831155, 10.250116526990134, 9.932592771951638, 10.290598008004823, 10.449478191916445, 10.276356825239466, 10.113759164471317, 10.589966849350933, 10.94208757896883, 10.367993863961145, 10.608009952131212, 10.25239945150897, 10.767242202261208, 10.620622599051845, 9.516585358394941, 8.728742838563585, 7.606234534027751, 10.714388953509257, 10.612750602380649, 10.531695051550079, 10.37629216011768, 9.994257133039913, 10.705382312071556, 10.517765874544144, 10.772852508316321, 10.218892659271875, 10.62237796153942, 10.791993228134888, 10.489665753393155, 10.235038329095799, 10.635312516174242, 10.536087703516108, 10.675868940517573, 10.741121767942492, 10.718504985825401, 10.182678876251897, 10.08528655658111, 10.726950221832322, 10.613386892249725, 10.507483934847468, 10.52238990347078, 10.256075012082574, 9.769351574604608, 9.56194981856947, 7.557216897348909, 10.732415202480949, 10.290877431867385, 10.489728373070452, 10.636334401533034, 9.901690089779036, 10.504316214204747, 9.957088938087153, 10.54696518995753, 10.195587441423552, 10.61808195520191, 10.78715492641362, 10.610525662709165, 10.069474683391416, 10.410026780502891, 10.710125347170603, 10.565959810050845, 10.403452529800374, 10.634433764184216, 10.228436800731632, 10.180433213680137, 10.374744625697899, 10.498181847558639, 10.184517905198955, 10.63475685674437, 10.825771312013241, 10.530658942742264, 10.526671708370309, 10.486231250529219, 9.876460281841174, 10.94652584820282, 10.46612389506114, 10.55489827736296, 10.575395349416002, 10.012524116496259, 10.606498782933821, 10.708584699405444, 8.122396060646635, 10.154196659451426, 10.120298242986804, 10.53964554322809, 7.45424919423664, 9.938650365117063, 9.932195988507559, 10.307048264332535, 10.395607399071665, 10.54032898935679, 10.342538469251004, 10.213538717614957, 10.567700197168259, 10.289634663237855, 10.117112660690509, 8.758735258991447, 10.459491901928564, 10.340309616432465, 10.832324342598358, 10.556624173112912, 10.440320290779935, 10.73125498830882, 10.368279981288865, 10.096578678948715, 10.399409394893656, 10.485632751438786, 10.427689721476494, 9.70725497306627, 10.808715132854855, 9.105406358614056, 10.377677027208799, 10.315537491820706, 10.523558113745448, 10.825460951460386]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3929113410344485, (1.3239767748148665, 1.4618459072540304)
losslist: [10.70283965533641, 7.040878609984036, 10.14365083542878, 10.744150896918296, 10.600339277546565, 10.81891947662495, 10.774600710214965, 10.412162576338863, 9.992556907732618, 9.98646608445541, 10.491911816598028, 10.514889271971237, 10.61435861361198, 10.655682108304783, 10.710163424643682, 10.662365915785982, 10.615466113375113, 10.626011272604236, 10.72891503533988, 10.725019512600149, 10.87984916220881, 10.697268235579712, 10.76813940300322, 10.737278402753544, 10.17351934028916, 10.351621434122086, 9.89462267854376, 10.867219498422553, 10.495918132594442, 10.878570937966614, 10.815384805509158, 10.57222878910633, 10.721153709811624, 10.360143856844433, 10.587378709260333, 10.625793469806107, 10.680201228900406, 10.815488482480385, 9.501099577941655, 10.603083752405205, 10.879870750886594, 10.797779937983913, 11.136255140873729, 10.719737540561004, 10.64936334626898, 10.65186749899634, 10.354618468839535, 10.524047333958077, 10.79743539593408, 7.620258877810724, 10.776582443725832, 10.671345345461592, 10.326750443299742, 10.705821008298257, 10.937865193640755, 10.63547014963342, 9.540894558645942, 10.837342566465887, 10.495614223293115, 10.131011177688036, 10.55101400103835, 10.396601107081318, 10.738578118184991, 10.769573993769857, 10.485125408332708, 10.320125076242245, 10.660758181879661, 10.664359021581136, 10.245190286643197, 10.397710607885198, 10.567603707972914, 10.596337912496542, 10.476799885252754, 10.522363477375277, 10.236463130726394, 10.627659691384375, 10.624189911058775, 10.769403157162731, 10.679477262247193, 10.51535010707566, 10.696472201963433, 10.0809425619793, 9.009755882637707, 10.520678450949278, 9.94935705174497, 8.957945179224984, 10.747754864350394, 10.413920647223486, 10.581798544695795, 10.053164224421153, 9.593631018315623, 10.72268125583305, 10.972556809206274, 10.781717931233189, 10.633822807780234, 10.673073332231622, 10.591554007653372, 10.810225993629816, 10.822544667793634, 10.727448829347956, 10.46856707425235, 10.706947593205003, 10.699784291020954, 10.444444322025415, 10.639001022216522, 10.39051558290228, 9.746668210615535, 10.270678255380021, 10.68697226276086, 10.533279628416341, 10.114406393611583, 10.51436379955522, 10.675482383666981, 10.866692455171037, 10.594978833367987, 10.336636622961297, 10.524654819525868, 11.103075524560996, 10.542316715655522, 10.88213449392505, 10.588435205954191, 10.721078979363922, 10.784691618893383, 10.535541676296837, 0.36959937534278237, 10.250321069357945, 10.58609809656024, 10.690391035829519, 10.837861581318228, 10.626645912372434, 10.047957424634482, 10.395638219569065, 10.666170473593244, 10.439380732754145, 7.462477336740126, 10.093389939850002, 10.771656743922422, 10.581061135516658, 10.615778214852421, 10.915512855162731, 9.394058694760464, 10.99128681682451, 10.567304359999705, 10.375856189150475, 10.4036378431095, 10.584610353614092, 8.94370391681452, 9.800734399796703, 10.585162508185983, 10.1815562583831, 9.500493075061337, 10.862767716597928, 10.255829461484062, 10.008252983886575, 10.747869691893111, 10.186565852999468, 10.471268635638399, 10.89517424997652, 10.423186711393834, 10.229123419622958, 9.806185489583786, 10.674281977525162, 10.624375452506202, 10.075472072646706, 10.94518482235136, 10.77330947372399, 10.547913686601468, 10.560625672050335, 10.699758339512956, 10.409391992165116, 10.38011945550316, 10.854836655670102, 10.908562826804205, 10.416183174917595, 10.971594249289314, 10.417930189577708, 10.660787627225135, 10.61193378645024, 10.851563543447519, 10.87383973989533, 10.194289073081356, 10.658244668096035, 10.513266812188851, 10.646675457044852, 10.575209937976693, 10.320528917757612, 9.663600263570586, 10.540637520202846, 10.985711448518586, 10.47663358060134, 10.772052784656518, 10.524656850456685, 10.408995598141132, 10.745514323010442, 10.925482544399744, 9.850281515908568, 10.377176627868804, 10.282661134256765, 10.704745231457464, 10.603443521202468, 10.833459669623872, 10.003366207042902, 10.548235980746563, 10.633120973532018, 10.50350374529836, 10.877571797974506, 10.542764047642866, 7.875178498778096, 10.753903638028147, 10.52563818399272, 10.618604194476145, 10.753646290536766, 10.726065835453836, 10.6158783059111, 10.485417154205866, 10.791858090193479, 10.051259989027155, 10.13414109800903, 10.334571302575405, 10.269738430718478, 10.265023662896963, 10.90848040609883, 10.879574609211282, 9.997734451925592, 10.311513501634472, 10.599548195267516, 10.582048107176284, 9.647700899549516, 10.63977247255111, 10.722758659253792, 10.761771914632565, 10.466985386076555, 10.558655006959349, 10.631028880745275, 10.56771707525482, 10.726356083609646, 10.734907279031441, 10.70498206490823, 10.788207030943255, 10.787320114247768, 10.55579725334725, 9.930869228373265, 10.698513816702135, 10.865218479508993, 10.43321118945183, 10.513197668623423, 10.741964492052048, 10.709202161423901, 10.747992900513314, 10.502436238846448, 10.462955953189246, 10.851620989083672, 10.867330754054677, 10.599411380276692, 8.787593989411278, 10.612658795531729, 10.754917147382402, 10.85022031226919, 10.941345144551223, 10.876195652802915, 10.762546023321127, 10.71019125787187, 10.463614107651548, 10.626595839869466, 10.207941980678475, 10.678470369976942, 10.956317479307245, 10.624442089292417, 10.598536905222266, 10.74737291208233, 10.155546812314343, 10.277763794499249, 10.70894418676361, 10.498863604540896, 10.698178881444564, 10.704427905932382, 10.878600236889296, 10.412807102720713, 10.749690609544993, 10.651345433052803, 10.54389169025791, 9.930653717542553, 10.514504751716986, 10.573833414050393, 10.339559476249345, 10.438107556772831, 10.628760557800074, 10.355137231924518, 10.53018402778762, 10.528052475285353, 10.731915599651549, 10.56139730478012, 10.848901361537218, 10.144280544324747, 10.10984804907744, 10.828654819916167, 10.74733042070549, 11.06233097198278, 10.755771087958468, 10.700373572024676, 10.462629650469399, 10.6021535196202, 10.567485565512712, 10.335597294008805, 9.989040734734498, 10.684650673446141, 10.751826468132338, 10.66696145709081, 10.235332159745472, 10.388300065581697, 10.241837484835377, 10.57575212307822, 10.753549974085855, 10.598936889563769, 10.810718405646815, 11.109867672049456, 10.51667776677698, 10.720612420345237, 10.565672247011973, 10.915524303563771, 10.781610013190171, 10.440388912209906, 10.918533957823312, 10.721361994873227, 10.851646127611172, 10.734031291740825, 10.601700579757408, 10.471926413315893, 10.925736874804937, 10.4121470669312, 10.490205451171907, 10.718722838062698, 10.38840578827643, 9.777451918200518, 10.222021582355234, 10.75235439528685, 9.539714381626455, 10.269631893925567, 10.273738265511083, 10.762196579607078, 10.035221535451496, 10.662287608611676, 10.259639671674945, 10.28774660584932, 10.703883264968576, 10.71635762535634, 10.250609642635911, 10.57750303194967, 10.53964733562956, 10.31902001045177, 10.505222319969782, 10.90378268653172, 9.947603945960301, 10.598935648294104, 10.695753472891967, 10.482569323053326, 10.76523898207228, 10.738899521069108, 5.992753337302926, 10.834415923129663, 10.83163779320094, 10.635204998503937, 10.334446340459927, 10.588234951769158, 10.26322603763427, 10.470254905498223, 10.607933714527997, 10.518924937685727, 9.484039990521463, 10.848131022916936, 10.939246212204425, 10.698199705181706, 8.43651118616923, 10.451104198894344, 10.87745103411274, 10.324479015992098, 10.485394531340711, 10.542452931781554, 10.726666295320957, 10.685718783459883, 10.866045405004215, 10.66108407401655, 10.71848744167163, 10.188874729571758, 10.666225594660236, 9.241225417511908, 10.240981520639187, 10.824975234531895, 7.834857578649388, 10.740269482465623, 10.385413681765765, 10.552478721925407, 10.620929426783999, 10.499248910202795, 10.793497533550166, 8.341815893061483, 10.531600056171099, 10.595388698779333, 10.298583145012147, 10.866756917391594, 10.15914777673499, 9.41553281690528, 10.666747547249082, 10.701185588081403, 10.911658371233717, 10.876191619979766, 10.846048214818428, 10.658976551542596, 10.675283426777622, 10.893983189340862, 10.59474659995725, 10.739817494873675, 10.672816414353548, 10.739208208931132, 9.903156659329973, 5.528389821301858, 10.348089931762491, 10.764369918630013, 10.430031187944712, 5.064561576821937, 10.056291087366017, 10.260011066661908, 10.578938331765132, 10.54279521536383, 10.674282986755259, 10.427932380467544, 10.248902873390833, 10.67916955531913, 10.644822696531405, 11.065538019310177, 10.732041131478827, 10.466096427847386, 10.748811138735475, 10.513017935949375, 10.672497814672404, 10.913276057039816, 10.728932640953573, 10.728890178959686, 7.6160221967807145, 10.551099524730057, 10.59674175396743, 10.53637138782671, 10.496667352645213, 10.766732047789187, 10.813544414176413, 10.976997363811543, 10.680611300420495, 10.594703162983663, 10.840776563675307, 10.675599866555851, 10.670833619393397, 10.798070966329425, 10.495261248391923, 5.507264506437786, 10.677823956495194, 10.608693710004282, 10.469676400136226, 10.378586516494263, 10.71004170146098, 10.917930541375846, 10.40817317720681, 10.43098207303894, 10.766303635529425, 10.666886833359156, 10.489543282147698, 10.501006010614569, 10.491316555889243, 10.612576921663798, 10.781847984750154, 10.7259564602035, 10.710107957052719, 10.742295743616827, 10.937841970125064, 10.756468538536122, 7.204390695235773, 10.604427010483953, 10.320437801415965, 10.606190102208416, 10.68126803972494, 10.683335169856303, 10.533688051389223, 10.263654886180118, 10.891682236067505, 6.482393648005127, 10.78999937527226, 10.331437412528182, 10.761936661541048, 10.557129803314702, 10.560826713395139, 10.97457915713247, 10.463923217104572, 10.714363475643383, 10.045537551529343, 10.785336386723966, 10.827902213296536, 10.843275611830544, 10.35433728951143, 10.582301683986417, 10.918351284538474, 10.688707843503789, 10.837864559889853, 10.78272776390675, 7.313046644755242, 10.476995003050153, 10.676512896593062, 10.330021085778874, 10.92632278205168, 10.518911054697996, 10.75771589935712, 10.289559195630885, 10.490153095405663, 10.24417411269764, 10.545148728347955, 10.682222683059857, 10.873245129668149, 10.176693872890322, 10.083580261577794, 10.89949136635793, 10.970446434884582, 10.965801539576045, 10.410166146528383, 10.948981334477772, 10.17084116112538, 10.552659482996717, 10.63182429278653, 10.542730574325674, 9.993668733774872, 10.705251174734437, 10.551018690798077, 10.942530747680438, 10.39924189728429, 10.778851508756993, 10.324049824222618, 11.118462468497151, 10.381650998483968, 10.720346350702393, 10.86062851534425, 10.307060738188698, 10.378091743448191, 10.782345493560962, 10.627584382417547, 10.758121672828961, 10.479159849729136, 10.5205371068305, 6.885269657015602, 10.769190339781918, 10.603720694513253, 10.659271378934084, 8.20223509432511, 9.663060623991468]

path 12
init_u, CI: 1.525344395455896, (1.453678030293739, 1.597010760618053)
losslist: [10.375350977445331, 10.54297581919305, 10.362134887162767, 10.410631981518012, 10.557047797687709, 10.565474414332158, 10.385342432101709, 10.409632108462626, 10.363262230564183, 10.281128323242694, 10.556622611760687, 10.618122505558306, 10.670903431682236, 10.345048947948268, 10.499143431219279, 10.627434936890818, 9.80724901779515, 10.666445022624385, 10.419073264156218, 10.167485176807388, 10.558409768503363, 10.39737097260961, 10.497371024544497, 9.963422343657813, 10.321887652879546, 10.411039727492955, 10.503520743053324, 10.378904581851398, 10.785252663470498, 10.716762590518488, 4.961191730102677, 10.216513402075002, 10.519628478643808, 10.540903834916001, 10.46816670682912, 10.257123700605264, 10.446410902367184, 10.171882419781767, 9.952864967348336, 7.7568929922620375, 10.327309374719462, 10.542095610113556, 10.792952547099857, 10.6374018563374, 10.165276243806984, 10.808564703944294, 9.904483017502509, 8.455864535724539, 9.88883542593132, 10.61086530744028, 10.354779520816408, 10.352342306158988, 10.132070636811957, 10.417901064625925, 10.508371890789999, 10.902912488741698, 10.588949358466552, 10.216979302629719, 9.886724145080734, 10.471818416092315, 10.101428245852919, 10.628062133803029, 9.006847442416051, 10.160309233406826, 10.684432920222221, 10.566382682770369, 6.101004916681294, 8.615503129540153, 10.222621451952014, 10.51362837690638, 10.74767533485789, 9.701276001070575, 10.126310805530997, 10.35476934384221, 10.733794085714838, 10.29575204192791, 10.516052837916801, 10.030249634039718, 10.156027137529303, 10.474364504546845, 10.400089937169971, 10.58509030584652, 10.577372648684133, 10.496891888520798, 10.80566402714517, 10.782479943015549, 10.63431512312991, 10.548932518932583, 10.527038697580686, 10.570557871536199, 10.466680775110921, 10.613072747158263, 10.587263814446137, 10.420322426075016, 10.205976966140161, 10.016131378893125, 10.437047667500496, 10.652648338948943, 10.166312517638447, 10.411476066984191, 10.57678160031876, 8.460485463826801, 10.452408620422002, 10.557932417929157, 10.724602171513196, 3.4575706081018387, 10.543980736718561, 10.329239901047766, 10.539300183346485, 10.428136966185964, 10.515940470413423, 10.357040194294921, 10.343232731203166, 10.6738399492096, 10.586266881650934, 10.72060664095496, 10.517610619645165, 9.30972804180813, 10.170443602927413, 10.548679003274662, 10.514769385593416, 10.503918695618609, 10.069805957382167, 10.4640972480382, 10.47617932065289, 10.619820871424542, 10.28981313784713, 10.6916911221955, 10.403950807565014, 9.763973905863178, 10.174242421688668, 10.466033856149815, 10.29068774932257, 10.119230867764779, 10.327354136511124, 10.367446623315235, 10.659195767057629, 10.52573451154025, 10.540235315838768, 10.389648980719633, 10.740735458824023, 10.325819728066879, 10.3415041350094, 10.30030795815989, 10.7461963154686, 9.93236718176606, 10.64120014259396, 10.563510991761458, 10.871434570242382, 10.348571591104204, 10.506264710754495, 10.510388184441684, 10.725771268766541, 10.301692464409447, 10.556000194539811, 10.563526370923496, 10.541494262765505, 9.916040845721783, 10.637940242008934, 10.573677172528923, 10.328068966182668, 10.801306775802924, 10.656022822288923, 10.210731114825723, 10.127085273979436, 10.577036184630353, 9.99046597481095, 10.57640985457235, 10.455615347732445, 10.594895879110153, 10.567783338029262, 10.390861241153234, 10.700551931394632, 9.965167461395199, 10.26078012066406, 10.56195506549341, 10.492335557012828, 10.24191730006632, 10.65840724571571, 10.327286449528225, 10.83375876343668, 10.613255863707462, 10.538165944317747, 10.380955711927145, 9.16252869809259, 10.680159497440092, 10.800856783184122, 10.405867646222879, 7.2964552060822045, 10.478343700393143, 10.413794236725064, 10.348273605852857, 10.152544729312657, 10.480519494416962, 10.832890667162651, 10.459296777874224, 10.604374580910726, 10.521093437166714, 10.63022355714616, 10.649583258363348, 10.807159324211357, 10.162006791512157, 9.948161788739744, 10.521126984864067, 10.335449231049056, 10.186041342071592, 10.651745005531323, 10.614865831769334, 10.645718761317712, 10.564670060365215, 10.618819237379967, 10.134403698751754, 10.320865065395646, 10.613322026682246, 10.618608960231022, 10.319798812993488, 10.597773783297782, 10.661699504404455, 10.51626143714258, 10.655482582910894, 10.493260652154197, 10.542523304547576, 10.095656824887214, 10.426981305434591, 9.683092264115142, 10.535555354735727, 10.619120681721233, 10.53551256375792, 10.198266478794485, 10.87338173763863, 10.580219731046622, 10.489342417676724, 10.420582248099363, 10.654272341541395, 9.332993987805711, 10.23397127343257, 10.62092257112611, 10.215479549971947, 10.41684784370429, 10.499287835439299, 9.95395585746125, 10.701136804328174, 9.393297194682495, 10.58505587183881, 10.533220919960701, 10.264458408507883, 10.715599720627973, 10.14112873676185, 10.637952301073494, 10.375306940499923, 10.057053510943067, 10.43986352341197, 9.487967413920012, 9.340520097078748, 10.567169686711704, 10.448816892969795, 10.178024449649705, 9.60662524287135, 10.554815646797651, 8.679528633644079, 8.93763108488457, 10.507104611830606, 10.700357482651208, 10.57745084493864, 10.372042658776001, 10.703717865033187, 10.439277673149487, 10.344851444872072, 3.281745235354481, 9.990484147479393, 10.537532195517846, 10.49481103626483, 10.662193550626839, 10.39216723677369, 10.12793514448996, 10.507694322629318, 10.703755216631444, 10.233504331109557, 10.532367024682003, 9.985783802933952, 10.72741723039993, 10.419277988401747, 10.637433201420551, 10.576677770539698, 10.688090966387124, 10.26439443771118, 10.145515784859583, 10.139197392243657, 10.549431854748782, 10.595221361739917, 10.765929720629252, 6.5754750259758445, 10.339716690340781, 10.546220703569482, 10.53730482268133, 10.007396329169872, 10.534188964466821, 9.036257024063822, 10.458524335684922, 10.298221711189612, 10.625339021638297, 10.586299762695543, 10.689890259769966, 6.033028660190062, 10.566905765266721, 10.103620487225369, 10.5741898207201, 10.681229459000024, 10.30382482704512, 10.78955470522938, 10.489031744073811, 9.468000403793095, 9.759670159679965, 10.476401100833789, 10.728573874296476, 9.700711654962374, 10.098710193281665, 10.568010284834187, 10.422700848260966, 10.48299813297923, 10.626856323767763, 10.418661237816154, 10.310471090870065, 10.721697215335523, 10.446442641245062, 10.518735991141524, 10.823855235305238, 10.336301095922892, 10.550722191532396, 10.436084739640844, 10.742294650160002, 10.634792359020253, 10.396579152080507, 10.475704694587971, 10.913336107083493, 10.506877809709536, 10.116447302136198, 9.659794517614175, 10.169309348573583, 10.452799351798005, 10.379141349510654, 10.429193766070197, 10.262772882727331, 10.687624392230743, 10.468323264845813, 10.651289965899325, 10.594497239677334, 10.600512287790405, 10.388944077329866, 10.877662292987171, 10.53080262278463, 10.737701253660335, 10.066877749691718, 10.574620498031612, 10.732700184358832, 9.624892264275253, 10.546767261038392, 9.806658054014852, 10.39678615789813, 10.505656254565276, 8.80522809582956, 10.41294549340911, 10.66474364498413, 10.317441598334502, 10.317950996999189, 10.585635557379158, 10.667694981120455, 10.438691695435947, 10.509983648064386, 10.536640943514866, 9.498046046337011, 10.21709598850206, 9.363780795603969, 10.58673682359247, 10.510826041382298, 10.343929709806998, 10.823128320023123, 10.162403521530058, 9.801153299233407, 10.752359466214129, 10.862666798769082, 8.69392865807731, 10.539790752573333, 10.240595737184767, 10.496707589700984, 10.281514994707146, 10.63940651756571, 10.655660942969805, 10.364443602696484, 10.60661173441764, 10.17339317342023, 10.575970862606908, 10.59635418261302, 9.111996386677935, 10.516226433119368, 10.42024654162515, 10.484590423999355, 10.662513503445291, 10.346841466955604, 10.338453283663933, 10.530441544712474, 10.49853707970351, 10.53727934006561, 10.632466985252623, 11.045822560571432, 10.685575599437534, 10.772522762731757, 10.315903757281326, 10.980017513687251, 10.245134119130334, 10.777491341165163, 10.518375446834355, 10.371742593577283, 10.568435578560216, 10.533909521988324, 10.580618014520512, 10.390924159664076, 10.37128307626762, 10.639080516285865, 7.629832585471575, 10.377707120325821, 10.379823610165321, 10.448021914900888, 10.640529193044165, 10.366462324379448, 10.56762303565747, 8.224073686781972, 10.231078772631035, 10.544141517404922, 10.269387881089921, 10.29375729106567, 10.408323152352665, 10.312249216734129, 10.802624237746201, 10.555914032477382, 10.03718507015057, 10.553232738874398, 10.432120509984086, 10.28753851880942, 9.602736333787268, 9.934492426275687, 10.64273485293649, 10.392374814725295, 10.625488784926352, 10.458117816831043, 10.67448979092277, 10.576445855612755, 8.795334699638456, 10.555631545601853, 10.650303033173724]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.4227788138682822, (1.3562471558748275, 1.489310471861737)
losslist: [10.683332857171836, 10.608077506269927, 10.664688315967297, 10.161027890295502, 10.60925565009915, 10.384594429219442, 10.748774408788815, 10.373259660700821, 6.098313207499936, 10.18611318584042, 10.421306579231485, 10.496506932742726, 10.093373823599078, 10.935319526452918, 10.575074865686991, 10.496086477337332, 7.4020643039561484, 8.613450496625383, 10.814503430321132, 10.455026179587483, 10.54758054913011, 8.657583961581999, 10.388323870119512, 10.647905255861474, 10.684324952806932, 10.575852649718438, 10.571622111176058, 10.678767218393395, 10.145866282125446, 8.858999565225439, 10.533819083109842, 9.076692837709528, 10.346376944169865, 10.336772336786723, 9.69589004175624, 9.874846155741569, 10.19400159876441, 10.750086567168134, 10.762751279055212, 10.596979549881564, 10.740742736752148, 10.530995885498054, 10.455319163453165, 10.253825692077116, 10.762386552107646, 10.595860477207655, 10.688182544551005, 10.553874739907506, 10.92432262698511, 10.957516815481183, 10.522043337501021, 10.870341911376963, 10.912597290527394, 10.483174897069864, 10.84799053062789, 10.276936561714189, 10.309265560228877, 10.374316003214933, 10.788658748905847, 10.928377167705703, 10.709019121792213, 10.589371447521962, 10.488542496657693, 10.732973257946947, 10.721989462114264, 10.420463572951366, 10.348336415625855, 8.796584213112428, 10.733781385921665, 10.73818889124414, 10.35916655375548, 10.167465988800133, 10.612531882914016, 10.748522087073944, 10.019963465132616, 9.926457606069588, 10.830806053110665, 10.66483469965613, 9.780742416521951, 10.528053699978958, 10.746248581128667, 10.452106391635144, 10.505919245399786, 10.488768214672374, 10.60447235753913, 10.440777436428707, 10.944027347285166, 10.794926863243958, 10.290886773473785, 10.93556903791802, 10.551757467552743, 10.812210156517237, 10.467783985275426, 10.706378390103744, 10.880437502749281, 10.389320507207044, 10.817779864661965, 10.874299872308855, 10.490382763753347, 10.583033774743372, 10.75915121340432, 10.389471448130497, 10.470192060693657, 10.824032360891879, 10.977103146310252, 10.615971145295076, 10.454158449290215, 10.773914155363489, 10.499698540990666, 10.46361564893734, 10.778448468188465, 10.690021562209395, 10.784669866765073, 11.00039348506133, 10.402585921528138, 10.558255318561878, 10.495263473400337, 10.40291471969101, 10.757047921577213, 10.555395305468236, 10.771910677658473, 10.82308544627936, 10.403409223674931, 10.46871474522738, 9.408632609603334, 10.705897203056992, 10.7221600869503, 9.498360214518934, 10.529665647026562, 10.920904409585814, 10.504942459157524, 10.491268537686851, 10.324556887607255, 10.385670119536497, 10.505869593062203, 10.640777293450801, 10.346800631350698, 10.648715938980954, 10.488914470492595, 10.586064414726321, 10.670548497105589, 10.623486851174555, 10.605062068778972, 4.319896424846468, 10.617889100019804, 10.517291181557272, 10.401200326594205, 10.461101831769765, 10.772548533259986, 10.484011302948502, 10.481385914004077, 10.723370527333202, 10.552781667699147, 10.664295907678795, 4.638631072280131, 10.705987985716103, 10.695403717043344, 9.959686972570507, 10.512374971776907, 10.517406633747282, 10.432567719665984, 10.234900831548218, 10.67845438495569, 10.601860636217179, 8.363952878551382, 10.42460190327304, 10.619568866656032, 10.432266557860498, 9.415638535987046, 10.242050029343416, 10.57479088663914, 10.694084948847802, 10.45348645246184, 10.902640487959786, 10.311301227785027, 10.553479861426974, 10.625861892687084, 10.786283879245069, 10.819963352924871, 10.6154565930666, 10.647692071554886, 10.631660998600667, 6.903803250862825, 10.83429433331396, 10.65206034236783, 10.901959094941102, 10.548350680047974, 9.78109829621361, 10.72181307024314, 10.691270966774193, 10.802205262923044, 10.217618633431847, 9.402647764154331, 10.580344810464558, 10.910170939915286, 10.481681122044654, 10.71314298409858, 10.481816997188881, 10.556185618775444, 10.064084505941477, 10.71063860009887, 10.69296623724747, 10.380368067815848, 10.287395312192064, 10.18271294314461, 10.489050653925688, 10.293961827173476, 10.468021786808432, 10.416689347693476, 10.710318153162243, 10.369980364926663, 10.7909441412826, 10.867728472576253, 10.372027273288301, 10.150207215769536, 9.908635056523167, 9.323300966385835, 10.6114174135437, 10.58383733654094, 11.133684711269472, 10.72207187911898, 10.586459093660793, 10.562123011229655, 10.009969495103633, 10.563346245890518, 10.689891342572178, 10.52144290104339, 10.301546737818608, 10.854883322084907, 10.740354816834438, 10.488809711677508, 10.392454813166731, 10.6582918014473, 10.782352600683938, 10.994240728944076, 10.805556021045224, 10.666877784433966, 10.472049146157223, 10.433650190122638, 10.419383907396636, 9.378638863750988, 10.182682201302619, 10.67677840359804, 10.764732597871491, 10.906244478298383, 10.651363817581252, 10.602485520712495, 10.470936932369643, 10.526136829602729, 10.399771351173795, 10.58687006900527, 10.668160522787904, 10.638239022800251, 10.851008475480858, 10.114645888078316, 10.43930759295645, 10.692906909305577, 10.644479169645523, 10.322534833897981, 10.724318658286473, 10.641711173821662, 10.661893820815871, 10.912725993348586, 10.901086715597888, 6.787901940449831, 10.60640640254495, 10.587231167179377, 9.891789200577241, 10.263081405191285, 10.479253140638116, 10.607785928537131, 10.676336752246218, 10.658672363150654, 10.628204325352018, 10.617689173366639, 10.664344733674511, 10.378302224411746, 10.459606554366315, 10.565155171066099, 9.320874047320398, 10.664764084303473, 10.326333877747498, 10.107483866886215, 10.069270621556832, 10.547746954548725, 10.789565565140997, 10.31255694628761, 10.482669956994997, 10.765972023634646, 10.706521553200982, 10.848642277581321, 10.696175760674915, 10.402510103426811, 10.492944500086617, 10.679520050534634, 10.576466865042104, 10.81009310685869, 10.432514402148398, 9.434931611549501, 10.84531903005259, 10.542323417510534, 9.831111637064446, 10.089828447836448, 10.631631449064384, 10.422050376146185, 10.942239589361341, 10.096133488135527, 10.24304862130038, 9.479522361391187, 10.629224242433498, 10.41385948773826, 10.613758481136163, 10.906285778742404, 10.88523982095455, 10.483248936052206, 9.802288355007454, 10.67410607265448, 10.841327021863577, 10.936104461770046, 10.342921966746772, 10.71948358041207, 10.274598367278934, 10.56712160987894, 10.577308247864105, 10.605253820228475, 10.532904111036922, 10.356420515705109, 10.326774593956575, 10.717459939316445, 10.804868110471023, 10.77155689186831, 10.95833242948108, 10.385306563620132, 10.05806354854987, 10.641667090937682, 10.254481384622075, 10.884956084336139, 10.774793383773202, 10.55567723274119, 10.723517216294505, 7.140065898968426, 10.504984025694055, 10.448336321246945, 10.014334333838855, 10.716245703938911, 10.758970292435771, 10.704755187560268, 10.553252042249548, 10.588340780613478, 10.643080181832515, 10.620479225792822, 9.855663172957199, 10.264653955665503, 10.319231532701373, 9.780416437515223, 10.649608104545713, 10.629517665293566, 10.535927370606531, 10.52602879738718, 10.6534571600417, 10.838807813408119, 10.568303319257813, 7.6916676444549195, 8.29468209250564, 10.261767005001726, 10.841440417801085, 10.52920349466052, 10.502939765484227, 10.69116117830478, 8.623312244536638, 10.765036024502024, 10.648486190170322, 10.660906450574625, 10.562754949374064, 10.837854397304866, 10.573713882822222, 9.84759247975834, 10.46008419796306, 10.49877420904335, 10.808662778966527, 10.747401930871613, 10.262271830490475, 10.36147994849237, 10.476501574261206, 10.241042519674199, 10.428665761222785, 10.670752145011953, 10.819607927359757, 10.784432760665625, 10.452431342163155, 10.118836304445587, 10.690611136241857, 10.459874338757466, 10.320437305677428, 10.73363763590454, 10.773894809543384, 6.646304704714259, 10.298402801204604, 10.805014879980028, 10.75698002315142, 10.639061644413864, 10.600394213281561, 10.0967745957593, 10.526976479746269, 10.487436814695617, 9.191993431479085, 10.702009884449241, 10.502186061439154, 10.707096265459114, 10.110545000033165, 10.342872513345885, 10.705660235528235, 10.580308949120239, 10.796680110088706, 10.793747850611894, 10.587517061312358, 8.550019946699315, 9.519809952734517, 10.372810555933457, 10.678666389658842, 10.811705272209618, 10.234213597287793, 10.164800200387512, 9.636762200593362, 9.414664594460936, 10.883931180596454, 10.340480427091514, 10.276110326263792, 10.661909501040075, 10.756198751732907, 10.74788876862458, 10.697290720613449, 10.735203438874228, 10.763234591475072, 10.772921821352744, 10.619391361005947, 10.411794962200455, 10.54019707321856, 10.372189716099845, 10.738028983963078, 10.714453160256308, 10.440921455909969, 10.39329424317828, 10.55036217472063, 10.417774632329564, 9.761951794304379, 9.398290069566007, 9.654916298231116, 10.610220796956273, 10.254829513349572]

path 13
init_u, CI: 1.5830781652944257, (1.5049209188995647, 1.6612354116892867)
losslist: [10.845753802227158, 8.17864248617368, 10.656762542816287, 10.506303829042475, 10.768602118944896, 10.68344079639356, 10.569073119409286, 5.687194890074369, 10.078858618250987, 10.501023568826291, 10.58724227553431, 10.359421672102863, 10.208367070882629, 10.642903481139898, 10.461821992373649, 10.343207667184442, 9.985450040147834, 10.859787223519865, 10.445744320407183, 10.596525837084018, 10.575948735135489, 10.50498353458833, 10.041734738695572, 10.5930223169375, 10.156785775096408, 10.668255744171864, 8.71862362079295, 9.910888764107876, 10.624259026900193, 4.977366640352849, 10.490373681433175, 10.421076029761847, 10.819083411863032, 10.724756529810874, 10.376267817616327, 10.626161941278331, 10.579179949491225, 10.691798101608141, 10.29948082210308, 10.453890882660255, 10.371495044279841, 10.335947984277043, 10.505423913197403, 9.938562230193627, 10.571665987739877, 10.467335477741438, 10.663965416388526, 10.510398120005831, 9.63614801220042, 9.943847946596144, 10.501566531258232, 10.807458870258136, 10.075042025420432, 10.09021857939092, 10.402510940957983, 10.570170190490181, 10.397576277894755, 10.481428207725454, 10.50626648618693, 10.603863408089172, 10.146415233366232, 10.330186043434407, 10.562826383965321, 10.307153427332818, 10.79176674128978, 10.411573183767093, 10.261942238358968, 10.222849170373948, 10.639624430534784, 10.155783534601554, 9.835873316494997, 10.326453968522339, 10.396621837653429, 10.713711914242184, 10.67979002571263, 10.64536419252232, 10.531706842417625, 9.21429099242616, 10.54315191971302, 10.716982315830052, 10.272005689166013, 10.304645386732021, 10.125433664972421, 9.98784409393826, 10.68455461272862, 10.641128763116608, 10.032800270021335, 10.763767214380723, 10.484014355627943, 10.349257357263966, 10.644236456185382, 10.515053853531336, 10.593185824854917, 10.874257731441103, 10.37829807547084, 10.082527802602327, 10.696674241975977, 9.966688135206718, 10.000849625841049, 8.834309556924032, 10.626564727322256, 10.431796141308421, 10.396126245814695, 10.583688332762197, 10.554217616696972, 10.056306794366959, 10.403599117167147, 10.38365785038779, 10.517444646363057, 8.957158438684546, 10.459291816054447, 10.596957064777143, 9.847394038932515, 10.392533010854422, 10.594259436956127, 10.415551137199595, 10.457263943987618, 9.72289237632146, 10.739114158791436, 5.463321935569488, 9.89832674759255, 10.579159490347925, 9.335941742312118, 10.0610418910783, 10.551253382240942, 10.73308309114378, 10.66034862319714, 10.246712152212282, 10.509077446477152, 9.722364081462585, 10.633326780008401, 9.013897608064344, 10.39010205289597, 10.501116741843, 10.265772229429855, 9.845560362822345, 9.667924012875694, 10.691833895556718, 10.660246957875689, 9.587935993637318, 10.630677424342265, 10.363111558694184, 10.251658286484119, 10.768324660242836, 10.168464038001924, 10.420930793533959, 10.197330934895097, 10.084093201027624, 10.648497020955688, 10.232878377974696, 10.297309239259363, 10.624413365190987, 10.581910603541663, 10.579236393648191, 9.72237238076371, 10.568042833171841, 10.373232513660225, 9.934038701781382, 9.84310751276901, 10.361719530899357, 10.401352398042407, 10.188310913931836, 9.549950056192623, 10.433787770048188, 9.977322477275763, 10.374367131093086, 10.337284384677762, 10.486229773812001, 10.760115455513136, 10.584687578728348, 10.283590257092289, 10.527242956893765, 9.117639959050022, 0.18830387429995893, 10.514668949838974, 10.425672833276941, 10.637684694779898, 10.675383173053119, 10.37200710145249, 10.791107200379905, 10.303185980714387, 10.339898284986397, 10.340512226479392, 9.991471126536421, 9.78905462914467, 10.460432486772133, 10.372839566957886, 10.331461370558243, 10.454136355587604, 10.286646433135889, 8.654037323304019, 8.214974999280829, 10.669015764129588, 10.142485765246251, 10.544996369558453, 10.547934706098689, 9.634744557113068, 10.4147797500554, 10.235233085724605, 10.186562652642895, 10.618612910630898, 10.315739123921048, 10.74959451939654, 10.014158329049614, 10.58077835793057, 10.63768383352366, 10.421375537381866, 10.486930758448933, 10.17359510063441, 10.496812887745465, 9.63479367818017, 10.330654316233927, 10.148220031094912, 10.427508106667718, 10.80070372721352, 10.630553834179059, 10.307571275471973, 10.165867851925407, 10.600484778518423, 10.616109403345702, 10.136832680625625, 10.189462502494948, 10.052421039169207, 10.582506486118044, 10.363657448991805, 10.655160747186617, 10.084025724939993, 10.486529220846156, 10.041483076065896, 10.050391392146862, 10.582175686734962, 10.89096961244893, 10.368342596473266, 10.730019713373737, 10.51664760546103, 10.429283717313158, 10.500556850049545, 8.441048165369098, 10.393096206864648, 10.464069376024185, 10.625645099101824, 10.537498442707614, 10.383619207130236, 10.625948508635242, 10.524531442851115, 10.172773357649131, 10.44171141715867, 10.635511037920926, 10.295465418468554, 10.52966770000239, 10.472039544208855, 10.431448519419764, 10.510558484403079, 10.538409099640814, 10.665990946414858, 8.954533914852483, 10.509230788885981, 10.471910548689499, 10.594598760942038, 9.984757482066781, 7.561528283618082, 10.59628638405063, 10.484160535495556, 10.661197809439518, 10.42488754217157, 10.213521994118638, 10.126216510863816, 10.230518693608818, 10.607305627223258, 10.600807319049117, 0.19610295895961358, 10.327992891571752, 10.374851006168198, 10.484774122737328, 10.540757466927815, 10.29951767823304, 10.363349074697068, 10.327244589245273, 10.412109176100873, 10.651812562950198, 10.39194598607785, 10.522198825971893, 1.928317779209164, 10.542987050249844, 10.224207443116196, 10.288805691200368, 10.445358282663575, 9.889280526319462, 10.653898682765554, 8.826878985041887, 10.49574030336703, 10.01280348482773, 10.382063700292544, 10.473398073002274, 10.151601694260803, 9.848866402725639, 10.510590630991109, 10.319320131059774, 10.563069280182178, 10.519981482079102, 10.516104143989365, 10.216266195790244, 10.083602364116258, 10.705672923751143, 9.387487593275793, 10.61539288264363, 10.647653158492503, 10.442961626561885, 10.470452207274027, 10.062345953230546, 10.435125871842835, 10.63323108569849, 10.42308681952406, 10.743256450151758, 10.268298515543904, 10.474802963635435, 10.833330231496129, 9.261801528058516, 10.0145547851249, 10.84109463191669, 10.574620239802558, 10.268310984564234, 10.607626903023316, 10.537706369579245, 10.658534019656726, 10.576189284677287, 10.209389712111042, 10.44180000857188, 10.526701884081119, 10.552043393558499, 9.884756358699663, 10.619195413019561, 8.416935096614669, 10.19354867517237, 10.416181682964039, 10.473408308761037, 10.573959131517855, 9.831017465900988, 9.977174809098601, 10.477893717344424, 10.345671020562401, 10.578262049184783, 6.906908751291178, 10.08314978640206, 10.611856640642513, 10.258881546480502, 10.494514747313383, 10.131722905798753, 10.29225812611417, 8.841765239882381, 10.373164510058759, 10.186741323338575, 10.417834264929166, 10.212270410936974, 9.572288436336219, 10.554685095126297, 10.374619951619279, 10.366931339050074, 10.757699343202368, 10.314336230224255, 10.99143422757751, 10.39058431527589, 10.461540435106738, 10.481700072522662, 10.166133065125123, 10.734197403127936, 10.495854116550646, 10.330025110524687, 10.793115868067996, 10.235664339598303, 9.767280347142046, 10.563143542142068, 10.366227706345711, 10.51165901421746, 10.37244207548144, 10.121348482838528, 10.477249160411086, 9.704035553527833, 10.366690189091138, 10.530089865301903, 10.158825198991517, 10.420335553183085, 10.656981241532582, 10.452770017764434, 10.529285631395561, 10.43863631598853, 10.173950528178374, 10.436740544218257, 10.494574249856472, 10.634662819659987, 10.43109206826264, 10.442336994667032, 10.327162060200338, 10.319313148369854, 10.636003751520173, 10.565172974064097, 10.441256187649593, 10.262975606874718, 10.917315885128708, 9.881623403262825, 10.403610491696437, 10.345497363800291, 10.744364127819829, 10.284896741308525, 10.664606100626637, 9.97658578983467, 10.436351551747876, 10.48187895755201, 10.419227982876297, 10.48371880047355, 10.707858671514378, 10.309635745636504, 10.554679840771621, 10.454964815316162, 10.211464936234217, 10.513107186174588, 10.731050425875058, 10.376685162029537, 9.987422965260944, 9.494255357238874, 8.002480001142212, 10.634408746840618, 10.713835316732245, 10.469763268960023, 10.304706687610606, 10.262128683237133, 10.52140463602124, 10.614630909555556, 10.126565658422617, 9.879232927801297, 10.573233700703177, 10.327611276644825, 10.547862252562384, 10.01448227872102, 10.429217510642138, 10.5866740552871, 10.339449531313251, 7.566274783769648, 10.57970415045025, 10.49867686205955, 10.66832766610793, 9.846909672359981, 10.716621706423792, 10.246073262459573, 10.26211494992344, 10.648792051931188, 10.253080500690258, 10.299025317188873, 10.317939867184773, 10.566174744901007, 10.749989900625755, 10.444320879859871, 10.268418892756586, 10.563122931122276, 10.598900037899735, 10.582074209535737, 9.773564289477056, 10.452377610129522, 10.76382380209889, 10.309795661130229, 10.568215746749857, 9.077064981021943, 10.420784721285502, 9.447365898645971, 10.50708956133895, 10.482116185579766, 10.475051819867412, 10.267150749392554, 10.498896595074857, 10.829009706209197, 9.010598632411172, 10.348546325800177, 9.959239455333131, 10.359130850707942, 10.56052376572796, 9.609827580075605, 10.697333852647184, 10.369598421633222, 9.975960419151308, 8.727837009905132, 9.966479036181681, 10.45516472837628, 10.725899762600694, 10.341839603569621, 10.415426776707504, 10.500660829789895, 10.2605468969957, 6.70573424578751, 10.259013877386998, 10.566527071004083, 10.114598221514818, 10.52205211044309, 9.400068285714001, 10.365869889028383, 10.464549191142467, 9.07746584303908, 10.291953959023862, 9.521446309066572, 10.426371492873376, 10.703916530164152, 10.381344057610852, 10.807150517557487, 10.373771591643825, 10.47504994584443, 10.72953473042665, 10.440880621564526, 10.754141577477046, 10.788660624844917, 9.880822250492221, 10.374682111626445, 10.508070272403856, 10.677383729415423, 10.500219581065872, 10.601119361737371, 10.361157488342995, 10.506891983188774, 10.240437178417043, 10.879364670365208, 10.62141980397482, 10.57938521010761, 10.593333183413602, 10.743121968899315, 10.461297576761872, 10.478529415914076, 10.492172181937962, 10.326506743850345, 10.08512440130565, 10.599653888256416, 10.555205283872828, 10.518998849423692, 10.264953468455357, 10.15589330927627, 10.536750983672434, 10.487562148802423, 10.478566361987033, 10.247338801640751, 10.471004861626, 10.702995749171667, 10.654014338166533, 10.432045009071638, 10.247531584264731, 9.665506277569568, 10.28126282305661, 10.757061194320968, 9.984786015341296, 10.720957257959961, 10.73243373237039, 9.826527161417005, 10.730450187997189, 9.96097134597626]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.4226324882688086, (1.3539410711811293, 1.491323905356488)
losslist: [10.299589549860023, 10.278128176685858, 10.558830501279946, 10.444286306319542, 10.677234166915904, 10.457383896357085, 10.48891761739722, 10.790091946989941, 10.472852436550099, 10.465873148946184, 10.574463975678524, 8.534673909854465, 5.729756926971316, 10.52695403791936, 10.597882879389507, 10.46620354056923, 10.596395956266804, 10.578371296606292, 10.510344730792431, 10.801035619117572, 10.737335670575792, 10.413794931209848, 10.664919134902414, 10.553578084327253, 10.719121452360513, 10.632213047163166, 10.70961930999519, 10.57486668282156, 10.429938666511582, 10.532318838206933, 10.835166156748786, 10.609656224873454, 10.550537702545572, 10.56856722819627, 10.205638563072597, 10.529326352572852, 9.727121649963605, 10.695750047079848, 10.613339594906549, 10.578278738887235, 10.155719252538093, 10.594890607731063, 9.828154683400317, 10.147057458232554, 10.534847750973023, 10.497724746732139, 10.433276162889596, 10.658532740843958, 10.386230603691274, 10.493376350148262, 10.706131221778321, 10.412814887713553, 10.26449112224846, 10.684197917774318, 10.629727740810365, 10.442115935946802, 10.400890773871144, 10.399985174879092, 10.637671020497931, 10.674246505093448, 10.137143253990288, 10.812985579430734, 10.320204297203455, 10.660292706055017, 9.912610488757219, 10.200741291765747, 10.346526536150956, 10.376285140464146, 9.411533705017034, 10.601372355455334, 5.418492827974835, 10.640740489885834, 10.385786230400228, 11.02925406472158, 9.599401784905279, 10.039952492569462, 10.69327271566229, 10.45874792157518, 10.665231230169395, 10.896038614941336, 10.414464415921147, 10.586389170222436, 10.538227932336863, 10.567010350030307, 10.446282099915416, 10.61864229237211, 10.456879803731033, 10.529753168320672, 10.656069893981176, 9.536750026340671, 10.991805245641633, 10.679368288928519, 10.509181609978356, 10.259362992515769, 10.609290754404187, 10.498489043503525, 10.451430120349603, 9.907397338689366, 10.384554735184842, 10.241506464862471, 10.510799539878859, 10.628717785026906, 10.544258191555333, 10.403081306245038, 10.756479614618518, 10.341851654685371, 10.561658293164243, 8.618753546324404, 10.68356585158238, 10.155326676153932, 10.847855291325548, 10.557339815900539, 10.604866603489429, 10.73668329370861, 10.570049856235277, 10.577730802447059, 10.328257094213207, 10.116585341561258, 10.594934580781034, 10.62417978835718, 10.76658146748169, 10.65339940632948, 10.527013310341738, 10.75219570565606, 10.361316225524298, 10.523792856746251, 10.62253361478158, 10.476976848996632, 10.620879626765475, 10.571896187268399, 10.651483384350131, 10.295837192850401, 10.379009780937238, 10.448815967296136, 10.762426453877437, 10.230639165243662, 10.579206593045122, 10.545296516731728, 10.180471942173758, 10.56743609835914, 9.591754357623332, 10.675569795946037, 10.46769098011024, 10.7791677508453, 10.731701650006674, 10.77690449130696, 10.627136398394324, 8.660786754806972, 10.171084106488781, 10.633858169987489, 10.680275113833874, 10.769013076921864, 9.740811178126773, 10.760170321742498, 10.505006175882595, 10.420473283056607, 10.757796146788499, 10.566767546558728, 10.729997035780068, 10.635678481275598, 10.64078668985791, 10.435655528632688, 10.599456960045652, 10.420469940195886, 10.783641666517305, 10.145400992789336, 10.376236946753563, 10.502552504050872, 10.50102811972339, 10.251421436738447, 10.740097289145128, 10.64975410745999, 10.801358256158485, 10.730177122953728, 10.782450485298, 10.657298698648614, 10.415619601662323, 10.58978777760948, 10.669407689182586, 10.830266924948077, 10.295591324342722, 10.27230515689274, 9.968525207395826, 10.357544997695399, 10.619570041544602, 10.72895368226662, 10.534468539319194, 10.349878045881288, 10.670824560194403, 10.57665601485153, 9.916845208194202, 10.868027998736123, 10.482978756005782, 10.645467284744244, 10.2805892331603, 9.655765410057047, 10.280727630342568, 10.36498066577628, 10.565670492796768, 10.36751023572602, 9.943294819110985, 10.49088234132918, 10.40280847621079, 10.631289062225688, 10.49049359360635, 10.203085842246795, 10.631256721904608, 10.808942612377486, 10.595826155026916, 10.543993157243628, 10.772835581098274, 10.918619156361803, 10.60770755035089, 10.434727666154231, 6.26016356315851, 10.464041962428826, 10.743126480927836, 10.641896547240208, 10.190227646440729, 10.319799336894368, 9.875265479213953, 9.693274069443657, 10.683558025275966, 10.539826817259776, 10.31705392285149, 10.519154736973157, 10.612737079723368, 10.667274774722781, 10.70323850758364, 10.069753339345858, 10.269018570710035, 10.75408489562739, 10.255213853128414, 10.45785737253148, 10.581283057642556, 10.88511512685569, 10.516530992683252, 10.505056879564915, 10.282951567394214, 10.591383772795107, 10.523022486803576, 10.802599057525876, 9.927389082314358, 10.440510004114556, 10.675502528698832, 10.531102462423748, 9.479160972078107, 10.547610272567237, 10.551980897782794, 10.570773096826679, 10.54438414276837, 10.462021006631087, 10.62932833101234, 10.675760309156281, 10.408190044816246, 10.250150254002678, 10.597557410615842, 10.565843313039071, 10.65289013113159, 10.517236827822984, 10.303271552217984, 10.554579912766181, 10.499521101461943, 10.626223290850126, 10.629980666161531, 10.505632841186957, 10.273261011091803, 10.71174560819374, 10.728359462867266, 10.375189365710492, 10.573327654609669, 2.5635124479996145, 10.639114586129647, 10.635563195234129, 10.568566353463268, 10.073691434836254, 10.428490932094377, 10.642565199255754, 10.673456262473243, 10.403645978584837, 10.615637210973603, 9.193309995414348, 10.540108453125194, 10.60432066181822, 10.537745134397396, 10.245680936782243, 10.631576843242783, 10.488499239791341, 10.530932599588377, 8.24561480765437, 10.483090569850312, 10.567035830405159, 9.855543079369655, 10.605167976916208, 10.880833179695758, 10.399825423770928, 10.693929178828329, 10.553321373556907, 10.640127090072669, 10.371394544664188, 10.434350423608072, 10.190635188684418, 10.723367846565955, 10.661749138929979, 10.633642085152886, 10.642326611960819, 10.684421125451014, 10.968643896297065, 9.101896850984792, 10.593682859199964, 10.892503930151724, 10.465436592733418, 10.626742549328341, 10.404821853411766, 10.391546060490489, 10.420878605990158, 8.285569989701628, 10.639666745023487, 10.522087665148893, 10.650729720043733, 10.603776063045277, 10.599838770972609, 10.672415204428216, 10.264684944251623, 10.391224329312053, 10.677536185860268, 10.706075961857133, 10.630095396397847, 10.397406134265381, 10.86325742406959, 10.3443971030464, 10.727786478758878, 10.59836138682799, 10.565506143320084, 10.519417739983838, 10.685069139109197, 10.592224884026662, 10.558603705650253, 10.699022129971238, 10.556972163904488, 10.677843483537458, 10.466731046777907, 10.496692528874624, 10.421472110516143, 10.418173495393889, 10.34408349910497, 10.443996925366191, 10.691640357553998, 10.420880188500075, 10.377294699588681, 10.719412846364971, 10.837830910929009, 10.716238339206294, 10.634459090530274, 10.45698234984242, 10.681405901775161, 10.63826306095067, 10.019066682529768, 10.463745743052218, 10.594910952404335, 10.343952278702517, 10.749295975695551, 11.098707763406448, 10.512883064723807, 10.457358737677321, 10.706543042919408, 10.421052202871648, 10.60132377787701, 10.609319976034064, 9.688225688559998, 10.638517087435435, 10.135792357386272, 10.486596679364018, 10.565787205657486, 10.084767017295597, 9.537252334084073, 10.7070449588476, 10.407379647821976, 9.291173431864204, 10.729081679193081, 9.009705882004074, 10.68118532515304, 10.600216427921742, 10.409085461074433, 10.757390048899461, 10.38708944236085, 10.605172189661499, 10.518026155925996, 10.423833471547265, 10.657604663852807, 7.45098864463922, 10.54063848494241, 10.50057062139768, 10.198905552992924, 10.647405574894945, 10.251942676949573, 10.329829930533322, 7.619248355595577, 10.585259384927427, 10.689423988960494]

path 14
init_u, CI: 1.7260606756595127, (1.6415468292949935, 1.810574522024032)
losslist: [10.353214894644976, 10.205943164615345, 10.489685473749985, 9.485275349651566, 10.346802771473284, 10.623960280851088, 7.955597690854633, 7.675560521533029, 10.25789391645504, 10.269642384566895, 10.436090592359992, 10.384459544403951, 10.127587511711226, 10.747333025582577, 10.312772905591453, 10.513834027829162, 9.724182475092556, 10.248380821528993, 10.259217710022256, 10.556612615752456, 10.311932952750272, 10.16015748236558, 10.423958335212953, 10.49551360693507, 10.549403595031066, 9.939065218680087, 10.123491306082814, 10.27944381240391, 10.010090900092486, 10.194978246815067, 10.456230533541184, 10.452373008491323, 10.713350692558043, 10.170808925935095, 10.329079500851362, 10.527545648147191, 10.208931202355108, 10.28030299230013, 7.400608812912324, 10.08955870481734, 10.244221575925135, 10.271372914593115, 10.320692062636692, 10.033959482355288, 9.710010429700954, 10.20062405946635, 10.635530009666756, 10.510620996421695, 10.665076055177371, 10.495656656154848, 10.351895111820001, 9.312639503989713, 10.384217620507028, 10.519232510438059, 9.509078018172747, 10.565232348480636, 10.056809019812647, 9.949066591263685, 10.137931392235744, 10.231401049313527, 10.536716840841326, 10.521680653168499, 9.94039269441062, 10.317679093503443, 10.645892943379568, 9.936948782362265, 10.6188743369135, 10.396857271159577, 10.059476911903042, 10.153331956337743, 10.10905252070986, 6.873482632794069, 10.461992702196953, 10.031296738208392, 10.314653980223701, 8.488610780576083, 10.312549788170127, 10.287826432712373, 10.272521449183255, 9.857475434664606, 10.253273899001144, 10.41313011029969, 10.107442413479102, 10.521397541054379, 10.226465457097532, 10.493038977368542, 8.28896537060019, 9.921958062161748, 8.081482769357368, 10.428894615291066, 9.318268538338442, 9.960441104377185, 10.255507328761166, 10.348991355135892, 10.479459681132651, 10.439786596316864, 10.55572261576841, 10.173615310397498, 10.121101352961135, 10.229963329817025, 10.281543388775269, 10.274583991137684, 9.685685790054762, 10.500433949437348, 10.302023508628741, 10.275954817189648, 9.790505446486822, 10.330589159773524, 9.901961782022882, 10.557458964344677, 10.070027757213161, 10.18414527545026, 10.401255734784765, 10.247523340166346, 1.6083960859531865, 10.163148683028645, 10.595724003018791, 10.575827589690272, 10.453912166734987, 10.226727660049045, 10.36092998028843, 9.380162507714056, 10.559651478951823, 10.203259058429907, 10.366258947151978, 9.551461605701329, 10.418767234938423, 10.314852865009431, 7.395689873332606, 10.660577479429008, 10.41396334215456, 10.40500388275338, 10.643162437677947, 9.945585725164365, 9.957684371712114, 10.21134879448037, 10.363016315303973, 9.925790792860438, 10.37805422601517, 10.394179690292802, 10.468418447734273, 10.542569994773602, 10.27836160346578, 9.693095725208824, 10.351061217387326, 10.139054756765743, 10.223906421587813, 10.309920498367534, 10.470835981421871, 10.569206581075766, 10.083111272720494, 10.292664866691396, 10.182359018095044, 10.397798195225302, 10.296223055953666, 10.567774886835226, 10.403177345031638, 10.495966170991343, 10.150509873949623, 9.565102805786355, 8.963095663599248, 10.282975783036838, 9.859836921018204, 10.48277875778346, 5.103520893688851, 10.282742628975276, 10.319783400965271, 10.43576514636413, 10.359491415711618, 10.577485832310245, 10.066730533943991, 10.495967300989255, 10.49829088166446, 10.393583766329556, 10.609397260441726, 10.330064025748474, 9.74621231129639, 10.118121228011335, 10.432657039831557, 9.127926012962016, 10.261092870851181, 10.315099961462867, 10.21723339375861, 9.126258213410464, 10.494757099753391, 10.289580250021288, 9.41349192387852, 10.378376221595179, 10.041935679942922, 8.815770412764891, 9.164060173066519, 10.246777281364443, 10.322639538285054, 10.321579983651173, 10.48690465007248, 10.209187749496202, 10.377830935164148, 10.098588728083135, 10.51551128653431, 9.694660451776203, 10.225942979427543, 10.159470526379023, 10.467740189199262, 10.489358954717515, 10.093366770568085, 10.336648384654913, 9.941420550170985, 10.40743909608967, 10.49081254338436, 10.376807552020617, 10.028076495123235, 9.989806410909523, 10.4574674080301, 10.385867006387382, 10.506683901962214, 10.25377069983603, 10.244234683776185, 10.661705676280674, 10.066930572120965, 10.558169017991045, 10.11663750051102, 3.6810167567256142, 10.746632934906973, 10.422572327804984, 10.779999931129494, 10.367239773211855, 10.43383585243583, 10.248677829733856, 10.428489431761312, 10.456542245128825, 10.462268510805714, 10.37693096378357, 10.28580082894212, 10.53616731085613, 10.308158035357149, 10.316708454606676, 10.480567418012264, 9.324944327576583, 10.27353212490879, 10.000179996499615, 10.780081051712088, 10.286287383417339, 10.375756509467683, 10.653478612821672, 9.924829808545324, 10.480371749854042, 10.464399909105175, 10.406326282342638, 9.725850961770838, 10.293479109072909, 8.796676743705302, 9.237792652186206, 10.479313092685794, 10.12976787458542, 10.248915470919055, 10.117586813605508, 10.348255802105292, 10.561546271346627, 9.532218597895456, 9.878717598747215, 10.254819711866666, 10.5258045446839, 10.502609086759696, 10.41303195009957, 9.133634647257356, 10.392451988533384, 10.665588799659607, 10.444471798404377, 10.339412488987753, 9.205773005452896, 10.210483537458492, 10.40408037317014, 10.582095707090797, 10.379000617579582, 10.05076820416084, 10.58995793192048, 10.291253200510514, 10.503902866256038, 10.408237963511386, 10.221103108027116, 10.130869284415525, 10.498736963955862, 10.336495498798813, 10.301831038198214, 9.965605804764056, 10.433222622473236, 10.345889159889913, 10.490546544725461, 10.355938533371816, 10.467384070496855, 10.594532001338083, 10.243580444648325, 10.11522473495366, 10.613417168971068, 10.42955354681165, 10.363405760805378, 10.09141898141271, 9.971750939079747, 10.6253281964778, 10.047384371803954, 10.440317393092272, 10.713708610750794, 10.002693512888678, 10.179405441112117, 10.333775279662309, 9.87020530137045, 10.780112049007688, 6.612839474520656, 8.85140248925839, 10.415347150593657, 6.909934932022621, 10.608080927373113, 10.421695659115016, 10.545971569840598, 10.431583049277181, 7.470668880916556, 10.465989568543767, 10.452000569576887, 10.171146994987739, 10.554495913790111, 10.398357309959486, 10.28503050321765, 10.21956131873402, 10.215176153235804, 10.455858637656709, 10.133316298341748, 10.203803370932095, 10.290621574445062, 8.46156104460867, 10.149703552386958, 9.553317151432417, 10.318443058301318, 8.225772747672972, 10.275351000201155, 10.524397103457085, 10.281756619600955, 10.472911675067559, 10.078877091572716, 10.08750587979202, 10.174988928173763, 9.96977852981116, 10.41010063334697, 10.155229786985759, 10.35566151623627, 8.510212782722297, 10.31941664203828, 10.427342572968456, 10.550379486504983, 10.377624376191324, 9.654792459629759, 10.41947790615807, 10.660424467226214, 10.280830792212846, 10.149691543819976, 9.870619942657143, 9.854551550286336, 9.433825469328442, 10.533215919015607, 10.452952476382624, 10.540315574453636, 8.875891197274907, 10.082264182968897, 10.453076911830111, 10.562961850208252, 10.142905191803406, 10.314992350576759, 10.649802850000052, 10.414250798187831, 10.101953347467877, 10.537757878672867, 10.391263063472596, 10.162422533188696, 10.451729446441842, 10.394120906440493, 10.324079830702926, 8.989486691121217, 10.58348407083191, 9.673930194536908, 10.183472850752633, 10.320419476938522, 9.79941099379731, 10.48779237248433, 10.100652895399419, 9.98299845618758, 10.32610750030959, 10.363291815550344, 10.160400994121124, 7.0568552365550685, 10.532181885777128, 10.427841311429452, 10.213198523610075, 10.339317796744872, 10.229988784815834, 10.43453170162809, 6.718777478300936, 9.932488825165487, 10.06023546697531, 10.654099716273308, 10.501981222815534, 10.44884709726657]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.5490896524051845, (1.4745067541683117, 1.6236725506420573)
losslist: [10.826367659240244, 9.950767942809648, 10.499210230133162, 10.440562101714905, 10.506649285445173, 10.46344171172917, 10.398385149730984, 10.427382686065048, 10.47716129791702, 9.677451383853457, 10.3896644939547, 10.272439311695166, 10.5035113601203, 8.71744195106333, 10.629002894945662, 9.20112874110138, 9.86881643660543, 10.338230835645495, 10.395691038530929, 10.459520681763305, 10.387816861680689, 10.692439234662084, 10.532970700645295, 10.375100178582892, 10.481701222476191, 9.84595344972125, 10.682412073839636, 10.00685719323239, 10.619915526429422, 10.58811949892659, 10.327004735372547, 10.607692523071616, 10.361605367933437, 9.609117961366124, 10.59516969981641, 10.239792450517582, 10.534850513594916, 10.508237053253144, 10.79844551153672, 10.786895170911606, 10.515628961209467, 9.926729835586494, 10.588671922536019, 10.877501538086367, 10.298483035333382, 10.377839910797064, 10.408826956120148, 10.665656083138657, 10.612061695739019, 8.56238619732857, 10.468002380459955, 10.52601918867478, 6.90735003000348, 5.307485884941698, 10.339330480274086, 10.529487058386188, 10.590760873290021, 10.437008256960613, 10.285570113817062, 10.148911399350894, 10.259465154810265, 10.369278978310499, 10.61760722792759, 10.428826246691001, 10.50089810456346, 10.099050936881106, 10.59893446974299, 10.424122599414801, 10.430515051316648, 10.547983668010756, 10.13472547006769, 10.329615382881236, 10.16200160606805, 10.214017572345675, 10.139511749034009, 10.283701359817313, 10.456499036148788, 10.5141176098204, 9.825750153116672, 8.328782095322293, 10.73202859308224, 10.674454032658158, 10.147251928843556, 10.219531855529207, 10.57429156924551, 10.377016105330444, 10.591192303759703, 10.912200925055597, 10.482944323680554, 10.485643382140937, 10.572999952155946, 10.707476849019201, 10.308917296050316, 10.570819165831972, 10.554551288958216, 10.614867957252594, 10.666977362035105, 10.383769540491123, 9.466799182566577, 10.206683379302127, 8.650641183740964, 9.371108191855823, 10.637286766900157, 10.348536831916402, 10.535305699634677, 10.457883052302233, 10.76291655133698, 10.192137356839764, 10.63951058419484, 10.586377509483745, 10.528277263224874, 10.485393669059206, 10.185482738800106, 10.473442527738259, 10.523569619055978, 10.315784671264323, 10.535705558230907, 10.551561340910318, 10.54263530581437, 10.385656156718035, 10.440212038027514, 10.732576924864016, 10.55407045044457, 10.441949608409125, 10.562884142712097, 10.44107824286692, 10.327875170389529, 10.795132288122018, 10.434184946892067, 10.616456770309853, 10.257143974319224, 10.681054745417931, 10.214766821577896, 10.520087635729869, 10.472926410117294, 8.99085972252047, 10.364152383778796, 10.378218414775942, 6.876036282313435, 10.603122964707218, 4.702854522974307, 10.492364279741253, 9.939745052681422, 10.475908265258022, 10.613243903761798, 10.413065359912842, 10.211261439892787, 10.440310768963576, 9.934159563926006, 9.637034268155066, 10.318213238976275, 10.271910096439118, 10.066546764347672, 10.320509631198968, 10.274404822259536, 10.482367065881908, 10.603079096369221, 10.440593217022922, 10.478748740920853, 10.402310215363007, 10.704330807701389, 10.479596775082292, 10.16093487646947, 10.531552316829634, 9.685869294491699, 9.99872604747517, 10.414178960848494, 10.582513182079131, 10.461111908625998, 10.437000497060506, 10.170654176691722, 10.440661613554392, 10.533954694229516, 10.493740512700805, 10.225866700601127, 10.598740667567847, 10.435448591416627, 10.851131884325465, 10.498513438522416, 10.640004435316108, 10.472740745546028, 10.545639090170102, 10.779913893389871, 10.470993147190358, 10.498702491645405, 10.049722425633735, 10.370239441525383, 10.567453564885867, 10.473853490311305, 10.541429193793112, 10.649992280931857, 10.202865397345251, 10.452163455160616, 9.61136463445749, 10.596176398843888, 10.84030570530323, 9.655461740263378, 10.728390565516547, 10.599492550351036, 10.701114335747842, 10.247453243886687, 8.996219692653314, 8.863243447061398, 10.553114595268852, 10.497495781025528, 10.804590240489638, 10.372154722239149, 10.304348768067682, 10.260873593506078, 10.666189049255067, 10.415308383369347, 10.467263239101268, 10.54276952200036, 9.81382591908144, 10.170291520012013, 9.147659948512656, 9.09293852503558, 10.497410335280213, 10.57866665125154, 10.492686376794936, 10.631935961298467, 10.608950400921474, 10.55097159712646, 10.531002001668123, 10.242839497683793, 10.696060279208758, 10.22189629944352, 10.344675532895753, 10.31078892157598, 10.8566021111985, 10.471406974599114, 10.290913541104393, 8.400368320787194, 10.73947237513205, 8.950740380749021, 10.84785243701156, 10.307714206594088, 10.251793203530136, 10.366494398958714, 10.246290372831249, 10.395000944991311, 10.313182770586922, 10.74852254611653, 10.637215635225665, 9.884950474509672, 10.446769248981491, 10.057734709358158, 10.450908953538663, 10.33594892629495, 9.970967829015896, 10.117327882310956, 10.370273545715452, 9.94998782524746, 9.784420712592684, 10.567289444324924, 10.488565192859527, 10.175615158917912, 10.18529372166656, 10.623997847436852, 10.230603815831659, 10.585928369281243, 10.473125951640123, 9.89508706620895, 10.45013495200686, 10.354426033258408, 4.9882248100392435, 10.278524210060963, 10.537789539701084, 10.581487811484376, 10.593267066592837, 10.395230876557187, 10.430003882474384, 10.411785157904319, 10.395705882675387, 10.610503781716902, 10.485588762152192, 10.441029194262653, 10.736797858330391, 9.449914218984365, 8.355198836177706, 10.55095447360504, 10.415314750965347, 10.52863784561934, 10.518385294225146, 10.448505794356965, 10.459382702400895, 10.568900982839962, 10.821018007201761, 10.251231173683841, 10.370304936692834, 10.247154724477339, 10.516015190055624, 10.477239121786152, 10.69443830359672, 9.550252413268138, 10.634954114887895, 9.619730424326988, 10.324049055720293, 10.604593573224546, 10.663038488733049, 10.462910094831562, 10.508128475468801, 10.46450153639274, 10.648723930567398, 9.080459235765199, 9.967772102033766, 9.794639116061475, 10.43852965249705, 10.775327245035738, 10.156577354412498, 10.562509385651587, 10.26852014812941, 10.372761396120762, 10.57842603262779, 10.110604034967844, 10.417088038321287, 9.848169168626912, 10.499414650992932, 10.567763797410388, 10.158726603493184, 10.566185246451193, 10.578791046329256, 9.911103862654027, 10.509215497969752, 10.440451377690874, 10.62100118297607, 10.43224581558387, 10.569283796494238, 10.356472561196503, 10.297391930300028, 10.528163921957612, 10.429842478988924, 10.46902162777034, 10.34373659348255, 10.644041806212066, 10.457785062214024, 10.43816756821708, 10.686215742344721, 9.888594925754646, 10.30602209139801, 8.250880418544241, 10.589083909709132, 8.040796115609723, 10.862126902440828, 10.312472976753632, 10.539512382415174, 10.385681385316268, 10.61364791017236, 10.727067538058717, 10.748258934275755]

path 15
init_u, CI: 1.4294400608504034, (1.3602820693550157, 1.4985980523457911)
losslist: [10.079648283680287, 10.546397366577368, 10.66235145470789, 10.639072928971812, 10.682259292769254, 7.547885877810657, 9.62004552755584, 10.500211192437565, 10.69791965306675, 10.489088223275015, 10.617557479187676, 10.633738479214866, 10.56141540882526, 10.418341364306418, 10.852706776553033, 10.64124189923991, 10.486671366723694, 10.83186873455694, 9.86062143371239, 10.63580061503031, 10.519989497393357, 10.424831899951297, 10.636451006837245, 10.394574298793852, 10.635345524967509, 10.532129008256767, 10.58025670964692, 10.190230897985991, 10.177030813813586, 10.545010307915952, 9.963140083978622, 10.827868261775562, 10.548716226427016, 10.462271654753383, 10.31167014753769, 10.781916685058858, 10.50754496269037, 10.215126821600215, 10.457063201627498, 10.544259022844892, 10.154179692332221, 10.242501465206802, 10.411444379234322, 10.621303569146248, 10.641725298472108, 10.591982632656295, 10.698890065047811, 10.354078198289276, 9.385291735711487, 10.53167379907329, 10.53018836568374, 10.336349602936032, 10.750313862190852, 10.138387143850425, 10.44509182984007, 10.77117288691063, 10.638901374765554, 10.743646648277384, 9.458652548206194, 10.463487944284802, 10.399382477320584, 10.692175294638622, 10.568658355279377, 10.487829230332231, 8.185300799749388, 10.173086685981959, 10.556981070018814, 10.575160669466753, 10.386113615544504, 10.803883704779711, 10.469238850754314, 10.621242158982179, 10.156774379278552, 10.484194830539806, 10.65605369862926, 10.679677687146814, 10.377412007326718, 10.432495980396236, 10.491670135602178, 10.511199206378157, 10.27790638795266, 10.443667275269823, 10.287831016170525, 10.517939175853565, 10.755592378932437, 10.481664123086803, 10.378625242179108, 10.460417331185669, 10.427720338201638, 10.67126358134783, 10.600423075782926, 10.435089950211761, 9.601381779587392, 10.485815858758158, 10.607143233811499, 10.641566884839927, 9.94221523829759, 8.672096514720897, 10.385033768694917, 10.505615515447694, 8.457024566276292, 10.446836092817259, 10.10580114350155, 10.533072611848475, 10.810975848609315, 10.72247710289383, 10.155765188803894, 10.54498706415385, 10.475701658435755, 10.21245920706523, 10.743507188197746, 9.882850845639416, 10.571232195211746, 10.07890628981584, 10.68152096148702, 10.511384482750115, 9.509815371298812, 10.565186404270111, 10.350466184620839, 10.640366079806483, 10.885107226135045, 10.678717141179526, 10.464406750357261, 10.842616985813862, 10.849450974158698, 10.623982800943482, 9.614842691950154, 10.638427401602915, 10.264082249598177, 10.710998719106856, 10.528655139465746, 9.788740675869011, 9.967457939723115, 10.571524389677544, 10.709089661966471, 10.459766483978038, 10.930869398602347, 10.967867024627784, 10.599386491677347, 10.563088566121271, 10.747095404904394, 10.967309993704685, 10.484209518155, 10.343386841981305, 10.574168760636322, 10.228313019719774, 10.673013226570887, 10.584100648051022, 9.621938960892663, 10.53252561666151, 10.257331435886758, 8.36320399283345, 10.800722012406275, 10.34965606482968, 10.655063570104664, 10.795653927294062, 10.379877177418205, 10.753817485848595, 10.514788484642894, 10.54669067596929, 10.829577097047872, 10.795586503890302, 10.446203951581344, 10.689516390152464, 10.544317025453797, 10.551675083531801, 10.052310612702442, 10.675986853640616, 10.3122200105614, 10.07145442772628, 10.427771237597529, 11.047804847442555, 10.583543388167842, 10.657920021475654, 10.63862043417341, 10.690187570460076, 10.289590376629397, 10.344250745239123, 10.724416073568221, 9.412418077490287, 10.319865639955664, 10.045710100507236, 9.992279147839733, 10.396737773560117, 10.734409552760349, 10.565174339481683, 10.323254602194844, 10.459683379412036, 7.933662797732483, 9.881640377264285, 10.565645051830302, 10.794107509506958, 10.552276012362736, 10.392810297035393, 10.20747375609299, 10.583607130221587, 10.030956598479372, 9.458500451185984, 10.15149413697038, 10.452278792815907]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.4107884525634784, (1.3421672189217553, 1.4794096862052015)
losslist: [10.710572049451594, 10.634105850783257, 10.482888511921956, 10.28744646402291, 10.645240358390108, 10.740275966433053, 10.63483428697619, 10.702257768932807, 10.622019034384204, 10.397299740593258, 10.764539344791258, 10.66642486615641, 10.621187213457954, 10.648334647258528, 10.521621613583621, 10.63863741542708, 10.98141334891876, 8.6077117414309, 10.520547029714091, 10.454433800442287, 10.56083724740572, 10.49589024234092, 10.680716888811865, 10.365511733151024, 10.580530433610393, 10.509442757167163, 10.693943698014417, 10.568257654809347, 10.76601511862712, 10.412050429716258, 10.586432551368674, 9.525342266844474, 10.659398570625664, 10.579865432588079, 10.347721104324709, 10.337463571710838, 10.53637885964527, 10.630549235494732, 10.363800598241093, 10.289730733542646, 10.374159637753197, 10.394407020335736, 10.415941083208388, 10.803721149141264, 10.668371797778194, 10.728859342497106, 6.4682142865350745, 10.532329112957342, 10.620618376778921, 10.614210852882323, 10.571585452919365, 10.476417391088681, 10.63861669108424, 10.025616269986624, 10.562067191682967, 10.554328054425877, 10.621772753788733, 10.732960672345493, 10.141269130378117, 10.510074720442246, 10.524911573898837, 9.518922432606175, 10.415247027871336, 10.706178650764521, 10.283879739647253, 10.586987517985005, 10.539122681044692, 10.11062222302701, 10.104372470960007, 10.702186474388629, 10.322935965682635, 10.558986723500686, 9.800175724739182, 10.671944387535236, 10.295278460396947, 3.5946605853667886, 10.586878517104566, 10.562800595070504, 10.415240102837094, 10.826649913114666, 10.208985589821175, 10.58067745696358, 10.3790030531536, 10.61220465192907, 10.0208379728785, 10.747640799351325, 10.802416973174081, 10.442138359815086, 10.130337442703444, 10.672939680475176, 10.831067920864841, 10.386529374102896, 10.654941312120759, 7.696144190090807, 10.404338027957468, 10.504173856242671, 10.342194146048561, 10.646602287225782, 10.592618724524122, 10.176408293775722, 10.587320900964247, 10.751033292628367, 10.491347731964277, 10.508940362379082, 10.693897315718417, 10.287513846604174, 10.585232815838383, 10.526261591949911, 10.40016909040505, 10.599865538034912, 10.74282580757998, 9.22618973111473, 10.627579293925876, 10.559559444972395, 9.199447752107657, 10.67632382810166, 10.610200630518994, 10.406852094838515, 10.315729778876717, 10.662431521999899, 10.634260930415603, 10.715847757300375, 10.746695389068927, 10.707675376713956, 10.64839923858844, 10.802135444074931, 10.651566092625671, 10.49373049396601, 10.781472707743939, 10.532516059712933, 10.517262555352158, 10.420281587845672, 10.726325834159663, 10.617791252001528, 6.836121548313072, 10.338912764412013, 10.871370104109575, 10.223430789422393, 10.539808932735035, 10.734909824433657, 10.640034571420523, 10.470988202624563, 10.560978047216079, 10.753407183788287, 10.631242732542848, 10.555086172339402, 10.466342553065221, 10.53219793591899, 10.614334528631272, 10.482297722673243, 10.280750440274476, 9.929324351657478, 4.905198729819562, 10.837032110068968, 10.5910068245359, 10.607894583058135, 10.952783192378893, 10.534545942893232, 10.549322875410452, 10.517974378379737, 10.816830470837505, 10.733770163729789, 10.636167217177775, 10.947307842941544, 10.08591704603596, 10.118135451713545, 10.49421668590162, 10.425373541637947, 10.669059354535376, 10.51682619009539, 10.702015574033041, 9.539044649594405, 10.575986132649744, 10.575336345491435, 10.892312601636135, 10.68576189794147, 10.411021572858743, 10.665721274657622, 10.662260299121241, 9.846352053137226, 10.286743879899834, 10.571490016267322, 10.615860288892591, 10.62414552898692, 10.765938320126086, 11.068189353931233, 10.663663403647542, 10.532378490952572, 10.418572752022786, 10.789459440650065, 9.63641399333938, 10.451349617895797, 10.138420415566063, 10.352135448744006, 10.505975107980806, 10.686048571328042, 10.776273678884941, 10.58036411402625, 9.977439331513661, 10.570528664182756, 10.570771231453815, 10.418600856557058, 10.299136563187352, 10.018992249063135, 10.540177333015128, 10.634321678382838, 10.128588516816144, 10.68173508665426, 10.787044021065453, 10.343272293223432, 10.690429920516031, 10.49822165190984, 10.747933367804546, 10.696132416857797, 10.38865490123913, 10.508505193689627, 10.453400882367712, 10.567960816749853, 10.41797589143212, 10.479285865157038, 10.58914263293569, 10.408562143675988, 10.545559893048807, 10.588939492066984, 10.663271014827254, 10.39036635267178, 10.199620630480776, 10.690371399079396, 10.470668810979772, 10.523446745634994, 10.188530447016133, 10.57257097330284, 9.108554570889863, 10.475866549545168, 10.780480601981239, 10.736614840092678, 9.378329165530008, 9.392936489446077, 10.735849025167383, 10.175668364228642, 10.642053661744821, 10.285530953574302, 10.850954104806231, 10.854711498301663, 10.549726808917272, 10.953623521115045, 8.237421136857629, 10.57541658146367, 10.500942393708431, 10.699819009228955, 10.409674150839919, 10.406177996512477, 10.667476828725157, 9.685287175872435, 10.823837159669237, 10.724597172100175, 10.78391964746088, 10.526607121959602, 10.379644480141838, 10.479436076124225, 10.90860248784972, 10.49637630497018, 10.459501536182112, 10.476662792033272, 9.763192857095705, 10.22034751869803, 9.176482363593486, 10.595476669697081, 10.281124426169612, 10.684408919463129, 10.296031190331938, 10.678617737590054, 10.672819866272265, 10.345313080389003, 10.482617483700164, 10.392520331178504, 9.553279264540668, 10.654067777631722, 8.633808799295014, 10.823010147909972, 10.195075782071502, 10.674501201349639, 10.308502571504368, 10.755162934470512, 10.393292382328674, 10.770741390495605, 10.682535432527468, 10.5049318036033, 10.465022833290107, 10.728842563228776, 9.82455646465243, 10.821061794408417, 10.506106124086298, 10.57148977597382, 10.802119497924705, 10.822830404971151, 10.61936017287485, 10.64686357526173, 10.429602466529422, 10.594552516263423, 10.168794948642688, 9.679334618114392, 10.416027434728154, 10.786303837954888, 8.945551614231876, 10.690512867953935, 10.814457986198748, 10.839195580737005, 10.0370649947042, 10.690031952555453, 10.700300684080444, 10.715387902534987, 10.595209954672084, 10.361599789556806, 10.744758336572808, 10.525684438655, 9.951059100894845, 10.487526697000193, 10.444594748731632, 10.64963188412122, 10.586703046221023, 9.751619305452488, 10.630308090868999, 10.50828615340205, 10.366735376927432, 10.60313214413282, 10.436179458715031, 10.750001339552497, 10.38593436137855, 10.52776587073552, 9.930553238524988, 10.636049631103848, 10.739424316790759, 10.63246874798344, 10.354054703165668, 10.636390028923442, 10.345617581937386, 10.579915494720609, 10.818574361159659, 10.609380986847643, 10.136987999717661, 9.999238654410348, 10.494223483757997, 10.968162532202506, 10.072103396512327, 10.71404285778808, 4.839386207873775, 10.272365041468579, 10.693704552208098, 10.189915844125458, 10.388027791564783, 10.660271169259115, 10.797473333919061, 10.729992876530662, 10.439482081025902, 10.355543101653126, 10.597698005117493, 10.61099562428096, 10.503747788953126, 10.68936381928242, 10.628950232018, 10.615271738893927, 10.601620501062326, 10.327217676165056, 10.66065221276918, 10.756856355356117, 10.5607642590429, 10.780554382425231, 10.54014320861344, 10.51903012651412, 10.531714048548382, 10.50719927798392, 10.353221584839005, 10.84280125254225, 10.434080251066725, 10.467124666495232, 10.340545781967943, 10.790608460166395, 10.510686671867076, 10.552674485300873, 10.776919170377596, 10.653095112052778, 10.653277129680173, 10.408915799384399, 10.43342131103306, 10.22668416503311, 10.480078622015146, 10.07105086400188, 10.198343460398922, 10.746869945887424, 10.738472211219358, 10.35118749215637, 10.751352423948255, 10.67484121290101, 9.943911578628537, 10.699751531799487, 10.491232290514176, 10.620048400306851, 10.64925087104771, 9.333017481902093]

path 16
init_u, CI: 1.5364151800985653, (1.4671177550469423, 1.6057126051501882)
losslist: [10.64432234953896, 10.005043621596439, 9.146848035328398, 10.441088962130515, 10.641985697449071, 10.137191438542695, 10.306139571571208, 9.87481159889651, 10.488055017823244, 10.346623396620304, 10.355334907897483, 10.435874268904344, 10.327939664382882, 10.46166997047182, 10.822587867201053, 10.340807203315325, 10.776406949415012, 10.6322313094283, 10.448854291152402, 10.42218585724483, 10.514953681364805, 10.5663630116629, 10.332060299028969, 10.568528957365915, 10.727374565743528, 10.27340768856038, 10.579934821729138, 9.848896222702194, 10.195702965634363, 10.572667675647914, 10.44432723551783, 10.556881073415502, 9.715196136607878, 10.345509714202311, 10.428048585951828, 10.05912076963224, 10.03088674164619, 10.604239950059947, 8.385662141047392, 10.569470778053118, 9.867302168224999, 9.929470254945091, 10.501128781823027, 10.305527796454621, 10.27792322166722, 10.274215258103577, 10.473370717979432, 10.534228343195334, 10.346641625443068, 10.505468083046175, 9.283789791929829, 10.536260983908036, 10.20542017503424, 10.491411775125828, 10.585228545919456, 10.679863536310812, 10.678049727314436, 10.293195882048416, 10.517905715773137, 10.531449299801764, 10.340740180666515, 10.518275676557257, 10.502956599823078, 10.43332578862917, 10.653720451591917, 10.64566510833986, 10.639674280944238, 10.27620517454388, 9.672399066849207, 10.732406632575328, 10.663107028722477, 8.52719574376419, 10.474759429101155, 10.397560749670754, 10.544240045080885, 10.318133754924105, 10.500052910417422, 10.23407454893472, 10.353732568023732, 10.440808535999349, 10.521287655320933, 10.396494628584303, 10.364511339671756, 9.495552758681757, 10.276687788247004, 10.684286412699754, 10.279541277136083, 10.425322554288627, 10.260899616977198, 10.59321871364785, 10.635909804281278, 10.525231216216607, 10.503705549934171, 10.39237674585303, 9.628260357999759, 9.348376420718548, 10.410124761070989, 10.328842089323537, 10.285450537579033, 10.17623233371649, 10.248540663637723, 10.536090685995596, 10.652561780526563, 10.287528578940229, 10.465943338602166, 10.511998874371809, 10.25587584361009, 10.469099621729436, 10.519407467565381, 10.628725844449017, 10.59800942168225, 10.748298579708297, 10.13627176237323, 10.562755045319427, 10.190252101883608, 10.480396659717906, 10.123139875462376, 10.460833592786631, 10.47548857431532, 10.508371791555033, 4.90838525842967, 10.147919507092501, 10.148133486311814, 10.443508859002566, 10.375460976495031, 10.708170180905462, 10.388127354760137, 10.608425160835917, 10.451714344259905, 10.578647191241021, 10.735796455383925, 10.472012147806682, 10.692989175052325, 10.318335729544351, 10.30342137833658, 10.380296824899492, 10.440673191597657, 10.345985025661923, 10.084727959888795, 9.948860167641692, 10.518990398494473, 10.436215699691928, 10.314424101693758, 10.45025987879602, 10.390165501855277, 10.77430646201197, 10.037210298521774, 10.550848112126834, 10.4767879968479, 10.274279685358396, 10.609276844312008, 9.917982196654437, 10.42431397416077, 9.811318678713869, 10.57233405616684, 10.268533639102472, 10.460458318713068, 9.871404025617617, 9.95241942489695, 10.320958471692533, 10.132304991837636, 10.452176536359712, 10.526601380916617, 10.347443272183185, 10.353421882011647, 10.222745390403642, 10.414841830739498, 8.139715901635894, 10.184420705392542, 10.375153157414074, 10.592709797720252, 10.48648732556575, 10.850158026295762, 10.164955963672664, 10.490938837508168, 10.18324284197838, 10.607801602467992, 10.262761977290705, 10.119042616264071, 10.636934544556663, 10.572064967489188, 10.836363792554252, 10.427379086033849, 10.433493095525701, 10.526179987155864, 11.019901024208114, 10.051137907466913, 10.439219440579901, 4.331109997729129, 10.422471336159587, 10.179136881660376, 9.599732165814684, 10.297366292363298, 10.06192043302815, 10.47021537930031, 10.22403741625688, 10.361211915340398, 10.37420912954807, 10.364940940452172, 10.400444538966937, 10.65387456334456, 10.148939680859147, 11.006206567314349, 10.561276011344427, 10.424843623068679, 10.980975735131754, 10.565520754304263, 10.310723204814954, 10.711912983420902, 10.104051689004141, 9.425179371724708, 10.415749071503766, 10.208081459635606, 10.09312146422426, 10.444751547325618, 10.33021829829589, 10.063675769980827, 10.391205630187994, 10.481262694281059, 10.406488342310036, 10.063566682013057, 9.903811346079076, 10.563900122444268, 10.495782926620686, 10.628456496729452, 10.763896510290284, 10.084132938362718, 10.295202202760013, 10.427683836647795, 10.313561369807429, 10.392366887991788, 8.47789283174296, 10.802717437652918, 10.209149678242284, 10.588331148217431, 10.556488347856183, 10.315064054013398, 10.322982987196067, 10.474860607258437, 9.370065529335168, 10.481154222317127, 10.64768719445869, 10.708775594650916, 9.80588529657231, 10.43312580802228, 9.935902250707345, 10.44079659882585, 10.565048034783299, 10.59817211942426, 10.529164780023777, 10.285828509319561, 10.557411572888308, 10.32260085363092, 10.312725820835324, 10.386089239203125, 10.304765256380946, 10.562026682768984, 10.75145866551346, 10.247120558812208, 10.025431899396883, 9.663243015175222, 9.90844278043297, 10.403600934294243, 10.316867615405103, 10.20734411884926, 10.693388884472581, 10.284397055125824, 10.576994329418373, 10.480085939646413, 10.530377846440388, 10.412059952865036, 10.220257685499401, 9.599139186725584, 10.571470336287305, 10.359438347581147, 9.960615770420931, 10.159360840077898, 10.15634688792471, 10.327660460227372, 10.38048298468213, 9.407710056281253, 10.421232335304682, 10.543576909064889, 10.078260428132744, 9.95927032290286, 10.50974872888673, 10.277873565574456, 10.07084920209368, 10.350424741576369, 10.067548381231907, 10.26179836631431, 10.528377009756214, 8.00934106938507, 10.678371187419769, 10.080012195804349, 9.425057312244787, 10.009293485541344, 9.444671878093336, 10.413172554057093, 10.550099797610315]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3936448242971693, (1.3309104835535948, 1.4563791650407438)
losslist: [10.4561360622855, 10.613438597907479, 10.393863303322494, 9.901066338538874, 10.779397824876597, 10.254576722857509, 10.69997254708064, 10.393878885762014, 10.396384541961083, 10.583554487582933, 10.844954099357768, 10.461971693839084, 9.181049675951733, 10.473272165494295, 8.058348686110369, 10.586306556067045, 10.713424760031385, 10.508262087517792, 10.55565048824333, 10.386232045219058, 10.555849865590258, 10.992017819357386, 10.153450564984162, 10.483486193931302, 10.687339873128506, 10.55834940455889, 10.63876353766771, 10.293987431829057, 10.22558054248246, 10.44534627156539, 10.886417072794002, 10.729519951027513, 10.232162150280887, 10.337170356085469, 10.719011918143883, 10.355318020693579, 10.595686676710704, 10.43139273848384, 10.57747308813238, 10.472457718178271, 10.36424658229672, 10.255434816928636, 10.957400834540687, 10.70740805020704, 10.705570988693093, 10.438917870669542, 10.589774580330932, 10.10301976722823, 10.49323361305359, 10.588535087926033, 10.39999429742201, 10.556208130892092, 10.115732228752345, 10.701606446914504, 9.753770644635427, 6.537939535205667, 10.347991796006761, 10.378397293391137, 10.346673652780712, 10.157619188598078, 10.46101712555751, 10.631448192115124, 10.665166882245478, 10.66371713230445, 10.415004765647337, 10.583255472429359, 10.737918125520672, 10.627256503916168, 10.028309895647345, 10.317923177355352, 10.675807080860569, 10.719535481411262, 10.324757849309183, 9.878731317149638, 9.393766333250165, 10.060499888124491, 10.48536493753533, 10.600215075466311, 10.290947774858562, 10.431701965494913, 10.25325375471436, 10.574104455546529, 10.719559822819479, 10.371728352625567, 10.452976954620649, 10.464751169602682, 10.373727150486639, 10.609037335308736, 10.687740870987902, 10.358155710414334, 10.462554589691177, 10.527838178992653, 10.270877059141746, 2.8299763449507918, 10.96343353618245, 10.725247262930488, 10.300964390548595, 10.8201924260979, 10.632944048208206, 9.336415334651594, 10.480437846328392, 9.947444313337776, 10.388602004618761, 10.492635927460325, 10.622597464824718, 10.46171971822243, 10.697392239098228, 10.702800891946874, 10.478276437854253, 10.638897880993039, 10.28140084526332, 9.800219754216654, 10.422097926620966, 10.423025121781542, 10.394779278325647, 10.24594180109016, 10.355991968832685, 10.513782210786047, 10.551262545293838, 10.232934116190577, 10.746168201874212, 10.704998050389365, 10.585449956939694, 10.67064065417934, 10.384951370427975, 10.466374299903542, 10.499106684160445, 10.535271633951115, 10.419112691206832, 10.676821772870756, 10.539347810739292, 10.5496835896237, 10.493162485625646, 10.774239684463398, 10.511742962747114, 10.726618602080237, 10.636338301056496, 10.764251862708209, 10.899573598728207, 10.720380710373279, 10.559804814828635, 10.336085753760546, 10.405610574391588, 10.47121818957725, 10.692538786850156, 10.83658286008361, 10.375041376857268, 10.326052733966204, 10.786769228704038, 9.698826229593442, 10.888847370532352, 9.688290934193219, 6.687526016624532, 10.3861740409734, 10.865323248808712, 10.623710159670843, 10.181736547527914, 10.199057053737995, 10.525274169927085, 10.81306385844908, 10.432139877950313, 10.62041249100456, 10.305871601706253, 10.436446428270528, 10.382610280103933, 10.746122539232005, 10.461381210088382, 10.917124996111967, 10.486445401084769, 10.626191432112273, 10.280188999415147, 10.359387264361288, 10.551451593459136, 9.715800014500715, 10.204415950040719, 9.987326097985738, 11.300354904576988, 9.777178114051493, 10.334732304360307, 10.403162575930365, 10.66714911941082, 10.346213622748415, 10.629871018412869, 10.723385284747408, 10.575361958185049, 10.476246530365266, 10.513900379424658, 10.757374287266538, 10.289703526294305, 10.451791830613962, 10.891974652882595, 10.573402131254896, 10.458927018239711, 10.740600629109965, 10.540985237581134, 10.63043200192979, 10.562916302082037, 10.50023818604942, 10.395037452029557, 10.478911466143733, 10.802382503449188, 10.39287841077666, 10.646313615780054, 10.821324883010778, 10.488060954226194, 10.426605373098893, 10.555110732660058, 10.500503020176993, 10.785700495241965, 10.582809965184486, 10.6645074022727, 10.96138617331172, 10.308654969135652, 10.1926252774286, 9.496997559163269, 10.722839934436188, 10.42684684755259, 10.588700609102448, 10.670717675732654, 10.521118354557503, 10.680502496551778, 10.537830515013267, 10.47295018437477, 10.234854982430155, 10.291756354064981, 10.236165518763656, 10.742598996066572, 10.430104470509171, 10.509392089067351, 10.755149141579418, 10.14767311880691, 10.777634276759374, 10.509883650127467, 10.471517036187889, 10.417540349190402, 10.40863135056535, 10.637281082151347, 10.344598460497618, 10.773380273537034, 10.538947208676088, 10.373997526552987, 10.484259704297491, 10.561169136868864, 10.228908376592274, 10.3616128971682, 10.24114971658581, 10.56797386539915, 10.480510422133545, 10.304297162068602, 10.540511267053684, 10.567372107727632, 10.550057613254578, 10.630045158360728, 10.345897536735553, 10.252557213058736, 10.754923777879132, 9.639280687776553, 10.679393454063161, 10.406671831661313, 10.693240229603802, 10.509181282932413, 10.18939338902852, 10.759668256077079, 10.610379786746714, 10.620692951523441, 10.558350223194559, 10.514711661425862, 10.548990077750707, 10.665162120829526, 10.214846333431591, 10.628939469757404, 10.971906227632408, 10.678254332591102, 10.27121833479037, 10.797166130270956, 10.228022306922174, 10.494691843000496, 10.507711220870043, 10.561611516237347, 10.453272142029114, 10.495850740518033, 8.20733549709912, 10.356235273235809, 10.654978397216391, 10.536410106196968, 9.287516153043777, 10.227313639814861, 10.546275030476744, 10.512320299741136, 10.607967308966321, 10.43967864721692, 10.45094244939339, 10.546026494989833, 10.50297030250113, 10.627319881021574, 10.184517869992897, 10.474975629770615, 10.576779250472187, 10.402685310613823, 10.103971805534416, 10.740106356871888, 10.800197320082727, 10.547516198676353, 10.402151758997325, 9.781198312864932, 10.707511828021687, 10.739337422388992, 10.329548693351162, 10.696324396978644, 10.655872281677658, 10.492639194181104, 10.799103548459914, 10.559958013414109, 10.438352836179785, 10.569599300354026, 10.508793945920582, 10.509323385472287, 10.483050751946937, 10.451849827406571, 10.290454546729274, 10.52275842071425, 9.727130849229583, 10.624172446156777, 10.552968166765528, 10.721029279879115, 10.464507257560767, 10.327273133130193, 10.617807095721213, 10.476873709559383, 10.15864045740647, 11.025292086579338, 10.449518583806434, 11.084971936307774, 10.592683391441378, 10.54617994169759, 10.372378090038074, 10.635543976954486, 10.589917061996994, 10.722484894606897, 10.740294326839166, 10.066890220592644, 10.783420608979242, 10.78036709368058, 10.60030039218246, 10.05889113077715, 10.311539013985604, 10.408304983292478, 10.403648636822153, 10.274749391145289, 10.166875820439534]

path 17
init_u, CI: 1.4199442799652342, (1.357013932630661, 1.4828746272998075)
losslist: [10.020163069892428, 10.131965832477883, 10.394869281176623, 9.970616509581934, 10.329957695901996, 10.448447139531652, 10.671421542211274, 10.457333372851616, 10.237930603323141, 10.651993866801776, 10.304095143571418, 10.773456553012828, 10.439816812143512, 10.484695699259019, 9.982315019804009, 10.457931513990168, 10.735415039808474, 10.348832745003, 10.345659646496552, 10.606933627676439, 10.260151116507476, 10.188395830063145, 10.543830092763429, 9.665347459148633, 10.486812302808323, 10.249208200825606, 10.247329153113615, 10.467246993647215, 10.890347158879733, 10.501137652851467, 10.4541251999836, 10.39237120378939, 10.4102694049553, 10.590525794978726, 10.201660822712306, 10.581105439998757, 10.1123843399679, 10.372095250874299, 10.411065178425034, 10.449963463611335, 10.68072404613002, 10.567898971489587, 10.186676307737455, 10.433280712306615, 10.443882824558123, 10.242033482925521, 10.4625399502459, 10.49045136415419, 10.432952703678355, 10.494199190853129]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.357605830559418, (1.2995453701985564, 1.4156662909202797)
losslist: [10.41146945597147, 10.7025702799244, 10.682250863188356, 10.695079496634404, 10.341784700824716, 10.282435473294662, 10.495673782680432, 10.63211991910785, 10.655191006312986, 10.293342363454318, 10.295623400411642, 10.153046586001864, 10.44116647645875, 10.645791697106883, 10.666572577099876, 10.341158230026327, 9.890103480229772, 10.36881367911625, 10.575701715449892, 10.595876730028039, 10.648322387534856, 10.208013775121746, 10.594359684422143, 10.248676832536445, 10.776192168082948, 10.602092746169411, 10.467209701841515, 10.584586205751004, 10.4910443656616, 10.666462641662042, 9.923254010028511, 10.254708059087429, 10.338720529660772, 10.652008340222716, 10.504477944836307, 10.222429388071866, 10.53163111588741, 10.427688438970431, 10.820514228090408, 10.426298523590528, 10.353900531612947, 10.48043857470943, 10.353351363911017, 10.658683086889523, 10.60080693447386, 10.06490446888976, 10.44129700999844, 10.435001398577363, 10.460707254883653, 10.417231174291885]

path 18
init_u, CI: 1.729335463705576, (1.6478560246709488, 1.8108149027402032)
losslist: [10.407642440110923, 9.52705231687431, 8.970290823262399, 10.193301680586682, 10.401836008702029, 10.572886002457727, 6.302348813715272, 10.245476368820421, 10.289314548036556, 10.236686131598278, 10.481309016637606, 10.06567351306672, 10.631717494370129, 10.17389706801077, 10.539074561528555, 10.052191711690789, 10.342361111296164, 10.180451879668059, 10.248264649340594, 9.948320791722868, 10.723947692305167, 10.525801283607613, 10.465036041187414, 10.34219783689204, 10.335541059424003, 10.016848860662313, 7.1484150911024305, 10.31950163709714, 9.857396895570501, 10.434200501153347, 10.4023824848701, 8.684479269622772, 10.262798831873692, 10.469973431585586, 9.98775743107805, 9.70407552651513, 9.808124076890405, 10.144393119231033, 9.202140506859049, 10.093012756408793, 10.53498341528605, 10.362706213763493, 9.87271984651285, 6.633452028567698, 10.423597341756912, 10.312532674353411, 10.31192392585888, 10.318841420115815, 10.079522782107517, 9.91438227659627, 10.319334371949292, 9.70260536876173, 10.600263099489965, 10.400163925741294, 9.225714044441672, 10.096999573520316, 9.5834708677027, 10.432262696336277, 10.284720255045247, 10.549319179988913, 10.538594116908397, 10.52910031358186, 10.473478819272417, 10.183928336654407, 10.351351144914442, 10.673841410406174, 10.213585830882822, 10.213287798667, 10.330249909152297, 10.582587610247266, 10.854209692495644, 9.460929492010893, 9.490743070132972, 10.408549289605537, 10.54193756977583, 10.699538421796417, 10.580378859263991, 10.174311563137973, 8.990448441385707, 9.771664839192315, 9.902429084161344, 10.249724031324115, 10.422729354139685, 10.45600748595005, 9.85368808982566, 10.266244468078723, 10.446600311812865, 10.571805294649335, 8.684815248460291, 9.89878688333572, 9.860669141489915, 10.366564114795612, 10.015354340256904, 10.326154467747923, 10.622023671556377, 10.41857132884125, 10.63823848592545, 10.329376351664386, 10.56071234749252, 10.156177657505413, 9.47839870759098, 10.29724893785804, 8.547386598079123, 10.347535408867632, 9.705428046842725, 9.988754332451382, 9.200741360218373, 10.41721881657626, 10.228618728579512, 10.272616353995955, 10.478680914670758, 10.13707314186296, 10.201084024267244, 10.318716691689865, 10.1888757303705, 10.282558624705135, 10.459058750302693, 10.323030622297862, 10.26893646172933, 10.39524918946835, 10.11341804546403, 9.925532226857408, 10.224050078473848, 10.503377038870557, 10.314246573903066, 10.540701607442081, 10.327906469755717, 10.661323546854828, 10.510631928832519, 9.797106426447158, 10.39872639647207, 9.924134881357139, 10.25837704262737, 10.409646650968948, 10.380884458227913, 10.299811984718842, 10.090179352559987, 9.961716469041498, 10.439856597678238, 10.284268795454436, 9.94592152651381, 9.790293920663519, 9.558867510026369, 9.299819631714644, 10.332675439532364, 9.573589073747144, 10.610585756211044, 10.408348538373847, 10.274089834061545, 10.508882766870165, 10.308685901652172, 10.352410274677508, 9.899149798434475, 10.212404858480856, 10.0810418919909, 10.343646461125827, 10.053106807762102, 10.576592074486378, 10.6122465262248, 5.829609615508247, 10.42662448720979, 10.532578677311328, 9.782967603112718, 10.435695415352006, 10.086682524860024, 10.2779715888834, 10.074884365745797, 10.363057748408076, 9.614545154847079, 10.531351226309958, 8.799170486071999, 10.403026519019003, 8.21471320748307, 10.467169894537644, 9.856298600176352, 10.39089235511199, 10.414551683121584, 10.134930370333455, 10.243043515971797, 10.745519182880638, 10.254365230488673, 10.603058429683974, 9.583643220058677, 10.376982877668171, 10.11303741417783, 9.997894339622002, 8.533155259461905, 10.368265540500753, 10.282634254383025, 10.560123504512516, 10.717437096305805, 10.219434734201128, 10.351382575183553, 10.64529164021172, 10.142632079560881, 10.116210517154967, 9.666017898819014, 10.481330745841708, 8.612271292086003, 10.170144193191055, 10.358821797868869, 10.049441764646232, 10.249019705746782, 10.448254545511602, 10.041592005306626, 10.283772292800087, 10.597722287033752, 10.362442027826429, 10.34060936160147, 9.965496858714472, 10.53041507465607, 6.781800988735137, 10.555943584194416, 10.590064864498569, 8.921591622366833, 10.079117496428081, 10.058309098022006, 8.935430730226985, 10.788803843426026, 10.15004007566189, 8.820663322052392, 10.219997932567484, 10.303917229484881, 10.251557221648829, 10.15411638615812, 10.001018642899252, 5.502470806424209, 10.28690460828993, 10.184862566621026, 10.40294188372526, 10.228641262277842, 10.379319785218804, 9.96343774628652, 10.237273743794185, 10.337331475679061, 10.219254298899566, 10.421695004060224, 10.313329326598915, 10.49504509109883, 10.16131488319858, 9.227457063479298, 10.313319518619442, 10.348529280489897, 10.575416360904383, 10.56474028018696, 10.400768903940524, 8.595536255791709, 10.338174006308224, 9.537009401217636, 10.773380690068686, 8.196610270302042, 10.429910045768809, 10.25590426056358, 10.479712007351294, 10.24859970106412, 9.201530560880165, 10.552753152783565, 10.716134710721219, 10.36628192332878, 10.197156867931103, 10.254767421695323, 10.595430388171565, 10.735627776885302, 10.424734003588776, 10.257735680117616, 10.745904600104597, 10.009577520475082, 10.282425154692161, 10.377941725191167, 10.44630561454518, 10.623827216640313, 9.394937651382948, 10.466154542917351, 10.280611966528765, 10.44964401237545, 9.97471298916771, 9.922694305415364, 10.504511048433086, 10.154210022396358, 10.767020888864973, 10.565954525603871, 10.496913518383536, 10.309594356455822, 9.634773891803219, 9.785231448706236, 10.433584740297734, 10.103829034489067, 10.320563660457287, 9.042785310565527, 7.9917576181352485, 10.359485369574521, 10.216733810253633, 10.131230569006322, 10.568405567452652, 10.006394975540998, 10.214530198900242, 9.937163994703155, 10.547055489954039, 10.44978392877554, 10.455474872112733]
AVOIDCORR
Most correlated pair: (14, 28) (Guinguineo, Mbacke)
Cut district: 14 (Guinguineo)
u, CI: 1.7710611380324792, (1.6856646041734447, 1.8564576718915138)
losslist: [10.443768134795851, 10.255227742340665, 10.663484638020599, 10.273215681295765, 10.171871919023626, 10.259610794118768, 4.3403308100321665, 10.491668031599886, 10.317139759354514, 10.56374152588272, 10.548743182278647, 9.95563529669746, 10.688001050763512, 10.187808761367396, 10.43248407444444, 9.910222052830745, 8.289462511254603, 10.183027579825003, 9.403426774724501, 10.421774439114511, 10.53306132786221, 10.565479568385644, 10.03783487960468, 8.979353359717795, 10.461496415564103, 10.263329211166463, 10.41417259181509, 10.461683744520272, 10.570379144011687, 10.16917785052386, 9.946117218173521, 10.512103051932018, 9.326847072529983, 10.487885280625724, 10.179899874897808, 10.659650043966018, 10.20558991431389, 10.249354265366733, 6.0144221986900055, 10.55414109173566, 10.37596569943787, 9.718797939550422, 9.245572217912617, 10.387999350387377, 10.416837034302054, 10.27365080201844, 10.296885596299411, 10.076739532289947, 9.9293765109572, 8.63213016697587, 10.329655570461382, 10.581069583652916, 10.410909363171065, 10.478643503104632, 10.263490875805036, 9.728261066297515, 10.544067136655842, 8.877508886741204, 10.40107347662991, 8.738745184631123, 10.8774573680787, 9.893434856220198, 10.190678864569541, 10.106990471258229, 10.505107516474618, 10.398964598961326, 10.644821056533267, 10.414954208711974, 10.229979621311037, 10.69534089727835, 9.030806791239808, 9.662977890603994, 10.290541215143676, 10.465551974504862, 10.203910463058637, 10.152519331331588, 10.569411725440832, 9.404347285869957, 10.449300133794544, 10.281559501295687, 7.529761827030401, 10.29641790842882, 10.364219306589643, 10.544199121132024, 10.462374534420023, 10.182286035669918, 10.469443826939207, 10.481095523132542, 10.310335300226527, 10.618506911908003, 10.404905967790066, 10.419250378800248, 10.422294425131248, 4.894599408755637, 10.744984655063861, 10.322577993692, 9.842134979775713, 5.893070416575599, 10.302388427480594, 10.30006211358225, 10.54199804104667, 10.508782952670126, 10.342911201092182, 10.54781452130813, 10.01998406793893, 10.367916428267893, 9.929376680675823, 9.989941260010243, 10.760858781453678, 10.245667402567712, 10.544811776877232, 10.1596536418103, 10.450662669654571, 10.64729421113366, 10.103280811100934, 10.230200464032638, 9.265203450061202, 10.556219999734994, 10.398238116403498, 10.145252563845075, 9.68040809196617, 10.363608483300133, 10.101035607855783, 10.60212096791725, 10.088390854709388, 10.678576535563034, 10.216872850089011, 8.355005978816669, 10.251337967322838, 10.451984227411819, 10.188856247308841, 10.00671508967857, 10.186242579474388, 9.369541032417953, 9.033357555821686, 10.421390860301779, 9.722051865815674, 10.355034656464014, 10.348271178010235, 10.201822807309117, 10.456398571739516, 10.734683302902626, 9.553973249260066, 10.41233898864926, 10.294193634205913, 10.48947709052272, 9.728791540776154, 10.71904322698364, 10.07425951447247, 10.37246127875651, 10.572942754078571, 10.378965265954937, 10.158740173272767, 7.696843042500332, 8.081990838883264, 8.19826847817849, 9.063706716362365, 9.041070434793612, 10.324226852659898, 10.519181922218594, 5.392965592080972, 10.123520341208671, 9.781060111364564, 10.3802409205473, 9.644396060972218, 10.335146143449942, 10.547867884876487, 10.56375866379493, 10.366168272802971, 10.478446964296994, 10.200770062235204, 10.306467683111812, 10.485344563339615, 8.926439318570587, 10.448902731514929, 10.144892363886255, 9.76947360968871, 10.395342501876184, 10.259831801604568, 10.28767303319508, 10.29276012954622, 7.485971036804136, 10.652548817065847, 10.589927249802276, 10.698980562311208, 10.020147309883813, 10.365570615937244, 10.566387249735522, 10.29957097555164, 8.658078943962709, 10.381046609080192, 10.231269406044545, 9.705242335457386, 10.163260804746658, 9.993435693387543, 8.445184341275985, 9.836966238334034, 10.458140668692007, 10.65513614892027, 10.777438292279378, 10.697340170228541, 10.124991561709047, 10.275584843303943, 10.284670719139335, 10.454345499603887, 10.480807947506749, 10.289442372518968, 10.40010271279838, 9.9127493640651, 8.485386158603962, 10.271176943754657, 10.502361773584164, 10.611049391220604, 10.228481499079127, 10.342462000015901, 6.371123743731845, 10.413890947127149, 10.358130338492668, 10.55523788059159, 10.65996132690968, 10.546355742398848, 10.46254228511247, 10.198806634252529, 10.03310972115063, 10.285693578249667, 10.171640227842234, 10.362007930207406, 10.138428719486393, 3.7590444261481872, 10.38113841398494, 10.284935873692806, 10.599985808150837, 10.49859141481814, 9.702356040031633, 8.260203486929166, 10.25006486787519, 10.472269944380258, 10.359719690066797, 10.393699153699423, 9.667809865220208, 10.463971998423268, 10.418984808276177, 10.303419748983892, 10.475945206017045, 10.506159051603207, 10.288317032114028, 9.919144701687948, 10.198258660239796, 10.297335967671073, 10.440268570436853, 10.07230233441078, 9.868129153083146, 10.349059597070216, 10.206029174411135, 10.325530511394254, 9.816537344653165, 10.002990547450196, 8.753550194627158, 10.49966195897508, 7.260091512724962, 10.613235508112103, 10.57924693666027, 10.259216707681146, 10.531909614993149, 10.414454097605292, 10.582105413739564, 9.737720238416415, 10.63428366214054, 10.317417434027483, 10.56736134565396, 6.843186928835468, 9.993235288817631, 9.108473337711922, 10.413480048362123, 10.687516168595893, 10.131611420080542, 10.47825601005479, 10.228993936170822, 10.310798575217932, 10.437086462164016, 8.324271467949863, 9.924664086616282, 10.154285955213728, 10.263522407871678, 10.346274820783648, 9.745719986878386, 10.569047667844503, 10.388223164090501, 10.226600696160956, 10.172151383084802, 10.404984583361244, 9.34855714152462, 10.186667501680533, 10.21775242751819, 8.628281758091052, 10.515804170928838, 10.106730891514966, 10.392605562089512, 10.457555175269944, 10.328688981689949, 10.618979732761822, 9.603130294695605, 10.432295704453031, 10.584282892951418, 4.449537862327983, 9.770863482070924, 10.489231259211449, 10.329909221288137, 10.615341185040467, 10.263690220572748, 9.285141500983588, 10.257586860242371, 9.822059680398525, 10.753584390512936, 10.1539302110413, 10.460943713099343, 10.23400277760362, 10.72012300050324, 10.321812626849406, 10.171529387806723, 7.196161634663729, 10.35624867216552, 8.647720958625131, 10.41653000126514, 9.981217543957502, 10.552588066813675, 10.109400964592993, 10.284738760311491, 10.4867225132586, 10.209093219281964, 5.808714787670767, 9.82938601265897, 9.716806301104631, 10.41304695261771, 9.258367218935167, 10.01123574603095, 8.857406437053484, 10.520251450050548, 10.430014946194968, 9.361815888508005, 10.881014410105996, 10.541409102592935, 10.539811357623563, 10.35131254869803, 10.486513039155891, 10.343705981638982, 10.379293460194381, 10.468867970959012, 10.53435572536075, 10.12980735681775, 10.598851664996358, 10.2717805734482, 10.58119087533218, 10.651956132622805, 10.074521793738283, 10.33389820795715, 10.705870486833973, 10.33656901115002, 7.452485217572461, 10.356617276106853, 10.373188576339324, 10.576448808068411, 10.508015683751198, 9.655429277698767, 9.837737321338292, 10.468801000150671, 10.67031370908625, 9.296458581579497, 10.264508722034073, 10.319766489772828, 10.385107863241643, 10.548118917074953, 8.817402287458998, 10.39168859266084, 10.573193414120876, 3.624721885831876, 10.60103949382752, 10.403713983343089, 10.240867518591172, 10.482445420965078, 9.960534767966754, 10.471876694885989, 10.20338462619107, 10.475291701721474, 10.126378671564492, 10.271742536003773, 10.226137592305788, 10.299800497486284, 10.200327312769943, 10.293108213319847, 10.29144917447345, 9.25496496433807, 9.420274581603953, 10.293070858728264, 10.406012870948155, 10.285331662480692, 10.503884496531704, 10.629646894708825, 10.45297785889876, 10.699160627565385, 10.09062296621266, 10.300700199125547, 10.466926944315514, 10.193231422561293, 10.399900380886878, 10.618420674412153, 10.114142152218744, 10.694849438617792, 10.226112395652603, 10.41214345634865, 10.176902342208678, 10.015318935033662, 10.395317023850266, 10.160576005228027, 10.478431935309548, 6.8424449993973635, 9.626816529754944, 10.72366031918727, 10.323717076329268, 10.374339510449955, 10.280605690946645, 10.50006500169107, 10.607094609224243, 10.590354911574327, 10.276490110036892, 10.189051829791188, 0.3419578717217126, 7.998185962345148, 10.275350210074865, 10.119792513584144, 10.480047022441767, 10.649153669728182, 10.452415631568558, 10.351659980851917, 4.8085329357636395, 10.390786701916424, 10.65588426907145, 10.209859516058847, 10.448086068994419, 10.415635072050952, 10.349792964432472, 8.922443564193781, 10.455698914891986, 10.590291697315902, 10.286743716299021, 10.085235782696806, 10.409050269537321, 10.575546189654403, 10.25186659694384, 10.535175064408662, 10.0846797021357, 10.49960879283904, 10.266106462802128, 10.274865287649279, 9.581346393921807, 9.970713813773715, 10.719591054728484, 9.553775015455372, 10.345263894603757, 10.272043195089054, 9.242979723294505, 10.5791606635144, 10.3893213204086, 10.34759746526295, 10.299078798643105, 10.332985856924198, 9.511453438386027, 10.439894057872316, 10.531516562987393, 10.542895954868131, 10.394195617213633, 10.43520904460334, 10.386673914164806, 10.355279291049674, 10.727873006666465, 10.182189262663218, 10.103617353155542, 10.305161177452474, 9.898147058940198, 10.044900555329084, 10.269865895768156, 9.938183123610298, 9.440579509934892, 10.293653866145558, 9.647883223681577, 10.554517573976238, 10.639443708529724, 10.60789057473474, 10.200338323060198, 10.565185215361094, 10.554635891273373, 10.615999194522823, 10.508199300473445, 10.497032848611132, 10.297629279786278, 10.621248141506813, 10.577073652970036, 10.289831614598087, 10.098287249859807, 10.409198190964663, 10.586369409550565, 9.671136282699214, 10.019471135052564, 10.677993177476019, 10.72340821545817, 10.02699973703892, 10.25120152783162, 10.236769292763476, 10.465243541125863, 10.140963884381906, 9.931514732373122, 10.245015790094678, 10.427576499872043, 10.188559898097672, 10.60311702708837, 10.346988566266994, 10.575564564914028, 10.585485629009106, 10.199669127414928, 10.285358628866415, 10.149595941061186, 10.19682195237678, 9.75011821080746, 10.222010402271874, 10.471813044100442, 10.044304603152376, 9.94361492310058, 10.327364249318128, 9.537590650800004, 10.52200916835106, 10.345282998215279, 10.328239215596508, 10.341527437516861, 10.347135842717437, 10.403944446800647, 10.51367733110792, 9.999778339757402, 10.463578325634746, 10.662795741878142, 10.638021682929095, 10.273162803830292, 9.073247338915785, 10.686126959289341, 10.411682488759848, 10.13156316009171, 10.49430616768372, 9.541139948571013, 10.26227663877553, 10.132579606936881, 9.907709138558499]
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3506299017532726, (1.2993090609417202, 1.401950742564825)
losslist: [10.558448924294842, 10.427879687935748, 10.88939860792885, 10.961285046372073, 10.601844217546505, 9.660432362659941, 10.648002255134266, 10.676219947900957, 10.325972929594695, 9.876169238758424, 10.520847983576042, 10.571025743923913, 10.531397102621575, 10.398599645659738, 10.62466131317272, 10.37991454344349, 10.551092652950443, 10.384461650663335, 10.680886051280812, 10.37833242887954, 10.37426044103699, 9.735259038998944, 9.84273666136396, 10.471828625980072, 9.93309213347243, 10.368501407476224, 10.359220425783526, 10.802695406879758, 10.194597342232216, 10.687421767890967, 10.518949607010388, 10.548416526530405, 10.50817366525105, 10.456581944735449, 10.55986366615777, 10.590723547340607, 10.398496808567005, 10.319335512671751, 10.306514343929296, 10.531794778214914, 10.432545913528479, 10.747686372158945, 10.692936276434917, 10.229195781958486, 10.405895456909134, 10.619685246969334, 10.811964967632541, 10.353730834328019, 9.90232500325144, 10.575468850668278, 10.765890534763217, 10.625432056888064, 10.413035801986334, 10.531161130245847, 10.518667851411571, 10.691690119599047, 10.282966737200192, 10.441700356651653, 10.586062243428897, 10.34396111830399, 10.848006285802073, 10.762251060627536, 9.980622265944188, 10.579601717622491, 10.753868042885836, 10.110115444183789, 10.00603963428253, 11.005348847904077, 10.856916345519942, 10.525771465047166, 10.29895576229899, 10.641253609825604, 9.930046457904735, 10.706209829032204, 10.615062201987676, 10.694891319107183, 10.360038359176043, 10.633332926927377, 10.418258116291378, 10.374391819642916, 10.72342222957069, 10.442498479273977, 10.26057686012274, 10.432079694554039, 10.624044526273627, 10.48568433229145, 10.356463401469707, 10.417595983594628, 10.12344977892106, 10.737819667555417, 10.757034185125635, 10.358667203777584, 10.519758613421171, 10.490791954639148, 10.117927243042248, 10.439323574141792, 10.330743020748995, 10.577517295710608, 10.480553098679438, 10.43489118312874]
Improved path index 92 by cutting districts [14]

path 19
init_u, CI: 1.6493052523195075, (1.5688500487538253, 1.7297604558851898)
losslist: [10.230750034494616, 10.343863666397132, 10.463577063746595, 10.534711121574201, 9.637256598784141, 10.18858702288168, 8.549216651463588, 10.375193949588553, 10.535670464092084, 10.518752614949138, 9.91947229855079, 10.42531311129936, 9.960553999494778, 10.451722136743987, 9.693895395350603, 10.454750382843441, 10.203819514385433, 10.401777275920674, 10.534393857042167, 10.489942956813064, 10.366223087264018, 10.420290633001407, 10.667439766564955, 10.145822149853357, 10.57452071038637, 10.193868717683348, 10.30856212206194, 10.409918775273066, 10.404710869773186, 10.436856691228616, 10.404976286676451, 10.459910236561822, 10.524369717892846, 10.61475139667389, 10.226359759691269, 10.19910970022314, 10.175486511550531, 10.317563692581151, 10.448700466922542, 10.39875005966347, 10.322018337860428, 10.533526857135907, 10.307348288787201, 10.132479636337614, 4.736105920113962, 9.59458842330097, 10.408871235556196, 10.19216630671333, 10.489458450658647, 10.543676106839701, 10.275753652057185, 10.205454973760698, 10.725604898670882, 10.801056157958262, 9.377895511112204, 10.286581386705294, 10.40676311956866, 9.983002349551496, 10.52347381907558, 1.6709548353740422, 10.403601853745224, 10.515096354939836, 7.810145533524005, 10.618803623426524, 9.365695168803397, 10.35722955951663, 10.240895709751705, 10.387550409648634, 10.016625157057849, 10.143145289248181, 9.412351818240554, 10.104626550952068, 10.237079323750988, 10.133254435949912, 10.978212612804017, 10.202059042018766, 10.073757011032638, 10.13371951108423, 9.987423812498184, 10.302933177177376, 10.753378966730928, 10.480219355982122, 10.066134644816888, 10.105630287762867, 10.449513714693339, 10.156748073267488, 10.304830407728861, 10.699626704399975, 10.306659577073834, 10.442439814931674, 10.456744147716087, 10.060142078200956, 10.397998774979905, 10.509990374524556, 10.384610722651118, 10.543528738863339, 10.388362974110985, 10.30800342841524, 10.662557803327132, 10.30056215613485, 8.96486074102443, 10.417229612298623, 10.397725508574897, 10.165781781706213, 10.601122900799318, 10.33265026885256, 10.49640832227053, 10.150762915079252, 10.553639948567175, 10.752912746587686, 10.458593861897151, 10.107166919704339, 10.190480668766307, 10.582564806912481, 10.309613002077654, 10.28022839241398, 10.29511577873094, 10.43948385040978, 10.266147593019245, 10.62608259507078, 6.258077292722855, 10.446307879618098, 10.110416961101903, 10.497065697015884, 10.574837351492224, 10.413285096148142, 10.57615130194242, 10.119869073210914, 10.286267163554127, 10.495870501442672, 10.337199314399305, 10.37834861202263, 10.316841580218409, 10.136085958889414, 10.654631517739505, 10.361268045037031, 10.101680678565053, 10.499898986320694, 10.049519782463042, 10.441647793414983, 10.270329218147072, 9.475401764777184, 10.37397791325154, 9.899613302661745, 8.912449784298689, 10.19863905631206, 10.588336195114554, 10.303567119049438, 10.111130033357158, 10.521734185549606, 7.803175013091678, 10.242824804445679, 10.442336008730043, 10.259007787025162, 10.33802623873572, 10.327203873887262, 10.378402179426194, 10.69103097804117, 10.339642350832428, 10.431779654466938, 10.442645987510394, 10.043783725449199, 10.609896491070957, 10.336334730190822, 10.272031693615986, 10.33944065046291, 10.464028158502641, 10.428533029815185, 10.335087087575767, 10.300039594502618, 10.34729801907147, 10.429120102836727, 10.583890517916812, 10.232336325702692, 10.649417224742413, 10.215547201657921, 10.3353715952573, 10.740429521563465, 10.455493620606019, 10.334186329349153, 10.23295785851392, 10.195762033786385, 10.475878506145174, 10.541090297833424, 9.569440708293266, 10.416327694069743, 10.430209919886845, 10.47360994355177, 10.3839086379557, 10.186223032329021, 10.302270887776569, 10.493754457430176, 10.61723942458728, 10.07894833455211, 10.393263116204276, 10.641943793173489, 10.137409963714502, 9.589529849031955, 10.294827115871259, 10.236463677550082, 10.29348684555981, 10.125479136936592, 10.488385636227271, 9.480565038407207, 10.359598407911482, 9.899986115372233, 10.387839649381466, 10.159330822733944, 10.50436784336924, 10.409909593567855, 10.527694764643284, 10.430883707400744, 10.139467165230236, 10.377382235614489, 10.246622928560752, 10.16658605329019, 7.648229408275161, 10.496466473418447, 10.280379897372011, 10.617496028062755, 9.910549954877874, 10.129394268730026, 10.652304391371379, 10.460773763758448, 10.720091765422142, 10.487155352158618, 10.603684977719874, 10.019972028151932, 9.46007887516898, 9.510050879718717, 10.509260209206579, 10.147992316259604, 10.29221408655952, 10.229099152074712, 10.407179621805696, 10.67016836893722, 10.169450156438808, 9.94807842757359, 10.1867991327398, 10.212400468371188, 10.403446949665211, 10.589981715414005, 9.963168067983792, 10.472824398977469, 10.290378572354472, 10.535676728248628, 10.088942446088845, 10.83888249601433, 10.085240556611577, 1.8448902152856759, 9.920660900922984, 10.65640523378205, 9.928724962081413, 10.352591126328532, 10.312196028249506, 10.301784658129028, 10.476763948705148, 10.697054592322164, 10.77322560737612, 10.407396176538931, 10.299437160523519, 10.356687740393012, 10.084256484963845, 10.367658444402545, 10.544492866182704, 9.892154520809667, 9.311694128281031, 10.294194869427653, 9.31691277654489, 10.400614875260384, 10.529731113501636, 9.91093660085207, 10.150144557198594, 10.518173361325598, 10.38147261415116, 10.34422098227265, 10.503620217841453, 10.45175986878863, 10.147940921618657, 9.523466244471045, 10.206154862085642, 10.462138699899512, 10.569669928992841, 10.229426688910943, 10.170717933336661, 10.362483467043122, 10.456118732386463, 10.578090008799812, 9.620716553421826, 10.275803563324617, 10.123791035412921, 9.44108400213559, 10.448399869695335, 10.105730299169293, 10.425398071377318, 9.925233536843221, 10.06372203950475, 10.284156107164344, 9.916882529357162, 10.1766880525763, 10.456765802683053, 10.788969072840231, 10.503933961435465, 10.298947983969548, 10.475970497107246, 10.323987663215334, 9.550169060075277, 10.614071698194797, 10.216415683676768, 10.526369076305551, 10.27007446331135, 10.02091421292174, 10.38246155655819, 10.356232483592445, 10.426237057712598, 10.146930828490893, 9.837903982991836, 10.337317919029466, 9.51786257921991, 10.22667027447015, 10.030271836153634, 10.523793786395098, 10.303582589160545, 10.367634010509772, 9.912730449007864, 10.30961511687505, 10.210398085592459, 10.35036971290268, 10.640015861380494, 10.32504031973208, 9.957681677489541, 10.222298663392236, 10.35208362953398, 10.255148731748308, 10.018146523685314, 10.65643505067156, 9.798184748393904, 10.457948259151433, 10.66820405256847, 10.369012651750346, 9.993687301266215, 10.537855936328128, 10.361543320024387, 10.099257636173467, 10.550414198660462, 10.542944061673397, 9.212682453056393, 7.35996264363818, 10.285236709877582, 10.107677443388999, 10.287669977017092, 10.615572790679712, 9.879129386029438, 10.659059321322609, 10.355503658469477, 10.47882895194268, 10.142388247108052, 10.348503360164269, 10.524989629824054, 10.307910413280261, 10.371884891299917, 10.530831937413726, 10.431683829979317, 10.296533255298968, 10.394734169600966, 10.271182602414026, 10.540562576814501, 10.18451911285037, 9.870704902940286, 10.342490454585866, 9.612263345708804, 10.545859005227449, 10.378163087481349, 9.256254408363477, 10.154618079477848, 9.290721591174576, 10.245211149127385, 10.101042668311795, 10.484184460258474, 10.24022756617337, 9.942111047103701, 10.374461631685968, 10.321778492371577, 10.30273010922982, 10.38866393315006, 8.213312273226322, 10.432718038378583, 10.370340892550766, 9.94971847966607, 10.526485693551933, 8.34081768409121, 10.313894819351134, 10.237482943000094, 9.903627738565753, 9.96120417725621, 7.957216556123698, 10.256774792151234, 9.448170500414177, 9.80663802114027, 10.489500495743368]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.518128082496327, (1.449491637894445, 1.5867645270982091)
losslist: [10.557598653140232, 9.959642517018118, 10.766377996898827, 10.620682862432412, 8.418182697020898, 10.716909638726786, 10.431706761393682, 10.561560635199655, 10.252441315536464, 6.991440026070611, 10.487087072773864, 10.456705863645501, 10.64504787585713, 10.679989875651463, 10.066895222291892, 9.11795032421011, 10.682094860646192, 10.194781792279654, 10.239395672436041, 10.274406693684712, 10.593094605997305, 10.269183196723096, 10.5965103189981, 10.649401980991119, 10.592542952360187, 10.108257001141077, 10.682181556606222, 9.485688992683244, 10.315215192347647, 10.437140857456967, 10.613122473996118, 10.420748704979, 10.413484256291502, 10.54595913366707, 10.029038683045252, 10.506221888217867, 10.677752348982215, 10.306609279401568, 10.551739355045147, 10.72633321875026, 10.454020018938396, 9.724901516737964, 10.601802542323695, 10.68849892878776, 10.497920381178677, 10.62488563455349, 9.89360318730027, 10.12998154333904, 9.86923985464409, 10.754456005384863, 10.787488717357252, 10.237564398692722, 10.708261736912572, 7.164657749004009, 10.787467705348664, 10.22630245771279, 10.483814586959422, 10.91923862447974, 9.113360821094664, 10.515598628167675, 9.363577422722116, 10.634835088650195, 10.597437388792864, 10.85653853475997, 10.584664897284599, 10.450528210301483, 10.344484364847778, 10.751769258674342, 10.318144662600167, 10.713404506457922, 10.312655568537494, 10.62877757321009, 10.804316130515797, 10.511450309521683, 10.579298302236557, 10.528956287585709, 10.263158459147938, 10.511525886563671, 10.185317578031293, 10.194253987897735, 10.39036082172044, 10.296548670720131, 10.376257061754936, 10.083695745633891, 10.468261694102612, 9.053052779739694, 9.780499883640978, 10.211859422682997, 4.750213660448719, 10.288068750718669, 4.99948090413041, 9.855293109095507, 10.359231400132956, 10.856559002721543, 10.577386289667434, 10.708799967591087, 9.781049668828388, 10.3008391032422, 10.843102029417828, 10.601860856726557, 10.516687091115452, 10.568811290876848, 10.639075203789371, 10.420447944841928, 10.661442810226621, 10.341955471661404, 8.737530288830666, 10.41179828645022, 10.393357572944572, 10.717377340860546, 10.397982718873484, 10.34053372136072, 10.541895784158047, 10.589013631468102, 10.63861220678328, 10.226558140609624, 10.511771797764947, 10.568023991240171, 10.214118203436213, 10.644955423791101, 10.206229149328365, 10.536580422005285, 10.337662530940172, 10.41571789415095, 10.749747238235097, 10.592377160347748, 10.402661648059695, 10.319453700376219, 8.72818103547873, 10.224692170763378, 10.044301049958454, 10.643626728216882, 10.47420430623592, 10.661715839652896, 10.423976449224151, 10.480288159641738, 10.177099282049234, 8.643383441002218, 10.495247191825998, 10.111937987001632, 10.372249809370077, 10.732339202372978, 9.68863762129364, 10.3756782978265, 10.655708035970184, 10.69232619642469, 10.695357722308778, 10.487864269280225, 10.544376470455473, 10.874970529159667, 10.374370010340737, 10.834733084416811, 10.581227288601271, 10.716752450285723, 10.535589752662169, 10.081035570658742, 10.51610346035861, 10.670125495656384, 10.507461719493628, 10.020618782340314, 10.678837720641027, 10.578857425859029, 10.796728869802475, 10.663346546234099, 10.14487558405984, 10.41669648053189, 10.413641117752936, 10.646461630047778, 10.364470407790641, 10.389162493354515, 10.288594094084486, 10.093835113416228, 10.497839560998802, 9.560279215610201, 10.341879742232706, 10.590403413408662, 9.829115504213718, 8.643616354917622, 10.593176847835407, 10.565392925089231, 9.761251576491476, 10.382212723445832, 10.586443595095886, 10.63366178247873, 10.457586706646037, 10.263414172651414, 10.532720196825037, 10.673593681310665, 10.199446093462358, 9.815056452653522, 10.394251602776142, 10.241940875634416, 10.601234102220175, 10.818685039721492, 10.283251872317683, 10.596827999361185, 10.605905656454995, 10.359009246367549, 10.243222097434472, 8.565462867165134, 10.501942011625315, 10.308141754317022, 10.293601704056092, 10.771910030784214, 10.719783230990142, 10.721335394796329, 9.629109320802199, 10.337952581855257, 10.392427480782908, 10.587136015209767, 10.573000948603127, 10.504705522837318, 10.383465803717367, 9.72200468655694, 10.516022083761973, 10.534730440426644, 10.180331842858486, 9.902761351545848, 10.296970274296113, 10.121217607835659, 10.433430308096712, 10.27018967407215, 10.054466314538313, 10.754705607812594, 10.492766464077649, 10.205500249286686, 10.246637123184692, 7.504115584408173, 10.299159566834572, 10.656130374786217, 9.314883517017114, 10.258969245216822, 10.591150734133613, 10.714514768994443, 10.359948375807505, 10.403240956211679, 10.047880599443898, 9.190254437561746, 10.509483693648178, 10.639126341663385, 10.669121719215074, 10.03751253908115, 10.113513463241395, 10.490958722567155, 10.016421553150355, 10.68869717937653, 10.602441415263465, 10.576796315580678, 10.4941102266768, 10.579767786492354, 10.50817839693712, 10.501010194546462, 10.582164618178666, 10.4170584395736, 10.873827319439442, 10.475957983189884, 10.313836419000603, 10.323094174916626, 10.781813950584105, 10.12327023760391, 10.296191902197023, 9.915790887072594, 10.476210754365624, 10.507648976955238, 10.623520925806428, 10.608286905500831, 10.198195563946982, 10.695582984524222, 10.754646169039058, 10.242592609001314, 10.800918687624767, 9.654171912603008, 9.836746933407836, 10.753607551946303, 10.761979970644319, 10.0915298049069, 10.414424911134917, 10.327588540965317, 10.412292055180131, 8.777276289431123, 10.814547112078099, 10.722627161802114, 10.760822504792378, 10.648545877300457, 10.688016393123021, 10.233687982870931, 10.884488200171157, 10.401489920767427, 10.438070147132668, 10.673651435917822, 8.870738203172778, 10.598370979086088, 10.10980476874174, 10.560996134525597, 9.978814466526352, 10.547641559830227, 10.587924486116199, 9.682320943117936, 10.490807153408793, 10.025310235871967, 10.233490798653062, 10.04384508240404, 10.427964373517254, 10.773995352686178, 10.404842367288335, 10.705252089578373, 10.268544590616749, 10.394424406559832, 9.891539730534888, 8.456636856249672, 10.511326612120904, 10.631029038329574, 10.359073012822131, 10.26504267654212, 10.475343706533634, 10.355512825379298, 10.302730182825675, 10.257091049569055, 10.242610841931155, 10.635335544637076, 9.95970263069633, 10.693393631168075, 10.312819839025902, 10.327617905682597, 9.415966921344598, 10.453901980390443, 10.458917180793335, 10.656522323132988, 10.601423586232617, 10.170637575448104, 10.54153161677624, 10.349378478454861, 10.10019264399594, 10.336992147114367, 10.697034640697211, 10.432002090675702, 10.05613134133956, 10.288251127263077, 10.530837149557856, 10.465649342916125, 10.127226031845275, 10.533591020005098, 10.486877500707687, 10.442537123809903, 10.512174583861214, 10.421047003748575, 10.50907430289476, 10.804346129826142, 10.596791390401277, 10.299316255535025]


path 20
init_u, CI: 1.7134521285427606, (1.629968007658924, 1.7969362494265972)
losslist: [10.24112483139324, 10.316961794966911, 10.313950435927639, 10.48577108853422, 10.406385520102969, 1.9027530030202318, 10.47703405196474, 10.653846849606708, 10.36963881210619, 10.22101072472928, 6.021158044416776, 10.169512317182736, 10.510845693711694, 10.182217004563741, 10.279348429606944, 10.51982445344242, 10.215559935078563, 10.36689338701732, 9.55139715672114, 9.949983789176258, 10.578225391174266, 10.49435183429435, 8.001679152803852, 10.396486431746101, 10.682763148709792, 10.586529587237521, 10.21836569820784, 10.210500471052598, 10.316248599454108, 9.915690462996498, 10.339446300846866, 10.542994928703413, 10.542063856890614, 10.262330588680001, 10.372876569406419, 10.042158077660169, 10.459148629048114, 10.082317169208716, 10.44946571896205, 10.287170591198382, 10.364537945482919, 10.274372106958143, 7.701471838383488, 10.151576977677465, 10.303062947115837, 10.368384135996694, 10.128877883632512, 10.022046208555206, 10.428421270902044, 10.492402752257442, 10.267532593279583, 10.30734166946143, 10.27794188355805, 10.566214729120189, 10.345940815157983, 10.2914262517081, 9.9299638651812, 10.213174518359882, 10.438178331890287, 10.035707430005457, 10.313241280699128, 10.3888512014811, 10.311182064118437, 10.132962100351065, 10.398482308416595, 9.95330730598265, 10.249020625793205, 10.342327999619075, 10.305608856725948, 10.419192553741933, 10.315273302821884, 10.44880526387959, 9.980838862709211, 10.502951764563512, 10.430078693581475, 10.37830925026446, 10.109697265176417, 10.016790122007581, 10.294150695413304, 9.912923218238515, 10.435736443773097, 9.545680486278929, 9.260770405978553, 8.126463335339961, 10.413696268687957, 10.561735204298078, 10.191299458666085, 9.911459487493763, 10.451175983156556, 10.246069371323847, 10.181313411300298, 10.45781412040589, 10.22976834464878, 10.231572175433163, 10.43723414895325, 10.502972011970051, 9.834055141430305, 10.543563524453303, 10.255271331535019, 10.327772560486059, 10.523556509748708, 10.319124631551642, 10.780919922727234, 10.66704074167509, 10.321447700670019, 5.66021668008852, 10.355320052291153, 10.804135135727558, 10.59181563165797, 10.49349728253212, 10.266708759120958, 10.39635948073044, 10.368047503374571, 8.386450259776646, 9.989676996055975, 10.09992675256153, 10.451176933058083, 10.127649745723655, 10.37208042254804, 10.298954154919546, 10.111417546867152, 10.567490908863263, 10.172646128941615, 10.050672855536058, 10.295177741538406, 9.815406526045445, 10.111563299129783, 10.365009307267169, 10.320139345129194, 9.945298967252462, 10.246890119932864, 10.188697862146006, 9.998664131599933, 10.465095244728223, 10.375345898493629, 10.576635032248259, 10.251659471369232, 10.575309161444524, 9.139596886006613, 10.61285592034917, 10.356703031175208, 9.646162567216352, 10.50679575443237, 10.348707507269358, 10.39055844181154, 10.075949087484982, 9.72597619545795, 10.190318358538159, 10.206162941117988, 10.196264093919709, 10.64387395034982, 10.41362062800665, 8.39422501577325, 10.38434846540277, 10.327452779166107, 10.639131246947388, 10.519983186883831, 10.44850434064065, 10.387924701654114, 10.392167357763853, 3.136825990590685, 10.428667767291625, 10.357222487530542, 10.582724458497413, 9.293090200143903, 10.380009789270774, 9.705386816612954, 9.340939331445178, 7.872976555494304, 10.374701902736827, 10.154917444487571, 10.236939327960513, 9.926875619104118, 10.452976747761886, 9.35079865194748, 10.694052258363056, 10.342418657232825, 10.404214274215416, 10.348808841846253, 10.023956184090643, 10.1558446302402, 10.25513592308251, 9.919096922624895, 10.389859484298391, 10.515792928658444, 10.489639280848937, 9.767014860421538, 10.43234822824401, 10.19842811459385, 10.229599263594856, 10.429285617976845, 10.699756014441682, 10.22931973211248, 10.398994657009355, 9.554876026966596, 9.604726893620132, 10.31486021948641, 10.421405422717651, 9.860978357787877, 10.01321360974238, 10.256574239296878, 10.723528565649255, 9.304882492067495, 10.659837881077108, 9.557270614467747, 10.113241554289877, 10.791008361179031, 10.286118550684007, 9.176940089894265, 10.456545141076374, 10.500023586036, 10.200402259500148, 10.38041659634781, 10.29616673953815, 4.750075169747711, 10.539220131537446, 10.452754835571183, 9.303461238801978, 7.719353841065578, 10.44510676207716, 10.000468370454147, 10.534630035677475, 10.39010096334506, 10.490160588871449, 10.47954034694813, 10.243551771838918, 10.218184620660267, 10.350285477964063, 10.23180895122146, 10.080934605165194, 10.839066603724305, 10.524868560426016, 10.557943915940669, 10.332086328316123, 9.935401371355159, 10.375932835163622, 10.41510072111967, 10.002922336241351, 10.321212846245212, 10.583020475261483, 10.72497599207211, 10.15214420869437, 10.070733910898594, 10.313988729740718, 10.518439964350751, 10.01311356912739, 10.484185345380132, 10.202722956086673, 9.985928234612693, 10.133498301901655, 10.272417521389348, 9.85689322783497, 10.079785184479436, 10.481740830346373, 10.80141083251494, 10.452439407273813, 10.81647941846056, 10.144602093835566, 9.229058191961128, 10.411964190017297, 10.187662046904322, 10.452734780283723, 10.350676825989288, 10.108119515335458, 10.287118168460077, 10.59165294449812, 10.321949708511047, 10.209815630556477, 10.20935573027689, 10.609853315416627, 10.40787004850727, 10.2830622703476, 10.512979585072939, 10.298875234987207, 10.304416769114736, 10.590684976817816, 10.102157149400895, 10.421986765835573, 10.276100306040986, 10.348315546269802, 10.306951824197894, 10.319430741313402, 10.20692611794963, 9.748559554469484, 10.081144582589166, 7.149180832663699, 10.493964552559875, 10.586520853913894, 10.440557435361802, 10.4448226329858, 10.237921629503616, 10.398957608541187, 10.117364987679352, 9.307362946290016, 10.136451329834923, 10.251147120276569, 10.163206692235354, 7.5213723240912325, 10.352331364698344, 10.541610990993885, 10.111363077290909, 10.555196924576352, 10.31278116814292, 10.42628832058411, 10.415467906750706, 10.52989859304865, 10.144595641350202, 10.52182337097594, 10.154581056856, 10.000954998699846, 10.469368569091959, 10.42529979935903, 10.342658812273934, 8.852086959272585, 10.316356191832137, 9.882144175008337, 9.828065334796943, 10.383844184310647, 10.167440415882059, 10.464999125252382, 9.242650629714207, 9.938410999750895, 10.505393742391023, 10.231355048166584, 10.345023555855395, 10.45975970690775, 10.458379112450784, 10.248674710912033, 10.460326683075474, 9.90189201600263, 10.57653923230073, 10.363677057297448, 9.588528966246729, 10.20804979851566, 10.383280554830064, 9.852604826230557, 9.231578193980786, 10.479660518904515, 10.36347947456406, 10.213331742044513, 10.309500561009846, 10.3400530489749, 9.631659787185933, 10.739559504999347, 10.10503494871835, 10.16363761999029, 10.242717506614618, 10.477880402109728, 9.376873093100855, 10.770805470641914, 10.423960762332078, 10.203446959082003, 10.669422518559113, 10.576499198756911, 10.264183483495417, 10.473652469270698, 10.338417711834264, 10.545121014195853, 10.61506205778919, 10.682868543074536, 9.782885745186963, 10.295520430798582, 10.359768451653457, 10.361136869018626, 10.149422437908715, 10.304256660283537, 10.400282143942059, 9.697408296542939, 10.46471425187892, 10.023319950512043, 10.653377191553558, 10.274431197486944, 10.668917359608853, 10.383087738660144, 10.156069436806192, 10.313616199878984, 10.290114135602762, 10.45108496843598, 10.381892384034213, 10.462599750898496, 10.261193958636236, 10.437392691919626, 10.71901384428822, 10.29602371244756, 10.236700174264323, 10.267820031628315, 10.624295346136961, 10.450940184407077, 10.089200464805486, 10.284665404799156, 9.01458867281547, 10.23498042050809, 9.897328077746467, 10.130413480700941, 10.477184879301012, 10.057601228814367, 0.1403691454631012, 4.733126888296638, 10.693175588431977, 10.508652022231914, 10.048671972026096, 9.976687590471759, 8.4652569644127, 10.531331831224538, 10.239956713967587, 9.598003322943288, 10.486942561062007, 10.505863364324696, 10.282467905109801, 10.195616760485386, 10.365807178168359, 10.043993465347311, 10.523631935898614, 10.554502106892555, 9.208410469011811, 10.249223631195868, 10.077987430445981, 10.65495878055634, 10.316377577716628, 10.561960599882626, 10.186759529929258, 9.655720783126485, 10.736536263632628, 8.892447155949844, 10.453726243843658, 10.215668787313591, 10.433786489156658, 10.65466250661431, 10.492444602908892, 10.500063179762089, 10.395874323572652, 10.146740782360515, 10.444203634679727, 10.47119532216532, 10.360893290186295, 10.455929735763343, 10.460897852954869, 6.223093781985852, 9.825741587948148, 10.47024523465754, 10.406938384057282, 10.237880820815285, 10.418995497291164, 10.608568019567345, 10.249286130076873, 10.40355336781228, 10.494374053569018, 10.130590215398803, 10.078791093111596, 7.943726761861288, 10.381921771391115, 10.22768550563213, 10.231924807516672, 10.455322009519247, 10.374493454593802, 10.325430999002545, 9.380537696731215, 10.499012831678609, 10.44140230605218, 10.606328884361323, 10.203965231258968, 10.246888241382997, 10.433624572114379, 10.148011973477939, 10.132240358840418, 10.468765796656148, 9.947618638651253, 10.192228253461698, 10.38334068494654, 10.419959265197656, 10.296989235932545, 10.095239286793001, 10.293314949233068, 10.135587515451743, 9.590260752450062, 9.574908711768863, 9.991331526739081, 10.248136869147102, 10.603783163119779, 10.349109849783298, 9.703698619266854, 7.6059191668506765, 10.390429515140156, 7.5666122770224815, 10.429491585358681, 10.406490455094302, 10.077386498545767, 10.504633587572187, 10.064707804304, 10.565223487215516, 10.506821410870703, 10.393627302051252, 10.859801889752108, 10.452577400246367, 10.304790409903891, 10.20220590524875, 10.360624468480646, 9.651047898590239, 9.437864082626279, 10.262595457859009]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3766402580796875, (1.3221002505074608, 1.4311802656519141)
losslist: [10.745791690438683, 10.381770646898966, 10.446255111066227, 10.308390905987437, 10.505818971847608, 10.52524633087697, 10.400469484306052, 10.618770392851863, 10.404748431676397, 10.478956376997699, 10.562245541253633, 10.387617809731854, 10.332968531058015, 10.425488870895217, 10.259833913008475, 10.750906502716727, 10.257041274694652, 10.389917829701176, 10.517837262473991, 10.69393147493835, 10.396699078009231, 10.31934670708452, 10.06865820379595, 10.375738029411691, 10.514638565786646, 10.278315512344072, 10.676254540744814, 10.475390864494871, 10.179817867640015, 10.468595052798316, 10.439456767327517, 10.289279363799126, 10.381202686790937, 10.504570093296712, 10.193382803883734, 10.391985465861769, 10.49820136131633, 10.465143728033686, 10.402904066743396, 10.518575082313799, 10.56712068848025, 9.610334901327908, 10.32711457007564, 10.704177401070126, 10.491946317976433, 10.439404715067518, 10.54874313861588, 10.660944868564629, 10.534478932613021, 10.752634694088883]

path 21
init_u, CI: 1.4114938721987187, (1.3526212002314963, 1.470366544165941)
losslist: [10.451077142100546, 10.320115626490947, 10.416978129928017, 10.157903246279995, 10.511021863466052, 10.612325460624266, 10.417038653742331, 10.373129466126658, 10.705889275438189, 10.360872581228856, 10.76371101457717, 10.58253772237881, 10.504575542498204, 9.152094203761333, 10.48201894541844, 10.58686121322445, 9.829376188703142, 10.307299653343922, 10.53206809876837, 10.456888013728149, 10.45013190575092, 10.567399721648279, 10.477382257078578, 10.537378838277192, 10.498802052826798, 10.654980298701856, 10.435127561643611, 10.004335689201264, 10.350101964043596, 10.360447808195609, 10.411495394093501, 10.255493180507658, 9.450403346734458, 10.53026819602452, 10.483140200808233, 10.542342124881738, 10.463384966528862, 10.191265854316883, 9.924235769850233, 10.39738878220024, 9.394332149759702, 10.410021456724092, 10.373631398080411, 10.502817731866932, 10.449345109896718, 10.298075998257763, 10.11201420050702, 10.20341760576168, 10.313677250049702, 10.71364965774506, 10.487536810920894, 10.76562151895101, 10.70002791384245, 10.377593847984118, 10.582149065483664, 10.49730914575068, 10.040452911557987, 10.58035380931769, 10.852629517208308, 10.169369697418816, 10.500979626454358, 8.306883032213763, 10.64059796351337, 10.160383160702033, 9.1052648048158, 10.803209569488569, 10.562323454064098, 10.62360024799155, 10.662215593857987, 10.565610503354579, 10.198649043802119, 10.645074276696127, 10.392357437618733, 10.227305620828245, 10.714004706915953, 10.181338777285973, 10.141169749027227, 10.78755994071195, 10.50690484318189, 10.439740694554116, 10.170193020520495, 10.14545960766219, 10.58035668726826, 9.812863921849729, 10.764546949014017, 10.760642403702521, 10.417137524271519, 10.51966202769487, 10.769777920625085, 10.296173426300228, 9.909801746951457, 10.364764110486956, 10.444267599563075, 10.47589573069134, 8.907870976922007, 10.594188687662632, 10.734378532483541, 10.475363448233955, 10.453875176785894, 10.401520490058273, 10.655307457211242, 10.521610863965648, 10.225415191167638, 10.539718054027071, 10.724300090796117, 10.548080027215741, 10.645885179062919, 10.608086893689524, 10.500425223275673, 10.1903503711378, 10.545321466183461, 10.587268865281311, 10.727620591315565, 10.678812388594038, 10.474948687722874, 10.638337600774644, 10.350204556413862, 10.461289099923848, 10.702050948176522, 10.409335683741856, 10.706759741962285, 10.219295998109125, 10.521973247624162, 10.658145089681739, 9.383752415148408, 10.596400250193518, 10.872895416484473, 10.709242736984145, 10.20968761952858, 10.71984956307079, 10.556269086065413, 10.782594725349796, 10.485412349158851, 10.227819787986087, 10.466738362985568, 10.467821599056133, 10.389504364541375, 10.570889475677427, 10.340530483010687, 10.356238159506297, 10.50480510677655, 10.657699015703207, 10.358711027669735, 10.287828748632613, 10.484945839335602, 10.675544462718936, 9.99255611128729, 10.417415394866474, 10.831838551622063, 10.69438639200953]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.291210047182048, (1.2280807170489823, 1.3543393773151138)
losslist: [9.983686809497648, 10.597198095515145, 10.563657156005645, 10.61649936223111, 10.200908203409309, 10.72097790234338, 10.445051081427222, 10.189230644193778, 10.585224256711559, 10.449858518818646, 10.941414871894676, 10.362299155390533, 10.525389055059941, 10.375719321849784, 10.411697731322747, 10.799823968836304, 10.6656940154751, 10.610990505845058, 10.509128945110378, 10.116150917403822, 10.663264636945181, 10.857302965768705, 10.223083581998928, 10.594356507643724, 10.60543199526583, 10.409206007973905, 10.318816429701673, 10.536148059488704, 10.764808219275059, 10.212129058436334, 10.466163990426669, 10.379186560649888, 10.667363856299911, 10.377672872628848, 10.542665933121398, 10.845057110891194, 10.616019876565433, 10.903053342412443, 10.655061122528567, 10.14565856553143, 10.759759692063827, 10.509591693396345, 10.668031240404359, 10.542541258023567, 10.382149294708418, 10.989411889980246, 10.248177234363853, 10.468988579729343, 10.642327077578825, 10.476544795515034]

path 22
init_u, CI: 1.3727707408987087, (1.3131693317588002, 1.432372150038617)
losslist: [10.75943797403763, 10.465850079963573, 10.331112921312904, 10.686144829927862, 10.411263033572247, 10.472998072322453, 10.550407967981236, 10.595316535127141, 6.037875460920014, 10.380083172595587, 10.567762022553193, 10.353453111266013, 10.845443438873303, 10.699620648254514, 10.68113602357076, 10.787326267098987, 10.498655864196634, 10.755415390704146, 10.586584296604638, 9.061967811358011, 10.827326225123121, 10.336717243195286, 10.833450741525288, 10.277815471279181, 10.352843465599488, 10.730435171939874, 10.490274084456358, 10.386653464032834, 9.455837466937071, 10.271693611695927, 10.217822518961638, 10.595180383631497, 10.596322374105611, 10.572074634041222, 10.538011911144393, 10.751710225360561, 10.548560689153682, 10.535765914336984, 10.814520339258774, 10.6418852857012, 10.405909830159102, 8.899833359315158, 10.669274579729825, 10.705559063342879, 10.372193691512896, 10.622466986891395, 10.7622511032717, 10.704701625436222, 9.976690402493828, 10.30003043558595, 10.4457158785197, 10.498970051662214, 10.137395949373548, 10.876114999401377, 10.631948667066668, 10.668778570742267, 10.594565383298823, 10.418723532242023, 10.537994092243704, 10.509624538938086, 10.621602491844287, 10.657402749782284, 9.997721462038172, 10.54273764470011, 10.113605747557221, 10.366801120513244, 10.632189934587261, 10.680710683488389, 10.727894271291284, 10.739461325271025, 10.19882394668139, 10.388538510793845, 10.592422232900892, 10.311338503653332, 10.349815418979432, 10.927411752707343, 11.03212358399319, 10.228786056173913, 10.656385616247432, 10.617429793371677, 10.685666379321844, 10.44795890242796, 10.76568281526809, 7.268721871660245, 10.503120531555446, 10.648533279821878, 10.75485222319148, 10.51277639139497, 10.557469990545483, 10.475568125490163, 8.979702236108157, 10.507557690024935, 10.338169386605129, 10.876780465524018, 10.652195472141921, 10.366775826608917, 10.556088574155883, 10.600809406708176, 10.552414253407015, 10.76224535933243, 10.512861330253047, 10.410334706809763, 10.531774123334118, 10.560997277611312, 10.810254380018591, 10.426285364972745, 10.04775579301599, 10.939635737838644, 10.717339857789431, 10.39471411545083, 6.639750022796664, 10.535867291675482, 10.706648576422007, 10.58907685750924, 10.3112456313039, 10.604264532033032, 9.927233455325025, 10.575749292192576, 10.606732853530303, 10.523437669184753, 10.575630214244066, 10.471922942874647, 10.739903029984504, 10.479479084342138, 10.497799823957102, 10.557954663529156, 10.662724274991144, 10.745068249192013, 10.31074560312976, 10.755527376457598, 10.469029952368276, 10.50807706530884, 10.645854052018773, 10.562987671532744, 10.250847823520251, 10.37238017413211, 10.125086410522279, 10.7560876240264, 10.22552679093107, 10.544457671963606, 10.803943114680926, 10.54898274789836, 10.699414447339452, 9.955110749192102, 10.527658231076424, 10.536202192855605, 10.746028117617795, 10.528578056548207, 10.443536227689409, 10.43035379655774, 10.29790440251362, 10.50236202653157, 10.681541013054632, 10.584511669760538, 10.805002434949948, 10.568063096481469, 10.590461128943774, 10.541276267371979, 10.144505526382053, 10.561325574417735, 10.680708974690612, 10.642073066757009, 10.111427398591385, 10.671877380799728, 10.695038834192117, 10.43454786397634, 10.425855906141958, 10.454024694563666, 10.617563051344918, 10.429395743418219, 10.552086030459797, 10.660609693266371, 10.597835677693153, 10.478676799471502, 10.702743650692225, 10.791567738630054, 10.56595461416965, 10.684944491961428, 10.741177084757089, 10.901490975619804, 10.642322416753501, 10.915702852109142, 9.994522666229143, 10.418895416383897, 10.669448442247756, 10.710240086877317, 10.418568787375605, 10.67610689131548, 10.506409229371021, 10.902998616373084, 10.530757568718768, 10.364893944621285, 8.481769234240609, 10.532002485195617, 10.176515168749667, 10.252552156121926, 10.480359613079063, 10.122759498009977, 10.828620594267228, 10.638657667094753, 10.47937239240781, 10.52617274661595, 10.257230852603168, 10.8347660086356, 10.327614757176594, 10.509169470651344, 10.390677716498212, 10.762598158981424, 10.55131357997145, 10.670081684625833, 10.647718200195067, 10.250691033429458, 10.696239774584065, 10.300835582944918, 10.372295136601766, 10.76018997648753, 10.449563426891698, 10.643750669486055, 10.680371468722951, 10.380936719992281, 10.524066807454465, 10.66718916952198, 10.406789470356536, 8.84136107472854, 10.243100434760468, 10.57934993496432, 10.416271108843556, 10.535003650949953, 10.862560495269488, 10.381060905450072, 10.795085933280847, 10.58426535584072, 10.546179548059706, 10.573117894122122, 10.311101972987768, 8.887104681678418, 10.385661432236798, 10.547255778544224, 10.072197553043472, 10.524561854022126, 10.621276453339032, 10.69244813132023, 10.797343060496644, 10.301159680915019, 10.573729644839824, 10.592729130370449, 7.817683476212734, 10.540901744352697, 10.573377892641439, 10.62774444516627, 10.28750636359299, 10.688291072193536, 10.438031495123226, 10.09064919651079, 10.338434003571676, 10.55415690582635, 10.565816382960397, 10.47183867041657, 10.646527279731831, 10.686647866280351, 10.45041425634481, 10.426429319471763, 10.714128807533097, 10.583718340862248, 10.384088300859867, 10.480342100176722, 10.170699040199443, 10.579610792464567, 10.383774524493091, 10.383755374528047, 10.533111915276388, 10.788422691856438, 10.623717428150304, 10.245017880430048, 10.203291348991945, 10.665855396426458, 10.709401574267815, 8.968753861443012, 10.816738748282662, 10.597173778399766, 10.474191543167235, 10.459375492428938, 10.575388967242437, 10.4167912142198, 10.534642743827446, 10.645475933168544, 10.380101970551147, 10.517075104032052, 10.493446491464868, 10.275520208507269, 10.48172598310557, 10.426770087287837, 10.635851843418525, 10.377263180641409, 10.563874794921743, 10.407782386850297, 10.738696031196744, 10.647002872906397, 10.567741208845082, 10.499600734127974]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3848606156474457, (1.32386079041531, 1.4458604408795814)
losslist: [10.591104981727744, 10.248579131476566, 10.395111028380844, 10.40006488914874, 10.646877990292975, 10.617636290979384, 10.47132812969057, 10.096276674811904, 9.868397990130322, 10.538446918442359, 10.709029183424416, 10.572208509944009, 10.304634697130687, 10.320422809704974, 10.829001342093129, 10.59828160900713, 10.188426459502567, 10.497787333330677, 10.27277067428091, 10.341880184406255, 10.747086136757066, 10.3747448114472, 10.585522102463319, 10.383495505767423, 10.386630711753304, 10.355283177904777, 10.532617655615928, 10.651989286692633, 10.613062482515646, 10.591866091615541, 10.227606212248457, 10.235645390158439, 10.670098395617796, 10.718179027230226, 10.74337688450742, 10.677084591257401, 10.393366324900267, 10.533831536564728, 9.866537388566668, 10.513392567159391, 10.552391352721184, 10.591670916325311, 10.516356703953413, 9.561925647330764, 10.649643018607156, 10.321814092396203, 10.101074517836853, 9.150163448637564, 10.13239335548665, 10.243772328121775, 10.67994420580302, 10.32205808315199, 10.678572993788567, 10.777448583875056, 10.767269005150524, 10.520682038415208, 10.369556599804625, 9.437770475495727, 10.559542180034473, 10.668506394238966, 9.136370701961518, 9.911138978726378, 10.449566013940133, 9.016816044992142, 6.781930790884184, 10.737379486613072, 10.7115294848371, 10.353478216039381, 8.421579501197256, 10.713779457376873, 10.669421765436216, 10.623289437562429, 10.008302879958666, 10.048123934396058, 10.310479976820087, 10.539999694471522, 10.748819800322181, 10.605895105748111, 10.67935382913849, 10.733260877367574, 10.540427573607158, 10.598132832811338, 10.09587568974592, 10.528922074865166, 10.57122294703956, 10.53465262881201, 10.6809619532079, 9.950567492310826, 10.661272643010943, 10.31963558329451, 10.514030512384295, 10.475301324257018, 10.588637018549148, 10.341761094009305, 10.818132622666816, 10.62792319016844, 10.581848659670765, 10.448100080935763, 10.818240205948817, 10.463598005979247, 10.53377907986627, 10.606833196081967, 10.460071033504404, 10.002426205499193, 10.641958968460504, 10.088446437935653, 10.119032657459238, 10.593909656234155, 10.468766709123408, 10.334243252237137, 10.414899965360632, 10.668163812096806, 10.392232933988097, 10.69064342856103, 9.681064430164211, 10.534383756455679, 10.399824663093668, 10.602344357168361, 10.645912589499611, 10.837776110167502, 10.428418690338418, 10.730973993892269, 10.551665570963111, 10.746846326214854, 10.529851381467887, 10.346677584634433, 10.303337216234068, 10.604941051094823, 10.533874055405985, 10.354436373059489, 10.382086460790706, 10.531405890533739, 10.594422199696425, 10.355143377287533, 10.452850866971989, 10.74286383038163, 10.72433615290034, 10.555862554207831, 10.54320867549223, 10.593386463603233, 10.597564667606987, 9.382548447963662, 10.786424402297197, 10.798214718937864, 10.668145972414917, 10.570137230743335, 10.555913386163029, 10.397011040970735, 9.969047837727816, 10.396378290979252, 10.875009516297938, 10.459650094782859, 10.310791945528484, 10.877754681619363, 10.552732403362638, 10.413038722658184, 10.51847004018332, 9.036566879403702, 10.6130203654688, 9.929197814463757, 10.238978826080212, 10.487543888581579, 10.354770145470708, 10.704116856329113, 10.284091238015701, 10.550519603074305, 10.550400539088383, 10.619017371009772, 10.870790944382541, 10.66434022843228, 10.668096977807409, 10.859848491119847, 10.536228129240973, 10.978718643440711, 10.400252091890902, 10.623030651263088, 10.510333155997754, 10.41011878594391, 10.786622494441566, 10.682496741205984, 10.567090342915202, 10.884464773814269, 10.763774165145716, 10.527605534816388, 10.449151418745661, 10.752122344159146, 10.683827250948116, 10.389483750381308, 10.546627660982557, 10.5626743765498, 10.315412859968564, 10.831135696238595, 10.276346733547042, 10.441253790587687, 10.658675106102809, 10.436049994498894, 10.681312895270933, 10.671906180853307, 10.09476168267943, 10.215270237943864]
Most correlated pair: (14, 28) (Guinguineo, Mbacke)
Cut district: 14 (Guinguineo)
u, CI: 1.3161767085590235, (1.2597308408861814, 1.3726225762318656)
losslist: [10.316755493271971, 10.622706512662386, 9.660429996357731, 10.458546967331882, 10.543523212683745, 10.783062358835148, 10.746225754120251, 10.519593978326059, 10.339134268435217, 10.611870223356377, 10.745186058685045, 10.74657221852771, 10.645031677347209, 10.702105849937364, 10.673895489189327, 10.463440370840665, 10.760152719799438, 9.96619550775739, 10.646348876519967, 9.477363948223696, 10.748429955894503, 10.539069232651205, 10.565732144211166, 10.482668696571881, 10.430132808948972, 10.366991391438193, 10.479070807076377, 10.446454584022836, 10.422948901445286, 10.569929054696676, 10.094312215332495, 10.684980955640151, 10.465621093860086, 10.777357399662876, 10.461335647071849, 10.704085734539666, 10.538207668369916, 10.58766958576302, 10.4236848411844, 10.543836545950784, 10.15930724635567, 10.663780020946515, 10.545103568154657, 10.740861702271186, 10.503640427836002, 10.40427204428881, 10.466613928513993, 10.645527275303307, 10.112243720814167, 10.705107206191338, 9.708467070867357, 10.376234657005824, 10.609307532781324, 10.684758849756207, 10.727055306572572, 10.696019100403653, 10.58915308765207, 10.473734011936084, 10.735193422118565, 10.438422184308651, 10.667089961558537, 10.676766347025442, 10.677645147432145, 10.548906573032674, 10.803887998139569, 10.410666387970387, 10.501945024318307, 10.182420311791672, 10.621871313124121, 10.610135148068741, 10.58528983589097, 10.580875544793628, 10.701797548381974, 10.683315343013701, 10.785522329331501, 10.583603699176834, 10.576147526671102, 10.6426145512878, 9.475424138179415, 8.526480648722016, 10.780283093658888, 8.410158349508444, 10.478923680746904, 10.746961035892468, 9.9575242677477, 10.82220100442622, 10.819609970131314, 10.600847647428193, 10.80898813868799, 10.438059110949279, 10.493609424323544, 10.314254189258714, 10.576329118696254, 10.765708829076184, 10.689598077377187, 10.75086109662635, 10.794119341255186, 10.710935595536688, 10.46013677455598, 9.86433723309662, 10.558191182294012, 10.445807320987733, 10.620589201798875, 10.532233638116956, 10.474019787210542, 10.402985523776648, 10.66998633490407, 10.583833542583196, 10.689839145023997, 10.940862243613777, 10.511832911716779, 10.340984116022495, 10.284259583318217, 10.323396819991032, 10.599603657636312, 10.425963397310987, 9.785779311640624, 10.596314501322396, 10.240623051437451, 10.71291222887335, 9.97630072857959, 10.768972861580576, 10.729019996108379, 10.502431479514811, 10.511202305356802, 10.291693891584442, 10.660491923335744, 10.758933675414115, 10.702150350493417, 9.91444439224542, 10.516640673714656, 10.757701889262975, 10.563385201512673, 10.775534637624304, 10.390899538916644, 10.579146869712998, 10.641612981637925, 10.554073722050765, 10.607675881431376, 10.454357396045332, 10.67645320518677, 10.404105782324912, 10.667932116118168, 10.445327474877793, 10.545448275126608, 10.896972475167052, 10.523532251169513, 10.714340618392498, 10.89164161627565, 10.642966518580527]
Improved path index 393by cutting districts [9]

path 23
init_u, CI: 1.4574138734041782, (1.3914073747767528, 1.5234203720316035)
losslist: [10.504186224825627, 10.387992201422836, 10.559567532549273, 10.341933626268647, 10.401950934133017, 10.64091451445577, 10.373574153982773, 10.643098950911028, 10.30802425062872, 10.304996103626973, 10.571883654243619, 10.801691357302959, 10.52028903406042, 10.28982236536911, 10.583129132649827, 10.464811341348407, 8.73712761749468, 10.281555816368899, 10.64908448303127, 10.522757761711679, 10.573346667724556, 10.421317729212298, 10.531369402220168, 10.109236893566695, 10.265981691352973, 10.35381450614298, 10.522509229339324, 9.70514471078724, 10.498369420781431, 10.76994478495297, 10.168323875746726, 10.6496094963168, 10.069235856909824, 10.386575300739832, 10.009887272791522, 10.312912168297446, 10.666412776914141, 10.23384307806064, 10.392467181417787, 10.66576698878946, 10.384653088155305, 10.25513797964965, 10.385474387641223, 9.626448711493818, 10.140502980289742, 10.83193976717975, 10.412820442917523, 9.732209312044645, 10.869857025877092, 10.472795253260163, 10.405093289600883, 10.522498062356759, 10.375251181774226, 10.345734402710715, 10.754835811086913, 10.77376537135991, 10.498753676484013, 10.390971102819174, 10.618907989766962, 10.298110803924892, 10.519891636480052, 9.983824582815053, 10.060804437819725, 10.197859916563857, 10.783010622378344, 10.434444156482344, 10.694382251817336, 10.364083828958302, 8.007515703960824, 10.347550749944327, 10.641905620086604, 10.499395827518224, 10.34260340371291, 10.787040213788856, 7.865063771450998, 10.21694312422628, 10.573455646079356, 10.457956528445706, 10.295833811236188, 10.457524851035776, 10.714752444250145, 10.367849361889176, 10.486930750119898, 10.591627332041597, 10.521177290474691, 10.681985237233087, 10.63416345675114, 10.467410719097755, 10.73580636637934, 10.033393704421012, 10.493125174837255, 10.178606828654534, 9.725846338555936, 10.410524669294881, 5.927396071274369, 10.44656787020171, 10.468279677693092, 10.333372077844423, 10.56590300321402, 10.340630630183123, 10.579105884729415, 10.58651577745481, 10.352217485177226, 10.51173454295034, 10.371980252571802, 10.652234007102207, 10.359776768850377, 10.368883612739472, 9.002666598694429, 10.62303719706729, 10.57821644655607, 10.513726704597788, 10.407398566949038, 10.548522256838753, 10.586809006762952, 10.462073790382476, 10.581212354366139, 9.889351234140427, 10.645851388030868, 10.549369010847983, 10.655148971126085, 10.42253533088788, 10.543300018192271, 10.46871387542897, 10.475913258705576, 10.566869249182176, 10.402094496137789, 10.600828778487736, 10.822255828170803, 10.864986602473213, 10.515332405600438, 10.227123935286096, 10.627658875324556, 10.661838266222988, 10.266814634006995, 10.335430456959196, 10.601031242136463, 10.68321957930677, 10.460549245950395, 10.618718836467643, 10.635066918565526, 10.51847905182878, 10.803062664651616, 10.608224829337912, 10.471683475849622, 10.494925945104022, 10.367842106534058, 10.452407021788364, 10.164663671642685, 10.369188089462305, 9.866720559179297, 10.48565242346715, 10.551018739233733, 10.568408691771662, 10.579871722566113, 10.363227323868662, 10.532230635629347, 9.363781745017459, 10.503026110215744, 10.11675715078716, 10.409338281099796, 10.60253393414442, 10.722352254730891, 10.502210409104032, 10.338373225983766, 10.520474967672845, 10.415623053909979, 10.395842146255765, 8.4446094963997, 10.643555918238391, 10.323024669366646, 10.773143570404912, 10.327223279158366, 10.583141319492581, 9.825871232325737, 10.481678803075985, 6.319492940553285, 9.991962735687896, 10.674523516250957, 10.466982527496155, 10.513828420229641, 10.654243837432167, 8.193302997459886, 10.480354929274425, 10.544301722165716, 10.65541650412757, 9.649375846592282, 10.32969281304347, 10.430061792833198, 10.623304917985827, 10.689709967525122, 10.775664692172814, 10.694467048836337, 10.89967947341321, 10.349394915684774, 10.628954056494385, 10.590050346576007, 10.557004408276853, 10.654832423083837, 10.205039484099615, 10.509589615525796, 10.329132568105969, 10.187319567264899, 8.559416395254253, 10.59905488877524, 10.215851599638968, 10.656800794062587, 10.758100583402511, 10.033073133629237, 9.571664888126316, 10.473372471168165, 10.374619731725787, 10.417459123822916, 10.57348490323124, 9.264930719218032, 10.340004493738652, 10.36793313445767, 10.318284954933922, 10.557290581737512, 10.756073306276033, 10.570612381365397, 10.106796812693503, 10.611140315629049, 10.39815472451548, 10.367202007554079, 10.63407147606028, 10.238364840787408, 10.518081890562392, 10.426763600105673, 10.38870200082062, 10.556415966439944, 10.147626487665319, 9.13812942962285, 10.446677148924811, 10.576566588331238, 10.361061226358602, 10.503679144742273, 10.363653753278532, 10.24549868163069, 10.387831691525001, 10.612019908597233, 10.42974222973279, 10.750049620118373, 10.661649415387712, 10.602629239152021, 2.806627120895735, 10.66214699949675, 10.48247286908778, 10.496216634146117, 10.680062698074156, 10.687475063845891, 10.573546560686763, 10.544481106135754, 10.230200817598663, 10.434638751328032, 10.456814809674745, 10.497463493010203, 10.67966417717499, 10.625330323312161, 10.358717131972142, 10.571333709337662, 10.520445162820286, 10.823499401362085, 10.592719079670598, 10.630649073707662, 10.578779140202949, 10.917227938545661, 9.536709986826175, 10.624984782058412, 10.147894210989055, 10.465364862231585, 10.67270587036777, 10.581517306118691, 10.809069619491057, 10.855103870307566, 10.286021643272578, 10.839162663160954, 10.355792850880212, 10.596546816588289, 10.474896670845297, 10.282432625768166, 10.722246952830682, 10.881741329460153, 8.187429376410295, 10.453049274541753, 10.48799719193582, 10.381629617080382, 10.398467069749698, 10.432669743084402, 10.389868641007942, 10.184520248542169, 10.681311186356318, 10.463912050390633, 10.719941451367308, 9.517312463609853, 10.717047736876243, 10.563295246187574, 10.567013350093577, 10.325065249159794, 6.810437136238732, 10.479477126630714, 10.861815961672209, 10.060876434746671, 10.447040074118656, 10.790085265777089, 10.591234018044005, 10.33936593991321, 9.478570024187766, 10.572496231474586, 10.60978844062841, 10.452566094782858, 10.59011683200324, 10.521159903784156, 9.94243700854894, 8.395522349233715, 10.409362799297554, 10.719668960987818, 8.681577860391046, 10.638346356855907, 10.413149890001149, 10.41332005875789, 10.572701366709605, 9.862391241294986, 10.814030430327238, 10.369847325049545, 10.527708971706815, 10.173362203509077, 10.639499670841015, 10.793507254199383, 10.858125833167295, 10.485632140533681, 10.064841203367962, 10.684210898403865, 10.909557717202391, 10.62523504684011, 10.57007047918618, 10.530074737396287, 10.289207882222664, 10.985617364707311, 10.707152062420926, 10.600007052051044, 10.648924538055983, 10.271148836471598, 10.63917329118291, 10.458615035620806, 10.70054474080672, 10.53680923461371, 10.323875081041777, 10.225957688739072, 10.588774854969468, 10.352249280375307, 10.463840066411713, 10.437714757975263, 10.05716198418106, 10.791635178836973, 10.412077530781993, 10.655941703761584, 10.506905425446563, 9.649217958877921, 10.485254941540855, 10.503089071043618, 10.430072542416307, 10.612727317612038, 10.614233861621896, 10.688357437377366, 10.677891049960417, 10.636874336280203, 10.466027593573152, 10.846925649893734, 10.716170441055947, 10.52253051449427, 10.485026311939421, 10.377019195299678, 10.755942012824798, 8.276103067245316, 10.612610098795498, 10.268128890007876, 10.208019393265973, 10.663728283640197, 10.500794490197611, 10.637841743741578, 10.733700901010518, 10.494170368061784, 10.502174954973837, 10.427185747843184, 10.79534769366233, 10.634981843565477, 10.603840783050913, 10.254486527197383, 10.546221543089958, 10.630135979834986, 10.303852076562517, 10.395428563423316, 10.53263700527086, 10.89849896027603, 10.358185466310266, 10.750228642291413, 10.49903328075364, 10.604738962040852, 10.696683870556397]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.355324837184309, (1.291322751439255, 1.419326922929363)
losslist: [10.541579529659089, 10.92862396541646, 10.580106970239957, 10.365074561876504, 10.06268978206358, 10.132577345730594, 10.54633006755273, 10.499309706414785, 10.080180546495267, 10.65510174711436, 10.14904103944668, 10.310416032084122, 10.058124273678175, 10.549348529910072, 10.529210511771, 10.697023706758877, 10.640421902908928, 10.928810569015278, 10.673230531345245, 10.512676368085396, 10.43569466873265, 10.57653829317573, 10.843262677560178, 10.491646748347073, 10.462047913892848, 10.623084618113607, 10.452592817177605, 10.442770779358009, 10.594234222052433, 10.506367723600714, 10.436179646464517, 10.32696203459524, 10.855282272452769, 10.586379710780871, 10.266246967322855, 10.832584001516736, 10.292800726296676, 10.963236544074045, 10.497790923641066, 10.642272517853016, 10.510732243056683, 10.117048145054168, 10.618795377132328, 10.242416972201028, 10.500721836293462, 10.465067552641768, 10.4043304975537, 10.723769842721923, 9.688759412133184, 10.603789508824624, 10.547922341636383, 10.568484294084415, 9.337469960373264, 10.696716092168437, 10.793799831229144, 10.396184827675876, 7.026155608605094, 10.32804222861029, 10.861355973721645, 10.689677161647317, 10.356130645084518, 10.782326552571398, 10.623211020624158, 10.350764415847715, 10.178408018602367, 10.687088430822119, 10.387605894951747, 10.622440543707818, 10.664469351710906, 10.18313943565245, 10.619759797415925, 10.887848415576006, 10.481449439287582, 10.407197499473622, 10.221535792165541, 10.388265634088665, 10.46072139099548, 10.311984803751255, 10.596229014661747, 10.499412178954621, 10.693951655514853, 10.590667270195441, 10.17287867285888, 10.329787230457942, 9.509494364356764, 10.514906922648162, 9.325946243199132, 10.61370182840356, 10.559558953502334, 10.740470841637313, 10.343560984737941, 10.52401969146648, 10.764324613195408, 9.859425650444875, 10.468457933422458, 10.68805830179302, 10.127466791931935, 10.309389937503887, 10.092200549922763, 10.594946067794883, 10.639327970754005, 10.306061808149018, 10.701890342431426, 10.695849373187475, 10.631162872400933, 10.298047324397535, 10.4336910011814, 10.635385190246168, 10.697257475722548, 10.5565231388849, 10.54134870822587, 10.450036365222438, 10.296253773443139, 10.531867693018363, 10.64293222570571, 10.601297341303006, 9.878083771846729, 10.504567316333436, 10.776782246391683, 10.744920614922043, 10.753543027503436, 10.715293284054923, 10.654841509409682, 10.544888926147584, 10.815099645346828, 10.471470557483656, 10.649794617786476, 10.435539381241258, 10.384508581409222, 10.36632318945565, 10.576481593096792, 10.576898163488641, 10.354196363774399, 10.548866757349055, 10.855349119604488, 10.422931152467138, 10.403882560275614, 10.698694793982613, 10.157435076316188, 10.556232905207924, 11.125369327191997, 9.828742941470841, 10.440991272932337, 10.408059508940008, 10.710182393740451, 10.618879654681516, 10.572113775339405, 10.14337212556081, 10.753800870304042, 10.47513779043355]

path 24
init_u, CI: 1.5217708963790315, (1.448916616932289, 1.5946251758257741)
losslist: [10.671763084289317, 10.317317346678992, 10.434644032069725, 10.560074327857784, 8.86832697349916, 10.342215088452157, 10.504107892598762, 10.355714111435443, 10.671721192146403, 10.25236979099721, 10.494393129325154, 10.306594615760185, 10.043684780169205, 10.73856478340542, 10.186506221928799, 7.529404700122781, 10.319380782580465, 10.419626349993456, 10.605618381084138, 10.2280494596992, 11.005139306037735, 10.35544791721383, 10.32126218185663, 10.480277964701582, 10.19200372455486, 8.288505056567478, 10.428341886033666, 10.170898054543672, 10.244631921049367, 10.578190913864363, 10.471251607392631, 9.914022231521063, 10.558973697464715, 10.497897587981166, 10.397314882599911, 9.745225933675153, 10.20542032931044, 10.668558862857381, 10.707458167663594, 10.527778196266638, 10.299145692818314, 10.336373052813096, 10.528487951172172, 10.615442302854573, 10.529526336557792, 10.422360421620004, 10.333960808332824, 10.075905511833987, 10.513052364845912, 10.253688489890186, 10.354247935497222, 9.798672325273198, 8.799053803117054, 10.33960591311123, 10.545790300195346, 9.895302812887316, 10.48869979772168, 10.61877517413885, 10.447208301040309, 9.914186791480116, 10.22017084034934, 10.088809970226626, 10.60010881245215, 10.386809621339635, 10.135132008735377, 10.887733477417408, 10.345609901361348, 10.360718416346014, 10.220874440303408, 10.516398017566557, 10.119226467131506, 10.455479096356584, 10.032028129027944, 10.278966943216552, 10.358931998971645, 10.333920826366422, 10.260238807009793, 10.246316652118537, 10.568790325341158, 10.265401525304242, 9.477386827518032, 10.330717798232818, 10.386817608959293, 10.293246953099343, 10.352127158580975, 9.9424367662146, 10.358587558342885, 10.566379516542733, 10.172765261870529, 10.597882554776941, 10.698142908910828, 10.337928729250754, 10.374535584111284, 10.640780158317082, 10.572924257891192, 10.377700856716139, 10.497328386473558, 10.494102100995743, 9.602275383321299, 9.089322914770017, 10.397004981280086, 10.444337791157839, 10.324109623819854, 10.069660435009979, 10.578866055993243, 8.277885872033089, 10.53444614495834, 10.285383321495074, 9.948075614844926, 10.282529043270955, 10.65110367638132, 10.381555849455413, 9.893858216004482, 10.221856034511381, 10.33921644079233, 10.140698778047419, 10.319611559704908, 10.497063460509107, 10.339742321617885, 10.527174507967022, 10.506180940711145, 10.489936654490743, 10.435048570955015, 10.365034487965083, 9.608465294255236, 10.599722145535969, 10.403547386437804, 10.267406774531137, 10.265608181990691, 10.601877860694094, 10.433032024771972, 10.516897660218882, 10.515519760197066, 10.755501564212338, 10.32732576277656, 10.16500235022662, 10.434429348751435, 10.393992551233028, 10.388862687980469, 10.464815660140747, 10.32956242326721, 10.626447956040424, 10.413053200469497, 10.286145462381683, 10.622928021561103, 10.25731355644089, 10.607226027697644, 10.70210871348166, 10.412270274285543, 10.624932374585125]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.3828002919504883, (1.3167226409362947, 1.4488779429646819)
losslist: [10.512132987951771, 10.603932498397498, 10.195074378451823, 10.32128871576488, 10.36845501582091, 10.60330119141467, 10.576861502222924, 10.574791183222253, 10.305516054556117, 10.490617443942616, 10.377677092651549, 10.628481478282353, 8.890828986772409, 10.655526677494132, 10.764000630246128, 10.169063204415858, 10.339084183143173, 10.31809401757944, 10.628471539858007, 10.661011295534063, 10.356851471144282, 10.403212449199382, 10.651424100849859, 10.575014921569064, 10.576892960510294, 10.803341871101342, 10.41150454212291, 10.711213089814704, 10.57663613933609, 10.671125871331423, 10.405443604653149, 10.350175509432276, 10.311784427032705, 10.465189168833627, 9.467787883124638, 10.185188856372898, 10.725658933530662, 10.4909641219625, 9.710416443763245, 10.445127362890153, 10.444912245378697, 10.436875249518987, 10.819014404283338, 10.363542629349373, 10.563893722664401, 10.538048852213228, 10.562429932655354, 10.477445038762852, 10.61011780069254, 10.498901428587631, 10.395233015158, 10.595489222448194, 10.276193588294518, 10.86810995272391, 10.414920602709834, 10.959176577283156, 10.678213031347523, 10.365573131690322, 10.59519134880219, 10.511083757418534, 10.458705899737186, 10.726624402694151, 10.670743006415503, 10.818822029637198, 10.308740013594528, 10.444639172666173, 10.670423426136802, 10.414241114565545, 10.514730194002315, 10.567804927299559, 10.670661365304229, 10.801452370588839, 11.20777732697262, 10.47749583252693, 10.51791457392889, 10.693455699004916, 10.671515493987243, 10.338566260465479, 10.556977217213086, 8.52903725865234, 9.888516476110038, 10.420281963063665, 10.563653766893234, 10.647282575926075, 10.526089772391403, 10.4213280469645, 10.523220259634712, 10.44340699685224, 10.448145406735284, 10.456113057810025, 10.592076358347372, 10.58854536142002, 10.71160391435687, 10.479611675574688, 10.435759357093207, 10.696464126135394, 10.564848075198897, 10.203173561232155, 6.730668402140451, 10.406771045220115, 10.849705086598235, 10.775788708900889, 8.529411478289305, 10.728425695822907, 10.464434166857497, 10.629194166705716, 10.694022238633558, 10.585450933422258, 10.250633613019255, 10.747055601069562, 10.559124960765155, 10.684509787877602, 10.770898795517512, 10.571321725638807, 7.623075622699248, 10.600775234330028, 10.596136969836099, 10.27923951628133, 8.765675947633182, 10.577017125411688, 7.394126781967401, 10.36449293134598, 10.774827282013057, 10.561546492882002, 10.475545329988995, 10.510553810815463, 10.819706683784132, 10.727337026979294, 10.986145243563502, 10.584925426380918, 10.64305147405224, 10.391510551925034, 10.580161984354955, 10.376540939651328, 10.506411297689258, 10.665335277474915, 10.336952582098892, 10.494550356526261, 10.51121548944818, 10.693150578977551, 10.051904450769051, 10.54710432484416, 10.57838719524342, 10.84110035352204, 10.64406505766203, 10.396750449434702, 10.306809411721652, 10.799434646436836, 10.492522721626765, 10.510513705394317, 10.62616722819106, 10.142328325040554, 10.536393279822681, 10.737930850603663, 10.745444307007084, 10.565264352333722, 10.351561972435684, 10.613681889484395, 10.593584345075877, 9.958555351781433, 10.861881785114596, 10.563989531957747, 10.616775745558405, 10.64400576665214, 10.696314910104809, 10.464803676221702, 10.485943235176236, 10.774908198604392, 10.65409979741384, 9.652904992723702, 10.711855221699388, 10.012040579710648, 9.546794689136522, 10.534335937829184, 10.504521446431387, 10.365533396678321, 10.367767414098648, 10.298492183081702, 10.815881810324301, 10.52128816674433, 10.853797636959065, 10.446586932173304, 10.599355909816381, 10.76833078242996, 10.277494419705741, 10.512443962619253, 10.456277603837526, 10.554299840613766, 10.637573232149355, 10.72831801673614, 10.569096938314535, 9.301649287477167, 10.615361296974234, 10.754140412018188, 10.386934184086938, 10.588291164308188, 10.729279715675636, 10.49341530980361, 10.700869677851605, 9.812192452812097, 10.75391954321348, 10.248639621476315, 10.738843371896484, 10.543615616022109, 10.673428822884553, 10.28246435399689, 10.154196209008246, 10.942938727419003, 10.693977272371397, 10.657560832680533, 10.245235985499583, 10.442407810339759, 10.467895228494662, 10.312362274689812, 10.554671025594779, 10.64075388494906, 10.346811727767106, 10.708498260274485, 10.370443592216494, 10.471066932820646, 10.377555509219517, 10.727974855036344, 10.851093217903214, 10.537823608981046, 10.662375324773667, 10.604911577161575, 10.402922348508934, 10.324327920655048, 10.34153140680534, 10.314826855570846, 10.868215153346295, 7.570257055795288, 10.804290800824244, 10.617397621580363, 9.373405204792643, 9.093777993526814, 10.663025049791406, 10.297039626059478, 10.598751461836718, 10.563028433806338, 10.720573443383474, 10.680849268385915, 10.58285222518196, 10.657237943627251, 10.448225214494034, 10.463805932891436, 10.60434048603844, 10.612457755450839, 10.742993955474034, 10.78695678160926]

path 25
init_u, CI: 1.2977156649273933, (1.2540482196032023, 1.3413831102515843)
losslist: [10.264168431901226, 10.617425653270047, 10.795569287539802, 10.500014745756742, 10.370633440420969, 10.945162604165688, 10.699222314705661, 10.809662453571486, 10.518404846164673, 10.405972948776268, 10.579335054362724, 10.45406519565476, 10.291870615324658, 10.713319879982302, 10.557269527995704, 10.331099254991956, 10.564706369196688, 10.513860476146023, 9.657609280222458, 10.480941193037218, 10.379024017763264, 9.614384053626967, 10.670446848604307, 10.651677161858316, 10.39756381761575, 10.453674792873123, 10.633133307751296, 10.497553368494305, 10.767177767381394, 10.482942829967095, 10.032009460504558, 10.61424768064264, 10.574722844443649, 10.469291334686446, 10.63630775036434, 10.444528912840607, 10.594421797845197, 10.108004940731526, 10.4896346061992, 10.370373932905041, 10.5590367630346, 10.586487367468976, 10.709701797538399, 10.821494679468085, 10.824568523594133, 10.561111655282561, 10.661764792735626, 10.564825149558372, 10.494702054151457, 10.543209409439822, 10.475895114946766, 10.726414202680981, 10.652578768302975, 10.607249765990362, 10.622633406816616, 10.433743507136905, 10.514332046097104, 10.642037626714613, 10.593916178559867, 10.642673825000198, 10.511277044324556, 10.373760935066239, 10.372278321528844, 10.901848353367852, 10.506578696176803, 9.781984030790328, 10.569444650846444, 10.66688246546899, 10.625908280133348, 10.525741993541395, 10.378714524680541, 10.442053526017819, 10.382544703608874, 10.623319784681106, 10.488184243951006, 10.577752528597735, 10.350933414185652, 10.74747155380859, 10.006993868391039, 10.61871335082529, 10.474828890754914, 10.604964194695048, 10.50128760691058, 10.647869055524776, 10.473551064163923, 10.565012605997827, 10.85624816131617, 10.421210575896284, 10.69033767080788, 10.391166772105658, 10.764736269276652, 10.457217773778131, 10.327985712211726, 10.468808172599719, 10.67176049946831, 10.815528953915177, 10.474546061826965, 10.40812311396436, 10.500825626373961, 10.47237967439931]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.1994347195531656, (1.1399588128009928, 1.2589106263053385)
losslist: [10.850790244585136, 10.928673230753917, 10.649736466467708, 10.488701321737707, 10.931650422106678, 10.750097946312422, 10.54897442907755, 10.511697487255027, 10.501740216586692, 10.74035287966014, 10.93032758761169, 10.631957681607599, 10.68350878815433, 10.84299079237932, 10.43026263704662, 10.64928772781078, 10.483546155019292, 10.34530339773534, 10.611982322557031, 10.776093313799407, 10.590202607898645, 10.023954901372418, 10.46283431146914, 10.653813080756823, 10.74464020682255, 10.586959527087387, 10.507107959337596, 10.777350784730467, 10.431115586730588, 10.764827521583355, 10.739596919931802, 10.679374864239968, 10.788930328551837, 10.639635812217099, 10.553131148981334, 10.520959381453645, 10.882027782857755, 10.723805276009056, 10.787052118757927, 10.764411492027548, 10.442618694604803, 10.747006948208218, 10.717491604440085, 10.653979345245459, 10.839189481110626, 10.480320671737084, 10.653124495363866, 10.719749716084, 10.852400565023792, 9.811036716631445, 10.925869150453511, 10.922162018354452, 10.720630261688353, 10.713244520380137, 10.679604280910068, 10.866029799712923, 10.947553092521472, 10.504326467044317, 10.735914917645555, 10.603070372864831, 10.521265234769773, 10.49689356586604, 5.636290945273131, 10.552299163439644, 10.615592982496409, 10.63290927867362, 10.481943858390503, 10.655177513488892, 10.490342208570262, 9.324322587170167, 10.601101613592895, 10.716379875037283, 10.828445212575408, 10.748594164098026, 10.884061683429703, 10.369892970462203, 10.606566674710473, 10.734284002581362, 10.406616102897772, 10.71798554641914, 10.197122676988158, 10.924288585293839, 10.280964088558935, 10.7930584760742, 10.402270764071668, 10.241039566527942, 10.71229505973335, 10.715253094216555, 10.641939751888376, 10.840161735171641, 10.669144279119491, 9.76858023536445, 10.718705503061244, 10.497931785724102, 10.53877282126107, 10.378140563892991, 10.99117317988371, 10.803697475293552, 10.892442266881732, 10.461555545950363, 10.446449871792067, 10.14183734737224, 10.545086179002391, 10.527583690968145, 10.874259119555306, 10.648845699417725, 10.884371330470588, 10.764326073017315, 10.858893545248682, 10.659822522475684, 10.59389545664817, 10.764760569341044, 10.827118181201863, 10.718388571701556, 10.700208351119013, 10.619636822018402, 10.703880651385683, 10.841291256088587, 10.994775240985598, 10.583251628459697, 10.547029903737174, 10.507234770574234, 10.543238460429343, 10.60106216923182, 10.687865189765603, 10.799548534741106, 10.577610817485784, 10.505116776767284, 10.615006013330092, 10.562914356606075, 10.820923917534886, 9.552413249847595, 10.84032858214506, 10.636035072958743, 10.762941900866355, 10.579413443455449, 10.930984776826296, 10.622637545931333, 10.788233264155235, 10.641314885944258, 10.664904115934075, 10.662384813755681, 10.808737510507148, 10.804962892605463, 10.770346414875155, 10.570781465979632, 10.825139925783576, 10.754016679819836, 10.753815332468054, 10.723888955253868, 10.586733057926455, 10.35707398775583, 10.780095513056054, 10.880338354044772, 10.671406792849249, 10.859815311052142, 10.952675557595555, 10.25688806356109, 10.591850150104495, 10.603107860054918, 10.823676777055498, 10.25860081939012, 10.484562813482727, 10.695455362207593, 10.974484959030873, 10.634510380648189, 10.047814728275643, 10.754160205189551, 10.728291176185188, 10.847264170930096, 10.761482527591614, 10.74724039952714, 10.940737089820283, 10.622132942710124, 10.5547920299789, 10.69219486144116, 11.003872896912352, 10.421056009779988, 10.574072339414805, 10.93202160425204, 10.522810336694064, 10.001537605685478, 10.724176779261173, 10.639961754928052, 10.587850942072379, 10.799395818825875, 10.630996062290935, 10.616606436935594, 10.750609650925476, 10.635888657957299, 10.616465091321837, 10.846702417042437, 10.774035119747316, 10.368171208629642, 10.998086920411199, 10.78251555465246, 10.308276324706528, 10.543215213234927, 10.974513970248573, 10.66339052142526]

path 26
init_u, CI: 1.3394279293908014, (1.2809907400793428, 1.39786511870226)
losslist: [10.74997307750931, 10.499699352075714, 10.87221984878308, 10.687430315335908, 10.6101263216784, 10.656948208428297, 10.592226269405165, 10.29747182294581, 10.54257044376745, 10.13107091024942, 10.523277169219744, 10.57030831784471, 10.54947805252844, 10.5227257585261, 10.571242013319251, 10.01814742889924, 10.289318456714538, 10.597631014785414, 10.560320186128209, 8.841932874766968, 10.51432086869353, 10.70716128178737, 10.372637655961512, 10.611045757016601, 10.583555851444313, 10.691050045089309, 10.631210143499532, 10.446855423510936, 10.612874234357289, 10.138903913753964, 10.614171398918215, 10.193816047750355, 10.652828695618105, 10.659715984633753, 10.442038192372472, 10.80155141997261, 6.217072778460914, 10.459634553644017, 10.488181667938589, 10.646210028228097, 10.549945780474687, 10.689667099387542, 10.709035026354606, 10.583552089811947, 10.338942962885294, 10.246308038021699, 10.240770215944124, 10.23528583982438, 10.64827746744778, 10.344597743615589, 10.369938738824313, 10.59416302358415, 7.160984031799024, 10.52811316323463, 10.733824131748447, 10.743120375837114, 10.476887851860152, 10.383070731415616, 10.638844612823059, 9.043774989293503, 10.577273752785596, 10.473846258810951, 10.443118125324505, 10.512677809602053, 10.815063201891281, 10.8314739278909, 10.753652806005393, 10.589126633361952, 10.865433212685264, 10.714280263081399, 10.851106680081186, 10.782791106235862, 10.691516778911545, 10.724226196579007, 10.535219419571927, 10.297360604516339, 10.524567179315511, 10.505727016714351, 10.516918043671545, 10.742605239558737, 10.769193013048485, 10.795000799914884, 10.516520377536558, 10.947875353789273, 10.553255764840651, 10.632153513857615, 10.504906111483304, 10.601630159364774, 10.787286853170087, 10.522879279389688, 10.597104641264242, 10.69895894878007, 10.68213378224685, 10.609429135425149, 10.528046977086362, 10.587470676581239, 10.57291867292534, 10.512963997282013, 10.378100321782728, 10.50095531510842, 10.40964883140753, 9.94179375635871, 10.63864620780725, 10.318643402368984, 10.603425310102761, 10.594788193828272, 10.562746192990035, 10.70402780421937, 10.737370116388318, 10.269290036011922, 10.419499597746691, 10.629470986799962, 10.738821224556718, 10.649576059194644, 10.620588928893387, 10.695329420780913, 10.686996961132984, 10.51037349079105, 10.452188442322864, 10.649988697511697, 10.63483043751155, 10.831919106314231, 10.839199534832538, 10.5070270828583, 10.324611100417266, 10.517971475650754, 10.2978719704297, 10.777182196030418, 9.892169855766419, 10.656035954148374, 10.649762234697763, 10.392361514710872, 10.555972533910928, 10.189604629420721, 10.527445931353165, 10.668753205833502, 10.564930442479769, 10.722081442445294, 10.582383541257148, 10.302268007816046, 10.578972366287879, 10.63478209822501, 10.53016557080659, 10.66017148536814, 10.845452092370355, 10.383454002629772, 10.355771693627737, 10.651416677281238, 10.496508538120617, 10.396740524245631, 10.899168666543941, 9.81522554660722, 10.613059158957462, 10.74731512273277, 10.36534192730837, 10.365535989004062, 10.637257458479434, 10.644137968083953, 10.666524107910211, 10.18071582834198, 10.697778503472849, 10.877273119957984, 10.151569967923376, 10.404193768119326, 10.68183298883615, 10.583606330014197, 10.78822402778791, 10.734620927429091, 10.47777766277788, 10.443429000958748, 10.375398469062096, 10.260809349485099, 10.520043306447242, 10.615936232308254, 10.601949859365194, 10.076309330303113, 10.433510230336152, 10.634955056325111, 10.594329790774921, 10.377401526224576, 10.73952405711898, 10.482854037727858, 10.566041126873385, 10.554362165065323, 10.709454308107514, 10.011687893997912, 10.726169472164127, 10.670612035460193, 10.800754183197437, 10.428119180028075, 10.760284158192198, 10.610954779015767, 10.531891477250399, 10.674559637393969, 10.198503690706051, 8.313560373381126, 10.705828175448753, 10.717444279153368, 10.395088816529478, 10.625951683832241, 10.465309364792647, 10.455360644174332, 10.534417207911853, 10.782197570202847, 10.529751134036909, 10.398232669025488, 10.659680380232782, 10.85690307198296, 10.439795376871428, 10.289507669334913, 10.506224712289471, 10.421649757482081, 10.60941644287663, 10.428607640269869, 10.675046598816166, 10.261695639358782, 10.577102444158344, 10.47779223310667, 10.615260650830983, 10.698176180642688, 10.776857600664396, 10.443908845797697, 10.463275564275282, 10.511238890797285, 10.280421600657988, 10.668873041698284, 10.456005830150994, 10.77976083837288, 7.246315146462024, 10.656998766156144, 9.971552902581855, 10.385292730902478, 10.542316902265801, 10.705687289001814, 10.472921578668618, 10.779060550619148, 10.684720950609227, 10.62900387000098, 10.732075258124585, 10.683328282341945, 11.018527512598967, 9.692060800035184, 10.457841647803415, 10.685760261813392, 10.440497840763673, 10.57591969097781, 10.461119848172727, 6.293168759707352, 10.772361367240748, 10.510656795595306, 10.82081535384927, 10.581493656484048, 10.563311561451705, 10.299518605367782, 10.788924356656167, 10.714815614195969, 10.593466535079775, 10.490147030146469, 10.532625338376416, 10.721614990678857, 10.61247141097066, 10.557803340774917, 10.036993385850229, 10.522556320050498, 10.597506130769434, 10.418777392339939, 10.644646128232253, 10.326639232430077, 10.580674200809169, 10.354996070449086, 10.505297887259289, 10.560053373597562, 10.663264032070192, 10.631087994271516, 10.541377109512954, 10.63339210840776, 10.472905684267154, 10.635577803226742, 10.415112664472373, 10.502015848546067, 10.650597446459782, 10.796223500509788, 10.46883903970195, 10.179284753548314, 10.52936026444109, 10.52848840354848, 10.692400773239841, 10.726672718412612, 10.430019237051534, 10.439622032648996, 10.183029008969317, 10.39487292419948, 10.052909730320547, 10.64085031018325, 10.609915717674731, 10.822004960347973, 10.491684364984476, 10.20131492612551, 10.499908735640814, 10.495807469662783]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.2688401546211114, (1.2199322422560446, 1.3177480669861783)
losslist: [10.539361633586289, 10.657175462459602, 10.545494439632416, 10.789996255289282, 10.551991846331019, 9.862291267612584, 10.7445098733793, 10.710131101125533, 10.576979377763179, 10.632564148538236, 10.266817790324074, 10.638565154223604, 10.57933016102789, 10.481535455393633, 10.614837233997536, 10.283269022840026, 10.755802212097532, 10.81262200020952, 10.475198467589422, 8.757861714961956, 10.338311139715184, 10.691618133922601, 10.191513734890691, 10.690025009841742, 10.710521472273298, 10.549790257729246, 10.688094339286748, 10.690159715786638, 10.765945658378445, 10.31503592856499, 10.003140387937199, 10.661012388382856, 10.803670191053499, 10.218525099291405, 11.079681209605383, 10.567164802208888, 10.774183506938263, 9.960599134176032, 10.827385522162043, 10.506020977199393, 10.67318861366298, 10.535278034355796, 10.43555006334963, 10.791124526384689, 10.537218883780913, 10.564671274517854, 10.627774459772613, 10.633836545847345, 10.627022976013109, 10.129897382524941, 9.998913897363389, 10.480267990253939, 11.03087092793784, 10.452386672981355, 10.715216096133835, 10.652411767821304, 10.503189975952534, 10.81627667844554, 10.866396100050009, 10.599852039926304, 10.684270281650942, 10.779135088153605, 10.535801824248889, 10.352609833578358, 10.670305107066966, 10.58609369760567, 10.616666218140464, 10.635130167452205, 10.346612584933998, 10.912314032445968, 10.755538851794514, 10.85152789662063, 10.5406497286223, 10.623344954387544, 10.636871597632101, 10.57149113191505, 10.370464860783873, 10.870864400788598, 8.840782280755247, 10.793924251516152, 10.243064688513542, 10.100107129656315, 10.611566358895697, 10.650216609682172, 10.382845151054159, 10.525701427816267, 10.776240290571392, 10.494646540850281, 10.582759396634275, 10.135337318465051, 10.52806441641427, 10.677281105124926, 10.662766291356432, 10.646139981153658, 10.499823524379693, 10.613913212848257, 10.550956202209331, 10.650126146104794, 10.803956830183026, 10.618588602377104, 10.780020658121815, 10.824438696460042, 10.335306748311641, 10.441066874367126, 10.362775315355703, 10.688030735098238, 10.702097681746523, 10.521353185860866, 10.283649241950485, 10.68945878956991, 10.599929396818585, 10.413747136232939, 10.036708105110229, 10.80775531027086, 10.773282894285346, 10.342401307638887, 10.825827166460513, 10.749903131400837, 10.72942445170716, 10.402045210136519, 10.906871044141683, 10.608352830507227, 10.207084719674365, 10.30564907500073, 10.707121059041777, 10.62827530643086, 10.475781723302589, 10.457279417021986, 10.741087770765281, 10.304942161529253, 10.467389535252245, 10.314345892801668, 10.671360711159744, 10.52818234251921, 10.772735675901055, 10.629384564900512, 10.356626250759907, 10.633488584172207, 10.718435955751824, 10.645342735719755, 9.719766751784595, 10.567290946585976, 10.766600392742378, 10.661702935396278, 10.898612345587475, 10.63498112225082, 10.61060784392102, 10.328947677163145, 10.664400472159054, 10.826757757082685]

path 27
init_u, CI: 1.4043780368014769, (1.3415770929940258, 1.467178980608928)
losslist: [10.553406442428098, 10.479026336854938, 10.563808454849285, 10.767912288560675, 10.616563948347304, 10.319022833685834, 10.579440110083562, 10.69394886068166, 10.737750504862355, 10.531638049873063, 10.383735771314466, 10.166030788339228, 10.121400950982627, 10.577529164861401, 9.811189245158227, 10.481018435769421, 10.290428837415583, 10.376489366655983, 10.030235152912065, 10.479690074527863, 10.554532559526244, 10.56059552420119, 10.560453231481914, 10.562744220032512, 10.584368033516165, 10.553856994333833, 10.257943583587217, 10.361749093523631, 9.332063797752193, 10.779982307201323, 10.338273508870284, 10.207650106897441, 10.280009765221546, 10.857521195407795, 10.635719850301703, 10.431041782210182, 10.097642239751172, 10.651681913202099, 10.540541622986932, 10.671838075460954, 7.495269307204538, 10.463178094270239, 10.612853885111345, 10.364576837666814, 10.300793562244186, 10.511440343832595, 10.467762260460985, 10.428921702281711, 10.350012897096075, 10.62926983221162, 9.987693506113734, 10.358605511531707, 10.574896806849592, 10.434279362859382, 10.66835502990524, 10.562256352729298, 10.46377808668414, 10.714353053365283, 10.803769056809099, 10.017194660969235, 10.027568488011955, 10.21994812771587, 10.406820015221138, 10.775281341643, 10.52443682906987, 10.585465016081653, 10.529779985414958, 10.491610280856305, 9.901700412056014, 10.484004038932397, 10.385581340574547, 10.747256646565843, 10.374747042607494, 10.051296745909896, 10.432406480467908, 10.348483301102197, 9.970451968586026, 10.45289714892757, 10.730557994946544, 10.175941797358592, 10.017449720755746, 10.146254570018641, 10.28205916005042, 10.454869552831555, 10.47988627853216, 10.613664971230776, 10.458587792694003, 10.387016724436487, 10.198088512866027, 10.42812417637916, 10.396174129167763, 10.377800058775142, 10.290330287451242, 10.277471900247994, 10.75846165115844, 10.661230562632026, 10.523458740255316, 10.543135379737846, 10.68083961533239, 10.636729689342786, 10.675085963645955, 10.48547564217567, 10.53084202627196, 10.896665572258284, 10.237145006206125, 10.068456455524846, 10.648262599476823, 10.532093031733972, 10.790043874797385, 10.503572581079608, 10.454502057844238, 10.494382848342951, 10.638638310450503, 10.580085051855114, 10.478496368874751, 10.59704091434594, 9.672371778984806, 9.525114277133762, 10.457259901388044, 10.239104897096022, 10.68668504471458, 10.730228282950918, 10.93049231385017, 10.523648663221342, 10.8519576668316, 10.615122461473218, 10.578914786495222, 10.041854638535675, 10.52606378629896, 10.466511521022143, 10.400742479431605, 10.987487591826282, 8.396789936176393, 10.348951556699857, 10.349528940284085, 10.152701321335563, 10.62414324024808, 10.652174213522079, 10.271381392605132, 10.894010461127264, 10.436048329241686, 10.670568789066767, 10.376164369264094, 10.3688395710139, 10.234768998922842, 10.537495449812667, 10.310829977955533, 10.544292034448269, 10.130432635007441, 10.48545019742062]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.2697834033770796, (1.2156822459149161, 1.323884560839243)
losslist: [10.252556017620368, 10.737686897936703, 10.701682535664053, 10.466094576825563, 10.51312155003519, 10.781267116590579, 10.674124133849261, 8.02033557342947, 10.693398912418743, 10.374509022762318, 10.665338732571971, 10.585946833121428, 10.829103376648298, 10.601681667070785, 10.489996466920147, 10.399754731594372, 10.225392658786228, 10.387621782269516, 10.49307298765302, 10.47080013595459, 10.55104517594968, 10.578929757273219, 10.452570593676676, 9.70847031801554, 10.508693646599745, 10.53691088296422, 10.581373105566264, 10.718248400173504, 10.486446140559492, 10.968285692647562, 10.485199131949326, 10.65339730683941, 10.671093556283147, 10.646442433321441, 10.893387059729823, 10.442949852064718, 10.550080426261802, 10.492647518318252, 10.750341158191823, 10.568252577348714, 10.746340993180603, 10.514794717814203, 10.396024630561879, 10.635815180607711, 8.286645221702752, 10.607982107658263, 10.574738882284777, 10.743222503901427, 10.5183780361933, 10.657368579349024, 10.383292725978647, 10.871054732900959, 10.507578404052724, 10.510497793716667, 10.840841141385164, 10.746992268474171, 10.5110952744843, 10.605232395935587, 10.869213520647435, 10.852460937389285, 10.866840607179016, 10.634573454451216, 10.402004967211239, 10.736990983367331, 10.58994125891258, 10.554143838535989, 9.939642187744619, 10.637978701739618, 10.480347827147234, 10.429028436238223, 10.631003847157887, 10.647420615279263, 10.318881003918426, 10.45201741864621, 10.412984000667926, 10.523293238743706, 10.895307225046974, 10.674444772785504, 10.481604212658253, 10.51684234618335, 10.813043905240184, 10.867655032272133, 10.517910739254443, 10.463122534412795, 10.591559922804947, 10.755485022352154, 10.707436442242322, 10.748285424828593, 10.480851990629565, 10.665341376776961, 10.514868788206059, 10.89612120800085, 10.75570913115701, 10.651674271208654, 10.559796451593211, 10.786002915315802, 10.754480746549188, 10.522475551240655, 10.517916782747397, 10.521286910993672, 10.359682837604524, 10.371989488117157, 10.698252890070105, 10.629764478083041, 10.40774048849851, 10.70149955072835, 10.437610187784369, 10.495597463542243, 10.864878329803064, 10.224785058982157, 10.351226411498157, 10.679224692297417, 10.241172475960967, 10.346364468866707, 10.864805203718541, 10.40308887571176, 10.28928791176707, 10.523959275320253, 10.467286255855504, 10.580224942877074, 10.681312852925283, 10.565990752475946, 10.84582749718408, 10.482908822064239, 10.624408801487347, 10.285523337038459, 10.36523647844923, 10.620083053692221, 10.708150283420864, 10.422135410521618, 10.543477209120267, 10.619183360238036, 10.787309413257708, 10.673446737173293, 10.387199536419063, 10.673907064665542, 10.694083506872719, 10.750474863718022, 10.545407293206688, 10.476375104303772, 10.351224186769523, 10.63301926147882, 10.551054214103816, 10.435601911602285, 10.852442528782866, 10.62571934936348, 10.487690572640492, 10.922136819317352, 10.376732265026039, 10.805078116200175]

path 28
init_u, CI: 1.3278112946974474, (1.2657968202439687, 1.3898257691509261)
losslist: [10.778071630030738, 10.71056694577153, 10.647573212060387, 10.535048128452972, 10.500585053825613, 10.327300950196406, 10.732728290511472, 10.556452458559903, 10.861918061944197, 10.945437952208511, 10.557897833194005, 10.725348734010174, 10.628154799270412, 9.701166207094197, 10.459823006495574, 10.528810094109431, 10.015472157203934, 10.609573422259492, 10.351271461177808, 10.370962952904776, 10.55971214045044, 10.556405348068452, 10.78724011106952, 10.55388380830251, 10.704186854495983, 10.476985803655886, 10.649184478056775, 10.48744973080997, 10.801819196676737, 8.004990401567625, 10.680127935166329, 9.432033241674187, 10.397996486950477, 10.567959971413984, 10.781638583425634, 10.442357215291542, 10.55128230183317, 10.54145918371111, 10.743363294765176, 10.523020839954617, 10.755386424980987, 10.595622676653777, 10.612170595445496, 8.805185785444055, 10.372879021661523, 10.466878119573947, 10.761373104547458, 10.5311625189022, 10.488112010279366, 10.481131231520298, 6.908219084366214, 10.44271839435794, 10.651447331222721, 10.534650615789433, 10.716843943304214, 10.034452416362432, 10.70821173788067, 10.629782917463404, 10.403375596840668, 10.204415843914113, 10.58897157765269, 10.850753283464387, 10.782580039611968, 10.471978182539795, 10.501271052908788, 10.407152773751314, 10.725784545268734, 10.879167069237083, 10.696190438583477, 10.353384976683287, 10.656096765606906, 10.602007038034252, 10.727761536708199, 10.283416573906143, 10.527791683316659, 10.722740596915852, 10.733046670905951, 10.755464550756837, 10.199805285921736, 10.665366419867581, 10.267469275657492, 9.968987095438726, 10.876968066236511, 10.45360129743524, 10.645383918562926, 10.896159640184925, 10.662395883934419, 10.58163323634514, 10.491830621923866, 10.768582799688735, 10.401851024797983, 10.768270671288494, 10.728372054863357, 10.665601987375327, 10.613877349933379, 10.807085210043981, 10.700621831820854, 10.554840723322965, 10.712629896253102, 10.503802148000204, 10.381098949309921, 10.606151561785563, 10.449565935561187, 10.796776120882377, 10.51898464988559, 10.450594580239558, 10.680138818230832, 10.524638168882918, 10.483459739189245, 10.523979697908539, 10.049874955834309, 10.744438592020519, 10.568373239235546, 10.384175465236975, 9.355121532876261, 10.244463157871758, 10.385146562657745, 10.518635865525185, 10.423447735414854, 10.719305396643605, 10.591503716463261, 10.509728313723722, 10.673727642726474, 10.489883667882069, 10.58402069969488, 10.469395738568826, 10.656780796021732, 10.756858640980907, 10.404621740931907, 10.134190410219404, 10.573211533248708, 10.347764008367697, 10.676897753188756, 9.663358017074028, 10.341977015987435, 10.537005365694704, 10.589402112559034, 10.664533446499798, 10.876087706462133, 9.849932868706706, 10.80048732056596, 10.599804075093823, 10.628830461978312, 10.439052017874202, 10.630986171372243, 10.522942989277333, 10.84845597971705, 10.602181798450482, 10.827076023022185, 10.180321106993437, 10.567930543632587, 10.559196286388921, 8.102794693936449, 10.22984535731458, 10.730994119499435, 10.666262988699701, 10.43252886280859, 10.75498948174157, 10.48924614371186, 10.653482919687892, 10.47684439647477, 10.538839900006204, 10.694747516781895, 10.336564881354048, 9.886576451246995, 10.491809728479778, 10.30505812287689, 10.809775941790164, 10.650169088382519, 10.5990008429461, 10.68644626347601, 10.80222636536438, 10.708968598983521, 10.247848314395412, 10.59727022858701, 10.510096505839337, 10.368387336687315, 10.535953362320422, 10.359328810327582, 10.280604996042184, 10.524827950489934, 10.52593576828008, 10.950305978997996, 10.720949702127047, 10.56471422529312, 10.372396582457378, 10.556276936011708, 10.351916092910072, 10.59101609044206, 10.63809779713515, 10.431549619100831, 10.48157334932065, 10.608374323838525, 10.556312049107563, 10.83123470153798, 10.379679984794599, 10.484604067198834, 10.808288826390353, 10.769350146296821, 10.649487817620827]
AVOIDCORR
Most correlated pair: (8, 9) (Fatick, Foundiougne)
Cut district: 9 (Foundiougne)
u, CI: 1.2936727204013998, (1.233567581324321, 1.3537778594784786)
losslist: [10.932353358223665, 10.456391320029741, 10.723343526833533, 10.818915314661153, 10.573552519913617, 10.74954235704849, 10.300178570115175, 10.54621534109875, 10.490045735632972, 10.582698886813812, 10.613313950390381, 10.539877586179935, 10.361269826202765, 10.510965038931165, 11.029299575241712, 10.681700130537878, 10.815925937497942, 10.50484667389913, 10.71042439803913, 10.332993711090355, 10.482364741047618, 9.269562093892027, 10.386853591566332, 10.617551252746948, 10.601626736310793, 10.261456016077288, 10.633558218248487, 10.566300267420802, 10.732636658393208, 9.837906111256498, 10.603837224184566, 10.588981372799818, 10.703359589913582, 10.488086632339874, 10.18677151149425, 10.790087330917148, 10.646307605752941, 10.622234253579991, 10.73731350581978, 10.14001132144521, 10.65211005682199, 10.507660668317548, 10.632088314605712, 10.569166222114234, 10.649705705209099, 10.38630602237608, 10.642085196365585, 10.924767618190744, 10.492339625973921, 10.64946943540468, 10.472114060851373, 10.536627440282057, 10.49593989963511, 10.35535513895903, 10.965825808517055, 10.641617066416437, 9.997290366031013, 9.860323945749398, 10.608035880515677, 10.70476781687169, 10.81595680033086, 10.329353666875402, 10.407457888256689, 9.522613275294866, 10.538116487298252, 10.569120353461841, 10.596967253444095, 10.667878726734047, 10.631460765344599, 10.502589511434824, 9.170807350698858, 10.525335489635596, 10.886129397216907, 10.727203950846182, 10.709148118351157, 10.41620341596394, 10.766400591726889, 10.585146465279607, 10.567128108559967, 10.06937006754339, 10.090188027671163, 10.598683502587335, 10.450968223324992, 10.749923223549164, 10.678311147911765, 10.66684646269724, 10.442921997096828, 10.785869658885897, 10.531910975688291, 10.480716803669546, 10.379266127259818, 10.736509864256606, 10.580477871898603, 10.777134862257995, 10.377166512388404, 10.517268539817056, 10.657236078620102, 10.94837831493162, 10.298936643975935, 10.367522007800215]
'''


''' RUN BEFORE DOING PLOTTING BELOW
phase2paths_df.iloc[eligPathInds_sort[0], 5] = 1.212514932297184
phase2paths_df.iloc[eligPathInds_sort[0], 6] = 1.1539925129541722
phase2paths_df.iloc[eligPathInds_sort[0], 7] = 1.2710373516401958
phase2paths_df.iloc[eligPathInds_sort[1], 5] = 1.5988931545712113
phase2paths_df.iloc[eligPathInds_sort[1], 6] = 1.5226730983699461
phase2paths_df.iloc[eligPathInds_sort[1], 7] = 1.6751132107724764
phase2paths_df.iloc[eligPathInds_sort[2], 5] = 1.1616119907975282
phase2paths_df.iloc[eligPathInds_sort[2], 6] = 1.1045601027555385
phase2paths_df.iloc[eligPathInds_sort[2], 7] = 1.2186638788395179
phase2paths_df.iloc[eligPathInds_sort[3], 5] = 1.5054090994868403
phase2paths_df.iloc[eligPathInds_sort[3], 6] = 1.4349911746252015
phase2paths_df.iloc[eligPathInds_sort[3], 7] = 1.575827024348479
phase2paths_df.iloc[eligPathInds_sort[4], 5] = 1.692904950303518
phase2paths_df.iloc[eligPathInds_sort[4], 6] = 1.6145134687307134
phase2paths_df.iloc[eligPathInds_sort[4], 7] = 1.7712964318763227
phase2paths_df.iloc[eligPathInds_sort[5], 5] = 1.3115487411562174
phase2paths_df.iloc[eligPathInds_sort[5], 6] = 1.2480938617544037
phase2paths_df.iloc[eligPathInds_sort[5], 7] = 1.3750036205580312
phase2paths_df.iloc[eligPathInds_sort[6], 5] = 1.5967286302980845
phase2paths_df.iloc[eligPathInds_sort[6], 6] = 1.5186136249978208
phase2paths_df.iloc[eligPathInds_sort[6], 7] = 1.6748436355983483
phase2paths_df.iloc[eligPathInds_sort[7], 5] = 1.9203010691352596
phase2paths_df.iloc[eligPathInds_sort[7], 6] = 1.827701755353317
phase2paths_df.iloc[eligPathInds_sort[7], 7] = 2.012900382917202
phase2paths_df.iloc[eligPathInds_sort[8], 5] = 1.5151175398479975
phase2paths_df.iloc[eligPathInds_sort[8], 6] = 1.4395405105724137
phase2paths_df.iloc[eligPathInds_sort[8], 7] = 1.5906945691235812
phase2paths_df.iloc[eligPathInds_sort[9], 5] = 1.4247158818142633
phase2paths_df.iloc[eligPathInds_sort[9], 6] = 1.3549259032100203
phase2paths_df.iloc[eligPathInds_sort[9], 7] = 1.4945058604185064
phase2paths_df.iloc[eligPathInds_sort[10], 5] = 1.359581302788575
phase2paths_df.iloc[eligPathInds_sort[10], 6] = 1.3066834638841218
phase2paths_df.iloc[eligPathInds_sort[10], 7] = 1.4124791416930282
phase2paths_df.iloc[eligPathInds_sort[11], 5] = 1.6138151791706825
phase2paths_df.iloc[eligPathInds_sort[11], 6] = 1.5347448851631214
phase2paths_df.iloc[eligPathInds_sort[11], 7] = 1.6928854731782437
phase2paths_df.iloc[eligPathInds_sort[12], 5] = 1.525344395455896
phase2paths_df.iloc[eligPathInds_sort[12], 6] = 1.453678030293739
phase2paths_df.iloc[eligPathInds_sort[12], 7] = 1.597010760618053
phase2paths_df.iloc[eligPathInds_sort[13], 5] = 1.5830781652944257
phase2paths_df.iloc[eligPathInds_sort[13], 6] = 1.5049209188995647
phase2paths_df.iloc[eligPathInds_sort[13], 7] = 1.6612354116892867
phase2paths_df.iloc[eligPathInds_sort[14], 5] = 1.7260606756595127
phase2paths_df.iloc[eligPathInds_sort[14], 6] = 1.6415468292949935
phase2paths_df.iloc[eligPathInds_sort[14], 7] = 1.810574522024032
phase2paths_df.iloc[eligPathInds_sort[15], 5] = 1.4294400608504034
phase2paths_df.iloc[eligPathInds_sort[15], 6] = 1.3602820693550157
phase2paths_df.iloc[eligPathInds_sort[15], 7] = 1.4985980523457911
phase2paths_df.iloc[eligPathInds_sort[16], 5] = 1.5364151800985653
phase2paths_df.iloc[eligPathInds_sort[16], 6] = 1.4671177550469423
phase2paths_df.iloc[eligPathInds_sort[16], 7] = 1.6057126051501882
phase2paths_df.iloc[eligPathInds_sort[17], 5] = 1.4199442799652342
phase2paths_df.iloc[eligPathInds_sort[17], 6] = 1.357013932630661
phase2paths_df.iloc[eligPathInds_sort[17], 7] = 1.4828746272998075
phase2paths_df.iloc[eligPathInds_sort[18], 5] = 1.729335463705576
phase2paths_df.iloc[eligPathInds_sort[18], 6] = 1.6478560246709488
phase2paths_df.iloc[eligPathInds_sort[18], 7] = 1.8108149027402032
phase2paths_df.iloc[eligPathInds_sort[19], 5] = 1.6493052523195075
phase2paths_df.iloc[eligPathInds_sort[19], 6] = 1.5688500487538253
phase2paths_df.iloc[eligPathInds_sort[19], 7] = 1.7297604558851898
phase2paths_df.iloc[eligPathInds_sort[20], 5] = 1.7134521285427606
phase2paths_df.iloc[eligPathInds_sort[20], 6] = 1.629968007658924
phase2paths_df.iloc[eligPathInds_sort[20], 7] = 1.7969362494265972
phase2paths_df.iloc[eligPathInds_sort[21], 5] = 1.4114938721987187
phase2paths_df.iloc[eligPathInds_sort[21], 6] = 1.3526212002314963
phase2paths_df.iloc[eligPathInds_sort[21], 7] = 1.470366544165941
phase2paths_df.iloc[eligPathInds_sort[22], 5] = 1.3727707408987087
phase2paths_df.iloc[eligPathInds_sort[22], 6] = 1.3131693317588002
phase2paths_df.iloc[eligPathInds_sort[22], 7] = 1.432372150038617
phase2paths_df.iloc[eligPathInds_sort[23], 5] = 1.4574138734041782
phase2paths_df.iloc[eligPathInds_sort[23], 6] = 1.3914073747767528
phase2paths_df.iloc[eligPathInds_sort[23], 7] = 1.5234203720316035
phase2paths_df.iloc[eligPathInds_sort[24], 5] = 1.5217708963790315
phase2paths_df.iloc[eligPathInds_sort[24], 6] = 1.448916616932289
phase2paths_df.iloc[eligPathInds_sort[24], 7] = 1.5946251758257741
phase2paths_df.iloc[eligPathInds_sort[25], 5] = 1.2977156649273933
phase2paths_df.iloc[eligPathInds_sort[25], 6] = 1.2540482196032023
phase2paths_df.iloc[eligPathInds_sort[25], 7] = 1.3413831102515843
phase2paths_df.iloc[eligPathInds_sort[26], 5] = 1.3394279293908014
phase2paths_df.iloc[eligPathInds_sort[26], 6] = 1.2809907400793428
phase2paths_df.iloc[eligPathInds_sort[26], 7] = 1.39786511870226
phase2paths_df.iloc[eligPathInds_sort[27], 5] = 1.4043780368014769
phase2paths_df.iloc[eligPathInds_sort[27], 6] = 1.3415770929940258
phase2paths_df.iloc[eligPathInds_sort[27], 7] = 1.467178980608928
phase2paths_df.iloc[eligPathInds_sort[28], 5] = 1.3278112946974474
phase2paths_df.iloc[eligPathInds_sort[28], 6] = 1.2657968202439687
phase2paths_df.iloc[eligPathInds_sort[28], 7] = 1.3898257691509261


'''
####### Or load #######
# phase2paths_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'phase2paths.pkl'))


# Generate a plot for our improvement runs
xvals = np.arange(1,len(eligPathInds)+2) # Add 1 for our initial feasible solution
UBvals = [phase2paths_df.iloc[i, 3] for i in eligPathInds_sort]
UBvals.insert(0, UB)
utilvals = [phase2paths_df.iloc[i, 5] for i in eligPathInds_sort]
utilvals.insert(0, solUtil)
utilvalCIs = [(phase2paths_df.iloc[i, 7]-phase2paths_df.iloc[i, 6])/2 for i in eligPathInds_sort]
utilvalCIs.insert(0, (2.300548646586247-2.0683527673839848)/4)

# Plot
fig, ax = plt.subplots()
# yerr should be HALF the length of the total error bar
ax.plot(xvals,UBvals,'v',color='royalblue',alpha=0.4, markersize=4)
ax.errorbar(xvals, utilvals, yerr=utilvalCIs, fmt='o',
            color='black', linewidth=0.5, capsize=1.5)
# Plot the first Gain and noGain lists before everything else, so as to get the legend right
lst = avoidcorrlist_Gain[0]
ax.errorbar(lst[0],lst[1], yerr=[(lst[3]-lst[2])/2], fmt='^', markersize=6,
                color='darkgreen',linewidth=0.5,capsize=1.5,alpha=0.4)
lst = avoidcorrlist_noGain[0]
ax.errorbar(lst[0],lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='crimson',linewidth=0.5,capsize=1.5,alpha=0.4)
for lst in avoidcorrlist_Gain[1:]:
    ax.errorbar(lst[0],lst[1], yerr=[(lst[3]-lst[2])/2], fmt='^', markersize=6,
                color='darkgreen',linewidth=0.5,capsize=1.5,alpha=0.4)
for lst in avoidcorrlist_noGain[1:]:
    ax.errorbar(lst[0],lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='crimson',linewidth=0.5,capsize=1.5,alpha=0.4)
ax.set(xticks=xvals, ylim=(1., 3.1))
plt.xticks(fontsize=8)
plt.ylabel('Utility', fontsize=12)
plt.xlabel('Candidate index', fontsize=12)
plt.title('Candidate solution evaluations', fontsize=14)
plt.legend(['IP-RP Objective', 'Candidate Utility', 'AVOIDCORR: Gain', 'AVOIDCORR: No Gain'],
           fontsize=9, loc='upper right')
plt.axhline(2.184450706985116, xmin=0.06, color='gray', linestyle='dashed', alpha=0.4) # Evaluated utility
plt.show()



# Sort the same values by UBs
UBsortInds = np.argsort(UBvals).tolist()
UBsortInds.reverse()
newUBvals = [UBvals[x] for x in UBsortInds]
newutilvals = [utilvals[x] for x in UBsortInds]
newutilvalCIs = [utilvalCIs[x] for x in UBsortInds]


fig, ax = plt.subplots()
ax.plot(xvals, newUBvals,'^',color='royalblue',alpha=0.4, markersize=4)
ax.errorbar(xvals, newutilvals, yerr=newutilvalCIs, fmt='o',
            color='black', linewidth=0.5, capsize=1.5)
lst = avoidcorrlist_Gain[0]
ax.errorbar(UBsortInds.index(lst[0]-1)+1, lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='darkgreen',linewidth=0.5,capsize=1.5,alpha=0.4)
lst = avoidcorrlist_noGain[0]
ax.errorbar(UBsortInds.index(lst[0]-1)+1, lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='crimson',linewidth=0.5,capsize=1.5,alpha=0.4)
for lst in avoidcorrlist_Gain[1:]:
    ax.errorbar(UBsortInds.index(lst[0]-1)+1, lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='darkgreen',linewidth=0.5,capsize=1.5,alpha=0.4)
for lst in avoidcorrlist_noGain[1:]:
    ax.errorbar(UBsortInds.index(lst[0]-1)+1, lst[1], yerr=[(lst[3]-lst[2])/2], fmt='x', markersize=5,
                color='crimson',linewidth=0.5,capsize=1.5,alpha=0.4)
ax.set(xticks=xvals, ylim=(1., 3.1))
plt.xticks(fontsize=8)
plt.ylabel('Utility', fontsize=12)
plt.xlabel('Path index', fontsize=12)
plt.title('Second stage utility evaluations\nSorted by upper bounds', fontsize=14)
plt.legend(['RIP Objective (UB)', 'RIP Utility', 'AVOIDCORR: Gain', 'AVOIDCORR: No Gain'],
           fontsize=9, loc='upper right')
plt.show()

