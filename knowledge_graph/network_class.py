from owlready2 import *
from knowledge_graph.ontology_processing_utils import give_alias


class Network:
    """A class which runs a depth-first-search on the ontology and creates
    a graph network from the data.

    Parameters
    ----------
    ontology : OWL2 climate mind ontology file

       Completes a depth-first search for the ontology and return edges in
       the component reachable from source.
    """

    def __init__(self, ontology, source=None):
        self.ontology = ontology
        self.result = []
        self.visited = set()
        self.node_family = []
        self.class_family = []
        if source:
            self.source = source
        else:
            self.source = None
        # Add labels the ontology object in a way that makes them pythonicly accessible through . invocation method.
        obj_props = list(self.ontology.object_properties())
        annot_props = list(self.ontology.annotation_properties())
        self.obj_properties = [give_alias(x) for x in obj_props]
        self.annot_properties = [give_alias(x) for x in annot_props]

    def add_child_to_result(self, child, parent, edge_type):
        """Adds a node to the results and if needed adds the node's family
        to node_family (a stack of nodes to continue exploring).

            Parameters
            ----------
            child: A node in the ontology
            parent: A node in the ontology
            edge_type: The relationship between child and parent
                        i.e. causes, inhibits, etc
        """
        self.result.append((parent.label[0], child.label[0], edge_type))
        if child not in self.visited:
            self.visited.add(child)
            for obj_prop in self.obj_properties:
                self.node_family.append(
                    (child, eval("iter(child." + obj_prop + ")"), obj_prop)
                )

    def add_class_to_explore(self, class_name):
        """Adds all nodes related to a particular class. Some of these nodes
        will not actually be a class, but that is irrelevant as they will get ignored.

            Parameters
            ----------
            class_name: A node in the ontology
        """
        for obj_prop in self.obj_properties:
            try:
                self.class_family.append(
                    (class_name, eval("iter(class_name." + obj_prop + ")"), obj_prop)
                )
            except:
                pass
        try:
            self.class_family.append(
                (class_name, iter(self.ontology.get_parents_of(class_name)), "is_a")
            )  # the class(es) of the ont_class. This could pull classes that are just Restriction classes, so really should add code here that checks the class is found in self.ontology.classes() before adding it to the class_family.
        except:
            pass

    def dfs_for_classes(self, node):
        """Performs a depth-first-search on parent classes from a node.

        Parameters
        ----------
        node: The starting point node in the ontology
        """
        visited_classes = set()
        classes = self.ontology.get_parents_of(node)

        if classes:

            for ont_class in classes:
                if ont_class != owl.Thing:
                    self.add_class_to_explore(ont_class)

            while self.class_family:
                parent2, children2, edge_type2 = self.class_family[-1]
                visited_classes.add(parent2)  # these are not all classses

                try:
                    child2 = next(children2)
                    if child2 != owl.Thing:

                        if child2 in self.ontology.individuals():
                            self.add_child_to_result(child2, node, edge_type2)
                        elif (
                            child2 not in visited_classes
                            and child2 in self.ontology.classes()
                        ):
                            visited_classes.add(child2)
                            self.add_class_to_explore(child2)

                except StopIteration:
                    self.class_family.pop()

    def dfs_labeled_edges(self):

        """Produce edges in a depth-first-search (DFS) labeled by type.

        Notes
        -----
        Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
        by D. Eppstein, July 2004.
        If a source is not specified then a source is chosen arbitrarily and
        repeatedly until all components in the graph are searched.

        TODO Find why a couple of duplicates are created
        Example: increase in carbon capture,
                  greenhouse-gas externality,
                  is_inhibited_or_prevented_or_blocked_or_slowed_by

        """
        if self.source:
            nodes = [self.ontology.search_one(label=self.source)]
        else:
            nodes = self.ontology.individuals()

        for node in nodes:
            if node not in self.visited:
                self.visited.add(node)
                for obj_prop in self.obj_properties:
                    self.node_family.append(
                        (node, eval("iter(node." + obj_prop + ")"), obj_prop)
                    )

                while self.node_family:
                    parent, children, edge_type = self.node_family[-1]
                    self.visited.add(parent)

                    try:
                        child = next(children)
                        self.add_child_to_result(child, parent, edge_type)

                    except StopIteration:
                        self.node_family.pop()
                        self.dfs_for_classes(parent)

