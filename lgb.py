import re
import gc
import string

import pandas as pd
import numpy as np

from scipy.sparse import csr_matrix, hstack

from sklearn.preprocessing import OneHotEncoder, LabelEncoder

import lightgbm as lgb

from cv import run_cv_model
from utils import print_step, rmse
from cache import get_data, is_in_cache, load_cache, save_in_cache


# LGB Model Definition
def runLGB(train_X, train_y, test_X, test_y, test_X2):
    d_train = lgb.Dataset(train_X, label=train_y)
    d_valid = lgb.Dataset(test_X, label=test_y)
    watchlist = [d_train, d_valid]
    params = {'learning_rate': 0.05,
              'application': 'regression',
              'num_leaves': 31,
              'verbosity': -1,
              'metric': 'rmse',
              'data_random_seed': 3,
              'bagging_fraction': 0.8,
              'feature_fraction': 0.8,
              'nthread': 3,
              'lambda_l1': 1,
              'lambda_l2': 1}
    model = lgb.train(params,
                      train_set=d_train,
                      num_boost_round=2000,
                      valid_sets=watchlist,
                      verbose_eval=100)
    print_step('Predict 1/2')
    pred_test_y = model.predict(test_X)
    print_step('Predict 2/2')
    pred_test_y2 = model.predict(test_X2)
    return pred_test_y, pred_test_y2


print('~~~~~~~~~~~~~~~~~~~')
print_step('Importing Data')
train, test = get_data()

#if not is_in_cache('cleaned'):
print('~~~~~~~~~~~~~~~')
print_step('Subsetting')
target = train['deal_probability']
train_id = train['item_id']
test_id = test['item_id']
train.drop(['deal_probability', 'item_id'], axis=1, inplace=True)
test.drop(['item_id'], axis=1, inplace=True)

print('~~~~~~~~~~~~')
print_step('Merging')
merge = pd.concat([train, test])

print('~~~~~~~~~~~~~~~')
print_step('Impute 1/6')
merge['param_1_missing'] = merge['param_1'].isna().astype(int)
merge['param_1'].fillna('missing', inplace=True)
print_step('Impute 2/6')
merge['param_2_missing'] = merge['param_2'].isna().astype(int)
merge['param_2'].fillna('missing', inplace=True)
print_step('Impute 3/6')
merge['param_3_missing'] = merge['param_3'].isna().astype(int)
merge['param_3'].fillna('missing', inplace=True)
print_step('Impute 4/6')
merge['price_missing'] = merge['price'].isna().astype(int)
merge['price'].fillna(merge['price'].median(), inplace=True)
merge['has_price'] = (merge['price'] > 0).astype(int)
print_step('Impute 5/6')
merge['description_missing'] = merge['description'].isna().astype(int)
merge['description'].fillna('', inplace=True)
print_step('Impute 6/6')
merge['image_missing'] = merge['image'].isna().astype(int)
merge['image_top_1'] = merge['image_top_1'].astype('str').fillna('missing')

print('~~~~~~~~~~~~~~')
print_step('Basic NLP 1/32')
merge['num_words_description'] = merge['description'].apply(lambda x: len(str(x).split()))
print_step('Basic NLP 2/32')
merge['num_words_title'] = merge['title'].apply(lambda x: len(str(x).split()))
print_step('Basic NLP 3/32')
merge['num_chars_description'] = merge['description'].apply(lambda x: len(str(x)))
print_step('Basic NLP 4/32')
merge['num_chars_title'] = merge['title'].apply(lambda x: len(str(x)))
print_step('Basic NLP 5/32')
merge['num_capital_description'] = merge['description'].apply(lambda x: len([c for c in x if c.isupper()]))
print_step('Basic NLP 6/32')
merge['num_capital_title'] = merge['title'].apply(lambda x: len([c for c in x if c.isupper()]))
print_step('Basic NLP 7/32')
merge['num_lowercase_description'] = merge['description'].apply(lambda x: len([c for c in x if c.islower()]))
print_step('Basic NLP 8/32')
merge['num_lowercase_title'] = merge['title'].apply(lambda x: len([c for c in x if c.islower()]))
print_step('Basic NLP 9/32')
merge['capital_per_char_description'] = merge['num_capital_description'] / merge['num_chars_description']
merge['capital_per_char_description'].fillna(0, inplace=True)
print_step('Basic NLP 10/32')
merge['capital_per_char_title'] = merge['num_capital_title'] / merge['num_chars_title']
merge['capital_per_char_title'].fillna(0, inplace=True)
print_step('Basic NLP 11/32')
merge['num_punctuations'] = merge['description'].apply(lambda x: len([c for c in str(x) if c in string.punctuation]))
print_step('Basic NLP 12/32')
merge['punctuation_per_char'] = merge['num_punctuations'] / merge['num_chars_description']
merge['punctuation_per_char'].fillna(0, inplace=True)
print_step('Basic NLP 13/32')
merge['num_words_upper_description'] = merge['description'].apply(lambda x: len([w for w in str(x).split() if w.isupper()]))
print_step('Basic NLP 14/32')
merge['num_words_upper_title'] = merge['title'].apply(lambda x: len([w for w in str(x).split() if w.isupper()]))
print_step('Basic NLP 15/32')
merge['num_words_lower_description'] = merge['description'].apply(lambda x: len([w for w in str(x).split() if w.islower()]))
print_step('Basic NLP 16/32')
merge['num_words_lower_title'] = merge['title'].apply(lambda x: len([w for w in str(x).split() if w.islower()]))
print_step('Basic NLP 17/32')
merge['num_words_entitled_description'] = merge['description'].apply(lambda x: len([w for w in str(x).split() if w.istitle()]))
print_step('Basic NLP 18/32')
merge['num_words_entitled_title'] = merge['title'].apply(lambda x: len([w for w in str(x).split() if w.istitle()]))
print_step('Basic NLP 19/32')
merge['chars_per_word_description'] = merge['num_chars_description'] / merge['num_words_description']
merge['chars_per_word_description'].fillna(0, inplace=True)
print_step('Basic NLP 20/32')
merge['chars_per_word_title'] = merge['num_chars_title'] / merge['num_words_title']
merge['chars_per_word_title'].fillna(0, inplace=True)
print_step('Basic NLP 21/32')
merge['description_words_per_title_words'] = merge['num_words_description'] / merge['num_words_title']
print_step('Basic NLP 22/32')
merge['description_words_per_title_words'].fillna(0, inplace=True)
print_step('Basic NLP 23/32')
merge['description_chars_per_title_chars'] = merge['num_chars_description'] / merge['num_chars_title']
print_step('Basic NLP 24/32')
merge['description_chars_per_title_chars'].fillna(0, inplace=True)
print_step('Basic NLP 25/32')
merge['num_english_chars_description'] = merge['description'].apply(lambda ss: len([s for s in ss.lower().translate(ss.maketrans('', '', string.punctuation)).replace('\n', '').replace(' ', '') if s in string.ascii_lowercase]))
print_step('Basic NLP 26/32')
merge['num_english_chars_title'] = merge['title'].apply(lambda ss: len([s for s in ss.lower().translate(ss.maketrans('', '', string.punctuation)).replace('\n', '').replace(' ', '') if s in string.ascii_lowercase]))
print_step('Basic NLP 27/32')
merge['english_chars_per_char_description'] = merge['num_english_chars_description'] / merge['num_chars_description']
merge['english_chars_per_char_description'].fillna(0, inplace=True)
print_step('Basic NLP 28/32')
merge['english_chars_per_char_title'] = merge['num_english_chars_title'] / merge['num_chars_title']
merge['english_chars_per_char_title'].fillna(0, inplace=True)
print_step('Basic NLP 29/32')
merge['num_english_words_description'] = merge['description'].apply(lambda ss: len([w for w in ss.lower().translate(ss.maketrans('', '', string.punctuation)).replace('\n', ' ').split(' ') if all([s in string.ascii_lowercase for s in w]) and len(w) > 0]))
print_step('Basic NLP 30/32')
merge['num_english_words_title'] = merge['title'].apply(lambda ss: len([w for w in ss.lower().translate(ss.maketrans('', '', string.punctuation)).replace('\n', ' ').split(' ') if all([s in string.ascii_lowercase for s in w]) and len(w) > 0]))
print_step('Basic NLP 31/32')
merge['english_words_per_char_description'] = merge['num_english_words_description'] / merge['num_words_description']
merge['english_words_per_char_description'].fillna(0, inplace=True)
print_step('Basic NLP 32/32')
merge['english_words_per_char_title'] = merge['num_english_words_title'] / merge['num_words_title']
merge['english_words_per_char_title'].fillna(0, inplace=True)

print('~~~~~~~~~~~~~~~~~~~~')
print_step('Activation Date')
merge['activation_date'] = pd.to_datetime(merge['activation_date'])
merge['day_of_week'] = merge['activation_date'].dt.weekday
merge['weekend'] = ((merge['day_of_week'] == 5) | (merge['day_of_week'] == 6)).astype(int)

print('~~~~~~~~~~~~~')
print_step('Dropping')
drops = ['activation_date', 'title', 'description']
merge.drop(drops, axis=1, inplace=True)
currently_unused = ['user_id', 'image']
merge.drop(currently_unused, axis=1, inplace=True)

print('~~~~~~~~~~~~')
print_step('Dummies 1/2')
print(merge.shape)
dummy_cols = ['parent_category_name', 'category_name', 'user_type', 'param_1',
              'param_2', 'param_3', 'image_top_1', 'day_of_week', 'region', 'city']
for col in dummy_cols:
    le = LabelEncoder()
    merge[col] = le.fit_transform(merge[col])
print_step('Dummies 2/2')
ohe = OneHotEncoder(categorical_features=[merge.columns.get_loc(c) for c in dummy_cols])
merge = ohe.fit_transform(merge)
print(merge.shape)

print_step('Unmerge')
merge = merge.tocsr()
dim = train.shape[0]
train_ = merge[:dim]
test_ = merge[dim:]


print('~~~~~~~~~~~~')
print_step('Run LGB')
print(train_.shape)
print(test_.shape)

results = run_cv_model(train_, test_, target, runLGB, rmse, 'lgb')
import pdb
pdb.set_trace()

#print('~~~~~~~~~~')
#print_step('Cache')
#save_in_cache('lvl1_lgb', train, test)

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print_step('Prepping submission file')
submission = pd.DataFrame()
submission['item_id'] = test_id
submission['deal_probability'] = results['test'].clip(0.0, 1.0)
submission.to_csv('submit/submit_lgb.csv', index=False)
print_step('Done!')

# LGB: no text, geo, date, image, param data, or item_seq_number                   - Dim 51,   5CV 0.2313, Submit 0.235, Delta -.00371
# LGB: +missing data, +OHE params (no text, geo, date, image, or item_seq_number)  - Dim 5057, 5CV 0.2269, Submit 0.230, Delta -.00306
# LGB: +basic NLP (no other text, geo, date, image, or item_seq_number)            - Dim 5078, 5CV 0.2261, Submit 0.229, Delta -.00293  <a9e424c>
# LGB: +date (no other text, geo, image, or item_seq_number)                       - Dim 5086, 5CV 0.2261, Submit ?                     <f6c28f2>
# LGB: +OHE city and region (no other text, image, or item_seq_number)             - Dim 6866, 5CV 0.2254, Submit ?                     <531df17>
# LGB: +item_seq_number (no other text or image)                                   - Dim 6867, 5CV 0.2252, Submit ?                     <624f1a4>
# LGB: +more basic NLP (no other text or image)                                    - Dim 6877, 5CV 0.2251, Submit ?
# LGB: +                                                                           - Dim ?, 5CV ?, Submit ?

# CURRENT
# [2018-04-26 14:53:32.834101] lgb cv scores : [0.2256567380989068, 0.2246736622115502, 0.22490071131939054, 0.22484800048773446, 0.22533893816001835]
# [2018-04-26 14:53:32.840178] lgb mean cv score : 0.22508361005552008
# [2018-04-26 14:53:32.841407] lgb std cv score : 0.0003607462393285434


# TODO
# TFIDF concat(title, description) -> Ridge
    # https://www.kaggle.com/iggisv9t/basic-tfidf-on-text-features-0-233-lb
# TFIDF concat(title, description, param_1, param_2, param_3, parent_category_name, category_name) -> Ridge
# Frequency encode user_id, city, region, parent_category_name, category_name, param_1, param_2, param_3, image_top_1, day_of_week
# encode(mean, median, std, min, max) of target, price, item_seq_number with user_id
# encode(mean, median, std, min, max) of target, price with city, region, parent_category_name, category_name, param_1, param_2, param_3, image_top_1, user_type, day_of_week
# Image analysis
    # img_hash.py?
	# pic2vec
    # https://www.kaggle.com/classtag/extract-avito-image-features-via-keras-vgg16)
    # Contrast? https://dsp.stackexchange.com/questions/3309/measuring-the-contrast-of-an-image
    # https://www.pyimagesearch.com/2014/03/03/charizard-explains-describe-quantify-image-using-feature-vectors/
    # NNs?
# Check feature impact and tuning in DR
# Tune models some
# Train classification and regression
# Vary model
	# Train Ridge on text, include into as-is LGB
    # Take LGB, add text OHE with Ridge / SelectKBest
    # Take LGB, add text OHE with SVD + embedding
    # OHE everything into Ridge and then take just encoded categorical and numeric into LGB and boost with LGB
	# OHE everything into LGB except text, then use text and residuals and boost with Ridge
# Train more models (Ridge, FM, Ridge, NNs)
# Look to DonorsChoose
    # https://www.kaggle.com/qinhui1999/deep-learning-is-all-you-need-lb-0-80x/code
    # https://www.kaggle.com/fizzbuzz/the-all-in-one-model
    # https://www.kaggle.com/emotionevil/beginners-workflow-meanencoding-lgb-nn-ensemble
    # https://www.kaggle.com/safavieh/ultimate-feature-engineering-xgb-lgb-nn
    # https://www.kaggle.com/jagangupta/understanding-approval-donorschoose-eda-fe-eli5
    # https://www.kaggle.com/fizzbuzz/beginner-s-guide-to-capsule-networks
    # https://www.kaggle.com/nicapotato/abc-s-of-tf-idf-boosting-0-798
# https://www.kaggle.com/c/avito-duplicate-ads-detection
# Use train_active and test_active somehow?
