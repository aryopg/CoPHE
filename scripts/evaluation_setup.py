import numpy as np
from scipy.sparse import csr_matrix


def setup_matrices_by_layer(code_ids, translation_dict, max_layer = 1, include_duplicates = True):
    """
    Sets up the transition matrices and ID dictionaries for each layer of the ontology up to a maximum value (from the bottom up).
    sample_code_ids - a dictionary mapping IDs in the output layer to codes
    translation_dict - a dictionary containing the codes' ordered parent list (coming from the .json file provided in the ICD9 folder)
    max_layer - integer maximum layer of the ontology (from the bottom up) up to which the hierarchical evaluation is applied
    include_duplicates - boolean, default = True; maintains duplication across lower layers if a leaf is not present in the lowest layer (results in presence of all leafs in all layers)
    returns a tuple:
        matrices - a list of transition matrices from the leaves to each layer of the ontology up to max_layer (from bottom up)
        layer_id_dicts - a list of dictionaries of code IDs in vectors for each layer of the ontology up to max_layer (from the bottom up)
    """
    matrices = [] # tranlsation matrices per layer
    layer_id_dicts = [] # id-to-code dictionary per layer
    for layer in range(max_layer):
        rows, cols, vals = [], [], [] # setup for a sparse matrix
        layer_codeset = set() # codeset for ancestors - in order to remove duplicates for layer representation
        for code in code_ids:
            layer_codeset.add(translation_dict[code]["parents"][layer]) # collection of relevant ancestors in the layer
            
        layer_ranges = list(range(len(layer_codeset)))
        layer_id_dict = dict(zip(list(layer_codeset), layer_ranges)) # association of IDs with relevant acestors in the layer
        
        for code in code_ids:
            rows.append(code_ids[code])  # row number (current code)
            ancestor = translation_dict[code]["parents"][layer]
            cols.append(layer_id_dict[ancestor]) # col number (ancestor)
            if include_duplicates or layer == max_layer-2:  # if duplicates are allowed or the next layer is the final layer, create an edge
                vals.append(1)
            else:  # otherwise observe the ancestor of the ancestor - if this matches the current code, do not create an edge. Otherwise create an edge.
                double_ancestor = translation_dict[ancestor]["parents"][layer]  
                duplicate_ancestor = double_ancestor == code
                vals.append(not(duplicate_ancestor)*1)

        matrix = csr_matrix((vals, (rows, cols)), shape=((len(rows)), (len(set(cols))))) # set up the sparse matrix
        
        matrices.append(matrix) # append the matrix for this layer
        layer_id_dicts.append(layer_id_dict) # append the id dictionary for this layer
    return matrices, layer_id_dicts 

def low_level_diagonal(matrix):
    """
    Creates a diagonal matrix from the input. Intended as a filter for the lowest level of the ontology
    """
    bin_vector = np.sum(matrix, axis = 1)
    return np.diag(bin_vector)
                
def hierarchical_eval_setup(preds, golds, layer_matrices, max_onto_layers):
    """
    inputs:
      preds - a numpy array, a matrix of predictions
      golds - a numpy array, a matrix of true labels
      layer_matrices - a list of numpy arrays translating the leaf nodes into layers of the ontology
      max_onto_layers - an integer describing the maximum layer (from the bottom up) within the ontology to be evaluated on
    """
    
    # isolation of leaves appearing at the lowest level
    lowest_layer_filter = low_level_diagonal(layer_matrices[0]) 
    combined_preds = [preds*lowest_layer_filter]
    combined_golds = [golds*lowest_layer_filter]
    
    # handling further layers
    for i in range(max_onto_layers):
        translation_matrix = layer_matrices[i] # layer matrix retrieval
        translated_preds, translated_golds = preds*translation_matrix, golds*translation_matrix # translation from flat predictions into the layer
        combined_preds.append(translated_preds)
        combined_golds.append(translated_golds)
    
    # concatenation between layers for predictions and true labels respectively
    combined_preds = np.concatenate(combined_preds, 1)
    combined_golds = np.concatenate(combined_golds, 1)
    
    return combined_preds, combined_golds
    
if __name__ == "__main__":
    print(f"Hierarchical Evaluation Setup Demonstration")
    print(f"Vectors correspond to leafs: \n(a.1, a.2, a.3, b.1, b.2, c.1, d.1, d.2, d.3)")
    print(f"Their corresponding parents are: \b (a, a, a, b, b, c, d, d, d)")
    
    code_ids = dict(zip(["a.1", "a.2", "a.3", "b.1", "b.2", "c.1", "d.1", "d.2", "d.3"], range(9)))
    translation_dict = dict({"a.1":dict({"parents":["a", "AB"]}), 
                             "a.2":dict({"parents":["a", "AB"]}), 
                             "a.3":dict({"parents":["a", "AB"]}), 
                             "b.1":dict({"parents":["b", "AB"]}), 
                             "b.2":dict({"parents":["b", "AB"]}), 
                             "c.1":dict({"parents":["c", "CD"]}), 
                             "d.1":dict({"parents":["d", "CD"]}), 
                             "d.2":dict({"parents":["d", "CD"]}), 
                             "d.3":dict({"parents":["d", "CD"]})})
    matrices, layer_id_dicts  = (setup_matrices_by_layer(code_ids, translation_dict, max_layer = 2))
    print("========TRANSLATION MATRICES========")
    print("Layer 0 to 1")
    print(matrices[0].toarray(), layer_id_dicts[0])
    print("====================================")
    print("Layer 1 to 2")
    print(matrices[1].toarray(), layer_id_dicts[1])


    sample_matrix = np.array([[0, 1, 1, 0, 1, 0, 0, 1, 0],  
                              [0, 1, 0, 0, 0, 1, 0, 1, 1],
                              [0, 1, 1, 1, 0, 0, 1, 0, 1],
                              [0, 0, 1, 1, 1, 0, 0, 1, 1],
                              [1, 1, 0, 1, 0, 0, 0, 1, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0, 0],
                              [1, 1, 1, 1, 1, 1, 1, 1, 1]])
                              
    print("========Sample Transitions========")
    print("Sample prediction Matrix:")
    print(sample_matrix)
    print("Layer 1")
    print((sample_matrix.dot(matrices[0].toarray())), layer_id_dicts[0])
    print("Layer 2")
    print((sample_matrix.dot(matrices[1].toarray())), layer_id_dicts[1])
    
    
    print("Sample gold standard Matrix:")
    sample_gold_matrix = np.array([[0, 0, 1, 0, 1, 0, 1, 1, 0],
                                   [0, 1, 0, 0, 0, 1, 0, 1, 1],
                                   [1, 0, 1, 1, 0, 1, 0, 1, 1],
                                   [0, 0, 1, 1, 1, 0, 0, 0, 0],
                                   [0, 0, 0, 0, 0, 0, 0, 0, 0],
                                   [0, 0, 1, 0, 0, 0, 1, 0, 0],
                                   [0, 0, 1, 1, 1, 0, 1, 1, 0]])
    print(sample_gold_matrix)
    print("========Overall Cross-Layer Evaluation Setup========")
    
    combined_preds, combined_golds = hierarchical_eval_setup(sample_matrix, sample_gold_matrix, matrices, 2)
    print("Combined prediction vectors across layers")
    print(combined_preds)
    print("Combined gold standard vectors across layers")
    print(combined_golds)
    print("With these combined predictions and gold standard labels across layers we can now apply the evaluation measures for the non-binary scenario in multi_level_eval.py")