
# import your functions here


# format: <visible_algorithm_name, function>


from tensorflow.keras.models import load_model
import numpy as np


SNATCHED_MODEL = load_model('best_model.h5')
OUTPUT_SIZE = 32

def DeepLearning(t1, t2):
    result = SNATCHED_MODEL(inputs=[np.array([t1]), np.array([t2])])
    output = np.asarray(result[0])
    output = np.round(output) * 255
    return output.reshape((OUTPUT_SIZE, OUTPUT_SIZE))


algorithms = {
    'Algorithm 1': DeepLearning,
    'Algorithm 2': (lambda: print('Algorithm 2 works')),
    'Algorithm 3': (lambda: print('Algorithm 3 works')),
    'Algorithm 4': (lambda: print('Algorithm 4 works')),
}
