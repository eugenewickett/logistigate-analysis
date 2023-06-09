"""
Script that generates plots presented in the paper.
Inference generation requires use of the logistigate package, available at https://logistigate.readthedocs.io/en/main/.
"""

from logistigate.logistigate import utilities as util  # Pull from the submodule "develop" branch
from logistigate.logistigate import methods, lg
from logistigate.logistigate import lossfunctions as lf
from logistigate.logistigate import samplingplanfunctions as sampf
from logistigate.logistigate.priors import prior_normal_assort
import os
import numpy as np
from numpy.random import choice
import scipy.special as sps
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def showriskvalues():
    """Generate a figure showcasing how the risk changes with different parameter choices"""
    x = np.linspace(0.001, 0.999, 1000)
    t = 0.3  # Our target
    y1 = (x + 2 * (0.5 - t)) * (1 - x)
    tauvec = [0.05, 0.2, 0.4, 0.6, 0.95]
    fig, ax = plt.subplots(figsize=(8, 7))
    for tau in tauvec:
        newy = [1 - x[i] * (tau - (1 - (t / x[i]) if x[i] < t else 0)) for i in range(len(x))]
        plt.plot(x, newy)
    # plt.plot(x,y1)
    import matplotlib.ticker as mtick
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.title('Values for selected risk terms\n$l=30\%$', fontdict={'fontsize': 16, 'fontname': 'Trebuchet MS'})
    plt.ylabel('Risk value', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.xlabel('SFP rate', fontdict={'fontsize': 14, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.97, '$m=0.05$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.84, '$m=0.2$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.675, '$m=0.4$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.50, '$m=0.6$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    plt.text(0.84, 0.21, '$m=0.95$', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    # plt.text(0.00, 0.47, 'Parabolic', fontdict={'fontsize': 12, 'fontname': 'Trebuchet MS'})
    fig.tight_layout()
    plt.show()
    plt.close()
    return


def showpriorselicitedfromrisk():
    """Produce chart depicting SFP rate priors, as in Section 5.2 of the paper"""
    # Extremely Low Risk, Very Low Risk, Low Risk, Moderate Risk, Moderately High Risk, High Risk, Very High Risk
    riskList = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25]
    riskNames = ['Extremely Low', 'Very Low', 'Low', 'Moderate', 'Moderately High', 'High', 'Very High']
    varConst = 2.
    xArr = sps.logit(np.arange(0.001, 1., 0.001))
    for riskInd, currRisk in enumerate(riskList):
        currPriorObj = prior_normal_assort(sps.logit(currRisk), np.array([varConst]).reshape((1, 1)))
        yArr = np.exp(np.array([currPriorObj.lpdf(xArr[i]) for i in range(xArr.shape[0])]))
        plt.plot(sps.expit(xArr), yArr, label=riskNames[riskInd], dashes=[1, riskInd])
    plt.xlabel('SFP Rate')
    plt.ylabel('Density')
    plt.legend(fancybox=True, title='Risk Level', fontsize='small')
    plt.title('Densities for Assessed SFP Rate Risks')
    plt.show()

    currRisk = 0.2
    currPriorObj = prior_normal_assort(sps.logit(currRisk), np.array([varConst]).reshape((1, 1)))
    yArr = np.exp(np.array([currPriorObj.lpdf(xArr[i]) for i in range(xArr.shape[0])]))
    yArrcmsm = np.cumsum(yArr) / np.sum(yArr)
    ind1 = next(x for x, val in enumerate(yArrcmsm) if val > 0.05) - 1
    ind2 = next(x for x, val in enumerate(yArrcmsm) if val > 0.95)
    sps.expit(xArr[ind1])
    sps.expit(xArr[ind2])

    return


def example_planutility():
    """Produce two plots of the example of plan utility"""
    baseutil_arr = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_arr_example_base.npy'))
    adjutil_arr = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_arr_example_adj.npy'))
    testmax, testint = 60, 4
    util.plot_marg_util(baseutil_arr, testmax=testmax, testint=testint,
                        colors=['blue', 'red', 'green'], titlestr='$v=1$',
                        labels=['Focused', 'Uniform', 'Adapted'])
    util.plot_marg_util(adjutil_arr, testmax=testmax, testint=testint,
                        colors=['blue', 'red', 'green'], titlestr='$v=10$',
                        labels=['Focused', 'Uniform', 'Adapted'])

    return


def casestudyplots_familiar():
    """
    Cleaned up plots for use in case study in paper
    """
    testmax, testint = 400, 10
    TNnames = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26']
    numTN = len(TNnames)

    heur_util = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_fam.npy'))

    #### REMOVE LATER; 9-JUN
    heur_util_hi = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_hi_fam.npy'))
    heur_util_lo = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_lo_fam.npy'))
    util.plot_marg_util(heur_util,testmax,testint,colors = cm.rainbow(np.linspace(0, 0.5, numTN)),utilmax=1.0)
    util.plot_marg_util_CI(heur_util,heur_util_hi, heur_util_lo,testmax,testint, utilmax=1.0,
                           colors = cm.rainbow(np.linspace(0, 0.5, numTN)))
    ################

    # Size of figure layout for all figures
    figtup = (7, 5)
    titleSz, axSz, labelSz = 12, 10, 9
    xMax = 450

    #######################
    # Plot of marginal utilities
    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [TNnames[ind] for ind in range(numTN)]

    x = range(testint, testmax + 1, testint)
    deltaArr = np.zeros((heur_util.shape[0], heur_util.shape[1] - 1))
    for rw in range(deltaArr.shape[0]):
        for col in range(deltaArr.shape[1]):
            deltaArr[rw, col] = heur_util[rw, col + 1] - heur_util[rw, col]
    yMax = np.max(deltaArr) * 1.1

    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    for tnind in range(numTN):
        plt.text(testint * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., yMax])
    plt.xlim([0., xMax])
    plt.xlabel('Number of Tests', fontsize=axSz)
    plt.ylabel('Marginal Utility Gain', fontsize=axSz)
    plt.title('Marginal Utility with Increasing Tests\nFamiliar Setting', fontsize=titleSz)
    plt.show()
    plt.close()
    #######################

    #######################
    # Allocation plot
    allocArr, objValArr = sampf.smooth_alloc_forward(heur_util)
    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [TNnames[ind] for ind in range(numTN)]
    x = range(testint, testmax + 1, testint)
    _ = plt.figure(figsize=figtup)
    for tnind in range(allocArr.shape[0]):
        plt.plot(x, allocArr[tnind] * testint, linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    # allocMax = allocArr.max() * testInt * 1.1
    allocMax = 185
    for tnind in range(numTN):
        plt.text(testmax * 1.01, allocArr[tnind, -1] * testint, labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., allocMax])
    plt.xlim([0., xMax])
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Test Node Allocation', fontsize=axSz)
    plt.title('Sampling Plan vs. Budget\nFamiliar Setting', fontsize=titleSz)
    # plt.tight_layout()
    plt.show()
    plt.close()
    #######################

    #######################
    # Policy utility comparison
    util_arr = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_arr_fam.npy'))
    util_arr_hi = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_hi_arr_fam.npy'))
    util_arr_lo = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_lo_arr_fam.npy'))
    # Utility comparison plot
    colors = cm.rainbow(np.linspace(0, 0.8, 3))
    labels = ['Heuristic', 'Uniform', 'Rudimentary']
    x = range(0, testmax + 1, testint)
    utilMax = -1
    for lst in util_arr:
        currMax = np.amax(np.array(lst))
        if currMax > utilMax:
            utilMax = currMax
    utilMax = utilMax * 1.1

    _ = plt.figure(figsize=figtup)
    for groupind in range(3):
        plt.plot(x, util_arr[groupind], color=colors[groupind], linewidth=0.7, alpha=1.,
                 label=labels[groupind] + ' 95% CI')
        plt.fill_between(x, util_arr_hi[groupind], util_arr_lo[groupind], color=colors[groupind], alpha=0.2)
        # Line label
        plt.text(x[-1] * 1.01, util_arr[groupind][-1], labels[groupind].ljust(15), fontsize=labelSz - 1)
    plt.ylim(0, utilMax)
    # plt.xlim(0,x[-1]*1.12)
    plt.xlim([0., xMax])
    leg = plt.legend(loc='upper left', fontsize=labelSz)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(1.0)
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Plan Utility', fontsize=axSz)
    plt.title('Utility from Heuristic vs. Uniform and Rudimentary Allocations\nFamiliar Setting', fontsize=titleSz)
    '''
    # Add text box showing budgetary savings
    heurutilavg = np.average(np.array(heur_utillist), axis=0)
    x2, x3 = 130, 156
    plt.plot([100, x3], [heurutilavg[9], heurutilavg[9]], color='black', linestyle='--')
    iv = 0.015
    plt.plot([100, 100], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.plot([x2, x2], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.plot([x3, x3], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.text(110, heurutilavg[9] + iv / 2, '30', fontsize=labelSz)
    plt.text(139, heurutilavg[9] + iv / 2, '26', fontsize=labelSz)
    # plt.tight_layout()
    '''
    plt.show()
    plt.close()
    #######################






    # List of comprehensive utilities for heuristic
    heur_utillist = [np.array([0.06382507, 0.10506746, 0.14113592, 0.17609555, 0.20035397,
                               0.22949996, 0.25375875, 0.2778598, 0.29984599, 0.31620371,
                               0.33690511, 0.35860444, 0.38146605, 0.39525024, 0.41716017,
                               0.43594724, 0.45317528, 0.47051066, 0.49091332, 0.50682803,
                               0.52018989, 0.5418224, 0.55684317, 0.57245363, 0.58670926,
                               0.60898051, 0.62757192, 0.63987248, 0.65232003, 0.65433092,
                               0.67671267, 0.69184994, 0.70314622, 0.72154417, 0.73680664,
                               0.75444832, 0.76425734, 0.7791746, 0.79497273, 0.81572736]),
                     np.array([0.06462517, 0.10961266, 0.14617499, 0.17780936, 0.20363225,
                               0.23041206, 0.25740358, 0.27766876, 0.29312512, 0.31557361,
                               0.33530329, 0.36081813, 0.37704713, 0.39551182, 0.41443499,
                               0.42955573, 0.45339857, 0.46742178, 0.48380338, 0.49736288,
                               0.51375158, 0.52478321, 0.54409508, 0.56177912, 0.57468272,
                               0.60456728, 0.61228665, 0.62588728, 0.64313516, 0.65165524,
                               0.67121902, 0.68439816, 0.70397772, 0.70821652, 0.72513014,
                               0.74635225, 0.76193202, 0.78094993, 0.79430877, 0.79052913]),
                     np.array([0.06085764, 0.0980188, 0.13265826, 0.16569316, 0.18822259,
                               0.21785427, 0.24407703, 0.2614815, 0.27854984, 0.29983535,
                               0.32327982, 0.33844527, 0.36191535, 0.37881142, 0.40331534,
                               0.41365246, 0.43214752, 0.45162729, 0.46968644, 0.48396314,
                               0.50285393, 0.51030504, 0.52897311, 0.54987342, 0.56226242,
                               0.57793117, 0.59861256, 0.62137804, 0.6242618, 0.64609686,
                               0.66280318, 0.67326059, 0.68449137, 0.70604726, 0.71027971,
                               0.73686349, 0.7435827, 0.76857242, 0.78926802, 0.79741367]),
                     np.array([0.03106763, 0.07286322, 0.10998372, 0.13812251, 0.16879457,
                               0.19922628, 0.22801597, 0.2485636, 0.2655454, 0.28958374,
                               0.31674403, 0.33936658, 0.36231108, 0.38167127, 0.3972411,
                               0.41753462, 0.43264919, 0.45685282, 0.47436211, 0.49088067,
                               0.50921795, 0.51783368, 0.54229446, 0.55684378, 0.57610806,
                               0.5857951, 0.6096527, 0.6216253, 0.64198431, 0.65428421,
                               0.67196841, 0.69638327, 0.70304679, 0.7208629, 0.7348868,
                               0.75061593, 0.76318879, 0.772441, 0.79820724, 0.80558449]),
                     np.array([0.05668697, 0.10262769, 0.14105674, 0.17363495, 0.19806695,
                               0.22564098, 0.2548294, 0.27660807, 0.29434048, 0.31304457,
                               0.3343722, 0.35648835, 0.37606117, 0.39276222, 0.41150551,
                               0.42859706, 0.44436224, 0.4648064, 0.47967852, 0.49365363,
                               0.51332197, 0.52561107, 0.53779699, 0.55870816, 0.57876923,
                               0.59554469, 0.60538101, 0.62178017, 0.64004709, 0.6613331,
                               0.66403962, 0.68249925, 0.70066103, 0.7172556, 0.73394783,
                               0.75314802, 0.76254153, 0.7733508, 0.79292171, 0.79750005]),
                     np.array([0.07613541, 0.12165789, 0.15831771, 0.19297246, 0.21287435,
                               0.24560646, 0.26539924, 0.29110604, 0.31387596, 0.33061212,
                               0.35200531, 0.3753401, 0.39611738, 0.41093078, 0.4336867,
                               0.45234595, 0.46762176, 0.48661515, 0.50080393, 0.52090974,
                               0.53825081, 0.55038007, 0.56724664, 0.58236747, 0.60817663,
                               0.62400145, 0.63779373, 0.64763286, 0.67565383, 0.67301454,
                               0.70715914, 0.7096781, 0.72837052, 0.74372657, 0.75980874,
                               0.78666726, 0.79364461, 0.80827571, 0.82764946, 0.83088659])]
    # List of rudimentary comprehensive utilities
    rudi_utillist = [np.array([0.01121986, 0.02582556, 0.05046794, 0.06909151, 0.09436937,
                               0.11395778, 0.13825574, 0.15913521, 0.18671247, 0.20126907,
                               0.22741945, 0.24433737, 0.26078601, 0.27958456, 0.30440025,
                               0.31756519, 0.33673802, 0.35254002, 0.37326871, 0.39652775,
                               0.41000818, 0.43284291, 0.43977554, 0.46238721, 0.47483195,
                               0.48857267, 0.51441441, 0.53274999, 0.54548249, 0.55525837,
                               0.57250429, 0.59758681, 0.61096384, 0.62156961, 0.64501836,
                               0.65556402, 0.68559985, 0.67583804, 0.70181668, 0.71108492]),
                     np.array([0.02795243, 0.04726679, 0.0672626, 0.08798852, 0.10614938,
                               0.13053853, 0.15074945, 0.16747773, 0.18907569, 0.20509474,
                               0.22974192, 0.24578162, 0.25939473, 0.2756333, 0.29528029,
                               0.31613174, 0.33619955, 0.35107068, 0.3705562, 0.38667639,
                               0.40195513, 0.42197244, 0.43369534, 0.45898202, 0.47330496,
                               0.49375738, 0.5031161, 0.51690998, 0.53128846, 0.54648137,
                               0.56853023, 0.58321203, 0.59913081, 0.60826631, 0.63340863,
                               0.64153133, 0.65420011, 0.66901826, 0.68571198, 0.69962928]),
                     np.array([0.04086377, 0.05221949, 0.07480906, 0.09650311, 0.1114406,
                               0.13082882, 0.14498035, 0.16857216, 0.18237847, 0.20280144,
                               0.2231874, 0.23503265, 0.25486982, 0.27445497, 0.29105611,
                               0.3066886, 0.33083936, 0.34721591, 0.35844714, 0.38550175,
                               0.39518974, 0.41596949, 0.42867096, 0.4442613, 0.45951736,
                               0.47113222, 0.49388963, 0.50549801, 0.53117332, 0.54374756,
                               0.55286615, 0.57443072, 0.57891583, 0.6097668, 0.61971831,
                               0.63586965, 0.64704409, 0.66162538, 0.66971241, 0.69195201]),
                     np.array([0.01254531, 0.02879158, 0.05278567, 0.07742554, 0.09959865,
                               0.12440331, 0.1466998, 0.16690664, 0.19043403, 0.21231485,
                               0.23001318, 0.25082075, 0.26544161, 0.28613121, 0.30800187,
                               0.32662875, 0.35020767, 0.36735421, 0.3919072, 0.39784319,
                               0.41268325, 0.43892994, 0.45696821, 0.46975601, 0.48625379,
                               0.50348896, 0.52252359, 0.53017677, 0.55093142, 0.56604239,
                               0.58815811, 0.60038772, 0.61420697, 0.6325675, 0.65074301,
                               0.66382202, 0.6776332, 0.68637533, 0.70271301, 0.72212557]),
                     np.array([0.03337605, 0.05147919, 0.07110944, 0.09467589, 0.11535336,
                               0.13082484, 0.15407198, 0.17047731, 0.18791144, 0.21047454,
                               0.22739688, 0.24646216, 0.26520206, 0.2820505, 0.30520826,
                               0.31922798, 0.33720306, 0.35925602, 0.36941223, 0.39679792,
                               0.40310058, 0.42532935, 0.43732679, 0.46038079, 0.47657938,
                               0.49378628, 0.51291656, 0.52468943, 0.54440889, 0.55303288,
                               0.56610784, 0.58843534, 0.60933449, 0.61384461, 0.62954021,
                               0.64933632, 0.66456395, 0.67793322, 0.69492135, 0.68922654])]

    avgheurarr = np.average(np.array(heurlist), axis=0)









    return


def casestudyplots_familiar_market():
    """
    Cleaned up plots for use in case study in paper
    """
    testmax, testint = 400, 10
    TNnames = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26']
    numTN = len(TNnames)

    heur_util = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_fam_market.npy'))

    #### REMOVE LATER; 9-JUN
    heur_util_hi = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_hi_fam_market.npy'))
    heur_util_lo = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_lo_fam_market.npy'))
    util.plot_marg_util(heur_util,testmax,testint,colors = cm.rainbow(np.linspace(0, 0.5, numTN)),utilmax=1.0)
    util.plot_marg_util_CI(heur_util,heur_util_hi, heur_util_lo,testmax,testint, utilmax=1.0,
                           colors = cm.rainbow(np.linspace(0, 0.5, numTN)))
    ################

    # Size of figure layout for all figures
    figtup = (7, 5)
    titleSz, axSz, labelSz = 12, 10, 9
    xMax = 450

    #######################
    # Plot of marginal utilities
    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [TNnames[ind] for ind in range(numTN)]

    x = range(testint, testmax + 1, testint)
    deltaArr = np.zeros((heur_util.shape[0], heur_util.shape[1] - 1))
    for rw in range(deltaArr.shape[0]):
        for col in range(deltaArr.shape[1]):
            deltaArr[rw, col] = heur_util[rw, col + 1] - heur_util[rw, col]
    yMax = np.max(deltaArr) * 1.1

    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    for tnind in range(numTN):
        plt.text(testint * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., yMax])
    plt.xlim([0., xMax])
    plt.xlabel('Number of Tests', fontsize=axSz)
    plt.ylabel('Marginal Utility Gain', fontsize=axSz)
    plt.title('Marginal Utility with Increasing Tests\nFamiliar Setting', fontsize=titleSz)
    plt.show()
    plt.close()
    #######################

    #######################
    # Allocation plot
    allocArr, objValArr = sampf.smooth_alloc_forward(heur_util)
    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [TNnames[ind] for ind in range(numTN)]
    x = range(testint, testmax + 1, testint)
    _ = plt.figure(figsize=figtup)
    for tnind in range(allocArr.shape[0]):
        plt.plot(x, allocArr[tnind] * testint, linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    # allocMax = allocArr.max() * testInt * 1.1
    allocMax = 185
    for tnind in range(numTN):
        plt.text(testmax * 1.01, allocArr[tnind, -1] * testint, labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., allocMax])
    plt.xlim([0., xMax])
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Test Node Allocation', fontsize=axSz)
    plt.title('Sampling Plan vs. Budget\nFamiliar Setting', fontsize=titleSz)
    # plt.tight_layout()
    plt.show()
    plt.close()
    #######################

    #######################
    # Policy utility comparison
    util_arr = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_avg_arr_fam.npy'))
    util_arr_hi = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_hi_arr_fam.npy'))
    util_arr_lo = np.load(os.path.join('casestudyoutputs', '31MAY', 'util_lo_arr_fam.npy'))
    # Utility comparison plot
    colors = cm.rainbow(np.linspace(0, 0.8, 3))
    labels = ['Heuristic', 'Uniform', 'Rudimentary']
    x = range(0, testmax + 1, testint)
    utilMax = -1
    for lst in util_arr:
        currMax = np.amax(np.array(lst))
        if currMax > utilMax:
            utilMax = currMax
    utilMax = utilMax * 1.1

    _ = plt.figure(figsize=figtup)
    for groupind in range(3):
        plt.plot(x, util_arr[groupind], color=colors[groupind], linewidth=0.7, alpha=1.,
                 label=labels[groupind] + ' 95% CI')
        plt.fill_between(x, util_arr_hi[groupind], util_arr_lo[groupind], color=colors[groupind], alpha=0.2)
        # Line label
        plt.text(x[-1] * 1.01, util_arr[groupind][-1], labels[groupind].ljust(15), fontsize=labelSz - 1)
    plt.ylim(0, utilMax)
    # plt.xlim(0,x[-1]*1.12)
    plt.xlim([0., xMax])
    leg = plt.legend(loc='upper left', fontsize=labelSz)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(1.0)
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Plan Utility', fontsize=axSz)
    plt.title('Utility from Heuristic vs. Uniform and Rudimentary Allocations\nFamiliar Setting', fontsize=titleSz)
    '''
    # Add text box showing budgetary savings
    heurutilavg = np.average(np.array(heur_utillist), axis=0)
    x2, x3 = 130, 156
    plt.plot([100, x3], [heurutilavg[9], heurutilavg[9]], color='black', linestyle='--')
    iv = 0.015
    plt.plot([100, 100], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.plot([x2, x2], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.plot([x3, x3], [heurutilavg[9] - iv, heurutilavg[9] + iv], color='black', linestyle='--')
    plt.text(110, heurutilavg[9] + iv / 2, '30', fontsize=labelSz)
    plt.text(139, heurutilavg[9] + iv / 2, '26', fontsize=labelSz)
    # plt.tight_layout()
    '''
    plt.show()
    plt.close()
    #######################
    return


def casestudyplots_exploratory():
    """
    Cleaned up plots for use in case study in paper
    """
    testMax, testInt = 400, 10
    tnNames = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26',
               'MODHIGH_EXPL_1', 'MOD_EXPL_1', 'MODHIGH_EXPL_2', 'MOD_EXPL_2']
    numTN = len(tnNames)

    unif_utillist = [np.array([0.08841012, 0.15565143, 0.24106519, 0.29720411, 0.34670028,
                               0.40441693, 0.4520183, 0.49299778, 0.53293407, 0.56663843,
                               0.6068871, 0.64709646, 0.69159897, 0.72380886, 0.76514307,
                               0.79660616, 0.83239866, 0.86195176, 0.89731708, 0.94318546,
                               0.96943093, 1.00218572, 1.03152891, 1.06727324, 1.10070594,
                               1.11977055, 1.15212293, 1.1835634, 1.22617661, 1.24228975,
                               1.25780729, 1.2959397, 1.30176525, 1.34451775, 1.35307222,
                               1.38860051, 1.40130638, 1.41632717, 1.46246785, 1.46821944]),
                     np.array([0.10204536, 0.17203302, 0.26286992, 0.32361954, 0.37307678,
                               0.43085786, 0.47399878, 0.51503033, 0.56066216, 0.58983501,
                               0.63725473, 0.68409818, 0.72126763, 0.7579929, 0.79671422,
                               0.82811037, 0.87382789, 0.90458568, 0.93059176, 0.97441651,
                               1.00657399, 1.04076035, 1.06359108, 1.10439937, 1.13673226,
                               1.16499527, 1.19547982, 1.22635456, 1.24430843, 1.27061623,
                               1.30162455, 1.3234999, 1.34651722, 1.37148126, 1.38155695,
                               1.41888158, 1.42802216, 1.46714458, 1.47241259, 1.49288413]),
                     np.array([0.09591184, 0.16438589, 0.2464366, 0.29357483, 0.34867104,
                               0.40393655, 0.44666241, 0.48435072, 0.51989594, 0.56288725,
                               0.60492358, 0.64595947, 0.68866638, 0.720943, 0.7516753,
                               0.78981393, 0.8418654, 0.86775926, 0.90246394, 0.92999427,
                               0.97223517, 0.99205388, 1.02163245, 1.05835929, 1.0956864,
                               1.12370356, 1.14435483, 1.16793021, 1.20470649, 1.2345608,
                               1.25611448, 1.29008477, 1.309387, 1.31975911, 1.36674577,
                               1.37997659, 1.41873672, 1.41450192, 1.43315206, 1.47705606]),
                     np.array([0.0944134, 0.15753564, 0.2466545, 0.29581787, 0.34538147,
                               0.40123685, 0.43931291, 0.48930003, 0.52918134, 0.56084947,
                               0.60789135, 0.64990563, 0.69058907, 0.72247047, 0.74809329,
                               0.7948111, 0.83155204, 0.86321651, 0.90468742, 0.94411321,
                               0.96898088, 1.0108199, 1.04053446, 1.06833746, 1.09215482,
                               1.12378437, 1.1659193, 1.18378993, 1.21288696, 1.24283401,
                               1.27446602, 1.28378132, 1.32848316, 1.32849597, 1.36228587,
                               1.37765224, 1.4101449, 1.434839, 1.46371489, 1.49483553]),
                     np.array([0.08167338, 0.14426625, 0.23216857, 0.28673666, 0.34123239,
                               0.40118761, 0.4392709, 0.48147611, 0.51745304, 0.55110435,
                               0.59909138, 0.63991174, 0.67302489, 0.7198011, 0.75057478,
                               0.78746757, 0.81611783, 0.84495377, 0.90048518, 0.91688154,
                               0.95922155, 0.99517221, 1.02932481, 1.04923235, 1.07165201,
                               1.1074072, 1.13628663, 1.16238786, 1.19292199, 1.2345284,
                               1.2403106, 1.27659058, 1.30487102, 1.31820484, 1.35435169,
                               1.36126559, 1.38600291, 1.41808144, 1.42049657, 1.4753968])]
    u1 = np.array([[0., 0.01370871, 0.02721286, 0.03927982, 0.05452284,
                    0.06793247, 0.08467647, 0.09884958, 0.11188748, 0.12701369,
                    0.14242682, 0.15519745, 0.16426655, 0.17721345, 0.18874887,
                    0.20080715, 0.2174723, 0.22957547, 0.24128003, 0.25284885,
                    0.26999562, 0.27227524, 0.285285, 0.30104995, 0.3106667,
                    0.32308282, 0.34033547, 0.34960294, 0.36711967, 0.36755109,
                    0.38213335, 0.39813622, 0.40431941, 0.41807373, 0.44008736,
                    0.44621208, 0.45729339, 0.47182772, 0.48041673, 0.50118371,
                    0.50578378], [0., 0.0177643, 0.0484185, 0.08466584, 0.11830092,
                                  0.14526983, 0.17521789, 0.1959544, 0.2245966, 0.23822277,
                                  0.26394879, 0.27914504, 0.29824563, 0.31080199, 0.33435344,
                                  0.34475255, 0.35845854, 0.37206035, 0.39446089, 0.40394131,
                                  0.42265103, 0.43150062, 0.44479741, 0.46461682, 0.47565933,
                                  0.48575569, 0.49356322, 0.50997754, 0.52745362, 0.54225208,
                                  0.55063018, 0.56191794, 0.5748904, 0.59308343, 0.59980207,
                                  0.61386689, 0.62652607, 0.6404477, 0.64798804, 0.65706472,
                                  0.67933473], [0., 0.01860281, 0.03618445, 0.05157131, 0.06651107,
                                                0.08038161, 0.09281834, 0.10386108, 0.11924589, 0.13002617,
                                                0.14412546, 0.16067258, 0.16773345, 0.18438164, 0.19582281,
                                                0.20574012, 0.21796031, 0.23243894, 0.24337217, 0.2538692,
                                                0.26680333, 0.28101002, 0.29062747, 0.29779574, 0.31459065,
                                                0.32642133, 0.33884015, 0.34894659, 0.36112478, 0.37493854,
                                                0.38390646, 0.3995448, 0.41034582, 0.42423312, 0.441534,
                                                0.45350752, 0.46307694, 0.47441329, 0.48733603, 0.50068675,
                                                0.51561299],
                   [0., 0.00499312, 0.00937327, 0.01325934, 0.0201864,
                    0.02342159, 0.03017277, 0.03308807, 0.03778782, 0.0401396,
                    0.04797272, 0.05014935, 0.0498213, 0.05927459, 0.0615047,
                    0.06385748, 0.06644146, 0.07134689, 0.07430214, 0.0787555,
                    0.0795194, 0.07970275, 0.08742641, 0.08823035, 0.09368481,
                    0.09892619, 0.09545174, 0.10107404, 0.1014675, 0.10578594,
                    0.10843766, 0.11033136, 0.1121058, 0.1143788, 0.11878527,
                    0.11866421, 0.12307765, 0.12554614, 0.12820374, 0.1338453,
                    0.13209692], [0., 0.06753916, 0.11102386, 0.14171526, 0.16561019,
                                  0.18470288, 0.20110686, 0.21548701, 0.23090971, 0.24588359,
                                  0.25715521, 0.27331621, 0.27901669, 0.29116912, 0.30392201,
                                  0.31685425, 0.32447691, 0.33532122, 0.34488459, 0.34980556,
                                  0.36711906, 0.3724163, 0.38672256, 0.39754085, 0.40694953,
                                  0.41181078, 0.42506026, 0.4347105, 0.4456633, 0.45751324,
                                  0.46231055, 0.46985531, 0.48506576, 0.49429605, 0.49278221,
                                  0.51080041, 0.51818947, 0.5273377, 0.53723917, 0.54475222,
                                  0.56189272], [0., 0.04789961, 0.07651653, 0.09216094, 0.11196046,
                                                0.12604742, 0.13907624, 0.15326034, 0.15988534, 0.16789339,
                                                0.17992271, 0.18796854, 0.19548305, 0.2055738, 0.21052402,
                                                0.21848837, 0.22457757, 0.231984, 0.24354059, 0.24976444,
                                                0.25901347, 0.26271451, 0.27196188, 0.27694731, 0.28917653,
                                                0.29700992, 0.29796911, 0.309138, 0.31974951, 0.32615696,
                                                0.33441138, 0.34054645, 0.34848665, 0.35434708, 0.3557176,
                                                0.37620324, 0.37246803, 0.38837597, 0.39107254, 0.39851604,
                                                0.40797497],
                   [0., 0.06672969, 0.10620611, 0.13393342, 0.15588391,
                    0.17321403, 0.18634844, 0.1994182, 0.21172324, 0.22335018,
                    0.23195684, 0.24295284, 0.25054209, 0.25933377, 0.26967944,
                    0.27611864, 0.28248287, 0.29301519, 0.30000162, 0.30392916,
                    0.31281392, 0.32085651, 0.32841254, 0.33075745, 0.34052802,
                    0.35052362, 0.35457928, 0.36143623, 0.36908656, 0.37500426,
                    0.38275917, 0.38565137, 0.39109715, 0.40094247, 0.41008627,
                    0.41188694, 0.42282457, 0.42458837, 0.43117168, 0.43868673,
                    0.44432574], [0., 0.11955574, 0.1640861, 0.19837867, 0.22337565,
                                  0.24261872, 0.26437644, 0.27878976, 0.29118663, 0.31205011,
                                  0.32381485, 0.33999031, 0.35343822, 0.36836073, 0.38166926,
                                  0.39679554, 0.40953576, 0.41804517, 0.43979394, 0.44116064,
                                  0.45868164, 0.46856915, 0.49008209, 0.49448835, 0.51797729,
                                  0.51739829, 0.54037498, 0.55495042, 0.55546033, 0.5779394,
                                  0.59028687, 0.60248343, 0.61412209, 0.62864904, 0.64096585,
                                  0.65333774, 0.65992137, 0.68423057, 0.69196808, 0.70103968,
                                  0.71655086]])
    u2 = np.array([[0., 0.03098646, 0.05545746, 0.07545278, 0.09587002,
                    0.11218518, 0.1289216, 0.14907976, 0.16050172, 0.17975011,
                    0.19085945, 0.20455536, 0.21882758, 0.22764167, 0.24029007,
                    0.25447976, 0.26779484, 0.27510806, 0.29216032, 0.30202506,
                    0.30831239, 0.31984437, 0.34223229, 0.35177372, 0.35798304,
                    0.3709517, 0.38576783, 0.39326947, 0.40968629, 0.42754807,
                    0.431818, 0.44828232, 0.44874349, 0.47099549, 0.48051323,
                    0.49763808, 0.50824426, 0.51673666, 0.52778818, 0.5532053,
                    0.54917844],
                   [0., 0.07551708, 0.1170532, 0.15216193, 0.18166764,
                    0.20359138, 0.23135444, 0.24912772, 0.27113952, 0.29389022,
                    0.30847596, 0.32541801, 0.33943834, 0.35989591, 0.37180304,
                    0.3859453, 0.39804626, 0.42043131, 0.43533962, 0.44441893,
                    0.45749463, 0.47317309, 0.48438685, 0.49786174, 0.50686493,
                    0.5169629, 0.53642026, 0.54788681, 0.55946063, 0.57297367,
                    0.59183436, 0.60031666, 0.61064276, 0.62670694, 0.64145624,
                    0.64992796, 0.66694115, 0.67537887, 0.69711312, 0.69669367,
                    0.70691219],
                   [0., 0.02689769, 0.04637463, 0.06107751, 0.07982749,
                    0.09594169, 0.1120347, 0.12399533, 0.13631527, 0.15126529,
                    0.16050993, 0.17405488, 0.188608, 0.20339066, 0.21101378,
                    0.22069657, 0.23875572, 0.24928892, 0.25904662, 0.27115289,
                    0.28545744, 0.29950451, 0.30656425, 0.31675572, 0.3286219,
                    0.34925112, 0.35830421, 0.36912206, 0.38357135, 0.39354416,
                    0.40401191, 0.41465255, 0.42368689, 0.4505914, 0.45190246,
                    0.47308189, 0.47628597, 0.49218386, 0.50985051, 0.52424114,
                    0.53579416],
                   [0., 0.01708874, 0.02883109, 0.03667255, 0.04230664,
                    0.05451478, 0.05964277, 0.06556297, 0.06892387, 0.07205092,
                    0.07841962, 0.08109198, 0.0853806, 0.09239387, 0.09310937,
                    0.09813186, 0.10053086, 0.10639613, 0.10846062, 0.11106773,
                    0.11633562, 0.11677947, 0.11836627, 0.12378049, 0.12455875,
                    0.12804027, 0.13414478, 0.13555213, 0.13699382, 0.1417969,
                    0.14485852, 0.14680395, 0.14778798, 0.15108578, 0.1551278,
                    0.15586863, 0.15905876, 0.16184291, 0.16639193, 0.16714403,
                    0.16686271],
                   [0., 0.07672131, 0.12080113, 0.15045971, 0.17705163,
                    0.19692219, 0.21546218, 0.22979872, 0.24408165, 0.25970666,
                    0.26993065, 0.28438958, 0.29309198, 0.30756059, 0.31889584,
                    0.3279575, 0.33792407, 0.35044328, 0.36157932, 0.36997488,
                    0.38073964, 0.38907229, 0.40495923, 0.41054035, 0.42316576,
                    0.42900621, 0.44260092, 0.45901566, 0.4634223, 0.4738164,
                    0.47805477, 0.48548481, 0.50078621, 0.51390053, 0.52269021,
                    0.52380674, 0.54410166, 0.54971428, 0.56596145, 0.57210381,
                    0.58232933],
                   [0., 0.07471898, 0.11631598, 0.14296631, 0.16031253,
                    0.17638093, 0.18957802, 0.20321353, 0.21255584, 0.22103481,
                    0.23047212, 0.23954361, 0.24942612, 0.25670621, 0.2622554,
                    0.27213119, 0.27801828, 0.28188971, 0.29399333, 0.29948858,
                    0.30805492, 0.31951219, 0.32054038, 0.33139569, 0.33699455,
                    0.34272546, 0.3550778, 0.35899377, 0.36825548, 0.37299163,
                    0.38362941, 0.38840386, 0.39988028, 0.40539919, 0.40708572,
                    0.41943303, 0.42176454, 0.43467769, 0.44019444, 0.45153434,
                    0.46259523],
                   [0., 0.08240114, 0.12830295, 0.15852443, 0.1821383,
                    0.20188941, 0.21789249, 0.23301763, 0.24378633, 0.25730949,
                    0.27034973, 0.27702661, 0.28643502, 0.29958311, 0.30489884,
                    0.31298878, 0.3194941, 0.32706576, 0.33494348, 0.34318945,
                    0.35181924, 0.35823116, 0.36484217, 0.37144773, 0.37948287,
                    0.38332729, 0.39318779, 0.40124312, 0.40585105, 0.41014022,
                    0.4157716, 0.42543976, 0.42998526, 0.43793809, 0.44665563,
                    0.45205136, 0.45686589, 0.4609227, 0.46610309, 0.48129111,
                    0.48464345],
                   [0., 0.1033762, 0.15350442, 0.18626652, 0.20710819,
                    0.23075308, 0.24740932, 0.2624254, 0.28090551, 0.30083535,
                    0.31275032, 0.33039902, 0.34281, 0.35477928, 0.37116398,
                    0.38855409, 0.40102353, 0.41034802, 0.42613745, 0.43577597,
                    0.44626494, 0.46325795, 0.48054213, 0.48813205, 0.50378531,
                    0.52053394, 0.53163138, 0.5455243, 0.56083229, 0.57009311,
                    0.58534544, 0.59849949, 0.61672903, 0.62411636, 0.6327805,
                    0.64805585, 0.65686436, 0.67572655, 0.69443073, 0.71092771,
                    0.73139903]])
    u3 = np.array([[0., 0.03081863, 0.0527894, 0.07782224, 0.09537967,
                    0.11349139, 0.13168765, 0.14705853, 0.16220863, 0.17179254,
                    0.19021725, 0.20057298, 0.21408938, 0.22465646, 0.24186168,
                    0.25290945, 0.26331392, 0.27745694, 0.29045497, 0.29765751,
                    0.31266901, 0.32761463, 0.34004139, 0.34708337, 0.36000375,
                    0.37595728, 0.3883401, 0.39307808, 0.40767591, 0.41703234,
                    0.42934089, 0.43911006, 0.45923675, 0.47194087, 0.48390491,
                    0.49571493, 0.50653375, 0.51705657, 0.53829651, 0.5465961,
                    0.56116035], [0., 0.08233712, 0.12747965, 0.17129993, 0.19887041,
                                  0.22627468, 0.24999041, 0.27658098, 0.28910545, 0.31715906,
                                  0.33441932, 0.35661743, 0.36613704, 0.38149848, 0.39602802,
                                  0.41166863, 0.42847398, 0.43653212, 0.45835203, 0.46765623,
                                  0.48406193, 0.49251129, 0.50711631, 0.52052815, 0.53173583,
                                  0.54843912, 0.55819837, 0.57175478, 0.58628646, 0.59514144,
                                  0.60710949, 0.61658135, 0.64226823, 0.64275242, 0.65855208,
                                  0.67230725, 0.68014764, 0.68653887, 0.70041541, 0.7173231,
                                  0.72424264], [0., 0.02645928, 0.04533553, 0.06391671, 0.07997661,
                                                0.09524908, 0.10775454, 0.12443089, 0.13767579, 0.14919801,
                                                0.16063437, 0.17727591, 0.19107149, 0.19795911, 0.21543414,
                                                0.22402926, 0.23337132, 0.24784457, 0.2637198, 0.2704253,
                                                0.28340141, 0.29554628, 0.30505532, 0.31559309, 0.33283123,
                                                0.34709135, 0.35398513, 0.37192588, 0.38272009, 0.39190232,
                                                0.4092616, 0.42210159, 0.42844564, 0.43703027, 0.45647147,
                                                0.46965102, 0.47706894, 0.49146581, 0.51518061, 0.51729404,
                                                0.52750451],
                   [0., 0.01382872, 0.0261459, 0.03424761, 0.04204375,
                    0.04865203, 0.0525434, 0.05905673, 0.0632947, 0.06853196,
                    0.07348816, 0.07973456, 0.08129568, 0.08604582, 0.09291592,
                    0.09359603, 0.09989245, 0.10097941, 0.1088442, 0.11130437,
                    0.11468198, 0.11726117, 0.12245268, 0.12195467, 0.12633606,
                    0.12812196, 0.13314964, 0.13596483, 0.14060527, 0.14152195,
                    0.1414028, 0.14756329, 0.14678283, 0.15122965, 0.15370203,
                    0.15969286, 0.15783312, 0.16366145, 0.16389982, 0.16916611,
                    0.17042002],
                   [0., 0.07856059, 0.12286287, 0.15266845, 0.1750593,
                    0.19496588, 0.21388132, 0.22720148, 0.24348924, 0.25849352,
                    0.26823953, 0.28208186, 0.29662247, 0.30475848, 0.31744225,
                    0.33046281, 0.33605176, 0.34561967, 0.35876194, 0.36766547,
                    0.3812906, 0.3883938, 0.39899888, 0.40692039, 0.41816074,
                    0.42461135, 0.43754497, 0.44038159, 0.4562245, 0.46720164,
                    0.47013881, 0.48770168, 0.49946263, 0.5044829, 0.5083996,
                    0.52783481, 0.52769874, 0.55213556, 0.54970914, 0.56409398,
                    0.57334249],
                   [0., 0.08231723, 0.1252854, 0.14892317, 0.17054632,
                    0.18544656, 0.19769604, 0.21029603, 0.22282106, 0.2336895,
                    0.24077359, 0.25078171, 0.2579476, 0.2671546, 0.27183576,
                    0.28275129, 0.29199246, 0.29586755, 0.30350242, 0.31136387,
                    0.31567599, 0.32927513, 0.33030731, 0.33977915, 0.34625475,
                    0.35384833, 0.3622732, 0.36303362, 0.37580137, 0.38184011,
                    0.3865366, 0.39286376, 0.4015065, 0.41302165, 0.42128013,
                    0.42734722, 0.430626, 0.44084943, 0.44391602, 0.45804634,
                    0.45979836],
                   [0., 0.08910958, 0.12587999, 0.15074427, 0.16879331,
                    0.18569558, 0.19969491, 0.21404039, 0.22651253, 0.23291678,
                    0.24446909, 0.25221156, 0.26274786, 0.27239071, 0.28658094,
                    0.29197025, 0.30073359, 0.30919813, 0.31409007, 0.32005067,
                    0.32935433, 0.33854749, 0.34216383, 0.35097922, 0.35751183,
                    0.37054854, 0.37081861, 0.37965901, 0.38380931, 0.39080162,
                    0.40142117, 0.40701135, 0.41513175, 0.41802382, 0.42758642,
                    0.4363531, 0.43665116, 0.44994632, 0.45483913, 0.4600544,
                    0.46603391],
                   [0., 0.11805766, 0.16316877, 0.19595858, 0.21983699,
                    0.23899707, 0.26000733, 0.27832413, 0.29518585, 0.31487064,
                    0.32542658, 0.34299287, 0.35182493, 0.36783001, 0.38038822,
                    0.39535585, 0.40743, 0.42056828, 0.43471334, 0.44813492,
                    0.45883966, 0.47143409, 0.48850253, 0.49598404, 0.51248737,
                    0.529045, 0.5388413, 0.55375405, 0.5668353, 0.57850531,
                    0.5921315, 0.60825361, 0.6206921, 0.62899631, 0.64005373,
                    0.65394913, 0.67809021, 0.67795569, 0.70161011, 0.7019527,
                    0.7209558]])
    u4 = np.array([[0., 0.0329008, 0.05681413, 0.07320405, 0.09585632,
                    0.11026733, 0.12794564, 0.1415033, 0.1588689, 0.16732073,
                    0.18571756, 0.19289378, 0.20520341, 0.21867071, 0.23413516,
                    0.24511457, 0.25809714, 0.26620574, 0.27909579, 0.2910901,
                    0.30943515, 0.31960034, 0.32608195, 0.34641642, 0.35742107,
                    0.3625134, 0.37539401, 0.38251951, 0.40391444, 0.41061194,
                    0.42783109, 0.44164165, 0.45588619, 0.45697798, 0.4703475,
                    0.48319394, 0.49236782, 0.49956949, 0.52336387, 0.53622955,
                    0.5511688],
                   [0., 0.08076551, 0.12624508, 0.15756616, 0.18811749,
                    0.21259615, 0.23433519, 0.25772869, 0.27751808, 0.29837323,
                    0.31204992, 0.33165051, 0.3459293, 0.36162799, 0.37685366,
                    0.38806836, 0.40932215, 0.41924295, 0.43322648, 0.44979224,
                    0.45653393, 0.47807935, 0.49091664, 0.50571243, 0.51232404,
                    0.5313199, 0.53763218, 0.54979238, 0.56966317, 0.58006376,
                    0.59528592, 0.61324562, 0.62750872, 0.63095055, 0.64300852,
                    0.65688067, 0.67011357, 0.67475167, 0.69605437, 0.70676348,
                    0.71621947],
                   [0., 0.02572493, 0.04633596, 0.06213378, 0.07837258,
                    0.09102376, 0.10501791, 0.12122802, 0.13594022, 0.14526056,
                    0.15997184, 0.17241854, 0.18156726, 0.19676383, 0.20516738,
                    0.21964717, 0.23214709, 0.23853681, 0.25306497, 0.26899251,
                    0.27406361, 0.28833096, 0.30274033, 0.31404764, 0.32656506,
                    0.33207709, 0.35375365, 0.36514041, 0.37933229, 0.38923607,
                    0.39865752, 0.41506893, 0.42555193, 0.44078553, 0.45158345,
                    0.46182527, 0.47782638, 0.48839444, 0.5098406, 0.51464262,
                    0.52631549],
                   [0., 0.01705719, 0.02726291, 0.03806715, 0.0429495,
                    0.0506775, 0.05558712, 0.05862918, 0.06239197, 0.06669482,
                    0.07288592, 0.07451002, 0.08071623, 0.08144461, 0.08614294,
                    0.08954148, 0.09167323, 0.09024303, 0.09877318, 0.09750274,
                    0.09976558, 0.1095682, 0.10633132, 0.11205958, 0.10967206,
                    0.11846346, 0.11905989, 0.1241088, 0.12698743, 0.12700436,
                    0.13029252, 0.13023389, 0.13763632, 0.13425824, 0.14096799,
                    0.145361, 0.14471305, 0.14506705, 0.14685129, 0.15196524,
                    0.14961962],
                   [0., 0.07895384, 0.11422358, 0.14043638, 0.16222946,
                    0.1804383, 0.19706974, 0.21601087, 0.22906672, 0.24270489,
                    0.25592941, 0.26760058, 0.27973768, 0.28982821, 0.30225789,
                    0.31304007, 0.31994169, 0.33183069, 0.34672535, 0.3555045,
                    0.3686865, 0.37458265, 0.38434279, 0.39686141, 0.4021533,
                    0.41524194, 0.42649379, 0.43654619, 0.44479384, 0.46002004,
                    0.46512415, 0.47901508, 0.48387449, 0.49103623, 0.50025014,
                    0.51294049, 0.52592947, 0.53655326, 0.5446245, 0.55020822,
                    0.55623998],
                   [0., 0.07991151, 0.12720012, 0.14924084, 0.17089626,
                    0.18769198, 0.1971003, 0.20912042, 0.21832895, 0.22836286,
                    0.24023138, 0.24537945, 0.25398046, 0.2633968, 0.27375395,
                    0.27990551, 0.28764079, 0.29520356, 0.29953405, 0.30694862,
                    0.31350581, 0.31676465, 0.33266716, 0.33498058, 0.34442284,
                    0.34867304, 0.35832075, 0.36757402, 0.36819781, 0.38334247,
                    0.38548681, 0.39887668, 0.40280978, 0.40712101, 0.42238701,
                    0.42130341, 0.43100562, 0.43752775, 0.45294033, 0.44854182,
                    0.46593281],
                   [0., 0.07904918, 0.12340373, 0.15509668, 0.17779867,
                    0.19846265, 0.20888572, 0.22673303, 0.23797389, 0.24724668,
                    0.2580588, 0.26920367, 0.27558728, 0.28382711, 0.29422291,
                    0.30443162, 0.31174101, 0.31896156, 0.32370365, 0.33105211,
                    0.33904528, 0.34467237, 0.35105718, 0.35700094, 0.36725428,
                    0.3707328, 0.37395795, 0.38320777, 0.39053309, 0.39846676,
                    0.40162943, 0.40371759, 0.41774064, 0.41752659, 0.42135476,
                    0.42754302, 0.43811643, 0.44550828, 0.45340986, 0.46129888,
                    0.45974796],
                   [0., 0.12075714, 0.16489326, 0.19094228, 0.21543934,
                    0.24167953, 0.25481811, 0.2700129, 0.28754893, 0.30540806,
                    0.31439637, 0.32927589, 0.34473749, 0.36121412, 0.37432179,
                    0.38387276, 0.39413125, 0.41184222, 0.42117117, 0.44222711,
                    0.44712865, 0.46216598, 0.47471888, 0.49074205, 0.49983806,
                    0.51702131, 0.52090467, 0.54112512, 0.55795562, 0.57120835,
                    0.58807758, 0.59615115, 0.60424646, 0.62116589, 0.64037946,
                    0.64399186, 0.66507817, 0.67846889, 0.69863474, 0.70598133,
                    0.71343893]])
    u5 = np.array([[0., 0.03419526, 0.06106537, 0.08363693, 0.10023437,
                    0.12010886, 0.1372147, 0.14809132, 0.16644198, 0.17650712,
                    0.19525588, 0.203217, 0.21639757, 0.23067463, 0.23795989,
                    0.25551454, 0.26624964, 0.28650893, 0.29041481, 0.30689358,
                    0.3129451, 0.32606585, 0.34243403, 0.35358092, 0.358743,
                    0.37163603, 0.38809451, 0.4023986, 0.41353393, 0.42984679,
                    0.43689596, 0.44889551, 0.46399161, 0.4725532, 0.48803417,
                    0.50876203, 0.5173254, 0.52765801, 0.5388461, 0.54437467,
                    0.56799155],
                   [0., 0.08460609, 0.13151738, 0.16258146, 0.19057303,
                    0.2179877, 0.23953151, 0.26671567, 0.28155928, 0.30263759,
                    0.32418305, 0.33688382, 0.34874307, 0.36988218, 0.38543992,
                    0.3932005, 0.41100312, 0.42394904, 0.43746898, 0.44893087,
                    0.46790874, 0.47856713, 0.49655061, 0.51004686, 0.51340021,
                    0.53208669, 0.5449762, 0.54936708, 0.56667644, 0.57789963,
                    0.58545746, 0.60417324, 0.61356517, 0.62888066, 0.63707755,
                    0.64949969, 0.66736349, 0.67651526, 0.69319853, 0.71159326,
                    0.71982167],
                   [0., 0.02921259, 0.05145619, 0.06515595, 0.08181224,
                    0.09740054, 0.11069694, 0.12782116, 0.13716524, 0.1488061,
                    0.16047183, 0.17920788, 0.18651375, 0.20246075, 0.21426862,
                    0.22489649, 0.23606615, 0.24917321, 0.26085068, 0.27030882,
                    0.28507927, 0.29876992, 0.30784013, 0.32151349, 0.33405289,
                    0.33680712, 0.36047028, 0.36905788, 0.38452325, 0.39276469,
                    0.4092929, 0.41725528, 0.434302, 0.44460987, 0.45891777,
                    0.47385638, 0.48192982, 0.50045806, 0.51385026, 0.52966898,
                    0.54138884],
                   [0., 0.0180313, 0.02981642, 0.04028218, 0.04802976,
                    0.05478352, 0.06227586, 0.06784539, 0.07162594, 0.07576562,
                    0.08435649, 0.0861502, 0.08957085, 0.09328103, 0.10164419,
                    0.1052676, 0.11001538, 0.10788614, 0.11338114, 0.12121686,
                    0.12182372, 0.12768829, 0.12910016, 0.13591967, 0.13478137,
                    0.1389145, 0.14218716, 0.14192669, 0.14918019, 0.15408787,
                    0.15790428, 0.15751328, 0.15866265, 0.1641125, 0.16391763,
                    0.16620922, 0.17170878, 0.17364372, 0.17840221, 0.1800772,
                    0.18515136],
                   [0., 0.09820298, 0.13979267, 0.17236879, 0.19784291,
                    0.21769372, 0.23379349, 0.24811097, 0.26473189, 0.27958332,
                    0.29354421, 0.30346164, 0.31447766, 0.32359014, 0.33957839,
                    0.34653059, 0.36017463, 0.37135207, 0.37914871, 0.38941131,
                    0.39715482, 0.41540168, 0.42356258, 0.43054496, 0.43982175,
                    0.45364692, 0.45928162, 0.47543354, 0.47802231, 0.48573871,
                    0.5038805, 0.5173376, 0.52991526, 0.53149149, 0.54499781,
                    0.55851449, 0.56199648, 0.56713602, 0.58179126, 0.59004522,
                    0.60575868],
                   [0., 0.09108692, 0.13159347, 0.15629631, 0.17697816,
                    0.19248406, 0.20667378, 0.22033041, 0.22857403, 0.2356067,
                    0.2450487, 0.25734352, 0.2669013, 0.27524461, 0.28170424,
                    0.28503469, 0.29816797, 0.30537364, 0.31263341, 0.31995794,
                    0.32518439, 0.33254311, 0.34223871, 0.35290102, 0.35766044,
                    0.36317362, 0.37121948, 0.37687833, 0.38386578, 0.38763799,
                    0.40324415, 0.40889715, 0.41597955, 0.42106754, 0.43199889,
                    0.44068257, 0.44621341, 0.45003886, 0.45773625, 0.47635379,
                    0.47399941],
                   [0., 0.09656323, 0.13907831, 0.16643895, 0.18831079,
                    0.20416599, 0.22146826, 0.23420992, 0.24605322, 0.25781775,
                    0.27002966, 0.27712129, 0.2904694, 0.2961916, 0.30697965,
                    0.31120752, 0.3189238, 0.33065062, 0.33345647, 0.33850769,
                    0.3483043, 0.35305826, 0.36393986, 0.3689507, 0.37537252,
                    0.38460102, 0.38751136, 0.39535303, 0.40189018, 0.40623969,
                    0.41466916, 0.42075055, 0.43002419, 0.43348089, 0.43896764,
                    0.44243181, 0.45007139, 0.45319369, 0.47043444, 0.47000835,
                    0.47058773],
                   [0., 0.11371192, 0.16381933, 0.19980788, 0.22416634,
                    0.24743092, 0.26194733, 0.28439855, 0.30097705, 0.31643165,
                    0.32849502, 0.34388337, 0.35752436, 0.37122382, 0.37975955,
                    0.39899098, 0.40812569, 0.42161761, 0.43754811, 0.44768242,
                    0.46007175, 0.47146972, 0.48393068, 0.49757308, 0.50934906,
                    0.52662073, 0.54335588, 0.55344027, 0.5574864, 0.57567189,
                    0.59127342, 0.61003942, 0.61539338, 0.63108121, 0.64609013,
                    0.66202173, 0.67396187, 0.68433755, 0.69254069, 0.71184933,
                    0.7269053]])
    heurlist = [u1, u2, u3, u4, u5]
    heur_utillist = [np.array([0.11431596, 0.17342761, 0.27237211, 0.34772361, 0.42201331,
                               0.46421732, 0.52215145, 0.56258228, 0.61307315, 0.65136179,
                               0.70774646, 0.7362975, 0.79181096, 0.8173512, 0.85761582,
                               0.89614471, 0.93459148, 0.96095919, 1.00033909, 1.04123174,
                               1.0565142, 1.10377655, 1.13537857, 1.17279409, 1.1881757,
                               1.22163501, 1.26004209, 1.25844677, 1.32045081, 1.34090466,
                               1.34279745, 1.38799544, 1.39778234, 1.4122447, 1.44379363,
                               1.4545468, 1.48638373, 1.49276271, 1.52909561, 1.53955685]),
                     np.array([0.11824539, 0.17921349, 0.27227615, 0.35563589, 0.40868895,
                               0.45965295, 0.50776644, 0.55323044, 0.60542637, 0.64974086,
                               0.68383406, 0.73754184, 0.77267857, 0.80977957, 0.84993551,
                               0.87872208, 0.92224673, 0.94827536, 0.98459975, 1.00612438,
                               1.04574377, 1.07831565, 1.1074873, 1.14694138, 1.19219577,
                               1.19763791, 1.23639268, 1.2573178, 1.28074392, 1.29342311,
                               1.34334417, 1.35538405, 1.38308684, 1.40606437, 1.42666259,
                               1.46696952, 1.47990614, 1.48967596, 1.51552606, 1.54685017]),
                     np.array([0.11082292, 0.17298705, 0.25435897, 0.3419658, 0.40777705,
                               0.45528758, 0.51026334, 0.55736408, 0.60624828, 0.64403187,
                               0.69499754, 0.74124776, 0.7646112, 0.81675401, 0.85514783,
                               0.89452736, 0.92442669, 0.95527187, 1.00110561, 1.0181837,
                               1.07022645, 1.10149222, 1.12473377, 1.16534315, 1.1972839,
                               1.23593781, 1.25112424, 1.27189965, 1.3046614, 1.32271085,
                               1.34594176, 1.36502416, 1.40905441, 1.42277059, 1.43587757,
                               1.47146837, 1.50057071, 1.50579509, 1.53840853, 1.56139734]),
                     np.array([0.11593436, 0.18133894, 0.27289623, 0.36453934, 0.42639136,
                               0.47121222, 0.52601259, 0.56416475, 0.6124129, 0.65596568,
                               0.70297612, 0.74508809, 0.78056249, 0.81849921, 0.84793013,
                               0.89641819, 0.92243707, 0.95614298, 0.99470177, 1.01673434,
                               1.0432323, 1.09299947, 1.12591187, 1.15542853, 1.18767469,
                               1.22152379, 1.24914204, 1.27425745, 1.29394087, 1.33224555,
                               1.34566491, 1.37065939, 1.39051277, 1.41674257, 1.42917069,
                               1.45926123, 1.49682661, 1.51212307, 1.52563911, 1.54974496]),
                     np.array([0.10602101, 0.18191936, 0.26436622, 0.34609054, 0.4079323,
                               0.45954303, 0.51809874, 0.56184905, 0.60693437, 0.65704142,
                               0.70327859, 0.74942598, 0.77587466, 0.81581962, 0.86073208,
                               0.90353553, 0.92796626, 0.96117227, 0.99589492, 1.02585077,
                               1.05010257, 1.0853512, 1.13742249, 1.15491382, 1.19949646,
                               1.22070716, 1.25596724, 1.26850264, 1.29831861, 1.34410516,
                               1.34979522, 1.38181635, 1.39846767, 1.43422538, 1.45854528,
                               1.46974914, 1.48314679, 1.51447933, 1.52723034, 1.56089958])]
    rudi_utillist = [np.array([0.02782408, 0.04748855, 0.06840516, 0.0879303, 0.10657535,
                               0.12555678, 0.13974917, 0.16492282, 0.18010035, 0.19426166,
                               0.2153278, 0.23156652, 0.24563396, 0.26108007, 0.27959015,
                               0.30408262, 0.33713123, 0.34218969, 0.36414772, 0.40102144,
                               0.40370474, 0.4395967, 0.45107627, 0.47007509, 0.48017034,
                               0.51198321, 0.5283318, 0.54597593, 0.57088198, 0.58599377,
                               0.61389474, 0.62529131, 0.65915883, 0.68747812, 0.69685301,
                               0.71871954, 0.73572084, 0.74629047, 0.79783955, 0.79112253]),
                     np.array([0.04859418, 0.06086642, 0.08853113, 0.11049274, 0.13175328,
                               0.15241292, 0.16916202, 0.18803521, 0.20508796, 0.22351268,
                               0.24283847, 0.26074275, 0.2739954, 0.29094278, 0.30773907,
                               0.33223479, 0.37037767, 0.37209796, 0.38763903, 0.42613958,
                               0.4327728, 0.46529419, 0.471341, 0.49284701, 0.51287379,
                               0.52775766, 0.54722181, 0.56469771, 0.58150908, 0.60790747,
                               0.63083578, 0.66514928, 0.66939849, 0.69113055, 0.7003905,
                               0.72869131, 0.75964309, 0.77017693, 0.81072421, 0.81706695]),
                     np.array([0.03555813, 0.04437638, 0.06634329, 0.0834248, 0.10136096,
                               0.12448743, 0.14371782, 0.16463435, 0.1863686, 0.204936,
                               0.2250287, 0.24721582, 0.26055852, 0.28508597, 0.3052582,
                               0.32501774, 0.3643604, 0.36455279, 0.38954529, 0.42753366,
                               0.4251898, 0.47054249, 0.46903591, 0.49450484, 0.51422276,
                               0.53934689, 0.56051306, 0.57724114, 0.60352949, 0.62303856,
                               0.64193006, 0.66176272, 0.68444669, 0.70732812, 0.73515595,
                               0.73560723, 0.76790717, 0.78161387, 0.81333717, 0.81489961]),
                     np.array([0.01348256, 0.0153099, 0.03553821, 0.04718251, 0.06656089,
                               0.08151434, 0.10044076, 0.12058882, 0.13342243, 0.16056361,
                               0.1773875, 0.19423595, 0.20479916, 0.23138496, 0.25431674,
                               0.27062901, 0.30343841, 0.30128138, 0.33126151, 0.3691016,
                               0.3670993, 0.41737146, 0.41161035, 0.4324922, 0.45876234,
                               0.47349503, 0.48750493, 0.51246764, 0.5408795, 0.55339761,
                               0.57083161, 0.58973429, 0.62158921, 0.64219545, 0.67086635,
                               0.6905359, 0.7018246, 0.71182997, 0.7402795, 0.75600682]),
                     np.array([0.02551143, 0.03993898, 0.07005365, 0.09526721, 0.117477,
                               0.14293463, 0.16138723, 0.18074229, 0.20148731, 0.21889254,
                               0.24584289, 0.25945681, 0.27780987, 0.29191529, 0.31487885,
                               0.33695287, 0.37468603, 0.37310461, 0.3993615, 0.42922739,
                               0.43742476, 0.48360472, 0.48553688, 0.49965235, 0.52589264,
                               0.54465636, 0.56376548, 0.58338899, 0.61340136, 0.63284834,
                               0.64230094, 0.67870712, 0.70463026, 0.70434832, 0.7305568,
                               0.75971935, 0.76436461, 0.80001255, 0.8283422, 0.82860185]), ]

    # Size of dashes for unexplored nodes
    dshSz = 2
    # Size of figure layout
    figtup = (7, 5)
    titleSz, axSz, labelSz = 12, 10, 9
    xMax = 450

    avgHeurMat = np.average(np.array(heurlist), axis=0)

    # Plot of marginal utilities
    colors = cm.rainbow(np.linspace(0, 1., numTN))
    labels = [tnNames[ind] for ind in range(numTN)]

    x = range(testInt, testMax + 1, testInt)
    deltaArr = np.zeros((avgHeurMat.shape[0], avgHeurMat.shape[1] - 1))
    for rw in range(deltaArr.shape[0]):
        for col in range(deltaArr.shape[1]):
            deltaArr[rw, col] = avgHeurMat[rw, col + 1] - avgHeurMat[rw, col]
    yMax = np.max(deltaArr) * 1.1

    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        if tnind < 4:
            plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6)
        else:
            plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6, dashes=[1, dshSz])
    for tnind in range(numTN):
        plt.text(testInt * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., yMax])
    plt.xlim([0., xMax])
    plt.xlabel('Number of Tests', fontsize=axSz)
    plt.ylabel('Marginal Utility Gain', fontsize=axSz)
    plt.title('Marginal Utility with Increasing Tests\nExploratory Setting', fontsize=titleSz)
    plt.show()
    plt.close()

    # Allocation plot
    allocArr, objValArr = sampf.smooth_alloc_forward(avgHeurMat)

    # average distance from uniform allocation
    # np.linalg.norm(allocArr[:,-1]-np.ones((8))*4)

    colors = cm.rainbow(np.linspace(0, 1., numTN))
    labels = [tnNames[ind] for ind in range(numTN)]
    x = range(testInt, testMax + 1, testInt)
    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        if tnind < 4:
            plt.plot(x, allocArr[tnind] * testInt, linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6)
        else:
            plt.plot(x, allocArr[tnind] * testInt, linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6, dashes=[1, dshSz])
    # allocMax = allocArr.max() * testInt * 1.1
    allocMax = 185
    adj = 2.5
    for tnind in range(numTN):
        if tnind == 0:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 6:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        else:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt, labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., allocMax])
    plt.xlim([0., xMax])
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Test Node Allocation', fontsize=axSz)
    plt.title('Sampling Plan vs. Budget\nExploratory Setting', fontsize=titleSz)
    # plt.tight_layout()
    plt.show()
    plt.close()

    # Utility comparison plot
    colors = cm.rainbow(np.linspace(0, 0.8, 3))
    labels = ['Heuristic', 'Uniform', 'Rudimentary']
    x = range(testInt, testMax + 1, testInt)
    margUtilGroupList = [heur_utillist, unif_utillist, rudi_utillist]
    utilMax = -1
    for lst in margUtilGroupList:
        currMax = np.amax(np.array(lst))
        if currMax > utilMax:
            utilMax = currMax
    utilMax = utilMax * 1.1

    _ = plt.figure(figsize=figtup)
    for groupInd, margUtilGroup in enumerate(margUtilGroupList):
        groupArr = np.array(margUtilGroup)
        groupAvgArr = np.average(groupArr, axis=0)
        # Compile error bars
        stdevs = [np.std(groupArr[:, i]) for i in range(groupArr.shape[1])]
        group05Arr = [groupAvgArr[i] - (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        group95Arr = [groupAvgArr[i] + (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        plt.plot(x, groupAvgArr, color=colors[groupInd], linewidth=0.7, alpha=1., label=labels[groupInd] + ' 95% CI')
        plt.fill_between(x, groupAvgArr, group05Arr, color=colors[groupInd], alpha=0.2)
        plt.fill_between(x, groupAvgArr, group95Arr, color=colors[groupInd], alpha=0.2)
        # Line label
        plt.text(x[-1] * 1.01, groupAvgArr[-1], labels[groupInd].ljust(15), fontsize=labelSz - 1)
    plt.ylim(0, utilMax)
    # plt.xlim(0,x[-1]*1.12)
    plt.xlim([0., xMax])
    leg = plt.legend(loc='upper left', fontsize=labelSz)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(1.0)
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Plan Utility', fontsize=axSz)
    plt.title('Utility from Heuristic vs. Uniform and Rudimentary Allocations\nExploratory Setting', fontsize=titleSz)
    # Add text box showing budgetary savings
    compUtilAvg = np.average(np.array(heur_utillist), axis=0)
    x2, x3 = 119, 325
    plt.plot([100, x3], [compUtilAvg[9], compUtilAvg[9]], color='black', linestyle='--')
    iv = 0.03
    plt.plot([100, 100], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    plt.plot([x2, x2], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    plt.plot([x3, x3], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    plt.text(105, compUtilAvg[9] + iv / 2, str(x2 - 100), fontsize=labelSz)
    plt.text(205, compUtilAvg[9] + iv / 2, str(x3 - x2), fontsize=labelSz)
    # plt.tight_layout()
    plt.show()
    plt.close()

    '''
    Determining the budget saved for the sensitivity table
    currCompInd = 8
    compUtilAvg = np.average(np.array(compUtilList),axis=0) 
    evenUtilArr = np.array(evenUtilList)
    evenAvgArr = np.average(evenUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(evenAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    evenSampSaved = round((compUtilAvg[currCompInd] - evenAvgArr[kInd - 1]) / (evenAvgArr[kInd] - evenAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(evenSampSaved)
    rudiUtilArr = np.array(origUtilList)
    rudiAvgArr = np.average(rudiUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(rudiAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    rudiSampSaved = round((compUtilAvg[currCompInd] - rudiAvgArr[kInd - 1]) / (rudiAvgArr[kInd] - rudiAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(rudiSampSaved)
    currCompInd = 17
    compUtilAvg = np.average(np.array(compUtilList),axis=0) 
    evenUtilArr = np.array(evenUtilList)
    evenAvgArr = np.average(evenUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(evenAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    evenSampSaved = round((compUtilAvg[currCompInd] - evenAvgArr[kInd - 1]) / (evenAvgArr[kInd] - evenAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(evenSampSaved)
    rudiUtilArr = np.array(origUtilList)
    rudiAvgArr = np.average(rudiUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(rudiAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    rudiSampSaved = round((compUtilAvg[currCompInd] - rudiAvgArr[kInd - 1]) / (rudiAvgArr[kInd] - rudiAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(rudiSampSaved)
    '''

    return


def casestudyplots_familiar_market_OLD():
    """
    Cleaned up plots for use in case study in paper
    """
    testMax, testInt = 400, 10
    tnNames = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26']
    numTN = len(tnNames)

    u1 = np.array([[0., 0.00370115, 0.00754817, 0.01135109, 0.01479645,
                    0.01758527, 0.02030329, 0.02259548, 0.02448801, 0.02629825,
                    0.02829514, 0.02962516, 0.03138007, 0.0326162, 0.03449499,
                    0.03538848, 0.03667447, 0.03799814, 0.03929416, 0.04036802,
                    0.04140968, 0.04257587, 0.04357084, 0.04464618, 0.04520553,
                    0.04657966, 0.04729778, 0.04834846, 0.04956614, 0.05011356,
                    0.05103478, 0.05199911, 0.05252499, 0.05394043, 0.05429637,
                    0.05569998, 0.05589374, 0.05721676, 0.05778797, 0.05861981,
                    0.05930399],
                   [0., 0.00521452, 0.00870771, 0.01171401, 0.01407166,
                    0.01589169, 0.01781393, 0.01904592, 0.02079136, 0.022038,
                    0.02301334, 0.02453337, 0.02557969, 0.02674125, 0.0279136,
                    0.02873882, 0.02967468, 0.03094835, 0.03143568, 0.03294725,
                    0.03368311, 0.03481678, 0.03548372, 0.03636627, 0.03716428,
                    0.03766831, 0.03882564, 0.03983031, 0.040566, 0.0415074,
                    0.04250661, 0.04337499, 0.04389559, 0.04446009, 0.04546068,
                    0.04665717, 0.04673674, 0.04763698, 0.04802086, 0.04932291,
                    0.050506],
                   [0., 0.0014053, 0.00322013, 0.00493932, 0.00654305,
                    0.0081079, 0.00949472, 0.01117921, 0.01228255, 0.01346887,
                    0.0143818, 0.01554535, 0.01630068, 0.01762815, 0.01850313,
                    0.01960297, 0.02047381, 0.02125984, 0.02224282, 0.02323489,
                    0.02399671, 0.02464509, 0.0254197, 0.02622097, 0.02755008,
                    0.02793045, 0.02874102, 0.02951064, 0.03035057, 0.03111919,
                    0.03182885, 0.03281573, 0.03353631, 0.03474923, 0.03516451,
                    0.03652088, 0.03693728, 0.03731689, 0.03807466, 0.03870402,
                    0.03936204],
                   [0., 0.00314582, 0.00569568, 0.00782086, 0.00940753,
                    0.01122483, 0.01249399, 0.01421837, 0.01517978, 0.01632066,
                    0.01735236, 0.01849111, 0.01929125, 0.02006249, 0.02088718,
                    0.0214489, 0.02232413, 0.02315192, 0.02327692, 0.02415047,
                    0.02481726, 0.02545835, 0.02601869, 0.02649082, 0.02710559,
                    0.02768553, 0.02802426, 0.02818379, 0.02872339, 0.02921671,
                    0.02963969, 0.02978535, 0.030412, 0.03113037, 0.03120091,
                    0.03154167, 0.03200194, 0.0323137, 0.03283407, 0.0329886,
                    0.03343052]])
    u2 = np.array([[0., 0.00860469, 0.01294241, 0.0165686, 0.0199242,
                    0.02292024, 0.02518087, 0.02747581, 0.02927122, 0.03148234,
                    0.03297068, 0.0346668, 0.03615564, 0.03751565, 0.03890605,
                    0.03986519, 0.04145114, 0.04248229, 0.043568, 0.04491099,
                    0.045734, 0.04703067, 0.04792455, 0.04875156, 0.04998573,
                    0.05081761, 0.05196107, 0.0521089, 0.0536374, 0.05402785,
                    0.05479015, 0.05597345, 0.056553, 0.05792589, 0.05845984,
                    0.05909072, 0.06005931, 0.06051539, 0.0618456, 0.06215876,
                    0.06329104],
                   [0., 0.00739167, 0.01107353, 0.01405984, 0.01615787,
                    0.01814626, 0.01973297, 0.02142834, 0.02294227, 0.02413458,
                    0.02523861, 0.02644127, 0.02761599, 0.02859885, 0.02974212,
                    0.03062931, 0.03160926, 0.03265488, 0.0333362, 0.03459991,
                    0.0356767, 0.03630018, 0.03727267, 0.03832525, 0.03851656,
                    0.03998126, 0.04062207, 0.04128952, 0.04209633, 0.0432705,
                    0.04383543, 0.04448347, 0.04582006, 0.04651314, 0.04718448,
                    0.04764169, 0.0487322, 0.04950383, 0.05081679, 0.0515608,
                    0.05214483],
                   [0., 0.00293431, 0.00490201, 0.00695281, 0.00851317,
                    0.00994663, 0.01132517, 0.0126475, 0.0136747, 0.01479383,
                    0.01617769, 0.01698776, 0.01778916, 0.01908657, 0.02001666,
                    0.02112334, 0.02168893, 0.02289492, 0.0240148, 0.0244771,
                    0.02549256, 0.02624776, 0.02736876, 0.02808296, 0.02896959,
                    0.0296957, 0.03033917, 0.03126855, 0.03221468, 0.03314103,
                    0.0340838, 0.03459135, 0.03544298, 0.03583768, 0.03706063,
                    0.03758037, 0.03884796, 0.03942053, 0.04001358, 0.04135206,
                    0.04187006],
                   [0., 0.00502337, 0.00807084, 0.01040023, 0.01228201,
                    0.01397281, 0.01549529, 0.0167255, 0.01823126, 0.01915355,
                    0.02018165, 0.0211485, 0.02201256, 0.02266172, 0.0234618,
                    0.02423871, 0.0247597, 0.02563762, 0.02594973, 0.026655,
                    0.02738462, 0.02779939, 0.02815653, 0.02878524, 0.02928367,
                    0.02980185, 0.03002636, 0.03067315, 0.03097241, 0.03143577,
                    0.03183575, 0.03213842, 0.03280875, 0.03296834, 0.03351604,
                    0.03350797, 0.03383155, 0.03428221, 0.03472323, 0.03502255,
                    0.03526587]])
    u3 = np.array([[0., 0.00711556, 0.01150972, 0.01532889, 0.01869296,
                    0.02119778, 0.02366509, 0.02552842, 0.02792431, 0.02955705,
                    0.03131056, 0.03319253, 0.0346699, 0.03621119, 0.03728356,
                    0.03891454, 0.04009902, 0.04125446, 0.04224636, 0.04358109,
                    0.04510113, 0.04596333, 0.04663845, 0.04784529, 0.04876396,
                    0.04985436, 0.05067459, 0.05205941, 0.05280988, 0.05328098,
                    0.0542067, 0.05536842, 0.05620125, 0.0572857, 0.05791991,
                    0.0585348, 0.05970898, 0.06082106, 0.06131992, 0.06212156,
                    0.06305715],
                   [0., 0.00639301, 0.01021574, 0.01294498, 0.01520062,
                    0.01724888, 0.01902083, 0.02052484, 0.02186303, 0.02291359,
                    0.02454369, 0.02551462, 0.02666984, 0.02779756, 0.02883131,
                    0.02955402, 0.03099169, 0.03196599, 0.03302385, 0.03380456,
                    0.03477402, 0.03537011, 0.03626216, 0.03749014, 0.03833976,
                    0.03886624, 0.04030046, 0.0408202, 0.04169604, 0.04233374,
                    0.04344108, 0.04348666, 0.04471365, 0.04587692, 0.04690817,
                    0.04704024, 0.04857898, 0.04895659, 0.04954359, 0.05076005,
                    0.05165409],
                   [0., 0.00277466, 0.0048798, 0.00676431, 0.00873648,
                    0.0101361, 0.01155595, 0.01286064, 0.01397221, 0.01520344,
                    0.01620918, 0.0170672, 0.01814683, 0.01917101, 0.0201052,
                    0.02108787, 0.0219236, 0.0228308, 0.0234907, 0.02428553,
                    0.02507818, 0.02620773, 0.02702154, 0.02792971, 0.02865268,
                    0.02926112, 0.0305603, 0.03135117, 0.03181649, 0.03276924,
                    0.03383046, 0.03447665, 0.03529807, 0.03605051, 0.0367038,
                    0.03792761, 0.03845844, 0.03936174, 0.04008653, 0.04093969,
                    0.04213261],
                   [0., 0.00399593, 0.00695755, 0.00930951, 0.01170449,
                    0.01345595, 0.01503473, 0.01623996, 0.01749645, 0.0186022,
                    0.01969436, 0.02052746, 0.02159807, 0.02240492, 0.02309774,
                    0.02400491, 0.02433944, 0.02533524, 0.02581863, 0.02657205,
                    0.02728838, 0.02769013, 0.02804411, 0.02863255, 0.02947358,
                    0.02945576, 0.02985546, 0.03031563, 0.0309346, 0.03162595,
                    0.03220458, 0.03202554, 0.03264078, 0.03307859, 0.03339639,
                    0.03413365, 0.03400162, 0.03449237, 0.03480022, 0.03517938,
                    0.03544547]])
    u4 = np.array([[0., 0.00623742, 0.0107683, 0.01419663, 0.0168955,
                    0.0191606, 0.0218966, 0.02363346, 0.02587655, 0.02718637,
                    0.02902425, 0.03058422, 0.03195352, 0.03358174, 0.03505111,
                    0.03647073, 0.03726103, 0.03868613, 0.03988063, 0.04131397,
                    0.04186797, 0.04308399, 0.04456227, 0.0447169, 0.04570323,
                    0.04717786, 0.04774681, 0.04904583, 0.04934617, 0.05030685,
                    0.05182604, 0.05231423, 0.052729, 0.05408944, 0.05442993,
                    0.05608707, 0.05679886, 0.0574922, 0.05825421, 0.05877748,
                    0.05933952],
                   [0., 0.00614568, 0.00960895, 0.01250915, 0.01490775,
                    0.01690714, 0.01844857, 0.02001247, 0.02135596, 0.02247329,
                    0.02388596, 0.02485091, 0.02604058, 0.02706147, 0.02796199,
                    0.02881599, 0.02974943, 0.03075337, 0.03148059, 0.03268307,
                    0.03364999, 0.03416761, 0.03498369, 0.03617498, 0.03693221,
                    0.03767087, 0.03816067, 0.03972862, 0.03979821, 0.04095362,
                    0.0416963, 0.04209237, 0.0434257, 0.04419295, 0.04468817,
                    0.04566068, 0.04629111, 0.04676275, 0.04813874, 0.04837465,
                    0.04937065],
                   [0., 0.00313393, 0.00530882, 0.00691432, 0.00860079,
                    0.00987225, 0.01120622, 0.01239862, 0.01349885, 0.01464663,
                    0.01550153, 0.0166227, 0.0176624, 0.01847827, 0.01922681,
                    0.02028269, 0.02108873, 0.02232152, 0.0229235, 0.02359952,
                    0.02454151, 0.02497414, 0.02625075, 0.02716752, 0.02784766,
                    0.02849041, 0.0292009, 0.0298024, 0.03090284, 0.03163269,
                    0.03247929, 0.03280397, 0.03417415, 0.03510546, 0.03569961,
                    0.03666486, 0.03687342, 0.03743126, 0.03823399, 0.03912125,
                    0.03968534],
                   [0., 0.00503518, 0.00776116, 0.00982997, 0.01151161,
                    0.01276737, 0.01459745, 0.01549585, 0.01677736, 0.0178023,
                    0.01858633, 0.0200048, 0.02058045, 0.02134676, 0.02195429,
                    0.02275256, 0.02366321, 0.02402966, 0.02458911, 0.02526218,
                    0.02539541, 0.02625045, 0.02656343, 0.02723677, 0.02774086,
                    0.02798527, 0.02865532, 0.02892523, 0.02946974, 0.02968859,
                    0.03012616, 0.03029527, 0.03128969, 0.03151363, 0.03147276,
                    0.03185545, 0.03244756, 0.03271437, 0.03290864, 0.03329439,
                    0.03392747]])
    u5 = np.array([[0., 0.00296879, 0.00581073, 0.00781251, 0.01022734,
                    0.01272988, 0.01466399, 0.01665458, 0.01859456, 0.02004764,
                    0.02169879, 0.02319546, 0.02459926, 0.0254176, 0.02749068,
                    0.02837275, 0.02942549, 0.03044908, 0.03211243, 0.03250083,
                    0.03368589, 0.03471309, 0.03541739, 0.03674223, 0.03734385,
                    0.03861745, 0.03941934, 0.04066658, 0.04130804, 0.04238657,
                    0.04312362, 0.04385675, 0.04477351, 0.04526967, 0.04593654,
                    0.04687454, 0.04749814, 0.04825281, 0.04940673, 0.04981676,
                    0.05041162],
                   [0., 0.00298406, 0.00596691, 0.00831903, 0.01004583,
                    0.01165395, 0.01285181, 0.01428776, 0.01544564, 0.01620029,
                    0.01749797, 0.01839554, 0.01946618, 0.02053511, 0.0208972,
                    0.02196977, 0.02281524, 0.02339476, 0.02407525, 0.0249937,
                    0.02601466, 0.02679039, 0.02743121, 0.0280771, 0.02943302,
                    0.02951979, 0.03041261, 0.03083825, 0.03183935, 0.03278749,
                    0.03371893, 0.03397548, 0.03467423, 0.03546449, 0.03653094,
                    0.03706408, 0.0374169, 0.03809877, 0.03890872, 0.04013037,
                    0.04041997],
                   [0., 0.00029799, 0.00138495, 0.00246707, 0.00358361,
                    0.00446076, 0.00563562, 0.00671886, 0.0071145, 0.00842626,
                    0.00927072, 0.01008385, 0.01089839, 0.01197313, 0.0127413,
                    0.01351113, 0.01385828, 0.01452063, 0.01537415, 0.01631401,
                    0.01702082, 0.01774181, 0.01835399, 0.0194173, 0.0199734,
                    0.02086879, 0.02140004, 0.0220287, 0.02284598, 0.02365675,
                    0.02430936, 0.02497317, 0.02555566, 0.02635179, 0.02743173,
                    0.02795019, 0.02832947, 0.02950637, 0.03013035, 0.03089876,
                    0.03159442],
                   [0., 0.00052088, 0.00135599, 0.00244395, 0.00387364,
                    0.00483859, 0.00594226, 0.00722953, 0.00820936, 0.0089994,
                    0.00974168, 0.01075634, 0.01141105, 0.01238851, 0.01299728,
                    0.01347053, 0.0144116, 0.0148174, 0.0154108, 0.01619118,
                    0.01693934, 0.01718124, 0.01757721, 0.01822484, 0.01854279,
                    0.01883865, 0.0194574, 0.02005639, 0.02038545, 0.02065996,
                    0.02113112, 0.02145101, 0.02199908, 0.02208797, 0.02249012,
                    0.02286966, 0.02320055, 0.02358441, 0.02377961, 0.02391892,
                    0.02457124]])
    heurlist = [u1, u2, u3, u4, u5]

    unif_utillist = [np.array([0.00444674, 0.00849487, 0.01145364, 0.01483015, 0.0182642,
                               0.02045837, 0.02341296, 0.02587959, 0.0285271, 0.03066484,
                               0.03272858, 0.03499641, 0.03694944, 0.0385483, 0.04079861,
                               0.04229113, 0.04419591, 0.04588342, 0.04737929, 0.0492428,
                               0.05107569, 0.05190923, 0.0537082, 0.05506989, 0.05671258,
                               0.0579137, 0.05913619, 0.06054511, 0.06259035, 0.06388868,
                               0.06497329, 0.06612, 0.06761998, 0.06836801, 0.06977942,
                               0.07116515, 0.07212518, 0.07320407, 0.07407188, 0.07549588]),
                     np.array([0.00025635, 0.0010916, 0.0026349, 0.00472597, 0.00737031,
                               0.00938474, 0.01105182, 0.01351506, 0.01617596, 0.01809892,
                               0.01920147, 0.02193281, 0.02381952, 0.02570726, 0.02728908,
                               0.0295041, 0.03112049, 0.03267621, 0.03406354, 0.03587964,
                               0.0382313, 0.03933848, 0.04051184, 0.04254011, 0.04393701,
                               0.04585793, 0.04625594, 0.04736641, 0.04960632, 0.04995877,
                               0.05180538, 0.05279984, 0.05479813, 0.05624012, 0.05659225,
                               0.05796138, 0.05881081, 0.06032094, 0.06063839, 0.06237299]),
                     np.array([0.00703767, 0.01123162, 0.01471185, 0.01849512, 0.02210158,
                               0.02470907, 0.02712273, 0.02986327, 0.03245172, 0.03434599,
                               0.0364074, 0.03877422, 0.04071795, 0.04245288, 0.04385183,
                               0.04656132, 0.04763907, 0.04948099, 0.05129809, 0.05240616,
                               0.05453225, 0.05597957, 0.05746177, 0.05885112, 0.05997174,
                               0.06175392, 0.06399858, 0.06495419, 0.06576366, 0.06759076,
                               0.06890413, 0.06929593, 0.07136165, 0.072091, 0.0731512,
                               0.0741711, 0.0755706, 0.0767682, 0.07819103, 0.07903985]),
                     np.array([0.00283648, 0.00556726, 0.00824927, 0.01110076, 0.01364964,
                               0.01630112, 0.01817734, 0.02030188, 0.02316294, 0.02471869,
                               0.02654946, 0.0285962, 0.03089963, 0.03247331, 0.03402275,
                               0.0359974, 0.03799343, 0.03914502, 0.04065613, 0.04248823,
                               0.04426663, 0.04560806, 0.04711877, 0.04831721, 0.04976997,
                               0.05140065, 0.05284068, 0.05418655, 0.05570785, 0.05654378,
                               0.05797034, 0.05940224, 0.06005792, 0.06180126, 0.06330745,
                               0.06390966, 0.06576, 0.06609435, 0.06735738, 0.06847434]),
                     np.array([0.00732392, 0.01182978, 0.0152388, 0.01868701, 0.02189468,
                               0.02459627, 0.02727848, 0.02967733, 0.03183084, 0.03381241,
                               0.03614884, 0.03801314, 0.04034143, 0.0419046, 0.04333761,
                               0.04508281, 0.04702327, 0.04893576, 0.05048394, 0.05247957,
                               0.05422883, 0.05504704, 0.05636547, 0.05743409, 0.05977996,
                               0.0607719, 0.06216097, 0.06359161, 0.06508585, 0.0660644,
                               0.06717837, 0.06923899, 0.06983411, 0.07116665, 0.0717448,
                               0.07326356, 0.07428002, 0.07554445, 0.07663304, 0.07735115]),
                     np.array([0.0051047, 0.00909776, 0.01245413, 0.01615499, 0.01995187,
                               0.02198991, 0.02478221, 0.02731725, 0.03001515, 0.03213346,
                               0.03425097, 0.03601164, 0.03853605, 0.04037408, 0.04219365,
                               0.04393262, 0.04628136, 0.04788809, 0.04941699, 0.05132261,
                               0.05261582, 0.0542335, 0.05591487, 0.05749708, 0.05933186,
                               0.0604367, 0.06159741, 0.0630387, 0.06405631, 0.06590958,
                               0.06715936, 0.06880624, 0.06961094, 0.07152515, 0.07198018,
                               0.0736776, 0.07512589, 0.07535801, 0.07661507, 0.07670517]),
                     np.array([0.00304834, 0.00534396, 0.00756298, 0.01035888, 0.01289413,
                               0.014816, 0.01688487, 0.01964123, 0.02148032, 0.0233961,
                               0.02553934, 0.02696869, 0.02949682, 0.03082611, 0.03274153,
                               0.03406817, 0.03555929, 0.03741182, 0.03885598, 0.04065256,
                               0.04218061, 0.04375435, 0.04509817, 0.04642677, 0.04791937,
                               0.0498107, 0.04999173, 0.05217394, 0.0533035, 0.05500204,
                               0.05533083, 0.05688471, 0.05829265, 0.05901847, 0.06027591,
                               0.06190367, 0.06238302, 0.06389444, 0.06508395, 0.06494084]),
                     np.array([0.00253256, 0.00392835, 0.00556523, 0.00751142, 0.00957761,
                               0.01144588, 0.01344019, 0.01570824, 0.01771092, 0.01970091,
                               0.02107289, 0.02328334, 0.02511366, 0.02714577, 0.02828164,
                               0.03012061, 0.03212793, 0.03310231, 0.03492135, 0.03693991,
                               0.0381809, 0.03927757, 0.04140825, 0.04263294, 0.04426681,
                               0.04571483, 0.04653211, 0.04820108, 0.0499501, 0.05125159,
                               0.05184135, 0.05315146, 0.05408872, 0.05609921, 0.05663821,
                               0.05832352, 0.05898698, 0.06090304, 0.06125949, 0.06226988]),
                     np.array([0.00539675, 0.00947555, 0.01305815, 0.01608278, 0.01985614,
                               0.02233945, 0.02444981, 0.02694209, 0.02963127, 0.03195145,
                               0.03403879, 0.0360177, 0.03772628, 0.03985437, 0.0420644,
                               0.04341397, 0.0458051, 0.04707867, 0.04849754, 0.0496959,
                               0.05173489, 0.05393075, 0.05486597, 0.05674172, 0.05835943,
                               0.05887492, 0.06048333, 0.0618013, 0.06398069, 0.06434541,
                               0.06594791, 0.06801227, 0.06891677, 0.07012194, 0.07033183,
                               0.0717419, 0.07355959, 0.07476762, 0.07507512, 0.07632044]),
                     np.array([0.00402346, 0.00749703, 0.01051984, 0.01390495, 0.01736331,
                               0.01959497, 0.02235938, 0.02510998, 0.02775047, 0.02966821,
                               0.03136968, 0.03421596, 0.0363641, 0.03761386, 0.03997168,
                               0.04181672, 0.04352603, 0.04545391, 0.04682332, 0.04809054,
                               0.04993904, 0.05210706, 0.05266389, 0.05482227, 0.05620326,
                               0.05817602, 0.05905501, 0.05977953, 0.06230666, 0.06306103,
                               0.06329548, 0.0647916, 0.06694046, 0.06764727, 0.06912574,
                               0.07008886, 0.07149945, 0.0719053, 0.07331014, 0.07444215]),
                     np.array([0.00138062, 0.00408097, 0.00686082, 0.00982036, 0.01248437,
                               0.01458715, 0.01683015, 0.01944936, 0.02189357, 0.02357684,
                               0.0256377, 0.02750402, 0.02941194, 0.03095238, 0.0328006,
                               0.03501333, 0.03656592, 0.03810282, 0.03956621, 0.04158878,
                               0.0428052, 0.04426131, 0.04547268, 0.04693587, 0.04880038,
                               0.04958692, 0.05114909, 0.05282402, 0.05399142, 0.05417034,
                               0.05590181, 0.05766249, 0.05900385, 0.05975172, 0.06087636,
                               0.06260299, 0.06433214, 0.06427961, 0.06530009, 0.06591696]),
                     np.array([0.00711019, 0.01085605, 0.01435248, 0.01745601, 0.02060696,
                               0.02342777, 0.02585723, 0.02818387, 0.0304994, 0.0329436,
                               0.03438214, 0.0370773, 0.03871701, 0.04070438, 0.0418963,
                               0.04403498, 0.04594828, 0.04773598, 0.04901016, 0.05106045,
                               0.05279095, 0.05410377, 0.0552095, 0.05667757, 0.05822969,
                               0.06004265, 0.06088337, 0.0621031, 0.06383303, 0.06497417,
                               0.0655975, 0.06770385, 0.06867271, 0.06986109, 0.07100161,
                               0.07154874, 0.07397299, 0.07431816, 0.0759655, 0.07578661]),
                     ]
    heur_utillist = [np.array([0.0046462, 0.01035949, 0.01411212, 0.01714631, 0.02095333,
                               0.02396591, 0.02722726, 0.02941946, 0.03239284, 0.03416396,
                               0.03665252, 0.03832415, 0.04056339, 0.04215187, 0.04380399,
                               0.04549616, 0.04766778, 0.04911511, 0.05029734, 0.05266795,
                               0.0535055, 0.05532648, 0.05706223, 0.05852287, 0.05940419,
                               0.06061065, 0.06216974, 0.06338533, 0.06542705, 0.06641016,
                               0.0677027, 0.06884568, 0.06989114, 0.07142511, 0.07236781,
                               0.07310875, 0.07317939, 0.0750093, 0.07671098, 0.07695983]),
                     np.array([0.00020349, 0.00207989, 0.00440029, 0.00639653, 0.00903138,
                               0.01206191, 0.01500055, 0.0172858, 0.01999293, 0.02196349,
                               0.02408376, 0.02581674, 0.0274018, 0.02969528, 0.03190946,
                               0.03315755, 0.03413799, 0.03609891, 0.03730621, 0.0389168,
                               0.04121093, 0.04214762, 0.04361272, 0.04545618, 0.04679511,
                               0.04855134, 0.04929698, 0.05072829, 0.05195741, 0.05357404,
                               0.05473883, 0.05591608, 0.05705343, 0.05815234, 0.05870053,
                               0.06018681, 0.06098253, 0.06176503, 0.06388697, 0.06449945]),
                     np.array([0.00725582, 0.01383744, 0.01817013, 0.02139215, 0.02486906,
                               0.02812926, 0.03134038, 0.03377465, 0.0363445, 0.0381698,
                               0.04022212, 0.04248223, 0.04386724, 0.04623705, 0.04723456,
                               0.04939564, 0.05191, 0.05268847, 0.05391454, 0.05556149,
                               0.05811214, 0.05810327, 0.06043693, 0.06261572, 0.06318541,
                               0.06465417, 0.06544086, 0.06705201, 0.06832875, 0.07023569,
                               0.0712074, 0.07248264, 0.07308533, 0.07517388, 0.07471973,
                               0.07704273, 0.07737933, 0.07864575, 0.07950125, 0.08027674]),
                     np.array([0.00339671, 0.00708141, 0.01073328, 0.01367482, 0.01629427,
                               0.01908748, 0.0219989, 0.0242982, 0.02704123, 0.02890102,
                               0.03097881, 0.03302688, 0.03368925, 0.03641985, 0.03764801,
                               0.03969069, 0.04147443, 0.04228124, 0.04390448, 0.04533844,
                               0.04727205, 0.04863131, 0.05046999, 0.05135328, 0.05300424,
                               0.05440796, 0.05533924, 0.05692319, 0.0582036, 0.05971727,
                               0.06075003, 0.06153945, 0.06354397, 0.06371107, 0.0652679,
                               0.06616482, 0.06690135, 0.068701, 0.06954478, 0.0706907]),
                     np.array([0.00764816, 0.01355206, 0.01836639, 0.02155743, 0.02432815,
                               0.02774378, 0.03117883, 0.03344898, 0.0357721, 0.03767681,
                               0.04025065, 0.04206496, 0.04352038, 0.04553335, 0.04717358,
                               0.04874179, 0.05050465, 0.0515029, 0.05358544, 0.05487749,
                               0.05643779, 0.05798099, 0.05984695, 0.06097773, 0.06200518,
                               0.06313272, 0.06542077, 0.06651899, 0.06720031, 0.06850545,
                               0.06991254, 0.07132995, 0.07343545, 0.07321637, 0.0745857,
                               0.07516392, 0.07650051, 0.0776102, 0.07871795, 0.07966502]),
                     np.array([0.00647161, 0.01149149, 0.01640462, 0.0187805, 0.0228018,
                               0.02630502, 0.02897579, 0.03197415, 0.0345634, 0.03653043,
                               0.03853351, 0.04086522, 0.04223477, 0.04439702, 0.04654666,
                               0.04771872, 0.04984945, 0.0514608, 0.0529949, 0.05462646,
                               0.05582061, 0.05801399, 0.05899962, 0.06077242, 0.06184289,
                               0.0636995, 0.06444484, 0.06628207, 0.06725785, 0.06901733,
                               0.07051056, 0.07135393, 0.0723466, 0.07388339, 0.07486021,
                               0.07537993, 0.07677777, 0.07784303, 0.0786345, 0.07912031]),
                     np.array([0.00415652, 0.00726548, 0.01059736, 0.0125016, 0.01488439,
                               0.01788249, 0.02064037, 0.02266717, 0.02501105, 0.02702041,
                               0.02913442, 0.03080734, 0.03215389, 0.03458209, 0.03612018,
                               0.03751438, 0.03908485, 0.04063601, 0.04191199, 0.04393703,
                               0.045758, 0.04637577, 0.04776906, 0.04941938, 0.05044835,
                               0.05184896, 0.05307754, 0.05466853, 0.055308, 0.05734965,
                               0.05804387, 0.05960022, 0.06027925, 0.06151143, 0.06173254,
                               0.06348775, 0.06377267, 0.06566634, 0.06634666, 0.06740955]),
                     np.array([0.00055796, 0.0051622, 0.00720947, 0.00896756, 0.01136099,
                               0.01420935, 0.01667858, 0.01918914, 0.02138392, 0.02278328,
                               0.02560025, 0.02698725, 0.02839227, 0.03020708, 0.03211961,
                               0.03410682, 0.03563588, 0.03664023, 0.03832939, 0.04004059,
                               0.04107076, 0.042656, 0.04393685, 0.04588421, 0.04655946,
                               0.04866742, 0.04945316, 0.05100608, 0.052239, 0.05330604,
                               0.05495698, 0.05657656, 0.05801949, 0.0584588, 0.05944025,
                               0.05983759, 0.06078678, 0.06208536, 0.06340837, 0.06430935]),
                     np.array([0.00552772, 0.01131269, 0.0154464, 0.01846612, 0.02156943,
                               0.02513478, 0.02801869, 0.03054322, 0.03337384, 0.03565864,
                               0.03775806, 0.03993399, 0.04142035, 0.04359693, 0.04542059,
                               0.04719663, 0.04870726, 0.050058, 0.05168551, 0.05334383,
                               0.05483241, 0.05642239, 0.05798872, 0.05999344, 0.06046496,
                               0.06228919, 0.06323393, 0.06465847, 0.06566684, 0.06772959,
                               0.06899459, 0.07084851, 0.07090663, 0.07205188, 0.07318417,
                               0.07430809, 0.07514461, 0.07682052, 0.07755364, 0.07921898]),
                     np.array([0.0064704, 0.01059929, 0.01484298, 0.01726363, 0.02062342,
                               0.02404291, 0.027135, 0.02963889, 0.0321668, 0.03377895,
                               0.03638693, 0.03838921, 0.03975317, 0.04156821, 0.04376421,
                               0.04573316, 0.04731535, 0.04824959, 0.04988863, 0.05184101,
                               0.05357701, 0.0551889, 0.05607437, 0.05840382, 0.05841144,
                               0.06050722, 0.0613347, 0.06302827, 0.06441185, 0.06596663,
                               0.06752497, 0.06842396, 0.06931113, 0.07061332, 0.07208368,
                               0.07233877, 0.07290209, 0.07410425, 0.07590374, 0.07642556]),
                     np.array([0.00195351, 0.005996, 0.00950744, 0.01197115, 0.01464623,
                               0.01814034, 0.02077385, 0.02271045, 0.02484791, 0.02694271,
                               0.02928275, 0.03114973, 0.03226727, 0.03458648, 0.0364148,
                               0.03816507, 0.03961385, 0.04115199, 0.04214948, 0.04431452,
                               0.04566881, 0.0473726, 0.0486056, 0.04951938, 0.05137307,
                               0.0517825, 0.05370327, 0.05522388, 0.0561777, 0.05771888,
                               0.05886016, 0.06049343, 0.06159252, 0.06256414, 0.0636969,
                               0.0646857, 0.06545432, 0.06627704, 0.06793369, 0.06888449]),
                     np.array([0.00675569, 0.01280486, 0.01674118, 0.01995713, 0.02335414,
                               0.02619607, 0.02967097, 0.03203834, 0.03452025, 0.03625238,
                               0.03820573, 0.04086554, 0.04201165, 0.0439072, 0.04588404,
                               0.04730589, 0.04951778, 0.0509673, 0.05213855, 0.05391669,
                               0.0551118, 0.05644544, 0.05787105, 0.0592641, 0.06087489,
                               0.06253584, 0.06339515, 0.06524073, 0.06597361, 0.06699455,
                               0.06844243, 0.06997564, 0.07116806, 0.07203081, 0.07282702,
                               0.07390442, 0.07487548, 0.07611546, 0.07697084, 0.07821039]),
                     ]
    rudi_utillist = [np.array([0.00408365, 0.00659668, 0.00971391, 0.01268393, 0.01501705,
                               0.01774011, 0.01976965, 0.02259873, 0.02469648, 0.02671448,
                               0.02863334, 0.03074868, 0.03234869, 0.03406916, 0.0356964,
                               0.03728166, 0.03950018, 0.04107576, 0.04279211, 0.04446256,
                               0.04587693, 0.04774602, 0.04888318, 0.0501046, 0.05135876,
                               0.05281397, 0.05407643, 0.0557159, 0.05696343, 0.05856421,
                               0.05962955, 0.06088553, 0.06257154, 0.06331485, 0.06456221,
                               0.06562104, 0.06635407, 0.06799553, 0.06960971, 0.06982799]),
                     np.array([5.56895702e-05, 5.13147758e-04, 1.85191311e-03, 3.02232280e-03,
                               4.84449534e-03, 6.66102465e-03, 8.65909275e-03, 1.03893910e-02,
                               1.22334467e-02, 1.47401231e-02, 1.63642911e-02, 1.81851217e-02,
                               1.99360475e-02, 2.16337664e-02, 2.29616417e-02, 2.47217598e-02,
                               2.68716515e-02, 2.75226742e-02, 3.00391198e-02, 3.15081930e-02,
                               3.26962166e-02, 3.44466912e-02, 3.56752715e-02, 3.73298014e-02,
                               3.91979842e-02, 3.99450217e-02, 4.10929280e-02, 4.29711582e-02,
                               4.41416575e-02, 4.50060550e-02, 4.70866593e-02, 4.81924493e-02,
                               4.97055463e-02, 5.08851120e-02, 5.13173699e-02, 5.28013004e-02,
                               5.36984834e-02, 5.52692587e-02, 5.64604967e-02, 5.69393934e-02]),
                     np.array([0.00624513, 0.00924312, 0.01314998, 0.01594177, 0.01847883,
                               0.02109886, 0.02363969, 0.02609058, 0.02806433, 0.03022749,
                               0.03278048, 0.03396266, 0.0355753, 0.03787875, 0.03974472,
                               0.04098801, 0.04282443, 0.04484681, 0.0461558, 0.04816634,
                               0.0486513, 0.05095573, 0.0522068, 0.05389503, 0.05479844,
                               0.05611818, 0.0583461, 0.05933398, 0.06044396, 0.06171221,
                               0.06287189, 0.06463325, 0.06614747, 0.06701871, 0.06824458,
                               0.06910167, 0.07111794, 0.07143086, 0.07334579, 0.07368217]),
                     np.array([0.00185496, 0.00420385, 0.00679184, 0.00891011, 0.01105383,
                               0.01314866, 0.01496854, 0.01717227, 0.0189893, 0.02128364,
                               0.02313533, 0.02454412, 0.02619626, 0.027497, 0.02977068,
                               0.0312323, 0.0329067, 0.03443605, 0.03661142, 0.03774861,
                               0.03900009, 0.04056855, 0.04216052, 0.04369585, 0.04502832,
                               0.04571217, 0.04747114, 0.04889706, 0.0504788, 0.05139976,
                               0.05310803, 0.0540409, 0.05532461, 0.05558057, 0.05744643,
                               0.05846275, 0.05989369, 0.06085441, 0.06277245, 0.06292839]),
                     np.array([0.00575105, 0.00943192, 0.01291857, 0.01588746, 0.01858635,
                               0.02092013, 0.02332059, 0.02565167, 0.0280451, 0.029584,
                               0.03173562, 0.03388384, 0.03536185, 0.03691797, 0.03901287,
                               0.04019002, 0.04240905, 0.04406599, 0.04547479, 0.04711793,
                               0.04755674, 0.05004567, 0.05151874, 0.05273532, 0.05387794,
                               0.05590677, 0.0569012, 0.05808209, 0.05981104, 0.06054725,
                               0.06233294, 0.06287915, 0.06495156, 0.06526643, 0.06673481,
                               0.06791432, 0.06985476, 0.07011118, 0.07206724, 0.07281596]),
                     np.array([0.00417477, 0.00738503, 0.01089018, 0.01372497, 0.01608757,
                               0.01875562, 0.02107689, 0.02381095, 0.02584553, 0.02803378,
                               0.03012905, 0.03204936, 0.03378924, 0.03603153, 0.03752491,
                               0.03917651, 0.04071801, 0.04269854, 0.0448977, 0.04626001,
                               0.04749626, 0.04935769, 0.05062121, 0.05148194, 0.05333243,
                               0.05464218, 0.05615321, 0.05828795, 0.05911391, 0.06053408,
                               0.06120145, 0.06343912, 0.06366771, 0.06561829, 0.06679009,
                               0.06848108, 0.06948148, 0.07044105, 0.07159861, 0.07212605]),
                     np.array([0.00249475, 0.004263, 0.00642725, 0.00861726, 0.01049375,
                               0.01254357, 0.01446801, 0.01606049, 0.0181734, 0.01955183,
                               0.02182479, 0.02309072, 0.02504946, 0.02668825, 0.02798671,
                               0.02937966, 0.03102101, 0.03273824, 0.03442921, 0.03559429,
                               0.03770017, 0.03852744, 0.04014393, 0.04135599, 0.04288356,
                               0.04389802, 0.04504697, 0.04666363, 0.0479733, 0.04909028,
                               0.05053897, 0.05187059, 0.05294037, 0.05434318, 0.05480351,
                               0.05578399, 0.05728122, 0.05853206, 0.05915364, 0.06058793]),
                     np.array([0.00212341, 0.00250198, 0.00388314, 0.00515876, 0.00705254,
                               0.00876153, 0.01007762, 0.01235754, 0.01392531, 0.01632288,
                               0.01801731, 0.01916136, 0.02073698, 0.02238082, 0.02428741,
                               0.02579626, 0.02723345, 0.0287232, 0.03013392, 0.03199127,
                               0.03322426, 0.03507253, 0.03655417, 0.03775634, 0.03913108,
                               0.04032295, 0.04182248, 0.04305654, 0.04459139, 0.04579149,
                               0.04676922, 0.04836767, 0.04966458, 0.05013935, 0.05159697,
                               0.05291859, 0.05393223, 0.0556623, 0.05647055, 0.05705561]),
                     np.array([0.00491709, 0.00756564, 0.01108461, 0.01412748, 0.01632436,
                               0.01891749, 0.02145888, 0.02399148, 0.02605067, 0.02813657,
                               0.02971819, 0.03163095, 0.03368306, 0.03563044, 0.03738984,
                               0.03867736, 0.04099428, 0.0417811, 0.04373861, 0.04524962,
                               0.04675861, 0.04844468, 0.04965868, 0.05104928, 0.05284955,
                               0.05407092, 0.05495924, 0.05696784, 0.05787937, 0.05937224,
                               0.06078033, 0.0619069, 0.06337105, 0.06430933, 0.06612802,
                               0.06707971, 0.06831321, 0.06939889, 0.07090704, 0.07136969]),
                     np.array([0.00314358, 0.00622251, 0.00908917, 0.01187678, 0.01437231,
                               0.01671245, 0.01918516, 0.02130019, 0.02370937, 0.02578973,
                               0.02732329, 0.02954287, 0.03118523, 0.03340041, 0.03459009,
                               0.03697241, 0.03832703, 0.04045214, 0.041965, 0.04313408,
                               0.04462605, 0.04627602, 0.04762416, 0.0491017, 0.05051299,
                               0.05199839, 0.05347508, 0.05490359, 0.05613741, 0.05753028,
                               0.05894325, 0.06013363, 0.06131545, 0.06306812, 0.06341947,
                               0.06478305, 0.06602575, 0.06714543, 0.06838719, 0.06857477]),
                     np.array([0.00113874, 0.00284709, 0.00502388, 0.00747854, 0.00948046,
                               0.01214541, 0.01398012, 0.01609501, 0.01806956, 0.01999714,
                               0.02164383, 0.02334505, 0.0243806, 0.02691557, 0.02789882,
                               0.03017626, 0.03194412, 0.03323843, 0.03479656, 0.03652,
                               0.03776607, 0.03870202, 0.04081107, 0.04205389, 0.04325931,
                               0.04454114, 0.04597108, 0.04707416, 0.04849632, 0.049911,
                               0.05120595, 0.0520281, 0.0535093, 0.05467934, 0.05588911,
                               0.05736156, 0.0583585, 0.05898744, 0.06059826, 0.0618648]),
                     np.array([0.00635291, 0.00917955, 0.01283235, 0.01545897, 0.01782269,
                               0.0199719, 0.02260452, 0.02472763, 0.02701618, 0.028323,
                               0.03073523, 0.03275324, 0.03433378, 0.03609062, 0.03732886,
                               0.0390764, 0.04110953, 0.04213128, 0.04398686, 0.04601431,
                               0.04735494, 0.04874462, 0.04994827, 0.05140626, 0.05234608,
                               0.0546654, 0.05571111, 0.05714959, 0.05910852, 0.05928901,
                               0.06088414, 0.0614911, 0.06349796, 0.06415743, 0.06579347,
                               0.0665886, 0.06812555, 0.06876468, 0.07042643, 0.07124037]),
                     ]

    avgHeurMat = np.average(np.array(heurlist), axis=0)

    # Size of figure layout
    figtup = (7, 5)
    titleSz, axSz, labelSz = 12, 10, 9
    xMax = 450

    # Plot of marginal utilities
    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [tnNames[ind] for ind in range(numTN)]

    x = range(testInt, testMax + 1, testInt)
    deltaArr = np.zeros((avgHeurMat.shape[0], avgHeurMat.shape[1] - 1))
    for rw in range(deltaArr.shape[0]):
        for col in range(deltaArr.shape[1]):
            deltaArr[rw, col] = avgHeurMat[rw, col + 1] - avgHeurMat[rw, col]
    yMax = np.max(deltaArr) * 1.1

    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    for tnind in range(numTN):
        adj = 0.00005
        if tnind == 0:
            plt.text(testInt * 1.1, deltaArr[tnind, 0] + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 1:
            plt.text(testInt * 1.1, deltaArr[tnind, 0] - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        else:
            plt.text(testInt * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., yMax])
    plt.xlim([0., xMax])
    plt.xlabel('Number of Tests', fontsize=axSz)
    plt.ylabel('Marginal Utility Gain', fontsize=axSz)
    plt.title('Marginal Utility with Increasing Tests\nFamiliar Setting with Market Term', fontsize=titleSz)
    plt.show()
    plt.close()

    # Allocation plot
    allocArr, objValArr = sampf.smooth_alloc_forward(avgHeurMat)

    colors = cm.rainbow(np.linspace(0, 0.5, numTN))
    labels = [tnNames[ind] for ind in range(numTN)]
    x = range(testInt, testMax + 1, testInt)
    _ = plt.figure(figsize=figtup)
    for tnind in range(allocArr.shape[0]):
        plt.plot(x, allocArr[tnind] * testInt, linewidth=2, color=colors[tnind],
                 label=labels[tnind], alpha=0.6)
    # allocMax = allocArr.max() * testInt * 1.1
    allocMax = 185
    for tnind in range(numTN):
        adj = 2.9
        if tnind == 1:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 3:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        else:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt, labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., allocMax])
    plt.xlim([0., xMax])
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Test Node Allocation', fontsize=axSz)
    plt.title('Sampling Plan vs. Budget\nFamiliar Setting with Market Term', fontsize=titleSz)
    # plt.tight_layout()
    plt.show()
    plt.close()

    # Utility comparison plot
    colors = cm.rainbow(np.linspace(0, 0.8, 3))
    labels = ['Heuristic', 'Uniform', 'Rudimentary']
    x = range(testInt, testMax + 1, testInt)
    margUtilGroupList = [heur_utillist, unif_utillist, rudi_utillist]
    utilMax = -1
    for lst in margUtilGroupList:
        currMax = np.amax(np.array(lst))
        if currMax > utilMax:
            utilMax = currMax
    utilMax = utilMax * 1.1

    _ = plt.figure(figsize=figtup)
    for groupInd, margUtilGroup in enumerate(margUtilGroupList):
        groupArr = np.array(margUtilGroup)
        groupAvgArr = np.average(groupArr, axis=0)
        # Compile error bars
        stdevs = [np.std(groupArr[:, i]) for i in range(groupArr.shape[1])]
        group05Arr = [groupAvgArr[i] - (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        group95Arr = [groupAvgArr[i] + (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        plt.plot(x, groupAvgArr, color=colors[groupInd], linewidth=0.7, alpha=1., label=labels[groupInd] + ' 95% CI')
        plt.fill_between(x, groupAvgArr, group05Arr, color=colors[groupInd], alpha=0.2)
        plt.fill_between(x, groupAvgArr, group95Arr, color=colors[groupInd], alpha=0.2)
        # Line label
        plt.text(x[-1] * 1.01, groupAvgArr[-1], labels[groupInd].ljust(15), fontsize=labelSz - 1)
    plt.ylim(0, utilMax)
    # plt.xlim(0,x[-1]*1.12)
    plt.xlim([0., xMax])
    leg = plt.legend(loc='upper left', fontsize=labelSz)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(1.0)
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Plan Utility', fontsize=axSz)
    plt.title('Utility from Heuristic vs. Uniform and Rudimentary Allocations\nFamiliar Setting with Market Term',
              fontsize=titleSz)
    # Add text box showing budgetary savings
    heurUtilAvg = np.average(np.array(heur_utillist), axis=0)
    x2, x3 = 120, 144
    plt.plot([100, x3], [heurUtilAvg[9], heurUtilAvg[9]], color='black', linestyle='--')
    iv = 0.0015
    plt.plot([100, 100], [heurUtilAvg[9] - iv, heurUtilAvg[9] + iv], color='black', linestyle='--')
    plt.plot([x2, x2], [heurUtilAvg[9] - iv, heurUtilAvg[9] + iv], color='black', linestyle='--')
    plt.plot([x3, x3], [heurUtilAvg[9] - iv, heurUtilAvg[9] + iv], color='black', linestyle='--')
    plt.text(103, heurUtilAvg[9] + iv / 2, '30', fontsize=labelSz)
    plt.text(125, heurUtilAvg[9] + iv / 2, '26', fontsize=labelSz)
    # plt.tight_layout()
    plt.show()
    plt.close()

    return


def casestudyplots_exploratory_market():
    """
    Cleaned up plots for use in case study in paper
    """
    testMax, testInt = 400, 10
    tnNames = ['MOD_39', 'MOD_17', 'MODHIGH_95', 'MODHIGH_26',
               'MODHIGH_EXPL_1', 'MOD_EXPL_1', 'MODHIGH_EXPL_2', 'MOD_EXPL_2']
    numTN = len(tnNames)

    unif_utillist = [np.array([0.01464967, 0.0229887, 0.03584062, 0.04179026, 0.04775673,
                               0.05543825, 0.06025951, 0.06475962, 0.06894527, 0.07285823,
                               0.07772007, 0.08107989, 0.08526541, 0.08870335, 0.0918858,
                               0.09471104, 0.09881675, 0.10139817, 0.10384348, 0.10754363,
                               0.1094074, 0.11270981, 0.11473015, 0.11667244, 0.12068755,
                               0.12226979, 0.12450583, 0.12648042, 0.12857005, 0.13127864,
                               0.13321517, 0.13420477, 0.13694135, 0.13838002, 0.13928167,
                               0.14230523, 0.14408117, 0.1456639, 0.14596233, 0.14952923]),
                     np.array([0.0139362, 0.0225148, 0.03599858, 0.04298375, 0.04888883,
                               0.05697708, 0.06121599, 0.06585707, 0.07055392, 0.07428761,
                               0.07974163, 0.08269428, 0.08626072, 0.0906986, 0.09361123,
                               0.09650964, 0.09964081, 0.10295796, 0.10538408, 0.10810733,
                               0.11172224, 0.11517426, 0.11641704, 0.11874652, 0.12139643,
                               0.12363176, 0.12632997, 0.12897328, 0.13049864, 0.13256257,
                               0.1345099, 0.13647788, 0.13862263, 0.13865588, 0.14197676,
                               0.14361184, 0.14621618, 0.14602534, 0.14862478, 0.14923932]),
                     np.array([0.00923481, 0.01651557, 0.03004286, 0.03602463, 0.04222123,
                               0.0493772, 0.05358076, 0.05787152, 0.06187306, 0.06536282,
                               0.07055878, 0.07438939, 0.07815394, 0.08227689, 0.0849347,
                               0.08769323, 0.09175722, 0.09364522, 0.09720825, 0.1005212,
                               0.10303259, 0.10596367, 0.10827563, 0.11047925, 0.11279049,
                               0.11394729, 0.11797724, 0.11974588, 0.12195965, 0.12356092,
                               0.12561642, 0.12684814, 0.12933415, 0.13072326, 0.13249803,
                               0.13492749, 0.13615158, 0.13719615, 0.13913036, 0.14054828]),
                     np.array([0.01439621, 0.02228214, 0.03466415, 0.04154927, 0.04738035,
                               0.05599791, 0.06049649, 0.06468376, 0.06897861, 0.07240472,
                               0.07801586, 0.08221604, 0.08460067, 0.08846472, 0.09218048,
                               0.09564121, 0.09756695, 0.10040465, 0.10381762, 0.10715562,
                               0.10937437, 0.11222642, 0.11426446, 0.11707731, 0.11870296,
                               0.12161138, 0.12412389, 0.12714744, 0.1275714, 0.13021352,
                               0.13173752, 0.13395222, 0.13763802, 0.13812745, 0.13987455,
                               0.14234941, 0.14319524, 0.14487606, 0.14707328, 0.14659313]),
                     np.array([0.01257098, 0.02139432, 0.03409391, 0.04060844, 0.04601931,
                               0.0540546, 0.05850705, 0.06350191, 0.06672185, 0.07153847,
                               0.07603903, 0.07944896, 0.08310238, 0.08768118, 0.0906845,
                               0.09334303, 0.09641097, 0.09910477, 0.10345229, 0.10515126,
                               0.10758629, 0.11188565, 0.11384016, 0.11693916, 0.11818187,
                               0.12009328, 0.1226744, 0.12459362, 0.12707462, 0.12981212,
                               0.13214225, 0.13333261, 0.13671357, 0.13758735, 0.13931797,
                               0.14110086, 0.14298402, 0.14469668, 0.14562638, 0.14757289]),
                     np.array([0.01165207, 0.02097778, 0.03484701, 0.04153442, 0.04683575,
                               0.05504851, 0.05997599, 0.06437074, 0.0685178, 0.07318873,
                               0.07826873, 0.08210943, 0.08471372, 0.08977436, 0.09254309,
                               0.096578, 0.09837596, 0.10134863, 0.10461208, 0.10879483,
                               0.11136273, 0.11329766, 0.11650803, 0.11931556, 0.12201899,
                               0.12405044, 0.12513765, 0.12932461, 0.13027671, 0.13277558,
                               0.13423078, 0.13667872, 0.13931965, 0.14067241, 0.14172243,
                               0.14490939, 0.14526402, 0.14844154, 0.14930412, 0.15060652]),
                     np.array([0.01311511, 0.02240771, 0.03605929, 0.04223084, 0.04782919,
                               0.05590389, 0.06036553, 0.06517178, 0.06986181, 0.07289917,
                               0.07827076, 0.08200794, 0.08561967, 0.09046584, 0.09287982,
                               0.09605129, 0.09922784, 0.1021162, 0.10515267, 0.10859804,
                               0.11228896, 0.11408649, 0.11570524, 0.11887276, 0.12207649,
                               0.12273191, 0.12721416, 0.12776474, 0.12958381, 0.13220313,
                               0.13528835, 0.13632453, 0.13866308, 0.14029551, 0.14271408,
                               0.14408406, 0.14431634, 0.14787882, 0.14838643, 0.15009423])
                     ]
    u1 = np.array([[0., 0.00294156, 0.00505353, 0.00622081, 0.00833352,
                    0.01016614, 0.01167477, 0.01308104, 0.01442442, 0.01605372,
                    0.01700349, 0.01872152, 0.01982057, 0.02110486, 0.02251956,
                    0.02300636, 0.0242151, 0.02536069, 0.0266946, 0.02797237,
                    0.02888131, 0.0302996, 0.03178587, 0.03214798, 0.03403775,
                    0.03438991, 0.03600066, 0.03737367, 0.03858834, 0.03999715,
                    0.04146897, 0.04215595, 0.04339687, 0.04421634, 0.04548668,
                    0.04603785, 0.04873142, 0.04920739, 0.0501841, 0.05102084,
                    0.05196587],
                   [0., 0.00491095, 0.00700718, 0.00805448, 0.00934249,
                    0.01009402, 0.01114307, 0.01176502, 0.01242792, 0.01350043,
                    0.01441502, 0.01500855, 0.01611189, 0.01687593, 0.017714,
                    0.01877624, 0.01997259, 0.02052398, 0.02163861, 0.02256561,
                    0.02371864, 0.02470197, 0.02566034, 0.02653166, 0.02744203,
                    0.02836392, 0.02931027, 0.03078558, 0.03199085, 0.03363543,
                    0.03489766, 0.03598385, 0.03651481, 0.03774292, 0.03863593,
                    0.04028127, 0.04115285, 0.04313653, 0.04300859, 0.04383249,
                    0.04595533],
                   [0., 0.00238291, 0.00344937, 0.00448634, 0.00528027,
                    0.00602451, 0.00700927, 0.00766571, 0.00815682, 0.00926578,
                    0.0096705, 0.01052858, 0.01131783, 0.01183957, 0.01292317,
                    0.01332831, 0.0145101, 0.01477779, 0.01612766, 0.01680281,
                    0.01751967, 0.01844222, 0.01975638, 0.02036133, 0.02178071,
                    0.02271226, 0.02333835, 0.02432454, 0.02553437, 0.02646583,
                    0.02742135, 0.0288147, 0.02921815, 0.03151026, 0.03150182,
                    0.03237576, 0.03412854, 0.03550132, 0.03573409, 0.03703065,
                    0.0383397],
                   [0., 0.00259007, 0.00424876, 0.00540979, 0.0065792,
                    0.00763452, 0.0085711, 0.00936231, 0.00993063, 0.01070996,
                    0.01137705, 0.01211878, 0.01273082, 0.01330849, 0.01395264,
                    0.01439195, 0.0147341, 0.01505793, 0.01570199, 0.01603922,
                    0.01639898, 0.01670605, 0.01761948, 0.01780266, 0.01828775,
                    0.01848148, 0.01883935, 0.01899126, 0.01936471, 0.01959431,
                    0.0201425, 0.02016977, 0.02073374, 0.02096085, 0.02143542,
                    0.02176227, 0.02183575, 0.02243779, 0.02244614, 0.02285064,
                    0.02317446],
                   [0., 0.02233237, 0.02885546, 0.0325918, 0.03527222,
                    0.03737751, 0.03905537, 0.04053635, 0.04178747, 0.04290894,
                    0.04423204, 0.04520843, 0.04602293, 0.04727829, 0.04790469,
                    0.04887675, 0.04983815, 0.05018195, 0.05155552, 0.05217648,
                    0.05308929, 0.05418031, 0.05473924, 0.05529253, 0.05629469,
                    0.05729903, 0.05839222, 0.05897359, 0.05968929, 0.06057427,
                    0.06178252, 0.06178343, 0.06300318, 0.06353017, 0.06476846,
                    0.0653556, 0.06647302, 0.0671801, 0.06839626, 0.06839037,
                    0.07039903],
                   [0., 0.02247959, 0.03028494, 0.03459138, 0.03819429,
                    0.04058716, 0.04254356, 0.04427986, 0.04610555, 0.04740889,
                    0.04849462, 0.04991845, 0.05083364, 0.05208966, 0.05277805,
                    0.05368482, 0.05501408, 0.05536098, 0.05643717, 0.05777378,
                    0.05849088, 0.05946219, 0.06002456, 0.06100677, 0.06186559,
                    0.06229836, 0.06290462, 0.06428467, 0.06450949, 0.06556034,
                    0.06609305, 0.0669713, 0.06804497, 0.06858331, 0.06959695,
                    0.07071425, 0.07126606, 0.07151226, 0.0723019, 0.07321877,
                    0.07382898],
                   [0., 0.01267891, 0.01548799, 0.01725044, 0.01879362,
                    0.01989068, 0.02085653, 0.02176546, 0.02294816, 0.02357287,
                    0.02441636, 0.02525693, 0.02589601, 0.02632173, 0.02730554,
                    0.02785034, 0.02858383, 0.02919281, 0.02947804, 0.03044411,
                    0.03128764, 0.03168889, 0.03242975, 0.03294639, 0.03309182,
                    0.03407238, 0.03489403, 0.03541111, 0.03575074, 0.03648439,
                    0.03728957, 0.03769298, 0.03770279, 0.03863778, 0.03977777,
                    0.03999375, 0.0407124, 0.04150927, 0.04222682, 0.04220722,
                    0.04299015],
                   [0., 0.0108917, 0.01494471, 0.01745847, 0.01895519,
                    0.0205655, 0.02155158, 0.0228554, 0.02405234, 0.02486323,
                    0.02635916, 0.02705598, 0.02788735, 0.02908409, 0.02957137,
                    0.03090377, 0.03201417, 0.03319185, 0.03383869, 0.03526646,
                    0.03647863, 0.03694083, 0.03838219, 0.04005099, 0.04085091,
                    0.04177836, 0.04278106, 0.04410066, 0.04535052, 0.04635712,
                    0.04770807, 0.04856994, 0.05026377, 0.05070915, 0.05234411,
                    0.05360933, 0.05506561, 0.05578664, 0.0580636, 0.05784155,
                    0.05910849]])
    u2 = np.array([[0., 0.0017391, 0.00413226, 0.00631547, 0.00793208,
                    0.00963334, 0.01159244, 0.01324519, 0.01425938, 0.01568667,
                    0.01721078, 0.01854201, 0.01964271, 0.02081237, 0.02175855,
                    0.02303991, 0.02424796, 0.02556294, 0.02671244, 0.02806033,
                    0.02942707, 0.02958896, 0.03155797, 0.03252214, 0.03312585,
                    0.03495868, 0.03641971, 0.03685336, 0.03829092, 0.03938805,
                    0.04095306, 0.04146367, 0.04262935, 0.04447943, 0.04481056,
                    0.04619983, 0.04810934, 0.04959416, 0.0505974, 0.05178179,
                    0.05319956],
                   [0., 0.00231791, 0.00350776, 0.00481711, 0.00613428,
                    0.00709796, 0.00824363, 0.00928286, 0.01014489, 0.01140601,
                    0.01255994, 0.01345432, 0.01436086, 0.0155068, 0.01632129,
                    0.01760341, 0.01861113, 0.01922368, 0.02056294, 0.02149764,
                    0.02265735, 0.02353863, 0.02481567, 0.02581908, 0.02722326,
                    0.02784546, 0.02950156, 0.03081676, 0.0312838, 0.03267807,
                    0.03414836, 0.03468929, 0.03632871, 0.03764755, 0.03779825,
                    0.03942321, 0.04025591, 0.04265774, 0.04306133, 0.04493257,
                    0.04606077],
                   [0., 0.0009454, 0.00213638, 0.00284136, 0.00385025,
                    0.00454305, 0.00517511, 0.00628037, 0.00695672, 0.00805026,
                    0.00907689, 0.00973237, 0.01069154, 0.01127122, 0.01216995,
                    0.01326622, 0.01430017, 0.01483581, 0.01569763, 0.01669873,
                    0.01753402, 0.01832635, 0.01932405, 0.02064235, 0.02126214,
                    0.02219918, 0.02344619, 0.02458658, 0.02541872, 0.02712247,
                    0.02738855, 0.0287634, 0.02967205, 0.03069341, 0.03214733,
                    0.03290439, 0.03378069, 0.03495422, 0.03581358, 0.03722088,
                    0.03902371],
                   [0., 0.00179716, 0.00336623, 0.00431036, 0.00570964,
                    0.00680191, 0.00792687, 0.0083432, 0.00930071, 0.00989137,
                    0.01080367, 0.01163467, 0.01208788, 0.01285389, 0.01314359,
                    0.01397297, 0.01438498, 0.01495565, 0.01524248, 0.01559405,
                    0.01616131, 0.0164277, 0.01692834, 0.01749708, 0.01774813,
                    0.0179802, 0.01799058, 0.01870734, 0.01912318, 0.01964657,
                    0.01978837, 0.02028394, 0.02082708, 0.02077518, 0.0209773,
                    0.02159124, 0.02163671, 0.02201062, 0.02259383, 0.02278231,
                    0.02310111],
                   [0., 0.02742735, 0.03302642, 0.03588228, 0.03788424,
                    0.03900204, 0.04042585, 0.04106171, 0.04228469, 0.04301551,
                    0.04425758, 0.04474978, 0.04562603, 0.04652927, 0.04740158,
                    0.04830957, 0.0491803, 0.04993549, 0.05042071, 0.0513904,
                    0.05229612, 0.05310801, 0.05375726, 0.05412177, 0.05577907,
                    0.05628909, 0.05715499, 0.05736192, 0.05900464, 0.05957257,
                    0.06053306, 0.06078261, 0.06201133, 0.06276236, 0.06328475,
                    0.06527064, 0.06491799, 0.0665144, 0.06687056, 0.06775844,
                    0.06839921],
                   [0., 0.0225182, 0.0294706, 0.03331682, 0.0363048,
                    0.03873126, 0.04086881, 0.04256863, 0.04402254, 0.04562137,
                    0.04676107, 0.0480464, 0.0492577, 0.05022138, 0.05113628,
                    0.0520775, 0.05340016, 0.05395093, 0.05512483, 0.05638137,
                    0.05736809, 0.05819165, 0.05854991, 0.05904234, 0.06012375,
                    0.0613492, 0.06183886, 0.06293424, 0.06308086, 0.06402376,
                    0.06558966, 0.06615244, 0.06660281, 0.06723777, 0.06793817,
                    0.06931329, 0.06965837, 0.07086099, 0.0711183, 0.07166538,
                    0.07279197],
                   [0., 0.00635727, 0.00944357, 0.01175358, 0.01321331,
                    0.0144822, 0.01601747, 0.01678146, 0.01793414, 0.01863792,
                    0.01987791, 0.02039072, 0.02130575, 0.0223351, 0.02295511,
                    0.02371655, 0.0244535, 0.02536343, 0.02609373, 0.02642666,
                    0.02745635, 0.02790724, 0.02837081, 0.02937632, 0.0295128,
                    0.03041032, 0.03123937, 0.03183153, 0.03258291, 0.03321887,
                    0.03395253, 0.03463422, 0.03503193, 0.03565558, 0.03649766,
                    0.03659866, 0.03745525, 0.03841801, 0.03855072, 0.03908428,
                    0.04007217],
                   [0., 0.00666261, 0.01016339, 0.0125588, 0.01485631,
                    0.01639646, 0.01780462, 0.01916847, 0.02045316, 0.0214463,
                    0.02263655, 0.02368692, 0.02480178, 0.02591129, 0.02713168,
                    0.02806906, 0.02919227, 0.03017831, 0.03130595, 0.03245392,
                    0.0332501, 0.03471176, 0.03540512, 0.03789307, 0.03823173,
                    0.03879365, 0.04012662, 0.04130752, 0.04269316, 0.04395496,
                    0.04538693, 0.04664258, 0.04754776, 0.0487676, 0.04948142,
                    0.05135684, 0.05261211, 0.05360377, 0.05513707, 0.05561504,
                    0.05716933]])
    u3 = np.array([[0., 0.00292447, 0.00480057, 0.00658342, 0.00822542,
                    0.00944735, 0.01066059, 0.01153016, 0.01281226, 0.0136289,
                    0.01495729, 0.01601854, 0.01721076, 0.01833174, 0.01929691,
                    0.01995287, 0.02122343, 0.02212817, 0.02318724, 0.02425353,
                    0.02533391, 0.02637504, 0.02706205, 0.02885997, 0.02951471,
                    0.03126011, 0.03130787, 0.03273876, 0.03424094, 0.03555594,
                    0.03664342, 0.0370949, 0.03828725, 0.03841933, 0.04056766,
                    0.04179399, 0.04264748, 0.04399446, 0.04487499, 0.04588711,
                    0.04639787],
                   [0., 0.00190322, 0.00306546, 0.00400407, 0.00482337,
                    0.00563315, 0.00657345, 0.00734054, 0.00789975, 0.00880256,
                    0.00965498, 0.0103446, 0.01148912, 0.01220097, 0.01313068,
                    0.01372557, 0.01461603, 0.0155163, 0.016531, 0.01706941,
                    0.01861269, 0.01978363, 0.02027005, 0.02145154, 0.02239371,
                    0.02272158, 0.02426778, 0.02630002, 0.02660261, 0.02744996,
                    0.02887531, 0.02993215, 0.03106347, 0.03232399, 0.03365166,
                    0.03405152, 0.03569531, 0.03682333, 0.03736247, 0.03852051,
                    0.03949081],
                   [0., 0.0011884, 0.00195679, 0.00261055, 0.00337473,
                    0.00396699, 0.00467606, 0.00506884, 0.0058727, 0.00660392,
                    0.00705081, 0.0077327, 0.00864091, 0.00896095, 0.01025279,
                    0.01057569, 0.01115508, 0.01201242, 0.01253347, 0.01318974,
                    0.01419501, 0.01488692, 0.01594896, 0.01664329, 0.01796224,
                    0.01879842, 0.0191551, 0.01985812, 0.02103185, 0.02214024,
                    0.02264387, 0.0240517, 0.0247183, 0.02580615, 0.02715531,
                    0.02856513, 0.02872878, 0.02965486, 0.03153891, 0.0321365,
                    0.03291353],
                   [0., 0.00201785, 0.00313398, 0.00382026, 0.00445497,
                    0.00508291, 0.00592151, 0.00614427, 0.0067873, 0.00757806,
                    0.00811553, 0.00850167, 0.00909221, 0.00947603, 0.00989742,
                    0.01021754, 0.01052604, 0.010977, 0.0116524, 0.0116868,
                    0.01222512, 0.01282082, 0.01275281, 0.01324527, 0.01353942,
                    0.0141051, 0.0142847, 0.01460722, 0.01482567, 0.0153177,
                    0.01566496, 0.0160387, 0.01612715, 0.01662379, 0.01659124,
                    0.01694377, 0.01753346, 0.01759724, 0.01771382, 0.01811891,
                    0.01865521],
                   [0., 0.0192249, 0.02513563, 0.02830984, 0.03053475,
                    0.03244553, 0.03363943, 0.03513867, 0.03646008, 0.03746618,
                    0.03840732, 0.03938065, 0.04012179, 0.04138335, 0.04188101,
                    0.04272292, 0.0440334, 0.04450651, 0.04571878, 0.0465795,
                    0.04693199, 0.04748132, 0.04846783, 0.04940526, 0.05049572,
                    0.05117543, 0.05187601, 0.05231591, 0.05339594, 0.05367199,
                    0.05492437, 0.05591361, 0.05658002, 0.05677028, 0.05794597,
                    0.05855944, 0.0597263, 0.0606767, 0.06089329, 0.06238665,
                    0.06230869],
                   [0., 0.01514981, 0.02251309, 0.0269226, 0.03031565,
                    0.03297344, 0.03510183, 0.03717064, 0.03843964, 0.04004105,
                    0.04151236, 0.04260006, 0.04377768, 0.04488986, 0.04611108,
                    0.04667239, 0.04762304, 0.04875662, 0.04973024, 0.05026295,
                    0.05127754, 0.05245856, 0.05270457, 0.05371764, 0.05468581,
                    0.05539387, 0.05582306, 0.05732158, 0.05753845, 0.05866103,
                    0.05890715, 0.05968901, 0.06047244, 0.06087026, 0.06175572,
                    0.06269276, 0.0630814, 0.06384716, 0.06476997, 0.06577574,
                    0.06612679],
                   [0., 0.00278294, 0.00521942, 0.00684575, 0.00841767,
                    0.00972256, 0.01077953, 0.01161165, 0.01283437, 0.01348916,
                    0.01448782, 0.01527355, 0.01607493, 0.01696502, 0.01780507,
                    0.01800857, 0.019037, 0.01949349, 0.02046644, 0.0206756,
                    0.02175168, 0.02241395, 0.0232497, 0.02354939, 0.02405069,
                    0.02501095, 0.02539841, 0.02549399, 0.02679611, 0.02716407,
                    0.02783542, 0.02859171, 0.02907126, 0.02962453, 0.03026597,
                    0.03108157, 0.03187858, 0.03239498, 0.03295831, 0.03326473,
                    0.03433141],
                   [0., 0.00336105, 0.00702542, 0.00936218, 0.01124918,
                    0.01278707, 0.01427432, 0.01550372, 0.01669429, 0.01769135,
                    0.01889866, 0.01998421, 0.02095295, 0.02134471, 0.02272742,
                    0.02359614, 0.02464932, 0.02556556, 0.02697096, 0.02769694,
                    0.02873375, 0.02993691, 0.03096722, 0.03164894, 0.03320473,
                    0.03414116, 0.03513923, 0.03620067, 0.03703005, 0.03848555,
                    0.03997776, 0.04062479, 0.04170903, 0.04380891, 0.04449142,
                    0.04524801, 0.04686168, 0.04805262, 0.04900197, 0.04956221,
                    0.05110342]])
    u4 = np.array([[0., 0.00299187, 0.00564652, 0.00766154, 0.00899766,
                    0.01086988, 0.01295404, 0.01392214, 0.0156104, 0.01688021,
                    0.01826993, 0.01923553, 0.02083954, 0.0218393, 0.02279299,
                    0.0240834, 0.02524449, 0.02633193, 0.02788655, 0.02914818,
                    0.03003303, 0.03076753, 0.03204568, 0.03341971, 0.0340526,
                    0.03595448, 0.03652788, 0.03823819, 0.03967212, 0.04062831,
                    0.04157212, 0.0428609, 0.04365788, 0.044913, 0.04527096,
                    0.04730649, 0.04833768, 0.04970853, 0.05125308, 0.05185667,
                    0.05305843],
                   [0., 0.00164329, 0.00335756, 0.00456881, 0.00588376,
                    0.00696404, 0.00804094, 0.00931999, 0.0101686, 0.01128158,
                    0.01245819, 0.01348578, 0.01429449, 0.0150016, 0.01611414,
                    0.01724728, 0.01797072, 0.01942409, 0.0205775, 0.0211677,
                    0.02214802, 0.02359303, 0.02432193, 0.02604374, 0.02678142,
                    0.02824566, 0.02848257, 0.02996579, 0.0309389, 0.03240033,
                    0.03257107, 0.03450454, 0.03531074, 0.03639482, 0.03830676,
                    0.03898794, 0.04038775, 0.04202926, 0.04232813, 0.04376946,
                    0.04526533],
                   [0., 0.00195623, 0.00313435, 0.00430352, 0.00508364,
                    0.00631071, 0.00692016, 0.00803667, 0.00896746, 0.00951922,
                    0.01029418, 0.01122376, 0.01195596, 0.01301098, 0.01358393,
                    0.01426997, 0.01516676, 0.01629274, 0.01709336, 0.01775326,
                    0.01854061, 0.01940287, 0.02046429, 0.02129094, 0.02209033,
                    0.02315537, 0.02391866, 0.02459942, 0.02627035, 0.02749608,
                    0.02799257, 0.02934424, 0.03043411, 0.03097683, 0.03185161,
                    0.03251535, 0.03402147, 0.03545626, 0.0365558, 0.03805145,
                    0.03906855],
                   [0., 0.0021746, 0.00353874, 0.0046552, 0.00555986,
                    0.00653635, 0.00761999, 0.00826737, 0.00903378, 0.00993461,
                    0.010261, 0.01094116, 0.011698, 0.01192285, 0.01279554,
                    0.01317448, 0.01364013, 0.01429263, 0.01451903, 0.01511449,
                    0.01532313, 0.0160785, 0.01610688, 0.01663202, 0.01688395,
                    0.01749619, 0.01757378, 0.01802439, 0.01865731, 0.01898152,
                    0.01926489, 0.01933638, 0.0196417, 0.02008224, 0.02030172,
                    0.02047304, 0.02122644, 0.02135261, 0.02142715, 0.02237125,
                    0.02221484],
                   [0., 0.01732472, 0.02426673, 0.0286151, 0.03129383,
                    0.03362499, 0.03574057, 0.03727293, 0.03886267, 0.04007774,
                    0.04137585, 0.04290368, 0.04379427, 0.04490745, 0.04594037,
                    0.04651331, 0.04744643, 0.04916956, 0.04943996, 0.05033304,
                    0.05090518, 0.05225187, 0.0532764, 0.05370949, 0.0550821,
                    0.05613071, 0.0562659, 0.05761182, 0.05832129, 0.05930197,
                    0.0601629, 0.06084673, 0.06190002, 0.06294693, 0.06313865,
                    0.06396791, 0.06511249, 0.06589405, 0.06728554, 0.06774715,
                    0.06855804],
                   [0., 0.02313029, 0.03032454, 0.03490739, 0.03813865,
                    0.0405665, 0.04261851, 0.0445413, 0.04621839, 0.04767336,
                    0.04881545, 0.04991295, 0.0511499, 0.05226189, 0.05326962,
                    0.05386925, 0.05495153, 0.05601518, 0.05656711, 0.05764901,
                    0.05829754, 0.05935144, 0.05976864, 0.06071527, 0.06156729,
                    0.06214216, 0.06321068, 0.06351268, 0.06483901, 0.06502547,
                    0.06629314, 0.06682985, 0.06761676, 0.06802545, 0.06860748,
                    0.06954411, 0.07054443, 0.07116551, 0.07151624, 0.07286335,
                    0.07348336],
                   [0., 0.00623538, 0.00993809, 0.01238207, 0.01390676,
                    0.01575628, 0.01682851, 0.01811502, 0.01904157, 0.01959724,
                    0.0207932, 0.02152678, 0.02207561, 0.02331984, 0.02383459,
                    0.02463086, 0.025442, 0.02634532, 0.02694441, 0.02731631,
                    0.02744516, 0.02841034, 0.02881465, 0.02965037, 0.03080854,
                    0.03127242, 0.03172746, 0.03231916, 0.03303221, 0.03342555,
                    0.03373128, 0.0348793, 0.03550129, 0.0359825, 0.03732511,
                    0.03707814, 0.03750257, 0.03886392, 0.03918173, 0.04020236,
                    0.03985249],
                   [0., 0.00970621, 0.01303195, 0.01510036, 0.016829,
                    0.01836864, 0.01914594, 0.02037703, 0.02154067, 0.02232246,
                    0.02348166, 0.02448321, 0.02557887, 0.02701856, 0.02745,
                    0.02878297, 0.02957426, 0.03059549, 0.03225116, 0.03308672,
                    0.03322218, 0.0349125, 0.03564646, 0.03661597, 0.03806268,
                    0.03903763, 0.04009641, 0.04126003, 0.04217487, 0.04346801,
                    0.0452342, 0.04670526, 0.04723606, 0.04831737, 0.04940036,
                    0.05040349, 0.05205119, 0.0537115, 0.0546, 0.05549706,
                    0.05709012]])
    u5 = np.array([[0., 0.00354605, 0.00641502, 0.00902709, 0.01111765,
                    0.01290165, 0.01445205, 0.01565319, 0.01764713, 0.01872563,
                    0.02012479, 0.02118426, 0.02274831, 0.02407065, 0.02464102,
                    0.02585802, 0.0273357, 0.02888128, 0.02976888, 0.03089727,
                    0.0316335, 0.03315846, 0.03395349, 0.03524524, 0.03641384,
                    0.0384498, 0.03867669, 0.04036621, 0.04083845, 0.04199802,
                    0.04330614, 0.04503045, 0.04571009, 0.04668384, 0.048489,
                    0.04882283, 0.04987642, 0.05192447, 0.05262581, 0.05365192,
                    0.05424676],
                   [0., 0.00568969, 0.00806513, 0.0094273, 0.01067373,
                    0.01202865, 0.01297933, 0.01374903, 0.01499907, 0.0157926,
                    0.01671927, 0.01749251, 0.01837352, 0.01936557, 0.02009969,
                    0.02090668, 0.02216278, 0.02315338, 0.0238359, 0.02485679,
                    0.02550925, 0.0266067, 0.02775716, 0.0287001, 0.02963042,
                    0.03102693, 0.03223705, 0.03309253, 0.03470795, 0.03520903,
                    0.03613517, 0.03759352, 0.03844606, 0.04016956, 0.04102021,
                    0.04201013, 0.04286284, 0.04402149, 0.04534031, 0.04627435,
                    0.04784973],
                   [0., 0.00155291, 0.003, 0.0040832, 0.00519177,
                    0.00630471, 0.00712972, 0.00793885, 0.0090591, 0.01009493,
                    0.01063462, 0.01184199, 0.01251603, 0.01314171, 0.01422003,
                    0.01460924, 0.01590664, 0.01666344, 0.01755424, 0.01817345,
                    0.01936577, 0.02041186, 0.02093993, 0.02205261, 0.0228527,
                    0.02406599, 0.0249931, 0.02604072, 0.02680271, 0.02799266,
                    0.02885915, 0.03047001, 0.0310637, 0.03162753, 0.03345594,
                    0.03395548, 0.03502555, 0.03586228, 0.03765317, 0.03902283,
                    0.03946157],
                   [0., 0.00146087, 0.00294314, 0.00395593, 0.00534393,
                    0.00627078, 0.00702149, 0.00792084, 0.00860498, 0.0094903,
                    0.01037337, 0.01080641, 0.01113008, 0.01233803, 0.01274078,
                    0.01301592, 0.01352018, 0.01420004, 0.01441482, 0.01470987,
                    0.01577561, 0.01588495, 0.01579751, 0.01670791, 0.01710777,
                    0.01779289, 0.01776832, 0.0181922, 0.01879385, 0.01940854,
                    0.01932005, 0.02019403, 0.02007807, 0.02038137, 0.02082543,
                    0.02089632, 0.02161, 0.02146148, 0.0217766, 0.02237086,
                    0.02275099],
                   [0., 0.02018111, 0.0269432, 0.03082883, 0.03343219,
                    0.03585655, 0.03791821, 0.03954878, 0.04074643, 0.04211369,
                    0.04338633, 0.04451844, 0.04553696, 0.0467601, 0.04784031,
                    0.0487724, 0.04971502, 0.05055031, 0.05150602, 0.05267229,
                    0.0536437, 0.05433267, 0.05567003, 0.05578841, 0.05642481,
                    0.05803695, 0.05805357, 0.05930942, 0.06066082, 0.06092719,
                    0.06152486, 0.06273818, 0.06371157, 0.06424276, 0.06570193,
                    0.06575781, 0.0671785, 0.06768339, 0.06881301, 0.06929803,
                    0.06979846],
                   [0., 0.01910227, 0.0271765, 0.03192722, 0.03519914,
                    0.03814525, 0.04054042, 0.04231339, 0.04393665, 0.04561284,
                    0.0470659, 0.048786, 0.04991142, 0.05115235, 0.05226107,
                    0.05311122, 0.05412391, 0.05498471, 0.05628442, 0.05712792,
                    0.05799241, 0.05873256, 0.05965568, 0.06061292, 0.06143874,
                    0.06253082, 0.06301898, 0.063885, 0.06488644, 0.06527671,
                    0.06648461, 0.06696046, 0.06808834, 0.06906722, 0.06932177,
                    0.07004143, 0.07119462, 0.07103399, 0.0721715, 0.07319553,
                    0.07434806],
                   [0., 0.01087611, 0.01387919, 0.01548825, 0.01700026,
                    0.01823521, 0.01948419, 0.02045358, 0.02167235, 0.02230127,
                    0.02354183, 0.0240812, 0.02526564, 0.0256969, 0.02642544,
                    0.02715899, 0.02789689, 0.02860417, 0.02961441, 0.03004638,
                    0.03063597, 0.03140226, 0.03219211, 0.03247066, 0.03309092,
                    0.03388173, 0.0348307, 0.03503889, 0.03566248, 0.03631732,
                    0.03700422, 0.03773381, 0.0382796, 0.03861399, 0.0401057,
                    0.04064091, 0.0410691, 0.04111583, 0.04239887, 0.04276704,
                    0.04357626],
                   [0., 0.01296731, 0.01650029, 0.01888234, 0.02058507,
                    0.02195327, 0.02332989, 0.02431407, 0.02547793, 0.02648238,
                    0.02777087, 0.02871126, 0.02974498, 0.03045685, 0.03171766,
                    0.0322698, 0.03322524, 0.03493512, 0.03589817, 0.0365492,
                    0.03785283, 0.03852952, 0.03997539, 0.04087655, 0.04238689,
                    0.04358438, 0.04408245, 0.04613824, 0.04675192, 0.04853688,
                    0.0487029, 0.05041095, 0.05138137, 0.05264454, 0.05411054,
                    0.05466933, 0.05603835, 0.05710342, 0.05803283, 0.05924297,
                    0.06051867]])
    heurlist = [u1, u2, u3, u4, u5]
    heur_utillist = [np.array([0.01814256, 0.0392398, 0.04833426, 0.05598427, 0.06314142,
                               0.06976089, 0.07494779, 0.07871695, 0.08296518, 0.08628346,
                               0.09047718, 0.09309045, 0.09515336, 0.09841416, 0.10077472,
                               0.10376161, 0.10731877, 0.10940703, 0.11178777, 0.11369807,
                               0.11701572, 0.12044481, 0.12139491, 0.1238926, 0.12494185,
                               0.12580324, 0.12787467, 0.13054121, 0.13346172, 0.13423636,
                               0.13693912, 0.13996881, 0.14134538, 0.14150722, 0.14267676,
                               0.14398828, 0.14716366, 0.14733987, 0.14834699, 0.15000153]),
                     np.array([0.02329047, 0.03944378, 0.04663968, 0.05411333, 0.06144854,
                               0.06784217, 0.07244782, 0.07641531, 0.0805262, 0.08438177,
                               0.08747199, 0.09121573, 0.09377057, 0.09688332, 0.09925528,
                               0.10370465, 0.10570696, 0.10842042, 0.11174701, 0.11465724,
                               0.11651213, 0.11911722, 0.12087279, 0.12237647, 0.12439484,
                               0.12664851, 0.12827595, 0.13076115, 0.13263908, 0.13566195,
                               0.13667025, 0.13897559, 0.14039614, 0.14173603, 0.14428475,
                               0.14545878, 0.14614048, 0.14893251, 0.15048789, 0.15091192]),
                     np.array([0.01695832, 0.0382108, 0.04639173, 0.05446646, 0.06140647,
                               0.06859343, 0.07326426, 0.07669097, 0.08183018, 0.08481751,
                               0.08874762, 0.09183676, 0.09525752, 0.09865699, 0.10023648,
                               0.10363625, 0.10711158, 0.10994669, 0.11162405, 0.11549179,
                               0.1172276, 0.11967426, 0.12194647, 0.12369962, 0.12531369,
                               0.12769047, 0.12981065, 0.13218526, 0.13437024, 0.13536095,
                               0.13898425, 0.14071677, 0.14154419, 0.1443899, 0.14434034,
                               0.14540799, 0.14779547, 0.14848819, 0.14998711, 0.15122533]),
                     np.array([0.02124987, 0.04191757, 0.0500854, 0.0579956, 0.06561595,
                               0.0720533, 0.07712795, 0.08093198, 0.08512157, 0.08799387,
                               0.0924802, 0.09552747, 0.09858149, 0.10135565, 0.10374803,
                               0.10759322, 0.11045134, 0.11268488, 0.11487223, 0.11788325,
                               0.12171286, 0.12337377, 0.12512656, 0.12646354, 0.12951048,
                               0.13116879, 0.13308644, 0.13425978, 0.13778158, 0.14010257,
                               0.14086833, 0.14308825, 0.14393847, 0.14664934, 0.14804355,
                               0.14892363, 0.15055838, 0.15097085, 0.15409871, 0.15516216]),
                     np.array([0.02104651, 0.03919003, 0.04724104, 0.05494644, 0.06290493,
                               0.07031784, 0.07496161, 0.07956153, 0.08356809, 0.08697792,
                               0.0913731, 0.09417241, 0.09699998, 0.10092451, 0.10340344,
                               0.10711787, 0.1096748, 0.11151794, 0.11484896, 0.11765569,
                               0.12059403, 0.12342986, 0.12464453, 0.12662809, 0.12855005,
                               0.13135516, 0.13280989, 0.13443131, 0.13763338, 0.13927827,
                               0.1406853, 0.14289964, 0.14370643, 0.14554851, 0.14529921,
                               0.14823558, 0.15058108, 0.15022587, 0.15218993, 0.15362771])]
    rudi_utillist = [np.array([0.00592904, 0.00418302, 0.00634326, 0.00764617, 0.00908217,
                               0.010689, 0.01221645, 0.01332686, 0.01500069, 0.01600048,
                               0.01729633, 0.01896349, 0.02036388, 0.0217542, 0.02299005,
                               0.02435636, 0.02964544, 0.02805402, 0.02907389, 0.03460694,
                               0.03271205, 0.03740925, 0.03556156, 0.03769725, 0.03901393,
                               0.04095898, 0.04302215, 0.04503518, 0.04611126, 0.04827051,
                               0.05050588, 0.05263409, 0.0531344, 0.05549862, 0.05665526,
                               0.05885047, 0.06109977, 0.06215455, 0.06701077, 0.06552782]),
                     np.array([0.00694586, 0.00279358, 0.00416905, 0.00554578, 0.0063777,
                               0.00767235, 0.00891596, 0.01010921, 0.0111275, 0.01253385,
                               0.01389775, 0.01468506, 0.01629588, 0.01728261, 0.01909634,
                               0.01985745, 0.02552302, 0.02261479, 0.02417485, 0.02898049,
                               0.0269803, 0.03269441, 0.03029667, 0.03175096, 0.03301152,
                               0.03404298, 0.03664335, 0.03815271, 0.04021758, 0.04138837,
                               0.04302354, 0.04484734, 0.04622785, 0.0472827, 0.05015989,
                               0.05045147, 0.05252364, 0.05434396, 0.05974822, 0.05848724]),
                     np.array([0.00461086, 0.00384497, 0.00554389, 0.00705809, 0.00828575,
                               0.00921552, 0.01040475, 0.01199432, 0.01320823, 0.01464502,
                               0.01562525, 0.01688675, 0.0186291, 0.01977712, 0.02058289,
                               0.02217214, 0.02692035, 0.0254793, 0.02745764, 0.03254391,
                               0.03071939, 0.03548135, 0.03413378, 0.03548403, 0.03744606,
                               0.03772309, 0.04067221, 0.04187363, 0.04379567, 0.04494479,
                               0.04694609, 0.04927933, 0.05075456, 0.05206539, 0.05482818,
                               0.05537164, 0.05783975, 0.05873665, 0.06313941, 0.06187772]),
                     np.array([0.00763499, 0.00246421, 0.00378872, 0.00457872, 0.00614876,
                               0.00685967, 0.00817996, 0.00944489, 0.01063237, 0.0120274,
                               0.0131469, 0.01424402, 0.01587989, 0.01671808, 0.01753638,
                               0.01944326, 0.02466656, 0.02185225, 0.02321271, 0.0285509,
                               0.02673051, 0.0331634, 0.03017542, 0.03101633, 0.03231672,
                               0.03470929, 0.03543255, 0.03775326, 0.0390266, 0.0412813,
                               0.04286953, 0.04444233, 0.04649168, 0.04747674, 0.04924038,
                               0.0508214, 0.05290599, 0.05439339, 0.06031112, 0.0575003]),
                     np.array([0.00602332, 0.00451044, 0.00665905, 0.00835994, 0.0099727,
                               0.01124371, 0.01291957, 0.01463127, 0.01570543, 0.01723665,
                               0.01837455, 0.02034364, 0.02106383, 0.02223824, 0.02414705,
                               0.02564654, 0.03017238, 0.02890664, 0.03040098, 0.03463143,
                               0.03297644, 0.03834997, 0.03698688, 0.03730653, 0.03986618,
                               0.04110855, 0.04285007, 0.04518375, 0.04672349, 0.04833095,
                               0.0504122, 0.05267026, 0.05387019, 0.05561619, 0.05724393,
                               0.05909958, 0.06073187, 0.06206293, 0.06809557, 0.06513665])]

    # Size of dashes for unexplored nodes
    dshSz = 2
    # Size of figure layout
    figtup = (7, 5)
    titleSz, axSz, labelSz = 12, 10, 9
    xMax = 450

    avgHeurMat = np.average(np.array(heurlist), axis=0)

    # Plot of marginal utilities
    colors = cm.rainbow(np.linspace(0, 1., numTN))
    labels = [tnNames[ind] for ind in range(numTN)]

    x = range(testInt, testMax + 1, testInt)
    deltaArr = np.zeros((avgHeurMat.shape[0], avgHeurMat.shape[1] - 1))
    for rw in range(deltaArr.shape[0]):
        for col in range(deltaArr.shape[1]):
            deltaArr[rw, col] = avgHeurMat[rw, col + 1] - avgHeurMat[rw, col]
    yMax = np.max(deltaArr) * 1.1

    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        if tnind < 4:
            plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6)
        else:
            plt.plot(x, deltaArr[tnind], linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6, dashes=[1, dshSz])
    adj = 0.0002
    for tnind in range(numTN):
        if tnind == 0:
            plt.text(testInt * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 1:
            plt.text(testInt * 1.1, deltaArr[tnind, 0] + 2 * adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 3:
            plt.text(testInt * 1.1, deltaArr[tnind, 0] + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 2:
            plt.text(testInt * 1.1, deltaArr[tnind, 0] - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        else:
            plt.text(testInt * 1.1, deltaArr[tnind, 0], labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., yMax])
    plt.xlim([0., xMax])
    plt.xlabel('Number of Tests', fontsize=axSz)
    plt.ylabel('Marginal Utility Gain', fontsize=axSz)
    plt.title('Marginal Utility with Increasing Tests\nExploratory Setting with Market Term', fontsize=titleSz)
    plt.show()
    plt.close()

    # Allocation plot
    allocArr, objValArr = sampf.smooth_alloc_forward(avgHeurMat)
    # average distance from uniform allocation
    # np.linalg.norm(allocArr[:,-1]-np.ones((8))*4)

    colors = cm.rainbow(np.linspace(0, 1., numTN))
    labels = [tnNames[ind] for ind in range(numTN)]
    x = range(testInt, testMax + 1, testInt)
    _ = plt.figure(figsize=figtup)
    for tnind in range(numTN):
        if tnind < 4:
            plt.plot(x, allocArr[tnind] * testInt, linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6)
        else:
            plt.plot(x, allocArr[tnind] * testInt, linewidth=2, color=colors[tnind],
                     label=labels[tnind], alpha=0.6, dashes=[1, dshSz])
    # allocMax = allocArr.max() * testInt * 1.1
    allocMax = 185
    adj = 2.5
    for tnind in range(numTN):
        if tnind == 7:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 6:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 1:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt - adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        elif tnind == 3:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt + adj, labels[tnind].ljust(15), fontsize=labelSz - 1)
        else:
            plt.text(testMax * 1.01, allocArr[tnind, -1] * testInt, labels[tnind].ljust(15), fontsize=labelSz - 1)
    plt.legend(fontsize=labelSz)
    plt.ylim([0., allocMax])
    plt.xlim([0., xMax])
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Test Node Allocation', fontsize=axSz)
    plt.title('Sampling Plan vs. Budget\nExploratory Setting with Market Term', fontsize=titleSz)
    # plt.tight_layout()
    plt.show()
    plt.close()

    # Utility comparison plot
    colors = cm.rainbow(np.linspace(0, 0.8, 3))
    labels = ['Heuristic', 'Uniform', 'Rudimentary']
    x = range(testInt, testMax + 1, testInt)
    margUtilGroupList = [heur_utillist, unif_utillist, rudi_utillist]
    utilMax = -1
    for lst in margUtilGroupList:
        currMax = np.amax(np.array(lst))
        if currMax > utilMax:
            utilMax = currMax
    utilMax = utilMax * 1.1

    _ = plt.figure(figsize=figtup)
    for groupInd, margUtilGroup in enumerate(margUtilGroupList):
        groupArr = np.array(margUtilGroup)
        groupAvgArr = np.average(groupArr, axis=0)
        # Compile error bars
        stdevs = [np.std(groupArr[:, i]) for i in range(groupArr.shape[1])]
        group05Arr = [groupAvgArr[i] - (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        group95Arr = [groupAvgArr[i] + (1.96 * stdevs[i] / np.sqrt(groupArr.shape[0])) for i in
                      range(groupArr.shape[1])]
        plt.plot(x, groupAvgArr, color=colors[groupInd], linewidth=0.7, alpha=1., label=labels[groupInd] + ' 95% CI')
        plt.fill_between(x, groupAvgArr, group05Arr, color=colors[groupInd], alpha=0.2)
        plt.fill_between(x, groupAvgArr, group95Arr, color=colors[groupInd], alpha=0.2)
        # Line label
        plt.text(x[-1] * 1.01, groupAvgArr[-1], labels[groupInd].ljust(15), fontsize=labelSz - 1)
    plt.ylim(0, utilMax)
    # plt.xlim(0,x[-1]*1.12)
    plt.xlim([0., xMax])
    leg = plt.legend(loc='upper left', fontsize=labelSz)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(1.0)
    plt.xlabel('Sampling Budget', fontsize=axSz)
    plt.ylabel('Plan Utility', fontsize=axSz)
    plt.title('Utility from Heuristic vs. Uniform and Rudimentary Allocations\nExploratory Setting with Market Term',
              fontsize=titleSz)
    # Add text box showing budgetary savings
    compUtilAvg = np.average(np.array(heur_utillist), axis=0)
    x2, x3 = 134, 332
    plt.plot([100, x2], [compUtilAvg[9], compUtilAvg[9]], color='black', linestyle='--')
    iv = 0.003
    plt.plot([100, 100], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    plt.plot([x2, x2], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    # plt.plot([x3, x3], [compUtilAvg[9] - iv, compUtilAvg[9] + iv], color='black', linestyle='--')
    plt.text(110, compUtilAvg[9] + iv / 2, str(x2 - 100), fontsize=labelSz)
    # plt.text(205, compUtilAvg[9] + iv/2, str(x3-x2), fontsize=labelSz)

    # plt.tight_layout()
    plt.show()
    plt.close()

    '''
    Determining the budget saved for the sensitivity table
    currCompInd = 8
    compUtilAvg = np.average(np.array(compUtilList),axis=0) 
    evenUtilArr = np.array(evenUtilList)
    evenAvgArr = np.average(evenUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(evenAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    evenSampSaved = round((compUtilAvg[currCompInd] - evenAvgArr[kInd - 1]) / (evenAvgArr[kInd] - evenAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(evenSampSaved)
    rudiUtilArr = np.array(origUtilList)
    rudiAvgArr = np.average(rudiUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(rudiAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    rudiSampSaved = round((compUtilAvg[currCompInd] - rudiAvgArr[kInd - 1]) / (rudiAvgArr[kInd] - rudiAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(rudiSampSaved)
    currCompInd = 17
    compUtilAvg = np.average(np.array(compUtilList),axis=0) 
    evenUtilArr = np.array(evenUtilList)
    evenAvgArr = np.average(evenUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(evenAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    evenSampSaved = round((compUtilAvg[currCompInd] - evenAvgArr[kInd - 1]) / (evenAvgArr[kInd] - evenAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(evenSampSaved)
    rudiUtilArr = np.array(origUtilList)
    rudiAvgArr = np.average(rudiUtilArr, axis=0)
    kInd = next(x for x, val in enumerate(rudiAvgArr.tolist()) if val > compUtilAvg[currCompInd])
    rudiSampSaved = round((compUtilAvg[currCompInd] - rudiAvgArr[kInd - 1]) / (rudiAvgArr[kInd] - rudiAvgArr[kInd - 1]) * testInt) + (
                kInd - 1) * testInt - (currCompInd*testInt)
    print(rudiSampSaved)
    '''

    return


def caseStudyPlots_Familiar_Bootstrap_Example():
    """
    Use 50 sets of marginal utility curves in the Familiar setting to show allocations are robust
        under a given number of separate runs
    """
    # Load stored file
    margUtilSet = np.load(os.path.join('casestudyoutputs', 'PREVIOUS', 'STUDY_bootstrap_utilmatrices',
                                       'margutilset.npy'))

    numSets = len(margUtilSet)
    numBoot = 50
    numTN = margUtilSet[0].shape[0]
    testInt, testMax = 10, 400
    xRange = np.arange(testInt, testMax + 1, testInt)
    # Generate numBoot bootstrap sets for different sizes and examine the resulting allocations at each node
    setSize = [5, 10, 15, 20]
    np.random.seed(101)
    setAllocList = []
    for currSetSize in setSize:
        currSetAllocList = []
        for bootInd in range(numBoot):
            randInds = choice(np.arange(numSets), currSetSize, replace=False).tolist()
            bootUtilList = [margUtilSet[randInds[i]] for i in range(currSetSize)]
            # Take average and get allocation
            bootAvgMat = np.average(np.array(bootUtilList), axis=0)
            allocArr, _ = sampf.smooth_alloc_forward(bootAvgMat)
            currSetAllocList.append(allocArr)
        setAllocList.append(currSetAllocList)
        # Plot allocations
        colors = cm.rainbow(np.linspace(0, 0.5, numTN))
        for bootInd in range(numBoot):
            for tnInd in range(numTN):
                if bootInd == 0:
                    plt.plot(xRange, currSetAllocList[bootInd][tnInd] * testInt, label='TN ' + str(tnInd),
                             color=colors[tnInd],
                             alpha=0.3, linewidth=1.)
                else:
                    plt.plot(xRange, currSetAllocList[bootInd][tnInd] * testInt, color=colors[tnInd], alpha=0.5,
                             linewidth=1.)
        plt.title('Allocations under average of ' + str(currSetSize) + ' generated utility curves\n' + str(
            numBoot) + ' bootstrap samples')
        plt.ylim([0., 180])
        plt.legend()
        plt.show()
        plt.close()
    # What is range of utilities for each number of bootstrap samples at 'messiest' alloction point?
    sampBudget = 200  # Looks to be biggest allocation
    setUtilList = [[] for i in setSize]
    for newChain in range(10):
        pass
    '''1-MAY runs
    setUtilList = 
    '''

    return

