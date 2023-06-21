from logistigate.logistigate import utilities as util # Pull from the submodule "develop" branch
from logistigate.logistigate import methods
from logistigate.logistigate.priors import prior_normal_assort
from logistigate.logistigate import lossfunctions as lf
from logistigate.logistigate import samplingplanfunctions as sampf

import os
import numpy as np
import matplotlib.cm as cm
import matplotlib
import matplotlib.pyplot as plt

from numpy.random import choice
import scipy.special as sps

# Set up initial data
Nfam = np.array([[1., 1., 10., 1., 3., 0., 1., 6., 7., 5., 0., 0., 4.],
                      [1., 1., 4., 2., 0., 1., 1., 2., 0., 4., 0., 0., 1.],
                      [3., 17., 31., 4., 2., 0., 1., 6., 0., 23., 1., 2., 5.],
                      [1., 1., 15., 2., 0., 0., 0., 1., 0., 6., 0., 0., 0.]])
Yfam = np.array([[0., 0., 7., 0., 3., 0., 1., 0., 1., 0., 0., 0., 4.],
                      [0., 0., 2., 2., 0., 1., 1., 0., 0., 1., 0., 0., 1.],
                      [0., 0., 15., 3., 2., 0., 0., 2., 0., 1., 1., 2., 5.],
                      [0., 0., 5., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0.]])
(numTN, numSN) = Nfam.shape # For later use
csdict_fam = util.initDataDict(Nfam, Yfam) # Initialize necessary logistigate keys
csdict_fam['TNnames'] = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26']
csdict_fam['SNnames'] = ['MNFR ' + str(i+1) for i in range(numSN)]

# Some summaries
TNtesttotals = np.sum(Nfam, axis=1)
TNsfptotals = np.sum(Yfam, axis=1)
TNrates = np.divide(TNsfptotals,TNtesttotals)
print('Tests at each test node:')
print(TNtesttotals)
print('Positives at each test node:')
print(TNsfptotals)
print('Positive rates at each test node:')
print(TNrates)

# Build prior
SNpriorMean = np.repeat(sps.logit(0.1), numSN)
# Establish test node priors according to assessment by regulators
TNpriorMean = sps.logit(np.array([0.1, 0.1, 0.15, 0.15]))
priorMean = np.concatenate((SNpriorMean, TNpriorMean))
TNvar, SNvar = 2., 4.  # Variances for use with prior; supply nodes are wide due to large
priorCovar = np.diag(np.concatenate((np.repeat(SNvar, numSN), np.repeat(TNvar, numTN))))
priorObj = prior_normal_assort(priorMean, priorCovar)
csdict_fam['prior'] = priorObj

# Set up MCMC
csdict_fam['MCMCdict'] = {'MCMCtype': 'NUTS', 'Madapt': 5000, 'delta': 0.4}
# Generate posterior draws
numdraws = 75000
csdict_fam['numPostSamples'] = numdraws
np.random.seed(1000) # To replicate draws later
csdict_fam = methods.GeneratePostSamples(csdict_fam)
# Print inference from initial data
# util.plotPostSamples(csdict_fam, 'int90')

# Loss specification
paramdict = lf.build_diffscore_checkrisk_dict(scoreunderestwt=5., riskthreshold=0.15, riskslope=0.6,
                                              marketvec=np.ones(numTN + numSN))

# Set limits of data collection and intervals for calculation
testmax, testint = 400, 10
testarr = np.arange(testint, testmax + testint, testint)

# Set MCMC draws to use in fast algorithm
numtruthdraws, numdatadraws = 75000, 2000
# Get random subsets for truth and data draws
np.random.seed(444)
truthdraws, datadraws = util.distribute_truthdata_draws(csdict_fam['postSamples'], numtruthdraws, numdatadraws)
paramdict.update({'truthdraws': truthdraws, 'datadraws': datadraws})
# Get base loss
paramdict['baseloss'] = sampf.baseloss(paramdict['truthdraws'], paramdict)

util.print_param_checks(paramdict)  # Check of used parameters

###############
# UPDATED HEURISTIC
###############
alloc, util_avg, util_hi, util_lo = sampf.get_greedy_allocation(csdict_fam, testmax, testint, paramdict,
                                                                printupdate=True, plotupdate=True,
                                                                plottitlestr='Familiar Setting')
'''
[1, 1, 1, 1, 1, 0, 1, 1, 0,
 0, 1, 1, 2, 2, 0, 2, 1, 2,
 0, 2, 2, 1, 1, 1, 2, 3, 0,
 2, 0, 0, 2, 0, 2, 1, ]
[(0.08709501401732922, 0.09248817606288728), (0.15485069147878416, 0.16180554729293029), (0.21132869080310357, 0.21931614005076927),
(0.25203372890146003, 0.26063269080331164), (0.29508233713522936, 0.3040828160807423), (0.3287205863959288, 0.33822854576624817), 
(0.36679105798445644, 0.3762582028535526), (0.3971444263505597, 0.4070388117759731), (0.42485199517149574, 0.4353124807349904),
(0.4486951832489643, 0.45897840819784275), (0.4761109827432908, 0.48670866415972003), (0.4987593570451616, 0.5097299074978237),
(0.5263266477028608, 0.5378674990051908), (0.5478847373930049, 0.5603035172340813), (0.5694258037490463, 0.5816813331255415),
(0.5935104072398629, 0.6068050714362494), (0.6142821720902099, 0.6267292115039553), (0.6375264642099632, 0.651162904882391),
(0.6569186350254319, 0.6712814975687573), (0.6751661618775924, 0.6901828740981897), (0.6991582605312183, 0.7140608585450436),
(0.7218481897152977, 0.7377503914991284), (0.7391189140792602, 0.7550833236590053), (0.7595669154703588, 0.7763418662828772),
(0.7728264632929887, 0.7898690825001178), (0.7930497369742868, 0.8103019605083919), (0.8096944981072554, 0.8272548106037041),
(0.8314307088795085, 0.8494696827012405), (0.8509469900480071, 0.8700952115080858), (0.8698554241240988, 0.8897037201438907),
(0.8914266265511126, 0.9116777365803721), (0.9113010414418516, 0.9332423013141198), (0.9227597014567777, 0.9449340291518391),
(0.9476763861351147, 0.9699704646742606), 
]
'''
np.save(os.path.join('casestudyoutputs', 'familiar', 'fam_alloc'), alloc)
np.save(os.path.join('casestudyoutputs', 'familiar', 'fam_util_avg'), util_avg)
np.save(os.path.join('casestudyoutputs', 'familiar', 'fam_util_hi'), util_hi)
np.save(os.path.join('casestudyoutputs', 'familiar', 'fam_util_lo'), util_lo)

# Evaluate utility for uniform and rudimentary
util_avg_unif, util_hi_unif, util_lo_unif = np.zeros((int(testmax / testint) + 1)), \
                                            np.zeros((int(testmax / testint) + 1)), \
                                            np.zeros((int(testmax / testint) + 1))
util_avg_rudi, util_hi_rudi, util_lo_rudi = np.zeros((int(testmax / testint) + 1)), \
                                            np.zeros((int(testmax / testint) + 1)), \
                                            np.zeros((int(testmax / testint) + 1))
plotupdate = True
for testind in range(testarr.shape[0]):
    # Uniform utility
    des_unif = util.round_design_low(np.ones(numTN) / numTN, testarr[testind]) / testarr[testind]
    currlosslist = sampf.sampling_plan_loss_list(des_unif, testarr[testind], csdict_fam, paramdict)
    avg_loss, avg_loss_CI = sampf.process_loss_list(currlosslist, zlevel=0.95)
    util_avg_unif[testind+1] = paramdict['baseloss'] - avg_loss
    util_lo_unif[testind+1] = paramdict['baseloss'] - avg_loss_CI[1]
    util_hi_unif[testind+1] = paramdict['baseloss'] - avg_loss_CI[0]
    print(des_unif)
    print('Utility at ' + str(testarr[testind]) + ' tests, Uniform: ' + str(util_avg_unif[testind+1]))
    # Rudimentary utility
    des_rudi = util.round_design_low(np.divide(np.sum(Nfam, axis=1), np.sum(Nfam)), testarr[testind]) / testarr[testind]
    currlosslist = sampf.sampling_plan_loss_list(des_rudi, testarr[testind], csdict_fam, paramdict)
    avg_loss, avg_loss_CI = sampf.process_loss_list(currlosslist, zlevel=0.95)
    util_avg_rudi[testind+1] = paramdict['baseloss'] - avg_loss
    util_lo_rudi[testind+1] = paramdict['baseloss'] - avg_loss_CI[1]
    util_hi_rudi[testind+1] = paramdict['baseloss'] - avg_loss_CI[0]
    print(des_rudi)
    print('Utility at ' + str(testarr[testind]) + ' tests, Rudimentary: ' + str(util_avg_rudi[testind+1]))
    if plotupdate:
        util_avg_arr = np.vstack((util_avg_unif, util_avg_rudi))
        util_hi_arr = np.vstack((util_hi_unif, util_hi_rudi))
        util_lo_arr = np.vstack((util_lo_unif, util_lo_rudi))
        # Plot
        util.plot_marg_util_CI(util_avg_arr, util_hi_arr, util_lo_arr, testmax=testmax, testint=testint,
                               titlestr='Familiar Setting, comparison with other approaches')

# Store matrices
np.save(os.path.join('casestudyoutputs', 'familiar', 'util_avg_arr_fam'), util_avg_arr)
np.save(os.path.join('casestudyoutputs', 'familiar', 'util_hi_arr_fam'), util_hi_arr)
np.save(os.path.join('casestudyoutputs', 'familiar', 'util_lo_arr_fam'), util_lo_arr)

targind = 5 # where do we want to gauge budget savings?
targval = util_avg_arr[0][targind]

# Uniform
kInd = next(x for x, val in enumerate(util_avg_arr[1].tolist()) if val > targval)
unif_saved = round((targval - util_avg_arr[1][kInd - 1]) / (util_avg_arr[1][kInd] - util_avg_arr[1][kInd - 1]) *\
                      testint) + (kInd - 1) * testint - targind*testint
print(unif_saved)  #
# Rudimentary
kInd = next(x for x, val in enumerate(util_avg_arr[2].tolist()) if val > targval)
rudi_saved = round((targval - util_avg_arr[2][kInd - 1]) / (util_avg_arr[2][kInd] - util_avg_arr[2][kInd - 1]) *\
                      testint) + (kInd - 1) * testint - targind*testint
print(rudi_saved)  #
