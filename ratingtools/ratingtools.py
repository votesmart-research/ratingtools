#!/usr/bin/env python3

# internal packages
import ratingtools_cli
import match
import match_cli
import harvest
import harvest_cli

# external packages
from vs_library import database, cli
from vs_library.database import database_cli


# SOURCE
ratings_harvest = harvest.RatingHarvest()
ratings_worksheet = match.RatingWorksheet()
connection_manager = database.ConnectionManager()
connection_adapter = database.PostgreSQL(None)
query_tool = database.QueryTool(connection_adapter)

# INTERFACE / CONTROLLER
import_rating_worksheet_match = match_cli.ImportRatingWorksheet(ratings_worksheet)
analyze_rating_worksheet = match_cli.AnalyzeRatingWorksheet(ratings_worksheet, parent=import_rating_worksheet_match)
database_connection = match_cli.DatabaseConnection(connection_manager, connection_adapter, parent=analyze_rating_worksheet)
query_forms = match_cli.SelectQueryForms(query_tool, parent=database_connection)
execute_query = database_cli.QueryExecution(query_tool, query_bundle=query_forms, parent=query_forms)
rating_match = match_cli.RatingMatch(query_tool, ratings_worksheet, ratings_harvest, query_bundle=query_forms, parent=execute_query)

import_ratings_worksheet_harvest = match_cli.ImportRatingWorksheet(ratings_worksheet)
generate_harvest = harvest_cli.GenerateHarvest(ratings_harvest, ratings_worksheet, parent=import_ratings_worksheet_harvest)

intro_bundle = ratingtools_cli.IntroToRatingTools(import_rating_worksheet_match, import_ratings_worksheet_harvest)

# CONFIGURATIONS
import_rating_worksheet_match.entry_node.clear_screen = True
import_ratings_worksheet_harvest.entry_node.clear_screen = True
analyze_rating_worksheet.entry_node.clear_screen = True
generate_harvest.entry_node.clear_screen=True
execute_query.entry_node.clear_screen = True

engine = cli.Engine(intro_bundle.entry_node)

if __name__ == "__main__":
    engine.run()
