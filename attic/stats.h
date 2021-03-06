/******************************************************************
*                            Melissa                              *
*-----------------------------------------------------------------*
*   COPYRIGHT (C) 2017  by INRIA and EDF. ALL RIGHTS RESERVED.    *
*                                                                 *
* This source is covered by the BSD 3-Clause License.             *
* Refer to the  LICENCE file for further information.             *
*                                                                 *
*-----------------------------------------------------------------*
*  Original Contributors:                                         *
*    Theophile Terraz,                                            *
*    Bruno Raffin,                                                *
*    Alejandro Ribes,                                             *
*    Bertrand Iooss,                                              *
******************************************************************/

/**
 *
 * @file stats.h
 * @author Terraz Théophile
 * @date 2016-15-02
 *
 **/

#ifndef STATS_H
#define STATS_H

#include <stdio.h>
#ifdef BUILD_WITH_MPI
#include <mpi.h>
#endif // BUILD_WITH_MPI
#include "melissa_utils.h"
#include "melissa_options.h"
#include "melissa_data.h"
#include "mean.h"
#include "variance.h"
#include "min_max.h"
#include "threshold.h"
#include "covariance.h"
#include "sobol.h"

/**
 *******************************************************************************
 *
 * @enum return_status
 *
 * Values that can be returned by functions depending on what appened
 *
 *******************************************************************************/

enum return_status
{
    SUCCESS,                  /**< nothing to report                          */
    WARNING_NOTHING_RETURNED, /**< a in/out object is returned unmodified     */
    ERROR_BAD_PARAMETER       /**< a bad parameter was givent to the function */
};

/**
 *******************************************************************************
 *
 * @ingroup sobol
 *
 * @struct conditional_mean_s
 *
 * Recursive structure of conditional means, needs to be more documented
 *
 *******************************************************************************/

struct conditional_mean_s
{
    mean_t                     mean;                   /**< mean structure                                                  */
    int                       *indices;                /**< -1 if variable parameter, the indice of the parameter otherwise */
    int                        order;                  /**< order of this mean                                              */
    int                        is_leaf;                /**< to kwnow if this mean have sons                                 */
    int                       *indice_ptr;             /**< ptr to the indices in next_conditional_means                    */
    int                        indice_ptr_size;        /**< size of *indice_ptr                                             */
    struct conditional_mean_s *next_conditional_means; /**< sons of conditional_mean                                        */
};

typedef struct conditional_mean_s conditional_mean_t; /**< type corresponding to conditional_mean_s */

/**
 *******************************************************************************
 *
 * @ingroup sobol
 *
 * @struct conditional_variance_s
 *
 * Structure containing a conditional variance and its corresponding mean
 *
 *******************************************************************************/

struct conditional_variance_s
{
    variance_t  variance;      /**< variance structure                                       */
    int        *fixed_indices; /**< 1 if fixed parameter, 0 otherwise (size nb_parameters)   */
    int         order;         /**< order of this variance (nb of 1 in fixed_indices)        */
};

typedef struct conditional_variance_s conditional_variance_t; /**< type corresponding to conditional_variance_s */

///**
// *******************************************************************************
// *
// * @ingroup sobol
// *
// * @struct sobol_index_s
// *
// * Structure containing a conditional variance and its corresponding sobol index vector
// *
// *******************************************************************************/

//struct sobol_index_s
//{
//    conditional_variance_t conditional_variance; /**< numerators of this sobol indices */
//    double                 *values;              /**< values of this sobol indices     */
//};

//typedef struct sobol_index_s sobol_index_t; /**< type corresponding to sobol_index_s */

//void init_conditional_means (conditional_mean_t *conditional_means,
//                             stats_data_t       *data);

//void init_next_conditional_mean (conditional_mean_t *conditional_means,
//                                 const int           depth,
//                                 const int           new_fixed_parameter[],
//                                 const int           previous_indices[],
//                                 stats_data_t       *data);

//void increment_conditional_mean (conditional_mean_t *conditional_means,
//                                 double              in_vect[],
//                                 const int           parameters[],
//                                 stats_data_t       *data);

//int get_conditional_mean (conditional_mean_t *conditional_means,
//                          double             *out_mean,
//                          int                *out_increment,
//                          const int           parameters[],
//                          stats_data_t       *data);

//void free_conditional_mean (conditional_mean_t *conditional_means);

//void init_conditional_variance (conditional_variance_t *conditional_variance,
//                                const int               indices_to_fix[],
//                                stats_data_t           *data);

//int compute_conditional_variance (conditional_variance_t *conditional_variance,
//                                  conditional_mean_t     *conditional_means,
//                                  stats_data_t           *data);

//void free_conditional_variance (conditional_variance_t *conditional_variance);

#endif // STATS_H
