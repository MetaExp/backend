import multiprocessing

from util.datastructures import MetaPath
from util.config import MAX_META_PATH_LENGTH, AVAILABLE_DATA_SETS, PARALLEL_EXISTENCE_TEST_PROCESSES
from api.neo4j_own import Neo4j
from api.redis_own import Redis
from typing import Dict, List, Tuple
import logging
import ast
import pickle


class RedisImporter:
    def __init__(self, enable_existence_check=True):
        self.enable_existence_check = enable_existence_check
        self.logger = self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))
        self.id_to_edge_type_map = None
        self.id_to_node_type_map = None
        self.redis = None

    def import_all(self):
        for data_set in AVAILABLE_DATA_SETS:
            self.import_data_set(data_set)

    def import_data_set(self, data_set: Dict):
        self.redis = Redis(data_set['name'])
        with Neo4j(data_set['bolt-url'], data_set['username'], data_set['password']) as neo4j:
            for record in neo4j.get_meta_paths_schema_weigths(MAX_META_PATH_LENGTH):
                meta_path_dict = ast.literal_eval(record['metaPaths'])
                self.logger.debug(type(meta_path_dict))
                meta_path_list = list(meta_path_dict.items())
                self.logger.debug("Received meta paths from neo4j: {}".format(meta_path_list))
                self.logger.debug("Number of meta paths is: {}".format(len(meta_path_list)))
                # meta_paths_without_duplicates = list(set(meta_path_list))
                # self.logger.debug("After removal of duplicates: {}".format(len(meta_paths_without_duplicates)))
                self.id_to_edge_type_map = ast.literal_eval(record['edgesIDTypeDict'])
                self.id_to_node_type_map = ast.literal_eval(record['nodesIDTypeDict'])
                self.write_mappings(self.id_to_node_type_map, self.id_to_edge_type_map)
                # meta_paths_without_duplicates.sort(key=len)
                if self.enable_existence_check:
                    result = self.start_parallel_existence_checks(meta_path_list, data_set)
                    self.logger.debug("Got result from existence check {}".format(result))
                    existing_meta_paths = [x for x in result if x is not None]
                    self.logger.debug("Existing meta_paths are {}".format(existing_meta_paths))
                    self.logger.debug("From {} mps {} exist in graph {}".format(len(meta_path_list),
                                                                                len(existing_meta_paths),
                                                                                data_set['name']))
                else:
                    self.write_paths([(str(mp[0]).split("|"), float(mp[1])) for mp in meta_path_list])

    # Executed if existence check is enabled
    @staticmethod
    def check_existence(args):
        logger = logging.getLogger('MetaExp.ExistenceCheck')
        labels = []
        (meta_path, structural_value, data_set, edge_map, node_map) = args
        mp_as_list = meta_path.split("|")
        logger.debug("Checking existance of {}".format(mp_as_list))
        for i, type in enumerate(mp_as_list):
            if i % 2:
                labels.append("[n{}:{}]".format(i, edge_map[type]))
            else:
                labels.append("(e{}: {})".format(i, node_map[type]))
        logger.debug("Querying for mp {}".format(mp_as_list))
        with Neo4j(data_set['bolt-url'], data_set['username'], data_set['password']) as neo4j:
            if neo4j.test_whether_meta_path_exists("-".join(labels)):
                logger.debug("Mp {} exists!".format("-".join(labels)))
                start_node = mp_as_list[0]
                end_node = mp_as_list[-1]
                logger.debug("Adding metapath {} to record {}".format(mp_as_list, "{}_{}_{}".format(data_set['name'],
                                                                                                    start_node,
                                                                                                    end_node)))
                mp_object = MetaPath(edge_node_list=mp_as_list)
                logger.debug("Storing structural value {}...".format(structural_value))
                mp_object.store_structural_value(float(structural_value))
                Redis(data_set['name'])._client.lpush("{}_{}_{}".format(data_set['name'], start_node, end_node),
                                                      pickle.dumps(mp_object))
                return mp_as_list
        return None

    # Executed if existence check is enabled
    def start_parallel_existence_checks(self, meta_paths: List[str], data_set: Dict) -> List[List[str]]:
        with multiprocessing.Pool(processes=PARALLEL_EXISTENCE_TEST_PROCESSES) as pool:
            args = [(mp[0], mp[1], data_set, self.id_to_edge_type_map, self.id_to_node_type_map) for mp in meta_paths]
            return pool.map(self.check_existence, args)

    # Executed if existence check is disabled
    def write_paths(self, paths: List[Tuple[List[str], float]]):
        for path in paths:
            self.write_path(path[0], path[1])

    # Executed if existence check is disabled
    def write_path(self, path: List[str], structural_value: float):
        start_node = path[0]
        end_node = path[-1]
        self.logger.debug("Adding metapath {} to record {}".format(path, "{}_{}_{}".format(self.redis.data_set,
                                                                                           start_node,
                                                                                           end_node)))
        mp_object = MetaPath(edge_node_list=path)
        self.logger.debug("Storing structural value {}...".format(structural_value))
        mp_object.store_structural_value(structural_value)
        self.redis._client.lpush("{}_{}_{}".format(self.redis.data_set, start_node, end_node),
                                 pickle.dumps(mp_object))

    def write_mappings(self, node_type_mapping: Dict[int, str], edge_type_mapping: Dict[int, str]):
        self.redis._client.hmset("{}_node_type_map".format(self.redis.data_set), node_type_mapping)
        self.redis._client.hmset("{}_edge_type_map".format(self.redis.data_set), edge_type_mapping)
        self.redis._client.hmset("{}_node_type_map_reverse".format(self.redis.data_set),
                                 {v: k for k, v in node_type_mapping.items()})
        self.redis._client.hmset("{}_edge_type_map_reverse".format(self.redis.data_set),
                                 {v: k for k, v in edge_type_mapping.items()})
