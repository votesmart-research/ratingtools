# built-in
import os

# external packages
import pandas

from vs_library.tools import pandas_functions


class RatingHarvest:

    def __init__(self):

        self.span = ''
        self.sig_id = ''
        self.usesigrating = ''
        self.ratingsession = ''
        self.ratingformat_id = ''

        self.columns = ['candidate_id', 'sig_rating', 'our_rating',
                        'span', 'sig_id', 'usesigrating', 'ratingsession', 'ratingformat_id']

        self.df = pandas.DataFrame(columns=self.columns)


    def generate(self, specified_rows=100):
        
        df = pandas.DataFrame(columns=self.columns)

        for column in self.columns[:3]:
            if column in self.df.columns:
                if any(self.df[column]):
                    df[column] = self.df[column]

        number_of_rows = specified_rows if not(len(df)) else len(df)

        df['span'] = [self.span] * number_of_rows
        df['sig_id'] = [self.sig_id] * number_of_rows
        df['usesigrating'] = [self.usesigrating] * number_of_rows
        df['ratingsession'] = [self.ratingsession] * number_of_rows
        df['ratingformat_id'] = [self.ratingformat_id] * number_of_rows

        self.df = df

    def export(self, filepath):
        try:
            success, message = pandas_functions.to_spreadsheet(self.df, filepath)
            return success, message

        except Exception as e:
            return False, str(e)

    def __dict__(self):
        return self.df.to_dict('records')