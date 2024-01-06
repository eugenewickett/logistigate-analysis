from logistigate.logistigate import utilities as util # Pull from the submodule "develop" branch
from logistigate.logistigate import methods
from logistigate.logistigate.priors import prior_normal_assort
from logistigate.logistigate import lossfunctions as lf
from logistigate.logistigate import samplingplanfunctions as sampf

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

    return dept_df, regcost_mat, testresults_df, regNames, manufNames

# Pull district-level Senegal data
# N, Y, SNnames, TNprovs, TNnames = GetSenegalDataMatrices(deidentify=False)
dept_df, regcost_mat, testresults_df, regNames, manufNames = GetSenegalCSVData()
deptNames = dept_df['Department'].sort_values().tolist()
numReg = len(regNames)
testdatadict = {'dataTbl':testresults_df.values.tolist(), 'type':'Tracked', 'TNnames':deptNames, 'SNnames':manufNames}
testdatadict = util.GetVectorForms(testdatadict)
N, Y, TNnames, SNnames = testdatadict['N'], testdatadict['Y'], testdatadict['TNnames'], testdatadict['SNnames']
(numTN, numSN) = N.shape # For later use

def GetRegion(dept_str, dept_df):
    """Retrieves the region associated with a department"""
    return dept_df.loc[dept_df['Department']==dept_str,'Region'].values[0]
def GetDeptChildren(reg_str, dept_df):
    """Retrieves the departments associated with a region"""
    return dept_df.loc[dept_df['Region']==reg_str,'Department'].values.tolist()

##############
### Print some data summaries
# Overall data
print('TNs by SNs: ' + str(N.shape) + '\nNumber of Obsvns: ' + str(N.sum()) + '\nNumber of SFPs: ' + str(Y.sum()) + '\nSFP rate: ' + str(round(
    Y.sum() / N.sum(), 4)))
# TN-specific data
print('Tests at TNs: ' + str(np.sum(N, axis=1)) + '\nSFPs at TNs: ' + str(np.sum(Y, axis=1)) + '\nSFP rates: ' + str(
    (np.sum(Y, axis=1) / np.sum(N, axis=1)).round(4)))
# Set up logistigate dictionary
lgdict = util.initDataDict(N, Y)
lgdict.update({'TNnames':TNnames, 'SNnames':SNnames})

##############
# Set up priors for SFP rates at nodes
# TODO: INSPECT CHOICE HERE LATER
# All SNs are `Moderate'
SNpriorMean = np.repeat(spsp.logit(0.1), numSN)
# TNs are randomly assigned risk, such that 5% are in the 1st and 7th levels, 10% are in the 2nd and 6th levels,
#   20% are in the 3rd and 5th levels, and 30% are in the 4th level
np.random.seed(15)
tempCategs = np.random.multinomial(n=1, pvals=[0.05,0.1,0.2,0.3,0.2,0.1,0.05], size=numTN)
riskMeans = [0.01,0.02,0.05,0.1,0.15,0.2,0.25]
randriskinds = np.mod(np.where(tempCategs.flatten()==1), len(riskMeans))[0]
TNpriorMean = spsp.logit(np.array([riskMeans[randriskinds[i]] for i in range(numTN)]))
# Concatenate prior means
priorMean = np.concatenate((SNpriorMean, TNpriorMean))
TNvar, SNvar = 2., 3.  # Variances for use with prior; supply nodes are wider due to unknown risk assessments
priorCovar = np.diag(np.concatenate((np.repeat(SNvar, numSN), np.repeat(TNvar, numTN))))
priorObj = prior_normal_assort(priorMean, priorCovar)
lgdict['prior'] = priorObj

# Set up MCMC
lgdict['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}

'''
# TODO: INSPECT CHOICE HERE LATER
numdraws = 5000
lgdict['numPostSamples'] = numdraws

np.random.seed(300) # For first 4 sets of 5k draws
np.random.seed(301) # For second 17 sets of 5k draws
np.random.seed(410) # For third 11 sets of 5k draws
np.random.seed(466) # For fourth XX sets of 5k draws

time0 = time.time()
lgdict = methods.GeneratePostSamples(lgdict, maxTime=5000)
print(time.time()-time0)

tempobj = lgdict['postSamples']
np.save(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws40'),tempobj)

file_name = "operationalizedsamplingplans/numpy_objects/draws35.npy"
file_stats = os.stat(file_name)
print(f'File Size in MegaBytes is {file_stats.st_size / (1024 * 1024)}')
'''

# Load draws from files
tempobj = np.load(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws1.npy'))
for drawgroupind in range(2, 41):
    newobj = np.load(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'draws' + str(drawgroupind) +'.npy'))
    tempobj = np.concatenate((tempobj, newobj))
lgdict['postSamples'] = tempobj
# Print inference from initial data
util.plotPostSamples(lgdict, 'int90')

# Generate Q via bootstrap sampling of known traces
numvisitedTNs = np.count_nonzero(np.sum(lgdict['Q'],axis=1))
numboot = 20 # Average across each department in original data
SNprobs = np.sum(lgdict['N'], axis=0) / np.sum(lgdict['N']) # SN sourcing probabilities across original data
np.random.seed(44)
Qvecs = np.random.multinomial(numboot, SNprobs, size=numTN - numvisitedTNs) / numboot
# Only update rows with no observed traces
Qindcount = 0
tempQ = lgdict['Q'].copy()
for i in range(tempQ.shape[0]):
    if lgdict['Q'][i].sum() == 0:
        tempQ[i] = Qvecs[Qindcount]
        Qindcount += 1
lgdict.update({'Q':tempQ})

# Loss specification
# TODO: INSPECT CHOICE HERE LATER, ESP MARKETVEC
paramdict = lf.build_diffscore_checkrisk_dict(scoreunderestwt=5., riskthreshold=0.15, riskslope=0.6,
                                              marketvec=np.ones(numTN + numSN))

# Set MCMC draws to use in fast algorithm
numtruthdraws, numdatadraws = 200000, 100
# Get random subsets for truth and data draws
np.random.seed(56)
truthdraws, datadraws = util.distribute_truthdata_draws(lgdict['postSamples'], numtruthdraws, numdatadraws)
paramdict.update({'truthdraws': truthdraws, 'datadraws': datadraws})
# Get base loss
paramdict['baseloss'] = sampf.baseloss(paramdict['truthdraws'], paramdict)

util.print_param_checks(paramdict)  # Check of used parameters

def getUtilityEstimate(n, lgdict, paramdict, zlevel=0.95):
    """
    Return a utility estimate average and confidence interval for allocation array n
    """
    testnum = int(np.sum(n))
    des = n/testnum
    currlosslist = sampf.sampling_plan_loss_list(des, testnum, lgdict, paramdict)
    currloss_avg, currloss_CI = sampf.process_loss_list(currlosslist, zlevel=zlevel)
    return paramdict['baseloss'] - currloss_avg, (paramdict['baseloss']-currloss_CI[1], paramdict['baseloss']-currloss_CI[0])


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
# TODO: INSPECT CHOICES HERE LATER, ESP bigM
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
def GetUpperBounds(optparamdict):
    """Returns a numpy vector of upper bounds for an inputted parameter dictionary"""
    B, f_dept, f_reg = optparamdict['budget'], optparamdict['deptfixedcostvec'], optparamdict['arcfixedcostmat']
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
    currind = HQind
    currbesttup = 0
    for permuttuple in permutlist:
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

''' TEST TRIANGLE INTERPOLATION
xlist = [0,1,30]
flist = [0,1,5]

retx, retf = GetTriangleInterpolation(xlist, flist)

plt.plot(retx, retf)
plt.ylim([0,25])
plt.show()
'''


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
'''

# Load previously calculated lower and upper utility evaluations
util_df = pd.read_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'utilevals.pkl'))

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

### GENERATE PATHS FOR CASE STUDY ###
# What is the upper bound on the number of regions in any feasible tour that uses at least one test?
maxregnum = GetSubtourMaxCardinality(optparamdict=optparamdict)

listinds1 = list(itertools.combinations(np.arange(1,numReg).tolist(),1))
listinds2 = list(itertools.combinations(np.arange(1,numReg).tolist(),2))
listinds3 = list(itertools.combinations(np.arange(1,numReg).tolist(),3))
listinds4 = list(itertools.combinations(np.arange(1,numReg).tolist(),4))
listinds5 = list(itertools.combinations(np.arange(1,numReg).tolist(),5))

mastlist = listinds1 + listinds2 + listinds3 + listinds4 + listinds5
len(mastlist)

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

# Save to avoid generating later
paths_df.to_pickle(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'paths.pkl'))

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
lvec, juncvec, m1vec, m2vec, = [], [], [], []
for ind, row in util_df.iterrows():
    currBound, loval, hival = row[1], row[2], row[4]
    # Get interpolation values
    _, _, l, k, m1, m2 = GetTriangleInterpolation([0, 1, currBound], [0, loval, hival])
    lvec.append(l)
    juncvec.append(k)
    m1vec.append(m1)
    m2vec.append(m2)
    
# What is the curvature, kappa, for our estimates?
kappavec = [1-m2vec[i]/m1vec[i] for i in range(len(m2vec))]
plt.hist(kappavec)
plt.title('Histogram of $\kappa$ curvature at each district')
plt.show()

# Make histograms of our interpolated values
plt.hist(lvec,color='orange')
plt.title('Histogram of zero intercepts ($l$ values)')
plt.xlabel('$l$')
plt.ylabel('Count')
plt.show()

plt.hist(juncvec,color='darkgreen')
plt.title('Histogram of slope junctures ($j$ values)')
plt.xlabel('$j$')
plt.ylabel('Count')
plt.show()

plt.hist(m1vec,color='crimson')
plt.title('Histogram of first slopes ($m_1$ values)')
plt.xlabel('$m_1$')
plt.ylabel('Count')
plt.xlim([0,0.025])
plt.show()

plt.hist(m2vec,color='pink')
plt.title('Histogram of second slopes ($m_2$ values)')
plt.xlabel('$m_2$')
plt.ylabel('Count')
plt.xlim([0,0.025])
plt.show()

# Now we construct our various program vectors and matrices per the scipy standards
numPath = paths_df.shape[0]

# Variable bounds
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
optconstraintmat4 = np.vstack((np.array(seqcostlist_trim), np.zeros((numTN*3, numPath)),
                               (-bindistaccessvectors_trim).T, np.ones(numPath)))

optconstraintmat = np.hstack((optconstraintmat1, optconstraintmat2, optconstraintmat3, optconstraintmat4))

optconstraints = spo.LinearConstraint(optconstraintmat, optconstrlower, optconstrupper)

# Define integrality for all variables
optintegrality = np.ones_like(optobjvec)

# Solve
spoOutput = milp(c=optobjvec, constraints=optconstraints, integrality=optintegrality, bounds=optbounds)
soln = spoOutput.x


# Make function for turning scipy output into our case study
def scipytoallocation(spo_x):
    z = spo_x[:numTN]
    n1 = spo_x[numTN:numTN * 2]
    n2 = spo_x[numTN * 2:numTN * 3]
    x = spo_x[numTN * 3:]
    path = seqlist_trim[np.where(x == 1)[0][0]]
    # Print district name with
    for distind, distname in enumerate(deptNames):
        print(str(distname)+':', str(int(z[distind])), str(int(n1[distind])), str(int(n2[distind])))
    pathstr = ''
    for regind in path:
        pathstr = pathstr + str(regNames[regind]) + ' '
    print('Path: '+ pathstr)
    return

scipytoallocation(spoOutput.x)

### Inspect our solution
# How does our utility value compare with the real utility?
n1 = soln[numTN:numTN * 2]
n2 = soln[numTN * 2:numTN * 3]
n_init = n1+n2

time0 = time.time()
u_init, u_init_CI = getUtilityEstimate(n_init, lgdict, paramdict)
time1 = time.time() - time0
print(time1)
''' 4-JAN
spoOutput*-1: 2.7690379399483853
150k/500 draws:
u_init, u_init_CI:  2.184450706985116, (2.0683527673839848, 2.300548646586247)
                    2.189141541015074, (2.063870236586828, 2.3144128454433197)
                    2.1243090313794664, (2.0040581266308806, 2.244559936128052)
Bound is about 27% above actual value
100k/500 draws:     (2.217041463121607, (2.098915436652165, 2.335167489591049))

'''
spoOutput.fun*-1

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
        print('New utility range: ' + str(epsgap))

    return paramdict['baseloss'] - currloss_avg, \
           (paramdict['baseloss']-currloss_CI[1], paramdict['baseloss']-currloss_CI[0]), masterlosslist




time0 = time.time()
u_init, u_init_CI = getUtilityEstimateSequential(n_init, lgdict, paramdict)
runtime = time.time()-time0
print(runtime)


################################
################################
# COMPARATIVE CASE: GENERATE RANDOM PATHS AND ALLOCATIONS AND COMPARE WITH THE UTILITY OF OUR INITIAL FEASIBLE SOLUTION
################################
################################
comparepathsdict = {}
# Choose 2|D|+1 feasible paths
np.random.seed(55893)
numcomparepaths = 2*len(deptNames)+277
compare_pathinds = np.random.choice(np.arange(numPath),size=numcomparepaths,replace=False)
compare_pathinds.sort()
comparepathsdict.update({'pathinds':compare_pathinds})
# Iterate through each path and designate visited districts
compare_visiteddistinds = []
compare_allocvecs = []
pathstoadd = 0 # For ensuring we end up with 93 feasible paths
for pathind in comparepathsdict['pathinds'].tolist():
    curr_distaccess = [0 for x in range(numTN)]
    curr_regs = paths_df.iloc[pathind]['Sequence']
    for r in curr_regs:
        if r == 0: # Flip coin for HQ region
            possDists = GetDeptChildren(regNames[r], dept_df)
            possDistsInds = [deptNames.index(x) for x in possDists]
            for distInd in possDistsInds:
                curr_distaccess[distInd] = np.random.binomial(n=1,p=0.25)
        else:
            # Guarantee one district is visited
            possDists = GetDeptChildren(regNames[r], dept_df)
            defVisitDist = possDists[np.random.choice(np.arange(len(possDists)))]
            curr_distaccess[deptNames.index(defVisitDist)] = 1
            possDists.remove(defVisitDist)
            possDistsInds = [deptNames.index(x) for x in possDists]
            for distInd in possDistsInds:
                curr_distaccess[distInd] = np.random.binomial(1, 0.25)
    compare_visiteddistinds.append(curr_distaccess)
    # Add one test to each visited district
    curr_n = np.array(curr_distaccess)
    # Check if budget is feasible
    budgetcost = np.sum(np.array(curr_distaccess) * f_dept) + paths_df.iloc[pathind]['Cost'] + curr_n.sum()*ctest
    if budgetcost > B:
        pathstoadd += 1
    else: # Expend rest of budget on tests at random locations
        teststoadd = int(np.floor((B-budgetcost)/ctest))
        multinom_num = curr_n.sum()
        multinom_vec = np.random.multinomial(n=teststoadd,pvals=np.ones(multinom_num)/multinom_num)
        curraddind = 0
        for t_ind in range(curr_n.shape[0]):
            if curr_n[t_ind] > 0:
                curr_n[t_ind] += multinom_vec[curraddind]
                curraddind += 1
    compare_allocvecs.append(curr_n)
comparepathsdict.update({'visiteddistinds':compare_visiteddistinds})
comparepathsdict.update({'allocvecs':compare_allocvecs})
print(numcomparepaths-pathstoadd) # Target is 93

# Save comparative paths dictionary
'''
comparepathsdict.update({'lossevals':[[] for x in range(numcomparepaths)]})
with open(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'comparepaths.pkl'), 'wb') as fp:
    pickle.dump(comparepathsdict, fp)
'''

#########
# Load previous runs and append to those
with open(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'comparepaths.pkl'), 'rb') as fp:
    comparepathsdict = pickle.load(fp)


# Now loop through feasible budgets and get loss evaluations
for temp_i, pathind in enumerate(comparepathsdict['pathinds'].tolist()):
    budgetcost = (np.array(np.array(comparepathsdict['visiteddistinds']).tolist()[temp_i])*f_dept).sum() +\
                 paths_df['Cost'].tolist()[pathind] +\
                 np.array(np.array(comparepathsdict['allocvecs']).tolist()[temp_i]).sum()*ctest
    if budgetcost <= B: # Get utility
        print('Getting utility for comparative path '+str(temp_i)+'...')
        curr_n = comparepathsdict['allocvecs'][temp_i]
        currlosslist = sampf.sampling_plan_loss_list(curr_n/curr_n.sum(), curr_n.sum(), lgdict, paramdict)
        comparepathsdict['lossevals'][temp_i] = comparepathsdict['lossevals'][temp_i] + currlosslist

with open(os.path.join('operationalizedsamplingplans', 'numpy_objects', 'comparepaths.pkl'), 'wb') as fp:
    pickle.dump(comparepathsdict, fp)



########################
########################
########################
# todo: WHY DONT' THE COMPARATIVE UTILITIES MAKE SENSE
# Put answer into interpolated functions and check that the modified objective is working as intended
tempobjval = 0
for ind, row in util_df.iterrows():
    currBound, loval, hival = row[1], row[2], row[4]
    # Get interpolation values
    retx, retf, l, k, m1, m2 = GetTriangleInterpolation([0, 1, currBound], [0, loval, hival])
    tempobjval += retf[int(n_init[ind])]
# MATCHES
# tempobjval: 2.7690379399483893

# Take hi vals of CIs and see how much the interpolations change
tempobjval = 0
for ind, row in util_df.iterrows():
    currBound, loval, loval_CI, hival, hival_CI = row[1], row[2], row[3], row[4], row[5]
    # Get interpolation values
    retx, retf, l, k, m1, m2 = GetTriangleInterpolation([0, 1, currBound], [0, loval_CI[0], hival_CI[0]])
    tempobjval += retf[int(n_init[ind])]
print(tempobjval)
'''
HI-HI: 2.943311577936248
LO-HI: 
HI-LO: 2.6811757278907646
LO-LO: 
'''

# Choose two correlated districts and check sum of utilities
# iterate through Q
currminnorm, currmaxnorm = 1e4, 0.
ind1min, ind2min = 0, 0
ind1max, ind2max = 0, 0
for i, qvec in enumerate(Qvecs):
    for j, qvec2 in enumerate(Qvecs):
        if np.linalg.norm((qvec-qvec2))<currminnorm and i != j:
            currminnorm = np.linalg.norm((qvec-qvec2))
            ind1min, ind2min = i, j
        if np.linalg.norm((qvec - qvec2)) > currmaxnorm and i != j:
            currmaxnorm = np.linalg.norm((qvec - qvec2))
            ind1max, ind2max = i, j

ntemp = np.zeros(numTN)
ntemp[ind1] = 100
ntemp[ind2] = 100
realutil, realutil_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(realutil, realutil_CI) #0.7081823056941321 (0.6771539227322343, 0.7392106886560299)

ntemp = np.zeros(numTN)
ntemp[ind1] = 100
tildeutil1, tildutil1_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(tildeutil1, tildutil1_CI) #0.3484752939904734 (0.3414514488824043, 0.35549913909854247)

ntemp = np.zeros(numTN)
ntemp[ind2] = 100
tildeutil2, tildutil2_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(tildeutil2, tildutil2_CI) #0.22789067301994415 (0.22005794709540005, 0.23572339894448824)

# Equal to 81% of real combined utility

# Look at just 2 tests
ntemp = np.zeros(numTN)
ntemp[ind1] = 1
ntemp[ind2] = 1
realutil, realutil_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
# realutil: 0.038604538610504946 (0.03658020869356271, 0.04062886852744718), for ind1, ind2 = 9, 16
util_df.iloc[ind1][2] + util_df.iloc[ind2][2] # 0.036228213316286784
util_df.iloc[ind1][3][0] + util_df.iloc[ind2][3][0] # 0.03333885619967347
util_df.iloc[ind1][3][1] + util_df.iloc[ind2][3][1] # 0.039117570432900095

# Look at *least* correlated districts
# indices 1 and 15
ntemp = np.zeros(numTN)
ntemp[ind1max] = 100
ntemp[ind2max] = 100
realutil, realutil_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(realutil, realutil_CI) # 0.6592539560234485 (0.6296673529836117, 0.6888405590632853)

ntemp = np.zeros(numTN)
ntemp[ind1max] = 100
tildeutil1, tildutil1_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(tildeutil1, tildutil1_CI) # 0.3904876268310815 (0.3826728966658255, 0.39830235699633754)

ntemp = np.zeros(numTN)
ntemp[ind2max] = 100
tildeutil2, tildutil2_CI = getUtilityEstimate(ntemp, lgdict, paramdict)
print(tildeutil2, tildutil2_CI) # 0.16721586913591047 (0.16076033432742953, 0.1736714039443914)
# Equal to 85% of real combined utility

# Iterate through a pair of samples and plot
utilcomblist, utilcombCIlist = [0], [(0,0)]
utilsumlist, utilsumCIlist = [0], [(0,0)]
for i in range(20, 101, 20):
    print('On ' + str(i) + ' tests...')
    print('Location 8...')
    n = np.zeros(numTN)
    n[8] = i
    util1, util1_CI = getUtilityEstimate(n, lgdict, paramdict)
    print('Location 9...')
    n = np.zeros(numTN)
    n[9] = i
    util2, util2_CI = getUtilityEstimate(n, lgdict, paramdict)
    utilsumlist.append(util1+util2)
    utilsumCIlist.append((util1_CI[0]+util2_CI[0], util1_CI[1]+util2_CI[1]))
    # Holistic utility
    print('Holistic...')
    n = np.zeros(numTN)
    n[8], n[9] = i, i
    utilcomb, utilcomb_CI = getUtilityEstimate(n, lgdict, paramdict)
    utilcomblist.append(utilcomb)
    utilcombCIlist.append(utilcomb_CI)
    # Update plotting lists
    utilsumCIlistlower = [x[0] for x in utilsumCIlist]
    utilsumCIlistupper = [x[1] for x in utilsumCIlist]
    utilcombCIlistlower = [x[0] for x in utilcombCIlist]
    utilcombCIlistupper = [x[1] for x in utilcombCIlist]
    # Plot
    plt.plot(range(0,i + 1,20), utilsumlist, color='darkgreen',linewidth=3)
    plt.plot(range(0,i + 1,20), utilcomblist, color='black',linewidth=3)
    plt.plot(range(0,i + 1,20), utilsumCIlistlower, color='lightgreen',linestyle='dashed')
    plt.plot(range(0,i + 1,20), utilsumCIlistupper, color='lightgreen',linestyle='dashed')
    plt.plot(range(0,i + 1,20), utilcombCIlistlower, color='gray',linestyle='dashed')
    plt.plot(range(0,i + 1,20), utilcombCIlistupper, color='gray',linestyle='dashed')
    plt.legend(['$U(n_1)+U(n_2)$','$U(n_1+n_2)$'])
    plt.title('Equal tests at Locations 8 and 9\n150k truth, 500 data')
    plt.xlabel('Number of tests at each location')
    plt.show()

# Focus *only* at 100 tests for each location; compare the bound and holistic utility under different levels of
#   truth draws
truthdrawslist = [5000, 20000, 50000, 75000, 100000, 125000, 150000]
utilcomblist, utilcombCIlist = [0 for x in range(len(truthdrawslist))], [(0,0) for x in range(len(truthdrawslist))]
utilsumlist, utilsumCIlist = [0 for x in range(len(truthdrawslist))], [(0,0) for x in range(len(truthdrawslist))]
tn1, tn2 = 9, 16
for i, currtruthdraws in enumerate(truthdrawslist):
    print('On ' + str(currtruthdraws) + ' draws...')
    # Set MCMC draws to use in fast algorithm
    numtruthdraws, numdatadraws = currtruthdraws, 300
    # Get random subsets for truth and data draws
    np.random.seed(58)
    truthdraws, datadraws = util.distribute_truthdata_draws(lgdict['postSamples'], numtruthdraws, numdatadraws)
    paramdict.update({'truthdraws': truthdraws, 'datadraws': datadraws})
    # Get base loss
    paramdict['baseloss'] = sampf.baseloss(paramdict['truthdraws'], paramdict)
    util.print_param_checks(paramdict)

    # Get bounds and holistic utility
    print('Location '+str(tn1) +'...')
    n = np.zeros(numTN)
    n[tn1] = 100
    util1, util1_CI = getUtilityEstimate(n, lgdict, paramdict)
    print('Location '+str(tn2) +'...')
    n = np.zeros(numTN)
    n[tn2] = 100
    util2, util2_CI = getUtilityEstimate(n, lgdict, paramdict)
    utilsumlist[i] = util1 + util2
    utilsumCIlist[i] = (util1_CI[0] + util2_CI[0], util1_CI[1] + util2_CI[1])
    # Holistic utility
    print('Holistic...')
    n = np.zeros(numTN)
    n[tn1], n[tn2] = 100, 100
    utilcomb, utilcomb_CI = getUtilityEstimate(n, lgdict, paramdict)
    utilcomblist[i] = utilcomb
    utilcombCIlist[i] = utilcomb_CI
    # Update plotting lists
    utilsumCIlistlower = [x[0] for x in utilsumCIlist]
    utilsumCIlistupper = [x[1] for x in utilsumCIlist]
    utilcombCIlistlower = [x[0] for x in utilcombCIlist]
    utilcombCIlistupper = [x[1] for x in utilcombCIlist]
    # Plot
    plt.plot(truthdrawslist, utilsumlist, color='orange', linewidth=3)
    plt.plot(truthdrawslist, utilcomblist, color='black', linewidth=3)
    plt.plot(truthdrawslist, utilsumCIlistlower, color='bisque', linestyle='dashed')
    plt.plot(truthdrawslist, utilsumCIlistupper, color='bisque', linestyle='dashed')
    plt.plot(truthdrawslist, utilcombCIlistlower, color='gray', linestyle='dashed')
    plt.plot(truthdrawslist, utilcombCIlistupper, color='gray', linestyle='dashed')
    plt.legend(['$U(n_1)+U(n_2)$', '$U(n_1+n_2)$'])
    plt.title('Bounds and real utility vs. truth draws\n100 tests at Locations 8 and 9, 300 MCMC data draws')
    plt.xlabel('Number of truth draws')
    plt.show()


# todo: (END OF COMPARING UTILITIES)
