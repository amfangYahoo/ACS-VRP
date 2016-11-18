from math import pow
from threading import *
import random
import logging

logger = logging.getLogger("logger")


class Ant(Thread):
    def __init__(self, ID, start_node, colony):
        Thread.__init__(self)
        self.id = ID
        self.start_node = start_node
        self.colony = colony

        self.curr_node = self.start_node
        self.graph = self.colony.graph
        self.path_vec = []
        self.path_vec.append(self.start_node)
        self.path_cost = 0
        self.path_mat = [[0 for i in range(0, self.graph.nodes_num)] for i in range(0, self.graph.nodes_num)]

        self.Beta = 2.0
        self.Q0 = 0.5
        self.Rho = 0.1

        self.nodes_to_visit = {}

        for i in range(0, self.graph.nodes_num):
            if i != self.start_node:
                self.nodes_to_visit[i] = i

    def run(self):
        graph = self.colony.graph
        while not self.end():
            new_node = self.state_transition_rule(self.curr_node)
            self.path_cost += graph.delta(self.curr_node, new_node)
            self.path_vec.append(new_node)
            self.path_mat[self.curr_node][new_node] = 1
            # current state of ant
            logger.debug('Ant {} : {}'.format(str(self.id), self.path_vec))
            logger.debug('cost : {}'.format(self.path_cost))
            self.local_updating_rule(self.curr_node, new_node)
            self.curr_node = new_node
        self.local_updating_rule(self.path_vec[-1], self.path_vec[0])
        self.path_cost += graph.delta(self.path_vec[-1], self.path_vec[0])
        logger.debug('Ant {} : {}'.format(str(self.id), self.path_vec))
        logger.debug('cost : {}'.format(self.path_cost))

        self.colony.update(self)

        # update global colony
        logger.debug('===========Ant {} terminated==========='.format(self.id))

        self.__init__(self.id, self.start_node, self.colony)

    def end(self):
        return not self.nodes_to_visit

    def state_transition_rule(self, curr_node):
        graph = self.colony.graph
        q = random.random()
        max_node = -1

        if q < self.Q0:
            logger.debug("Exploitation")
            max_val = -1
            val = None

            for node in self.nodes_to_visit.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")

                val = graph.tau(curr_node, node) * pow(graph.etha(curr_node, node), self.Beta)
                if val > max_val:
                    max_val = val
                    max_node = node
        else:
            logger.debug("Exploration")
            sum = 0
            node = -1

            for node in self.nodes_to_visit.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")
                sum += graph.tau(curr_node, node) * pow(graph.etha(curr_node, node), self.Beta)
            if sum == 0:
                raise Exception("sum = 0")

            avg = sum / len(self.nodes_to_visit)

            #print("avg = " + str(avg))

            # random node selected according to the probability distribution
            # TODO check this method
            probability = {}
            pre_probability = 0
            r = random.random()
            #logger.info("r " + str(r))
            for node in self.nodes_to_visit.values():
                probability[node] = graph.tau(curr_node, node) * pow(graph.etha(curr_node, node), self.Beta) / sum
                pre_probability = pre_probability + probability[node]
                #logger.info("p " + str(pre_probability))
                if pre_probability >= r:
                    max_node = node
                    break

            if max_node == -1:
                max_node = node

        if max_node < 0:
            raise Exception("max_node < 0")

        del self.nodes_to_visit[max_node]

        return max_node

    def local_updating_rule(self, curr_node, next_node):
        graph = self.colony.graph
        val = (1 - self.Rho) * graph.tau(curr_node, next_node) + (self.Rho * graph.tau0)
        graph.update_tau(curr_node, next_node, val)