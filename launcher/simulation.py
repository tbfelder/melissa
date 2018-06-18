###################################################################
#                            Melissa                              #
#-----------------------------------------------------------------#
#   COPYRIGHT (C) 2017  by INRIA and EDF. ALL RIGHTS RESERVED.    #
#                                                                 #
# This source is covered by the BSD 3-Clause License.             #
# Refer to the  LICENCE file for further information.             #
#                                                                 #
#-----------------------------------------------------------------#
#  Original Contributors:                                         #
#    Theophile Terraz,                                            #
#    Bruno Raffin,                                                #
#    Alejandro Ribes,                                             #
#    Bertrand Iooss,                                              #
###################################################################


"""
    Simulations and server jobs module
"""

import numpy
import os
import time
import subprocess
import logging
from threading import RLock
from ctypes import cdll, create_string_buffer
get_message = cdll.LoadLibrary('@CMAKE_INSTALL_PREFIX@/share/launcher/libget_message.so')

# Jobs and executions status

NOT_SUBMITTED = -1
PENDING = 0
WAITING = 0
RUNNING = 1
FINISHED = 2
TIMEOUT = 4
COUPLING_DICT = {"MELISSA_COUPLING_NONE":0,
                 "MELISSA_COUPLING_DEFAULT":0,
                 "MELISSA_COUPLING_ZMQ":0,
                 "MELISSA_COUPLING_MPI":1,
                 "MELISSA_COUPLING_FLOWVR":2}

class Job(object):
    """
        Job class
    """
    usr_func = {}
    stdy_opt = {}
    ml_stats = {}
    def __init__(self):
        """
            Job constructor
        """
        self.job_status = NOT_SUBMITTED
        self.job_id = 0
        self.cmd_opt = ''
        self.start_time = 0.0

    def set_usr_func(usr_func):
        Job.usr_func = usr_func

    def set_stdy_opt(stdy_opt):
        Job.stdy_opt = stdy_opt

    def set_ml_stats(ml_stats):
        Job.ml_stats = ml_stats

    set_usr_func = staticmethod(set_usr_func)
    set_stdy_opt = staticmethod(set_stdy_opt)
    set_ml_stats = staticmethod(set_ml_stats)

    def cancel(self):
        """
            Cancels a job (mandatory)
        """
        if "cancel_job" in Job.usr_func.keys() \
        and Job.usr_func['cancel_job']:
            return Job.usr_func['cancel_job'](self)
        else:
            logging.error('Error: no \'cancel_job\' function provided')
            exit()

class Group(Job):
    """
        Group class
    """
    nb_groups = 0
    def __init__(self):
        """
            Group constructor
        """
        Job.__init__(self)
        self.nb_restarts = 0
        self.status = NOT_SUBMITTED
        self.lock = RLock()
        self.coupling = COUPLING_DICT.get(Job.stdy_opt['coupling'].upper(), "MELISSA_COUPLING_DEFAULT")
        Group.nb_groups += 1

#    @classmethod
    def reset():
        Group.nb_groups = 0

    reset = staticmethod(reset)

    def create(self):
        """
            Creates a group environment
        """
        if "create_group" in Job.usr_func.keys() \
        and Job.usr_func['create_group']:
            Job.usr_func['create_group'](self)
        else:
            logging.warning('Warning: no \'create_group\''
                          +' function provided')

    def launch(self):
        """
            Launches the group (mandatory)
        """
        if "launch_group" in Job.usr_func.keys() \
        and Job.usr_func['launch_group']:
            Job.usr_func['launch_group'](self)
        else:
            logging.error('Error: no \'launch_group\' function provided')
            exit()
        self.job_status = PENDING
        self.status = WAITING

    def check_job(self):
        """
            Checks the group job status (mandatory)
        """
        if "check_group_job" in Job.usr_func.keys() \
        and Job.usr_func['check_group_job']:
            Job.usr_func['check_group_job'](self)
        else:
            logging.error('Error: no \'check_group_job\''
                          +' function provided')
            exit()

    def finalize(self):
        """
            Finalize the group (optional)
        """

        if "finalize_group" in Job.usr_func.keys():
            if Job.usr_func['finalize_group']:
                Job.usr_func['finalize_group'](self)


class SingleSimuGroup(Group):
    """
    Single simulation group class
    """
    def __init__(self, param_set):
        """
            SingleSimuGroup constructor
        """
        Group.__init__(self)
        self.rank = Group.nb_groups-1
        self.simu_id = self.rank
        self.param_set = numpy.copy(param_set)
        self.coupling = 0

    def restart(self):
        """
            Ends and restarts the simulation (mandatory)
        """
        self.cancel()
        self.nb_restarts += 1
        if self.nb_restarts > 4:
            logging.warning('Simulation ' + self.rank +
                            'crashed 5 times, drawing new parameter set')
            logging.info('old parameter set: ' + str(self.param_set))
            self.param_set = Job.usr_func['draw_parameter_set']()
            logging.info('new parameter set: ' + str(self.param_set))
            self.nb_restarts = 0

        if "restart_group" in Job.usr_func.keys() \
        and Job.usr_func['restart_group']:
            Job.usr_func['restart_group'](self)
        else:
            logging.warning('warning: no \'restart_group\''
                            +' function provided,'
                            +' using \'launch_group\' instead')
            self.launch()
        self.job_status = PENDING
        self.status = WAITING


class SobolGroup(Group):
    """
        Sobol coupled group class
    """
    def __init__(self, param_set_a, param_set_b):
        """
            SobolGroup constructor
        """
        Group.__init__(self)
        self.rank = Group.nb_groups-1
        self.param_set = list()
        self.simu_id = list()
        self.param_set.append(numpy.copy(param_set_a))
        self.simu_id.append(self.rank*(len(param_set_a)+2))
        self.param_set.append(numpy.copy(param_set_b))
        self.simu_id.append(self.rank*(len(param_set_a)+2)+1)
        for i in range(len(param_set_a)):
            self.param_set.append(numpy.copy(self.param_set[0]))
            self.param_set[i+2][i] = numpy.copy(self.param_set[1][i])
            self.simu_id.append(self.rank*(len(param_set_a)+2)+i+2)

    def restart(self):
        """
            Ends and restarts the Sobol group (mandatory)
        """
        self.cancel()
        self.nb_restarts += 1
        if self.nb_restarts > 4:
            logging.warning('Group ' +
                            str(self.rank) +
                            'crashed 5 times, drawing new parameter sets')
            logging.debug('old parameter set A: ' + str(self.param_set[0]))
            logging.debug('old parameter set B: ' + str(self.param_set[1]))
            self.param_set[0] = Job.usr_func['draw_parameter_set']()
            self.param_set[1] = Job.usr_func['draw_parameter_set']()
            logging.info('new parameter set A: ' + str(self.param_set[0]))
            logging.info('new parameter set B: ' + str(self.param_set[1]))
            for i in range(len(self.param_set[0])):
                self.param_set[i+2] = numpy.copy(self.param_set[0])
                self.param_set[i+2][i] = numpy.copy(self.param_set[1][i])
            self.nb_restarts = 0

        if "restart_group" in Job.usr_func.keys() \
        and Job.usr_func['restart_group']:
            Job.usr_func['restart_group'](self)
        else:
            logging.warning('warning: no \'restart_group\''
                            +' function provided,'
                            +' using \'launch_group\' instead')
            self.launch()
        self.job_status = PENDING
        self.status = WAITING

class Server(Job):
    """
        Server class
    """
    def __init__(self):
        """
            Server constructor
        """
        Job.__init__(self)
        self.status = WAITING
        self.node_name = ''
        self.first_job_id = ''
#        self.create_options()
        self.lock = RLock()
        self.path = '@CMAKE_INSTALL_PREFIX@/bin'

    def set_path(self, work_dir="./"):
        self.directory = work_dir

    def write_node_name(self):
        os.chdir(self.directory)
        fichier=open("server_name.txt", "w")
        fichier.write(self.node_name)
        fichier.close()
        os.system("chmod 744 server_name.txt")

    def create_options(self):
        """
            Melissa Server command line options
        """
        op_str = ':'.join([x for x in Job.ml_stats if Job.ml_stats[x]])
        if op_str == '':
            logging.error('error bad option: no operation given')
            return
        field_str = ':'.join([x for x in Job.stdy_opt['field_names']])
        if field_str == '':
            logging.error('error bad option: no field name given')
            return
        if Job.ml_stats['quantiles']:
            quantile_str = ':'.join([str(x) for x in Job.stdy_opt['quantile_values']])
            if quantile_str == '':
                logging.error('error bad option: no quantile value given')
                return
        buff = create_string_buffer('\000' * 256)
        get_message.get_node_name(buff)
        self.cmd_opt = ' '.join(('-o', op_str,
                                 '-p', str(Job.stdy_opt['nb_parameters']),
                                 '-s', str(Job.stdy_opt['sampling_size']),
                                 '-t', str(Job.stdy_opt['nb_time_steps']),
                                 '-q', quantile_str,
                                 '-e', str(Job.stdy_opt['threshold_value']),
                                 '-c', str(Job.stdy_opt['checkpoint_interval']),
                                 '-w', str(Job.stdy_opt['simulation_timeout']),
                                 '-f', field_str,
                                 '-n', str(buff.value)))

    def launch(self):
        """
            Launches server job
        """
        os.chdir(self.directory)
        logging.info('launch server')
        logging.info('server options: '+self.cmd_opt)
        if "launch_server" in Job.usr_func.keys() \
        and Job.usr_func['launch_server']:
            Job.usr_func['launch_server'](self)
        else:
            logging.error('Error: no \'launch_server\' function provided')
            exit()
        self.first_job_id = self.job_id
        self.job_status = PENDING

    def wait_start(self):
        """
            Waits for the server to start
        """
        with self.lock:
            status = self.status
        while status < RUNNING:
            time.sleep(1)
            with self.lock:
                status = self.status
        if status > RUNNING:
            logging.warning('Server crashed')
        else:
            logging.info('Server running')
        self.start_time = time.time()

    def restart(self):
        """
            Restarts the server
        """
        if not "-r" in self.cmd_opt:
            self.cmd_opt += ' -r ' + self.directory
        os.chdir(self.directory)
        if "restart_server" in Job.usr_func.keys() \
        and Job.usr_func['restart_server']:
            Job.usr_func['restart_server'](self)
        else:
            logging.warning('Warning: no \'restart_server\' function provided'
                            +' using launch_server instead')
            self.launch()
        with self.lock:
            self.status = WAITING
            self.job_status = PENDING
        self.start_time = 0.0
        self.wait_start()

    def check_job(self):
        """
            Checks server job status
        """
        if "check_server_job" in Job.usr_func.keys() \
         and Job.usr_func['check_server_job']:
            Job.usr_func['check_server_job'](self)
        else:
            logging.error('Error: no \'check_server_job\' function provided')
            exit()
