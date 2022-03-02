# built-in
import os

# external packages
import pandas

from vs_library.tools import pandas_extension


class RatingHarvest:

    """An object to represent a rating harvest sheet
    
    Attributes
    ----------
    
    
    """

    def __init__(self):

        self.span = ''
        self.sig_id = ''
        self.usesigrating = ''
        self.ratingsession = ''
        self.ratingformat_id = ''

        self.columns = ['candidate_id', 'sig_rating', 'our_rating',
                        'span', 'sig_id', 'usesigrating', 'ratingsession', 'ratingformat_id']

        self.df = pandas.DataFrame(columns=self.columns)


    def generate(self, number_of_rows=100):

        """
        Generatea pandas.DataFrame by attributes specified in class

        Parameters
        ----------
        number_of_rows : int, default=100
            If pandas.DataFrame is empty, it will generate a dataframe with a specified number of rows
        """
        
        df = pandas.DataFrame(columns=self.columns)

        # only takes the first 3 columns
        for column in self.columns[:3]:
            if column in self.df.columns:
                if any(self.df[column]):
                    df[column] = self.df[column]

        number_of_rows = number_of_rows if not(len(df)) else len(df)

        df['span'] = [self.span] * number_of_rows
        df['sig_id'] = [self.sig_id] * number_of_rows
        df['usesigrating'] = [self.usesigrating] * number_of_rows
        df['ratingsession'] = [self.ratingsession] * number_of_rows
        df['ratingformat_id'] = [self.ratingformat_id] * number_of_rows

        self.df = df

    def export(self, filepath):
        try:
            success, message = pandas_extension.to_spreadsheet(self.df, filepath)
            return success, message

        except Exception as e:
            return False, str(e)

    def __dict__(self):
        return self.df.to_dict('records')