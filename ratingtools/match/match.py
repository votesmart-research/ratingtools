
# external packages
import pandas
from tqdm import tqdm
from vs_library.tools import recordmatch, pandas_extension


class RatingWorksheet:

    """An object to represent a rating worksheet"""

    def __init__(self):

        self.columns = ['lastname', 'firstname', 'middlename', 'suffix', 'nickname',
                        'party', 'state', 'state_id','office', 'district',
                        'candidate_id', 'sig_rating', 'our_rating']

        self.__df = pandas.DataFrame(columns=self.columns)

        self.__columns_added = []
        self.__not_required_df = pandas.DataFrame()

    @property
    def df(self):
        return self.__df

    @df.setter
    def df(self, df):

        """Sets the df by only taking required columns and add the necessary columns"""

        # self.__df.drop(self.__df.index, inplace=True)
        # columns_added = []
        # for column in self.columns:
        #     if column in df.columns:
        #         self.__df[column] = df[column]
        #     else:
        #         columns_added.append(column)
        #         self.__df[column] = [''] * len(df)
        # self.__columns_added = columns_added
        
        self.__df = df
        self.__not_required_df = df[[c for c in df.columns if c not in self.columns]]

    @property
    def not_required_columns(self):

        """Returns a list of columns not required by the worksheet"""

        return list(self.__not_required_df.columns)

    @property
    def worksheet_info(self):

        """Return a dictionary describing the structure of the worksheet"""

        return {'number_of_columns': len(self.__df.columns),
                'number_of_rows': len(self.__df),
                # 'columns_added': ', '.join(map(str, self.__columns_added)),
                'columns_not_required': ', '.join(map(str, self.__not_required_df.columns))}

    
    def read(self, filepaths):
        
        """Imports a spreadsheet file and sets this instance's pandas.DataFrame"""

        try:
            dfs = []
            messages = []

            for filepath in filepaths:
                df, message = pandas_extension.read_spreadsheet(filepath, dtype=str)
                dfs.append(df)
                messages.append(message)

            concat_df = pandas.concat(dfs, ignore_index=True)

            if concat_df.empty:
                return False, "\n".join(messages)

            self.df = concat_df
            self.df.fillna(value='', inplace=True)
            return True, "\n".join(messages)

        except Exception as e:
            return False, str(e)

    def concat_not_required(self, selected_columns=None):
        
        """Concatenate self.__df with not required columns"""

        if not selected_columns:
            self.__df = pandas.concat([self.__df, self.__not_required_df], axis=1)
        else:
            self.__df = pandas.concat([self.__df, self.__not_required_df[selected_columns]], axis=1)


    def generate(self, number_of_rows=100):

        """
        Generates pandas.DataFrame using columns from self.__df

        Parameters
        ----------
        number_of_rows : int, default=100
            If self.__df is empty, it will generate a dataframe with the specified number of rows
        """

        df = pandas.DataFrame(columns=self.columns)

        for column in self.columns:
            if column in self.__df.columns:
                if any(self.__df[column]):
                    df[column] = self.__df[column]

        if len(df) and number_of_rows > len(df):
            df_2 = pandas.DataFrame([[''] * len(self.columns)] * (number_of_rows-len(self.__df)), columns=self.columns)
            df = pandas.concat([df, df_2]).reset_index(drop=True)

        elif len(df) and number_of_rows < len(df):
            number_of_rows = len(df)
        
        else:
            pass

        self.__df = df
