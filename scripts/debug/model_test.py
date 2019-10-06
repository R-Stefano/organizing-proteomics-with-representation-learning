import yaml
import sys
import numpy as np
import tensorflow as tf
with open('../../hyperparams.yml', 'r') as f:
    hyperparams=yaml.load(f)

data_dir=hyperparams['data_dir']

sys.path.append(hyperparams['shared_scripts'])
import Transformer as model_wrapper 

#np.random.seed(0)
tf.random.set_seed(0)

batch_size=20
sequence_length=512

inputData=np.load(data_dir+'dataset/unsupervised/training_90.npy')[:batch_size]
evaluationData=np.load(data_dir+'dataset/unsupervised/evaluation.npy')[:batch_size]

model_utils=model_wrapper.Model(hyperparams['models_dir'],'test')
model=model_utils.architecture()
model_dir=model_utils.dir

#model_utils.exportModel(model)
#print(model.predict(inputData).shape)

train_generator=model_utils.BatchGenerator(inputData, batch_size)
test_generator=model_utils.BatchGenerator(evaluationData, batch_size)
'''
for batch in train_generator:
    x=batch[0]
    y=batch[1]
    test=batch[2]
    print('Original oinput:')
    print(test[0][:30])
    print('Input:')
    print(x[0][:30])
    print('Labels:')
    print(y[0][:30])
    break
'''
model.fit_generator(
    generator=train_generator,
    validation_data=test_generator,
    epochs=100,
    verbose=1
)