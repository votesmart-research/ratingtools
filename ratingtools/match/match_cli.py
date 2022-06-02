
# external packages
from vs_library.cli import Node, NodeBundle, DecoyNode, textformat
from vs_library.cli.objects import Command, Display, Prompt, Table
from vs_library.vsdb import queries_cli
from vs_library.database import database_cli
from vs_library.tools import pandas_extension_cli


class ImportRatingWorksheet(pandas_extension_cli.ImportSpreadsheets):
    
    """Imports the ratings worksheet file"""
    
    def __init__(self, rating_worksheet, parent=None):

        """
        Parameters
        ----------
        rating_worksheet : match.RatingWorksheet
            Controller of this NodeBundle
        """
        
        name = 'import-rating-worksheet'
        self.rating_worksheet = rating_worksheet

        super().__init__(name, parent=parent)

    def _execute(self):
        return super()._execute(self.rating_worksheet.read)


class AnalyzeRatingWorksheet(NodeBundle):
    
    """Shows worksheet summary and allow user to retain or discard columns"""
    
    def __init__(self, rating_worksheet, parent=None):

        """
        Parameters
        ----------
        rating_worksheet : match.RatingWorksheet
            Controller of this NodeBundle
        """
        
        name = 'analyze-rating-worksheet'
        self.rating_worksheet = rating_worksheet

        # OBJECTS
        self.__table_0 = Table([[]], header=False, command=Command(self._execute))
        self.__prompt_0 = Prompt("There are columns that are not required for match, would you like to keep them?")
        self.__prompt_1 = Prompt("Select the columns you want to keep:", command=Command(self._keep_selected_columns))

        # NODES
        self.__entry_node = Node(self.__table_0, name=f'{name}_table-analysis', 
                             acknowledge=True, show_hideout=True)
        self.__node_0 = Node(self.__prompt_0, name=f'{name}_column-not-required', parent=self.__entry_node,
                             show_hideout=True, clear_screen=True)
        self.__node_1 = Node(self.__prompt_1, name=f'{name}_column-to-keep', parent=self.__node_0)
        self.__exit_node = DecoyNode(name=f'{name}_last-node', parent=self.__entry_node)

        self.__node_0.adopt(self.__exit_node)
        self.__node_1.adopt(self.__exit_node)

        # CONFIGURATIONS
        self.__table_0.table_header = "Worksheet Summary"
        self.__table_0.description = "Shows the summary of the worksheet imported."

        self.__prompt_0.options = {
            '1': Command(self.rating_worksheet.concat_not_required, value="Keep all columns",
                         command=Command(lambda: self.__node_0.set_next(self.__exit_node))),
            '2': Command(lambda: self.__node_0.set_next(self.__node_1), value="Keep selected Columns",
                         command=Command(self._populate_prompt)),
            '3': Command(lambda: self.__node_0.set_next(self.__exit_node), value="Discard all")
            }

        self.__prompt_1.multiple_selection = True

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)
    
    def _execute(self):
        info = self.rating_worksheet.worksheet_info
        self.__table_0.table = [[textformat.apply('Number of Columns', emphases=['bold']), info['number_of_columns']],
                                [textformat.apply('Number of Rows', emphases=['bold']), info['number_of_rows']],
                                [textformat.apply('Columns Added', emphases=['bold']), info['columns_added']],
                                [textformat.apply('Columns not Required', emphases=['bold']), info['columns_not_required']]]

        if self.rating_worksheet.not_required_columns:
            self.__entry_node.set_next(self.__node_0)
        else:
            self.__entry_node.set_next(self.__exit_node)

    def _keep_selected_columns(self):
        selected_columns = [self.__prompt_1.options[o] for o in self.__prompt_1.responses]
        self.rating_worksheet.concat_not_required(selected_columns)
    
    def _populate_prompt(self):
        self.__prompt_1.options = {str(k): v for k, v in enumerate(self.rating_worksheet.not_required_columns, 1)}


class SelectQueryForms(NodeBundle):

    """Prompts user to select the appropriate query forms for candidate matching"""

    def __init__(self, query_tool, parent):
        
        """
        Parameters
        ----------
        query_tool : vs_library.database.QueryTool
            Controller of this NodeBundle
        """

        name = 'select-query'
        self.query_tool = query_tool
        
        # OBJECTS
        self.__prompt = Prompt("Are these rating for incumbents or for candidates?")
        
        # NODES
        self.__entry_node = Node(self.__prompt, name=f'{name}_choices', clear_screen=True, show_hideout=True)
        self.__exit_node = DecoyNode(name=f'{name}_last')

        self.__bundle_0 = queries_cli.IncumbentQueryForm(self.query_tool, parent=self.__entry_node)
        self.__bundle_1 = queries_cli.CandidateQueryForm(self.query_tool, parent=self.__entry_node)
        
        self.__bundle_0.adopt_node(self.__exit_node)
        self.__bundle_1.adopt_node(self.__exit_node)

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': Command(lambda: self.__entry_node.set_next(self.__bundle_0.entry_node), value='Incumbents'),
            '2': Command(lambda: self.__entry_node.set_next(self.__bundle_1.entry_node), value='Candidates')
            }

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)


class DatabaseConnection(NodeBundle):

    """Add, Selects, Edits and Establish connection to Vote Smart Database"""

    def __init__(self, connection_manager, connection_adapter, parent=None):

        """
        Parameters
        ----------
        connection_manager : vs_library.database.ConnectionManager
            Manages the selection and editing of connections

        connection_adapter : vs_library.database.PostgreSQL
            Responsible for establishing the connection
        """
        
        name = 'rating-database-connection'

        # OBJECTS
        self.__display_0 = Display("Connection to the Vote Smart Database is required. Proceed to connection selection...")
        self.__prompt_0 = Prompt("{message}", command=Command(lambda: self._check_for_connection(connection_manager)))
        self.__prompt_1 = Prompt("Establish connection to \'{database}\' on \'{host}\'?",
                                 command=Command(self._format_message))

        # NODES
        self.__entry_node = Node(self.__display_0, name=f'{name}_connection-required', 
                             acknowledge=True, show_hideout=True, clear_screen=True)
        self.__node_0 = Node(self.__prompt_0, name=f'{name}_pick-new-or-existing', parent=self.__entry_node, 
                             show_hideout=True, clear_screen=True)
        self.__node_1 = Node(self.__prompt_1, name=f'{name}_to-connect-or-no',
                             show_hideout=True, clear_screen=True)

        self.__bundle_0 = database_cli.AddConnection(connection_manager, parent=self.__node_0)
        self.__bundle_1 = database_cli.SelectConnection(connection_manager, parent=self.__node_0)
        self.__bundle_2 = database_cli.EstablishConnection(connection_adapter, self.__bundle_1.selected_connection, 
                                                           selection_bundle=self.__bundle_1, parent=self.__node_1)
        self.__bundle_3 = database_cli.EditConnection(connection_manager, self.__bundle_1.selected_connection, parent=self.__node_1)

        self.__node_1.adopt(self.__node_0)
        self.__bundle_0.adopt_node(self.__node_0)
        self.__bundle_1.adopt_node(self.__node_1)
        self.__bundle_3.adopt_node(self.__node_0)

        # CONFIGURATIONS
        self.__bundle_0.entry_node.clear_screen = True
        self.__bundle_2.entry_node.clear_screen = True
        self.__bundle_3.entry_node.clear_screen = True

        # traverse to AddConnection or SelectConnection NodeBundle
        self.__prompt_0.options = {
            '1': Command(lambda: self.__node_0.set_next(self.__bundle_0.entry_node), value="Create a New Connection"),
            '2': Command(lambda: self.__node_0.set_next(self.__bundle_1.entry_node), value="Use an Existing Connection")
            }

        # traverse to EstablishConnection or EditConnection NodeBundle
        self.__prompt_1.options = {
            '1': Command(lambda: self.__node_1.set_next(self.__bundle_2.entry_node), value="Yes, certainly"),
            '2': Command(lambda: self.__node_1.set_next(self.__bundle_3.entry_node), value="Edit Connection"),
            '3': Command(lambda: self.__node_1.set_next(self.__node_0), value="Return to Menu")
            }

        self.__prompt_0.exe_seq = 'before'
        self.__prompt_1.exe_seq = 'before'
        
        super().__init__(self.__entry_node, self.__bundle_2.exit_node, name=name, parent=parent)

    def _format_message(self):
        connection_info = next(iter(self.__bundle_1.selected_connection))
        self.__prompt_1.question.format_dict = {'host': connection_info.host,
                                            'database': connection_info.database}
    
    def _check_for_connection(self, connection_manager):
        connections, _ = connection_manager.read()

        if not connections:
            self.__prompt_0.question.format_dict = {'message': "There are no stored connections. Select the following:"}
            self.__prompt_0.options['2'].method = lambda: self.__node_0.engine_call('quit')
            self.__prompt_0.options['2'].value = "Exit Application"
        else:
            self.__prompt_0.question.format_dict = {'message': "Stored connections detected. Select the following:"}
            self.__prompt_0.options['2'].method = lambda: self.__node_0.set_next(self.__bundle_1.entry_node)
            self.__prompt_0.options['2'].value = "Use an Existing Connection"


class RatingMatch(NodeBundle):

    """Performs match on rating worksheet with query results"""

    def __init__(self, rating_worksheet, query_tool, pandas_matcher, query_forms=None, parent=None):

        """
        Parameters
        ----------
        rating_worksheet : match.RatingWorksheet
            Controller of this NodeBundle

        query_tool : vs_library.database.QueryTool
            Controller that contains the results of query

        pandas_matcher: vs_library.tools.pandas_extension.PandasMatcher
            Controller that manages matching with pandas

        query_forms : NodeBundle, optional
            A bundle to select query forms or a bundle before a query is executed.
            The purpose of having this bundle is so that user can change the query results
            before matching
        """
        
        name = 'rating-match'
        self.rating_worksheet = rating_worksheet
        self.query_tool = query_tool
        self.pandas_matcher = pandas_matcher
        
        # OBJECTS
        self.__prompt_0 = Prompt("Things are set. Which matching tool would you like to use?")
        self.__prompt_1 = Prompt(textformat.apply("Pandas Matcher Menu", emphases=['bold', 'underline']))
        self.__display_0 = Display("Matching in progress...", command=Command(self._execute))
        self.__table_0 = Table([], header=False)
        
        # NODES
        self.__entry_node = Node(self.__prompt_0, name=f'{name}_choose-tool',
                             show_hideout=True)
        
        self.__node_0 = Node(self.__display_0, name=f'{name}_execute', parent=self.__entry_node,
                             show_hideout=True, clear_screen=True, store=False)
        self.__node_1 = Node(self.__table_0, name=f'{name}_results', parent=self.__node_0, 
                             acknowledge=True)
        self.__node_2 = Node(self.__prompt_1, name=f"{name}_pandas-matcher", parent=self.__entry_node,
                             clear_screen=True)

        self.__bundle_0 = pandas_extension_cli.PMSettings(pandas_matcher, parent=self.__node_2)
        self.__bundle_1 = ExportMatchedDf(None, parent=self.__node_1)
        self.__bundle_2 = database_cli.ExportQueryResults(self.query_tool, parent=self.__bundle_1)

        self.__exit_node = DecoyNode(name=f'{name}_last-node', parent=self.__bundle_2.exit_node)
        
        self.__node_2.adopt(self.__node_0)

        # CONFIGURATIONS
        self.__bundle_1.entry_node.clear_screen = True
        self.__bundle_2.entry_node.clear_screen = True

        self.__table_0.table_header = "Match Results"
        self.__table_0.description = "Above shows the results of the match"

        self.__prompt_0.options = {
            '1': Command(lambda: self.__entry_node.set_next(self.__node_0), value="Record Match"),
            '2': Command(lambda: self.__entry_node.set_next(self.__node_2), value="Pandas Matcher",
                         command=Command(self._set_pandas_matcher))
            }
        
        self.__prompt_1.options = {
            '1': Command(lambda: self.__node_2.set_next(self.__bundle_0.entry_node), value="Settings"),
            'M': Command(lambda: self.__node_2.set_next(self.__node_0), value="Commence Match")
        }

        # allow user to return to selecting query forms
        if query_forms:
            self.__node_2.adopt(query_forms.entry_node)
            self.__prompt_1.options['R'] = Command(lambda: self.__node_2.set_next(query_forms.entry_node), value="Return to Query Edit")

        super().__init__(self.__entry_node, self.__exit_node, name=name, parent=parent)

    def _execute(self):
    
        if self.__prompt_0.responses == '1':
            query_records = self.query_tool.results(as_format='records')
            df, match_info = self.rating_worksheet.match_records(query_records)
            
        elif self.__prompt_0.responses == '2':
            df, match_info = self.pandas_matcher.match()
        else:
            return

        self.__bundle_1.df = df
        self._populate_table(match_info)

    def _populate_table(self, match_info):

        self.__table_0.clear()

        for k, v in match_info.items():
            self.__table_0.table.append([k, str(v)])

    def _set_pandas_matcher(self):
        self.pandas_matcher.df_to = self.rating_worksheet.df
        self.pandas_matcher.df_from = self.query_tool.results(as_format='pandas_df')


class ExportMatchedDf(pandas_extension_cli.ExportSpreadsheet):

    """Matched results can be save as a spreadsheet to the user's local host"""

    def __init__(self, df, parent=None):

        """
        Parameter
        ---------
        df : pandas.DataFrame
            This pandas.DataFrame is the result of the matched ratings worksheet
        """

        name = 'export-matched-df'

        self.df = df
        super().__init__(name, parent)


    def _execute(self):
        return super()._execute(df=self.df)
