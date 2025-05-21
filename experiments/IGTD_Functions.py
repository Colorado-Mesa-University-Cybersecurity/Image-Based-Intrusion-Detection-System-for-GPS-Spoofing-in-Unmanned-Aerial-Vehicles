from scipy.stats import spearmanr, rankdata
from scipy.spatial.distance import pdist, squareform

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import shutil
import time
import pickle as cp  # Changed from _pickle
import sys
from astropy.stats import median_absolute_deviation


def select_features_by_variation(data, variation_measure='var', threshold=None, num=None, draw_histogram=False,
                                 bins=100, log=False):
    '''
    This function evaluates the variations of individual features and returns the indices of features with large
    variations. Missing values are ignored in evaluating variation.

    Parameters:
    -----------
    data: numpy array or pandas data frame of numeric values, with a shape of [n_samples, n_features].
    variation_measure: string indicating the metric used for evaluating feature variation. 'var' indicates variance;
        'std' indicates standard deviation; 'mad' indicates median absolute deviation. Default is 'var'.
    threshold: float. Features with a variation larger than threshold will be selected. Default is None.
    num: positive integer. It is the number of features to be selected based on variation.
        The number of selected features will be the smaller of num and the total number of
        features with non-missing variations. Default is None. threshold and num can not take values
        and be used simultaneously.
    draw_histogram: boolean, whether to draw a histogram of feature variations. Default is False.
    bins: positive integer, the number of bins in the histogram. Default is the smaller of 50 and the number of
        features with non-missing variations.
    log: boolean, indicating whether the histogram should be drawn on log scale.


    Returns:
    --------
    indices: 1-D numpy array containing the indices of selected features. If both threshold and
        num are None, indices will be an empty array.
    '''

    if isinstance(data, pd.DataFrame):
        data = data.values
    elif not isinstance(data, np.ndarray):
        print('Input data must be a numpy array or pandas data frame')
        sys.exit(1)

    if variation_measure == 'std':
        v_all = np.nanstd(a=data, axis=0)
    elif variation_measure == 'mad':
        v_all = median_absolute_deviation(data=data, axis=0, ignore_nan=True)
    else:
        v_all = np.nanvar(a=data, axis=0)

    indices = np.where(np.invert(np.isnan(v_all)))[0]
    v = v_all[indices]

    if draw_histogram:
        if len(v) < 50:
            print('There must be at least 50 features with variation measures to draw a histogram')
        else:
            bins = int(min(bins, len(v)))
            _ = plt.hist(v, bins=bins, log=log)
            plt.show()

    if threshold is None and num is None:
        return np.array([])
    elif threshold is not None and num is not None:
        print('threshold and num can not be used simultaneously. Only one of them can take a real value')
        sys.exit(1)

    if threshold is not None:
        indices = indices[np.where(v > threshold)[0]]
    else:
        n_f = int(min(num, len(v)))
        indices = indices[np.argsort(-v)[:n_f]]

    indices = np.sort(indices)

    return indices


def min_max_transform(data):
    '''
    This function does a linear transformation of each feature, so that the minimum and maximum values of a
    feature are 0 and 1, respectively.

    Input:
    data: an input data array with a size of [n_sample, n_feature]
    Return:
    norm_data: the data array after transformation
    '''

    norm_data = np.empty(data.shape)
    norm_data.fill(np.nan)
    for i in range(data.shape[1]):
        v = data[:, i].copy()
        if np.max(v) == np.min(v):
            norm_data[:, i] = 0
        else:
            v = (v - np.min(v)) / (np.max(v) - np.min(v))
            norm_data[:, i] = v
    return norm_data


def generate_feature_distance_ranking(data, method='Pearson'):
    '''
    This function generates ranking of distances/dissimilarities between features for tabular data.

    Input:
    data: input data, n_sample by n_feature
    method: 'Euclidean' calculates similarity between features based on Euclidean distance;
        'Pearson' uses Pearson correlation coefficient to evaluate similarity between features;
        'Spearman' uses Spearman correlation coefficient to evaluate similarity between features;
        'set' uses Jaccard index to evaluate similarity between features that are binary variables.

    Return:
    ranking: symmetric ranking matrix based on dissimilarity
    corr: matrix of distances between features
    '''

    num = data.shape[1]
    if method == 'Pearson':
        corr = np.corrcoef(np.transpose(data))
    elif method == 'Spearman':
        corr = spearmanr(data).correlation
    elif method == 'Euclidean':
        corr = squareform(pdist(np.transpose(data), metric='euclidean'))
        corr = np.max(corr) - corr
        corr = corr / np.max(corr)
    elif method == 'set':
        corr1 = np.dot(np.transpose(data), data)
        corr2 = data.shape[0] - np.dot(np.transpose(1 - data), 1 - data)
        corr = corr1 / corr2

    corr = 1 - corr
    corr = np.around(a=corr, decimals=10)

    tril_id = np.tril_indices(num, k=-1)
    rank = rankdata(corr[tril_id])
    ranking = np.zeros((num, num))
    ranking[tril_id] = rank
    ranking = ranking + np.transpose(ranking)

    return ranking, corr


def generate_matrix_distance_ranking(num_r, num_c, method='Euclidean', num=None):
    '''
    This function calculates the ranking of distances between all pairs of entries in a matrix of size num_r by num_c.

    Input:
    num_r: number of rows in the matrix
    num_c: number of columns in the matrix
    method: method used to calculate distance. Can be 'Euclidean' or 'Manhattan'.
    num: number of real features. If None, num = num_r * num_c. If num < num_r * num_c, num_r * num_c - num
        zeros will be padded to the image representation.

    Return:
    coordinate: a num-by-2 matrix giving the coordinates of elements in the matrix.
    ranking: a num-by-num matrix giving the ranking of pair-wise distance.

    '''

    if num is None:
        num = num_r * num_c

    for r in range(num_r):
        if r == 0:
            coordinate = np.transpose(np.vstack((np.zeros(num_c), range(num_c))))
        else:
            coordinate = np.vstack((coordinate, np.transpose(np.vstack((np.ones(num_c) * r, range(num_c))))))
    coordinate = coordinate[:num, :]

    cord_dist = np.zeros((num, num))
    if method == 'Euclidean':
        for i in range(num):
            cord_dist[i, :] = np.sqrt(np.square(coordinate[i, 0] * np.ones(num) - coordinate[:, 0]) +
                                      np.square(coordinate[i, 1] * np.ones(num) - coordinate[:, 1]))
    elif method == 'Manhattan':
        for i in range(num):
            cord_dist[i, :] = np.abs(coordinate[i, 0] * np.ones(num) - coordinate[:, 0]) + \
                              np.abs(coordinate[i, 1] * np.ones(num) - coordinate[:, 1])

    # generate the ranking based on distance
    tril_id = np.tril_indices(num, k=-1)
    rank = rankdata(cord_dist[tril_id])
    ranking = np.zeros((num, num))
    ranking[tril_id] = rank
    ranking = ranking + np.transpose(ranking)

    coordinate = np.int64(coordinate)
    return (coordinate[:, 0], coordinate[:, 1]), ranking


def IGTD_absolute_error(source, target, max_step=30000, switch_t=0, val_step=300, min_gain=0.00001, random_state=1,
                        save_folder=None, file_name=''):
    '''
    This function switches the order of rows (columns) in the source ranking matrix to make it similar to the target
    ranking matrix. In each step, the algorithm randomly picks a row that has not been switched with others for
    the longest time and checks all possible switch of this row, and selects the switch that reduces the
    dissimilarity most. Dissimilarity (i.e. the error) is the summation of absolute difference of
    lower triangular elements between the rearranged source ranking matrix and the target ranking matrix.

    Input:
    source: a symmetric ranking matrix with zero diagonal elements.
    target: a symmetric ranking matrix with zero diagonal elements. 'source' and 'target' should have the same size.
    max_step: the maximum steps that the algorithm should run if never converges.
    switch_t: the threshold to determine whether feature switching should happen
    val_step: number of steps for checking gain on the objective function to determine convergence
    min_gain: if the objective function is not improved more than 'min_gain' in 'val_step' steps,
        the algorithm terminates.
    random_state: for setting random seed.
    save_folder: a path to save the picture of source ranking matrix in the optimization process.
    file_name: a string as part of the file names for saving results

    Return:
    index_record: indices to rearrange the rows(columns) in source obtained the optimization process
    err_record: error obtained in the optimization process
    run_time: the time at which each step is completed in the optimization process
    '''

    np.random.RandomState(seed=random_state)
    if save_folder and os.path.exists(save_folder):  # Check if save_folder is not None before using os.path.exists
        shutil.rmtree(save_folder)
    if save_folder:  # Check if save_folder is not None before using os.mkdir
        os.mkdir(save_folder)

    source = source.copy()
    num = source.shape[0]
    tril_id = np.tril_indices(num, k=-1)
    index = np.array(range(num))
    index_record = np.empty((max_step + 1, num))
    index_record.fill(np.nan)
    index_record[0, :] = index.copy()

    # calculate the error associated with each row
    err_v = np.empty(num)
    err_v.fill(np.nan)
    for i in range(num):
        err_v[i] = np.sum(np.abs(source[i, 0:i] - target[i, 0:i])) + \
                   np.sum(np.abs(source[(i + 1):, i] - target[(i + 1):, i]))

    step_record = -np.ones(num)
    err_record = [np.sum(abs(source[tril_id] - target[tril_id]))]
    pre_err = err_record[0]
    t1 = time.time()
    run_time = [0]

    for s in range(max_step):
        delta = - np.ones(num) * np.inf

        # randomly pick a row that has not been considered for the longest time
        idr = np.where(step_record == np.min(step_record))[0]
        ii = idr[np.random.permutation(len(idr))[0]]  # Consider rng.permutation if using default_rng

        for jj in range(num):
            if jj == ii:
                continue

            if ii < jj:
                i = ii
                j = jj
            else:
                i = jj
                j = ii

            err_ori = err_v[i] + err_v[j] - np.abs(source[j, i] - target[j, i])

            err_i = np.sum(np.abs(source[j, :i] - target[i, :i])) + \
                    np.sum(np.abs(source[(i + 1):j, j] - target[(i + 1):j, i])) + \
                    np.sum(np.abs(source[(j + 1):, j] - target[(j + 1):, i])) + np.abs(source[i, j] - target[j, i])
            err_j = np.sum(np.abs(source[i, :i] - target[j, :i])) + \
                    np.sum(np.abs(source[i, (i + 1):j] - target[j, (i + 1):j])) + \
                    np.sum(np.abs(source[(j + 1):, i] - target[(j + 1):, j])) + np.abs(source[i, j] - target[j, i])
            err_test = err_i + err_j - np.abs(source[i, j] - target[j, i])

            delta[jj] = err_ori - err_test

        # Ensure pre_err is not zero to avoid division by zero if that's possible
        if pre_err == 0:  # Handle case where pre_err might be zero
            delta_norm = np.zeros_like(delta)  # or some other appropriate handling
            if np.any(delta > 0):  # If any improvement, consider it significant
                delta_norm[delta > 0] = 1.0
        else:
            delta_norm = delta / pre_err

        id_val = np.where(delta_norm >= switch_t)[0]  # Renamed from id to avoid conflict with built-in
        if len(id_val) > 0:
            jj = np.argmax(delta)

            # Update the error associated with each row
            if ii < jj:
                i = ii
                j = jj
            else:
                i = jj
                j = ii
            for k in range(num):
                if k < i:
                    err_v[k] = err_v[k] - np.abs(source[i, k] - target[i, k]) - np.abs(source[j, k] - target[j, k]) + \
                               np.abs(source[j, k] - target[i, k]) + np.abs(source[i, k] - target[j, k])
                elif k == i:
                    err_v[k] = np.sum(np.abs(source[j, :i] - target[i, :i])) + \
                               np.sum(np.abs(source[(i + 1):j, j] - target[(i + 1):j, i])) + \
                               np.sum(np.abs(source[(j + 1):, j] - target[(j + 1):, i])) + np.abs(
                        source[i, j] - target[j, i])
                elif k < j:
                    err_v[k] = err_v[k] - np.abs(source[k, i] - target[k, i]) - np.abs(source[j, k] - target[j, k]) + \
                               np.abs(source[k, j] - target[k, i]) + np.abs(source[i, k] - target[j, k])
                elif k == j:
                    err_v[k] = np.sum(np.abs(source[i, :i] - target[j, :i])) + \
                               np.sum(np.abs(source[i, (i + 1):j] - target[j, (i + 1):j])) + \
                               np.sum(np.abs(source[(j + 1):, i] - target[(j + 1):, j])) + np.abs(
                        source[i, j] - target[j, i])
                else:
                    err_v[k] = err_v[k] - np.abs(source[k, i] - target[k, i]) - np.abs(source[k, j] - target[k, j]) + \
                               np.abs(source[k, j] - target[k, i]) + np.abs(source[k, i] - target[k, j])

            # switch rows i and j
            ii_v = source[ii, :].copy()
            jj_v = source[jj, :].copy()
            source[ii, :] = jj_v
            source[jj, :] = ii_v
            ii_v = source[:, ii].copy()
            jj_v = source[:, jj].copy()
            source[:, ii] = jj_v
            source[:, jj] = ii_v
            err = pre_err - delta[jj]

            # update rearrange index
            t = index[ii]
            index[ii] = index[jj]
            index[jj] = t

            # update step record
            step_record[ii] = s
            step_record[jj] = s
        else:
            # error is not changed due to no switch
            err = pre_err

            # update step record
            step_record[ii] = s

        err_record.append(err)
        print('Step ' + str(s) + ' err: ' + str(err))
        index_record[s + 1, :] = index.copy()
        run_time.append(time.time() - t1)

        if s > val_step:
            # Ensure err_record[-val_step - 1] is not zero for division
            current_min_gain_check_val = err_record[-val_step - 1]
            if current_min_gain_check_val == 0:  # Avoid division by zero
                if not np.any(
                        np.array(err_record[(-val_step):]) < current_min_gain_check_val):  # if no improvement from 0
                    break
            elif np.sum((current_min_gain_check_val - np.array(
                    err_record[(-val_step):])) / current_min_gain_check_val >= min_gain) == 0:
                break
        pre_err = err

    index_record = index_record[:len(err_record), :].astype(int)  # Changed from np.int
    if save_folder is not None:
        pd.DataFrame(index_record).to_csv(save_folder + '/' + file_name + '_index.txt', header=False, index=False,
                                          sep='\t', lineterminator='\r\n')  # Corrected lineterminator
        pd.DataFrame(np.transpose(np.vstack((err_record, np.array(range(s + 2))))),
                     # s might be undefined if loop doesn't run
                     columns=['error', 'steps']).to_csv(save_folder + '/' + file_name + '_error_and_step.txt',
                                                        header=True, index=False, sep='\t',
                                                        lineterminator='\r\n')  # Corrected lineterminator
        pd.DataFrame(np.transpose(np.vstack((err_record, run_time))), columns=['error', 'run_time']).to_csv(
            save_folder + '/' + file_name + '_error_and_time.txt', header=True, index=False, sep='\t',
            lineterminator='\r\n')  # Corrected lineterminator

    return index_record, err_record, run_time


def IGTD_square_error(source, target, max_step=30000, switch_t=0, val_step=300, min_gain=0.000001, random_state=1,
                      save_folder=None, file_name=''):
    '''
    This function switches the order of rows (columns) in the source ranking matrix to make it similar to the target
    ranking matrix. In each step, the algorithm randomly picks a row that has not been switched with others for
    the longest time and checks all possible switch of this row, and selects the switch that reduces the
    dissimilarity most. Dissimilarity (i.e. the error) is the summation of squared difference of
    lower triangular elements between the rearranged source ranking matrix and the target ranking matrix.
    '''

    # Consider using np.random.default_rng(seed=random_state) for newer NumPy versions
    np.random.RandomState(seed=random_state)
    if save_folder and os.path.exists(save_folder):  # Check if save_folder is not None
        shutil.rmtree(save_folder)
    if save_folder:  # Check if save_folder is not None
        os.mkdir(save_folder)

    source = source.copy()
    num = source.shape[0]
    tril_id = np.tril_indices(num, k=-1)
    index = np.array(range(num))
    index_record = np.empty((max_step + 1, num))
    index_record.fill(np.nan)
    index_record[0, :] = index.copy()

    err_v = np.empty(num)
    err_v.fill(np.nan)
    for i in range(num):
        err_v[i] = np.sum(np.square(source[i, 0:i] - target[i, 0:i])) + \
                   np.sum(np.square(source[(i + 1):, i] - target[(i + 1):, i]))

    step_record = -np.ones(num)
    err_record = [np.sum(np.square(source[tril_id] - target[tril_id]))]
    pre_err = err_record[0]
    t1 = time.time()
    run_time = [0]

    for s in range(max_step):
        delta = - np.ones(num) * np.inf
        idr = np.where(step_record == np.min(step_record))[0]
        ii = idr[np.random.permutation(len(idr))[0]]  # Consider rng.permutation

        for jj in range(num):
            if jj == ii:
                continue
            if ii < jj:
                i = ii;
                j = jj
            else:
                i = jj;
                j = ii

            err_ori = err_v[i] + err_v[j] - np.square(source[j, i] - target[j, i])
            err_i = np.sum(np.square(source[j, :i] - target[i, :i])) + \
                    np.sum(np.square(source[(i + 1):j, j] - target[(i + 1):j, i])) + \
                    np.sum(np.square(source[(j + 1):, j] - target[(j + 1):, i])) + np.square(
                source[i, j] - target[j, i])
            err_j = np.sum(np.square(source[i, :i] - target[j, :i])) + \
                    np.sum(np.square(source[i, (i + 1):j] - target[j, (i + 1):j])) + \
                    np.sum(np.square(source[(j + 1):, i] - target[(j + 1):, j])) + np.square(
                source[i, j] - target[j, i])
            err_test = err_i + err_j - np.square(source[i, j] - target[j, i])
            delta[jj] = err_ori - err_test

        if pre_err == 0:  # Handle case where pre_err might be zero
            delta_norm = np.zeros_like(delta)
            if np.any(delta > 0):
                delta_norm[delta > 0] = 1.0
        else:
            delta_norm = delta / pre_err

        id_val = np.where(delta_norm >= switch_t)[0]  # Renamed from id
        if len(id_val) > 0:
            jj = np.argmax(delta)
            if ii < jj:
                i = ii;
                j = jj
            else:
                i = jj;
                j = ii
            for k in range(num):
                if k < i:
                    err_v[k] = err_v[k] - np.square(source[i, k] - target[i, k]) - np.square(
                        source[j, k] - target[j, k]) + \
                               np.square(source[j, k] - target[i, k]) + np.square(source[i, k] - target[j, k])
                elif k == i:
                    err_v[k] = np.sum(np.square(source[j, :i] - target[i, :i])) + \
                               np.sum(np.square(source[(i + 1):j, j] - target[(i + 1):j, i])) + \
                               np.sum(np.square(source[(j + 1):, j] - target[(j + 1):, i])) + np.square(
                        source[i, j] - target[j, i])
                elif k < j:
                    err_v[k] = err_v[k] - np.square(source[k, i] - target[k, i]) - np.square(
                        source[j, k] - target[j, k]) + \
                               np.square(source[k, j] - target[k, i]) + np.square(source[i, k] - target[j, k])
                elif k == j:
                    err_v[k] = np.sum(np.square(source[i, :i] - target[j, :i])) + \
                               np.sum(np.square(source[i, (i + 1):j] - target[j, (i + 1):j])) + \
                               np.sum(np.square(source[(j + 1):, i] - target[(j + 1):, j])) + np.square(
                        source[i, j] - target[j, i])
                else:
                    err_v[k] = err_v[k] - np.square(source[k, i] - target[k, i]) - np.square(
                        source[k, j] - target[k, j]) + \
                               np.square(source[k, j] - target[k, i]) + np.square(source[k, i] - target[k, j])

            ii_v = source[ii, :].copy();
            jj_v = source[jj, :].copy()
            source[ii, :] = jj_v;
            source[jj, :] = ii_v
            ii_v = source[:, ii].copy();
            jj_v = source[:, jj].copy()
            source[:, ii] = jj_v;
            source[:, jj] = ii_v
            err = pre_err - delta[jj]
            t_val = index[ii];
            index[ii] = index[jj];
            index[jj] = t_val  # Renamed t to t_val
            step_record[ii] = s;
            step_record[jj] = s
        else:
            err = pre_err
            step_record[ii] = s

        err_record.append(err)
        print('Step ' + str(s) + ' err: ' + str(err))
        index_record[s + 1, :] = index.copy()
        run_time.append(time.time() - t1)

        if s > val_step:
            current_min_gain_check_val = err_record[-val_step - 1]
            if current_min_gain_check_val == 0:
                if not np.any(np.array(err_record[(-val_step):]) < current_min_gain_check_val):
                    break
            elif np.sum((current_min_gain_check_val - np.array(
                    err_record[(-val_step):])) / current_min_gain_check_val >= min_gain) == 0:
                break
        pre_err = err

    index_record = index_record[:len(err_record), :].astype(np.int64)  # This is fine, or use int
    if save_folder is not None:
        pd.DataFrame(index_record).to_csv(save_folder + '/' + file_name + '_index.txt', header=False, index=False,
                                          sep='\t', lineterminator='\r\n')  # Corrected
        pd.DataFrame(np.transpose(np.vstack((err_record, np.array(range(s + 2))))),  # s might be undefined
                     columns=['error', 'steps']).to_csv(save_folder + '/' + file_name + '_error_and_step.txt',
                                                        header=True, index=False, sep='\t',
                                                        lineterminator='\r\n')  # Corrected
        pd.DataFrame(np.transpose(np.vstack((err_record, run_time))), columns=['error', 'run_time']).to_csv(
            save_folder + '/' + file_name + '_error_and_time.txt', header=True, index=False, sep='\t',
            lineterminator='\r\n')  # Corrected

    return index_record, err_record, run_time


def IGTD(source, target, err_measure='abs', max_step=30000, switch_t=0, val_step=300, min_gain=0.000001, random_state=1,
         save_folder=None, file_name=''):
    '''
    This is just a wrapper function that wraps the two search functions using different error measures.
    '''
    # Initialize to ensure they are defined in all paths
    index_record, err_record, run_time = None, None, None
    if err_measure == 'abs':
        index_record, err_record, run_time = IGTD_absolute_error(source=source,
                                                                 target=target, max_step=max_step, switch_t=switch_t,
                                                                 val_step=val_step, min_gain=min_gain,
                                                                 random_state=random_state, save_folder=save_folder,
                                                                 file_name=file_name)
    elif err_measure == 'squared':  # Changed to elif for clarity
        index_record, err_record, run_time = IGTD_square_error(source=source,
                                                               target=target, max_step=max_step, switch_t=switch_t,
                                                               val_step=val_step, min_gain=min_gain,
                                                               random_state=random_state, save_folder=save_folder,
                                                               file_name=file_name)
    else:  # Handle case where err_measure is not 'abs' or 'squared'
        print(f"Unsupported error measure: {err_measure}")
        # Optionally, raise an error or return default values
        # raise ValueError(f"Unsupported error measure: {err_measure}")

    return index_record, err_record, run_time


def generate_image_data(data, index, num_row, num_column, coord, image_folder=None, file_name=''):
    '''
    This function generates the data in image format according to rearrangement indices. It saves the data
    sample-by-sample in both txt files and image files
    '''

    if isinstance(data, pd.DataFrame):
        samples = data.index.map(str)  # Changed from np.str
        data_values = data.values  # Use a different variable name
    else:
        samples = [str(i) for i in range(data.shape[0])]
        data_values = data  # Use a different variable name

    if image_folder and os.path.exists(image_folder):  # Check if image_folder is not None
        shutil.rmtree(image_folder)
    if image_folder:  # Check if image_folder is not None
        os.mkdir(image_folder)

    data_2 = data_values.copy()  # Use data_values
    data_2 = data_2[:, index]

    # Handle cases where all values are the same to avoid division by zero
    max_v = np.max(data_2)
    min_v = np.min(data_2)
    if max_v == min_v:
        data_2_normalized = np.zeros_like(data_2)  # or np.full_like(data_2, 255) depending on desired output
    else:
        data_2_normalized = 255 - (data_2 - min_v) / (
                    max_v - min_v) * 255  # Black color in heatmap indicates high value

    image_data_out = np.empty((num_row, num_column, data_2.shape[0]))  # Renamed image_data
    image_data_out.fill(np.nan)

    for i in range(data_2.shape[0]):
        data_i = np.empty((num_row, num_column))
        data_i.fill(np.nan)
        data_i[coord] = data_2_normalized[i, :]  # Use normalized data

        idd = np.where(np.isnan(data_i))
        data_i[idd] = 255

        image_data_out[:, :, i] = data_i
        image_data_out[:, :, i] = 255 - image_data_out[:, :, i]
        if image_folder is not None:
            fig = plt.figure()
            # Use data_i for imshow as it's [0, 255] where 0 is high (black)
            plt.imshow(data_i, cmap='gray', vmin=0, vmax=255)
            plt.axis('scaled')
            plt.savefig(fname=image_folder + '/' + file_name + '_' + samples[i] + '_image.png', bbox_inches='tight',
                        pad_inches=0)
            plt.close(fig)

            pd.DataFrame(image_data_out[:, :, i], index=None, columns=None).to_csv(image_folder + '/' + file_name + '_'
                                                                                   + samples[i] + '_data.txt',
                                                                                   header=None,
                                                                                   index=None, sep='\t',
                                                                                   lineterminator='\r\n')  # Corrected

    return image_data_out, samples  # Return renamed variable


def table_to_image(norm_d, scale, fea_dist_method, image_dist_method, save_image_size, max_step, val_step, normDir,
                   error, switch_t=0, min_gain=0.000001):
    '''
    This function converts tabular data into images using the IGTD algorithm.
    '''

    if normDir and os.path.exists(normDir):  # Check if normDir is not None
        shutil.rmtree(normDir)
    if normDir:  # Check if normDir is not None
        os.mkdir(normDir)

    ranking_feature, corr = generate_feature_distance_ranking(data=norm_d, method=fea_dist_method)
    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_feature) - ranking_feature, cmap='gray', interpolation='nearest')
        plt.savefig(fname=normDir + '/original_feature_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    coordinate, ranking_image = generate_matrix_distance_ranking(num_r=scale[0], num_c=scale[1],
                                                                 method=image_dist_method, num=norm_d.shape[1])
    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_image) - ranking_image, cmap='gray', interpolation='nearest')
        plt.savefig(fname=normDir + '/image_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    # Ensure normDir + '/' + error is a valid path if normDir is None
    save_folder_path = normDir + '/' + error if normDir else error

    index, err, time_taken = IGTD(source=ranking_feature, target=ranking_image,  # Renamed time to time_taken
                                  err_measure=error, max_step=max_step, switch_t=switch_t, val_step=val_step,
                                  min_gain=min_gain, random_state=1,
                                  save_folder=save_folder_path, file_name='')

    if err is None:  # Handle if IGTD returns None for err
        print("Error: IGTD did not return error records.")
        return  # Or handle appropriately

    if normDir:  # Check if normDir is not None
        fig = plt.figure()
        plt.plot(time_taken, err)  # Use renamed time_taken
        plt.savefig(fname=normDir + '/error_and_runtime.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        fig = plt.figure()
        plt.plot(range(len(err)), err)
        plt.savefig(fname=normDir + '/error_and_iteration.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    min_id = np.argmin(err)
    ranking_feature_random = ranking_feature[index[min_id, :], :]
    ranking_feature_random = ranking_feature_random[:, index[min_id, :]]

    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_feature_random) - ranking_feature_random, cmap='gray',
                   interpolation='nearest')
        plt.savefig(fname=normDir + '/optimized_feature_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    # Ensure normDir + '/data' is valid if normDir is None
    image_folder_path = normDir + '/data' if normDir else 'data'

    image_data_gen, samples = generate_image_data(data=norm_d, index=index[min_id, :], num_row=scale[0],
                                                  num_column=scale[1],  # Renamed data to image_data_gen
                                                  coord=coordinate, image_folder=image_folder_path, file_name='')

    if normDir:  # Check if normDir is not None
        with open(normDir + '/Results.pkl', 'wb') as output_file:  # Renamed output to output_file
            cp.dump(norm_d, output_file)
            cp.dump(image_data_gen, output_file)  # Use renamed image_data_gen
            cp.dump(samples, output_file)

        with open(normDir + '/Results_Auxiliary.pkl', 'wb') as output_file:  # Renamed output to output_file
            cp.dump(ranking_feature, output_file)
            cp.dump(ranking_image, output_file)
            cp.dump(coordinate, output_file)
            cp.dump(err, output_file)
            cp.dump(time_taken, output_file)  # Use renamed time_taken


def multi_generate_image_data(data_list, index, num_row, num_column, coord, image_folder=None, file_name=''):
    '''
    This function generates data in the multi-channel image format according to rearrangement indices.
    '''
    data_list_processed = []  # Renamed
    if isinstance(data_list[0], pd.DataFrame):
        data_list_copy = data_list  # Keep original name for clarity in this block
        samples = data_list_copy[0].index.map(str)  # Changed from np.str
        for i in range(len(data_list_copy)):
            if np.sum(samples != data_list_copy[i].index.map(str)) > 0:  # Changed from np.str
                print('Channel ' + str(i) + ' sample names are NOT consistent.')  # Keep print for now
                sys.exit('Channel ' + str(i) + ' sample names are NOT consistent.')
            else:
                data_list_processed.append(data_list_copy[i].values)
    else:
        samples = [str(i) for i in range(data_list[0].shape[0])]
        data_list_processed = [d.copy() for d in data_list]  # Ensure we have copies if they are numpy arrays

    if image_folder and os.path.exists(image_folder):  # Check if image_folder is not None
        shutil.rmtree(image_folder)
    if image_folder:  # Check if image_folder is not None
        os.mkdir(image_folder)

    num_sample = data_list_processed[0].shape[0]
    num_channel = len(data_list_processed)
    image_data_multi = np.empty((num_channel, num_row, num_column, num_sample))  # Renamed
    image_data_multi.fill(np.nan)

    for j in range(num_channel):
        data_2 = data_list_processed[j].copy()
        data_2 = data_2[:, index]

        max_v = np.max(data_2)
        min_v = np.min(data_2)
        if max_v == min_v:
            data_2_normalized = np.zeros_like(data_2)
        else:
            data_2_normalized = 255 - (data_2 - min_v) / (max_v - min_v) * 255

        for i in range(num_sample):
            data_i = np.empty((num_row, num_column))
            data_i.fill(np.nan)
            data_i[coord] = data_2_normalized[i, :]

            idd = np.where(np.isnan(data_i))
            data_i[idd] = 255

            image_data_multi[j, :, :, i] = data_i
            image_data_multi[j, :, :, i] = 255 - image_data_multi[j, :, :, i]
            if image_folder is not None:
                fig = plt.figure()
                plt.imshow(data_i, cmap='gray', vmin=0, vmax=255)
                plt.axis('scaled')
                plt.savefig(fname=image_folder + '/' + file_name + '_' + samples[i] + '_image_channel_' + str(j) +
                                  '.png', bbox_inches='tight', pad_inches=0)
                plt.close(fig)

                pd.DataFrame(image_data_multi[j, :, :, i], index=None, columns=None).to_csv(
                    image_folder + '/' + file_name +
                    '_' + samples[i] + '_data_channel_' + str(j) +
                    '.txt', header=None, index=None, sep='\t',
                    lineterminator='\r\n')  # Corrected

    return image_data_multi, samples  # Return renamed


def multi_table_to_image(norm_d_list, weight_list, fea_dist_method_list, scale, image_dist_method, save_image_size,
                         max_step, val_step, normDir, error, switch_t=0, min_gain=0.000001):
    '''
    This function converts multiple data tables of different feature types into multi-channel images.
    '''

    if normDir and os.path.exists(normDir):  # Check if normDir is not None
        shutil.rmtree(normDir)
    if normDir:  # Check if normDir is not None
        os.mkdir(normDir)

    weight_list_normalized = np.array(weight_list)  # Create a copy to modify
    sum_weight = np.sum(weight_list_normalized)
    if sum_weight == 0:  # Avoid division by zero if all weights are zero
        print("Warning: Sum of weights is zero. Using equal weights.")
        weight_list_normalized = np.ones(len(norm_d_list)) / len(norm_d_list)
    else:
        weight_list_normalized = weight_list_normalized / sum_weight

    num_channel = len(norm_d_list)
    ranking_feature_list = []
    # corr_list = [] # This was unused, so removed for now. Add back if needed.
    for i in range(num_channel):
        a, b = generate_feature_distance_ranking(data=norm_d_list[i], method=fea_dist_method_list[i])
        ranking_feature_list.append(a)
        # corr_list.append(b) # Unused
        if normDir:  # Check if normDir is not None
            fig = plt.figure(figsize=(save_image_size, save_image_size))
            plt.imshow(np.max(ranking_feature_list[i]) - ranking_feature_list[i], cmap='gray', interpolation='nearest')
            plt.savefig(fname=normDir + '/original_feature_ranking_channel_' + str(i) + '.png', bbox_inches='tight',
                        pad_inches=0)
            plt.close(fig)

    ranking_feature = np.zeros((ranking_feature_list[0].shape[0], ranking_feature_list[0].shape[1]))
    for i in range(num_channel):
        ranking_feature = ranking_feature + ranking_feature_list[i] * weight_list_normalized[
            i]  # Use normalized weights

    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_feature) - ranking_feature, cmap='gray', interpolation='nearest')
        plt.savefig(fname=normDir + '/original_feature_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    coordinate, ranking_image = generate_matrix_distance_ranking(num_r=scale[0], num_c=scale[1],
                                                                 method=image_dist_method, num=norm_d_list[0].shape[1])
    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_image) - ranking_image, cmap='gray', interpolation='nearest')
        plt.savefig(fname=normDir + '/image_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    save_folder_path = normDir + '/' + error if normDir else error

    index, err, time_taken = IGTD(source=ranking_feature, target=ranking_image, err_measure=error, max_step=max_step,
                                  # Renamed time
                                  switch_t=switch_t, val_step=val_step, min_gain=min_gain, random_state=1,
                                  save_folder=save_folder_path, file_name='')

    if err is None:
        print("Error: IGTD did not return error records for multi_table_to_image.")
        return

    if normDir:  # Check if normDir is not None
        fig = plt.figure()
        plt.plot(time_taken, err)  # Use renamed time_taken
        plt.savefig(fname=normDir + '/error_and_runtime.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        fig = plt.figure()
        plt.plot(range(len(err)), err)
        plt.savefig(fname=normDir + '/error_and_iteration.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    min_id = np.argmin(err)
    ranking_feature_random = ranking_feature[index[min_id, :], :]
    ranking_feature_random = ranking_feature_random[:, index[min_id, :]]

    if normDir:  # Check if normDir is not None
        fig = plt.figure(figsize=(save_image_size, save_image_size))
        plt.imshow(np.max(ranking_feature_random) - ranking_feature_random, cmap='gray',
                   interpolation='nearest')
        plt.savefig(fname=normDir + '/optimized_feature_ranking.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    image_folder_path = normDir + '/data' if normDir else 'data'
    image_data_multi_gen, samples = multi_generate_image_data(data_list=norm_d_list, index=index[min_id, :],
                                                              num_row=scale[0],  # Renamed data
                                                              num_column=scale[1], coord=coordinate,
                                                              image_folder=image_folder_path,
                                                              file_name='')

    if normDir:  # Check if normDir is not None
        with open(normDir + '/Results.pkl', 'wb') as output_file:  # Renamed output
            cp.dump(norm_d_list, output_file)
            cp.dump(image_data_multi_gen, output_file)  # Use renamed
            cp.dump(samples, output_file)

        with open(normDir + '/Results_Auxiliary.pkl', 'wb') as output_file:  # Renamed output
            cp.dump(ranking_feature, output_file)
            cp.dump(ranking_image, output_file)
            cp.dump(coordinate, output_file)
            cp.dump(err, output_file)
            cp.dump(time_taken, output_file)  # Use renamed