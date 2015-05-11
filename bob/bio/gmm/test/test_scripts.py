

from __future__ import print_function

import bob.measure

import os
import sys
import shutil
import tempfile
import numpy

import bob.io.base.test_utils
import bob.io.image
import bob.bio.base
import bob.bio.gmm
from . import utils

from nose.plugins.skip import SkipTest

import pkg_resources

regenerate_reference = False

from bob.bio.base.script.verify import main

data_dir = pkg_resources.resource_filename('bob.bio.gmm', 'test/data')

def _verify(parameters, test_dir, sub_dir, ref_modifier="", score_modifier=('scores',''), executable = main):
  try:
    executable([sys.argv[0]] + parameters)

    # assert that the score file exists
    score_files = [os.path.join(test_dir, sub_dir, 'Default', norm, '%s-dev%s'%score_modifier) for norm in ('nonorm',  'ztnorm')]
    assert os.path.exists(score_files[0]), "Score file %s does not exist" % score_files[0]
    assert os.path.exists(score_files[1]), "Score file %s does not exist" % score_files[1]

    # also assert that the scores are still the same -- though they have no real meaning
    reference_files = [os.path.join(data_dir, 'scores-%s%s-dev'%(norm, ref_modifier)) for norm in ('nonorm',  'ztnorm')]

    if regenerate_reference:
      for i in (0,1):
        shutil.copy(score_files[i], reference_files[i])

    for i in (0,1):
      d = []
      # read reference and new data
      for score_file in (score_files[i], reference_files[i]):
        f = bob.measure.load.open_file(score_file)
        d_ = []
        for line in f:
          if isinstance(line, bytes): line = line.decode('utf-8')
          d_.append(line.rstrip().split())
        d.append(numpy.array(d_))

      assert d[0].shape == d[1].shape
      # assert that the data order is still correct
      assert (d[0][:,0:3] == d[1][:, 0:3]).all()
      # assert that the values are OK
      assert numpy.allclose(d[0][:,3].astype(float), d[1][:,3].astype(float), 1e-5)

  finally:
    shutil.rmtree(test_dir)


def test_gmm_base():
  test_dir = tempfile.mkdtemp(prefix='frltest_')
  # define dummy parameters
  parameters = [
      '-d', 'dummy',
      '-p', 'dummy',
      '-e', 'dummy',
      '-a', 'bob.bio.gmm.algorithm.GMM(2, 2, 2)', '--import', 'bob.bio.gmm',
      '--zt-norm',
      '-s', 'test_gmm_sequential', '-vv',
      '--temp-directory', test_dir,
      '--result-directory', test_dir
  ]

  print (bob.bio.base.tools.command_line(parameters))

  _verify(parameters, test_dir, 'test_gmm_sequential', ref_modifier='-gmm')


def test_gmm_parallel():
  from bob.bio.gmm.script.verify_gmm import main
  test_dir = tempfile.mkdtemp(prefix='frltest_')
  test_database = os.path.join(test_dir, "submitted.sql3")
  # define dummy parameters
  parameters = [
      '-d', 'dummy',
      '-p', 'dummy',
      '-e', 'dummy',
      '-a', 'bob.bio.gmm.algorithm.GMM(2, 2, 2)', '--import', 'bob.bio.gmm', 'bob.io.image',
      '-g', 'bob.bio.base.grid.Grid(grid = "local", number_of_parallel_processes = 2, scheduler_sleep_time = 0.1)', '-G', test_database, '--run-local-scheduler', '-R',
      '--clean-intermediate',
      '--zt-norm',
      '-s', 'test_gmm_parallel', '-vv',
      '--temp-directory', test_dir,
      '--result-directory', test_dir,
  ]

  print (bob.bio.base.tools.command_line(parameters))

  _verify(parameters, test_dir, 'test_gmm_parallel', executable=main, ref_modifier='-gmm')
