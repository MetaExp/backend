from abc import ABC, abstractmethod, ABCMeta
from enum import Enum
from typing import List, Dict
import numpy as np
import logging
import math
from copy import copy

from util.datastructures import MetaPath
from .hypothesis import GaussianProcessHypothesis, MPLengthHypothesis

# algorithm types
NO_USER_FEEDBACK = 'no_user_feedback'
ITERATIVE_BATCHING = 'iterative_batching'
COLLECT_ALL = 'collect_all'


class State(Enum):
    VISITED = 0
    NOT_VISITED = 1


class AbstractActiveLearningAlgorithm(ABC):
    STANDARD_RATING = 0.5
    UI_MAX_VALUE = 1.0
    UI_MIN_VALUE = 0.0

    def __init__(self, meta_paths: List[MetaPath], seed: int):
        self.meta_paths = np.array(meta_paths)
        self.meta_paths_rating = np.array(np.zeros(len(meta_paths)))
        self.visited = np.array([State.NOT_VISITED] * len(meta_paths))
        self.random = np.random.RandomState(seed=seed)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes.
        d = dict(self.__dict__)
        # Remove the unpicklable entries.
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))

    def get_max_ref_path(self) -> Dict:
        idx = np.where(self.visited == State.VISITED)
        # Retrieve the last occurrence of the maximum value, so that max_ref_path and min_ref_path are never the same.
        reversed_ratings = self.meta_paths_rating[idx][::-1]
        max_ref_path_idx = len(reversed_ratings) - np.argmax(reversed_ratings) - 1
        max_ref_path_id = np.where(self.visited == State.VISITED)[0][max_ref_path_idx]
        self.logger.debug(
            "Max ref path is {} with rating {}".format(max_ref_path_id, self.meta_paths_rating[max_ref_path_id]))
        return {'id': int(max_ref_path_id),
                'metapath': self.meta_paths[max_ref_path_id].get_representation('UI'),
                'rating': self.UI_MAX_VALUE}

    def get_min_ref_path(self) -> Dict:
        idx = np.where(self.visited == State.VISITED)
        min_ref_path_idx = np.argmin(self.meta_paths_rating[idx])
        min_ref_path_id = np.where(self.visited == State.VISITED)[0][min_ref_path_idx]
        self.logger.debug(
            "Max ref path is {} with rating {}".format(min_ref_path_id, self.meta_paths_rating[min_ref_path_id]))
        return {'id': int(min_ref_path_id),
                'metapath': self.meta_paths[min_ref_path_id].get_representation('UI'),
                'rating': self.UI_MIN_VALUE}

    def has_one_batch_left(self, batch_size):
        if len(np.where(self.visited == State.NOT_VISITED)[0]) >= batch_size:
            return False
        return True

    def is_first_batch(self):
        if len(np.where(self.visited == State.NOT_VISITED)[0]) == len(self.meta_paths):
            return True
        return False

    def update(self, meta_paths):
        idx = [mp['id'] for mp in meta_paths]
        ratings = [mp['rating'] for mp in meta_paths]
        self.visited[idx] = State.VISITED
        self.logger.debug("Refreshed visited list: {}".format(self.visited))
        self.meta_paths_rating[idx] = ratings
        self.logger.debug("Refreshed rating list: {}".format(self.meta_paths_rating))

    def get_next(self, batch_size=1) -> (List[MetaPath], bool):
        """
        :return: requested number of next meta-paths to be rated next.
        """
        is_last_batch = self.has_one_batch_left(batch_size)
        self.logger.info("Last Batch: {}".format(is_last_batch))
        if is_last_batch:
            batch_size = len(np.where(self.visited == State.NOT_VISITED)[0])
        ids = self._select(batch_size)

        mps = [{'id': int(meta_id),
                'metapath': meta_path.get_representation('UI'),
                'rating': self.STANDARD_RATING} for meta_id, meta_path in
               zip(ids, self.meta_paths[ids])]

        reference_paths = {'max_path': self.get_max_ref_path(),
                           'min_path': self.get_min_ref_path()} if not self.is_first_batch() else {}
        return mps, is_last_batch, reference_paths

    @abstractmethod
    def _select(self, n):
        """
        Select the next n paths to be labeled
        """
        pass

    def create_output(self):
        mps = [{'id': int(meta_id[0]),
                'metapath': meta_path.get_representation('UI'),
                'rating': self.meta_paths_rating[meta_id]} for meta_id, meta_path in np.ndenumerate(self.meta_paths) if
               self.visited[meta_id] == State.VISITED]
        return mps


class RandomSelectionAlgorithm(AbstractActiveLearningAlgorithm):
    """
    An active learning algorithm, that asks for randomly labeled instances.
    """

    def __init__(self, meta_paths: List[MetaPath], standard_rating: float = 0.5, seed=42):
        self.standard_rating = standard_rating
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))
        super(RandomSelectionAlgorithm, self).__init__(meta_paths, seed)

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes.
        d = dict(self.__dict__)
        # Remove the unpicklable entries.
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))

    def available_hypotheses(self):
        return [None]

    def _select(self, n):
        """
        Choose the next paths to be rated randomly.
        """
        return self.random.choice(range(len(self.meta_paths)), replace=False, p=self._prob_choose_meta_path(),
                                  size=n)

    def _predict(self, id):
        if self.visited[id] == State.VISITED:
            return self.meta_paths_rating[id]
        return sum(self.meta_paths_rating[np.where(self.visited == State.VISITED)]) / len(self.meta_paths_rating)

    def _predict_rating(self, idx):
        return [self._predict(id) for id in idx]

    def get_all_predictions(self):
        idx = range(len(self.meta_paths))
        return [{'id': id, 'rating': rating, 'metapath': self.meta_paths[id]} for id, rating in
                zip(idx, self._predict_rating(idx))]

    """
    Functions
    """

    def _prob_choose_meta_path(self) -> np.ndarray:
        not_visited = np.where(self.visited == State.NOT_VISITED)[0]
        if len(not_visited) > 0:
            probs = np.zeros(len(self.meta_paths))
            probs[not_visited] = 1.0
            return probs / len(not_visited)
        else:
            return np.append(np.zeros(len(self.meta_paths) - 1), [1])


class HypothesisBasedAlgorithm(AbstractActiveLearningAlgorithm, metaclass=ABCMeta):
    available_hypotheses = {'Gaussian Process': GaussianProcessHypothesis,
                            'MP Length': MPLengthHypothesis}
    default_hypotheses = 'Gaussian Process'

    def __init__(self, meta_paths: List[MetaPath], seed: int = 42, **hypothesis_params):
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))
        if 'hypothesis' not in hypothesis_params:
            self.logger.debug('Default hypothesis {} was set'.format(self.default_hypotheses))
            self.hypothesis = self.available_hypotheses[self.default_hypotheses](meta_paths, **hypothesis_params)
        elif hypothesis_params['hypothesis'] not in self.available_hypotheses:
            self.logger.error('This Hypotheses is unavailable! Try another one.')
        else:
            self.logger.debug('Hypothesis {} was set'.format(hypothesis_params['hypothesis']))
            self.hypothesis = self.available_hypotheses[hypothesis_params['hypothesis']](meta_paths,
                                                                                         **hypothesis_params)
        super().__init__(meta_paths, seed)

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes.
        d = dict(self.__dict__)
        # Remove the unpicklable entries.
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))

    def update(self, meta_paths):
        super().update(meta_paths)
        self.logger.debug("Fitting {} to new data points...".format(self.hypothesis.__class__.__name__))
        self.hypothesis.update(np.where(self.visited == State.VISITED)[0],
                               self.meta_paths_rating[np.where(self.visited == State.VISITED)[0]])

    def _select(self, batch_size):
        criterion = self.compute_selection_criterion()
        n = len(criterion)
        ids = np.arange(n)
        unvisited = np.where(self.visited == State.NOT_VISITED)[0]

        similarity = self.hypothesis.get_similarity()

        #self.logger.debug("Meta paths that were already rated were filtered: {}".format(criterion))
        selected_ids = []
        for i in range(batch_size):
            if len(unvisited) > 0:
                criterion_unvisited = criterion[unvisited]
                ids_unvisited = ids[unvisited]
                most_uncertain = np.random.choice(np.where(criterion_unvisited == np.amax(criterion_unvisited))[0])
                most_uncertain_id = ids_unvisited[most_uncertain]
                unvisited = np.delete(unvisited, np.where(most_uncertain_id == unvisited))
                selected_ids.append(most_uncertain_id)

                # remove the len/batchsize - 1 closest elements from the list
                remove_n = int(math.floor(n/batch_size) - 1)
                self.logger.debug("Removing {} elements close to the most uncertain element.".format(remove_n))
                if len(unvisited) > remove_n and remove_n > 0:
                    ids_unvisited = ids[unvisited]
                    closest_elements = np.argpartition(similarity[most_uncertain_id][unvisited],remove_n)[:remove_n]
                    ignore_closest_idx = ids_unvisited[closest_elements]
                    for ignore in ignore_closest_idx:
                        unvisited = np.delete(unvisited,np.where(np.isin(ignore, unvisited)))
            else:
                self.logger.debug("Not items left")



        self.logger.debug("Most {} uncertain ids are {}".format(batch_size, selected_ids))
        return selected_ids

    @abstractmethod
    def compute_selection_criterion(self):
        """
        Select the next metapaths based on the uncertainty of them in the current model.
        """
        pass

    def get_all_predictions(self):
        idx = range(len(self.meta_paths))
        return [{'id': id, 'rating': rating, 'metapath': self.meta_paths[id]} for id, rating in
                zip(idx, self.hypothesis.predict_rating(idx))]


class UncertaintySamplingAlgorithm(HypothesisBasedAlgorithm):
    """
        An active learning algorithm, that requests labels on the data he is most uncertain of.
    """

    def __init__(self, meta_paths: List[MetaPath], seed: int = 42, **hypothesis_params):
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))
        super().__init__(meta_paths, seed, **hypothesis_params)

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes.
        d = dict(self.__dict__)
        # Remove the unpicklable entries.
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))

    @staticmethod
    def options():
        return {}

    def get_complete_rating(self):
        idx = range(len(self.meta_paths))
        mps = [{'id': int(meta_id[0]),
                'metapath': self.meta_paths[int(meta_id[0])],
                'domain_value': rating}
               for meta_id, rating in np.ndenumerate(self.hypothesis.predict_rating(idx))]
        return mps

    def compute_selection_criterion(self):
        """
        Select the next meta paths based on the uncertainty of them in the current model.
        """
        self.logger.info('Computing selection criterion for next meta path batch')
        std = self.hypothesis.get_uncertainty(range(len(self.meta_paths)))
        return std


class RandomSamplingAlgorithm(HypothesisBasedAlgorithm):
    """
        An active learning algorithm, that requests labels on the data he is most uncertain of.
    """

    @staticmethod
    def options():
        return {}

    def compute_selection_criterion(self):
        """
        Select the next metapaths based on the uncertainty of them in the current model.
        """
        random_criterion = self.random.randn(len(self.meta_paths))
        return random_criterion


class GPSelect_Algorithm(HypothesisBasedAlgorithm):
    """
        An active learning algorithm, that selects the most uncertain data, but prefers more highly rated datapoints.
        The parameter beta weights the trade-off between exploitation and exploration.
        ...
        Hastagiri P. Vanchinathan, Andreas Marfurt, Charles-Antoine Robelin, Donald Kossmann, and Andreas Krause. 2015. 
        Discovering Valuable items from Massive Data. In Proceedings of the 21th ACM SIGKDD (KDD '15).
        ACM, New York, NY, USA, 1195-1204. DOI: https://doi.org/10.1145/2783258.2783360
    """

    def __init__(self, meta_paths: List[MetaPath], seed: int = 42, **hypothesis_params):
        super().__init__(meta_paths, seed, **hypothesis_params)
        if 'beta' in hypothesis_params:
            self.beta = hypothesis_params['beta']
        else:
            self.beta = 0.5

    @staticmethod
    def options():
        return {
            'hypothesis': [GaussianProcessHypothesis]
        }

    def compute_selection_criterion(self):
        """
        Select the next metapaths based on the uncertainty of them in the current model.
        """
        all_paths = range(len(self.meta_paths))
        criterion = np.sqrt(self.beta) * self.hypothesis.get_uncertainty(all_paths) \
                    + self.hypothesis.predict_rating(all_paths)
        return criterion
