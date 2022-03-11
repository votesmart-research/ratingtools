
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

        columns_added = []
        self.__df.drop(self.__df.index, inplace=True)
        
        for column in self.columns:
            if column in df.columns:
                self.__df[column] = df[column]
            else:
                columns_added.append(column)
                self.__df[column] = [''] * len(df)

        self.__columns_added = columns_added
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
                'columns_added': ', '.join(map(str, self.__columns_added)),
                'columns_not_required': ', '.join(map(str, self.__not_required_df.columns))}

    
    def read(self, filepath):
        
        """Imports a spreadsheet file and sets this instance's pandas.DataFrame"""

        try:
            df, message = pandas_extension.read_spreadsheet(filepath)

            if df.empty:
                return False, message
            else:
                pass

            self.df = df

            return True, message

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

    def match_records(self, records, column_to_get='candidate_id'):

        """
        Matches worksheet with other records to obtain the 'candidate_id'

        This type of matching has a very specific process that is intended to maximize
        the efficiency of matches that pertains to ratings worksheet. It works best
        when match with a similar set of data.

        Parameters
        ----------
        records : list
            A list of dictionaries such that [record_1=dict(), record_2=dict()...]
            Each dictionary should contain the same keys
        
        columns_to_get : list
            Contains the list of column names that brings over to the self.__df from
            matching records

        Returns
        -------
        (pandas.DataFrame, dict)
        """

        if 'match_status' not in self.__df.columns:
            self.__df['match_status'] = [''] * len(self.__df)

        match_info = {'Rows Matched': 0,
                      'Needs Review': 0}

        # an inside funtion to determine if the 
        def apply_match(X, results, match_status):
            nonlocal match_info

            if len(results) == 1:
                X[column_to_get] = results[0][column_to_get]
                X['match_status'] = match_status
                match_info['Rows Matched'] += 1
                return True
            else:
                return False

        df_records = self.__df.to_dict('records')
        df_records_uniqueness = recordmatch.uniqueness(df_records)

        other_info = ['state', 'party', 'district', 'office']
        
        for X in tqdm(df_records):
            
            # lastnames are the crucial distinction of candidates
            LAST = recordmatch.match(records, X, column='lastname', threshold=1.0)

            if len(LAST) == 1:
                # this section is to capture false positives
                LAST_FUZZY_FIRST = recordmatch.match(LAST, X, column='firstname', threshold=0.7) 
                
                COMBINED_LAST = recordmatch.combined(LAST, X, other_info, df_records_uniqueness, 
                                                      threshold=0.6)
                LAST_CROSS_FIRST = recordmatch.cross(LAST, X, 'firstname', ['nickname','middlename'], 
                                                      threshold=0.8)

                if LAST_FUZZY_FIRST:
                    apply_match(X, LAST_FUZZY_FIRST, 'LAST_FUZZY-FIRST')
                elif COMBINED_LAST:
                    apply_match(X, COMBINED_LAST, 'COMBINED_LAST')
                elif LAST_CROSS_FIRST:
                    apply_match(X, LAST_CROSS_FIRST, 'LAST_CROSS-FIRST')
                else:
                    apply_match(X, LAST, 'REVIEW')
                    match_info['Needs Review'] += 1
                
                continue

            elif len(LAST) > 1:

                LAST_FIRST = recordmatch.match(LAST, X, column='firstname', threshold=1.0)
                # True of False, if the match applies, continue to next on loop
                continuable = apply_match(X, LAST_FIRST, 'LAST_FIRST')

                if not continuable and LAST_FIRST:
                    LAST_COMBINED_FIRST = recordmatch.combined(LAST_FIRST, X, other_info, df_records_uniqueness, 
                                                                threshold=0.6)
                    continuable = apply_match(X, LAST_COMBINED_FIRST, 'LAST_COMBINED-FIRST')

                if not continuable:
                    LAST_FUZZY_FIRST = recordmatch.match(LAST, X, column='firstname', threshold=0.7)
                    continuable = apply_match(X, LAST_FUZZY_FIRST, 'LAST_FUZZY-FIRST')

                if not continuable and LAST_FUZZY_FIRST:
                    COMBINED_LAST_FUZZY_FIRST = recordmatch.combined(LAST_FUZZY_FIRST, X, other_info, df_records_uniqueness, 
                                                                      threshold=0.5)
                    continuable = apply_match(X, COMBINED_LAST_FUZZY_FIRST, 'COMBINED_LAST_FUZZY-FIRST')

                if not continuable:
                    COMBINED_LAST = recordmatch.combined(LAST, X, other_info, df_records_uniqueness, 
                                                          threshold=0.6)
                    continuable = apply_match(X, COMBINED_LAST, 'COMBINED_LAST')
                                
                if not continuable:
                    LAST_CROSS_FIRST = recordmatch.cross(LAST, X, 'firstname', ['nickname','middlename'], 
                                                         threshold=1.0)
                    continuable = apply_match(X, LAST_CROSS_FIRST, 'LAST_CROSS-FIRST')

                if not continuable and LAST_CROSS_FIRST:
                    COMBINED_LAST_CROSS_FIRST = recordmatch.combined(LAST_CROSS_FIRST, X, other_info, df_records_uniqueness, 
                                                                     threshold=0.6)
                    continuable = apply_match(X, COMBINED_LAST_CROSS_FIRST, 'COMBINED_LAST_CROSS-FIRST')
                                    
                if not continuable:
                    LAST_FUZZY_CROSS_FIRST = recordmatch.cross(LAST, X, 'firstname', ['nickname','middlename'], 
                                                                threshold=0.8)
                    continuable = apply_match(X, LAST_FUZZY_CROSS_FIRST, 'LAST_FUZZY-CROSS-FIRST')

                if not continuable and LAST_FUZZY_CROSS_FIRST:
                    COMBINED_LAST_FUZZY_CROSS_FIRST = recordmatch.combined(LAST_FUZZY_CROSS_FIRST, X, other_info, df_records_uniqueness, 
                                                                            threshold=0.6)
                    continuable = apply_match(X, COMBINED_LAST_FUZZY_CROSS_FIRST, 'COMBINED_LAST_FUZZY-CROSS-FIRST')

            else:
                X['match_status'] = ''

        # pandas.DataFrame for easier parsing of data
        df_matched = pandas.DataFrame.from_records(df_records)

        dupe_index, dupes = pandas_extension.get_column_dupes(df_matched, column_to_get)
        blank_index, blanks = pandas_extension.get_column_blanks(df_matched, column_to_get)

        # alter the match_status to reflect the error
        for d_i in dupe_index:
            df_matched.at[d_i, 'match_status'] = 'DUPLICATE'
        
        for b_i in blank_index:
            df_matched.at[b_i, 'match_status'] = 'UNMATCHED'

        rows_matched = match_info['Rows Matched']
        match_info['Duplicates'] = len(dupes)
        match_info['Unmatched'] = len(blanks)
        match_info['Match Score'] = round(rows_matched/len(self.__df)*100,2)

        return df_matched, match_info
