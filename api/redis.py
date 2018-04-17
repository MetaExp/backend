import redis
import logging
import pickle

from typing import List
from util.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

class Redis:

    def __init__(self):
        self._client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))
        self.logger.debug("current keys are: {}", self._client.keys())

    def meta_paths(self, data_set_name: str, start_type: str, end_type: str) -> List:
        self.logger.debug("Retrieving meta paths...")
        pickled_list = self._client.lrange("{}_{}_{}".format(data_set_name, start_type, end_type), 0, -1)
        self.logger.debug(pickled_list)
        return [pickle.loads(pickled_entry) for pickled_entry in pickled_list]

    def id_to_edge_type_map(self, data_set_name: str):
        return self._client.hgetall("{}_edge_type_mapping".format(data_set_name))

    def id_to_node_type_map(self, data_set_name: str):
        return self._client.hgetall("{}_node_type_mapping".format(data_set_name))

    def node_type_to_id_map(self, data_set_name: str):
        return self._client.hgetall("{}_node_type_mapping_reverse".format(data_set_name))

    def edge_type_to_id_map(self, data_set_name: str):
        return self._client.hgetall("{}_edge_type_mapping_reverse".format(data_set_name))
