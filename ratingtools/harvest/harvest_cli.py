
# built-ins
import re

# external packages
from vs_library.cli import Node, NodeBundle, DecoyNode, textformat
from vs_library.cli.objects import Command, Prompt, Table
from vs_library.vsdb import references
from vs_library.tools import pandas_functions_cli


class GenerateHarvest(NodeBundle):

    """Prompts user to enter information necessary to generate a harvest file"""
    
    def __init__(self, rating_harvest, rating_worksheet=None, parent=None):

        """
        Parameters
        ----------
        rating_harvest : harvest.RatingHarvest
            The controller of this NodeBundle
        
        rating_worksheet : harvest.RatingWorksheet, optional
            An optional controller, if present, will transfer recognized columns to rating_harvest
        """

        name = 'generate-harvest'
        self.rating_harvest = rating_harvest
        self.rating_worksheet = rating_worksheet

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
                             show_hideout=True)
        self.__node_0 = Node(self.__prompt_1, name=f'{name}_sig-id', parent=self.__entry_node, 
                             show_hideout=True)
        self.__node_1 = Node(self.__prompt_2, name=f'{name}_usesigrating', parent=self.__node_0, 
                             show_hideout=True)
        self.__node_2 = Node(self.__prompt_3, name=f'{name}_ratingsession', parent=self.__node_1, 
                             show_hideout=True)
        self.__node_3 = Node(self.__prompt_4, name=f'{name}_ratingformat', parent=self.__node_2, 
                             show_hideout=True)
        self.__node_4 = Node(self.__table_0, name=f'{name}_summary', parent=self.__node_3,
                             store=False)
        self.__node_5 = Node(self.__prompt_5, name=f'{name}_continue', parent=self.__node_4, 
                             show_hideout=True, store=False)
        self.__exit_node = DecoyNode(name=f'{name}_last-node')

        self.__bundle_0 = ExportHarvestFile(rating_harvest, parent=self.__node_5)

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
            '2': Command(lambda: self.__node_5.set_next(self.__entry_node), value="No, re-enter responses",
                         command=Command(self.clear_all))
            }

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)

    # to prevent unintended edits
    def clear_all(self):

        """Clear all user's inputs"""

        self.__prompt_0.clear()
        self.__prompt_1.clear()
        self.__prompt_2.clear()
        self.__prompt_3.clear()
        self.__prompt_4.clear()

    def _execute(self):

        self.rating_harvest.span = self.__prompt_0.responses
        self.rating_harvest.sig_id = self.__prompt_1.responses
        self.rating_harvest.usesigrating = self.__prompt_2.responses
        self.rating_harvest.ratingsession = self.__prompt_3.responses
        self.rating_harvest.ratingformat_id = self.__prompt_4.responses

        if self.rating_worksheet:
            self.rating_harvest.df = self.rating_worksheet.df
            self.rating_harvest.generate()
        else:
            self.rating_harvest.generate()

    def _populate_table(self):
        self.__table_0.table = [[textformat.apply('Span', emphases=['bold']), self.__prompt_0.responses],
                                [textformat.apply('SIG ID', emphases=['bold']), self.__prompt_1.responses],
                                [textformat.apply('Website Display', emphases=['bold']), self.__prompt_2.option_responses(string=True)],
                                [textformat.apply('Rating Session', emphases=['bold']), self.__prompt_3.option_responses(string=True)],
                                [textformat.apply('Rating Format', emphases=['bold']), self.__prompt_4.option_responses(string=True)]]
    @staticmethod
    def is_validyear(x):

        """Provide a verification to user's input of year"""

        pattern = r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)[\-]' \
                  r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)|' \
                  r'(19[8-9][9]|2[0-9][0-9][0-9]|3000)'

        return re.fullmatch(pattern, x), "Year must be between 1989 to 3000."


class ExportHarvestFile(pandas_functions_cli.ExportSpreadsheet):

    """Harvest file can be saved to the user's local host"""

    def __init__(self, rating_harvest, parent=None):

        name = 'export-ratings-harvest'
        self.rating_harvest = rating_harvest
        
        super().__init__(name, parent)
    
    def _execute(self):
        return super()._execute(self.rating_harvest.export)