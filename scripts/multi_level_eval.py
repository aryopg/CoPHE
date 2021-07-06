import pandas as pd
from scipy.sparse import csr_matrix
import numpy as np


import logging

def tp_matrix_mul(pred, gold, axes):
    """
    Calculation of True Positives in non-binary setting.
    On the ancestor levels leaf-level mismatches do not matter. If an ancestor-prediction has an ancestor-gold counterpart, it is considered a TP. Hence, the overall TP for an ancestor is the minimum of the count of the predicted ancestor and the count of the gold standard ancestor.
    inputs
      pred: numpy array of predictions
      gold: numpy array of true labels
      axes: axes on which summing is to be performed (all dimensions for overall TP)
    returns integer if axes represent all dimensions, a vector of integers otherwise 
    """
    return np.sum(np.minimum(pred, gold), axis=axes)

def fp_matrix_mul(pred, gold, axes):
    """
    Calculation of False Positives in non-binary setting.
    If an ancestor-prediction does not have an ancestor-gold counterpart, it is considered a FP. Hence, the overall FP for an ancestor represents how many more times the ancestor has been predicted in a document compared to how many times it appears in the gold standard.
    inputs
      pred: numpy array of predictions
      gold: numpy array of true labels
      axes: axes on which summing is to be performed (all dimensions for overall FP)
    returns integer if axes represent all dimensions, a vector of integers otherwise 
    """
    return np.sum(np.maximum(pred - gold, 0), axis=axes)

def fn_matrix_mul(pred, gold, axes):
    """
    Calculation of False Negatives in non-binary setting.
    If an ancestor-gold does not have an ancestor-prediction counterpart, it is considered a FN. Hence, the overall FN for an ancestor represents how many more times the ancestor appears in a document compared to how many times it was predicted for the document.
    inputs
      pred: numpy array of predictions
      gold: numpy array of true labels
      axes: axes on which summing is to be performed (all dimensions for overall FN)
    returns integer if axes represent all dimensions, a vector of integers otherwise 
    """
    return np.sum(np.maximum(gold - pred, 0), axis=axes)
    
    
def tp_matrix_mul_full(pred, gold, axes = (0,1)):
    """
    Overall TP for a non-binary 2d matrix
    returns integer
    """
    return tp_matrix_mul(pred, gold, axes)
    
def fp_matrix_mul_full(pred, gold, axes = (0,1)):
    """
    Overall FP for a non-binary 2d matrix
    returns integer
    """
    return fp_matrix_mul(pred, gold, axes)
    
def fn_matrix_mul_full(pred, gold, axes = (0,1)):
    """
    Overall FN for a non-binary 2d matrix
    returns integer
    """
    return fn_matrix_mul(pred, gold, axes)
    
    
def tp_matrix_mul_per_class(pred, gold, axes = 0):
    """
    per-class TP for a non-binary 2d matrix
    returns 1d np.array
    """
    return tp_matrix_mul(pred, gold, axes)
    
def fp_matrix_mul_per_class(pred, gold, axes = 0):
    """
    per-class FP for a non-binary 2d matrix
    returns 1d np.array
    """
    return fp_matrix_mul(pred, gold, axes)
    
def fn_matrix_mul_per_class(pred, gold, axes = 0):
    """
    per-class FN for a non-binary 2d matrix
    returns 1d np.array
    """
    return fn_matrix_mul(pred, gold, axes)

def report(pred, gold, code_id_dict):
    """
    Creates a per-class dataframe report.
    This includes the Precision, Recall, F1 score, Support in the evaluation set, and the code itself.
    inputs:
        pred          2d np.array prediction matrix
        gold          2d np.array matrix of gold standard labels
        code_id_dict  dictionary mapping codes to their ID in the prediction/gold vectors
    returns Pandas DataFrame
    """
    
    # Calculation of TP/FP/FN per class
    tp = tp_matrix_mul_per_class(pred, gold)
    fp = fp_matrix_mul_per_class(pred, gold)
    fn = fn_matrix_mul_per_class(pred, gold)
    
    # Calculation of the support within the evaluation set
    support = np.sum(gold, axis = 0)
    
    
    # Precision
    prec_denom = tp+fp
    prec_denom_corrected = prec_denom + (prec_denom == 0)*1
    prec = tp/prec_denom_corrected
    
    # Recall
    rec_denom = tp+fn
    rec_denom_corrected = rec_denom + (rec_denom == 0)*1
    rec = tp/(rec_denom_corrected)
    
    # F1 score
    f1_denom = prec+rec
    f1_denom_corrected = f1_denom+((f1_denom == 0)*1)
    f1 = 2*(prec*rec)/(f1_denom_corrected)
    
    # matchin codes
    code_ids = sorted(code_id_dict)
    codes = [code_id_dict[k] for k in code_ids]
    
    df = pd.DataFrame(list(zip(prec, rec, f1, support, codes)),
                                              columns =['Precision', "Recall", "F1", "Support", "Code"])
    return df

def report_micro(pred, gold):
    """
    Creates an overall report on the micro lvel.
    This includes the micro Precision, Recall, F1 score.
    inputs:
        pred          2d np.array prediction matrix
        gold          2d np.array matrix of gold standard labels
        code_id_dict  dictionary mapping codes to their ID in the prediction/gold vectors
    returns a dictionary with real values for "Precision", "Recall", and "F1"
    """
    tp = tp_matrix_mul_full(pred, gold)
    fp = fp_matrix_mul_full(pred, gold)
    fn = fn_matrix_mul_full(pred, gold)
    
    prec_denom = tp+fp
    prec_denom_corrected = prec_denom + (prec_denom == 0)*1
    prec_micro = tp/prec_denom_corrected
    
    rec_denom = tp+fn
    rec_denom_corrected = rec_denom + (rec_denom == 0)*1
    rec_micro = tp/(rec_denom_corrected)
    
    f1_denom = prec_micro+rec_micro
    f1_denom_corrected = f1_denom+((f1_denom == 0)*1)
    f1 = 2*(prec_micro*rec_micro)/(f1_denom_corrected)
    
    report_dict = dict({"Precision":prec_micro, "Recall":rec_micro,"F1":f1})
    
    return report_dict
    
def report_macro(pred, gold):
    """
    Creates an overall report on the macro lvel.
    This includes the macro Precision, Recall, F1 score.
    inputs:
        pred          2d np.array prediction matrix
        gold          2d np.array matrix of gold standard labels
        code_id_dict  dictionary mapping codes to their ID in the prediction/gold vectors
    returns a dictionary with real values for "Precision", "Recall", and "F1"
    """
    tp = tp_matrix_mul_per_class(pred, gold)
    fp = fp_matrix_mul_per_class(pred, gold)
    fn = fn_matrix_mul_per_class(pred, gold)
    
    prec_denom = tp+fp
    prec_denom_corrected = prec_denom + (prec_denom == 0)*1
    prec = tp/prec_denom_corrected
    prec_macro = np.average(prec, axis = 0)
    
    rec_denom = tp+fn
    rec_denom_corrected = rec_denom + (rec_denom == 0)*1
    rec = tp/(rec_denom_corrected)
    rec_macro = np.average(rec, axis = 0)
    
    f1_denom = prec_macro+rec_macro
    f1_denom_corrected = f1_denom+((f1_denom == 0)*1)
    f1 = 2*(prec_macro*rec_macro)/(f1_denom_corrected)
    report_dict = dict({"Precision":prec_macro, "Recall":rec_macro,"F1":f1})
    
    return report_dict

def report_macro_bin(pred, gold):
    """
    binarised version of report_macro - the prediction and gold matrix are set to binary, where positive entries are set to 1.
    return report_macro on these binarised inputs
    """
    pred_bin = (pred>0)*1
    gold_bin = (gold>0)*1
    return report_macro(pred_bin, gold_bin)

def report_micro_bin(pred, gold):
    """
    binarised version of report_micro - the prediction and gold matrix are set to binary, where positive entries are set to 1.
    return report_micro on these binarised inputs
    """
    pred_bin = (pred>0)*1
    gold_bin = (gold>0)*1
    return report_micro(pred_bin, gold_bin)

def report_bin(pred, gold):
    """
    Creates a per-class dataframe report on binarised inputs.
    """
    pred_bin = (pred>0)*1
    gold_bin = (gold>0)*1
    return report(pred_bin, gold_bin)

if __name__ == "__main__":
    print(f"Hierarchical Evaluation Demonstration")
    print(f"Vectors correspond to leafs: \n(a.1, a.2, a.3, b.1, b.2, c.1, d)")
    print(f"Their corresponding level 1 are: \b (a, a, a, b, b, c, d)")
    
    leaf_dict = dict(zip(range(7), ["a.1", "a.2", "a.3", "b.1", "b.2", "c.1", "d"]))
    print ("Gold Standard")
    gold_matrix = np.array([[0, 0, 1, 0, 1, 0, 1],
                            [0, 1, 0, 0, 0, 1, 0],
                            [1, 0, 1, 1, 0, 1, 0],
                            [0, 0, 1, 1, 1, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0, 1],
                            [0, 0, 1, 1, 1, 0, 1]])# sample matrix gold standard
    print(gold_matrix)


    print ("Prediction")
    pred_matrix = np.array([[0, 1, 1, 0, 1, 0, 0],  
                            [0, 1, 0, 0, 0, 1, 0],
                            [0, 1, 1, 1, 0, 0, 1],
                            [0, 0, 1, 1, 1, 0, 0],
                            [1, 1, 0, 1, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [1, 1, 1, 1, 1, 1, 1]])# sample matrix prediction
    print(pred_matrix)
                            
    test_tp_mul = tp_matrix_mul_per_class(pred_matrix, gold_matrix)
    test_fp_mul = fp_matrix_mul_per_class(pred_matrix, gold_matrix)
    test_fn_mul = fn_matrix_mul_per_class(pred_matrix, gold_matrix)
    
    print(f"TP: {test_tp_mul} FP: {test_fp_mul} FN:{test_fn_mul}")
    
    print(report(pred_matrix, gold_matrix, leaf_dict))
    
    print("============================================")
    print("=============PARENT-LEVEL===================")
    print("============================================")
    
    child_to_parent_matrix = np.array([[1,0,0,0],
                                   [1,0,0,0],
                                   [1,0,0,0],
                                   [0,1,0,0],
                                   [0,1,0,0],
                                   [0,0,1,0],
                                   [0,0,0,1]])
    
    parent_pred_matrix = pred_matrix.dot(child_to_parent_matrix)
    parent_gold_matrix = gold_matrix.dot(child_to_parent_matrix)
    
    parent_dict = dict(zip(range(4), ["a", "b", "c", "d"]))
    
    print("Parent-Translated Gold Standard")
    print(parent_gold_matrix)
    print("Parent-Translated Prediction")
    print(parent_pred_matrix)
    
    print(report(parent_pred_matrix, parent_gold_matrix, parent_dict))
