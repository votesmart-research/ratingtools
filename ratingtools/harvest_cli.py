
# built-ins
import re

# external packages
from vs_library.cli import Node, NodeBundle, DecoyNode
from vs_library.cli.objects import Command, Prompt, Table
from vs_library.vsdb import references
from vs_library.tools import pandas_functions_cli


class GenerateHarvest(NodeBundle):
    
    def __init__(self, ratings_harvest, ratings_worksheet=None, parent=None):

        name = 'generate-harvest'
        self.ratings_harvest = ratings_harvest
        self.ratings_worksheet = ratings_worksheet

        # OBJECTS
        self.__prompt_0 = Prompt("What is the span or year of the ratings?", 
                                 verification=self.is_validyear)
        self.__prompt_1 = Prompt("What is the database sig_id of the SIG?")
        self.__prompt_2 = Prompt("Do you want SIG Rating or Our Rating to be displayed on the web?")
        self.__prompt_3 = Prompt("What is the legislative session of this rating?")
        self.__prompt_4 = Prompt("Select the appropriate format for this rating")
        self.__table_0 = Table([], header=False, command=Command(self._populate_table))
        self.__prompt_5 = Prompt("Proceed with the above response?")
        
        # NODES
        self.__entry_node = Node(self.__prompt_0, name=f'{name}_span', 
                             show_instructions=True)
        self.__node_0 = Node(self.__prompt_1, name=f'{name}_sig-id', parent=self.__entry_node, 
                             show_instructions=True)
        self.__node_1 = Node(self.__prompt_2, name=f'{name}_usesigrating', parent=self.__node_0, 
                             show_instructions=True)
        self.__node_2 = Node(self.__prompt_3, name=f'{name}_ratingsession', parent=self.__node_1, 
                             show_instructions=True)
        self.__node_3 = Node(self.__prompt_4, name=f'{name}_ratingformat', parent=self.__node_2, 
                             show_instructions=True)
        self.__node_4 = Node(self.__table_0, name=f'{name}_summary', parent=self.__node_3)
        self.__node_5 = Node(self.__prompt_5, name=f'{name}_continue', parent=self.__node_4, 
                             show_instructions=True)
        self.__exit_node = DecoyNode(name=f'{name}_last-node')

        self.__bundle_0 = ExportHarvestFile(ratings_harvest, parent=self.__node_5)

        self.__bundle_0.adopt_node(self.__exit_node)
        self.__node_5.adopt(self.__entry_node)
        self.__node_5.adopt(self.__exit_node)

        # CONFIGURATIONS
        self.__bundle_0.entry_node.clear_screen = True

        self.__table_0.table_header = "Harvest Information"
        self.__table_0.description = "Shows the harvest information entered"

        self.__prompt_2.options = {'t': "SIG Rating", 'f': "Our Rating"}
        self.__prompt_3.options = references.RATING_SESSION
        self.__prompt_4.options = references.RATING_FORMAT

        self.__prompt_5.options = {
            '1': Command(self._execute, value="Yes",
                         command=Command(lambda: self.__node_5.set_next(self.__bundle_0.entry_node))),
            '2': Command(lambda: self.__node_5.set_next(self.__entry_node), value="No, re-enter responses")
            }

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)

    def _execute(self):

        self.ratings_harvest.span = self.__prompt_0.responses
        self.ratings_harvest.sig_id = self.__prompt_1.responses
        self.ratings_harvest.usesigrating = self.__prompt_2.responses
        self.ratings_harvest.ratingsession = self.__prompt_3.responses
        self.ratings_harvest.ratingformat_id = self.__prompt_4.responses

        if self.ratings_worksheet:
            self.ratings_harvest.df = self.ratings_worksheet.df
            self.ratings_harvest.generate()
        else:
            self.ratings_harvest.generate()

    def _populate_table(self):
        self.__table_0.table = [['Span', self.__prompt_0.responses],
                                ['SIG ID', self.__prompt_1.responses],
                                ['Website Display', self.__prompt_2.option_responses(string=True)],
                                ['Rating Session', self.__prompt_3.option_responses(string=True)],
                                ['Rating Format', self.__prompt_4.option_responses(string=True)]]
    @staticmethod
    def is_validyear(x):

        regex = r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)[\-]' \
                r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)|' \
                r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)'

        return re.fullmatch(regex, x), "Year must be between 1989 to 3000."


class ExportHarvestFile(pandas_functions_cli.ExportSpreadsheet):

    def __init__(self, ratings_harvest, parent=None):

        name = 'export-ratings-harvest'
        self.ratings_harvest = ratings_harvest
        
        super().__init__(name, parent)
    
    def _execute(self):
        return super()._execute(controller=self.ratings_harvest.export)