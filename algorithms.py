import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model


class Algorithm:
    def getInputSize(self):
        raise NotImplementedError

    def performImpl(self, t1, t2):
        raise NotImplemented


def performAlgorithm(algo, t1_pic, t2_pic):
    width = t1_pic.width
    height = t1_pic.height

    t1_arr = np.array(t1_pic.resize(algo.getInputSize(), Image.ANTIALIAS))
    t2_arr = np.array(t2_pic.resize(algo.getInputSize(), Image.ANTIALIAS))

    algo_result = algo.performImpl(t1_arr, t2_arr)

    res_im = Image.fromarray(algo_result)
    res_im = res_im.resize((width, height), Image.NEAREST)
    return res_im


SNATCHED_MODEL = load_model('best_model.h5')
OUTPUT_SIZE = 32


class DeepLearning(Algorithm):
    def getInputSize(self):
        return (512, 512)

    def performImpl(self, t1, t2):
        result = SNATCHED_MODEL(inputs=[np.array([t1]), np.array([t2])])
        output = np.asarray(result[0])
        output = np.round(output) * 255
        return output.reshape((OUTPUT_SIZE, OUTPUT_SIZE))


class SVMAlgorithm(Algorithm):
    def getInputSize(self):
        return (512, 512)

    def performImpl(self, t1, t2):
        result = SNATCHED_MODEL(inputs=[np.array([t1]), np.array([t2])])
        output = np.asarray(result[0])
        output = np.round(output) * 255
        return output.reshape((OUTPUT_SIZE, OUTPUT_SIZE))


class DecisionTreeAlgorithm(Algorithm):
    def getInputSize(self):
        return (512, 512)

    def performImpl(self, t1, t2):
        result = SNATCHED_MODEL(inputs=[np.array([t1]), np.array([t2])])
        output = np.asarray(result[0])
        output = np.round(output) * 255
        return output.reshape((OUTPUT_SIZE, OUTPUT_SIZE))


class FuzzyARTMAPAlgorithm(Algorithm):
    def getInputSize(self):
        return (512, 512)

    def performImpl(self, t1, t2):
        result = SNATCHED_MODEL(inputs=[np.array([t1]), np.array([t2])])
        output = np.asarray(result[0])
        output = np.round(output) * 255
        return output.reshape((OUTPUT_SIZE, OUTPUT_SIZE))


# format: <visible_algorithm_name, algorithm_class(Algorithm)>
algorithms = {
    'CNN Algorithm': DeepLearning(),
    'SVM Algorithm': SVMAlgorithm(),
    'Decision tree Algorithm': DecisionTreeAlgorithm(),
    'FuzzyARTMAP': FuzzyARTMAPAlgorithm(),
}
