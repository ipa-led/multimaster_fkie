# Software License Agreement (BSD License)
#
# Copyright (c) 2017, Fraunhofer FKIE/CMS, Alexander Tiderko
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Fraunhofer nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import os
from rosclean import get_disk_usage
import rospy
import rospkg

import subprocess
from .supervised_popen import SupervisedPopen


class ScreenException(Exception):
    pass


LOG_PATH = ''.join([os.environ.get('ROS_LOG_DIR'), os.path.sep]) if os.environ.get('ROS_LOG_DIR') else os.path.join(os.path.expanduser('~'), '.ros/log/')
''':var LOG_PATH: logging path where all screen configuration and log files are stored.'''
SCREEN = "/usr/bin/screen"
''':var SCREEN: Defines the path to screen binary.'''
SLASH_SEP = '_'
''':var SLASH_SEP: this character is used to replace the slashes in ROS-Names.'''


def create_session_name(node=''):
    '''
    Creates a name for the screen session. All slash separators are replaced by `SLASH_SEP`
    and all `SLASH_SEP` are replaced by double `SLASH_SEP`.

    :param str node: the name of the node
    :return: name for the screen session.
    :rtype: str
    '''
    if node is None:
        return ''
    result = rospy.names.ns_join('/', node).replace(SLASH_SEP, '%s%s' % (SLASH_SEP, SLASH_SEP))
    result = result.replace('/', SLASH_SEP)
    return result


def session_name2node_name(session):
    '''
    Create a node name from screen session name. Revert changes done by :meth:`create_session_name`

    :param str session: the name of the session without pid
    :return: name name.
    :rtype: str
    '''
    node_name = session.replace('%s%s' % (SLASH_SEP, SLASH_SEP), '//')
    node_name = node_name.replace(SLASH_SEP, '/')
    node_name = node_name.replace('//', SLASH_SEP)
    return node_name


def split_session_name(session):
    '''
    Splits the screen session name into PID and session name generated by `create_session_name()`.

    :param str session: the screen session name
    :return: PID, session name generated by `create_session_name()`. Not presented
      values are coded as empty strings. Not valid session names have an empty
      PID string.
    :rtype: int, str
    '''
    if session is None:
        return '', ''
    result = session.split('.', 1)
    if len(result) != 2:
        return -1, ''
    pid = result[0].strip()
    try:
        pid = int(pid)
    except Exception:
        return -1, ''
    node = result[1].split('\t')
    if not node:
        return -1, ''
    return pid, node[0].strip()


def get_active_screens(nodename=''):
    '''
    Returns the dictionary (session name: node name) with all compatible screen names. If the session is set to
    an empty string all screens will be returned.

    :param str nodename: the name of the node.
    :return: On empty nodename returns all screen.
    :rtype: {str: [str]}
    '''
    result = {}
    ps = SupervisedPopen([SCREEN, '-ls'], stdout=subprocess.PIPE)
    output = ps.stdout.read()
    if output:
        splits = output.splitlines()
        for item in splits:
            pid, nodepart = split_session_name(item)
            if pid != -1:
                screen_name = '%d.%s' % (pid, nodepart)
                if nodename:
                    # put all sessions which starts with '_'
                    if nodepart.startswith('_'):
                        if nodename == session_name2node_name(nodepart):
                            result[screen_name] = nodename
                else:
                    # only sessions for given node
                    name = session_name2node_name(nodepart)
                    result[screen_name] = name
    return result


def test_screen():
    '''
    Tests for whether the SCREEN binary exists and raise an exception if not.

    :raise ScreenHandlerException: if the screen binary not found.
    '''
    if not os.path.isfile(SCREEN):
        raise ScreenException(SCREEN, "%s is missing" % SCREEN)


def get_logfile(session=None, node=None):
    '''
    Generates a log file name of the ROS log.

    :param str node: the name of the node
    :return: the ROS log file name
    :rtype: str
    :todo: get the run_id from the ROS parameter server and search in this log folder
           for the log file (handle the node started using a launch file).
    '''
    if session is not None:
        return "%s%s.log" % (LOG_PATH, session)
    elif node is not None:
        return "%s%s.log" % (LOG_PATH, create_session_name(node))
    return "%s%s.log" % (LOG_PATH, 'unknown')


def get_ros_logfile(node):
    '''
    Generates a log file name for the ROS log

    :param str node: the name of the node
    :return: the log file name
    :rtype: str
    '''
    if node is not None:
        return "%s%s.log" % (LOG_PATH, node.strip('/').replace('/', '_'))
    return ''


def get_cfgfile(session=None, node=None):
    '''
    Generates a configuration file name for the screen session.

    :param str session: the name of the screen session
    :return: the configuration file name
    :rtype: str
    '''
    if session is not None:
        return "%s%s.conf" % (LOG_PATH, session)
    elif node is not None:
        return "%s%s.conf" % (LOG_PATH, create_session_name(node))
    return "%s%s.conf" % (LOG_PATH, 'unknown')


def get_pidfile(session=None, node=None):
    '''
    Generates a PID file name for the screen session.

    :param str session: the name of the screen session
    :return: the PID file name
    :rtype: str
    '''
    if session is not None:
        return "%s%s.pid" % (LOG_PATH, session)
    elif node is not None:
        return "%s%s.pid" % (LOG_PATH, create_session_name(node))
    return "%s%s.pid" % (LOG_PATH, 'unknown')


def _append_env(cfgfile, arg, env):
    if arg in env:
        value = env[arg]
        if value:
            cfgfile.write('setenv %s %s\n' % (arg, value))
            return True
    return False


def get_cmd(node, env=[], keys=[]):
    '''
    Generates a screen configuration file and return the command prefix to start the given node
    in a screen terminal.

    :param str node: the name of the node
    :return: the command prefix
    :rtype: str
    '''
    filename = get_cfgfile(node=node)
    f = None
    try:
        f = open(filename, 'w')
    except Exception:
        os.makedirs(os.path.dirname(filename))
        f = open(filename, 'w')
    f.write("logfile %s\n" % get_logfile(node=node))
    f.write("logfile flush 0\n")
    f.write("defscrollback 10000\n")
    addkeys = list(keys)
    addkeys.append('LD_LIBRARY_PATH')
    addkeys.append('ROS_ETC_DIR')
    addkeys.append('ROS_MASTER_URI')
    addkeys.append('ROS_HOSTNAME')
    addkeys.append('ROS_NAMESPACE')
    addkeys.append('ROSCONSOLE_FORMAT')
    addkeys.append('ROSCONSOLE_CONFIG_FILE')
    addkeys.append('RESPAWN_DELAY')
    addkeys.append('RESPAWN_MAX')
    addkeys.append('RESPAWN_MIN_RUNTIME')
    for key in addkeys:
        if not _append_env(f, key, env):
            _append_env(f, key, os.environ)
    f.close()
    return "%s -c %s -L -dmS %s" % (SCREEN, filename, create_session_name(node=node))


def rosclean():
    '''
    Removes the content of the log directory. We didn't use rosclean purge because it
    removes the log-directory. This needs restart of ros nodes or recreate log directory
    to get log again.
    '''
    d = rospkg.get_log_dir()
    ps = SupervisedPopen(['rm -fr %s/*' % d], stdout=subprocess.PIPE, shell=True)
    output_err = ps.stderr.read()
    if output_err:
        raise Exception(output_err)


def log_dir_size():
    d = rospkg.get_log_dir()
    disk_usage = get_disk_usage(d)
    return disk_usage


def delete_log(nodename):
    screen_log = get_logfile(node=nodename)
    screen_conf = get_cfgfile(node=nodename)
    pid_file = get_pidfile(node=nodename)
    roslog = get_ros_logfile(nodename)
    if os.path.isfile(screen_log):
        os.remove(screen_log)
    if os.path.isfile(screen_conf):
        os.remove(screen_conf)
    if os.path.isfile(pid_file):
        os.remove(pid_file)
    if os.path.isfile(roslog):
        os.remove(roslog)
