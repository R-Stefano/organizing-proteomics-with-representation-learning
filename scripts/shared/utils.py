import numpy as np
import yaml
import time

with open('../../hyperparams.yml', 'r') as f:
    hyperparams=yaml.load(f)

sequence_aa=hyperparams['max_sequence_length']

batch_size=hyperparams['training']['batch_size']

stride=hyperparams['prepare_batch']['stride'] #window stride for generating sequence_length patches as input
padding=hyperparams['prepare_batch']['padding']
window_size=hyperparams['prepare_batch']['window_size'] # #window size for stride

sequence_length=hyperparams['CPC']['input_sequence_length'] #computed: ((in - w + 2p)/s)+1
num_predic_terms=hyperparams['CPC']['num_pred_terms']
num_samples=hyperparams['CPC']['num_samples'] #tot number of samples for each pred
num_samples_positive=hyperparams['CPC']['num_samples_pos']
encoding_length=hyperparams['CPC']['encoding_size'] #encoding_length=len(hyperparams['aminos'])

def prepareBatch(dataset):
    '''
    Batch comes in shape [batch_size, sequence_aa, 1].
    This function returns 2 tensors:
    -InputData: [batch_size, sequence_length, window_size, encoding_length]
    -targetData: [batch_size, sequence_length, num_predic_terms, num_samples,  window_size, encoding_length]
    -labels: [batch_size, sequence_length, num_predic_terms, num_samples,  1 (index of correct target)]
    '''

    while (True):
        time_s=time.time()
        batch_idxs=np.random.choice(len(dataset), batch_size, replace=False)
        batch=dataset[batch_idxs]

        #1. batch encoding
        #batch_encoded=np.zeros((batch_size, sequence_aa, encoding_length))
        #batch_encoded[:, :, batch[:,:]]=1
        batch_encoded=np.reshape(batch, (batch_size, sequence_aa, 1))

        #2. generate input data
        #padding
        if padding>0:
            pads=np.zeros((batch_size, padding, 1), dtype=np.int8)-1
            batch_encoded=np.concatenate((batch_encoded, pads), axis=1)
        inputData=np.zeros((batch_size, sequence_length, window_size, encoding_length), dtype=np.int8)-1
        for i in range(sequence_length):
            patch_start=i*stride
            patch=batch_encoded[:, patch_start: patch_start+window_size]
            inputData[:, i]=patch 

        targetData=np.zeros((batch_size, sequence_length, num_predic_terms, num_samples,  window_size, encoding_length), dtype=np.int8)-1
        labels=np.zeros((batch_size, sequence_length, num_predic_terms, num_samples), dtype=np.int8)
        #3. generate target data & labels
        for i in range(sequence_length):
            next_t=i
            #1. Random patches (negative examples)
            #Create a mask to avoid sample the true target data
            mask=np.zeros((batch_size, sequence_length), dtype=np.int8)
            mask[:, next_t: next_t+num_predic_terms]=1

            #sample the idxs of random target data 
            neg_idxs=np.argwhere(mask==0)
            idxs=np.random.randint(low=0, high=len(neg_idxs)-1, size=(batch_size*num_predic_terms*num_samples))

            #sample the random target data using the idxs
            neg_idxs=neg_idxs[idxs]
            b=neg_idxs[:, 0]
            t=neg_idxs[:, 1]
            step_targetData=np.reshape(inputData[b, t], (batch_size, 1, num_predic_terms, num_samples, window_size, encoding_length))
            
            #2. True patch
            pos_target=np.reshape(inputData[:, next_t: next_t+num_predic_terms], (batch_size, 1, -1, 1, window_size, encoding_length))# extract shifted data and adapt dimension
            #assign a random num_samples index to the positive examples (same across batch for paralle purposes)
            pos_idxs=np.random.randint(low=0, high=(num_samples-1), size=(num_predic_terms))
            #Reset position for positive example to avoid mixing..
            step_targetData[:, :, :, pos_idxs]=-1
            #update with positive example
            step_targetData[:, :, :pos_target.shape[2], pos_idxs]=pos_target

            #Save the positive of positive examples
            labels[:, i, :, pos_idxs]=1

            targetData[:, i]=step_targetData[:, 0]
        print('Preparing batch in {}s'.format(time.time()-time_s))
        yield [inputData, targetData], labels