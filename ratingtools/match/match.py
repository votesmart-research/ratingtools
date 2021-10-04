
# external packages
import pandas
from tqdm import tqdm
from vs_library.tools import recordmatch, pandas_functions


class RatingWorksheet:

    def __init__(self):

        self.columns = ['lastname', 'firstname', 'middlename', 'suffix', 'nickname',
                        'party', 'state', 'office', 'district',
                        'candidate_id', 'sig_rating', 'our_rating']

        self.df = pandas.DataFrame(columns=self.columns)

        self.__columns_added = []
        self.__not_required_df = pandas.DataFrame()

    @property
    def not_required_columns(self):
        return list(self.__not_required_df.columns)

    @property
    def worksheet_info(self):
        info = {'number_of_columns': len(self.df.columns),
                'number_of_rows': len(self.df),
                'columns_added': ', '.join(map(str, self.__columns_added)),
                'columns_not_required': ', '.join(map(str, self.__not_required_df.columns))}
        return info
    
    def read(self, filepath):
        
        try:
            df, message = pandas_functions.read_spreadsheet(filepath)

            if df.empty:
                return message
            else:
                pass

            columns_added = []
            self.df.drop(self.df.index, inplace=True)
            
            for column in self.columns:
                if column in df.columns:
                    self.df[column] = df[column]
                else:
                    columns_added.append(column)
                    self.df[column] = [''] * len(df)

            self.__columns_added = columns_added
            self.__not_required_df = df[[c for c in df.columns if c not in self.columns]]

            return True, message

        except Exception as e:
            return False, str(e)

    def concat_not_required(self, selected_columns=None):
        
        if not selected_columns:
            self.df = pandas.concat([self.df, self.__not_required_df], axis=1)
        else:
            self.df = pandas.concat([self.df, self.__not_required_df[selected_columns]], axis=1)


    def generate(self, number_of_rows=100):

        df = pandas.DataFrame(columns=self.columns)

        for column in self.columns:
            if column in self.df.columns:
                if any(self.df[column]):
                    df[column] = self.df[column]

        if len(df) and number_of_rows > len(df):
            df_2 = pandas.DataFrame([[''] * len(self.columns)] * (number_of_rows-len(self.df)), columns=self.columns)
            df = pandas.concat([df, df_2]).reset_index(drop=True)

        elif len(df) and number_of_rows < len(df):
            number_of_rows = len(df)
        
        else:
            pass

        self.df = df

    def match_with(self, records, column_to_get='candidate_id'):

        if 'match_status' not in self.df.columns:
            self.df['match_status'] = [''] * len(self.df)

        matched_count = 0
        review_count = 0

        def apply_match(X, results, match_status):
            nonlocal matched_count

            if len(results) == 1:
                X[column_to_get] = results[0][column_to_get]
                X['match_status'] = match_status
                matched_count += 1
                return True
            else:
                return False

        df_records = self.df.to_dict('records')
        df_records_uniqueness = recordmatch.uniqueness(df_records)

        other_info = ['state', 'party', 'district', 'office']
        
        for X in tqdm(df_records):

            LAST = recordmatch.match(records, X, column='lastname', threshold=1.0)

            if len(LAST) == 1:

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
                    review_count += 1
                
                continue

            elif len(LAST) > 1:

                LAST_FIRST = recordmatch.match(LAST, X, column='firstname', threshold=1.0)
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

        matched_df = pandas.DataFrame.from_records(df_records)

        match_score = round(matched_count/len(self.df)*100, 2)

        dupe_index, dupes = pandas_functions.get_column_dupes(matched_df, column_to_get)
        blank_index, blanks = pandas_functions.get_column_blanks(matched_df, column_to_get)

        for d_i in dupe_index:
            matched_df.at[d_i, 'match_status'] = 'DUPLICATE'
        
        for b_i in blank_index:
            matched_df.at[b_i, 'match_status'] = 'UNMATCHED'

        match_info = {'score': match_score,
                      'duplicates': len(dupes),
                      'unmatched': len(blanks),
                      'review': review_count}

        return matched_df, match_info

    
    def __dict__(self):
        return self.df.to_dict('records')
