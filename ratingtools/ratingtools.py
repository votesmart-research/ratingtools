#!/usr/bin/env python3

# built-ins
import os

# internal packages
import ratingtools_cli
from match import match, match_cli
from harvest import harvest, harvest_cli

# external packages
from vs_library import database, cli
from vs_library.database import database_cli
from vs_library.tools import pandas_extension

from tabular_matcher import matcher
from rapidfuzz import fuzz


def main():

    # SOURCE
    rating_harvest = harvest.RatingHarvest()
    rating_worksheet_match = match.RatingWorksheet()
    rating_worksheet_harvest = match.RatingWorksheet()
    connection_manager = database.ConnectionManager(os.path.dirname(__file__))
    connection_adapter = database.PostgreSQL(None)
    query_tool = database.QueryTool(connection_adapter)
    pandas_matcher = pandas_extension.PandasMatcher()
    tabular_matcher = matcher.TabularMatcher()

    clean = lambda x: str(x).strip().lower()

    tabular_matcher.config.scorers_by_column.SCORERS.update(
                                        {'Base': lambda x,y: fuzz.ratio(clean(x), clean(y)),
                                      'Partial': lambda x,y: fuzz.partial_ratio(clean(x), clean(y)),
                                    'Token Set': lambda x,y: fuzz.token_set_ratio(clean(x), clean(y)),
                            'Partial Token Set': lambda x,y: fuzz.partial_token_set_ratio(clean(x), clean(y)),
                                   'Token Sort': lambda x,y: fuzz.token_sort_ratio(clean(x), clean(y)),
                           'Partial Token Sort': lambda x,y: fuzz.partial_token_sort_ratio(clean(x), clean(y)),
                                     'Weighted': lambda x,y: fuzz.WRatio(clean(x), clean(y)),
                                        })
    tabular_matcher.config.scorers_by_column.default = 'Weighted'


    # INTERFACE / CONTROLLER
    import_rating_worksheet_match = match_cli.ImportRatingWorksheet(rating_worksheet_match)
    analyze_rating_worksheet = match_cli.AnalyzeRatingWorksheet(rating_worksheet_match, parent=import_rating_worksheet_match)
    database_connection = match_cli.DatabaseConnection(connection_manager, connection_adapter, parent=analyze_rating_worksheet)
    query_forms = match_cli.SelectQueryForms(query_tool, parent=database_connection)
    execute_query = database_cli.QueryExecution(query_tool, query_form=query_forms, parent=query_forms)
    rating_match = match_cli.RatingMatch(rating_worksheet_match, query_tool, tabular_matcher, query_forms=query_forms, parent=execute_query)

    import_rating_worksheet_harvest = match_cli.ImportRatingWorksheet(rating_worksheet_harvest)
    generate_harvest = harvest_cli.GenerateHarvest(rating_harvest, rating_worksheet_harvest, parent=import_rating_worksheet_harvest)

    intro_bundle = ratingtools_cli.IntroToRatingTools(import_rating_worksheet_match, import_rating_worksheet_harvest)

    # CONFIGURATIONS
    import_rating_worksheet_match.entry_node.clear_screen = True
    import_rating_worksheet_harvest.entry_node.clear_screen = True
    analyze_rating_worksheet.entry_node.clear_screen = True
    generate_harvest.entry_node.clear_screen = True
    execute_query.entry_node.clear_screen = True

    engine = cli.Engine(intro_bundle.entry_node)
    engine.run(loop=True)


if __name__ == "__main__":
    main()