
# external packages
from vs_library.cli import Node, NodeBundle, DecoyNode
from vs_library.cli.objects import Command, Display, Prompt, textformat


class IntroToRatingTools(NodeBundle):
    
    def __init__(self, rm_bundle, rh_bundle, parent=None):

        name = 'intro-to-rating-tools'

        # OBJECTS
        welcome_msg = "Welcome to rating tools! This tool performs candidate matching\n" \
                      "on ratings and generates harvest file."

        self.__display_0 = Display(textformat.apply(welcome_msg, emphases=['bold']))
        self.__prompt_0 = Prompt("What would you like to do?")

        # NODES
        self.__entry_node = Node(self.__display_0, name=f'{name}_welcome-msg', 
                             acknowledge=True, clear_screen=True)
        self.__node_0 = Node(self.__prompt_0, name=f'{name}_pick-match-or-harvest', parent=self.__entry_node, 
                             show_instructions=True, clear_screen=True)
        self.__exit_node = DecoyNode(name=f'{name}_last-node', parent=self.__node_0)

        self.__bundle_0 = rm_bundle
        self.__bundle_1 = rh_bundle

        self.__node_0.adopt(self.__bundle_0.entry_node)
        self.__node_0.adopt(self.__bundle_1.entry_node)

        # CONFIGURATIONS
        self.__bundle_0.entry_node.clear_screen = True
        self.__bundle_1.entry_node.clear_screen = True

        self.__prompt_0.options = {
            '1': Command(lambda: self.__node_0.set_next(self.__bundle_0.entry_node), value="Match Ratings"),
            '2': Command(lambda: self.__node_0.set_next(self.__bundle_1.entry_node), 
                                     value="Generate Harvest File from existing worksheet")
            }

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)
