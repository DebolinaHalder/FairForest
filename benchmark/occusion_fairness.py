#%%
import numpy as np
import pandas as pd
from scipy.special import logit
from fairforest import d_tree, random_tree
from fairforest import utils
import warnings
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
#%%
warnings.simplefilter("ignore")

#%%
np.random.seed(10)

#%%
def build_dataset(total_sample,number_of_correlated_features,number_of_important_features,number_of_uncorrelated_features,mean_correlated_0,mean_correlated_1,mean_imp_0,mean_imp_1):
    mid = int(total_sample/2)
    z0_prob = 0.3
    z1_prob = 0.65
    z = np.ones(total_sample)
    x_correlated = np.zeros((total_sample,number_of_correlated_features))
    x_important = np.zeros((total_sample,number_of_important_features))
    
    var_0 = var_1 = 1
    #y1z1 = np.ones(650)
    #y1z0 = np.zeros(350)
    #y0z1 = np.ones(300)
    #y0z0 = np.zeros(700)
    #z = np.concatenate((y1z1,y1z0,y0z1,y0z0))
    y = np.zeros(total_sample)
    for i in range (mid):
        y[i] = 1
        z[i] = np.random.binomial(1, z1_prob)
        if z[i] == 1:
            for j in range (number_of_correlated_features):
                x_correlated[i][j] = np.random.normal(mean_correlated_1[j], 1)
        else:
            for j in range (number_of_correlated_features):
                x_correlated[i][j] = np.random.normal(mean_correlated_0[j], 1)
        for k in range(number_of_important_features):
            x_important[i][k] = np.random.normal(mean_imp_1[k], 1)


    for i in range (mid):
        z[mid+i] = np.random.binomial(1, z0_prob)
        if z[mid+i] == 0:
            for j in range (number_of_correlated_features):
                x_correlated[mid+i][j] =  np.random.normal(mean_correlated_0[j], 1)
        else:
            for j in range (number_of_correlated_features):
                x_correlated[mid+i][j] = np.random.normal(mean_correlated_1[j], 1)
        for k in range(number_of_important_features):
            x_important[mid+i][k] = np.random.normal(mean_imp_0[k], 1)
    #x_unimportant =  np.random.multivariate_normal(uncorr_sample_mean, uncorr_sample_cov, size=total_sample)
    x = np.concatenate((x_correlated,x_important),axis = 1)
    x = np.concatenate((x,np.reshape(z,(-1,1))),axis = 1)
    #np.random.shuffle(x)



    count_z0 = count_z1 = 0
    count0 = count1 = 0
    z0 = z1 = 0
    for i in range (total_sample):
        if y[i] == 0:
            count0+=1
        else:
            count1+=1
            if x[i][total_feature-1] == 0:
                count_z0 += 1
            else:
                count_z1 +=1
        if x[i][total_feature-1] == 0:
            z0+=1
        else:
            z1+=1
    print(count0,count1, count_z0,count_z1,z0,z1)

    total_features = number_of_correlated_features+number_of_important_features+1
    column = []
    for i in range(total_features):
        column.append(str(i+1))
    print(column)
    dataframe = pd.DataFrame(x, columns = column)
    return dataframe,y
#%%
total_sample = 5500
number_of_correlated_features = 3
number_of_important_features = 5
number_of_uncorrelated_features = 0
total_feature = number_of_important_features+number_of_correlated_features+1
feature = np.arange(number_of_important_features+number_of_correlated_features+1)
score_fairness = np.zeros(number_of_important_features+number_of_correlated_features+1)
occlusion_fairness = np.zeros(total_feature)
score_feature = np.zeros(number_of_important_features+number_of_correlated_features+1)
mean_correlated_1 = [20, 20, 20]
mean_correlated_0 = [11, 9, 7]
mean_imp_1 = [0,4,8,12,16]
mean_imp_0 = [-1,3,7,11,15]

for i in range (1):
    dataframe, y = build_dataset(total_sample,number_of_correlated_features,number_of_important_features,number_of_uncorrelated_features,mean_correlated_0,mean_correlated_1,mean_imp_0,mean_imp_1)
    #####protected_attribute,protected_value,protected_feature,fairness_metric
    model_dtree = d_tree.DecisionTree(total_feature - 1,0,str(total_feature),2)
    model_dtree.fit(dataframe.copy(),y)
    sklearn_dataframe = dataframe.copy().drop(columns=[str(total_feature)])
    
    testX,testy = build_dataset(5000,number_of_correlated_features,number_of_important_features,number_of_uncorrelated_features,mean_correlated_0,mean_correlated_1,mean_imp_0,mean_imp_1)
    testX_without_protected_all = testX.copy().drop(columns=str(total_feature))
    sklearn_tree_all = RandomForestClassifier()
    sklearn_tree_all.fit(sklearn_dataframe,y)
    pred_all = sklearn_tree_all.predict(testX_without_protected_all)
    fairness_all = utils.DP(testX.to_numpy(),pred_all,testy,total_feature-1,0)
    for j in range (total_feature - 1):
        #print(j+1)
        train_data = sklearn_dataframe.copy().drop(columns=[str(j+1)])
        sklearn_tree= RandomForestClassifier()
        sklearn_tree.fit(train_data,y)
        
        testX_without_protected = testX.copy().drop(columns=[str(total_feature),str(j+1)])
        prediction = sklearn_tree.predict(testX_without_protected)

        occlusion_fairness[j] += (fairness_all - utils.DP(testX.to_numpy(),prediction,testy,total_feature-1,0))
    fairness_importance = model_dtree._fairness_importance()
    feature_importance = model_dtree._feature_importance()
    for key, value in fairness_importance.items():
        score_fairness[int(key)-1] += value
    for key, value in feature_importance.items():
        score_feature[int(key)-1] += value
for i in range (total_feature):
    score_fairness[i] /= 1
    score_feature[i] /= 1
    occlusion_fairness[i] /= 1

with open('Results/Synthetic/no_corr/result_eqoptest_g.txt', 'a') as f:
    f.writelines(str(score_fairness))
    f.writelines("\n")
    f.writelines(str(score_feature))

with open('Results/Synthetic/no_corr/result_occlusion_eqop_test_g.txt', 'a') as f:
    f.writelines(str(occlusion_fairness))
#%%
utils.draw_plot(feature,score_fairness,"Results/Synthetic/no_corr/eqop_fairness_test_g.pdf","Fairness Importance")
utils.draw_plot(feature,occlusion_fairness,"Results/Synthetic/no_corr/eqop_fairness_occlusion_test_g.pdf","Fairness")
utils.draw_plot(feature,score_feature,"Results/Synthetic/no_corr/eqop_feature_test_g.pdf","Accuracy Importance")




 # %%

# %%
print(occlusion_fairness)

# %%
